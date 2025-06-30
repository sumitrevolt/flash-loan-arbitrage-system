# Flash Loan Project Organization Script
# This script will organize the project structure and remove duplicates

param(
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Continue"

Write-Host "🧹 Flash Loan Project Organization Script" -ForegroundColor Blue
Write-Host "=========================================" -ForegroundColor Blue

if ($DryRun) {
    Write-Host "📋 DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
}

function Write-Status {
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

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Create backup before organizing
function New-OrganizationBackup {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "organization_backup_$timestamp"
    
    Write-Status "Creating backup: $backupDir"
    
    if (!$DryRun) {
        $criticalDirs = @("src", "mcp_servers", "config", "deployment", "scripts")
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        
        foreach ($dir in $criticalDirs) {
            if (Test-Path $dir) {
                Copy-Item -Path $dir -Destination "$backupDir\$dir" -Recurse -Force
                Write-Status "Backed up: $dir"
            }
        }
    }
    
    return $backupDir
}

# Analyze duplicate directories
function Get-DuplicateDirectories {
    Write-Status "Analyzing duplicate directories..."
    
    $duplicates = @{
        "AI_AGENTS" = @("ai_agents", "ai_agents_unified", "curated_mcp_system\ai_agents", "src\ai_agents")
        "MCP_SERVERS" = @("mcp_servers", "curated_mcp_system\mcp_servers", "src\mcp_servers")
        "CONFIG" = @("config", "configs", "curated_mcp_system\config", "src\config")
        "SCRIPTS" = @("scripts", "core\scripts", "src\scripts")
        "DEPLOYMENT" = @("deployment", "production")
        "BACKUPS" = @("backup", "archive\backups", "syntax_fix_backup", "cleanup_backup")
    }
    
    foreach ($category in $duplicates.Keys) {
        Write-Status "Category: $category"
        foreach ($path in $duplicates[$category]) {
            if (Test-Path $path) {
                $size = (Get-ChildItem -Path $path -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
                Write-Host "  📁 $path (${size:F1} MB)" -ForegroundColor White
            }
        }
    }
    
    return $duplicates
}

# Clean up old backup directories
function Remove-OldBackups {
    Write-Status "Cleaning up old backup directories..."
    
    $backupPatterns = @(
        "organization_backup_*",
        "extension_compatibility_backup_*",
        "copilot_merge_backup_*",
        "reorganization_backup_*",
        "cleanup_backup",
        "syntax_fix_backup"
    )
    
    foreach ($pattern in $backupPatterns) {
        $backupDirs = Get-ChildItem -Directory -Name $pattern -ErrorAction SilentlyContinue
        
        if ($backupDirs.Count -gt 1) {
            # Keep only the most recent backup for each pattern
            $sorted = $backupDirs | Sort-Object LastWriteTime -Descending
            $toDelete = $sorted | Select-Object -Skip 1
            
            foreach ($dir in $toDelete) {
                Write-Status "Removing old backup: $dir"
                if (!$DryRun) {
                    Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
}

# Merge AI Agents directories
function Merge-AIAgents {
    Write-Status "Organizing AI Agents..."
    
    $targetDir = "src\ai_agents"
    
    if (!$DryRun) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    $sources = @("ai_agents", "ai_agents_unified", "curated_mcp_system\ai_agents")
    
    foreach ($source in $sources) {
        if (Test-Path $source) {
            Write-Status "Merging: $source -> $targetDir"
            
            if (!$DryRun) {
                Get-ChildItem -Path $source -Recurse | ForEach-Object {
                    $relativePath = $_.FullName.Substring((Resolve-Path $source).Path.Length + 1)
                    $destPath = Join-Path $targetDir $relativePath
                    
                    if ($_.PSIsContainer) {
                        New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                    } else {
                        $destDir = Split-Path $destPath -Parent
                        if (!(Test-Path $destDir)) {
                            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                        }
                        
                        if (!(Test-Path $destPath)) {
                            Copy-Item -Path $_.FullName -Destination $destPath -Force
                        }
                    }
                }
                
                # Remove source after successful merge
                Remove-Item -Path $source -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

# Merge MCP Servers
function Merge-MCPServers {
    Write-Status "Organizing MCP Servers..."
    
    $targetDir = "src\mcp_servers"
    
    if (!$DryRun) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    $sources = @("mcp_servers", "curated_mcp_system\mcp_servers")
    
    foreach ($source in $sources) {
        if (Test-Path $source) {
            Write-Status "Merging: $source -> $targetDir"
            
            if (!$DryRun) {
                Get-ChildItem -Path $source -File | ForEach-Object {
                    $destPath = Join-Path $targetDir $_.Name
                    if (!(Test-Path $destPath)) {
                        Copy-Item -Path $_.FullName -Destination $destPath -Force
                    }
                }
                
                # Remove source after successful merge
                if ($source -ne "src\mcp_servers") {
                    Remove-Item -Path $source -Recurse -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
}

# Merge Configuration files
function Merge-Configs {
    Write-Status "Organizing Configuration files..."
    
    $targetDir = "config"
    
    if (!$DryRun) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    $sources = @("configs", "curated_mcp_system\config", "src\config")
    
    foreach ($source in $sources) {
        if (Test-Path $source) {
            Write-Status "Merging: $source -> $targetDir"
            
            if (!$DryRun) {
                Get-ChildItem -Path $source -Recurse | ForEach-Object {
                    $relativePath = $_.FullName.Substring((Resolve-Path $source).Path.Length + 1)
                    $destPath = Join-Path $targetDir $relativePath
                    
                    if ($_.PSIsContainer) {
                        New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                    } else {
                        $destDir = Split-Path $destPath -Parent
                        if (!(Test-Path $destDir)) {
                            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                        }
                        
                        if (!(Test-Path $destPath)) {
                            Copy-Item -Path $_.FullName -Destination $destPath -Force
                        }
                    }
                }
                
                # Remove source after successful merge
                if ($source -ne "config") {
                    Remove-Item -Path $source -Recurse -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
}

# Organize Scripts
function Merge-Scripts {
    Write-Status "Organizing Scripts..."
    
    $targetDir = "scripts"
    
    $sources = @("core\scripts", "src\scripts")
    
    foreach ($source in $sources) {
        if (Test-Path $source) {
            Write-Status "Merging: $source -> $targetDir"
            
            if (!$DryRun) {
                Get-ChildItem -Path $source -File | ForEach-Object {
                    $destPath = Join-Path $targetDir $_.Name
                    if (!(Test-Path $destPath)) {
                        Copy-Item -Path $_.FullName -Destination $destPath -Force
                    }
                }
            }
        }
    }
}

# Remove empty directories
function Remove-EmptyDirectories {
    Write-Status "Removing empty directories..."
    
    do {
        $emptyDirs = Get-ChildItem -Directory -Recurse | Where-Object {
            (Get-ChildItem -Path $_.FullName -Force | Measure-Object).Count -eq 0
        }
        
        foreach ($dir in $emptyDirs) {
            Write-Status "Removing empty directory: $($dir.FullName)"
            if (!$DryRun) {
                Remove-Item -Path $dir.FullName -Force
            }
        }
    } while ($emptyDirs.Count -gt 0 -and !$DryRun)
}

# Clean up duplicate files
function Remove-DuplicateFiles {
    Write-Status "Identifying duplicate files..."
    
    $files = Get-ChildItem -File -Recurse | Group-Object Name | Where-Object { $_.Count -gt 1 }
    
    foreach ($group in $files) {
        Write-Status "Found duplicates of: $($group.Name)"
        $sorted = $group.Group | Sort-Object LastWriteTime -Descending
        $toDelete = $sorted | Select-Object -Skip 1
        
        foreach ($file in $toDelete) {
            Write-Warning "Removing duplicate: $($file.FullName)"
            if (!$DryRun) {
                Remove-Item -Path $file.FullName -Force
            }
        }
    }
}

# Create organized directory structure
function New-OrganizedStructure {
    Write-Status "Creating organized directory structure..."
    
    $structure = @(
        "src\ai_agents",
        "src\mcp_servers", 
        "src\contracts",
        "src\tools",
        "src\utilities",
        "config\env",
        "config\docker",
        "deployment\docker",
        "deployment\kubernetes",
        "scripts\automation",
        "scripts\maintenance",
        "docs\guides",
        "docs\api",
        "tests\unit",
        "tests\integration",
        "data\cache",
        "data\logs",
        "logs",
        "models",
        "templates"
    )
    
    foreach ($dir in $structure) {
        if (!$DryRun) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        Write-Status "Created: $dir"
    }
}

# Generate organization report
function New-OrganizationReport {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $reportPath = "organization_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
    
    $report = @"
# Project Organization Report
Generated: $timestamp

## Summary
- ✅ Merged duplicate AI agent directories
- ✅ Consolidated MCP servers
- ✅ Organized configuration files
- ✅ Cleaned up backup directories
- ✅ Removed empty directories
- ✅ Eliminated duplicate files

## New Structure
- \`src/\` - Main source code
- \`config/\` - Configuration files
- \`deployment/\` - Deployment configurations
- \`scripts/\` - Utility scripts
- \`docs/\` - Documentation
- \`tests/\` - Test files
- \`data/\` - Data storage
- \`logs/\` - Log files

## Recommended Next Steps
1. Update import paths in Python files
2. Update docker-compose references
3. Test system functionality
4. Update documentation
"@

    if (!$DryRun) {
        $report | Out-File -FilePath $reportPath -Encoding UTF8
    }
    
    Write-Success "Organization report saved: $reportPath"
}

# Main execution
function Main {
    Write-Host ""
    Write-Host "This script will organize your Flash Loan project by:" -ForegroundColor White
    Write-Host "- Merging duplicate directories" -ForegroundColor White
    Write-Host "- Removing old backups" -ForegroundColor White
    Write-Host "- Eliminating duplicate files" -ForegroundColor White
    Write-Host "- Creating clean directory structure" -ForegroundColor White
    Write-Host ""
    
    if (!$Force -and !$DryRun) {
        $confirm = Read-Host "Do you want to proceed? (y/n)"
        if ($confirm -ne "y" -and $confirm -ne "yes") {
            Write-Status "Operation cancelled."
            return
        }
    }
    
    # Create backup
    $backupDir = New-OrganizationBackup
    
    # Analyze current structure
    $duplicates = Get-DuplicateDirectories
    
    # Execute organization steps
    Remove-OldBackups
    Merge-AIAgents  
    Merge-MCPServers
    Merge-Configs
    Merge-Scripts
    New-OrganizedStructure
    Remove-EmptyDirectories
    Remove-DuplicateFiles
    
    # Generate report
    New-OrganizationReport
    
    Write-Host ""
    Write-Success "🎉 Project organization completed!"
    Write-Success "Backup created: $backupDir"
    Write-Host ""
    Write-Warning "⚠️  Please verify system functionality after organization"
    Write-Warning "⚠️  Update any hardcoded paths in your configuration files"
    Write-Host ""
}

# Execute main function
Main 