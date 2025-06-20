# Master LangChain System Startup Script (PowerShell) - Fixed
# ==========================================================

param(
    [switch]$CleanInstall = $false,
    [switch]$SkipDependencies = $false,
    [switch]$TestMode = $false
)

Write-Host "🚀 Starting Master LangChain System..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Set environment variables
$env:PYTHONPATH = "$ScriptDir;$ScriptDir\src"
$env:LANGCHAIN_PROJECT = "master_system"

Write-Host "📁 Working Directory: $ScriptDir" -ForegroundColor Yellow
Write-Host "🔧 PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Yellow

# Check Python installation
Write-Host "🐍 Checking Python installation..." -ForegroundColor Green
try {
    $PythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python found: $PythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and add it to your PATH" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
$VenvPath = ".\venv"
if (Test-Path $VenvPath) {
    Write-Host "📦 Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

if (-not $SkipDependencies) {
    # Upgrade pip first
    Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip setuptools wheel

    if ($CleanInstall) {
        Write-Host "🧹 Performing clean install..." -ForegroundColor Yellow
        # Remove any problematic packages
        pip uninstall -y eth-brownie cytoolz 2>$null
    }

    # Install critical packages first
    Write-Host "📦 Installing critical packages..." -ForegroundColor Yellow
    $CriticalPackages = @(
        "psutil>=5.9.0",
        "setuptools>=68.0.0", 
        "wheel>=0.41.0"
    )
    
    foreach ($Package in $CriticalPackages) {
        Write-Host "Installing $Package..." -ForegroundColor Cyan
        pip install $Package --no-cache-dir
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to install $Package" -ForegroundColor Red
        } else {
            Write-Host "✅ $Package installed successfully" -ForegroundColor Green
        }
    }
    
    # Install main requirements
    Write-Host "📦 Installing main dependencies..." -ForegroundColor Yellow
    Write-Host "Note: This may take several minutes..." -ForegroundColor Cyan
    
    pip install -r requirements.txt --no-cache-dir --timeout 300
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Some packages failed to install. Trying individual installation..." -ForegroundColor Yellow
        
        # Try to install essential packages individually
        $EssentialPackages = @(
            "langchain",
            "langchain-community",
            "langchain-openai", 
            "aiohttp",
            "requests",
            "pandas",
            "numpy",
            "web3",
            "rich",
            "click"
        )
        
        foreach ($Package in $EssentialPackages) {
            Write-Host "Installing $Package..." -ForegroundColor Cyan
            pip install $Package --no-cache-dir
        }
    } else {
        Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    }
}

# Test critical imports
Write-Host "🧪 Testing critical imports..." -ForegroundColor Yellow
$TestImports = @("psutil", "asyncio", "pathlib", "json", "logging", "aiohttp", "requests")
$FailedImports = @()

foreach ($ImportTest in $TestImports) {
    try {
        python -c "import $ImportTest; print('✅ $ImportTest OK')" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $FailedImports += $ImportTest
            Write-Host "❌ $ImportTest failed" -ForegroundColor Red
        } else {
            Write-Host "✅ $ImportTest OK" -ForegroundColor Green
        }
    } catch {
        $FailedImports += $ImportTest
        Write-Host "❌ $ImportTest failed" -ForegroundColor Red
    }
}

if ($FailedImports.Count -gt 0) {
    Write-Host "⚠️ Failed imports: $($FailedImports -join ', ')" -ForegroundColor Yellow
    if ($TestMode) {
        Write-Host "In test mode, stopping due to failed imports" -ForegroundColor Red
        exit 1
    }
}

# Create necessary directories
$Directories = @("logs", "data", "config", "backups")
foreach ($Dir in $Directories) {
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        Write-Host "📁 Created directory: $Dir" -ForegroundColor Green
    }
}

# Check for required files
$RequiredFiles = @(
    "src\langchain_coordinators\master_langchain_system.py"
)

$MissingFiles = @()
foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        $MissingFiles += $File
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "❌ Missing required files:" -ForegroundColor Red
    foreach ($File in $MissingFiles) {
        Write-Host "   - $File" -ForegroundColor Red
    }
    Write-Host "Please ensure all system files are present" -ForegroundColor Yellow
    exit 1
}

if ($TestMode) {
    Write-Host "✅ Test mode complete - all checks passed!" -ForegroundColor Green
    exit 0
}

# Start the system
Write-Host "🎯 Starting Master LangChain System..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the system" -ForegroundColor Yellow
Write-Host "" 

try {
    python -c "
import sys
import os
sys.path.insert(0, r'$ScriptDir')
sys.path.insert(0, r'$ScriptDir\src')
os.chdir(r'$ScriptDir')

try:
    from src.langchain_coordinators.master_langchain_system import MasterLangChainSystem
    import asyncio
    
    async def main():
        system = MasterLangChainSystem()
        await system.start()
    
    if __name__ == '__main__':
        asyncio.run(main())
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"
} catch {
    Write-Host "❌ Error starting system: $_" -ForegroundColor Red
    Write-Host "Check the logs for more details" -ForegroundColor Yellow
    exit 1
}

Write-Host "👋 System shutdown complete" -ForegroundColor Green
