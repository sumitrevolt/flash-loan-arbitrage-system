#!/usr/bin/env python3
"""
Flash Loan Contract Deployment Script
Deploys the FlashLoanArbitrageFixed contract using environment variables
"""

import os
import sys
import json
import time
from decimal import Decimal
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
import subprocess
import logging
from typing import Dict, Any, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ContractDeployer")

class ContractDeployer:
    def __init__(self):
        """Initialize the contract deployer"""
        # Load environment variables
        load_dotenv()
        
        # Get credentials from environment
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.private_key = os.getenv('PRIVATE_KEY')
        self.polygon_rpc = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
        
        if not self.wallet_address or not self.private_key:
            raise ValueError("WALLET_ADDRESS and PRIVATE_KEY must be set in .env file")
        
        # Initialize Web3
        self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
        if not self.web3.is_connected():
            raise ConnectionError(f"Failed to connect to Polygon RPC: {self.polygon_rpc}")
        
        # Load account
        self.account = Account.from_key(self.private_key)
        logger.info(f"Loaded account: {self.account.address}")
        
        # Verify wallet address matches private key
        if self.account.address.lower() != self.wallet_address.lower():
            raise ValueError("Wallet address doesn't match private key")
        
        # Contract configuration
        self.contract_file = "core/contracts/FlashLoanArbitrageFixed.sol"
        self.constructor_args = {
            "aave_pool_provider": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"  # Aave V3 Pool Address Provider on Polygon
        }
        
        logger.info(f"Connected to Polygon network (Chain ID: {self.web3.eth.chain_id})")
        logger.info(f"Account balance: {self.web3.from_wei(self.web3.eth.get_balance(self.account.address), 'ether')} MATIC")
    
    def compile_contract(self) -> Dict[str, Any]:
        """Compile the contract using Foundry forge"""
        logger.info("Compiling contract...")
        
        try:
            # Check if foundry is installed
            result = subprocess.run(['forge', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("Foundry forge not found. Please install Foundry first.")
            
            logger.info(f"Using Foundry: {result.stdout.strip()}")
            
            # Compile the contract
            compile_cmd = [
                'forge', 'build',
                '--optimize',
                '--optimizer-runs', '200',
                '--out', 'out'
            ]
            
            result = subprocess.run(compile_cmd, capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode != 0:
                logger.error(f"Compilation failed: {result.stderr}")
                raise RuntimeError(f"Contract compilation failed: {result.stderr}")
            
            logger.info("Contract compiled successfully")
            
            # Load compiled contract
            contract_name = "FlashLoanArbitrageFixed"
            artifact_path = Path(f"out/{contract_name}.sol/{contract_name}.json")
            
            if not artifact_path.exists():
                raise FileNotFoundError(f"Compiled contract artifact not found: {artifact_path}")
            
            with open(artifact_path, 'r') as f:
                artifact = json.load(f)
            
            return {
                'abi': artifact['abi'],
                'bytecode': artifact['bytecode']['object'],
                'metadata': artifact.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Error compiling contract: {e}")
            raise
    
    def estimate_deployment_gas(self, contract_data: Dict[str, Any]) -> int:
        """Estimate gas required for deployment"""
        logger.info("Estimating deployment gas...")
        
        try:
            # Create contract factory
            contract_factory = self.web3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            # Estimate gas for deployment
            gas_estimate = contract_factory.constructor(
                self.constructor_args['aave_pool_provider']
            ).estimate_gas({'from': self.account.address})
            
            logger.info(f"Estimated gas for deployment: {gas_estimate}")
            return gas_estimate
            
        except Exception as e:
            logger.error(f"Error estimating gas: {e}")
            # Return a reasonable default
            return 3000000
    
    def get_optimal_gas_price(self) -> int:
        """Get optimal gas price for deployment"""
        logger.info("Calculating optimal gas price...")
        
        try:
            # Get current gas price
            current_gas_price = self.web3.eth.gas_price
            
            # Add 10% buffer for faster confirmation
            optimal_gas_price = int(current_gas_price * 1.1)
            
            logger.info(f"Current gas price: {self.web3.from_wei(current_gas_price, 'gwei')} gwei")
            logger.info(f"Optimal gas price: {self.web3.from_wei(optimal_gas_price, 'gwei')} gwei")
            
            return optimal_gas_price            
        except Exception as e:
            logger.error(f"Error getting gas price: {e}")
            # Return a reasonable default (30 gwei)
            return self.web3.to_wei(30, 'gwei')
    
    def deploy_contract(self, contract_data: Dict[str, Any]) -> Tuple[str, str]:
        """Deploy the contract to Polygon network"""
        logger.info("Deploying contract to Polygon network...")
        
        try:
            # Get deployment parameters
            gas_estimate = self.estimate_deployment_gas(contract_data)
            gas_price = self.get_optimal_gas_price()
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            
            # Calculate deployment cost
            deployment_cost_wei = gas_estimate * gas_price
            deployment_cost_matic = self.web3.from_wei(deployment_cost_wei, 'ether')
            
            logger.info(f"Estimated deployment cost: {deployment_cost_matic} MATIC")
            
            # Check account balance
            account_balance = self.web3.eth.get_balance(self.account.address)
            if account_balance < deployment_cost_wei:
                raise ValueError(f"Insufficient balance. Need {deployment_cost_matic} MATIC, have {self.web3.from_wei(account_balance, 'ether')} MATIC")
            
            # Create contract factory
            contract_factory = self.web3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            # Build deployment transaction
            constructor_txn = contract_factory.constructor(
                self.constructor_args['aave_pool_provider']
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'chainId': self.web3.eth.chain_id
            })
            
            # Sign transaction
            signed_txn = self.web3.eth.account.sign_transaction(constructor_txn, self.private_key)
            
            # Send transaction
            logger.info("Sending deployment transaction...")
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Deployment transaction sent: {tx_hash.hex()}")
            logger.info("Waiting for transaction confirmation...")
            
            # Wait for transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt['status'] == 1:
                contract_address = tx_receipt['contractAddress']
                if not contract_address:
                    raise RuntimeError("Contract address not found in transaction receipt")
                    
                logger.info(f"✅ Contract deployed successfully!")
                logger.info(f"Contract address: {contract_address}")
                logger.info(f"Transaction hash: {tx_hash.hex()}")
                logger.info(f"Gas used: {tx_receipt['gasUsed']}")
                logger.info(f"Block number: {tx_receipt['blockNumber']}")
                
                return str(contract_address), tx_hash.hex()
            else:
                raise RuntimeError("Contract deployment failed")                
        except Exception as e:
            logger.error(f"Error deploying contract: {e}")
            raise
    
    def verify_deployment(self, contract_address: str, contract_data: Dict[str, Any]) -> bool:
        """Verify the deployed contract"""
        logger.info(f"Verifying deployed contract at {contract_address}...")
        
        try:
            # Convert to checksum address
            checksum_address = Web3.to_checksum_address(contract_address)
            
            # Check if contract code exists
            code = self.web3.eth.get_code(checksum_address)
            if len(code) <= 2:  # '0x' is 2 characters
                logger.error("No contract code found at address")
                return False
            
            logger.info(f"Contract code size: {len(code)} bytes")
            
            # Create contract instance
            contract = self.web3.eth.contract(
                address=checksum_address,
                abi=contract_data['abi']
            )
            
            # Test contract functions
            try:
                owner = contract.functions.owner().call()
                logger.info(f"Contract owner: {owner}")
                
                if str(owner).lower() != self.account.address.lower():
                    logger.warning("Contract owner doesn't match deployer address")
                
                # Test other view functions
                failed_count = contract.functions.failedTransactionsCount().call()
                max_failed = contract.functions.maxFailedTransactions().call()
                slippage = contract.functions.slippageTolerance().call()
                
                logger.info(f"Failed transactions count: {failed_count}")
                logger.info(f"Max failed transactions: {max_failed}")
                logger.info(f"Slippage tolerance: {slippage} basis points")
                
                logger.info("✅ Contract verification successful")
                return True
                
            except Exception as e:
                logger.error(f"Error calling contract functions: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying contract: {e}")
            return False
    
    def save_deployment_info(self, contract_address: str, tx_hash: str, contract_data: Dict[str, Any]):
        """Save deployment information to file"""
        deployment_info = {
            'contract_address': contract_address,
            'transaction_hash': tx_hash,
            'network': 'polygon',
            'chain_id': self.web3.eth.chain_id,
            'deployer_address': self.account.address,
            'deployment_timestamp': int(time.time()),
            'constructor_args': self.constructor_args,
            'abi': contract_data['abi']
        }
        
        # Save to JSON file
        output_file = Path('deployment_info.json')
        with open(output_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info(f"Deployment info saved to {output_file}")
        
        # Update network config if it exists
        network_config_file = Path('src/config/network_config.json')
        if network_config_file.exists():
            try:
                with open(network_config_file, 'r') as f:
                    network_config = json.load(f)
                
                network_config['flash_loan_contract_address'] = contract_address
                network_config['deployment_tx_hash'] = tx_hash
                
                with open(network_config_file, 'w') as f:
                    json.dump(network_config, f, indent=2)
                
                logger.info("Network config updated with new contract address")
            except Exception as e:
                logger.warning(f"Could not update network config: {e}")

def main():
    """Main deployment function"""
    try:
        logger.info("🚀 Starting Flash Loan Contract Deployment")
        logger.info("=" * 50)
        
        # Initialize deployer
        deployer = ContractDeployer()
        
        # Compile contract
        contract_data = deployer.compile_contract()
        
        # Deploy contract
        contract_address, tx_hash = deployer.deploy_contract(contract_data)
        
        # Verify deployment
        if deployer.verify_deployment(contract_address, contract_data):
            # Save deployment info
            deployer.save_deployment_info(contract_address, tx_hash, contract_data)
            
            logger.info("=" * 50)
            logger.info("🎉 DEPLOYMENT SUCCESSFUL!")
            logger.info(f"📍 Contract Address: {contract_address}")
            logger.info(f"🔗 Transaction Hash: {tx_hash}")
            logger.info(f"🌐 Network: Polygon Mainnet")
            logger.info(f"👤 Owner: {deployer.account.address}")
            logger.info("=" * 50)
            
            print(f"\n✅ Contract deployed successfully!")
            print(f"📍 Address: {contract_address}")
            print(f"🔗 TX Hash: {tx_hash}")
            print(f"🌐 View on Polygonscan: https://polygonscan.com/address/{contract_address}")
            
        else:
            logger.error("❌ Contract deployment verification failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
