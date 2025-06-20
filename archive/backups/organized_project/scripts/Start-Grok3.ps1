# Grok 3 MCP Server - Windows PowerShell Startup Script
# Advanced coordination and agentic capabilities server

param(
    [switch]$Install,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Reset,
    [string]$Port = "3003",
    [string]$Host = "localhost"
)

$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Info = "Cyan"
    Success = "Green" 
    Warning = "Yellow"
    Error = "Red"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Show-Banner {
    Write-ColorOutput "=====================================" "Info"
    Write-ColorOutput "    Grok 3 MCP Server Manager       " "Info"
    Write-ColorOutput "  Advanced Agentic Coordination     " "Info"
    Write-ColorOutput "=====================================" "Info"
    Write-Host ""
}

function Test-PythonInstallation {
    Write-ColorOutput "Checking Python installation..." "Info"
    
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            
            if ($major -ge 3 -and $minor -ge 8) {
                Write-ColorOutput "✓ $pythonVersion" "Success"
                return $true
            } else {
                Write-ColorOutput "✗ Python 3.8+ required, found $pythonVersion" "Error"
                return $false
            }
        } else {
            Write-ColorOutput "✗ Could not determine Python version" "Error"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Python not found in PATH" "Error"
        return $false
    }
}

function Test-RequiredPorts {
    param([string]$TestPort = $Port)
    
    Write-ColorOutput "Checking port availability..." "Info"
    
    try {
        $connection = Test-NetConnection -ComputerName $Host -Port $TestPort -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-ColorOutput "✗ Port $TestPort is already in use" "Warning"
            return $false
        } else {
            Write-ColorOutput "✓ Port $TestPort is available" "Success"
            return $true
        }
    } catch {
        Write-ColorOutput "✓ Port $TestPort appears to be available" "Success"
        return $true
    }
}

function Install-Dependencies {
    Write-ColorOutput "Installing Python dependencies..." "Info"
    
    $currentDir = Get-Location
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir
    
    try {
        # Check if requirements.txt exists
        if (-not (Test-Path "requirements.txt")) {
            Write-ColorOutput "✗ requirements.txt not found" "Error"
            return $false
        }
        
        # Install requirements
        Write-ColorOutput "Installing packages from requirements.txt..." "Info"
        $installResult = python -m pip install -r requirements.txt 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ Dependencies installed successfully" "Success"
            return $true
        } else {
            Write-ColorOutput "✗ Failed to install dependencies" "Error"
            Write-ColorOutput $installResult "Error"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Error during installation: $($_.Exception.Message)" "Error"
        return $false
    } finally {
        Set-Location $currentDir
    }
}

function Start-Grok3Server {
    param([string]$ServerHost = $Host, [string]$ServerPort = $Port)
    
    Write-ColorOutput "Starting Grok 3 MCP Server..." "Info"
    
    $currentDir = Get-Location
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir
    
    try {
        # Check if server files exist
        if (-not (Test-Path "grok3_mcp_server.py")) {
            Write-ColorOutput "✗ grok3_mcp_server.py not found" "Error"
            return $false
        }
        
        Write-ColorOutput "Server starting on $ServerHost`:$ServerPort..." "Info"
        Write-ColorOutput "Press Ctrl+C to stop the server" "Warning"
        Write-Host ""
        
        # Start the server
        python start_grok3.py
        
    } catch {
        Write-ColorOutput "✗ Error starting server: $($_.Exception.Message)" "Error"
        return $false
    } finally {
        Set-Location $currentDir
    }
}

function Stop-Grok3Server {
    Write-ColorOutput "Stopping Grok 3 MCP Server..." "Info"
    
    try {
        # Find Python processes running grok3
        $processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*grok3*"
        }
        
        if ($processes) {
            foreach ($process in $processes) {
                Write-ColorOutput "Stopping process ID: $($process.Id)" "Info"
                Stop-Process -Id $process.Id -Force
            }
            Write-ColorOutput "✓ Server stopped" "Success"
        } else {
            Write-ColorOutput "No Grok 3 server processes found" "Warning"
        }
    } catch {
        Write-ColorOutput "✗ Error stopping server: $($_.Exception.Message)" "Error"
    }
}

