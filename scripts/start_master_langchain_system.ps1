# Master LangChain System Startup Script
# =====================================

param(
    [string]$Mode = "interactive",
    [switch]$StartServices,
    [switch]$Force
)

Write-Host "🚀 Starting Master LangChain System..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Set project root
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

# Create virtual environment if it doesn't exist
$venvPath = Join-Path $PROJECT_ROOT "venv"
if (-not (Test-Path $venvPath) -or $Force) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "⚠️ Could not find virtual environment activation script" -ForegroundColor Yellow
}

# Install/update requirements
$requirementsPath = Join-Path $PROJECT_ROOT "requirements.txt"
if (Test-Path $requirementsPath) {
    Write-Host "📥 Installing/updating Python packages from requirements.txt..." -ForegroundColor Yellow
    pip install -r $requirementsPath
} else {
    Write-Host "📥 Installing essential packages..." -ForegroundColor Yellow
    $packages = @(
        "langchain",
        "langchain-community", 
        "langchain-openai",
        "aiohttp",
        "aiofiles", 
        "requests",
        "psutil",
        "docker",
        "redis",
        "pandas",
        "numpy",
        "matplotlib",
        "openai",
        "tiktoken",
        "faiss-cpu",
        "sentence-transformers",
        "sqlalchemy",
        "gitpython"
    )
    
    foreach ($package in $packages) {
        Write-Host "  Installing $package..." -ForegroundColor Cyan
        pip install $package --quiet
    }
}

# Create necessary directories
$directories = @("logs", "training_data", "backups", "models")
foreach ($dir in $directories) {
    $dirPath = Join-Path $PROJECT_ROOT $dir
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        Write-Host "📁 Created directory: $dir" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "✅ Environment setup complete!" -ForegroundColor Green
Write-Host ""

# Prepare arguments
$scriptArgs = @()
if ($StartServices) {
    $scriptArgs += "--start-services"
}
$scriptArgs += "--mode", $Mode

# Run the master system
Write-Host "🚀 Starting Master LangChain System in $Mode mode..." -ForegroundColor Green
$masterScript = Join-Path $PROJECT_ROOT "src\langchain_coordinators\master_langchain_system.py"

try {
    python $masterScript @scriptArgs
} catch {
    Write-Host "❌ Error starting Master LangChain System: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "👋 Master LangChain System has exited." -ForegroundColor Yellow
