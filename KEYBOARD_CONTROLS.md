# SQL-Excel REPL - Keyboard Controls Reference

## Working Controls (Verified)

### Query Execution
- **`;` + Enter** - Submit SQL query (most reliable)
- **Meta+Enter** - Force submit query
  - On Linux/Mac: `Alt+Enter` or `Esc` then `Enter`
  - This is the standard prompt_toolkit multiline submit

### Autocomplete
- **Tab** - Show autocomplete suggestions
- **Esc** - Dismiss autocomplete menu

### Navigation & Exit
- **Ctrl+D** - Exit REPL (EOF signal)
- **`exit`** or **`quit`** - Exit via command

## Multi-Line Mode Behavior

When you type a query without `;`:
1. Press **Enter** → Adds new line (continuation)
2. Keep typing your query across multiple lines
3. End with **`;`** and press **Enter** to execute
4. OR press **Meta+Enter** (Alt+Enter) to force submit

## Notes

- **Ctrl+C behavior**: Varies by terminal - may not work reliably in multiline mode
- **Best practice**: Always end SQL queries with `;` for predictable behavior
- **Commands** (load, tables, etc.): Automatically submit on Enter (no `;` needed)
