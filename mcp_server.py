#!/usr/bin/env python3
"""
MCP Server for Excel to SQLite
Exposes Excel loading and SQL querying capabilities via Model Context Protocol
"""

from fastmcp import FastMCP
from loader import ExcelLoader
import pandas as pd
from typing import Optional

# Initialize MCP server
mcp = FastMCP("excel-sqlite")

# Global loader instance (in-memory database)
loader = ExcelLoader()

@mcp.tool()
def load_excel(path: str) -> str:
    """
    Load Excel file(s) from a path into the SQLite database.
    
    Args:
        path: File path or directory path containing Excel files
        
    Returns:
        Status message with loaded table names
    """
    tables = loader.load_path(path)
    if tables:
        return f"Successfully loaded {len(tables)} tables: {', '.join(tables)}"
    else:
        return "No tables loaded. Check if the path contains valid Excel files."

@mcp.tool()
def execute_sql(query: str) -> str:
    """
    Execute a SQL query against the loaded Excel data.
    
    Args:
        query: SQL query to execute (SELECT, INSERT, UPDATE, DELETE, etc.)
        
    Returns:
        Query results as formatted text or error message
    """
    result = loader.execute_query(query)
    
    if isinstance(result, pd.DataFrame):
        if not result.empty:
            return result.to_string(index=False)
        else:
            return "Query returned no results."
    elif result is None:
        return "Query executed successfully."
    else:
        return str(result)

@mcp.tool()
def list_tables() -> str:
    """
    List all available tables in the database with metadata.
    
    Returns:
        Formatted list of tables with row counts, column counts, and column names with types
    """
    details = loader.get_table_details()
    if not details:
        return "No tables found. Load Excel files first using load_excel()."
    
    output = []
    for d in details:
        cols_str = ", ".join(d['columns'])
        output.append(f"Table: {d['name']}")
        output.append(f"  Rows: {d['rows']}")
        output.append(f"  Columns ({d['cols']}): {cols_str}")
        output.append("")
    
    return "\n".join(output)

@mcp.tool()
def get_schema(table_name: str) -> str:
    """
    Get the CREATE TABLE statement for a specific table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        CREATE TABLE SQL statement or error message
    """
    schema = loader.get_schema(table_name)
    if schema:
        return schema
    else:
        return f"Table '{table_name}' not found."

@mcp.resource("tables://list")
def get_tables_resource() -> str:
    """
    Resource endpoint to get list of all tables.
    """
    tables = loader.get_tables()
    if tables:
        return "\n".join(tables)
    else:
        return "No tables loaded."

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
