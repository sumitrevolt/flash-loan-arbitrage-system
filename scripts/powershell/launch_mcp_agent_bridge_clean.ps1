# MCP Agent Bridge Launcher Script
# Launches the MCP-Agent connection bridge and dashboard

# Color definitions for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"
$White = "White"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = $White
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check prerequisites
function Test-Prerequisites {
    param(
        [string[]]$RequiredPackages = @("fastapi", "uvicorn", "docker", "redis", "aioredis", "requests", "pydantic")
    )
    
    $allGood = $true
    
    Write-ColorOutput "`n=== Checking Prerequisites ===" $Blue
    
    # Check Python
    try {
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonCmd) {
            $pythonVersion = python --version 2>&1
            Write-ColorOutput "[OK] Python found: $pythonVersion" $Green
        } else {
            Write-ColorOutput "[ERROR] Python not found or not in PATH" $Red
            $allGood = $false
        }
    } catch {
        Write-ColorOutput "[ERROR] Python not found or not in PATH" $Red
        $allGood = $false
    }
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[OK] Docker found: $dockerVersion" $Green
            
            # Check running containers
            $mcpContainers = docker ps --filter "name=mcp" --format "table {{.Names}}" 2>&1
            if ($mcpContainers -and $mcpContainers.Count -gt 1) {
                $mcpCount = ($mcpContainers | Where-Object { $_ -notmatch "NAMES" }).Count
                Write-ColorOutput "[OK] Found $mcpCount MCP server containers running" $Green
            } else {
                Write-ColorOutput "[WARNING] No MCP server containers found running" $Yellow
            }
            
            $agentContainers = docker ps --filter "name=agent" --format "table {{.Names}}" 2>&1
            if ($agentContainers -and $agentContainers.Count -gt 1) {
                $agentCount = ($agentContainers | Where-Object { $_ -notmatch "NAMES" }).Count
                Write-ColorOutput "[OK] Found $agentCount AI agent containers running" $Green
            } else {
                Write-ColorOutput "[WARNING] No AI agent containers found running" $Yellow
            }
        } else {
            Write-ColorOutput "[ERROR] Docker not found or not running" $Red
            $allGood = $false
        }
    } catch {
        Write-ColorOutput "[ERROR] Docker not found or not running" $Red
        $allGood = $false
    }

    # Check Python packages
    foreach ($package in $RequiredPackages) {
        try {
            $packageCheck = python -c "import $package; print('OK')" 2>&1
            if ($LASTEXITCODE -eq 0 -and $packageCheck -like "*OK*") {
                Write-ColorOutput "[OK] Python package '$package' is available" $Green
            } else {
                Write-ColorOutput "[WARNING] Python package '$package' not found (will try to install)" $Yellow
                $allGood = $false
            }
        } catch {
            Write-ColorOutput "[WARNING] Python package '$package' not found (will try to install)" $Yellow
            $allGood = $false
        }
    }
    
    # Check Redis (optional)
    try {
        $redisCheck = python -c "import redis; r=redis.Redis(host='localhost', port=6379); r.ping(); print('Redis OK')" 2>&1
        if ($LASTEXITCODE -eq 0 -and $redisCheck -like "*Redis OK*") {
            Write-ColorOutput "[OK] Redis is available for inter-service communication" $Green
        } else {
            Write-ColorOutput "[WARNING] Redis not available (optional, but recommended)" $Yellow
        }
    } catch {
        Write-ColorOutput "[WARNING] Redis not available (optional, but recommended)" $Yellow
    }
    
    return $allGood
}

