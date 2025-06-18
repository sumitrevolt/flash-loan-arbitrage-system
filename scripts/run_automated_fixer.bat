@echo off
REM Automated LangChain Project Fixer Launcher
REM This script runs the comprehensive project-wide automated fix

echo ============================================
echo  Automated LangChain Project Fixer
echo ============================================
echo.

echo 🚀 Starting automated project-wide fix...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Install/upgrade required packages first
echo 📦 Installing/upgrading required packages...
pip install --upgrade pip
pip install langchain langchain-community langchain-openai langchain-core
pip install sentence-transformers faiss-cpu
pip install aiohttp asyncio-mqtt pyyaml python-dotenv
pip install uvicorn fastapi websockets typing-extensions

echo.
echo 🔧 Running automated project fixer...
echo.

REM Run the automated fixer
python automated_langchain_project_fixer.py

if errorlevel 1 (
    echo.
    echo ❌ Automated fix encountered errors. Check the log file for details.
    echo.
) else (
    echo.
    echo 🎉 Automated project fix completed successfully!
    echo.
    echo 📊 Check PROJECT_FIX_REPORT.md for detailed results
    echo 📝 Check automated_project_fixer.log for detailed logs
    echo.
    echo 🚀 Next steps:
    echo    1. Review the fix report
    echo    2. Test the system: python test_enhanced_system.py
    echo    3. Launch enhanced system: python launch_enhanced_system.py
    echo.
)

echo.
echo Press any key to exit...
pause >nul
