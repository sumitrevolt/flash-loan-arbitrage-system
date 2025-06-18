# Enhanced LangChain Orchestrator Docker Deployment Script for Windows
# PowerShell script to deploy the orchestrator with auto-fixing

param(
    [switch]$Clean,
    [switch]$Build,
    [switch]$Deploy,
    [switch]$Status,
    [switch]$Stop,
    [switch]$Help
)

function Show-Help {
    Write-Host "Enhanced LangChain Orchestrator Docker Deployment" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\deploy-langchain-docker.ps1 [OPTIONS]" -ForegroundColor Green
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Deploy    Full deployment (build and start)" -ForegroundColor White
    Write-Host "  -Build     Build Docker images only" -ForegroundColor White
    Write-Host "  -Status    Show deployment status" -ForegroundColor White
    Write-Host "  -Stop      Stop all services" -ForegroundColor White
    Write-Host "  -Clean     Clean up everything" -ForegroundColor White
    Write-Host "  -Help      Show this help" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\deploy-langchain-docker.ps1 -Deploy" -ForegroundColor Gray
    Write-Host "  .\deploy-langchain-docker.ps1 -Status" -ForegroundColor Gray
    Write-Host "  .\deploy-langchain-docker.ps1 -Stop" -ForegroundColor Gray
}

function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Cyan
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Docker command not found" -ForegroundColor Red
        return $false
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker Compose: $composeVersion" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker Compose is not installed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Docker Compose command not found" -ForegroundColor Red
        return $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Python not found, some auto-fix features may not work" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Python not available" -ForegroundColor Yellow
    }
    
    # Check required files
    $requiredFiles = @(
        "Dockerfile",
        "docker-compose.yml", 
        "enhanced_langchain_orchestrator.py",
        "requirements-enhanced-complete.txt"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Host "✅ Found: $file" -ForegroundColor Green
        } else {
            Write-Host "❌ Required file missing: $file" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

function Initialize-Environment {
    Write-Host "🔧 Setting up environment..." -ForegroundColor Cyan
    
    # Create .env if it doesn't exist
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Host "✅ Created .env from example" -ForegroundColor Green
        } else {
            # Create minimal .env
            $envContent = @"
# Basic configuration for Enhanced LangChain Orchestrator
OPENAI_API_KEY=your_openai_api_key_here
REDIS_PASSWORD=langchain_redis_password_2025
POSTGRES_PASSWORD=langchain_password_2025
SECRET_KEY=your_super_secret_key_here_change_this
JWT_SECRET=your_jwt_secret_here_change_this
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
"@
            $envContent | Out-File -FilePath ".env" -Encoding UTF8
            Write-Host "✅ Created minimal .env file" -ForegroundColor Green
        }
    }
    
    # Check for placeholder values
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "your_.*_api_key_here") {
        Write-Host "⚠️  Warning: Please update your API keys in .env file" -ForegroundColor Yellow
        Write-Host "   Edit .env and replace placeholder values with real API keys" -ForegroundColor Gray
    }
    
    return $true
}

function Invoke-AutoFix {
    Write-Host "🔧 Running auto-fix on orchestrator..." -ForegroundColor Cyan
    
    if (Test-Path "auto_fix_orchestrator.py") {
        try {
            $result = python auto_fix_orchestrator.py enhanced_langchain_orchestrator.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Auto-fix completed successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Auto-fix encountered issues but continuing..." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️  Could not run auto-fix: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Auto-fix script not found, skipping..." -ForegroundColor Yellow
    }
    
    return $true
}

function Build-Images {
    Write-Host "🏗️  Building Docker images..." -ForegroundColor Cyan
    
    try {
        docker-compose build --no-cache
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker images built successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Failed to build Docker images" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error building images: $_" -ForegroundColor Red
        return $false
    }
}

function Start-Services {
    Write-Host "🚀 Starting services..." -ForegroundColor Cyan
    
    try {
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Services started successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Failed to start services" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error starting services: $_" -ForegroundColor Red
        return $false
    }
}

function Wait-ForServices {
    param([int]$TimeoutSeconds = 300)
    
    Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Cyan
    
    $startTime = Get-Date
    $healthUrls = @(
        @{Url = "http://localhost:8000/health"; Name = "LangChain Orchestrator"}
    )
    
    while (((Get-Date) - $startTime).TotalSeconds -lt $TimeoutSeconds) {
        $allHealthy = $true
        
        foreach ($service in $healthUrls) {
            try {
                $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -UseBasicParsing
                if ($response.StatusCode -ne 200) {
                    $allHealthy = $false
                    Write-Host "⏳ Waiting for $($service.Name)..." -ForegroundColor Yellow
                    break
                }
            } catch {
                $allHealthy = $false
                Write-Host "⏳ Waiting for $($service.Name)..." -ForegroundColor Yellow
                break
            }
        }
        
        if ($allHealthy) {
            Write-Host "✅ All services are ready!" -ForegroundColor Green
            return $true
        }
        
        Start-Sleep -Seconds 10
    }
    
    Write-Host "❌ Timeout waiting for services" -ForegroundColor Red
    return $false
}

function Show-Status {
    Write-Host "📊 Deployment Status:" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    try {
        Write-Host "🐳 Container Status:" -ForegroundColor Yellow
        docker-compose ps
        
        Write-Host "`n📋 Recent Logs (last 20 lines):" -ForegroundColor Yellow
        docker-compose logs --tail=20 langchain-orchestrator
        
    } catch {
        Write-Host "Error getting status: $_" -ForegroundColor Red
    }
    
    Write-Host "`n🌐 Service URLs:" -ForegroundColor Green
    Write-Host "- Main Orchestrator: http://localhost:8000" -ForegroundColor Gray
    Write-Host "- Health Check: http://localhost:8000/health" -ForegroundColor Gray
    Write-Host "- Grafana Dashboard: http://localhost:3000 (admin/langchain_admin_2025)" -ForegroundColor Gray
    Write-Host "- Prometheus: http://localhost:9090" -ForegroundColor Gray
    
    # Test main endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "`n✅ Main service is responding!" -ForegroundColor Green
        }
    } catch {
        Write-Host "`n⚠️  Main service not responding" -ForegroundColor Yellow
    }
}

