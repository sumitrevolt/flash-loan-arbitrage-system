@echo off
REM GitHub MCP Server Startup Script for Windows

echo Starting GitHub MCP Services...

REM Check if GitHub token is set
if "%GITHUB_PERSONAL_ACCESS_TOKEN%"=="" (
    echo ERROR: GITHUB_PERSONAL_ACCESS_TOKEN environment variable not set
    echo Please set your GitHub Personal Access Token:
    echo set GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
    pause
    exit /b 1
)

REM Pull latest images
echo Pulling latest images...
docker pull ghcr.io/github/github-mcp-server
docker pull ghcr.io/cyanheads/filesystem-mcp-server

REM Start services
echo Starting GitHub MCP services...
docker-compose -f mcp_servers/docker-compose.github-mcp.yml up -d

REM Wait for services to be ready
echo Waiting for services to start...
timeout /t 10 /nobreak

REM Check service status
echo Checking service status...
docker-compose -f mcp_servers/docker-compose.github-mcp.yml ps

echo GitHub MCP services started successfully!
echo.
echo Available services:
echo - GitHub MCP Server: http://localhost:8017
echo - Filesystem MCP Server: http://localhost:8018
echo.
echo To test GitHub MCP server:
echo docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server --toolsets repos

pause
