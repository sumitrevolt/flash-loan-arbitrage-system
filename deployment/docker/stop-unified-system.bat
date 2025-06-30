@echo off
:: Unified Docker Orchestration System Shutdown Script (Windows)
:: ===========================================================

setlocal EnableDelayedExpansion

:: Configuration
set SCRIPT_DIR=%~dp0
set COMPOSE_FILE=%SCRIPT_DIR%docker-compose.unified.yml
set LOG_FILE=%SCRIPT_DIR%logs\shutdown.log

:: Colors (limited in Windows CMD)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set PURPLE=[95m
set CYAN=[96m
set NC=[0m

:: Default options
set FORCE_STOP=false
set CLEANUP_VOLUMES=false
set REMOVE_IMAGES=false
set QUIET_MODE=false

:: Parse command line arguments
:parse_args
if "%~1"=="" goto start_shutdown
if "%~1"=="--help" goto show_usage
if "%~1"=="-h" goto show_usage
if "%~1"=="--force" set FORCE_STOP=true
if "%~1"=="-f" set FORCE_STOP=true
if "%~1"=="--cleanup" (
    set CLEANUP_VOLUMES=true
    set KEEP_DATA=false
)
if "%~1"=="-c" (
    set CLEANUP_VOLUMES=true
    set KEEP_DATA=false
)
if "%~1"=="--remove-images" set REMOVE_IMAGES=true
if "%~1"=="-r" set REMOVE_IMAGES=true
if "%~1"=="--quiet" set QUIET_MODE=true
if "%~1"=="-q" set QUIET_MODE=true
shift
goto parse_args

:show_usage
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   -h, --help          Show this help message
echo   -f, --force         Force stop all containers without graceful shutdown
echo   -c, --cleanup       Clean up volumes and networks (DESTRUCTIVE)
echo   -r, --remove-images Remove built images after stopping
echo   -q, --quiet         Quiet mode - minimal output
echo.
echo Examples:
echo   %0                  # Graceful shutdown, keep all data
echo   %0 --cleanup        # Stop and remove all volumes/networks
echo   %0 --force          # Force stop all containers immediately
echo   %0 --remove-images  # Stop and remove custom images
exit /b 0

:start_shutdown
:: Create logs directory
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

:: Initialize log file
echo Shutdown log - %date% %time% > "%LOG_FILE%"

if "%QUIET_MODE%"=="false" (
    echo.
    echo %PURPLE%========================================%NC%
    echo %PURPLE%🛑 UNIFIED SYSTEM SHUTDOWN%NC%
    echo %PURPLE%========================================%NC%
    echo.
)

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

:: Check if compose file exists
if not exist "%COMPOSE_FILE%" (
    echo %RED%[ERROR]%NC% Docker Compose file not found: %COMPOSE_FILE%
    pause
    exit /b 1
)

:: Confirmation for destructive operations
if "%CLEANUP_VOLUMES%"=="true" (
    if "%QUIET_MODE%"=="false" (
        echo %RED%⚠️  WARNING: This will permanently delete all data volumes!%NC%
        echo %RED%   This includes databases, logs, and all persistent data.%NC%
        echo.
        set /p CONFIRM="Are you sure you want to continue? [y/N]: "
        if /i not "!CONFIRM!"=="y" if /i not "!CONFIRM!"=="yes" (
            echo %CYAN%[INFO]%NC% Operation cancelled by user
            pause
            exit /b 0
        )
    )
)

:: Show shutdown strategy
if "%QUIET_MODE%"=="false" (
    echo %PURPLE%[SHUTDOWN STRATEGY]%NC%
    echo Force stop: %FORCE_STOP%
    echo Cleanup volumes: %CLEANUP_VOLUMES%
    echo Remove images: %REMOVE_IMAGES%
    echo.
)

:: Service shutdown
if "%QUIET_MODE%"=="false" echo %PURPLE%[STOPPING SERVICES]%NC%

if "%FORCE_STOP%"=="true" (
    echo %CYAN%[INFO]%NC% Force stopping all services...
    !COMPOSE_CMD! -f "%COMPOSE_FILE%" kill
    !COMPOSE_CMD! -f "%COMPOSE_FILE%" down --remove-orphans
) else (
    echo %CYAN%[INFO]%NC% Gracefully stopping services...
    
    :: Stop non-critical services first
    echo %CYAN%[INFO]%NC% Stopping monitoring and dashboard services...
    !COMPOSE_CMD! -f "%COMPOSE_FILE%" stop health-checker web-dashboard grafana kibana elasticsearch system-monitor 2>nul
    
    :: Stop coordination services
    echo %CYAN%[INFO]%NC% Stopping coordination services...
    !COMPOSE_CMD! -f "%COMPOSE_FILE%" stop langchain-coordinator autogen-coordinator 2>nul
    
    :: Stop MCP servers
    echo %CYAN%[INFO]%NC% Stopping MCP servers...
    !COMPOSE_CMD! -f "%COMPOSE_FILE%" stop mcp-taskmanager mcp-filesystem mcp-context7 mcp-supermemory 2>nul
    
    :: Stop infrastructure services last
    echo %CYAN%[INFO]%NC% Stopping infrastructure services...
    !COMPOSE_CMD! -f "%COMPOSE_FILE%" stop rabbitmq redis postgres 2>nul
    
    :: Remove containers
    echo %CYAN%[INFO]%NC% Removing containers...
    if "%CLEANUP_VOLUMES%"=="true" (
        !COMPOSE_CMD! -f "%COMPOSE_FILE%" down --volumes --remove-orphans
    ) else (
        !COMPOSE_CMD! -f "%COMPOSE_FILE%" down --remove-orphans
    )
)

echo %GREEN%[SUCCESS]%NC% All services stopped successfully

:: Volume cleanup
if "%CLEANUP_VOLUMES%"=="true" (
    if "%QUIET_MODE%"=="false" echo %PURPLE%[CLEANING UP VOLUMES]%NC%
    
    echo %CYAN%[INFO]%NC% Removing data volumes...
    
    :: Remove specific volumes
    docker volume rm flash-loan_postgres_data 2>nul
    docker volume rm flash-loan_redis_data 2>nul
    docker volume rm flash-loan_rabbitmq_data 2>nul
    docker volume rm flash-loan_vector_store_data 2>nul
    docker volume rm flash-loan_langchain_data 2>nul
    docker volume rm flash-loan_autogen_data 2>nul
    docker volume rm flash-loan_mcp_data 2>nul
    
    :: Remove orphaned volumes
    echo %CYAN%[INFO]%NC% Removing orphaned volumes...
    docker volume prune -f >nul 2>&1
    
    echo %GREEN%[SUCCESS]%NC% Volume cleanup completed
) else (
    if "%QUIET_MODE%"=="false" echo %CYAN%[INFO]%NC% Data volumes preserved (use --cleanup to remove)
)

:: Network cleanup
if "%CLEANUP_VOLUMES%"=="true" (
    if "%QUIET_MODE%"=="false" echo %PURPLE%[CLEANING UP NETWORKS]%NC%
    
    echo %CYAN%[INFO]%NC% Removing custom networks...
    docker network rm flash-loan-network 2>nul
    
    :: Remove orphaned networks
    echo %CYAN%[INFO]%NC% Removing orphaned networks...
    docker network prune -f >nul 2>&1
    
    echo %GREEN%[SUCCESS]%NC% Network cleanup completed
) else (
    if "%QUIET_MODE%"=="false" echo %CYAN%[INFO]%NC% Networks preserved (use --cleanup to remove)
)

:: Image cleanup
if "%REMOVE_IMAGES%"=="true" (
    if "%QUIET_MODE%"=="false" echo %PURPLE%[CLEANING UP IMAGES]%NC%
    
    echo %CYAN%[INFO]%NC% Removing custom built images...
    docker rmi flash-loan-langchain:latest 2>nul
    docker rmi flash-loan-autogen:latest 2>nul
    
    :: Remove dangling images
    echo %CYAN%[INFO]%NC% Removing dangling images...
    docker image prune -f >nul 2>&1
    
    echo %GREEN%[SUCCESS]%NC% Image cleanup completed
) else (
    if "%QUIET_MODE%"=="false" echo %CYAN%[INFO]%NC% Images preserved (use --remove-images to clean up)
)

:: System cleanup
if "%CLEANUP_VOLUMES%"=="true" (
    if "%QUIET_MODE%"=="false" echo %PURPLE%[SYSTEM CLEANUP]%NC%
    
    echo %CYAN%[INFO]%NC% Performing comprehensive Docker cleanup...
    docker container prune -f >nul 2>&1
    docker image prune -a -f >nul 2>&1
    docker builder prune -f >nul 2>&1
    
    echo %GREEN%[SUCCESS]%NC% System cleanup completed
)

:: Final status
if "%QUIET_MODE%"=="false" (
    echo.
    echo %PURPLE%========================================%NC%
    echo %PURPLE%📊 SHUTDOWN SUMMARY%NC%
    echo %PURPLE%========================================%NC%
    echo.
    
    :: Show remaining containers
    for /f %%i in ('docker ps -a --filter "name=flash-loan" --format "{{.Names}}" 2^>nul ^| find /c /v ""') do set REMAINING_COUNT=%%i
    
    if !REMAINING_COUNT! EQU 0 (
        echo %GREEN%✅ All flash-loan containers stopped and removed%NC%
    ) else (
        echo %YELLOW%⚠️ Some containers may still be running%NC%
        docker ps -a --filter "name=flash-loan" --format "table {{.Names}}\t{{.Status}}"
    )
    
    if "%CLEANUP_VOLUMES%"=="false" (
        echo.
        echo %CYAN%[INFO]%NC% 📦 Data volumes preserved for restart
    )
    
    echo.
    echo %PURPLE%🔄 RESTART INSTRUCTIONS%NC%
    
    if "%CLEANUP_VOLUMES%"=="true" (
        echo %CYAN%[INFO]%NC% Complete system cleanup performed.
        echo To restart the system:
        echo   1. Review and update: %SCRIPT_DIR%.env
        echo   2. Run: start-unified-system.bat
        echo   3. All data will be initialized fresh
    ) else (
        echo %CYAN%[INFO]%NC% Data preserved shutdown completed.
        echo To restart the system:
        echo   1. Run: start-unified-system.bat
        echo   2. All data and configurations will be restored
    )
    
    echo.
    echo %GREEN%🏁 Unified Docker Orchestration System shutdown completed!%NC%
    echo %CYAN%[INFO]%NC% Shutdown log saved to: %LOG_FILE%
) else (
    echo Shutdown completed successfully
)

pause