function Get-ServerStatus {
    Write-ColorOutput "Checking Grok 3 MCP Server status..." "Info"
    
    try {
        # Check if server is responding
        $response = Invoke-WebRequest -Uri "http://$Host`:$Port/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "✓ Server is running and healthy" "Success"
            
            # Parse response for additional info
            try {
                $healthData = $response.Content | ConvertFrom-Json
                Write-ColorOutput "Server Name: $($healthData.name)" "Info"
                Write-ColorOutput "Status: $($healthData.status)" "Info"
                Write-ColorOutput "Uptime: $($healthData.uptime)" "Info"
            } catch {
                Write-ColorOutput "Server responding but health data unavailable" "Warning"
            }
        } else {
            Write-ColorOutput "✗ Server returned status code: $($response.StatusCode)" "Error"
        }
    } catch {
        Write-ColorOutput "✗ Server is not responding" "Error"
        Write-ColorOutput "Check if the server is running on $Host`:$Port" "Warning"
    }
}

function Reset-Grok3Server {
    Write-ColorOutput "Resetting Grok 3 MCP Server..." "Warning"
    
    $confirmation = Read-Host "This will stop the server and clear data. Continue? (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-ColorOutput "Reset cancelled" "Info"
        return
    }
    
    # Stop server
    Stop-Grok3Server
    
    # Clear data files
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $dataFiles = @(
        "$scriptDir\grok3_coordination.db",
        "$scriptDir\grok3_mcp_server.log",
        "$scriptDir\logs\*",
        "$scriptDir\temp\*"
    )
    
    foreach ($pattern in $dataFiles) {
        if (Test-Path $pattern) {
            Remove-Item $pattern -Force -Recurse -ErrorAction SilentlyContinue
            Write-ColorOutput "Cleared: $pattern" "Info"
        }
    }
    
    Write-ColorOutput "✓ Reset complete" "Success"
}

function Show-Help {
    Write-ColorOutput "Grok 3 MCP Server Management Commands:" "Info"
    Write-Host ""
    Write-ColorOutput "  -Install    Install Python dependencies" "Info"
    Write-ColorOutput "  -Start      Start the server" "Info" 
    Write-ColorOutput "  -Stop       Stop the server" "Info"
    Write-ColorOutput "  -Status     Check server status" "Info"
    Write-ColorOutput "  -Reset      Reset server and clear data" "Info"
    Write-Host ""
    Write-ColorOutput "  -Port       Specify port (default: 3003)" "Info"
    Write-ColorOutput "  -Host       Specify host (default: localhost)" "Info"
    Write-Host ""
    Write-ColorOutput "Examples:" "Info"
    Write-ColorOutput "  .\Start-Grok3.ps1 -Install" "Info"
    Write-ColorOutput "  .\Start-Grok3.ps1 -Start" "Info"
    Write-ColorOutput "  .\Start-Grok3.ps1 -Start -Port 3004" "Info"
    Write-ColorOutput "  .\Start-Grok3.ps1 -Status" "Info"
}

# Main execution
Show-Banner

# Check parameters
if (-not ($Install -or $Start -or $Stop -or $Status -or $Reset)) {
    Show-Help
    exit 0
}

# Validate Python installation
if (-not (Test-PythonInstallation)) {
    Write-ColorOutput "Please install Python 3.8+ and ensure it's in your PATH" "Error"
    exit 1
}

# Execute requested action
if ($Install) {
    if (Install-Dependencies) {
        Write-ColorOutput "Installation completed successfully!" "Success"
    } else {
        Write-ColorOutput "Installation failed!" "Error"
        exit 1
    }
}

if ($Stop) {
    Stop-Grok3Server
}

if ($Reset) {
    Reset-Grok3Server
}

if ($Status) {
    Get-ServerStatus
}

if ($Start) {
    # Check port availability
    if (-not (Test-RequiredPorts -TestPort $Port)) {
        Write-ColorOutput "Port conflict detected. Use -Port to specify a different port." "Warning"
    }
    
    Start-Grok3Server -ServerHost $Host -ServerPort $Port
}

Write-Host ""
Write-ColorOutput "Grok 3 MCP Server management complete." "Success"
