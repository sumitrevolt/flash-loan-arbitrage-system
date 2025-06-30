# Simple Flash Loan Project Organization Script
param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Continue"

Write-Host "Flash Loan Project Organization Script" -ForegroundColor Blue
Write-Host "=====================================" -ForegroundColor Blue

if ($DryRun) {
    Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
}

function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

# First, let's analyze what we have
Write-Info "Analyzing current project structure..."

$duplicateDirs = @{
    "ai_agents" = @("ai_agents", "ai_agents_unified", "curated_mcp_system\ai_agents")
    "mcp_servers" = @("mcp_servers", "curated_mcp_system\mcp_servers")
    "configs" = @("config", "configs", "curated_mcp_system\config")
}

foreach ($category in $duplicateDirs.Keys) {
    Write-Info "Checking category: $category"
    foreach ($path in $duplicateDirs[$category]) {
        if (Test-Path $path) {
            $itemCount = (Get-ChildItem -Path $path -Recurse -File | Measure-Object).Count
            Write-Host "  Found: $path ($itemCount files)" -ForegroundColor White
        }
    }
}

# Show backup directories
Write-Info "Backup directories found:"
$backupDirs = Get-ChildItem -Directory | Where-Object { 
    $_.Name -like "*backup*" -or 
    $_.Name -like "*archive*" -or 
    $_.Name -like "*compatibility*" 
}

foreach ($dir in $backupDirs) {
    $size = (Get-ChildItem -Path $dir.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "  $($dir.Name) ($($size.ToString('F1')) MB)" -ForegroundColor Yellow
}

if (!$Force -and !$DryRun) {
    Write-Host ""
    Write-Host "This will organize your project by:" -ForegroundColor White
    Write-Host "1. Merging duplicate directories" -ForegroundColor White
    Write-Host "2. Removing old backup directories" -ForegroundColor White
    Write-Host "3. Creating organized structure" -ForegroundColor White
    Write-Host ""
    
    $confirm = Read-Host "Do you want to proceed? (y/n)"
    if ($confirm -ne "y" -and $confirm -ne "yes") {
        Write-Info "Operation cancelled."
        exit 0
    }
}

# Create backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "organization_backup_$timestamp"

Write-Info "Creating backup: $backupDir"
if (!$DryRun) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Backup critical directories
    $criticalDirs = @("src", "mcp_servers", "config", "deployment")
    foreach ($dir in $criticalDirs) {
        if (Test-Path $dir) {
            Copy-Item -Path $dir -Destination "$backupDir\$dir" -Recurse -Force
            Write-Info "Backed up: $dir"
        }
    }
}

# Step 1: Organize AI Agents
Write-Info "Step 1: Organizing AI Agents..."
$targetAI = "src\ai_agents"

if (!$DryRun) {
    New-Item -ItemType Directory -Path $targetAI -Force | Out-Null
}

$aiSources = @("ai_agents", "ai_agents_unified", "curated_mcp_system\ai_agents")
foreach ($source in $aiSources) {
    if (Test-Path $source) {
        Write-Info "Merging $source into $targetAI"
        if (!$DryRun) {
            # Copy all files from source to target
            robocopy $source $targetAI /E /XO /R:1 /W:1 > $null
            # Remove source directory
            Remove-Item -Path $source -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# Step 2: Organize MCP Servers  
Write-Info "Step 2: Organizing MCP Servers..."
$targetMCP = "src\mcp_servers"

if (!$DryRun) {
    New-Item -ItemType Directory -Path $targetMCP -Force | Out-Null
}

$mcpSources = @("mcp_servers", "curated_mcp_system\mcp_servers")
foreach ($source in $mcpSources) {
    if (Test-Path $source) {
        Write-Info "Merging $source into $targetMCP"
        if (!$DryRun) {
            robocopy $source $targetMCP /E /XO /R:1 /W:1 > $null
            if ($source -ne $targetMCP) {
                Remove-Item -Path $source -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

# Step 3: Organize Config files
Write-Info "Step 3: Organizing Configuration files..."
$targetConfig = "config"

$configSources = @("configs", "curated_mcp_system\config")
foreach ($source in $configSources) {
    if (Test-Path $source) {
        Write-Info "Merging $source into $targetConfig"
        if (!$DryRun) {
            robocopy $source $targetConfig /E /XO /R:1 /W:1 > $null
            if ($source -ne $targetConfig) {
                Remove-Item -Path $source -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

# Step 4: Clean up old backups
Write-Info "Step 4: Cleaning up old backup directories..."
$oldBackups = @(
    "extension_compatibility_backup_*",
    "copilot_merge_backup_*", 
    "reorganization_backup_*",
    "cleanup_backup",
    "syntax_fix_backup"
)

foreach ($pattern in $oldBackups) {
    $dirs = Get-ChildItem -Directory -Name $pattern -ErrorAction SilentlyContinue
    foreach ($dir in $dirs) {
        Write-Info "Removing old backup: $dir"
        if (!$DryRun) {
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# Step 5: Remove curated_mcp_system if empty
if (Test-Path "curated_mcp_system") {
    $remaining = Get-ChildItem -Path "curated_mcp_system" -Recurse
    if ($remaining.Count -eq 0) {
        Write-Info "Removing empty curated_mcp_system directory"
        if (!$DryRun) {
            Remove-Item -Path "curated_mcp_system" -Recurse -Force
        }
    }
}

# Step 6: Remove empty directories
Write-Info "Step 6: Removing empty directories..."
if (!$DryRun) {
    do {
        $emptyDirs = Get-ChildItem -Directory -Recurse | Where-Object {
            (Get-ChildItem -Path $_.FullName -Force | Measure-Object).Count -eq 0
        }
        
        foreach ($dir in $emptyDirs) {
            Remove-Item -Path $dir.FullName -Force -ErrorAction SilentlyContinue
        }
    } while ($emptyDirs.Count -gt 0)
}

# Generate report
$reportPath = "organization_report_$timestamp.txt"
$report = @"
Flash Loan Project Organization Report
Generated: $(Get-Date)

SUMMARY:
- Merged AI agents into src\ai_agents
- Merged MCP servers into src\mcp_servers  
- Consolidated config files into config\
- Removed old backup directories
- Cleaned up empty directories

BACKUP CREATED: $backupDir

NEW STRUCTURE:
- src\ai_agents\ - All AI agent code
- src\mcp_servers\ - All MCP server implementations
- config\ - All configuration files
- deployment\ - Docker and deployment configs
- scripts\ - Utility scripts
- docs\ - Documentation

NEXT STEPS:
1. Test system functionality
2. Update any hardcoded paths
3. Verify docker-compose still works
"@

if (!$DryRun) {
    $report | Out-File -FilePath $reportPath -Encoding UTF8
}

Write-Host ""
Write-Success "Project organization completed!"
Write-Success "Backup created: $backupDir"
Write-Success "Report saved: $reportPath"
Write-Host ""
Write-Warning "Please test your system to ensure everything still works"
Write-Host "" 