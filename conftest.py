"""Pytest configuration and fixtures for Excel to SQLite REPL tests."""

import pytest
import tempfile
import os
from pathlib import Path
import pandas as pd
from loader import ExcelLoader


@pytest.fixture
def temp_db():
    """Create a temporary database file that gets cleaned up after tests."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_excel_dir():
    """Create a temporary directory for test Excel files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_excel_file(temp_excel_dir):
    """Create a simple test Excel file with one sheet."""
    file_path = temp_excel_dir / "simple.xlsx"
    
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100, 200, 300]
    })
    
    df.to_excel(file_path, sheet_name='Sheet1', index=False)
    return file_path


@pytest.fixture
def multi_sheet_excel_file(temp_excel_dir):
    """Create an Excel file with multiple sheets."""
    file_path = temp_excel_dir / "multi_sheet.xlsx"
    
    df1 = pd.DataFrame({
        'user_id': [1, 2, 3],
        'username': ['alice', 'bob', 'charlie']
    })
    
    df2 = pd.DataFrame({
        'order_id': [101, 102, 103],
        'user_id': [1, 2, 1],
        'amount': [50.0, 75.0, 100.0]
    })
    
    with pd.ExcelWriter(file_path) as writer:
        df1.to_excel(writer, sheet_name='Users', index=False)
        df2.to_excel(writer, sheet_name='Orders', index=False)
    
    return file_path


@pytest.fixture
def special_names_excel_file(temp_excel_dir):
    """Create an Excel file with special characters in sheet and column names."""
    file_path = temp_excel_dir / "special_names.xlsx"
    
    df = pd.DataFrame({
        'Employee ID': [1, 2, 3],
        'Full Name (Last, First)': ['Doe, John', 'Smith, Jane', 'Brown, Bob'],
        'Salary ($)': [50000, 60000, 70000],
        'Start Date': ['2020-01-01', '2021-02-15', '2022-03-20']
    })
    
    df.to_excel(file_path, sheet_name='Employee Records (2024)', index=False)
    return file_path


@pytest.fixture
def loader_with_temp_db(temp_db):
    """Create an ExcelLoader instance with a temporary database."""
    loader = ExcelLoader(db_path=temp_db)
    yield loader
    loader.conn.close()


@pytest.fixture
def loader_with_simple_data(loader_with_temp_db, simple_excel_file):
    """Create a loader with simple test data already loaded."""
    loader_with_temp_db.load_path(str(simple_excel_file))
    return loader_with_temp_db


@pytest.fixture
def loader_with_multi_sheet_data(loader_with_temp_db, multi_sheet_excel_file):
    """Create a loader with multi-sheet test data already loaded."""
    loader_with_temp_db.load_path(str(multi_sheet_excel_file))
    return loader_with_temp_db
