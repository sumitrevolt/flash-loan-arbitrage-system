@echo off
echo ========================================
echo STOPPING ALL MCP SERVERS
echo ========================================
echo.

echo [%TIME%] Stopping all MCP server processes...
echo.

REM Stop TaskManager MCP Server
echo Stopping TaskManager MCP Server...
taskkill /FI "WINDOWTITLE eq TaskManager-MCP*" /F >nul 2>&1
taskkill /IM node.exe /FI "WINDOWTITLE eq TaskManager-MCP*" /F >nul 2>&1

REM Stop Flash Loan MCP Server
echo Stopping Flash Loan MCP Server...
taskkill /FI "WINDOWTITLE eq FlashLoan-MCP*" /F >nul 2>&1

REM Stop Foundry MCP Server
echo Stopping Foundry MCP Server...
taskkill /FI "WINDOWTITLE eq Foundry-MCP*" /F >nul 2>&1

REM Stop Copilot MCP Server
echo Stopping Copilot MCP Server...
taskkill /FI "WINDOWTITLE eq Copilot-MCP*" /F >nul 2>&1

REM Stop Production MCP Server
echo Stopping Production MCP Server...
taskkill /FI "WINDOWTITLE eq Production-MCP*" /F >nul 2>&1

REM Also try to kill any Python processes running MCP servers
echo.
echo Stopping any remaining Python MCP processes...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO csv ^| findstr "mcp_server"') do (
    echo Killing process %%i
    taskkill /PID %%i /F >nul 2>&1
)

REM Also try to kill any Node.js processes running in MCP directories
echo Stopping any remaining Node.js MCP processes...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq node.exe" /FO csv ^| findstr "mcp-taskmanager"') do (
    echo Killing process %%i
    taskkill /PID %%i /F >nul 2>&1
)

echo.
echo ========================================
echo ALL MCP SERVERS STOPPED
echo ========================================
echo.
echo All MCP server processes have been terminated.
echo.
echo To restart the servers, run:
echo - START_ALL_MCP_SERVERS.bat (interactive mode)
echo - START_ALL_MCP_SERVERS_BACKGROUND.bat (background mode)
echo.

REM Wait for user input before closing
echo Press any key to close this window...
pause >nul
