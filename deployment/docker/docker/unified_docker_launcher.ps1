#!/usr/bin/env powershell
<#
.SYNOPSIS
    Unified MCP Docker System Launcher
.DESCRIPTION
    Comprehensive Docker system launcher that combines functionality from multiple previous scripts.
    Supports multiple deployment modes: full, minimal, dev, optimized
.EXAMPLE
    .\unified_docker_launcher.ps1                    # Default full deployment
    .\unified_docker_launcher.ps1 -Mode minimal      # Minimal services only
    .\unified_docker_launcher.ps1 -Mode dev          # Development infrastructure
    .\unified_docker_launcher.ps1 -Mode optimized    # Optimized configuration
    .\unified_docker_launcher.ps1 -Clean -Rebuild    # Fresh rebuild
#>

param(
    [ValidateSet("full", "minimal", "dev", "optimized")]
    [string]$Mode = "full",
    [switch]$Clean = $false,
    [switch]$Rebuild = $false,
    [switch]$Quick = $false,
    [switch]$InfraOnly = $false,
    [switch]$ServersOnly = $false,
    [switch]$Monitoring = $false,
    [switch]$Detached = $true,
    [switch]$ShowLogs = $false
)

$ErrorActionPreference = "Continue"

# Enhanced output functions
function Write-ColorOutput($ForegroundColor, $Message) {
    $currentColor = $Host.UI.RawUI.ForegroundColor
    try {
        $Host.UI.RawUI.ForegroundColor = $ForegroundColor
        Write-Output $Message
    } finally {
        $Host.UI.RawUI.ForegroundColor = $currentColor
    }
}

function Write-Success($Message) { Write-ColorOutput "Green" "[SUCCESS] $Message" }
function Write-Info($Message) { Write-ColorOutput "Cyan" "[INFO] $Message" }
function Write-Warning($Message) { Write-ColorOutput "Yellow" "[WARNING] $Message" }
function Write-Error($Message) { Write-ColorOutput "Red" "[ERROR] $Message" }
function Write-Header($Message) { 
    Write-Output ""
    Write-ColorOutput "Magenta" ("=" * 70)
    Write-ColorOutput "Magenta" "  $Message"
    Write-ColorOutput "Magenta" ("=" * 70)
}

# Configuration for different modes
$ModeConfigs = @{
    "full" = @{
        Description = "Complete system with all 39 containers (6 infrastructure + 21 MCP servers + 10 agents + 2 services)"
        ComposeFiles = @("docker-compose.complete.yml")
        Services = @("all")
        HealthChecks = @("master-coordinator", "enhanced-coordinator", "token-scanner")
        Ports = @("3000", "3001", "3003", "8080", "9090", "3030", "15672")
    }
    "minimal" = @{
        Description = "Core services only - essential infrastructure and key MCP servers"
        ComposeFiles = @("docker-compose.complete.yml")
        Services = @("redis", "postgres", "rabbitmq", "mcp-master-coordinator", "mcp-execution", "mcp-risk-management", "mcp-monitoring", "agent-master-coordinator", "agent-execution", "agent-monitoring")
        HealthChecks = @("master-coordinator", "execution")
        Ports = @("3000", "3001", "3002", "9090", "15672")
    }
    "dev" = @{
        Description = "Development environment - infrastructure only for local development"
        ComposeFiles = @("docker-compose.complete.yml")
        Services = @("redis", "postgres", "rabbitmq", "etcd", "prometheus", "grafana", "nginx")
        HealthChecks = @("redis", "postgres", "rabbitmq")
        Ports = @("6379", "5432", "15672", "9090", "3030", "80")
    }
    "optimized" = @{
        Description = "Streamlined configuration with essential services for production"
        ComposeFiles = @("docker-compose.optimized.yml")
        Services = @("all")
        HealthChecks = @("coordinator", "arbitrage", "flash-loan", "risk", "dex")
        Ports = @("3000", "3001", "3002", "3003", "3004", "8080", "9090", "15672")
    }
}

Clear-Host
Write-Header "UNIFIED MCP DOCKER SYSTEM LAUNCHER"

# Display mode information
$currentConfig = $ModeConfigs[$Mode]
Write-Info "Deployment Mode: $Mode"
Write-Info "Description: $($currentConfig.Description)"
Write-Output ""

