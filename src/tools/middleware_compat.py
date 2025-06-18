"""
Web3 middleware compatibility utilities for different versions of web3.py
All middleware functions are centralized here to avoid redundancy.
"""

import logging
from typing import Callable, Any, Optional, Dict, cast

# Import from the central provider to avoid duplication
from src.utils.web3_provider import WEB3_IMPORTED, Web3, RPCEndpoint, RPCResponse

logger = logging.getLogger(__name__)

def construct_sign_and_send_raw_middleware(private_key: str) -> Optional[Callable]:
    """
    Construct signing middleware compatible with different web3.py versions
    
    Args:
        private_key: Private key for signing transactions
        
    Returns:
        Middleware function or None if creation fails
    """
    if not WEB3_IMPORTED:
        logger.error("Web3 not imported, cannot create signing middleware")
        return None
        
    try:
        from eth_account import Account
        from eth_account.signers.local import LocalAccount
        
        account = Account.from_key(private_key)
        
        def signing_middleware(make_request: Callable[[RPCEndpoint, Any], RPCResponse],
                             w3: Web3) -> Callable[[RPCEndpoint, Any], RPCResponse]:
            def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
                if method == "eth_sendTransaction":
                    # Sign the transaction
                    transaction = params[0]
                    if 'from' in transaction and transaction['from'].lower() == account.address.lower():
                        # Add missing fields
                        if 'nonce' not in transaction:
                            transaction['nonce'] = w3.eth.get_transaction_count(account.address)
                        if 'gasPrice' not in transaction and 'maxFeePerGas' not in transaction:
                            transaction['gasPrice'] = w3.eth.gas_price
                        if 'gas' not in transaction:
                            transaction['gas'] = 2000000  # Default gas limit
                        
                        # Sign transaction
                        signed_txn = account.sign_transaction(transaction)
                        
                        # Send raw transaction
                        return make_request(
                            cast(RPCEndpoint, "eth_sendRawTransaction"),
                            [signed_txn.raw_transaction.hex()]
                        )
                return make_request(method, params)
            return middleware
        
        return signing_middleware
        
    except Exception as e:
        logger.error(f"Error creating signing middleware: {e}")
        return None

def get_poa_middleware():
    """
    Get POA middleware compatible with different web3.py versions
    
    Returns:
        POA middleware or None if not available
    """
    if not WEB3_IMPORTED:
        logger.warning("Web3 not imported, cannot get POA middleware")
        return None
        
    try:
        # Try import path for Web3.py v7+
        from web3.middleware import ExtraDataToPOAMiddleware
        logger.debug("Using ExtraDataToPOAMiddleware")
        return ExtraDataToPOAMiddleware
    except ImportError:
        try:
            # Try legacy import path
            from web3.middleware import geth_poa_middleware
            logger.debug("Using geth_poa_middleware")
            return geth_poa_middleware
        except ImportError:
            # In case middleware is entirely unavailable 
            logger.warning("No POA middleware found")
            return None

def apply_geth_poa_middleware(w3: Web3) -> None:
    """
    Apply Geth POA middleware for networks that use Proof of Authority.
    Compatible with Web3.py v7+
    
    Args:
        w3: Web3 instance to apply middleware to
    """
    if not WEB3_IMPORTED:
        logger.warning("Web3 not imported, cannot apply POA middleware")
        return
        
    # Dynamically resolve geth_poa_middleware 
    try:
        import importlib
        mw_mod = importlib.import_module('web3.middleware')
        geth_poa = getattr(mw_mod, 'geth_poa_middleware', None)
        if geth_poa and hasattr(w3, 'middleware_onion'):
            w3.middleware_onion.inject(geth_poa, layer=0)
            logger.debug("Successfully applied geth_poa_middleware")
            return
    except Exception:
        pass
    
    # Try alternative POA middleware
    try:
        import importlib
        mw_mod = importlib.import_module('web3.middleware')
        alt = getattr(mw_mod, 'ExtraDataToPOAMiddleware', None)
        if alt and hasattr(w3, 'middleware_onion'):
            w3.middleware_onion.inject(alt, layer=0)
            logger.debug("Successfully applied ExtraDataToPOAMiddleware")
            return
    except Exception as e:
        logger.warning(f"Could not apply POA middleware: {e}")
        return
        
    logger.warning("No POA middleware available in this web3 version.")

