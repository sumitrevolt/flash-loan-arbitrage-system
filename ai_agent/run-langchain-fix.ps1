#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run LangChain MCP Coordinator to fix all 21 MCP servers and 10 AI agents

.DESCRIPTION
    This script coordinates the fixing of all MCP servers and AI agents using LangChain.
    It will:
    1. Check system prerequisites
    2. Start Docker if needed
    3. Run the LangChain coordinator
    4. Monitor the fixing process
    5. Generate comprehensive report

.EXAMPLE
    .\run-langchain-fix.ps1
    .\run-langchain-fix.ps1 -Verbose
    .\run-langchain-fix.ps1 -DryRun

.NOTES
    Author: GitHub Copilot Assistant
    Date: June 15, 2025
#>

param(
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$Force
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow" 
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Test-Prerequisites {
    Write-ColoredOutput "🔍 Checking prerequisites..." -Color "Info"
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-ColoredOutput "✅ Docker: $dockerVersion" -Color "Success"
    }
    catch {
        Write-ColoredOutput "❌ Docker not found or not running" -Color "Error"
        Write-ColoredOutput "Please install Docker and ensure it's running" -Color "Warning"
        return $false
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-ColoredOutput "✅ Docker Compose: $composeVersion" -Color "Success"
    }
    catch {
        Write-ColoredOutput "❌ Docker Compose not found" -Color "Error"
        return $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-ColoredOutput "✅ Python: $pythonVersion" -Color "Success"
    }
    catch {
        Write-ColoredOutput "❌ Python not found" -Color "Error"
        return $false
    }
    
    # Check required Python packages
    $requiredPackages = @(
        "langchain",
        "openai", 
        "docker",
        "aiohttp",
        "psutil",
        "pyyaml"
    )
    
    foreach ($package in $requiredPackages) {
        try {
            $result = pip show $package 2>$null
            if ($result) {
                Write-ColoredOutput "✅ Python package: $package" -Color "Success"
            } else {
                Write-ColoredOutput "⚠️ Missing Python package: $package" -Color "Warning"
                Write-ColoredOutput "Installing $package..." -Color "Info"
                pip install $package
            }
        }
        catch {
            Write-ColoredOutput "❌ Failed to check/install $package" -Color "Error"
        }
    }
    
    return $true
}

function Start-DockerServices {
    Write-ColoredOutput "🐳 Starting Docker services..." -Color "Info"
    
    try {
        # Start Docker Desktop if on Windows
        if ($IsWindows -or $env:OS -eq "Windows_NT") {
            $dockerDesktop = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
            if (-not $dockerDesktop) {
                Write-ColoredOutput "Starting Docker Desktop..." -Color "Info"
                Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
                Start-Sleep -Seconds 30
            }
        }
        
        # Check if Docker daemon is running
        docker info | Out-Null
        Write-ColoredOutput "✅ Docker daemon is running" -Color "Success"
        
        # Start essential infrastructure services
        Write-ColoredOutput "Starting infrastructure services..." -Color "Info"
        docker-compose up -d redis postgres
        
        Start-Sleep -Seconds 10
        
        # Verify services are running
        $redisStatus = docker-compose ps redis --format "table {{.Status}}"
        $postgresStatus = docker-compose ps postgres --format "table {{.Status}}"
        
        Write-ColoredOutput "✅ Infrastructure services started" -Color "Success"
        
    }
    catch {
        Write-ColoredOutput "❌ Failed to start Docker services: $_" -Color "Error"
        return $false
    }
    
    return $true
}

function Invoke-LangChainCoordinator {
    param([bool]$DryRunMode = $false)
    
    Write-ColoredOutput "🚀 Starting LangChain MCP Coordinator..." -Color "Header"
    
    if ($DryRunMode) {
        Write-ColoredOutput "🧪 Running in DRY RUN mode - no actual changes will be made" -Color "Warning"
    }
    
    try {
        # Set environment variables
        $env:PYTHONPATH = $PWD
        $env:LANGCHAIN_VERBOSE = if ($Verbose) { "true" } else { "false" }
        $env:DRY_RUN = if ($DryRunMode) { "true" } else { "false" }
        
        # Check for OpenAI API key
        if (-not $env:OPENAI_API_KEY) {
            Write-ColoredOutput "⚠️ OPENAI_API_KEY not set. LangChain features may be limited." -Color "Warning"
            $apiKey = Read-Host "Enter your OpenAI API key (or press Enter to skip)"
            if ($apiKey) {
                $env:OPENAI_API_KEY = $apiKey
            }
        }
        
        # Run the coordinator
        Write-ColoredOutput "🤖 Executing LangChain MCP Coordinator..." -Color "Info"
        python langchain-mcp-coordinator.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColoredOutput "✅ LangChain coordination completed successfully!" -Color "Success"
        } else {
            Write-ColoredOutput "❌ LangChain coordination failed with exit code: $LASTEXITCODE" -Color "Error"
            return $false
        }
        
    }
    catch {
        Write-ColoredOutput "❌ Error running LangChain coordinator: $_" -Color "Error"
        return $false
    }
    
    return $true
}