# Validate environment
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Docker
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed!"
        Write-Info "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    # Check Docker Compose
    if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose is not installed!"
        Write-Info "Please install Docker Compose"
        exit 1
    }
    
    # Check if Docker is running
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker is not running!"
            Write-Info "Please start Docker Desktop and try again"
            exit 1
        }
    } catch {
        Write-Error "Docker is not available!"
        exit 1
    }
    
    Write-Success "All prerequisites met"
}

# Set working directory
function Set-WorkingDirectory {
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptPath
    Set-Location $projectRoot
    Write-Info "Working directory: $(Get-Location)"
}

# Initialize required directories
function Initialize-Directories {
    Write-Info "Initializing directories..."
    
    $directories = @(
        "logs",
        "logs/nginx",
        "logs/coordinator",
        "logs/arbitrage", 
        "logs/flash-loan",
        "logs/risk",
        "logs/dex",
        "logs/dashboard",
        "logs/bot",
        "docker/compose/config",
        "docker/compose/backups",
        "docker/compose/logs",
        "docker/compose/sql",
        "docker/volumes/redis_data",
        "docker/volumes/postgres_data", 
        "docker/volumes/prometheus_data",
        "docker/volumes/grafana_data",
        "dashboard/public",
        "dashboard/src"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Info "  Created: $dir"
        }
    }
    
    Write-Success "Directories initialized"
}

# Setup environment configuration
function Initialize-Environment {
    Write-Info "Checking environment configuration..."
    
    # Check for .env file in multiple locations
    $envLocations = @(".env", "docker/.env", "docker/compose/.env")
    $envFound = $false
    
    foreach ($envPath in $envLocations) {
        if (Test-Path $envPath) {
            $envFound = $true
            Write-Info "Found .env file at: $envPath"
            break
        }
    }
    
    if (!$envFound) {
        # Try to create from example
        $examplePaths = @(".env.example", "docker/.env.example", "docker/compose/.env.example")
        $exampleFound = $false
        
        foreach ($examplePath in $examplePaths) {
            if (Test-Path $examplePath) {
                $targetPath = Split-Path $examplePath -Parent
                $targetPath = Join-Path $targetPath ".env"
                Copy-Item $examplePath $targetPath
                Write-Success "Created .env from $examplePath"
                $exampleFound = $true
                break
            }
        }
        
        if (!$exampleFound) {
            # Create default .env
            $defaultEnv = @"
# MCP System Configuration
NODE_ENV=production
REDIS_URL=redis://redis:6379
POSTGRES_URL=postgresql://postgres:mcp_password_2025@postgres:5432/mcp_coordination
RABBITMQ_URL=amqp://mcp_admin:mcp_secure_2025@rabbitmq:5672
TOTAL_AGENTS=10
MCP_LOG_LEVEL=info
DISCORD_BOT_TOKEN=your_discord_bot_token_here
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_ADMIN_PASSWORD=admin
"@
            Set-Content -Path ".env" -Value $defaultEnv -Encoding UTF8
            Write-Success "Created default .env file"
            Write-Warning "Please update .env with your actual values!"
        }
    }
    
    # Load environment variables
    if (Test-Path ".env") {
        Get-Content .env | ForEach-Object {
            if ($_ -match '^([^#][^=]+)=(.*)$') {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
    }
    
    Write-Success "Environment configured"
}

# Clean up existing containers
function Clear-ExistingContainers {
    if ($Clean -or $Rebuild) {
        Write-Info "Cleaning up existing containers..."
        
        # Get current config
        $config = $ModeConfigs[$Mode]
        
        # Stop and remove containers for each compose file
        foreach ($composeFile in $config.ComposeFiles) {
            $composePath = "docker/compose/$composeFile"
            if (Test-Path $composePath) {
                Write-Info "  Stopping services from $composeFile..."
                docker-compose -f $composePath down --volumes --remove-orphans 2>$null | Out-Null
            }
        }
        
        # Clean up MCP-related containers
        $mcpContainers = docker ps -a --format "{{.Names}}" | Where-Object { $_ -match "mcp-" -or $_ -match "agent-" }
        
        if ($mcpContainers) {
            Write-Info "  Removing $($mcpContainers.Count) MCP containers..."
            docker stop $mcpContainers 2>$null | Out-Null
            docker rm $mcpContainers 2>$null | Out-Null
        }
        
        # Clean volumes if rebuild
        if ($Rebuild) {
            Write-Info "  Cleaning up volumes and images..."
            docker volume prune -f | Out-Null
            docker system prune -f | Out-Null
        }
        
        Write-Success "Cleanup complete"
    }
}

# Build Docker images
function Build-DockerImages {
    if ($Rebuild -or (!$Quick)) {
        Write-Info "Building Docker images..."
        
        $config = $ModeConfigs[$Mode]
        
        foreach ($composeFile in $config.ComposeFiles) {
            $composePath = "docker/compose/$composeFile"
            if (Test-Path $composePath) {
                Write-Info "  Building images from $composeFile..."
                if ($Rebuild) {
                    docker-compose -f $composePath build --no-cache
                } else {
                    docker-compose -f $composePath build
                }
                
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "Failed to build images from $composeFile"
                    exit 1
                }
            }
        }
        
        Write-Success "Images built successfully"
    }
}

# Start services based on mode
function Start-Services {
    Write-Header "STARTING SERVICES - $($Mode.ToUpper()) MODE"
    
    $config = $ModeConfigs[$Mode]
    Write-Info $config.Description
    
    foreach ($composeFile in $config.ComposeFiles) {
        $composePath = "docker/compose/$composeFile"
        
        if (!(Test-Path $composePath)) {
            Write-Warning "Compose file not found: $composePath"
            continue
        }
        
        Write-Info "Starting services from $composeFile..."
        
        # Build compose command
        $composeArgs = @("-f", $composePath, "up")
        
        if ($Detached) {
            $composeArgs += "-d"
        }
        
        # Add specific services if not "all"
        if ($config.Services -ne @("all")) {
            $composeArgs += $config.Services
        }
        
        # Execute docker-compose
        docker-compose @composeArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to start services from $composeFile"
            exit 1
        }
    }
    
    # Start monitoring if requested
    if ($Monitoring -and $Mode -ne "dev") {
        Write-Info "Starting additional monitoring services..."
        docker-compose -f docker/compose/docker-compose.complete.yml up -d prometheus grafana
    }
    
    Write-Success "Services started successfully"
}

