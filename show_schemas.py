#!/usr/bin/env python3
"""Script to display all table schemas with column details."""

import sqlite3
from rich.console import Console
from rich.table import Table
from pathlib import Path

def show_all_schemas():
    """Display schema information for all tables."""
    console = Console()
    
    # Connect to the database
    db_path = Path.home() / '.sql_excel_data.db'
    if not db_path.exists():
        console.print("[red]Database not found. Please load data first.[/red]")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    if not tables:
        console.print("[yellow]No tables found in database.[/yellow]")
        return
    
    console.print(f"\n[bold cyan]Found {len(tables)} table(s)[/bold cyan]\n")
    
    # For each table, show its schema
    for (table_name,) in tables:
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Create a rich table for display
        rich_table = Table(title=f"[bold]{table_name}[/bold] ({row_count:,} rows)")
        rich_table.add_column("Column #", style="cyan", no_wrap=True)
        rich_table.add_column("Column Name", style="green")
        rich_table.add_column("Data Type", style="yellow")
        rich_table.add_column("Not Null", style="magenta")
        rich_table.add_column("Default", style="blue")
        rich_table.add_column("Primary Key", style="red")
        
        for col in columns:
            cid, name, dtype, notnull, default, pk = col
            rich_table.add_row(
                str(cid),
                name,
                dtype or "NULL",
                "✓" if notnull else "",
                str(default) if default is not None else "",
                "✓" if pk else ""
            )
        
        console.print(rich_table)
        console.print()
    
    conn.close()

if __name__ == "__main__":
    show_all_schemas()
