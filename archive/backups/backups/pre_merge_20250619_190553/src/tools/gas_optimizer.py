"""
Gas Optimizer for Flash Loan Arbitrage System.
Optimizes gas usage for transactions on Polygon Mainnet.
"""
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3


import logging
import json
import os
import time
import asyncio
from typing import Dict, Any, Optional, Tuple
import aiohttp
# Enhanced Web3 import with error handling
try:
    # Import from central web3_provider
    from src.utils.web3_provider import Web3
    from web3.types import TxParams, Wei, ChecksumAddress
    # Import exceptions from central provider
    from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
    # Import middleware from centralized modules
    from src.utils.middleware_compat import apply_poa_middleware
    WEB3_IMPORTED = True
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import Web3: {e}")
    logger.error("Gas optimizer requires Web3 to function properly")
    WEB3_IMPORTED = False
    Web3 = None
    TxParams = dict
    Wei = int
    ChecksumAddress = str
    Web3Exception = Exception
    ContractLogicError = Exception
    TransactionNotFound = Exception

from src.blockchain.rpc_manager import get_rpc_manager

logger = logging.getLogger("GasOptimizer")

class GasOptimizer:
    """
    Optimizes gas usage for transactions on Polygon Mainnet.
    Fetches gas prices from multiple sources and recommends optimal gas settings.
    """
    
    def __init__(self, config_path='config/gas_optimizer_config.json'):
        """
        Initialize the GasOptimizer.
        
        Args:
            config_path (str): Path to the gas optimizer configuration file.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_path = config_path
        self.config = self._load_config()
        
        self.rpc_manager = get_rpc_manager()
        
        # Cache for gas prices
        self.gas_price_cache = {
            'timestamp': 0,
            'prices': None
        }
        self.cache_ttl = self.config.get('cache_ttl_seconds', 30)
        
        # Gas price sources
        self.gas_station_url = self.config.get('gas_station_url', 'https://gasstation-mainnet.matic.network/v2')
        self.polygonscan_api_key = self.config.get('polygonscan_api_key', '')
        self.polygonscan_url = 'https://api.polygonscan.com/api?module=gastracker&action=gasoracle'
        if self.polygonscan_api_key:
            self.polygonscan_url += f'&apikey={self.polygonscan_api_key}'
        
        # Default gas settings
        self.default_gas_price = self.config.get('default_gas_price_gwei', 50)
        self.default_gas_limit = self.config.get('default_gas_limit', 500000)
        self.default_max_priority_fee = self.config.get('default_max_priority_fee_gwei', 30)
        
        # Gas price multipliers for different speed settings
        self.speed_multipliers = {
            'fastest': self.config.get('fastest_multiplier', 1.5),
            'fast': self.config.get('fast_multiplier', 1.2),
            'standard': self.config.get('standard_multiplier', 1.0),
            'slow': self.config.get('slow_multiplier', 0.8)
        }
        
        self.logger.info("Gas Optimizer initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the gas optimizer configuration from the JSON file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Gas optimizer config file not found at {self.config_path}. Using defaults.")
                return {
                    'cache_ttl_seconds': 30,
                    'gas_station_url': 'https://gasstation-mainnet.matic.network/v2',
                    'default_gas_price_gwei': 50,
                    'default_gas_limit': 500000,
                    'default_max_priority_fee_gwei': 30,
                    'fastest_multiplier': 1.5,
                    'fast_multiplier': 1.2,
                    'standard_multiplier': 1.0,
                    'slow_multiplier': 0.8
                }
        except Exception as e:
            self.logger.error(f"Failed to load gas optimizer config: {e}")
            return {
                'cache_ttl_seconds': 30,
                'gas_station_url': 'https://gasstation-mainnet.matic.network/v2',
                'default_gas_price_gwei': 50,
                'default_gas_limit': 500000,
                'default_max_priority_fee_gwei': 30,
                'fastest_multiplier': 1.5,
                'fast_multiplier': 1.2,
                'standard_multiplier': 1.0,
                'slow_multiplier': 0.8
            }
    
    async def get_gas_price_from_rpc(self) -> Optional[int]:
        """
        Get the current gas price from the RPC endpoint.
        
        Returns:
            Optional[int]: Gas price in wei, or None if the request fails.
        """
        try:
            web3 = self.rpc_manager.get_web3()
            if not web3:
                self.logger.error("Failed to get Web3 instance for gas price check")
                return None
            
            gas_price = web3.eth.gas_price
            self.logger.debug(f"Gas price from RPC: {gas_price} wei ({gas_price / 1e9:.2f} Gwei)")
            return gas_price
        except Exception as e:
            self.logger.error(f"Failed to get gas price from RPC: {e}")
            return None
    
    async def get_gas_price_from_gas_station(self) -> Optional[Dict[str, Any]]:
        """
        Get gas prices from the Polygon Gas Station API.
        
        Returns:
            Optional[Dict[str, Any]]: Gas price data, or None if the request fails.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.gas_station_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.debug(f"Gas price from Gas Station: {data}")
                        return data
                    else:
                        self.logger.warning(f"Gas Station API returned status {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Failed to get gas price from Gas Station: {e}")
            return None
    
    async def get_gas_price_from_polygonscan(self) -> Optional[Dict[str, Any]]:
        """
        Get gas prices from the Polygonscan API.
        
        Returns:
            Optional[Dict[str, Any]]: Gas price data, or None if the request fails.
        """
        if not self.polygonscan_api_key:
            self.logger.debug("Skipping Polygonscan gas price check (no API key)")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.polygonscan_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == '1':
                            self.logger.debug(f"Gas price from Polygonscan: {data}")
                            return data.get('result', {})
                        else:
                            self.logger.warning(f"Polygonscan API error: {data.get('message')}")
                            return None
                    else:
                        self.logger.warning(f"Polygonscan API returned status {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Failed to get gas price from Polygonscan: {e}")
            return None
    
    async def get_optimal_gas_settings(self, speed='fast') -> Dict[str, int]:
        """
        Get optimal gas settings for a transaction.
        
        Args:
            speed (str): Speed setting ('fastest', 'fast', 'standard', 'slow').
            
        Returns:
            Dict[str, int]: Gas settings with 'gas_price', 'max_fee_per_gas', 'max_priority_fee_per_gas', and 'gas_limit'.
        """
        # Check if cache is valid
        current_time = time.time()
        if self.gas_price_cache['timestamp'] + self.cache_ttl > current_time and self.gas_price_cache['prices']:
            self.logger.debug("Using cached gas prices")
            gas_data = self.gas_price_cache['prices']
        else:
            # Fetch fresh gas prices
            gas_data = await self._fetch_gas_prices()
            self.gas_price_cache = {
                'timestamp': current_time,
                'prices': gas_data
            }
        
        # Get multiplier for the requested speed
        multiplier = self.speed_multipliers.get(speed, 1.0)
        
        # Calculate gas settings
        gas_price_gwei = gas_data.get('gas_price_gwei', self.default_gas_price)
        max_fee_gwei = gas_data.get('max_fee_gwei', gas_price_gwei)
        max_priority_fee_gwei = gas_data.get('max_priority_fee_gwei', self.default_max_priority_fee)
        
        # Apply speed multiplier
        gas_price_gwei = int(gas_price_gwei * multiplier)
        max_fee_gwei = int(max_fee_gwei * multiplier)
        max_priority_fee_gwei = int(max_priority_fee_gwei * multiplier)
        
        # Convert to wei
        gas_price = gas_price_gwei * 10**9
        max_fee = max_fee_gwei * 10**9
        max_priority_fee = max_priority_fee_gwei * 10**9
        
        return {
            'gas_price': gas_price,
            'max_fee_per_gas': max_fee,
            'max_priority_fee_per_gas': max_priority_fee,
            'gas_limit': self.default_gas_limit
        }
    
    async def _fetch_gas_prices(self) -> Dict[str, float]:
        """
        Fetch gas prices from all available sources and combine them.
        
        Returns:
            Dict[str, float]: Combined gas price data.
        """
        results = {}
        
        # Get gas price from RPC
        rpc_gas_price = await self.get_gas_price_from_rpc()
        if rpc_gas_price:
            results['rpc_gas_price_gwei'] = rpc_gas_price / 10**9
        
        # Get gas price from Gas Station
        gas_station_data = await self.get_gas_price_from_gas_station()
        if gas_station_data:
            try:
                results['gas_station_standard_gwei'] = gas_station_data.get('standard', {}).get('maxFee', 0)
                results['gas_station_fast_gwei'] = gas_station_data.get('fast', {}).get('maxFee', 0)
                results['gas_station_priority_fee_gwei'] = gas_station_data.get('standard', {}).get('maxPriorityFee', 0)
            except (KeyError, TypeError) as e:
                self.logger.warning(f"Error parsing Gas Station data: {e}")
        
        # Get gas price from Polygonscan
        polygonscan_data = await self.get_gas_price_from_polygonscan()
        if polygonscan_data:
            try:
                results['polygonscan_standard_gwei'] = float(polygonscan_data.get('ProposeGasPrice', 0))
                results['polygonscan_fast_gwei'] = float(polygonscan_data.get('FastGasPrice', 0))
                results['polygonscan_priority_fee_gwei'] = float(polygonscan_data.get('suggestBaseFee', 0))
            except (KeyError, TypeError, ValueError) as e:
                self.logger.warning(f"Error parsing Polygonscan data: {e}")
        
        # Combine results
        gas_price_gwei = self.default_gas_price
        max_fee_gwei = self.default_gas_price
        max_priority_fee_gwei = self.default_max_priority_fee
        
        # Prioritize Gas Station data if available
        if 'gas_station_fast_gwei' in results:
            gas_price_gwei = results['gas_station_fast_gwei']
            max_fee_gwei = results['gas_station_fast_gwei']
        elif 'polygonscan_fast_gwei' in results:
            gas_price_gwei = results['polygonscan_fast_gwei']
            max_fee_gwei = results['polygonscan_fast_gwei']
        elif 'rpc_gas_price_gwei' in results:
            gas_price_gwei = results['rpc_gas_price_gwei']
            max_fee_gwei = results['rpc_gas_price_gwei']
        
        # Set priority fee
        if 'gas_station_priority_fee_gwei' in results:
            max_priority_fee_gwei = results['gas_station_priority_fee_gwei']
        elif 'polygonscan_priority_fee_gwei' in results:
            max_priority_fee_gwei = results['polygonscan_priority_fee_gwei']
        
        return {
            'gas_price_gwei': gas_price_gwei,
            'max_fee_gwei': max_fee_gwei,
            'max_priority_fee_gwei': max_priority_fee_gwei
        }
    
    async def estimate_gas_for_transaction(self, tx_params: Dict[str, Any]) -> int:
        """
        Estimate gas for a transaction.
        
        Args:
            tx_params (Dict[str, Any]): Transaction parameters.
            
        Returns:
            int: Estimated gas limit.
        """
        try:
            web3 = self.rpc_manager.get_web3()
            if not web3:
                self.logger.error("Failed to get Web3 instance for gas estimation")
                return self.default_gas_limit
            
            gas_estimate = web3.eth.estimate_gas(tx_params)
            # Add 20% buffer
            gas_limit = int(gas_estimate * 1.2)
            self.logger.debug(f"Estimated gas: {gas_estimate}, with buffer: {gas_limit}")
            return gas_limit
        except Exception as e:
            self.logger.error(f"Failed to estimate gas: {e}")
            return self.default_gas_limit
    
    async def optimize_transaction(self, tx_params: Dict[str, Any], speed='fast') -> Dict[str, Any]:
        """
        Optimize a transaction with gas settings.
        
        Args:
            tx_params (Dict[str, Any]): Transaction parameters.
            speed (str): Speed setting ('fastest', 'fast', 'standard', 'slow').
            
        Returns:
            Dict[str, Any]: Optimized transaction parameters.
        """
        # Get optimal gas settings
        gas_settings = await self.get_optimal_gas_settings(speed)
        
        # Estimate gas if not provided
        if 'gas' not in tx_params:
            try:
                gas_limit = await self.estimate_gas_for_transaction(tx_params)
                gas_settings['gas_limit'] = gas_limit
            except Exception as e:
                self.logger.error(f"Failed to estimate gas: {e}")
        
        # Update transaction parameters
        optimized_tx = tx_params.copy()
        
        # Use EIP-1559 if supported
        web3 = self.rpc_manager.get_web3()
        if web3 and hasattr(web3.eth, 'fee_history'):
            self.logger.debug("Using EIP-1559 gas settings")
            optimized_tx['maxFeePerGas'] = gas_settings['max_fee_per_gas']
            optimized_tx['maxPriorityFeePerGas'] = gas_settings['max_priority_fee_per_gas']
            # Remove gasPrice if present
            if 'gasPrice' in optimized_tx:
                del optimized_tx['gasPrice']
        else:
            self.logger.debug("Using legacy gas price")
            optimized_tx['gasPrice'] = gas_settings['gas_price']
        
        # Set gas limit
        optimized_tx['gas'] = gas_settings['gas_limit']
        
        self.logger.info(f"Optimized transaction with {speed} gas settings: {gas_settings}")
        return optimized_tx
    
    async def initialize(self):
        """Initialize the gas optimizer."""
        self.logger.info("Initializing gas optimizer...")
        
        # Test connection to gas price sources
        try:
            gas_station_data = await self.get_gas_price_from_gas_station()
            if gas_station_data:
                self.logger.info("Successfully connected to Polygon Gas Station")
            else:
                self.logger.warning("Failed to connect to Polygon Gas Station")
            
            polygonscan_data = await self.get_gas_price_from_polygonscan()
            if polygonscan_data:
                self.logger.info("Successfully connected to Polygonscan Gas Tracker")
            else:
                self.logger.warning("Failed to connect to Polygonscan Gas Tracker")
            
            rpc_gas_price = await self.get_gas_price_from_rpc()
            if rpc_gas_price:
                self.logger.info(f"Successfully got gas price from RPC: {rpc_gas_price / 1e9:.2f} Gwei")
            else:
                self.logger.warning("Failed to get gas price from RPC")
            
            # Fetch initial gas prices
            gas_data = await self._fetch_gas_prices()
            self.gas_price_cache = {
                'timestamp': time.time(),
                'prices': gas_data
            }
            
            self.logger.info(f"Initial gas prices: {gas_data}")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing gas optimizer: {e}")
            return False


# Create a singleton instance
gas_optimizer = GasOptimizer()