def apply_web3_middleware(w3):
    """
    Apply appropriate middleware to a Web3 instance.
    This is a simplified approach to quickly apply the right middleware.
    
    Args:
        w3: Web3 instance to apply middleware to
    """
    if not WEB3_IMPORTED or w3 is None:
        logger.warning("Cannot apply middleware - Web3 not imported or instance is None")
        return
        
    # Dynamically resolve POA middleware
    try:
        import importlib
        mw_mod = importlib.import_module('web3.middleware')
        geth_poa = getattr(mw_mod, 'geth_poa_middleware', None)
        if geth_poa and hasattr(w3, 'middleware_onion'):
            w3.middleware_onion.inject(geth_poa, layer=0)
            return
    except Exception:
        pass
        
    try:
        import importlib
        mw_mod = importlib.import_module('web3.middleware')
        alt = getattr(mw_mod, 'ExtraDataToPOAMiddleware', None)
        if alt and hasattr(w3, 'middleware_onion'):
            w3.middleware_onion.inject(alt, layer=0)
            logger.debug("Successfully applied ExtraDataToPOAMiddleware")
            return
    except Exception as e:
        logger.warning(f"Could not apply POA middleware: {e}")
        return
        
    logger.warning("No POA middleware available in this web3 version.")

def construct_exception_handler_middleware(
    error_handlers: Dict[RPCEndpoint, Any]
) -> Any:
    """
    Construct exception handler middleware.
    This is a compatibility function for Web3 v7+
    
    Args:
        error_handlers: Dictionary mapping RPC methods to error handler functions
        
    Returns:
        Middleware function
    """
    def exception_handler_middleware(
        make_request, w3: Web3
    ) -> Any:
        def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
            try:
                return make_request(method, params)
            except Exception as e:
                if method in error_handlers:
                    error_handler = error_handlers[method]
                    return error_handler(e)
                raise
        return middleware
    
    return exception_handler_middleware

def apply_poa_middleware(w3: Web3) -> None:
    """
    Apply POA middleware with proper error handling for different Web3 versions.
    This function provides a unified interface for applying POA middleware.
    
    Args:
        w3: Web3 instance to apply middleware to
    """
    if not WEB3_IMPORTED or w3 is None:
        logger.warning("Cannot apply middleware - Web3 not imported or instance is None")
        return
        
    # Dynamically resolve and apply POA middleware
    try:
        import importlib
        mw_mod = importlib.import_module('web3.middleware')
        geth_poa = getattr(mw_mod, 'geth_poa_middleware', None)
        if geth_poa and hasattr(w3, 'middleware_onion'):
            w3.middleware_onion.inject(geth_poa, layer=0)
            logger.debug("Successfully applied geth_poa_middleware")
            return
    except Exception as e:
        logger.debug(f"geth_poa_middleware not available: {e}")
        
    try:
        import importlib
        mw_mod = importlib.import_module('web3.middleware')
        alt = getattr(mw_mod, 'ExtraDataToPOAMiddleware', None)
        if alt and hasattr(w3, 'middleware_onion'):
            w3.middleware_onion.inject(alt, layer=0)
            logger.debug("Successfully applied ExtraDataToPOAMiddleware")
            return
    except Exception as e:
        logger.warning(f"Could not apply POA middleware: {e}")
        
    logger.warning("No POA middleware available in this web3 version.")

# Alias for backward compatibility
Middleware = Callable[[Callable[[RPCEndpoint, Any], RPCResponse], Web3], Callable[[RPCEndpoint, Any], RPCResponse]]

# Correct the method for converting to checksum address
def convert_to_checksum_address(address: str) -> str:
    """
    Convert an Ethereum address to a checksum address.
    This is a compatibility function that works with all Web3.py versions.
    
    Args:
        address: Ethereum address to convert
        
    Returns:
        Checksum address
    """
    if not WEB3_IMPORTED:
        logger.warning("Web3 not imported, returning address as is")
        return address
        
    from web3 import Web3
    return Web3.to_checksum_address(address)
