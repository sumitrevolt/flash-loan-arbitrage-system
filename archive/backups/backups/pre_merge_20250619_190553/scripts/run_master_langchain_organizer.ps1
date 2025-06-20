#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Master LangChain MCP Server & Agent Organizer Launcher
    
.DESCRIPTION
    This PowerShell script launches the Master LangChain MCP Organizer to:
    - Analyze all MCP servers and AI agents
    - Remove duplicates intelligently
    - Organize Docker configurations
    - Fix system issues
    - Optimize the entire system using LangChain multi-agent coordination
    
.EXAMPLE
    .\run_master_langchain_organizer.ps1
    
.EXAMPLE 
    .\run_master_langchain_organizer.ps1 -Verbose
#>

param(
    [switch]$Verbose,
    [switch]$Force,
    [switch]$SkipDependencies
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Enhanced logging function
function Write-EnhancedLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Color = "White"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "INFO" { Write-Host $logMessage -ForegroundColor $Color }
        default { Write-Host $logMessage -ForegroundColor White }
    }
}

# Banner function
function Show-Banner {
    Write-Host @"

🚀 Master LangChain MCP Server & Agent Organizer
============================================
    
🧠 LangChain Multi-Agent System
📡 MCP Server Organization  
🤖 AI Agent Coordination
🐳 Docker Optimization
🔧 System Fixing & Enhancement

Powered by GitHub Copilot Intelligence
Date: $(Get-Date -Format 'MMMM dd, yyyy')

"@ -ForegroundColor Cyan
}

# Check prerequisites
function Test-Prerequisites {
    Write-EnhancedLog "🔍 Checking prerequisites..." "INFO" "Cyan"
    
    $missing = @()
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [Version]$matches[1]
            if ($version -lt [Version]"3.8") {
                $missing += "Python 3.8+ (found $($matches[1]))"
            } else {
                Write-EnhancedLog "✅ Python: $pythonVersion" "SUCCESS"
            }
        }
    } catch {
        $missing += "Python 3.8+"
    }
    
    # Check pip
    try {
        pip --version | Out-Null
        Write-EnhancedLog "✅ pip is available" "SUCCESS"
    } catch {
        $missing += "pip"
    }
    
    # Check Docker
    try {
        docker --version | Out-Null
        Write-EnhancedLog "✅ Docker is available" "SUCCESS"
    } catch {
        Write-EnhancedLog "⚠️ Docker not available (some features will be limited)" "WARNING"
    }
    
    # Check Git
    try {
        git --version | Out-Null
        Write-EnhancedLog "✅ Git is available" "SUCCESS"
    } catch {
        Write-EnhancedLog "⚠️ Git not available" "WARNING"
    }
    
    if ($missing.Count -gt 0 -and -not $Force) {
        Write-EnhancedLog "❌ Missing prerequisites: $($missing -join ', ')" "ERROR"
        Write-EnhancedLog "Use -Force to continue anyway" "WARNING"
        exit 1
    }
    
    if ($missing.Count -eq 0) {
        Write-EnhancedLog "✅ All prerequisites satisfied" "SUCCESS"
    }
}

# Install Python dependencies
function Install-PythonDependencies {
    if ($SkipDependencies) {
        Write-EnhancedLog "⏭️ Skipping dependency installation" "WARNING"
        return
    }
    
    Write-EnhancedLog "📦 Installing Python dependencies..." "INFO" "Cyan"
    
    # Core dependencies
    $dependencies = @(
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5", 
        "langchain-community>=0.0.12",
        "openai>=1.0.0",
        "docker>=6.1.3",
        "redis>=5.0.1",
        "psycopg2-binary>=2.9.9",
        "aiohttp>=3.9.1",
        "pyyaml>=6.0.1",
        "psutil>=5.9.6",
        "numpy>=1.24.3",
        "faiss-cpu>=1.7.4",
        "sentence-transformers>=2.2.2"
    )
    
    foreach ($dep in $dependencies) {
        try {
            Write-EnhancedLog "Installing $dep..." "INFO"
            pip install $dep --quiet --disable-pip-version-check
            Write-EnhancedLog "✅ Installed $dep" "SUCCESS"
        } catch {
            Write-EnhancedLog "❌ Failed to install $dep" "ERROR"
        }
    }
    
    Write-EnhancedLog "✅ Python dependencies installation complete" "SUCCESS"
}

# Setup environment
function Initialize-Environment {
    Write-EnhancedLog "🔧 Setting up environment..." "INFO" "Cyan"
    
    # Set environment variables
    $env:PYTHONPATH = "$PWD;$($env:PYTHONPATH)"
    $env:LANGCHAIN_TRACING_V2 = "false"  # Disable tracing for performance
    $env:LANGCHAIN_CACHE_TYPE = "memory"
    
    # Create necessary directories
    $directories = @(
        "logs",
        "backup_duplicates", 
        "organized_project",
        "docker/optimized"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-EnhancedLog "📁 Created directory: $dir" "INFO"
        }
    }
    
    Write-EnhancedLog "✅ Environment setup complete" "SUCCESS"
}

# Check system resources
function Test-SystemResources {
    Write-EnhancedLog "💾 Checking system resources..." "INFO" "Cyan"
    
    # Check available memory
    $memory = Get-CimInstance -ClassName Win32_ComputerSystem
    $totalMemoryGB = [math]::Round($memory.TotalPhysicalMemory / 1GB, 2)
    
    if ($totalMemoryGB -lt 4) {
        Write-EnhancedLog "⚠️ Low memory: ${totalMemoryGB}GB (4GB+ recommended)" "WARNING"
    } else {
        Write-EnhancedLog "✅ Memory: ${totalMemoryGB}GB available" "SUCCESS"
    }
    
    # Check disk space
    $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='$($PWD.Drive)'"
    $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    
    if ($freeSpaceGB -lt 2) {
        Write-EnhancedLog "⚠️ Low disk space: ${freeSpaceGB}GB (2GB+ recommended)" "WARNING"
    } else {
        Write-EnhancedLog "✅ Disk space: ${freeSpaceGB}GB available" "SUCCESS"
    }
}

