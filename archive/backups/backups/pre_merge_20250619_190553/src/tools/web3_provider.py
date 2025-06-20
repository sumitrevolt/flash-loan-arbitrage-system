"""
Central Web3 provider module for the Flash Loan Arbitrage System.
This module provides a unified way to handle Web3 initialization, connections,
middleware, and common utility functions across the entire application.
"""

import logging
import os
import json
import time
import functools
from functools import lru_cache
from typing import Optional, Any, Dict, Callable, List

logger = logging.getLogger(__name__)

# Real Web3 import - no mock fallback, with version compatibility
try:
    from web3 import Web3
    from web3.types import TxParams, BlockIdentifier, Wei, TxReceipt, BlockData, HexStr
    from web3._utils.evm import Hash32  # Importing from the correct module
    from web3._utils.encoding import HexStr  # Correct import for HexStr
    ChecksumAddress = str  # robust fallback for all web3 versions
    from web3.exceptions import Web3Exception, ContractLogicError, TransactionNotFound

    # Simplified imports and fallbacks for HexStr and Hash32
    HexStr = str  # Direct fallback to str
    Hash32 = bytes  # Direct fallback to bytes

    # Middleware handling with Web3's Middleware type
    from web3.middleware import Middleware
    from typing import Callable, Any

    def geth_poa_middleware(make_request: Callable[[str, Any], Any], w3: Any) -> Middleware:
        raise NotImplementedError("geth_poa_middleware is not available in this Web3 version")

    def construct_sign_and_send_raw_middleware(private_key: str) -> Middleware:
        raise NotImplementedError("construct_sign_and_send_raw_middleware is not available in this Web3 version")

    # Updated type annotations
    from typing import Dict
    TxParams = Dict[str, Any]  # Simplified fallback for transaction parameters

    # Refined transaction handling
    def send_transaction(w3: Any, transaction: Dict[str, Any]) -> str:
        """
        Send a transaction and return its hash.

        Args:
            w3: Web3 instance
            transaction: Transaction dictionary

        Returns:
            Transaction hash as a string
        """
        if 'from' not in transaction:
            raise ValueError("Transaction must include a 'from' address")

        if 'gas' not in transaction:
            transaction['gas'] = w3.eth.estimate_gas(transaction)

        tx_hash = w3.eth.send_transaction(transaction)
        return tx_hash.hex()

    # Refined receipt handling
    def get_transaction_receipt(w3: Any, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        """
        Get the transaction receipt.

        Args:
            w3: Web3 instance
            tx_hash: Transaction hash
            timeout: Timeout in seconds

        Returns:
            Transaction receipt as a dictionary
        """
        return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)

    WEB3_IMPORTED = True
    logger.info("Web3 successfully imported")
except ImportError as e:
    logger.error(f"CRITICAL: Failed to import Web3: {e}")
    logger.error("Web3 is required for this application to function. Please install web3.py package.")
    raise ImportError(f"Web3 is required but not available: {e}")

