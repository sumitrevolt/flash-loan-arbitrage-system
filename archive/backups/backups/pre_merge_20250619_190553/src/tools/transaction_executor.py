"""
Transaction executor for Flash Loan Arbitrage System.
Handles transaction building, signing, and execution with proper error handling.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Tuple, List, cast
from decimal import Decimal
import json
import os

# Import Web3 with proper error handling
try:
    from web3 import Web3
    from web3.types import TxParams, Wei
    from eth_account import Account
    WEB3_IMPORTED = True
except ImportError as e:
    logging.getLogger(__name__).error(f"Failed to import Web3: {e}")
    WEB3_IMPORTED = False
    Web3 = None
    TxParams = Any
    Wei = Any

# Stub for TransactionMonitor to prevent AttributeError
class TransactionMonitor:
    def add_failed_transaction(self, *args, **kwargs):
        pass

    def add_successful_transaction(self, *args, **kwargs):
        pass

# Import standardized middleware utility
try:
    from util.web3_middleware import apply_web3_middleware
except ImportError:
    try:
        from src.utils.web3_middleware_utils import apply_web3_middleware
    except ImportError:
        # Define inline fallback if needed
        pass

import logging
from src.flash_loan.core.intermediate_token_selector import intermediate_token_selector
import requests  # Added import for requests library

# Import our new modules - avoid name conflicts by using aliases
try:
    from src.flash_loan.core.dynamic_slippage import DynamicSlippageCalculator
    from src.flash_loan.core.transaction_analyzer import TransactionAnalyzer
    from src.flash_loan.core.price_impact import PriceImpactCalculator
    from src.flash_loan.core.circuit_breaker import CircuitBreaker
    # Import with alias to avoid conflict with our local TransactionMonitor
    from src.flash_loan.core.transaction_monitor import TransactionMonitor as ExternalTransactionMonitor
    from src.flash_loan.core.parameter_tuning_manager import ParameterTuningManager
    ENHANCED_MODULES_AVAILABLE = True
except ImportError as e:
    ENHANCED_MODULES_AVAILABLE = False
    logging.getLogger("transaction_executor").warning(f"Enhanced modules not available: {e}. Some features will be disabled.")

# Import Aave integration for flash loan fee calculation and liquidity checking
try:
    from agents.aave_integration import aave_integration
except ImportError:
    aave_integration = None

# Import Aave liquidity checker
try:
    from src.flash_loan.core.aave_liquidity_checker import aave_liquidity_checker
except ImportError:
    try:
        from flash_loan.core.aave_liquidity_checker import aave_liquidity_checker
    except ImportError:
        aave_liquidity_checker = None

# Import DEX fee manager
from src.flash_loan.core.dex_fee_manager import dex_fee_manager

# Import utilities for Web3.py compatibility (optional)
try:
    # Try to import the new v7 compatible middleware
    from src.utils.web3_v7_middleware import get_compatible_middleware
    from src.utils.abi_loader import load_contract_abi
    geth_poa_middleware = get_compatible_middleware()
except ImportError as e:
    # Fall back to older middleware if available
    try:
        from src.utils.middleware_utils import get_poa_middleware, apply_poa_middleware
        from src.utils.abi_utils import encode_abi, decode_abi  # Updated import
        geth_poa_middleware = get_poa_middleware()
    except ImportError as e2:
        logging.getLogger("transaction_executor").warning(f"Could not import compatibility utilities: {e2}. Some features may not work correctly.")
        geth_poa_middleware = None

from web3 import Web3
from web3.exceptions import TransactionNotFound

# Import the enhanced RPC manager for better rate limit handling
try:
    from src.flash_loan.core.enhanced_rpc_manager import enhanced_rpc_manager
    ENHANCED_RPC_AVAILABLE = True
except ImportError:
    ENHANCED_RPC_AVAILABLE = False
    logging.getLogger("transaction_executor").warning("Enhanced RPC Manager not available. Falling back to standard RPC Manager.")

from src.config.config_manager import get_config_manager  # Adjusted for direct src import
from src.blockchain.rpc_manager import RPCManager  # Adjusted for direct src import
from src.blockchain.gas_price_monitor import get_gas_price_monitor  # Adjusted for direct src import
from src.flash_loan.utils.token_utils import TokenUtils
from src.flash_loan.core.dex_integration_singleton import initialize as dex_integration_initialize, get_instance as get_dex_integration  # Use singleton

class TransactionExecutor:
    """
    Handles flash loan arbitrage transaction execution on Polygon Mainnet.
    """

    def _reset_circuit_breaker(self, token_address: str) -> Tuple[bool, str]:
        """Reset the circuit breaker by toggling token whitelist status.
        Args:
            token_address: Address of token to toggle whitelist status
        Returns:
            (success, message): Tuple containing success status and message
        """
        if not self.web3 or not self.flashloan_contract or not self.wallet_manager:
            self.logger.error("Required components not initialized")
            return False, "Required components not initialized"

        try:
            wallet_address = self.wallet_manager.get_wallet_address()
            if not wallet_address:
                self.logger.error("No wallet address available")
                return False, "No wallet address available"

            contract_owner = None
            try:
                contract_owner = self.flashloan_contract.functions.owner().call()
            except Exception as e:
                self.logger.error(f"Error fetching contract owner: {e}")
                return False, "Error fetching contract owner"

            if not contract_owner or contract_owner.lower() != wallet_address.lower():
                self.logger.error("Wallet is not contract owner")
                return False, "Not contract owner"

            try:
                wallet = self.web3.to_checksum_address(wallet_address)
                token = self.web3.to_checksum_address(token_address)
            except Exception as e:
                self.logger.error(f"Invalid address format: {e}")
                return False, "Invalid address format"

            try:
                current_status = self.flashloan_contract.functions.whitelistedTokens(token).call()
                failed_count = self.flashloan_contract.functions.failedTransactionsCount().call()
            except Exception as e:
                self.logger.error(f"Error fetching contract state: {e}")
                return False, "Error fetching contract state"

            self.logger.info(f"Current state - Failed count: {failed_count}, Token whitelisted: {current_status}")

            for i in range(2):
                try:
                    nonce = self.web3.eth.get_transaction_count(wallet) + i
                    tx_params = {
                        'from': wallet,
                        'nonce': nonce,
                        'gas': 100000,
                        'gasPrice': self.web3.eth.gas_price,
                        'chainId': self.web3.eth.chain_id
                    }
                    tx = self.flashloan_contract.functions.whitelistToken(
                        token,
                        not current_status if i == 0 else current_status
                    ).build_transaction(tx_params)
                    signed = self.wallet_manager.sign_transaction(dict(tx))
                    if not signed:
                        self.logger.error(f"Failed to sign transaction {i+1}")
                        return False, f"Failed to sign transaction {i+1}"
                    # Try both attribute names for compatibility
                    raw_tx = getattr(signed, 'rawTransaction', None) or getattr(signed, 'raw_transaction', None)
                    if not raw_tx:
                        self.logger.error(f"Could not extract raw transaction bytes from signed transaction {i+1}")
                        return False, f"Failed to extract raw transaction data for transaction {i+1}"
                    tx_hash = self.web3.eth.send_raw_transaction(raw_tx)
                    receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                    if not receipt or receipt.get('status') != 1:
                        self.logger.error(f"Transaction {i+1} failed")
                        return False, f"Transaction {i+1} failed"
                    self.logger.info(f"Reset transaction {i+1} succeeded: {tx_hash.hex()}")
                except Exception as e:
                    self.logger.error(f"Error in reset transaction {i+1}: {e}")
                    return False, f"Error in reset transaction {i+1}: {e}"

            time.sleep(2)
            try:
                new_count = self.flashloan_contract.functions.failedTransactionsCount().call()
            except Exception as e:
                self.logger.error(f"Error fetching new failed transaction count: {e}")
                return False, "Error fetching new failed transaction count"
            self.logger.info(f"New failed transaction count: {new_count}")
            if new_count < failed_count:
                return True, "Circuit breaker reset successful"
            else:
                return False, "Circuit breaker reset verification failed"
        except Exception as e:
            self.logger.error(f"Circuit breaker reset failed: {str(e)}", exc_info=True)
            return False, f"Reset failed: {str(e)}"

    async def calculate_gas_cost_usd(self, estimated_gas: int) -> float:
        """
        Calculate the gas cost in USD for a given gas estimate.
        Args:
            estimated_gas (int): The estimated gas usage for the transaction.
        Returns:
            float: The gas cost in USD.
        """
        try:
            # Get current gas price in wei
            gas_price_wei = None
            if self.gas_price_monitor and hasattr(self.gas_price_monitor, 'get_gas_price_gwei'):
                gas_price_gwei = self.gas_price_monitor.get_gas_price_gwei()
                gas_price_wei = int(float(gas_price_gwei) * 1e9)
            elif self.web3:
                gas_price_wei = self.web3.eth.gas_price
            else:
                self.logger.warning("No gas price source available, using default gas price 30 Gwei.")
                gas_price_wei = int(30 * 1e9)

            # Calculate total gas cost in wei
            total_gas_cost_wei = estimated_gas * gas_price_wei

            # Get current MATIC price in USD (Polygon network assumed)
            matic_price_usd = 0.0
            try:
                # Try to get price from DEX integration if available
                if self.dex_integration and hasattr(self.dex_integration, 'get_token_price'):
                    matic_price_usd = await self.dex_integration.get_token_price("MATIC")
                if not matic_price_usd or matic_price_usd <= 0:
                    # Fallback to CoinGecko API
                    resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=matic-network&vs_currencies=usd", timeout=5)
                    if resp.ok:
                        matic_price_usd = resp.json().get("matic-network", {}).get("usd", 0.0)
            except Exception as e:
                self.logger.warning(f"Failed to fetch MATIC price: {e}")
                matic_price_usd = 0.0

            if not matic_price_usd or matic_price_usd <= 0:
                # TODO: CRITICAL - Using a hardcoded fallback MATIC price is not suitable for production.
                # Ensure that the primary price fetching mechanisms (DEX integration or CoinGecko) are robust.
                # If they consistently fail, the system should halt or alert, not rely on a stale fallback.
                self.logger.error("CRITICAL: Could not determine MATIC price. Using fallback $0.75. THIS IS UNSAFE FOR PRODUCTION.")
                matic_price_usd = 0.75

            # Convert wei to MATIC
            total_gas_cost_matic = total_gas_cost_wei / 1e18
            gas_cost_usd = total_gas_cost_matic * matic_price_usd
            return float(gas_cost_usd)
        except Exception as e:
            self.logger.error(f"Error calculating gas cost in USD: {e}")
            return 0.0

    def calculate_aave_fee_usd(self, amount: int, token_price_usd: float, token_decimals: int = 18) -> float:
        """
        Calculate the Aave flash loan fee in USD.
        Args:
            amount (int): The amount borrowed (in token's smallest unit).
            token_price_usd (float): The price of the token in USD.
            token_decimals (int): The number of decimals for the token.
        Returns:
            float: The Aave fee in USD.
        """
        try:
            # Aave v2/v3 fee is typically 0.09%
            aave_fee_rate = 0.0009
            amount_float = float(amount) / (10 ** token_decimals)
            fee_token = amount_float * aave_fee_rate
            fee_usd = fee_token * float(token_price_usd)
            return float(fee_usd)
        except Exception as e:
            self.logger.error(f"Error calculating Aave fee in USD: {e}")
            return 0.0
    """
    Executes blockchain transactions for the flash loan system
    """

    def __init__(self):
        """Initialize the transaction executor"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing transaction executor")

        # Initialize configuration
        self.config_manager = get_config_manager()
        self.network_config = self.config_manager.get_network_config()
        self.auto_executor_config = self.config_manager.get_auto_executor_config()

        # Initialize token utils
        self.token_utils = TokenUtils()

        # Use enhanced RPC manager if available, otherwise fall back to standard RPC manager
        self.use_enhanced_rpc = ENHANCED_RPC_AVAILABLE and self.auto_executor_config.get("use_enhanced_rpc", True)
        if self.use_enhanced_rpc:
            self.logger.info("Using Enhanced RPC Manager with rate limit handling and fallbacks")
            self.rpc_manager = enhanced_rpc_manager
            self.web3 = enhanced_rpc_manager.get_web3()
        else:
            self.logger.info("Using standard RPC Manager")
            self.rpc_manager = RPCManager()
            self.web3 = self.rpc_manager.get_web3()

        # Initialize gas price monitor
        self.gas_price_monitor = get_gas_price_monitor()

        # Use the singleton wallet manager to ensure consistent state
        from src.blockchain.wallet_manager import get_wallet_manager
        self.wallet_manager = get_wallet_manager(self.web3) if self.web3 else None

        # Log wallet manager status
        if self.wallet_manager:
            wallet_address = self.wallet_manager.get_wallet_address()
            if wallet_address:
                self.logger.info(f"Wallet manager initialized with address: {wallet_address}")
            else:
                self.logger.warning("Wallet manager initialized but no wallet address is available")

        # Initialize DexIntegration using the singleton pattern
        self.dex_integration = None  # Define the attribute
        if self.rpc_manager:
            try:
                # Initialize the singleton with our RPC manager
                dex_integration_initialize(self.rpc_manager)
                # Get the singleton instance
                self.dex_integration = get_dex_integration()
                self.logger.info("DexIntegration initialized successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialize DexIntegration: {e}", exc_info=True)
        else:
            self.logger.warning(
                "RPC Manager not available, so DexIntegration was not initialized. "
                "DEX-related price fetching for MATIC in get_current_matic_price might be limited to fallbacks."
            )

        # Initialize enhanced modules
        self.dynamic_slippage = None
        self.transaction_analyzer = None
        self.price_impact_calculator = None
        self.circuit_breaker = None
        self.transaction_monitor = None
        self.parameter_tuning_manager = None

        if ENHANCED_MODULES_AVAILABLE:
            # Initialize dynamic slippage calculator
            try:
                self.dynamic_slippage = DynamicSlippageCalculator()
                self.logger.info("Dynamic slippage calculator initialized successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialize dynamic slippage calculator: {e}", exc_info=True)

            # Initialize transaction analyzer
            if self.web3:
                try:
                    self.transaction_analyzer = TransactionAnalyzer(self.web3, debug_mode=True)
                    self.logger.info("Transaction analyzer initialized successfully.")
                except Exception as e:
                    self.logger.error(f"Failed to initialize transaction analyzer: {e}", exc_info=True)

            # Initialize price impact calculator
            try:
                self.price_impact_calculator = PriceImpactCalculator()
                self.logger.info("Price impact calculator initialized successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialize price impact calculator: {e}", exc_info=True)

            # Initialize circuit breaker
            try:
                self.circuit_breaker = CircuitBreaker()
                self.logger.info("Circuit breaker initialized successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialize circuit breaker: {e}", exc_info=True)

            # Initialize transaction monitor
            try:
                self.transaction_monitor = TransactionMonitor()
                self.logger.info("Transaction monitor initialized successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialize transaction monitor: {e}", exc_info=True)

            # Initialize parameter tuning manager
            try:
                self.parameter_tuning_manager = ParameterTuningManager()
                self.logger.info("Parameter tuning manager initialized successfully.")
            except Exception as e:
                self.logger.error(f"Failed to initialize parameter tuning manager: {e}", exc_info=True)

        # Set retry parameters
        self.max_retries = self.auto_executor_config.get('max_retries', 3)
        # Get retry delay from config (can be int, float or list)
        retry_delay_config = self.auto_executor_config.get('retry_delay', 5)

        # Handle both list and scalar retry delays
        if isinstance(retry_delay_config, list):
            self.retry_delay = retry_delay_config
        else:
            self.retry_delay = float(retry_delay_config)  # Convert to float to handle all numeric types  # seconds

        # Set default parameters
        self.gas_buffer = self.auto_executor_config.get('gas_buffer', 1.2) # 20% gas buffer default
        self.confirmation_blocks = self.auto_executor_config.get('confirmation_blocks', 2)
        self.max_confirmations_wait = self.auto_executor_config.get('max_confirmations_wait', 600) # 10 minutes default

        # Load flash loan contract for direct arbitrage
        self.flashloan_contract = None
        try:
            # Try to load the contract ABI from multiple locations
            possible_paths = [
                # Current working directory
                'contract_abi.json',

                # Relative to project root
                os.path.join(os.getcwd(), 'contract_abi.json'),

                # Relative to this file
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'contract_abi.json'),

                # Standardized ABI location
                os.path.join(os.getcwd(), 'abi', 'flash_loan_contract.json'),

                # Other common locations
                os.path.join(os.getcwd(), 'contracts_fixed', 'FlashLoanArbitrageImproved.abi.json'),
                os.path.join(os.getcwd(), 'contracts', 'FlashLoanArbitrageImproved.abi.json')
            ]

            # Try each path
            contract_abi = None
            for path in possible_paths:
                if os.path.exists(path):
                    self.logger.info(f"Loading contract ABI from {path}")
                    with open(path, 'r') as f:
                        contract_abi = json.load(f)
                        break

            # If we couldn't find the ABI, create a fallback
            if not contract_abi:
                self.logger.warning("Contract ABI not found in any location, creating fallback ABI")
                fallback_abi = [
                    {
                        "inputs": [
                            {"internalType": "address", "name": "token", "type": "address"},
                            {"internalType": "uint256", "name": "amount", "type": "uint256"},
                            {"internalType": "address", "name": "sourceRouter", "type": "address"},
                            {"internalType": "address", "name": "targetRouter", "type": "address"},
                            {"internalType": "uint24", "name": "sourceFee", "type": "uint24"},
                            {"internalType": "uint24", "name": "targetFee", "type": "uint24"}
                        ],
                        "name": "executeFlashLoan",
                        "outputs": [],
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
                    }
                ]
                contract_abi = fallback_abi

            # Get contract address from network config
            addr = self.network_config.get('flash_loan_contract_address')

            # Initialize contract if we have all the necessary components
            if contract_abi and self.web3 and addr and Web3.is_address(addr):
                checksum_addr = Web3.to_checksum_address(addr)
                # Create contract instance
                self.flashloan_contract = self.web3.eth.contract(address=checksum_addr, abi=contract_abi)
                self.logger.info(f"Flash loan contract loaded at address: {checksum_addr}")
                
                # Verify contract deployment and ABI match
                try:
                    code = self.web3.eth.get_code(checksum_addr)
                    if code == '0x' or code == b'\x00':
                        self.logger.error("No contract code found at specified address!")
                        return
                        
                    self.logger.info("Verifying contract functions...")
                    # Test view functions from ABI
                    fail_count = self.flashloan_contract.functions.failedTransactionsCount().call()
                    max_fails = self.flashloan_contract.functions.maxFailedTransactions().call()
                    self.logger.info(f"Contract state verified: failedCount={fail_count}, maxFails={max_fails}")
                    self.logger.info("Contract deployment matches ABI")
                except Exception as e:
                    self.logger.error(f"Contract verification failed: {e}")
            elif not contract_abi:
                self.logger.error("Contract ABI could not be loaded from any location")
            elif not self.web3:
                self.logger.error("Web3 is not initialized, cannot create contract instance")
            elif not addr:
                self.logger.error("Flash loan contract address is missing in network config")
            else:
                self.logger.error(f"Invalid flash loan contract address format: {addr}")

        except Exception as e:
            self.logger.error(f"Failed to load flash loan contract: {e}", exc_info=True)

    async def initialize(self):
        """
        Initialize the transaction executor asynchronously.
        Currently a placeholder, can be expanded for async setup if needed.

        Returns:
            bool: True if successfully initialized
        """
        self.logger.info("Initializing transaction executor asynchronously")
        # Add any async initialization steps here if required
        if not self.web3:
            self.logger.error("Async Initialization Failed: Web3 is not available.")
            return False
        if not self.wallet_manager:
            self.logger.error("Async Initialization Failed: Wallet Manager is not available.")
            return False
        if not self.flashloan_contract:
             self.logger.error("Async Initialization Failed: Flash loan contract is not loaded.")
             return False
        self.logger.info("Transaction executor initialized successfully.")
        return True

    def _get_dex_name_from_router(self, router_address: str) -> str:
        """
        Get the DEX name from a router address.

        Args:
            router_address: Router address

        Returns:
            str: DEX name
        """
        # Common router addresses on Polygon
        router_to_dex = {
            "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff": "QuickSwap",
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506": "SushiSwap",
            "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45": "UniswapV3",
            "0xE592427A0AEce92De3Edee1F18E0157C05861564": "UniswapV3",
            "0xf5b509bB0909a69B1c207E495f687a596C168E12": "Quickswap",
            "0xC0788A3aD43d79aa53B09c2EaCc313A787d1d607": "ApeSwap"
        }

        # Normalize address
        normalized_address = router_address.lower()

        # Check if we have a match
        for addr, dex in router_to_dex.items():
            if addr.lower() == normalized_address:
                return dex

        # If no match, return generic name
        return "Unknown"


    def _load_dex_v2_fee_config(self) -> Dict[str, Any]:
        """
        Load DEX V2 fee configuration from file.

        Returns:
            Dict[str, Any]: DEX V2 fee configuration
        """
        try:
            config_path = "config/dex_v2_fee_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"DEX V2 fee configuration file not found at {config_path}. Using default values.")
                return {
                    "uniswapv3": {
                        "default": 0.003,
                        "fee_tiers": [0.0005, 0.003, 0.01]
                    },
                    "quickswap": {
                        "default": 0.003,
                        "fee_tiers": [0.003]
                    },
                    "sushiswap": {
                        "default": 0.003,
                        "fee_tiers": [0.003]
                    }
                }
        except Exception as e:
            self.logger.error(f"Error loading DEX V2 fee configuration: {e}")
            return {
                "uniswapv3": {
                    "default": 0.003,
                    "fee_tiers": [0.0005, 0.003, 0.01]
                },
                "quickswap": {
                    "default": 0.003,
                    "fee_tiers": [0.003]
                },
                "sushiswap": {
                    "default": 0.003,
                    "fee_tiers": [0.003]
                }
            }


    def _get_dex_fee_tier(self, router_address, token_symbol=None):
        # Get the appropriate fee tier for a given DEX router and token

        # Default fee tier (0.3%)
        default_fee_tier = 3000

        try:
            # Get DEX name from router address
            dex_name = self._get_dex_name_from_router(router_address)
            if not dex_name:
                self.logger.debug(f"Unknown DEX router: {router_address}, using default fee tier {default_fee_tier}")
                return default_fee_tier

            # Load fee tier configuration
            fee_tier_config = {}
            config_path = "config/dex_fee_tiers.json"

            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        fee_tier_config = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Error loading DEX fee tier config: {e}")

            # Check for token-specific fee tiers first
            if token_symbol and "token_specific_fee_tiers" in fee_tier_config:
                token_specific = fee_tier_config.get("token_specific_fee_tiers", {}).get(token_symbol, {})
                if dex_name.lower() in token_specific:
                    fee_tier = token_specific[dex_name.lower()]
                    self.logger.debug(f"Using token-specific fee tier for {token_symbol} on {dex_name}: {fee_tier}")
                    return fee_tier

            # Check for DEX-specific default fee tiers
            if "default_fee_tiers" in fee_tier_config:
                dex_fees = fee_tier_config.get("default_fee_tiers", {})
                if dex_name.lower() in dex_fees:
                    fee_tier = dex_fees[dex_name.lower()]
                    self.logger.debug(f"Using dex-specific fee tier for {dex_name}: {fee_tier}")
                    return fee_tier

            # Hardcoded fee tiers as fallback
            # Get real fee tiers from DEX contracts
            try:
                fee_manager = self.fee_manager
                if fee_manager:
                    real_fee = fee_manager.get_dex_fee(dex_name)
                    if real_fee:
                        self.logger.debug(f"Using real fee tier for {dex_name}: {real_fee}")
                        return real_fee
                
                # If fee manager unavailable, query DEX directly for real fees
                real_fee_tier = self._query_dex_fee_tier(dex_name)
                if real_fee_tier:
                    self.logger.debug(f"Queried real fee tier for {dex_name}: {real_fee_tier}")
                    return real_fee_tier
                    
            except Exception as e:
                self.logger.error(f"Failed to get real fee tier for {dex_name}: {e}")
                raise ValueError(f"Cannot determine real fee tier for {dex_name}")

            # Special handling for UniswapV3 tokens that typically use specific fee tiers
            if dex_name.lower() == "uniswapv3" and token_symbol:
                if token_symbol in ["USDC", "USDT", "DAI"]:
                    # Stablecoins often use 0.05% fee tier (500)
                    self.logger.debug(f"Using stablecoin fee tier for {token_symbol} on UniswapV3: 500")
                    return 500
                elif token_symbol in ["WETH", "WBTC"]:
                    # Major tokens often use 0.3% fee tier (3000)
                    self.logger.debug(f"Using major token fee tier for {token_symbol} on UniswapV3: 3000")
                    return 3000
                elif token_symbol in ["WMATIC", "LINK", "AAVE", "UNI", "SUSHI"]:
                    # Medium volatility tokens often use 0.3% fee tier (3000)
                    self.logger.debug(f"Using medium volatility token fee tier for {token_symbol} on UniswapV3: 3000")
                    return 3000
                else:
                    # Other tokens often use 1% fee tier (10000)
                    self.logger.debug(f"Using high volatility token fee tier for {token_symbol} on UniswapV3: 10000")
                    return 10000

            self.logger.debug(f"No specific fee tier found for {dex_name}, using default: {default_fee_tier}")
            return default_fee_tier

        except Exception as e:
            self.logger.warning(f"Error determining fee tier: {e}")
            return default_fee_tier

    def _query_dex_fee_tier(self, dex_name: str) -> Optional[int]:
        """
        Query the DEX contract directly for real fee tiers.
        
        Args:
            dex_name: Name of the DEX
            
        Returns:
            Real fee tier from DEX contract or None if not found
        """
        try:
            if not self.web3:
                return None
                
            # Map DEX names to their factory contract methods
            dex_query_methods = {
                "uniswapv3": self._query_uniswap_v3_fees,
                "quickswap": self._query_quickswap_fees,
                "sushiswap": self._query_sushiswap_fees
            }
            
            query_method = dex_query_methods.get(dex_name.lower())
            if query_method:
                return query_method()
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error querying DEX fee tier for {dex_name}: {e}")
            return None
            
    def _query_uniswap_v3_fees(self) -> Optional[int]:
        """
        TODO: CRITICAL - THIS METHOD USES A HARDCODED FALLBACK FEE TIER.
        UniswapV3 has multiple fee tiers (e.g., 0.01%, 0.05%, 0.3%, 1%).
        This method currently returns a hardcoded 3000 (0.3%).
        For production use, this MUST be replaced with actual on-chain calls
        to the UniswapV3 factory or relevant pool contracts to determine the correct fee tier
        for a given token pair.
        """
        try:
            self.logger.warning("CRITICAL WARNING: _query_uniswap_v3_fees is returning a hardcoded default fee tier (3000), NOT a real on-chain queried fee.")
            # UniswapV3 has multiple fee tiers, return the most common one
            # In practice, you would query the factory contract for pool fees
            # For now, return the standard 0.3% fee tier
            return 3000
        except Exception as e:
            self.logger.error(f"Error querying UniswapV3 fees: {e}")
            return None
            
    def _query_quickswap_fees(self) -> Optional[int]:
        """
        TODO: CRITICAL - THIS METHOD USES A HARDCODED FALLBACK FEE TIER.
        QuickSwap (UniswapV2 fork) typically has a fixed fee (e.g., 0.3%).
        This method currently returns a hardcoded 3000 (0.3%).
        For production use, verify if this can be fetched dynamically from the
        QuickSwap factory/router or if a reliable, up-to-date constant must be used
        and regularly verified.
        """
        try:
            self.logger.warning("CRITICAL WARNING: _query_quickswap_fees is returning a hardcoded default fee tier (3000), NOT a real on-chain queried fee.")
            # QuickSwap typically uses 0.3% fees
            # In practice, you would query their factory contract
            return 3000
        except Exception as e:
            self.logger.error(f"Error querying QuickSwap fees: {e}")
            return None
            
    def _query_sushiswap_fees(self) -> Optional[int]:
        """
        TODO: CRITICAL - THIS METHOD USES A HARDCODED FALLBACK FEE TIER.
        SushiSwap (UniswapV2 fork) also typically has a fixed fee (e.g., 0.3%).
        This method currently returns a hardcoded 3000 (0.3%).
        For production use, verify if this can be fetched dynamically from the
        SushiSwap factory/router or if a reliable, up-to-date constant must be used
        and regularly verified.
        """
        try:
            self.logger.warning("CRITICAL WARNING: _query_sushiswap_fees is returning a hardcoded default fee tier (3000), NOT a real on-chain queried fee.")
            # SushiSwap typically uses 0.3% fees
            # In practice, you would query their factory contract
            return 3000
        except Exception as e:
            self.logger.error(f"Error querying SushiSwap fees: {e}")
            return None

    def wait_for_transaction_receipt(self, tx_hash, timeout=None):
        """
        Wait for transaction receipt with enhanced reliability.

        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds

        Returns:
            dict: Transaction receipt
        """
        if timeout is None:
            timeout = self.max_confirmations_wait

        self.logger.info(f"Waiting for transaction receipt (timeout: {timeout}s)...")

        # Check if we're using the enhanced RPC manager and it has the wait_for_transaction_receipt method
        if self.use_enhanced_rpc:
            # Import the enhanced RPC manager directly to check if it's the correct type
            try:
                from src.flash_loan.core.enhanced_rpc_manager import EnhancedRpcManager
                if isinstance(self.rpc_manager, EnhancedRpcManager) and hasattr(self.rpc_manager, 'wait_for_transaction_receipt'):
                    try:
                        self.logger.info("Using enhanced RPC manager's wait_for_transaction_receipt method")
                        return self.rpc_manager.wait_for_transaction_receipt(tx_hash, timeout=timeout)
                    except Exception as e:
                        self.logger.error(f"Error waiting for receipt with enhanced RPC: {e}")
                        # Fall back to standard method
            except ImportError:
                self.logger.warning("Could not import EnhancedRpcManager, falling back to standard method")

        # Standard wait method
        if not self.web3:
            error_msg = "Web3 instance is not initialized, cannot wait for transaction receipt"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            self.logger.info("Using standard Web3 wait_for_transaction_receipt method")
            return self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        except Exception as e:
            self.logger.error(f"Error waiting for transaction receipt: {e}")
            raise

    async def check_aave_liquidity(self, token_address: str, amount_in_wei: int) -> Tuple[bool, int]:
        """
        Check if Aave has sufficient liquidity for a flash loan.

        Args:
            token_address (str): The address of the token.
            amount_in_wei (int): The amount of the token required, in wei.

        Returns:
            Tuple[bool, int]: (True if liquidity is sufficient, available liquidity in wei)
        """
        if not aave_liquidity_checker:
            self.logger.warning("Aave liquidity checker is not available. Skipping check.")
            return True, 0  # Assume liquidity is sufficient if checker is not available

        try:
            self.logger.info(f"Checking Aave liquidity for token {token_address}, amount: {amount_in_wei} wei")
            available_liquidity_wei = await asyncio.to_thread(
                aave_liquidity_checker.get_aave_available_liquidity,
                token_address,
                self.web3
            )

            if available_liquidity_wei is None:
                self.logger.warning(f"Could not retrieve Aave liquidity for token {token_address}. Assuming sufficient.")
                return True, 0

            self.logger.info(f"Aave available liquidity for {token_address}: {available_liquidity_wei} wei")
            if available_liquidity_wei >= amount_in_wei:
                return True, available_liquidity_wei
            else:
                return False, available_liquidity_wei
        except Exception as e:
            self.logger.error(f"Error checking Aave liquidity for {token_address}: {e}", exc_info=True)
            return False, 0 # Assume insufficient liquidity on error to be safe

    async def execute_flash_loan_arbitrage(self, opportunity: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Execute an arbitrage trade using flash loans from the contract.
        Checks Aave liquidity before executing the transaction.

        Args:
            opportunity (Dict[str, Any]): Opportunity details including token, amount, DEX routers, etc.

        Returns:
            Tuple[bool, Optional[str]]: (True if successful, transaction hash) or (False, error reason/message)
        """
        token_address = opportunity.get("token_address")
        amount = opportunity.get("amount")
        buy_dex_router = opportunity.get("buy_dex_router")
        sell_dex_router = opportunity.get("sell_dex_router")
        token_symbol = opportunity.get("token_symbol")
        if token_symbol is None:
            token_symbol = "UNKNOWN"
        expected_profit = opportunity.get("expected_profit", 0.0)

        # --- FIX: Prevent zero or negative amount transactions ---
        if amount is None or amount <= 0:
            self.logger.error(f"Invalid arbitrage amount: {amount}. Skipping opportunity.")
            return False, "Invalid arbitrage amount (must be > 0)"

        if not self.web3:
            msg = "Web3 instance is not initialized"
            self.logger.error(msg)
            return False, msg

        if not self.wallet_manager or not self.wallet_manager.get_wallet_address():
            msg = "Wallet manager not initialized or no wallet address available"
            self.logger.error(msg)
            return False, msg

        if not self.flashloan_contract:
            msg = "Flash loan contract is not loaded"
            self.logger.error(msg)
            return False, msg

        # Check contract circuit breaker before proceeding
        try:
            # Log complete contract info for diagnosis
            self.logger.info("--- Contract Circuit Breaker Diagnosis ---")
            self.logger.info("1. Checking contract state variables...")
            
            # Check circuit breaker state
            failed_count = self.flashloan_contract.functions.failedTransactionsCount().call()
            max_failed = self.flashloan_contract.functions.maxFailedTransactions().call()
            self.logger.info(f"- Failed transactions count: {failed_count}")
            self.logger.info(f"- Max failed transactions: {max_failed}")
            
            # Convert values to integers for comparison
            failed_count_int = int(failed_count)
            max_failed_int = int(max_failed)
            self.logger.info(f"- Circuit breaker status: {'TRIPPED' if failed_count_int >= max_failed_int else 'OK'}")

            # Log contract address and ABI
            self.logger.info("\n2. Contract Configuration:")
            self.logger.info(f"- Contract address: {self.flashloan_contract.address}")
            self.logger.info("- Available functions:")
            for fn in self.flashloan_contract.all_functions():
                self.logger.info(f"  * {fn}")
                
            self.logger.info("\n3. Circuit Breaker Check:")
            # Check if circuit breaker is tripped
            if failed_count_int >= max_failed_int:
                self.logger.warning("Circuit breaker tripped. Attempting recovery via owner functions...")
                
                # Get wallet and verify owner status
                wallet_address = self.wallet_manager.get_wallet_address()
                if not wallet_address:
                    self.logger.error("No wallet address available for circuit breaker recovery")
                    return False, "No wallet address available"
                
                try:
                    # Check if wallet is contract owner
                    contract_owner = self.flashloan_contract.functions.owner().call()
                    is_owner = contract_owner.lower() == wallet_address.lower()
                    self.logger.info(f"Owner check - Contract: {contract_owner}, Wallet: {wallet_address}, Is Owner: {is_owner}")
                    
                    if not is_owner:
                        self.logger.error("Wallet is not contract owner - cannot perform recovery")
                        return False, "Not contract owner"

                    # Prepare transaction parameters
                    from web3 import Web3
                    nonce = self.web3.eth.get_transaction_count(Web3.to_checksum_address(wallet_address))
                    gas_price_wei = self.web3.eth.gas_price
                    
                    # Get token address from opportunity
                    token = opportunity.get("token_address")
                    if not token:
                        self.logger.error("No token address available for recovery transaction")
                        return False, "No token address available"
                    
                    # Get current whitelist status (we'll toggle it and back)
                    current_status = self.flashloan_contract.functions.whitelistedTokens(token).call()
                    self.logger.info(f"Current whitelist status for {token}: {current_status}")
                except Exception as e:
                    self.logger.error(f"Error checking wallet owner status: {e}")
                    return False, f"Error checking owner status: {e}"
        except Exception as e:
            self.logger.error(f"Error checking contract circuit breaker: {e}")
            # Continue execution as this is just diagnostic info

        # Check gas price
        if self.gas_price_monitor:
            try:
                if hasattr(self.gas_price_monitor, 'get_gas_price_gwei'):
                    gas_price_raw = self.gas_price_monitor.get_gas_price_gwei()
                    if gas_price_raw is None:
                        self.logger.error("Gas price is None, cannot proceed with transaction.")
                        if self.circuit_breaker: self.circuit_breaker.record_failure(token_symbol=token_symbol, dex_name=opportunity.get("buy_dex_name"), loss_usd=float(opportunity.get("expected_profit", 0.0)))
                        return False, "Gas price not available"

                    gas_price_gwei_decimal: Decimal
                    if isinstance(gas_price_raw, float):
                        gas_price_gwei_decimal = Decimal(str(gas_price_raw))
                    elif isinstance(gas_price_raw, Decimal):
                        gas_price_gwei_decimal = gas_price_raw
                    else:
                        try:
                            gas_price_gwei_decimal = Decimal(str(gas_price_raw))
                        except Exception:
                            self.logger.error(f"Invalid gas price type/value: {gas_price_raw}. Aborting.")
                            if self.circuit_breaker: self.circuit_breaker.record_failure(token_symbol=token_symbol, dex_name=opportunity.get("buy_dex_name"), loss_usd=float(opportunity.get("expected_profit", 0.0)))
                            return False, "Invalid gas price format"

                    gas_price_wei = int(gas_price_gwei_decimal * Decimal('1e9'))
                    self.logger.info(f"Using gas price: {gas_price_gwei_decimal:.2f} Gwei ({gas_price_wei} Wei)")
                # Removed 'else:' and the line below it, as it seemed to be a misplaced block.
            except Exception as e:
                self.logger.warning(f"Error checking network conditions: {e}")

        # Check circuit breaker
        if self.circuit_breaker:
            if hasattr(self.circuit_breaker, 'check_circuit'):
                is_allowed, reason = self.circuit_breaker.check_circuit(token_symbol=token_symbol, dex_name=opportunity.get("buy_dex_name"))
                if not is_allowed:
                    self.logger.warning(f"Circuit breaker tripped for {token_symbol} on {opportunity.get('buy_dex_name')}: {reason}. Skipping transaction.")
                    return False, f"Circuit breaker tripped: {reason}"
            else:
                self.logger.warning("CircuitBreaker does not have check_circuit method. Skipping circuit breaker check.")

        # Get wallet address
        wallet_address = self.wallet_manager.get_wallet_address()
        if not wallet_address:
            msg = "Wallet address not available"
            self.logger.error(msg)
            return False, msg
            
        # Convert amount to human-readable for logging
        # Ensure token_address is treated as a string for token_utils
        safe_token_symbol = token_symbol if token_symbol is not None else "UNKNOWN"
        token_decimals = self.token_utils.get_token_decimals(safe_token_symbol) or 18
        amount_readable = amount / (10**token_decimals)

        # Safely convert addresses to strings for logging
        safe_token_address = str(token_address) if token_address is not None else "UNKNOWN"
        safe_buy_router = str(buy_dex_router) if buy_dex_router is not None else "UNKNOWN"
        safe_sell_router = str(sell_dex_router) if sell_dex_router is not None else "UNKNOWN"

        self.logger.info(f"Attempting to execute flash loan: {amount_readable} of token {safe_token_symbol or safe_token_address} "
                         f"from {safe_buy_router} to {safe_sell_router}")

        # Get DEX fee tiers - use safe strings
        buy_dex_fee_tier = self._get_dex_fee_tier(safe_buy_router, safe_token_symbol)
        sell_dex_fee_tier = self._get_dex_fee_tier(safe_sell_router, safe_token_symbol)

        # Use safe router addresses for _get_dex_name_from_router
        buy_dex_name = self._get_dex_name_from_router(safe_buy_router)
        sell_dex_name = self._get_dex_name_from_router(safe_sell_router)
        self.logger.info(f"Using fee tiers: Buy DEX ({buy_dex_name}) -> {buy_dex_fee_tier}, "
                         f"Sell DEX ({sell_dex_name}) -> {sell_dex_fee_tier}")


        try:
            # Import Web3 to avoid unbound variable errors
            from web3 import Web3
            
            # Get Web3 instance
            w3 = self.rpc_manager.get_web3() if self.rpc_manager else None
            if not w3:
                self.logger.error("No Web3 instance available")
                return False, "No Web3 connection"
                
            # Validate Web3 connection
            if not w3.is_connected():
                self.logger.error("Web3 not connected")
                return False, "Web3 connection failed"

            # Get nonce - Convert wallet_address to Web3.py acceptable format (ChecksumAddress)
            wallet_checksum = Web3.to_checksum_address(wallet_address) if wallet_address else None
            if not wallet_checksum:
                return False, "Invalid wallet address"

            nonce = self.web3.eth.get_transaction_count(wallet_checksum)
            self.logger.info(f"Using nonce: {nonce}")

            # Prepare transaction - add null checks for all addresses
            token_address_cs = Web3.to_checksum_address(token_address) if token_address is not None else None
            buy_dex_router_cs = Web3.to_checksum_address(buy_dex_router) if buy_dex_router is not None else None
            sell_dex_router_cs = Web3.to_checksum_address(sell_dex_router) if sell_dex_router is not None else None

            # Determine the best intermediate token for this opportunity
            # Ensure token_symbol is always a string
            intermediate_token_address = intermediate_token_selector.get_best_intermediate_token(
                str(token_symbol), buy_dex_name, sell_dex_name
            )
            intermediate_token_cs = Web3.to_checksum_address(intermediate_token_address)

            # Validate all addresses are available
            missing = []
            if not token_address_cs: missing.append("token address")
            if not buy_dex_router_cs: missing.append("buy DEX router")
            if not sell_dex_router_cs: missing.append("sell DEX router")
            if not intermediate_token_cs: missing.append("intermediate token")
            if missing:
                return False, f"Missing required addresses: {', '.join(missing)}"

            tx_params = {
                'from': wallet_address,
                'nonce': nonce,
                'gasPrice': gas_price_wei,
            }

            if 'chainId' not in tx_params:
                tx_params['chainId'] = self.web3.eth.chain_id

            # Calculate deadline for the transaction
            deadline: str = int(time.time()) + self.auto_executor_config.get('transaction_deadline_seconds', 300) # Default 5 mins
            self.logger.info(f"Calculated deadline for transaction: {deadline} (timestamp)")

            self.logger.info(f"Building transaction for flash loan contract function: executeArbitrage with params: "
                             f"borrowToken={token_address_cs}, amount={amount}, dex1={buy_dex_router_cs}, "
                             f"dex2={sell_dex_router_cs}, intermediateToken={intermediate_token_cs}, "
                             f"dex1Fee={buy_dex_fee_tier}, dex2Fee={sell_dex_fee_tier}, deadline={deadline}")

            # Estimate gas
            try:
                from web3.types import TxParams, Wei
                estimate_tx = {'from': wallet_address, 'value': 0}
                estimated_gas = self.flashloan_contract.functions.executeArbitrage(
                    token_address_cs,  # borrowToken
                    amount,
                    buy_dex_router_cs, # dex1
                    sell_dex_router_cs,# dex2
                    intermediate_token_cs, # intermediateToken
                    buy_dex_fee_tier,  # dex1Fee
                    sell_dex_fee_tier, # dex2Fee
                    deadline
                ).estimate_gas(estimate_tx)

                tx_params['gas'] = int(estimated_gas * self.gas_buffer)
                self.logger.info(f"Estimated gas: {estimated_gas}, Gas with buffer: {tx_params['gas']}")
            except Exception as e:
                self.logger.warning(f"Failed to estimate gas: {e}. Using default gas limit.")
                tx_params['gas'] = self.auto_executor_config.get('default_gas_limit_flash_loan', 1500000)
                
            # Sign and send transaction
            self.logger.info(f"Signing and sending transaction with parameters: {tx_params}")

            from web3 import Web3
            from web3.types import TxParams, Wei
            from eth_typing import ChecksumAddress
            import logging
            
            # Ensure tx_params is correctly typed for build_transaction
            # Create a new dictionary with all keys as strings to satisfy TxParams type
            tx_params_dict = {}
            for k, v in tx_params.items():
                tx_params_dict[str(k)] = v
                
            # Cast to TxParams type
            tx_params_cast = cast(TxParams, tx_params_dict)
            
            transaction = self.flashloan_contract.functions.executeArbitrage(
                token_address_cs,  # borrowToken
                amount,
                buy_dex_router_cs, # dex1
                sell_dex_router_cs,# dex2
                intermediate_token_cs, # intermediateToken
                buy_dex_fee_tier,  # dex1Fee
                sell_dex_fee_tier, # dex2Fee
                deadline
            ).build_transaction(tx_params_cast)

            # Convert transaction to Dict[str, Any] as expected by sign_transaction
            # Use a dictionary comprehension to ensure all keys are strings
            tx_dict = {str(k): v for k, v in transaction.items()}
            signed_tx = self.wallet_manager.sign_transaction(tx_dict)
            if not signed_tx:
                msg = "Failed to sign transaction"
                self.logger.error(msg)
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure(token_symbol=token_symbol, dex_name=opportunity.get("buy_dex_name"), loss_usd=float(opportunity.get("expected_profit", 0.0)))
                return False, msg
                
            # Robust extraction of raw transaction bytes
            # Try multiple attribute names for different web3.py versions
            raw_tx = getattr(signed_tx, 'rawTransaction', None)
            if raw_tx is None:
                raw_tx = getattr(signed_tx, 'raw_transaction', None)
            if raw_tx is None and hasattr(signed_tx, '__dict__'):
                tx_dict = signed_tx.__dict__
                raw_tx = tx_dict.get('rawTransaction') or tx_dict.get('raw_transaction')
            if raw_tx is None and isinstance(signed_tx, dict):
                raw_tx = signed_tx.get('rawTransaction') or signed_tx.get('raw_transaction')
            if raw_tx is None:
                self.logger.error(f"Could not extract raw transaction bytes from signed transaction. Type: {type(signed_tx)}. Dir: {dir(signed_tx)}")
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure(token_symbol=token_symbol, dex_name=opportunity.get("buy_dex_name"), loss_usd=float(opportunity.get("expected_profit", 0.0)))
                return False, "Could not extract raw transaction bytes from signed transaction"

            tx_hash_hex = self.web3.eth.send_raw_transaction(raw_tx).hex()
            self.logger.info(f"Transaction sent with hash: {tx_hash_hex}")

            # Wait for receipt
            receipt = self.wait_for_transaction_receipt(tx_hash_hex, timeout=self.max_confirmations_wait)

            if receipt and receipt.get('status') == 1:
                self.logger.info(f"Flash loan arbitrage successful. Tx: {tx_hash_hex}")
                if self.circuit_breaker: self.circuit_breaker.record_success(token_symbol=token_symbol, dex_name=opportunity.get("buy_dex_name"), profit_usd=float(opportunity.get("expected_profit", 0.0)))
                if self.transaction_monitor: self.transaction_monitor.add_successful_transaction(tx_hash_hex, "flash_loan_arbitrage", amount, token_symbol or token_address)
                return True, tx_hash_hex
            else:
                error_message = f"Transaction failed or timed out. Tx: {tx_hash_hex}. Receipt: {receipt}"
                self.logger.error(error_message)
                if self.circuit_breaker: self.circuit_breaker.record_failure(token_symbol=token_symbol, dex_name=opportunity.get("buy_dex_name"), loss_usd=float(opportunity.get("expected_profit", 0.0)))
                if self.transaction_monitor: self.transaction_monitor.add_failed_transaction(tx_hash_hex, "flash_loan_arbitrage", error_message)
                if self.transaction_analyzer:
                    analysis = self.transaction_analyzer.analyze_transaction(tx_hash_hex)
                    self.logger.info(f"Failed transaction analysis: {analysis}")
                return False, error_message

        except Exception as e:
            error_msg = f"Error executing flash loan arbitrage: {e}"
            self.logger.error(error_msg, exc_info=True)
            if self.circuit_breaker: self.circuit_breaker.record_failure(token_symbol=token_symbol, dex_name=opportunity.get("buy_dex_name"), loss_usd=float(opportunity.get("expected_profit", 0.0)))
            return False, error_msg

    def execute_arbitrage(self, token_address: str, amount: int, buy_dex_router: str, sell_dex_router: str, expected_profit: float = 0.0, token_symbol: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        '''
        Execute an arbitrage trade using the flash loan contract.
        This is a wrapper around execute_flash_loan_arbitrage to maintain backward compatibility.

        Args:
            token_address (str): Hex address of the token to trade.
            amount (int): Amount of tokens to trade (in smallest units).
            buy_dex_router (str): Hex address of the buy DEX router.
            sell_dex_router (str): Hex address of the sell DEX router.
            expected_profit (float, optional): Expected profit in USD. Defaults to 0.0.
            token_symbol (str, optional): Symbol of the token being traded. Used for dynamic slippage.

        Returns:
            Tuple[bool, Optional[str]]: (True if successful, transaction hash) or (False, error reason/message)
        '''
        self.logger.debug(f"execute_arbitrage wrapper called with: token_address={token_address}, amount={amount}, " +
                        f"buy_dex_router={buy_dex_router}, sell_dex_router={sell_dex_router}, expected_profit={expected_profit}")

        # Create the opportunity dictionary
        opportunity = {
            "token_address": token_address,
            "amount": amount,
            "buy_dex_router": buy_dex_router,
            "sell_dex_router": sell_dex_router,
            "expected_profit": expected_profit,
            "token_symbol": token_symbol
        }

        # Since execute_flash_loan_arbitrage is async, we need to run it synchronously
        import asyncio
        try:
            # Get the event loop or create one if it doesn't exist
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run the async function and return its result
            return loop.run_until_complete(self.execute_flash_loan_arbitrage(opportunity))
        except Exception as e:
            self.logger.error(f"Error executing arbitrage: {e}")
            return False, str(e)

    def _prepare_transaction(self, contract_function, value=0, gas_limit=None):
        """Prepare a transaction with proper gas estimation and pricing"""
        try:
            if not self.web3 or not self.wallet_manager:
                raise Exception("Web3 or wallet manager not initialized")
                
            wallet_address = self.wallet_manager.get_wallet_address()
            if not wallet_address:
                raise Exception("Wallet address not available")
                
            # Get current nonce
            wallet_checksum = Web3.to_checksum_address(wallet_address)
            nonce = self.web3.eth.get_transaction_count(wallet_checksum)
            
            # Get gas price
            gas_price = self.web3.eth.gas_price
            
            # Estimate gas with buffer
            try:
                gas_estimate_tx = {
                    'from': wallet_checksum,
                    'to': self.flashloan_contract.address if self.flashloan_contract else wallet_checksum,
                    'value': value,
                    'data': contract_function._encode_transaction_data() if hasattr(contract_function, '_encode_transaction_data') else b'',
                }

                estimated_gas = self.web3.eth.estimate_gas(gas_estimate_tx)
                gas_limit = int(estimated_gas * self.gas_buffer) if gas_limit is None else gas_limit
            except Exception as e:
                self.logger.warning(f"Gas estimation failed: {e}, using default gas limit")
                gas_limit = gas_limit or 2000000

            # Prepare transaction dictionary
            tx = {
                'from': wallet_checksum,
                'to': self.flashloan_contract.address if self.flashloan_contract else wallet_checksum,
                'data': contract_function._encode_transaction_data() if hasattr(contract_function, '_encode_transaction_data') else b'',
                'value': value,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': self.web3.eth.chain_id
            }

            return tx
        except Exception as e:
            self.logger.error(f"Error preparing transaction: {e}")
            return None

    async def reset_circuit_breaker(self):
        """Reset the circuit breaker by calling the contract method."""
        try:
            if not self.flashloan_contract or not self.wallet_manager or not self.web3:
                self.logger.error("Required components not initialized for circuit breaker reset")
                return None
                
            wallet_address = self.wallet_manager.get_wallet_address()
            if not wallet_address:
                self.logger.error("No wallet address available")
                return None
                
            wallet_checksum = Web3.to_checksum_address(wallet_address)
            tx = self.flashloan_contract.functions.resetFailedTransactions().build_transaction({
                'from': wallet_checksum,
                'nonce': self.web3.eth.get_transaction_count(wallet_checksum),
                'gasPrice': self.web3.eth.gas_price,
                'chainId': self.web3.eth.chain_id,
                'gas': 200000
            })
            signed_tx = self.wallet_manager.sign_transaction(dict(tx))
            if not signed_tx:
                self.logger.error("Failed to sign circuit breaker reset transaction")
                return None
                
            # Try both attribute names for compatibility
            raw_tx = getattr(signed_tx, 'rawTransaction', None) or getattr(signed_tx, 'raw_transaction', None)
            if not raw_tx:
                self.logger.error("Could not extract raw transaction bytes from signed circuit breaker reset transaction")
                return None
            tx_hash = self.web3.eth.send_raw_transaction(raw_tx)
            self.logger.info(f"Circuit breaker reset transaction sent: {tx_hash.hex()}")
            return tx_hash
        except Exception as e:
            self.logger.error(f"Failed to reset circuit breaker: {e}")
            return None

    async def _prepare_web3_instance(self, endpoint: str) -> Optional[Any]:
        """Prepare a web3 instance with proper middleware"""
        try:
            w3 = Web3(Web3.HTTPProvider(endpoint))
            if w3.is_connected():
                # Apply POA middleware if needed
                try:
                    from src.utils.middleware_compat import apply_poa_middleware
                    apply_poa_middleware(w3)
                except ImportError:
                    self.logger.warning("Could not import apply_poa_middleware")
                except Exception as e:
                    self.logger.warning(f"Could not apply POA middleware: {e}")
                return w3
        except Exception as e:
            self.logger.error(f"Failed to prepare web3 instance: {e}")
        return None

# Create a singleton instance of the TransactionExecutor
transaction_executor = TransactionExecutor()
