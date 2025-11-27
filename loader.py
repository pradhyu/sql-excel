import os
import sqlite3
import pandas as pd
from pathlib import Path
from utils import sanitize_identifier

class ExcelLoader:
    def __init__(self, db_path=None, backend='duckdb'):
        """
        Initialize ExcelLoader with specified backend.
        
        Args:
            db_path: Path to database file (default: ~/.sql_excel_data.db or .duckdb)
            backend: 'sqlite' or 'duckdb' (default: 'duckdb')
        """
        self.backend = backend.lower()
        
        # Set default path based on backend
        if db_path is None:
            ext = '.duckdb' if self.backend == 'duckdb' else '.db'
            db_path = str(Path.home() / f'.sql_excel_data{ext}')
        
        self.db_path = db_path
        
        # Create connection based on backend
        if self.backend == 'duckdb':
            import duckdb
            self.conn = duckdb.connect(db_path)
            self.cursor = self.conn.cursor()
        else:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            
            # SQLite-specific optimizations
            self.cursor.execute("PRAGMA journal_mode=WAL")
            self.cursor.execute("PRAGMA synchronous=NORMAL")
            self.cursor.execute("PRAGMA cache_size=-64000")
            self.cursor.execute("PRAGMA temp_store=MEMORY")
            self.conn.commit()

    def load_path(self, path):
        """
        Loads Excel files from a directory or a single file.
        Returns a list of loaded table names.
        """
        import concurrent.futures
        
        loaded_tables = []
        files_to_process = []
        
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        filepath = os.path.join(root, file)
                        files_to_process.append(filepath)
        elif os.path.isfile(path) and path.endswith(('.xlsx', '.xls')):
            files_to_process.append(path)
        else:
            print(f"Invalid path or no Excel files found: {path}")
            return []
        
        # Process files in parallel to read data
        # Writing to DB must be sequential to avoid locking/concurrency issues
        print(f"Processing {len(files_to_process)} files with {os.cpu_count()} threads...")
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all read tasks
            future_to_file = {executor.submit(self.read_excel_file, f): f for f in files_to_process}
            
            for future in concurrent.futures.as_completed(future_to_file):
                filepath = future_to_file[future]
                try:
                    # Get read results (list of (table_name, df))
                    results = future.result()
                    
                    # Write to DB sequentially
                    for table_name, df in results:
                        self.dataframe_to_db(df, table_name)
                        loaded_tables.append(table_name)
                        
                    # Print status (using the timing from the read operation)
                    # We could track write time too but reading is usually the bottleneck
                    pass 
                except Exception as e:
                    print(f"Error processing file {filepath}: {e}")
        
        return loaded_tables

    def read_excel_file(self, filepath):
        """
        Reads an Excel file and returns a list of (table_name, dataframe) tuples.
        """
        import time
        start_time = time.time()
        
        filename = os.path.splitext(os.path.basename(filepath))[0]
        sanitized_filename = sanitize_identifier(filename)
        results = []

        try:
            # Try using calamine engine first (much faster)
            try:
                xls = pd.ExcelFile(filepath, engine='calamine')
            except ImportError:
                # Fallback to default (openpyxl) if calamine not available
                xls = pd.ExcelFile(filepath)
            except Exception:
                # Fallback for other errors
                xls = pd.ExcelFile(filepath)
                
            for sheet_name in xls.sheet_names:
                # Use the same engine for reading sheets
                if hasattr(xls, 'engine') and xls.engine == 'calamine':
                    df = pd.read_excel(xls, sheet_name=sheet_name, engine='calamine')
                else:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                
                # Sanitize table name
                sanitized_sheet = sanitize_identifier(sheet_name)
                table_name = f"{sanitized_filename}_{sanitized_sheet}"
                
                # Sanitize column names
                df.columns = [sanitize_identifier(col) for col in df.columns]
                
                results.append((table_name, df))
                
            elapsed = time.time() - start_time
            engine_used = "calamine" if hasattr(xls, 'engine') and xls.engine == 'calamine' else "openpyxl"
            print(f"Read {filepath} -> {len(results)} sheet(s) in {elapsed:.2f}s ({engine_used})")
                
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            raise e

        return results

    def dataframe_to_db(self, df, table_name):
        """
        Writes a pandas DataFrame to the database (SQLite or DuckDB).
        """
        try:
            if self.backend == 'duckdb':
                # DuckDB can insert directly from pandas (very fast)
                self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
            else:
                # SQLite with optimizations
                df.to_sql(table_name, self.conn, if_exists='replace', index=False, method='multi', chunksize=1000)
        except Exception as e:
            print(f"Error writing table {table_name}: {e}")

    def has_data(self):
        """
        Check if the database has any tables loaded.
        """
        tables = self.get_tables()
        return len(tables) > 0
    
    def clear_data(self):
        """
        Clear all tables from the database.
        """
        tables = self.get_tables()
        for table in tables:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
        self.conn.commit()
        print(f"Cleared {len(tables)} table(s) from database.")
    
    def get_tables(self):
        """
        Returns a list of all tables in the database.
        """
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in self.cursor.fetchall()]

    def get_table_details(self):
        """
        Returns a list of dictionaries containing table metadata:
        name, row_count, col_count, columns (with types)
        """
        tables = self.get_tables()
        details = []
        for table in tables:
            # Get row count
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = self.cursor.fetchone()[0]
            except:
                row_count = 0
            
            # Get columns info with types
            try:
                # PRAGMA table_info returns (cid, name, type, notnull, dflt_value, pk)
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns_info = self.cursor.fetchall()
                # Format as "column_name (TYPE)"
                columns = [f"{col[1]} ({col[2]})" if col[2] else col[1] for col in columns_info]
                col_count = len(columns)
            except:
                columns = []
                col_count = 0
            
            details.append({
                "name": table,
                "rows": row_count,
                "cols": col_count,
                "columns": columns
            })
        return details

    def get_schema(self, table_name):
        """
        Returns the CREATE TABLE statement for a given table.
        """
        self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        result = self.cursor.fetchone()
        return result[0] if result else None

    def execute_query(self, query):
        """
        Executes a raw SQL query and returns the results and headers.
        """
        try:
            # Check if it's a SELECT query to return results
            if query.strip().upper().startswith("SELECT"):
                df = pd.read_sql_query(query, self.conn)
                return df
            else:
                self.cursor.execute(query)
                self.conn.commit()
                return None
        except Exception as e:
            return f"Error: {e}"
