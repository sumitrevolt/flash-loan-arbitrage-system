# Multi-MCP Server Container Setup for Windows
# PowerShell script to deploy the GitHub Pro enhanced system

Write-Host "🚀 Multi-MCP Server Container Setup" -ForegroundColor Green
Write-Host "Following MULTI_MCP_SERVER_CONTAINER_PLAN.md" -ForegroundColor Blue

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  Consider running as Administrator for better Docker access" -ForegroundColor Yellow
}

# Set execution policy for current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Change to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "📍 Working directory: $scriptPath" -ForegroundColor Cyan

# Check prerequisites
Write-Host "`n🔍 Checking prerequisites..." -ForegroundColor Yellow

$prerequisites = @{
    "Docker" = "docker --version"
    "Docker Compose" = "docker-compose --version"
    "Python" = "python --version"
    "Git" = "git --version"
}

$missingPrereqs = @()

foreach ($tool in $prerequisites.Keys) {
    try {
        $output = Invoke-Expression $prerequisites[$tool] 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $tool`: $output" -ForegroundColor Green
        } else {
            $missingPrereqs += $tool
        }
    } catch {
        $missingPrereqs += $tool
    }
}

if ($missingPrereqs.Count -gt 0) {
    Write-Host "❌ Missing prerequisites: $($missingPrereqs -join ', ')" -ForegroundColor Red
    Write-Host "Please install missing tools and run again." -ForegroundColor Red
    
    Write-Host "`n📋 Installation instructions:" -ForegroundColor Yellow
    Write-Host "Docker Desktop: https://docs.docker.com/desktop/install/windows/" -ForegroundColor Cyan
    Write-Host "Python: https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "Git: https://git-scm.com/download/win" -ForegroundColor Cyan
    
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "`n⚠️  .env file not found. Creating template..." -ForegroundColor Yellow
    
    $envContent = @"
# Multi-MCP Server Container Environment Variables
# Please update these values with your actual credentials

# GitHub Integration
GITHUB_TOKEN=your_github_token_here
COPILOT_API_KEY=your_copilot_api_key_here

# Database Configuration
POSTGRES_PASSWORD=your_secure_postgres_password
POSTGRES_USER=flashloan_user
POSTGRES_DB=flashloan

# Redis Configuration
REDIS_PASSWORD=your_secure_redis_password

# InfluxDB Configuration
INFLUX_PASSWORD=your_secure_influx_password

# Grafana Configuration
GRAFANA_PASSWORD=your_secure_grafana_password

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Repository Configuration (update with your repo)
GITHUB_REPO_OWNER=your_github_username
GITHUB_REPO_NAME=flash-loan
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "📝 Please update .env file with your actual values and run the script again." -ForegroundColor Red
    Write-Host "Opening .env file in notepad..." -ForegroundColor Yellow
    
    Start-Process notepad ".env"
    
    Write-Host "`n💡 Required API keys:" -ForegroundColor Yellow
    Write-Host "- GitHub Token: https://github.com/settings/tokens" -ForegroundColor Cyan
    Write-Host "- OpenAI API Key: https://platform.openai.com/api-keys" -ForegroundColor Cyan
    
    exit 1
}

# Check if environment variables are updated
$envContent = Get-Content ".env" -Raw
if ($envContent -match "your_.*_here") {
    Write-Host "❌ Please update .env file with your actual values" -ForegroundColor Red
    Write-Host "Found placeholder values that need to be updated." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Environment variables configured" -ForegroundColor Green

# Run Python setup script
Write-Host "`n🐍 Running Python setup script..." -ForegroundColor Yellow

try {
    python setup_multi_mcp_containers.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 Setup completed successfully!" -ForegroundColor Green
        
        # Display service endpoints
        Write-Host "`n📊 Service Endpoints:" -ForegroundColor Yellow
        Write-Host "Orchestrator:     http://localhost:8080" -ForegroundColor Cyan
        Write-Host "MCP Servers:      http://localhost:8000-8030" -ForegroundColor Cyan
        Write-Host "AI Agents:        http://localhost:8001" -ForegroundColor Cyan
        Write-Host "Prometheus:       http://localhost:9090" -ForegroundColor Cyan
        Write-Host "Grafana:          http://localhost:3000" -ForegroundColor Cyan
        Write-Host "InfluxDB:         http://localhost:8086" -ForegroundColor Cyan
        
        # Ask if user wants to open Grafana
        $openGrafana = Read-Host "`nWould you like to open Grafana dashboard? (y/n)"
        if ($openGrafana -eq 'y' -or $openGrafana -eq 'Y') {
            Start-Process "http://localhost:3000"
        }
        
        Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
        Write-Host "1. Configure GitHub repository settings" -ForegroundColor White
        Write-Host "2. Set up branch protection rules" -ForegroundColor White
        Write-Host "3. Add repository secrets in GitHub" -ForegroundColor White
        Write-Host "4. Monitor system performance in Grafana" -ForegroundColor White
        Write-Host "5. Review setup_report.json for details" -ForegroundColor White
        
    } else {
        Write-Host "`n❌ Setup failed. Check the logs above for details." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`n❌ Error running setup script: $_" -ForegroundColor Red
    exit 1
}

# Optional: Show container status
$showStatus = Read-Host "`nWould you like to see Docker container status? (y/n)"
if ($showStatus -eq 'y' -or $showStatus -eq 'Y') {
    Write-Host "`n🐳 Docker Container Status:" -ForegroundColor Yellow
    docker-compose -f docker-compose.github-enhanced.yml ps
}

Write-Host "`n✨ Multi-MCP Server Container system is now running!" -ForegroundColor Green
Write-Host "Happy trading! 🚀" -ForegroundColor Yellow
