import sys
import argparse
import pandas as pd
from loader import ExcelLoader
from rich.console import Console
from rich.table import Table
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

# Initialize Rich Console
console = Console()

class ExcelSqlRepl:
    def __init__(self, auto_load_path=None):
        self.loader = ExcelLoader()
        self.session = PromptSession(history=InMemoryHistory())
        self.auto_load_path = auto_load_path
        
        # Custom style for the prompt
        self.style = Style.from_dict({
            'prompt': 'ansicyan bold',
            'continuation': 'ansigray',
        })

    def print_welcome(self):
        console.print("[bold green]Welcome to the Excel-to-SQLite REPL.[/bold green]")
        console.print("Type [bold cyan]help[/bold cyan] or [bold cyan]?[/bold cyan] to list commands.")
        console.print("Ends SQL queries with a semicolon ([bold yellow];[/bold yellow]).\n")
        
        # Auto-load data if path provided and no data exists
        if self.auto_load_path:
            if self.loader.has_data():
                table_count = len(self.loader.get_tables())
                console.print(f"[dim]Using cached data ({table_count} tables). Use [bold]refresh[/bold] to reload.[/dim]\n")
            else:
                console.print(f"[dim]Auto-loading data from: {self.auto_load_path}[/dim]")
                self.do_load(self.auto_load_path)
                console.print()

    def do_load(self, arg):
        """Load an Excel file or directory."""
        if not arg:
            console.print("[bold red]Usage:[/bold red] load <path>")
            return
        
        with console.status("[bold green]Loading files...[/bold green]"):
            tables = self.loader.load_path(arg)
        
        if tables:
            console.print(f"[bold green]Successfully loaded {len(tables)} tables.[/bold green]")
        else:
            console.print("[yellow]No tables loaded.[/yellow]")

    def do_tables(self, arg):
        """List all available tables with metadata."""
        details = self.loader.get_table_details()
        if details:
            table = Table(title="Loaded Tables", box=box.ROUNDED)
            table.add_column("Table Name", style="cyan", no_wrap=True)
            table.add_column("Rows", justify="right", style="magenta")
            table.add_column("Cols", justify="right", style="magenta")
            table.add_column("Columns", style="green")

            for d in details:
                # Show all columns without truncation, with color-coded types
                colored_cols = []
                for col in d['columns']:
                    # Apply color coding to types
                    if '(INTEGER)' in col:
                        col = col.replace('(INTEGER)', '[blue](INTEGER)[/blue]')
                    elif '(TEXT)' in col:
                        col = col.replace('(TEXT)', '[yellow](TEXT)[/yellow]')
                    elif '(REAL)' in col:
                        col = col.replace('(REAL)', '[magenta](REAL)[/magenta]')
                    elif '(TIMESTAMP)' in col:
                        col = col.replace('(TIMESTAMP)', '[cyan](TIMESTAMP)[/cyan]')
                    elif '(BLOB)' in col:
                        col = col.replace('(BLOB)', '[red](BLOB)[/red]')
                    colored_cols.append(col)
                
                cols_str = ", ".join(colored_cols)
                
                table.add_row(
                    d['name'], 
                    str(d['rows']), 
                    str(d['cols']), 
                    cols_str
                )
            console.print(table)
        else:
            console.print("[yellow]No tables found.[/yellow]")

    def do_schema(self, arg):
        """Show the schema for a table."""
        if not arg:
            console.print("[bold red]Usage:[/bold red] schema <table_name>")
            return
        
        schema = self.loader.get_schema(arg)
        if schema:
            console.print(f"[dim]{schema}[/dim]")
        else:
            console.print(f"[red]Table '{arg}' not found.[/red]")
    
    def do_refresh(self, arg):
        """Refresh/reload data from the auto-load path."""
        if not self.auto_load_path:
            console.print("[yellow]No auto-load path specified. Use: load <path>[/yellow]")
            return
        
        console.print("[yellow]Clearing cached data...[/yellow]")
        self.loader.clear_data()
        console.print(f"[green]Reloading data from: {self.auto_load_path}[/green]")
        self.do_load(self.auto_load_path)

    def do_help(self, arg):
        """List available commands."""
        console.print("\n[bold]Available Commands:[/bold]")
        console.print("  [cyan]load <path>[/cyan]   - Load Excel file or directory")
        console.print("  [cyan]tables[/cyan]        - List loaded tables with details")
        console.print("  [cyan]schema <table>[/cyan] - Show CREATE TABLE statement")
        console.print("  [cyan]refresh[/cyan]       - Clear cache and reload data")
        console.print("  [cyan]exit / quit[/cyan]   - Exit the REPL")
        console.print("  [cyan]<sql query>[/cyan]  - Execute SQL query (end with ;)\n")

    def execute_sql(self, query):
        """Execute SQL query and print results using Rich."""
        result = self.loader.execute_query(query)
        
        if isinstance(result, pd.DataFrame):
            if not result.empty:
                # Convert DataFrame to Rich Table
                table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
                
                # Add columns
                for col in result.columns:
                    table.add_column(str(col))
                
                # Add rows
                for _, row in result.iterrows():
                    table.add_row(*[str(val) for val in row])
                
                console.print(table)
            else:
                console.print("[yellow]Query returned no results.[/yellow]")
        elif result is None:
            console.print("[green]Query executed successfully.[/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {result}")
    
    def execute_query_and_exit(self, query):
        """Execute a query and exit (for non-interactive mode)."""
        # Load data if auto_load_path is provided and no data exists
        if self.auto_load_path and not self.loader.has_data():
            console.print(f"[dim]Loading data from: {self.auto_load_path}[/dim]")
            self.do_load(self.auto_load_path)
            console.print()
        
        # Execute the query
        self.execute_sql(query)

    def run(self):
        self.print_welcome()
        
        while True:
            try:
                # Prompt for input
                text = self.session.prompt(
                    HTML('<prompt>(sql-excel)</prompt> '),
                    style=self.style,
                    multiline=True,
                    prompt_continuation=HTML('<continuation>   > </continuation>'),
                    # Custom validator to determine when to submit
                    # We submit if the text ends with ';' or is a known single-line command
                )
                
                text = text.strip()
                if not text:
                    continue

                # Check for commands
                parts = text.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd in ['exit', 'quit']:
                    console.print("[bold green]Goodbye![/bold green]")
                    break
                elif cmd == 'load':
                    self.do_load(arg)
                elif cmd == 'tables':
                    self.do_tables(arg)
                elif cmd == 'schema':
                    self.do_schema(arg)
                elif cmd == 'refresh':
                    self.do_refresh(arg)
                elif cmd in ['help', '?']:
                    self.do_help(arg)
                else:
                    # Treat as SQL
                    # If it doesn't end with semicolon, prompt_toolkit multiline=True 
                    # usually requires Meta+Enter to submit. 
                    # However, we can enforce semicolon check if we want strict SQL mode,
                    # but prompt_toolkit's default multiline behavior is user-friendly enough 
                    # (Meta+Enter to submit). 
                    # BUT user specifically asked for "Ends SQL queries with a semicolon".
                    # The prompt_toolkit loop above waits for submit. 
                    # If we want Enter to submit for commands but NOT for SQL unless semicolon...
                    # That requires a custom key binding or validator.
                    # For simplicity and robustness with the "multiline=True" flag:
                    # Users usually press Esc+Enter or Meta+Enter to submit in multiline mode.
                    # To make it behave like "Enter adds newline unless semicolon", we need a key binding.
                    # Let's stick to standard prompt_toolkit multiline behavior for now 
                    # but check for semicolon before executing SQL.
                    
                    self.execute_sql(text)

            except KeyboardInterrupt:
                continue
            except EOFError:
                break

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Excel to SQLite REPL')
    parser.add_argument('data_folder', nargs='?', help='Path to folder containing Excel files to auto-load')
    parser.add_argument('--db', help='Path to SQLite database file (default: ~/.sql_excel_data.db)')
    parser.add_argument('--query', '-q', help='Execute a SQL query and exit (non-interactive mode)')
    parser.add_argument('--source', '-s', default='test_data', help='Default data source folder (default: test_data)')
    args = parser.parse_args()
    
    # Determine which data folder to use
    # Priority: positional argument > --source flag
    data_path = args.data_folder if args.data_folder else args.source
    
    # Create REPL instance
    repl = ExcelSqlRepl(auto_load_path=data_path)
    
    # If query is provided, execute it and exit
    if args.query:
        repl.execute_query_and_exit(args.query)
        sys.exit(0)
    
    # To enable "Enter to submit if ends with ;", we need a bit more config.
    # But for now, let's use a simpler approach: 
    # We will use a custom accept_handler or just rely on the user knowing 
    # how to submit in multiline mode (Esc+Enter) OR we can use a loop 
    # that accumulates lines like the previous implementation but with prompt_toolkit history.
    # ACTUALLY, the best way to satisfy "multi line quries should be one entry in history"
    # is to use prompt_toolkit's prompt() which returns the whole block.
    # To make "Enter" smart (submit if ';', else newline), we use a key binding.
    
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.filters import Condition

    kb = KeyBindings()

    @kb.add('enter')
    def _(event):
        buff = event.current_buffer
        text = buff.text.strip()
        
        # Commands that are single line
        is_command = text.split()[0].lower() in ['load', 'tables', 'schema', 'refresh', 'exit', 'quit', 'help', '?']
        
        # SQL ending with semicolon
        is_sql_complete = text.endswith(';')
        
        if is_command or is_sql_complete:
            buff.validate_and_handle()
        else:
            buff.insert_text('\n')

    # Enter interactive REPL mode
    repl.session.app.key_bindings = kb # Apply bindings to the session
    repl.run()
