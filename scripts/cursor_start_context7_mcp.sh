#!/bin/bash

echo "Starting Context7 MCP Server for Cursor..."
echo

# Set environment variables for Cursor integration
export MCP_PORT=8007
export MCP_COORDINATOR_URL=http://localhost:9000
export CURSOR_INTEGRATION=true

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the Context7 MCP server
echo "Starting Context7 MCP Server..."
python3 mcp_servers/context7_mcp_server.py

echo
echo "Context7 MCP Server stopped." 