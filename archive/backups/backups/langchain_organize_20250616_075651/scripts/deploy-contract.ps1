# Foundry installation and contract deployment script
Write-Host "====================================================" -ForegroundColor Green
Write-Host "🚀 FLASH LOAN ARBITRAGE CONTRACT DEPLOYMENT" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Step 1: Installing Foundry..." -ForegroundColor Cyan
# Run the Foundry installer
Invoke-WebRequest -Uri https://foundry.paradigm.xyz -OutFile foundry-installer.sh
# The next line requires WSL or Git Bash to run
# If you have WSL installed, uncomment the next line
# wsl bash foundry-installer.sh

Write-Host "Note: If the above command failed, please install Foundry manually by following instructions at https://book.getfoundry.sh/getting-started/installation" -ForegroundColor Yellow
Write-Host ""

# Set environment variable for current session
Write-Host "Step 2: Adding Foundry to PATH..." -ForegroundColor Cyan
$env:PATH += ";$env:USERPROFILE\.foundry\bin"
Write-Host "Foundry path added for this session. For permanent addition, add this path to your system environment variables." -ForegroundColor Yellow
Write-Host ""

# Check forge version
Write-Host "Step 3: Verifying Foundry installation..." -ForegroundColor Cyan
try {
    forge --version
    Write-Host "Foundry successfully installed!" -ForegroundColor Green
} catch {
    Write-Host "Forge command not found. Please install Foundry manually and make sure it's in your PATH." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Navigate to foundry directory and install dependencies
Write-Host "Step 4: Installing dependencies..." -ForegroundColor Cyan
cd foundry
forge install aave/aave-v3-core --no-commit
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge install Uniswap/v2-periphery --no-commit
forge install Uniswap/v3-periphery --no-commit
Write-Host "Dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# Build the project
Write-Host "Step 5: Building the FlashLoanArbitrage contract..." -ForegroundColor Cyan
forge build
Write-Host "Contract compiled successfully!" -ForegroundColor Green
Write-Host ""

Write-Host "Step 6: Running tests..." -ForegroundColor Cyan
forge test
Write-Host ""

Write-Host "====================================================" -ForegroundColor Green
Write-Host "✅ CONTRACT READY FOR DEPLOYMENT" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To deploy to a testnet, run:" -ForegroundColor Cyan
Write-Host "forge create src/FlashLoanArbitrage.sol:FlashLoanArbitrage --rpc-url <RPC_URL> --private-key <PRIVATE_KEY> --constructor-args <AAVE_POOL_ADDRESSES_PROVIDER>" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
