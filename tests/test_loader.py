"""Tests for loader.py - ExcelLoader class."""

import pytest
import pandas as pd
from loader import ExcelLoader


class TestExcelLoaderInitialization:
    """Test ExcelLoader initialization."""
    
    def test_init_with_temp_db(self, temp_db):
        """Test initialization with a temporary database path."""
        loader = ExcelLoader(db_path=temp_db)
        assert loader.db_path == temp_db
        assert loader.conn is not None
        assert loader.cursor is not None
        loader.conn.close()
    
    def test_init_creates_connection(self, loader_with_temp_db):
        """Test that initialization creates a valid database connection."""
        # Try to execute a simple query
        loader_with_temp_db.cursor.execute("SELECT 1")
        result = loader_with_temp_db.cursor.fetchone()
        assert result == (1,)


class TestExcelLoading:
    """Test Excel file loading functionality."""
    
    def test_load_single_file(self, loader_with_temp_db, simple_excel_file):
        """Test loading a single Excel file."""
        tables = loader_with_temp_db.load_path(str(simple_excel_file))
        
        assert len(tables) == 1
        assert 'simple_Sheet1' in tables[0]
    
    def test_load_multi_sheet_file(self, loader_with_temp_db, multi_sheet_excel_file):
        """Test loading an Excel file with multiple sheets."""
        tables = loader_with_temp_db.load_path(str(multi_sheet_excel_file))
        
        assert len(tables) == 2
        table_names = [t for t in tables]
        assert any('Users' in t for t in table_names)
        assert any('Orders' in t for t in table_names)
    
    def test_load_directory(self, loader_with_temp_db, temp_excel_dir, simple_excel_file, multi_sheet_excel_file):
        """Test loading all Excel files from a directory."""
        tables = loader_with_temp_db.load_path(str(temp_excel_dir))
        
        # Should load both files (1 sheet + 2 sheets = 3 tables)
        assert len(tables) == 3
    
    def test_sanitized_table_names(self, loader_with_temp_db, special_names_excel_file):
        """Test that table names are properly sanitized."""
        tables = loader_with_temp_db.load_path(str(special_names_excel_file))
        
        assert len(tables) == 1
        # Should sanitize "Employee Records (2024)" to something like "special_names_Employee_Records__2024_"
        assert '_' in tables[0]
        assert '(' not in tables[0]
        assert ')' not in tables[0]
    
    def test_data_integrity(self, loader_with_simple_data):
        """Test that loaded data matches the source."""
        df = loader_with_simple_data.execute_query("SELECT * FROM simple_Sheet1")
        
        assert len(df) == 3
        assert list(df.columns) == ['id', 'name', 'value']
        assert df['name'].tolist() == ['Alice', 'Bob', 'Charlie']
        assert df['value'].tolist() == [100, 200, 300]


class TestDatabaseOperations:
    """Test database operation methods."""
    
    def test_has_data_empty(self, loader_with_temp_db):
        """Test has_data returns False for empty database."""
        assert loader_with_temp_db.has_data() is False
    
    def test_has_data_with_tables(self, loader_with_simple_data):
        """Test has_data returns True when tables exist."""
        assert loader_with_simple_data.has_data() is True
    
    def test_get_tables(self, loader_with_multi_sheet_data):
        """Test get_tables returns all loaded tables."""
        tables = loader_with_multi_sheet_data.get_tables()
        
        assert len(tables) == 2
        assert all(isinstance(t, str) for t in tables)
    
    def test_clear_data(self, loader_with_simple_data):
        """Test clear_data removes all tables."""
        assert loader_with_simple_data.has_data() is True
        
        loader_with_simple_data.clear_data()
        
        assert loader_with_simple_data.has_data() is False
        assert len(loader_with_simple_data.get_tables()) == 0
    
    def test_get_table_details(self, loader_with_simple_data):
        """Test get_table_details returns correct metadata."""
        details = loader_with_simple_data.get_table_details()
        
        assert len(details) == 1
        table_detail = details[0]
        
        assert 'name' in table_detail
        assert table_detail['rows'] == 3
        assert table_detail['cols'] == 3
        assert len(table_detail['columns']) == 3
    
    def test_get_schema(self, loader_with_simple_data):
        """Test get_schema returns CREATE TABLE statement."""
        tables = loader_with_simple_data.get_tables()
        schema = loader_with_simple_data.get_schema(tables[0])
        
        assert schema is not None
        assert 'CREATE TABLE' in schema
        assert tables[0] in schema


class TestQueryExecution:
    """Test SQL query execution."""
    
    def test_simple_select(self, loader_with_simple_data):
        """Test simple SELECT query."""
        result = loader_with_simple_data.execute_query("SELECT * FROM simple_Sheet1")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
    
    def test_select_with_where(self, loader_with_simple_data):
        """Test SELECT with WHERE clause."""
        result = loader_with_simple_data.execute_query(
            "SELECT * FROM simple_Sheet1 WHERE id = 1"
        )
        
        assert len(result) == 1
        assert result.iloc[0]['name'] == 'Alice'
    
    def test_aggregation(self, loader_with_simple_data):
        """Test aggregation queries."""
        result = loader_with_simple_data.execute_query(
            "SELECT COUNT(*) as count, SUM(value) as total FROM simple_Sheet1"
        )
        
        assert result.iloc[0]['count'] == 3
        assert result.iloc[0]['total'] == 600
    
    def test_join_query(self, loader_with_multi_sheet_data):
        """Test JOIN query across multiple tables."""
        tables = loader_with_multi_sheet_data.get_tables()
        users_table = [t for t in tables if 'Users' in t][0]
        orders_table = [t for t in tables if 'Orders' in t][0]
        
        query = f"""
            SELECT u.username, COUNT(o.order_id) as order_count
            FROM {users_table} u
            LEFT JOIN {orders_table} o ON u.user_id = o.user_id
            GROUP BY u.username
        """
        
        result = loader_with_multi_sheet_data.execute_query(query)
        
        assert len(result) == 3
        assert 'username' in result.columns
        assert 'order_count' in result.columns
    
    def test_order_by(self, loader_with_simple_data):
        """Test ORDER BY clause."""
        result = loader_with_simple_data.execute_query(
            "SELECT * FROM simple_Sheet1 ORDER BY value DESC"
        )
        
        assert result.iloc[0]['value'] == 300
        assert result.iloc[2]['value'] == 100
    
    def test_invalid_query_returns_error(self, loader_with_simple_data):
        """Test that invalid queries return error messages."""
        result = loader_with_simple_data.execute_query("SELECT * FROM nonexistent_table")
        
        assert isinstance(result, str)
        assert 'Error' in result or 'error' in result.lower()
    
    def test_empty_result(self, loader_with_simple_data):
        """Test query that returns no results."""
        result = loader_with_simple_data.execute_query(
            "SELECT * FROM simple_Sheet1 WHERE id > 1000"
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestColumnSanitization:
    """Test that column names are properly sanitized."""
    
    def test_special_column_names(self, loader_with_temp_db, special_names_excel_file):
        """Test that special characters in column names are sanitized."""
        loader_with_temp_db.load_path(str(special_names_excel_file))
        tables = loader_with_temp_db.get_tables()
        
        details = loader_with_temp_db.get_table_details()
        columns = details[0]['columns']
        
        # Check that parentheses and special chars are removed
        column_names = [col.split(' (')[0] for col in columns]
        assert all('(' not in col for col in column_names)
        assert all('$' not in col for col in column_names)
