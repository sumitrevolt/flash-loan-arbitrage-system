# Live Trading Configuration Setup for Flash Loan Arbitrage
# ⚠️ WARNING: This enables REAL MONEY transactions!

param(
    [switch]$Confirm,
    [string]$Network = "mainnet"
)

$ErrorActionPreference = "Stop"

Write-Host "🔥 LIVE TRADING SETUP FOR FLASH LOAN ARBITRAGE" -ForegroundColor Red
Write-Host "===============================================" -ForegroundColor Red

if (!$Confirm) {
    Write-Host ""
    Write-Host "⚠️  CRITICAL WARNING ⚠️" -ForegroundColor Yellow
    Write-Host "This will configure your system for LIVE TRADING with REAL MONEY!" -ForegroundColor Red
    Write-Host "You could lose significant funds if not configured properly." -ForegroundColor Red
    Write-Host ""
    Write-Host "Requirements for live trading:" -ForegroundColor White
    Write-Host "• Valid API keys for data providers (Infura, Alchemy, etc.)" -ForegroundColor White
    Write-Host "• Deployed flash loan contracts on target network" -ForegroundColor White
    Write-Host "• Sufficient ETH for gas fees" -ForegroundColor White
    Write-Host "• Understanding of MEV and arbitrage risks" -ForegroundColor White
    Write-Host ""
    $confirm = Read-Host "Type 'I UNDERSTAND THE RISKS' to continue"
    if ($confirm -ne "I UNDERSTAND THE RISKS") {
        Write-Host "Setup cancelled for safety." -ForegroundColor Green
        exit 0
    }
}

Write-Host "🔧 Configuring live trading environment..." -ForegroundColor Cyan

# Create live trading .env configuration
$liveEnvConfig = @"
# ================================================
# FLASH LOAN ARBITRAGE - LIVE TRADING CONFIGURATION
# ================================================
# ⚠️ WARNING: REAL MONEY TRADING ENABLED ⚠️

# =================
# TRADING SETTINGS
# =================
EXECUTE_TRADES=true
NETWORK=$Network
TRADING_MODE=live

# =================
# BLOCKCHAIN PROVIDERS (REQUIRED)
# =================
# Get these from: https://infura.io, https://alchemy.com, or https://quicknode.com
INFURA_PROJECT_ID=your_infura_project_id_here
ALCHEMY_API_KEY=your_alchemy_api_key_here
QUICKNODE_ENDPOINT=your_quicknode_endpoint_here

# Primary RPC endpoints
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
ARBITRUM_RPC_URL=https://arbitrum-mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
OPTIMISM_RPC_URL=https://optimism-mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID

# =================
# WALLET CONFIGURATION (CRITICAL)
# =================
# ⚠️ Your actual private key - KEEP SECURE!
PRIVATE_KEY=0xYOUR_ACTUAL_PRIVATE_KEY_HERE
WALLET_ADDRESS=0xYOUR_WALLET_ADDRESS_HERE

# =================
# DEPLOYED CONTRACTS (REQUIRED)
# =================
# Your deployed flash loan contract addresses
FLASH_LOAN_CONTRACT_MAINNET=0xYOUR_DEPLOYED_CONTRACT_ADDRESS
FLASH_LOAN_CONTRACT_POLYGON=0xYOUR_DEPLOYED_CONTRACT_ADDRESS
FLASH_LOAN_CONTRACT_ARBITRUM=0xYOUR_DEPLOYED_CONTRACT_ADDRESS

# =================
# DEX ROUTER ADDRESSES (MAINNET)
# =================
UNISWAP_V2_ROUTER=0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D
UNISWAP_V3_ROUTER=0xE592427A0AEce92De3Edee1F18E0157C05861564
SUSHISWAP_ROUTER=0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F
PANCAKESWAP_V2_ROUTER=0x10ED43C718714eb63d5aA57B78B54704E256024E
BALANCER_VAULT=0xBA12222222228d8Ba445958a75a0704d566BF2C8

# =================
# RISK MANAGEMENT (CRITICAL)
# =================
MAX_GAS_PRICE=200000000000  # 200 gwei in wei
MAX_GAS_LIMIT=500000
MIN_PROFIT_THRESHOLD=0.005  # 0.5% minimum profit
MAX_TRADE_SIZE_ETH=10       # Maximum 10 ETH per trade
MAX_SLIPPAGE=0.03           # 3% max slippage
STOP_LOSS_PERCENTAGE=0.02   # 2% stop loss

# =================
# MEV PROTECTION
# =================
FLASHBOTS_RELAY_URL=https://relay.flashbots.net
FLASHBOTS_PRIVATE_KEY=0xYOUR_FLASHBOTS_PRIVATE_KEY
MEV_BLOCKER_ENABLED=true
PRIVATE_MEMPOOL=true

