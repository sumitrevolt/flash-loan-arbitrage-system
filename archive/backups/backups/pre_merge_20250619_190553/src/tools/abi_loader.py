"""
ABI loader utility for the Flash Loan Arbitrage System.
This module provides functions to load contract ABIs from various locations.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("abi_loader")

def load_contract_abi(contract_name: str = "FlashLoanArbitrageImproved") -> Optional[List[Dict[str, Any]]]:
    """
    Load contract ABI from various possible locations.

    Args:
        contract_name (str): Name of the contract (without extension)

    Returns:
        Optional[List[Dict[str, Any]]]: The contract ABI or None if not found
    """
    # Define possible ABI file paths
    possible_paths = [
        # Root directory
        "contract_abi.json",

        # Standardized ABI location
        "abi/flash_loan_contract.json",

        # Contract-specific ABI
        f"abi/{contract_name}.json",

        # Contracts directories
        f"contracts_fixed/{contract_name}.abi.json",
        f"contracts/{contract_name}.abi.json",

        # Other common locations
        f"data/flash_loan_abi.json",
        f"contracts/abi/{contract_name}.json"
    ]

    # Get the project root directory
    root_dir = Path.cwd()

    # Try each path
    for path in possible_paths:
        full_path = root_dir / path
        if full_path.exists():
            try:
                logger.info(f"Loading contract ABI from {full_path}")
                with open(full_path, 'r') as f:
                    abi = json.load(f)
                return abi
            except Exception as e:
                logger.warning(f"Error loading ABI from {full_path}: {e}")

    # If we get here, we couldn't find the ABI
    logger.error(f"Could not find ABI for {contract_name} in any of the expected locations")

    # Try to create a fallback ABI file
    try:
        create_fallback_abi()
        if os.path.exists("contract_abi.json"):
            logger.info("Created fallback ABI file, attempting to load it")
            with open("contract_abi.json", 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to create fallback ABI: {e}")

    return None

def create_fallback_abi():
    """
    Create a fallback ABI file with basic functions for the FlashLoanArbitrageFixed contract.
    """
    fallback_abi = [
        {
            "inputs": [
                {"internalType": "address", "name": "borrowToken", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "address", "name": "dex1", "type": "address"},
                {"internalType": "address", "name": "dex2", "type": "address"},
                {"internalType": "address", "name": "intermediateToken", "type": "address"},
                {"internalType": "uint24", "name": "dex1Fee", "type": "uint24"},
                {"internalType": "uint24", "name": "dex2Fee", "type": "uint24"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "executeArbitrage",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "tokenFrom", "type": "address"},
                {"internalType": "address", "name": "tokenTo", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "address", "name": "dex1", "type": "address"},
                {"internalType": "address", "name": "dex2", "type": "address"},
                {"internalType": "uint24", "name": "dex1Fee", "type": "uint24"},
                {"internalType": "uint24", "name": "dex2Fee", "type": "uint24"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "executeDirectArbitrage",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "token", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
                {"internalType": "uint256", "name": "premium", "type": "uint256"},
                {"internalType": "address", "name": "initiator", "type": "address"},
                {"internalType": "bytes", "name": "params", "type": "bytes"}
            ],
            "name": "executeOperation",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
            "name": "withdrawToken",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "token", "type": "address"},
                {"internalType": "bool", "name": "status", "type": "bool"}
            ],
            "name": "whitelistToken",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    # Save to both locations for maximum compatibility
    with open("contract_abi.json", 'w') as f:
        json.dump(fallback_abi, f, indent=2)

    # Also save to the standardized location
    os.makedirs("abi", exist_ok=True)
    with open("abi/flash_loan_contract.json", 'w') as f:
        json.dump(fallback_abi, f, indent=2)

    logger.info("Created fallback ABI files at contract_abi.json and abi/flash_loan_contract.json")
