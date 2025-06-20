"""
Wallet manager for the Flash Loan Arbitrage System.
Handles wallet operations and transaction signing.
"""

import os
import json
import logging
import backoff
from typing import Optional, Dict, Any, cast, TypeVar, Type
from hexbytes import HexBytes

# Import from central web3_provider to ensure consistent Web3 usage
from src.utils.web3_provider import (
    Web3, Web3Exception, ContractLogicError, TransactionNotFound,
    requires_web3, WEB3_IMPORTED, get_web3_instance, to_checksum_address,
    TxParams, Wei, ChecksumAddress, HexStr
)

logger = logging.getLogger(__name__)

# Type for the account
T = TypeVar('T')

# Determine the absolute path to the config directory
PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(PROJECT_ROOT_DIR, "config")

class WalletManager:
    """
    Manages wallet operations and transaction signing.
    """
    def __init__(self, web3=None, config_path=None):
        """
        Initialize the wallet manager.

        Args:
            web3 (Web3): Web3 provider instance
            config_path (str, optional): Path to network configuration file. 
                                         Defaults to 'network_config.json' in the project's config directory.
        """
        # Set config path
        self.config_path = config_path
        
        # Default RPC URL
        default_rpc_url = "https://polygon-rpc.com"  # Use a default Polygon RPC
        
        if web3:
            self.web3 = web3
        else:
            # If config path is provided, try to load RPC URL from it
            rpc_url = default_rpc_url
            if self.config_path and os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f:
                        config = json.load(f)
                        rpc_url = config.get("polygon_rpc_url", default_rpc_url)
                except Exception as e:
                    logger.error(f"Error loading config: {e}")
            
            self.web3 = get_web3_instance(rpc_url=rpc_url, apply_poa=True)
            
        self.private_key = None

    def get_balance(self, wallet_address):
        """
        Get the balance of the wallet.

        Args:
            wallet_address (str): Wallet address

        Returns:
            float: Balance in ETH
        """
        if not self.web3 or not self.web3.is_connected():
            raise ValueError("Web3 is not connected")
        wallet_checksum = self.web3.to_checksum_address(wallet_address)
        balance_wei = self.web3.eth.get_balance(wallet_checksum)
        return float(self.web3.from_wei(balance_wei, "ether"))

    def send_transaction(self, transaction):
        """
        Sign and send a transaction.

        Args:
            transaction (dict): Transaction to sign and send

        Returns:
            str: Transaction hash
        """
        if not self.web3 or not self.web3.is_connected():
            raise ValueError("Web3 is not connected")
        
        if not self.private_key:
            self._load_private_key()
            
        signed_tx = self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)
        raw_tx = getattr(signed_tx, "rawTransaction", None)
        if raw_tx is None:
            raise ValueError("Signed transaction does not have rawTransaction")
        tx_hash = self.web3.eth.send_raw_transaction(raw_tx)
        return tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)

    def sign_transaction(self, transaction):
        """
        Sign a transaction.

        Args:
            transaction (dict): Transaction to sign

        Returns:
            SignedTransaction: Signed transaction
        """
        if not self.private_key:
            self._load_private_key()
            
        return self.web3.eth.account.sign_transaction(transaction, private_key=self.private_key)

    def _load_private_key(self):
        """Load private key from environment variable or config"""
        try:
            # Try to load from environment variable first
            private_key = os.getenv("PRIVATE_KEY")
            if private_key:
                self.private_key = private_key
                return self.private_key
            
            # Try to load from config file
            config_file = os.path.join(CONFIG_DIR, "wallet_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.private_key = config.get("private_key")
                    if self.private_key:
                        return self.private_key
            
            logger.error("No private key found in environment or config")
            raise ValueError("Private key not configured. Set PRIVATE_KEY environment variable or create config/wallet_config.json")
        except Exception as e:
            logger.error(f"Error loading private key: {e}")
            raise

    def get_wallet_address(self):
        """Get wallet address from private key"""
        try:
            if not self.private_key:
                self._load_private_key()
            
            if self.private_key and self.web3:
                account = self.web3.eth.account.from_key(self.private_key)
                return account.address
            
            logger.error("Cannot derive wallet address - missing private key or web3")
            raise ValueError("Cannot derive wallet address")
        except Exception as e:
            logger.error(f"Error getting wallet address: {e}")
            raise

    def wait_for_transaction(self, tx_hash: str, timeout: int = 180) -> Dict[str, Any]:
        """
        Wait for a transaction to be mined.

        Args:
            tx_hash (str): Transaction hash
            timeout (int, optional): Timeout in seconds

        Returns:
            dict: Transaction receipt
        """
        try:
            # Convert string hash to HexBytes
            hex_hash = HexBytes(tx_hash)

            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(hex_hash, timeout=timeout)

            # Check status using dictionary access
            if receipt["status"] == 1:
                logger.info(f"Transaction successful: {tx_hash}")
            else:
                logger.warning(f"Transaction failed: {tx_hash}")

            return dict(receipt)
        except Exception as e:
            logger.error(f"Failed to wait for transaction: {e}")
            return {}

# Singleton instance
_wallet_manager_instance = None

def get_wallet_manager(web3 = None) -> "WalletManager":
    """
    Get the wallet manager instance.

    Args:
        web3 (Web3, optional): Web3 provider instance

    Returns:
        WalletManager: Wallet manager instance
    """
    global _wallet_manager_instance
    if _wallet_manager_instance is None:
        if web3 is None:
            from src.blockchain.rpc_manager import get_rpc_manager
            web3 = get_rpc_manager().get_web3()
        if web3 is not None:
            _wallet_manager_instance = WalletManager(web3)

            # Ensure private key is loaded
            try:
                if not _wallet_manager_instance.private_key:
                    logger.info("Loading private key in singleton instance")
                    _wallet_manager_instance._load_private_key()

                # Log wallet address status
                wallet_address = _wallet_manager_instance.get_wallet_address()
                if wallet_address:
                    logger.info(f"Wallet manager initialized with address: {wallet_address}")
                else:
                    logger.warning("Wallet manager initialized but no wallet address is available")
            except Exception as e:
                logger.error(f"Failed to initialize wallet manager with real credentials: {e}")
                logger.error("Please configure PRIVATE_KEY environment variable or config/wallet_config.json")
                raise
        else:
            raise ValueError("Web3 instance is required but could not be obtained")
    return _wallet_manager_instance
