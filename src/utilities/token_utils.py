"""
Token utilities for the Flash Loan System.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

class TokenUtils:
    """
    Utility class for token-related operations.
    """

    def __init__(self, token_data_path='config/token_data.json', dex_config_path='config/dex_config.json'):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.token_data_path = token_data_path
        self.dex_config_path = dex_config_path
        self.token_data = self._load_token_data()
        self.dex_info = self._load_dex_info()

    def _load_token_data(self) -> Dict[str, Any]:
        """Load token data from configuration."""
        try:
            if os.path.exists(self.token_data_path):
                with open(self.token_data_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading token data: {e}")

        # Default token data
        return {
            "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
            "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "LINK": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
            "AAVE": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
            "UNI": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",
            "SUSHI": "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a",
            "CRV": "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
            "QUICK": "0x831753DD7087CaC61aB5644b308642cc1c33Dc13",
            "MATIC": "0x0000000000000000000000000000000000001010"
        }

    def get_token_address(self, symbol_or_address: str) -> Optional[str]:
        """
        Get token address by symbol or return the address if it's already an address.

        Args:
            symbol_or_address (str): Token symbol or address

        Returns:
            Optional[str]: Token address
        """
        # If it's already an address (starts with 0x), return it
        if symbol_or_address and symbol_or_address.startswith('0x'):
            return symbol_or_address

        # Otherwise, look up the address by symbol
        return self.token_data.get(symbol_or_address.upper())

    def get_token_symbol(self, address_or_symbol: str) -> Optional[str]:
        """
        Get token symbol by address or return the symbol if it's already a symbol.

        Args:
            address_or_symbol (str): Token address or symbol

        Returns:
            Optional[str]: Token symbol
        """
        # If it's already a symbol (doesn't start with 0x), check if it's in our token data
        if not address_or_symbol.startswith('0x'):
            symbol = address_or_symbol.upper()
            if symbol in self.token_data:
                return symbol

        # Otherwise, look up the symbol by address
        address = address_or_symbol.lower()
        for symbol, addr in self.token_data.items():
            if addr.lower() == address:
                return symbol

        return None

    def is_token_supported(self, symbol: str) -> bool:
        """Check if a token is supported."""
        return symbol.upper() in self.token_data

    def get_supported_tokens(self) -> list:
        """Get list of supported tokens."""
        return list(self.token_data.keys())

    def add_token(self, symbol: str, address: str) -> bool:
        """Add a new token."""
        try:
            symbol = symbol.upper()
            self.token_data[symbol] = address
            return self._save_token_data()
        except Exception as e:
            self.logger.error(f"Error adding token {symbol}: {e}")
            return False

    def remove_token(self, symbol: str) -> bool:
        """Remove a token."""
        try:
            symbol = symbol.upper()
            if symbol in self.token_data:
                del self.token_data[symbol]
                return self._save_token_data()
            return False
        except Exception as e:
            self.logger.error(f"Error removing token {symbol}: {e}")
            return False

    def _save_token_data(self) -> bool:
        """Save token data to file."""
        try:
            os.makedirs(os.path.dirname(self.token_data_path), exist_ok=True)
            with open(self.token_data_path, 'w') as f:
                json.dump(self.token_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving token data: {e}")
            return False

    def _load_dex_info(self) -> Dict[str, Any]:
        """
        Load DEX information from configuration file.

        Returns:
            Dict[str, Any]: DEX information.
        """
        try:
            if os.path.exists(self.dex_config_path):
                with open(self.dex_config_path, 'r') as f:
                    return json.load(f)
            else:
                # Default DEX information
                return {
                    "quickswap": {
                        "name": "QuickSwap",
                        "router_address": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
                        "factory_address": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"
                    },
                    "sushiswap": {
                        "name": "SushiSwap",
                        "router_address": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
                        "factory_address": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
                    },
                    "uniswap": {
                        "name": "UniswapV3",
                        "router_address": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
                        "factory_address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
                    }
                }
        except Exception as e:
            self.logger.error(f"Error loading DEX information: {e}")
            return {}

    def get_dex_router_address(self, dex_name: str) -> Optional[str]:
        """
        Get the router address for a DEX.

        Args:
            dex_name (str): DEX name.

        Returns:
            Optional[str]: Router address.
        """
        dex_name = dex_name.lower()
        if dex_name in self.dex_info:
            return self.dex_info[dex_name].get("router_address")
        return None

    def get_token_decimals(self, token_symbol: str) -> int:
        """
        Get the number of decimals for a token.

        Args:
            token_symbol (str): Token symbol.

        Returns:
            int: Number of decimals.
        """
        # Default token decimals
        token_decimals = {
            "WETH": 18,
            "WBTC": 8,
            "USDC": 6,
            "USDT": 6,
            "DAI": 18,
            "WMATIC": 18,
            "LINK": 18,
            "AAVE": 18,
            "UNI": 18,
            "SUSHI": 18,
            "CRV": 18,
            "QUICK": 18,
            "MATIC": 18
        }

        token_symbol = token_symbol.upper()
        return token_decimals.get(token_symbol, 18)  # Default to 18 decimals

    def get_token_info(self, symbol_or_address: str) -> Dict[str, Any]:
        """
        Get token information by symbol or address.

        Args:
            symbol_or_address (str): Token symbol or address.

        Returns:
            Dict[str, Any]: Token information including address and decimals.
        """
        # Default token decimals
        token_decimals = {
            "WETH": 18,
            "WBTC": 8,
            "USDC": 6,
            "USDT": 6,
            "DAI": 18,
            "WMATIC": 18,
            "LINK": 18,
            "AAVE": 18,
            "UNI": 18,
            "SUSHI": 18,
            "CRV": 18,
            "QUICK": 18,
            "MATIC": 18
        }

        # If it's an address, get the symbol first
        if symbol_or_address and symbol_or_address.startswith('0x'):
            symbol = self.get_token_symbol(symbol_or_address)
            if not symbol:
                # If we can't find the symbol, create a basic info object with the address
                return {
                    "address": symbol_or_address,
                    "decimals": 18,  # Default to 18 decimals
                    "symbol": "UNKNOWN"
                }
        else:
            symbol = symbol_or_address.upper()

        # Now we have a symbol, get the address
        if symbol not in self.token_data:
            return {}

        return {
            "address": self.token_data[symbol],
            "decimals": token_decimals.get(symbol, 18),  # Default to 18 decimals if not specified
            "symbol": symbol
        }

# Create singleton instance
token_utils = TokenUtils()
