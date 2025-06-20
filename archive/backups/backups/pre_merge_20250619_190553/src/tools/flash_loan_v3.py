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



def calculate_arbitrage_amount(self, token_symbol, trade_size_usd, token_price):
        """Calculate the amount of tokens to arbitrage based on USD value"""
        try:
            # Calculate token amount based on USD value
            token_amount = trade_size_usd / token_price
            
            # Get token decimals
            token_address = self.token_addresses.get(token_symbol)
            if not token_address:
                self.logger.error(f"Token address not found for {token_symbol}")
                return 0
                
            # Get decimals from contract
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=[{"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}]
            )
            
            try:
                decimals = token_contract.functions.decimals().call()
            except:
                # Default to 18 decimals if call fails
                decimals = 18
                
            # Convert to wei/smallest unit
            amount_in_wei = int(token_amount * (10 ** decimals))
            
            # Ensure minimum amount (at least 1 token)
            min_amount = 10 ** decimals
            if amount_in_wei < min_amount:
                amount_in_wei = min_amount
                
            self.logger.info(f"Calculated arbitrage amount for {token_symbol}: {amount_in_wei} wei ({token_amount:.6f} tokens)")
            return amount_in_wei
            
        except Exception as e:
            self.logger.error(f"Error calculating arbitrage amount for {token_symbol}: {e}")
            return 0