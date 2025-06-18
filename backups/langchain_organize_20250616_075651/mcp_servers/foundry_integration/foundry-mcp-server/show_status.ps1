# Foundry MCP Server Status Display
Write-Host "🚀 FOUNDRY MCP SERVER STATUS" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Check if server is running
Write-Host "📊 SERVER STATUS:" -ForegroundColor Yellow
Write-Host "-----------------" -ForegroundColor Yellow

$port8001 = netstat -an | Select-String ":8001"
if ($port8001) {
    Write-Host "✅ Foundry MCP Server: RUNNING on port 8001" -ForegroundColor Green
    Write-Host "   $port8001" -ForegroundColor Cyan
} else {
    Write-Host "❌ Foundry MCP Server: NOT RUNNING" -ForegroundColor Red
}

# Check Python processes
$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -eq "python"} 
if ($pythonProcesses) {
        Write-Host "✅ Python processes running: $($pythonProcesses.Count)" -ForegroundColor Green
    $pythonProcesses | ForEach-Object {
        try {
            $cmd = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
            if ($cmd -match "foundry-mcp-server" -or $cmd -match "simple_server") {
                Write-Host "   📈 $($_.Id): MCP Server Process" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "   📈 $($_.Id): [Process details not accessible]" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "❌ No Python processes running" -ForegroundColor Red
}

Write-Host ""

# Test server connection
Write-Host "🌐 SERVER CONNECTION TEST:" -ForegroundColor Yellow
Write-Host "---------------------------" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Server responds: $($response.status)" -ForegroundColor Green
    if ($response.error) {
        Write-Host "⚠️  Server error: $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Server not responding or error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check recent logs
Write-Host "📋 RECENT SERVER LOGS:" -ForegroundColor Yellow
Write-Host "-----------------------" -ForegroundColor Yellow

if (Test-Path "logs\mcp_server.log") {
    $recentLogs = Get-Content "logs\mcp_server.log" -Tail 5 -ErrorAction SilentlyContinue
    if ($recentLogs) {
        Write-Host "📄 Last 5 log entries:" -ForegroundColor Cyan
        $recentLogs | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    } else {
        Write-Host "❌ No recent log entries" -ForegroundColor Red
    }
} else {
    Write-Host "❌ No log file found" -ForegroundColor Red
}

Write-Host ""

# Show available endpoints
Write-Host "🔧 FOUNDRY MCP SERVER ENDPOINTS:" -ForegroundColor Yellow
Write-Host "---------------------------------" -ForegroundColor Yellow
Write-Host "✅ Health Check: http://localhost:8001/health" -ForegroundColor Green
Write-Host "✅ Server Info: http://localhost:8001/info" -ForegroundColor Green
Write-Host "✅ Tools List: http://localhost:8001/tools" -ForegroundColor Green
Write-Host "✅ WebSocket: ws://localhost:8001/ws" -ForegroundColor Green

Write-Host ""

# Show integration status
Write-Host "🔗 INTEGRATION STATUS:" -ForegroundColor Yellow
Write-Host "-----------------------" -ForegroundColor Yellow

# Check if foundry tools are available
$forgeAvailable = $false
try {
    $null = Get-Command "forge" -ErrorAction Stop
    $forgeAvailable = $true
    Write-Host "✅ Forge (Foundry): Available" -ForegroundColor Green
} catch {
    Write-Host "❌ Forge (Foundry): Not installed or not in PATH" -ForegroundColor Red
}

try {
    $null = Get-Command "cast" -ErrorAction Stop
    Write-Host "✅ Cast (Foundry): Available" -ForegroundColor Green
} catch {
    Write-Host "❌ Cast (Foundry): Not installed or not in PATH" -ForegroundColor Red
}

try {
    $null = Get-Command "anvil" -ErrorAction Stop
    Write-Host "✅ Anvil (Foundry): Available" -ForegroundColor Green
} catch {
    Write-Host "❌ Anvil (Foundry): Not installed or not in PATH" -ForegroundColor Red
}

Write-Host ""

if (-not $forgeAvailable) {
    Write-Host "💡 TO INSTALL FOUNDRY:" -ForegroundColor Cyan
    Write-Host "   1. Visit: https://getfoundry.sh/" -ForegroundColor White
    Write-Host "   2. Run: curl -L https://foundry.paradigm.xyz | bash" -ForegroundColor White
    Write-Host "   3. Run: foundryup" -ForegroundColor White
    Write-Host ""
}

Write-Host "🔄 To refresh status: .\show_status.ps1" -ForegroundColor Green
Write-Host "🛑 To stop server: Find Python process and kill it" -ForegroundColor Yellow
Write-Host ""
