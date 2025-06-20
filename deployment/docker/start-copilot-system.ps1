# GitHub Copilot Pro LangChain System Startup Script (PowerShell)
# ===============================================================

Write-Host "🚀 Starting GitHub Copilot Pro LangChain Multi-Agent System..." -ForegroundColor Green

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "⚠️  No .env file found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host "📝 Please edit .env file with your API keys before continuing." -ForegroundColor Yellow
    Write-Host "   Required keys: OPENAI_API_KEY, GITHUB_TOKEN, GITHUB_COPILOT_API_KEY" -ForegroundColor Yellow
    exit 1
}

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#]*[^=]+)=(.*)$") {
            $name = $matches[1]
            $value = $matches[2]
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Check for required environment variables
Write-Host "🔍 Checking environment variables..." -ForegroundColor Blue

$requiredVars = @("OPENAI_API_KEY", "GITHUB_TOKEN")
$missingVars = @()

foreach ($var in $requiredVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing required environment variables:" -ForegroundColor Red
    $missingVars | ForEach-Object { Write-Host "   $_" -ForegroundColor Red }
    Write-Host "   Please set these in your .env file" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Environment variables validated" -ForegroundColor Green

# Check Docker installation
try {
    docker --version | Out-Null
    Write-Host "✅ Docker installation verified" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker is not installed or not in PATH. Please install Docker first." -ForegroundColor Red
    exit 1
}

try {
    docker compose version | Out-Null
    Write-Host "✅ Docker Compose installation verified" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker Compose is not installed or not in PATH. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Build and start containers
Write-Host "🏗️  Building and starting containers..." -ForegroundColor Blue
docker compose -f docker-compose.langchain-enhanced.yml down --remove-orphans
docker compose -f docker-compose.langchain-enhanced.yml build --no-cache
docker compose -f docker-compose.langchain-enhanced.yml up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Blue
Start-Sleep -Seconds 30

# Health checks
Write-Host "🏥 Performing health checks..." -ForegroundColor Blue

$services = @{
    "Redis" = 6379
    "PostgreSQL" = 5432
    "RabbitMQ" = 15672
    "LangChain Coordinator" = 8000
}

foreach ($service in $services.GetEnumerator()) {
    Write-Host "   Checking $($service.Key) on port $($service.Value)..." -ForegroundColor Gray
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $service.Value)
        $connection.Close()
        Write-Host "   ✅ $($service.Key) is ready" -ForegroundColor Green
    }
    catch {
        Write-Host "   ❌ $($service.Key) is not responding" -ForegroundColor Red
    }
}

# Test GitHub Copilot Pro agent
Write-Host "🤖 Testing GitHub Copilot Pro agent..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ GitHub Copilot Pro agent is ready" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  GitHub Copilot Pro agent may not be fully ready (HTTP $($response.StatusCode))" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  GitHub Copilot Pro agent is not responding" -ForegroundColor Yellow
}

# Display service URLs
Write-Host ""
Write-Host "🌐 Service URLs:" -ForegroundColor Cyan
Write-Host "   Main API:           http://localhost:8000" -ForegroundColor White
Write-Host "   Agent Coordination: http://localhost:8001" -ForegroundColor White
Write-Host "   RAG Service:        http://localhost:8003" -ForegroundColor White
Write-Host "   Code Interpreter:   http://localhost:8004" -ForegroundColor White
Write-Host "   Grafana Dashboard:  http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host "   RabbitMQ Admin:     http://localhost:15672 (flash_loan_mq/flash_loan_mq_2025)" -ForegroundColor White
Write-Host "   Prometheus:         http://localhost:9090" -ForegroundColor White
Write-Host "   Health Check:       http://localhost:8080/health" -ForegroundColor White
Write-Host ""

Write-Host "🎉 GitHub Copilot Pro LangChain System is running!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Quick Start Guide:" -ForegroundColor Cyan
Write-Host "   1. Test the system:"
Write-Host "      Invoke-WebRequest -Uri 'http://localhost:8000/health'" -ForegroundColor Gray
Write-Host "   2. Generate code:"
Write-Host "      Invoke-RestMethod -Uri 'http://localhost:8000/api/agents/github_copilot' -Method POST -ContentType 'application/json' -Body '{\"action\":\"generate_code\",\"specification\":\"Flash loan contract\"}'" -ForegroundColor Gray
Write-Host "   3. Review code:"
Write-Host "      Invoke-RestMethod -Uri 'http://localhost:8000/api/agents/github_copilot' -Method POST -ContentType 'application/json' -Body '{\"action\":\"review_code\",\"code\":\"your_code_here\"}'" -ForegroundColor Gray
Write-Host "   4. View logs:"
Write-Host "      docker logs flash-loan-langchain-coordinator" -ForegroundColor Gray
Write-Host "   5. Stop system:"
Write-Host "      docker compose -f docker-compose.langchain-enhanced.yml down" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 For detailed documentation, see README_COPILOT.md" -ForegroundColor Cyan
