"""
System Status Check for Flash Loan Arbitrage
Checks transaction status and identifies failures without Unicode issues
"""

import os
import sys
import requests
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import logging

# Configure logging to avoid Unicode issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_status.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemStatusChecker:
    def __init__(self):
        load_dotenv()
        self.setup_web3()
        self.load_contract()
        self.foundry_server_url = "http://localhost:8002"
    
    def setup_web3(self):
        """Initialize Web3 connection"""
        polygon_rpc = os.getenv('POLYGON_RPC_URL')
        self.web3 = Web3(Web3.HTTPProvider(polygon_rpc))
        
        if not self.web3.is_connected():
            logger.error("Failed to connect to Polygon network")
            sys.exit(1)
        
        logger.info(f"Connected to Polygon (Chain ID: {self.web3.eth.chain_id})")
        
        # Load account
        private_key = os.getenv('WALLET_PRIVATE_KEY')
        self.account = Account.from_key(private_key)
        logger.info(f"Account loaded: {self.account.address}")
    
    def load_contract(self):
        """Load the smart contract"""
        contract_address = os.getenv('CONTRACT_ADDRESS')
        
        with open('arbitrage_abi.json', 'r') as f:
            contract_abi = json.load(f)
        
        self.contract = self.web3.eth.contract(
            address=contract_address,
            abi=contract_abi
        )
        logger.info(f"Contract loaded: {contract_address}")
    
    def check_foundry_server(self):
        """Check if Foundry MCP server is running"""
        try:
            response = requests.get(f"{self.foundry_server_url}/info", timeout=5)
            if response.status_code == 200:
                logger.info("Foundry MCP Server: Available")
                return True
            else:
                logger.warning(f"Foundry MCP Server: Status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Foundry MCP Server: Not Available - {str(e)}")
            return False
    
    def check_circuit_breaker(self):
        """Check circuit breaker status"""
        try:
            failed_count = self.contract.functions.getFailedTransactionsCount().call()
            max_failures = self.contract.functions.MAX_FAILED_TRANSACTIONS().call()
            
            logger.info(f"Circuit Breaker Status:")
            logger.info(f"  Failed transactions: {failed_count}/{max_failures}")
            
            if failed_count >= max_failures:
                logger.error("Circuit breaker is TRIPPED")
                return False
            else:
                logger.info("Circuit breaker is OK")
                return True
                
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
            return False
    
    def check_account_balance(self):
        """Check account ETH balance"""
        try:
            balance_wei = self.web3.eth.get_balance(self.account.address)
            balance_eth = self.web3.from_wei(balance_wei, 'ether')
            logger.info(f"Account balance: {balance_eth:.6f} MATIC")
            
            if balance_eth < 0.01:
                logger.warning("Low balance warning: Less than 0.01 MATIC")
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return False
    
    def check_recent_transactions(self):
        """Check recent transactions for failures"""
        try:
            # Get recent blocks to find transactions
            latest_block = self.web3.eth.get_block('latest')
            logger.info(f"Latest block: {latest_block.number}")
            
            # Check last 10 blocks for our transactions
            failed_txs = []
            successful_txs = []
            
            for block_num in range(latest_block.number - 10, latest_block.number + 1):
                try:
                    block = self.web3.eth.get_block(block_num, full_transactions=True)
                    for tx in block.transactions:
                        if tx['from'].lower() == self.account.address.lower():
                            receipt = self.web3.eth.get_transaction_receipt(tx.hash)
                            if receipt.status == 0:
                                failed_txs.append(tx.hash.hex())
                            else:
                                successful_txs.append(tx.hash.hex())
                except Exception:
                    continue
            
            logger.info(f"Recent transactions found:")
            logger.info(f"  Successful: {len(successful_txs)}")
            logger.info(f"  Failed: {len(failed_txs)}")
            
            if failed_txs:
                logger.warning("Recent failed transactions:")
                for tx_hash in failed_txs[-5:]:  # Show last 5 failures
                    logger.warning(f"  {tx_hash}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking recent transactions: {e}")
            return False
    
    def run_full_check(self):
        """Run complete system status check"""
        logger.info("=" * 60)
        logger.info("FLASH LOAN ARBITRAGE SYSTEM STATUS CHECK")
        logger.info("=" * 60)
        
        checks = {
            "Foundry MCP Server": self.check_foundry_server(),
            "Circuit Breaker": self.check_circuit_breaker(),
            "Account Balance": self.check_account_balance(),
            "Recent Transactions": self.check_recent_transactions()
        }
        
        logger.info("\nSUMMARY:")
        logger.info("-" * 40)
        
        all_ok = True
        for check_name, result in checks.items():
            status = "OK" if result else "FAILED"
            logger.info(f"{check_name}: {status}")
            if not result:
                all_ok = False
        
        logger.info("-" * 40)
        
        if all_ok:
            logger.info("SYSTEM STATUS: HEALTHY")
            logger.info("No immediate issues detected")
        else:
            logger.error("SYSTEM STATUS: ISSUES DETECTED")
            logger.error("Manual intervention may be required")
        
        return all_ok

def main():
    try:
        checker = SystemStatusChecker()
        checker.run_full_check()
    except KeyboardInterrupt:
        logger.info("Status check interrupted by user")
    except Exception as e:
        logger.error(f"System check failed: {e}")

if __name__ == "__main__":
    main()
