@echo off
echo Foundry MCP Server Status Check
echo ================================

echo Checking server on port 8001...
netstat -an | findstr ":8001" >nul
if %errorlevel% == 0 (
    echo ✓ Port 8001 is in use
) else (
    echo ✗ Port 8001 is not in use - server may not be running
)

echo.
echo Testing health endpoint...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8001/health' -TimeoutSec 5; Write-Host '✓ Server Status:' $response.status; Write-Host '✓ Service:' $response.service; Write-Host '✓ Server Running:' $response.server_running; Write-Host ''; Write-Host 'Foundry Integration Status:'; Write-Host '- Foundry Available:' $response.foundry_available; Write-Host '- Installation Status:' $response.foundry_installation_status; if ($response.foundry_tools) { Write-Host '- Tools Status:'; $response.foundry_tools.PSObject.Properties | ForEach-Object { Write-Host ('  {0}: {1}' -f $_.Name, (if ($_.Value.available) { 'Available (' + $_.Value.version + ')' } else { 'Not Available - ' + $_.Value.error })) } }; if ($response.installation_help) { Write-Host ''; Write-Host 'Installation Help:'; Write-Host ('- {0}' -f $response.installation_help.message); Write-Host ('- URL: {0}' -f $response.installation_help.install_url) } } catch { Write-Host '✗ Server health check failed:' $_.Exception.Message }"

echo.
echo Testing info endpoint...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8001/info' -TimeoutSec 5; Write-Host '✓ Server Name:' $response.name; Write-Host '✓ Version:' $response.version; Write-Host '✓ Description:' $response.description; Write-Host '✓ Available Endpoints:' ($response.endpoints -join ', ') } catch { Write-Host '✗ Server info check failed:' $_.Exception.Message }"

echo.
pause
