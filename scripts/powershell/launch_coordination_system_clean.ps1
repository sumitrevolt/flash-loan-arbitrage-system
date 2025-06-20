# PowerShell Script to Launch Complete MCP System
# Usage: .\launch_coordination_system.ps1

param(
    [string]$Action = "start",
    [string]$System = "self-healing",
    [switch]$Help
)

function Show-Help {
    Write-Host @"
Complete MCP System Launcher
============================

Usage: .\launch_coordination_system.ps1 [OPTIONS]

Options:
  -Action <action>    Action to perform (start, stop, health, info, test)
  -System <system>    System type (test, full, self-healing, complete, test-complete)
  -Help              Show this help message

Actions:
  start              Start the coordination system (default)
  stop               Stop all services
  health             Check system health
  info               Show system information and URLs
  logs               Show system logs
  restart            Restart the system
  test               Run system tests

System Types:
  test               Start minimal test system (5 MCP servers)
  full               Start complete system with all 81 MCP servers
  self-healing       Start self-healing system (recommended)
  complete           Start complete system with all 81 MCP servers + self-healing
  test-complete      Start test system with all agents but only core MCP servers

Examples:
  .\launch_coordination_system.ps1
  .\launch_coordination_system.ps1 -Action test
  .\launch_coordination_system.ps1 -System complete
  .\launch_coordination_system.ps1 -Action stop
  .\launch_coordination_system.ps1 -Action health

"@
}

function Get-ComposeFile {
    param([string]$SystemType)
    
    switch ($SystemType) {
        "test" { return "docker\docker-compose-test.yml" }
        "full" { return "docker\docker-compose-complete.yml" }
        "self-healing" { return "docker\docker-compose-self-healing.yml" }
        "complete" { return "docker\docker-compose-complete.yml" }
        "test-complete" { return "docker\docker-compose-test-complete.yml" }
        default { return "docker\docker-compose-self-healing.yml" }
    }
}

function Start-System {
    param([string]$SystemType)
    
    $composeFile = Get-ComposeFile $SystemType
    Write-Host "Starting $SystemType system using $composeFile..." -ForegroundColor Green
    
    if ($SystemType -eq "test") {
        Write-Host "Running system tests first..." -ForegroundColor Yellow
        python test_complete_system.py --quick
        if ($LASTEXITCODE -ne 0) {
            Write-Host "System tests failed. Please check the logs." -ForegroundColor Red
            return
        }
    }
    
    if ($SystemType -eq "self-healing" -or $SystemType -eq "complete") {
        Write-Host "Starting comprehensive self-healing system..." -ForegroundColor Magenta
        python self_healing_coordination_launcher.py
    } else {
        # Start basic system
        docker compose -f $composeFile up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "System started successfully!" -ForegroundColor Green
            Show-SystemInfo
        } else {
            Write-Host "Failed to start system. Check Docker logs." -ForegroundColor Red
        }
    }
}

function Test-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Cyan
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "Docker not found. Please install Docker Desktop." -ForegroundColor Red
        return $false
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker compose version
        Write-Host "Docker Compose found: $composeVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "Docker Compose not found." -ForegroundColor Red
        return $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "Python not found. Some features may not work." -ForegroundColor Yellow
    }
    
    # Check required files
    $requiredFiles = @(
        "unified_mcp_config.json",
        "ai_agents_config.json"
    )
    
    $missingFiles = @()
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Host "Missing required files:" -ForegroundColor Red
        $missingFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        return $false
    }
    
    Write-Host "All prerequisites met!" -ForegroundColor Green
    return $true
}

function Stop-CoordinationSystem {
    Write-Host "Stopping coordination system..." -ForegroundColor Yellow
    
    $composeFiles = @(
        "docker\docker-compose-complete.yml",
        "docker\docker-compose-test-complete.yml", 
        "docker\docker-compose-self-healing.yml",
        "docker\docker-compose-test.yml"
    )
    
    foreach ($file in $composeFiles) {
        if (Test-Path $file) {
            Write-Host "Stopping services in $file" -ForegroundColor Gray
            docker compose -f $file down --remove-orphans
        }
    }
    
    Write-Host "All services stopped!" -ForegroundColor Green
}

