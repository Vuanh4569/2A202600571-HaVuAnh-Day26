from fastmcp import FastMCP
import json
import os
from db import SQLiteAdapter, ValidationError

# Create the server object
mcp = FastMCP("SQLite Lab MCP Server")

# Initialize database adapter
DB_PATH = os.path.join(os.path.dirname(__file__), "lab_database.db")

# Check if database exists, if not create it
if not os.path.exists(DB_PATH):
    from init_db import create_database
    create_database(DB_PATH)

adapter = SQLiteAdapter(DB_PATH)


@mcp.tool(name="search")
def search(
    table: str,
    filters: dict = None,
    columns: list = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str = None,
    descending: bool = False
) -> str:
    """
    Search for records in a database table with optional filters, ordering, and pagination.
    
    Args:
        table: Name of the table to search (e.g., 'students', 'courses', 'enrollments')
        filters: Dictionary of filter conditions. Format: {"column": {"operator": "eq", "value": ...}}
                 Supported operators: eq, ne, gt, lt, ge, le, like, in
                 Example: {"cohort": {"operator": "eq", "value": "A1"}}
        columns: List of column names to return (None for all columns)
        limit: Maximum number of rows to return (default: 20)
        offset: Number of rows to skip (default: 0)
        order_by: Column name to sort by
        descending: Sort in descending order if True (default: False)
    
    Returns:
        JSON string with search results including rows and metadata
    """
    try:
        result = adapter.search(
            table=table,
            columns=columns,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending
        )
        return json.dumps(result, indent=2, default=str)
    except ValidationError as e:
        return json.dumps({"error": str(e), "type": "validation_error"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": "server_error"}, indent=2)


@mcp.tool(name="insert")
def insert(table: str, values: dict) -> str:
    """
    Insert a new record into a database table.
    
    Args:
        table: Name of the table to insert into (e.g., 'students', 'courses', 'enrollments')
        values: Dictionary of column-value pairs for the new record
                Example: {"name": "John Doe", "email": "john@example.com", "cohort": "A1", "score": 90.0}
    
    Returns:
        JSON string with inserted payload including generated ID
    """
    try:
        result = adapter.insert(table=table, values=values)
        return json.dumps(result, indent=2, default=str)
    except ValidationError as e:
        return json.dumps({"error": str(e), "type": "validation_error"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": "server_error"}, indent=2)


@mcp.tool(name="aggregate")
def aggregate(
    table: str,
    metric: str,
    column: str = None,
    filters: dict = None,
    group_by: str = None
) -> str:
    """
    Perform aggregate calculations on table data.
    
    Args:
        table: Name of the table to aggregate (e.g., 'students', 'courses', 'enrollments')
        metric: Aggregate function to apply. Supported: count, avg, sum, min, max
        column: Column to aggregate (required for most metrics, optional for count)
        filters: Optional dictionary of filter conditions (same format as search tool)
        group_by: Optional column name to group results by
    
    Returns:
        JSON string with aggregate results
    
    Examples:
        - Count all students: aggregate("students", "count")
        - Average score by cohort: aggregate("students", "avg", "score", group_by="cohort")
        - Count enrollments per course: aggregate("enrollments", "count", group_by="course_id")
    """
    try:
        result = adapter.aggregate(
            table=table,
            metric=metric,
            column=column,
            filters=filters,
            group_by=group_by
        )
        return json.dumps(result, indent=2, default=str)
    except ValidationError as e:
        return json.dumps({"error": str(e), "type": "validation_error"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": "server_error"}, indent=2)


@mcp.resource("schema://database")
def database_schema() -> str:
    """
    Get the complete database schema including all tables and their columns.
    
    Returns:
        JSON string describing the full database schema
    """
    try:
        tables = adapter.list_tables()
        schema = {}
        
        for table in tables:
            table_info = adapter.get_table_schema(table)
            schema[table] = table_info
        
        return json.dumps({
            "database": DB_PATH,
            "tables": schema
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource("schema://table/{table_name}")
def table_schema(table_name: str) -> str:
    """
    Get the schema for a specific table.
    
    Args:
        table_name: Name of the table (e.g., 'students', 'courses', 'enrollments')
    
    Returns:
        JSON string describing the table's schema
    """
    try:
        schema = adapter.get_table_schema(table_name)
        return json.dumps(schema, indent=2, default=str)
    except ValidationError as e:
        return json.dumps({"error": str(e), "type": "validation_error"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": "server_error"}, indent=2)


if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run()
