#!/usr/bin/env python3
"""
MCP Server (REST Client) for Excel to SQLite
Connects to the running API server to perform operations.
"""

from fastmcp import FastMCP
import httpx
import json

# Initialize MCP server
mcp = FastMCP("excel-sqlite-rest")

API_URL = "http://localhost:8000"

@mcp.tool()
async def load_excel(path: str, force: bool = False) -> str:
    """
    Load Excel file(s) from a path into the database via the API.
    
    Args:
        path: File path or directory path containing Excel files
        force: Force reload even if cached
        
    Returns:
        Status message
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_URL}/load", json={"path": path, "force": force})
            resp.raise_for_status()
            data = resp.json()
            return f"Successfully loaded {data['count']} tables: {', '.join(data['loaded_tables'])}"
        except httpx.HTTPStatusError as e:
            return f"Error loading data: {e.response.text}"
        except Exception as e:
            return f"Connection error: {str(e)}. Is the API server running on {API_URL}?"

@mcp.tool()
async def execute_sql(query: str) -> str:
    """
    Execute a SQL query via the API.
    
    Args:
        query: SQL query to execute
        
    Returns:
        Query results as Markdown table or JSON
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_URL}/query", json={"query": query}, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            
            if data['status'] == 'error':
                return f"Error: {data['message']}"
            
            if data['type'] == 'data':
                rows = data['data']
                if not rows:
                    return "Query returned no results."
                
                # Format as simple text table for LLM readability
                # (We could use tabulate here too if we want pretty printing)
                import pandas as pd
                df = pd.DataFrame(rows)
                return df.to_markdown(index=False)
            else:
                return data['message']
                
        except httpx.HTTPStatusError as e:
            return f"API Error: {e.response.text}"
        except Exception as e:
            return f"Connection error: {str(e)}"

@mcp.tool()
async def list_tables() -> str:
    """
    List all available tables with metadata via the API.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_URL}/tables")
            resp.raise_for_status()
            data = resp.json()
            
            output = []
            for d in data['tables']:
                cols_str = ", ".join(d['columns'])
                output.append(f"Table: {d['name']}")
                output.append(f"  Rows: {d['rows']}")
                output.append(f"  Columns ({d['cols']}): {cols_str}")
                output.append("")
            
            return "\n".join(output)
        except Exception as e:
            return f"Connection error: {str(e)}"

@mcp.tool()
async def get_schema(table_name: str) -> str:
    """
    Get the CREATE TABLE statement for a specific table via the API.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_URL}/schema/{table_name}")
            if resp.status_code == 404:
                return f"Table '{table_name}' not found."
            resp.raise_for_status()
            data = resp.json()
            return data['schema']
        except Exception as e:
            return f"Connection error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
