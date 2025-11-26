import os
import sqlite3
import pandas as pd
from utils import sanitize_identifier

class ExcelLoader:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def load_path(self, path):
        """
        Loads Excel files from a directory or a single file.
        Returns a list of loaded table names.
        """
        loaded_tables = []
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        filepath = os.path.join(root, file)
                        tables = self.process_file(filepath)
                        loaded_tables.extend(tables)
        elif os.path.isfile(path) and path.endswith(('.xlsx', '.xls')):
            tables = self.process_file(path)
            loaded_tables.extend(tables)
        else:
            print(f"Invalid path or no Excel files found: {path}")
        
        return loaded_tables

    def process_file(self, filepath):
        """
        Reads an Excel file and converts each sheet to a SQLite table.
        """
        filename = os.path.splitext(os.path.basename(filepath))[0]
        sanitized_filename = sanitize_identifier(filename)
        loaded_tables = []

        try:
            # Read all sheets
            xls = pd.ExcelFile(filepath)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                
                # Sanitize table name
                sanitized_sheet = sanitize_identifier(sheet_name)
                table_name = f"{sanitized_filename}_{sanitized_sheet}"
                
                # Sanitize column names
                df.columns = [sanitize_identifier(col) for col in df.columns]
                
                self.dataframe_to_sqlite(df, table_name)
                loaded_tables.append(table_name)
                print(f"Loaded {filepath} [{sheet_name}] -> Table: {table_name}")
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

        return loaded_tables

    def dataframe_to_sqlite(self, df, table_name):
        """
        Writes a pandas DataFrame to SQLite.
        """
        try:
            df.to_sql(table_name, self.conn, if_exists='replace', index=False)
        except Exception as e:
            print(f"Error writing table {table_name}: {e}")

    def get_tables(self):
        """
        Returns a list of all tables in the database.
        """
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in self.cursor.fetchall()]

    def get_schema(self, table_name):
        """
        Returns the CREATE TABLE statement for a given table.
        """
        self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        result = self.cursor.fetchone()
        return result[0] if result else None

    def execute_query(self, query):
        """
        Executes a raw SQL query and returns the results and headers.
        """
        try:
            # Check if it's a SELECT query to return results
            if query.strip().upper().startswith("SELECT"):
                df = pd.read_sql_query(query, self.conn)
                return df
            else:
                self.cursor.execute(query)
                self.conn.commit()
                return None
        except Exception as e:
            return f"Error: {e}"
