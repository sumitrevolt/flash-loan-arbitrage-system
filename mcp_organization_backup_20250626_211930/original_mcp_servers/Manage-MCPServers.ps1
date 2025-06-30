# MCP Server Management Script
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "status", "restart", "organize")]
    [string]$Action = "start",
    
    [Parameter(Mandatory=$false)]
    [string]$Category = "all"
)

$mcpServersPath = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers"
$logPath = "$mcpServersPath\logs"

# Ensure log directory exists
if (!(Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath -Force | Out-Null
}

function Write-ColoredOutput {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Start-MCPServers {
    param($CategoryFilter = "all")
    
    Write-ColoredOutput "🚀 Starting MCP Servers..." "Green"
    
    $categories = @(
        "orchestration",
        "blockchain_integration", 
        "data_providers",
        "ai_integration",
        "market_analysis",
        "execution",
        "risk_management",
        "ui"
    )
    
    $totalStarted = 0
    
    foreach ($category in $categories) {
        if ($CategoryFilter -ne "all" -and $CategoryFilter -ne $category) {
            continue
        }
        
        $categoryPath = "$mcpServersPath\$category"
        
        if (Test-Path $categoryPath) {
            Write-ColoredOutput "`n📁 Starting $category servers..." "Cyan"
            
            $serverFiles = Get-ChildItem -Path $categoryPath -Filter "*.py" | 
                Where-Object { $_.Name -notlike "__*" }
            
            foreach ($server in $serverFiles) {
                try {
                    Write-ColoredOutput "  ▶️  Starting $($server.Name)..." "Yellow"
                    
                    # Start server in background
                    $process = Start-Process -FilePath "python" -ArgumentList $server.FullName -WorkingDirectory $categoryPath -WindowStyle Hidden -PassThru
                    
                    if ($process) {
                        Write-ColoredOutput "  ✅ Started $($server.Name) (PID: $($process.Id))" "Green"
                        $totalStarted++
                        
                        # Log process info
                        "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) - Started $category/$($server.Name) - PID: $($process.Id)" | 
                            Out-File -FilePath "$logPath\server_processes.log" -Append
                    }
                    
                    # Small delay between server starts
                    Start-Sleep -Seconds 2
                    
                } catch {
                    Write-ColoredOutput "  ❌ Failed to start $($server.Name): $_" "Red"
                }
            }
            
            # Delay between categories
            Start-Sleep -Seconds 3
        }
    }
    
    Write-ColoredOutput "`n📊 Total servers started: $totalStarted" "Green"
}

function Stop-MCPServers {
    Write-ColoredOutput "🛑 Stopping MCP Servers..." "Red"
    
    # Get all python processes that might be MCP servers
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
    
    if ($pythonProcesses) {
        foreach ($process in $pythonProcesses) {
            try {
                # Check if it's running from mcp_servers directory
                if ($process.Path -and $process.Path.Contains("mcp_servers")) {
                    Write-ColoredOutput "Stopping process $($process.Id)..." "Yellow"
                    $process.Kill()
                }
            } catch {
                Write-Host "Could not stop process $($process.Id): $_" -ForegroundColor Red
            }
        }
        Write-ColoredOutput "✅ MCP servers stopped" "Green"
    } else {
        Write-ColoredOutput "No MCP server processes found" "Yellow"
    }
}

function Show-MCPStatus {
    Write-ColoredOutput "📊 MCP Server Status" "Cyan"
    Write-ColoredOutput "=" * 50 "Cyan"
    
    # Check running Python processes
    $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
    
    if ($pythonProcesses) {
        Write-ColoredOutput "`nRunning Python processes:" "White"
        foreach ($process in $pythonProcesses) {
            if ($process.Path) {
                $fileName = Split-Path $process.Path -Leaf
                Write-ColoredOutput "  PID: $($process.Id) - $fileName" "Green"
            }
        }
    } else {
        Write-ColoredOutput "No Python processes running" "Yellow"
    }
    
    # Show directory structure
    Write-ColoredOutput "`nMCP Servers Directory Structure:" "White"
    if (Test-Path $mcpServersPath) {
        $categories = Get-ChildItem -Path $mcpServersPath -Directory
        foreach ($category in $categories) {
            $serverCount = (Get-ChildItem -Path $category.FullName -Filter "*.py" | Where-Object { $_.Name -notlike "__*" }).Count
            Write-ColoredOutput "  📁 $($category.Name): $serverCount servers" "Cyan"
        }
    }
}

function Show-OrganizationSummary {
    Write-ColoredOutput "📋 MCP Server Organization Summary" "Green"
    Write-ColoredOutput "=" * 60 "Green"
    
    if (Test-Path "$mcpServersPath\ORGANIZATION_REPORT.md") {
        Write-ColoredOutput "✅ Organization report available at:" "Green"
        Write-ColoredOutput "   $mcpServersPath\ORGANIZATION_REPORT.md" "Cyan"
    }
    
    # Count servers by category
    $categories = @("orchestration", "blockchain_integration", "data_providers", "ai_integration", 
                   "market_analysis", "execution", "risk_management", "ui", "utils")
    
    $totalServers = 0
    foreach ($category in $categories) {
        $categoryPath = "$mcpServersPath\$category"
        if (Test-Path $categoryPath) {
            $serverCount = (Get-ChildItem -Path $categoryPath -Filter "*.py" | Where-Object { $_.Name -notlike "__*" }).Count
            if ($serverCount -gt 0) {
                Write-ColoredOutput "📁 $category`: $serverCount servers" "Cyan"
                $totalServers += $serverCount
            }
        }
    }
    
    Write-ColoredOutput "`n📊 Total organized servers: $totalServers" "Green"
}

# Main execution
switch ($Action) {
    "start" {
        Start-MCPServers -CategoryFilter $Category
    }
    "stop" {
        Stop-MCPServers
    }
    "status" {
        Show-MCPStatus
    }
    "restart" {
        Stop-MCPServers
        Start-Sleep -Seconds 5
        Start-MCPServers -CategoryFilter $Category
    }
    "organize" {
        Show-OrganizationSummary
    }
}

Write-ColoredOutput "`n🎉 MCP Server management completed!" "Green"
