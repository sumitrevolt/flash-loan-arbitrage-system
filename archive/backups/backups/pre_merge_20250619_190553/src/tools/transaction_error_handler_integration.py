"""
Transaction Error Handler Integration
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3


This module integrates the TransactionErrorHandler with the existing
transaction execution code in the flash loan system.
"""

import logging
import os
# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)
# Import the transaction error handler
from flash_loan.core.transaction_error_handler import TransactionErrorHandler

# Configure logging
logger = logging.getLogger("TransactionErrorHandlerIntegration")
if not os.path.exists("logs"):
    os.makedirs("logs")
file_handler = logging.FileHandler("logs/transaction_integration.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def integrate_with_transaction_executor(transaction_executor):
    """
    Integrate the TransactionErrorHandler with an existing TransactionExecutor.

    Args:
        transaction_executor: The transaction executor instance to enhance
    """
    # Check if we already integrated
    # Use getattr with a default value to avoid attribute errors
    if getattr(transaction_executor, '_error_handler_integrated', False):
        logger.info("Transaction error handler already integrated")
        return

    # Store original methods for potential future use or rollback
    # We're not using these variables directly, but keeping them for reference
    # and potential future enhancement to add a rollback mechanism
    _ = transaction_executor.wait_for_transaction_receipt  # Original wait_for_receipt method
    _ = transaction_executor.execute_flash_loan_arbitrage  # Original execute_flash_loan_arbitrage method

    # Create error handler
    error_handler = TransactionErrorHandler(
        web3=transaction_executor.web3,
        max_retries=3,
        retry_delay=2
    )

    # Store the error handler
    transaction_executor.error_handler = error_handler

    # Enhance execute_flash_loan_arbitrage method
    original_execute_flash_loan = transaction_executor.execute_flash_loan_arbitrage

    def enhanced_execute_flash_loan_arbitrage(token_address, amount, buy_dex_router, sell_dex_router, expected_profit=0.0):
        """Enhanced flash loan arbitrage execution with better error handling"""
        logger.info("Using enhanced flash loan arbitrage execution with error handling")

        try:
            # Get the wallet address and private key
            wallet_address = getattr(transaction_executor, 'wallet_address', None)
            private_key = getattr(transaction_executor, 'private_key', None)

            if not wallet_address or not private_key:
                logger.error("Wallet address or private key not available")
                return False, "Wallet configuration missing"

            # Get the contract
            contract = getattr(transaction_executor, 'flashloan_contract', None)
            if not contract:
                logger.error("Flash loan contract not available")
                return False, "Contract not available"

            # Build the transaction
            try:
                # Get the current nonce and gas price
                web3 = transaction_executor.web3
                nonce = web3.eth.get_transaction_count(wallet_address)
                gas_price = web3.eth.gas_price

                # Build the transaction
                tx_data = {
                    'from': wallet_address,
                    'nonce': nonce,
                    'gasPrice': int(gas_price * 1.1),  # 10% higher than current gas price
                    'gas': 3000000,  # High gas limit for flash loans
                    'chainId': web3.eth.chain_id
                }

                # Execute with retry using our error handler
                success, result: str = error_handler.execute_transaction_with_retry(
                    tx_params=tx_data,
                    private_key=private_key,
                    max_confirmations_wait=getattr(transaction_executor, 'max_confirmations_wait', 180)
                )

                if success:
                    logger.info(f"Flash loan arbitrage executed successfully: {result}")
                    return True, result
                else:
                    logger.error(f"Flash loan arbitrage failed: {result}")
                    return False, str(result) if not isinstance(result, str) else result

            except Exception as e:
                logger.error(f"Error building transaction: {e}")
                # Fall back to original method
                return original_execute_flash_loan(token_address, amount, buy_dex_router, sell_dex_router, expected_profit)

        except Exception as e:
            logger.error(f"Error in enhanced execute_flash_loan_arbitrage: {e}")
            # Fall back to original method
            return original_execute_flash_loan(token_address, amount, buy_dex_router, sell_dex_router, expected_profit)

    # Replace wait_for_receipt method
    def enhanced_wait_for_receipt(tx_hash, timeout=180):
        """Enhanced wait for receipt with better error handling"""
        logger.info(f"Using enhanced wait for receipt with error handling for tx: {tx_hash}")

        try:
            # Try to get receipt with exponential backoff
            

            # Start with a short polling interval
            poll_latency = 0.1

            # Track time spent waiting
            import time
            start_time = time.time()
            elapsed = 0

            while elapsed < timeout:
                try:
                    receipt = transaction_executor.web3.eth.get_transaction_receipt(tx_hash)
                    if receipt is not None:
                        logger.info(f"Got receipt for tx {tx_hash}")
                        return receipt
                except TransactionNotFound:
                    # Transaction not yet mined
                    pass

                # Sleep with exponential backoff
                time.sleep(poll_latency)
                poll_latency = min(poll_latency * 1.5, 5)  # Cap at 5 seconds

                # Update elapsed time
                elapsed = time.time() - start_time

            # If we get here, we timed out
            raise TimeExhausted(
                f"Transaction {tx_hash} not mined within {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Error waiting for receipt: {e}")
            raise

    # Replace the methods
    transaction_executor.execute_flash_loan_arbitrage = enhanced_execute_flash_loan_arbitrage
    transaction_executor.wait_for_transaction_receipt = enhanced_wait_for_receipt

    # Mark as integrated
    transaction_executor._error_handler_integrated = True

    logger.info("Transaction error handler successfully integrated")
