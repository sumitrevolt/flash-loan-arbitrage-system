# MCP Server Diagnostics and Fix Script
# This script will help diagnose and fix common MCP server issues

Write-Host "🔍 MCP Server Diagnostics and Fix Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Test Python dependencies
Write-Host "`n📦 Testing Python Dependencies..." -ForegroundColor Yellow

$dependencies = @("aiohttp", "aiofiles", "web3", "mcp", "asyncio", "requests")
$missing_deps = @()

foreach ($dep in $dependencies) {
    try {
        $result = python -c "import $dep; print('✅ $dep')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host $result -ForegroundColor Green
        } else {
            Write-Host "❌ $dep - Failed to import" -ForegroundColor Red
            $missing_deps += $dep
        }
    } catch {
        Write-Host "❌ $dep - Error testing" -ForegroundColor Red
        $missing_deps += $dep
    }
}

# Install missing dependencies
if ($missing_deps.Count -gt 0) {
    Write-Host "`n🔧 Installing missing dependencies..." -ForegroundColor Yellow
    foreach ($dep in $missing_deps) {
        Write-Host "Installing $dep..." -ForegroundColor Yellow
        pip install $dep
    }
}

# Test server file existence
Write-Host "`n📁 Checking MCP Server Files..." -ForegroundColor Yellow

$server_paths = @{
    "flash_loan_enhanced_copilot" = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\ai_integration\working_enhanced_copilot_mcp_server.py"
    "context7_clean" = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\ai_integration\clean_context7_mcp_server.py"
    "flash_loan_blockchain" = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\blockchain_integration\working_flash_loan_mcp.py"
    "matic_mcp_server" = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\blockchain_integration\matic-mcp-server\matic_mcp_server.py"
    "evm_mcp_server" = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\blockchain_integration\evm-mcp-server\evm_mcp_server.py"
    "price_oracle_mcp_server" = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\data_providers\price-oracle-mcp-server\price_oracle_mcp_server.py"
    "unified_flash_loan" = "C:\Users\Ratanshila\Documents\flash loan\mcp_servers\execution\working_unified_flash_loan_mcp_server.py"
}

foreach ($server_name in $server_paths.Keys) {
    $path = $server_paths[$server_name]
    if (Test-Path $path) {
        Write-Host "✅ $server_name - File exists" -ForegroundColor Green
        
        # Test if the file can be executed
        try {
            $result = python $path --help 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Can execute successfully" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️ Execution issues detected" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ❌ Cannot execute" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ $server_name - File not found: $path" -ForegroundColor Red
    }
}

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "1. All required Python dependencies should now be installed" -ForegroundColor White
Write-Host "2. Restart Cline to reload the MCP server connections" -ForegroundColor White
Write-Host "3. The servers should now connect properly" -ForegroundColor White

Write-Host "`n✨ MCP Server Diagnostics Complete!" -ForegroundColor Green
