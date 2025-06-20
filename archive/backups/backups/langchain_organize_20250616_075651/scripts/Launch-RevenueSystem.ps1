# Enhanced Flash Loan Arbitrage Revenue Generation System Launcher
# Version 2.0

# Define constants
$CONFIG_PATH = "config/arbitrage-config.json"
$BASE_DIR = $PSScriptRoot
$ENV_MODE = "production" # Can be "development" or "production"
$SYSTEM_VERSION = "2.0.0"

# Clear the screen
Clear-Host

# Helper functions
function Show-Header {
    param (
        [string]$Title
    )
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host "🚀 $Title" -ForegroundColor Yellow
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host ""
}

function Verify-Directories {
    $directories = @(
        "config",
        "dashboard",
        "testing",
        "mcp",
        "mcp/flash-loan-arbitrage-mcp",
        "foundry",
        "foundry/src",
        "foundry/script",
        "foundry/test",
        "logs"
    )

    foreach ($dir in $directories) {
        $fullPath = Join-Path -Path $BASE_DIR -ChildPath $dir
        if (-not (Test-Path $fullPath)) {
            Write-Host "Creating directory: $dir" -ForegroundColor Yellow
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Host "✅ Directory created" -ForegroundColor Green
        }
    }
    Write-Host "✅ All required directories verified" -ForegroundColor Green
}

function Validate-Configuration {
    $configFullPath = Join-Path -Path $BASE_DIR -ChildPath $CONFIG_PATH
    if (-not (Test-Path $configFullPath)) {
        Write-Host "❌ Configuration file not found: $CONFIG_PATH" -ForegroundColor Red
        return $false
    }

    try {
        $config = Get-Content -Path $configFullPath -Raw | ConvertFrom-Json
        
        # Check for placeholder values
        $placeholders = @()
        foreach ($network in $config.networks.PSObject.Properties) {
            $networkObj = $network.Value
            if ($networkObj.enabled -eq $true -and $networkObj.rpc_url -match "YOUR_API_KEY") {
                $placeholders += "RPC URL for $($network.Name) network"
            }
        }

        if ($config.wallet.address -eq "") {
            $placeholders += "Wallet address"
        }

        if ($placeholders.Count -gt 0) {
            Write-Host "⚠️ Configuration contains placeholders that need to be updated:" -ForegroundColor Yellow
            foreach ($p in $placeholders) {
                Write-Host "  - $p" -ForegroundColor Yellow
            }
            Write-Host "Would you like to update these now? (y/n)" -ForegroundColor Cyan
            $updateNow = Read-Host
            if ($updateNow -eq "y") {
                return (Update-Configuration)
            } else {
                Write-Host "Please update the configuration manually before proceeding." -ForegroundColor Yellow
                return $false
            }
        }

        return $true
    } catch {
        Write-Host "❌ Error reading configuration: $_" -ForegroundColor Red
        return $false
    }
}

function Update-Configuration {
    $configFullPath = Join-Path -Path $BASE_DIR -ChildPath $CONFIG_PATH
    $config = Get-Content -Path $configFullPath -Raw | ConvertFrom-Json

    Write-Host "Updating configuration..." -ForegroundColor Cyan
    
    # Update wallet
    Write-Host "Enter your wallet address (or press Enter to skip):" -ForegroundColor White
    $walletAddress = Read-Host
    if ($walletAddress -ne "") {
        $config.wallet.address = $walletAddress
    }

    # Update enabled networks
    foreach ($network in $config.networks.PSObject.Properties) {
        $networkObj = $network.Value
        if ($networkObj.enabled -eq $true) {
            Write-Host "Enter RPC URL for $($network.Name) network (or press Enter to skip):" -ForegroundColor White
            $rpcUrl = Read-Host
            if ($rpcUrl -ne "") {
                $networkObj.rpc_url = $rpcUrl
            }
        }
    }

    # Save updated config
    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFullPath
    Write-Host "✅ Configuration updated successfully" -ForegroundColor Green
    return $true
}

