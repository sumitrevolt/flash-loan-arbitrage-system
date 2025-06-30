# Cursor Extension Compatibility Fixer for Windows
# This script fixes extension compatibility issues by removing problematic extensions

param(
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

# Set error action preference
$ErrorActionPreference = "Continue"

# Define problematic extensions
$ProblematicExtensions = @(
    "r-moriut.dfile-profiler-1.1.0",
    "automatalabs.copilot-mcp-0.0.50",
    "ms-python.vscode-python-envs-0.3.11701010-win32-x64"
)

# Define paths
$CursorExtensionsPath = Join-Path $env:APPDATA "Cursor\User\extensions"
$VSCodeExtensionsPath = Join-Path $env:APPDATA "Code\User\extensions"
$CursorSettingsPath = Join-Path $env:APPDATA "Cursor\User\settings.json"
$VSCodeSettingsPath = Join-Path $env:APPDATA "Code\User\settings.json"

# Create backup directory
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = "extension_compatibility_backup_$Timestamp"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function New-BackupDirectory {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-ColorOutput "📁 Created backup directory: $Path" -Color "Green"
    }
}

function Backup-Item {
    param([string]$SourcePath, [string]$BackupPath)
    
    try {
        if (Test-Path $SourcePath) {
            $BackupFullPath = Join-Path $BackupDir $BackupPath
            New-Item -ItemType Directory -Path (Split-Path $BackupFullPath -Parent) -Force | Out-Null
            
            if (Test-Path $SourcePath -PathType Container) {
                Copy-Item -Path $SourcePath -Destination $BackupFullPath -Recurse -Force
                Write-ColorOutput "📁 Backed up directory: $SourcePath" -Color "Yellow"
            } else {
                Copy-Item -Path $SourcePath -Destination $BackupFullPath -Force
                Write-ColorOutput "📄 Backed up file: $SourcePath" -Color "Yellow"
            }
            return $true
        } else {
            Write-ColorOutput "⚠️  Source path does not exist: $SourcePath" -Color "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "❌ Failed to backup $SourcePath : $($_.Exception.Message)" -Color "Red"
        return $false
    }
}

function Find-ProblematicExtensions {
    param([string]$ExtensionsPath)
    
             $FoundExtensions = @()
     
     if (-not (Test-Path $ExtensionsPath)) {
         Write-ColorOutput "⚠️  Extensions directory does not exist: $ExtensionsPath" -Color "Red"
         return $FoundExtensions
     }
     
     Write-ColorOutput "🔍 Scanning for problematic extensions in: $ExtensionsPath" -Color "Cyan"
     
     Get-ChildItem -Path $ExtensionsPath -Directory | ForEach-Object {
         $ExtensionName = $_.Name
         foreach ($Problematic in $ProblematicExtensions) {
             if (($ExtensionName -like "*$($Problematic.Split('.')[0])*") -or 
                 ($ExtensionName -like "*$($Problematic.Split('.')[1])*") -or
                 ($ExtensionName -eq $Problematic)) {
                 $FoundExtensions += $_.FullName
                 Write-ColorOutput "  🚫 Found problematic extension: $ExtensionName" -Color "Red"
                 break
             }
         }
     }
    
    return $FoundExtensions
}

function Remove-Extension {
    param([string]$ExtensionPath)
    
    try {
        if ($DryRun) {
            Write-ColorOutput "🗑️  [DRY RUN] Would remove extension: $ExtensionPath" -Color "Magenta"
            return $true
        } else {
            Write-ColorOutput "🗑️  Removing extension: $ExtensionPath" -Color "Red"
            Remove-Item -Path $ExtensionPath -Recurse -Force
            return $true
        }
    } catch {
        Write-ColorOutput "❌ Failed to remove extension $ExtensionPath : $($_.Exception.Message)" -Color "Red"
        return $false
    }
}

function Update-Settings {
    param([string]$SettingsPath)
    
    try {
        $Settings = @{}
        
        # Load existing settings if file exists
        if (Test-Path $SettingsPath) {
            $SettingsContent = Get-Content -Path $SettingsPath -Raw -Encoding UTF8
            $Settings = $SettingsContent | ConvertFrom-Json -AsHashtable
        }
        
        # Add compatibility settings
        $CompatibilitySettings = @{
            "extensions.autoCheckUpdates" = $false
            "extensions.autoUpdate" = $false
            "extensions.ignoreRecommendations" = $true
            "update.mode" = "none"
            "extensions.showRecommendationsOnlyOnDemand" = $true
            "workbench.enableExperiments" = $false
            "extensions.closeExtensionDetailsOnViewChange" = $true
        }
        
        foreach ($Key in $CompatibilitySettings.Keys) {
            $Settings[$Key] = $CompatibilitySettings[$Key]
        }
        
        if ($DryRun) {
            Write-ColorOutput "📝 [DRY RUN] Would update settings: $SettingsPath" -Color "Magenta"
            return $true
        } else {
            # Create directory if it doesn't exist
            $SettingsDir = Split-Path $SettingsPath -Parent
            if (-not (Test-Path $SettingsDir)) {
                New-Item -ItemType Directory -Path $SettingsDir -Force | Out-Null
            }
            
            # Write updated settings
            $Settings | ConvertTo-Json -Depth 10 | Set-Content -Path $SettingsPath -Encoding UTF8
            Write-ColorOutput "✅ Updated settings: $SettingsPath" -Color "Green"
            return $true
        }
    } catch {
        Write-ColorOutput "❌ Failed to update settings $SettingsPath : $($_.Exception.Message)" -Color "Red"
        return $false
    }
}

function Clear-ExtensionCache {
    $CachePaths = @(
        (Join-Path $env:APPDATA "Code\CachedExtensions"),
        (Join-Path $env:APPDATA "Cursor\CachedExtensions"),
        (Join-Path $env:APPDATA "Code\logs"),
        (Join-Path $env:APPDATA "Cursor\logs")
    )
    
    $Success = $true
    foreach ($CachePath in $CachePaths) {
        if (Test-Path $CachePath) {
            try {
                if ($DryRun) {
                    Write-ColorOutput "🧹 [DRY RUN] Would clear cache: $CachePath" -Color "Magenta"
                } else {
                    Write-ColorOutput "🧹 Clearing cache: $CachePath" -Color "Yellow"
                    Remove-Item -Path $CachePath -Recurse -Force
                }
            } catch {
                Write-ColorOutput "⚠️  Could not clear cache $CachePath : $($_.Exception.Message)" -Color "Red"
                $Success = $false
            }
        }
    }
    return $Success
}

function Fix-PackageJsonFiles {
    param([string]$ExtensionsPath)
    
    $FixedCount = 0
    
    if (-not (Test-Path $ExtensionsPath)) {
        return $FixedCount
    }
    
    Write-ColorOutput "🔧 Fixing package.json files in: $ExtensionsPath" -Color "Cyan"
    
    Get-ChildItem -Path $ExtensionsPath -Directory | ForEach-Object {
        $PackageJsonPath = Join-Path $_.FullName "package.json"
        if (Test-Path $PackageJsonPath) {
            try {
                $PackageContent = Get-Content -Path $PackageJsonPath -Raw -Encoding UTF8
                $PackageData = $PackageContent | ConvertFrom-Json
                
                if ($PackageData.engines -and $PackageData.engines.vscode) {
                    $EngineVersion = $PackageData.engines.vscode
                    
                                         # Check if it requires a version higher than 1.96.2
                     if (($EngineVersion -match "\^1\.9[7-9]") -or ($EngineVersion -match "\^1\.1\d\d")) {
                        if ($DryRun) {
                            Write-ColorOutput "  🔧 [DRY RUN] Would fix $($_.Name): $EngineVersion -> ^1.96.0" -Color "Magenta"
                        } else {
                            Write-ColorOutput "  🔧 Fixing $($_.Name): $EngineVersion -> ^1.96.0" -Color "Yellow"
                            $PackageData.engines.vscode = "^1.96.0"
                            $PackageData | ConvertTo-Json -Depth 10 | Set-Content -Path $PackageJsonPath -Encoding UTF8
                        }
                        $FixedCount++
                    }
                }
            } catch {
                Write-ColorOutput "⚠️  Could not fix $PackageJsonPath : $($_.Exception.Message)" -Color "Red"
            }
        }
    }
    
    return $FixedCount
}

function Run-Diagnostics {
    Write-ColorOutput "`n🔍 Running diagnostics..." -Color "Cyan"
    
    $Diagnostics = @{
        VSCodeExtensionsExist = Test-Path $VSCodeExtensionsPath
        CursorExtensionsExist = Test-Path $CursorExtensionsPath
        VSCodeSettingsExist = Test-Path $VSCodeSettingsPath
        CursorSettingsExist = Test-Path $CursorSettingsPath
        ProblematicExtensionsFound = @{
            VSCode = @()
            Cursor = @()
        }
    }
    
    # Check for remaining problematic extensions
    if ($Diagnostics.VSCodeExtensionsExist) {
        $Diagnostics.ProblematicExtensionsFound.VSCode = Find-ProblematicExtensions -ExtensionsPath $VSCodeExtensionsPath
    }
    
    if ($Diagnostics.CursorExtensionsExist) {
        $Diagnostics.ProblematicExtensionsFound.Cursor = Find-ProblematicExtensions -ExtensionsPath $CursorExtensionsPath
    }
    
    # Print diagnostics
    Write-ColorOutput "`n📊 Diagnostic Results:" -Color "Cyan"
    Write-ColorOutput "  VS Code Extensions Directory: $(if ($Diagnostics.VSCodeExtensionsExist) { '✅' } else { '❌' })" -Color "White"
    Write-ColorOutput "  Cursor Extensions Directory: $(if ($Diagnostics.CursorExtensionsExist) { '✅' } else { '❌' })" -Color "White"
    Write-ColorOutput "  VS Code Settings: $(if ($Diagnostics.VSCodeSettingsExist) { '✅' } else { '❌' })" -Color "White"
    Write-ColorOutput "  Cursor Settings: $(if ($Diagnostics.CursorSettingsExist) { '✅' } else { '❌' })" -Color "White"
    
    $TotalProblematic = $Diagnostics.ProblematicExtensionsFound.VSCode.Count + $Diagnostics.ProblematicExtensionsFound.Cursor.Count
    Write-ColorOutput "  Remaining Problematic Extensions: $TotalProblematic" -Color "White"
    
    return $Diagnostics
}

# Main execution
function Main {
    Write-ColorOutput "🚀 Starting Cursor Extension Compatibility Fix..." -Color "Green"
    Write-ColorOutput "📅 Timestamp: $Timestamp" -Color "Green"
    
    if ($DryRun) {
        Write-ColorOutput "🔍 DRY RUN MODE - No changes will be made" -Color "Magenta"
    }
    
    $Success = $true
    
    # Create backup directory
    New-BackupDirectory -Path $BackupDir
    
    # Process VS Code extensions
    if (Test-Path $VSCodeExtensionsPath) {
        Write-ColorOutput "`n🔧 Processing VS Code extensions..." -Color "Cyan"
        
        # Create backup
        Backup-Item -SourcePath $VSCodeExtensionsPath -BackupPath "vscode_extensions"
        
        # Find and remove problematic extensions
        $ProblematicVSCode = Find-ProblematicExtensions -ExtensionsPath $VSCodeExtensionsPath
        foreach ($Ext in $ProblematicVSCode) {
            if (-not (Remove-Extension -ExtensionPath $Ext)) {
                $Success = $false
            }
        }
        
        # Fix remaining extensions
        $FixedCount = Fix-PackageJsonFiles -ExtensionsPath $VSCodeExtensionsPath
        Write-ColorOutput "  ✅ Fixed $FixedCount extension package.json files" -Color "Green"
        
        # Update settings
        if (-not (Update-Settings -SettingsPath $VSCodeSettingsPath)) {
            $Success = $false
        }
    }
    
    # Process Cursor extensions
    if (Test-Path $CursorExtensionsPath) {
        Write-ColorOutput "`n🔧 Processing Cursor extensions..." -Color "Cyan"
        
        # Create backup
        Backup-Item -SourcePath $CursorExtensionsPath -BackupPath "cursor_extensions"
        
        # Find and remove problematic extensions
        $ProblematicCursor = Find-ProblematicExtensions -ExtensionsPath $CursorExtensionsPath
        foreach ($Ext in $ProblematicCursor) {
            if (-not (Remove-Extension -ExtensionPath $Ext)) {
                $Success = $false
            }
        }
        
        # Fix remaining extensions
        $FixedCount = Fix-PackageJsonFiles -ExtensionsPath $CursorExtensionsPath
        Write-ColorOutput "  ✅ Fixed $FixedCount extension package.json files" -Color "Green"
        
        # Update settings
        if (-not (Update-Settings -SettingsPath $CursorSettingsPath)) {
            $Success = $false
        }
    }
    
    # Clear caches
    Write-ColorOutput "`n🧹 Clearing extension caches..." -Color "Cyan"
    if (-not (Clear-ExtensionCache)) {
        Write-ColorOutput "⚠️  Some cache files could not be cleared (this is often normal)" -Color "Yellow"
    }
    
    # Run diagnostics
    Run-Diagnostics
    
    # Final instructions
    $StatusIcon = if ($Success) { "✅" } else { "⚠️ " }
    Write-ColorOutput "`n$StatusIcon Extension compatibility fix completed!" -Color "Green"
    Write-ColorOutput "📁 Backups stored in: $(Resolve-Path $BackupDir)" -Color "Green"
    Write-ColorOutput "`n🔄 IMPORTANT: Please restart VS Code/Cursor to apply changes" -Color "Yellow"
    Write-ColorOutput "📋 Manual steps if issues persist:" -Color "Yellow"
    Write-ColorOutput "   1. Close VS Code/Cursor completely" -Color "White"
    Write-ColorOutput "   2. Wait 10 seconds" -Color "White"
    Write-ColorOutput "   3. Restart the application" -Color "White"
    Write-ColorOutput "   4. Check Extensions panel for any remaining error notifications" -Color "White"
    
    return $Success
}

# Execute main function
try {
    $Result = Main
    exit $(if ($Result) { 0 } else { 1 })
} catch {
    Write-ColorOutput "`nUnexpected error: $($_.Exception.Message)" -Color "Red"
    Write-ColorOutput $_.ScriptStackTrace -Color "Red"
    exit 1
}