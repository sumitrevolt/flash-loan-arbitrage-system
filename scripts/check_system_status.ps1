# Flash Loan Arbitrage System Status Checker
Write-Host "=== FLASH LOAN ARBITRAGE SYSTEM STATUS ===" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Gray
Write-Host ""

# Check Docker containers
Write-Host "=== CONTAINER STATUS ===" -ForegroundColor Yellow
docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}" | Where-Object { $_ -match "blockchain-monitor|arbitrage-executor|flash-loan|langchain|redis|postgres" }

Write-Host ""

# Check blockchain monitor API
Write-Host "=== BLOCKCHAIN MONITOR API ===" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8070/health" -UseBasicParsing -TimeoutSec 5
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✅ Status: $($data.status)" -ForegroundColor Green
    Write-Host "✅ Latest Block: $($data.latest_block)" -ForegroundColor Green
    Write-Host "✅ Timestamp: $($data.timestamp)" -ForegroundColor Green
} catch {
    Write-Host "❌ Blockchain Monitor API not accessible" -ForegroundColor Red
}

Write-Host ""

# Check Web3 node
Write-Host "=== WEB3 NODE STATUS ===" -ForegroundColor Yellow
try {
    $web3Response = Invoke-WebRequest -Uri "http://localhost:8545" -Method POST -Body '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' -ContentType "application/json" -UseBasicParsing -TimeoutSec 5
    $web3Data = $web3Response.Content | ConvertFrom-Json
    $blockNumber = [Convert]::ToInt64($web3Data.result, 16)
    Write-Host "✅ Web3 RPC responding" -ForegroundColor Green
    Write-Host "✅ Current Block: $blockNumber" -ForegroundColor Green
} catch {
    Write-Host "❌ Web3 node not accessible" -ForegroundColor Red
}

Write-Host ""

# Check LangChain API
Write-Host "=== LANGCHAIN ORCHESTRATOR ===" -ForegroundColor Yellow
try {
    $langchainResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ LangChain API responding" -ForegroundColor Green
    Write-Host "✅ Status Code: $($langchainResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ LangChain API not accessible" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== SYSTEM READY STATUS ===" -ForegroundColor Cyan

$coreServices = @("flash-loan-web3-node", "flash-loan-redis", "flash-loan-postgres", "langchain")
$arbitrageServices = @("blockchain-monitor", "arbitrage-executor")

$coreStatus = $true
$arbitrageStatus = $true

# Check core services
foreach ($service in $coreServices) {
    $status = docker ps --filter "name=$service" --format "{Status}"
    if ($status -like "*healthy*" -or $status -like "*Up*") {
        Write-Host "✅ ${service}: Running" -ForegroundColor Green
    } else {
        Write-Host "❌ ${service}: Not running" -ForegroundColor Red
        $coreStatus = $false
    }
}

# Check arbitrage services
foreach ($service in $arbitrageServices) {
    $status = docker ps --filter "name=$service" --format "{Status}"
    if ($status -like "*healthy*" -or $status -like "*Up*") {
        Write-Host "✅ ${service}: Running" -ForegroundColor Green
    } else {
        Write-Host "⚠️ ${service}: Not running" -ForegroundColor Yellow
        $arbitrageStatus = $false
    }
}

Write-Host ""
if ($coreStatus) {
    Write-Host "🚀 CORE INFRASTRUCTURE: READY" -ForegroundColor Green
} else {
    Write-Host "❌ CORE INFRASTRUCTURE: ISSUES DETECTED" -ForegroundColor Red
}

if ($arbitrageStatus) {
    Write-Host "🚀 ARBITRAGE SYSTEM: FULLY OPERATIONAL" -ForegroundColor Green
} else {
    Write-Host "⚠️ ARBITRAGE SYSTEM: PARTIALLY OPERATIONAL" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== PORTS & ENDPOINTS ===" -ForegroundColor Yellow
Write-Host "• Blockchain Monitor API: http://localhost:8070" -ForegroundColor White
Write-Host "• Arbitrage Executor API: http://localhost:8071" -ForegroundColor White
Write-Host "• Web3 Node RPC: http://localhost:8545" -ForegroundColor White
Write-Host "• Web3 Node WebSocket: ws://localhost:8546" -ForegroundColor White
Write-Host "• LangChain API: http://localhost:8000" -ForegroundColor White
Write-Host "• Redis: localhost:6379" -ForegroundColor White
Write-Host "• PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "• RabbitMQ Management: http://localhost:15672" -ForegroundColor White
Write-Host "" 