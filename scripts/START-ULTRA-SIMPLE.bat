@echo off
REM Ultra Simple MCP Docker System Starter

echo.
echo 🚀 ULTRA SIMPLE MCP DOCKER STARTER
echo ==================================
echo.

REM Change to script directory
cd /d "%~dp0"

echo 📋 Starting your MCP infrastructure...
echo.

REM Use existing MCP network or create a new one
echo 🌐 Setting up network...
docker network create flashloan-mcp-net 2>nul
if errorlevel 1 (
    echo    Network already exists or using existing one
) else (
    echo    ✅ Network created
)

echo.
echo 🔧 Starting core services...

REM Start Redis using simple docker run
echo 📦 Starting Redis...
docker run -d --name mcp-redis --network flashloan-mcp-net -p 6379:6379 redis:7-alpine

REM Start PostgreSQL
echo 📦 Starting PostgreSQL...
docker run -d --name mcp-postgres --network flashloan-mcp-net -p 5432:5432 -e POSTGRES_PASSWORD=mcp_password_2025 -e POSTGRES_DB=mcp_coordination postgres:15

REM Start RabbitMQ
echo 📦 Starting RabbitMQ...
docker run -d --name mcp-rabbitmq --network flashloan-mcp-net -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=mcp_admin -e RABBITMQ_DEFAULT_PASS=mcp_secure_2025 rabbitmq:3-management

REM Check if containers are running
echo.
echo 📊 Checking status...
timeout /t 5 /nobreak >nul

docker ps --filter "name=mcp-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo ✅ Basic MCP infrastructure is running!
echo.
echo 🌐 Access Points:
echo    • Redis: localhost:6379
echo    • PostgreSQL: localhost:5432 (mcp_password_2025)
echo    • RabbitMQ: http://localhost:15672 (mcp_admin/mcp_secure_2025)
echo.
echo 🔧 Next Steps:
echo    1. Your infrastructure is ready
echo    2. You can now start your MCP servers manually
echo    3. Check status: docker ps
echo    4. Stop all: docker stop mcp-redis mcp-postgres mcp-rabbitmq
echo.
pause
