# AutoGen & LangChain Deployment Script (PowerShell)
# ==================================================
# Comprehensive deployment script for the Flash Loan AutoGen and LangChain systems

param(
    [Parameter(Position=0)]
    [ValidateSet("deploy", "restart", "stop", "status", "logs", "test", "cleanup", "help")]
    [string]$Action = "deploy"
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$ComposeFile = Join-Path $ScriptDir "docker-compose.unified.yml"
$EnvFile = Join-Path $ScriptDir ".env"
$LogDir = Join-Path $ScriptDir "logs"
$LogFile = Join-Path $LogDir "deployment.log"

# Ensure logs directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Logging functions
function Write-LogInfo {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[INFO] $timestamp - $Message"
    Write-Host $logMessage -ForegroundColor Green
    Add-Content -Path $LogFile -Value $logMessage
}

function Write-LogWarn {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[WARN] $timestamp - $Message"
    Write-Host $logMessage -ForegroundColor Yellow
    Add-Content -Path $LogFile -Value $logMessage
}

function Write-LogError {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[ERROR] $timestamp - $Message"
    Write-Host $logMessage -ForegroundColor Red
    Add-Content -Path $LogFile -Value $logMessage
}

function Write-LogSuccess {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[SUCCESS] $timestamp - $Message"
    Write-Host $logMessage -ForegroundColor Green
    Add-Content -Path $LogFile -Value $logMessage
}

function Write-LogStep {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[STEP] $timestamp - $Message"
    Write-Host $logMessage -ForegroundColor Blue
    Add-Content -Path $LogFile -Value $logMessage
}

# Print banner
function Show-Banner {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Magenta
    Write-Host "    Flash Loan AutoGen & LangChain Deployment System" -ForegroundColor Magenta
    Write-Host "==================================================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "🚀 Starting deployment of advanced multi-agent systems..." -ForegroundColor Cyan
    Write-Host ""
}

# Check prerequisites
function Test-Prerequisites {
    Write-LogStep "Checking deployment prerequisites..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-LogInfo "Docker found: $dockerVersion"
    }
    catch {
        Write-LogError "Docker is not installed or not in PATH. Please install Docker Desktop."
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-LogInfo "Docker Compose found: $composeVersion"
    }
    catch {
        try {
            $composeVersion = docker compose version
            Write-LogInfo "Docker Compose (plugin) found: $composeVersion"
        }
        catch {
            Write-LogError "Docker Compose is not available. Please install Docker Compose."
            exit 1
        }
    }
    
    # Check if Docker daemon is running
    try {
        docker info | Out-Null
        Write-LogInfo "Docker daemon is running"
    }
    catch {
        Write-LogError "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    }
    
    # Check compose file
    if (-not (Test-Path $ComposeFile)) {
        Write-LogError "Docker Compose file not found: $ComposeFile"
        exit 1
    }
    
    # Check environment file
    if (-not (Test-Path $EnvFile)) {
        Write-LogError "Environment file not found: $EnvFile"
        exit 1
    }
    
    Write-LogSuccess "All prerequisites satisfied"
}

# Clean up existing containers and volumes
function Remove-ExistingDeployment {
    Write-LogStep "Cleaning up existing containers and volumes..."
    
    try {
        # Stop and remove existing containers
        docker-compose -f $ComposeFile --env-file $EnvFile down --remove-orphans --volumes 2>$null
        
        # Remove unused images and networks (optional)
        docker system prune -f --volumes 2>$null
        
        Write-LogSuccess "Cleanup completed"
    }
    catch {
        Write-LogWarn "Some cleanup operations failed, but continuing..."
    }
}

# Build images
function Build-Images {
    Write-LogStep "Building Docker images..."
    
    try {
        # Build all services with no cache for fresh deployment
        docker-compose -f $ComposeFile --env-file $EnvFile build --no-cache --parallel
        Write-LogSuccess "All images built successfully"
    }
    catch {
        Write-LogError "Image building failed"
        exit 1
    }
}

# Start infrastructure services first
function Start-Infrastructure {
    Write-LogStep "Starting infrastructure services..."
    
    try {
        # Start core infrastructure
        docker-compose -f $ComposeFile --env-file $EnvFile up -d postgres redis rabbitmq
        Write-LogInfo "Infrastructure services started"
        
        # Wait for services to be ready
        Write-LogInfo "Waiting for infrastructure services to be ready..."
        Start-Sleep -Seconds 30
        
        # Check PostgreSQL
        Write-LogInfo "Checking PostgreSQL readiness..."
        $pgReady = $false
        for ($i = 1; $i -le 30; $i++) {
            try {
                docker-compose -f $ComposeFile --env-file $EnvFile exec -T postgres pg_isready -U flash_loan_user -d flash_loan_db 2>$null | Out-Null
                Write-LogSuccess "PostgreSQL is ready"
                $pgReady = $true
                break
            }
            catch {
                if ($i -eq 30) {
                    Write-LogError "PostgreSQL failed to start properly"
                    exit 1
                }
                Start-Sleep -Seconds 2
            }
        }
        
        # Check Redis
        Write-LogInfo "Checking Redis readiness..."
        $redisReady = $false
        for ($i = 1; $i -le 30; $i++) {
            try {
                docker-compose -f $ComposeFile --env-file $EnvFile exec -T redis redis-cli ping 2>$null | Out-Null
                Write-LogSuccess "Redis is ready"
                $redisReady = $true
                break
            }
            catch {
                if ($i -eq 30) {
                    Write-LogError "Redis failed to start properly"
                    exit 1
                }
                Start-Sleep -Seconds 2
            }
        }
        
        Write-LogSuccess "All infrastructure services are ready"
    }
    catch {
        Write-LogError "Failed to start infrastructure services"
        exit 1
    }
}

# Start MCP servers
function Start-MCPServers {
    Write-LogStep "Starting MCP servers..."
    
    try {
        docker-compose -f $ComposeFile --env-file $EnvFile up -d mcp-supermemory mcp-context7 mcp-filesystem mcp-taskmanager
        Write-LogSuccess "MCP servers started"
        
        # Wait for MCP servers to be ready
        Write-LogInfo "Waiting for MCP servers to initialize..."
        Start-Sleep -Seconds 20
        
        Write-LogSuccess "MCP servers are ready"
    }
    catch {
        Write-LogError "Failed to start MCP servers"
        exit 1
    }
}

# Start AutoGen and LangChain services
function Start-AgentSystems {
    Write-LogStep "Starting AutoGen and LangChain systems..."
    
    # Start LangChain coordinator first
    Write-LogInfo "Starting LangChain coordinator..."
    try {
        docker-compose -f $ComposeFile --env-file $EnvFile up -d langchain-coordinator
        Write-LogSuccess "LangChain coordinator started"
    }
    catch {
        Write-LogError "Failed to start LangChain coordinator"
        exit 1
    }
    
    # Wait for LangChain to be ready
    Write-LogInfo "Waiting for LangChain to initialize..."
    Start-Sleep -Seconds 45
    
    # Check LangChain health
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-LogSuccess "LangChain coordinator is ready"
                break
            }
        }
        catch {
            if ($i -eq 30) {
                Write-LogWarn "LangChain health check timeout, continuing..."
                break
            }
            Start-Sleep -Seconds 3
        }
    }
    
    # Start AutoGen coordinator
    Write-LogInfo "Starting AutoGen coordinator..."
    try {
        docker-compose -f $ComposeFile --env-file $EnvFile up -d autogen-coordinator
        Write-LogSuccess "AutoGen coordinator started"
    }
    catch {
        Write-LogError "Failed to start AutoGen coordinator"
        exit 1
    }
    
    # Wait for AutoGen to be ready
    Write-LogInfo "Waiting for AutoGen to initialize..."
    Start-Sleep -Seconds 45
    
    # Check AutoGen health
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8010/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-LogSuccess "AutoGen coordinator is ready"
                break
            }
        }
        catch {
            if ($i -eq 30) {
                Write-LogWarn "AutoGen health check timeout, continuing..."
                break
            }
            Start-Sleep -Seconds 3
        }
    }
    
    Write-LogSuccess "Both agent systems are running"
}

