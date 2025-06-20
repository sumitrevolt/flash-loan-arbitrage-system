"""
Middleware utilities for Web3.py compatibility across different versions.
This module provides a unified way to import and use middleware components
that may have different import paths in different versions of Web3.py.
"""
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3


import logging
from functools import lru_cache
# Import from central web3_provider
from src.utils.web3_provider import Web3
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware
WEB3_IMPORTED = True


logger = logging.getLogger("middleware_utils")

# Custom PoA middleware for compatibility
def custom_poa_middleware(make_request, web3):
    """
    Custom middleware for PoA chains when ExtraDataToPOAMiddleware is not available.
    This is a fallback implementation that handles ExtraDataLengthError.
    
    Args:
        make_request: The make_request function from web3
        web3: The Web3 instance
        
    Returns:
        A middleware function
    """
    try:
        
        def middleware(method, params):
            try:
                return make_request(method, params)
            except ExtraDataLengthError:
                return None
        return middleware
    except ImportError as e:
        logger.warning(f"Failed to create custom PoA middleware: {e}")
        # Return a pass-through middleware if we can't create the proper one
        return lambda request_method, params: make_request(request_method, params)

# Cache the middleware resolution - only run once
@lru_cache(maxsize=1)
def _resolve_poa_middleware():
    """
    Resolve the correct PoA middleware based on the web3.py version.
    Uses caching to prevent repeated import attempts and warnings.
    
    Returns:
        tuple: (middleware_function, is_native_middleware)
    """
    try:
        return ExtraDataToPOAMiddleware, True
    except Exception as e:
        logger.warning(f"Could not resolve PoA middleware: {e}")
        return custom_poa_middleware, False

def get_poa_middleware():
    """
    Get PoA middleware with fallbacks for different web3.py versions.
    This is the main function that should be used by other modules.
    
    Returns:
        function: The middleware function to use
    """
    middleware, is_native = _resolve_poa_middleware()
    return middleware

def apply_poa_middleware(web3_instance):
    """
    Apply PoA middleware to a Web3 instance.
    This is a convenience function that applies the middleware to the instance.
    
    Args:
        web3_instance: The Web3 instance to apply middleware to
        
    Returns:
        bool: True if middleware was applied successfully, False otherwise
    """
    try:
        middleware, is_native = _resolve_poa_middleware()
        web3_instance.middleware_onion.inject(middleware, layer=0)
        logger.info(f"Applied {'native' if is_native else 'custom'} PoA middleware to Web3 instance")
        return True
    except Exception as e:
        logger.warning(f"Failed to apply PoA middleware: {e}")
        return False