function Check-MCP-Status {
    Write-Host "Checking MCP server status..." -ForegroundColor Cyan
    $mcpDir = Join-Path -Path $BASE_DIR -ChildPath "mcp/flash-loan-arbitrage-mcp"
    
    if (-not (Test-Path "$mcpDir/package.json")) {
        Write-Host "❌ MCP server package.json not found" -ForegroundColor Red
        return $false
    }

    if (-not (Test-Path "$mcpDir/node_modules")) {
        Write-Host "⚠️ MCP server dependencies not installed, installing now..." -ForegroundColor Yellow
        Push-Location $mcpDir
        try {
            npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Failed to install MCP dependencies" -ForegroundColor Red
                Pop-Location
                return $false
            }
        } catch {
            Write-Host "❌ Error installing MCP dependencies: $_" -ForegroundColor Red
            Pop-Location
            return $false
        }
        Pop-Location
    }

    Write-Host "✅ MCP server is ready" -ForegroundColor Green
    return $true
}

function Verify-ContractDeployment {
    $configFullPath = Join-Path -Path $BASE_DIR -ChildPath $CONFIG_PATH
    $config = Get-Content -Path $configFullPath -Raw | ConvertFrom-Json
    
    $contractDeployed = $false
    foreach ($network in $config.networks.PSObject.Properties) {
        $networkObj = $network.Value
        if ($networkObj.enabled -eq $true -and $networkObj.deployed_contract -ne "") {
            $contractDeployed = $true
            Write-Host "✅ Contract deployed on $($network.Name): $($networkObj.deployed_contract)" -ForegroundColor Green
        }
    }

    if (-not $contractDeployed) {
        Write-Host "⚠️ No deployed contract found in configuration" -ForegroundColor Yellow
        Write-Host "   Please deploy the contract before starting the system" -ForegroundColor Yellow
        return $false
    }

    return $true
}

function Update-ContractAddress {
    param (
        [string]$Network,
        [string]$Address
    )
    
    $configFullPath = Join-Path -Path $BASE_DIR -ChildPath $CONFIG_PATH
    $config = Get-Content -Path $configFullPath -Raw | ConvertFrom-Json
    
    if ($config.networks.PSObject.Properties.Name -contains $Network) {
        $config.networks.$Network.deployed_contract = $Address
        $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFullPath
        Write-Host "✅ Updated contract address for $Network: $Address" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Network '$Network' not found in configuration" -ForegroundColor Red
        return $false
    }
}

function System-Health-Check {
    Write-Host "Running system health check..." -ForegroundColor Cyan
    $healthStatus = $true

    # Check environment variables
    if ($env:ARBITRAGE_WALLET_KEY -eq "YOUR_PRIVATE_KEY_HERE" -or $env:ARBITRAGE_WALLET_KEY -eq $null) {
        Write-Host "⚠️ Private key not set correctly" -ForegroundColor Yellow
        $healthStatus = $false
    }

    # Check API keys
    if ($env:ETHERSCAN_API_KEY -eq "YOUR_ETHERSCAN_API_KEY_HERE" -or $env:ETHERSCAN_API_KEY -eq $null) {
        Write-Host "⚠️ Etherscan API key not set" -ForegroundColor Yellow
    }

    if ($env:POLYGONSCAN_API_KEY -eq "YOUR_POLYGONSCAN_API_KEY_HERE" -or $env:POLYGONSCAN_API_KEY -eq $null) {
        Write-Host "⚠️ Polygonscan API key not set" -ForegroundColor Yellow
    }

    # Check for Python
    try {
        $pythonVersion = python --version
        Write-Host "✅ Python detected: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python not found. Please install Python 3.8 or later." -ForegroundColor Red
        $healthStatus = $false
    }

    # Check for Node.js
    try {
        $nodeVersion = node --version
        Write-Host "✅ Node.js detected: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Node.js not found. Please install Node.js 14 or later." -ForegroundColor Red
        $healthStatus = $false
    }

    # Check configuration
    if (-not (Validate-Configuration)) {
        $healthStatus = $false
    }

    # Check MCP status
    if (-not (Check-MCP-Status)) {
        $healthStatus = $false
    }

    return $healthStatus
}

function Check-Python-Dependencies {
    Write-Host "Checking Python dependencies..." -ForegroundColor Cyan
    $packages = @(
        "web3", 
        "eth_account", 
        "aiohttp", 
        "requests", 
        "matplotlib", 
        "pandas", 
        "tkinter"
    )

    $missingPackages = @()
    foreach ($package in $packages) {
        python -c "import $package" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missingPackages += $package
        }
    }

    if ($missingPackages.Count -gt 0) {
        Write-Host "Installing missing Python packages: $($missingPackages -join ', ')" -ForegroundColor Yellow
        pip install $missingPackages
        Write-Host "✅ Python dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "✅ All Python dependencies are installed" -ForegroundColor Green
    }
}

