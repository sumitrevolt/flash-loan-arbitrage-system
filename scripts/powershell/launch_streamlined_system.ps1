# Flash Loan Task Orchestration System Launcher
# ============================================
# This script launches the complete task orchestration system

Write-Host "🚀 Flash Loan Task Orchestration System Launcher" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Set the working directory
$workDir = "c:\Users\Ratanshila\Documents\flash loan"
Set-Location $workDir

Write-Host "📁 Working directory: $workDir" -ForegroundColor Blue

# Check if Docker containers are running
Write-Host "🐳 Checking Docker containers..." -ForegroundColor Yellow
$containers = docker ps --filter "name=flashloan-" --format "table {{.Names}}\t{{.Status}}" 2>$null

if ($LASTEXITCODE -eq 0 -and $containers) {
    Write-Host "✅ Flash Loan containers are running" -ForegroundColor Green
    Write-Host $containers
} else {
    Write-Host "⚠️  Flash Loan containers not found. Make sure they are running." -ForegroundColor Red
    Write-Host "   You can start them with: docker-compose -f docker/docker-compose-complete.yml up -d"
    Write-Host ""
}

# Check Python installation
Write-Host "🐍 Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Install requirements if needed
$requirementsFile = "requirements-bridge.txt"
if (Test-Path $requirementsFile) {
    Write-Host "📦 Installing requirements..." -ForegroundColor Yellow
    pip install -r $requirementsFile --quiet
    Write-Host "✅ Requirements installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Requirements file not found, proceeding anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Starting Task Orchestration System..." -ForegroundColor Cyan
Write-Host "   • Service Discovery: Automatic" -ForegroundColor White
Write-Host "   • Task Management: Enabled" -ForegroundColor White  
Write-Host "   • Web Dashboard: http://localhost:8500/dashboard" -ForegroundColor White
Write-Host "   • API Documentation: http://localhost:8500/docs" -ForegroundColor White
Write-Host ""

# Launch the streamlined system
Write-Host "🚀 Launching system..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop the system" -ForegroundColor Yellow
Write-Host ""

try {
    python streamlined_system.py
} catch {
    Write-Host ""
    Write-Host "❌ System stopped with error: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "👋 System shutdown complete" -ForegroundColor Blue
}
