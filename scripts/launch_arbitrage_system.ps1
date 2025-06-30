# Flash Loan Arbitrage System Launcher (Windows PowerShell)
param(
    [switch]$SkipChecks,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Flash Loan Arbitrage System Launcher" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

# Function to print colored output
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

# Check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check Docker
    try {
        $null = docker --version
        Write-Success "Docker is installed"
    }
    catch {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    # Check Docker Compose
    try {
        $null = docker-compose --version
        Write-Success "Docker Compose is available"
    }
    catch {
        Write-Error "Docker Compose is not available. Please ensure Docker Desktop is properly installed."
        exit 1
    }
    
    # Check if Docker daemon is running
    try {
        $null = docker info 2>$null
        Write-Success "Docker daemon is running"
    }
    catch {
        Write-Error "Docker daemon is not running. Please start Docker Desktop first."
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

# Create necessary directories
function New-RequiredDirectories {
    Write-Status "Creating necessary directories..."
    
    $directories = @(
        "logs",
        "data\cache",
        "data\databases", 
        "blockchain_data",
        "arbitrage_logs"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Status "Created directory: $dir"
        }
    }
    
    Write-Success "Directories created"
}

# Check environment variables
function Test-Environment {
    Write-Status "Checking environment variables..."
    
    # Create .env file if it doesn't exist
    if (!(Test-Path ".env")) {
        Write-Warning ".env file not found. Creating template..."
        
        $envContent = @"
# Flash Loan Arbitrage System Configuration

# API Keys (REQUIRED for live trading)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GITHUB_TOKEN=your_github_token_here

# Database Passwords
POSTGRES_PASSWORD=flashloan_secure_password_2024
RABBITMQ_PASSWORD=rabbitmq_secure_password_2024
GRAFANA_PASSWORD=admin

# Trading Configuration (IMPORTANT!)
PRIVATE_KEY=0x1234567890abcdef...  # Your private key for trading (KEEP SECURE!)
FLASH_LOAN_CONTRACT=0x...  # Your deployed flash loan contract address
EXECUTE_TRADES=false  # Set to 'true' for live trading, 'false' for simulation

# Risk Management
MAX_GAS_PRICE=500  # Maximum gas price in gwei
MIN_PROFIT_THRESHOLD=0.001  # Minimum profit threshold (0.1%)

# System Configuration
LOG_LEVEL=INFO
MONITORING_INTERVAL=1
"@
        
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Warning "Please edit .env file with your actual values before proceeding!"
        Write-Warning "⚠️  NEVER commit your private keys to version control!"
        Read-Host "Press Enter to continue after editing .env file"
    }
    
    # Read .env file
    $envVars = @{}
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.+)$") {
            $envVars[$matches[1]] = $matches[2]
        }
    }
    
    if (!$envVars["OPENAI_API_KEY"] -or $envVars["OPENAI_API_KEY"] -eq "your_openai_api_key_here") {
        Write-Warning "OPENAI_API_KEY not set. AI features will be limited."
    }
    
    if ($envVars["EXECUTE_TRADES"] -eq "true") {
        if (!$envVars["PRIVATE_KEY"] -or $envVars["PRIVATE_KEY"] -eq "0x1234567890abcdef...") {
            Write-Error "PRIVATE_KEY must be set for live trading!"
            Write-Error "Set EXECUTE_TRADES=false for simulation mode."
            exit 1
        }
        
        if (!$envVars["FLASH_LOAN_CONTRACT"] -or $envVars["FLASH_LOAN_CONTRACT"] -eq "0x...") {
            Write-Error "FLASH_LOAN_CONTRACT must be set for live trading!"
            exit 1
        }
        
        Write-Warning "⚠️  LIVE TRADING MODE ENABLED ⚠️"
        Write-Warning "This will execute real transactions with real money!"
        $confirm = Read-Host "Are you sure you want to continue? (yes/no)"
        if ($confirm -ne "yes") {
            Write-Status "Switching to simulation mode..."
            (Get-Content ".env") -replace "EXECUTE_TRADES=true", "EXECUTE_TRADES=false" | Set-Content ".env"
        }
    }
    else {
        Write-Status "Running in simulation mode (safe)"
    }
    
    Write-Success "Environment check completed"
}

# Build Docker images
function Build-Images {
    Write-Status "Building Docker images..."
    
    Push-Location "deployment\docker\docker"
    
    try {
        # Build images
        docker-compose -f docker-compose.advanced-langchain.yml build --parallel
        Write-Success "Docker images built successfully"
    }
    finally {
        Pop-Location
    }
}

