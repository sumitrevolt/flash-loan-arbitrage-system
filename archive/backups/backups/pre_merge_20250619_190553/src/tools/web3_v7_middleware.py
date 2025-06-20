"""
Web3.py v7 compatible middleware for PoA chains like Polygon.
This module provides compatibility across different Web3.py versions.
"""

import logging
from typing import Optional, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)

try:
    from web3 import Web3
    from web3.types import RPCEndpoint, RPCResponse
    WEB3_AVAILABLE = True
except ImportError:
    logger.error("Web3 not available")
    WEB3_AVAILABLE = False

def get_compatible_middleware():
    """
    Get compatible PoA middleware for the current Web3.py version.
    
    Returns:
        Compatible middleware function or None if not available
    """
    if not WEB3_AVAILABLE:
        return None
    
    try:
        # Try newer Web3.py middleware (v6+)
        from web3.middleware import ExtraDataToPOAMiddleware
        logger.debug("Using ExtraDataToPOAMiddleware for Web3.py v6+")
        return ExtraDataToPOAMiddleware
    except ImportError:
        try:
            # Try older Web3.py middleware (v5)
            from web3.middleware import geth_poa_middleware
            logger.debug("Using geth_poa_middleware for Web3.py v5")
            return geth_poa_middleware
        except ImportError:
            # Create custom PoA middleware as fallback
            logger.debug("Creating custom PoA middleware fallback")
            return create_custom_poa_middleware()

def create_custom_poa_middleware():
    """
    Create a custom PoA middleware for handling extra data in block headers.
    This is a fallback when standard middleware is not available.
    """
    def poa_middleware(make_request: Callable[[str, Any], RPCResponse], w3: Web3) -> Callable[[str, Any], RPCResponse]:
        """
        Custom PoA middleware that handles extraData field in block headers.
        """
        @wraps(make_request)
        def middleware(method: str, params: Any) -> RPCResponse:
            response = make_request(method, params)
            
            # Handle block-related responses that might have extraData
            if method in ['eth_getBlockByHash', 'eth_getBlockByNumber'] and response.get('result'):
                block = response['result']
                if block and isinstance(block, dict):
                    # Ensure extraData field exists and is properly formatted
                    if 'extraData' in block:
                        extra_data = block['extraData']
                        if isinstance(extra_data, str) and len(extra_data) > 66:  # More than 32 bytes
                            # Truncate to 32 bytes for PoA compatibility
                            block['extraData'] = extra_data[:66]
                            logger.debug(f"Truncated extraData from {len(extra_data)} to 66 characters")
            
            return response
        
        return middleware
    
    return poa_middleware

def apply_middleware(w3: Web3, middleware, layer: int = 0):
    """
    Apply middleware to Web3 instance with error handling.
    
    Args:
        w3: Web3 instance
        middleware: Middleware function to apply
        layer: Layer position (0 = outermost)
    """
    try:
        if hasattr(w3, 'middleware_onion'):
            w3.middleware_onion.inject(middleware, layer=layer)
            logger.debug(f"Successfully applied middleware at layer {layer}")
        else:
            logger.warning("Web3 instance does not support middleware_onion")
    except Exception as e:
        logger.error(f"Error applying middleware: {e}")
        raise

