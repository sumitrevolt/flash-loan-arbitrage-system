# Enhanced LangChain MCP System Launcher for PowerShell
# ====================================================

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Enhanced LangChain MCP System Launcher" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✓ Python is available: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if pip is available
try {
    $pipVersion = python -m pip --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "pip not found"
    }
    Write-Host "✓ pip is available" -ForegroundColor Green
}
catch {
    Write-Host "✗ ERROR: pip is not available" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import langchain" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        python -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install dependencies"
        }
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "✓ Dependencies already satisfied" -ForegroundColor Green
    }
}
catch {
    Write-Host "✗ ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check if Docker is available
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not found"
    }
    Write-Host "✓ Docker is available: $dockerVersion" -ForegroundColor Green
    
    # Check if Docker daemon is running
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠ WARNING: Docker daemon is not running" -ForegroundColor Yellow
        Write-Host "Please start Docker Desktop" -ForegroundColor Yellow
    } else {
        Write-Host "✓ Docker daemon is running" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠ WARNING: Docker is not available" -ForegroundColor Yellow
    Write-Host "Please install Docker Desktop from https://docker.com/get-started" -ForegroundColor Yellow
    Write-Host "The system will continue but some features may not work" -ForegroundColor Yellow
}

Write-Host ""

# Launch the system
Write-Host "Launching Enhanced LangChain MCP System..." -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Dashboard will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "📊 API endpoints available at: http://localhost:8000/api/" -ForegroundColor Green
Write-Host "🔧 Press Ctrl+C to stop the system" -ForegroundColor Yellow
Write-Host ""

try {
    python launch_enhanced_system.py
}
catch {
    Write-Host "✗ ERROR: System launch failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
finally {
    Write-Host ""
    Write-Host "System stopped" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}
