"""
CONFIGURATION FILE FOR OPTIMIZED ARBITRAGE BOT
==============================================

Set up your API keys and endpoints here for production use.

DEVELOPMENT NOTES:
- Follow COPILOT_AGENT_RULES.md for development guidelines
- Extend this file for new configuration options rather than creating new config files
- Maintain consistency with existing patterns and naming conventions
"""

import os
import platform
import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Optional, List
from cryptography.fernet import Fernet

# Windows-specific asyncio event loop fix for aiodns compatibility
if platform.system() == 'Windows':
    try:
        # Set the event loop policy to WindowsProactorEventLoopPolicy to avoid aiodns issues
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        print("✅ Set Windows ProactorEventLoopPolicy for aiodns compatibility")
    except AttributeError:
        # Fallback for older Python versions
        try:
            import asyncio.windows_events
            asyncio.set_event_loop_policy(asyncio.windows_events.WindowsProactorEventLoopPolicy())
            print("✅ Set Windows ProactorEventLoopPolicy (fallback)")
        except ImportError:
            print("⚠️ Unable to set Windows event loop policy, may encounter aiodns issues")

# Enhanced Security Configuration
@dataclass
class SecurityEnhancedConfig:
    """Enhanced security configuration with encryption support"""
    
    # Encryption key for sensitive data (auto-generate if not provided)
    ENCRYPTION_KEY: str = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())
    
    # Private key encryption (encrypted form in environment)
    ENCRYPTED_PRIVATE_KEY: Optional[str] = os.getenv('ENCRYPTED_PRIVATE_KEY')
    PRIVATE_KEY_PASSWORD: Optional[str] = os.getenv('PRIVATE_KEY_PASSWORD')
    
    # API key encryption
    ENCRYPTED_API_KEYS: Dict[str, str] = {}
    
    # MEV Protection
    USE_FLASHBOTS: bool = os.getenv('USE_FLASHBOTS', 'true').lower() == 'true'
    FLASHBOTS_RELAY_URL: str = os.getenv('FLASHBOTS_RELAY_URL', 'https://relay.flashbots.net')
    USE_PRIVATE_MEMPOOL: bool = os.getenv('USE_PRIVATE_MEMPOOL', 'true').lower() == 'true'
    
    # Rate limiting and circuit breakers
    MAX_CONSECUTIVE_FAILURES: int = int(os.getenv('MAX_CONSECUTIVE_FAILURES', '5'))
    CIRCUIT_BREAKER_RESET_TIME: int = int(os.getenv('CIRCUIT_BREAKER_RESET_TIME', '300'))
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        f = Fernet(self.ENCRYPTION_KEY.encode())
        return f.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        f = Fernet(self.ENCRYPTION_KEY.encode())
        return f.decrypt(encrypted_data.encode()).decode()
    
    def get_decrypted_private_key(self) -> Optional[str]:
        """Get decrypted private key"""
        if self.ENCRYPTED_PRIVATE_KEY:
            try:
                return self.decrypt_data(self.ENCRYPTED_PRIVATE_KEY)
            except Exception as e:
                logging.error(f"Failed to decrypt private key: {e}")
                return None
        return os.getenv('PRIVATE_KEY')

