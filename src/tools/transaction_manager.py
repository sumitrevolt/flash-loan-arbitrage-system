import logging
from src.utils.web3_provider import get_web3_instance, WEB3_IMPORTED
from src.blockchain.rpc_manager import RPCManager

logger = logging.getLogger(__name__)

def requires_web3(func):
    """Decorator to check if Web3 is available before executing function"""
    def wrapper(*args, **kwargs):
        if not WEB3_IMPORTED:
            logger.error(f"Web3 required for {func.__name__} but not available")
            return None
        return func(*args, **kwargs)
    return wrapper



from .rpc_manager import get_rpc_manager

class TransactionManager:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rpc_manager = RPCManager()
        self.web3 = get_web3_instance(apply_poa=True)
        
    def refresh_web3(self):
        """Get a fresh web3 instance from RPCManager to ensure we're using the current RPC"""
        self.web3 = self.rpc_manager.get_web3()
        
    def send_transaction(self, signed_tx, timeout=300):
        """Send a transaction and wait for receipt with improved reliability"""
        try:
            # Extract transaction details for diagnostics
            if hasattr(signed_tx, 'rawTransaction'):
                # It's a signed transaction object
                tx_raw = signed_tx.rawTransaction
                self.logger.info(f"[TX DIAGNOSTICS] Sending signed transaction with raw data length: {len(tx_raw) if tx_raw else 0}")
            else:
                # It's likely a dict
                tx_dict = signed_tx if isinstance(signed_tx, dict) else {}
                
                # Log nonce and gas diagnostics
                self.logger.info(f"[NONCE DIAGNOSTICS] Transaction nonce: {tx_dict.get('nonce', 'N/A')}")
                self.logger.info(f"[GAS DIAGNOSTICS] Gas price: {tx_dict.get('gasPrice', 'N/A')}, Gas limit: {tx_dict.get('gas', 'N/A')}")
                
                # Get current network state for comparison
                try:
                    from_addr = tx_dict.get('from')
                    if from_addr and self.web3:
                        current_nonce = self.web3.eth.get_transaction_count(from_addr)
                        current_gas_price = self.web3.eth.gas_price
                        self.logger.info(f"[NONCE DIAGNOSTICS] Current network nonce for {from_addr}: {current_nonce}")
                        self.logger.info(f"[GAS DIAGNOSTICS] Current network gas price: {current_gas_price}")
                        
                        # Check for nonce mismatch
                        if 'nonce' in tx_dict and tx_dict['nonce'] < current_nonce:
                            self.logger.warning(f"[NONCE WARNING] Transaction nonce ({tx_dict['nonce']}) is lower than current nonce ({current_nonce})")
                        
                        # Check for underpriced gas
                        if 'gasPrice' in tx_dict and int(tx_dict['gasPrice']) < int(current_gas_price * 0.9):
                            self.logger.warning(f"[GAS WARNING] Transaction gas price may be too low: {tx_dict['gasPrice']} < {current_gas_price * 0.9}")
                except Exception as diag_e:
                    self.logger.debug(f"Could not perform diagnostic checks: {diag_e}")
            
            tx_hash = self.rpc_manager.send_transaction(signed_tx)
            self.logger.info(f"Transaction sent: {tx_hash}")
            
            # Wait for transaction receipt
            receipt = self.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            if not receipt:
                self.logger.error(f"Failed to get receipt for transaction {tx_hash} within {timeout} seconds")
                return None, None
                
            status = receipt.get('status')
            if status == 1:
                self.logger.info(f"Transaction {tx_hash} confirmed successfully")
            else:
                self.logger.error(f"Transaction {tx_hash} failed with status: {status}")
                
            return tx_hash, receipt
            
        except Exception as e:
            self.logger.error(f"Error sending transaction: {str(e)}")
            self.logger.error(f"[TRANSACTION ERROR DETAILS] {type(e).__name__}: {str(e)}")
            return None, None
            
    def wait_for_transaction_receipt(self, tx_hash, timeout=300):
        """
        Wait for a transaction receipt with improved error handling
        
        Args:
            tx_hash: Transaction hash (hex string)
            timeout: Maximum time to wait in seconds
            
        Returns:
            Transaction receipt or None if not found within timeout
        """
        if isinstance(tx_hash, str) and not tx_hash.startswith('0x'):
            tx_hash = f"0x{tx_hash}"
            
        receipt = self.rpc_manager.get_transaction_receipt(
            tx_hash, 
            timeout=timeout,
            poll_latency=2,
            exponential_backoff=True
        )
        
        if receipt and receipt.get('status') == 1:
            self.logger.info(f"Transaction {tx_hash} was successful")
        elif receipt:
            self.logger.error(f"Transaction {tx_hash} failed with status: {receipt.get('status')}")
            
        return receipt
        
    def verify_transaction_success(self, tx_hash, receipt=None):
        """Verify that a transaction was successful"""
        if not receipt:
            receipt = self.wait_for_transaction_receipt(tx_hash)
            
        if not receipt:
            self.logger.error(f"Cannot verify transaction {tx_hash}: No receipt available")
            return False
            
        status = receipt.get('status')
        if status != 1:
            self.logger.error(f"Transaction {tx_hash} failed with status: {status}")
            return False
            
        self.logger.info(f"Transaction {tx_hash} confirmed successfully with status: {status}")
        return True
        
    def get_gas_estimate(self, tx):
        """Get gas estimate with improved error handling that extracts revert reasons"""
        try:
            # First try to simulate the transaction to get a better error message if it fails
            self.rpc_manager.make_eth_call(tx)
            
            # If simulation succeeds, estimate gas
            gas_estimate = self.rpc_manager.estimate_gas(tx)
            return gas_estimate
            
        except Exception as e:
            # Extract revert reason if available
            error_msg = str(e)
            revert_reason = self._extract_revert_reason(error_msg)
            
            if revert_reason:
                self.logger.error(f"Transaction would revert: {revert_reason}")
            else:
                self.logger.error(f"Failed to estimate gas: {error_msg}")
                
            raise
            
    def _extract_revert_reason(self, error_message):
        """Extract a human-readable revert reason from error message if possible"""
        # Common patterns in revert messages
        if "execution reverted" in error_message:
            # Try to extract more specific reason
            if "execution reverted:" in error_message:
                parts = error_message.split("execution reverted:")
                if len(parts) > 1:
                    return parts[1].strip()
        
        return None

# Transaction manager now only uses real RPCManager - no mock implementations
