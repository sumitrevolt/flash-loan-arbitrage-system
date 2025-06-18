"""
Performance metrics collector for flash loan arbitrage.

This module collects and analyzes performance metrics for the flash loan
arbitrage system to feed into the parameter tuner.
"""

import logging
import time
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import threading
import statistics

# Set up logging
logger = logging.getLogger(__name__)

class PerformanceMetricsCollector:
    def cleanup(self, timeout: float = 5.0):
        """Join the auto-save thread if it is alive (for explicit cleanup)."""
        if hasattr(self, 'auto_save_thread') and self.auto_save_thread.is_alive():
            self.logger.info("Joining auto_save_thread for cleanup...")
            self._stop_auto_save.set()  # Signal thread to stop
            self.auto_save_thread.join(timeout=timeout)
            if self.auto_save_thread.is_alive():
                self.logger.warning("auto_save_thread did not terminate within timeout.")
            else:
                self.logger.info("auto_save_thread terminated successfully.")
    """
    Collects and analyzes performance metrics for the flash loan arbitrage system.
    """

    def __init__(self, config_path: str = None, state_path: str = None):
        """
        Initialize the performance metrics collector.

        Args:
            config_path: Path to the performance metrics configuration file
            state_path: Path to the performance metrics state file
        """
        # Use environment variables if available, otherwise use default paths
        config_path = os.getenv('PERFORMANCE_METRICS_CONFIG_PATH', config_path or "config/performance_metrics_config.json")
        state_path = os.getenv('PERFORMANCE_METRICS_STATE_PATH', state_path or "data/performance_metrics_state.json")
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.state_path = state_path

        # Load configuration
        self.config = self._load_config()

        # Load state
        self.state = self._load_state()

        # Initialize state if needed
        if not self.state:
            self.state = {
                "transactions": [],
                "metrics": {
                    "success_rate": 0.0,
                    "average_profit_usd": 0.0,
                    "average_gas_cost_usd": 0.0,
                    "profit_per_gas": 0.0,
                    "average_execution_time_s": 0.0,
                    "retry_rate": 0.0
                },
                "token_metrics": {},
                "dex_metrics": {},
                "time_metrics": {
                    "hourly": {},
                    "daily": {}
                },
                "last_update": time.time()
            }

        # Initialize lock for thread safety
        self.lock = threading.Lock()

        # Start auto-save thread if enabled
        if self.config.get("auto_save_enabled", True):
            # SNYK-FIX: This daemon thread is intentionally not joined; it will not block program exit.
            self.auto_save_thread = threading.Thread(target=self._auto_save_thread, daemon=True)
            self.auto_save_thread.start()

    def _load_config(self) -> Dict[str, Any]:
        """Load performance metrics configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading performance metrics config: {e}")

        # Default configuration
        return {
            "max_transactions_to_keep": 1000,
            "auto_save_enabled": True,
            "auto_save_interval_seconds": 300,
            "metrics_update_interval_seconds": 60,
            "window_sizes": {
                "short_term": 20,
                "medium_term": 100,
                "long_term": 500
            },
            "token_specific_metrics_enabled": True,
            "dex_specific_metrics_enabled": True,
            "time_based_metrics_enabled": True
        }

    def _load_state(self) -> Dict[str, Any]:
        """Load performance metrics state."""
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading performance metrics state: {e}")

        return {}

    def _save_state(self):
        """Save performance metrics state."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)

            # Limit the number of transactions to keep
            max_transactions = self.config.get("max_transactions_to_keep", 1000)
            if len(self.state["transactions"]) > max_transactions:
                self.state["transactions"] = self.state["transactions"][-max_transactions:]

            with open(self.state_path, 'w') as f:
                json.dump(self.state, f, indent=2)

            self.logger.debug(f"Saved performance metrics state to {self.state_path}")
        except Exception as e:
            self.logger.error(f"Error saving performance metrics state: {e}")

    def _auto_save_thread(self):
        """Auto-save thread function."""
        interval = self.config.get("auto_save_interval_seconds", 300)
        while True:
            time.sleep(interval)
            with self.lock:
                self._save_state()

    def record_transaction(self, transaction_data: Dict[str, Any]):
        """
        Record a transaction and update metrics.

        Args:
            transaction_data: Transaction data
        """
        with self.lock:
            # Add timestamp if not present
            if "timestamp" not in transaction_data:
                transaction_data["timestamp"] = time.time()

            # Add to transactions list
            self.state["transactions"].append(transaction_data)

            # Check if it's time to update metrics
            now = time.time()
            last_update = self.state.get("last_update", 0)
            update_interval = self.config.get("metrics_update_interval_seconds", 60)

            if now - last_update >= update_interval:
                self._update_metrics()
                self.state["last_update"] = now

    def _update_metrics(self):
        """Update all metrics based on transaction history."""
        self.logger.debug("Updating performance metrics...")

        # Get transactions
        transactions = self.state.get("transactions", [])

        if not transactions:
            return

        # Update global metrics
        self._update_global_metrics(transactions)

        # Update token-specific metrics if enabled
        if self.config.get("token_specific_metrics_enabled", True):
            self._update_token_metrics(transactions)

        # Update DEX-specific metrics if enabled
        if self.config.get("dex_specific_metrics_enabled", True):
            self._update_dex_metrics(transactions)

        # Update time-based metrics if enabled
        if self.config.get("time_based_metrics_enabled", True):
            self._update_time_metrics(transactions)

    def _update_global_metrics(self, transactions: List[Dict[str, Any]]):
        """
        Update global metrics.

        Args:
            transactions: List of transactions
        """
        # Get window sizes
        window_sizes = self.config.get("window_sizes", {})
        short_term = window_sizes.get("short_term", 20)

        # Use the most recent transactions for short-term metrics
        recent_txs = transactions[-short_term:] if len(transactions) >= short_term else transactions

        # Calculate success rate
        total_txs = len(recent_txs)
        successful_txs = sum(1 for tx in recent_txs if tx.get("status") == "success")
        success_rate = successful_txs / total_txs if total_txs > 0 else 0

        # Calculate average profit
        profits = [tx.get("profit_usd", 0) for tx in recent_txs if tx.get("status") == "success"]
        avg_profit = statistics.mean(profits) if profits else 0

        # Calculate average gas cost
        gas_costs = [tx.get("gas_cost_usd", 0) for tx in recent_txs]
        avg_gas_cost = statistics.mean(gas_costs) if gas_costs else 0

        # Calculate profit per gas
        profit_per_gas = sum(profits) / sum(gas_costs) if sum(gas_costs) > 0 else 0

        # Calculate average execution time
        exec_times = [tx.get("execution_time_s", 0) for tx in recent_txs]
        avg_exec_time = statistics.mean(exec_times) if exec_times else 0

        # Calculate retry rate
        retry_counts = [tx.get("retry_count", 0) for tx in recent_txs]
        retry_rate = sum(1 for r in retry_counts if r > 0) / total_txs if total_txs > 0 else 0

        # Update metrics
        self.state["metrics"] = {
            "success_rate": success_rate,
            "average_profit_usd": avg_profit,
            "average_gas_cost_usd": avg_gas_cost,
            "profit_per_gas": profit_per_gas,
            "average_execution_time_s": avg_exec_time,
            "retry_rate": retry_rate,
            "total_transactions": total_txs,
            "successful_transactions": successful_txs
        }

        self.logger.debug(f"Updated global metrics: success_rate={success_rate:.2f}, avg_profit=${avg_profit:.2f}")

    def _update_token_metrics(self, transactions: List[Dict[str, Any]]):
        """
        Update token-specific metrics.

        Args:
            transactions: List of transactions
        """
        # Group transactions by token
        token_txs = {}
        for tx in transactions:
            token = tx.get("token")
            if token:
                if token not in token_txs:
                    token_txs[token] = []
                token_txs[token].append(tx)

        # Calculate metrics for each token
        for token, txs in token_txs.items():
            # Calculate success rate
            total_txs = len(txs)
            successful_txs = sum(1 for tx in txs if tx.get("status") == "success")
            success_rate = successful_txs / total_txs if total_txs > 0 else 0

            # Calculate average profit
            profits = [tx.get("profit_usd", 0) for tx in txs if tx.get("status") == "success"]
            avg_profit = statistics.mean(profits) if profits else 0

            # Calculate average gas cost
            gas_costs = [tx.get("gas_cost_usd", 0) for tx in txs]
            avg_gas_cost = statistics.mean(gas_costs) if gas_costs else 0

            # Calculate profit per gas
            profit_per_gas = sum(profits) / sum(gas_costs) if sum(gas_costs) > 0 else 0

            # Update token metrics
            self.state.setdefault("token_metrics", {})[token] = {
                "success_rate": success_rate,
                "average_profit_usd": avg_profit,
                "average_gas_cost_usd": avg_gas_cost,
                "profit_per_gas": profit_per_gas,
                "total_transactions": total_txs,
                "successful_transactions": successful_txs
            }

    def _update_dex_metrics(self, transactions: List[Dict[str, Any]]):
        """
        Update DEX-specific metrics.

        Args:
            transactions: List of transactions
        """
        # Group transactions by DEX pair
        dex_txs = {}
        for tx in transactions:
            buy_dex = tx.get("buy_dex")
            sell_dex = tx.get("sell_dex")
            if buy_dex and sell_dex:
                dex_pair = f"{buy_dex}-{sell_dex}"
                if dex_pair not in dex_txs:
                    dex_txs[dex_pair] = []
                dex_txs[dex_pair].append(tx)

        # Calculate metrics for each DEX pair
        for dex_pair, txs in dex_txs.items():
            # Calculate success rate
            total_txs = len(txs)
            successful_txs = sum(1 for tx in txs if tx.get("status") == "success")
            success_rate = successful_txs / total_txs if total_txs > 0 else 0

            # Calculate average profit
            profits = [tx.get("profit_usd", 0) for tx in txs if tx.get("status") == "success"]
            avg_profit = statistics.mean(profits) if profits else 0

            # Calculate average gas cost
            gas_costs = [tx.get("gas_cost_usd", 0) for tx in txs]
            avg_gas_cost = statistics.mean(gas_costs) if gas_costs else 0

            # Calculate profit per gas
            profit_per_gas = sum(profits) / sum(gas_costs) if sum(gas_costs) > 0 else 0

            # Update DEX metrics
            self.state.setdefault("dex_metrics", {})[dex_pair] = {
                "success_rate": success_rate,
                "average_profit_usd": avg_profit,
                "average_gas_cost_usd": avg_gas_cost,
                "profit_per_gas": profit_per_gas,
                "total_transactions": total_txs,
                "successful_transactions": successful_txs
            }

    def _update_time_metrics(self, transactions: List[Dict[str, Any]]):
        """
        Update time-based metrics.

        Args:
            transactions: List of transactions
        """
        # Group transactions by hour and day
        hourly_txs = {}
        daily_txs = {}

        for tx in transactions:
            timestamp = tx.get("timestamp", 0)
            dt = datetime.fromtimestamp(timestamp)

            # Get hour and day keys
            hour_key = dt.strftime("%Y-%m-%d %H:00")
            day_key = dt.strftime("%Y-%m-%d")

            # Add to hourly transactions
            if hour_key not in hourly_txs:
                hourly_txs[hour_key] = []
            hourly_txs[hour_key].append(tx)

            # Add to daily transactions
            if day_key not in daily_txs:
                daily_txs[day_key] = []
            daily_txs[day_key].append(tx)

        # Calculate hourly metrics
        hourly_metrics = {}
        for hour_key, txs in hourly_txs.items():
            # Calculate success rate
            total_txs = len(txs)
            successful_txs = sum(1 for tx in txs if tx.get("status") == "success")
            success_rate = successful_txs / total_txs if total_txs > 0 else 0

            # Calculate total profit
            total_profit = sum(tx.get("profit_usd", 0) for tx in txs if tx.get("status") == "success")

            # Calculate total gas cost
            total_gas_cost = sum(tx.get("gas_cost_usd", 0) for tx in txs)

            # Update hourly metrics
            hourly_metrics[hour_key] = {
                "success_rate": success_rate,
                "total_profit_usd": total_profit,
                "total_gas_cost_usd": total_gas_cost,
                "net_profit_usd": total_profit - total_gas_cost,
                "total_transactions": total_txs,
                "successful_transactions": successful_txs
            }

        # Calculate daily metrics
        daily_metrics = {}
        for day_key, txs in daily_txs.items():
            # Calculate success rate
            total_txs = len(txs)
            successful_txs = sum(1 for tx in txs if tx.get("status") == "success")
            success_rate = successful_txs / total_txs if total_txs > 0 else 0

            # Calculate total profit
            total_profit = sum(tx.get("profit_usd", 0) for tx in txs if tx.get("status") == "success")

            # Calculate total gas cost
            total_gas_cost = sum(tx.get("gas_cost_usd", 0) for tx in txs)

            # Update daily metrics
            daily_metrics[day_key] = {
                "success_rate": success_rate,
                "total_profit_usd": total_profit,
                "total_gas_cost_usd": total_gas_cost,
                "net_profit_usd": total_profit - total_gas_cost,
                "total_transactions": total_txs,
                "successful_transactions": successful_txs
            }

        # Update time metrics
        self.state["time_metrics"] = {
            "hourly": hourly_metrics,
            "daily": daily_metrics
        }

    def get_metrics_for_tuning(self, window_size: str = "short_term") -> Dict[str, Any]:
        """
        Get metrics for parameter tuning.

        Args:
            window_size: Window size to use ("short_term", "medium_term", or "long_term")

        Returns:
            Dict[str, Any]: Metrics for parameter tuning
        """
        with self.lock:
            # Get window size
            window_sizes = self.config.get("window_sizes", {})
            size = window_sizes.get(window_size, 20)

            # Get transactions
            transactions = self.state.get("transactions", [])

            if not transactions:
                return {
                    "success_rate": 0.0,
                    "average_profit_usd": 0.0,
                    "profit_per_gas": 0.0,
                    "status": "no_data"
                }

            # Use the most recent transactions for the specified window size
            recent_txs = transactions[-size:] if len(transactions) >= size else transactions

            # Calculate metrics
            total_txs = len(recent_txs)
            successful_txs = sum(1 for tx in recent_txs if tx.get("status") == "success")
            success_rate = successful_txs / total_txs if total_txs > 0 else 0

            profits = [tx.get("profit_usd", 0) for tx in recent_txs if tx.get("status") == "success"]
            avg_profit = statistics.mean(profits) if profits else 0

            gas_costs = [tx.get("gas_cost_usd", 0) for tx in recent_txs]
            avg_gas_cost = statistics.mean(gas_costs) if gas_costs else 0

            profit_per_gas = sum(profits) / sum(gas_costs) if sum(gas_costs) > 0 else 0

            return {
                "success_rate": success_rate,
                "average_profit_usd": avg_profit,
                "average_gas_cost_usd": avg_gas_cost,
                "profit_per_gas": profit_per_gas,
                "total_transactions": total_txs,
                "successful_transactions": successful_txs,
                "status": "success"
            }

    def get_token_metrics_for_tuning(self, token_symbol: str) -> Dict[str, Any]:
        """
        Get token-specific metrics for parameter tuning.

        Args:
            token_symbol: Symbol of the token

        Returns:
            Dict[str, Any]: Token-specific metrics for parameter tuning
        """
        with self.lock:
            if token_symbol in self.state.get("token_metrics", {}):
                return {
                    **self.state["token_metrics"][token_symbol],
                    "status": "success"
                }
            else:
                return {
                    "success_rate": 0.0,
                    "average_profit_usd": 0.0,
                    "profit_per_gas": 0.0,
                    "status": "no_data"
                }

    def get_dex_metrics_for_tuning(self, dex_name: str) -> Dict[str, Any]:
        """
        Get DEX-specific metrics for parameter tuning.

        Args:
            dex_name: Name of the DEX

        Returns:
            Dict[str, Any]: DEX-specific metrics for parameter tuning
        """
        with self.lock:
            # Look for any DEX pair that includes the specified DEX
            dex_metrics = {}

            for dex_pair, metrics in self.state.get("dex_metrics", {}).items():
                if dex_name in dex_pair:
                    # Combine metrics from all pairs involving this DEX
                    if not dex_metrics:
                        dex_metrics = metrics.copy()
                    else:
                        # Update counts
                        dex_metrics["total_transactions"] += metrics["total_transactions"]
                        dex_metrics["successful_transactions"] += metrics["successful_transactions"]

                        # Update weighted averages
                        weight = metrics["total_transactions"] / dex_metrics["total_transactions"]
                        dex_metrics["success_rate"] = (1 - weight) * dex_metrics["success_rate"] + weight * metrics["success_rate"]
                        dex_metrics["average_profit_usd"] = (1 - weight) * dex_metrics["average_profit_usd"] + weight * metrics["average_profit_usd"]
                        dex_metrics["average_gas_cost_usd"] = (1 - weight) * dex_metrics["average_gas_cost_usd"] + weight * metrics["average_gas_cost_usd"]
                        dex_metrics["profit_per_gas"] = (1 - weight) * dex_metrics["profit_per_gas"] + weight * metrics["profit_per_gas"]

            if dex_metrics:
                return {
                    **dex_metrics,
                    "status": "success"
                }
            else:
                return {
                    "success_rate": 0.0,
                    "average_profit_usd": 0.0,
                    "profit_per_gas": 0.0,
                    "status": "no_data"
                }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics.

        Returns:
            Dict[str, Any]: Performance summary
        """
        with self.lock:
            return {
                "global_metrics": self.state.get("metrics", {}),
                "token_metrics": self.state.get("token_metrics", {}),
                "dex_metrics": self.state.get("dex_metrics", {}),
                "total_transactions": len(self.state.get("transactions", [])),
                "last_update": self.state.get("last_update", 0)
            }
