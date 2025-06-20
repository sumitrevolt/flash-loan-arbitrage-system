# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)
"""
Custom middleware for Web3.py
"""
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3




def custom_poa_middleware(make_request, web3):
    """
    Custom middleware for PoA chains
    """
    
    return construct_exception_handler_middleware({
        ExtraDataLengthError: lambda _: Any: None,
    })(make_request, web3)
