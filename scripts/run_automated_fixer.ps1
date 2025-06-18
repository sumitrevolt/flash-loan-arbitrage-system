# Automated LangChain Project Fixer Launcher (PowerShell)
# This script runs the comprehensive project-wide automated fix

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Automated LangChain Project Fixer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🚀 Starting automated project-wide fix..." -ForegroundColor Green
Write-Host ""

# Change to the script directory
Set-Location -Path $PSScriptRoot

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Install/upgrade required packages first
Write-Host "📦 Installing/upgrading required packages..." -ForegroundColor Yellow
try {
    pip install --upgrade pip
    pip install langchain langchain-community langchain-openai langchain-core
    pip install sentence-transformers faiss-cpu
    pip install aiohttp asyncio-mqtt pyyaml python-dotenv
    pip install uvicorn fastapi websockets typing-extensions
    Write-Host "✅ Packages installed successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some packages may have failed to install, continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Running automated project fixer..." -ForegroundColor Yellow
Write-Host ""

# Run the automated fixer
try {
    python automated_langchain_project_fixer.py
    
    Write-Host ""
    Write-Host "🎉 Automated project fix completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Check PROJECT_FIX_REPORT.md for detailed results" -ForegroundColor Cyan
    Write-Host "📝 Check automated_project_fixer.log for detailed logs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🚀 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Review the fix report" -ForegroundColor White
    Write-Host "   2. Test the system: python test_enhanced_system.py" -ForegroundColor White
    Write-Host "   3. Launch enhanced system: python launch_enhanced_system.py" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ Automated fix encountered errors. Check the log file for details." -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

Write-Host ""
Read-Host "Press Enter to exit"
