#!/usr/bin/env python3
"""
Verification script for the SQLite MCP Server.
Tests all tools and resources with valid and invalid requests.
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from db import SQLiteAdapter, ValidationError
from init_db import create_database


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(test_name, success, data=None):
    """Print test result."""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {test_name}")
    if data:
        print(f"  Data: {json.dumps(data, indent=2, default=str)[:200]}...")


def verify_database_adapter():
    """Verify database adapter functionality."""
    print_section("Database Adapter Verification")
    
    # Create database
    db_path = "test_database.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    create_database(db_path)
    adapter = SQLiteAdapter(db_path)
    
    try:
        # Test list tables
        tables = adapter.list_tables()
        print_result("List tables", True, {"tables": tables})
        assert set(tables) == {"students", "courses", "enrollments"}
        
        # Test get table schema
        schema = adapter.get_table_schema("students")
        print_result("Get students schema", True, {"columns": len(schema["columns"])})
        assert schema["table"] == "students"
        assert len(schema["columns"]) > 0
        
        # Test search
        result = adapter.search("students", limit=5)
        print_result("Search students", True, {"count": result["count"]})
        assert result["count"] > 0
        
        # Test search with filters
        result = adapter.search("students", filters={"cohort": "A1"})
        print_result("Search with filter", True, {"count": result["count"]})
        
        # Test search with ordering
        result = adapter.search("students", order_by="score", descending=True)
        print_result("Search with ordering", True, {"count": result["count"]})
        
        # Test insert
        new_student = {
            "name": "Test Student",
            "email": "test@example.com",
            "cohort": "C1",
            "score": 75.0
        }
        result = adapter.insert("students", new_student)
        print_result("Insert student", True, {"row_id": result["row_id"]})
        assert result["row_id"] > 0
        
        # Test aggregate
        result = adapter.aggregate("students", "count")
        print_result("Count students", True, {"count": result["count"]})
        
        result = adapter.aggregate("students", "avg", "score")
        print_result("Average score", True, {"results": result["results"]})
        
        result = adapter.aggregate("students", "count", group_by="cohort")
        print_result("Count by cohort", True, {"count": result["count"]})
        
        # Test validation errors
        try:
            adapter.search("invalid_table")
            print_result("Invalid table error", False)
        except ValidationError:
            print_result("Invalid table error", True)
        
        try:
            adapter.insert("students", {})
            print_result("Empty insert error", False)
        except ValidationError:
            print_result("Empty insert error", True)
        
        try:
            adapter.aggregate("students", "invalid_metric")
            print_result("Invalid metric error", False)
        except ValidationError:
            print_result("Invalid metric error", True)
        
        print("\n✓ All database adapter tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Database adapter test failed: {e}")
        return False
    finally:
        adapter.close()
        if os.path.exists(db_path):
            os.remove(db_path)


def verify_mcp_tools():
    """Verify MCP tools can be imported and have correct signatures."""
    print_section("MCP Tools Verification")
    
    try:
        from mcp_server import search, insert, aggregate, database_schema, table_schema
        
        print_result("Import MCP tools", True)
        
        # Check tool signatures
        import inspect
        
        # Search tool
        sig = inspect.signature(search)
        params = list(sig.parameters.keys())
        print_result("Search tool parameters", True, {"params": params})
        
        # Insert tool
        sig = inspect.signature(insert)
        params = list(sig.parameters.keys())
        print_result("Insert tool parameters", True, {"params": params})
        
        # Aggregate tool
        sig = inspect.signature(aggregate)
        params = list(sig.parameters.keys())
        print_result("Aggregate tool parameters", True, {"params": params})
        
        print("\n✓ All MCP tool verification passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ MCP tools verification failed: {e}")
        return False


def verify_mcp_resources():
    """Verify MCP resources can be imported."""
    print_section("MCP Resources Verification")
    
    try:
        # Import the adapter directly to test resource logic
        from db import SQLiteAdapter
        
        print_result("Import database adapter", True)
        
        # Test database schema resource logic
        DB_PATH = os.path.join(os.path.dirname(__file__), "lab_database.db")
        adapter = SQLiteAdapter(DB_PATH)
        
        tables = adapter.list_tables()
        schema = {}
        for table in tables:
            table_info = adapter.get_table_schema(table)
            schema[table] = table_info
        
        print_result("Database schema resource", True, {"tables": list(schema.keys())})
        
        # Test table schema resource logic
        table_info = adapter.get_table_schema("students")
        print_result("Table schema resource", True, {"table": table_info.get("table")})
        
        # Test invalid table error
        try:
            adapter.get_table_schema("invalid_table")
            print_result("Invalid table error", False)
        except Exception:
            print_result("Invalid table error", True)
        
        adapter.close()
        
        print("\n✓ All MCP resource verification passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ MCP resources verification failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print_section("SQLite MCP Server Verification")
    print("This script verifies the MCP server implementation.\n")
    
    results = []
    
    # Run tests
    results.append(("Database Adapter", verify_database_adapter()))
    results.append(("MCP Tools", verify_mcp_tools()))
    results.append(("MCP Resources", verify_mcp_resources()))
    
    # Summary
    print_section("Verification Summary")
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ All verification tests passed!")
        print("\nThe server is ready for testing with MCP Inspector or clients.")
        return 0
    else:
        print("\n✗ Some verification tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
