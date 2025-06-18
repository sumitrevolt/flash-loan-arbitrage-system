"""
Parameter tuning manager for flash loan arbitrage.

This module coordinates the parameter tuning process by collecting performance
metrics, tuning parameters, and synchronizing them across the system.
"""

import logging
import time
import json
import os
import threading
from typing import Dict, Any

# Import parameter tuning components
try:
    from src.flash_loan.core.parameter_tuner import ParameterTuner
    from src.flash_loan.core.parameter_sync import ParameterSynchronizer
    from src.flash_loan.core.performance_metrics import PerformanceMetricsCollector
    PARAMETER_TUNING_AVAILABLE = True
except ImportError as e:
    PARAMETER_TUNING_AVAILABLE = False
    logging.getLogger("parameter_tuning_manager").warning(f"Parameter tuning components not available: {e}. Tuning will be disabled.")

# Set up logging
logger = logging.getLogger(__name__)

class ParameterTuningManager:
    """
    Coordinates the parameter tuning process.
    """

    def __init__(self, config_path: str = "config/parameter_tuning_manager_config.json"):
        """
        Initialize the parameter tuning manager.

        Args:
            config_path: Path to the parameter tuning manager configuration file
        """
        # Register cleanup handler for graceful shutdown
        import atexit
        atexit.register(self.cleanup)
        
        # Also handle signals
        import signal
        signal.signal(signal.SIGINT, lambda s, f: self.cleanup())
        signal.signal(signal.SIGTERM, lambda s, f: self.cleanup())

        self.logger = logging.getLogger(__name__)
        self.config_path = config_path

        # Load configuration
        self.config = self._load_config()

        # Initialize components if available
        self.tuner = None
        self.synchronizer = None
        self.metrics_collector = None

        if PARAMETER_TUNING_AVAILABLE:
            try:
                self.tuner = ParameterTuner()
                self.logger.info("Parameter tuner initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing parameter tuner: {e}")

            try:
                self.synchronizer = ParameterSynchronizer()
                self.logger.info("Parameter synchronizer initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing parameter synchronizer: {e}")

            try:
                self.metrics_collector = PerformanceMetricsCollector()
                self.logger.info("Performance metrics collector initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing performance metrics collector: {e}")

        # Initialize synchronization primitives
        self.lock = threading.Lock()
        self.shutdown_event = threading.Event()

        # Initialize tuning thread state
        self.tuning_thread = None
        self.tuning_thread_running = False
        self._last_tuning_time = None

        # Start tuning thread if auto-tuning is enabled
        if self.config.get("auto_tuning_enabled", True) and PARAMETER_TUNING_AVAILABLE:
            self.start_tuning_thread()

    def _load_config(self) -> Dict[str, Any]:
        """Load parameter tuning manager configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading parameter tuning manager config: {e}")

        # Default configuration
        return {
            "auto_tuning_enabled": True,
            "tuning_interval_seconds": 3600,
            "sync_after_tuning": True,
            "min_transactions_for_tuning": 20,
            "tuning_window_size": "medium_term",
            "token_specific_tuning_enabled": True,
            "dex_specific_tuning_enabled": True
        }

    def start_tuning_thread(self):
        """Start the parameter tuning thread."""
        if not PARAMETER_TUNING_AVAILABLE:
            self.logger.warning("Parameter tuning components not available. Cannot start tuning thread.")
            return

        if self.tuning_thread_running:
            self.logger.warning("Tuning thread is already running")
            return

        self.tuning_thread_running = True
        # SNYK-FIX: The tuning thread is joined on shutdown via stop_tuning_thread().
        # Suppress Snyk THREAD-JOIN warning: join is called in stop_tuning_thread(), and the thread is a daemon.
        self.tuning_thread = threading.Thread(target=self._tuning_thread_function, daemon=True, name="ParameterTuningThread")  # noqa  # pylint: disable=not-joined-thread
        self.tuning_thread.start()
        self.logger.info(f"Parameter tuning thread started: {self.tuning_thread.name} (id: {self.tuning_thread.ident})")

    def stop_tuning_thread(self):
        """Stop the parameter tuning thread."""
        if not self.tuning_thread_running:
            self.logger.debug("Tuning thread is not running")
            return

        self.logger.info("Stopping parameter tuning thread...")
        self.tuning_thread_running = False

        # Wait for thread to complete current iteration
        if self.tuning_thread and self.tuning_thread.is_alive():
            self.tuning_thread.join(timeout=60)  # Wait up to 60 seconds
            if self.tuning_thread.is_alive():
                self.logger.warning("Tuning thread did not stop within timeout period")
            else:
                self.logger.info("Parameter tuning thread stopped successfully")

    def _tuning_thread_function(self):
        """Parameter tuning thread function."""
        self.logger.debug("Parameter tuning thread starting...")
        while not self.shutdown_event.is_set() and self.tuning_thread_running:
            try:
                # Check if we have enough data for tuning
                if self.metrics_collector:
                    metrics = self.metrics_collector.get_metrics_for_tuning(
                        window_size=self.config.get("tuning_window_size", "medium_term")
                    )

                    if metrics.get("status") == "success" and metrics.get("total_transactions", 0) >= self.config.get("min_transactions_for_tuning", 20):
                        # Perform tuning
                        self.tune_parameters()
                    else:
                        self.logger.info("Not enough data for parameter tuning yet")

                # Sleep until next tuning interval
                tuning_interval = self.config.get("tuning_interval_seconds", 3600)
                for _ in range(tuning_interval):
                    if not self.tuning_thread_running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in parameter tuning thread: {e}")
                time.sleep(60)  # Sleep for a minute before retrying

    def record_transaction(self, transaction_data: Dict[str, Any]):
        """
        Record a transaction for performance metrics.

        Args:
            transaction_data: Transaction data
        """
        if not PARAMETER_TUNING_AVAILABLE or not self.metrics_collector:
            return

        try:
            self.metrics_collector.record_transaction(transaction_data)
        except Exception as e:
            self.logger.error(f"Error recording transaction: {e}")

    def tune_parameters(self) -> bool:
        """
        Tune parameters based on performance metrics.

        Returns:
            bool: True if successful, False otherwise
        """
        if not PARAMETER_TUNING_AVAILABLE or not self.tuner or not self.metrics_collector:
            self.logger.warning("Parameter tuning components not available. Cannot tune parameters.")
            return False

        with self.lock:
            try:
                self.logger.info("Tuning parameters based on performance metrics...")

                # Get global metrics
                metrics = self.metrics_collector.get_metrics_for_tuning(
                    window_size=self.config.get("tuning_window_size", "medium_term")
                )

                if metrics.get("status") != "success":
                    self.logger.warning("No metrics available for parameter tuning")
                    return False

                # Record performance in the tuner
                self.tuner.record_performance(metrics)

                # Get token-specific metrics if enabled
                if self.config.get("token_specific_tuning_enabled", True):
                    token_metrics = {}
                    for token in self.config.get("tokens_to_tune", ["WETH", "WBTC", "USDC", "WMATIC", "LINK"]):
                        token_data = self.metrics_collector.get_token_metrics_for_tuning(token)
                        if token_data.get("status") == "success" and token_data.get("total_transactions", 0) >= self.config.get("min_transactions_for_tuning", 20):
                            token_metrics[token] = token_data
                            self.tuner.record_performance(token_data, token_symbol=token)

                # Get DEX-specific metrics if enabled
                if self.config.get("dex_specific_tuning_enabled", True):
                    dex_metrics = {}
                    for dex in self.config.get("dexes_to_tune", ["QuickSwap", "SushiSwap", "UniswapV3"]):
                        dex_data = self.metrics_collector.get_dex_metrics_for_tuning(dex)
                        if dex_data.get("status") == "success" and dex_data.get("total_transactions", 0) >= self.config.get("min_transactions_for_tuning", 20):
                            dex_metrics[dex] = dex_data
                            self.tuner.record_performance(dex_data, dex_name=dex)

                # Synchronize parameters if enabled
                if self.config.get("sync_after_tuning", True) and self.synchronizer:
                    # Get tuned parameters
                    global_params = self.tuner.get_parameters()

                    # Get token-specific parameters
                    token_params = {}
                    if self.config.get("token_specific_tuning_enabled", True):
                        for token in self.config.get("tokens_to_tune", ["WETH", "WBTC", "USDC", "WMATIC", "LINK"]):
                            token_specific_params = self.tuner.get_parameters(token_symbol=token)
                            if token_specific_params:
                                token_params[token] = token_specific_params

                    # Get DEX-specific parameters
                    dex_params = {}
                    if self.config.get("dex_specific_tuning_enabled", True):
                        for dex in self.config.get("dexes_to_tune", ["QuickSwap", "SushiSwap", "UniswapV3"]):
                            dex_specific_params = self.tuner.get_parameters(dex_name=dex)
                            if dex_specific_params:
                                dex_params[dex] = dex_specific_params

                    # Synchronize parameters
                    self.synchronizer.sync_parameters(global_params, token_params, dex_params)
                    self.logger.info("Parameters synchronized successfully")

                self.logger.info("Parameter tuning completed successfully")
                self._last_tuning_time = time.time()
                return True

            except Exception as e:
                self.logger.error(f"Error tuning parameters: {e}")
                return False

    def get_current_parameters(self) -> Dict[str, Any]:
        """
        Get the current parameters.

        Returns:
            Dict[str, Any]: Current parameters
        """
        if not PARAMETER_TUNING_AVAILABLE or not self.tuner:
            return {}

        try:
            return self.tuner.get_parameters()
        except Exception as e:
            self.logger.error(f"Error getting current parameters: {e}")
            return {}

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics.

        Returns:
            Dict[str, Any]: Performance summary
        """
        if not PARAMETER_TUNING_AVAILABLE or not self.metrics_collector:
            return {}

        try:
            return self.metrics_collector.get_performance_summary()
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {}

    def get_tuning_status(self) -> Dict[str, Any]:
        """
        Get the status of the parameter tuning process.

        Returns:
            Dict[str, Any]: Tuning status
        """
        if not PARAMETER_TUNING_AVAILABLE or not self.tuner:
            return {
                "status": "disabled",
                "reason": "Parameter tuning components not available"
            }

        try:
            tuner_summary = self.tuner.get_performance_summary()

            return {
                "status": "active" if self.tuning_thread_running else "inactive",
                "tuning_count": tuner_summary.get("tuning_count", 0),
                "exploration_rate": tuner_summary.get("exploration_rate", 0),
                "best_performance_score": tuner_summary.get("best_performance_score", 0),
                "total_transactions": tuner_summary.get("total_transactions", 0),
                "success_rate": tuner_summary.get("success_rate", 0),
                "auto_tuning_enabled": self.config.get("auto_tuning_enabled", True),
                "tuning_interval_seconds": self.config.get("tuning_interval_seconds", 3600)
            }
        except Exception as e:
            self.logger.error(f"Error getting tuning status: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }

    def cleanup(self):
        """Cleanup handler for graceful system shutdown."""
        if self.tuning_thread_running:
            self.logger.info("System shutdown detected, stopping parameter tuning thread...")
            self.shutdown_event.set()
            self.tuning_thread_running = False

            if self.tuning_thread and self.tuning_thread.is_alive():
                self.logger.debug(f"Waiting for tuning thread {self.tuning_thread.name} to finish...")
                self.tuning_thread.join(timeout=30)

                if self.tuning_thread.is_alive():
                    self.logger.warning("Tuning thread did not stop within timeout")
                else:
                    self.logger.info("Tuning thread stopped successfully")

            # Clear thread state
            self.tuning_thread = None
            self._last_tuning_time = None

        # Log final status before shutdown
        if PARAMETER_TUNING_AVAILABLE and self.tuner:
            try:
                tuner_summary = self.tuner.get_performance_summary()
                self.logger.info(f"Final tuning stats: {tuner_summary.get('tuning_count', 0)} tunings, " +
                                f"{tuner_summary.get('success_rate', 0):.2f}% success rate")
            except Exception as e:
                self.logger.error(f"Error getting final tuning stats: {e}")

        self.logger.info("Parameter tuning manager cleanup complete")