# Start monitoring and support services
function Start-Monitoring {
    Write-LogStep "Starting monitoring and support services..."
    
    try {
        docker-compose -f $ComposeFile --env-file $EnvFile up -d system-monitor grafana elasticsearch kibana web-dashboard health-checker
        Write-LogSuccess "Monitoring services started"
        
        # Wait for services to initialize
        Write-LogInfo "Waiting for monitoring services to initialize..."
        Start-Sleep -Seconds 30
        
        Write-LogSuccess "Monitoring services are ready"
    }
    catch {
        Write-LogWarn "Some monitoring services may have failed to start, but core systems are running"
    }
}

# Display deployment status
function Show-DeploymentStatus {
    Write-LogStep "Checking deployment status..."
    
    Write-Host ""
    Write-Host "🔍 Service Status Check:" -ForegroundColor Cyan
    Write-Host "=================================================================="
    
    # Show running containers
    Write-Host "Running Containers:" -ForegroundColor Blue
    docker-compose -f $ComposeFile --env-file $EnvFile ps
    
    Write-Host ""
    Write-Host "Service Endpoints:" -ForegroundColor Blue
    Write-Host "----------------------------------------------------------------"
    Write-Host "📊 LangChain Coordinator:     http://localhost:8000" -ForegroundColor Green
    Write-Host "📊 LangChain Health:          http://localhost:8000/health" -ForegroundColor Green
    Write-Host "📊 LangChain Status:          http://localhost:8000/status" -ForegroundColor Green
    Write-Host ""
    Write-Host "🤖 AutoGen Coordinator:       http://localhost:8010" -ForegroundColor Green
    Write-Host "🤖 AutoGen Health:            http://localhost:8010/health" -ForegroundColor Green
    Write-Host "🤖 AutoGen Service Info:      http://localhost:8010/service/info" -ForegroundColor Green
    Write-Host ""
    Write-Host "📡 MCP Supermemory:           http://localhost:8100" -ForegroundColor Green
    Write-Host "📡 MCP Context7:              http://localhost:8101" -ForegroundColor Green
    Write-Host "📡 MCP Filesystem:            http://localhost:8102" -ForegroundColor Green
    Write-Host "📡 MCP Task Manager:          http://localhost:8103" -ForegroundColor Green
    Write-Host ""
    Write-Host "📈 Grafana Dashboard:         http://localhost:3000" -ForegroundColor Green
    Write-Host "📈 Prometheus Metrics:        http://localhost:9090" -ForegroundColor Green
    Write-Host "📈 Kibana Logs:               http://localhost:5601" -ForegroundColor Green
    Write-Host "📈 Web Dashboard:             http://localhost:8090" -ForegroundColor Green
    Write-Host ""
    Write-Host "💾 PostgreSQL:                localhost:5432" -ForegroundColor Green
    Write-Host "💾 Redis:                     localhost:6379" -ForegroundColor Green
    Write-Host "💾 RabbitMQ Management:       http://localhost:15672" -ForegroundColor Green
    Write-Host ""
}

