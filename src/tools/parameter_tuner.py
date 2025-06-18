"""
Parameter tuner for flash loan arbitrage.

This module automatically adjusts system parameters based on performance metrics
to optimize the flash loan arbitrage system over time.
"""

import logging
import time
import json
import os
import math
import statistics
import secrets  # Use secrets module for cryptographically secure random numbers
from typing import Dict, Any, Optional, List, Tuple, Union

from datetime import datetime, timedelta
import threading

# Set up logging
logger = logging.getLogger(__name__)

class ParameterTuner:
    """
    Automatically tunes system parameters based on performance metrics.
    """

    def __init__(
        self,
        config_path: str = "config/parameter_tuner_config.json",
        state_path: str = "data/parameter_tuner_state.json",
        auto_save: bool = True
    ):
        """
        Initialize the parameter tuner.

        Args:
            config_path: Path to the parameter tuner configuration file
            state_path: Path to the parameter tuner state file
            auto_save: Whether to automatically save state periodically
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.state_path = state_path
        self.auto_save = auto_save

        # Load configuration
        self.config = self._load_config()

        # Load state
        self.state = self._load_state()

        # Initialize state if needed
        if not self.state:
            self.state = {
                "last_tuning": time.time(),
                "tuning_count": 0,
                "performance_history": [],
                "parameter_history": [],
                "current_parameters": self._get_default_parameters(),
                "best_parameters": None,
                "best_performance": None,
                "exploration_rate": self.config.get("initial_exploration_rate", 0.3),
                "token_specific_parameters": {},
                "dex_specific_parameters": {}
            }
            self._save_state()

        # Initialize lock for thread safety
        self.lock = threading.Lock()

        # Start auto-save thread if enabled
        if self.auto_save:
            # SNYK-FIX: This daemon thread is intentionally not joined. It will not block program exit and is safe by design.
            # deepcode ignore MissingAPI: <please specify a reason of ignoring this>
            # SNYK-SUPPRESS: THREAD-JOIN - Daemon thread does not require join; suppression is intentional and documented.
            # deepcode ignore MissingAPI: <please specify a reason of ignoring this>
            self.auto_save_thread = threading.Thread(target=self._auto_save_thread, daemon=True)  # noqa  # pylint: disable=not-joined-thread
            self.auto_save_thread.start()

    def _load_config(self) -> Dict[str, Any]:
        """Load parameter tuner configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading parameter tuner config: {e}")

        # Default configuration
        return {
            "tuning_interval_seconds": 3600,  # 1 hour
            "performance_window_size": 100,
            "min_samples_for_tuning": 20,
            "exploration_decay_rate": 0.95,
            "min_exploration_rate": 0.05,
            "max_exploration_rate": 0.5,
            "initial_exploration_rate": 0.3,
            "learning_rate": 0.1,
            "performance_metrics": {
                "success_rate_weight": 0.4,
                "profit_weight": 0.4,
                "gas_efficiency_weight": 0.2
            },
            "tunable_parameters": {
                "slippage": {
                    "base_slippage": {
                        "min": 0.1,
                        "max": 1.0,
                        "step": 0.1,
                        "default": 0.5
                    },
                    "max_slippage": {
                        "min": 1.0,
                        "max": 5.0,
                        "step": 0.5,
                        "default": 3.0
                    },
                    "volatility_factor": {
                        "min": 0.1,
                        "max": 1.0,
                        "step": 0.1,
                        "default": 0.5
                    }
                },
                "circuit_breaker": {
                    "max_consecutive_failures": {
                        "min": 2,
                        "max": 10,
                        "step": 1,
                        "default": 3
                    },
                    "cooldown_period_seconds": {
                        "min": 60,
                        "max": 1800,
                        "step": 60,
                        "default": 300
                    }
                },
                "gas": {
                    "gas_price_multipliers.standard": {
                        "min": 0.8,
                        "max": 1.2,
                        "step": 0.05,
                        "default": 1.0
                    },
                    "gas_price_multipliers.fast": {
                        "min": 1.0,
                        "max": 1.5,
                        "step": 0.05,
                        "default": 1.2
                    }
                },
                "retry": {
                    "max_retries": {
                        "min": 1,
                        "max": 5,
                        "step": 1,
                        "default": 3
                    },
                    "retry_delay": {
                        "min": 1,
                        "max": 30,
                        "step": 1,
                        "default": 5
                    }
                },
                "trade": {
                    "min_profit_threshold_usd": {
                        "min": 1.0,
                        "max": 10.0,
                        "step": 0.5,
                        "default": 3.0
                    },
                    "min_profit_percentage": {
                        "min": 0.1,
                        "max": 1.0,
                        "step": 0.1,
                        "default": 0.5
                    }
                }
            },
            "token_specific_tuning": {
                "enabled": True,
                "min_samples_per_token": 10
            },
            "dex_specific_tuning": {
                "enabled": True,
                "min_samples_per_dex": 10
            }
        }

    def _load_state(self) -> Dict[str, Any]:
        """Load parameter tuner state."""
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading parameter tuner state: {e}")

        return {}

    def _save_state(self):
        """Save parameter tuner state."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)

            with open(self.state_path, 'w') as f:
                json.dump(self.state, f, indent=2)

            self.logger.debug(f"Saved parameter tuner state to {self.state_path}")
        except Exception as e:
            self.logger.error(f"Error saving parameter tuner state: {e}")

    def _auto_save_thread(self):
        """Auto-save thread function."""
        interval = self.config.get("auto_save_interval_seconds", 300)
        while True:
            time.sleep(interval)
            with self.lock:
                self._save_state()

    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters from configuration."""
        default_params = {}

        # Extract default values from tunable parameters
        for category, params in self.config.get("tunable_parameters", {}).items():
            for param_name, param_config in params.items():
                param_key = f"{category}.{param_name}"
                default_params[param_key] = param_config.get("default")

        return default_params

    def get_parameters(self, token_symbol: Optional[str] = None, dex_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current parameters, optionally for a specific token or DEX.

        Args:
            token_symbol: Symbol of the token
            dex_name: Name of the DEX

        Returns:
            Dict[str, Any]: Current parameters
        """
        with self.lock:
            # Start with global parameters
            params = self.state["current_parameters"].copy()

            # Apply token-specific parameters if available
            if token_symbol and self.config.get("token_specific_tuning", {}).get("enabled", False):
                if token_symbol in self.state.get("token_specific_parameters", {}):
                    token_params = self.state["token_specific_parameters"][token_symbol]
                    params.update(token_params)

            # Apply DEX-specific parameters if available
            if dex_name and self.config.get("dex_specific_tuning", {}).get("enabled", False):
                if dex_name in self.state.get("dex_specific_parameters", {}):
                    dex_params = self.state["dex_specific_parameters"][dex_name]
                    params.update(dex_params)

            return params

    def record_performance(self, performance_metrics: Dict[str, Any], token_symbol: Optional[str] = None, dex_name: Optional[str] = None):
        """
        Record performance metrics for parameter tuning.

        Args:
            performance_metrics: Performance metrics
            token_symbol: Symbol of the token
            dex_name: Name of the DEX
        """
        with self.lock:
            # Add timestamp
            metrics = performance_metrics.copy()
            metrics["timestamp"] = time.time()

            # Add token and DEX info if available
            if token_symbol:
                metrics["token"] = token_symbol
            if dex_name:
                metrics["dex"] = dex_name

            # Add current parameters
            metrics["parameters"] = self.state["current_parameters"].copy()

            # Add to performance history
            self.state["performance_history"].append(metrics)

            # Limit history size
            max_history = self.config.get("performance_window_size", 100)
            if len(self.state["performance_history"]) > max_history:
                self.state["performance_history"] = self.state["performance_history"][-max_history:]

            # Check if it's time to tune parameters
            self._check_tuning_time()

    def _check_tuning_time(self):
        """Check if it's time to tune parameters and do so if needed."""
        now = time.time()
        last_tuning = self.state.get("last_tuning", 0)
        tuning_interval = self.config.get("tuning_interval_seconds", 3600)

        if now - last_tuning >= tuning_interval:
            # Check if we have enough samples
            min_samples = self.config.get("min_samples_for_tuning", 20)
            if len(self.state["performance_history"]) >= min_samples:
                self._tune_parameters()

                # Update last tuning time
                self.state["last_tuning"] = now
                self.state["tuning_count"] += 1

                # Save state after tuning
                self._save_state()

    def _tune_parameters(self):
        """Tune parameters based on performance history."""
        self.logger.info("Tuning parameters based on performance history...")

        # Calculate current performance score
        current_score = self._calculate_performance_score(self.state["performance_history"])
        self.logger.info(f"Current performance score: {current_score:.4f}")

        # Update best parameters if current performance is better
        if self.state.get("best_performance") is None or current_score > self.state["best_performance"]:
            self.state["best_parameters"] = self.state["current_parameters"].copy()
            self.state["best_performance"] = current_score
            self.logger.info(f"New best performance: {current_score:.4f}")

        # Decide whether to explore or exploit
        if secrets.randbelow(100) < int(self.state["exploration_rate"] * 100):
            # Exploration: try new parameter values
            self._explore_parameters()
        else:
            # Exploitation: refine current parameters
            self._exploit_parameters()

        # Decay exploration rate
        decay_rate = self.config.get("exploration_decay_rate", 0.95)
        min_rate = self.config.get("min_exploration_rate", 0.05)
        self.state["exploration_rate"] = max(min_rate, self.state["exploration_rate"] * decay_rate)

        # Save parameter history
        self.state["parameter_history"].append({
            "parameters": self.state["current_parameters"].copy(),
            "performance": current_score,
            "timestamp": time.time(),
            "exploration_rate": self.state["exploration_rate"]
        })

        # Tune token-specific parameters if enabled
        if self.config.get("token_specific_tuning", {}).get("enabled", False):
            self._tune_token_specific_parameters()

        # Tune DEX-specific parameters if enabled
        if self.config.get("dex_specific_tuning", {}).get("enabled", False):
            self._tune_dex_specific_parameters()

        self.logger.info("Parameter tuning completed")

    def _calculate_performance_score(self, performance_history: List[Dict[str, Any]]) -> float:
        """
        Calculate a performance score based on multiple metrics.

        Args:
            performance_history: List of performance metrics

        Returns:
            float: Performance score (higher is better)
        """
        if not performance_history:
            return 0.0

        # Get weights for different metrics
        weights = self.config.get("performance_metrics", {})
        success_weight = weights.get("success_rate_weight", 0.4)
        profit_weight = weights.get("profit_weight", 0.4)
        gas_weight = weights.get("gas_efficiency_weight", 0.2)

        # Calculate success rate
        total_txs = len(performance_history)
        successful_txs = sum(1 for p in performance_history if p.get("status") == "success")
        success_rate = successful_txs / total_txs if total_txs > 0 else 0

        # Calculate average profit
        total_profit = sum(p.get("profit_usd", 0) for p in performance_history)
        avg_profit = total_profit / total_txs if total_txs > 0 else 0

        # Calculate gas efficiency (profit per gas used)
        total_gas_cost = sum(p.get("gas_cost_usd", 0.01) for p in performance_history)
        gas_efficiency = total_profit / total_gas_cost if total_gas_cost > 0 else 0

        # Normalize metrics to 0-1 range
        # For success rate, it's already 0-1
        # For profit, normalize based on a target profit
        target_profit = 5.0  # $5 per transaction is a good target
        normalized_profit = min(1.0, avg_profit / target_profit)

        # For gas efficiency, normalize based on a target efficiency
        target_efficiency = 10.0  # 10x return on gas is a good target
        normalized_efficiency = min(1.0, gas_efficiency / target_efficiency)

        # Calculate weighted score
        score = (
            success_weight * success_rate +
            profit_weight * normalized_profit +
            gas_weight * normalized_efficiency
        )

        return score

    def _explore_parameters(self):
        """Explore new parameter values randomly."""
        self.logger.info("Exploring new parameter values...")

        new_params = self.state["current_parameters"].copy()

        # Randomly select parameters to modify
        tunable_params = self.config.get("tunable_parameters", {})
        all_param_keys = []

        for category, params in tunable_params.items():
            for param_name in params:
                all_param_keys.append(f"{category}.{param_name}")

        # Randomly select 1-3 parameters to modify
        num_params_to_modify = min(3, len(all_param_keys))
        if num_params_to_modify > 1:
            num_params_to_modify = secrets.randbelow(num_params_to_modify) + 1  # 1 to min(3, len(all_param_keys))

        # Securely sample parameters to modify
        params_to_modify = []
        available_keys = all_param_keys.copy()
        for _ in range(num_params_to_modify):
            if not available_keys:
                break
            idx = secrets.randbelow(len(available_keys))
            params_to_modify.append(available_keys.pop(idx))

        for param_key in params_to_modify:
            category, param_name = param_key.split(".", 1)
            param_config = tunable_params[category][param_name]

            min_val = param_config.get("min")
            max_val = param_config.get("max")
            step = param_config.get("step")

            if isinstance(min_val, int) and isinstance(max_val, int) and isinstance(step, int):
                # Integer parameter
                steps = (max_val - min_val) // step + 1
                if steps > 0:
                    new_value = min_val + (secrets.randbelow(steps) * step)
                else:
                    new_value = min_val
            else:
                # Float parameter
                steps = int((max_val - min_val) / step)
                if steps > 0:
                    new_value = min_val + (secrets.randbelow(steps + 1) * step)
                else:
                    new_value = min_val
                new_value = round(new_value, 2)  # Round to 2 decimal places

            new_params[param_key] = new_value
            self.logger.info(f"Exploring parameter {param_key}: {new_params[param_key]}")

        # Update current parameters
        self.state["current_parameters"] = new_params

    def _exploit_parameters(self):
        """Refine current parameters based on best known parameters."""
        self.logger.info("Exploiting best known parameters...")

        # If we don't have best parameters yet, just explore
        if not self.state.get("best_parameters"):
            self._explore_parameters()
            return

        new_params = self.state["current_parameters"].copy()
        best_params = self.state["best_parameters"]

        # Get learning rate
        learning_rate = self.config.get("learning_rate", 0.1)

        # Move current parameters towards best parameters
        for param_key, best_value in best_params.items():
            if param_key in new_params:
                current_value = new_params[param_key]

                # Calculate new value (move towards best)
                if isinstance(current_value, (int, float)) and isinstance(best_value, (int, float)):
                    # Move towards best value with some randomness
                    diff = best_value - current_value
                    # Use secrets to generate a random factor between 0.5 and 1.5
                    random_factor = 0.5 + (secrets.randbelow(100) / 100.0)
                    adjustment = diff * learning_rate * random_factor

                    # Get parameter config
                    category, param_name = param_key.split(".", 1)
                    param_config = self.config.get("tunable_parameters", {}).get(category, {}).get(param_name, {})

                    # Apply adjustment
                    if isinstance(current_value, int) and isinstance(best_value, int):
                        # Integer parameter
                        step = param_config.get("step", 1)
                        adjustment = int(adjustment / step) * step
                        new_value = current_value + adjustment
                    else:
                        # Float parameter
                        step = param_config.get("step", 0.1)
                        adjustment = round(adjustment / step) * step
                        new_value = round(current_value + adjustment, 2)

                    # Ensure new value is within bounds
                    min_val = param_config.get("min")
                    max_val = param_config.get("max")
                    if min_val is not None and max_val is not None:
                        new_value = max(min_val, min(max_val, new_value))

                    new_params[param_key] = new_value

                    if new_value != current_value:
                        self.logger.info(f"Adjusting parameter {param_key}: {current_value} -> {new_value}")

        # Update current parameters
        self.state["current_parameters"] = new_params

    def _tune_token_specific_parameters(self):
        """Tune token-specific parameters."""
        # Group performance history by token
        token_history = {}
        min_samples = self.config.get("token_specific_tuning", {}).get("min_samples_per_token", 10)

        for entry in self.state["performance_history"]:
            token = entry.get("token")
            if token:
                if token not in token_history:
                    token_history[token] = []
                token_history[token].append(entry)

        # Tune parameters for each token with enough samples
        for token, history in token_history.items():
            if len(history) >= min_samples:
                self.logger.info(f"Tuning parameters for token {token}...")

                # Calculate token-specific performance
                token_score = self._calculate_performance_score(history)

                # Initialize token-specific parameters if not exist
                if token not in self.state.get("token_specific_parameters", {}):
                    self.state.setdefault("token_specific_parameters", {})[token] = {}

                # Tune parameters for this token
                # For simplicity, we'll just tune a few key parameters
                key_params = [
                    "slippage.base_slippage",
                    "slippage.volatility_factor",
                    "trade.min_profit_threshold_usd"
                ]

                for param_key in key_params:
                    category, param_name = param_key.split(".", 1)
                    param_config = self.config.get("tunable_parameters", {}).get(category, {}).get(param_name, {})

                    # Get current global value
                    current_value = self.state["current_parameters"].get(param_key)

                    if current_value is not None:
                        # Adjust based on token-specific performance
                        # This is a simple heuristic - in a real system, you'd use more sophisticated methods
                        min_val = param_config.get("min")
                        max_val = param_config.get("max")
                        step = param_config.get("step")

                        # Adjust value based on token performance relative to global performance
                        global_score = self.state.get("best_performance", 0.5)
                        if token_score < global_score * 0.8:
                            # Token performing worse than global - make bigger adjustments
                            if param_key == "slippage.base_slippage":
                                # Increase slippage for poorly performing tokens
                                new_value = min(max_val, current_value + step)
                            elif param_key == "trade.min_profit_threshold_usd":
                                # Increase profit threshold for poorly performing tokens
                                new_value = min(max_val, current_value + step)
                            else:
                                # Random adjustment for other parameters
                                # Use secrets to choose between -1 and 1
                                adjustment = (1 if secrets.randbelow(2) == 0 else -1) * step
                                new_value = max(min_val, min(max_val, current_value + adjustment))
                        else:
                            # Token performing similar to or better than global - make smaller adjustments
                            # Use secrets to choose between -0.5, 0, and 0.5
                            choice = secrets.randbelow(3)
                            if choice == 0:
                                adjustment = -0.5 * step
                            elif choice == 1:
                                adjustment = 0
                            else:
                                adjustment = 0.5 * step
                            new_value = max(min_val, min(max_val, current_value + adjustment))

                        # Round to appropriate precision
                        if isinstance(new_value, float):
                            new_value = round(new_value, 2)

                        # Update token-specific parameter
                        if new_value != current_value:
                            self.state["token_specific_parameters"][token][param_key] = new_value
                            self.logger.info(f"Adjusted {param_key} for {token}: {current_value} -> {new_value}")

    def _tune_dex_specific_parameters(self):
        """Tune DEX-specific parameters."""
        # Group performance history by DEX
        dex_history = {}
        min_samples = self.config.get("dex_specific_tuning", {}).get("min_samples_per_dex", 10)

        for entry in self.state["performance_history"]:
            dex = entry.get("dex")
            if dex:
                if dex not in dex_history:
                    dex_history[dex] = []
                dex_history[dex].append(entry)

        # Tune parameters for each DEX with enough samples
        for dex, history in dex_history.items():
            if len(history) >= min_samples:
                self.logger.info(f"Tuning parameters for DEX {dex}...")

                # Calculate DEX-specific performance
                dex_score = self._calculate_performance_score(history)

                # Initialize DEX-specific parameters if not exist
                if dex not in self.state.get("dex_specific_parameters", {}):
                    self.state.setdefault("dex_specific_parameters", {})[dex] = {}

                # Tune parameters for this DEX
                # For simplicity, we'll just tune a few key parameters
                key_params = [
                    "gas.gas_price_multipliers.standard",
                    "gas.gas_price_multipliers.fast",
                    "slippage.max_slippage"
                ]

                for param_key in key_params:
                    category, param_name = param_key.split(".", 1)
                    param_config = self.config.get("tunable_parameters", {}).get(category, {}).get(param_name, {})

                    # Get current global value
                    current_value = self.state["current_parameters"].get(param_key)

                    if current_value is not None:
                        # Adjust based on DEX-specific performance
                        min_val = param_config.get("min")
                        max_val = param_config.get("max")
                        step = param_config.get("step")

                        # Adjust value based on DEX performance relative to global performance
                        global_score = self.state.get("best_performance", 0.5)
                        if dex_score < global_score * 0.8:
                            # DEX performing worse than global - make bigger adjustments
                            if param_key.startswith("gas.gas_price_multipliers"):
                                # Increase gas price for poorly performing DEXes
                                new_value = min(max_val, current_value + step)
                            elif param_key == "slippage.max_slippage":
                                # Increase max slippage for poorly performing DEXes
                                new_value = min(max_val, current_value + step)
                            else:
                                # Random adjustment for other parameters
                                # Use secrets to choose between -1 and 1
                                adjustment = (1 if secrets.randbelow(2) == 0 else -1) * step
                                new_value = max(min_val, min(max_val, current_value + adjustment))
                        else:
                            # DEX performing similar to or better than global - make smaller adjustments
                            # Use secrets to choose between -0.5, 0, and 0.5
                            choice = secrets.randbelow(3)
                            if choice == 0:
                                adjustment = -0.5 * step
                            elif choice == 1:
                                adjustment = 0
                            else:
                                adjustment = 0.5 * step
                            new_value = max(min_val, min(max_val, current_value + adjustment))

                        # Round to appropriate precision
                        if isinstance(new_value, float):
                            new_value = round(new_value, 2)

                        # Update DEX-specific parameter
                        if new_value != current_value:
                            self.state["dex_specific_parameters"][dex][param_key] = new_value
                            self.logger.info(f"Adjusted {param_key} for {dex}: {current_value} -> {new_value}")

    def apply_parameters_to_config(self, config_path: str, config_key: str):
        """
        Apply tuned parameters to a configuration file.

        Args:
            config_path: Path to the configuration file
            config_key: Key in the configuration to update
        """
        try:
            # Load the configuration file
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Get current parameters
            params = self.state["current_parameters"]

            # Update configuration
            for param_key, value in params.items():
                category, param_name = param_key.split(".", 1)

                if category == config_key:
                    # Update the parameter
                    if "." in param_name:
                        # Handle nested parameters
                        parts = param_name.split(".")
                        target = config
                        for part in parts[:-1]:
                            if part not in target:
                                target[part] = {}
                            target = target[part]
                        target[parts[-1]] = value
                    else:
                        # Handle top-level parameters
                        config[param_name] = value

            # Save the updated configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            self.logger.info(f"Applied parameters to {config_path}")

        except Exception as e:
            self.logger.error(f"Error applying parameters to {config_path}: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics.

        Returns:
            Dict[str, Any]: Performance summary
        """
        with self.lock:
            history = self.state.get("performance_history", [])

            if not history:
                return {
                    "total_transactions": 0,
                    "success_rate": 0,
                    "average_profit": 0,
                    "total_profit": 0,
                    "best_performance_score": 0
                }

            # Calculate metrics
            total_txs = len(history)
            successful_txs = sum(1 for p in history if p.get("status") == "success")
            success_rate = successful_txs / total_txs if total_txs > 0 else 0

            total_profit = sum(p.get("profit_usd", 0) for p in history)
            avg_profit = total_profit / successful_txs if successful_txs > 0 else 0

            return {
                "total_transactions": total_txs,
                "successful_transactions": successful_txs,
                "success_rate": success_rate,
                "average_profit": avg_profit,
                "total_profit": total_profit,
                "best_performance_score": self.state.get("best_performance", 0),
                "tuning_count": self.state.get("tuning_count", 0),
                "exploration_rate": self.state.get("exploration_rate", 0.3)
            }
