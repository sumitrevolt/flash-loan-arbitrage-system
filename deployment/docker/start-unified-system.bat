@echo off
:: Unified Docker Orchestration System Startup Script (Windows)
:: ============================================================

setlocal EnableDelayedExpansion

:: Configuration
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..
set COMPOSE_FILE=%SCRIPT_DIR%docker-compose.unified.yml
set ENV_FILE=%SCRIPT_DIR%.env
set LOG_FILE=%SCRIPT_DIR%logs\startup.log

:: Colors (limited in Windows CMD)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set PURPLE=[95m
set CYAN=[96m
set NC=[0m

echo.
echo %PURPLE%========================================%NC%
echo %PURPLE%🚀 UNIFIED DOCKER ORCHESTRATION SYSTEM%NC%
echo %PURPLE%========================================%NC%
echo.

:: Create logs directory
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

:: Initialize log file
echo Startup log - %date% %time% > "%LOG_FILE%"

echo %CYAN%[INFO]%NC% Starting unified Docker orchestration system...

:: Check if Docker is installed and running
docker --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Docker is not installed or not available
    pause
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% Docker is available

:: Check if Docker Compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo %RED%[ERROR]%NC% Docker Compose is not available
        pause
        exit /b 1
    ) else (
        set COMPOSE_CMD=docker-compose
    )
) else (
    set COMPOSE_CMD=docker compose
)

echo %GREEN%[SUCCESS]%NC% Docker Compose is available: !COMPOSE_CMD!

:: Check for required files
if not exist "%COMPOSE_FILE%" (
    echo %RED%[ERROR]%NC% Docker Compose file not found: %COMPOSE_FILE%
    pause
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% Docker Compose configuration found

:: Check for environment file
if not exist "%ENV_FILE%" (
    echo %YELLOW%[WARNING]%NC% Environment file not found: %ENV_FILE%
    echo %CYAN%[INFO]%NC% Copying from template...
    
    if exist "%SCRIPT_DIR%.env.template" (
        copy "%SCRIPT_DIR%.env.template" "%ENV_FILE%" >nul
        echo %YELLOW%[WARNING]%NC% Please edit %ENV_FILE% with your actual API keys
        echo %YELLOW%[WARNING]%NC% The system will start with default/demo values where possible
    ) else (
        echo %RED%[ERROR]%NC% Environment template not found
        pause
        exit /b 1
    )
)

echo %GREEN%[SUCCESS]%NC% Environment configuration ready

:: Start infrastructure services first
echo.
echo %PURPLE%[INFRASTRUCTURE]%NC% Starting core infrastructure services...
!COMPOSE_CMD! -f "%COMPOSE_FILE%" up -d postgres redis rabbitmq

:: Wait for infrastructure
echo %CYAN%[INFO]%NC% Waiting for infrastructure services to become ready...
timeout /t 30 /nobreak >nul

:: Start MCP servers
echo.
echo %PURPLE%[MCP SERVERS]%NC% Starting MCP servers...
!COMPOSE_CMD! -f "%COMPOSE_FILE%" up -d mcp-supermemory mcp-context7 mcp-filesystem mcp-taskmanager

:: Wait for MCP servers
echo %CYAN%[INFO]%NC% Waiting for MCP servers to become ready...
timeout /t 20 /nobreak >nul

:: Start coordinators
echo.
echo %PURPLE%[COORDINATORS]%NC% Starting LangChain and AutoGen coordinators...
!COMPOSE_CMD! -f "%COMPOSE_FILE%" up -d langchain-coordinator autogen-coordinator

:: Wait for coordinators
echo %CYAN%[INFO]%NC% Waiting for coordinators to become ready...
timeout /t 30 /nobreak >nul

:: Start monitoring services
echo.
echo %PURPLE%[MONITORING]%NC% Starting monitoring services...
!COMPOSE_CMD! -f "%COMPOSE_FILE%" up -d system-monitor grafana elasticsearch kibana

:: Start remaining services
echo.
echo %PURPLE%[SERVICES]%NC% Starting remaining services...
!COMPOSE_CMD! -f "%COMPOSE_FILE%" up -d web-dashboard health-checker

:: Show status
echo.
echo %PURPLE%========================================%NC%
echo %PURPLE%🎉 STARTUP COMPLETE%NC%
echo %PURPLE%========================================%NC%
echo.

echo %GREEN%Service endpoints available:%NC%
echo   • Unified Dashboard: http://localhost:8090
echo   • LangChain Coordinator: http://localhost:8000
echo   • AutoGen Coordinator: http://localhost:8010
echo   • Grafana Monitoring: http://localhost:3000
echo   • Prometheus: http://localhost:9090
echo   • Kibana: http://localhost:5601
echo.

echo %CYAN%Management commands:%NC%
echo   • Stop system: stop-unified-system.bat
echo   • View logs: docker compose -f "%COMPOSE_FILE%" logs -f
echo   • System status: docker compose -f "%COMPOSE_FILE%" ps
echo.

echo %GREEN%🚀 Unified Docker Orchestration System is ready!%NC%
echo.

pause