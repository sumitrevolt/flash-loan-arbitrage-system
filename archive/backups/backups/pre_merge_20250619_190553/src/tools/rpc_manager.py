"""
RPC connection manager for blockchain operations
"""

import logging
from typing import List, Optional

from src.utils.web3_provider import Web3, get_web3_provider, WEB3_IMPORTED

logger = logging.getLogger(__name__)

class RPCManager:
    """Manage RPC connections and failover"""
    
    def __init__(self, rpc_urls: Optional[List[str]] = None):
        """
        Initialize the RPC Manager.
        
        Args:
            rpc_urls: Optional list of RPC URLs to use
        """
        self.rpc_urls = rpc_urls or [
            "https://polygon-rpc.com",
            "https://polygon.llamarpc.com",
            "https://polygon-bor.publicnode.com"
        ]
        self.current_provider = None
        self.current_index = 0
    
    def get_provider(self) -> Optional[Web3]:
        """Get a working Web3 provider"""
        if self.current_provider and self.current_provider.is_connected():
            return self.current_provider
            
        # Try to connect to a provider
        for i, url in enumerate(self.rpc_urls[self.current_index:], self.current_index):
            provider = get_web3_provider(url)
            if provider:
                self.current_provider = provider
                self.current_index = i
                return provider
        
        # If we've tried all, start from beginning
        self.current_index = 0
        return None
