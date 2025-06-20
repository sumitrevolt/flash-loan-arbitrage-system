@echo off
REM Master LangChain System Startup Script
REM ======================================

echo 🚀 Starting Master LangChain System...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Set project root
set PROJECT_ROOT=%~dp0

REM Create virtual environment if it doesn't exist
if not exist "%PROJECT_ROOT%venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv "%PROJECT_ROOT%venv"
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call "%PROJECT_ROOT%venv\Scripts\activate.bat"

REM Install/update requirements
if exist "%PROJECT_ROOT%requirements.txt" (
    echo 📥 Installing/updating Python packages...
    pip install -r "%PROJECT_ROOT%requirements.txt"
) else (
    echo 📥 Installing essential packages...
    pip install langchain langchain-community langchain-openai
    pip install aiohttp aiofiles requests psutil docker redis
    pip install pandas numpy matplotlib
    pip install openai tiktoken
    pip install faiss-cpu sentence-transformers
    pip install sqlalchemy
    pip install gitpython
)

REM Create log directories
if not exist "%PROJECT_ROOT%logs" mkdir "%PROJECT_ROOT%logs"
if not exist "%PROJECT_ROOT%training_data" mkdir "%PROJECT_ROOT%training_data"
if not exist "%PROJECT_ROOT%backups" mkdir "%PROJECT_ROOT%backups"

echo.
echo ✅ Environment setup complete!
echo.

REM Run the master system
echo 🚀 Starting Master LangChain System in Interactive Mode...
python "%PROJECT_ROOT%src\langchain_coordinators\master_langchain_system.py" --start-services --mode interactive

echo.
echo 👋 Master LangChain System has exited.
pause
