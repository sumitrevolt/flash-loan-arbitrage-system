#!/usr/bin/env powershell
# Claude Docker Management Script

Write-Host "🤖 Claude Docker Manager for Flash Loan Project" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Show-ClaudeMenu {
    Write-Host ""
    Write-Host "🎯 Claude Docker Options:" -ForegroundColor Yellow
    Write-Host "1. Start Claude Full Stack" -ForegroundColor White
    Write-Host "2. Start Claude Core Services" -ForegroundColor White
    Write-Host "3. Start Claude Bridge Only" -ForegroundColor White
    Write-Host "4. Start MCP Servers Only" -ForegroundColor White
    Write-Host "5. Start AI Agents Only" -ForegroundColor White
    Write-Host "6. View Claude Services Status" -ForegroundColor White
    Write-Host "7. View Claude Logs" -ForegroundColor White
    Write-Host "8. Stop Claude Services" -ForegroundColor White
    Write-Host "9. Set Claude Desktop Config" -ForegroundColor White
    Write-Host "10. Health Check All Services" -ForegroundColor White
    Write-Host "11. Exit" -ForegroundColor White
    Write-Host ""
}

function Start-ClaudeFullStack {
    Write-Host "🚀 Starting Claude Full Stack..." -ForegroundColor Green
    Write-Host "This includes:"
    Write-Host "- Infrastructure (Redis, PostgreSQL)"
    Write-Host "- Claude Desktop Bridge"
    Write-Host "- All MCP Servers"
    Write-Host "- AI Agent System"
    Write-Host "- Web UI and Monitoring"
    
    docker compose -f docker-compose-claude.yml up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Claude Full Stack started successfully!" -ForegroundColor Green
        Show-ClaudeServiceInfo
        Show-ClaudeAccessUrls
    } else {
        Write-Host "❌ Failed to start Claude Full Stack" -ForegroundColor Red
    }
}

function Start-ClaudeCoreServices {
    Write-Host "🚀 Starting Claude Core Services..." -ForegroundColor Green
    docker compose -f docker-compose-claude.yml up -d redis postgres claude-desktop-bridge mcp-coordinator
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Claude Core Services started!" -ForegroundColor Green
        Show-ClaudeServiceInfo
    } else {
        Write-Host "❌ Failed to start Claude Core Services" -ForegroundColor Red
    }
}

function Start-ClaudeBridgeOnly {
    Write-Host "🌉 Starting Claude Desktop Bridge..." -ForegroundColor Green
    docker compose -f docker-compose-claude.yml up -d redis postgres claude-desktop-bridge
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Claude Desktop Bridge started!" -ForegroundColor Green
        Write-Host "🌐 Access at: http://localhost:8080" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Failed to start Claude Desktop Bridge" -ForegroundColor Red
    }
}

function Start-MCPServersOnly {
    Write-Host "🔌 Starting MCP Servers..." -ForegroundColor Green
    docker compose -f docker-compose-claude.yml up -d redis postgres mcp-coordinator mcp-flash-loan mcp-price-monitor mcp-aave
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ MCP Servers started!" -ForegroundColor Green
        Show-MCPServerInfo
    } else {
        Write-Host "❌ Failed to start MCP Servers" -ForegroundColor Red
    }
}

function Start-AIAgentsOnly {
    Write-Host "🤖 Starting AI Agents..." -ForegroundColor Green
    docker compose -f docker-compose-claude.yml up -d redis ai-agent-coordinator ai-agent-code ai-agent-trading
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ AI Agents started!" -ForegroundColor Green
        Show-AIAgentInfo
    } else {
        Write-Host "❌ Failed to start AI Agents" -ForegroundColor Red
    }
}

function Show-ClaudeServiceStatus {
    Write-Host "📊 Claude Services Status:" -ForegroundColor Cyan
    docker compose -f docker-compose-claude.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host ""
    Write-Host "🔍 Health Checks:" -ForegroundColor Cyan
    
    # Check Claude Bridge
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 5
        Write-Host "✅ Claude Bridge: Healthy" -ForegroundColor Green
        Write-Host "   Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
    } catch {
        Write-Host "❌ Claude Bridge: Unhealthy" -ForegroundColor Red
    }
    
    # Check MCP Coordinator
    try {
        Invoke-RestMethod -Uri "http://localhost:8900/health" -TimeoutSec 5 | Out-Null
        Write-Host "✅ MCP Coordinator: Healthy" -ForegroundColor Green
    } catch {
        Write-Host "❌ MCP Coordinator: Unhealthy" -ForegroundColor Red
    }
    
    # Check AI Coordinator
    try {
        Invoke-RestMethod -Uri "http://localhost:7000/health" -TimeoutSec 5 | Out-Null
        Write-Host "✅ AI Coordinator: Healthy" -ForegroundColor Green
    } catch {
        Write-Host "❌ AI Coordinator: Unhealthy" -ForegroundColor Red
    }
}

function Show-ClaudeLogs {
    Write-Host "📋 Claude Services Logs (last 50 lines):" -ForegroundColor Cyan
    docker compose -f docker-compose-claude.yml logs --tail=50 --follow
}

function Stop-ClaudeServices {
    Write-Host "🛑 Stopping Claude Services..." -ForegroundColor Yellow
    docker compose -f docker-compose-claude.yml down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Claude Services stopped successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to stop Claude Services" -ForegroundColor Red
    }
}

