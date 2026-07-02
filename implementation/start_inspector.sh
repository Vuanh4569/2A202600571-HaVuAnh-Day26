#!/bin/bash
# Helper script to start MCP Inspector for the SQLite Lab MCP Server

set -e

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_PATH="$SCRIPT_DIR/mcp_server.py"

# Check if the server file exists
if [ ! -f "$MCP_SERVER_PATH" ]; then
    echo "Error: MCP server file not found at $MCP_SERVER_PATH"
    exit 1
fi

# Create npm cache directory
mkdir -p "$SCRIPT_DIR/.npm-cache"

# Set npm cache
export NPM_CONFIG_CACHE="$SCRIPT_DIR/.npm-cache"

# Get Python path from virtual environment
PYTHON_PATH="$SCRIPT_DIR/.venv/bin/python"

if [ -z "$PYTHON_PATH" ]; then
    echo "Error: Python not found in PATH"
    exit 1
fi

echo "Starting MCP Inspector..."
echo "Server path: $MCP_SERVER_PATH"
echo "Python path: $PYTHON_PATH"
echo ""

# Start the inspector
npx -y @modelcontextprotocol/inspector "$PYTHON_PATH" "$MCP_SERVER_PATH"
