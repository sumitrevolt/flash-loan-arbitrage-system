"""
Execution Result Manager for the Flash Loan Arbitrage System.
Handles saving and loading execution results.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("ExecutionResultManager")

class ExecutionResultManager:
    """
    Manages execution results for the Flash Loan Arbitrage System.
    """
    
    def __init__(self, results_file_path="data/profits/profit_log.json"):
        """
        Initialize the execution result manager.
        
        Args:
            results_file_path (str): Path to the results file.
        """
        self.results_file_path = results_file_path
        self.results = self._load_results()
        
    def _load_results(self) -> Dict[str, Any]:
        """
        Load execution results from file.
        
        Returns:
            Dict[str, Any]: Execution results.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.results_file_path), exist_ok=True)
            
            # Load results if file exists
            if os.path.exists(self.results_file_path):
                with open(self.results_file_path, "r") as f:
                    results = json.load(f)
                    
                # Ensure 'trades' is a list
                if "trades" not in results:
                    results["trades"] = []
                elif not isinstance(results["trades"], list):
                    logger.warning(f"'trades' in {self.results_file_path} is not a list. Resetting to empty list.")
                    results["trades"] = []
                    
                return results
            else:
                # Create default results structure
                return {
                    "total_profit_usd": 0,
                    "total_trades": 0,
                    "successful_trades": 0,
                    "failed_trades": 0,
                    "trades": []
                }
        except Exception as e:
            logger.error(f"Error loading execution results: {e}")
            return {
                "total_profit_usd": 0,
                "total_trades": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "trades": []
            }
    
    def save_execution_result(self, result: Dict[str, Any]) -> bool:
        """
        Save an execution result.
        
        Args:
            result (Dict[str, Any]): Execution result.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Add timestamp
            result["timestamp"] = datetime.now().isoformat()
            
            # Update totals
            self.results["total_trades"] += 1
            if result.get("status") == "success":
                self.results["successful_trades"] += 1
                profit = result.get("profit_usd", 0)
                if isinstance(profit, (int, float)):
                    self.results["total_profit_usd"] += profit
            else:
                self.results["failed_trades"] += 1
            
            # Add to trades list
            self.results["trades"].append(result)
            
            # Save to file
            with open(self.results_file_path, "w") as f:
                json.dump(self.results, f, indent=2)
            
            logger.info(f"Saved execution result: {result}")
            return True
        except Exception as e:
            logger.error(f"Error saving execution result: {e}")
            return False
    
    def get_execution_results(self) -> Dict[str, Any]:
        """
        Get all execution results.
        
        Returns:
            Dict[str, Any]: Execution results.
        """
        return self.results
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent trades.
        
        Args:
            limit (int): Maximum number of trades to return.
            
        Returns:
            List[Dict[str, Any]]: Recent trades.
        """
        return self.results.get("trades", [])[-limit:]
    
    def get_profit_summary(self) -> Dict[str, Any]:
        """
        Get profit summary.
        
        Returns:
            Dict[str, Any]: Profit summary.
        """
        return {
            "total_profit_usd": self.results.get("total_profit_usd", 0),
            "total_trades": self.results.get("total_trades", 0),
            "successful_trades": self.results.get("successful_trades", 0),
            "failed_trades": self.results.get("failed_trades", 0)
        }

# Create a singleton instance
execution_result_manager = ExecutionResultManager()
