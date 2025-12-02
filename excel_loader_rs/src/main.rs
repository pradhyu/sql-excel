use anyhow::{Context, Result};
use calamine::{open_workbook, Data, Reader, Xlsx};
use clap::Parser;
use duckdb::Connection;
use indicatif::{ProgressBar, ProgressStyle};
use rayon::prelude::*;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::Instant;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to the folder containing Excel files
    #[arg(short, long, default_value = "test_data")]
    path: String,

    /// Path to the output DuckDB database
    #[arg(short, long, default_value = "rust_speedup.duckdb")]
    db: String,

    /// Refresh flag – clear existing tables before loading
    #[arg(long)]
    refresh: bool,

    /// Execute a single query and exit (non-interactive mode)
    #[arg(long)]
    query: Option<String>,

    /// Choose backend (duckdb or sqlite) – currently only duckdb is supported in Rust
    #[arg(long, default_value = "duckdb")]
    backend: String,
}

fn sanitize_identifier(name: &str) -> String {
    let mut sanitized = String::with_capacity(name.len());
    for c in name.chars() {
        if c.is_alphanumeric() {
            sanitized.push(c);
        } else {
            sanitized.push('_');
        }
    }
    // Remove duplicate underscores
    let mut result = String::new();
    let mut last_char_was_underscore = false;
    for c in sanitized.chars() {
        if c == '_' {
            if !last_char_was_underscore {
                result.push(c);
                last_char_was_underscore = true;
            }
        } else {
            result.push(c);
            last_char_was_underscore = false;
        }
    }
    result.trim_matches('_').to_string()
}

fn main() -> Result<()> {
    let args = Args::parse();
    let start_total = Instant::now();

    // Collect files
    let mut files = Vec::new();
    let path = Path::new(&args.path);
    if path.is_dir() {
        for entry in fs::read_dir(path)? {
            let entry = entry?;
            let path = entry.path();
            if let Some(ext) = path.extension() {
                if ext == "xlsx" || ext == "xls" {
                    files.push(path);
                }
            }
        }
    } else if path.is_file() {
        files.push(path.to_path_buf());
    }

    println!("Found {} Excel files to process.", files.len());

    // Initialize DuckDB connection
    // Note: DuckDB handles concurrency well, but for bulk loading, 
    // it's often best to have one connection per thread or share one if using appender.
    // However, DuckDB's single-writer model means we should probably process files in parallel 
    // but write sequentially OR use separate connections if DuckDB supports it (it does for WAL).
    // For this POC, let's try parallel reading and sequential writing to be safe and fair comparison to Python v2.
    
    // Actually, we can do better: Read in parallel, collect data, then write. 
    // But for 1M rows, holding in memory is fine.
    
    let pb = ProgressBar::new(files.len() as u64);
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta}) {msg}")
        .unwrap()
        .progress_chars("#>-"));

    // We will use a mutex to protect the DB connection for sequential writing
    // This mimics the Python optimization we did (parallel read, sequential write)
    let conn = Connection::open(&args.db)?;
    
    // Refresh if requested
    if args.refresh {
        println!("Clearing existing tables...");
        let mut stmt = conn.prepare("SELECT name FROM sqlite_master WHERE type='table'")?;
        let tables_iter = stmt.query_map([], |row| row.get::<_, String>(0))?;
        
        let mut tables = Vec::new();
        for table in tables_iter {
            tables.push(table?);
        }
        
        for table in tables {
            conn.execute(&format!("DROP TABLE IF EXISTS \"{}\"", table), [])?;
        }
        println!("Cleared tables.");
    }

    let conn_mutex = Arc::new(Mutex::new(conn));

    files.par_iter().for_each(|file_path| {
        let filename = file_path.file_stem().unwrap().to_string_lossy();
        let sanitized_filename = sanitize_identifier(&filename);
        
        let start_read = Instant::now();
        
        // Read Excel file
        match process_excel_file(file_path, &sanitized_filename, &conn_mutex) {
            Ok(count) => {
                let duration = start_read.elapsed();
                pb.set_message(format!("Processed {} ({} sheets) in {:.2?}", filename, count, duration));
            },
            Err(e) => {
                pb.set_message(format!("Error processing {}: {}", filename, e));
            }
        }
        pb.inc(1);
    });

    pb.finish_with_message("Done!");
    println!("Total time: {:.2?}", start_total.elapsed());

    // Execute query if provided
    if let Some(query_str) = args.query {
        let conn = conn_mutex.lock().unwrap();
        
        // Check for CSV export syntax: query >> filename.csv
        let (query, output_file) = if let Some(idx) = query_str.find(">>") {
            let q = query_str[..idx].trim();
            let f = query_str[idx+2..].trim();
            (q, Some(f))
        } else {
            (query_str.as_str(), None)
        };

        if let Some(path) = output_file {
            // Use DuckDB's COPY command for fast CSV export
            let copy_sql = format!("COPY ({}) TO '{}' (HEADER, DELIMITER ',')", query, path);
            match conn.execute(&copy_sql, []) {
                Ok(_) => println!("Saved query results to {}", path),
                Err(e) => println!("Error exporting to CSV: {}", e),
            }
        } else {
            // Print results to stdout
            // For simplicity in this POC, we'll just print row counts or basic info
            // Printing full table in Rust requires a bit more code (comfy-table)
            // Let's print the first few rows
            
            let mut stmt = conn.prepare(query)?;
            let column_count = stmt.column_count();
            
            // We need to handle dynamic types which is verbose in Rust/rusqlite
            // For this POC, let's just print "Query executed successfully" 
            // or try to print rows as debug string if possible.
            // DuckDB's arrow support is great but we are using the basic driver.
            
            println!("Executing query: {}", query);
            // Just execute and print count for now to verify it works
            // Or use a simple loop
            
            let mut rows = stmt.query([])?;
            let mut count = 0;
            while let Some(_row) = rows.next()? {
                count += 1;
            }
            println!("Query returned {} rows.", count);
        }
    }

    Ok(())
}

