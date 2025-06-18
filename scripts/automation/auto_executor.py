"""
Auto executor module for Flash Loan System.
Handles automated execution of arbitrage opportunities.
"""

import os

# Import standardized middleware utility
try:
    from util.web3_middleware import apply_web3_middleware
except ImportError:
    try:
        from src.utils.web3_middleware_utils import apply_web3_middleware
    except ImportError:
        # Define inline fallback if needed
        pass

import json
import time
import logging
import asyncio
from decimal import Decimal
from typing import Dict, Any, Optional, List, Union, cast
from pathlib import Path

# Import from central web3_provider
from src.utils.web3_provider import Web3
# Import PoA middleware using the project's custom_middleware
try:
    from .custom_middleware import get_poa_middleware
    # get_poa_middleware from custom_middleware.py returns the actual middleware callable.
    geth_poa_middleware = get_poa_middleware()
except ImportError:
    # This means .custom_middleware or its get_poa_middleware couldn't be imported.
    print("CRITICAL WARNING: Failed to import PoA middleware resolver from .custom_middleware. PoA features will likely fail.")
    geth_poa_middleware = None # Fallback to None
except Exception as e:
    # This catches any other unexpected error during the import or call.
    print(f"CRITICAL WARNING: Error obtaining PoA middleware via .custom_middleware: {e}. PoA features will likely fail.")
    geth_poa_middleware = None # Fallback to None

if geth_poa_middleware is None:
    # This warning is consistent with the original script's behavior if middleware is not found.
    print("Warning: Could not import/configure geth_poa_middleware. PoA-related features may not work correctly.")

from eth_account import Account
from eth_account.signers.local import LocalAccount
from hexbytes import HexBytes

from src.flash_loan.core.dex_integration_singleton import get_instance as get_dex_integration_instance
from src.flash_loan.core.message_bus import message_bus
# RPC manager is imported inside the class
from src.flash_loan.utils.token_utils import TokenUtils

