@echo off
echo ========================================
echo STARTING ALL MCP SERVERS
echo ========================================
echo.

REM Set the working directory to the flash loan project
cd /d "c:\Users\Ratanshila\Documents\flash loan"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo [%TIME%] Starting MCP servers...
echo.

REM Start TaskManager MCP Server (TypeScript/Node.js)
echo [%TIME%] Starting TaskManager MCP Server (Port 8007)...
cd "mcp\mcp-taskmanager"
start "TaskManager-MCP" cmd /k "node dist/index.js"
cd ..\..

REM Wait a moment between starts
timeout /t 2 /nobreak >nul

REM Start Unified Flash Loan MCP Server (Python)
echo [%TIME%] Starting Unified Flash Loan MCP Server (Port 8000)...
start "FlashLoan-MCP" cmd /k "python mcp\working_unified_flash_loan_mcp_server.py --config unified_config.json"

REM Wait a moment between starts
timeout /t 2 /nobreak >nul

REM Start Enhanced Foundry MCP Server (Python)
echo [%TIME%] Starting Enhanced Foundry MCP Server (Port 8002)...
start "Foundry-MCP" cmd /k "python foundry-mcp-server\working_enhanced_foundry_mcp_server.py --config unified_config.json"

REM Wait a moment between starts
timeout /t 2 /nobreak >nul

REM Start Enhanced Copilot MCP Server (Python)
echo [%TIME%] Starting Enhanced Copilot MCP Server (Port 8003)...
start "Copilot-MCP" cmd /k "python core\working_enhanced_copilot_mcp_server.py"

REM Wait a moment between starts
timeout /t 2 /nobreak >nul

REM Start Production MCP Server (Python)
echo [%TIME%] Starting Production MCP Server (Port 8004)...
start "Production-MCP" cmd /k "python enhanced_production_mcp_server_v2.py"

echo.
echo ========================================
echo ALL MCP SERVERS STARTED
echo ========================================
echo.
echo Started the following MCP servers:
echo - TaskManager MCP Server (TypeScript) - Port 8007
echo - Unified Flash Loan MCP Server - Port 8000  
echo - Enhanced Foundry MCP Server - Port 8002
echo - Enhanced Copilot MCP Server - Port 8003
echo - Production MCP Server - Port 8004
echo.
echo Each server is running in its own command window.
echo To stop all servers, close their respective windows.
echo.
echo Health check URLs:
echo - http://localhost:8000/health (Flash Loan MCP)
echo - http://localhost:8002/health (Foundry MCP)  
echo - http://localhost:8003/health (Copilot MCP)
echo - http://localhost:8004/health (Production MCP)
echo - http://localhost:8007/health (TaskManager MCP)
echo.
echo Logs are being written to respective log files:
echo - unified_mcp_server.log
echo - enhanced_foundry_mcp.log
echo - enhanced_copilot_mcp.log
echo.

REM Wait for user input before closing
echo Press any key to close this window...
pause >nul
