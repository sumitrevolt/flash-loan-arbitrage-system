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

# Test MCP server endpoints
Write-Host "🔍 ENDPOINT TESTING:" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow

try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8001/health" -Method GET -TimeoutSec 5
    Write-Host "✅ Health endpoint: RESPONSIVE" -ForegroundColor Green
} catch {
    Write-Host "❌ Health endpoint: NOT RESPONSIVE" -ForegroundColor Red
}

try {
    $infoResponse = Invoke-WebRequest -Uri "http://localhost:8001/info" -Method GET -TimeoutSec 5
    Write-Host "✅ Info endpoint: RESPONSIVE" -ForegroundColor Green
} catch {
    Write-Host "❌ Info endpoint: NOT RESPONSIVE" -ForegroundColor Red
}

Write-Host ""

# Check arbitrage bot status
Write-Host "🤖 ARBITRAGE BOT STATUS:" -ForegroundColor Yellow
Write-Host "------------------------" -ForegroundColor Yellow

$arbitrageProcesses = Get-Process | Where-Object {$_.ProcessName -eq "python"} | Where-Object {
    try {
        $cmd = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmd -match "arbitrage" -or $cmd -match "flash.*loan"
    } catch {
        $false
    }
}

if ($arbitrageProcesses) {
    Write-Host "✅ Arbitrage bot processes: $($arbitrageProcesses.Count)" -ForegroundColor Green
} else {
    Write-Host "❌ No arbitrage bot processes found" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 SYSTEM SUMMARY:" -ForegroundColor Magenta
Write-Host "------------------" -ForegroundColor Magenta
Write-Host "Total Python processes: $(($pythonProcesses | Measure-Object).Count)" -ForegroundColor White
Write-Host "MCP Server status: $(if($port8001){'RUNNING'}else{'STOPPED'})" -ForegroundColor White
Write-Host "Arbitrage processes: $(($arbitrageProcesses | Measure-Object).Count)" -ForegroundColor White
Write-Host ""
