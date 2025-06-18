# GitHub Copilot MCP Integration Setup
# This script configures GitHub Copilot to work with MCP servers in Docker

Write-Host "Setting up GitHub Copilot MCP Integration..." -ForegroundColor Green

# Check if Docker containers are running
Write-Host "Checking Docker container status..." -ForegroundColor Yellow
$containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "flashloan-mcp"

if ($containers.Count -eq 0) {
    Write-Host "No MCP containers found running. Starting containers..." -ForegroundColor Red
    docker-compose up -d
    Start-Sleep 10
}

# Display running MCP servers
Write-Host "`nRunning MCP Servers:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "flashloan-mcp" | ForEach-Object {
    Write-Host $_ -ForegroundColor White
}

# Start the MCP Bridge
Write-Host "`nStarting MCP Bridge..." -ForegroundColor Yellow
if (Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*mcp_bridge.py*" }) {
    Write-Host "MCP Bridge is already running" -ForegroundColor Green
} else {
    Start-Process -NoNewWindow -FilePath "python" -ArgumentList "mcp_bridge.py", "--verbose"
    Start-Sleep 3
    Write-Host "MCP Bridge started on port 8888" -ForegroundColor Green
}

# Test connectivity to MCP servers
Write-Host "`nTesting MCP server connectivity..." -ForegroundColor Yellow

$mcpServers = @{
    "flash_loan_blockchain" = "8101"
    "defi_analyzer" = "8102"
    "flash_loan" = "8103"
    "arbitrage" = "8104"
    "liquidity" = "8105"
    "price_feed" = "8106"
    "risk_manager" = "8107"
    "portfolio" = "8108"
    "api_client" = "8109"
    "database" = "8110"
    "cache_manager" = "8111"
    "file_processor" = "8112"
    "notification" = "8113"
    "monitoring" = "8114"
    "security" = "8115"
    "data_analyzer" = "8116"
    "web_scraper" = "8117"
    "task_queue" = "8118"
    "filesystem" = "8119"
    "coordinator" = "8120"
}

$healthyServers = @()
$unhealthyServers = @()

foreach ($server in $mcpServers.GetEnumerator()) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$($server.Value)/health" -Method GET -TimeoutSec 5
        Write-Host "✓ $($server.Key) (port $($server.Value)) - HEALTHY" -ForegroundColor Green
        $healthyServers += $server.Key
    } catch {
        Write-Host "✗ $($server.Key) (port $($server.Value)) - UNHEALTHY" -ForegroundColor Red
        $unhealthyServers += $server.Key
    }
}

Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "Healthy servers: $($healthyServers.Count)" -ForegroundColor Green
Write-Host "Unhealthy servers: $($unhealthyServers.Count)" -ForegroundColor Red

if ($unhealthyServers.Count -eq 0) {
    Write-Host "`n🎉 All MCP servers are running and healthy!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ Some MCP servers are not responding. You may need to restart them." -ForegroundColor Yellow
}

# Create environment file for GitHub Copilot
Write-Host "`nCreating GitHub Copilot environment configuration..." -ForegroundColor Yellow

$envContent = @"
# GitHub Copilot MCP Configuration
# Generated on $(Get-Date)

# MCP Bridge Configuration
MCP_BRIDGE_ENABLED=true
MCP_BRIDGE_HOST=localhost
MCP_BRIDGE_PORT=8888
MCP_BRIDGE_PROTOCOL=ws

# MCP Server Endpoints
$(foreach ($server in $mcpServers.GetEnumerator()) { "MCP_${($server.Key.ToUpper())}_ENDPOINT=http://localhost:$($server.Value)" })

# Health Check Interval (seconds)
MCP_HEALTH_CHECK_INTERVAL=30

# Timeout for MCP requests (milliseconds)
MCP_REQUEST_TIMEOUT=10000

# Enable MCP logging
MCP_LOGGING_ENABLED=true
MCP_LOG_LEVEL=INFO
"@

$envContent | Out-File -FilePath ".env.copilot" -Encoding UTF8
Write-Host "Environment configuration saved to .env.copilot" -ForegroundColor Green

# Create VS Code task for MCP Bridge
Write-Host "Creating VS Code task configuration..." -ForegroundColor Yellow

$tasksJson = @{
    "version" = "2.0.0"
    "tasks" = @(
        @{
            "label" = "Start MCP Bridge"
            "type" = "shell"
            "command" = "python"
            "args" = @("mcp_bridge.py", "--verbose")
            "group" = "build"
            "presentation" = @{
                "echo" = $true
                "reveal" = "always"
                "focus" = $false
                "panel" = "shared"
                "showReuseMessage" = $true
                "clear" = $false
            }
            "problemMatcher" = @()
            "isBackground" = $true
        },
        @{
            "label" = "Test MCP Servers"
            "type" = "shell"
            "command" = "python"
            "args" = @("-c", "import asyncio; import aiohttp; import json; asyncio.run(test_mcp_servers())")
            "group" = "test"
            "presentation" = @{
                "echo" = $true
                "reveal" = "always"
                "focus" = $false
                "panel" = "shared"
            }
        },
        @{
            "label" = "Stop MCP Bridge"
            "type" = "shell" 
            "command" = "taskkill"
            "args" = @("/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq mcp_bridge*")
            "group" = "build"
        }
    )
}

$tasksJsonString = $tasksJson | ConvertTo-Json -Depth 10
$tasksJsonString | Out-File -FilePath ".vscode/tasks.json" -Encoding UTF8
Write-Host "VS Code tasks configuration created" -ForegroundColor Green

Write-Host "`n🚀 GitHub Copilot MCP Integration setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Restart VS Code to apply changes" -ForegroundColor White
Write-Host "2. Use Ctrl+Shift+P and run 'Tasks: Run Task' -> 'Start MCP Bridge'" -ForegroundColor White
Write-Host "3. GitHub Copilot should now have access to your MCP servers" -ForegroundColor White
Write-Host "`nMCP Bridge WebSocket URL: ws://localhost:8888" -ForegroundColor Yellow
Write-Host "Available MCP servers: $($healthyServers -join ', ')" -ForegroundColor Yellow
