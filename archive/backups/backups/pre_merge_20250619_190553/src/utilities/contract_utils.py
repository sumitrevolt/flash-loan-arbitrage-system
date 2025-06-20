"""
Contract utilities for Flash Loan Arbitrage System.
Provides utilities for working with smart contracts.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional

class ContractUtils:
    """
    Utility class for working with smart contracts.
    Provides methods for loading ABIs, creating contract instances, etc.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.abi_cache = {}
        
        # Common ABIs for quick access
        self.common_abis = {
            "erc20": self._load_default_erc20_abi(),
            "uniswap_v2_router": self._load_default_uniswap_v2_router_abi(),
            "uniswap_v2_pair": self._load_default_uniswap_v2_pair_abi(),
            "uniswap_v3_router": self._load_default_uniswap_v3_router_abi(),
            "uniswap_v3_pool": self._load_default_uniswap_v3_pool_abi(),
        }
    
    def get_abi(self, abi_name: str) -> List[Dict[str, Any]]:
        """
        Get an ABI by name.
        
        Args:
            abi_name (str): Name of the ABI to get.
            
        Returns:
            List[Dict[str, Any]]: The ABI.
        """
        # Check if it's a common ABI
        if abi_name in self.common_abis:
            return self.common_abis[abi_name]
        
        # Check if it's in the cache
        if abi_name in self.abi_cache:
            return self.abi_cache[abi_name]
        
        # Try to load from file
        abi_path = f"abi/{abi_name}.json"
        if os.path.exists(abi_path):
            try:
                with open(abi_path, 'r') as f:
                    abi = json.load(f)
                    self.abi_cache[abi_name] = abi
                    return abi
            except Exception as e:
                self.logger.error(f"Failed to load ABI from {abi_path}: {e}")
        
        # Return empty ABI if not found
        self.logger.warning(f"ABI {abi_name} not found, returning empty ABI")
        return []
    
    def _load_default_erc20_abi(self) -> List[Dict[str, Any]]:
        """Load the default ERC20 ABI."""
        return [
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "transferFrom",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
    
    def _load_default_uniswap_v2_router_abi(self) -> List[Dict[str, Any]]:
        """Load the default Uniswap V2 Router ABI."""
        return [
            {
                "inputs": [],
                "name": "WETH",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsIn",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
    
    def _load_default_uniswap_v2_pair_abi(self) -> List[Dict[str, Any]]:
        """Load the default Uniswap V2 Pair ABI."""
        return [
            {
                "constant": True,
                "inputs": [],
                "name": "token0",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token1",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                    {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                    {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def _load_default_uniswap_v3_router_abi(self) -> List[Dict[str, Any]]:
        """Load the default Uniswap V3 Router ABI."""
        return [
            {
                "inputs": [],
                "name": "factory",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "components": [
                            {"internalType": "bytes", "name": "path", "type": "bytes"},
                            {"internalType": "address", "name": "recipient", "type": "address"},
                            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}
                        ],
                        "internalType": "struct ISwapRouter.ExactInputParams",
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "exactInput",
                "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            }
        ]
    
    def _load_default_uniswap_v3_pool_abi(self) -> List[Dict[str, Any]]:
        """Load the default Uniswap V3 Pool ABI."""
        return [
            {
                "inputs": [],
                "name": "token0",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "token1",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "liquidity",
                "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "slot0",
                "outputs": [
                    {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
                    {"internalType": "int24", "name": "tick", "type": "int24"},
                    {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
                    {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
                    {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
                    {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
                    {"internalType": "bool", "name": "unlocked", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]

# Create a singleton instance
contract_utils = ContractUtils()
