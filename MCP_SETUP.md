# MCP Server Setup

This project includes an MCP (Model Context Protocol) server that exposes the Excel-to-SQLite functionality to AI assistants like Claude Desktop, GitHub Copilot, or Antigravity.

## What is MCP?

MCP is an open standard that allows AI assistants to interact with external tools and data sources. This server exposes the Excel loading and SQL querying capabilities via stdio-based communication.

## Available Tools

The MCP server provides the following tools:

1. **load_excel(path)** - Load Excel file(s) from a path into the SQLite database
2. **execute_sql(query)** - Execute SQL queries against loaded data
3. **list_tables()** - List all tables with metadata (rows, columns, types)
4. **get_schema(table_name)** - Get the CREATE TABLE statement for a table

## Available Resources

- **tables://list** - Get a list of all loaded table names

## Configuration

### For Antigravity

There are two ways to configure the MCP server for Antigravity:

#### Option 1: Via Antigravity UI (Recommended)

1. Open Antigravity
2. Press `Ctrl+Cmd+B` to open the Agent Side Panel (if not visible)
3. Click the "Additional options" menu button (three dots `...`)
4. Select "MCP Servers"
5. Click "Add Custom MCP" or "New MCP Server"
6. Fill in the details:
   - **Name:** `excel-sqlite`
   - **Type:** `local` or `stdio`
   - **Command:** `/Users/pkshrestha/git/sql-excel/.venv/bin/python`
   - **Args:** `/Users/pkshrestha/git/sql-excel/mcp_server.py`
7. Click "Refresh" to activate the server

#### Option 2: Manual Configuration

Add this to `~/.gemini/antigravity/mcp_config.json`:

```json
{
  "mcpServers": {
    "excel-sqlite": {
      "command": "/Users/pkshrestha/git/sql-excel/.venv/bin/python",
      "args": [
        "/Users/pkshrestha/git/sql-excel/mcp_server.py"
      ]
    }
  }
}
```

After adding the configuration, restart Antigravity or refresh the MCP servers list.

### For Claude Desktop

Add this to your Claude Desktop MCP configuration file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "excel-sqlite": {
      "command": "/Users/pkshrestha/git/sql-excel/.venv/bin/python",
      "args": [
        "/Users/pkshrestha/git/sql-excel/mcp_server.py"
      ]
    }
  }
}
```

### For Other MCP Clients

Use the provided `mcp_config.json` or configure your client to run:

```bash
/Users/pkshrestha/git/sql-excel/.venv/bin/python /Users/pkshrestha/git/sql-excel/mcp_server.py
```

## Testing the MCP Server

You can test the server directly using the MCP inspector:

```bash
npx @modelcontextprotocol/inspector uv --directory /Users/pkshrestha/git/sql-excel run mcp_server.py
```

## Usage Example

Once configured, you can ask your AI assistant:

- "Load the Excel files from /path/to/data"
- "Show me all the tables"
- "Execute this SQL query: SELECT * FROM users_Sheet1"
- "What's the schema for the orders table?"

The AI will use the MCP tools to interact with your Excel data.
