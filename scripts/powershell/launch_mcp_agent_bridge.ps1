# MCP-Agent Connection Bridge Launcher
# ====================================
# PowerShell script to start the MCP-Agent connection bridge on Windows
# 
# Usage:
#   .\launch_mcp_agent_bridge.ps1                # Start full system
#   .\launch_mcp_agent_bridge.ps1 -BridgeOnly    # Start bridge only
#   .\launch_mcp_agent_bridge.ps1 -ApiOnly       # Start API only
#   .\launch_mcp_agent_bridge.ps1 -CheckOnly     # Check prerequisites only
#
# Author: GitHub Copilot Assistant
# Date: June 18, 2025

param(
    [switch]$BridgeOnly,
    [switch]$ApiOnly,
    [switch]$CheckOnly,
    [switch]$Help
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$Cyan = "Cyan"

function Write-ColorOutput {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-ColorOutput "🌉 MCP-Agent Connection Bridge Launcher" $Blue
    Write-ColorOutput "=======================================" $Blue
    Write-ColorOutput ""
    Write-ColorOutput "This script launches the connection bridge between MCP servers and AI agents." $Cyan
    Write-ColorOutput ""
    Write-ColorOutput "Usage:" $Yellow
    Write-ColorOutput "  .\launch_mcp_agent_bridge.ps1                # Start full system (bridge + API)" $Green
    Write-ColorOutput "  .\launch_mcp_agent_bridge.ps1 -BridgeOnly    # Start bridge only" $Green
    Write-ColorOutput "  .\launch_mcp_agent_bridge.ps1 -ApiOnly       # Start API only" $Green
    Write-ColorOutput "  .\launch_mcp_agent_bridge.ps1 -CheckOnly     # Check prerequisites only" $Green
    Write-ColorOutput "  .\launch_mcp_agent_bridge.ps1 -Help          # Show this help" $Green
    Write-ColorOutput ""
    Write-ColorOutput "Features:" $Yellow
    Write-ColorOutput "  • Auto-discovery of Docker containers" $Cyan
    Write-ColorOutput "  • Real-time health monitoring" $Cyan
    Write-ColorOutput "  • Task coordination between services" $Cyan
    Write-ColorOutput "  • Web dashboard at http://localhost:8500/dashboard" $Cyan
    Write-ColorOutput "  • REST API for programmatic control" $Cyan
    Write-ColorOutput ""
}

function Test-Prerequisites {
    Write-ColorOutput "🔍 Checking prerequisites..." $Blue
    
    $allGood = $true
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Python found: $pythonVersion" $Green
        } else {
            Write-ColorOutput "❌ Python not found or not in PATH" $Red
            $allGood = $false
        }
    } catch {
        Write-ColorOutput "❌ Python not found or not in PATH" $Red
        $allGood = $false
    }
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Docker found: $dockerVersion" $Green
            
            # Check Docker containers
            $mcpContainers = docker ps --filter "name=mcp" --format "{{.Names}}" 2>$null
            $agentContainers = docker ps --filter "name=agent" --format "{{.Names}}" 2>$null
            
            if ($mcpContainers) {
                $mcpCount = ($mcpContainers | Measure-Object).Count
                Write-ColorOutput "✅ Found $mcpCount MCP server containers running" $Green
            } else {
                Write-ColorOutput "⚠️ No MCP server containers found running" $Yellow
            }
            
            if ($agentContainers) {
                $agentCount = ($agentContainers | Measure-Object).Count
                Write-ColorOutput "✅ Found $agentCount AI agent containers running" $Green
            } else {
                Write-ColorOutput "⚠️ No AI agent containers found running" $Yellow
            }
            
        } else {
            Write-ColorOutput "❌ Docker not found or not running" $Red
            $allGood = $false
        }
    } catch {
        Write-ColorOutput "❌ Docker not found or not running" $Red
        $allGood = $false
    }
    
    # Check required Python packages
    $requiredPackages = @("aiohttp", "fastapi", "docker", "redis")
    foreach ($package in $requiredPackages) {
        try {
            $result = python -c "import $package; print('OK')" 2>&1
            if ($LASTEXITCODE -eq 0 -and $result -eq "OK") {
                Write-ColorOutput "✅ Python package '$package' is available" $Green
            } else {
                Write-ColorOutput "⚠️ Python package '$package' not found (will try to install)" $Yellow
            }
        } catch {
            Write-ColorOutput "⚠️ Python package '$package' not found (will try to install)" $Yellow
        }
    }
    
    # Check Redis (optional)
    try {
        $redisCheck = python -c "import redis; r=redis.Redis(host='localhost', port=6379); r.ping(); print('Redis OK')" 2>&1
        if ($LASTEXITCODE -eq 0 -and $redisCheck -like "*Redis OK*") {
            Write-ColorOutput "✅ Redis is available for inter-service communication" $Green        } else {
            Write-ColorOutput "WARNING Redis not available (optional, but recommended)" $Yellow
        }
    } catch {
        Write-ColorOutput "WARNING Redis not available (optional, but recommended)" $Yellow
    }
    
    return $allGood
}

