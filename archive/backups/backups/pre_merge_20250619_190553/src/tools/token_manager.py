"""
Token manager for the Flash Loan Arbitrage System.
Handles token addresses and conversions.
"""
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3


import os
import json
import logging
# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)
logger = logging.getLogger("TokenManager")

class TokenManager:
    """
    Manages token addresses and conversions.
    """
    
    def __init__(self, web3: Web3, contract_manager=None):
        """
        Initialize the token manager.
        
        Args:
            web3 (Web3): Web3 provider instance
            contract_manager (ContractManager, optional): Contract manager instance
        """
        self.web3 = web3
        self.contract_manager = contract_manager
        self.token_addresses = {}
        self.token_symbols = {}
        self.token_decimals = {}
        self.dex_addresses = {}
        
        # Load token addresses
        self._load_token_addresses()
        
        # Load DEX addresses
        self._load_dex_addresses()
    
    def _load_token_addresses(self):
        """Load token addresses from configuration."""
        try:
            # Default token addresses for Polygon
            default_addresses = {
                "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
                "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
                "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                "LINK": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
                "AAVE": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
                "UNI": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",
                "SUSHI": "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a"
            }
            
            # Try to load from file
            token_path = os.path.join("config", "token_addresses.json")
            if os.path.exists(token_path):
                with open(token_path, "r") as f:
                    self.token_addresses = json.load(f)
            else:
                # Use default addresses
                self.token_addresses = default_addresses
                
                # Save to file
                os.makedirs("config", exist_ok=True)
                with open(token_path, "w") as f:
                    json.dump(default_addresses, f, indent=2)
            
            # Create reverse mapping (address -> symbol)
            for symbol, address in self.token_addresses.items():
                self.token_symbols[address.lower()] = symbol
            
            logger.info(f"Loaded {len(self.token_addresses)} token addresses")
        
        except Exception as e:
            logger.error(f"Failed to load token addresses: {e}")
            self.token_addresses = {}
    
    def _load_dex_addresses(self):
        """Load DEX addresses from configuration."""
        try:
            # Default DEX addresses for Polygon
            default_addresses = {
                "quickswap": {
                    "router": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
                    "factory": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
                    "fee": 3000  # 0.3%
                },
                "sushiswap": {
                    "router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
                    "factory": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
                    "fee": 3000  # 0.3%
                },
                "uniswap": {
                    "router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                    "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
                    "fee": 3000  # 0.3%
                }
            }
            
            # Try to load from file
            dex_path = os.path.join("config", "dex_addresses.json")
            if os.path.exists(dex_path):
                with open(dex_path, "r") as f:
                    self.dex_addresses = json.load(f)
            else:
                # Use default addresses
                self.dex_addresses = default_addresses
                
                # Save to file
                os.makedirs("config", exist_ok=True)
                with open(dex_path, "w") as f:
                    json.dump(default_addresses, f, indent=2)
            
            logger.info(f"Loaded {len(self.dex_addresses)} DEX addresses")
        
        except Exception as e:
            logger.error(f"Failed to load DEX addresses: {e}")
            self.dex_addresses = {}
    
    def get_token_address(self, symbol):
        """
        Get the address of a token by symbol.
        
        Args:
            symbol (str): Token symbol
            
        Returns:
            str: Token address
        """
        try:
            symbol = symbol.upper()
            address = self.token_addresses.get(symbol)
            if not address:
                logger.error(f"Token address not found for symbol: {symbol}")
                return None
            
            return self.web3.to_checksum_address(address)
        
        except Exception as e:
            logger.error(f"Failed to get token address: {e}")
            return None
    
    def get_token_symbol(self, address):
        """
        Get the symbol of a token by address.
        
        Args:
            address (str): Token address
            
        Returns:
            str: Token symbol
        """
        try:
            address = address.lower()
            symbol = self.token_symbols.get(address)
            if not symbol:
                logger.error(f"Token symbol not found for address: {address}")
                return None
            
            return symbol
        
        except Exception as e:
            logger.error(f"Failed to get token symbol: {e}")
            return None
    
    def get_token_decimals(self, symbol):
        """
        Get the decimals of a token by symbol.
        
        Args:
            symbol (str): Token symbol
            
        Returns:
            int: Token decimals
        """
        try:
            symbol = symbol.upper()
            
            # Check if decimals are cached
            if symbol in self.token_decimals:
                return self.token_decimals[symbol]
            
            # Get token address
            token_address = self.get_token_address(symbol)
            if not token_address:
                return 18  # Default to 18 decimals
            
            # Get decimals from contract
            if self.contract_manager:
                decimals = self.contract_manager.get_token_decimals(token_address)
                self.token_decimals[symbol] = decimals
                return decimals
            
            # Default decimals based on token
            default_decimals = {
                "WMATIC": 18,
                "WETH": 18,
                "WBTC": 8,
                "USDC": 6,
                "USDT": 6,
                "DAI": 18,
                "LINK": 18,
                "AAVE": 18,
                "UNI": 18,
                "SUSHI": 18
            }
            
            decimals = default_decimals.get(symbol, 18)
            self.token_decimals[symbol] = decimals
            return decimals
        
        except Exception as e:
            logger.error(f"Failed to get token decimals: {e}")
            return 18  # Default to 18 decimals
    
    def get_dex_router_address(self, dex_name):
        """
        Get the router address of a DEX by name.
        
        Args:
            dex_name (str): DEX name
            
        Returns:
            str: Router address
        """
        try:
            dex_name = dex_name.lower()
            if dex_name in self.dex_addresses:
                return self.web3.to_checksum_address(self.dex_addresses[dex_name]["router"])
            
            logger.error(f"DEX router address not found for name: {dex_name}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to get DEX router address: {e}")
            return None
    
    def get_dex_factory_address(self, dex_name):
        """
        Get the factory address of a DEX by name.
        
        Args:
            dex_name (str): DEX name
            
        Returns:
            str: Factory address
        """
        try:
            dex_name = dex_name.lower()
            if dex_name in self.dex_addresses:
                return self.web3.to_checksum_address(self.dex_addresses[dex_name]["factory"])
            
            logger.error(f"DEX factory address not found for name: {dex_name}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to get DEX factory address: {e}")
            return None
    
    def get_dex_fee(self, dex_name):
        """
        Get the fee of a DEX by name.
        
        Args:
            dex_name (str): DEX name
            
        Returns:
            int: Fee in basis points
        """
        try:
            dex_name = dex_name.lower()
            if dex_name in self.dex_addresses:
                return self.dex_addresses[dex_name]["fee"]
            
            logger.error(f"DEX fee not found for name: {dex_name}")
            return 3000  # Default to 0.3%
        
        except Exception as e:
            logger.error(f"Failed to get DEX fee: {e}")
            return 3000  # Default to 0.3%
    
    def convert_to_wei(self, amount, symbol):
        """
        Convert an amount to wei (smallest unit).
        
        Args:
            amount (float): Amount in token units
            symbol (str): Token symbol
            
        Returns:
            int: Amount in wei
        """
        try:
            decimals = self.get_token_decimals(symbol)
            return int(amount * (10 ** decimals))
        
        except Exception as e:
            logger.error(f"Failed to convert to wei: {e}")
            return 0
    
    def convert_from_wei(self, amount_wei, symbol):
        """
        Convert an amount from wei (smallest unit) to token units.
        
        Args:
            amount_wei (int): Amount in wei
            symbol (str): Token symbol
            
        Returns:
            float: Amount in token units
        """
        try:
            decimals = self.get_token_decimals(symbol)
            return amount_wei / (10 ** decimals)
        
        except Exception as e:
            logger.error(f"Failed to convert from wei: {e}")
            return 0