# Real Web3 and DEX Configuration
@dataclass 
class ProductionAPIConfig:
    """Production API configuration with real credentials"""
    
    # Primary Web3 Providers
    ETH_RPC_URL: str = os.getenv('ETH_RPC_URL', 'https://mainnet.infura.io/v3/YOUR-PROJECT-ID')
    ETH_BACKUP_RPC_URL: str = os.getenv('ETH_BACKUP_RPC_URL', 'https://eth-mainnet.alchemyapi.io/v2/YOUR-API-KEY')
    ETH_WEBSOCKET_URL: str = os.getenv('ETH_WEBSOCKET_URL', 'wss://mainnet.infura.io/ws/v3/YOUR-PROJECT-ID')
    
    # Polygon Network  
    POLYGON_RPC_URL: str = os.getenv('POLYGON_RPC_URL', 'https://polygon-mainnet.infura.io/v3/YOUR-PROJECT-ID')
    POLYGON_BACKUP_RPC_URL: str = os.getenv('POLYGON_BACKUP_RPC_URL', 'https://rpc-mainnet.matic.network')
    
    # Arbitrum Network
    ARB_RPC_URL: str = os.getenv('ARB_RPC_URL', 'https://arbitrum-mainnet.infura.io/v3/YOUR-PROJECT-ID')
    ARB_BACKUP_RPC_URL: str = os.getenv('ARB_BACKUP_RPC_URL', 'https://arb1.arbitrum.io/rpc')
    
    # Optimism Network
    OP_RPC_URL: str = os.getenv('OP_RPC_URL', 'https://optimism-mainnet.infura.io/v3/YOUR-PROJECT-ID')
    OP_BACKUP_RPC_URL: str = os.getenv('OP_BACKUP_RPC_URL', 'https://mainnet.optimism.io')
    
    # Real DEX API Keys
    UNISWAP_V3_SUBGRAPH: str = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    SUSHISWAP_SUBGRAPH: str = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
    BALANCER_SUBGRAPH: str = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2"
    
    # 1inch API
    ONEINCH_API_KEY: Optional[str] = os.getenv('ONEINCH_API_KEY')
    ONEINCH_API_URL: str = "https://api.1inch.io/v5.0/1"
    
    # Moralis API (for enhanced data)
    MORALIS_API_KEY: Optional[str] = os.getenv('MORALIS_API_KEY')
    
    # CoinGecko API (for price validation)
    COINGECKO_API_KEY: Optional[str] = os.getenv('COINGECKO_API_KEY')
    
    # Dextools API (for additional DEX data)
    DEXTOOLS_API_KEY: Optional[str] = os.getenv('DEXTOOLS_API_KEY')
    
    # Etherscan API (for gas and transaction data)
    ETHERSCAN_API_KEY: Optional[str] = os.getenv('ETHERSCAN_API_KEY')
    POLYGONSCAN_API_KEY: Optional[str] = os.getenv('POLYGONSCAN_API_KEY')
    ARBISCAN_API_KEY: Optional[str] = os.getenv('ARBISCAN_API_KEY')
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate that required credentials are set"""
        validation_results = {
            'eth_rpc': 'YOUR-PROJECT-ID' not in self.ETH_RPC_URL,
            'polygon_rpc': 'YOUR-PROJECT-ID' not in self.POLYGON_RPC_URL,
            'oneinch_api': self.ONEINCH_API_KEY is not None,
            'etherscan_api': self.ETHERSCAN_API_KEY is not None,
            'moralis_api': self.MORALIS_API_KEY is not None
        }
        return validation_results

# Enhanced MCP Configuration with Windows Fixes
@dataclass
class MCPConfigEnhanced:
    """Enhanced MCP configuration with Windows aiodns compatibility"""
    
    # MCP Server URLs with health check endpoints
    TASK_MANAGER_URL: str = os.getenv('TASK_MANAGER_URL', 'http://localhost:8007')
    FLASH_LOAN_MCP_URL: str = os.getenv('FLASH_LOAN_MCP_URL', 'http://localhost:8000') 
    FOUNDRY_MCP_URL: str = os.getenv('FOUNDRY_MCP_URL', 'http://localhost:8002')
    COPILOT_MCP_URL: str = os.getenv('COPILOT_MCP_URL', 'http://localhost:8003')
    PRODUCTION_MCP_URL: str = os.getenv('PRODUCTION_MCP_URL', 'http://localhost:8004')
    
    # MCP Server Ports
    MCP_PORTS: Dict[str, int] = {
        'flash_loan_mcp': 8000,
        'foundry_mcp': 8002, 
        'copilot_mcp': 8003,
        'production_mcp': 8004,
        'taskmanager_mcp': 8007
    }
    
    # Connection settings
    MCP_REQUEST_TIMEOUT: int = int(os.getenv('MCP_REQUEST_TIMEOUT', '30'))
    MCP_HEALTH_CHECK_INTERVAL: int = int(os.getenv('MCP_HEALTH_CHECK_INTERVAL', '60'))
    MCP_RETRY_ATTEMPTS: int = int(os.getenv('MCP_RETRY_ATTEMPTS', '3'))
    
    # Authentication
    MCP_AUTH_TOKEN: Optional[str] = os.getenv('MCP_AUTH_TOKEN')
    
    def get_server_health_url(self, server_name: str) -> str:
        """Get health check URL for MCP server"""
        base_urls = {
            'task_manager': self.TASK_MANAGER_URL,
            'flash_loan': self.FLASH_LOAN_MCP_URL,
            'foundry': self.FOUNDRY_MCP_URL,
            'copilot': self.COPILOT_MCP_URL,
            'production': self.PRODUCTION_MCP_URL
        }
        base_url = base_urls.get(server_name, self.TASK_MANAGER_URL)
        return f"{base_url}/health"

@dataclass
class DEXConfig:
    """Configuration for DEX integrations"""
    
    # Web3 Provider URLs (get from Infura/Alchemy)
    WEB3_PROVIDER_URL: str = os.getenv('WEB3_PROVIDER_URL', 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID')
    WEB3_WEBSOCKET_URL: str = os.getenv('WEB3_WEBSOCKET_URL', 'wss://mainnet.infura.io/ws/v3/YOUR_PROJECT_ID')
    
    # Private key for transactions (NEVER commit this to git!)
    PRIVATE_KEY: Optional[str] = os.getenv('PRIVATE_KEY')  # Set in environment variable
    
    # DEX API Endpoints
    UNISWAP_V3_SUBGRAPH: str = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    SUSHISWAP_SUBGRAPH: str = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
    BALANCER_SUBGRAPH: str = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2"
    ONEINCH_API_URL: str = "https://api.1inch.io/v5.0/1"  # Ethereum mainnet
    
    # API Keys (get from respective platforms)
    ONEINCH_API_KEY: Optional[str] = os.getenv('ONEINCH_API_KEY')
    DEXTOOLS_API_KEY: Optional[str] = os.getenv('DEXTOOLS_API_KEY')
    
    # Flash Loan Providers
    AAVE_V3_POOL: str = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"  # Ethereum mainnet
    UNISWAP_V3_FACTORY: str = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    
    # Gas Configuration
    MAX_GAS_PRICE_GWEI: int = 50
    GAS_LIMIT_MULTIPLIER: float = 1.2
    
    # Trading Parameters
    MIN_PROFIT_USD: float = 25.0
    MAX_TRADE_SIZE_USD: float = 50000.0
    MAX_SLIPPAGE_PERCENT: float = 1.0
    
    # MEV Protection
    FLASHBOTS_RELAY_URL: str = "https://relay.flashbots.net"
    USE_PRIVATE_MEMPOOL: bool = True

@dataclass
class MCPConfig:
    """Configuration for MCP server endpoints"""
    
    # MCP Server URLs
    TASK_MANAGER_URL: str = os.getenv('TASK_MANAGER_URL', 'http://localhost:8007')
    FLASH_LOAN_MCP_URL: str = os.getenv('FLASH_LOAN_MCP_URL', 'http://localhost:8000')
    FOUNDRY_MCP_URL: str = os.getenv('FOUNDRY_MCP_URL', 'http://localhost:8001')
    PRODUCTION_MCP_URL: str = os.getenv('PRODUCTION_MCP_URL', 'http://localhost:8004')
    DEX_MONITOR_MCP_URL: str = os.getenv('DEX_MONITOR_MCP_URL', 'http://localhost:8005')
    
    # Authentication tokens if required
    MCP_AUTH_TOKEN: Optional[str] = os.getenv('MCP_AUTH_TOKEN')
    
    # Timeout settings
    MCP_REQUEST_TIMEOUT: int = 30
    MCP_HEALTH_CHECK_INTERVAL: int = 60

@dataclass
class DatabaseConfig:
    """Configuration for database connections"""
    
    # Redis for caching
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_TTL_SECONDS: int = 300  # 5 minutes
    
    # PostgreSQL for persistent storage
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://localhost/arbitrage_bot')
    
    # MongoDB for analytics (optional)
    MONGODB_URL: Optional[str] = os.getenv('MONGODB_URL')

@dataclass
class SecurityConfig:
    """Security and risk management configuration"""
    
    # Circuit Breaker Settings
    MAX_CONSECUTIVE_FAILURES: int = 5
    CIRCUIT_BREAKER_RESET_TIME: int = 300  # 5 minutes
    
    # Risk Management
    MAX_DAILY_LOSS_USD: float = 1000.0
    MAX_POSITION_SIZE_PERCENT: float = 10.0  # % of available balance
    
    # Rate Limiting
    API_REQUESTS_PER_SECOND: int = 10
    MAX_CONCURRENT_TRADES: int = 3
    
    # Monitoring
    ENABLE_REAL_TIME_ALERTS: bool = True
    DISCORD_WEBHOOK_URL: Optional[str] = os.getenv('DISCORD_WEBHOOK_URL')
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

@dataclass
class BotConfig:
    """Main bot configuration"""
    
    # Environment
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')  # development, staging, production
    
    # Execution Parameters
    CYCLE_INTERVAL_SECONDS: int = 5
    PRICE_UPDATE_INTERVAL_SECONDS: int = 2
    OPPORTUNITY_ANALYSIS_INTERVAL_SECONDS: int = 1
    
    # Performance Optimization
    MAX_PARALLEL_PRICE_FETCHES: int = 10
    CONNECTION_POOL_SIZE: int = 100
    ENABLE_CACHING: bool = True
    CACHE_TTL_SECONDS: int = 10
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = 'arbitrage_bot.log'
    ENABLE_FILE_LOGGING: bool = True
    ENABLE_CONSOLE_LOGGING: bool = True

# Main configuration instances
dex_config = DEXConfig()
mcp_config = MCPConfig()
database_config = DatabaseConfig()
security_config = SecurityConfig()
bot_config = BotConfig()
security_enhanced_config = SecurityEnhancedConfig()
production_api_config = ProductionAPIConfig()
mcp_config_enhanced = MCPConfigEnhanced()

# Token addresses for common pairs (Ethereum mainnet)
TOKEN_ADDRESSES = {
    'ETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
    'USDC': '0xA0b86a33E6417aff97058c1ba2b08fbef17B1aD4',
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    'LINK': '0x514910771AF9Ca656af840dff83E8264EcF986CA',
    'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
    'AAVE': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',
    'COMP': '0xc00e94Cb662C3520282E6f5717214004A7f26888',
}

# High-priority token pairs for arbitrage
PRIORITY_PAIRS = [
    ('ETH', 'USDC'),
    ('ETH', 'USDT'),
    ('WBTC', 'ETH'),
    ('ETH', 'DAI'),
    ('LINK', 'ETH'),
    ('UNI', 'ETH'),
]

# DEX router addresses for direct integration
DEX_ROUTERS = {
    'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
    'uniswap_v2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
    'sushiswap': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
    'balancer': '0xBA12222222228d8Ba445958a75a0704d566BF2C8',
}

def validate_config() -> List[str]:
    """Validate configuration settings"""
    
    errors: List[str] = []
    
    # Check required environment variables
    if not dex_config.PRIVATE_KEY:
        errors.append("PRIVATE_KEY environment variable is required")
    
    if 'YOUR_PROJECT_ID' in dex_config.WEB3_PROVIDER_URL:
        errors.append("Please set a valid Web3 provider URL with your Infura/Alchemy project ID")
    
    # Validate numeric ranges
    if security_config.MAX_CONSECUTIVE_FAILURES < 1:
        errors.append("MAX_CONSECUTIVE_FAILURES must be at least 1")
    
    if dex_config.MIN_PROFIT_USD < 0:
        errors.append("MIN_PROFIT_USD must be positive")
    
    if dex_config.MAX_SLIPPAGE_PERCENT > 10:
        errors.append("MAX_SLIPPAGE_PERCENT should not exceed 10% for safety")
    
    # Environment-specific validations
    if bot_config.ENVIRONMENT == 'production':
        if not dex_config.ONEINCH_API_KEY:
            errors.append("1inch API key is recommended for production")
        
        if security_config.MAX_DAILY_LOSS_USD > 10000:
            errors.append("MAX_DAILY_LOSS_USD is very high for production")
    
    return errors

def get_environment_setup_instructions():
    """Return setup instructions for environment variables"""
    
    return """