# Start the system
function Start-System {
    Write-Status "Starting Flash Loan Arbitrage System..."
    
    Push-Location "deployment\docker\docker"
    
    try {
        # Start infrastructure services first
        Write-Status "Starting infrastructure services..."
        docker-compose -f docker-compose.advanced-langchain.yml up -d redis postgres-master rabbitmq etcd
        
        # Wait for infrastructure to be ready
        Write-Status "Waiting for infrastructure services to be ready..."
        Start-Sleep 30
        
        # Start monitoring services
        Write-Status "Starting monitoring services..."
        docker-compose -f docker-compose.advanced-langchain.yml up -d prometheus grafana jaeger
        
        # Start core services
        Write-Status "Starting core arbitrage services..."
        docker-compose -f docker-compose.advanced-langchain.yml up -d web3-node blockchain-monitor arbitrage-executor langchain-orchestrator
        
        # Wait for core services
        Write-Status "Waiting for core services to initialize..."
        Start-Sleep 20
        
        # Start AI and analysis services
        Write-Status "Starting AI services..."
        docker-compose -f docker-compose.advanced-langchain.yml up -d quantum-decision-engine swarm-coordinator market-predictor risk-manager
        
        # Start agent swarm
        Write-Status "Starting agent swarm..."
        docker-compose -f docker-compose.advanced-langchain.yml up -d market-intelligence-director risk-management-chief dex-analyst-1 mev-protection-agent
        
        # Start dashboard and load balancer
        Write-Status "Starting dashboard and load balancer..."
        docker-compose -f docker-compose.advanced-langchain.yml up -d arbitrage-dashboard nginx
        
        Write-Success "System startup complete!"
    }
    finally {
        Pop-Location
    }
}

# Check system health
function Test-SystemHealth {
    Write-Status "Checking system health..."
    
    # Wait a bit for services to fully start
    Start-Sleep 10
    
    $services = @(
        @("http://localhost:8000/health", "LangChain Orchestrator"),
        @("http://localhost:8070/health", "Blockchain Monitor"),
        @("http://localhost:8071/health", "Arbitrage Executor"),
        @("http://localhost:3001/health", "Dashboard"),
        @("http://localhost:3000", "Grafana"),
        @("http://localhost:9090", "Prometheus")
    )
    
    $healthyCount = 0
    $totalServices = $services.Count
    
    foreach ($service in $services) {
        $url = $service[0]
        $name = $service[1]
        
        try {
            $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Success "$name is healthy"
                $healthyCount++
            }
            else {
                Write-Warning "$name returned status code $($response.StatusCode)"
            }
        }
        catch {
            Write-Warning "$name is not responding"
        }
    }
    
    Write-Status "Health check complete: $healthyCount/$totalServices services healthy"
    
    if ($healthyCount -eq $totalServices) {
        Write-Success "🎉 All services are running perfectly!"
    }
    else {
        Write-Warning "Some services may still be starting up. Wait a few minutes and check again."
    }
}

# Display system URLs
function Show-SystemUrls {
    Write-Host ""
    Write-Host "🌐 System Access URLs:" -ForegroundColor Blue
    Write-Host "======================" -ForegroundColor Blue
    Write-Host ""
    Write-Host "📊 Main Dashboard:           http://localhost:3001" -ForegroundColor White
    Write-Host "🎛️  Grafana Monitoring:      http://localhost:3000 (admin/admin)" -ForegroundColor White
    Write-Host "📈 Prometheus Metrics:       http://localhost:9090" -ForegroundColor White
    Write-Host "🔍 Jaeger Tracing:           http://localhost:16686" -ForegroundColor White
    Write-Host "🤖 LangChain Orchestrator:   http://localhost:8000" -ForegroundColor White
    Write-Host "⛓️  Blockchain Monitor:       http://localhost:8070" -ForegroundColor White
    Write-Host "💰 Arbitrage Executor:       http://localhost:8071" -ForegroundColor White
    Write-Host "🕸️  Web3 Node RPC:           http://localhost:8545" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Quick Commands:" -ForegroundColor Blue
    Write-Host "=================" -ForegroundColor Blue
    Write-Host "View logs:           docker-compose -f deployment\docker\docker\docker-compose.advanced-langchain.yml logs -f" -ForegroundColor Yellow
    Write-Host "Stop system:         docker-compose -f deployment\docker\docker\docker-compose.advanced-langchain.yml down" -ForegroundColor Yellow
    Write-Host "Restart service:     docker-compose -f deployment\docker\docker\docker-compose.advanced-langchain.yml restart [service]" -ForegroundColor Yellow
    Write-Host ""
}

# Main execution
function Main {
    Write-Host ""
    Write-Host "Welcome to the Flash Loan Arbitrage System!" -ForegroundColor Green
    Write-Host "This system will start a comprehensive blockchain arbitrage bot" -ForegroundColor White
    Write-Host "with AI-driven decision making and real-time monitoring." -ForegroundColor White
    Write-Host ""
    
    if (!$Force) {
        $confirm = Read-Host "Do you want to start the system? (y/n)"
        if ($confirm -ne "y" -and $confirm -ne "yes") {
            Write-Status "Operation cancelled."
            return
        }
    }
    
    if (!$SkipChecks) {
        Test-Prerequisites
        New-RequiredDirectories
        Test-Environment
    }
    
    Build-Images
    Start-System
    Test-SystemHealth
    Show-SystemUrls
    
    Write-Host ""
    Write-Success "🚀 Flash Loan Arbitrage System is now running!"
    Write-Status "Monitor the dashboard at http://localhost:3001"
    Write-Status "Check system logs for real-time activity"
    Write-Host ""
    Write-Warning "⚠️  Remember: This system can execute real trades if configured!"
    Write-Warning "Always monitor the system and understand the risks involved."
    Write-Host ""
}

# Script execution
if ($MyInvocation.InvocationName -ne '.') {
    Main
} 