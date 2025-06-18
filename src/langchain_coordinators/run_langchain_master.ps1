# LangChain Master Coordinator - PowerShell Execution Script
# =========================================================
# This script commands LangChain to fix all MCP servers and AI agents with proper coordination

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "COMMANDING LANGCHAIN TO FIX ALL MCP SERVERS AND AI AGENTS" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host

Write-Host "[CONTROL] Starting LangChain Master Coordinator..." -ForegroundColor Green
Write-Host

# Change to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Python version: $pythonVersion" -ForegroundColor Blue
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install required packages
Write-Host "[SETUP] Installing required Python packages..." -ForegroundColor Blue
try {
    pip install asyncio docker psutil aiohttp pyyaml 2>$null
    Write-Host "[SUCCESS] Python packages installed" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Some packages may already be installed" -ForegroundColor Yellow
}

# Option 1: Run Python Coordinator
Write-Host
Write-Host "Choose execution method:" -ForegroundColor Cyan
Write-Host "1. Run Python LangChain Master Coordinator" -ForegroundColor White
Write-Host "2. Run Docker Compose Master Configuration" -ForegroundColor White
Write-Host "3. Run both (Python first, then Docker)" -ForegroundColor White
Write-Host

$choice = Read-Host "Enter your choice (1, 2, or 3)"

switch ($choice) {
    "1" {
        Write-Host "[START] Executing Python LangChain Master Coordinator..." -ForegroundColor Green
        Write-Host
        
        try {
            python langchain_master_coordinator.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host
                Write-Host "[SUCCESS] Python Master coordination completed successfully!" -ForegroundColor Green
            } else {
                Write-Host
                Write-Host "[ERROR] Python Master coordination failed!" -ForegroundColor Red
                Write-Host "Check the logs for details: langchain_master_coordinator.log" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERROR] Failed to execute Python coordinator: $_" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host "[START] Executing Docker Compose Master Configuration..." -ForegroundColor Green
        Write-Host
        
        try {
            # Check if Docker is available
            docker --version 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] Docker is not installed or not running" -ForegroundColor Red
                Write-Host "Please install Docker Desktop and try again" -ForegroundColor Red
                Read-Host "Press Enter to exit"
                exit 1
            }
            
            Write-Host "[INFO] Starting all services with Docker Compose..." -ForegroundColor Blue
            docker compose -f docker-compose.master.yml up -d
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host
                Write-Host "[SUCCESS] Docker Master configuration started successfully!" -ForegroundColor Green
                Write-Host
                Write-Host "Services Status:" -ForegroundColor Cyan
                docker compose -f docker-compose.master.yml ps
                Write-Host
                Write-Host "Access points:" -ForegroundColor Cyan
                Write-Host "- Master Coordinator Dashboard: http://localhost:8080" -ForegroundColor White
                Write-Host "- Grafana Monitoring: http://localhost:3001 (admin/admin_secure_2025)" -ForegroundColor White
                Write-Host "- Prometheus Metrics: http://localhost:9090" -ForegroundColor White
                Write-Host "- RabbitMQ Management: http://localhost:15672 (mcp_admin/mcp_secure_2025)" -ForegroundColor White
            } else {
                Write-Host
                Write-Host "[ERROR] Docker Master configuration failed!" -ForegroundColor Red
                Write-Host "Check Docker logs for details" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERROR] Failed to execute Docker Compose: $_" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host "[START] Executing Combined Python + Docker coordination..." -ForegroundColor Green
        Write-Host
        
        # First run Python coordinator
        Write-Host "[PHASE 1] Running Python LangChain Master Coordinator..." -ForegroundColor Blue
        try {
            python langchain_master_coordinator.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[SUCCESS] Python coordination completed!" -ForegroundColor Green
            } else {
                Write-Host "[WARNING] Python coordination had issues, continuing..." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[WARNING] Python coordinator failed, continuing with Docker..." -ForegroundColor Yellow
        }
        
        Write-Host
        Write-Host "[PHASE 2] Starting Docker Compose Master Configuration..." -ForegroundColor Blue
        
        try {
            docker compose -f docker-compose.master.yml up -d
            if ($LASTEXITCODE -eq 0) {
                Write-Host
                Write-Host "[SUCCESS] Combined coordination completed successfully!" -ForegroundColor Green
                Write-Host
                Write-Host "All Services Status:" -ForegroundColor Cyan
                docker compose -f docker-compose.master.yml ps
            } else {
                Write-Host "[ERROR] Docker phase failed!" -ForegroundColor Red
            }
        } catch {
            Write-Host "[ERROR] Failed to start Docker services: $_" -ForegroundColor Red
        }
    }
    
    default {
        Write-Host "[ERROR] Invalid choice. Please run the script again and choose 1, 2, or 3." -ForegroundColor Red
    }
}

Write-Host
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Additional Commands:" -ForegroundColor Yellow
Write-Host "- View logs: docker compose -f docker-compose.master.yml logs -f" -ForegroundColor White
Write-Host "- Stop all: docker compose -f docker-compose.master.yml down" -ForegroundColor White
Write-Host "- Restart all: docker compose -f docker-compose.master.yml restart" -ForegroundColor White
Write-Host "- Health check: docker compose -f docker-compose.master.yml ps" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan

Read-Host "Press Enter to exit"
