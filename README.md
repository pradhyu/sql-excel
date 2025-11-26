# Excel to SQLite REPL

A Python-based interactive shell that allows you to load Excel files into an in-memory SQLite database and query them using SQL with a beautiful, colorful interface.

## Features

- **Load Excel Files**: Load a single `.xlsx` file or an entire directory of files.
- **Automatic Sanitization**: 
  - Sheet names are converted to valid SQL table names (e.g., "Sales Data (2024)" -> `Sales_Data__2024_`).
  - Column headers are sanitized to be valid SQL identifiers (e.g., "Salary ($)" -> `Salary____`).
- **SQL Querying**: Full SQLite support. You can `JOIN` tables derived from different Excel files.
- **Large Dataset Support**: Handles large Excel files (tested with 100k+ rows) using Pandas.
- **Rich UI**: Colorful, formatted output using the `rich` library.
- **Multi-line Queries**: Write SQL queries across multiple lines. Press Enter to continue, end with `;` to execute.
- **Smart History**: Multi-line queries are stored as a single history entry (use Up arrow to recall).
- **Detailed Metadata**: The `tables` command shows row count, column count, and all column names.

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

*Note: The database is in-memory. While you can execute `INSERT`, `UPDATE`, or `DELETE` statements, changes will be lost when you exit the REPL.*

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

1. **Generate Test Data** (optional):
   First, generate the sample data so you can follow the examples below:
   ```bash
   python create_test_data.py
   ```

2. **Start the REPL**:
   ```bash
   python main.py
   ```

3. **Load Data**:
   Inside the REPL, load the test data folder:
   ```text
   (sql-excel) load test_data
   ```
   *Output:*
   ```text
   Loaded test_data/users.xlsx [Sheet1] -> Table: users_Sheet1
   Loaded test_data/orders.xlsx [Sheet1] -> Table: orders_Sheet1
   Loaded test_data/complex_data.xlsx [Employee Records] -> Table: complex_data_Employee_Records
   Loaded test_data/complex_data.xlsx [Sales Data (2024)] -> Table: complex_data_Sales_Data__2024_
   Loaded test_data/large_data.xlsx [Sheet1] -> Table: large_data_Sheet1
   Successfully loaded 5 tables.
   ```

4. **View Tables with Metadata**:
   ```text
   (sql-excel) tables
   ```
   This displays a formatted table showing:
   - Table name
   - Number of rows
   - Number of columns
   - Column names

5. **Query Data**:

   **Example 1: Simple Select**
   ```sql
   SELECT * FROM users_Sheet1;
   ```

   **Example 2: Multi-line Join Query**
   ```sql
   SELECT u.name, o.product_name, o.amount 
   FROM users_Sheet1 u 
   JOIN orders_Sheet1 o ON u.id = o.user_id;
   ```
   *Note: Press Enter to add new lines. End with `;` and press Enter to execute.*

   **Example 3: Querying data with sanitized names**
   ```sql
   SELECT Full_Name, Salary____ 
   FROM complex_data_Employee_Records 
   WHERE Salary____ > 60000;
   ```

   **Example 4: Aggregation with Group By**
   ```sql
   SELECT u.name, SUM(o.amount) as total_spent 
   FROM users_Sheet1 u 
   JOIN orders_Sheet1 o ON u.id = o.user_id 
   GROUP BY u.name 
   ORDER BY total_spent DESC;
   ```

6. **Exit**:
   ```text
   (sql-excel) exit
   ```

## Additional Resources

- See `TEST_QUERIES.md` for more example queries you can copy and paste.
- Use the `help` command inside the REPL to see all available commands.
