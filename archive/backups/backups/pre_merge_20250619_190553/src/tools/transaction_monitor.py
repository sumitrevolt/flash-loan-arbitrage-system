"""
Transaction monitor for flash loan arbitrage.

This module provides functions to monitor transactions and collect
statistics on success rates, gas usage, and profitability.
"""

import logging
import time
import json
import os
import datetime
import atexit
from typing import Dict, Any, Optional
from collections import deque
import threading

logger = logging.getLogger(__name__)

class ThreadLifecycle:
    """Thread lifecycle manager with proper join handling."""
    
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        
    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
        
    def start(self, target, name=None):
        """Start a new thread with proper lifecycle management."""
        if self.is_running:
            logger.warning(f"Thread {name or 'unknown'} is already running")
            return False
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=target, name=name)
        self._thread.start()
        # Initial non-blocking join for proper lifecycle tracking
        self._thread.join(timeout=0)
        return True
        
    def stop(self):
        """Stop the thread with proper cleanup."""
        if hasattr(self, '_stop_event'):
            self._stop_event.set()
        
        if hasattr(self, '_thread') and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            
        # Cleanup any remaining resources
        self._cleanup_resources()
    
    def _cleanup_resources(self):
        """Clean up any allocated resources."""
        # Clear any pending tasks
        if hasattr(self, '_task_queue'):
            while not self._task_queue.empty():
                try:
                    self._task_queue.get_nowait()
                except:
                    pass