function Setup-Wizard {
    Show-Header "FLASH LOAN ARBITRAGE SETUP WIZARD"
    
    # Step 1: Create directories
    Write-Host "Step 1: Setting up directory structure..." -ForegroundColor Cyan
    Verify-Directories
    
    # Step 2: Configure wallet
    Write-Host "Step 2: Setting up wallet..." -ForegroundColor Cyan
    Write-Host "Enter your wallet address:" -ForegroundColor White
    $walletAddress = Read-Host
    
    Write-Host "Do you want to store your private key in an environment variable? (y/n)" -ForegroundColor White
    $storeKey = Read-Host
    if ($storeKey -eq "y") {
        Write-Host "Enter your private key:" -ForegroundColor White
        $privateKey = Read-Host
        $env:ARBITRAGE_WALLET_KEY = $privateKey
        
        # Securely store for this session only
        Write-Host "Private key stored in environment variable for this session" -ForegroundColor Green
        Write-Host "⚠️ Note: You'll need to set this again in future sessions or add it to your system environment variables" -ForegroundColor Yellow
    }
    
    # Step 3: Configure networks
    Write-Host "Step 3: Setting up networks..." -ForegroundColor Cyan
    $configFullPath = Join-Path -Path $BASE_DIR -ChildPath $CONFIG_PATH
    $config = Get-Content -Path $configFullPath -Raw | ConvertFrom-Json
    
    $config.wallet.address = $walletAddress
    
    foreach ($network in $config.networks.PSObject.Properties) {
        Write-Host "Do you want to enable $($network.Name) network? (y/n)" -ForegroundColor White
        $enableNetwork = Read-Host
        if ($enableNetwork -eq "y") {
            $config.networks.$($network.Name).enabled = $true
            
            Write-Host "Enter RPC URL for $($network.Name):" -ForegroundColor White
            $rpcUrl = Read-Host
            $config.networks.$($network.Name).rpc_url = $rpcUrl
        } else {
            $config.networks.$($network.Name).enabled = $false
        }
    }
    
    # Save updated config
    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFullPath
    
    # Step 4: Install dependencies
    Write-Host "Step 4: Installing dependencies..." -ForegroundColor Cyan
    Check-Python-Dependencies
    Check-MCP-Status
    
    # Step 5: Deploy contract
    Write-Host "Step 5: Deploy smart contract..." -ForegroundColor Cyan
    Write-Host "Do you want to deploy the smart contract now? (y/n)" -ForegroundColor White
    $deployContract = Read-Host
    
    if ($deployContract -eq "y") {
        & "$BASE_DIR\deploy-contract.ps1"
        
        Write-Host "Enter the deployed contract address:" -ForegroundColor White
        $contractAddress = Read-Host
        
        Write-Host "Enter the network it was deployed on (e.g. polygon, ethereum):" -ForegroundColor White
        $networkName = Read-Host
        
        Update-ContractAddress -Network $networkName -Address $contractAddress
    }
    
    Write-Host "✅ Setup complete! Your system is now ready to use." -ForegroundColor Green
}

# Main script starts here
Show-Header "FLASH LOAN ARBITRAGE REVENUE SYSTEM LAUNCHER v$SYSTEM_VERSION"

# Check for first-time setup flag
if ($args.Contains("--setup") -or $args.Contains("-s")) {
    Setup-Wizard
    exit 0
}

# Check for development mode flag
if ($args.Contains("--dev") -or $args.Contains("-d")) {
    $ENV_MODE = "development"
    Write-Host "🔧 Running in development mode" -ForegroundColor Magenta
}

# Verify required directories exist
Verify-Directories

# Check system health
$systemHealth = System-Health-Check

# Check dependencies
Check-Python-Dependencies

# Display system status
if ($systemHealth) {
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host "✅ SYSTEM READY TO GENERATE REVENUE" -ForegroundColor Yellow
    Write-Host "====================================================" -ForegroundColor Green
} else {
    Write-Host "====================================================" -ForegroundColor Yellow
    Write-Host "⚠️ SYSTEM HAS WARNINGS - USE CAUTION" -ForegroundColor Yellow
    Write-Host "====================================================" -ForegroundColor Yellow
}
Write-Host ""