# Wait for services to be ready
function Wait-ForServices {
    if ($Quick) {
        return $true
    }
    
    Write-Info "Waiting for services to be ready..."
    
    $config = $ModeConfigs[$Mode]
    $timeout = 120  # 2 minutes
    $elapsed = 0
    $checkInterval = 5
    $servicesReady = 0
    $totalServices = $config.HealthChecks.Count
    
    while ($elapsed -lt $timeout -and $servicesReady -lt $totalServices) {
        $servicesReady = 0
        
        foreach ($service in $config.HealthChecks) {
            # Try different port combinations for health checks
            $healthUrls = @()
            
            switch ($service) {
                "master-coordinator" { $healthUrls += "http://localhost:3000/health" }
                "enhanced-coordinator" { $healthUrls += "http://localhost:3001/health" }
                "token-scanner" { $healthUrls += "http://localhost:3003/health" }
                "coordinator" { $healthUrls += "http://localhost:3000/health" }
                "arbitrage" { $healthUrls += "http://localhost:3001/health" }
                "flash-loan" { $healthUrls += "http://localhost:3002/health" }
                "risk" { $healthUrls += "http://localhost:3003/health" }
                "dex" { $healthUrls += "http://localhost:3004/health" }
                "execution" { $healthUrls += "http://localhost:3002/health" }
                "redis" { 
                    try {
                        $redisCheck = docker exec redis redis-cli ping 2>&1
                        if ($redisCheck -match "PONG") { $servicesReady++; continue }
                    } catch { }
                }
                "postgres" {
                    try {
                        $pgCheck = docker exec postgres pg_isready -U postgres 2>&1
                        if ($pgCheck -match "accepting connections") { $servicesReady++; continue }
                    } catch { }
                }
                "rabbitmq" {
                    try {
                        $rabbitCheck = docker exec rabbitmq rabbitmq-diagnostics check_running 2>&1
                        if ($LASTEXITCODE -eq 0) { $servicesReady++; continue }
                    } catch { }
                }
            }
            
            # Try health URLs for HTTP services
            foreach ($url in $healthUrls) {
                try {
                    $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 3 -ErrorAction Stop
                    if ($response.status -eq "healthy" -or $response.StatusCode -eq 200) {
                        $servicesReady++
                        break
                    }
                } catch {
                    # Service not ready yet
                }
            }
        }
        
        if ($servicesReady -eq $totalServices) {
            Write-Success "All services are ready!"
            return $true
        }
        
        Write-Info "  Services ready: $servicesReady/$totalServices (waiting... $elapsed/$timeout seconds)"
        Start-Sleep -Seconds $checkInterval
        $elapsed += $checkInterval
    }
    
    if ($servicesReady -eq $totalServices) {
        Write-Success "All services are ready!"
        return $true
    } else {
        Write-Warning "Services taking longer than expected to start ($servicesReady/$totalServices ready)"
        return $false
    }
}

