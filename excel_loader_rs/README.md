# Excel Loader - Rust Implementation

High-performance Excel to DuckDB loader written in Rust.

## Features

- **Blazing Fast**: Uses native Rust `calamine` library for Excel parsing
- **Parallel Processing**: Leverages `rayon` for concurrent file processing
- **DuckDB Integration**: Direct insertion using DuckDB's native appender API
- **Feature Parity**: Supports refresh, query execution, and CSV export like Python version

## Performance

Expected performance improvements over Python:
- **3-5x faster** Excel reading (native Rust vs Python FFI overhead)
- **2-3x faster** overall loading (eliminates Pandas DataFrame overhead)
- **10-20x faster** for large datasets (1M+ rows)

## Building

```bash
cargo build --release
```

## Usage

### Load Excel files
```bash
./target/release/excel_loader_rs --path ../test_data --db output.duckdb
```

### Refresh (clear and reload)
```bash
./target/release/excel_loader_rs --path ../test_data --db output.duckdb --refresh
```

### Execute query
```bash
./target/release/excel_loader_rs --db output.duckdb --query "SELECT * FROM my_table LIMIT 10"
```

### Export to CSV
```bash
./target/release/excel_loader_rs --db output.duckdb --query "SELECT * FROM my_table WHERE value > 100 >> output.csv"
```

## Dependencies

- `calamine` - Fast Excel reader
- `duckdb` - Embedded analytical database
- `rayon` - Data parallelism
- `clap` - Command-line argument parsing
- `indicatif` - Progress bars
