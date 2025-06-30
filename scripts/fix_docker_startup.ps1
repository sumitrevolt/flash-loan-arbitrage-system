#!/usr/bin/env pwsh
# Flash Loan Docker Compose Fix and Startup Script

Write-Host "Flash Loan Docker Compose Fix and Startup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed"
    }
    Write-Host "Docker is available" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running or not installed" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker compose down --remove-orphans 2>$null

# Remove any problematic containers
Write-Host "Cleaning up old containers..." -ForegroundColor Yellow
docker container rm -f flash-loan-web3-node 2>$null
docker container rm -f flash-loan-postgres 2>$null
docker container rm -f flash-loan-redis 2>$null
docker container rm -f flash-loan-langchain 2>$null
docker container rm -f flash-loan-autogen 2>$null

# Clean up volumes if they exist
Write-Host "Cleaning up volumes..." -ForegroundColor Yellow
docker volume rm flashloan_postgres_data 2>$null
docker volume rm flashloan_redis_data 2>$null
docker volume rm flashloan_langchain_data 2>$null
docker volume rm flashloan_autogen_data 2>$null

# Create directories if they don't exist
Write-Host "Creating necessary directories..." -ForegroundColor Yellow
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force
}
if (!(Test-Path "deployment/docker/langchain")) {
    New-Item -ItemType Directory -Path "deployment/docker/langchain" -Force
}
if (!(Test-Path "deployment/docker/autogen")) {
    New-Item -ItemType Directory -Path "deployment/docker/autogen" -Force
}

# Copy environment file
Write-Host "Setting up environment..." -ForegroundColor Yellow
if (Test-Path "docker-compose.env") {
    Copy-Item "docker-compose.env" ".env" -Force
    Write-Host "Environment file configured" -ForegroundColor Green
} else {
    Write-Host "Creating default environment file..." -ForegroundColor Yellow
    $envContent = @"
# Docker Compose Environment Variables
POSTGRES_DB=flash_loan_db
POSTGRES_USER=flash_loan_user
POSTGRES_PASSWORD=flash_loan_secure_2025
POSTGRES_PORT=5432
REDIS_PASSWORD=flash_loan_redis_2025
REDIS_PORT=6379
WEB3_NODE_PORT=8545
WEB3_WS_PORT=8546
WEB3_NODE_LOG_LEVEL=3
LOG_LEVEL=INFO
AUTOGEN_MAX_AGENTS=10
OPENAI_API_KEY=demo_key
ANTHROPIC_API_KEY=demo_key
GITHUB_TOKEN=
ENABLE_REAL_EXECUTION=false
ENABLE_TESTING=true
ENABLE_MONITORING=true
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
}

# Start only the infrastructure services first
Write-Host "Starting infrastructure services..." -ForegroundColor Cyan
Write-Host "Starting PostgreSQL and Redis..." -ForegroundColor Yellow

# Start postgres and redis first
docker compose up -d postgres redis

# Wait for postgres and redis to be healthy
Write-Host "Waiting for database services to be ready..." -ForegroundColor Yellow
$maxWait = 60
$waited = 0
while ($waited -lt $maxWait) {
    $postgresHealthy = docker inspect --format='{{.State.Health.Status}}' flash-loan-postgres 2>$null
    $redisHealthy = docker inspect --format='{{.State.Health.Status}}' flash-loan-redis 2>$null
    
    if ($postgresHealthy -eq "healthy" -and $redisHealthy -eq "healthy") {
        Write-Host "Database services are healthy" -ForegroundColor Green
        break
    }
    
    Start-Sleep -Seconds 5
    $waited += 5
    Write-Host "Still waiting... ($waited/$maxWait seconds)" -ForegroundColor Yellow
}

if ($waited -ge $maxWait) {
    Write-Host "Database services failed to start properly" -ForegroundColor Red
    Write-Host "Checking logs..." -ForegroundColor Yellow
    docker compose logs postgres
    docker compose logs redis
    exit 1
}

# Start the web3 node
Write-Host "Starting Web3 development node..." -ForegroundColor Cyan
docker compose up -d web3-node

# Wait for web3-node to be healthy
Write-Host "Waiting for Web3 node to be ready..." -ForegroundColor Yellow
$maxWait = 90
$waited = 0
while ($waited -lt $maxWait) {
    $web3Healthy = docker inspect --format='{{.State.Health.Status}}' flash-loan-web3-node 2>$null
    
    if ($web3Healthy -eq "healthy") {
        Write-Host "Web3 node is healthy" -ForegroundColor Green
        break
    }
    
    Start-Sleep -Seconds 5
    $waited += 5
    Write-Host "Still waiting for Web3 node... ($waited/$maxWait seconds)" -ForegroundColor Yellow
}

if ($waited -ge $maxWait) {
    Write-Host "Web3 node failed to start properly" -ForegroundColor Red
    Write-Host "Checking logs..." -ForegroundColor Yellow
    docker compose logs web3-node
    Write-Host ""
    Write-Host "Troubleshooting tip: The Web3 node might need more time to initialize" -ForegroundColor Yellow
    Write-Host "You can continue starting other services while it initializes..." -ForegroundColor Yellow
}

# Show current status
Write-Host ""
Write-Host "Current container status:" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "Infrastructure setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Check that all containers are healthy: docker compose ps" -ForegroundColor White
Write-Host "2. View logs if needed: docker compose logs [service-name]" -ForegroundColor White
Write-Host "3. To start application services: docker compose up -d" -ForegroundColor White
Write-Host "4. To test Web3 connection: Use the test command in the troubleshooting guide" -ForegroundColor White
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "- Web3 RPC: http://localhost:8545" -ForegroundColor White
Write-Host "- Web3 WebSocket: ws://localhost:8546" -ForegroundColor White
Write-Host "- PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "- Redis: localhost:6379" -ForegroundColor White 