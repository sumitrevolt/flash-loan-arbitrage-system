"""
ABI utilities for the flash loan project
"""

# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider  
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)

import json
import os
from typing import Dict, List, Any, Optional

# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3

def load_abi(abi_path: str) -> Optional[List[Dict[str, Any]]]:
    """Load ABI from file"""
    try:
        if not os.path.exists(abi_path):
            logger.error(f"ABI file not found: {abi_path}")
            return None
            
        with open(abi_path, 'r', encoding='utf-8') as f:
            abi = json.load(f)
            
        if not isinstance(abi, list):
            logger.error(f"Invalid ABI format in {abi_path}")
            return None
            
        logger.info(f"Loaded ABI from {abi_path}")
        return abi
        
    except Exception as e:
        logger.error(f"Failed to load ABI from {abi_path}: {e}")
        return None

@requires_web3
def get_contract_instance(w3: Web3, address: str, abi: List[Dict[str, Any]]) -> Optional[Any]:
    """Get contract instance with error handling"""
    if not WEB3_IMPORTED:
        logger.error("Web3 not available for contract instance")
        return None
        
    try:
        checksum_address = w3.to_checksum_address(address)
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        logger.info(f"Created contract instance at {checksum_address}")
        return contract
        
    except Exception as e:
        logger.error(f"Failed to create contract instance: {e}")
        return None

def validate_abi(abi: List[Dict[str, Any]]) -> bool:
    """Validate ABI structure"""
    try:
        if not isinstance(abi, list):
            return False
            
        for item in abi:
            if not isinstance(item, dict):
                return False
            if 'type' not in item:
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"ABI validation failed: {e}")
        return False

def get_function_abi(abi: List[Dict[str, Any]], function_name: str) -> Optional[Dict[str, Any]]:
    """Get specific function ABI"""
    try:
        for item in abi:
            if item.get('type') == 'function' and item.get('name') == function_name:
                return item
        
        logger.warning(f"Function {function_name} not found in ABI")
        return None
        
    except Exception as e:
        logger.error(f"Failed to get function ABI: {e}")
        return None

# Common ABIs for flash loan contracts
AAVE_POOL_ABI = [
    {
        "inputs": [
            {"name": "assets", "type": "address[]"},
            {"name": "amounts", "type": "uint256[]"},
            {"name": "modes", "type": "uint256[]"},
            {"name": "onBehalfOf", "type": "address"},
            {"name": "params", "type": "bytes"},
            {"name": "referralCode", "type": "uint16"}
        ],
        "name": "flashLoan",
        "outputs": [],
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

def get_common_abi(contract_type: str) -> Optional[List[Dict[str, Any]]]:
    """Get common contract ABIs"""
    abis = {
        'aave_pool': AAVE_POOL_ABI,
        'erc20': ERC20_ABI
    }
    
    return abis.get(contract_type.lower())

if __name__ == "__main__":
    # Test ABI utilities
    logger.info("Testing ABI utilities...")
    
    # Test common ABIs
    aave_abi = get_common_abi('aave_pool')
    if aave_abi and validate_abi(aave_abi):
        logger.info("AAVE ABI validation passed")
    
    erc20_abi = get_common_abi('erc20')
    if erc20_abi and validate_abi(erc20_abi):
        logger.info("ERC20 ABI validation passed")
