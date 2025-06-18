"""
Transaction Error Handler for Flash Loan Arbitrage System
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3


This module provides enhanced error handling for blockchain transactions,
specifically targeting common issues with flash loan arbitrage transactions.
It includes:
- Error detection and classification
- Automatic retry mechanisms with backoff
- Gas price adjustment
- Nonce management
- Transaction receipt validation
- Detailed error logging and diagnostics
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)
# Configure logging
logger = logging.getLogger("TransactionErrorHandler")
tx_logger = logging.getLogger("TransactionLogger")

# File handler for transaction logs
import os
if not os.path.exists("logs"):
    os.makedirs("logs")
tx_handler = logging.FileHandler("logs/transactions.log")
tx_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
tx_logger.addHandler(tx_handler)
tx_logger.setLevel(logging.INFO)

class TransactionErrorHandler:
    """
    Handles transaction errors and provides retry mechanisms.
    """

    def __init__(self, web3: Web3, max_retries: int = 3, retry_delay: int = 2):
        """
        Initialize the transaction error handler.

        Args:
            web3: Web3 instance
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.web3 = web3
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger
        self.tx_logger = tx_logger

        # Track nonce usage
        self.last_used_nonce = {}

        # Error classification
        self.gas_related_errors = [
            "gas required exceeds allowance",
            "insufficient funds for gas",
            "gas limit reached",
            "intrinsic gas too low",
            "out of gas",
            "exceeds block gas limit"
        ]

        self.nonce_related_errors = [
            "nonce too low",
            "replacement transaction underpriced",
            "already known",
            "transaction with same nonce in the queue"
        ]

        self.contract_related_errors = [
            "execution reverted",
            "revert",
            "invalid opcode",
            "invalid jump destination"
        ]

        self.rpc_related_errors = [
            "connection failed",
            "timeout",
            "request failed",
            "too many requests",
            "rate limit",
            "internal error",
            "service unavailable"
        ]

    def classify_error(self, error: Exception) -> str:
        """
        Classify the error type to determine appropriate action.

        Args:
            error: The exception that occurred

        Returns:
            str: Error classification
        """
        error_str = str(error).lower()

        # Check for gas-related errors
        for gas_error in self.gas_related_errors:
            if gas_error in error_str:
                return "gas"

        # Check for nonce-related errors
        for nonce_error in self.nonce_related_errors:
            if nonce_error in error_str:
                return "nonce"

        # Check for contract-related errors
        for contract_error in self.contract_related_errors:
            if contract_error in error_str:
                return "contract"

        # Check for RPC-related errors
        for rpc_error in self.rpc_related_errors:
            if rpc_error in error_str:
                return "rpc"

        # Default classification
        return "unknown"

    def extract_revert_reason(self, error: Exception) -> Optional[str]:
        """
        Extract the revert reason from a contract error.

        Args:
            error: The exception that occurred

        Returns:
            Optional[str]: Extracted revert reason or None
        """
        error_str = str(error)

        # Look for common revert reason patterns
        if "execution reverted:" in error_str:
            # Extract reason after "execution reverted:"
            parts = error_str.split("execution reverted:")
            if len(parts) > 1:
                return parts[1].strip()

        # Look for hex-encoded revert reason
        if "0x" in error_str:
            try:
                # Find hex string in the error
                import re
                hex_match = re.search(r'0x[0-9a-fA-F]+', error_str)
                if hex_match:
                    hex_data = hex_match.group(0)
                    # Try to decode as string
                    try:
                        # Remove 0x prefix and function selector (first 8 chars)
                        if len(hex_data) > 10:
                            data = bytes.fromhex(hex_data[10:])
                            # Try to decode as string (skip first 32 bytes which is usually the length)
                            if len(data) > 32:
                                string_length = int.from_bytes(data[0:32], byteorder='big')
                                if 0 < string_length < len(data) - 32:
                                    try:
                                        # Try UTF-8 first
                                        return data[32:32+string_length].decode('utf-8')
                                    except UnicodeDecodeError:
                                        # Fall back to latin-1 which can handle any byte value
                                        return data[32:32+string_length].decode('latin-1')
                    except Exception:
                        pass
            except Exception:
                pass

        return None

    def get_optimal_gas_price(self, base_gas_price: int, retry_count: int = 0) -> int:
        """
        Calculate optimal gas price based on current network conditions and retry count.

        Args:
            base_gas_price: Base gas price in wei
            retry_count: Current retry attempt

        Returns:
            int: Optimal gas price in wei
        """
        # Increase gas price by 10% for each retry
        multiplier = 1.0 + (retry_count * 0.1)

        # Get current network gas price as a fallback
        try:
            current_gas_price = self.web3.eth.gas_price
            # Use the higher of the two
            base_gas_price = max(base_gas_price, current_gas_price)
        except Exception as e:
            self.logger.warning(f"Failed to get current gas price: {e}")

        # Apply multiplier
        new_gas_price = int(base_gas_price * multiplier)

        # Cap at a reasonable maximum (e.g., 300 gwei for Polygon)
        max_gas_price = 300 * 10**9  # 300 gwei in wei
        if new_gas_price > max_gas_price:
            new_gas_price = max_gas_price

        return new_gas_price

    def get_safe_nonce(self, address: str) -> int:
        """
        Get a safe nonce value that won't conflict with pending transactions.

        Args:
            address: The address to get the nonce for

        Returns:
            int: Safe nonce value
        """
        try:
            # Convert address to checksum format
            checksum_address = self.web3.to_checksum_address(address)

            # Get the on-chain nonce
            on_chain_nonce = self.web3.eth.get_transaction_count(checksum_address, 'pending')

            # Check if we have a higher tracked nonce
            last_nonce = self.last_used_nonce.get(checksum_address, 0)
            safe_nonce = max(on_chain_nonce, last_nonce + 1)

            # Update our tracking
            self.last_used_nonce[checksum_address] = safe_nonce

            return safe_nonce
        except Exception as e:
            self.logger.error(f"Error getting safe nonce: {e}")
            # Fallback to just getting the transaction count
            checksum_address = self.web3.to_checksum_address(address)
            return self.web3.eth.get_transaction_count(checksum_address)

    def execute_transaction_with_retry(
        self,
        tx_params: Dict[str, Any],
        private_key: str,
        max_confirmations_wait: int = 180
    ) -> Tuple[bool, Union[str, Dict[str, Any]]]:
        """
        Execute a transaction with automatic retry and error handling.

        Args:
            tx_params: Transaction parameters
            private_key: Private key to sign the transaction
            max_confirmations_wait: Maximum time to wait for confirmations in seconds

        Returns:
            Tuple[bool, Union[str, Dict[str, Any]]]: (success, result)
                If success is True, result is the transaction hash
                If success is False, result is an error message or details
        """
        retry_count = 0
        last_error = None

        # Ensure we have a from address
        if 'from' not in tx_params:
            return False, "Missing 'from' address in transaction parameters"

        from_address = tx_params['from']

        while retry_count <= self.max_retries:
            try:
                # Update nonce on each retry
                if retry_count > 0:
                    tx_params['nonce'] = self.get_safe_nonce(from_address)

                    # Adjust gas price based on retry count
                    if 'gasPrice' in tx_params:
                        tx_params['gasPrice'] = self.get_optimal_gas_price(
                            tx_params['gasPrice'],
                            retry_count
                        )

                # Log transaction attempt
                self.logger.info(f"Sending transaction (attempt {retry_count + 1}/{self.max_retries + 1})")
                self.tx_logger.info(f"Transaction params: {tx_params}")

                # Sign transaction
                signed_tx = self.web3.eth.account.sign_transaction(tx_params, private_key)

                # Send transaction
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hash_hex = tx_hash.hex()

                self.logger.info(f"Transaction sent with hash: {tx_hash_hex}")
                self.tx_logger.info(f"Transaction sent with hash: {tx_hash_hex}")

                # Wait for receipt
                self.logger.info(f"Waiting for transaction receipt (timeout: {max_confirmations_wait}s)...")
                receipt = self.web3.eth.wait_for_transaction_receipt(
                    tx_hash,
                    timeout=max_confirmations_wait
                )

                # Check transaction status
                if receipt['status'] == 1:
                    self.logger.info(f"Transaction successful: {tx_hash_hex}")
                    self.tx_logger.info(f"Transaction successful: {tx_hash_hex}")
                    return True, tx_hash_hex
                else:
                    error_msg = f"Transaction failed with status: {receipt['status']}"
                    self.logger.error(error_msg)
                    self.tx_logger.error(error_msg)

                    # Try to get more details about the failure
                    try:
                        # Try to get transaction trace or revert reason
                        trace_info = self._get_transaction_trace(tx_hash_hex)
                        if trace_info:
                            self.logger.error(f"Transaction trace: {trace_info}")
                            self.tx_logger.error(f"Transaction trace: {trace_info}")
                            return False, {"status": "failed", "hash": tx_hash_hex, "trace": trace_info}
                    except Exception as trace_error:
                        self.logger.warning(f"Failed to get transaction trace: {trace_error}")

                    return False, {"status": "failed", "hash": tx_hash_hex, "receipt": dict(receipt)}

            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)
                revert_reason = self.extract_revert_reason(e)

                error_msg = f"Transaction error ({error_type}): {str(e)}"
                if revert_reason:
                    error_msg += f" - Revert reason: {revert_reason}"

                self.logger.error(error_msg)
                self.tx_logger.error(error_msg)

                # Determine if we should retry based on error type
                if error_type in ["gas", "nonce", "rpc"]:
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        delay = self.retry_delay * (2 ** (retry_count - 1))  # Exponential backoff
                        self.logger.info(f"Retrying in {delay} seconds... (attempt {retry_count + 1}/{self.max_retries + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        return False, {"status": "failed", "error": str(e), "type": error_type, "revert_reason": revert_reason}
                else:
                    # Don't retry contract logic errors
                    return False, {"status": "failed", "error": str(e), "type": error_type, "revert_reason": revert_reason}

        # If we get here, all retries failed
        return False, {"status": "failed", "error": str(last_error), "retries_exhausted": True}

    def _get_transaction_trace(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Try to get a transaction trace for more detailed error information.

        Args:
            tx_hash: Transaction hash

        Returns:
            Optional[Dict[str, Any]]: Transaction trace if available
        """
        try:
            # Try to use debug_traceTransaction if available
            # This is a custom method that might not be available in all Web3 providers
            if hasattr(self.web3, 'provider') and hasattr(self.web3.provider, 'make_request'):
                try:
                    # Using a more generic approach to avoid type issues
                    
                    method = RPCEndpoint("debug_traceTransaction")
                    response = self.web3.provider.make_request(
                        method,
                        [tx_hash]
                    )
                    if response and 'result' in response:
                        return response['result']
                except Exception:
                    pass

            # Try to use Tenderly API if configured
            # This would require additional setup and API keys
            return None
        except Exception as e:
            self.logger.debug(f"Failed to get transaction trace: {e}")
            return None

    def decode_transaction_input(self, tx_hash: str, contract_abi: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Decode transaction input data using the contract ABI.

        Args:
            tx_hash: Transaction hash
            contract_abi: Contract ABI

        Returns:
            Optional[Dict[str, Any]]: Decoded transaction input
        """
        try:
            # Convert tx_hash to proper format
            try:
                # Try to convert to HexBytes
                from hexbytes import HexBytes
                if isinstance(tx_hash, str):
                    if not tx_hash.startswith('0x'):
                        tx_hash = f"0x{tx_hash}"
                    tx_hash_hex = HexBytes(tx_hash)
                else:
                    tx_hash_hex = HexBytes(tx_hash)

                # Get transaction
                tx = self.web3.eth.get_transaction(tx_hash_hex)
            except Exception as e:
                self.logger.error(f"Error converting transaction hash: {e}")
                return None
            if not tx:
                return None

            # Access transaction data using dictionary access
            input_data = tx.get('input', None)
            to_address = tx.get('to', None)

            if not input_data or input_data == '0x' or not to_address:
                return None

            # Create contract object
            contract = self.web3.eth.contract(address=to_address, abi=contract_abi)

            # Decode function input
            func_obj, func_params = contract.decode_function_input(input_data)

            return {
                "function": func_obj.fn_name,
                "params": func_params
            }
        except Exception as e:
            self.logger.error(f"Failed to decode transaction input: {e}")
            return None
