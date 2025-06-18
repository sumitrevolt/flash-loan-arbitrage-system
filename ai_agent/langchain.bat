@echo off
REM LangChain Flash Loan AI - Batch Commands
REM Usage: langchain.bat [command] [options]

set "PROJECT_DIR=%cd%"

echo.
echo 🤖 LangChain Flash Loan AI Controller
echo ====================================

if "%1"=="help" goto help
if "%1"=="test" goto test
if "%1"=="analyze" goto analyze
if "%1"=="decision" goto decision
if "%1"=="strategy" goto strategy
if "%1"=="monitor" goto monitor
if "%1"=="demo" goto demo
if "%1"=="setup" goto setup
if "%1"=="status" goto status
if "%1"=="" goto help

echo ❌ Unknown command: %1
echo Run 'langchain.bat help' for available commands
goto end

:help
echo.
echo 📚 Available Commands:
echo   help      - Show this help message
echo   test      - Test LangChain connection
echo   analyze   - Analyze current market conditions
echo   decision  - Get flash loan execution decision
echo   strategy  - Generate trading strategy
echo   monitor   - Start continuous monitoring
echo   demo      - Run the full demo
echo   setup     - Setup environment file
echo   status    - Check system status
echo.
echo 💡 Examples:
echo   langchain.bat test
echo   langchain.bat analyze
echo   langchain.bat decision ETH USDC 10
echo   langchain.bat monitor 5
echo.
echo 🔧 Setup:
echo   1. langchain.bat setup
echo   2. Edit .env file with your OpenAI API key
echo   3. langchain.bat test
goto end

:setup
echo.
echo 🔧 Setting up environment...
if exist .env (
    echo ⚠️  .env file already exists
) else (
    copy .env.template .env >nul
    echo ✅ Created .env file from template
)
echo.
echo 📝 Next steps:
echo 1. Edit .env file and add your OpenAI API key:
echo    OPENAI_API_KEY=sk-your-key-here
echo 2. Run: langchain.bat test
echo.
echo 🗒️  Opening .env file for editing...
notepad .env
goto end

:test
echo.
echo 🧪 Testing LangChain connection...
node langchain-cli.js test
goto end

:analyze
echo.
echo 📊 Analyzing market conditions...
node langchain-cli.js analyze
goto end

:decision
set "tokenA=%2"
set "tokenB=%3"
set "amount=%4"
if "%tokenA%"=="" set "tokenA=ETH"
if "%tokenB%"=="" set "tokenB=USDC"
if "%amount%"=="" set "amount=10"

echo.
echo 🤔 Getting decision for %amount% %tokenA% -^> %tokenB%...
node langchain-cli.js decision %tokenA% %tokenB% %amount%
goto end

:strategy
echo.
echo 📋 Generating trading strategy...
node langchain-cli.js strategy
goto end

:monitor
set "interval=%2"
if "%interval%"=="" set "interval=5"
echo.
echo 🔄 Starting monitoring (every %interval% minutes)...
echo Press Ctrl+C to stop
node langchain-cli.js monitor %interval%
goto end

:demo
echo.
echo 🚀 Running full LangChain demo...
npm run demo
goto end

:status
echo.
echo 📋 System Status:

if exist .env (
    echo ✅ Environment file exists
    findstr /C:"OPENAI_API_KEY=sk-" .env >nul
    if errorlevel 1 (
        echo ❌ OpenAI API key not configured
    ) else (
        echo ✅ OpenAI API key configured
    )
) else (
    echo ❌ Environment file missing
)

if exist node_modules (
    echo ✅ Dependencies installed
) else (
    echo ❌ Dependencies missing - run 'npm install'
)

if exist ai_agent\langchain-integration.ts (
    echo ✅ LangChain integration files present
) else (
    echo ❌ Integration files missing
)
goto end

:end
echo.
