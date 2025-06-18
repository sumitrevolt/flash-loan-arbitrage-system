#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs the Complete Automated Flash Loan System with Full MCP Server and Agent Coordination
.DESCRIPTION
    This script orchestrates the entire flash loan ecosystem including:
    - All MCP servers (market data, flash loan, DEX aggregator, etc.)
    - Enhanced LangChain orchestrator with quantum decisions
    - Automated execution coordinator
    - Full monitoring stack
.PARAMETER Mode
    Deployment mode: dev, staging, or production
.PARAMETER AutoStart
    Automatically start executing opportunities
.PARAMETER ConfigPath
    Path to automation configuration file
#>

param(
    [ValidateSet("dev", "staging", "production")]
    [string]$Mode = "production",
    
    [switch]$AutoStart,
    
    [string]$ConfigPath = "config/automation.yaml",
    
    [switch]$Clean,
    
    [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Stop"

# Color output functions
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# ASCII Art Banner
$banner = @"
╔═══════════════════════════════════════════════════════════════════════╗
║          AUTOMATED FLASH LOAN MULTI-AGENT SYSTEM v2.0                 ║
║                                                                       ║
║  ⚡ Quantum Decision Engine    🤖 50+ AI Agents                       ║
║  🧠 Deep Learning Predictions  🚀 Automated Execution                 ║
║  🛡️  MEV Protection            📊 Real-time Analytics                ║
╚═══════════════════════════════════════════════════════════════════════╝
"@

Write-Host $banner -ForegroundColor Magenta

# Check prerequisites
Write-Info "`n[1/8] Checking prerequisites..."
$required = @{
    "Docker" = { docker --version }
    "Docker Compose" = { docker-compose --version }
    "Python" = { python --version }
    "Node.js" = { node --version }
}

$missingPrereqs = @()
foreach ($tool in $required.Keys) {
    try {
        & $required[$tool] | Out-Null
        Write-Success "  ✓ $tool installed"
    } catch {
        Write-Error "  ✗ $tool not found"
        $missingPrereqs += $tool
    }
}

if ($missingPrereqs.Count -gt 0) {
    Write-Error "`nMissing prerequisites: $($missingPrereqs -join ', ')"
    exit 1
}

# Clean if requested
if ($Clean) {
    Write-Warning "`n[CLEAN MODE] Removing all containers and data..."
    docker-compose -f docker/docker-compose.advanced-langchain.yml down -v --remove-orphans
    docker system prune -f
    Remove-Item -Path "data/*" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "logs/*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Success "Clean complete!"
}

# Environment setup
Write-Info "`n[2/8] Setting up environment..."
$env:COMPOSE_PROJECT_NAME = "flashloan_system"
$env:DEPLOYMENT_MODE = $Mode
$env:CONFIG_PATH = $ConfigPath

# Load environment variables
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
    Write-Success "  ✓ Environment variables loaded"
}

# Create necessary directories
$directories = @("data", "logs", "config", "models", "cache")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}
Write-Success "  ✓ Directories created"

# Start infrastructure services
Write-Info "`n[3/8] Starting infrastructure services..."
$infraServices = @("redis", "postgres", "rabbitmq", "elasticsearch")
docker-compose -f docker/docker-compose.advanced-langchain.yml up -d $infraServices

# Wait for infrastructure
Write-Info "  Waiting for infrastructure to be ready..."
$maxRetries = 30
$retries = 0
while ($retries -lt $maxRetries) {
    $ready = $true
    
    # Check Redis
    try {
        docker exec flashloan_system_redis_1 redis-cli ping | Out-Null
    } catch {
        $ready = $false
    }
    
    # Check PostgreSQL
    try {
        docker exec flashloan_system_postgres_1 pg_isready | Out-Null
    } catch {
        $ready = $false
    }
    
    if ($ready) {
        Write-Success "  ✓ Infrastructure ready"
        break
    }
    
    $retries++
    Start-Sleep -Seconds 2
    Write-Host "." -NoNewline
}

if ($retries -eq $maxRetries) {
    Write-Error "  ✗ Infrastructure failed to start"
    exit 1
}

# Start monitoring stack
Write-Info "`n[4/8] Starting monitoring stack..."
$monitoringServices = @("prometheus", "grafana", "jaeger", "alertmanager")
docker-compose -f docker/docker-compose.advanced-langchain.yml up -d $monitoringServices
Write-Success "  ✓ Monitoring stack started"

# Start MCP servers
Write-Info "`n[5/8] Starting MCP servers..."
$mcpServers = @(
    "market-data-mcp",
    "flash-loan-mcp",
    "dex-aggregator-mcp",
    "risk-analyzer-mcp",
    "gas-optimizer-mcp",
    "mev-protector-mcp",
    "profit-calculator-mcp",
    "execution-engine-mcp"
)

foreach ($server in $mcpServers) {
    Write-Info "  Starting $server..."
    docker-compose -f docker/docker-compose.advanced-langchain.yml up -d $server
}
Write-Success "  ✓ All MCP servers started"

# Start quantum decision engine and ML services
Write-Info "`n[6/8] Starting advanced AI services..."
$aiServices = @(
    "quantum-decision-engine",
    "swarm-coordinator",
    "ml-training-node",
    "transformer-predictor"
)

