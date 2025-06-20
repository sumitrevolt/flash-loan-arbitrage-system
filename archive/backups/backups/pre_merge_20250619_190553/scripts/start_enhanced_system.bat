@echo off
echo ===============================================
echo Enhanced LangChain MCP System Launcher
echo ===============================================
echo.

REM Check if Python is available
python --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if pip is available
python -m pip --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    pause
    exit /b 1
)

echo Python and pip are available
echo.

REM Install dependencies if needed
echo Checking dependencies...
python -c "import langchain" > nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully
) else (
    echo Dependencies already satisfied
)
echo.

REM Check if Docker is available
docker --version > nul 2>&1
if errorlevel 1 (
    echo WARNING: Docker is not available
    echo Please install Docker Desktop from https://docker.com/get-started
    echo The system will continue but some features may not work
    echo.
) else (
    echo Docker is available
)

REM Launch the system
echo Launching Enhanced LangChain MCP System...
echo.
echo Dashboard will be available at: http://localhost:8000
echo Press Ctrl+C to stop the system
echo.

python launch_enhanced_system.py

echo.
echo System stopped
pause
