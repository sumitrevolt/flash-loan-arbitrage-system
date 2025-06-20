"""
Dynamic slippage calculation module for flash loan arbitrage.
This module provides functions to calculate optimal slippage tolerance
based on token volatility, trade size, and market conditions.
"""

import time
import logging
import math
from typing import Dict, Any, Optional, Tuple
import json
import os

# Import from central web3_provider - no mock fallback
try:
    from src.utils.web3_provider import Web3, TxParams, Wei, ChecksumAddress
    from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
    WEB3_IMPORTED = True
except ImportError as e:
    logging.getLogger(__name__).error(f"Failed to import Web3: {e}")
    raise ImportError(f"Web3 is required but not available: {e}")

# Set up logging
logger = logging.getLogger(__name__)

class DynamicSlippageCalculator:
    """
    Calculates optimal slippage tolerance based on market conditions.
    """
    
    def __init__(self, config_path: str = "config/slippage_config.json"):
        """
        Initialize the dynamic slippage calculator.
        
        Args:
            config_path: Path to the slippage configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.token_volatility_cache = {}
        self.volatility_cache_ttl = 300  # 5 minutes
        self.last_volatility_update = {}
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load slippage configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading slippage config: {e}")
            
        # Default configuration
        return {
            "base_slippage": 0.5,  # 0.5% base slippage
            "max_slippage": 3.0,   # 3% maximum slippage
            "volatility_factor": 0.5,  # How much volatility affects slippage
            "size_factor": 0.3,    # How much trade size affects slippage
            "gas_factor": 0.2,     # How much gas price affects slippage
            "token_specific_adjustments": {
                "WETH": 0.8,  # Reduce slippage for stable tokens
                "WBTC": 0.8,
                "USDC": 0.5,
                "USDT": 0.5,
                "DAI": 0.5,
                "WMATIC": 1.2,  # Increase slippage for volatile tokens
                "LINK": 1.0,
                "AAVE": 1.1,
                "UNI": 1.1,
                "SUSHI": 1.2
            },
            "dex_specific_adjustments": {
                "QuickSwap": 1.0,
                "SushiSwap": 1.1,
                "UniswapV3": 0.9
            }
        }
        
    def save_config(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Saved slippage configuration to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving slippage config: {e}")
            
    def calculate_slippage(
        self, 
        token_symbol: str, 
        trade_size_usd: float, 
        buy_dex: str, 
        sell_dex: str,
        token_price: float,
        gas_price_gwei: float
    ) -> Tuple[float, float]:
        """
        Calculate optimal slippage tolerance for a trade.
        
        Args:
            token_symbol: Symbol of the token being traded
            trade_size_usd: Size of the trade in USD
            buy_dex: Name of the DEX where tokens are bought
            sell_dex: Name of the DEX where tokens are sold
            token_price: Current price of the token in USD
            gas_price_gwei: Current gas price in Gwei
            
        Returns:
            Tuple[float, float]: (buy_slippage_percentage, sell_slippage_percentage)
        """
        # Get base slippage
        base_slippage = self.config["base_slippage"]
        
        # Get token-specific adjustment
        token_adjustment = self.config["token_specific_adjustments"].get(token_symbol, 1.0)
        
        # Get DEX-specific adjustments
        buy_dex_adjustment = self.config["dex_specific_adjustments"].get(buy_dex, 1.0)
        sell_dex_adjustment = self.config["dex_specific_adjustments"].get(sell_dex, 1.0)
        
        # Calculate volatility factor
        volatility = self.get_token_volatility(token_symbol, token_price)
        volatility_component = volatility * self.config["volatility_factor"]
        
        # Calculate size factor (larger trades need more slippage)
        size_ratio = min(trade_size_usd / 1000.0, 10.0)  # Cap at 10x
        size_component = math.log10(1 + size_ratio) * self.config["size_factor"]
        
        # Calculate gas factor (higher gas prices need more slippage)
        gas_ratio = min(gas_price_gwei / 100.0, 5.0)  # Cap at 5x
        gas_component = math.log10(1 + gas_ratio) * self.config["gas_factor"]
        
        # Calculate final slippage values
        buy_slippage = (base_slippage + volatility_component + size_component + gas_component) * token_adjustment * buy_dex_adjustment
        sell_slippage = (base_slippage + volatility_component + size_component + gas_component) * token_adjustment * sell_dex_adjustment
        
        # Cap at maximum slippage
        max_slippage = self.config["max_slippage"]
        buy_slippage = min(buy_slippage, max_slippage)
        sell_slippage = min(sell_slippage, max_slippage)
        
        self.logger.info(f"Calculated slippage for {token_symbol}: buy={buy_slippage:.2f}%, sell={sell_slippage:.2f}%")
        self.logger.debug(f"Slippage components - Base: {base_slippage}, Volatility: {volatility_component:.2f}, " +
                         f"Size: {size_component:.2f}, Gas: {gas_component:.2f}, Token Adj: {token_adjustment}")
        
        return buy_slippage, sell_slippage
        
    def get_token_volatility(self, token_symbol: str, current_price: float) -> float:
        """
        Get the volatility factor for a token.
        
        Args:
            token_symbol: Symbol of the token
            current_price: Current price of the token
            
        Returns:
            float: Volatility factor (0.0-1.0)
        """
        now = time.time()
        
        # Check if we have recent volatility data
        if token_symbol in self.token_volatility_cache and token_symbol in self.last_volatility_update:
            if now - self.last_volatility_update[token_symbol] < self.volatility_cache_ttl:
                return self.token_volatility_cache[token_symbol]
        
        # Update volatility with new price data
        if token_symbol not in self.token_volatility_cache:
            # Initialize with moderate volatility
            self.token_volatility_cache[token_symbol] = 0.5
            self.last_volatility_update[token_symbol] = now
        else:
            # Simple volatility calculation based on price change
            last_price = self.token_volatility_cache.get(f"{token_symbol}_last_price", current_price)
            price_change_pct = abs(current_price - last_price) / last_price if last_price > 0 else 0
            
            # Update volatility (exponential moving average)
            current_volatility = self.token_volatility_cache[token_symbol]
            new_volatility = 0.7 * current_volatility + 0.3 * min(price_change_pct * 10, 1.0)
            
            self.token_volatility_cache[token_symbol] = new_volatility
            self.token_volatility_cache[f"{token_symbol}_last_price"] = current_price
            self.last_volatility_update[token_symbol] = now
            
        return self.token_volatility_cache[token_symbol]

    def get_real_dex_prices(self, token_symbol: str, dex_list: list) -> Dict[str, float]:
        """
        Get real prices from all specified DEXes for a token.
        
        Args:
            token_symbol: Symbol of the token to get prices for
            dex_list: List of DEX names to query
            
        Returns:
            Dict[str, float]: Mapping of DEX name to token price
        """
        prices = {}
        
        for dex_name in dex_list:
            try:
                # This would integrate with actual DEX price fetching
                # For now, return placeholder that indicates real price needed
                price = self._fetch_real_dex_price(token_symbol, dex_name)
                if price and price > 0:
                    prices[dex_name] = price
                    self.logger.debug(f"Real price from {dex_name} for {token_symbol}: ${price:.6f}")
                else:
                    self.logger.warning(f"Could not get real price from {dex_name} for {token_symbol}")
            except Exception as e:
                self.logger.error(f"Error fetching real price from {dex_name} for {token_symbol}: {e}")
                
        return prices
    
    def _fetch_real_dex_price(self, token_symbol: str, dex_name: str) -> Optional[float]:
        """
        Fetch real price from a specific DEX.
        This should be implemented to query actual DEX contracts/APIs.
        
        Args:
            token_symbol: Symbol of the token
            dex_name: Name of the DEX
            
        Returns:
            float: Real price from DEX or None if unavailable
        """
        # TODO: Implement actual DEX price fetching here
        # This should query real DEX contracts or APIs
        self.logger.info(f"Fetching real price for {token_symbol} from {dex_name}")
        
        # For now, return None to indicate real implementation needed
        return None
