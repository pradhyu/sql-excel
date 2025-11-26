import cmd
import sys
from loader import ExcelLoader
from tabulate import tabulate
import pandas as pd

class ExcelSqlRepl(cmd.Cmd):
    intro = 'Welcome to the Excel-to-SQLite REPL. Type help or ? to list commands.\n'
    prompt = '(sql-excel) '

    def __init__(self):
        super().__init__()
        self.loader = ExcelLoader()

    def do_load(self, arg):
        """
        Load an Excel file or directory of Excel files.
        Usage: load <path>
        """
        if not arg:
            print("Usage: load <path>")
            return
        
        tables = self.loader.load_path(arg)
        if tables:
            print(f"Successfully loaded {len(tables)} tables.")
        else:
            print("No tables loaded.")

    def do_tables(self, arg):
        """
        List all available tables in the database.
        Usage: tables
        """
        tables = self.loader.get_tables()
        if tables:
            print(tabulate([[t] for t in tables], headers=['Table Name'], tablefmt='psql'))
        else:
            print("No tables found.")

    def do_schema(self, arg):
        """
        Show the schema (CREATE TABLE statement) for a specific table.
        Usage: schema <table_name>
        """
        if not arg:
            print("Usage: schema <table_name>")
            return
        
        schema = self.loader.get_schema(arg)
        if schema:
            print(schema)
        else:
            print(f"Table '{arg}' not found.")

    def default(self, line):
        """
        Treat unrecognized commands as SQL queries.
        """
        if line == 'EOF':
            return True
            
        result = self.loader.execute_query(line)
        
        if isinstance(result, pd.DataFrame):
            if not result.empty:
                print(tabulate(result, headers='keys', tablefmt='psql', showindex=False))
            else:
                print("Query returned no results.")
        elif result is None:
            print("Query executed successfully.")
        else:
            print(result)

    def do_exit(self, arg):
        """Exit the REPL."""
        print("Goodbye!")
        return True

    def do_quit(self, arg):
        """Exit the REPL."""
        return self.do_exit(arg)

if __name__ == '__main__':
    try:
        ExcelSqlRepl().cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