function Install-Dependencies {
    Write-ColorOutput "📦 Installing Python dependencies..." $Blue
    
    if (Test-Path "requirements-bridge.txt") {
        try {
            python -m pip install -r requirements-bridge.txt
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Dependencies installed successfully" $Green
                return $true
            } else {
                Write-ColorOutput "❌ Failed to install dependencies" $Red
                return $false
            }
        } catch {
            Write-ColorOutput "❌ Error installing dependencies" $Red
            return $false
        }
    } else {
        Write-ColorOutput "⚠️ requirements-bridge.txt not found, trying individual packages..." $Yellow
        
        $packages = @("aiohttp", "fastapi", "uvicorn", "docker", "redis", "websockets")
        foreach ($package in $packages) {
            try {
                python -m pip install $package
                Write-ColorOutput "✅ Installed $package" $Green
            } catch {
                Write-ColorOutput "⚠️ Failed to install $package" $Yellow
            }
        }
        return $true
    }
}

function Start-Bridge {
    param($Mode = "full")
    
    Write-ColorOutput "🚀 Starting MCP-Agent Connection Bridge..." $Blue
      # Prepare arguments
    $bridgeArgs = @()
    if ($Mode -eq "bridge-only") {
        $bridgeArgs += "--bridge-only"
        Write-ColorOutput "🌉 Starting in bridge-only mode" $Cyan
    } elseif ($Mode -eq "api-only") {
        $bridgeArgs += "--api-only"
        Write-ColorOutput "🔌 Starting in API-only mode" $Cyan
    } else {
        Write-ColorOutput "🎯 Starting full system (bridge + API)" $Cyan
    }
    
    try {
        if ($bridgeArgs.Count -gt 0) {
            python start_mcp_agent_bridge.py @bridgeArgs
        } else {
            python start_mcp_agent_bridge.py
        }
    } catch {
        Write-ColorOutput "❌ Error starting bridge: $_" $Red
        return $false
    }
    
    return $true
}

# Main execution
Write-ColorOutput ""
Write-ColorOutput "🌉 MCP-Agent Connection Bridge Launcher" $Blue
Write-ColorOutput "=======================================" $Blue
Write-ColorOutput ""

if ($Help) {
    Show-Help
    exit 0
}

# Check prerequisites
if (-not (Test-Prerequisites)) {
    Write-ColorOutput ""
    Write-ColorOutput "❌ Prerequisites check failed." $Red
    Write-ColorOutput "Please ensure Python and Docker are installed and running." $Yellow
    Write-ColorOutput "You may also need to install Python dependencies." $Yellow
    Write-ColorOutput ""
    Write-ColorOutput "To install dependencies, run:" $Cyan
    Write-ColorOutput "  pip install -r requirements-bridge.txt" $Green
    Write-ColorOutput ""
    exit 1
}

if ($CheckOnly) {
    Write-ColorOutput ""
    Write-ColorOutput "✅ All prerequisites are met!" $Green
    Write-ColorOutput "You can now start the bridge." $Cyan
    exit 0
}

# Try to install dependencies
Write-ColorOutput ""
if (-not (Install-Dependencies)) {
    Write-ColorOutput "⚠️ Some dependencies may be missing, but continuing..." $Yellow
}

# Determine mode and start
Write-ColorOutput ""
if ($BridgeOnly) {
    $result = Start-Bridge "bridge-only"
} elseif ($ApiOnly) {
    $result = Start-Bridge "api-only"
} else {
    $result = Start-Bridge "full"
    if ($result) {
        Write-ColorOutput ""
        Write-ColorOutput "🌐 Web dashboard available at: http://localhost:8500/dashboard" $Cyan
        Write-ColorOutput "📡 API documentation at: http://localhost:8500/docs" $Cyan
        Write-ColorOutput ""
    }
}

if ($result) {
    Write-ColorOutput ""
    Write-ColorOutput "🏁 MCP-Agent Bridge stopped successfully" $Green
} else {
    Write-ColorOutput ""
    Write-ColorOutput "💥 MCP-Agent Bridge encountered errors" $Red
    exit 1
}
