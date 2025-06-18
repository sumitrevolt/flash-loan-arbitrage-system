#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Enhanced LangChain Flash Loan System Runner
.DESCRIPTION
    Runs the most advanced multi-agent system with quantum-inspired decision making,
    swarm intelligence, deep learning, and hierarchical agent architecture.
.PARAMETER Mode
    Execution mode: dev, staging, or production
.PARAMETER GPUs
    Number of GPUs to use (default: all available)
.PARAMETER Clean
    Clean start - removes all containers and volumes
#>

param(
    [ValidateSet("dev", "staging", "production")]
    [string]$Mode = "dev",
    
    [int]$GPUs = -1,
    
    [switch]$Clean,
    
    [switch]$NoBuild,
    
    [switch]$Monitoring
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Configuration
$ProjectName = "flashloan-enhanced"
$ComposeFile = "docker/docker-compose.advanced-langchain.yml"
$EnvFile = ".env"

# Color functions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Show-Banner {
    Write-ColorOutput Cyan @"

╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🚀 ENHANCED LANGCHAIN FLASH LOAN SYSTEM 🚀                  ║
║                                                                  ║
║     Quantum-Inspired • Swarm Intelligence • Deep Learning       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

"@
}

function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
    
    # Check Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker is not installed or not in PATH"
    }
    
    # Check Docker Compose
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        throw "Docker Compose is not installed or not in PATH"
    }
    
    # Check NVIDIA Docker (if GPUs requested)
    if ($GPUs -ne 0) {
        docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "NVIDIA Docker runtime not available. Running without GPU support."
            $script:GPUs = 0
        } else {
            Write-Host "✅ NVIDIA Docker runtime detected" -ForegroundColor Green
        }
    }
    
    # Check environment file
    if (-not (Test-Path $EnvFile)) {
        Write-Warning "Environment file not found. Creating template..."
        Create-EnvFile
    }
    
    Write-Host "✅ All prerequisites met" -ForegroundColor Green
}

function Create-EnvFile {
    $envContent = @"
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here

# Database Configuration
POSTGRES_PASSWORD=secure_postgres_password
RABBITMQ_PASSWORD=secure_rabbitmq_password

# Grafana Configuration
GRAFANA_PASSWORD=secure_grafana_password

# Flash Loan Configuration
MAX_GAS_PRICE=500
SLIPPAGE_TOLERANCE=0.005

# Agent Configuration
AGENT_SPECIALIZATION=general
"@
    
    $envContent | Out-File -FilePath $EnvFile -Encoding UTF8
    Write-Host "📝 Created .env template. Please update with your credentials." -ForegroundColor Yellow
}

function Start-Infrastructure {
    Write-Host "`n🏗️  Starting infrastructure services..." -ForegroundColor Yellow
    
    $services = @(
        "redis-cluster",
        "postgres-master",
        "rabbitmq",
        "etcd"
    )
    
    if ($Monitoring) {
        $services += @("prometheus", "grafana", "jaeger")
    }
    
    $buildFlag = if ($NoBuild) { "" } else { "--build" }
    
    docker-compose -f $ComposeFile -p $ProjectName up -d $buildFlag $services
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Infrastructure services started" -ForegroundColor Green
        
        # Wait for services to be healthy
        Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Check service health
        foreach ($service in $services) {
            $health = docker inspect --format='{{.State.Health.Status}}' "${ProjectName}_${service}_1" 2>$null
            if ($health -eq "healthy") {
                Write-Host "  ✅ $service is healthy" -ForegroundColor Green
            } else {
                Write-Warning "  ⚠️  $service health check pending"
            }
        }
    } else {
        throw "Failed to start infrastructure services"
    }
}

function Start-CoreServices {
    Write-Host "`n🧠 Starting core AI services..." -ForegroundColor Yellow
    
    $services = @(
        "langchain-orchestrator",
        "quantum-decision-engine",
        "swarm-coordinator",
        "market-predictor",
        "risk-manager"
    )
    
    docker-compose -f $ComposeFile -p $ProjectName up -d $services
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Core AI services started" -ForegroundColor Green
    } else {
        throw "Failed to start core services"
    }
}

