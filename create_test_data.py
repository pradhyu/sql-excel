import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

os.makedirs('test_data', exist_ok=True)

def generate_data(n_rows, filename):
    print(f"Generating {filename} with {n_rows} rows...")
    
    dates = [datetime(2023, 1, 1) + timedelta(days=x % 365) for x in range(n_rows)]
    data = {
        'Transaction ID': np.arange(n_rows),
        'Value (Float)': np.random.rand(n_rows) * 1000,
        'Category Code': np.random.randint(1, 100, n_rows),
        'Transaction Date': dates,
        'Description': [f'Trans_{i}' for i in range(n_rows)]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(f'test_data/{filename}', index=False)
    print(f"Saved test_data/{filename}")

# 1. Generate requested datasets
datasets = [
    (10_000, 'data_10k.xlsx'),
    (20_000, 'data_20k.xlsx'),
    (50_000, 'data_50k.xlsx'),
    (70_000, 'data_70k.xlsx'),
    (1_000_000, 'data_1mil.xlsx')
]

for rows, fname in datasets:
    generate_data(rows, fname)

print("Test data generation complete.")
