"""
Intermediate Token Selector for Flash Loan Arbitrage
"""

from typing import Dict, Optional, List
import logging

class IntermediateTokenSelector:
    """
    Selects the optimal intermediate token for flash loan arbitrage based on token pairs and market conditions.
    """
    
    # Common token addresses on Polygon
    TOKEN_ADDRESSES = {
        "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
    }
    
    # Token categories for optimal routing
    STABLE_TOKENS = ["USDC", "USDT", "DAI"]
    BLUE_CHIP_TOKENS = ["WETH", "WBTC"]
    NATIVE_TOKENS = ["WMATIC"]
    
    def __init__(self):
        self.logger = logging.getLogger("intermediate_token_selector")
        self.token_pairs_cache: Dict[str, str] = {}
    
    def get_best_intermediate_token(self, token_symbol: str, buy_dex: str, sell_dex: str) -> str:
        """
        Get the best intermediate token address for a given token and DEX pair.
        
        Args:
            token_symbol: Symbol of the token being traded
            buy_dex: Name of the buy DEX
            sell_dex: Name of the sell DEX
            
        Returns:
            str: Address of the best intermediate token
        """
        # Create a cache key
        cache_key = f"{token_symbol}:{buy_dex}:{sell_dex}"
        
        # Check if we have a cached result
        if cache_key in self.token_pairs_cache:
            return self.token_pairs_cache[cache_key]
        
        # Default to WETH as fallback
        default_token = self.TOKEN_ADDRESSES["WETH"]
        
        # If the token is already one of our potential intermediate tokens, we need a different one
        if token_symbol in self.TOKEN_ADDRESSES:
            # For stable tokens, use WETH as intermediate
            if token_symbol in self.STABLE_TOKENS:
                selected_token = self.TOKEN_ADDRESSES["WETH"]
            
            # For WETH, use USDC as intermediate
            elif token_symbol == "WETH":
                selected_token = self.TOKEN_ADDRESSES["USDC"]
            
            # For WBTC, use WETH as intermediate
            elif token_symbol == "WBTC":
                selected_token = self.TOKEN_ADDRESSES["WETH"]
            
            # For WMATIC, use WETH as intermediate
            elif token_symbol == "WMATIC":
                selected_token = self.TOKEN_ADDRESSES["WETH"]
            
            # For any other token, use WETH as intermediate
            else:
                selected_token = default_token
        else:
            # For unknown tokens, use WETH as intermediate
            selected_token = default_token
        
        # Special case for UniswapV3 - it works better with USDC for some pairs
        if "uniswap" in buy_dex.lower() or "uniswap" in sell_dex.lower():
            # For stable pairs on Uniswap, use USDC
            if token_symbol in self.STABLE_TOKENS:
                if token_symbol != "USDC":
                    selected_token = self.TOKEN_ADDRESSES["USDC"]
        
        # Cache the result
        self.token_pairs_cache[cache_key] = selected_token
        
        self.logger.info(f"Selected {self._get_token_symbol_from_address(selected_token)} as intermediate token for {token_symbol} between {buy_dex} and {sell_dex}")
        return selected_token
    
    def _get_token_symbol_from_address(self, address: str) -> str:
        """Get token symbol from address"""
        for symbol, addr in self.TOKEN_ADDRESSES.items():
            if addr.lower() == address.lower():
                return symbol
        return "Unknown"

# Singleton instance
intermediate_token_selector = IntermediateTokenSelector()
