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
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3



from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def update_transaction_executor():
    """Update the transaction executor to use the correct function signatures"""
    try:
        # Path to transaction executor
        file_path = "core/transaction_executor.py"
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update direct arbitrage function
        content = content.replace(
            "self._flash_loan_contract.functions.executeArbitrage(",
            "self._flash_loan_contract.functions.executeDirectArbitrage("
        )
        
        # Update direct arbitrage function parameters
        content = content.replace(
            """                            # New contract with minAmountOut parameter
                            gas_estimate = self._flash_loan_contract.functions.executeArbitrage(
                                token1_address,
                                token2_address,
                                dex1_address,
                                dex2_address,
                                amount,
                                min_amount_out
                            ).estimate_gas({'from': self._wallet_address})""",
            """                            # New contract with expected outputs, fee tiers, and price limits
                            expected_outputs = [int(amount * 0.99), int(amount * 0.98)]  # 1% and 2% slippage
                            fee_tiers = [3000, 3000]  # Default fee tier for both swaps
                            price_limits = [0, 0]  # No price limits
                            
                            gas_estimate = self._flash_loan_contract.functions.executeDirectArbitrage(
                                token1_address,
                                token2_address,
                                dex1_address,
                                dex2_address,
                                amount,
                                expected_outputs,
                                fee_tiers,
                                price_limits
                            ).estimate_gas({'from': self._wallet_address})"""
        )
        
        # Update direct arbitrage transaction building
        content = content.replace(
            """                    # New contract with expected outputs, fee tiers, and price limits
                    expected_outputs = [int(amount * 0.99), int(amount * 0.98)]  # 1% and 2% slippage
                    fee_tiers = [3000, 3000]  # Default fee tier for both swaps
                    price_limits = [0, 0]  # No price limits
                    
                    tx = self._flash_loan_contract.functions.executeDirectArbitrage(
                        token1_address,
                        token2_address,
                        dex1_address,
                        dex2_address,
                        amount,
                        expected_outputs,
                        fee_tiers,
                        price_limits
                    ).build_transaction(tx_dict)  # type: ignore""",
            """                    # New contract with expected outputs, fee tiers, and price limits
                    expected_outputs = [int(amount * 0.99), int(amount * 0.98)]  # 1% and 2% slippage
                    fee_tiers = [3000, 3000]  # Default fee tier for both swaps
                    price_limits = [0, 0]  # No price limits
                    
                    # Create properly typed transaction parameters
                    tx_params: TxParams = {
                        'from': self._wallet_address,
                        'nonce': Nonce(self._web3.eth.get_transaction_count(self._wallet_address)),
                        'gas': Wei(3000000),
                        'gasPrice': Wei(self._web3.eth.gas_price),
                        'chainId': self._web3.eth.chain_id,
                        'value': Wei(0)
                    }
                    
                    tx = self._flash_loan_contract.functions.executeDirectArbitrage(
                        token1_address,
                        token2_address,
                        dex1_address,
                        dex2_address,
                        amount,
                        expected_outputs,
                        fee_tiers,
                        price_limits
                    ).build_transaction(tx_params)"""
        )
        
        # Update triangular arbitrage function parameters
        content = content.replace(
            """                            # New contract with minAmountOut parameter
                            gas_estimate = self._flash_loan_contract.functions.executeTriangularArbitrage(
                                token1_address,
                                token2_address,
                                token3_address,
                                dex_address,
                                amount,
                                min_amount_out
                            ).estimate_gas({'from': self._wallet_address})""",
            """                            # New contract with expected outputs, fee tiers, and price limits
                            expected_outputs = [int(amount * 0.99), int(amount * 0.98), int(amount * 0.97)]  # 1%, 2%, 3% slippage
                            fee_tiers = [3000, 3000, 3000]  # Default fee tier for all swaps
                            price_limits = [0, 0, 0]  # No price limits
                            
                            gas_estimate = self._flash_loan_contract.functions.executeTriangularArbitrage(
                                token1_address,
                                token2_address,
                                token3_address,
                                dex_address,
                                amount,
                                expected_outputs,
                                fee_tiers,
                                price_limits
                            ).estimate_gas({'from': self._wallet_address})"""
        )
        
        # Update triangular arbitrage transaction building
        content = content.replace(
            """                    # New contract with expected outputs, fee tiers, and price limits
                    expected_outputs = [int(amount * 0.99), int(amount * 0.98), int(amount * 0.97)]  # 1%, 2%, 3% slippage
                    fee_tiers = [3000, 3000, 3000]  # Default fee tier for all swaps
                    price_limits = [0, 0, 0]  # No price limits
                    
                    tx = self._flash_loan_contract.functions.executeTriangularArbitrage(
                        token1_address,
                        token2_address,
                        token3_address,
                        dex_address,
                        amount,
                        expected_outputs,
                        fee_tiers,
                        price_limits
                    ).build_transaction(tx_dict)  # type: ignore""",
            """                    # New contract with expected outputs, fee tiers, and price limits
                    expected_outputs = [int(amount * 0.99), int(amount * 0.98), int(amount * 0.97)]  # 1%, 2%, 3% slippage
                    fee_tiers = [3000, 3000, 3000]  # Default fee tier for all swaps
                    price_limits = [0, 0, 0]  # No price limits
                    
                    # Create properly typed transaction parameters
                    tx_params: TxParams = {
                        'from': self._wallet_address,
                        'nonce': Nonce(self._web3.eth.get_transaction_count(self._wallet_address)),
                        'gas': Wei(3500000),
                        'gasPrice': Wei(self._web3.eth.gas_price),
                        'chainId': self._web3.eth.chain_id,
                        'value': Wei(0)
                    }
                    
                    tx = self._flash_loan_contract.functions.executeTriangularArbitrage(
                        token1_address,
                        token2_address,
                        token3_address,
                        dex_address,
                        amount,
                        expected_outputs,
                        fee_tiers,
                        price_limits
                    ).build_transaction(tx_params)"""
        )
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Transaction executor updated successfully")
    
    except Exception as e:
        logger.error(f"Error updating transaction executor: {e}")

if __name__ == "__main__":
    update_transaction_executor()
