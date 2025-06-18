# Fix MCP Python Path Script
# This script will update all MCP server configurations to use the correct Python path

Write-Host "🔧 Fixing MCP Server Python Paths..." -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Define the correct Python path
$PYTHON_PATH = "C:\Program Files\Python311\python.exe"

# Test that this Python has the required packages
Write-Host "`n📦 Testing Python installation and packages..." -ForegroundColor Yellow
try {
    & $PYTHON_PATH -c "import aiohttp, aiofiles, web3, mcp; print('✅ All required packages available')"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Required packages not available in main Python installation" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error testing Python installation: $_" -ForegroundColor Red
    exit 1
}

# Define the MCP settings file path
$MCP_SETTINGS_PATH = "$env:APPDATA\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json"

Write-Host "`n📝 Updating MCP settings file..." -ForegroundColor Yellow
Write-Host "Settings file: $MCP_SETTINGS_PATH" -ForegroundColor Gray

# Read the current settings
if (Test-Path $MCP_SETTINGS_PATH) {
    $content = Get-Content $MCP_SETTINGS_PATH -Raw
    
    # Replace all instances of "command": "python" with the full path
    $newContent = $content -replace '"command":\s*"python"', "`"command`": `"$PYTHON_PATH`""
    
    # Create backup
    $backupPath = $MCP_SETTINGS_PATH + ".backup." + (Get-Date -Format "yyyyMMdd_HHmmss")
    Copy-Item $MCP_SETTINGS_PATH $backupPath
    Write-Host "✅ Backup created: $backupPath" -ForegroundColor Green
    
    # Write the updated content
    $newContent | Set-Content $MCP_SETTINGS_PATH -Encoding UTF8
    Write-Host "✅ Updated Python paths in MCP settings" -ForegroundColor Green
    
    # Verify the changes
    $updatedContent = Get-Content $MCP_SETTINGS_PATH -Raw
    $pythonCommandCount = ($updatedContent | Select-String '"command":\s*"python"' -AllMatches).Matches.Count
    $fullPathCommandCount = ($updatedContent | Select-String [regex]::Escape($PYTHON_PATH) -AllMatches).Matches.Count
    
    Write-Host "📊 Configuration updated:" -ForegroundColor Cyan
    Write-Host "  - Remaining 'python' commands: $pythonCommandCount" -ForegroundColor $(if ($pythonCommandCount -eq 0) { "Green" } else { "Yellow" })
    Write-Host "  - Full path commands: $fullPathCommandCount" -ForegroundColor Green
    
} else {
    Write-Host "❌ MCP settings file not found: $MCP_SETTINGS_PATH" -ForegroundColor Red
    exit 1
}

# Test one of the servers to verify it can start
Write-Host "`n🧪 Testing server startup..." -ForegroundColor Yellow

$testServers = @(
    "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\ai_integration\working_enhanced_copilot_mcp_server.py",
    "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\blockchain_integration\working_flash_loan_mcp.py",
    "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\execution\working_unified_flash_loan_mcp_server.py"
)

$successCount = 0
foreach ($serverPath in $testServers) {
    if (Test-Path $serverPath) {
        $serverName = Split-Path $serverPath -Leaf        try {
            Write-Host "Testing $serverName..." -ForegroundColor Gray
            & $PYTHON_PATH $serverPath --help 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ $serverName - OK" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "  ⚠️ $serverName - Issues detected" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ❌ $serverName - Error: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠️ Server file not found: $(Split-Path $serverPath -Leaf)" -ForegroundColor Yellow
    }
}

Write-Host "`n📋 Fix Summary:" -ForegroundColor Cyan
Write-Host "✅ Python path updated to: $PYTHON_PATH" -ForegroundColor Green
Write-Host "✅ All MCP server configurations updated" -ForegroundColor Green
Write-Host "✅ Backup created for safety" -ForegroundColor Green
Write-Host "✅ $successCount/$($testServers.Count) test servers verified" -ForegroundColor Green

Write-Host "`n🔄 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Restart Cline/Claude Dev extension" -ForegroundColor White
Write-Host "2. All MCP servers should now connect successfully" -ForegroundColor White
Write-Host "3. The dependency errors should be resolved" -ForegroundColor White

Write-Host "`n✨ MCP Python Path Fix Complete!" -ForegroundColor Green
