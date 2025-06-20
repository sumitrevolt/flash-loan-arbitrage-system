#!/usr/bin/env powershell
# Flash Loan Docker Manager Script - Unified Version

Write-Host "🐳 Flash Loan Docker Manager" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Show-Menu {
    Write-Host ""
    Write-Host "Select an option:" -ForegroundColor Yellow
    Write-Host "1. Run troubleshooting script" -ForegroundColor White
    Write-Host "2. Start core services only" -ForegroundColor White
    Write-Host "3. Start all services (full)" -ForegroundColor White
    Write-Host "4. Stop all services" -ForegroundColor White
    Write-Host "5. View service status" -ForegroundColor White
    Write-Host "6. View logs" -ForegroundColor White
    Write-Host "7. Clean up Docker" -ForegroundColor White
    Write-Host "8. Restart specific service" -ForegroundColor White
    Write-Host "9. Exit" -ForegroundColor White
    Write-Host ""
}

function Start-Troubleshooting {
    Write-Host "🔧 Running Docker troubleshooting..." -ForegroundColor Yellow
    python docker_troubleshoot.py
}

function Start-CoreServices {
    Write-Host "🚀 Starting core services (Redis, PostgreSQL, MCP Coordinator)..." -ForegroundColor Green
    docker compose up -d redis postgres mcp-coordinator
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Core services started successfully!" -ForegroundColor Green
        Show-CoreServiceInfo
    } else {
        Write-Host "❌ Failed to start core services" -ForegroundColor Red
    }
}

function Start-FullServices {
    Write-Host "🚀 Starting all services (full configuration)..." -ForegroundColor Green
    Write-Host "This includes 21+ MCP servers and 10 AI agents..." -ForegroundColor Yellow
    docker compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ All services started successfully!" -ForegroundColor Green
        Show-FullServiceInfo
    } else {
        Write-Host "❌ Failed to start services" -ForegroundColor Red
    }
}

function Stop-AllServices {
    Write-Host "🛑 Stopping all services..." -ForegroundColor Yellow
    docker compose down
    docker stop $(docker ps -q) 2>$null
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

function Show-ServiceStatus {
    Write-Host "📊 Service Status:" -ForegroundColor Cyan
    docker compose ps
    Write-Host ""
    Write-Host "📊 All Containers:" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

function Show-ServiceLogs {
    Write-Host "📋 Recent logs:" -ForegroundColor Cyan
    docker compose logs --tail=50
}

function Clean-Docker {
    Write-Host "🧹 Cleaning up Docker resources..." -ForegroundColor Yellow
    docker system prune -f
    docker volume prune -f
    Write-Host "✅ Cleanup completed" -ForegroundColor Green
}

function Restart-SpecificService {
    Write-Host "Available services:" -ForegroundColor Cyan
    docker compose ps --services
    Write-Host ""
    $service = Read-Host "Enter service name to restart"
    if ($service) {
        Write-Host "🔄 Restarting $service..." -ForegroundColor Yellow
        docker compose restart $service
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $service restarted successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to restart $service" -ForegroundColor Red
        }
    }
}

function Show-CoreServiceInfo {
    Write-Host ""
    Write-Host "🌐 Core Service URLs:" -ForegroundColor Cyan
    Write-Host "- MCP Coordinator: http://localhost:9000" -ForegroundColor White
    Write-Host "- MCP Health: http://localhost:9000/health" -ForegroundColor White
    Write-Host "- PostgreSQL: localhost:5432" -ForegroundColor White
    Write-Host "- Redis: localhost:6379" -ForegroundColor White
    Write-Host ""
}

function Show-FullServiceInfo {
    Write-Host ""
    Write-Host "🌐 Full System URLs:" -ForegroundColor Cyan
    Write-Host "- MCP Coordinator: http://localhost:9000" -ForegroundColor White
    Write-Host "- Web Dashboard: http://localhost:5000" -ForegroundColor White
    Write-Host "- Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "- Grafana: http://localhost:3001" -ForegroundColor White
    Write-Host "- AAVE Flash Loan: http://localhost:8001" -ForegroundColor White
    Write-Host "- Price Oracle: http://localhost:8005" -ForegroundColor White
    Write-Host ""
    Write-Host "🤖 AI Agents (10 total):" -ForegroundColor Cyan
    Write-Host "- Code Indexers: ports 3101-3102" -ForegroundColor White
    Write-Host "- Builders: ports 3121-3122" -ForegroundColor White
    Write-Host "- Executors: ports 3136-3137" -ForegroundColor White
    Write-Host "- Coordinators: ports 3151-3152" -ForegroundColor White
    Write-Host "- Planners: ports 3161-3162" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 MCP Servers (21+ total):" -ForegroundColor Cyan
    Write-Host "- AI Integration: ports 8004, 8006, 3003" -ForegroundColor White
    Write-Host "- Blockchain: ports 8002, 8003, 8007, 8008" -ForegroundColor White
    Write-Host "- Data Providers: ports 8005, 8009, 8013, 8014" -ForegroundColor White
    Write-Host "- Execution: ports 3004, 3005, 8015, 8016" -ForegroundColor White
    Write-Host "- Risk Management: ports 8011, 8012" -ForegroundColor White
    Write-Host "- Analytics: ports 8010, 8020, 8021, 8022" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 Useful Commands:" -ForegroundColor Cyan
    Write-Host "- View logs: docker compose logs -f [service]" -ForegroundColor White
    Write-Host "- Stop services: docker compose down" -ForegroundColor White
    Write-Host "- Restart service: docker compose restart [service]" -ForegroundColor White
    Write-Host "- Scale service: docker compose up -d --scale [service]=N" -ForegroundColor White
}

# Main script execution
if (!(Test-DockerRunning)) {
    Write-Host "❌ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop first." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Docker is running" -ForegroundColor Green

do {
    Show-Menu
    $choice = Read-Host "Enter your choice (1-9)"
    
    switch ($choice) {
        "1" { Start-Troubleshooting }
        "2" { Start-CoreServices }
        "3" { Start-FullServices }
        "4" { Stop-AllServices }
        "5" { Show-ServiceStatus }
        "6" { Show-ServiceLogs }
        "7" { Clean-Docker }
        "8" { Restart-SpecificService }
        "9" { 
            Write-Host "👋 Goodbye!" -ForegroundColor Cyan
            break 
        }
        default { 
            Write-Host "❌ Invalid choice. Please select 1-9." -ForegroundColor Red 
        }
    }
    
    if ($choice -ne "9") {
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    
} while ($choice -ne "9")
