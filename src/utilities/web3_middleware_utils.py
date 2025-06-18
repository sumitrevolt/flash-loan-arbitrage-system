"""
Utility module for standardized Web3 middleware handling.
This module provides a consistent way to apply PoA middleware across all Web3 instances,
handling different versions of web3.py and providing fallbacks.
"""

import logging
from typing import Any, Optional
from functools import lru_cache

# Import from central web3_provider to prevent duplication
from src.utils.web3_provider import WEB3_IMPORTED

logger = logging.getLogger(__name__)

def apply_web3_middleware(w3: Any, middleware: Optional[Any] = None) -> None:
    """
    Apply appropriate middleware to a Web3 instance based on Web3.py version.
    This function tries different import paths for the middleware based on the web3.py version
    and provides fallbacks for compatibility across versions.
    
    Args:
        w3: Web3 instance to apply middleware to
        middleware: Optional middleware to apply (if not provided, will attempt to find compatible one)
    """
    if w3 is None:
        logger.warning("Cannot apply middleware to None Web3 instance")
        return
        
    try:
        # Use provided middleware or try to find a compatible one
        if middleware is None:
            try:
                # Try our custom middleware first
                from src.utils.web3_v7_middleware import get_compatible_middleware
                middleware = get_compatible_middleware()
                if middleware is None:
                    # Fall back to standard geth_poa_middleware
                    try:
                        from web3.middleware import geth_poa_middleware
                        middleware = geth_poa_middleware
                    except ImportError:
                        logger.warning("Could not find any middleware to apply")
                        return
            except ImportError:
                # Try the standard middleware
                try:
                    from web3.middleware import geth_poa_middleware
                    middleware = geth_poa_middleware
                except ImportError:
                    logger.warning("Could not find any middleware to apply")
                    return
        
        # Apply middleware using the Web3 version's approach
        if hasattr(w3, 'middleware_onion') and hasattr(w3.middleware_onion, 'inject'):
            w3.middleware_onion.inject(middleware, layer=0)
            logger.debug("Applied middleware using middleware_onion.inject")
        elif hasattr(w3, 'middleware_stack') and hasattr(w3.middleware_stack, 'add'):
            w3.middleware_stack.add(middleware)
            logger.debug("Applied middleware using middleware_stack.add")
        else:
            logger.warning("No method found to apply middleware to Web3 instance")
    except Exception as e:
        logger.error(f"Error applying middleware: {str(e)}")
        # Continue without middleware - better than failing completely

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
        from web3.exceptions import ExtraDataLengthError
        
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
        from web3.middleware import ExtraDataToPOAMiddleware
        return ExtraDataToPOAMiddleware, True
    except ImportError:
        try:
            from web3.middleware import geth_poa_middleware
            return geth_poa_middleware, True
        except ImportError as e:
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
