"""
Token data module for the Flash Loan Arbitrage System.
Provides access to token data and utilities.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from src.data import TOKEN_DATA_PATH, load_json_data, save_json_data

logger = logging.getLogger(__name__)

class TokenData:
    """
    Manages token data for the Flash Loan Arbitrage System.
    """
    
    def __init__(self):
        """Initialize the token data manager."""
        self.tokens = self.load_token_data()
    
    def load_token_data(self) -> Dict[str, Any]:
        """Load token data from the token data file."""
        return load_json_data(TOKEN_DATA_PATH, default={})
    
    def save_token_data(self) -> bool:
        """Save token data to the token data file."""
        return save_json_data(TOKEN_DATA_PATH, self.tokens)
    
    def get_token_address(self, symbol: str) -> Optional[str]:
        """Get the address of a token by its symbol."""
        token = self.tokens.get(symbol.upper())
        if token:
            return token.get("address")
        return None
    
    def get_token_decimals(self, symbol: str) -> int:
        """Get the decimals of a token by its symbol."""
        token = self.tokens.get(symbol.upper())
        if token:
            return token.get("decimals", 18)
        return 18  # Default to 18 decimals (ETH standard)
    
    def get_all_tokens(self) -> List[Dict[str, Any]]:
        """Get all tokens."""
        return [{"symbol": symbol, **data} for symbol, data in self.tokens.items()]
    
    def add_token(self, symbol: str, address: str, decimals: int = 18, name: str = None) -> bool:
        """Add a token to the token data."""
        symbol = symbol.upper()
        self.tokens[symbol] = {
            "address": address,
            "decimals": decimals,
            "name": name or symbol
        }
        return self.save_token_data()
    
    def remove_token(self, symbol: str) -> bool:
        """Remove a token from the token data."""
        symbol = symbol.upper()
        if symbol in self.tokens:
            del self.tokens[symbol]
            return self.save_token_data()
        return False
    
    def update_token(self, symbol: str, **kwargs) -> bool:
        """Update a token in the token data."""
        symbol = symbol.upper()
        if symbol in self.tokens:
            self.tokens[symbol].update(kwargs)
            return self.save_token_data()
        return False

# Create a singleton instance
token_data = TokenData()
