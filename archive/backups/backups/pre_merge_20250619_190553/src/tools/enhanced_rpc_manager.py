#!/usr/bin/env python3
"""
Enhanced RPC Manager with failover, performance tracking, and reliability features
"""

import asyncio
import logging
import time
import os
import json
from typing import Dict, List, Optional, Any, Union, Callable

# Import Web3 with error handling
try:
    # Import from central web3_provider
    from src.utils.web3_provider import Web3
    from web3.types import Wei, TxParams
    from web3.providers import HTTPProvider
    # Import exceptions from central provider
    from src.utils.web3_provider import Web3Exception
    WEB3_IMPORTED = True
except ImportError as e:
    logging.getLogger(__name__).error(f"Failed to import Web3: {e}")
    WEB3_IMPORTED = False
    Web3 = None
    Wei = int
    TxParams = Any
    Web3Exception = Exception
    HTTPProvider = None

# Import middleware compatibility utilities
try:
    from src.utils.middleware_compat import get_poa_middleware, inject_middleware, apply_poa_middleware
except ImportError:
    def get_poa_middleware():
        return None
    def inject_middleware(w3, middleware, layer=0):
        pass

class EnhancedRpcManager:
    """Enhanced RPC manager with failover and performance tracking"""
    def __init__(self, rpc_urls: Optional[List[str]] = None, performance_tracking_enabled: bool = True, config_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not WEB3_IMPORTED:
            self.logger.error("Web3 not available - RPC manager will have limited functionality")
            
        # Default configuration with optimized settings
        self.default_config = {
            "rpc_urls": [
                "https://polygon.gateway.tenderly.co",
                "https://polygon-bor.publicnode.com",
                "https://polygon.drpc.org",
                "https://polygon.meowrpc.com",
                "https://polygon.rpc.blxrbdn.com",
                "https://polygon-mainnet.public.blastapi.io",
                "https://1rpc.io/matic",
                "https://rpc.ankr.com/polygon",
                "https://rpc-mainnet.matic.quiknode.pro",
                "https://polygon-mainnet.g.alchemy.com/v2/demo",
                "https://polygon.blockpi.network/v1/rpc/public",
                "https://polygon.api.onfinality.io/public",
                "https://polygon.llamarpc.com"
            ],
            "timeout": 20,  # Reduced timeout for faster failover
            "max_retries": 3,  # Reduced retries for faster failover
            "retry_delay": 1,  # Reduced delay for faster recovery
            "connection_pool_size": 10,  # Connection pooling for better performance
            "rate_limit_detection": {
                "keywords": [
                    "rate limit",
                    "too many requests",
                    "call rate limit",
                    "throttle",
                    "exceeded",
                    "retry",
                    "too many concurrent requests",
                    "request limit",
                    "limit reached",
                    "capacity",
                    "quota",
                    "429",  # HTTP status code for too many requests
                    "slow down"
                ],
                "max_failures": 2,  # More aggressive failure detection
                "cooldown_period": 180  # 3 minutes - shorter cooldown
            },
            "rotation": {
                "enabled": True,
                "requests_per_endpoint": 30,  # More frequent rotation
                "rotation_strategy": "performance"  # New strategy based on performance
            },
            "performance_tracking": {
                "enabled": True,
                "window_size": 100,  # Track last 100 requests
                "latency_threshold_ms": 1000,  # 1 second
                "success_rate_threshold": 0.8  # 80% success rate
            }
        }        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize RPC state with optimized settings
        # Use provided rpc_urls or get from config
        if rpc_urls:
            self.rpc_urls = rpc_urls
        else:
            self.rpc_urls = self.config.get("rpc_urls", [])
        self.timeout = self.config.get("timeout", 20)
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 1)
        self.connection_pool_size = self.config.get("connection_pool_size", 10)

        # Rate limit tracking
        self.rate_limit_keywords = self.config["rate_limit_detection"]["keywords"]
        self.max_failures = self.config["rate_limit_detection"]["max_failures"]
        self.cooldown_period = self.config["rate_limit_detection"]["cooldown_period"]

        # Performance tracking
        self.performance_tracking_enabled = self.config.get("performance_tracking", {}).get("enabled", True)
        self.performance_window_size = self.config.get("performance_tracking", {}).get("window_size", 100)
        self.latency_threshold_ms = self.config.get("performance_tracking", {}).get("latency_threshold_ms", 1000)
        self.success_rate_threshold = self.config.get("performance_tracking", {}).get("success_rate_threshold", 0.8)

        # Track endpoint health, usage and performance
        self.endpoint_status = {}
        for url in self.rpc_urls:
            self.endpoint_status[url] = {
                "active": True,
                "failures": 0,
                "rate_limited": False,
                "rate_limit_until": 0,  # Unix timestamp
                "last_success": 0,      # Unix timestamp
                "total_requests": 0,
                "successful_requests": 0,
                "consecutive_errors": 0,
                # Performance metrics
                "response_times": [],   # List of recent response times in ms
                "avg_response_time": 0, # Average response time in ms
                "success_rate": 1.0,    # Success rate (0.0-1.0)
                "performance_score": 0, # Calculated performance score
                "last_updated": time.time()
            }

        # Rotation settings
        self.rotation_enabled = self.config["rotation"]["enabled"]
        self.requests_per_endpoint = self.config["rotation"]["requests_per_endpoint"]
        self.rotation_strategy = self.config["rotation"]["rotation_strategy"]

        # Connection pooling
        self.web3_instances = {}  # Cache of Web3 instances by URL
        self.connection_pool = []  # Pool of active connections

        # Current state
        self.current_endpoint_index = 0
        self.current_endpoint = None
        self.current_web3 = None
        self.requests_since_rotation = 0

        # Initial endpoint selection
        self._select_best_endpoint()

        self.logger.info(f"Enhanced RPC Manager initialized with {len(self.rpc_urls)} endpoints")
        self.logger.info(f"Currently using endpoint: {self.current_endpoint}")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use default.

        Args:
            config_path: Path to the configuration file

        Returns:
            Dict with configuration
        """
        config = self.default_config.copy()

        if config_path is None:
            # Try to find config in common locations
            possible_paths = [
                "config/network_config.json",
                "network_config.json",
                os.path.join(os.getcwd(), "config/network_config.json"),
                os.path.join(os.getcwd(), "network_config.json"),
                os.path.join(os.path.dirname(__file__), "../../../config/network_config.json")
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)

                # Extract RPC URLs
                if "rpc_urls" in file_config:
                    config["rpc_urls"] = file_config["rpc_urls"]
                elif "rpc_url" in file_config:
                    # Single RPC URL
                    config["rpc_urls"] = [file_config["rpc_url"]]

                # Extract other settings if available
                if "timeout" in file_config:
                    config["timeout"] = file_config["timeout"]

                self.logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                self.logger.error(f"Error loading config from {config_path}: {e}")
        else:
            self.logger.warning("No configuration file found, using default configuration")

        # Ensure we have at least one RPC URL
        if not config["rpc_urls"]:
            self.logger.error("No RPC URLs configured. Using emergency fallback URLs.")
            config["rpc_urls"] = self.default_config["rpc_urls"]

        # Default polygon RPC endpoints
        default_endpoints = [
            os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
            os.getenv("POLYGON_BACKUP_RPC_URL", "https://rpc-mainnet.matic.network"),
            os.getenv("POLYGON_ARCHIVE_RPC_URL", "https://matic-mainnet.chainstacklabs.com"),
        ]
        
        # Add endpoints from environment
        env_rpc = os.getenv("POLYGON_RPC_ENDPOINTS")
        if env_rpc:
            try:
                env_endpoints = json.loads(env_rpc)

                # Validate and add each endpoint
                for endpoint in env_endpoints:
                    if isinstance(endpoint, str) and endpoint.startswith("http"):
                        config["rpc_urls"].append(endpoint)
                    else:
                        self.logger.warning(f"Invalid RPC endpoint from env: {endpoint}")
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse POLYGON_RPC_ENDPOINTS from env, using defaults")

        return config

    def _calculate_performance_score(self, url: str) -> float:
        """
        Calculate a performance score for an endpoint based on response time and success rate.

        Args:
            url: The RPC URL to calculate score for

        Returns:
            float: Performance score (higher is better)
        """
        status = self.endpoint_status.get(url)
        if not status:
            return 0.0

        # Calculate success rate
        total_requests = status["total_requests"]
        if total_requests == 0:
            success_rate = 1.0  # Assume perfect for new endpoints
        else:
            success_rate = status["successful_requests"] / total_requests

        # Calculate average response time (if available)
        response_times = status["response_times"]
        if not response_times:
            avg_response_time = 500  # Default assumption (500ms)
        else:
            avg_response_time = sum(response_times) / len(response_times)

        # Normalize response time (lower is better)
        # 100ms -> 1.0, 1000ms -> 0.1
        response_time_score = min(1.0, 100 / max(100, avg_response_time))


        # Calculate final score (70% success rate, 30% response time)
        score = (success_rate * 0.7) + (response_time_score * 0.3)
        return score

    def _select_best_endpoint(self):
        import secrets
        # Build the list of available endpoints
        available_endpoints = [
            (url, status)
            for url, status in self.endpoint_status.items()
            if status["active"] and not status["rate_limited"] and (status["rate_limit_until"] <= time.time())
        ]

        if not available_endpoints:
            self.logger.error("No healthy endpoints available! Attempting to reset all endpoints.")
            for url, status in self.endpoint_status.items():
                status["active"] = True
                status["rate_limited"] = False
                status["consecutive_errors"] = 0
                available_endpoints.append((url, status))

        if not available_endpoints:
            self.logger.critical("Cannot find any usable RPC endpoints!")
            return False

        # Choose endpoint based on strategy
        if self.rotation_strategy == "performance" and self.performance_tracking_enabled:
            # Calculate performance scores for all available endpoints
            scored_endpoints = []
            for url, status in available_endpoints:
                score = self._calculate_performance_score(url)
                scored_endpoints.append((url, status, score))

            # Sort by score (highest first)
            scored_endpoints.sort(key=lambda x: Any: Any: x[2], reverse=True)

            # Add some randomness to prevent always using the same endpoint
            # 80% chance of using the best endpoint, 20% chance of using another good one
            if len(scored_endpoints) > 1 and secrets.randbelow(100) > 80:  # 20% chance
                # Use the second-best endpoint occasionally
                chosen_url = scored_endpoints[1][0]
                self.logger.debug(f"Using second-best endpoint {chosen_url} for diversity")
            else:
                # Use the best endpoint
                chosen_url = scored_endpoints[0][0]
                self.logger.debug(f"Using best performing endpoint {chosen_url} with score {scored_endpoints[0][2]:.2f}")
        elif self.rotation_strategy == "random":
            # Use cryptographically secure random choice
            chosen_url, _ = available_endpoints[secrets.randbelow(len(available_endpoints))]
        else:  # "round_robin" or anything else
            # Skip to next available endpoint
            for _ in range(len(self.endpoint_status)):
                self.current_endpoint_index = (self.current_endpoint_index + 1) % len(self.rpc_urls)
                if self.rpc_urls[self.current_endpoint_index] in [url for url, _ in available_endpoints]:
                    break
            chosen_url = self.rpc_urls[self.current_endpoint_index]

        # Set the current endpoint
        old_endpoint = self.current_endpoint
        self.current_endpoint = chosen_url
        self.requests_since_rotation = 0

        # Check if we already have a Web3 instance for this endpoint in the pool
        if chosen_url in self.web3_instances:
            self.logger.debug(f"Using cached Web3 instance for {chosen_url}")
            self.current_web3 = self.web3_instances[chosen_url]
        # Create a new Web3 instance if needed
        elif old_endpoint != self.current_endpoint or self.current_web3 is None:
            try:
                self.logger.info(f"Creating new Web3 instance with endpoint: {chosen_url}")

                # Use connection pooling for better performance
                provider = HTTPProvider(
                    chosen_url,
                    request_kwargs={
                        'timeout': self.timeout
                    }
                )
                self.current_web3 = Web3(provider)

                # Apply middleware for PoA chains
                # Apply PoA middleware using compatibility helper
                try:
                    apply_poa_middleware(self.current_web3)
                    self.logger.info("Applied PoA middleware to Web3 instance")
                except Exception as e:
                    self.logger.warning(f"Error applying PoA middleware: {e}")

                # Cache the Web3 instance
                self.web3_instances[chosen_url] = self.current_web3

                # Manage connection pool size
                if len(self.web3_instances) > self.connection_pool_size:
                    # Remove the least recently used connection
                    least_used_url = min(
                        self.endpoint_status.items(),
                        key=lambda x: Any: Any: x[1]["last_updated"] if x[0] in self.web3_instances else float('inf')
                    )[0]
                    if least_used_url in self.web3_instances and least_used_url != chosen_url:
                        self.logger.debug(f"Removing least recently used connection: {least_used_url}")
                        del self.web3_instances[least_used_url]

            except Exception as e:
                self.logger.error(f"Error creating Web3 instance for {chosen_url}: {e}")
                # Mark this endpoint as having a problem
                self.endpoint_status[chosen_url]["consecutive_errors"] += 1
                # Try another endpoint
                return self._select_best_endpoint()

        self.logger.info(f"Selected RPC endpoint: {chosen_url}")
        return True

        # Set the current endpoint
        old_endpoint = self.current_endpoint
        self.current_endpoint = chosen_url
        self.requests_since_rotation = 0

        # Check if we already have a Web3 instance for this endpoint in the pool
        if chosen_url in self.web3_instances:
            self.logger.debug(f"Using cached Web3 instance for {chosen_url}")
            self.current_web3 = self.web3_instances[chosen_url]
        # Create a new Web3 instance if needed
        elif old_endpoint != self.current_endpoint or self.current_web3 is None:
            try:
                self.logger.info(f"Creating new Web3 instance with endpoint: {chosen_url}")

                # Use connection pooling for better performance
                provider = HTTPProvider(
                    chosen_url,
                    request_kwargs={
                        'timeout': self.timeout
                    }
                )
                self.current_web3 = Web3(provider)

                # Apply middleware for PoA chains
                try:
                    try:
                        # Try to import the new v7 compatible middleware
                        from src.utils.web3_v7_middleware import get_compatible_middleware, apply_middleware
                        middleware = get_compatible_middleware()
                        if middleware:
                            apply_middleware(self.current_web3)
                            self.logger.info("Applied compatible middleware to Web3 instance")
                    except ImportError:
                        # Fall back to standard geth_poa_middleware
                        try:
                            # Import middleware from centralized modules
                            from src.utils.middleware_compat import apply_poa_middleware
                            apply_poa_middleware(self.current_web3)
                            self.logger.info("Applied standard PoA middleware to Web3 instance")
                        except ImportError:
                            self.logger.warning("PoA middleware could not be applied.")
                except Exception as middleware_err:
                    self.logger.warning(f"Error applying middleware: {middleware_err}")

                # Cache the Web3 instance
                self.web3_instances[chosen_url] = self.current_web3

                # Manage connection pool size
                if len(self.web3_instances) > self.connection_pool_size:
                    # Remove the least recently used connection
                    least_used_url = min(
                        self.endpoint_status.items(),
                        key=lambda x: Any: Any: x[1]["last_updated"] if x[0] in self.web3_instances else float('inf')
                    )[0]
                    if least_used_url in self.web3_instances and least_used_url != chosen_url:
                        self.logger.debug(f"Removing least recently used connection: {least_used_url}")
                        del self.web3_instances[least_used_url]

            except Exception as e:
                self.logger.error(f"Error creating Web3 instance for {chosen_url}: {e}")
                # Mark this endpoint as having a problem
                self.endpoint_status[chosen_url]["consecutive_errors"] += 1
                # Try another endpoint
                return self._select_best_endpoint()

        self.logger.info(f"Selected RPC endpoint: {chosen_url}")
        return True

    def _rotate_if_needed(self) -> None:
        """
        Rotate to a new endpoint if we've reached the request limit for the current one.
        """
        if not self.rotation_enabled:
            return

        self.requests_since_rotation += 1

        if self.requests_since_rotation >= self.requests_per_endpoint:
            self.logger.info(f"Rotating endpoint after {self.requests_since_rotation} requests")
            self._select_best_endpoint()

    def _is_rate_limit_error(self, error_message: str) -> bool:
        """
        Check if an error message indicates a rate limit issue.

        Args:
            error_message: The error message to check

        Returns:
            bool: True if it's a rate limit error
        """
        error_lower = str(error_message).lower()
        for keyword in self.rate_limit_keywords:
            if keyword.lower() in error_lower:
                return True
        return False

    def _handle_error(self, url: Optional[str], error: Exception) -> None:
        """
        Handle an error that occurred when using an endpoint.

        Args:
            url: The RPC URL that had an error
            error: The exception that occurred
        """
        # Handle case where url might be None
        if url is None:
            self.logger.warning("Received error for None URL, using current endpoint")
            url = self.current_endpoint

        # If still None after fallback, can't proceed
        if url is None:
            self.logger.error("Cannot handle error: No valid URL provided or available")
            return

        status = self.endpoint_status.get(url)
        if not status:
            self.logger.warning(f"No status information for URL {url}, cannot update error stats")
            return

        # Increment error counters
        status["consecutive_errors"] += 1
        status["failures"] += 1

        error_str = str(error)

        # Check if this is a rate limit error
        if self._is_rate_limit_error(error_str):
            self.logger.warning(f"Rate limit detected for endpoint {url}: {error_str}")
            status["rate_limited"] = True

            # Extract retry time if available
            retry_seconds = self.cooldown_period  # Default cooldown

            # Try to parse retry time from error message
            try:
                # Common formats: "retry in 10m0s", "retry after 60s", etc.
                if "retry in" in error_str or "retry after" in error_str:
                    parts = error_str.split("retry in" if "retry in" in error_str else "retry after")[1].strip().split()
                    total_seconds = 0

                    for part in parts:
                        if part.endswith('m'):
                            total_seconds += int(part[:-1]) * 60  # minutes
                        elif part.endswith('s'):
                            total_seconds += int(part[:-1])  # seconds
                        elif part.endswith('h'):
                            total_seconds += int(part[:-1]) * 3600  # hours

                    if total_seconds > 0:
                        retry_seconds = total_seconds
                        self.logger.info(f"Parsed retry time from error message: {retry_seconds} seconds")
            except Exception as e:
                self.logger.debug(f"Could not parse retry time from error message: {e}")

            # Set cooldown period
            status["rate_limit_until"] = time.time() + retry_seconds
            self.logger.info(f"Endpoint {url} will be rate-limited for {retry_seconds} seconds")
        elif status["consecutive_errors"] >= self.max_failures:
            # Too many consecutive errors, mark as inactive temporarily
            self.logger.warning(f"Endpoint {url} has {status['consecutive_errors']} consecutive errors, marking as inactive")
            status["active"] = False
            status["rate_limit_until"] = time.time() + self.cooldown_period  # Use standard cooldown

    def _handle_success(self, url: Optional[str]) -> None:
        """
        Handle a successful operation with an endpoint.

        Args:
            url: The RPC URL that succeeded
        """
        # Handle case where url might be None
        if url is None:
            self.logger.warning("Received success for None URL, using current endpoint")
            url = self.current_endpoint

        # If still None after fallback, can't proceed
        if url is None:
            self.logger.error("Cannot handle success: No valid URL provided or available")
            return

        status = self.endpoint_status.get(url)
        if not status:
            self.logger.warning(f"No status information for URL {url}, cannot update stats")
            return

        status["consecutive_errors"] = 0
        status["successful_requests"] += 1
        status["last_success"] = time.time()
        status["total_requests"] += 1

        # If previously inactive, mark as active again
        if not status["active"]:
            self.logger.info(f"Endpoint {url} is working again, marking as active")
            status["active"] = True

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a Web3 function with automatic retry, RPC fallback, and performance tracking.

        Args:
            func: The function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Any: Function result

        Raises:
            Exception: If all retries and fallbacks fail
        """
        if not self.current_web3 or not self.current_endpoint:
            self._select_best_endpoint()
            if not self.current_web3:
                raise ValueError("No working RPC endpoint available")

        self._rotate_if_needed()

        # Track performance metrics
        start_time = time.time()
        current_url = self.current_endpoint

        # Try with current endpoint
        try:
            result: str = func(*args, **kwargs)

            # Record performance metrics
            response_time_ms = (time.time() - start_time) * 1000
            if current_url is not None:
                self._record_performance_metrics(current_url, True, response_time_ms)

            self._handle_success(current_url)
            return result
        except Exception as e:
            # Record performance metrics for failure
            response_time_ms = (time.time() - start_time) * 1000
            if current_url is not None:
                self._record_performance_metrics(current_url, False, response_time_ms)

            self._handle_error(current_url, e)
            self.logger.warning(f"Error with endpoint {current_url}: {e}")

            # Try other endpoints with retries
            for retry in range(self.max_retries):
                # Select a new endpoint
                if not self._select_best_endpoint():
                    raise ValueError("No working RPC endpoints available after retries")

                # Reset timer for the retry
                retry_start_time = time.time()
                retry_url = self.current_endpoint

                try:
                    self.logger.info(f"Retry {retry+1}/{self.max_retries} with endpoint {retry_url}")
                    result: str = func(*args, **kwargs)

                    # Record performance metrics for successful retry
                    retry_response_time_ms = (time.time() - retry_start_time) * 1000
                    if retry_url is not None:
                        self._record_performance_metrics(retry_url, True, retry_response_time_ms)

                    self._handle_success(retry_url)
                    return result
                except Exception as retry_error:
                    # Record performance metrics for failed retry
                    retry_response_time_ms = (time.time() - retry_start_time) * 1000
                    if retry_url is not None:
                        self._record_performance_metrics(retry_url, False, retry_response_time_ms)

                    self._handle_error(retry_url, retry_error)
                    self.logger.warning(f"Retry {retry+1} failed with endpoint {retry_url}: {retry_error}")

                    # Use exponential backoff with jitter for more efficient retries
                    backoff_time = self.retry_delay * (2 ** retry)
                    import secrets
                    # Use cryptographically secure random for jitter (0-10%)
                    jitter = (secrets.randbelow(1000) / 10000.0) * backoff_time  # Add up to 10% jitter
                    time.sleep(backoff_time + jitter)

            # If we get here, all retries failed
            raise Exception(f"All retries failed across {len(self.rpc_urls)} endpoints")

    def _record_performance_metrics(self, url: str, success: bool, response_time_ms: float) -> None:
        """
        Record performance metrics for an endpoint.

        Args:
            url: The RPC URL
            success: Whether the request was successful
            response_time_ms: Response time in milliseconds
        """
        if not self.performance_tracking_enabled or url is None:
            return

        status = self.endpoint_status.get(url)
        if not status:
            return

        # Update last updated timestamp
        status["last_updated"] = time.time()

        # Add response time to the list, keeping only the most recent ones
        status["response_times"].append(response_time_ms)
        if len(status["response_times"]) > self.performance_window_size:
            status["response_times"].pop(0)

        # Update average response time
        if status["response_times"]:
            status["avg_response_time"] = sum(status["response_times"]) / len(status["response_times"])

        # Update success rate based on this request
        if success:
            status["successful_requests"] += 1
        status["total_requests"] += 1

        # Recalculate success rate
        if status["total_requests"] > 0:
            status["success_rate"] = status["successful_requests"] / status["total_requests"]

        # Log extreme response times
        if response_time_ms > self.latency_threshold_ms:
            self.logger.warning(f"Slow response from {url}: {response_time_ms:.2f}ms")

    def get_web3(self) -> Optional[Any]:
        """
        Get the current Web3 instance.

        Returns:
            Web3: The current Web3 instance or None if not connected
        """
        if not WEB3_IMPORTED:
            self.logger.error("Web3 not imported")
            return None
            
        if not self.current_web3:
            self._select_best_endpoint()
        return self.current_web3

    def is_connected(self) -> bool:
        """
        Check if connected to the blockchain.

        Returns:
            bool: True if connected
        """
        web3 = self.get_web3()
        if not web3:
            return False

        try:
            return web3.is_connected()
        except Exception as e:
            self.logger.warning(f"Error checking connection: {e}")
            return False

    def get_transaction_receipt(self, tx_hash: Union[str, bytes]) -> Dict[str, Any]:
        """
        Get transaction receipt with retry logic and RPC fallback.

        Args:
            tx_hash: Transaction hash

        Returns:
            dict: Transaction receipt
        """
        web3 = self.get_web3()
        if not web3:
            raise ValueError("Web3 is not initialized")

        return self.execute_with_retry(web3.eth.get_transaction_receipt, tx_hash)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for all endpoints.

        Returns:
            Dict[str, Any]: Performance metrics for all endpoints
        """
        metrics = {}

        for url, status in self.endpoint_status.items():
            if status["total_requests"] > 0:
                metrics[url] = {
                    "avg_response_time_ms": status["avg_response_time"],
                    "success_rate": status["success_rate"],
                    "performance_score": status.get("performance_score", 0),
                    "total_requests": status["total_requests"],
                    "successful_requests": status["successful_requests"],
                    "active": status["active"],
                    "rate_limited": status["rate_limited"],
                    "last_updated": status["last_updated"]
                }

        # Add overall metrics
        total_requests = sum(status["total_requests"] for status in self.endpoint_status.values())
        successful_requests = sum(status["successful_requests"] for status in self.endpoint_status.values())

        metrics["overall"] = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 1.0,
            "active_endpoints": sum(1 for status in self.endpoint_status.values() if status["active"]),
            "total_endpoints": len(self.endpoint_status),
            "current_endpoint": self.current_endpoint
        }

        return metrics

    def wait_for_transaction_receipt(self, tx_hash: Union[str, bytes], timeout: int = 600, poll_interval: float = 0.5) -> Dict[str, Any]:
        """
        Wait for transaction receipt with enhanced reliability.

        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds
            poll_interval: Poll interval in seconds

        Returns:
            dict: Transaction receipt
        """
        web3 = self.get_web3()
        if not web3:
            raise ValueError("Web3 is not initialized")

        # Format tx_hash for logging
        tx_hash_str = str(tx_hash)
        if isinstance(tx_hash, bytes):
            try:
                tx_hash_str = '0x' + tx_hash.hex()
            except (AttributeError, TypeError):
                tx_hash_str = str(tx_hash)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                receipt = self.execute_with_retry(web3.eth.get_transaction_receipt, tx_hash)
                if receipt:
                    return receipt
                time.sleep(poll_interval)
            except Exception as e:
                self.logger.warning(f"Error waiting for receipt: {e}, will retry")
                # Don't sleep here as execute_with_retry already has backoff

        raise TimeoutError(f"Transaction {tx_hash_str} not mined within {timeout} seconds")

    def get_chain_id(self) -> int:
        """
        Get blockchain chain ID with fallback.

        Returns:
            int: Chain ID
        """
        web3 = self.get_web3()
        if not web3:
            raise ValueError("Web3 is not initialized")
        return self.execute_with_retry(lambda: web3.eth.chain_id)

    def get_block_number(self) -> int:
        """
        Get latest block number with fallback.

        Returns:
            int: Block number
        """
        web3 = self.get_web3()
        if not web3:
            raise ValueError("Web3 is not initialized")
        return self.execute_with_retry(lambda: web3.eth.block_number)

    def get_gas_price(self) -> int:
        """
        Get current gas price with fallback.

        Returns:
            int: Gas price in wei
        """
        web3 = self.get_web3()
        if not web3:
            raise ValueError("Web3 is not initialized")
        return self.execute_with_retry(lambda: web3.eth.gas_price)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of all RPC endpoints.

        Returns:
            dict: Status information
        """
        return {
            "current_endpoint": self.current_endpoint,
            "is_connected": self.is_connected(),
            "endpoints": self.endpoint_status
        }

    def _setup_middleware(self, w3: Any, endpoint: str):
        """Setup middleware for web3 instance"""
        if not WEB3_IMPORTED or not w3:
            return
            
        try:
            # Add POA middleware for Polygon compatibility
            poa_middleware = get_poa_middleware()
            if poa_middleware:
                inject_middleware(w3, poa_middleware, layer=0)
                self.logger.debug(f"Added POA middleware for {endpoint}")
        except Exception as e:
            self.logger.warning(f"Failed to add POA middleware for {endpoint}: {e}")
# Create a singleton instance
enhanced_rpc_manager = EnhancedRpcManager()
