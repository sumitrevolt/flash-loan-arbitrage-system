# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# Import middleware from centralized modules
from typing import Optional
import logging

from web3.types import TxParams, Wei, ChecksumAddress

from src.utils.middleware_compat import apply_poa_middleware
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
from src.utils.web3_provider import requires_web3
logger = logging.getLogger(__name__)
# Import requires_web3 decorator from central provider





def build_transaction()
    web3: Web3,
    from_address: str,
    to_address: str,
    value: int = 0,
    gas: int = 21000,
    gas_price: Optional[int] = None,
    nonce: Optional[int] = None,
    data: Optional[bytes] = None
) -> TxParams:
    """
    Build a type-safe Ethereum transaction dictionary.
    Args:
        web3: Web3 instance
        from_address: Sender address
        to_address: Recipient address
        value: Amount in wei
        gas: Gas limit
        gas_price: Gas price in wei (optional)
        nonce: Nonce (optional)
        data: Transaction data (optional)
    Returns:
        TxParams: Typed transaction dictionary
    """
    tx: TxParams = {}
        "from": web3.to_checksum_address(from_address),
        "to": web3.to_checksum_address(to_address),
        "value": Wei(value),
        "gas": gas,
    
    if gas_price is not None:
        tx["gasPrice"] = Wei(gas_price)
    if nonce is not None:
        tx["nonce"] = Nonce(nonce)
    if data is not None:
        tx["data"] = data
    return tx