def setup_polygon_web3(rpc_url: str, private_key: Optional[str] = None) -> Optional[Web3]:
    """
    Setup Web3 instance specifically configured for Polygon network.
    
    Args:
        rpc_url: Polygon RPC URL
        private_key: Optional private key for transaction signing
        
    Returns:
        Configured Web3 instance or None if setup fails
    """
    try:
        # Create Web3 instance
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
        
        # Apply PoA middleware
        middleware = get_compatible_middleware()
        if middleware:
            apply_middleware(w3, middleware, layer=0)
            logger.info("Applied PoA middleware for Polygon")
        else:
            logger.warning("No PoA middleware available - may have issues with Polygon blocks")
        
        # Add signing middleware if private key provided
        if private_key:
            try:
                from web3.middleware import construct_sign_and_send_raw_middleware
                w3.middleware_onion.add(construct_sign_and_send_raw_middleware(private_key))
                logger.debug("Added transaction signing middleware")
            except ImportError:
                logger.warning("Transaction signing middleware not available")
            except Exception as e:
                logger.warning(f"Error adding signing middleware: {e}")
        
        # Verify connection
        if not w3.is_connected():
            logger.error(f"Failed to connect to Polygon at {rpc_url}")
            return None
        
        # Test PoA compatibility
        try:
            latest_block = w3.eth.get_block('latest')
            logger.debug(f"Successfully retrieved latest block: {latest_block['number']}")
        except Exception as e:
            logger.warning(f"Potential PoA compatibility issue: {e}")
        
        logger.info(f"Successfully configured Web3 for Polygon at {rpc_url}")
        return w3
        
    except Exception as e:
        logger.error(f"Error setting up Polygon Web3: {e}")
        return None

def test_web3_compatibility(w3: Web3) -> bool:
    """
    Test Web3 instance compatibility with Polygon network.
    
    Args:
        w3: Web3 instance to test
        
    Returns:
        True if compatible, False otherwise
    """
    try:
        # Test basic connectivity
        if not w3.is_connected():
            logger.error("Web3 instance is not connected")
            return False
        
        # Test chain ID (Polygon mainnet = 137)
        chain_id = w3.eth.chain_id
        logger.debug(f"Connected to chain ID: {chain_id}")
        
        # Test block retrieval
        latest_block = w3.eth.get_block('latest')
        logger.debug(f"Latest block number: {latest_block['number']}")
        
        # Test gas price
        gas_price = w3.eth.gas_price
        logger.debug(f"Current gas price: {gas_price} wei")
        
        logger.info("Web3 compatibility test passed")
        return True
        
    except Exception as e:
        logger.error(f"Web3 compatibility test failed: {e}")
        return False

# Default RPC URLs for Polygon
POLYGON_RPC_URLS = [
    'https://polygon-rpc.com',
    'https://rpc-mainnet.matic.network',
    'https://matic-mainnet.chainstacklabs.com',
    'https://rpc-mainnet.maticvigil.com',
    'https://polygon-mainnet.public.blastapi.io'
]

def get_best_polygon_rpc() -> Optional[str]:
    """
    Find the best working Polygon RPC URL by testing connectivity.
    
    Returns:
        Best RPC URL or None if none work
    """
    for rpc_url in POLYGON_RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                # Quick test
                w3.eth.block_number
                logger.info(f"Found working Polygon RPC: {rpc_url}")
                return rpc_url
        except Exception as e:
            logger.debug(f"RPC {rpc_url} not working: {e}")
            continue
    
    logger.error("No working Polygon RPC URLs found")
    return None

def inject_compatible_middleware(w3: Web3, layer: int = 0):
    """
    Inject compatible PoA middleware into Web3 instance.
    This is a convenience function that gets the appropriate middleware
    and applies it to the Web3 instance.
    
    Args:
        w3: Web3 instance to inject middleware into
        layer: Layer position (0 = outermost)
    """
    if not WEB3_AVAILABLE:
        logger.warning("Web3 not available, cannot inject middleware")
        return
    
    try:
        middleware = get_compatible_middleware()
        if middleware:
            apply_middleware(w3, middleware, layer)
            logger.debug("Successfully injected compatible PoA middleware")
        else:
            logger.warning("No compatible middleware available")
    except Exception as e:
        logger.error(f"Error injecting compatible middleware: {e}")
        raise

__all__ = [
    'get_compatible_middleware',
    'create_custom_poa_middleware', 
    'apply_middleware',
    'inject_compatible_middleware',
    'setup_polygon_web3',
    'test_web3_compatibility',
    'get_best_polygon_rpc',
    'POLYGON_RPC_URLS'
]
