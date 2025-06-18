@echo off
REM Quick Start Script for MCP Docker System
REM This will launch your entire flash loan MCP system

echo.
echo 🚀 QUICK START: MCP DOCKER SYSTEM
echo ================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    echo    Then run this script again.
    pause
    exit /b 1
)

echo ✅ Docker is running
echo.

REM Change to script directory
cd /d "%~dp0"

echo 📋 Starting MCP System Components...
echo.

REM Start infrastructure first
echo 🏗️  Phase 1: Starting Infrastructure (Redis, PostgreSQL, RabbitMQ)...
docker-compose -f docker/compose/docker-compose.yml up -d redis postgres rabbitmq prometheus grafana
if errorlevel 1 (
    echo ❌ Failed to start infrastructure
    pause
    exit /b 1
)

echo ✅ Infrastructure started
echo.
echo ⏳ Waiting 15 seconds for services to initialize...
timeout /t 15 /nobreak >nul

REM Start MCP Coordinator
echo 🎯 Phase 2: Starting MCP Coordinator Hub...
docker-compose -f docker/compose/docker-compose.yml up -d mcp-coordinator
if errorlevel 1 (
    echo ❌ Failed to start MCP Coordinator
    pause
    exit /b 1
)

echo ✅ MCP Coordinator started
echo.
echo ⏳ Waiting 10 seconds for coordinator to initialize...
timeout /t 10 /nobreak >nul

REM Start all MCP servers
echo 🤖 Phase 3: Starting All 21 MCP Servers...
docker-compose -f docker/compose/docker-compose.mcp-servers.yml up -d
if errorlevel 1 (
    echo ❌ Failed to start MCP servers
    pause
    exit /b 1
)

echo ✅ All MCP servers started
echo.

REM Quick status check
echo 📊 Quick Status Check...
docker ps --filter "name=mcp-" --format "table {{.Names}}\t{{.Status}}" | findstr "mcp-"

echo.
echo 🎉 MCP DOCKER SYSTEM STARTED SUCCESSFULLY!
echo ==========================================
echo.
echo 🌐 Access Points:
echo    • MCP Coordinator: http://localhost:3000
echo    • Dashboard: http://localhost:8080  
echo    • Grafana: http://localhost:3030 (admin/admin)
echo    • RabbitMQ: http://localhost:15672 (mcp_admin/mcp_secure_2025)
echo.
echo 🔧 Useful Commands:
echo    • Check status: python check-mcp-status.py
echo    • View logs: docker-compose logs -f [service_name]
echo    • Stop system: docker-compose -f docker/compose/docker-compose.yml down
echo.
echo ✅ Ready for flash loan operations!
echo.
pause