function Start-AgentSwarm {
    Write-Host "`n🐝 Deploying agent swarm..." -ForegroundColor Yellow
    
    # Start swarm agents
    docker-compose -f $ComposeFile -p $ProjectName up -d swarm-agent
    
    # Start hierarchical agents
    $agents = @(
        "market-intelligence-director",
        "risk-management-chief",
        "dex-analyst-1",
        "mev-protection-agent"
    )
    
    docker-compose -f $ComposeFile -p $ProjectName up -d $agents
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Agent swarm deployed" -ForegroundColor Green
        
        # Show swarm status
        $swarmCount = docker ps --filter "name=${ProjectName}_swarm-agent" -q | Measure-Object | Select-Object -ExpandProperty Count
        Write-Host "  📊 $swarmCount swarm agents active" -ForegroundColor Cyan
    } else {
        throw "Failed to deploy agent swarm"
    }
}

function Start-ExecutionLayer {
    Write-Host "`n⚡ Starting high-frequency execution layer..." -ForegroundColor Yellow
    
    docker-compose -f $ComposeFile -p $ProjectName up -d hft-executor
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Execution layer started" -ForegroundColor Green
    } else {
        throw "Failed to start execution layer"
    }
}

function Show-SystemStatus {
    Write-Host "`n📊 System Status:" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor Cyan
    
    # Count running containers
    $totalContainers = docker ps --filter "label=com.docker.compose.project=$ProjectName" -q | Measure-Object | Select-Object -ExpandProperty Count
    Write-Host "  🐳 Total containers: $totalContainers" -ForegroundColor White
    
    # Show key endpoints
    Write-Host "`n🌐 Service Endpoints:" -ForegroundColor Cyan
    Write-Host "  • Orchestrator API: http://localhost:8000" -ForegroundColor White
    Write-Host "  • Orchestrator Metrics: http://localhost:8001" -ForegroundColor White
    
    if ($Monitoring) {
        Write-Host "  • Grafana Dashboard: http://localhost:3000 (admin/admin)" -ForegroundColor White
        Write-Host "  • Prometheus: http://localhost:9090" -ForegroundColor White
        Write-Host "  • Jaeger Tracing: http://localhost:16686" -ForegroundColor White
    }
    
    Write-Host "  • RabbitMQ Management: http://localhost:15672" -ForegroundColor White
    
    # Show resource usage
    Write-Host "`n💻 Resource Usage:" -ForegroundColor Cyan
    $stats = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | 
             Where-Object { $_ -match $ProjectName }
    $stats | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
}

function Watch-Logs {
    Write-Host "`n📜 Streaming logs (Ctrl+C to stop)..." -ForegroundColor Yellow
    docker-compose -f $ComposeFile -p $ProjectName logs -f --tail=100
}

function Stop-System {
    Write-Host "`n🛑 Stopping system..." -ForegroundColor Yellow
    
    docker-compose -f $ComposeFile -p $ProjectName down
    
    if ($Clean) {
        Write-Host "🧹 Cleaning volumes..." -ForegroundColor Yellow
        docker-compose -f $ComposeFile -p $ProjectName down -v
    }
    
    Write-Host "✅ System stopped" -ForegroundColor Green
}

# Main execution
try {
    Show-Banner
    Test-Prerequisites
    
    if ($Clean) {
        Stop-System
    }
    
    # Set GPU environment variable
    if ($GPUs -gt 0) {
        $env:CUDA_VISIBLE_DEVICES = (0..($GPUs-1)) -join ","
        Write-Host "🎮 Using GPUs: $env:CUDA_VISIBLE_DEVICES" -ForegroundColor Cyan
    }
    
    # Start services in order
    Start-Infrastructure
    Start-CoreServices
    Start-AgentSwarm
    Start-ExecutionLayer
    
    # Show status
    Show-SystemStatus
    
    # Offer to watch logs
    $response = Read-Host "`nWould you like to watch the logs? (y/n)"
    if ($response -eq 'y') {
        Watch-Logs
    }
    
} catch {
    Write-Error "❌ Error: $_"
    exit 1
}

Write-Host "`n✨ Enhanced LangChain system is running!" -ForegroundColor Green
Write-Host "📝 Run 'docker-compose -f $ComposeFile logs -f' to view logs" -ForegroundColor Cyan
