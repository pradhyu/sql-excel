# Excel to SQLite REPL

A Python-based interactive shell that allows you to load Excel files into an in-memory SQLite database and query them using SQL.

## Features

- **Load Excel Files**: Load a single `.xlsx` file or an entire directory of files.
- **Automatic Sanitization**: 
  - Sheet names are converted to valid SQL table names (e.g., "Sales Data (2024)" -> `Sales_Data__2024_`).
  - Column headers are sanitized to be valid SQL identifiers (e.g., "Salary ($)" -> `Salary____`).
- **SQL Querying**: Full SQLite support. You can `JOIN` tables derived from different Excel files.
- **Large Dataset Support**: Handles large Excel files (tested with 100k+ rows) using Pandas.

## Installation

This project uses `uv` for fast dependency management.

1. **Install uv** (if not already installed):
   ```bash
   pip install uv
   ```

2. **Set up the environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

## Usage

1. **Generate Test Data**:
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
   ```

4. **View Tables**:
   ```text
   (sql-excel) tables
   ```

5. **Query Data (Copy & Paste these examples)**:

   **Example 1: Simple Select**
   ```sql
   SELECT * FROM users_Sheet1;
   ```

   **Example 2: Join between two files (Users and Orders)**
   ```sql
   SELECT u.name, o.product_name, o.amount 
   FROM users_Sheet1 u 
   JOIN orders_Sheet1 o ON u.id = o.user_id;
   ```

   **Example 3: Querying data with sanitized names**
   *Note how "Salary ($)" became `Salary____` and "Sales Data (2024)" became `complex_data_Sales_Data__2024_`*
   ```sql
   SELECT Full_Name, Salary____ 
   FROM complex_data_Employee_Records 
   WHERE Salary____ > 60000;
   ```

6. **Exit**:
   ```text
   (sql-excel) exit
   ```
# sql-excel
