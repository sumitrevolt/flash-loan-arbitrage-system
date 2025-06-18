# Enhanced Copilot MCP Server Launcher
# This ensures the correct Python installation is used

$PYTHON_PATH = "C:\Program Files\Python311\python.exe"
$SERVER_PATH = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\ai_integration\working_enhanced_copilot_mcp_server.py"

Write-Host "Starting Enhanced Copilot MCP Server with Python: $PYTHON_PATH"
& $PYTHON_PATH $SERVER_PATH $args