# Function to install dependencies
function Install-Dependencies {
    Write-ColorOutput "`n=== Installing Dependencies ===" $Blue
    
    if (Test-Path "requirements-bridge.txt") {
        try {
            Write-ColorOutput "Installing from requirements-bridge.txt..." $White
            $installResult = python -m pip install -r requirements-bridge.txt 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "[OK] Dependencies installed successfully" $Green
                return $true
            } else {
                Write-ColorOutput "[ERROR] Failed to install dependencies" $Red
                Write-ColorOutput "Error: $installResult" $Red
                return $false
            }
        } catch {
            Write-ColorOutput "[ERROR] Error installing dependencies" $Red
            return $false
        }
    } else {
        Write-ColorOutput "[WARNING] requirements-bridge.txt not found, trying individual packages..." $Yellow
        
        $packages = @("fastapi", "uvicorn", "docker", "redis", "aioredis", "requests", "pydantic")
        foreach ($package in $packages) {
            try {
                $result = python -m pip install $package 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput "[OK] Installed $package" $Green
                } else {
                    Write-ColorOutput "[WARNING] Failed to install $package" $Yellow
                }
            } catch {
                Write-ColorOutput "[WARNING] Error installing $package" $Yellow
            }
        }
        return $true
    }
}

# Main execution
function Start-Bridge {
    Write-ColorOutput "[LAUNCH] Starting MCP-Agent Connection Bridge..." $Blue
    
    # Check prerequisites
    $prereqsOk = Test-Prerequisites
    
    if (-not $prereqsOk) {
        Write-ColorOutput "`nSome prerequisites are missing. Attempting to install..." $Yellow
        $installOk = Install-Dependencies
        if (-not $installOk) {
            Write-ColorOutput "[ERROR] Failed to install all dependencies. Please install manually." $Red
            return $false
        }
    }
    
    Write-ColorOutput "`n=== Starting Bridge System ===" $Blue
    
    # Start the bridge with both bridge and API
    if (Test-Path "start_mcp_agent_bridge.py") {
        Write-ColorOutput "Launching MCP Agent Bridge with Dashboard API..." $White
        Write-ColorOutput "Bridge API will be available at: http://localhost:8500" $Green
        Write-ColorOutput "Press Ctrl+C to stop the bridge" $Yellow
        
        try {
            python start_mcp_agent_bridge.py --bridge --api
        } catch {
            Write-ColorOutput "[ERROR] Failed to start bridge system" $Red
            return $false
        }
    } else {
        Write-ColorOutput "[ERROR] start_mcp_agent_bridge.py not found in current directory" $Red
        return $false
    }
}

# Show help
function Show-Help {
    Write-ColorOutput "`nMCP Agent Bridge Launcher" $Blue
    Write-ColorOutput "=========================" $Blue
    Write-ColorOutput ""
    Write-ColorOutput "This script launches the MCP-Agent connection bridge system that:"
    Write-ColorOutput "- Discovers running MCP servers and AI agents in Docker"
    Write-ColorOutput "- Establishes connections between compatible services"
    Write-ColorOutput "- Provides health monitoring and status reporting"
    Write-ColorOutput "- Offers a web dashboard at http://localhost:8500"
    Write-ColorOutput ""
    Write-ColorOutput "Usage:" $Green
    Write-ColorOutput "  .\launch_mcp_agent_bridge_clean.ps1        # Start bridge and dashboard"
    Write-ColorOutput "  .\launch_mcp_agent_bridge_clean.ps1 -help  # Show this help"
    Write-ColorOutput ""
    Write-ColorOutput "Make sure Docker containers are running before starting the bridge." $Yellow
}

# Parse command line arguments
if ($args.Contains("-help") -or $args.Contains("--help") -or $args.Contains("-h")) {
    Show-Help
    exit 0
}

# Run the bridge
Write-ColorOutput "MCP Agent Bridge Launcher v1.0" $Blue
Write-ColorOutput "===============================" $Blue

$success = Start-Bridge
if ($success -eq $false) {
    Write-ColorOutput "`n[ERROR] Bridge startup failed. Check the logs above." $Red
    exit 1
} else {
    Write-ColorOutput "`n[OK] Bridge system shutdown gracefully." $Green
    exit 0
}