class AutoExecutor:
    """
    Automated execution system for flash loan arbitrage opportunities.
    """

    def __init__(self, config_path='config/auto_executor_config.json'):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Set up a dedicated file handler for transaction logging
        self.tx_logger = logging.getLogger("TransactionExecutor")
        tx_handler = logging.FileHandler("logs/transaction_executor.log")
        tx_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.tx_logger.addHandler(tx_handler)
        self.tx_logger.setLevel(logging.DEBUG)

        self.config_path = config_path
        self.config = self._load_config()

        self.dex_integration = get_dex_integration_instance()
        if self.dex_integration is None:
            self.logger.error("DEXIntegration instance could not be initialized. Arbitrage execution will not work.")
        self.initialized = False
        self.execution_history = []
        self.max_history = 1000
        self.current_trade_size = self.config.get("initial_trade_size_usd", 500.0)

        # Defensive: ensure these attributes exist to avoid attribute errors
        self.gas_price_monitor = None
        self.transaction_executor = None
        self.risk_manager = None

        self.tx_logger.info("AutoExecutor initialized with config from: %s", config_path)

        # Get RPC manager instance
        from src.blockchain.rpc_manager import get_rpc_manager
        self.rpc_manager = get_rpc_manager()

        # Initialize w3 and flash_loan_contract to None.
        # They will be properly initialized in the async initialize() method
        # after the RPC manager has established a connection.
        self.w3 = None
        self.flash_loan_contract = None

        self.contract_abi = self._load_contract_abi()
        self.wallet_config = self._load_wallet_config()

        # Get private key and wallet address from polygon-mainnet section first
        self.private_key = self.wallet_config.get('polygon-mainnet', {}).get('privateKey')
        self.wallet_address = self.wallet_config.get('polygon-mainnet', {}).get('address')

        # If not found, try to get from root level
        if not self.private_key:
            self.private_key = self.wallet_config.get('privateKey')
        if not self.wallet_address:
            self.wallet_address = self.wallet_config.get('address')

        # Configuration flags
        self.real_execution = self.config.get("real_execution", True)
        self.auto_execute = self.config.get("auto_execute", False)
        self.use_real_prices = self.config.get("use_real_prices", True)

        if not self.private_key or not self.wallet_address:
            self.logger.error("Private key or wallet address not found in wallet_config.json. Transactions cannot be signed.")
        else:
            if self.private_key.startswith("0x"):
                self.account: LocalAccount = Account.from_key(self.private_key)
            else:
                self.account: LocalAccount = Account.from_key("0x" + self.private_key)
            self.wallet_address = self.account.address

        # Load contract address from config - FlashLoanArbitrageFixed only
        self.flash_loan_contract_address = self.config.get('contract_address', '0x153dDf13D58397740c40E9D1a6e183A8c0F36c32')
        if not self.flash_loan_contract_address:
            self.logger.error("FlashLoanArbitrageFixed contract address not found in auto_executor_config.json. Contract cannot be initialized.")

        # Log ABI loading status, as it's crucial for later contract initialization.
        if not self.contract_abi:
            self.logger.error("Flash loan contract ABI not loaded. Contract initialization will fail later.")
        # Removed premature Web3 instance retrieval and contract initialization from __init__.
        # This will now be handled in the async initialize() method.
        self.token_utils = TokenUtils()

    def _load_config(self) -> Dict[str, Any]:
        """Load the auto executor configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.error(f"Config file not found at {self.config_path}")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}

    def _load_contract_abi(self, abi_file_path='contract_abi.json') -> Optional[List[Dict[str, Any]]]:
        """Load contract ABI from a JSON file."""
        try:
            # Try multiple possible locations for the ABI file
            possible_paths = [
                # Current working directory
                abi_file_path,

                # Relative to project root
                os.path.join(os.getcwd(), abi_file_path),

                # Relative to this file
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), abi_file_path),

                # Other common locations
                os.path.join(os.getcwd(), 'contracts_fixed', f"{abi_file_path.replace('.json', '')}.abi.json"),
                os.path.join(os.getcwd(), 'contracts', f"{abi_file_path.replace('.json', '')}.abi.json"),
                os.path.join(os.getcwd(), 'abi', f"{abi_file_path.replace('.json', '')}.json"),
                os.path.join(os.getcwd(), 'abis', f"{abi_file_path.replace('.json', '')}.json")
            ]

            # Try each path
            for path in possible_paths:
                if os.path.exists(path):
                    self.logger.info(f"Loading contract ABI from {path}")
                    with open(path, 'r') as f:
                        return json.load(f)

            # If we get here, we couldn't find the ABI file
            self.logger.error(f"Contract ABI file not found in any of the expected locations")

            # Create a fallback ABI file
            self._create_fallback_abi()

            # Try to load the fallback ABI
            if os.path.exists(abi_file_path):
                self.logger.info(f"Loading fallback contract ABI from {abi_file_path}")
                with open(abi_file_path, 'r') as f:
                    return json.load(f)

            return None
        except Exception as e:
            self.logger.error(f"Error loading contract ABI: {e}")
            return None

    def _create_fallback_abi(self):
        """Create a fallback ABI file with basic functions."""
        try:
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
                    "name": "executeArbitrage",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
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

            with open("contract_abi.json", 'w') as f:
                json.dump(fallback_abi, f, indent=2)

            self.logger.info("Created fallback ABI file at contract_abi.json")
        except Exception as e:
            self.logger.error(f"Failed to create fallback ABI: {e}")

    def _load_wallet_config(self, config_path='config/wallet_config.json') -> Dict[str, Any]:
        """Load wallet configuration."""
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            absolute_config_path = base_dir / config_path
            if os.path.exists(absolute_config_path):
                with open(absolute_config_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.error(f"Wallet config file not found at {absolute_config_path}")
        except Exception as e:
            self.logger.error(f"Error loading wallet config: {e}")
        return {}

    def should_execute(self, opportunity: Dict[str, Any]) -> bool:
        """
        Determine if an opportunity should be executed.
        
        Args:
            opportunity (Dict[str, Any]): The opportunity to check.
            
        Returns:
            bool: True if the opportunity should be executed, False otherwise.
        """
        # IMPROVED_PROFITABILITY_CALCULATION_APPLIED
        try:
            # Extract relevant data
            token_symbol = opportunity.get("token")
            buy_dex = opportunity.get("buy_dex")
            sell_dex = opportunity.get("sell_dex")
            potential_profit = opportunity.get("potential_profit", 0)
            
            # Check required keys
            if not all([token_symbol, buy_dex, sell_dex]):
                self.logger.warning(f"Missing required keys in opportunity: {opportunity}")
                return False
            
            # Minimum profit threshold in USD
            min_profit_threshold = self.config.get("min_profit_threshold_usd", 10.0)
            
            # Check if profit is high enough
            if potential_profit < min_profit_threshold:
                self.logger.info(f"Potential profit (${potential_profit:.2f}) below threshold (${min_profit_threshold:.2f})")
                return False
            
            # Check if the token is in the allowed list
            allowed_tokens = self.config.get("allowed_tokens", [])
            if allowed_tokens and token_symbol not in allowed_tokens:
                self.logger.warning(f"Token {token_symbol} not in allowed list: {allowed_tokens}")
                return False
            
            # Check if the DEXes are in the allowed list
            allowed_dexes = self.config.get("allowed_dexes", [])
            if allowed_dexes and (buy_dex not in allowed_dexes or sell_dex not in allowed_dexes):
                self.logger.warning(f"DEXes {buy_dex}/{sell_dex} not in allowed list: {allowed_dexes}")
                return False
            
            # Enhanced profitability checks
            # 1. Get current gas price
            gas_price_gwei = None
            if hasattr(self, 'gas_price_monitor') and self.gas_price_monitor:
                gas_price_gwei = self.gas_price_monitor.get_gas_price_gwei()
            
            # 2. Estimate gas cost with current price
            estimated_gas = self.config.get("default_gas_limit", 750000)
            flash_loan_amount = opportunity.get("amount_usd", 1000)  # Default to $1000 if not specified
            
            # 3. Calculate estimated gas cost
            if hasattr(self, 'transaction_executor') and self.transaction_executor:
                # Use the transaction executor's method to calculate gas cost if available
                gas_cost = 0.0
                try:
                    gas_cost = asyncio.run(self.transaction_executor.calculate_gas_cost_usd(estimated_gas, gas_price_gwei))
                except Exception as e:
                    self.logger.error(f"Error calculating gas cost: {e}")
                    # Use fallback calculation
                    gas_price_gwei = gas_price_gwei or 100  # Default to 100 Gwei
                    matic_price = 0.85  # Fallback MATIC price
                    gas_cost = estimated_gas * gas_price_gwei * 1e-9 * matic_price
            else:
                # Fallback calculation
                gas_price_gwei = gas_price_gwei or 100  # Default to 100 Gwei
                matic_price = 0.85  # Fallback MATIC price
                gas_cost = estimated_gas * gas_price_gwei * 1e-9 * matic_price
            
            # 4. Calculate flash loan fee (Aave is 0.09%)
            flash_loan_fee = flash_loan_amount * 0.0009

            # 5. Calculate DEX fees (buy and sell)
            # You can make these dynamic or load from config if needed
            buy_dex_fee_rate = 0.003  # 0.3%
            sell_dex_fee_rate = 0.003  # 0.3%
            buy_dex_fee = flash_loan_amount * buy_dex_fee_rate
            sell_dex_fee = flash_loan_amount * sell_dex_fee_rate

            # 6. Calculate total cost (including DEX fees)
            total_cost = gas_cost + flash_loan_fee + buy_dex_fee + sell_dex_fee

            # 7. Calculate net profit
            net_profit = potential_profit - total_cost

            # 8. Minimum profit after fees
            min_profit_after_fees = self.config.get("min_profit_after_fees_usd", 5.0)

            # Check if net profit is sufficient
            if net_profit < min_profit_after_fees:
                self.logger.info(f"Net profit (${net_profit:.2f}) below threshold (${min_profit_after_fees:.2f})")
                self.logger.debug(f"Costs: Gas=${gas_cost:.2f}, Flash Loan Fee=${flash_loan_fee:.2f}, Buy DEX Fee=${buy_dex_fee:.2f}, Sell DEX Fee=${sell_dex_fee:.2f}")
                return False

            # Calculate profit percentage
            profit_percentage = (net_profit / flash_loan_amount) * 100

            # Minimum profit percentage
            min_profit_percentage = self.config.get("min_profit_percentage", 0.5)

            # Check if profit percentage is sufficient
            if profit_percentage < min_profit_percentage:
                self.logger.info(f"Profit percentage ({profit_percentage:.2f}%) below threshold ({min_profit_percentage:.2f}%)")
                return False

            # Enhanced risk assessment
            if hasattr(self, 'risk_manager') and self.risk_manager:
                risk_assessment = self.risk_manager.assess_risk(opportunity)
                if not risk_assessment["should_execute"]:
                    self.logger.warning(f"Risk manager advises against execution: {risk_assessment['reason']}")
                    return False

            # Enhanced price check - verify prices are still valid
            # This must be done in an async context. If you need to check prices, use the async helper below.
            return True
        except Exception as e:
            self.logger.error(f"Exception in should_execute: {e}")
            return False

    async def async_should_execute_price_check(self, opportunity: Dict[str, Any], min_profit_percentage: float, flash_loan_amount: float, total_cost: float) -> bool:
        """
        Async helper for price check logic in should_execute.
        """
        # Defensive: check dex_integration before using
        if self.dex_integration is None:
            self.logger.error("DEXIntegration instance is None in async_should_execute_price_check. Cannot check prices.")
            return False
        try:
            token_symbol = opportunity.get("token")
            buy_dex = opportunity.get("buy_dex")
            sell_dex = opportunity.get("sell_dex")
            if not (token_symbol and buy_dex and sell_dex):
                return False
            try:
                current_buy_price = await self.dex_integration.get_token_price(token_symbol, buy_dex)
                current_sell_price = await self.dex_integration.get_token_price(token_symbol, sell_dex)
            except Exception as e:
                self.logger.error(f"Exception in get_token_price: {e}")
                return False
            if current_buy_price is None or current_sell_price is None:
                self.logger.warning(f"Could not get current prices for {token_symbol} on {buy_dex}/{sell_dex}")
                return False
            price_diff_percentage = ((current_sell_price - current_buy_price) / current_buy_price) * 100
            opportunity_still_exists = price_diff_percentage > min_profit_percentage
            if not opportunity_still_exists:
                self.logger.info(f"Opportunity no longer exists. Current price diff: {price_diff_percentage:.2f}%")
                return False
            # Update opportunity with current prices and profit
            opportunity["buy_price"] = current_buy_price
            opportunity["sell_price"] = current_sell_price
            opportunity["potential_profit"] = (current_sell_price - current_buy_price) * (flash_loan_amount / current_buy_price)
            opportunity["net_profit"] = opportunity["potential_profit"] - total_cost
            opportunity["profit_percentage"] = price_diff_percentage
            return True
        except Exception as e:
            self.logger.error(f"Error checking current prices (async): {e}")
            return False

    async def _prepare_transaction(self, buy_dex: str,
                                 sell_dex: str, amount_usd: float, opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Prepare flash loan transaction data for execution."""
        if not self.flash_loan_contract or not self.w3 or not self.wallet_address:
            self.logger.error("Cannot prepare transaction: Contract, Web3, or wallet address not initialized.")
            self.tx_logger.error("Cannot prepare transaction: Contract, Web3, or wallet address not initialized.")
            return None

        try:
            # Check wallet balance before proceeding
            try:
                balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(self.wallet_address))
                balance_matic = self.w3.from_wei(balance_wei, "ether")
                self.tx_logger.info(f"Wallet MATIC balance: {balance_matic}")

                # Check if balance is sufficient for gas
                if balance_wei < self.w3.to_wei(0.05, "ether"):  # Minimum 0.05 MATIC for gas
                    self.tx_logger.error(f"Insufficient MATIC balance for gas: {balance_matic}")
                    self.logger.error(f"Insufficient MATIC balance for gas: {balance_matic}")
                    return None
            except Exception as balance_err:
                self.tx_logger.error(f"Error checking wallet balance: {balance_err}")
                self.logger.error(f"Error checking wallet balance: {balance_err}")

            token_from_symbol = opportunity.get("token")
            # Check if token_from_symbol is None or not a string
            if token_from_symbol is None:
                self.logger.error("Token symbol is None in opportunity data")
                self.tx_logger.error("Token symbol is None in opportunity data")
                return None
            # Ensure token_from_symbol is a string
            token_from_symbol = str(token_from_symbol)
            token_from_info = self.token_utils.get_token_info(token_from_symbol)
            if not token_from_info or 'address' not in token_from_info or 'decimals' not in token_from_info:
                self.logger.error(f"Could not get token info for {token_from_symbol}")
                self.tx_logger.error(f"Could not get token info for {token_from_symbol}")
                return None
            token_from_address_checksum = Web3.to_checksum_address(token_from_info['address'])
            token_from_decimals = token_from_info['decimals']

            # Verify the opportunity is still valid before proceeding
            try:
                if self.dex_integration is None:
                    self.logger.error("DEXIntegration instance is None. Cannot verify opportunity prices.")
                    self.tx_logger.error("DEXIntegration instance is None. Cannot verify opportunity prices.")
                    return None
                current_buy_price = await self.dex_integration.get_token_price(token_from_symbol, buy_dex)
                current_sell_price = await self.dex_integration.get_token_price(token_from_symbol, sell_dex)

                if current_buy_price and current_sell_price:
                    price_diff = current_sell_price - current_buy_price
                    profit_percentage = (price_diff / current_buy_price) * 100

                    self.tx_logger.info(f"Current prices - Buy: ${current_buy_price}, Sell: ${current_sell_price}, Profit: {profit_percentage:.2f}%")
                    self.logger.info(f"Current prices - Buy: ${current_buy_price}, Sell: ${current_sell_price}, Profit: {profit_percentage:.2f}%")

                    if profit_percentage < 0.5:  # Less than 0.5% profit
                        self.logger.warning(f"Opportunity no longer profitable. Current profit: {profit_percentage:.2f}%")
                        self.tx_logger.warning(f"Opportunity no longer profitable. Current profit: {profit_percentage:.2f}%")
                        return None
            except Exception as e:
                self.logger.warning(f"Could not verify opportunity: {e}")
                self.tx_logger.warning(f"Could not verify opportunity: {e}")

            # Calculate loan amount based on USD amount
            if 'trade_size_token' not in opportunity:
                self.logger.info(f"Calculating trade size for {token_from_symbol} based on USD amount: ${amount_usd}")
                if self.dex_integration is None:
                    self.logger.error("DEXIntegration instance is None. Cannot get price for trade size calculation.")
                    self.tx_logger.error("DEXIntegration instance is None. Cannot get price for trade size calculation.")
                    return None
                price = await self.dex_integration.get_token_price(token_from_symbol, buy_dex)
                if not price or price == 0:
                    self.logger.error(f"Could not get price for {token_from_symbol} to calculate amount from USD.")
                    self.tx_logger.error(f"Could not get price for {token_from_symbol} to calculate amount from USD.")
                    return None
                amount_in_human_units = Decimal(str(amount_usd)) / Decimal(str(price))
                self.logger.info(f"Calculated amount: {amount_in_human_units} {token_from_symbol}")
            else:
                amount_in_human_units = Decimal(str(opportunity['trade_size_token']))
                self.logger.info(f"Using provided amount: {amount_in_human_units} {token_from_symbol}")

            amount_in_wei = int(amount_in_human_units * (10**token_from_decimals))
            self.tx_logger.info(f"Amount in wei: {amount_in_wei}")

            # Get router addresses with case-insensitive matching
            buy_dex_router_address = None
            sell_dex_router_address = None

            # Find buy DEX router

            if self.dex_integration is None or not hasattr(self.dex_integration, 'config') or not self.dex_integration.config:
                self.logger.error("DEXIntegration instance or config is None. Cannot find router address for buy/sell DEX.")
                self.tx_logger.error("DEXIntegration instance or config is None. Cannot find router address for buy/sell DEX.")
                return None

            # Find buy DEX router
            for dex_name, dex_info in self.dex_integration.config['dexes'].items():
                if dex_name.lower() == buy_dex.lower():
                    buy_dex_router_address = Web3.to_checksum_address(dex_info['router'])
                    break

            # Find sell DEX router
            for dex_name, dex_info in self.dex_integration.config['dexes'].items():
                if dex_name.lower() == sell_dex.lower():
                    sell_dex_router_address = Web3.to_checksum_address(dex_info['router'])
                    break

            if not buy_dex_router_address:
                self.logger.error(f"Could not find router address for buy DEX: {buy_dex}")
                self.tx_logger.error(f"Could not find router address for buy DEX: {buy_dex}")
                return None

            if not sell_dex_router_address:
                self.logger.error(f"Could not find router address for sell DEX: {sell_dex}")
                self.tx_logger.error(f"Could not find router address for sell DEX: {sell_dex}")
                return None

            # Use dynamic fee tiers based on DEX and token
            source_router_fee = opportunity.get("buy_dex_fee", 3000)
            target_router_fee = opportunity.get("sell_dex_fee", 3000)

            # For Uniswap V3, try to determine the best fee tier
            if buy_dex.lower() == "uniswapv3":
                # Common fee tiers: 500 (0.05%), 3000 (0.3%), 10000 (1%)
                # Use lower fee for stable pairs, higher for volatile
                if token_from_symbol in ["USDC", "USDT", "DAI"]:
                    source_router_fee = 500  # 0.05% for stablecoins
                elif token_from_symbol in ["WETH", "WBTC"]:
                    source_router_fee = 3000  # 0.3% for major tokens
                else:
                    source_router_fee = 10000  # 1% for other tokens

                self.tx_logger.info(f"Using fee tier {source_router_fee} for {buy_dex} buy")

            if sell_dex.lower() == "uniswapv3":
                if token_from_symbol in ["USDC", "USDT", "DAI"]:
                    target_router_fee = 500
                elif token_from_symbol in ["WETH", "WBTC"]:
                    target_router_fee = 3000
                else:
                    target_router_fee = 10000

                self.tx_logger.info(f"Using fee tier {target_router_fee} for {sell_dex} sell")

            # Check if wallet_address is not None before calling get_transaction_count
            if not self.wallet_address:
                self.logger.error("Wallet address is None. Cannot get transaction count.")
                self.tx_logger.error("Wallet address is None. Cannot get transaction count.")
                return None

            nonce = self.w3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address))

            # Get current gas price and increase it slightly for faster confirmation
            base_gas_price = self.w3.eth.gas_price
            gas_price = int(base_gas_price * 1.1)  # 10% higher than current gas price

            self.tx_logger.info(f"Current gas price: {self.w3.from_wei(base_gas_price, 'gwei')} Gwei")
            self.tx_logger.info(f"Using gas price: {self.w3.from_wei(gas_price, 'gwei')} Gwei")

            # Import necessary types
            from web3.types import TxParams, Wei, Nonce

            # Create properly typed transaction parameters
            tx_params: TxParams = {
                'from': Web3.to_checksum_address(self.wallet_address),
                'nonce': Nonce(nonce),
                'gasPrice': Wei(gas_price),
            }

            try:
                # Create a properly typed transaction dictionary for estimate_gas
                from web3.types import TxParams

                # Convert wallet_address to ChecksumAddress explicitly
                from_address = Web3.to_checksum_address(self.wallet_address)

                # Create a properly typed estimation transaction
                # Convert integer values to Wei type for proper typing
                from web3.types import Wei

                estimate_tx: TxParams = {
                    'from': from_address,
                    'value': Wei(0)
                }

                self.tx_logger.info(f"Estimating gas for transaction...")

                # Try different flash loan functions in order of preference
                try:
                    # First try executeFlashLoanArbitrageV3 (with fee parameter)
                    gas_estimate = self.flash_loan_contract.functions.executeFlashLoanArbitrageV3(
                        token_from_address_checksum,
                        amount_in_wei,
                        buy_dex_router_address,
                        sell_dex_router_address,
                        source_router_fee
                    ).estimate_gas(estimate_tx)
                    self.tx_logger.info("Using executeFlashLoanArbitrageV3 function for gas estimation")
                except Exception as e:
                    self.tx_logger.warning(f"Error estimating gas with executeFlashLoanArbitrageV3: {e}")

                    try:
                        # Try executeFlashLoanArbitrage (without fee parameter)
                        gas_estimate = self.flash_loan_contract.functions.executeFlashLoanArbitrage(
                            token_from_address_checksum,
                            amount_in_wei,
                            buy_dex_router_address,
                            sell_dex_router_address
                        ).estimate_gas(estimate_tx)
                        self.tx_logger.info("Using executeFlashLoanArbitrage function for gas estimation")
                    except Exception as e2:
                        self.tx_logger.warning(f"Error estimating gas with executeFlashLoanArbitrage: {e2}")

                        # Use a default gas estimate if all else fails
                        gas_estimate = 750000
                        self.tx_logger.warning(f"Using default gas estimate: {gas_estimate}")

                # Add a larger buffer for complex operations
                tx_params['gas'] = int(gas_estimate * 1.5)  # 50% buffer
                self.logger.info(f"Gas estimate: {gas_estimate}, using: {tx_params['gas']}")
                self.tx_logger.info(f"Gas estimate: {gas_estimate}, using: {tx_params['gas']} (50% buffer)")
            except Exception as e:
                self.logger.error(f"Gas estimation failed: {e}. Using higher default gas limit.")
                self.tx_logger.error(f"Gas estimation failed: {e}. Using higher default gas limit.")
                # Use a higher gas limit for complex operations
                tx_params['gas'] = self.config.get("transaction_settings", {}).get("default_gas_limit", 750000)
                self.tx_logger.info(f"Using default gas limit: {tx_params['gas']}")

            # Try different flash loan functions in order of preference
            try:
                # First try executeFlashLoanArbitrageV3 (with fee parameter)
                transaction = self.flash_loan_contract.functions.executeFlashLoanArbitrageV3(
                    token_from_address_checksum,
                    amount_in_wei,
                    buy_dex_router_address,
                    sell_dex_router_address,
                    source_router_fee
                ).build_transaction(tx_params)
                self.tx_logger.info("Using executeFlashLoanArbitrageV3 function for transaction")
            except Exception as e:
                self.tx_logger.warning(f"Error building transaction with executeFlashLoanArbitrageV3: {e}")

                try:
                    # Try executeFlashLoanArbitrage (without fee parameter)
                    transaction = self.flash_loan_contract.functions.executeFlashLoanArbitrage(
                        token_from_address_checksum,
                        amount_in_wei,
                        buy_dex_router_address,
                        sell_dex_router_address
                    ).build_transaction(tx_params)
                    self.tx_logger.info("Using executeFlashLoanArbitrage function for transaction")
                except Exception as e2:
                    self.tx_logger.warning(f"Error building transaction with executeFlashLoanArbitrage: {e2}")

                    try:
                        # Try executeFlashLoan as last resort
                        transaction = self.flash_loan_contract.functions.executeFlashLoan(
                            token_from_address_checksum,
                            amount_in_wei,
                            buy_dex_router_address,
                            sell_dex_router_address
                        ).build_transaction(tx_params)
                        self.tx_logger.info("Using executeFlashLoan function for transaction")
                    except Exception as e3:
                        self.tx_logger.error(f"Error building transaction with all flash loan functions: {e3}")
                        return None

            # Convert to regular dictionary for return type compatibility
            transaction_dict = dict(transaction)

            self.logger.info(f"Transaction prepared: {transaction_dict}")
            self.tx_logger.info(f"Transaction prepared successfully: {transaction_dict}")
            return transaction_dict
        except Exception as e:
            self.logger.error(f"Error preparing transaction: {e}", exc_info=True)
            self.tx_logger.error(f"Error preparing transaction: {e}", exc_info=True)
            return None

    async def _send_transaction(self, tx_data: Dict[str, Any]) -> Optional[str]:
        """Sign and send transaction to the blockchain."""
        if not self.w3 or not self.account:
            self.logger.error("Cannot send transaction: Web3 or account not initialized.")
            self.tx_logger.error("Cannot send transaction: Web3 or account not initialized.")
            return None
        try:
            # Log transaction details for debugging
            self.logger.info(f"Preparing to sign and send transaction: {tx_data}")
            self.tx_logger.info(f"Preparing to sign and send transaction")

            # Verify nonce is correct
            if not self.wallet_address:
                self.logger.error("Wallet address is None. Cannot get transaction count.")
                self.tx_logger.error("Wallet address is None. Cannot get transaction count.")
                return None

            current_nonce = self.w3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address))
            if tx_data.get('nonce') != current_nonce:
                self.logger.warning(f"Nonce mismatch. Updating from {tx_data.get('nonce')} to {current_nonce}")
                self.tx_logger.warning(f"Nonce mismatch. Updating from {tx_data.get('nonce')} to {current_nonce}")
                tx_data['nonce'] = current_nonce

            # Verify gas price is reasonable and increase it for faster confirmation
            current_gas_price = self.w3.eth.gas_price
            tx_gas_price = tx_data.get('gasPrice', 0)

            # If gas price is too low or too high, update it
            if tx_gas_price < current_gas_price * 0.8 or tx_gas_price > current_gas_price * 1.5:
                self.logger.warning(f"Gas price may be outdated. Updating from {tx_gas_price} to {current_gas_price}")
                self.tx_logger.warning(f"Gas price may be outdated. Updating from {tx_gas_price} to {current_gas_price}")

                # Use a slightly higher gas price for faster confirmation
                new_gas_price = int(current_gas_price * 1.2)  # 20% higher
                tx_data['gasPrice'] = new_gas_price
                self.logger.info(f"Using increased gas price: {self.w3.from_wei(new_gas_price, 'gwei')} Gwei")
                self.tx_logger.info(f"Using increased gas price: {self.w3.from_wei(new_gas_price, 'gwei')} Gwei")

            # Increase gas limit for complex operations
            if 'gas' in tx_data and tx_data['gas'] < 500000:
                old_gas = tx_data['gas']
                tx_data['gas'] = 750000  # Higher gas limit for complex operations
                self.logger.info(f"Increasing gas limit from {old_gas} to {tx_data['gas']}")
                self.tx_logger.info(f"Increasing gas limit from {old_gas} to {tx_data['gas']}")

            # Sign the transaction
            self.logger.info(f"Signing transaction with account: {self.account.address}")
            self.tx_logger.info(f"Signing transaction with account: {self.account.address}")

            try:
                signed_tx = self.account.sign_transaction(tx_data)
                self.tx_logger.info("Transaction signed successfully")
            except Exception as sign_error:
                self.logger.error(f"Error signing transaction: {sign_error}")
                self.tx_logger.error(f"Error signing transaction: {sign_error}")
                return None

            # Send the transaction
            self.logger.info(f"Sending raw transaction to blockchain...")
            self.tx_logger.info(f"Sending raw transaction to blockchain...")            # Get the raw transaction bytes
            # Try multiple attribute names for different web3.py versions
            raw_tx = None

            # Try to access the attribute directly using getattr with a default
            raw_tx = getattr(signed_tx, 'rawTransaction', None)
            if raw_tx is None:
                raw_tx = getattr(signed_tx, 'raw_transaction', None)
            if raw_tx is None and hasattr(signed_tx, '__dict__'):
                try:
                    tx_dict = signed_tx.__dict__
                    raw_tx = tx_dict.get('rawTransaction') or tx_dict.get('raw_transaction')
                except (TypeError, ValueError, AttributeError):
                    pass

            if raw_tx is None and isinstance(signed_tx, dict):
                raw_tx = signed_tx.get('rawTransaction') or signed_tx.get('raw_transaction')

            if not raw_tx:
                self.logger.error(f"Could not extract raw transaction bytes. SignedTx type: {type(signed_tx)}")
                self.tx_logger.error(f"Could not extract raw transaction bytes. SignedTx type: {type(signed_tx)}")
                raise ValueError("Could not get raw transaction bytes from signed transaction")

            # Convert to proper type if needed
            try:
                tx_hash = self.w3.eth.send_raw_transaction(raw_tx)

                # Log success
                tx_hash_hex = tx_hash.hex()
                self.logger.info(f"Transaction sent successfully with hash: {tx_hash_hex}")
                self.tx_logger.info(f"Transaction sent successfully with hash: {tx_hash_hex}")
                self.logger.info(f"Transaction explorer URL: https://polygonscan.com/tx/{tx_hash_hex}")
                self.tx_logger.info(f"Transaction explorer URL: https://polygonscan.com/tx/{tx_hash_hex}")

                return tx_hash_hex
            except Exception as send_error:
                error_str = str(send_error)
                self.logger.error(f"Error sending transaction: {send_error}")
                self.tx_logger.error(f"Error sending transaction: {send_error}")

                # Try to extract useful information from the error
                if 'revert' in error_str or 'execution reverted' in error_str:
                    self.logger.error("Transaction reverted. This usually means the contract rejected the transaction.")
                    self.tx_logger.error("Transaction reverted. This usually means the contract rejected the transaction.")

                    # Try to decode the revert reason
                    try:
                        import re
                        reason_match = re.search(r"revert reason: '(.*?)'", error_str)
                        if reason_match:
                            revert_reason = reason_match.group(1)
                            self.logger.error(f"Revert reason: {revert_reason}")
                            self.tx_logger.error(f"Revert reason: {revert_reason}")
                    except Exception:
                        pass

                    # Suggest possible fixes
                    self.tx_logger.error("Possible fixes:")
                    self.tx_logger.error("1. Check if the contract has the correct permissions")
                    self.tx_logger.error("2. Verify that the token is approved for the contract")
                    self.tx_logger.error("3. Check if the DEX routers are correct")
                    self.tx_logger.error("4. Verify that the token has sufficient liquidity on both DEXes")

                elif 'insufficient funds' in error_str:
                    self.logger.error("Insufficient funds for transaction. Check wallet balance.")
                    self.tx_logger.error("Insufficient funds for transaction. Check wallet balance.")

                    # Try to get current balance
                    try:
                        balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(self.wallet_address))
                        balance_matic = self.w3.from_wei(balance_wei, "ether")
                        self.tx_logger.error(f"Current balance: {balance_matic} MATIC")

                        # Calculate required amount
                        gas_limit = tx_data.get('gas', 0)
                        gas_price = tx_data.get('gasPrice', 0)
                        required_wei = gas_limit * gas_price
                        required_matic = self.w3.from_wei(required_wei, "ether")
                        self.tx_logger.error(f"Required for gas: {required_matic} MATIC")
                    except Exception:
                        pass

                elif 'nonce too low' in error_str:
                    self.logger.error("Nonce too low. Another transaction may have been sent from this account.")
                    self.tx_logger.error("Nonce too low. Another transaction may have been sent from this account.")

                    # Try to get current nonce
                    try:
                        current_nonce = self.w3.eth.get_transaction_count(Web3.to_checksum_address(self.wallet_address))
                        self.tx_logger.error(f"Current nonce: {current_nonce}")
                        self.tx_logger.error(f"Used nonce: {tx_data.get('nonce', 'unknown')}")
                    except Exception:
                        pass

                elif 'already known' in error_str:
                    self.logger.warning("Transaction already in mempool. Not an error, but transaction is already pending.")
                    self.tx_logger.warning("Transaction already in mempool. Not an error, but transaction is already pending.")

                    # Extract tx hash from error message if possible
                    try:
                        import re
                        hash_match = re.search(r"0x[a-fA-F0-9]{64}", error_str)
                        if hash_match:
                            tx_hash = hash_match.group(0)
                            self.tx_logger.info(f"Transaction hash: {tx_hash}")
                            self.tx_logger.info(f"Transaction explorer URL: https://polygonscan.com/tx/{tx_hash}")
                            return tx_hash
                    except Exception:
                        pass

                elif 'underpriced' in error_str:
                    self.logger.error("Transaction underpriced. Gas price too low for current network conditions.")
                    self.tx_logger.error("Transaction underpriced. Gas price too low for current network conditions.")

                    # Try to get current gas price
                    try:
                        current_gas_price = self.w3.eth.gas_price
                        self.tx_logger.error(f"Current gas price: {self.w3.from_wei(current_gas_price, 'gwei')} Gwei")
                        self.tx_logger.error(f"Used gas price: {self.w3.from_wei(tx_data.get('gasPrice', 0), 'gwei')} Gwei")

                        # Suggest a higher gas price
                        suggested_gas_price = int(current_gas_price * 1.5)  # 50% higher
                        self.tx_logger.error(f"Suggested gas price: {self.w3.from_wei(suggested_gas_price, 'gwei')} Gwei")
                    except Exception:
                        pass

                return None

        except Exception as e:
            error_str = str(e)
            self.logger.error(f"Error in _send_transaction: {e}", exc_info=True)
            self.tx_logger.error(f"Error in _send_transaction: {e}")

            # Provide more detailed error information
            if 'revert' in error_str or 'execution reverted' in error_str:
                self.logger.error(f"Transaction reverted. This usually means the contract rejected the transaction.")
                self.tx_logger.error(f"Transaction reverted. This usually means the contract rejected the transaction.")
                self.logger.error(f"Full error: {e}")
                self.tx_logger.error(f"Full error: {e}")

                # Try to decode the revert reason if available
                if 'revert reason' in error_str:
                    import re
                    reason_match = re.search(r"revert reason: '(.*?)'", error_str)
                    if reason_match:
                        revert_reason = reason_match.group(1)
                        self.logger.error(f"Revert reason decoded: {revert_reason}")
                        self.tx_logger.error(f"Revert reason decoded: {revert_reason}")

            return None

    async def _wait_for_transaction(self, tx_hash: Union[str, HexBytes]) -> Optional[Dict[str, Any]]:
        """Wait for transaction confirmation."""
        if not self.w3:
            self.logger.error("Cannot wait for transaction: Web3 not initialized.")
            self.tx_logger.error("Cannot wait for transaction: Web3 not initialized.")
            return None
        try:
            self.logger.info(f"Waiting for transaction receipt for hash: {tx_hash}...")
            self.tx_logger.info(f"Waiting for transaction receipt for hash: {tx_hash}...")
            self.logger.info(f"Transaction explorer URL: https://polygonscan.com/tx/{tx_hash}")
            self.tx_logger.info(f"Transaction explorer URL: https://polygonscan.com/tx/{tx_hash}")

            # Get timeout from config with a reasonable default
            timeout_seconds = self.config.get("transaction_settings", {}).get("timeout_seconds", 180)
            self.logger.info(f"Waiting up to {timeout_seconds} seconds for confirmation...")
            self.tx_logger.info(f"Waiting up to {timeout_seconds} seconds for confirmation...")

            # Create a safe string representation of tx_hash for logging
            tx_hash_str = str(tx_hash)
            if isinstance(tx_hash, bytes) and hasattr(tx_hash, 'hex'):
                tx_hash_str = tx_hash.hex()

            self.logger.info(f"Using transaction hash: {tx_hash_str}")
            self.tx_logger.info(f"Using transaction hash: {tx_hash_str}")

            # We need to convert to HexBytes for compatibility with web3.py's internal _Hash32 type

            # Ensure tx_hash is in the correct format
            try:
                # Convert to HexBytes first, which is compatible with _Hash32
                try:
                    if isinstance(tx_hash, str):
                        # Make sure it starts with 0x
                        if not tx_hash.startswith('0x'):
                            tx_hash = '0x' + tx_hash
                        tx_hash_bytes = HexBytes(tx_hash)
                    else:
                        # Try to convert directly, will raise an error if not convertible
                        tx_hash_bytes = HexBytes(tx_hash)
                except Exception as e:
                    self.logger.error(f"Invalid transaction hash format: {type(tx_hash)}, Error: {e}")
                    self.tx_logger.error(f"Invalid transaction hash format: {type(tx_hash)}, Error: {e}")
                    return None

                # Now we have a HexBytes object which should work with wait_for_transaction_receipt
                self.tx_logger.info(f"Waiting for transaction receipt...")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=timeout_seconds)
                self.tx_logger.info(f"Received transaction receipt")
            except Exception as e:
                self.logger.error(f"Error waiting for transaction receipt: {e}")
                self.tx_logger.error(f"Error waiting for transaction receipt: {e}")

                # Check if transaction is still pending
                try:
                    # Try to get transaction status
                    tx = self.w3.eth.get_transaction(tx_hash_bytes)
                    if tx and tx.get('blockNumber') is None:
                        self.logger.info(f"Transaction is still pending in the mempool")
                        self.tx_logger.info(f"Transaction is still pending in the mempool")
                        self.tx_logger.info(f"Check status manually at https://polygonscan.com/tx/{tx_hash_str}")
                except Exception as tx_error:
                    self.logger.debug(f"Could not get transaction status: {tx_error}")

                return None

            # Convert receipt to dictionary to avoid type issues
            receipt_dict = dict(receipt)

            # Process receipt
            if receipt_dict['status'] == 1:
                # We already have tx_hash_str from above
                self.logger.info(f"Transaction {tx_hash_str} successful!")
                self.tx_logger.info(f"Transaction {tx_hash_str} successful!")
                self.logger.info(f"Gas used: {receipt.get('gasUsed')}")
                self.tx_logger.info(f"Gas used: {receipt.get('gasUsed')}")
                self.logger.info(f"Block number: {receipt.get('blockNumber')}")
                self.tx_logger.info(f"Block number: {receipt.get('blockNumber')}")

                # Calculate gas cost in MATIC
                gas_price_wei = receipt.get('effectiveGasPrice')
                gas_used = receipt.get('gasUsed')
                if gas_price_wei is not None and gas_used is not None:
                    gas_cost_wei = gas_price_wei * gas_used
                    gas_cost_matic = self.w3.from_wei(gas_cost_wei, 'ether')
                    self.logger.info(f"Gas cost: {gas_cost_matic} MATIC")
                    self.tx_logger.info(f"Gas cost: {gas_cost_matic} MATIC")
                else:
                    self.logger.warning("Could not calculate gas cost: missing effectiveGasPrice or gasUsed")
                    self.tx_logger.warning("Could not calculate gas cost: missing effectiveGasPrice or gasUsed")

                # Try to get current MATIC price to calculate USD cost
                try:
                    if self.dex_integration is None:
                        self.logger.error("DEXIntegration instance is None. Cannot get WMATIC price for gas cost calculation.")
                        self.tx_logger.error("DEXIntegration instance is None. Cannot get WMATIC price for gas cost calculation.")
                        matic_price = None
                    else:
                        matic_price = await self.dex_integration.get_token_price("WMATIC")
                    if matic_price:
                        gas_cost_usd = float(gas_cost_matic) * float(matic_price)
                        self.logger.info(f"Gas cost: ${gas_cost_usd:.4f} USD")
                        self.tx_logger.info(f"Gas cost: ${gas_cost_usd:.4f} USD")
                except Exception as price_error:
                    self.logger.debug(f"Could not calculate gas cost in USD: {price_error}")

                # Try to parse logs for events
                try:
                    if 'logs' in receipt_dict and isinstance(receipt_dict['logs'], list) and receipt_dict['logs']:
                        log_count = len(receipt_dict['logs'])
                        self.tx_logger.info(f"Transaction emitted {log_count} events")

                        # Look for ArbitrageExecuted event
                        if self.flash_loan_contract:  # Check if contract is initialized
                            for log in receipt_dict['logs']:
                                if isinstance(log, dict) and 'address' in log:
                                    # Check if this is our contract
                                    log_address = log.get('address', '').lower()
                                    contract_address = self.flash_loan_contract.address.lower()

                                    if log_address == contract_address:
                                        # Try to decode the event
                                        try:
                                            decoded_logs = self.flash_loan_contract.events.ArbitrageExecuted().process_receipt(receipt)
                                            if decoded_logs and isinstance(decoded_logs, list):
                                                for decoded_log in decoded_logs:
                                                    if isinstance(decoded_log, dict):
                                                        args = decoded_log.get('args', {})
                                                        if args and isinstance(args, dict):
                                                            token = args.get('token', 'unknown')
                                                            profit = args.get('profit', 0)
                                                            profit_human = self.w3.from_wei(profit, 'ether')
                                                            self.tx_logger.info(f"ArbitrageExecuted event: Token={token}, Profit={profit_human}")
                                        except Exception as decode_error:
                                            self.logger.debug(f"Could not decode event logs: {decode_error}")
                        else:
                            self.logger.debug("Flash loan contract not initialized, cannot decode events")
                except Exception as log_error:
                    self.logger.debug(f"Could not process transaction logs: {log_error}")

            else:
                # We already have tx_hash_str from above
                self.logger.error(f"Transaction {tx_hash_str} failed (reverted).")
                self.tx_logger.error(f"Transaction {tx_hash_str} failed (reverted).")
                self.logger.error(f"Block number: {receipt.get('blockNumber')}")
                self.tx_logger.error(f"Block number: {receipt.get('blockNumber')}")
                self.logger.error(f"Gas used: {receipt.get('gasUsed')}")
                self.tx_logger.error(f"Gas used: {receipt.get('gasUsed')}")

                # Try to get revert reason from transaction trace
                try:
                    # This requires an RPC that supports eth_call with state override
                    # Most public RPCs don't support this, so we'll just log the attempt
                    self.logger.info("Attempting to get revert reason (may not be supported by RPC)...")
                    self.tx_logger.info("Attempting to get revert reason (may not be supported by RPC)...")

                    # Suggest possible fixes
                    self.tx_logger.error("Possible reasons for transaction failure:")
                    self.tx_logger.error("1. Insufficient token allowance")
                    self.tx_logger.error("2. Price changed during transaction (slippage)")
                    self.tx_logger.error("3. Insufficient liquidity in DEX pools")
                    self.tx_logger.error("4. Contract logic error")
                    self.tx_logger.error("5. Gas limit too low")
                except Exception as trace_error:
                    self.logger.debug(f"Could not get transaction trace: {trace_error}")

            # Convert receipt to dictionary to ensure correct return type
            return dict(receipt)

        except (asyncio.TimeoutError, TimeoutError):
            # Create a safe string representation of tx_hash for logging
            tx_hash_str = str(tx_hash)
            if isinstance(tx_hash, bytes) and hasattr(tx_hash, 'hex'):
                tx_hash_str = tx_hash.hex()

            self.logger.error(f"Timeout waiting for transaction {tx_hash_str} after {timeout_seconds} seconds")
            self.tx_logger.error(f"Timeout waiting for transaction {tx_hash_str} after {timeout_seconds} seconds")
            self.logger.info(f"The transaction may still be pending or could be dropped from the mempool")
            self.tx_logger.info(f"The transaction may still be pending or could be dropped from the mempool")
            self.logger.info(f"Check status manually at https://polygonscan.com/tx/{tx_hash_str}")
            self.tx_logger.info(f"Check status manually at https://polygonscan.com/tx/{tx_hash_str}")

            # Try to check transaction status
            try:
                # Convert string to HexBytes for Web3.py compatibility
                tx_hash_hex = HexBytes(tx_hash_str) if tx_hash_str.startswith('0x') else HexBytes('0x' + tx_hash_str)

                tx = self.w3.eth.get_transaction(tx_hash_hex)
                if tx:
                    if tx.get('blockNumber') is None:
                        self.tx_logger.info(f"Transaction is still pending in the mempool")
                    else:
                        self.tx_logger.info(f"Transaction is included in block {tx.get('blockNumber')}")

                        # Try to get receipt again
                        try:
                            receipt = self.w3.eth.get_transaction_receipt(tx_hash_hex)
                            if receipt:
                                self.tx_logger.info(f"Transaction receipt found with status: {receipt.get('status')}")
                                return dict(receipt)
                        except Exception as receipt_error:
                            self.logger.debug(f"Error getting transaction receipt: {receipt_error}")
            except Exception as tx_error:
                self.logger.debug(f"Error checking transaction status: {tx_error}")

            return None

        except Exception as e:
            # Create a safe string representation of tx_hash for logging
            tx_hash_str = str(tx_hash)
            if isinstance(tx_hash, bytes) and hasattr(tx_hash, 'hex'):
                tx_hash_str = tx_hash.hex()

            self.logger.error(f"Error waiting for transaction receipt for {tx_hash_str}: {e}", exc_info=True)
            self.tx_logger.error(f"Error waiting for transaction receipt for {tx_hash_str}: {e}")
            return None

    async def _calculate_actual_profit(self, receipt: Dict[str, Any], opportunity: Dict[str, Any]) -> float:
        """Calculate actual profit from transaction receipt by parsing logs."""
        if not self.flash_loan_contract:
            self.logger.error("Contract not initialized, cannot calculate profit from logs.")
            return 0.0
        try:
            profit_usd = 0.0
            token_symbol = opportunity.get("token", "UNKNOWN_TOKEN")
            token_info = self.token_utils.get_token_info(token_symbol)
            token_decimals = token_info.get("decimals", 18) if token_info else 18

            for log_entry in receipt.get('logs', []):
                try:
                    event_data_direct = self.flash_loan_contract.events.DirectArbitrageExecuted().process_log(log_entry)
                    if event_data_direct:
                        profit_wei = event_data_direct.args.profit
                        profit_human = Decimal(profit_wei) / (10**token_decimals)
                        profit_token_symbol = self.token_utils.get_token_symbol(event_data_direct.args.tokenTo)
                        if not profit_token_symbol: profit_token_symbol = token_symbol

                        if profit_token_symbol.upper() in ["USDC", "USDT", "DAI"]:
                            profit_usd = float(profit_human)
                        else:
                            if self.dex_integration is None:
                                self.logger.error("DEXIntegration instance is None. Cannot get price for profit token.")
                                price = None
                            else:
                                price = await self.dex_integration.get_token_price(profit_token_symbol)
                            if price:
                                profit_usd = float(profit_human * Decimal(str(price)))
                            else:
                                self.logger.warning(f"Could not get price for {profit_token_symbol} to convert profit to USD.")
                                profit_usd = 0.0

                        self.logger.info(f"DirectArbitrageExecuted event found. Profit (wei): {profit_wei}, Profit ({profit_token_symbol}): {profit_human}, Profit (USD): {profit_usd}")
                        return profit_usd
                except Exception:
                    # Silently pass if this event type is not found
                    pass

                try:
                    event_data_generic = self.flash_loan_contract.events.ArbitrageExecuted().process_log(log_entry)
                    if event_data_generic:
                        profit_wei = event_data_generic.args.profit
                        profit_human = Decimal(profit_wei) / (10**token_decimals)
                        profit_token_symbol = self.token_utils.get_token_symbol(event_data_generic.args.tokenBorrow)
                        if not profit_token_symbol: profit_token_symbol = token_symbol

                        if profit_token_symbol.upper() in ["USDC", "USDT", "DAI"]:
                            profit_usd = float(profit_human)
                        else:
                            if self.dex_integration is None:
                                self.logger.error("DEXIntegration instance is None. Cannot get price for profit token.")
                                price = None
                            else:
                                price = await self.dex_integration.get_token_price(profit_token_symbol)
                            if price:
                                profit_usd = float(profit_human * Decimal(str(price)))
                            else:
                                self.logger.warning(f"Could not get price for {profit_token_symbol} to convert profit to USD.")
                                profit_usd = 0.0
                        self.logger.info(f"ArbitrageExecuted event found. Profit (wei): {profit_wei}, Profit ({profit_token_symbol}): {profit_human}, Profit (USD): {profit_usd}")
                        return profit_usd
                except Exception:
                    # Silently pass if this event type is not found
                    pass

            tx_hash = receipt.get('transactionHash', b'unknown').hex() if isinstance(receipt.get('transactionHash', b'unknown'), (bytes, HexBytes)) else 'unknown'
            self.logger.warning(f"No relevant profit event found in transaction logs for {tx_hash}. Estimated profit: {opportunity.get('profit_usd', 0.0)}")
            return float(opportunity.get('profit_usd', 0.0))

        except Exception as e:
            self.logger.error(f"Error calculating actual profit from receipt: {e}", exc_info=True)
            return float(opportunity.get('profit_usd', 0.0))

    async def _track_execution(self, opportunity: Dict[str, Any],
                             result: Dict[str, Any]) -> None:
        """Track execution result."""
        try:
            self.execution_history.append({
                "timestamp": time.time(),
                "opportunity": opportunity,
                "result": result
            })

            if len(self.execution_history) > self.max_history:
                self.execution_history = self.execution_history[-self.max_history:]

            if self.config.get("profit_tracking", {}).get("enabled", False) and \
               self.config.get("profit_tracking", {}).get("save_to_file", False):
                # Log instead of trying to save since the method is not implemented
                self.logger.info(f"Would save execution result for {opportunity.get('token')} to file (not implemented)")

            if 'receipt' in result and result['receipt'] and result['receipt'].get('status') == 1:
                actual_profit = await self._calculate_actual_profit(result['receipt'], opportunity)
                result['actual_profit_usd'] = actual_profit
                self.logger.info(f"Execution for {opportunity.get('token')}: Estimated Profit USD: {opportunity.get('profit_usd')}, Actual Profit USD: {actual_profit}")
        except Exception as e:
            self.logger.error(f"Error tracking execution: {e}")

    async def _on_opportunity_found(self, opportunity: Dict[str, Any]) -> None:
        """Handle opportunity found event."""
        # Add more detailed logging to track execution flow
        self.tx_logger.info(f"OPPORTUNITY RECEIVED: {opportunity}")
        self.logger.info(f"Received opportunity: {opportunity}")

        # Check if auto_execute is enabled
        if not self.auto_execute and not self.config.get("auto_execute", False):
            self.tx_logger.warning(f"Auto-execute disabled. Skipping opportunity for {opportunity.get('token')}")
            self.logger.info(f"Auto-execute disabled. Skipping opportunity for {opportunity.get('token')}")
            return

        # Check if real_execution is enabled
        if not self.real_execution and not self.config.get("real_execution", True):
            self.tx_logger.warning(f"Real execution disabled. Simulating opportunity: {opportunity}")
            self.logger.info(f"Real execution disabled. Simulating opportunity: {opportunity}")
            return

        if not self.initialized:
            self.tx_logger.error("AutoExecutor not fully initialized. Skipping opportunity.")
            self.logger.warning("AutoExecutor not fully initialized. Skipping opportunity.")
            return

        # Check if flash loan contract is available
        if not self.flash_loan_contract:
            self.tx_logger.error("Flash loan contract not available. Skipping opportunity.")
            self.logger.warning("Flash loan contract not available. Skipping opportunity.")
            return

        # Check if wallet is configured
        if not self.private_key or not self.wallet_address:
            self.tx_logger.error("Wallet not configured. Skipping opportunity.")
            self.logger.warning("Wallet not configured. Skipping opportunity.")
            return

        # Check if profit is above threshold
        min_profit_config = self.config.get("min_profit_threshold_usd", 5.0)
        profit_usd = opportunity.get("profit_usd", 0)

        # Handle both dictionary and object access for opportunity
        if isinstance(profit_usd, (int, float)):
            pass  # Already a number
        elif hasattr(opportunity, "profit_usd"):
            profit_usd = getattr(opportunity, "profit_usd", 0)

        if profit_usd < min_profit_config:
            token = opportunity.get("token") if isinstance(opportunity, dict) else getattr(opportunity, "token", "unknown")
            self.tx_logger.info(f"Skipping opportunity for {token}: Profit ${profit_usd:.2f} is below threshold ${min_profit_config:.2f}")
            self.logger.info(f"Skipping opportunity for {token}: Profit ${profit_usd:.2f} is below threshold ${min_profit_config:.2f}")
            return

        try:
            # Log that we're attempting to execute the opportunity
            self.tx_logger.info(f"EXECUTING OPPORTUNITY: {opportunity}")
            self.logger.info(f"EXECUTING OPPORTUNITY: {opportunity}")

            # Ensure we're only using Aave flash loan arbitrage (direct and triangular arbitrage disabled)
            self.tx_logger.info("Only Aave flash loan arbitrage is enabled. Direct and triangular arbitrage are disabled.")
            self.logger.info("Only Aave flash loan arbitrage is enabled. Direct and triangular arbitrage are disabled.")

            # Check wallet balance before proceeding
            try:
                if self.w3 and self.wallet_address:
                    balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(self.wallet_address))
                    balance_matic = self.w3.from_wei(balance_wei, "ether")
                    self.tx_logger.info(f"Wallet MATIC balance: {balance_matic}")

                    # Check if balance is sufficient for gas
                    if balance_wei < self.w3.to_wei(0.01, "ether"):  # Minimum 0.01 MATIC for gas
                        self.tx_logger.error(f"Insufficient MATIC balance for gas: {balance_matic}")
                        self.logger.error(f"Insufficient MATIC balance for gas: {balance_matic}")
                        return
            except Exception as balance_err:
                self.tx_logger.error(f"Error checking wallet balance: {balance_err}")

            # Get trade size from opportunity or config
            trade_size = self.config.get("trade_size_usd", 500.0)
            if isinstance(opportunity, dict) and "trade_size_usd" in opportunity:
                trade_size = float(opportunity["trade_size_usd"])

            # Get buy and sell DEX from opportunity
            buy_dex = ""
            sell_dex = ""

            # Opportunity should always be a dict at this point
            buy_dex = opportunity.get("buy_dex", "")
            sell_dex = opportunity.get("sell_dex", "")

            self.tx_logger.info(f"Preparing transaction for {buy_dex} to {sell_dex} with trade size ${trade_size}")
            self.logger.info(f"Preparing transaction for {buy_dex} to {sell_dex} with trade size ${trade_size}")

            # Use _prepare_transaction to prepare the transaction
            tx_data = await self._prepare_transaction(
                buy_dex=buy_dex,
                sell_dex=sell_dex,
                amount_usd=float(trade_size),
                opportunity=opportunity
            )

            if tx_data:
                self.tx_logger.info(f"Transaction prepared successfully: {tx_data}")
                self.logger.info(f"Transaction prepared successfully: {tx_data}")
                self.tx_logger.info(f"Sending transaction to blockchain...")
                self.logger.info(f"Sending transaction to blockchain...")

                # Send the transaction
                tx_hash = await self._send_transaction(tx_data)

                if tx_hash:
                    self.tx_logger.info(f"Transaction sent successfully with hash: {tx_hash}")
                    self.logger.info(f"Transaction sent successfully with hash: {tx_hash}")
                    self.tx_logger.info(f"Transaction explorer URL: https://polygonscan.com/tx/{tx_hash}")
                    self.tx_logger.info(f"Waiting for transaction confirmation...")
                    self.logger.info(f"Waiting for transaction confirmation...")

                    # Wait for transaction confirmation
                    receipt = await self._wait_for_transaction(tx_hash)

                    if receipt:
                        self.tx_logger.info(f"Transaction confirmed: {receipt}")
                        self.logger.info(f"Transaction confirmed: {receipt}")

                        # Calculate actual profit
                        try:
                            actual_profit = await self._calculate_actual_profit(receipt, opportunity)
                            self.tx_logger.info(f"Actual profit: ${actual_profit}")
                        except Exception as profit_err:
                            self.tx_logger.error(f"Error calculating actual profit: {profit_err}")
                            actual_profit = 0.0

                        # Create result and track execution
                        execution_result: str = {
                            "success": True,
                            "tx_hash": tx_hash,
                            "receipt": receipt,
                            "actual_profit_usd": actual_profit
                        }

                        # Track execution
                        await self._track_execution(opportunity, execution_result)

                        # Log success
                        token = opportunity.get("token") if isinstance(opportunity, dict) else getattr(opportunity, "token", "unknown")
                        self.tx_logger.info(f"Successfully executed opportunity for {token}. TxHash: {tx_hash}")
                        self.logger.info(f"Successfully executed opportunity for {token}. TxHash: {tx_hash}")
                        self.tx_logger.info(f"Transaction explorer URL: https://polygonscan.com/tx/{tx_hash}")
                        self.logger.info(f"Transaction explorer URL: https://polygonscan.com/tx/{tx_hash}")
                    else:
                        self.tx_logger.warning(f"Transaction confirmation failed or timed out")
                        self.logger.warning(f"Transaction confirmation failed or timed out")
                else:
                    self.tx_logger.warning(f"Failed to send transaction")
                    self.logger.warning(f"Failed to send transaction")
            else:
                self.tx_logger.warning(f"Failed to prepare transaction")
                self.logger.warning(f"Failed to prepare transaction")

        except Exception as e:
            token = opportunity.get("token") if isinstance(opportunity, dict) else getattr(opportunity, "token", "unknown")
            self.tx_logger.error(f"Error handling opportunity event for {token}: {e}", exc_info=True)
            self.logger.error(f"Error handling opportunity event for {token}: {e}", exc_info=True)

    async def initialize(self, real_execution: bool = True, auto_execute: bool = False,
                      use_real_prices: bool = True, force_real_data: bool = True,
                      track_profits: bool = True, min_profit_threshold: float = 5.0,
                      trade_size: float = 500.0, increase_percentage: float = 1.0,
                      max_trade_size: float = 5000.0, contract_address: str = "") -> bool:
        """
        Initialize the auto executor with runtime configuration.

        Args:
            real_execution (bool): Whether to execute real transactions
            auto_execute (bool): Whether to automatically execute opportunities
            use_real_prices (bool): Whether to use real prices from DEXes
            force_real_data (bool): Force using real data instead of simulated data
            track_profits (bool): Whether to track profits
            min_profit_threshold (float): Minimum profit threshold in USD
            trade_size (float): Trade size in USD
            increase_percentage (float): Percentage to increase trade size after successful trades
            max_trade_size (float): Maximum trade size in USD
            contract_address (str): Flash loan contract address

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing AutoExecutor...")

            # Initialize RPC connection first if Web3 is not available
            if not self.w3:
                self.logger.info("Initializing RPC connection...")
                try:
                    # Try to initialize the RPC connection
                    initialized_primary = await self.rpc_manager.initialize()

                    if initialized_primary:
                        self.logger.info("RPC connection initialized successfully on first attempt.")
                    else:
                        self.logger.warning("RPC initialization returned False on first attempt.")

                    # Get Web3 instance after initialization attempt
                    self.w3 = self.rpc_manager.get_web3()
                    if self.w3:
                        self.logger.info(f"Web3 instance available after first attempt. Connected: {self.rpc_manager.is_connected()}")
                    else:
                        self.logger.error("Web3 instance still not available after first rpc_manager.initialize() attempt.")
                        # Try one more time with a longer timeout
                        self.logger.info("Trying one more time with longer timeout for RPC initialization...")

                        # Update timeout in config safely
                        if hasattr(self.rpc_manager, 'config') and isinstance(self.rpc_manager.config, dict) and 'timeout' in self.rpc_manager.config:
                            original_timeout = self.rpc_manager.config.get('timeout', 10) # Default if somehow not set but key exists
                            self.rpc_manager.config['timeout'] = 30  # 30 seconds timeout
                            self.logger.info(f"Increased RPC manager timeout from {original_timeout} to 30 seconds for retry.")
                        else:
                            self.logger.warning("RPC manager config or timeout setting not found/invalid. Cannot adjust timeout for retry.")

                        # Try again
                        initialized_retry = await self.rpc_manager.initialize()
                        if initialized_retry:
                            self.w3 = self.rpc_manager.get_web3() # Attempt to get w3 again
                            if self.w3:
                                self.logger.info(f"Web3 instance available after second rpc_manager.initialize() attempt. Connected: {self.rpc_manager.is_connected()}")
                            else:
                                self.logger.error("Web3 instance still not available after second rpc_manager.initialize() attempt.")
                        else:
                            self.logger.error("Second attempt at rpc_manager.initialize() also failed.")
                except Exception as e:
                    self.logger.error(f"Error during RPC connection initialization sequence: {e}")
                    self.w3 = self.rpc_manager.get_web3()  # Try to get Web3 instance anyway, might be None

            # After all attempts to initialize self.w3, if it's now available
            # and the contract wasn't initialized in __init__ (i.e., self.flash_loan_contract is None),
            # try to initialize it now using the address from the configuration.
            if self.w3 and not self.flash_loan_contract:
                if self.flash_loan_contract_address and self.contract_abi:
                    self.logger.info(f"Attempting to initialize flash loan contract in initialize() as Web3 is now available, using configured address: {self.flash_loan_contract_address}")
                    try:
                        # self.flash_loan_contract_address should have been checksummed in __init__ if it was validly loaded.
                        checksum_address = Web3.to_checksum_address(self.flash_loan_contract_address)
                        self.flash_loan_contract = self.w3.eth.contract(
                            address=checksum_address,
                            abi=self.contract_abi
                        )
                        self.logger.info(f"Flash loan contract successfully initialized in initialize() at address: {checksum_address}")
                    except Exception as e:
                        self.logger.error(f"Error initializing flash loan contract in initialize() with configured address '{self.flash_loan_contract_address}': {e}")
                        self.flash_loan_contract = None # Ensure it's None if this attempt fails
                else:
                    self.logger.warning("Cannot initialize flash loan contract in initialize(): "
                                        "Configured contract address or ABI is missing. Contract remains uninitialized.")
            elif not self.w3 and not self.flash_loan_contract:
                self.logger.warning("Web3 instance is not available after initialization attempts; flash loan contract remains uninitialized.")


            # Update configuration
            self.real_execution = real_execution
            self.auto_execute = auto_execute
            self.use_real_prices = use_real_prices

            # Update config values
            self.config["real_execution"] = real_execution
            self.config["auto_execute"] = auto_execute
            self.config["use_real_prices"] = use_real_prices
            self.config["min_profit_threshold_usd"] = min_profit_threshold
            self.config["trade_size_usd"] = trade_size
            self.config["force_real_data"] = force_real_data
            self.config["track_profits"] = {
                "enabled": track_profits,
                "save_to_file": track_profits
            }
            self.config["increase_trade_size_with_profit"] = increase_percentage > 0
            self.config["increase_percentage"] = increase_percentage
            self.config["max_trade_size_usd"] = max_trade_size

            # Update contract address if provided
            if contract_address and self.w3 and self.contract_abi:
                try:
                    self.flash_loan_contract_address = Web3.to_checksum_address(contract_address)
                    self.flash_loan_contract = self.w3.eth.contract(
                        address=self.flash_loan_contract_address,
                        abi=self.contract_abi
                    )
                    self.logger.info(f"Updated flash loan contract address to {self.flash_loan_contract_address} via initialize() params.")
                except Exception as e:
                    self.logger.error(f"Error updating contract address via initialize() params: {e}")
            elif contract_address and (not self.w3 or not self.contract_abi):
                self.logger.error(f"Cannot update contract to {contract_address}: Web3 instance or contract ABI is not available.")


            # Initialize DEX integration
            self.dex_integration = get_dex_integration_instance()

            # Mark as initialized
            self.initialized = True
            self.logger.info(f"AutoExecutor initialized with: real_execution={real_execution}, "
                           f"auto_execute={auto_execute}, use_real_prices={use_real_prices}, "
                           f"min_profit=${min_profit_threshold}, trade_size=${trade_size}, "
                           f"max_trade_size=${max_trade_size}, increase_percentage={increase_percentage}%")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing AutoExecutor: {e}", exc_info=True)
            return False

# Create singleton instance
auto_executor = AutoExecutor()