function Get-SystemHealth {
    Write-Host "Checking system health..." -ForegroundColor Cyan
    
    $healthEndpoints = @(
        @{Name="Coordination System"; URL="http://localhost:8000/health"},
        @{Name="Self-Healing Agent"; URL="http://localhost:8300/health"},
        @{Name="Flash Loan Optimizer"; URL="http://localhost:9001/health"},
        @{Name="Price Feed Server"; URL="http://localhost:8091/health"}
    )
    
    foreach ($endpoint in $healthEndpoints) {
        try {
            $response = Invoke-RestMethod -Uri $endpoint.URL -Method GET -TimeoutSec 5
            if ($response.status -eq "healthy") {
                Write-Host "$($endpoint.Name): Healthy" -ForegroundColor Green
            } else {
                Write-Host "$($endpoint.Name): $($response.status)" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "$($endpoint.Name): Unreachable" -ForegroundColor Red
        }
    }
}

function Show-SystemInfo {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "                        COMPLETE MCP SYSTEM STARTED                            " -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Web Interfaces:" -ForegroundColor Cyan
    Write-Host "  Main Dashboard:        http://localhost:8080" -ForegroundColor White
    Write-Host "  Coordination API:      http://localhost:8000" -ForegroundColor White
    Write-Host "  Grafana Monitoring:    http://localhost:3000 (admin/admin)" -ForegroundColor White
    Write-Host "  RabbitMQ Management:   http://localhost:15672 (coordination/coordination_pass)" -ForegroundColor White
    Write-Host ""
    Write-Host "Infrastructure:" -ForegroundColor Cyan
    Write-Host "  Redis:                 localhost:6379" -ForegroundColor White
    Write-Host "  PostgreSQL:            localhost:5432" -ForegroundColor White
    Write-Host "  RabbitMQ:              localhost:5672" -ForegroundColor White
    Write-Host ""
    Write-Host "Example MCP Servers:" -ForegroundColor Cyan
    Write-Host "  Price Feed:            http://localhost:8091" -ForegroundColor White
    Write-Host "  Flash Loan:            http://localhost:8085" -ForegroundColor White
    Write-Host "  Arbitrage:             http://localhost:8073" -ForegroundColor White
    Write-Host ""
    Write-Host "AI Agents:" -ForegroundColor Cyan
    Write-Host "  Flash Loan Optimizer:  http://localhost:9001" -ForegroundColor White
    Write-Host "  Risk Manager:          http://localhost:9002" -ForegroundColor White
    Write-Host "  Arbitrage Detector:    http://localhost:9003" -ForegroundColor White
    Write-Host "  Self-Healing Agent:    http://localhost:8300" -ForegroundColor White
    Write-Host ""
    Write-Host "Monitoring:" -ForegroundColor Cyan
    Write-Host "  Prometheus:            http://localhost:9090" -ForegroundColor White
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Cyan
    Write-Host "  Health check:          .\launch_coordination_system.ps1 -Action health" -ForegroundColor White
    Write-Host "  Stop system:           .\launch_coordination_system.ps1 -Action stop" -ForegroundColor White
    Write-Host "  View logs:             .\launch_coordination_system.ps1 -Action logs" -ForegroundColor White
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "System is ready for coordination between 81 MCP servers and 11 AI agents!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Quick Test:" -ForegroundColor Yellow
    Write-Host "  Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method GET" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Open Dashboard: Start-Process 'http://localhost:8080'" -ForegroundColor Cyan
}

function Show-SystemLogs {
    Write-Host "Showing system logs..." -ForegroundColor Cyan
    $composeFile = Get-ComposeFile $System
    docker compose -f $composeFile logs -f --tail=50
}

function Restart-CoordinationSystem {
    Write-Host "Restarting coordination system..." -ForegroundColor Cyan
    Stop-CoordinationSystem
    Start-Sleep -Seconds 10
    Start-System $System
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

if (-not (Test-Prerequisites)) {
    Write-Host "Prerequisites not met. Please install required software." -ForegroundColor Red
    exit 1
}

switch ($Action.ToLower()) {
    "start" {
        Start-System $System
    }
    "stop" {
        Stop-CoordinationSystem
    }
    "health" {
        Get-SystemHealth
    }
    "info" {
        Show-SystemInfo
    }
    "logs" {
        Show-SystemLogs
    }
    "restart" {
        Restart-CoordinationSystem
    }
    "test" {
        Write-Host "Running comprehensive system tests..." -ForegroundColor Yellow
        python test_complete_system.py
    }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Show-Help
        exit 1
    }
}

Write-Host ""
Write-Host "Operation completed!" -ForegroundColor Green
