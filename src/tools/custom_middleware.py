"""Custom middleware implementations for web3"""

import logging

# Import Web3 with error handling
try:
    # Import from central web3_provider
    from src.utils.web3_provider import Web3
    from eth_account import Account
    WEB3_IMPORTED = True
except ImportError as e:
    logging.getLogger(__name__).error(f"Failed to import Web3: {e}")
    WEB3_IMPORTED = False
    Web3 = None
    Account = None

logger = logging.getLogger(__name__)

def get_poa_middleware():
    """
    Get POA middleware compatible with the current Web3 version
    
    Returns:
        A middleware function that correctly handles POA chains
    """
    try:
        # Try to get the actual middleware function, not the applier
        from src.utils.web3_v7_middleware import get_compatible_middleware
        return get_compatible_middleware()
    except ImportError:
        try:
            # Try to get middleware from web3 directly
            from web3.middleware import geth_poa_middleware
            return geth_poa_middleware
        except ImportError:
            try:
                from web3.middleware import ExtraDataToPOAMiddleware
                return ExtraDataToPOAMiddleware
            except ImportError:
                # Create a basic fallback middleware if nothing else is available
                logger.warning("Using fallback middleware for POA chain support")
                
                def fallback_middleware(make_request, web3):
                    """Fallback middleware that simply passes requests through"""
                    def middleware(method, params):
                        return make_request(method, params)
                    return middleware
                
                return fallback_middleware

class CustomMiddleware:
    """Custom middleware implementations"""
    
    @staticmethod
    def create_signing_middleware(private_key):
        """Create a middleware that signs transactions"""
        if not WEB3_IMPORTED:
            logger.error("Web3 not imported - cannot create signing middleware")
            return None
            
        try:
            # First try to import the built-in middleware
            from src.utils.middleware_compat import construct_sign_and_send_raw_middleware
            middleware = construct_sign_and_send_raw_middleware(private_key)
            if middleware:
                return middleware
        except ImportError:
            pass
        
        # If not available, create custom implementation
        account = Account.from_key(private_key)
        
        def signing_middleware(make_request, w3):
            def middleware(method, params):
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
                            transaction['gas'] = 21000  # Default gas limit
                        
                        # Sign and send transaction
                        signed_txn = account.sign_transaction(transaction)
                        return make_request("eth_sendRawTransaction", [signed_txn.rawTransaction.hex()])
                
                # For all other methods, just pass through
                return make_request(method, params)
            
            return middleware
        
        return signing_middleware

# Export commonly used middleware functions
__all__ = ['get_poa_middleware', 'CustomMiddleware']