ENVIRONMENT SETUP INSTRUCTIONS
=============================

1. Create a .env file in your project directory with:

# Web3 Provider (Required)
WEB3_PROVIDER_URL=https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
WEB3_WEBSOCKET_URL=wss://mainnet.infura.io/ws/v3/YOUR_INFURA_PROJECT_ID

# Private Key (Required - NEVER commit to git!)
PRIVATE_KEY=your_private_key_here

# API Keys (Optional but recommended)
ONEINCH_API_KEY=your_1inch_api_key
DEXTOOLS_API_KEY=your_dextools_api_key

# Database URLs (Optional)
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/arbitrage_bot

# MCP Server URLs (if different from defaults)
TASK_MANAGER_URL=http://localhost:8007
FLASH_LOAN_MCP_URL=http://localhost:8000
FOUNDRY_MCP_URL=http://localhost:8001
PRODUCTION_MCP_URL=http://localhost:8004

# Monitoring (Optional)
DISCORD_WEBHOOK_URL=your_discord_webhook_url
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Environment
ENVIRONMENT=development  # or staging, production
LOG_LEVEL=INFO

2. Install python-dotenv to load the .env file:
   pip install python-dotenv

3. Add this to the beginning of your bot script:
   from dotenv import load_dotenv
   load_dotenv()

4. Get API keys from:
   - Infura: https://infura.io/
   - Alchemy: https://alchemy.com/
   - 1inch: https://portal.1inch.io/
   - DexTools: https://www.dextools.io/api

5. For production, use environment variables directly instead of .env file
"""

if __name__ == "__main__":
    # Validate configuration when run directly
    errors: List[str] = validate_config()
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        print("\n" + get_environment_setup_instructions())
    else:
        print("✅ Configuration validation passed!")
        print(f"Environment: {bot_config.ENVIRONMENT}")
        print(f"Web3 Provider: {dex_config.WEB3_PROVIDER_URL[:50]}...")
        print(f"Private Key Set: {'Yes' if dex_config.PRIVATE_KEY else 'No'}")
        print(f"MCP Endpoints: {len([url for url in [mcp_config.TASK_MANAGER_URL, mcp_config.FLASH_LOAN_MCP_URL] if url])} configured")