def requires_web3(func: Callable[..., Any]) -> Callable[..., Optional[Any]]:
    """Decorator to check if Web3 is available before executing function"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Optional[Any]:
        if not WEB3_IMPORTED:
            logger.error(f"Web3 required for {func.__name__} but not available")
            return None
        return func(*args, **kwargs)
    return wrapper

def get_web3_instance(rpc_url: str, private_key: Optional[str] = None, apply_poa: bool = True) -> Optional[Web3]:
    """
    Get a Web3 instance configured with the specified RPC URL and optional private key.

    Args:
        rpc_url: The RPC URL to connect to
        private_key: Optional private key for transaction signing
        apply_poa: Whether to apply PoA middleware (for PoA chains)

    Returns:
        Configured Web3 instance or None if connection fails
    """
    try:
        # Create Web3 instance with HTTP provider
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))

        # Apply PoA middleware if requested and available
        if apply_poa and geth_poa_middleware:
            try:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                logger.debug(f"Applied PoA middleware to Web3 instance for {rpc_url}")
            except Exception as e:
                logger.warning(f"Error applying PoA middleware: {e}")
                # Try fallback middleware from our utility
                try:
                    from src.utils.web3_v7_middleware import get_compatible_middleware, apply_middleware as apply_v7_middleware
                    middleware = get_compatible_middleware()
                    if middleware:
                        apply_v7_middleware(w3, middleware, layer=0)
                        logger.debug(f"Applied compatible middleware to Web3 instance for {rpc_url}")
                except ImportError:
                    logger.warning("Could not apply PoA middleware - compatibility issues may occur")
                except Exception as e2:
                    logger.warning(f"Error applying fallback PoA middleware: {e2}")
        elif apply_poa:
            logger.warning("PoA middleware requested but not available in this Web3.py version")

        # Add signing middleware if private key is provided and available
        if private_key and construct_sign_and_send_raw_middleware:
            try:
                w3.middleware_onion.add(construct_sign_and_send_raw_middleware(private_key))
                logger.debug("Applied transaction signing middleware")
            except Exception as e:
                logger.warning(f"Error applying signing middleware: {e}")
        elif private_key:
            logger.warning("Transaction signing middleware requested but not available")

        # Verify connection
        if not w3.is_connected():
            logger.error(f"Could not connect to {rpc_url}")
            return None

        logger.info(f"Successfully connected to {rpc_url}")
        return w3
    except Exception as e:
        logger.error(f"Error creating Web3 instance: {e}")
        return None

def validate_web3_connection(w3: Web3) -> bool:
    """
    Validate that a Web3 instance is properly connected and functional.

    Args:
        w3: Web3 instance to validate

    Returns:
        True if connection is valid, False otherwise
    """
    try:
        if not w3.is_connected():
            return False

        # Try to get latest block number as a connectivity test
        block_number = w3.eth.block_number
        logger.debug(f"Web3 connection validated - latest block: {block_number}")
        return True
    except Exception as e:
        logger.error(f"Web3 connection validation failed: {e}")
        return False

def get_chain_id(w3: Web3) -> Optional[int]:
    """
    Get the chain ID from a Web3 instance.

    Args:
        w3: Web3 instance

    Returns:
        Chain ID or None if unable to retrieve
    """
    try:
        return w3.eth.chain_id
    except Exception as e:
        logger.error(f"Error getting chain ID: {e}")
        return None

def format_address(address: str) -> str:
    """
    Format an address to checksum format.

    Args:
        address: Address to format

    Returns:
        Checksum formatted address
    """
    try:
        return Web3.to_checksum_address(address)
    except Exception as e:
        logger.error(f"Error formatting address {address}: {e}")
        return address

def to_checksum_address(address: str) -> str:
    """
    Convert an address to checksum format.

    Args:
        address: Address to convert

    Returns:
        Checksum formatted address
    """
    return format_address(address)

def wei_to_ether(wei_amount: int) -> float:
    """
    Convert Wei to Ether.

    Args:
        wei_amount: Amount in Wei

    Returns:
        Amount in Ether
    """
    return Web3.from_wei(wei_amount, 'ether')

def ether_to_wei(ether_amount: float) -> int:
    """
    Convert Ether to Wei.

    Args:
        ether_amount: Amount in Ether

    Returns:
        Amount in Wei
    """
    return Web3.to_wei(ether_amount, 'ether')

def get_gas_price(w3: Web3) -> Optional[int]:
    """
    Get current gas price from the network.

    Args:
        w3: Web3 instance

    Returns:
        Gas price in Wei or None if unable to retrieve
    """
    try:
        return w3.eth.gas_price
    except Exception as e:
        logger.error(f"Error getting gas price: {e}")
        return None

def estimate_gas(w3: Web3, transaction: Dict[str, Any]) -> Optional[int]:
    """
    Estimate gas for a transaction.

    Args:
        w3: Web3 instance
        transaction: Transaction dictionary

    Returns:
        Estimated gas or None if estimation fails
    """
    try:
        return w3.eth.estimate_gas(transaction)
    except Exception as e:
        logger.error(f"Error estimating gas: {e}")
        return None

def get_account_balance(w3: Web3, address: str) -> Optional[float]:
    """
    Get account balance in Ether.

    Args:
        w3: Web3 instance
        address: Account address

    Returns:
        Balance in Ether or None if unable to retrieve
    """
    try:
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        return wei_to_ether(balance_wei)
    except Exception as e:
        logger.error(f"Error getting balance for {address}: {e}")
        return None

def get_transaction_receipt(w3: Web3, tx_hash: HexStr, timeout: int = 120) -> Optional[TxReceipt]:
    """
    Fetch the transaction receipt for a given transaction hash.

    Args:
        w3: Web3 instance
        tx_hash: Transaction hash
        timeout: Timeout in seconds

    Returns:
        Transaction receipt or None if not found
    """
    return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)

def get_contract_instance(w3: Web3, address: str, abi: List[Dict[str, Any]]) -> Optional[Any]:
    """
    Get a contract instance given its address and ABI.

    Args:
        w3: Web3 instance
        address: Contract address
        abi: Contract ABI

    Returns:
        Contract instance or None if creation fails
    """
    checksum_address = Web3.to_checksum_address(address)  # Use Web3's static method
    return w3.eth.contract(address=checksum_address, abi=abi)

def load_contract_abi(abi_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load contract ABI from file.

    Args:
        abi_path: Path to ABI file

    Returns:
        Contract ABI or None if loading fails
    """
    try:
        with open(abi_path, 'r') as abi_file:
            return json.load(abi_file)
    except Exception as e:
        logger.error(f"Error loading ABI from {abi_path}: {e}")
        return None