# Display comprehensive system status
function Show-SystemStatus {
    Write-Header "SYSTEM STATUS SUMMARY"
    
    # Get running containers
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-Object -Skip 1
    
    if (!$containers) {
        Write-Warning "No containers are currently running"
        return
    }
    
    # Group containers by type
    $infrastructure = $containers | Where-Object { $_ -notmatch "mcp-" -and $_ -notmatch "agent-" }
    $mcpServers = $containers | Where-Object { $_ -match "mcp-" }
    $agents = $containers | Where-Object { $_ -match "agent-" }
    $other = $containers | Where-Object { $_ -notmatch "mcp-" -and $_ -notmatch "agent-" -and $_ -notmatch "redis|postgres|rabbitmq|prometheus|grafana" }
    
    if ($infrastructure) {
        Write-Info "Infrastructure Services:"
        $infrastructure | ForEach-Object { Write-Success "  $_" }
    }
    
    if ($mcpServers) {
        Write-Info "`nMCP Servers:"
        $mcpServers | ForEach-Object { Write-Success "  $_" }
    }
    
    if ($agents) {
        Write-Info "`nAI Agents:"
        $agents | ForEach-Object { Write-Success "  $_" }
    }
    
    if ($other) {
        Write-Info "`nOther Services:"
        $other | ForEach-Object { Write-Info "  $_" }
    }
    
    # Show access URLs based on mode
    Write-Header "ACCESS INFORMATION"
    
    $config = $ModeConfigs[$Mode]
    
    Write-Info "Web Interfaces:"
    switch ($Mode) {
        "full" {
            Write-Info "  • MCP Coordinator Dashboard: http://localhost:8080"
            Write-Info "  • Master Coordinator API: http://localhost:3000"
            Write-Info "  • Enhanced Coordinator: http://localhost:3001" 
            Write-Info "  • Token Scanner: http://localhost:3003"
            Write-Info "  • Grafana Dashboard: http://localhost:3030 (admin/admin)"
            Write-Info "  • RabbitMQ Management: http://localhost:15672 (mcp_admin/mcp_secure_2025)"
            Write-Info "  • Prometheus: http://localhost:9090"
        }
        "minimal" {
            Write-Info "  • Master Coordinator: http://localhost:3000"
            Write-Info "  • Execution Service: http://localhost:3001"
            Write-Info "  • Risk Management: http://localhost:3002"
            Write-Info "  • RabbitMQ Management: http://localhost:15672"
            Write-Info "  • Prometheus: http://localhost:9090"
        }
        "dev" {
            Write-Info "  • RabbitMQ Management: http://localhost:15672"
            Write-Info "  • Prometheus: http://localhost:9090"
            Write-Info "  • Grafana: http://localhost:3030 (admin/admin)"
        }
        "optimized" {
            Write-Info "  • Coordinator: http://localhost:3000"
            Write-Info "  • Arbitrage Detector: http://localhost:3001"
            Write-Info "  • Flash Loan Executor: http://localhost:3002"
            Write-Info "  • Risk Manager: http://localhost:3003"
            Write-Info "  • DEX Monitor: http://localhost:3004"
            Write-Info "  • Dashboard: http://localhost:8080"
            Write-Info "  • Grafana: http://localhost:3005 (admin/admin)"
            Write-Info "  • RabbitMQ: http://localhost:15672 (admin/admin)"
        }
    }
    
    Write-Info "`nAPI Endpoints:"
    Write-Info "  • Health Check: http://localhost:3000/health"
    Write-Info "  • System Status: http://localhost:3000/status"
    Write-Info "  • Metrics: http://localhost:3000/metrics"
    
    Write-Info "`nManagement Commands:"
    Write-Info "  • View logs: docker-compose -f docker/compose/docker-compose.*.yml logs -f [service]"
    Write-Info "  • Stop system: docker-compose -f docker/compose/docker-compose.*.yml down"
    Write-Info "  • Restart service: docker-compose -f docker/compose/docker-compose.*.yml restart [service]"
    Write-Info "  • Check status: docker ps"
    Write-Info "  • Resource usage: docker stats"
}

