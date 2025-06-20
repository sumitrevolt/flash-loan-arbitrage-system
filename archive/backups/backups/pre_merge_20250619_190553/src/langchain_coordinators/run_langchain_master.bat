@echo off
REM LangChain Master Coordinator Execution Script
REM ============================================
REM This script commands LangChain to fix all MCP servers and AI agents

echo ================================================================
echo COMMANDING LANGCHAIN TO FIX ALL MCP SERVERS AND AI AGENTS
echo ================================================================
echo.

echo [CONTROL] Starting LangChain Master Coordinator...
echo.

REM Change to the project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Install required packages if needed
echo [SETUP] Installing required Python packages...
pip install asyncio docker psutil aiohttp pyyaml 2>nul

REM Execute the master coordinator
echo [START] Executing LangChain Master Coordinator...
echo.
python langchain_master_coordinator.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo [ERROR] Master coordination failed!
    echo Check the logs for details: langchain_master_coordinator.log
) else (
    echo.
    echo [SUCCESS] Master coordination completed successfully!
)

echo.
echo [INFO] You can also use Docker Compose with the master configuration:
echo docker compose -f docker-compose.master.yml up -d
echo.

pause