def get_block_info(w3: Web3, block_identifier: BlockIdentifier = 'latest') -> Optional[BlockData]:
    """
    Fetch block information for a given block identifier.

    Args:
        w3: Web3 instance
        block_identifier: Block number, hash, or 'latest'

    Returns:
        Block information or None if unable to retrieve
    """
    return w3.eth.get_block(block_identifier)

def send_transaction(w3: Any, transaction: Dict[str, Any]) -> str:
    """
    Send a transaction and return its hash.

    Args:
        w3: Web3 instance
        transaction: Transaction dictionary

    Returns:
        Transaction hash as a string
    """
    if 'from' not in transaction:
        raise ValueError("Transaction must include a 'from' address")

    if 'gas' not in transaction:
        transaction['gas'] = w3.eth.estimate_gas(transaction)

    tx_hash = w3.eth.send_transaction(transaction)
    return tx_hash.hex()

def build_transaction(w3: Web3, from_address: str, to_address: str, value: int = 0,
                     gas_limit: Optional[int] = None, gas_price: Optional[int] = None,
                     data: str = '0x', nonce: Optional[int] = None) -> Dict[str, Any]:
    """
    Build a transaction dictionary.

    Args:
        w3: Web3 instance
        from_address: Sender address
        to_address: Recipient address
        value: Value in Wei
        gas_limit: Gas limit
        gas_price: Gas price in Wei
        data: Transaction data
        nonce: Transaction nonce

    Returns:
        Transaction dictionary
    """
    try:
        transaction = {
            'from': Web3.to_checksum_address(from_address),
            'to': Web3.to_checksum_address(to_address),
            'value': value,
            'data': data,
        }

        if nonce is None:
            transaction['nonce'] = w3.eth.get_transaction_count(Web3.to_checksum_address(from_address))
        else:
            transaction['nonce'] = nonce

        if gas_price is None:
            transaction['gasPrice'] = w3.eth.gas_price
        else:
            transaction['gasPrice'] = gas_price

        if gas_limit is None:
            try:
                transaction['gas'] = w3.eth.estimate_gas(transaction)
            except Exception:
                transaction['gas'] = 21000  # Default gas limit
        else:
            transaction['gas'] = gas_limit

        return transaction
    except Exception as e:
        logger.error(f"Error building transaction: {e}")
        return {}

def is_transaction_successful(receipt: Dict[str, Any]) -> bool:
    """
    Check if a transaction was successful based on its receipt.

    Args:
        receipt: Transaction receipt

    Returns:
        True if transaction was successful, False otherwise
    """
    return receipt.get('status', 0) == 1

def get_transaction_cost(receipt: Dict[str, Any]) -> Optional[float]:
    """
    Calculate the cost of a transaction in Ether.

    Args:
        receipt: Transaction receipt

    Returns:
        Transaction cost in Ether or None if calculation fails
    """
    gas_used = receipt.get('gasUsed', 0)
    gas_price = receipt.get('effectiveGasPrice', 0)
    cost_wei = gas_used * gas_price
    return float(Web3.from_wei(cost_wei, 'ether')) if isinstance(cost_wei, int) else None

def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Retry a function on failure up to max_retries times.

    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds

    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                        raise
        return wrapper
    return decorator

@lru_cache(maxsize=10)
def get_cached_web3_instance(rpc_url: str, apply_poa: bool = True) -> Optional[Web3]:
    """
    Get a cached Web3 instance for the given RPC URL.

    Args:
        rpc_url: The RPC URL to connect to
        apply_poa: Whether to apply PoA middleware

    Returns:
        Cached Web3 instance or None if connection fails
    """
    return get_web3_instance(rpc_url, apply_poa=apply_poa)

def clear_web3_cache():
    """Clear the cached Web3 instances."""
    get_cached_web3_instance.cache_clear()
    logger.info("Web3 instance cache cleared")