# =================
# API KEYS FOR DATA PROVIDERS
# =================
# Real AI API keys for advanced analysis
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# Price feed APIs
COINGECKO_API_KEY=your_coingecko_api_key
COINMARKETCAP_API_KEY=your_coinmarketcap_api_key
DEFIPULSE_API_KEY=your_defipulse_api_key

# DeFi data providers
DUNE_ANALYTICS_API_KEY=your_dune_api_key
THE_GRAPH_API_KEY=your_graph_api_key
MORALIS_API_KEY=your_moralis_api_key

# =================
# ADVANCED SETTINGS
# =================
ARBITRAGE_TIMEOUT=30000     # 30 seconds
MAX_CONCURRENT_TRADES=3
HEALTH_CHECK_INTERVAL=5000  # 5 seconds
PROFIT_SHARING_ENABLED=false
PROFIT_SHARING_PERCENTAGE=0.1

# =================
# DATABASE & INFRASTRUCTURE
# =================
POSTGRES_PASSWORD=flashloan_secure_password_2024
RABBITMQ_PASSWORD=rabbitmq_secure_password_2024
GRAFANA_PASSWORD=admin

# =================
# MONITORING & ALERTS
# =================
DISCORD_WEBHOOK_URL=your_discord_webhook_for_alerts
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
SLACK_WEBHOOK_URL=your_slack_webhook_url

# =================
# LOGGING
# =================
LOG_LEVEL=INFO
ENABLE_TRADE_LOGGING=true
ENABLE_ERROR_ALERTS=true
LOG_RETENTION_DAYS=30

# =================
# SAFETY SWITCHES
# =================
EMERGENCY_STOP=false
MAX_DAILY_LOSS_USD=1000
CIRCUIT_BREAKER_ENABLED=true
RATE_LIMITING_ENABLED=true
"@

Write-Host "📝 Creating live trading configuration..." -ForegroundColor Cyan

# Backup current .env
Copy-Item -Path ".env" -Destination ".env.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Force
Write-Host "✅ Backed up current .env configuration" -ForegroundColor Green

# Create live .env
$liveEnvConfig | Out-File -FilePath ".env.live" -Encoding UTF8
Write-Host "✅ Created .env.live configuration template" -ForegroundColor Green

Write-Host ""
Write-Host "📋 NEXT STEPS TO COMPLETE LIVE TRADING SETUP:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 🔑 API KEYS - Update the following in .env.live:" -ForegroundColor White
Write-Host "   • INFURA_PROJECT_ID or ALCHEMY_API_KEY" -ForegroundColor Gray
Write-Host "   • OPENAI_API_KEY (for AI analysis)" -ForegroundColor Gray
Write-Host "   • Price feed API keys (CoinGecko, etc.)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 🔐 WALLET SETUP - Configure your trading wallet:" -ForegroundColor White
Write-Host "   • PRIVATE_KEY (your actual wallet private key)" -ForegroundColor Gray
Write-Host "   • WALLET_ADDRESS (your wallet address)" -ForegroundColor Gray
Write-Host "   • Ensure sufficient ETH for gas fees" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 📋 CONTRACTS - Deploy or configure flash loan contracts:" -ForegroundColor White
Write-Host "   • FLASH_LOAN_CONTRACT_MAINNET" -ForegroundColor Gray
Write-Host "   • Verify contracts are deployed and working" -ForegroundColor Gray
Write-Host ""
Write-Host "4. ⚙️  RISK MANAGEMENT - Review and adjust:" -ForegroundColor White
Write-Host "   • MAX_TRADE_SIZE_ETH (start small!)" -ForegroundColor Gray
Write-Host "   • MIN_PROFIT_THRESHOLD" -ForegroundColor Gray
Write-Host "   • MAX_DAILY_LOSS_USD" -ForegroundColor Gray
Write-Host ""
Write-Host "5. 🔔 ALERTS - Set up monitoring:" -ForegroundColor White
Write-Host "   • Discord/Telegram webhook for alerts" -ForegroundColor Gray
Write-Host "   • Emergency contact information" -ForegroundColor Gray

Write-Host ""
Write-Host "⚠️  IMPORTANT SAFETY REMINDERS:" -ForegroundColor Red
Write-Host "• START WITH SMALL AMOUNTS to test the system" -ForegroundColor Yellow
Write-Host "• Monitor the system closely during initial trades" -ForegroundColor Yellow
Write-Host "• Have emergency stop procedures ready" -ForegroundColor Yellow
Write-Host "• Keep private keys secure and backed up" -ForegroundColor Yellow

Write-Host ""
Write-Host "📁 Configuration files created:" -ForegroundColor Cyan
Write-Host "• .env.live - Live trading configuration template" -ForegroundColor White
Write-Host "• .env.backup.* - Backup of your current config" -ForegroundColor White 