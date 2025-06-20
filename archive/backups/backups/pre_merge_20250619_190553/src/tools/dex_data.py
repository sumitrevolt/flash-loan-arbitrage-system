"""
DEX data module for the Flash Loan Arbitrage System.
Provides access to DEX data and utilities.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from src.data import DEX_ROUTER_DATA_PATH, load_json_data, save_json_data

logger = logging.getLogger(__name__)

class DexData:
    """
    Manages DEX data for the Flash Loan Arbitrage System.
    """
    
    def __init__(self):
        """Initialize the DEX data manager."""
        self.dexes = self.load_dex_data()
    
    def load_dex_data(self) -> Dict[str, Any]:
        """Load DEX data from the DEX router data file."""
        return load_json_data(DEX_ROUTER_DATA_PATH, default={})
    
    def save_dex_data(self) -> bool:
        """Save DEX data to the DEX router data file."""
        return save_json_data(DEX_ROUTER_DATA_PATH, self.dexes)
    
    def get_dex_router_address(self, dex_name: str) -> Optional[str]:
        """Get the router address of a DEX by its name."""
        dex = self.dexes.get(dex_name.lower())
        if dex:
            return dex.get("router_address")
        return None
    
    def get_dex_factory_address(self, dex_name: str) -> Optional[str]:
        """Get the factory address of a DEX by its name."""
        dex = self.dexes.get(dex_name.lower())
        if dex:
            return dex.get("factory_address")
        return None
    
    def get_dex_version(self, dex_name: str) -> Optional[str]:
        """Get the version of a DEX by its name."""
        dex = self.dexes.get(dex_name.lower())
        if dex:
            return dex.get("version")
        return None
    
    def get_all_dexes(self) -> List[Dict[str, Any]]:
        """Get all DEXes."""
        return [{"name": name, **data} for name, data in self.dexes.items()]
    
    def add_dex(self, name: str, router_address: str, factory_address: str, version: str) -> bool:
        """Add a DEX to the DEX data."""
        name = name.lower()
        self.dexes[name] = {
            "name": name.capitalize(),
            "router_address": router_address,
            "factory_address": factory_address,
            "version": version
        }
        return self.save_dex_data()
    
    def remove_dex(self, name: str) -> bool:
        """Remove a DEX from the DEX data."""
        name = name.lower()
        if name in self.dexes:
            del self.dexes[name]
            return self.save_dex_data()
        return False
    
    def update_dex(self, name: str, **kwargs) -> bool:
        """Update a DEX in the DEX data."""
        name = name.lower()
        if name in self.dexes:
            self.dexes[name].update(kwargs)
            return self.save_dex_data()
        return False

# Create a singleton instance
dex_data = DexData()
