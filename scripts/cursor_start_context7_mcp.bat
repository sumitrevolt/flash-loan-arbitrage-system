@echo off
echo Starting Context7 MCP Server for Cursor...
echo.

REM Set environment variables for Cursor integration
set MCP_PORT=8007
set MCP_COORDINATOR_URL=http://localhost:9000
set CURSOR_INTEGRATION=true

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Start the Context7 MCP server
echo Starting Context7 MCP Server...
python mcp_servers/context7_mcp_server.py

echo.
echo Context7 MCP Server stopped.
pause 