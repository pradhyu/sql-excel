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
from prompt_toolkit.completion import Completer, Completion

# Initialize Rich Console
console = Console()

import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings

# Initialize Rich Console
console = Console()

class AdvancedSQLCompleter(Completer):
    def __init__(self, keywords, tables, columns, table_to_columns, column_to_tables):
        self.keywords = keywords
        self.tables = tables
        self.columns = columns
        self.table_to_columns = table_to_columns
        self.column_to_tables = column_to_tables

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        text_before_cursor = document.text_before_cursor
        
        # Parse the SQL up to the cursor
        parsed = sqlparse.parse(text_before_cursor)
        if not parsed:
            return
            
        stmt = parsed[0]
        tokens = list(stmt.flatten())
        
        # Filter out whitespace and the word being typed
        meaningful_tokens = [t for t in tokens if not t.is_whitespace]
        if word_before_cursor:
             if meaningful_tokens and meaningful_tokens[-1].value.upper().startswith(word_before_cursor.upper()):
                 meaningful_tokens.pop()
        
        last_keyword = ""
        if meaningful_tokens:
            for token in reversed(meaningful_tokens):
                if token.ttype in (Keyword, Keyword.DML):
                    last_keyword = token.value.upper()
                    break
                    
        # Extract context information
        present_tables = []
        present_columns = []
        
        # Scan tokens for known tables and columns
        # This is a simple scan, not structure-aware, but effective for this purpose
        for token in meaningful_tokens:
            val = token.value
            if val in self.tables:
                present_tables.append(val)
            # Check for columns (splitting by space to handle types if needed, though usually just name)
            # Our self.columns list has clean names
            if val in self.columns:
                present_columns.append(val)
        
        # Alias detection (simplified)
        aliases = {}
        from_seen = False
        for token in tokens:
            if token.ttype in (Keyword, Keyword.DML) and token.value.upper() in ('FROM', 'JOIN'):
                from_seen = True
                continue
            if from_seen:
                if isinstance(token, Identifier):
                    name = token.get_real_name()
                    alias = token.get_alias()
                    if name and alias:
                        aliases[alias] = name
                elif token.ttype in (Keyword, Keyword.DML) and token.value.upper() not in ('AS',):
                    from_seen = False

        # Context-based suggestions
        suggestions = []
        
        if last_keyword in ['FROM', 'JOIN', 'UPDATE', 'INTO']:
            # Suggest tables
            # Filter tables based on present_columns if any
            if present_columns:
                # Find tables that contain ALL present columns (or at least one? let's say at least one for now)
                # Better: tables that contain ANY of the columns
                candidate_tables = set()
                for col in present_columns:
                    if col in self.column_to_tables:
                        candidate_tables.update(self.column_to_tables[col])
                
                if candidate_tables:
                    suggestions.extend(list(candidate_tables))
                else:
                    suggestions.extend(self.tables)
            else:
                suggestions.extend(self.tables)
                
        elif last_keyword in ['SELECT', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'ON', 'SET', 
                              'AND', 'OR', 'NOT', 'MIN', 'MAX', 'AVG', 'SUM', 'COUNT', 
                              'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE']:
            # Suggest columns
            # Filter columns based on present_tables if any
            if present_tables:
                candidate_columns = set()
                for table in present_tables:
                    if table in self.table_to_columns:
                        candidate_columns.update(self.table_to_columns[table])
                suggestions.extend(list(candidate_columns))
            else:
                suggestions.extend(self.columns)
            
            # Also suggest tables and keywords
            suggestions.extend(self.tables)
            suggestions.extend(self.keywords)
            suggestions.extend(aliases.keys())
        else:
            # Default
            suggestions.extend(self.keywords)
            suggestions.extend(self.tables)
            
        # Filter and yield completions
        seen = set()
        for suggestion in suggestions:
            if suggestion in seen:
                continue
            seen.add(suggestion)
            
            if suggestion.lower().startswith(word_before_cursor.lower()):
                # Check if this is a column to add table context
                display_text = suggestion
                if suggestion in self.column_to_tables:
                    tables = self.column_to_tables[suggestion]
                    # If we have filtered tables (present_tables), show those
                    # Otherwise show all tables this column belongs to
                    relevant_tables = [t for t in tables if t in present_tables] if present_tables else tables
                    
                    if relevant_tables:
                        # Show up to 2 tables to avoid clutter
                        table_str = ", ".join(relevant_tables[:2])
                        if len(relevant_tables) > 2:
                            table_str += "..."
                        display_text = f"{suggestion} [{table_str}]"
                
                yield Completion(suggestion, start_position=-len(word_before_cursor), display=display_text)

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
        
        # SQL Keywords for autocompletion
        self.sql_keywords = [
            'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'LIMIT', 
            'JOIN', 'INNER', 'LEFT', 'RIGHT', 'ON', 'AS', 'DISTINCT', 
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CASE', 'WHEN', 'THEN', 
            'ELSE', 'END', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'LIKE', 
            'HAVING', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 
            'TABLE', 'ALTER', 'VALUES', 'SET', 'INTO'
        ]
        self.completer = None
        self.update_completer()
        
        # Setup key bindings for Ctrl+G to exit multi-line
        self.kb = KeyBindings()
        
        @self.kb.add('c-g')
        def _(event):
            """Ctrl+G: Cancel/abort current input"""
            event.app.current_buffer.reset()
            event.app.exit(exception=KeyboardInterrupt, style='class:aborting')

    def update_completer(self):
        """Update the autocompleter with current tables and columns."""
        tables = self.loader.get_tables()
        columns = []
        table_to_columns = {}
        column_to_tables = {}
        
        # Add column names
        details = self.loader.get_table_details()
        if details:
            for d in details:
                t_name = d['name']
                table_to_columns[t_name] = []
                
                for col in d['columns']:
                    col_name = col.split(' (')[0]
                    if col_name not in columns:
                        columns.append(col_name)
                    
                    table_to_columns[t_name].append(col_name)
                    
                    if col_name not in column_to_tables:
                        column_to_tables[col_name] = []
                    column_to_tables[col_name].append(t_name)
                    
        self.completer = AdvancedSQLCompleter(self.sql_keywords, tables, columns, table_to_columns, column_to_tables)

    def print_welcome(self):
        console.print("[bold green]Welcome to the Excel-to-SQLite REPL.[/bold green]")
        console.print("Type [bold cyan]help[/bold cyan] or [bold cyan]?[/bold cyan] to list commands.")
        console.print("Ends SQL queries with a semicolon ([bold yellow];[/bold yellow]).")
        console.print("[dim]Tip: Use Alt+Enter to submit multi-line queries.[/dim]\n")
        
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
            self.update_completer() # Update autocompletion
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
        console.print("  [cyan]<sql query>[/cyan]  - Execute SQL query (end with ;)")
        console.print("  [cyan]<query> > file.csv[/cyan] - Save query results to CSV")
        console.print("\n[dim]Keyboard shortcuts:[/dim]")
        console.print("  [cyan]Tab[/cyan]              - Show autocomplete")
        console.print("  [cyan]; + Enter[/cyan]       - Submit SQL query")
        console.print("  [cyan]Meta+Enter[/cyan]      - Force submit (Alt+Enter or Esc+Enter)")
        console.print("  [cyan]Ctrl+C[/cyan]          - Cancel (in some terminals)")
        console.print("  [cyan]Ctrl+D[/cyan]          - Exit REPL\n")

    def execute_sql(self, text):
        """Execute a SQL query and display results."""
        # Check for CSV export syntax: query > filename.csv
        output_file = None
        if '>' in text:
            parts = text.split('>', 1)
            text = parts[0].strip()
            output_file = parts[1].strip()
            
        result = self.loader.execute_query(text)
        
        if isinstance(result, pd.DataFrame):
            # If output file is specified, save to CSV
            if output_file:
                try:
                    result.to_csv(output_file, index=False)
                    console.print(f"[bold green]✓[/bold green] Saved {len(result)} rows to [cyan]{output_file}[/cyan]")
                    return
                except Exception as e:
                    console.print(f"[bold red]Error saving to CSV:[/bold red] {e}")
                    # Fall through to display the result
            
            # Display results in a table
            if result.empty:
                console.print("[yellow]Query returned no results.[/yellow]")
            else:
                table = Table(box=box.SIMPLE)
                for col in result.columns:
                    table.add_column(str(col), style="cyan")
                
                for _, row in result.iterrows():
                    table.add_row(*[str(val) for val in row])
                
                console.print(table)
                console.print(f"[dim]({len(result)} rows)[/dim]")
        elif result is None:
            console.print("[bold green]Query executed successfully.[/bold green]")
        else:
            console.print(f"[bold red]{result}[/bold red]")
    
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
                # Prompt for input with autocomplete
                text = self.session.prompt(
                    HTML('<prompt>(sql-excel)</prompt> '),
                    style=self.style,
                    multiline=True,
                    prompt_continuation=HTML('<continuation>   > </continuation>'),
                    completer=self.completer,
                    complete_while_typing=False,  # Only show on Tab
                    enable_suspend=False,  # Disable Ctrl+Z
                    key_bindings=self.kb  # Ctrl+G to cancel
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
                    self.execute_sql(text)

            except KeyboardInterrupt:
                # Ctrl+C exits multi-line mode and returns to prompt
                console.print()
                continue
            except EOFError:
                # Ctrl+D exits the REPL
                console.print("\n[bold green]Goodbye![/bold green]")
                break
            except Exception as e:
                # Catch any other errors
                console.print(f"[bold red]Error:[/bold red] {e}")
                continue

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
    
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.filters import Condition, has_focus, DEFAULT_BUFFER, is_done

    kb = KeyBindings()

    @kb.add('enter', filter=has_focus(DEFAULT_BUFFER) & ~is_done)
    def _(event):
        """Custom Enter behavior: submit on ; or command, otherwise newline"""
        buffer = event.current_buffer
        text = buffer.text.strip()
        
        # If empty, just continue (don't submit)
        if not text:
            buffer.insert_text('\n')
            return
        
        # Check if it's a command or ends with semicolon
        is_command = text.split()[0].lower() in ['load', 'tables', 'schema', 'refresh', 'exit', 'quit', 'help', '?']
        ends_with_semicolon = text.rstrip().endswith(';')
        
        if is_command or ends_with_semicolon:
            buffer.validate_and_handle()
        else:
            buffer.insert_text('\n')

    # Enter interactive REPL mode
    repl.session.app.key_bindings = kb # Apply bindings to the session
    repl.run()
