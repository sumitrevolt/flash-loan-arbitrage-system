@echo off
REM Flash Loan Arbitrage System Startup Script for Windows

echo 🚀 Starting Flash Loan Arbitrage System...

REM Check prerequisites
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is required but not installed
    exit /b 1
)

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is required but not installed
    exit /b 1
)

REM Load environment variables
if exist .env (
    for /f "tokens=*" %%i in (.env) do set %%i
)

REM Start services
set MODE=%1
if "%MODE%"=="" set MODE=development

if "%MODE%"=="development" (
    echo 🔧 Starting in development mode...
    npm run dev
) else if "%MODE%"=="production" (
    echo 🏭 Starting in production mode...
    docker-compose up -d
    echo ✅ Production services started
    echo 📊 Dashboard: http://localhost:8000
) else (
    echo ❌ Unknown mode: %MODE%
    echo Usage: %0 [development^|production]
    exit /b 1
)
