@echo off
echo Starting MCP Training System...
echo.

REM Change to project directory
cd /d "%~dp0\.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create necessary directories
if not exist "models" mkdir models
if not exist "logs" mkdir logs

REM Install requirements if needed
echo Checking Python dependencies...
pip install -r requirements.txt >nul 2>&1

REM Run the training script
echo.
echo Running MCP training coordinator...
python scripts/start_training.py

echo.
echo Training completed. Check the results above.
pause