# Show logs for debugging
function Show-Logs {
    param([string]$Service = "")
    
    $config = $ModeConfigs[$Mode]
    $composeFile = $config.ComposeFiles[0]
    $composePath = "docker/compose/$composeFile"
    
    if ($Service) {
        Write-Info "Showing logs for $Service..."
        docker logs --tail 50 -f $Service
    } else {
        Write-Info "Showing recent logs from all services..."
        docker-compose -f $composePath logs --tail 20
    }
}

# Perform system verification
function Verify-System {
    Write-Info "Performing system verification..."
    
    try {
        # Count containers by type
        $allContainers = docker ps --format "{{.Names}}"
        $mcpCount = ($allContainers | Where-Object { $_ -match "mcp-" }).Count
        $agentCount = ($allContainers | Where-Object { $_ -match "agent-" }).Count
        $infraCount = ($allContainers | Where-Object { $_ -match "redis|postgres|rabbitmq|prometheus|grafana" }).Count
        
        Write-Success "Container Status:"
        Write-Success "  • MCP Servers: $mcpCount running"
        Write-Success "  • AI Agents: $agentCount running"  
        Write-Success "  • Infrastructure: $infraCount running"
        
        # Quick health check on key services
        $config = $ModeConfigs[$Mode]
        $healthyServices = 0
        
        foreach ($service in $config.HealthChecks) {
            try {
                switch ($service) {
                    { $_ -match "coordinator|arbitrage|flash-loan|risk|dex" } {
                        $port = switch ($_) {
                            "coordinator" { "3000" }
                            "arbitrage" { "3001" }
                            "flash-loan" { "3002" }
                            "risk" { "3003" }
                            "dex" { "3004" }
                            default { "3000" }
                        }
                        $response = Invoke-RestMethod -Uri "http://localhost:$port/health" -TimeoutSec 2
                        if ($response) { $healthyServices++ }
                    }
                }
            } catch {
                # Service health check failed
            }
        }
        
        Write-Success "  • Healthy Services: $healthyServices/$($config.HealthChecks.Count)"
        Write-Success "System verification complete!"
        
    } catch {
        Write-Warning "System verification had some issues, but system should be operational"
    }
}

# Main execution function
function Start-MCPSystem {
    Write-Header "INITIALIZING MCP SYSTEM"
    
    # Setup phase
    Test-Prerequisites
    Set-WorkingDirectory
    Initialize-Directories
    Initialize-Environment
    Clear-ExistingContainers
    Build-DockerImages
    
    # Deployment phase
    if (!$InfraOnly -or $Mode -eq "dev") {
        Start-Services
        
        # Wait for services if not quick mode
        $servicesReady = Wait-ForServices
        
        # Show status
        Show-SystemStatus
        
        if (!$Quick) {
            Verify-System
        }
        
        # Final status
        if ($servicesReady) {
            Write-Header "DEPLOYMENT COMPLETE"
            Write-Success "MCP System successfully started in $Mode mode!"
            
            $config = $ModeConfigs[$Mode]
            Write-Info "Mode: $($config.Description)"
            Write-Info "Access the system using the URLs listed above."
        } else {
            Write-Header "DEPLOYMENT COMPLETED WITH WARNINGS"
            Write-Warning "System started but some services may not be fully ready"
            Write-Info "Check individual service logs for more details"
        }
        
        # Offer to show logs
        if ($ShowLogs) {
            Show-Logs
        }
    } else {
        Write-Info "Infrastructure-only mode requested - skipping service deployment"
    }
}

# Execute main function
try {
    Start-MCPSystem
} catch {
    Write-Error "Failed to start MCP system: $($_.Exception.Message)"
    Write-Info "Check Docker logs and system requirements"
    exit 1
}

# Keep window open in interactive mode
if ($Host.Name -eq "ConsoleHost" -and !$Detached) {
    Write-Info "`nPress any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
