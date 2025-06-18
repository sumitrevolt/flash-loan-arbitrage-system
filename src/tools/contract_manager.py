"""
Contract manager for the Flash Loan Arbitrage System.
Handles contract interactions and ABI loading.
"""
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3


import os
import json
import logging
# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)
logger = logging.getLogger("ContractManager")

class ContractManager:
    """
    Manages contract interactions and ABI loading.
    """

    def __init__(self, web3: Web3):
        """
        Initialize the contract manager.

        Args:
            web3 (Web3): Web3 provider instance
        """
        self.web3 = web3
        self.contracts = {}
        self.config = self._load_config()

        # Create contracts directory if it doesn't exist
        os.makedirs(os.path.join("contracts", "abi"), exist_ok=True)

        # Create ERC20 ABI if it doesn't exist
        self._create_erc20_abi()

    def _load_config(self):
        """
        Load configuration from file.

        Returns:
            dict: Configuration data
        """
        try:
            config_path = os.path.join("config", "network_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            else:
                logger.warning("Network configuration file not found")
                return {}
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}

    def _create_erc20_abi(self):
        """Create ERC20 ABI file if it doesn't exist."""
        abi_path = os.path.join("contracts", "abi", "ERC20.json")
        if os.path.exists(abi_path):
            return

        # ERC20 ABI
        erc20_abi = [
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
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}],
                "name": "transferFrom",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

        with open(abi_path, "w") as f:
            json.dump(erc20_abi, f, indent=2)

    def get_contract(self, contract_address, contract_type="FlashLoanArbitrage"):
        """
        Get a contract instance.

        Args:
            contract_address (str): Contract address
            contract_type (str, optional): Contract type. Defaults to "FlashLoanArbitrage".

        Returns:
            Contract: Contract instance
        """
        try:
            # Check if contract is already loaded
            if contract_address in self.contracts:
                return self.contracts[contract_address]

            # Load ABI
            if contract_type == "FlashLoanArbitrage":
                # Use the main, corrected ABI file from the project root
                abi_path = "contract_abi.json"
            else:
                # For other contract types like ERC20, use the existing path convention
                abi_path = os.path.join("contracts", "abi", f"{contract_type}.json")

            if not os.path.exists(abi_path):
                logger.error(f"ABI file not found: {abi_path}")
                return None

            with open(abi_path, "r") as f:
                abi = json.load(f)

            # Create contract instance
            contract = self.web3.eth.contract(address=contract_address, abi=abi)

            # Cache contract
            self.contracts[contract_address] = contract

            return contract

        except Exception as e:
            logger.error(f"Failed to get contract: {e}")
            return None

    def get_flash_loan_contract(self):
        """
        Get the flash loan contract instance.

        Returns:
            Contract: Flash loan contract instance
        """
        try:
            contract_address = self.config.get("flash_loan_contract_address")
            if not contract_address:
                logger.error("Flash loan contract address not found in configuration")
                return None

            return self.get_contract(contract_address, "FlashLoanArbitrage")

        except Exception as e:
            logger.error(f"Failed to get flash loan contract: {e}")
            return None

    def get_contract_address(self):
        """
        Get the flash loan contract address.

        Returns:
            str: Flash loan contract address
        """
        try:
            contract_address = self.config.get("flash_loan_contract_address")
            if not contract_address:
                logger.error("Flash loan contract address not found in configuration")
                return None

            return Web3.to_checksum_address(contract_address)

        except Exception as e:
            logger.error(f"Failed to get contract address: {e}")
            return None

    def get_token_contract(self, token_address):
        """
        Get a token contract instance.

        Args:
            token_address (str): Token address

        Returns:
            Contract: Token contract instance
        """
        try:
            return self.get_contract(token_address, "ERC20")

        except Exception as e:
            logger.error(f"Failed to get token contract: {e}")
            return None

    def get_token_decimals(self, token_address):
        """
        Get the decimals of a token.

        Args:
            token_address (str): Token address

        Returns:
            int: Token decimals
        """
        try:
            token_contract = self.get_token_contract(token_address)
            if not token_contract:
                return 18  # Default to 18 decimals

            decimals = token_contract.functions.decimals().call()
            return decimals

        except Exception as e:
            logger.error(f"Failed to get token decimals: {e}")
            return 18  # Default to 18 decimals

    def get_token_symbol(self, token_address):
        """
        Get the symbol of a token.

        Args:
            token_address (str): Token address

        Returns:
            str: Token symbol
        """
        try:
            token_contract = self.get_token_contract(token_address)
            if not token_contract:
                return "UNKNOWN"

            symbol = token_contract.functions.symbol().call()
            return symbol

        except Exception as e:
            logger.error(f"Failed to get token symbol: {e}")
            return "UNKNOWN"

    def get_token_balance(self, token_address, wallet_address):
        """
        Get the balance of a token for a wallet.

        Args:
            token_address (str): Token address
            wallet_address (str): Wallet address

        Returns:
            int: Token balance in wei
        """
        try:
            token_contract = self.get_token_contract(token_address)
            if not token_contract:
                return 0

            balance = token_contract.functions.balanceOf(wallet_address).call()
            return balance

        except Exception as e:
            logger.error(f"Failed to get token balance: {e}")
            return 0

    def get_token_allowance(self, token_address, owner_address, spender_address):
        """
        Get the allowance of a token for a spender.

        Args:
            token_address (str): Token address
            owner_address (str): Owner address
            spender_address (str): Spender address

        Returns:
            int: Token allowance in wei
        """
        try:
            token_contract = self.get_token_contract(token_address)
            if not token_contract:
                return 0

            allowance = token_contract.functions.allowance(owner_address, spender_address).call()
            return allowance

        except Exception as e:
            logger.error(f"Failed to get token allowance: {e}")
            return 0
