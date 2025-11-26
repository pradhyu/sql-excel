# Test Queries for SQL-Excel REPL

Copy and paste these queries into the REPL to test various scenarios with the generated `test_data`.

## 1. Basic Data Inspection
Check the contents of the loaded tables.

```sql
-- List all users
SELECT * FROM users_Sheet1;

-- List all orders
SELECT * FROM orders_Sheet1;
```

## 2. Joins (Users & Orders)
Join tables from two different Excel files (`users.xlsx` and `orders.xlsx`).

```sql
-- See which user bought what
SELECT u.name, o.product_name, o.amount 
FROM users_Sheet1 u 
JOIN orders_Sheet1 o ON u.id = o.user_id;

-- Total spending per user
SELECT u.name, SUM(o.amount) as total_spent 
FROM users_Sheet1 u 
JOIN orders_Sheet1 o ON u.id = o.user_id 
GROUP BY u.name;
```

## 3. Handling Special Characters (Complex Data)
Query tables where sheet names and column headers contained spaces and symbols.
*Note: `Salary ($)` became `Salary____` and `Is Active?` became `Is_Active_`.*

```sql
-- Select high earners who are active
SELECT Full_Name, Salary____, Date_of_Joining 
FROM complex_data_Employee_Records 
WHERE Is_Active_ = 1 AND Salary____ > 55000;

-- Order sales by amount (from "Sales Data (2024)")
SELECT Customer_Name, Total_Amount 
FROM complex_data_Sales_Data__2024_ 
ORDER BY Total_Amount DESC;
```

## 4. Large Dataset Aggregations
Perform analytics on the larger dataset (100k rows).

```sql
-- Count total rows
SELECT COUNT(*) FROM large_data_Sheet1;

-- Average value by category
SELECT Category_Code, COUNT(*) as transaction_count, AVG(Value__Float_) as avg_value 
FROM large_data_Sheet1 
GROUP BY Category_Code 
ORDER BY avg_value DESC 
LIMIT 10;
```

## 5. Date Filtering
Filter records based on date columns.

```sql
-- Find employees who joined after 2020
SELECT Full_Name, Date_of_Joining 
FROM complex_data_Employee_Records 
WHERE Date_of_Joining >= '2020-01-01';
```
