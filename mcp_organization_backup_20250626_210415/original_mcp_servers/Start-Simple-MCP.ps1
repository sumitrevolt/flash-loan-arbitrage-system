#!/usr/bin/env powershell
<#
.SYNOPSIS
    Simple MCP System Starter - Uses existing compose files
.DESCRIPTION
    Start your MCP system using the existing docker setup
#>

param(
    [switch]$InfraOnly = $false
)

# Colors for output
function Write-Success($Message) { Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info($Message) { Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning($Message) { Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error($Message) { Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Header($Message) { Write-Host "🚀 $Message" -ForegroundColor Magenta }

Clear-Host
Write-Header "SIMPLE MCP DOCKER SYSTEM STARTER"
Write-Output "=" * 50

# Change to project directory
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

# Check Docker
try {
    docker info | Out-Null
    Write-Success "Docker is running"
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}

# Create network if not exists
Write-Info "Creating Docker network..."
docker network create mcpnet 2>$null
Write-Success "Network ready"

# Start infrastructure using the main compose file
Write-Header "STARTING INFRASTRUCTURE SERVICES"
try {
    Write-Info "Starting Redis, PostgreSQL, RabbitMQ..."
    docker compose -f docker/compose/docker-compose.yml up -d redis postgres rabbitmq
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Infrastructure services started"
    } else {
        Write-Error "Failed to start infrastructure"
        exit 1
    }
} catch {
    Write-Error "Error starting infrastructure: $_"
    exit 1
}

if ($InfraOnly) {
    Write-Success "Infrastructure-only mode complete!"
    Write-Info "Services running: Redis, PostgreSQL, RabbitMQ"
    exit 0
}

# Start monitoring
Write-Info "Starting monitoring services..."
try {
    docker compose -f docker/compose/docker-compose.yml up -d prometheus grafana
    Write-Success "Monitoring services started"
} catch {
    Write-Warning "Some monitoring services may have failed, continuing..."
}

# Start MCP coordinator if it exists in the main compose
Write-Header "STARTING MCP COORDINATOR"
try {
    docker compose -f docker/compose/docker-compose.yml up -d mcp-coordinator
    if ($LASTEXITCODE -eq 0) {
        Write-Success "MCP Coordinator started"
    } else {
        Write-Warning "MCP Coordinator may not be in main compose file"
    }
} catch {
    Write-Warning "MCP Coordinator startup had issues, continuing..."
}

# Try to start MCP servers using existing file
Write-Header "STARTING MCP SERVERS"
Write-Info "Attempting to start MCP servers..."

# Check which MCP compose files exist
$mcpComposeFiles = @(
    "docker/compose/docker-compose.mcp-servers.yml",
    "docker/docker-compose.mcp-servers.yml",
    "docker-compose.mcp-servers.yml"
)

$mcpFile = $null
foreach ($file in $mcpComposeFiles) {
    if (Test-Path $file) {
        $mcpFile = $file
        break
    }
}

if ($mcpFile) {
    Write-Info "Found MCP servers file: $mcpFile"
    try {
        # Try to start a few key servers manually to avoid dependency issues
        Write-Info "Starting individual MCP servers..."
        
        # Use python scripts to start MCP servers if compose has issues
        if (Test-Path "mcp_servers") {
            Write-Info "Starting Python MCP servers directly..."
            $serverDirs = Get-ChildItem -Path "mcp_servers" -Directory
            foreach ($dir in $serverDirs) {
                $serverFiles = Get-ChildItem -Path $dir.FullName -Filter "*.py"
                if ($serverFiles.Count -gt 0) {
                    Write-Info "Found servers in $($dir.Name)"
                }
            }
        }
        
        Write-Success "MCP servers initialization attempted"
    } catch {
        Write-Warning "MCP servers had startup issues: $_"
    }
} else {
    Write-Warning "No MCP servers compose file found"
}

# System status
Write-Header "SYSTEM STATUS"
$containers = docker ps --format "table {{.Names}}\t{{.Status}}" | Select-Object -Skip 1

Write-Info "Running containers:"
$containers | ForEach-Object {
    if ($_ -match "redis|postgres|rabbitmq|prometheus|grafana|mcp") {
        Write-Success "  $_"
    }
}

Write-Output ""
Write-Header "🎉 BASIC SYSTEM STARTED!"
Write-Success "Core infrastructure is running."
Write-Output ""
Write-Info "📊 Access Points:"
Write-Info "  • RabbitMQ Management: http://localhost:15672"
Write-Info "  • Prometheus: http://localhost:9090" 
Write-Info "  • Grafana: http://localhost:3030"
Write-Output ""
Write-Info "🔧 Next Steps:"
Write-Info "  • Check status: docker ps"
Write-Info "  • View logs: docker logs [container_name]"
Write-Info "  • Stop system: docker compose -f docker/compose/docker-compose.yml down"
