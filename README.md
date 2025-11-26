# Excel to SQLite REPL

A Python-based interactive shell that allows you to load Excel files into a SQLite database and query them using SQL with a beautiful, colorful interface. Features persistent caching, auto-loading, and both interactive and non-interactive modes.

## Features

- **Load Excel Files**: Load a single `.xlsx` file or an entire directory of files.
- **Persistent Caching**: Data is cached in `~/.sql_excel_data.db` - load once, query anytime!
- **Auto-Loading**: Pass a data folder as argument to auto-load on startup.
- **Non-Interactive Mode**: Execute queries directly from command line with `--query`.
- **Automatic Sanitization**: 
  - Sheet names are converted to valid SQL table names (e.g., "Sales Data (2024)" -> `Sales_Data__2024_`).
  - Column headers are sanitized to be valid SQL identifiers (e.g., "Salary ($)" -> `Salary____`).
- **SQL Querying**: Full SQLite support. You can `JOIN` tables derived from different Excel files.
- **Large Dataset Support**: Handles large Excel files (tested with 100k+ rows) using Pandas.
- **Rich UI**: Colorful, formatted output using the `rich` library.
- **Multi-line Queries**: Write SQL queries across multiple lines. Press Enter to continue, end with `;` to execute.
- **Smart History**: Multi-line queries are stored as a single history entry (use Up arrow to recall).
- **Detailed Metadata**: The `tables` command shows row count, column count, and all column names with types.

## Supported SQL Features

Since this tool uses the standard SQLite engine, **all standard SQLite SQL syntax is supported**. This includes but is not limited to:

- **Standard Clauses**: `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`, `LIMIT`.
- **Joins**: `INNER JOIN`, `LEFT JOIN`, `CROSS JOIN` (Right and Full Outer joins are not natively supported by SQLite, but can be emulated).
- **Aggregations**: `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`.
- **Subqueries & CTEs**: Common Table Expressions (`WITH ... AS`) and nested queries.
- **Built-in Functions**:
  - String: `UPPER()`, `LOWER()`, `SUBSTR()`, `TRIM()`, `REPLACE()`.
  - Date/Time: `DATE()`, `TIME()`, `DATETIME()`, `STRFTIME()`.
  - Math: `ABS()`, `ROUND()`, `RANDOM()`.
- **Set Operations**: `UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`.

*Note: The database is persistent (stored in `~/.sql_excel_data.db`). Changes made with `INSERT`, `UPDATE`, or `DELETE` will persist across sessions. Use the `refresh` command to reload from Excel files.*

## Installation

This project uses `uv` for fast dependency management.

1. **Install uv** (if not already installed):
   ```bash
   pip install uv
   ```

2. **Set up the environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

## Usage

### Quick Start

1. **Generate Test Data** (optional):
   ```bash
   uv run python create_test_data.py
   ```

2. **Auto-load and start REPL** (recommended):
   ```bash
   uv run python main.py test_data
   ```
   This loads the data folder on first run and caches it. Subsequent runs use the cache automatically!

### Interactive Mode

**Start the REPL with auto-loading:**
```bash
uv run python main.py test_data
```

**Or start empty and load manually:**
```bash
uv run python main.py
```
Then inside the REPL:
```text
(sql-excel) load test_data
```

**View loaded tables:**
```text
(sql-excel) tables
```

**Refresh data from Excel files:**
```text
(sql-excel) refresh
```
This clears the cache and reloads from the original Excel files.

### Non-Interactive Mode

Execute queries directly without entering the REPL:

```bash
# Query using cached data (defaults to test_data folder)
uv run python main.py --query "SELECT * FROM users_Sheet1"

# Short form
uv run python main.py -q "SELECT name, email FROM users_Sheet1 WHERE id = 1"

# Specify a different source folder
uv run python main.py --source my_data -q "SELECT * FROM my_table"

# Complex query with joins (uses default test_data)
uv run python main.py -q "SELECT u.name, o.product_name FROM users_Sheet1 u JOIN orders_Sheet1 o ON u.id = o.user_id"
```

### Query Examples

**Simple Select:**
```sql
SELECT * FROM users_Sheet1;
```

**Multi-line Join Query:**
```sql
SELECT u.name, o.product_name, o.amount 
FROM users_Sheet1 u 
JOIN orders_Sheet1 o ON u.id = o.user_id;
```
*Note: Press Enter to add new lines. End with `;` and press Enter to execute.*

**Querying with Sanitized Names:**
```sql
SELECT Full_Name, Salary____ 
FROM complex_data_Employee_Records 
WHERE Salary____ > 60000;
```

**Aggregation with Group By:**
```sql
SELECT u.name, SUM(o.amount) as total_spent 
FROM users_Sheet1 u 
JOIN orders_Sheet1 o ON u.id = o.user_id 
GROUP BY u.name 
ORDER BY total_spent DESC;
```

### Available Commands

- `load <path>` - Load Excel file(s) from a path
- `tables` - List all tables with metadata (rows, columns, types)
- `schema <table>` - Show CREATE TABLE statement
- `refresh` - Clear cache and reload from Excel files
- `exit` / `quit` - Exit the REPL
- `<sql query>` - Execute any SQL query (end with `;`)

### Command-Line Arguments

```bash
python main.py [data_folder] [--query QUERY] [--source SOURCE] [--db DB_PATH]
```

- `data_folder` - Optional positional argument for data folder path
- `--query`, `-q` - Execute a query and exit (non-interactive)
- `--source`, `-s` - Default data source folder (default: `test_data`)
- `--db` - Custom database path (default: `~/.sql_excel_data.db`)

**Note:** The positional `data_folder` takes priority over `--source`. If neither is provided, it defaults to `test_data`.

## Additional Resources

- See `TEST_QUERIES.md` for more example queries you can copy and paste.
- Use the `help` command inside the REPL to see all available commands.