# Main menu
Write-Host "Choose an option:" -ForegroundColor Cyan
Write-Host "1. Deploy smart contract (required for first run)" -ForegroundColor White
Write-Host "2. Start revenue generation system" -ForegroundColor White
Write-Host "3. Start monitoring dashboard only" -ForegroundColor White
Write-Host "4. Run a system test" -ForegroundColor White
Write-Host "5. Update configuration" -ForegroundColor White
Write-Host "6. Run system health check" -ForegroundColor White
Write-Host "7. Show system diagnostics" -ForegroundColor White
Write-Host "8. Backup current configuration" -ForegroundColor White
Write-Host "9. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-9)"

switch ($choice) {
    "1" {
        Write-Host "Launching contract deployment script..." -ForegroundColor Cyan
        & "$BASE_DIR\deploy-contract.ps1"
        
        Write-Host "Do you want to update the configuration with the deployed contract address? (y/n)" -ForegroundColor Cyan
        $updateConfig = Read-Host
        
        if ($updateConfig -eq "y") {
            Write-Host "Enter the deployed contract address:" -ForegroundColor White
            $contractAddress = Read-Host
            
            Write-Host "Enter the network it was deployed on (e.g. polygon, ethereum):" -ForegroundColor White
            $networkName = Read-Host
            
            Update-ContractAddress -Network $networkName -Address $contractAddress
        }
    }
    "2" {
        if (-not (Verify-ContractDeployment)) {
            Write-Host "❌ Cannot start system without a deployed contract" -ForegroundColor Red
            Write-Host "Please deploy the contract first (option 1)" -ForegroundColor Yellow
            break
        }
        
        Write-Host "Starting full arbitrage revenue system..." -ForegroundColor Cyan
        python "$BASE_DIR\flash_loan_orchestrator.py" --config "$CONFIG_PATH" --mode $ENV_MODE
    }
    "3" {
        Write-Host "Starting monitoring dashboard only..." -ForegroundColor Cyan
        python "$BASE_DIR\dashboard\enhanced_mcp_dashboard_with_chat.py" --config "$CONFIG_PATH"
    }
    "4" {
        Write-Host "Running system test..." -ForegroundColor Cyan
        python "$BASE_DIR\testing\simple_performance_test.py" --config "$CONFIG_PATH"
    }
    "5" {
        Update-Configuration
    }
    "6" {
        System-Health-Check
    }
    "7" {
        Write-Host "System Diagnostics:" -ForegroundColor Cyan
        Write-Host "-------------------" -ForegroundColor Cyan
        
        # Check contract deployment
        Verify-ContractDeployment
        
        # Check MCP server
        Check-MCP-Status
        
        # Show enabled networks
        $configFullPath = Join-Path -Path $BASE_DIR -ChildPath $CONFIG_PATH
        $config = Get-Content -Path $configFullPath -Raw | ConvertFrom-Json
        
        Write-Host "Enabled Networks:" -ForegroundColor Cyan
        foreach ($network in $config.networks.PSObject.Properties) {
            if ($network.Value.enabled) {
                Write-Host "  - $($network.Name)" -ForegroundColor White
            }
        }
        
        # Show enabled DEXes
        Write-Host "Enabled DEXes:" -ForegroundColor Cyan
        foreach ($dex in $config.dexes.PSObject.Properties) {
            if ($dex.Value.enabled) {
                Write-Host "  - $($dex.Value.name)" -ForegroundColor White
            }
        }
        
        # Show enabled token pairs
        Write-Host "Enabled Token Pairs:" -ForegroundColor Cyan
        foreach ($pair in $config.token_pairs) {
            if ($pair.enabled) {
                Write-Host "  - $($pair.name)" -ForegroundColor White
            }
        }
    }
    "8" {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupDir = Join-Path -Path $BASE_DIR -ChildPath "backups"
        
        if (-not (Test-Path $backupDir)) {
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        }
        
        $configFullPath = Join-Path -Path $BASE_DIR -ChildPath $CONFIG_PATH
        $backupPath = Join-Path -Path $backupDir -ChildPath "arbitrage-config_$timestamp.json"
        
        Copy-Item -Path $configFullPath -Destination $backupPath
        Write-Host "✅ Configuration backed up to: $backupPath" -ForegroundColor Green
    }
    "9" {
        Write-Host "Exiting..." -ForegroundColor Cyan
    }
    default {
        Write-Host "Invalid choice. Exiting..." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
