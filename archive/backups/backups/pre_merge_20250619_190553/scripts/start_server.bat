@echo off
REM Foundry MCP Server Startup Script
echo Starting Foundry MCP Server...
cd /d "%~dp0"

REM Check if server is already running
echo Checking if server is already running on port 8001...
netstat -an | findstr ":8001" >nul
if %errorlevel% == 0 (
    echo Server appears to be already running on port 8001
    echo Testing health endpoint...
    powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8001/health' -TimeoutSec 5; Write-Host 'Server Status:' $response.status; Write-Host 'Foundry Available:' $response.foundry_available; Write-Host 'Installation Status:' $response.foundry_installation_status } catch { Write-Host 'Server not responding properly' }"
    pause
    exit /b
)

echo Starting server in background...
start /B python enhanced_foundry_mcp_server.py

echo Waiting for server to start...
timeout /t 3 /nobreak >nul

echo Testing server health...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8001/health' -TimeoutSec 10; Write-Host 'SUCCESS: Server is running'; Write-Host 'Status:' $response.status; Write-Host 'Foundry Available:' $response.foundry_available; Write-Host 'Installation Status:' $response.foundry_installation_status; if (-not $response.foundry_available) { Write-Host 'NOTE: Foundry is not installed, but server is functional for basic operations' } } catch { Write-Host 'FAILED: Server failed to start or respond' }"

echo.
echo Server startup complete!
echo - Health endpoint: http://localhost:8001/health
echo - Server info: http://localhost:8001/info  
echo - Dashboard: file:///c:/Users/Ratanshila/Documents/flash%%20loan/dashboard/index.html
echo.
echo To install Foundry and enable full functionality:
echo Visit: https://book.getfoundry.sh/getting-started/installation
echo.
pause
