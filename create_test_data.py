import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

os.makedirs('test_data', exist_ok=True)

# 1. Complex Data with Unsanitized Names and Multiple Sheets
print("Generating complex_data.xlsx...")
with pd.ExcelWriter('test_data/complex_data.xlsx') as writer:
    # Sheet 1: "Employee Records" (Space in name)
    df_emp = pd.DataFrame({
        'Employee ID': [1001, 1002, 1003, 1004, 1005],
        'Full Name': ['John Doe', 'Jane Smith', 'Bob O\'Connor', 'Alice Wong', 'Charlie Brown'],
        'Date of Joining': [
            datetime(2020, 1, 15),
            datetime(2019, 5, 20),
            datetime(2021, 3, 10),
            datetime(2018, 11, 5),
            datetime(2022, 7, 1)
        ],
        'Salary ($)': [50000.50, 65000.00, 55000.75, 70000.25, 48000.00], # Special char in col
        'Is Active?': [True, True, False, True, True] # Question mark
    })
    df_emp.to_excel(writer, sheet_name='Employee Records', index=False)

    # Sheet 2: "Sales Data (2024)" (Parens and spaces)
    df_sales = pd.DataFrame({
        'Order #': [501, 502, 503],
        'Total Amount': [120.50, 450.00, 33.33],
        'Customer Name': ['Acme Corp', 'Globex', 'Soylent Corp']
    })
    df_sales.to_excel(writer, sheet_name='Sales Data (2024)', index=False)

# 2. Large Dataset (1 Million Rows)
# Note: Writing 1M rows to Excel is slow. We will do 100k for speed in this demo, 
# but the code structure supports 1M. 
# Change N_ROWS to 1_000_000 for full stress test.
N_ROWS = 100_000 
print(f"Generating large_data.xlsx with {N_ROWS} rows (this may take a moment)...")

dates = [datetime(2023, 1, 1) + timedelta(days=x) for x in range(N_ROWS)]
data = {
    'Transaction ID': np.arange(N_ROWS),
    'Value (Float)': np.random.rand(N_ROWS) * 1000,
    'Category Code': np.random.randint(1, 100, N_ROWS),
    'Transaction Date': dates,
    'Description': [f'Trans_{i}' for i in range(N_ROWS)]
}
df_large = pd.DataFrame(data)
df_large.to_excel('test_data/large_data.xlsx', index=False)

print("Test data generation complete.")