function Stop-Services {
    Write-Host "🛑 Stopping services..." -ForegroundColor Cyan
    
    try {
        docker-compose down
        Write-Host "✅ Services stopped" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error stopping services: $_" -ForegroundColor Red
    }
}

function Clean-Deployment {
    Write-Host "🧹 Cleaning up deployment..." -ForegroundColor Cyan
    
    try {
        # Stop and remove containers, networks, and volumes
        docker-compose down -v --remove-orphans
        Write-Host "✅ Containers and volumes removed" -ForegroundColor Green
        
        # Remove images (optional)
        $images = docker images "enhanced-langchain-orchestrator*" -q
        if ($images) {
            docker rmi $images -f
            Write-Host "✅ Images removed" -ForegroundColor Green
        }
        
    } catch {
        Write-Host "❌ Error during cleanup: $_" -ForegroundColor Red
    }
}

function Deploy-Full {
    Write-Host "🚀 Starting Enhanced LangChain Orchestrator Deployment" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    $steps = @(
        @{Name = "Prerequisites Check"; Action = { Test-Prerequisites }},
        @{Name = "Environment Setup"; Action = { Initialize-Environment }},
        @{Name = "Auto-Fix Orchestrator"; Action = { Invoke-AutoFix }},
        @{Name = "Build Images"; Action = { Build-Images }},
        @{Name = "Start Services"; Action = { Start-Services }},
        @{Name = "Wait for Services"; Action = { Wait-ForServices }}
    )
    
    foreach ($step in $steps) {
        Write-Host "`n📋 Step: $($step.Name)" -ForegroundColor Yellow
        Write-Host ("-" * 40) -ForegroundColor Gray
        
        $result = & $step.Action
        if (-not $result) {
            Write-Host "❌ Failed at step: $($step.Name)" -ForegroundColor Red
            return $false
        }
    }
    
    Write-Host "`n🎉 Deployment completed successfully!" -ForegroundColor Green
    Show-Status
    return $true
}

# Main script logic
if ($Help) {
    Show-Help
    exit 0
}

if (-not ($Deploy -or $Build -or $Status -or $Stop -or $Clean)) {
    Write-Host "No action specified. Use -Help for usage information." -ForegroundColor Yellow
    Show-Help
    exit 1
}

try {
    if ($Clean) {
        Clean-Deployment
    } elseif ($Stop) {
        Stop-Services
    } elseif ($Status) {
        Show-Status
    } elseif ($Build) {
        if (Test-Prerequisites) {
            Initialize-Environment
            Invoke-AutoFix
            Build-Images
        }
    } elseif ($Deploy) {
        $success = Deploy-Full
        if ($success) {
            Write-Host "`n✅ Deployment successful!" -ForegroundColor Green
            Write-Host "📖 Use 'docker-compose logs -f' to follow logs" -ForegroundColor Cyan
            Write-Host "🛑 Use '.\deploy-langchain-docker.ps1 -Stop' to stop services" -ForegroundColor Cyan
        } else {
            Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
            Write-Host "🔍 Check the logs above for details" -ForegroundColor Gray
            exit 1
        }
    }
} catch {
    Write-Host "`n💥 Unexpected error: $_" -ForegroundColor Red
    Write-Host "🔍 Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Gray
    exit 1
}

Write-Host "`nScript completed!" -ForegroundColor Cyan