foreach ($service in $aiServices) {
    Write-Info "  Starting $service..."
    docker-compose -f docker/docker-compose.advanced-langchain.yml up -d $service
}
Write-Success "  ✓ AI services started"

# Start LangChain agents
Write-Info "`n[7/8] Starting LangChain agent hierarchy..."
$agentServices = @(
    "market-intelligence-director",
    "risk-management-chief",
    "execution-commander",
    "profit-maximization-strategist"
)

foreach ($agent in $agentServices) {
    Write-Info "  Starting $agent..."
    docker-compose -f docker/docker-compose.advanced-langchain.yml up -d $agent
}

# Start agent squadrons
Write-Info "  Starting tactical and operational agents..."
docker-compose -f docker/docker-compose.advanced-langchain.yml up -d --scale dex-analysis-agent=5 --scale mev-protection-agent=3 --scale gas-optimization-agent=3
docker-compose -f docker/docker-compose.advanced-langchain.yml up -d --scale price-monitor-agent=10 --scale execution-agent=10 --scale risk-assessment-agent=5
Write-Success "  ✓ All agents deployed"

# Health check
if (-not $SkipHealthCheck) {
    Write-Info "`n[8/8] Performing system health check..."
    Start-Sleep -Seconds 10
    
    # Check all services
    $allServices = docker-compose -f docker/docker-compose.advanced-langchain.yml ps --format json | ConvertFrom-Json
    $healthyServices = $allServices | Where-Object { $_.State -eq "running" }
    
    Write-Info "  Total services: $($allServices.Count)"
    Write-Success "  Healthy services: $($healthyServices.Count)"
    
    if ($healthyServices.Count -lt $allServices.Count) {
        Write-Warning "  Some services are not healthy:"
        $unhealthy = $allServices | Where-Object { $_.State -ne "running" }
        foreach ($service in $unhealthy) {
            Write-Warning "    - $($service.Service): $($service.State)"
        }
    }
}

# Start automated execution coordinator
if ($AutoStart) {
    Write-Info "`n🚀 Starting Automated Execution Coordinator..."
    
    # Run in background
    $coordinatorJob = Start-Job -ScriptBlock {
        param($configPath)
        Set-Location $using:PWD
        python automated_execution_coordinator.py --config $configPath
    } -ArgumentList $ConfigPath
    
    Write-Success "  ✓ Automated execution started (Job ID: $($coordinatorJob.Id))"
    Write-Info "  Monitor execution: Receive-Job -Id $($coordinatorJob.Id) -Keep"
}

# Display access information
Write-Host "`n" -NoNewline
Write-Success "═══════════════════════════════════════════════════════════════════════"
Write-Success "🎉 SYSTEM SUCCESSFULLY DEPLOYED!"
Write-Success "═══════════════════════════════════════════════════════════════════════"

$endpoints = @"

📊 MONITORING & DASHBOARDS:
  • Grafana Dashboard:      http://localhost:3000     (admin/admin)
  • Prometheus Metrics:     http://localhost:9090
  • Jaeger Tracing:        http://localhost:16686
  • Alert Manager:         http://localhost:9093

🔧 API ENDPOINTS:
  • Orchestrator API:      http://localhost:8000/api
  • Execution Status:      http://localhost:8000/status
  • Health Check:          http://localhost:8000/health
  • Metrics:              http://localhost:8000/metrics

🤖 MCP SERVERS:
  • Market Data:          http://localhost:8100
  • Flash Loan:           http://localhost:8101
  • DEX Aggregator:       http://localhost:8102
  • Risk Analyzer:        http://localhost:8103
  • Gas Optimizer:        http://localhost:8104
  • MEV Protector:        http://localhost:8105
  • Profit Calculator:    http://localhost:8106
  • Execution Engine:     http://localhost:8107

📁 LOGS & DATA:
  • Application Logs:     ./logs/
  • Execution History:    ./data/executions/
  • Model Checkpoints:    ./models/
  • Redis Cache:          redis://localhost:6379

"@

Write-Host $endpoints -ForegroundColor Cyan

# Monitoring commands
Write-Info "USEFUL COMMANDS:"
Write-Host @"

# View logs for a specific service:
docker-compose -f docker/docker-compose.advanced-langchain.yml logs -f [service-name]

# Scale agents:
docker-compose -f docker/docker-compose.advanced-langchain.yml up -d --scale price-monitor-agent=20

# Stop system:
docker-compose -f docker/docker-compose.advanced-langchain.yml down

# View execution status:
curl http://localhost:8000/api/executions/status

# Submit opportunity manually:
curl -X POST http://localhost:8000/api/opportunities -H "Content-Type: application/json" -d '{...}'

# Export metrics:
curl http://localhost:8000/metrics

"@ -ForegroundColor Gray

if ($AutoStart) {
    Write-Success "`n🤖 AUTOMATED EXECUTION IS ACTIVE!"
    Write-Warning "The system is now autonomously scanning for and executing profitable opportunities."
} else {
    Write-Info "`n💡 TIP: Run with -AutoStart flag to begin automated execution"
}

Write-Host "`n" -NoNewline
