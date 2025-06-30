# Simple Flash Loan Arbitrage System Launcher for Windows
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "Flash Loan Arbitrage System Launcher" -ForegroundColor Blue
Write-Host "=====================================" -ForegroundColor Blue

function Write-Status {
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

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check Docker
Write-Status "Checking Docker..."
try {
    $null = docker --version
    $null = docker info 2>$null
    Write-Success "Docker is running"
}
catch {
    Write-Error "Docker is not running. Please start Docker Desktop first."
    exit 1
}

# Create directories
Write-Status "Creating directories..."
$directories = @("logs", "data\cache", "data\databases", "blockchain_data", "arbitrage_logs")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Success "Directories created"

# Create .env file
if (!(Test-Path ".env")) {
    Write-Warning ".env file not found. Creating template..."
    @"
# Flash Loan Arbitrage System Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GITHUB_TOKEN=your_github_token_here
POSTGRES_PASSWORD=flashloan_secure_password_2024
RABBITMQ_PASSWORD=rabbitmq_secure_password_2024
GRAFANA_PASSWORD=admin
PRIVATE_KEY=0x1234567890abcdef...
FLASH_LOAN_CONTRACT=0x...
EXECUTE_TRADES=false
MAX_GAS_PRICE=500
MIN_PROFIT_THRESHOLD=0.001
LOG_LEVEL=INFO
MONITORING_INTERVAL=1
"@ | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Warning "Please edit .env file with your actual values!"
    Write-Warning "IMPORTANT: This is running in SIMULATION mode by default (safe)"
    
    if (!$Force) {
        Read-Host "Press Enter to continue"
    }
}

Write-Status "Starting system..."

# Change to docker directory
Push-Location "deployment\docker\docker"

try {
    Write-Status "Building images..."
    docker-compose -f docker-compose.advanced-langchain.yml build --parallel
    
    Write-Status "Starting infrastructure..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d redis postgres-master rabbitmq etcd
    Start-Sleep 15
    
    Write-Status "Starting monitoring..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d prometheus grafana jaeger
    Start-Sleep 10
    
    Write-Status "Starting core services..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d web3-node blockchain-monitor arbitrage-executor langchain-orchestrator
    Start-Sleep 15
    
    Write-Status "Starting AI services..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d quantum-decision-engine swarm-coordinator market-predictor risk-manager
    Start-Sleep 10
    
    Write-Status "Starting agents..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d market-intelligence-director risk-management-chief dex-analyst-1 mev-protection-agent
    Start-Sleep 10
    
    Write-Status "Starting dashboard..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d arbitrage-dashboard nginx
    
    Write-Success "System startup complete!"
    
    Write-Host ""
    Write-Host "System Access URLs:" -ForegroundColor Blue
    Write-Host "==================" -ForegroundColor Blue
    Write-Host "Main Dashboard:      http://localhost:3001" -ForegroundColor White
    Write-Host "Grafana Monitoring:  http://localhost:3000 (admin/admin)" -ForegroundColor White
    Write-Host "LangChain API:       http://localhost:8000" -ForegroundColor White
    Write-Host "Blockchain Monitor:  http://localhost:8070" -ForegroundColor White
    Write-Host "Arbitrage Executor:  http://localhost:8071" -ForegroundColor White
    Write-Host "Web3 Node RPC:       http://localhost:8545" -ForegroundColor White
    Write-Host ""
    Write-Host "Quick Commands:" -ForegroundColor Blue
    Write-Host "View logs:    docker-compose -f docker-compose.advanced-langchain.yml logs -f" -ForegroundColor Yellow
    Write-Host "Stop system:  docker-compose -f docker-compose.advanced-langchain.yml down" -ForegroundColor Yellow
    Write-Host ""
    Write-Success "Flash Loan Arbitrage System is now running!"
    Write-Warning "System is in SIMULATION mode - no real money at risk"
    Write-Host ""
}
finally {
    Pop-Location
} 