function Show-SystemStatus {
    Write-ColoredOutput "📊 System Status Report" -Color "Header"
    Write-ColoredOutput "========================" -Color "Header"
    
    # Docker containers status
    Write-ColoredOutput "`n🐳 Docker Containers:" -Color "Info"
    try {
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        Write-Output $containers
    }
    catch {
        Write-ColoredOutput "❌ Failed to get container status" -Color "Error"
    }
    
    # System resources
    Write-ColoredOutput "`n💻 System Resources:" -Color "Info"
    try {
        $cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
        $memory = Get-WmiObject -Class Win32_OperatingSystem
        $memoryUsed = [math]::Round((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / $memory.TotalVisibleMemorySize) * 100, 2)
        
        Write-ColoredOutput "CPU Usage: $($cpu.Average)%" -Color "Info"
        Write-ColoredOutput "Memory Usage: $memoryUsed%" -Color "Info"
    }
    catch {
        Write-ColoredOutput "❌ Failed to get system resources" -Color "Error"
    }
    
    # Check latest logs
    Write-ColoredOutput "`n📋 Latest Fix Report:" -Color "Info"
    try {
        $latestReport = Get-ChildItem "logs\fix_report_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latestReport) {
            Write-ColoredOutput "Latest report: $($latestReport.Name)" -Color "Success"
            $reportContent = Get-Content $latestReport.FullName | ConvertFrom-Json
            Write-ColoredOutput "Overall Status: $($reportContent.overall_status)" -Color "Info"
            Write-ColoredOutput "Completion Time: $($reportContent.completion_time)" -Color "Info"
        } else {
            Write-ColoredOutput "No fix reports found" -Color "Warning"
        }
    }
    catch {
        Write-ColoredOutput "❌ Failed to read fix reports" -Color "Error"
    }
}

function Show-Help {
    Write-ColoredOutput @"
🚀 LangChain MCP Coordinator - Help
===================================

This script coordinates fixing all 21 MCP servers and 10 AI agents using LangChain.

USAGE:
    .\run-langchain-fix.ps1 [OPTIONS]

OPTIONS:
    -DryRun     Run in dry-run mode (no actual changes)
    -Verbose    Enable verbose output
    -Force      Force execution even if prerequisites fail
    -Help       Show this help message

EXAMPLES:
    .\run-langchain-fix.ps1                    # Normal execution
    .\run-langchain-fix.ps1 -DryRun           # Test run without changes
    .\run-langchain-fix.ps1 -Verbose          # Detailed output
    .\run-langchain-fix.ps1 -DryRun -Verbose  # Test with detailed output

WHAT IT DOES:
1. ✅ Checks system prerequisites (Docker, Python, packages)
2. 🐳 Starts Docker services if needed
3. 🤖 Runs LangChain coordinator to analyze and fix:
   - 21 MCP (Model Context Protocol) servers
   - 10 AI agents
   - Docker container orchestration
   - Health monitoring and recovery
4. 📊 Generates comprehensive fix report
5. 🔍 Shows system status

REQUIREMENTS:
- Docker Desktop (running)
- Python 3.8+
- OpenAI API key (for LangChain features)
- Required Python packages (auto-installed)

LOGS:
- Main log: langchain_mcp_coordinator.log
- Fix reports: logs/fix_report_*.json

"@ -Color "Info"
}

# Main execution
try {
    Write-ColoredOutput @"
🚀 LangChain MCP Coordinator
============================
Fixing 21 MCP Servers + 10 AI Agents
"@ -Color "Header"

    # Show help if requested
    if ($Help) {
        Show-Help
        exit 0
    }
    
    # Check prerequisites
    if (-not (Test-Prerequisites) -and -not $Force) {
        Write-ColoredOutput "❌ Prerequisites check failed. Use -Force to override." -Color "Error"
        exit 1
    }
    
    # Start Docker services
    if (-not (Start-DockerServices)) {
        Write-ColoredOutput "❌ Failed to start Docker services" -Color "Error"
        exit 1
    }
    
    # Run the coordinator
    $success = Invoke-LangChainCoordinator -DryRunMode:$DryRun
    
    # Show status report
    Show-SystemStatus
    
    if ($success) {
        Write-ColoredOutput "`n🎉 All systems fixed successfully!" -Color "Success"
        Write-ColoredOutput "Check logs/fix_report_*.json for detailed results" -Color "Info"
        exit 0
    } else {
        Write-ColoredOutput "`n❌ Some issues were encountered" -Color "Error"
        Write-ColoredOutput "Check langchain_mcp_coordinator.log for details" -Color "Warning"
        exit 1
    }
    
}
catch {
    Write-ColoredOutput "❌ Fatal error: $_" -Color "Error"
    Write-ColoredOutput $_.ScriptStackTrace -Color "Error"
    exit 1
}