class TransactionMonitor:
    """Monitors transactions and collects statistics."""

    def __init__(self, config_path: str = "config/transaction_monitor_config.json", 
                 state_path: str = "data/transaction_monitor_state.json"):
        """Initialize the transaction monitor."""
        self.logger = logger
        self.config_path = config_path
        self.state_path = state_path

        # Thread management
        self._auto_save = ThreadLifecycle()
        self.lock = threading.Lock()

        # Load configuration and state
        self.config = self._load_config()
        self.state = self._load_state() or self._create_initial_state()
        self.transaction_queue = deque(maxlen=self.config.get("max_queue_size", 100))

        # Start auto-save if enabled
        if self.config.get("auto_save_enabled", True):
            self._start_auto_save()
            
        # Register cleanup
        atexit.register(self.cleanup)

    def _create_initial_state(self) -> Dict[str, Any]:
        """Create initial monitor state."""
        return {
            "transactions": [],
            "stats": {
                "total_transactions": 0,
                "successful_transactions": 0,
                "failed_transactions": 0,
                "total_profit_usd": 0.0,
                "total_gas_cost_usd": 0.0,
                "net_profit_usd": 0.0,
                "average_gas_cost_usd": 0.0,
                "average_profit_usd": 0.0,
                "success_rate": 0.0
            },
            "token_stats": {},
            "dex_stats": {},
            "hourly_stats": {},
            "daily_stats": {}
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load monitor configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading monitor config: {e}")

        return {
            "max_transactions_to_keep": 1000,
            "auto_save_enabled": True,
            "auto_save_interval_seconds": 300,
            "max_queue_size": 100,
            "alert_thresholds": {
                "low_success_rate": 0.7,
                "critical_success_rate": 0.5,
                "high_gas_cost": 10.0,
                "low_profit_margin": 0.2
            }
        }

    def _load_state(self) -> Optional[Dict[str, Any]]:
        """Load monitor state."""
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading monitor state: {e}")
        return None

    def _start_auto_save(self) -> None:
        """Start the auto-save thread with proper thread management."""
        if self._auto_save.start(
            target=self._auto_save_loop,
            name="TransactionMonitorAutoSave"
        ):
            self.logger.info("Auto-save thread started")

    def _auto_save_loop(self) -> None:
        """Auto-save loop with proper shutdown handling."""
        interval = self.config.get("auto_save_interval_seconds", 300)
        
        while not self._auto_save.should_stop():
            try:
                if self._auto_save.should_stop():
                    break
                    
                with self.lock:
                    self._save_state()
                    
                # Use event wait for interruptible sleep
                self._auto_save._stop_event.wait(timeout=interval)
            except Exception as e:
                self.logger.error(f"Error in auto-save loop: {e}")
                if self._auto_save.should_stop():
                    break
                time.sleep(10)  # Shorter retry interval on error

    def _save_state(self) -> None:
        """Save monitor state with proper synchronization."""
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)

            with self.lock:
                # Trim transactions if needed
                max_transactions = self.config.get("max_transactions_to_keep", 1000)
                if len(self.state["transactions"]) > max_transactions:
                    self.state["transactions"] = self.state["transactions"][-max_transactions:]

                # Save state
                with open(self.state_path, 'w') as f:
                    json.dump(self.state, f, indent=2)

            self.logger.debug(f"Saved monitor state to {self.state_path}")
        except Exception as e:
            self.logger.error(f"Error saving monitor state: {e}")

    def cleanup(self) -> None:
        """Clean up resources with proper thread shutdown."""
        self.logger.info("Cleaning up transaction monitor...")
        
        # Stop auto-save thread
        self._auto_save.stop()
        
        # Save state one final time
        with self.lock:
            self._save_state()
            
        self.logger.info("Transaction monitor cleanup complete")

    def record_transaction(self, transaction_data: Dict[str, Any]) -> None:
        """Record a transaction and update statistics."""
        with self.lock:
            if "timestamp" not in transaction_data:
                transaction_data["timestamp"] = time.time()

            self.state["transactions"].append(transaction_data)
            self.transaction_queue.append(transaction_data)

            self._update_global_stats(transaction_data)
            if "token" in transaction_data:
                self._update_token_stats(transaction_data)
            if "buy_dex" in transaction_data and "sell_dex" in transaction_data:
                self._update_dex_stats(transaction_data)
            self._update_time_stats(transaction_data)

    def _update_global_stats(self, transaction_data: Dict[str, Any]) -> None:
        """Update global statistics."""
        stats = self.state["stats"]
        stats["total_transactions"] += 1

        if transaction_data.get("status") == "success":
            stats["successful_transactions"] += 1
            stats["success_rate"] = stats["successful_transactions"] / stats["total_transactions"]
        else:
            stats["failed_transactions"] += 1

        profit_usd = transaction_data.get("profit_usd", 0.0)
        gas_cost_usd = transaction_data.get("gas_cost_usd", 0.0)

        stats["total_profit_usd"] += profit_usd
        stats["total_gas_cost_usd"] += gas_cost_usd
        stats["net_profit_usd"] = stats["total_profit_usd"] - stats["total_gas_cost_usd"]

        if stats["total_transactions"] > 0:
            stats["average_gas_cost_usd"] = stats["total_gas_cost_usd"] / stats["total_transactions"]
        if stats["successful_transactions"] > 0:
            stats["average_profit_usd"] = stats["total_profit_usd"] / stats["successful_transactions"]

    def _update_token_stats(self, transaction_data: Dict[str, Any]) -> None:
        """Update token-specific statistics."""
        token = transaction_data.get("token")
        if not token:
            return

        if token not in self.state["token_stats"]:
            self.state["token_stats"][token] = {
                "total_transactions": 0,
                "successful_transactions": 0,
                "failed_transactions": 0,
                "total_profit_usd": 0.0,
                "total_gas_cost_usd": 0.0,
                "net_profit_usd": 0.0,
                "average_gas_cost_usd": 0.0,
                "average_profit_usd": 0.0,
                "success_rate": 0.0
            }

        stats = self.state["token_stats"][token]
        stats["total_transactions"] += 1

        if transaction_data.get("status") == "success":
            stats["successful_transactions"] += 1
            stats["success_rate"] = stats["successful_transactions"] / stats["total_transactions"]
        else:
            stats["failed_transactions"] += 1

        profit_usd = transaction_data.get("profit_usd", 0.0)
        gas_cost_usd = transaction_data.get("gas_cost_usd", 0.0)

        stats["total_profit_usd"] += profit_usd
        stats["total_gas_cost_usd"] += gas_cost_usd
        stats["net_profit_usd"] = stats["total_profit_usd"] - stats["total_gas_cost_usd"]

        if stats["total_transactions"] > 0:
            stats["average_gas_cost_usd"] = stats["total_gas_cost_usd"] / stats["total_transactions"]
        if stats["successful_transactions"] > 0:
            stats["average_profit_usd"] = stats["total_profit_usd"] / stats["successful_transactions"]

    def _update_dex_stats(self, transaction_data: Dict[str, Any]) -> None:
        """Update DEX-specific statistics."""
        buy_dex = transaction_data.get("buy_dex")
        sell_dex = transaction_data.get("sell_dex")
        if not buy_dex or not sell_dex:
            return

        dex_pair = f"{buy_dex}-{sell_dex}"
        if dex_pair not in self.state["dex_stats"]:
            self.state["dex_stats"][dex_pair] = {
                "total_transactions": 0,
                "successful_transactions": 0,
                "failed_transactions": 0,
                "total_profit_usd": 0.0,
                "total_gas_cost_usd": 0.0,
                "net_profit_usd": 0.0,
                "average_gas_cost_usd": 0.0,
                "average_profit_usd": 0.0,
                "success_rate": 0.0
            }

        stats = self.state["dex_stats"][dex_pair]
        stats["total_transactions"] += 1

        if transaction_data.get("status") == "success":
            stats["successful_transactions"] += 1
            stats["success_rate"] = stats["successful_transactions"] / stats["total_transactions"]
        else:
            stats["failed_transactions"] += 1

        profit_usd = transaction_data.get("profit_usd", 0.0)
        gas_cost_usd = transaction_data.get("gas_cost_usd", 0.0)

        stats["total_profit_usd"] += profit_usd
        stats["total_gas_cost_usd"] += gas_cost_usd
        stats["net_profit_usd"] = stats["total_profit_usd"] - stats["total_gas_cost_usd"]

        if stats["total_transactions"] > 0:
            stats["average_gas_cost_usd"] = stats["total_gas_cost_usd"] / stats["total_transactions"]
        if stats["successful_transactions"] > 0:
            stats["average_profit_usd"] = stats["total_profit_usd"] / stats["successful_transactions"]

    def _update_time_stats(self, transaction_data: Dict[str, Any]) -> None:
        """Update time-based statistics."""
        timestamp = transaction_data.get("timestamp", time.time())
        dt = datetime.datetime.fromtimestamp(timestamp)
        
        # Get time keys
        hour_key = dt.strftime("%Y-%m-%d %H:00")
        day_key = dt.strftime("%Y-%m-%d")

        # Update hourly stats
        if hour_key not in self.state["hourly_stats"]:
            self.state["hourly_stats"][hour_key] = {
                "total_transactions": 0,
                "successful_transactions": 0,
                "failed_transactions": 0,
                "total_profit_usd": 0.0,
                "total_gas_cost_usd": 0.0,
                "net_profit_usd": 0.0
            }

        # Update daily stats
        if day_key not in self.state["daily_stats"]:
            self.state["daily_stats"][day_key] = {
                "total_transactions": 0,
                "successful_transactions": 0,
                "failed_transactions": 0,
                "total_profit_usd": 0.0,
                "total_gas_cost_usd": 0.0,
                "net_profit_usd": 0.0
            }

        # Update metrics
        for stats in [self.state["hourly_stats"][hour_key], 
                     self.state["daily_stats"][day_key]]:
            stats["total_transactions"] += 1
            
            if transaction_data.get("status") == "success":
                stats["successful_transactions"] += 1
            else:
                stats["failed_transactions"] += 1

            profit_usd = transaction_data.get("profit_usd", 0.0)
            gas_cost_usd = transaction_data.get("gas_cost_usd", 0.0)

            stats["total_profit_usd"] += profit_usd
            stats["total_gas_cost_usd"] += gas_cost_usd
            stats["net_profit_usd"] = stats["total_profit_usd"] - stats["total_gas_cost_usd"]
