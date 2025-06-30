# Flash Loan Arbitrage System Starter
# Updated for organized project structure

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Flash Loan Arbitrage System" -ForegroundColor Blue
Write-Host "=======================================" -ForegroundColor Blue

function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

# Check Docker
Write-Info "Checking Docker status..."
try {
    $null = docker info 2>$null
    Write-Success "Docker is running"
}
catch {
    Write-Error "Docker is not running. Please start Docker Desktop first."
    exit 1
}

# Check .env file
if (!(Test-Path "..\\.env")) {
    Write-Warning ".env file not found. Creating template..."
    @"
# Flash Loan Arbitrage System Configuration
OPENAI_API_KEY=sk-demo-key-not-real
ANTHROPIC_API_KEY=sk-ant-demo-key-not-real
GITHUB_TOKEN=ghp_demo-token-not-real
POSTGRES_PASSWORD=flashloan_secure_password_2024
RABBITMQ_PASSWORD=rabbitmq_secure_password_2024
GRAFANA_PASSWORD=admin
PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000001
FLASH_LOAN_CONTRACT=0x0000000000000000000000000000000000000000
EXECUTE_TRADES=false
MAX_GAS_PRICE=500
MIN_PROFIT_THRESHOLD=0.001
LOG_LEVEL=INFO
MONITORING_INTERVAL=1
"@ | Out-File -FilePath "..\\.env" -Encoding UTF8
    
    Write-Warning "Please edit .env file with your actual values!"
    Write-Warning "System is in SIMULATION mode (safe)"
}

# Check current running services
Write-Info "Checking current services..."
$runningContainers = docker ps --format "table {{.Names}}\t{{.Status}}"
Write-Host $runningContainers

Write-Info "Starting complete arbitrage system..."

# Change to deployment directory
Push-Location "..\\deployment\\docker\\docker"

try {
    Write-Info "Starting additional services..."
    
    # Start the blockchain monitor and arbitrage executor if not running
    Write-Info "Starting blockchain monitor..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d blockchain-monitor
    
    Write-Info "Starting arbitrage executor..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d arbitrage-executor
    
    Write-Info "Starting dashboard..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d arbitrage-dashboard
    
    Write-Info "Waiting for services to initialize..."
    Start-Sleep 15
    
    Write-Success "System startup complete!"
    
    Write-Host ""
    Write-Host "🌐 System Access URLs:" -ForegroundColor Blue
    Write-Host "======================" -ForegroundColor Blue
    Write-Host "📊 Main Dashboard:           http://localhost:3001" -ForegroundColor White
    Write-Host "🤖 LangChain API:            http://localhost:8000" -ForegroundColor White
    Write-Host "⛓️  Blockchain Monitor:       http://localhost:8070" -ForegroundColor White
    Write-Host "💰 Arbitrage Executor:       http://localhost:8071" -ForegroundColor White
    Write-Host "🕸️  Web3 Node RPC:           http://localhost:8545" -ForegroundColor White
    Write-Host "🐘 PostgreSQL:               localhost:5432" -ForegroundColor White
    Write-Host "🔴 Redis:                    localhost:6379" -ForegroundColor White
    Write-Host ""
    
    Write-Host "📋 Quick Commands:" -ForegroundColor Blue
    Write-Host "View logs:    docker-compose logs -f" -ForegroundColor Yellow
    Write-Host "Stop system:  docker-compose down" -ForegroundColor Yellow
    Write-Host "System status: docker ps" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Success "🎉 Flash Loan Arbitrage System is running!"
    Write-Warning "⚠️  System is in SIMULATION mode - no real money at risk"
    Write-Host ""
    
} catch {
    Write-Error "Failed to start system: $($_.Exception.Message)"
} finally {
    Pop-Location
} 