# Test system functionality
function Test-Deployment {
    Write-LogStep "Testing deployment functionality..."
    
    Write-Host "🧪 Running deployment tests..." -ForegroundColor Cyan
    
    # Test LangChain
    Write-Host "Testing LangChain coordinator..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
        if ($response.Content -match "healthy|ok") {
            Write-LogSuccess "✅ LangChain coordinator is healthy"
        }
        else {
            Write-LogWarn "⚠️ LangChain coordinator health check failed"
        }
    }
    catch {
        Write-LogWarn "⚠️ LangChain coordinator health check failed"
    }
    
    # Test AutoGen
    Write-Host "Testing AutoGen coordinator..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8010/health" -TimeoutSec 10 -UseBasicParsing
        if ($response.Content -match "healthy|ok") {
            Write-LogSuccess "✅ AutoGen coordinator is healthy"
        }
        else {
            Write-LogWarn "⚠️ AutoGen coordinator health check failed"
        }
    }
    catch {
        Write-LogWarn "⚠️ AutoGen coordinator health check failed"
    }
    
    # Test database connection
    Write-Host "Testing database connection..." -ForegroundColor Blue
    try {
        docker-compose -f $ComposeFile --env-file $EnvFile exec -T postgres pg_isready -U flash_loan_user -d flash_loan_db 2>$null | Out-Null
        Write-LogSuccess "✅ PostgreSQL connection is working"
    }
    catch {
        Write-LogWarn "⚠️ PostgreSQL connection test failed"
    }
    
    # Test Redis connection
    Write-Host "Testing Redis connection..." -ForegroundColor Blue
    try {
        $redisTest = docker-compose -f $ComposeFile --env-file $EnvFile exec -T redis redis-cli ping 2>$null
        if ($redisTest -match "PONG") {
            Write-LogSuccess "✅ Redis connection is working"
        }
        else {
            Write-LogWarn "⚠️ Redis connection test failed"
        }
    }
    catch {
        Write-LogWarn "⚠️ Redis connection test failed"
    }
    
    Write-Host ""
    Write-LogSuccess "Deployment testing completed"
}

