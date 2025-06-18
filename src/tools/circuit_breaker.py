"""
Circuit breaker for flash loan arbitrage.

This module provides a circuit breaker that can pause trading
during high volatility or when multiple consecutive trades fail.
"""

import logging
import time
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    Circuit breaker for flash loan arbitrage.
    """

    def __init__(self, config_path: str = "config/circuit_breaker_config.json", state_path: str = "data/circuit_breaker_state.json"):
        """
        Initialize the circuit breaker.

        Args:
            config_path: Path to the circuit breaker configuration file
            state_path: Path to the circuit breaker state file
        """
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
                "global": {
                    "is_tripped": False,
                    "trip_time": None,
                    "reset_time": None,
                    "consecutive_failures": 0,
                    "total_failures": 0,
                    "total_successes": 0,
                    "daily_loss_usd": 0.0,
                    "daily_profit_usd": 0.0,
                    "last_reset": time.time()
                },
                "tokens": {},
                "dexes": {}
            }
            self._save_state()

    def _load_config(self) -> Dict[str, Any]:
        """Load circuit breaker configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading circuit breaker config: {e}")

        # Default configuration
        return {
            "max_consecutive_failures": 3,
            "cooldown_period_seconds": 300,
            "max_daily_loss_usd": 100.0,
            "max_drawdown_percentage": 5.0,
            "token_specific_settings": {
                "WETH": {
                    "max_consecutive_failures": 5,
                    "cooldown_period_seconds": 600
                },
                "WBTC": {
                    "max_consecutive_failures": 5,
                    "cooldown_period_seconds": 600
                }
            },
            "dex_specific_settings": {
                "QuickSwap": {
                    "max_consecutive_failures": 4,
                    "cooldown_period_seconds": 450
                },
                "SushiSwap": {
                    "max_consecutive_failures": 4,
                    "cooldown_period_seconds": 450
                }
            },
            "volatility_thresholds": {
                "high": 3.0,  # 3% price change in 5 minutes
                "extreme": 5.0  # 5% price change in 5 minutes
            },
            "auto_reset": True,
            "enable_token_specific_breakers": True,
            "enable_dex_specific_breakers": True
        }

    def _load_state(self) -> Dict[str, Any]:
        """Load circuit breaker state."""
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading circuit breaker state: {e}")

        return {}

    def _save_state(self):
        """Save circuit breaker state."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)

            with open(self.state_path, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving circuit breaker state: {e}")

    def check_circuit(self, token_symbol: Optional[str] = None, dex_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Check if the circuit breaker is tripped.

        Args:
            token_symbol: Symbol of the token being traded
            dex_name: Name of the DEX being used

        Returns:
            Tuple[bool, str]: (is_allowed, reason)
                is_allowed: True if trading is allowed, False if the circuit breaker is tripped
                reason: Reason for the circuit breaker being tripped
        """
        # Initialize state if needed
        if "last_reset" not in self.state["global"]:
            self.state["global"]["last_reset"] = time.time()
            self._save_state()

        # Check if the global circuit breaker is tripped
        if self.state["global"]["is_tripped"]:
            # Check if the cooldown period has passed
            if self.state["global"]["reset_time"] and time.time() >= self.state["global"]["reset_time"]:
                # Reset the circuit breaker
                self.reset_circuit()  # No arguments for global reset
            else:
                # Circuit breaker is still tripped
                remaining_time = int(self.state["global"]["reset_time"] - time.time()) if self.state["global"]["reset_time"] else 0
                return False, f"Global circuit breaker tripped. Cooldown: {remaining_time}s"

        # Check token-specific circuit breaker if enabled
        if self.config["enable_token_specific_breakers"] and token_symbol:
            # Initialize token state if it doesn't exist
            if token_symbol not in self.state["tokens"]:
                self.state["tokens"][token_symbol] = {
                    "is_tripped": False,
                    "trip_time": None,
                    "reset_time": None,
                    "consecutive_failures": 0,
                    "total_failures": 0,
                    "total_successes": 0
                }
                self._save_state()

            if self.state["tokens"][token_symbol].get("is_tripped", False):
                # Check if the cooldown period has passed
                if self.state["tokens"][token_symbol].get("reset_time") and time.time() >= self.state["tokens"][token_symbol]["reset_time"]:
                    # Reset the token-specific circuit breaker
                    self.reset_circuit(token_symbol=token_symbol)
                else:
                    # Token-specific circuit breaker is still tripped
                    remaining_time = int(self.state["tokens"][token_symbol]["reset_time"] - time.time()) if self.state["tokens"][token_symbol].get("reset_time") else 0
                    return False, f"Circuit breaker tripped for {token_symbol}. Cooldown: {remaining_time}s"

        # Check DEX-specific circuit breaker if enabled
        if self.config["enable_dex_specific_breakers"] and dex_name:
            # Initialize DEX state if it doesn't exist
            if dex_name not in self.state["dexes"]:
                self.state["dexes"][dex_name] = {
                    "is_tripped": False,
                    "trip_time": None,
                    "reset_time": None,
                    "consecutive_failures": 0,
                    "total_failures": 0,
                    "total_successes": 0
                }
                self._save_state()

            if self.state["dexes"][dex_name].get("is_tripped", False):
                # Check if the cooldown period has passed
                if self.state["dexes"][dex_name].get("reset_time") and time.time() >= self.state["dexes"][dex_name]["reset_time"]:
                    # Reset the DEX-specific circuit breaker
                    self.reset_circuit(dex_name=dex_name)
                else:
                    # DEX-specific circuit breaker is still tripped
                    remaining_time = int(self.state["dexes"][dex_name]["reset_time"] - time.time()) if self.state["dexes"][dex_name].get("reset_time") else 0
                    return False, f"Circuit breaker tripped for {dex_name}. Cooldown: {remaining_time}s"

        # Check DEX pair-specific circuit breaker if both token and DEX are provided
        if self.config["enable_dex_specific_breakers"] and token_symbol and dex_name:
            dex_pair_key = f"{dex_name}-{token_symbol}"
            if dex_pair_key not in self.state["dexes"]:
                self.state["dexes"][dex_pair_key] = {
                    "is_tripped": False,
                    "trip_time": None,
                    "reset_time": None,
                    "consecutive_failures": 0,
                    "total_failures": 0,
                    "total_successes": 0
                }
                self._save_state()

            if self.state["dexes"][dex_pair_key].get("is_tripped", False):
                # Check if the cooldown period has passed
                if self.state["dexes"][dex_pair_key].get("reset_time") and time.time() >= self.state["dexes"][dex_pair_key]["reset_time"]:
                    # Reset the DEX pair-specific circuit breaker
                    self.reset_circuit(dex_name=dex_pair_key)
                else:
                    # DEX pair-specific circuit breaker is still tripped
                    remaining_time = int(self.state["dexes"][dex_pair_key]["reset_time"] - time.time()) if self.state["dexes"][dex_pair_key].get("reset_time") else 0
                    return False, f"Circuit breaker tripped for {dex_pair_key}. Cooldown: {remaining_time}s"

        # All circuit breakers are clear
        return True, "Trading allowed"

    def record_failure(self, token_symbol: Optional[str] = None, dex_name: Optional[str] = None, loss_usd: float = 0.0):
        """Record a failed trade."""
        self._record_event(success=False, token_symbol=token_symbol, dex_name=dex_name, profit_or_loss_usd=loss_usd)

    def record_success(self, token_symbol: Optional[str] = None, dex_name: Optional[str] = None, profit_usd: float = 0.0):
        """Record a successful trade."""
        self._record_event(success=True, token_symbol=token_symbol, dex_name=dex_name, profit_or_loss_usd=profit_usd)

    def _record_event(self, success: bool, token_symbol: Optional[str] = None, dex_name: Optional[str] = None, profit_or_loss_usd: float = 0.0):
        """Internal method to record trade events and update circuit breaker state."""
        current_time = time.time()

        # Update global state
        global_state = self.state["global"]
        if success:
            global_state["consecutive_failures"] = 0
            global_state["total_successes"] = global_state.get("total_successes", 0) + 1
            global_state["daily_profit_usd"] = global_state.get("daily_profit_usd", 0) + profit_or_loss_usd
        else:
            global_state["consecutive_failures"] += 1
            global_state["total_failures"] = global_state.get("total_failures", 0) + 1
            global_state["daily_loss_usd"] = global_state.get("daily_loss_usd", 0) + profit_or_loss_usd

        # Check global trip conditions
        max_consecutive_failures = self.config.get("max_consecutive_failures", 3)
        max_daily_loss_usd = self.config.get("max_daily_loss_usd", 100.0)

        if global_state["consecutive_failures"] >= max_consecutive_failures:
            self.trip_circuit(reason=f"Global: {global_state['consecutive_failures']} consecutive failures.")
        elif global_state["daily_loss_usd"] >= max_daily_loss_usd:
            self.trip_circuit(reason=f"Global: Daily loss ${global_state['daily_loss_usd']:.2f} exceeded limit of ${max_daily_loss_usd:.2f}.")

        # Update token-specific state if applicable
        if self.config.get("enable_token_specific_breakers") and token_symbol:
            if token_symbol not in self.state["tokens"]:
                self._initialize_entity_state("tokens", token_symbol)
            
            token_state = self.state["tokens"][token_symbol]
            token_config = self.config.get("token_specific_settings", {}).get(token_symbol, {})
            
            if success:
                token_state["consecutive_failures"] = 0
                token_state["total_successes"] = token_state.get("total_successes", 0) + 1
            else:
                token_state["consecutive_failures"] += 1
                token_state["total_failures"] = token_state.get("total_failures", 0) + 1

            token_max_consecutive_failures = token_config.get("max_consecutive_failures", max_consecutive_failures)
            if token_state["consecutive_failures"] >= token_max_consecutive_failures:
                self.trip_circuit(token_symbol=token_symbol, reason=f"Token {token_symbol}: {token_state['consecutive_failures']} consecutive failures.")

        # Update DEX-specific state if applicable
        if self.config.get("enable_dex_specific_breakers") and dex_name:
            if dex_name not in self.state["dexes"]:
                self._initialize_entity_state("dexes", dex_name)

            dex_state = self.state["dexes"][dex_name]
            dex_config = self.config.get("dex_specific_settings", {}).get(dex_name, {})

            if success:
                dex_state["consecutive_failures"] = 0
                dex_state["total_successes"] = dex_state.get("total_successes", 0) + 1
            else:
                dex_state["consecutive_failures"] += 1
                dex_state["total_failures"] = dex_state.get("total_failures", 0) + 1
            
            dex_max_consecutive_failures = dex_config.get("max_consecutive_failures", max_consecutive_failures)
            if dex_state["consecutive_failures"] >= dex_max_consecutive_failures:
                self.trip_circuit(dex_name=dex_name, reason=f"DEX {dex_name}: {dex_state['consecutive_failures']} consecutive failures.")
        
        self._save_state()

    def trip_circuit(self, token_symbol: Optional[str] = None, dex_name: Optional[str] = None, reason: str = "Unknown reason"):
        """Trip the circuit breaker."""
        now = time.time()

        if token_symbol:
            # Trip token-specific circuit breaker
            token_settings = self.config["token_specific_settings"].get(token_symbol, {})
            cooldown = token_settings.get("cooldown_period_seconds", self.config["cooldown_period_seconds"])

            self.state["tokens"][token_symbol]["is_tripped"] = True
            self.state["tokens"][token_symbol]["trip_time"] = now
            self.state["tokens"][token_symbol]["reset_time"] = now + cooldown

            self.logger.warning(f"Circuit breaker tripped for {token_symbol}: {reason}. Cooldown: {cooldown}s")
        elif dex_name:
            # Trip DEX-specific circuit breaker
            dex_settings = self.config["dex_specific_settings"].get(dex_name, {})
            cooldown = dex_settings.get("cooldown_period_seconds", self.config["cooldown_period_seconds"])

            self.state["dexes"][dex_name]["is_tripped"] = True
            self.state["dexes"][dex_name]["trip_time"] = now
            self.state["dexes"][dex_name]["reset_time"] = now + cooldown

            self.logger.warning(f"Circuit breaker tripped for {dex_name}: {reason}. Cooldown: {cooldown}s")
        else:
            # Trip global circuit breaker
            cooldown = self.config["cooldown_period_seconds"]

            self.state["global"]["is_tripped"] = True
            self.state["global"]["trip_time"] = now
            self.state["global"]["reset_time"] = now + cooldown

            self.logger.warning(f"Global circuit breaker tripped: {reason}. Cooldown: {cooldown}s")

        # Save the updated state
        self._save_state()

    def reset_circuit(self, token_symbol: Optional[str] = None, dex_name: Optional[str] = None):
        """Reset the circuit breaker."""
        current_time = time.time()
        if token_symbol:
            if token_symbol in self.state["tokens"]:
                self.state["tokens"][token_symbol]["is_tripped"] = False
                self.state["tokens"][token_symbol]["trip_time"] = None
                self.state["tokens"][token_symbol]["reset_time"] = None
                self.state["tokens"][token_symbol]["consecutive_failures"] = 0
                self.logger.info(f"Circuit breaker reset for token: {token_symbol}")
            else:
                self.logger.warning(f"Attempted to reset non-existent token circuit breaker: {token_symbol}")
        elif dex_name:
            if dex_name in self.state["dexes"]:
                self.state["dexes"][dex_name]["is_tripped"] = False
                self.state["dexes"][dex_name]["trip_time"] = None
                self.state["dexes"][dex_name]["reset_time"] = None
                self.state["dexes"][dex_name]["consecutive_failures"] = 0
                self.logger.info(f"Circuit breaker reset for DEX: {dex_name}")
            else:
                self.logger.warning(f"Attempted to reset non-existent DEX circuit breaker: {dex_name}")
        else:  # Global reset
            self.state["global"]["is_tripped"] = False
            self.state["global"]["trip_time"] = None
            self.state["global"]["reset_time"] = None
            self.state["global"]["consecutive_failures"] = 0
            self.state["global"]["daily_loss_usd"] = 0.0  # Reset daily loss on global reset
            self.logger.info("Global circuit breaker reset.")
        
        self._save_state()

    def _initialize_entity_state(self, entity_type: str, entity_name: str):
        """Initializes state for a token or DEX if it doesn't exist."""
        if entity_name not in self.state[entity_type]:
            self.state[entity_type][entity_name] = {
                "is_tripped": False,
                "trip_time": None,
                "reset_time": None,
                "consecutive_failures": 0,
                "total_failures": 0,
                "total_successes": 0
            }

    def record_volatility(self, token_symbol: str, price_change_percentage: float, timeframe_minutes: int = 5):
        """
        Record volatility and potentially trip the circuit breaker if volatility is too high.

        Args:
            token_symbol: Symbol of the token
            price_change_percentage: Absolute percentage price change
            timeframe_minutes: Timeframe in minutes over which the price change occurred
        """
        # Normalize to 5-minute timeframe for comparison with thresholds
        normalized_change = price_change_percentage * (5 / timeframe_minutes)

        # Check against volatility thresholds
        if normalized_change >= self.config["volatility_thresholds"]["extreme"]:
            self.trip_circuit(
                reason=f"Extreme volatility detected for {token_symbol}: {price_change_percentage:.2f}% in {timeframe_minutes} minutes",
                token_symbol=token_symbol
            )
            self.logger.warning(f"Circuit breaker tripped due to extreme volatility for {token_symbol}")
        elif normalized_change >= self.config["volatility_thresholds"]["high"]:
            self.logger.warning(f"High volatility detected for {token_symbol}: {price_change_percentage:.2f}% in {timeframe_minutes} minutes")

            # Increment consecutive failures to bring it closer to tripping
            if token_symbol in self.state["tokens"]:
                self.state["tokens"][token_symbol]["consecutive_failures"] += 1

                # Check if it should trip now
                token_settings = self.config["token_specific_settings"].get(token_symbol, {})
                max_failures = token_settings.get("max_consecutive_failures", self.config["max_consecutive_failures"])

                if self.state["tokens"][token_symbol]["consecutive_failures"] >= max_failures:
                    self.trip_circuit(
                        reason=f"High volatility and consecutive failures for {token_symbol}",
                        token_symbol=token_symbol
                    )

            # Save the updated state
            self._save_state()
