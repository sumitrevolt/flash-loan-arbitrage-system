"""
DEX integration module for Flash Loan Arbitrage System.
Clean implementation focusing on core functionality needed for revenue generation.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from decimal import Decimal
import traceback

# Web3 imports with error handling
try:
    # Import from central web3_provider
    from src.utils.web3_provider import Web3
    # Import exceptions from central provider
    from src.utils.web3_provider import ContractLogicError
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None
    ContractLogicError = Exception

class RateLimiter:
    """Rate limiter for RPC requests to prevent hitting rate limits."""

    def __init__(self, requests_per_second: float = 5.0, burst_limit: int = 10, cooldown_period: float = 1.0):
        self.requests_per_second = requests_per_second
        self.burst_limit = burst_limit
        self.cooldown_period = cooldown_period
        self.request_times = []
        self.is_cooled_down = False
        self.cooldown_start = None

    def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits."""
        current_time = time.time()
        
        # Check if we're in cooldown
        if self.is_cooled_down:
            if current_time - self.cooldown_start > self.cooldown_period:
                self.is_cooled_down = False
                self.request_times.clear()
            else:
                return False
        
        # Remove old requests outside the time window
        window_start = current_time - 1.0
        self.request_times = [t for t in self.request_times if t > window_start]
        
        # Check if we can make a request
        if len(self.request_times) >= self.burst_limit:
            self.is_cooled_down = True
            self.cooldown_start = current_time
            return False
        
        return True

    def record_request(self):
        """Record that a request was made."""
        self.request_times.append(time.time())