# Run the main organizer
function Start-LangChainOrganizer {
    Write-EnhancedLog "🚀 Starting Master LangChain MCP Organizer..." "INFO" "Cyan"
    
    try {
        # Check if the organizer script exists
        if (-not (Test-Path "master_langchain_mcp_organizer.py")) {
            Write-EnhancedLog "❌ master_langchain_mcp_organizer.py not found in current directory" "ERROR"
            exit 1
        }
        
        # Run the organizer
        if ($Verbose) {
            $env:PYTHONPATH = "$PWD;$($env:PYTHONPATH)"
            python master_langchain_mcp_organizer.py
        } else {
            $env:PYTHONPATH = "$PWD;$($env:PYTHONPATH)"
            python master_langchain_mcp_organizer.py 2>&1 | Tee-Object -FilePath "logs/organizer_output.log"
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-EnhancedLog "✅ Master LangChain MCP Organizer completed successfully!" "SUCCESS"
        } else {
            Write-EnhancedLog "❌ Master LangChain MCP Organizer failed with exit code $LASTEXITCODE" "ERROR"
            exit $LASTEXITCODE
        }
        
    } catch {
        Write-EnhancedLog "❌ Error running organizer: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Show results
function Show-Results {
    Write-EnhancedLog "📊 Showing results..." "INFO" "Cyan"
    
    # Check for generated files
    $resultFiles = @(
        "system_analysis_report.json",
        "organized_system_structure.json", 
        "docker/docker-compose.optimized.yml",
        "master_langchain_mcp_organizer.log"
    )
    
    Write-Host "`n📋 Generated Files:" -ForegroundColor Yellow
    foreach ($file in $resultFiles) {
        if (Test-Path $file) {
            $size = (Get-Item $file).Length
            Write-EnhancedLog "✅ $file ($([math]::Round($size/1KB, 2))KB)" "SUCCESS"
        } else {
            Write-EnhancedLog "❌ $file (not found)" "ERROR"
        }
    }
    
    # Show summary if analysis report exists
    if (Test-Path "system_analysis_report.json") {
        try {
            $report = Get-Content "system_analysis_report.json" | ConvertFrom-Json
            
            Write-Host "`n📈 System Analysis Summary:" -ForegroundColor Yellow
            Write-EnhancedLog "📡 Total MCP Servers: $($report.system_overview.total_mcp_servers)" "INFO"
            Write-EnhancedLog "🤖 Total AI Agents: $($report.system_overview.total_ai_agents)" "INFO"
            Write-EnhancedLog "🔍 Duplicates Found: $($report.system_overview.duplicates_found)" "INFO"
            Write-EnhancedLog "🔧 Health Issues: $($report.system_overview.health_issues)" "INFO"
            
        } catch {
            Write-EnhancedLog "⚠️ Could not parse analysis report" "WARNING"
        }
    }
    
    Write-Host "`n🎯 Next Steps:" -ForegroundColor Yellow
    Write-EnhancedLog "1. Review system_analysis_report.json for detailed analysis" "INFO"
    Write-EnhancedLog "2. Check docker/docker-compose.optimized.yml for optimized Docker config" "INFO"  
    Write-EnhancedLog "3. Review backup_duplicates/ for removed duplicate files" "INFO"
    Write-EnhancedLog "4. Run 'docker-compose -f docker/docker-compose.optimized.yml up -d' to deploy" "INFO"
}

# Cleanup function
function Invoke-Cleanup {
    Write-EnhancedLog "🧹 Performing cleanup..." "INFO" "Cyan"
    
    # Remove temporary files if they exist
    $tempFiles = @(
        "*.tmp",
        "__pycache__"
    )
    
    foreach ($pattern in $tempFiles) {
        $files = Get-ChildItem -Path . -Name $pattern -Recurse -Force -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            try {
                Remove-Item $file -Recurse -Force
                Write-EnhancedLog "🗑️ Removed $file" "INFO"
            } catch {
                # Ignore cleanup errors
            }
        }
    }
}

# Main execution
function Main {
    try {
        Show-Banner
        
        # Run all steps
        Test-Prerequisites
        Test-SystemResources 
        Initialize-Environment
        Install-PythonDependencies
        Start-LangChainOrganizer
        Show-Results
        
        Write-Host @"

🎉 Master LangChain MCP Organizer Complete! 
==========================================

Your MCP servers and AI agents have been analyzed, organized, and optimized using
advanced LangChain multi-agent coordination.

Check the generated reports and configurations for next steps.

"@ -ForegroundColor Green
        
    } catch {
        Write-EnhancedLog "❌ Fatal error: $($_.Exception.Message)" "ERROR"
        Write-EnhancedLog "💡 Try running with -Verbose for more details" "INFO"
        exit 1
    } finally {
        Invoke-Cleanup
    }
}

# Handle Ctrl+C gracefully
$null = Register-ObjectEvent -InputObject ([System.Console]) -EventName CancelKeyPress -Action {
    Write-Host "`n⏹️ Operation cancelled by user" -ForegroundColor Yellow
    Invoke-Cleanup
    exit 130
}

# Run main function
Main
