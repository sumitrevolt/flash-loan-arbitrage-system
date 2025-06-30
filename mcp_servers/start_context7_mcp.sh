#!/bin/bash

echo "Starting Context7 MCP Server..."
echo

# Set environment variables
export MCP_PORT=8007
export MCP_COORDINATOR_URL=http://localhost:9000

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the Context7 MCP server
python3 mcp_servers/context7_mcp_server.py

echo
echo "Context7 MCP Server stopped." 