class DEXIntegration:
    """
    Clean DEX integration class focused on essential functionality.
    Provides interfaces to interact with various DEXes on the Polygon network.
    """
    
    def __init__(self, config=None, logger=None, rpc_manager=None):
        """Initialize DEX integration with configuration."""
        # Handle legacy rpc_manager parameter for compatibility
        if rpc_manager is not None and config is None:
            # If rpc_manager is provided but no config, create a basic config
            config = {"rpc_manager": rpc_manager}
        
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        self.rpc_manager = rpc_manager  # Store for compatibility
        
        # Initialize Web3 connection
        self.w3 = None
        self._init_web3_connection()
        
        # Initialize rate limiter
        rate_limit_config = self.config.get("rate_limit_settings", {})
        self.rate_limiter = RateLimiter(
            requests_per_second=rate_limit_config.get("requests_per_second", 5.0),
            burst_limit=rate_limit_config.get("burst_limit", 10),
            cooldown_period=rate_limit_config.get("cooldown_period", 1.0)
        )
        
        # Token and DEX addresses
        self._init_addresses()
        
        self.logger.info("DEX Integration initialized successfully for real-time price fetching")

    def _init_web3_connection(self):
        """Initialize Web3 connection with fallback options."""
        if not WEB3_AVAILABLE:
            self.logger.error("Web3 not available")
            return
            
        rpc_urls = [
            self.config.get("polygon_rpc_url", "https://polygon-rpc.com"),
            "https://polygon-bor.publicnode.com",
            "https://rpc-mainnet.matic.network"
        ]
        
        for rpc_url in rpc_urls:
            try:
                self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
                if self.w3.is_connected():
                    self.logger.info(f"Connected to Polygon via {rpc_url}")
                    break
            except Exception as e:
                self.logger.warning(f"Failed to connect via {rpc_url}: {e}")
                continue
        
        if not self.w3 or not self.w3.is_connected():
            self.logger.error("Failed to establish Web3 connection")

    def _init_addresses(self):
        """Initialize token and DEX router addresses."""
        # Default Polygon mainnet addresses
        if WEB3_AVAILABLE and Web3:
            self.weth_address = Web3.to_checksum_address('0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619')
            self.wmatic_address = Web3.to_checksum_address('0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270')
        else:
            self.weth_address = '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'
            self.wmatic_address = '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'
        
        # Default router addresses
        self.default_routers = {
            "QuickSwap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
            "SushiSwap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
            "UniswapV3": "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        }
        
        # Default token addresses
        self.default_tokens = {
            "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
            "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
            "LINK": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
            "UNI": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",
            "AAVE": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
            "CRV": "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
            "SUSHI": "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a",
            "BAL": "0x9a71012B13CA4d3D0Cdc72A177DF3ef03b0E76A3"
        }

    @property
    def routers(self) -> Dict[str, str]:
        """Get a dictionary of DEX routers."""
        result: str = {}
        
        # Get from config if available
        dexes = self.config.get("dexes", {})
        if isinstance(dexes, dict):
            for dex_name, dex_info in dexes.items():
                if isinstance(dex_info, dict) and dex_info.get("router"):
                    if dex_name.lower() == "quickswap":
                        result["QuickSwap"] = dex_info["router"]
                    elif dex_name.lower() == "sushiswap":
                        result["SushiSwap"] = dex_info["router"]
                    elif dex_name.lower() == "uniswapv3":
                        result["UniswapV3"] = dex_info["router"]
        
        # Fallback to defaults
        for name, address in self.default_routers.items():
            if name not in result:
                result[name] = address
        
        return result

    @property
    def tokens(self) -> Dict[str, str]:
        """Get a dictionary of token addresses."""
        result: str = {}
        
        # Get from config if available
        tokens_config = self.config.get("tokens", {})
        if isinstance(tokens_config, dict):
            for symbol, address in tokens_config.items():
                result[symbol.upper()] = address
        
        # Fallback to defaults
        for symbol, address in self.default_tokens.items():
            if symbol not in result:
                result[symbol] = address
        
        return result

    def get_token_address(self, token_symbol: str) -> Optional[str]:
        """Get token address by symbol."""
        try:
            token_symbol = token_symbol.upper()
            tokens = self.tokens
            address = tokens.get(token_symbol)
            
            if address and WEB3_AVAILABLE and Web3:
                return Web3.to_checksum_address(address)
            return address
        except Exception as e:
            self.logger.error(f"Error getting token address for {token_symbol}: {e}")
            return None

    def get_router_address(self, dex_name: str) -> Optional[str]:
        """Get router address by DEX name."""
        try:
            routers = self.routers
            
            # Try exact match first
            if dex_name in routers:
                address = routers[dex_name]
                if WEB3_AVAILABLE and Web3:
                    return Web3.to_checksum_address(address)
                return address
            
            # Try case-insensitive match
            for router_name, address in routers.items():
                if router_name.lower() == dex_name.lower():
                    if WEB3_AVAILABLE and Web3:
                        return Web3.to_checksum_address(address)
                    return address
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting router address for {dex_name}: {e}")
            return None

    async def update_prices(self) -> bool:
        """Update token prices from all configured DEXes."""
        try:
            self.logger.info("Real-time price updates via UnifiedDEXPriceFetcher")
            # Prices are fetched in real-time when needed, no caching
            return True
        except Exception as e:
            self.logger.error(f"Error updating prices: {e}")
            return False

    async def get_token_price(self, token_symbol: str, dex_name: Optional[str] = None) -> Optional[float]:
        """Get real-time token price in USD from blockchain."""
        try:
            # Rate limiting
            if not self.rate_limiter.can_make_request():
                self.logger.warning("Rate limit exceeded, cannot fetch price")
                return None
            
            # Check if Web3 is connected
            if not self.w3 or not self.w3.is_connected():
                self.logger.error("Web3 not connected, cannot fetch real-time price")
                return None
            
            # Import and use UnifiedDEXPriceFetcher for real-time prices
            try:
                from src.utils.unified_dex_price_fetcher import UnifiedDEXPriceFetcher
                price_fetcher = UnifiedDEXPriceFetcher(self.w3)
                
                # Get real-time price from specific DEX or all DEXes
                if dex_name:
                    price = await price_fetcher.get_price_in_usdc(token_symbol, dex_name)
                else:
                    # Get average price from all DEXes
                    prices = await price_fetcher.get_all_dex_prices(token_symbol)
                    if prices:
                        price = sum(prices.values()) / len(prices)
                        self.logger.info(f"Average price for {token_symbol} from {len(prices)} DEXes: ${price:.6f}")
                    else:
                        price = None
                
                if price:
                    self.logger.info(f"Real-time price for {token_symbol}: ${price:.6f}")
                    self.rate_limiter.record_request()
                    return price
                else:
                    self.logger.warning(f"Could not fetch real-time price for {token_symbol}")
                    return None
                    
            except ImportError:
                self.logger.error("UnifiedDEXPriceFetcher not available")
                return None
            
        except Exception as e:
            self.logger.error(f"Error getting real-time token price for {token_symbol}: {e}")
            return None

    async def _get_uniswap_v2_price(self, token_address: str, usdc_address: str, dex_info: Dict[str, Any]) -> Optional[float]:
        """Get token price using Uniswap V2 style pair contract."""
        try:
            if not self.w3 or not self.w3.is_connected():
                self.logger.warning("Web3 not connected, cannot fetch real price")
                return None
            
            # Import UnifiedDEXPriceFetcher to handle the actual price fetching
            from src.utils.unified_dex_price_fetcher import UnifiedDEXPriceFetcher
            price_fetcher = UnifiedDEXPriceFetcher(self.w3)
            
            # Use the price fetcher's V2 method
            amount_in = 10 ** 18  # 1 token with 18 decimals
            price_wei = await price_fetcher.get_token_price_v2(
                token_address,
                usdc_address,
                amount_in,
                "quickswap"  # Default to QuickSwap for V2
            )
            
            if price_wei:
                # Convert to USD (USDC has 6 decimals)
                price_usd = float(price_wei) / (10 ** 6)
                return price_usd
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Uniswap V2 price: {e}")
            return None

    def reset_circuit_breaker(self):
        """Reset the rate limiter circuit breaker."""
        try:
            self.rate_limiter.is_cooled_down = False
            self.rate_limiter.cooldown_start = None
            self.rate_limiter.request_times.clear()
            self.logger.info("Circuit breaker reset successfully")
        except Exception as e:
            self.logger.error(f"Error resetting circuit breaker: {e}")

# Compatibility functions for the transaction executor
def create_dex_integration(config: Dict[str, Any] = None, logger: logging.Logger = None) -> DEXIntegration:
    """Factory function to create DEX integration instance."""
    return DEXIntegration(config, logger)
