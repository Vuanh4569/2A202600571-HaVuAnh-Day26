import sqlite3
import re
from typing import List, Dict, Any, Optional, Tuple


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""
    pass


class SQLiteAdapter:
    """
    SQLite database adapter for MCP server.
    Handles connection management, schema inspection, and safe query execution.
    """

    # Allowed operators for filters
    ALLOWED_OPERATORS = {"eq", "ne", "gt", "lt", "ge", "le", "like", "in"}
    
    # Allowed aggregate metrics
    ALLOWED_METRICS = {"count", "avg", "sum", "min", "max"}

    def __init__(self, db_path: str):
        """
        Initialize the adapter with a database path.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._conn = None

    def connect(self):
        """
        Open SQLite connection with row_factory enabled for dict-like access.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        """Close the database connection if open."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _validate_identifier(self, identifier: str) -> bool:
        """
        Validate that an identifier is safe (alphanumeric and underscores only).
        
        Args:
            identifier: The identifier to validate
            
        Returns:
            bool: True if safe, raises ValidationError otherwise
        """
        if not identifier or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValidationError(f"Invalid identifier: {identifier}")
        return True

    def list_tables(self) -> List[str]:
        """
        Query sqlite_master and return non-internal tables.
        
        Returns:
            List[str]: List of table names
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table: str) -> Dict[str, Any]:
        """
        Run PRAGMA table_info(table) and normalize result.
        
        Args:
            table: Table name
            
        Returns:
            Dict with table name and column information
        """
        self._validate_identifier(table)
        
        # Check if table exists
        if table not in self.list_tables():
            raise ValidationError(f"Table does not exist: {table}")
        
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "default_value": row[4],
                "primary_key": bool(row[5])
            })
        
        return {
            "table": table,
            "columns": columns
        }

    def _validate_columns(self, table: str, columns: Optional[List[str]]) -> List[str]:
        """
        Validate that column names exist in the table.
        
        Args:
            table: Table name
            columns: List of column names (None means all columns)
            
        Returns:
            List[str]: Validated column list
        """
        schema = self.get_table_schema(table)
        valid_columns = {col["name"] for col in schema["columns"]}
        
        if columns is None:
            return list(valid_columns)
        
        for col in columns:
            self._validate_identifier(col)
            if col not in valid_columns:
                raise ValidationError(f"Column does not exist in table {table}: {col}")
        
        return columns

    def _build_where_clause(self, filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Build WHERE clause from filters with safe parameterized queries.
        
        Args:
            filters: Dictionary of {column: {"operator": "eq", "value": ...}}
            
        Returns:
            Tuple of (WHERE clause SQL, parameter list)
        """
        if not filters:
            return "", []
        
        conditions = []
        params = []
        
        for column, filter_spec in filters.items():
            self._validate_identifier(column)
            
            if not isinstance(filter_spec, dict):
                # Simple equality filter
                operator = "eq"
                value = filter_spec
            else:
                operator = filter_spec.get("operator", "eq")
                value = filter_spec.get("value")
            
            if operator not in self.ALLOWED_OPERATORS:
                raise ValidationError(f"Unsupported operator: {operator}")
            
            op_map = {
                "eq": "=",
                "ne": "!=",
                "gt": ">",
                "lt": "<",
                "ge": ">=",
                "le": "<=",
                "like": "LIKE"
            }
            
            if operator == "in":
                if not isinstance(value, list):
                    raise ValidationError("IN operator requires a list of values")
                placeholders = ",".join(["?" for _ in value])
                conditions.append(f"{column} IN ({placeholders})")
                params.extend(value)
            else:
                sql_op = op_map.get(operator, "=")
                conditions.append(f"{column} {sql_op} ?")
                params.append(value)
        
        return " AND ".join(conditions), params

    def search(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> Dict[str, Any]:
        """
        Execute search query with filters, ordering, and pagination.
        
        Args:
            table: Table name
            columns: List of columns to select (None for all)
            filters: Dictionary of filter conditions
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            order_by: Column to sort by
            descending: Sort direction
            
        Returns:
            Dict with rows and metadata
        """
        self._validate_identifier(table)
        validated_columns = self._validate_columns(table, columns)
        
        # Build SELECT clause
        select_clause = ", ".join(validated_columns) if validated_columns else "*"
        
        # Build WHERE clause
        where_clause, where_params = self._build_where_clause(filters or {})
        
        # Build ORDER BY clause
        order_clause = ""
        if order_by:
            self._validate_identifier(order_by)
            validated_columns = self._validate_columns(table, [order_by])
            direction = "DESC" if descending else "ASC"
            order_clause = f"ORDER BY {order_by} {direction}"
        
        # Build complete query
        query = f"SELECT {select_clause} FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        if order_clause:
            query += f" {order_clause}"
        query += f" LIMIT {limit} OFFSET {offset}"
        
        # Execute query
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, where_params)
        
        rows = [dict(row) for row in cursor.fetchall()]
        
        return {
            "table": table,
            "columns": validated_columns if validated_columns else ["*"],
            "rows": rows,
            "count": len(rows),
            "limit": limit,
            "offset": offset
        }

    def insert(self, table: str, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute parameterized INSERT statement.
        
        Args:
            table: Table name
            values: Dictionary of column-value pairs
            
        Returns:
            Dict with inserted payload and generated ID
        """
        if not values:
            raise ValidationError("Cannot insert empty values")
        
        self._validate_identifier(table)
        
        # Validate columns
        columns = list(values.keys())
        validated_columns = self._validate_columns(table, columns)
        
        # Build INSERT statement
        placeholders = ",".join(["?" for _ in validated_columns])
        columns_clause = ",".join(validated_columns)
        
        query = f"INSERT INTO {table} ({columns_clause}) VALUES ({placeholders})"
        params = [values[col] for col in validated_columns]
        
        # Execute
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        
        # Get inserted row ID
        row_id = cursor.lastrowid
        
        # Return inserted payload
        result = values.copy()
        result["id"] = row_id
        
        return {
            "table": table,
            "inserted": result,
            "row_id": row_id
        }

    def aggregate(
        self,
        table: str,
        metric: str,
        column: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute aggregate query (COUNT, AVG, SUM, MIN, MAX).
        
        Args:
            table: Table name
            metric: Aggregate function (count, avg, sum, min, max)
            column: Column to aggregate (None for count(*))
            filters: Optional filter conditions
            group_by: Optional column to group by
            
        Returns:
            Dict with aggregate results
        """
        metric = metric.lower()
        if metric not in self.ALLOWED_METRICS:
            raise ValidationError(f"Unsupported metric: {metric}")
        
        self._validate_identifier(table)
        
        # Build SELECT clause
        if metric == "count" and column is None:
            select_clause = "COUNT(*) as value"
        else:
            if column:
                self._validate_identifier(column)
                self._validate_columns(table, [column])
            else:
                column = "*"
            select_clause = f"{metric.upper()}({column}) as value"
        
        # Build GROUP BY clause
        group_clause = ""
        select_items = [select_clause]
        if group_by:
            self._validate_identifier(group_by)
            self._validate_columns(table, [group_by])
            group_clause = f"GROUP BY {group_by}"
            select_items = [group_by, select_clause]
        
        # Build WHERE clause
        where_clause, where_params = self._build_where_clause(filters or {})
        
        # Build complete query
        query = f"SELECT {', '.join(select_items)} FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        if group_clause:
            query += f" {group_clause}"
        
        # Execute
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, where_params)
        
        rows = [dict(row) for row in cursor.fetchall()]
        
        return {
            "table": table,
            "metric": metric,
            "column": column,
            "results": rows,
            "count": len(rows)
        }