function Set-ClaudeDesktopConfig {
    Write-Host "⚙️ Setting up Claude Desktop Configuration..." -ForegroundColor Yellow
    
    # Path for Claude Desktop's configuration
    $claudeConfigPath = "$env:APPDATA\Claude\claude_desktop_config.json"
    # Source configuration file from the project root, designed for local execution
    $sourceConfigPath = "claude_desktop_config.json" # Use the root claude_desktop_config.json
    
    if (Test-Path $sourceConfigPath) {
        try {
            # Create directory if it doesn't exist
            $claudeDir = Split-Path $claudeConfigPath -Parent
            if (!(Test-Path $claudeDir)) {
                New-Item -ItemType Directory -Path $claudeDir -Force
            }
            
            # Copy configuration
            Copy-Item $sourceConfigPath $claudeConfigPath -Force
            Write-Host "✅ Claude Desktop config updated!" -ForegroundColor Green
            Write-Host "📍 Config location: $claudeConfigPath" -ForegroundColor Cyan
            Write-Host "Source: $sourceConfigPath" -ForegroundColor Cyan
            
            Write-Host ""
            Write-Host "📋 Next steps:" -ForegroundColor Yellow
            Write-Host "1. Restart Claude Desktop application" -ForegroundColor White
            Write-Host "2. Start Docker services with option 1" -ForegroundColor White
            Write-Host "3. Open new conversation in Claude Desktop" -ForegroundColor White
            Write-Host "4. MCP servers will be available automatically" -ForegroundColor White
            
        } catch {
            Write-Host "❌ Failed to setup Claude Desktop config: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Source config file not found: $sourceConfigPath" -ForegroundColor Red
    }
}

function Test-AllClaudeServices {
    Write-Host "🏥 Testing All Claude Services..." -ForegroundColor Yellow
    
    $services = @(
        @{ Name = "Claude Bridge"; Url = "http://localhost:8080/health" },
        @{ Name = "MCP Coordinator"; Url = "http://localhost:8900/health" },
        @{ Name = "AI Coordinator"; Url = "http://localhost:7000/health" },
        @{ Name = "Web UI"; Url = "http://localhost:3000/health" },
        @{ Name = "Prometheus"; Url = "http://localhost:9090/-/ready" },
        @{ Name = "Grafana"; Url = "http://localhost:3001/api/health" }
    )
    
    foreach ($service in $services) {
        try {
            Invoke-RestMethod -Uri $service.Url -TimeoutSec 5 | Out-Null
            Write-Host "✅ $($service.Name): Healthy" -ForegroundColor Green
        } catch {
            Write-Host "❌ $($service.Name): Unhealthy" -ForegroundColor Red
        }
    }
}

function Show-ClaudeServiceInfo {
    Write-Host ""
    Write-Host "🎯 Claude Services Information:" -ForegroundColor Cyan
    Write-Host "- Claude Desktop Bridge: Coordinates MCP servers"
    Write-Host "- MCP Coordinator: Manages Model Context Protocol servers"
    Write-Host "- AI Agent System: Provides intelligent automation"
    Write-Host "- Real-time Price Monitor: Tracks cryptocurrency prices"
    Write-Host "- Flash Loan Arbitrage: Detects and executes opportunities"
}

function Show-ClaudeAccessUrls {
    Write-Host ""
    Write-Host "🌐 Claude Access URLs:" -ForegroundColor Cyan
    Write-Host "- Claude Bridge API: http://localhost:8080" -ForegroundColor White
    Write-Host "- Claude Web UI: http://localhost:3000" -ForegroundColor White
    Write-Host "- MCP Coordinator: http://localhost:8900" -ForegroundColor White
    Write-Host "- AI Coordinator: http://localhost:7000" -ForegroundColor White
    Write-Host "- Monitoring (Grafana): http://localhost:3001" -ForegroundColor White
    Write-Host "- Metrics (Prometheus): http://localhost:9090" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 Database Access:" -ForegroundColor Cyan
    Write-Host "- PostgreSQL: localhost:5432 (claude/claude123)" -ForegroundColor White
    Write-Host "- Redis: localhost:6379" -ForegroundColor White
}

function Show-MCPServerInfo {
    Write-Host ""
    Write-Host "🔌 MCP Servers:" -ForegroundColor Cyan
    Write-Host "- Flash Loan Arbitrage (Port 8901)" -ForegroundColor White
    Write-Host "- Real-time Price Monitor (Port 8902)" -ForegroundColor White
    Write-Host "- Aave Protocol (Port 8903)" -ForegroundColor White
    Write-Host "- Simple Flash Loan (Port 8904)" -ForegroundColor White
    Write-Host "- Blockchain Integration (Port 8905)" -ForegroundColor White
    Write-Host "- Context7 AI (Port 8906)" -ForegroundColor White
}

function Show-AIAgentInfo {
    Write-Host ""
    Write-Host "🤖 AI Agents:" -ForegroundColor Cyan
    Write-Host "- AI Coordinator (Port 7000)" -ForegroundColor White
    Write-Host "- Code Analysis Agent (Port 7001)" -ForegroundColor White
    Write-Host "- Trading Strategy Agent (Port 7002)" -ForegroundColor White
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
    Show-ClaudeMenu
    $choice = Read-Host "Enter your choice (1-11)"
    
    switch ($choice) {
        "1" { Start-ClaudeFullStack }
        "2" { Start-ClaudeCoreServices }
        "3" { Start-ClaudeBridgeOnly }
        "4" { Start-MCPServersOnly }
        "5" { Start-AIAgentsOnly }
        "6" { Show-ClaudeServiceStatus }
        "7" { Show-ClaudeLogs }
        "8" { Stop-ClaudeServices }
        "9" { Set-ClaudeDesktopConfig }
        "10" { Test-AllClaudeServices }
        "11" { 
            Write-Host "👋 Goodbye!" -ForegroundColor Cyan
            break 
        }
        default { 
            Write-Host "❌ Invalid choice. Please select 1-11." -ForegroundColor Red 
        }
    }
    
    if ($choice -ne "11" -and $choice -ne "7") {
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    
} while ($choice -ne "11")
