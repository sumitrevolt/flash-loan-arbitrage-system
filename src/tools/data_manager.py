"""
Data manager module for the Flash Loan Arbitrage System.
Provides centralized access to data storage and retrieval.
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Import from the package
from src.data import (
    DATA_ROOT, OPPORTUNITIES_DIR, EXECUTIONS_DIR, PROFITS_DIR,
    TOKENS_DIR, DEXES_DIR, GAS_DIR, RISK_DIR, TRADE_SIZES_DIR,
    TRANSACTIONS_DIR, TOKEN_DATA_PATH, DEX_ROUTER_DATA_PATH,
    PRICE_CACHE_PATH, PROFIT_LOG_PATH
)

logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages data storage and retrieval for the Flash Loan Arbitrage System.
    """
    
    def __init__(self):
        """Initialize the data manager."""
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        for directory in [
            OPPORTUNITIES_DIR, EXECUTIONS_DIR, PROFITS_DIR, TOKENS_DIR, 
            DEXES_DIR, GAS_DIR, RISK_DIR, TRADE_SIZES_DIR, TRANSACTIONS_DIR
        ]:
            os.makedirs(directory, exist_ok=True)
    
    def load_token_data(self) -> Dict[str, Any]:
        """Load token data from the token data file."""
        return self.load_json_data(TOKEN_DATA_PATH, default={})
    
    def load_dex_router_data(self) -> Dict[str, Any]:
        """Load DEX router data from the DEX router data file."""
        return self.load_json_data(DEX_ROUTER_DATA_PATH, default={})
    
    def load_price_cache(self) -> Dict[str, Any]:
        """Load price cache data from the price cache file."""
        return self.load_json_data(PRICE_CACHE_PATH, default={})
    
    def save_price_cache(self, data: Dict[str, Any]) -> bool:
        """Save price cache data to the price cache file."""
        return self.save_json_data(PRICE_CACHE_PATH, data)
    
    def load_profit_log(self) -> List[Dict[str, Any]]:
        """Load profit log data from the profit log file."""
        return self.load_json_data(PROFIT_LOG_PATH, default=[])
    
    def save_profit_log(self, data: List[Dict[str, Any]]) -> bool:
        """Save profit log data to the profit log file."""
        return self.save_json_data(PROFIT_LOG_PATH, data)
    
    def save_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Save an opportunity to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        token = opportunity.get("token", "unknown")
        filename = f"opportunity_{token}_{timestamp}.json"
        path = os.path.join(OPPORTUNITIES_DIR, filename)
        return self.save_json_data(path, opportunity)
    
    def save_execution(self, execution: Dict[str, Any]) -> bool:
        """Save an execution to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        token = execution.get("token", "unknown")
        filename = f"execution_{token}_{timestamp}.json"
        path = os.path.join(EXECUTIONS_DIR, filename)
        return self.save_json_data(path, execution)
    
    def record_profit(self, profit_data: Dict[str, Any]) -> bool:
        """Record a profit in the profit log."""
        profit_log = self.load_profit_log()
        profit_data["timestamp"] = time.time()
        profit_data["datetime"] = datetime.now().isoformat()
        profit_log.append(profit_data)
        return self.save_profit_log(profit_log)
    
    def load_json_data(self, path: Union[str, Path], default: Any = None) -> Any:
        """Load JSON data from a file."""
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
            return default if default is not None else {}
        except Exception as e:
            logger.error(f"Error loading JSON data from {path}: {e}")
            return default if default is not None else {}
    
    def save_json_data(self, path: Union[str, Path], data: Any) -> bool:
        """Save JSON data to a file."""
        try:
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON data to {path}: {e}")
            return False
    
    def get_latest_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the latest opportunities."""
        opportunities = []
        try:
            files = sorted(
                [f for f in os.listdir(OPPORTUNITIES_DIR) if f.endswith('.json')],
                key=lambda x: Any: Any: os.path.getmtime(os.path.join(OPPORTUNITIES_DIR, x)),
                reverse=True
            )
            
            for file in files[:limit]:
                path = os.path.join(OPPORTUNITIES_DIR, file)
                opportunity = self.load_json_data(path)
                if opportunity:
                    opportunities.append(opportunity)
        except Exception as e:
            logger.error(f"Error getting latest opportunities: {e}")
        
        return opportunities
    
    def get_latest_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the latest executions."""
        executions = []
        try:
            files = sorted(
                [f for f in os.listdir(EXECUTIONS_DIR) if f.endswith('.json')],
                key=lambda x: Any: Any: os.path.getmtime(os.path.join(EXECUTIONS_DIR, x)),
                reverse=True
            )
            
            for file in files[:limit]:
                path = os.path.join(EXECUTIONS_DIR, file)
                execution = self.load_json_data(path)
                if execution:
                    executions.append(execution)
        except Exception as e:
            logger.error(f"Error getting latest executions: {e}")
        
        return executions

# Create a singleton instance
data_manager = DataManager()
