# Setup Instructions for SQLite MCP Server

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Node.js and npm (for MCP Inspector)

## Installation

1. Navigate to the implementation directory:
```bash
cd implementation
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

This will create a `lab_database.db` file with sample data for students, courses, and enrollments.

## Project Structure

```
implementation/
  db.py              # SQLite adapter with validation
  init_db.py         # Database initialization script
  mcp_server.py      # FastMCP server implementation
  verify_server.py   # Verification and testing script
  start_inspector.sh # Helper script to run MCP Inspector
  requirements.txt   # Python dependencies
  lab_database.db    # SQLite database (created after init)
  .venv/             # Virtual environment
  tests/
    (test files can be added here)
```

## Tool Descriptions

### search

Search for records in a database table with optional filters, ordering, and pagination.

**Parameters:**
- `table` (required): Name of the table to search (e.g., 'students', 'courses', 'enrollments')
- `filters` (optional): Dictionary of filter conditions. Format: `{"column": {"operator": "eq", "value": ...}}`
  - Supported operators: `eq`, `ne`, `gt`, `lt`, `ge`, `le`, `like`, `in`
  - Example: `{"cohort": {"operator": "eq", "value": "A1"}}`
- `columns` (optional): List of column names to return (None for all columns)
- `limit` (optional): Maximum number of rows to return (default: 20)
- `offset` (optional): Number of rows to skip (default: 0)
- `order_by` (optional): Column name to sort by
- `descending` (optional): Sort in descending order if True (default: False)

**Returns:** JSON with search results including rows and metadata

### insert

Insert a new record into a database table.

**Parameters:**
- `table` (required): Name of the table to insert into
- `values` (required): Dictionary of column-value pairs for the new record
  - Example: `{"name": "John Doe", "email": "john@example.com", "cohort": "A1", "score": 90.0}`

**Returns:** JSON with inserted payload including generated ID

### aggregate

Perform aggregate calculations on table data.

**Parameters:**
- `table` (required): Name of the table to aggregate
- `metric` (required): Aggregate function to apply. Supported: `count`, `avg`, `sum`, `min`, `max`
- `column` (optional): Column to aggregate (required for most metrics, optional for count)
- `filters` (optional): Dictionary of filter conditions (same format as search tool)
- `group_by` (optional): Column name to group results by

**Returns:** JSON with aggregate results

**Examples:**
- Count all students: `aggregate("students", "count")`
- Average score by cohort: `aggregate("students", "avg", "score", group_by="cohort")`
- Count enrollments per course: `aggregate("enrollments", "count", group_by="course_id")`

## MCP Resources

### schema://database

Get the complete database schema including all tables and their columns.

**Returns:** JSON describing the full database schema

### schema://table/{table_name}

Get the schema for a specific table.

**Parameters:**
- `table_name`: Name of the table (e.g., 'students', 'courses', 'enrollments')

**Returns:** JSON describing the table's schema

## Testing Steps

### 1. Run Verification Script

```bash
python verify_server.py
```

This will test:
- Database adapter functionality
- MCP tool imports and signatures
- MCP resource functionality
- Error handling for invalid requests

### 2. Test with MCP Inspector

Run the helper script:
```bash
./start_inspector.sh
```

Or manually:
```bash
mkdir -p .npm-cache
NPM_CONFIG_CACHE="$PWD/.npm-cache" npx -y @modelcontextprotocol/inspector .venv/bin/python mcp_server.py
```

In the Inspector UI:
1. Verify that tools appear: `search`, `insert`, `aggregate`
2. Verify that resources appear: `schema://database`, `schema://table/{table_name}`
3. Test valid tool calls:
   - Search: `{"table": "students", "filters": {"cohort": {"operator": "eq", "value": "A1"}}}`
   - Insert: `{"table": "students", "values": {"name": "Test", "email": "test@test.com", "cohort": "C1", "score": 80.0}}`
   - Aggregate: `{"table": "students", "metric": "avg", "column": "score", "group_by": "cohort"}`
4. Test invalid requests to verify error handling:
   - Search with invalid table: `{"table": "invalid_table"}`
   - Insert with empty values: `{"table": "students", "values": {}}`
   - Aggregate with invalid metric: `{"table": "students", "metric": "invalid"}`
5. Test resources:
   - Read `schema://database`
   - Read `schema://table/students`

## Client Configuration Examples

### Claude Code

Create or edit `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "sqlite-lab": {
      "type": "stdio",
      "command": "/Users/vuanh4569/Coding/VinUniHomeWork/2A202600571-HaVuAnh-Day26/implementation/.venv/bin/python",
      "args": ["/Users/vuanh4569/Coding/VinUniHomeWork/2A202600571-HaVuAnh-Day26/implementation/mcp_server.py"],
      "env": {}
    }
  }
}
```

Use absolute paths to avoid `spawn ... ENOENT` issues. Claude Code supports `@sqlite-lab:schema://database` references.

### Gemini CLI

```bash
gemini mcp add sqlite-lab /Users/vuanh4569/Coding/VinUniHomeWork/2A202600571-HaVuAnh-Day26/implementation/.venv/bin/python /Users/vuanh4569/Coding/VinUniHomeWork/2A202600571-HaVuAnh-Day26/implementation/mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
```

Verify the server appears as `Connected`. Test with:
```bash
gemini --allowed-mcp-server-names sqlite-lab --yolo -p "Use the sqlite-lab MCP server and show me the top 2 students by score."
```

### Codex

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.sqlite_lab]
command = "/Users/vuanh4569/Coding/VinUniHomeWork/2A202600571-HaVuAnh-Day26/implementation/.venv/bin/python"
args = ["/Users/vuanh4569/Coding/VinUniHomeWork/2A202600571-HaVuAnh-Day26/implementation/mcp_server.py"]
```

Add project instructions in `AGENTS.md`:
```md
Use the `sqlite_lab` MCP server whenever the task needs database schema context or SQL-backed record lookup.
```

## Data Model

The database contains three tables:

### students
- `id` (INTEGER PRIMARY KEY)
- `name` (TEXT NOT NULL)
- `email` (TEXT NOT NULL UNIQUE)
- `cohort` (TEXT NOT NULL)
- `score` (REAL)

### courses
- `id` (INTEGER PRIMARY KEY)
- `code` (TEXT NOT NULL UNIQUE)
- `title` (TEXT NOT NULL)
- `credits` (INTEGER NOT NULL)

### enrollments
- `id` (INTEGER PRIMARY KEY)
- `student_id` (INTEGER NOT NULL)
- `course_id` (INTEGER NOT NULL)
- `grade` (REAL)
- Foreign keys to students and courses tables

## References

- FastMCP quickstart: https://gofastmcp.com/v2/getting-started/quickstart
- FastMCP resources: https://gofastmcp.com/v2/servers/resources
- MCP Inspector: https://modelcontextprotocol.io/docs/tools/inspector
- Claude Code MCP: https://code.claude.com/docs/en/mcp
- OpenAI Codex MCP: https://developers.openai.com/learn/docs-mcp
- Gemini CLI MCP: https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md