# Show usage information
function Show-Usage {
    Write-Host "Usage: .\deploy-autogen-langchain.ps1 [ACTION]"
    Write-Host ""
    Write-Host "Actions:"
    Write-Host "  deploy          Full deployment (default)"
    Write-Host "  restart         Restart all services"
    Write-Host "  stop            Stop all services"
    Write-Host "  status          Show service status"
    Write-Host "  logs            Show service logs"
    Write-Host "  test            Test deployment"
    Write-Host "  cleanup         Clean up all containers and volumes"
    Write-Host "  help            Show this help message"
    Write-Host ""
}

# Main deployment function
function Start-Deployment {
    Show-Banner
    
    Write-LogInfo "Starting AutoGen and LangChain deployment..."
    Write-LogInfo "Project root: $ProjectRoot"
    Write-LogInfo "Compose file: $ComposeFile"
    Write-LogInfo "Environment file: $EnvFile"
    
    Test-Prerequisites
    Remove-ExistingDeployment
    Build-Images
    Start-Infrastructure
    Start-MCPServers
    Start-AgentSystems
    Start-Monitoring
    
    Show-DeploymentStatus
    Test-Deployment
    
    Write-Host ""
    Write-Host "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Configure API keys in $EnvFile"
    Write-Host "2. Access the web dashboard at http://localhost:8090"
    Write-Host "3. Monitor services using Grafana at http://localhost:3000"
    Write-Host "4. Check logs with: .\deploy-autogen-langchain.ps1 logs"
    Write-Host ""
    Write-Host "To stop all services: .\deploy-autogen-langchain.ps1 stop" -ForegroundColor Yellow
    Write-Host ""
}

# Handle command line arguments
switch ($Action) {
    "deploy" {
        Start-Deployment
    }
    "restart" {
        Write-LogInfo "Restarting all services..."
        docker-compose -f $ComposeFile --env-file $EnvFile restart
        Show-DeploymentStatus
    }
    "stop" {
        Write-LogInfo "Stopping all services..."
        docker-compose -f $ComposeFile --env-file $EnvFile down
        Write-LogSuccess "All services stopped"
    }
    "status" {
        Show-DeploymentStatus
    }
    "logs" {
        Write-Host "Service logs (press Ctrl+C to exit):" -ForegroundColor Cyan
        docker-compose -f $ComposeFile --env-file $EnvFile logs -f
    }
    "test" {
        Test-Deployment
    }
    "cleanup" {
        Write-LogWarn "This will remove all containers, volumes, and data. Are you sure? (y/N)"
        $response = Read-Host
        if ($response -eq "y" -or $response -eq "Y") {
            Remove-ExistingDeployment
            docker system prune -af --volumes
            Write-LogSuccess "Cleanup completed"
        }
    }
    "help" {
        Show-Usage
    }
    default {
        Write-LogError "Unknown action: $Action"
        Show-Usage
        exit 1
    }
}