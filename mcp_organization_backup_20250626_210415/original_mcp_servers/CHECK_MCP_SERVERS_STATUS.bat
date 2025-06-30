@echo off
echo ========================================
echo MCP SERVERS STATUS CHECK
echo ========================================
echo.

echo [%TIME%] Checking MCP server status...
echo.

REM Function to check if a port is listening
echo Checking running processes...
echo.

REM Check for Python MCP processes
echo Python MCP Servers:
tasklist /FI "IMAGENAME eq python.exe" | findstr python.exe >nul
if %ERRORLEVEL% EQU 0 (
    echo [RUNNING] Python processes found
    tasklist /FI "IMAGENAME eq python.exe" | findstr python.exe
) else (
    echo [STOPPED] No Python MCP processes found
)

echo.

REM Check for Node.js MCP processes
echo Node.js MCP Servers:
tasklist /FI "IMAGENAME eq node.exe" | findstr node.exe >nul
if %ERRORLEVEL% EQU 0 (
    echo [RUNNING] Node.js processes found
    tasklist /FI "IMAGENAME eq node.exe" | findstr node.exe
) else (
    echo [STOPPED] No Node.js MCP processes found
)

echo.
echo ========================================
echo PORT STATUS CHECK
echo ========================================
echo.

REM Check specific ports for MCP servers
echo Checking MCP server ports...
echo.

echo Port 8000 (Flash Loan MCP):
netstat -an | findstr :8000 >nul
if %ERRORLEVEL% EQU 0 (
    echo [LISTENING] Port 8000 is active
    netstat -an | findstr :8000
) else (
    echo [CLOSED] Port 8000 is not listening
)

echo.
echo Port 8001 (TaskManager MCP):
netstat -an | findstr :8001 >nul
if %ERRORLEVEL% EQU 0 (
    echo [LISTENING] Port 8001 is active
    netstat -an | findstr :8001
) else (
    echo [CLOSED] Port 8001 is not listening
)

echo.
echo Port 8002 (Foundry MCP):
netstat -an | findstr :8002 >nul
if %ERRORLEVEL% EQU 0 (
    echo [LISTENING] Port 8002 is active
    netstat -an | findstr :8002
) else (
    echo [CLOSED] Port 8002 is not listening
)

echo.
echo Port 8003 (Copilot MCP):
netstat -an | findstr :8003 >nul
if %ERRORLEVEL% EQU 0 (
    echo [LISTENING] Port 8003 is active
    netstat -an | findstr :8003
) else (
    echo [CLOSED] Port 8003 is not listening
)

echo.
echo Port 8004 (Production MCP):
netstat -an | findstr :8004 >nul
if %ERRORLEVEL% EQU 0 (
    echo [LISTENING] Port 8004 is active
    netstat -an | findstr :8004
) else (
    echo [CLOSED] Port 8004 is not listening
)

echo.
echo ========================================
echo LOG FILE STATUS
echo ========================================
echo.

REM Check log files
if exist "logs" (
    echo Recent log files in logs directory:
    dir logs\*.log /O:D 2>nul
    echo.
    
    if exist "logs\taskmanager_mcp.log" (
        echo Last 3 lines of TaskManager MCP log:
        powershell "Get-Content 'logs\taskmanager_mcp.log' -Tail 3" 2>nul
        echo.
    )
    
    if exist "logs\flashloan_mcp.log" (
        echo Last 3 lines of Flash Loan MCP log:
        powershell "Get-Content 'logs\flashloan_mcp.log' -Tail 3" 2>nul
        echo.
    )
    
    if exist "logs\foundry_mcp.log" (
        echo Last 3 lines of Foundry MCP log:
        powershell "Get-Content 'logs\foundry_mcp.log' -Tail 3" 2>nul
        echo.
    )
    
    if exist "logs\copilot_mcp.log" (
        echo Last 3 lines of Copilot MCP log:
        powershell "Get-Content 'logs\copilot_mcp.log' -Tail 3" 2>nul
        echo.
    )
) else (
    echo [INFO] Logs directory does not exist - servers may not have been started yet
)

echo.
echo ========================================
echo HEALTH CHECK URLS
echo ========================================
echo.
echo Test these URLs in your browser or with curl:
echo - http://localhost:8000/health (Flash Loan MCP)
echo - http://localhost:8002/health (Foundry MCP)
echo - http://localhost:8003/health (Copilot MCP)
echo - http://localhost:8004/health (Production MCP)
echo.

REM Wait for user input before closing
echo Press any key to close this window...
pause >nul
