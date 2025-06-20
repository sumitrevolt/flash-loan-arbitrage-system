@echo off
echo Starting Docker Desktop and troubleshooting...
echo.

REM Check if Docker Desktop is installed
where "Docker Desktop.exe" >nul 2>&1
if errorlevel 1 (
    echo Docker Desktop is not installed!
    echo Please install it from: https://www.docker.com/products/docker-desktop-windows
    pause
    exit /b 1
)

REM Start Docker Desktop
echo Starting Docker Desktop...
start "" "Docker Desktop.exe"

echo Waiting for Docker to start (this may take 1-2 minutes)...
timeout /t 30 /nobreak >nul

REM Check if Docker is running
:check_docker
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker is still starting... waiting...
    timeout /t 10 /nobreak >nul
    goto check_docker
)

echo Docker is now running!
echo.

REM Run the troubleshooting script
echo Running Docker troubleshooting script...
python docker_troubleshoot.py

echo.
echo Docker setup completed!
echo You can now run your flash loan services.
pause
