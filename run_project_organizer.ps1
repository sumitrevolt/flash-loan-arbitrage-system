# LangChain MCP Project Organizer - PowerShell Runner
# ================================================
# 
# This PowerShell script runs the comprehensive project organizer
# that uses LangChain to command all MCP servers for cleanup.
#
# Author: GitHub Copilot Assistant
# Date: June 18, 2025

param(
    [switch]$SkipBackup,
    [switch]$DryRun,
    [string]$OpenAIKey = $env:OPENAI_API_KEY
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🚀 LangChain MCP Project Organizer" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan

# Set project root
$ProjectRoot = Get-Location
$env:PROJECT_ROOT = $ProjectRoot
Write-Host "📁 Project Root: $ProjectRoot" -ForegroundColor Yellow

# Check Python
Write-Host "`n🐍 Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11 or higher." -ForegroundColor Red
    exit 1
}

# Set OpenAI API key if provided
if ($OpenAIKey) {
    $env:OPENAI_API_KEY = $OpenAIKey
    Write-Host "✅ OpenAI API key configured" -ForegroundColor Green
} elseif ($env:OPENAI_API_KEY) {
    Write-Host "✅ OpenAI API key found in environment" -ForegroundColor Green
} else {
    Write-Host "⚠️ No OpenAI API key found. LangChain AI features will be disabled." -ForegroundColor Yellow
    Write-Host "To enable AI features, set OPENAI_API_KEY environment variable." -ForegroundColor Yellow
}

# Create backup if not skipped
if (-not $SkipBackup) {
    Write-Host "`n💾 Creating backup..." -ForegroundColor Cyan
    $backupDir = Join-Path $ProjectRoot "backup_before_organization"
    
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        
        # Backup critical files
        $criticalFiles = @(
            "package.json",
            "requirements*.txt", 
            "docker-compose*.yml",
            "*.config.js",
            ".env*",
            "hardhat.config.js",
            "unified_mcp_config.json",
            "ai_agents_config.json"
        )
        
        foreach ($pattern in $criticalFiles) {
            $files = Get-ChildItem -Path $ProjectRoot -Name $pattern -File -ErrorAction SilentlyContinue
            foreach ($file in $files) {
                $sourcePath = Join-Path $ProjectRoot $file
                $destPath = Join-Path $backupDir $file
                Copy-Item -Path $sourcePath -Destination $destPath -Force -ErrorAction SilentlyContinue
                Write-Host "📋 Backed up: $file" -ForegroundColor Gray
            }
        }
        
        Write-Host "✅ Backup created successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Backup already exists, skipping..." -ForegroundColor Yellow
    }
}

# Install required packages
Write-Host "`n📦 Installing/updating required packages..." -ForegroundColor Cyan
$requiredPackages = @(
    "langchain>=0.2.17",
    "langchain-openai>=0.1.25", 
    "langchain-community>=0.2.19",
    "langchain-core>=0.2.43",
    "openai>=1.55.0",
    "requests",
    "aiohttp"
)

foreach ($package in $requiredPackages) {
    Write-Host "Installing $package..." -ForegroundColor Gray
    try {
        python -m pip install $package --quiet
    } catch {
        Write-Host "⚠️ Could not install $package" -ForegroundColor Yellow
    }
}

Write-Host "✅ Package installation completed" -ForegroundColor Green

# Run the organizer
Write-Host "`n🚀 Running LangChain MCP Project Organizer..." -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No files will be modified" -ForegroundColor Yellow
    $env:DRY_RUN = "true"
}

try {
    # Run the Python organizer script
    python run_project_organizer.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 Organization completed successfully!" -ForegroundColor Green
        
        # Show organization summary
        Write-Host "`n📊 Organization Summary:" -ForegroundColor Cyan
        
        $summaryFile = Join-Path $ProjectRoot "docs\ORGANIZATION_SUMMARY.md"
        if (Test-Path $summaryFile) {
            Write-Host "📄 Full report available at: $summaryFile" -ForegroundColor Gray
        }
        
        $reportFile = Join-Path $ProjectRoot "docs\organization_report.json"
        if (Test-Path $reportFile) {
            try {
                $report = Get-Content $reportFile | ConvertFrom-Json
                $stats = $report.statistics
                
                Write-Host "Files processed: $($stats.files_processed)" -ForegroundColor White
                Write-Host "Duplicates removed: $($stats.duplicates_removed)" -ForegroundColor White
                Write-Host "Files archived: $($stats.files_archived)" -ForegroundColor White
                Write-Host "MCP servers organized: $($stats.mcp_servers_organized)" -ForegroundColor White
                Write-Host "Configs consolidated: $($stats.configs_consolidated)" -ForegroundColor White
            } catch {
                Write-Host "📊 Report generated but could not parse statistics" -ForegroundColor Yellow
            }
        }
        
        # Next steps
        Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Review organized files in new directory structure" -ForegroundColor White
        Write-Host "2. Check archived files in archive/ directory" -ForegroundColor White  
        Write-Host "3. Update Docker configurations for new paths" -ForegroundColor White
        Write-Host "4. Test MCP servers using config/mcp_servers.json" -ForegroundColor White
        Write-Host "5. Update any hardcoded file paths in scripts" -ForegroundColor White
        
        # Show new structure
        Write-Host "`n📁 New Project Structure:" -ForegroundColor Cyan
        $newDirs = @("src", "config", "docs", "scripts", "tests", "docker", "archive")
        foreach ($dir in $newDirs) {
            $dirPath = Join-Path $ProjectRoot $dir
            if (Test-Path $dirPath) {
                $fileCount = (Get-ChildItem $dirPath -Recurse -File | Measure-Object).Count
                Write-Host "  📂 $dir/ ($fileCount files)" -ForegroundColor Gray
            }
        }
        
    } else {
        Write-Host "❌ Organization failed. Check the logs for details." -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "❌ Error running organizer: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ LangChain MCP Project Organization completed!" -ForegroundColor Green
Write-Host "Check langchain_project_organization.log for detailed logs." -ForegroundColor Gray