fn process_excel_file(file_path: &PathBuf, filename_prefix: &str, conn_mutex: &Arc<Mutex<Connection>>) -> Result<usize> {
    let mut workbook: Xlsx<_> = open_workbook(file_path).context("Cannot open file")?;
    let sheets = workbook.sheet_names().to_owned();
    let mut sheet_count = 0;

    for sheet_name in sheets {
        if let Ok(range) = workbook.worksheet_range(&sheet_name) {
            let sanitized_sheet = sanitize_identifier(&sheet_name);
            let table_name = format!("{}_{}", filename_prefix, sanitized_sheet);
            
            // Get headers
            let mut rows = range.rows();
            let headers = if let Some(h) = rows.next() {
                h
            } else {
                continue;
            };

            let mut column_names = Vec::new();
            let mut column_types = Vec::new(); // We'll infer types from the first data row

            // Peek at first data row to infer types
            // Note: This is a simple inference. A robust one would scan more rows.
            let first_data_row = range.rows().nth(1); 
            
            for (i, cell) in headers.iter().enumerate() {
                let name = cell.to_string();
                let sanitized_col = sanitize_identifier(&name);
                column_names.push(sanitized_col);
                
                // Infer type
                let duck_type = if let Some(row) = first_data_row {
                    if i < row.len() {
                        match row[i] {
                            Data::Int(_) => "BIGINT",
                            Data::Float(_) => "DOUBLE",
                            Data::Bool(_) => "BOOLEAN",
                            Data::String(_) => "VARCHAR",
                            Data::DateTime(_) => "TIMESTAMP",
                            _ => "VARCHAR",
                        }
                    } else {
                        "VARCHAR"
                    }
                } else {
                    "VARCHAR" // Default if no data
                };
                column_types.push(duck_type);
            }

            // Create Table
            {
                let conn = conn_mutex.lock().unwrap();
                let schema_cols: Vec<String> = column_names.iter().zip(column_types.iter())
                    .map(|(name, dtype)| format!("{} {}", name, dtype))
                    .collect();
                
                let create_sql = format!("CREATE OR REPLACE TABLE {} ({})", table_name, schema_cols.join(", "));
                conn.execute(&create_sql, [])?;
            }

            // Insert Data using Batch INSERT
            // DuckDB Appender API is strict with types, so we use SQL INSERTs for flexibility
            
            let rows_data: Vec<_> = range.rows().skip(1).collect();
            if !rows_data.is_empty() {
                let chunk_size = 1000;
                for chunk in rows_data.chunks(chunk_size) {
                    let mut query = format!("INSERT INTO {} VALUES ", table_name);
                    let mut params: Vec<String> = Vec::new(); // We'll inline values for simplicity/speed in this POC
                    // Note: In production, use prepared statements with parameters to avoid injection/issues.
                    // But for speed POC with trusted Excel files, string construction is fine and fast for DuckDB.
                    
                    let mut row_strings = Vec::new();
                    for row in chunk {
                        let mut val_strings = Vec::new();
                        for (i, cell) in row.iter().enumerate() {
                            if i >= column_types.len() { break; }
                            
                            let val = match cell {
                                Data::Int(v) => v.to_string(),
                                Data::Float(v) => v.to_string(),
                                Data::String(v) => format!("'{}'", v.replace("'", "''")), // Escape single quotes
                                Data::Bool(v) => v.to_string(),
                                Data::DateTime(v) => v.to_string(), // Might need formatting
                                Data::DateTimeIso(v) => format!("'{}'", v),
                                Data::DurationIso(v) => format!("'{}'", v),
                                Data::Error(_) | Data::Empty => "NULL".to_string(),
                            };
                            val_strings.push(val);
                        }
                        // Pad with NULLs if row is short
                        while val_strings.len() < column_types.len() {
                            val_strings.push("NULL".to_string());
                        }
                        row_strings.push(format!("({})", val_strings.join(", ")));
                    }
                    
                    query.push_str(&row_strings.join(", "));
                    
                    let conn = conn_mutex.lock().unwrap();
                    conn.execute(&query, [])?;
                }
            }
            
            sheet_count += 1;
        }
    }

    Ok(sheet_count)
}
