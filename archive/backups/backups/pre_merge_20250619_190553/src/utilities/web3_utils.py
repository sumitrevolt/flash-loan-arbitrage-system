#!/usr/bin/env python3
"""
Web3 utility functions for the Flash Loan Arbitrage System.
Provides robust RPC connection management and address handling.
"""

import logging
import time
import json
from typing import Optional, Any

# Import from central web3_provider to avoid duplication
from src.utils.web3_provider import (
    Web3, Web3Exception, ContractLogicError, TransactionNotFound,
    WEB3_IMPORTED, requires_web3, TxParams, Wei, ChecksumAddress
)
from src.utils.middleware_compat import apply_poa_middleware

logger = logging.getLogger("web3_utils")

def to_checksum_address(address: str) -> str:
    """
    Convert a string address to a Web3 ChecksumAddress.

    Args:
        address (str): Ethereum address as string

    Returns:
        ChecksumAddress: Web3 ChecksumAddress
    """
    if not address:
        raise ValueError("Address cannot be empty")

    if not Web3.is_address(address):
        raise ValueError(f"Invalid Ethereum address format: {address}")

    return Web3.to_checksum_address(address)

def is_connected(provider) -> bool:
    """
    Check if a Web3 provider is connected.
    Compatible with all Web3.py versions.

    Args:
        provider: Web3 provider

    Returns:
        bool: True if connected, False otherwise
    """
    try:
        # Try the newer is_connected() method first
        if hasattr(provider, 'is_connected') and callable(provider.is_connected):
            # Explicitly cast to bool to satisfy type checker
            return bool(provider.is_connected())

        # For older Web3.py versions, check if we can get the block number
        if hasattr(provider, 'make_request'):
            response = provider.make_request('eth_blockNumber', [])
            return 'result' in response and response['result'] is not None

        return False
    except Exception as e:
        logger.error(f"Error checking connection: {e}")
        return False

def create_web3_instance(rpc_url: str) -> Optional[Web3]:
    """
    Create a Web3 instance with the given RPC URL.

    Args:
        rpc_url (str): RPC URL

    Returns:
        Web3: Web3 instance or None if failed
    """
    try:
        # Create Web3 instance
        if not WEB3_IMPORTED:

            logger.error("Web3 not available for Web3 connection")

            return None

        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))

        # Add POA middleware for Polygon
        add_middleware(w3)

        # Check connection
        if not is_connected(w3.provider):
            logger.error(f"Failed to connect to RPC URL: {rpc_url}")
            return None

        logger.info(f"Connected to RPC URL: {rpc_url}")
        return w3

    except Exception as e:
        logger.error(f"Error creating Web3 instance: {e}")
        return None

def add_middleware(w3: Web3) -> None:
    """
    Add necessary middleware to a Web3 instance.

    Args:
        w3 (Web3): Web3 instance
    """
    try:
        # Use the apply_poa_middleware function from middleware_compat
        apply_poa_middleware(w3)
        logger.info("Applied PoA middleware successfully")
    except Exception as e:
        logger.warning(f"Failed to apply PoA middleware: {e}")

def create_contract(w3: Web3, address: str, abi_path: str) -> Optional[Any]:
    """
    Create a contract instance.

    Args:
        w3 (Web3): Web3 instance
        address (str): Contract address
        abi_path (str): Path to ABI file

    Returns:
        Contract: Contract instance or None if failed
    """
    try:
        # Check if address is valid
        if not Web3.is_address(address):
            logger.error(f"Invalid contract address: {address}")
            return None

        # Convert to checksum address
        checksum_address = to_checksum_address(address)

        # Load ABI
        with open(abi_path, "r") as f:
            abi = json.load(f)

        # Create contract instance
        if not WEB3_IMPORTED:

            logger.error("Web3 not available for Contract instance")

            return None

        contract = w3.eth.contract(address=checksum_address, abi=abi)
        return contract

    except Exception as e:
        logger.error(f"Error creating contract: {e}")
        return None

class RpcConnectionManager:
    """
    Manages RPC connections with single primary RPC URL.
    """

    def __init__(self, primary_rpc_url: str, max_retries: int = 3, retry_delay: int = 5):
        """
        Initialize the RPC connection manager.

        Args:
            primary_rpc_url (str): Primary RPC URL
            max_retries (int): Maximum number of retries
            retry_delay (int): Delay between retries in seconds
        """
        self.primary_url = primary_rpc_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.w3 = None

        # Initialize Web3 instance
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the Web3 instance with the primary URL."""
        try:
            logger.info(f"Initializing Web3 with RPC URL: {self.primary_url}")
            self.w3 = Web3(Web3.HTTPProvider(self.primary_url, request_kwargs={'timeout': 30}))

            # Add POA middleware for Polygon
            add_middleware(self.w3)

            # Check connection
            if not self.ensure_connected():
                logger.error(f"Failed to connect to primary RPC URL: {self.primary_url}")

        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")

    def ensure_connected(self) -> bool:
        """
        Ensure that the Web3 instance is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        if not self.w3:
            logger.error("Web3 instance is not initialized")
            return False

        # Check connection
        if not is_connected(self.w3.provider):
            logger.error(f"Lost connection to primary RPC URL: {self.primary_url}")
            return False

        return True

    def get_web3(self) -> Optional[Web3]:
        """
        Get the Web3 instance.

        Returns:
            Web3: Web3 instance or None if not connected
        """
        if not self.ensure_connected():
            return None

        return self.w3

    def execute_with_retry(self, func, *args, **kwargs):
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Any: Function result
        """
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Ensure connection before executing
                if not self.ensure_connected():
                    logger.error("Not connected to RPC")
                    retry_count += 1
                    time.sleep(self.retry_delay)
                    continue

                # Execute function
                return func(*args, **kwargs)

            except Exception as e:
                logger.error(f"Error executing function: {e}")
                retry_count += 1

                if retry_count < self.max_retries:
                    logger.info(f"Retrying... ({retry_count}/{self.max_retries})")
                    time.sleep(self.retry_delay)

        logger.error(f"Failed to execute function after {self.max_retries} retries")
        return None

def setup_web3_with_middleware(
    rpc_url: str,
    private_key: Optional[str] = None,
    poa_network: bool = True
) -> Optional[Web3]:
    """
    Setup Web3 instance with appropriate middleware
    
    Args:
        rpc_url: RPC endpoint URL
        private_key: Private key for signing transactions
        poa_network: Whether this is a POA network
        
    Returns:
        Configured Web3 instance or None
    """
    try:
        if not WEB3_IMPORTED:

            logger.error("Web3 not available for Web3 connection")

            return None

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            logger.error(f"Failed to connect to {rpc_url}")
            return None
        
        # Apply POA middleware if needed
        if poa_network:
            apply_poa_middleware(w3)
        
        # Apply signing middleware if private key provided
        if private_key:
            try:
                from src.flash_loan.core.custom_middleware import CustomMiddleware
                signing_middleware = CustomMiddleware.create_signing_middleware(private_key)
                if signing_middleware and hasattr(w3.middleware_onion, 'inject'):
                    # Cast to proper type for inject method
                    w3.middleware_onion.inject(signing_middleware, layer=0)  # type: ignore
            except Exception as e:
                logger.warning(f"Could not apply signing middleware: {e}")
        
        return w3
        
    except Exception as e:
        logger.error(f"Error setting up Web3: {e}")
        return None
