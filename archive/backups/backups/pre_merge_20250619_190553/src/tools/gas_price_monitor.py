"""
Gas price monitor for blockchain operations
"""
import logging
from typing import Optional

from src.utils.web3_provider import Web3, WEB3_IMPORTED, requires_web3

logger = logging.getLogger(__name__)


class GasPriceMonitor:
    """Monitor and manage gas prices for transactions"""
    
    def __init__(self, web3: Optional[Web3] = None):
        self.web3 = web3
        self._last_gas_price = None
        self._last_update = None
    
    @requires_web3
    def get_current_gas_price(self) -> Optional[int]:
        """Get current gas price from the network"""
        if not self.web3:
            return None
            
        try:
            return self.web3.eth.gas_price
        except Exception as e:
            logger.error(f"Failed to get gas price: {e}")
            return self._last_gas_price
    
    @requires_web3
    def get_recommended_gas_price(self, speed: str = "standard") -> Optional[int]:
        """Get recommended gas price based on speed preference"""
        base_price = self.get_current_gas_price()
        if not base_price:
            return None
            
        multipliers = {
            "slow": 0.9,
            "standard": 1.0,
            "fast": 1.2,
            "instant": 1.5
        }
        
        multiplier = multipliers.get(speed, 1.0)
        return int(base_price * multiplier)
