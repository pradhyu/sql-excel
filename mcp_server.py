from fastmcp import FastMCP
from loader import ExcelLoader
import pandas as pd
import json

# Initialize FastMCP
mcp = FastMCP("sql-excel")

# Initialize ExcelLoader
# We use the default persistent DB path
loader = ExcelLoader()

@mcp.tool()
def read_query(query: str) -> str:
    """
    Execute a SQL query against the loaded Excel data.
    Returns the result as a JSON string.
    """
    result = loader.execute_query(query)
    if isinstance(result, pd.DataFrame):
        return result.to_json(orient='records')
    elif result is None:
        return "Query executed successfully (no output)."
    else:
        return str(result)

@mcp.tool()
def list_tables() -> str:
    """
    List all available tables in the database.
    Returns a JSON string list of table names.
    """
    tables = loader.get_tables()
    return json.dumps(tables)

@mcp.tool()
def get_table_schema(table_name: str) -> str:
    """
    Get the CREATE TABLE schema for a specific table.
    """
    schema = loader.get_schema(table_name)
    if schema:
        return schema
    else:
        return f"Table '{table_name}' not found."

@mcp.tool()
def load_data(path: str) -> str:
    """
    Load Excel files from a directory or file path.
    Returns a list of loaded table names.
    """
    tables = loader.load_path(path)
    return json.dumps(tables)

@mcp.resource("schema://{table_name}")
def get_schema_resource(table_name: str) -> str:
    """
    Get the schema for a table as a resource.
    """
    schema = loader.get_schema(table_name)
    if schema:
        return schema
    else:
        return "Table not found."

if __name__ == "__main__":
    mcp.run()
