@echo off
echo 🚀 GitHub Copilot Multi-Agent System Test
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check for GitHub token
if "%GITHUB_TOKEN%"=="" (
    echo ⚠️  GITHUB_TOKEN environment variable not set
    echo.
    echo 🔧 To set up GitHub Copilot integration:
    echo    1. Go to: https://github.com/settings/tokens
    echo    2. Generate token with 'models' permission    echo    3. Set environment variable:
    echo       set GITHUB_TOKEN=github_pat_11AVGZXXA0M9a3SrL5fcGO_hLRJzHEEMWIntdFWHLa58u7gBaExlwuJH1WxA9s7bMCBZHQGRQZ

    echo.
    echo 💡 Or create a .env file with GITHUB_TOKEN=github_pat_11AVGZXXA0M9a3SrL5fcGO_hLRJzHEEMWIntdFWHLa58u7gBaExlwuJH1WxA9s7bMCBZHQGRQZ

    echo.
    pause
)

echo 🧪 Running GitHub Copilot Agent Tests...
python test_github_copilot_agents.py

echo ✅ Test completed
pause