class Web3Manager:
    """
    Manager class for handling multiple Web3 connections and providing
    unified access to Web3 functionality.
    """

    def __init__(self):
        self.connections: Dict[str, Web3] = {}
        self.default_connection: Optional[Web3] = None
        self.private_key: Optional[str] = None

    def add_connection(self, name: str, rpc_url: str, private_key: Optional[str] = None,
                      apply_poa: bool = True, set_as_default: bool = False) -> bool:
        """
        Add a new Web3 connection.

        Args:
            name: Connection name
            rpc_url: RPC URL
            private_key: Optional private key
            apply_poa: Whether to apply PoA middleware
            set_as_default: Whether to set as default connection

        Returns:
            True if connection was added successfully, False otherwise
        """
        w3 = get_web3_instance(rpc_url, private_key, apply_poa)
        if w3:
            self.connections[name] = w3
            if set_as_default or not self.default_connection:
                self.default_connection = w3
                self.private_key = private_key
            logger.info(f"Added Web3 connection '{name}' for {rpc_url}")
            return True
        else:
            logger.error(f"Failed to add Web3 connection '{name}' for {rpc_url}")
            return False

    def get_connection(self, name: Optional[str] = None) -> Optional[Web3]:
        """
        Get a Web3 connection by name or default.

        Args:
            name: Connection name (None for default)

        Returns:
            Web3 instance or None if not found
        """
        if name is None:
            return self.default_connection
        return self.connections.get(name)

    def remove_connection(self, name: str) -> bool:
        """
        Remove a Web3 connection.

        Args:
            name: Connection name

        Returns:
            True if connection was removed, False if not found
        """
        if name in self.connections:
            del self.connections[name]
            if self.default_connection == self.connections.get(name):
                self.default_connection = next(iter(self.connections.values())) if self.connections else None
            logger.info(f"Removed Web3 connection '{name}'")
            return True
        return False

    def validate_all_connections(self) -> Dict[str, bool]:
        """
        Validate all Web3 connections.

        Returns:
            Dictionary mapping connection names to validation results
        """
        results = {}
        for name, w3 in self.connections.items():
            results[name] = validate_web3_connection(w3)
        return results

    def get_connection_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all connections.

        Returns:
            Dictionary with connection information
        """
        info = {}
        for name, w3 in self.connections.items():
            try:
                chain_id = get_chain_id(w3)
                block_number = w3.eth.block_number if w3.is_connected() else None
                info[name] = {
                    'connected': w3.is_connected(),
                    'chain_id': chain_id,
                    'latest_block': block_number,
                    'is_default': w3 == self.default_connection
                }
            except Exception as e:
                info[name] = {
                    'connected': False,
                    'error': str(e),
                    'is_default': w3 == self.default_connection
                }
        return info

# Global Web3 manager instance
web3_manager = Web3Manager()

def get_default_web3() -> Optional[Web3]:
    """Get the default Web3 instance from the manager."""
    return web3_manager.get_connection()

def setup_web3_from_env() -> bool:
    """
    Setup Web3 connections from environment variables.

    Expected environment variables:
    - WEB3_RPC_URL: Primary RPC URL
    - WEB3_PRIVATE_KEY: Private key for transactions
    - WEB3_APPLY_POA: Whether to apply PoA middleware (default: true)

    Returns:
        True if setup was successful, False otherwise
    """
    try:
        rpc_url = os.getenv('WEB3_RPC_URL')
        if not rpc_url:
            logger.warning("WEB3_RPC_URL environment variable not set")
            return False

        private_key = os.getenv('WEB3_PRIVATE_KEY')
        apply_poa = os.getenv('WEB3_APPLY_POA', 'true').lower() == 'true'

        success = web3_manager.add_connection(
            name='default',
            rpc_url=rpc_url,
            private_key=private_key,
            apply_poa=apply_poa,
            set_as_default=True
        )

        if success:
            logger.info("Web3 setup from environment variables completed successfully")
        else:
            logger.error("Failed to setup Web3 from environment variables")

        return success
    except Exception as e:
        logger.error(f"Error setting up Web3 from environment: {e}")
        return False

# Initialize Web3 from environment variables on module import
if os.getenv('AUTO_SETUP_WEB3', 'false').lower() == 'true':
    setup_web3_from_env()

__all__ = [
    'Web3Manager', 'web3_manager', 'get_default_web3', 'setup_web3_from_env',
    'get_web3_instance', 'validate_web3_connection', 'get_chain_id', 'format_address',
    'to_checksum_address', 'wei_to_ether', 'ether_to_wei', 'get_gas_price', 'estimate_gas',
    'get_account_balance', 'get_transaction_receipt', 'get_contract_instance', 'load_contract_abi',
    'get_block_info', 'send_transaction', 'build_transaction', 'is_transaction_successful',
    'get_transaction_cost', 'retry_on_failure', 'get_cached_web3_instance', 'clear_web3_cache',
    'requires_web3', 'Web3', 'TxParams', 'BlockIdentifier', 'Hash32', 'Wei', 'ChecksumAddress',
    'HexStr', 'WEB3_IMPORTED', 'Web3Exception', 'ContractLogicError', 'TransactionNotFound'
]
