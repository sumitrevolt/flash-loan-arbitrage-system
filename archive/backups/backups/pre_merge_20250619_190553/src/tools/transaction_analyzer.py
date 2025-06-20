"""
Transaction analyzer for flash loan arbitrage.

This module provides functions to analyze failed transactions and
extract detailed error information.
"""

import logging
import json
import re
import time
from typing import Dict, Any, Optional, List, Tuple, Union

# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3

# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)
# Set up logging
logger = logging.getLogger(__name__)

class TransactionAnalyzer:
    """
    Analyzes blockchain transactions to extract detailed error information.
    """

    def __init__(self, web3_instance, debug_mode: bool = False):
        """
        Initialize the transaction analyzer.

        Args:
            web3_instance: Web3 instance
            debug_mode: Whether to enable debug mode
        """
        self.web3 = web3_instance
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)

        # Common error signatures and their meanings
        self.error_signatures = {
            # Aave flash loan errors
            "0x5a68151d": "Aave: Invalid flash loan parameters",
            "0x3e3f8f73": "Aave: Insufficient liquidity",
            "0x9e87fac8": "Aave: Flash loan callback failed",

            # Common contract errors
            "0x08c379a0": "Error(string)",  # Standard error string
            "0x4e487b71": "Panic(uint256)",  # Panic error

            # Custom contract errors
            "0x7939f424": "NoProfit()",
            "0x1f2a2005": "InsufficientRepayment()",
            "0x7c1f8113": "InvalidToken()",
            "0x3323e6ff": "InvalidDEX()",
            "0x4ddf4a64": "FailedSwap()",
            "0x9cb10b50": "Unauthorized()",
            "0x3db1f9af": "InvalidAmount()",
            "0x3499f8f7": "InvalidAddress()",
        }

    @requires_web3
    def analyze_transaction(self, tx_hash: str, receipt: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze a transaction to extract detailed error information.

        Args:
            tx_hash: Transaction hash
            receipt: Transaction receipt (may be used in future implementations)

        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            from hexbytes import HexBytes
            
            # Get transaction details
            tx = self.web3.eth.get_transaction(tx_hash)
            if receipt is None:
                receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            
            result: str = {
                "transaction_hash": tx_hash,
                "success": receipt.get('status', 0) == 1,
                "gas_used": receipt.get('gasUsed', 0),
                "gas_limit": tx.get('gas', 0),
                "block_number": receipt.get('blockNumber', 0),
                "block_timestamp": self.get_block_timestamp(receipt.get('blockNumber', 0)),
                "from_address": tx.get('from', ''),
                "to_address": tx.get('to', ''),
                "value": tx.get('value', 0),
                "gas_price": tx.get('gasPrice', 0),
                "logs": self.parse_logs(receipt.get('logs', [])),
            }

            # If transaction failed, extract error information
            if not result["success"]:
                error_info = self.extract_error_info(receipt, tx)
                result.update(error_info)

                # Try to get transaction trace for more detailed error analysis
                trace = self.get_transaction_trace(tx_hash)
                if trace:
                    result["trace"] = trace
                    revert_reason = self.extract_revert_reason(trace)
                    if revert_reason:
                        result["revert_reason"] = revert_reason

                # Decode error from input data
                decoded_error = self.decode_error_from_input(tx.get('input', ''))
                if decoded_error:
                    result["decoded_error"] = decoded_error

            return result

        except Exception as e:
            self.logger.error(f"Error analyzing transaction {tx_hash}: {e}")
            return {
                "transaction_hash": tx_hash,
                "error": str(e),
                "success": False
            }

    def get_block_timestamp(self, block_number: int) -> int:
        """
        Get the timestamp of a block.

        Args:
            block_number: Block number

        Returns:
            int: Block timestamp
        """
        try:
            if block_number == 0:
                return 0
            block = self.web3.eth.get_block(block_number)
            return block.get('timestamp', 0)
        except Exception as e:
            self.logger.error(f"Error getting block timestamp for block {block_number}: {e}")
            return 0

    def extract_error_info(self, receipt: Dict, tx: Dict) -> Dict[str, Any]:
        """
        Extract error information from a failed transaction.

        Args:
            receipt: Transaction receipt (may be used in future implementations)
            tx: Transaction details

        Returns:
            Dict[str, Any]: Error information
        """
        error_info = {
            "error_type": "unknown",
            "error_message": "Transaction failed",
        }

        try:
            # Check for known error patterns in logs
            logs = receipt.get('logs', [])
            for log in logs:
                topics = log.get('topics', [])
                if topics:
                    error_signature = topics[0].hex() if hasattr(topics[0], 'hex') else str(topics[0])
                    if error_signature in self.error_signatures:
                        error_info["error_type"] = "contract_error"
                        error_info["error_message"] = self.error_signatures[error_signature]
                        break

            # Check transaction input for error patterns
            input_data = tx.get('input', '')
            if input_data and len(input_data) >= 10:
                method_signature = input_data[:10]
                if method_signature in self.error_signatures:
                    error_info["error_type"] = "method_error"
                    error_info["error_message"] = self.error_signatures[method_signature]

        except Exception as e:
            self.logger.error(f"Error extracting error info: {e}")

        return error_info

    def get_transaction_trace(self, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction trace using debug_traceTransaction.

        Args:
            tx_hash: Transaction hash

        Returns:
            Optional[Dict]: Transaction trace
        """
        try:
            # This requires a node with debug API enabled
            trace = self.web3.manager.request_blocking("debug_traceTransaction", [tx_hash, {"tracer": "callTracer"}])
            return trace
        except Exception as e:
            if self.debug_mode:
                self.logger.debug(f"Could not get transaction trace for {tx_hash}: {e}")
            return None

    def extract_revert_reason(self, trace: Dict) -> Optional[str]:
        """
        Extract revert reason from transaction trace.

        Args:
            trace: Transaction trace

        Returns:
            Optional[str]: Revert reason
        """
        try:
            # Look for revert reason in the trace
            if isinstance(trace, dict):
                if 'error' in trace:
                    return trace['error']
                if 'revertReason' in trace:
                    return trace['revertReason']
                
                # Check calls recursively
                calls = trace.get('calls', [])
                for call in calls:
                    reason = self.extract_revert_reason(call)
                    if reason:
                        return reason
                        
            return None
        except Exception as e:
            self.logger.error(f"Error extracting revert reason: {e}")
            return None

    def decode_error_from_input(self, input_data: str) -> Optional[Dict[str, Any]]:
        """
        Decode error information from transaction input data.

        Args:
            input_data: Transaction input data

        Returns:
            Optional[Dict[str, Any]]: Decoded error information
        """
        try:
            if not input_data or len(input_data) < 10:
                return None

            method_signature = input_data[:10]
            if method_signature in self.error_signatures:
                return {
                    "method_signature": method_signature,
                    "error_name": self.error_signatures[method_signature],
                    "input_data": input_data
                }

            return None
        except Exception as e:
            self.logger.error(f"Error decoding error from input: {e}")
            return None

    def parse_logs(self, logs: List[Dict]) -> List[Dict]:
        """
        Parse transaction logs.

        Args:
            logs: Transaction logs

        Returns:
            List[Dict]: Parsed logs
        """
        parsed_logs = []
        for log in logs:
            parsed_log = {
                "address": log.get("address", ""),
                "topics": [topic.hex() if hasattr(topic, 'hex') else str(topic) for topic in log.get("topics", [])],
                "data": log.get("data", ""),
                "block_number": log.get("blockNumber", 0),
                "transaction_hash": log.get("transactionHash", ""),
                "log_index": log.get("logIndex", 0)
            }
            parsed_logs.append(parsed_log)
        return parsed_logs

# Create a default analyzer instance for module-level functions
default_analyzer = None

def analyze_failed_transaction(tx_hash: str, web3_instance=None) -> Dict[str, Any]:
    """
    Analyze a failed transaction and return detailed error information.
    
    Args:
        tx_hash: Hash of the failed transaction
        web3_instance: Web3 instance (optional)
        
    Returns:
        Dict containing detailed error analysis
    """
    global default_analyzer
    
    if web3_instance is None:
        # Try to use default analyzer
        if default_analyzer is None:
            logger.error("No Web3 instance provided and no default analyzer available")
            return {"error": "No Web3 instance available"}
        analyzer = default_analyzer
    else:
        analyzer = TransactionAnalyzer(web3_instance)
    
    return analyzer.analyze_transaction(tx_hash)

def set_default_analyzer(web3_instance):
    """Set the default analyzer for module-level functions."""
    global default_analyzer
    default_analyzer = TransactionAnalyzer(web3_instance)

# Module-level convenience functions using the default analyzer
def analyze_transaction(tx_hash: str) -> Dict[str, Any]:
    """
    Analyze a transaction to extract detailed error information.

    Args:
        tx_hash: Transaction hash

    Returns:
        Dict[str, Any]: Analysis results
    """
    return analyze_failed_transaction(tx_hash)

def get_block_timestamp(block_number: int) -> int:
    """
    Get the timestamp of a block.

    Args:
        block_number: Block number

    Returns:
        int: Block timestamp
    """
    global default_analyzer
    if default_analyzer is None:
        logger.error("No default analyzer available")
        return 0
    return default_analyzer.get_block_timestamp(block_number)

def extract_error_info(tx_hash: str, receipt: Optional[Dict] = None, tx: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Extract error information from a failed transaction.

    Args:
        tx_hash: Transaction hash
        receipt: Transaction receipt (may be used in future implementations)
        tx: Transaction details

    Returns:
        Dict[str, Any]: Error information
    """
    global default_analyzer
    if default_analyzer is None:
        logger.error("No default analyzer available")
        return {"error": "No default analyzer available"}
    
    if receipt is None or tx is None:
        # Get transaction and receipt
        try:
            if receipt is None:
                receipt = default_analyzer.web3.eth.get_transaction_receipt(tx_hash)
            if tx is None:
                tx = default_analyzer.web3.eth.get_transaction(tx_hash)
        except Exception as e:
            logger.error(f"Error getting transaction data: {e}")
            return {"error": str(e)}
    
    return default_analyzer.extract_error_info(receipt, tx)

def get_transaction_trace(tx_hash: str) -> Optional[Dict[str, Any]]:
    """
    Get transaction trace using debug_traceTransaction.

    Args:
        tx_hash: Transaction hash

    Returns:
        Optional[Dict[str, Any]]: Transaction trace
    """
    global default_analyzer
    if default_analyzer is None:
        logger.error("No default analyzer available")
        return None
    return default_analyzer.get_transaction_trace(tx_hash)

def extract_revert_reason(trace: Dict) -> Optional[str]:
    """
    Extract revert reason from transaction trace.

    Args:
        trace: Transaction trace

    Returns:
        Optional[str]: Revert reason
    """
    global default_analyzer
    if default_analyzer is None:
        logger.error("No default analyzer available")
        return None
    return default_analyzer.extract_revert_reason(trace)

def decode_error_from_input(input_data: str) -> Optional[Dict[str, Any]]:
    """
    Decode error information from transaction input data.

    Args:
        input_data: Transaction input data

    Returns:
        Optional[Dict[str, Any]]: Decoded error information
    """
    global default_analyzer
    if default_analyzer is None:
        logger.error("No default analyzer available")
        return None
    return default_analyzer.decode_error_from_input(input_data)

def parse_logs(logs: List[Dict]) -> List[Dict[str, Any]]:
    """
    Parse transaction logs.

    Args:
        logs: Transaction logs

    Returns:
        List[Dict[str, Any]]: Parsed logs
    """
    global default_analyzer
    if default_analyzer is None:
        logger.error("No default analyzer available")
        return []
    return default_analyzer.parse_logs(logs)
