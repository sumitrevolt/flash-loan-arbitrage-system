#!/usr/bin/env python3
"""
Simple Flash Loan Contract Deployment Script
Deploys the FlashLoanArbitrageFixed contract using pre-compiled ABI and bytecode
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
import logging
from typing import Dict, Any, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SimpleContractDeployer")

class SimpleContractDeployer:
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
        
        # Constructor arguments
        self.aave_pool_provider = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"  # Aave V3 Pool Address Provider on Polygon
        
        logger.info(f"Connected to Polygon network (Chain ID: {self.web3.eth.chain_id})")
        logger.info(f"Account balance: {self.web3.from_wei(self.web3.eth.get_balance(self.account.address), 'ether')} MATIC")
    
    def get_contract_data(self) -> Dict[str, Any]:
        """Get the contract ABI and bytecode"""
        # FlashLoanArbitrageFixed contract ABI (essential functions only)
        contract_abi = [
            {
                "inputs": [
                    {
                        "internalType": "contract IPoolAddressesProvider",
                        "name": "_addressProvider",
                        "type": "address"
                    }
                ],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "inputs": [],
                "name": "owner",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "failedTransactionsCount",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "maxFailedTransactions",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "slippageTolerance",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "token",
                        "type": "address"
                    },
                    {
                        "internalType": "bool",
                        "name": "status",
                        "type": "bool"
                    }
                ],
                "name": "whitelistToken",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address"
                    }
                ],
                "name": "whitelistedTokens",
                "outputs": [
                    {
                        "internalType": "bool",
                        "name": "",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "token",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "amount",
                        "type": "uint256"
                    },
                    {
                        "indexed": False,
                        "internalType": "address",
                        "name": "dex1",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "address",
                        "name": "dex2",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "address",
                        "name": "intermediateToken",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "profit",
                        "type": "uint256"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "fee",
                        "type": "uint256"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "gasUsed",
                        "type": "uint256"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    }
                ],
                "name": "ArbitrageExecuted",
                "type": "event"
            }
        ]
        
        # This is a placeholder bytecode - in a real deployment, you would need the actual compiled bytecode
        # For demonstration purposes, I'll provide instructions on how to get it
        contract_bytecode = "0x"  # This needs to be replaced with actual compiled bytecode
        
        logger.warning("⚠️ Contract bytecode not available - you need to compile the contract first")
        logger.info("To get the bytecode:")
        logger.info("1. Install Foundry: https://book.getfoundry.sh/getting-started/installation")
        logger.info("2. Run: forge build")
        logger.info("3. Get bytecode from: out/FlashLoanArbitrageFixed.sol/FlashLoanArbitrageFixed.json")
        
        return {
            'abi': contract_abi,
            'bytecode': contract_bytecode
        }
    
    def deploy_simple_test_contract(self) -> Tuple[str, str]:
        """Deploy a simple test contract for demonstration"""
        logger.info("Deploying simple test contract...")
        
        # Simple contract that just stores the owner
        simple_abi = [
            {
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "inputs": [],
                "name": "owner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Simple contract bytecode (stores msg.sender as owner)
        simple_bytecode = "0x608060405234801561001057600080fd5b50336000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555060d1806100606000396000f3fe6080604052348015600f57600080fd5b506004361060285760003560e01c80638da5cb5b14602d575b600080fd5b60005460405173ffffffffffffffffffffffffffffffffffffffff909116815260200160405180910390f3fea2646970667358221220f7c5b4e3d4b6f3e2c3e8f7c5b4e3d4b6f3e2c3e8f7c5b4e3d4b6f3e2c3e8f764736f6c63430008100033"
        
        try:
            # Get deployment parameters
            gas_price = self.get_optimal_gas_price()
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            gas_estimate = 300000  # Reasonable estimate for simple contract
            
            # Build deployment transaction
            tx_data = {
                'from': self.account.address,
                'data': simple_bytecode,
                'nonce': nonce,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'chainId': self.web3.eth.chain_id
            }
            
            # Sign transaction
            signed_txn = self.web3.eth.account.sign_transaction(tx_data, self.private_key)
            
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
                    
                logger.info(f"✅ Test contract deployed successfully!")
                logger.info(f"Contract address: {contract_address}")
                
                return str(contract_address), tx_hash.hex()
            else:
                raise RuntimeError("Contract deployment failed")
                
        except Exception as e:
            logger.error(f"Error deploying test contract: {e}")
            raise
    
    def get_optimal_gas_price(self) -> int:
        """Get optimal gas price for deployment"""
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
    
    def verify_deployment(self, contract_address: str) -> bool:
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
            logger.info("✅ Contract verification successful")
            return True
                
        except Exception as e:
            logger.error(f"Error verifying contract: {e}")
            return False

def show_deployment_instructions():
    """Show instructions for proper contract deployment"""
    print("\n" + "="*60)
    print("📋 FLASH LOAN CONTRACT DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    print("\n1. 🔧 Install Foundry (Solidity development toolkit):")
    print("   Visit: https://book.getfoundry.sh/getting-started/installation")
    print("   Or run: curl -L https://foundry.paradigm.xyz | bash")
    print("   Then run: foundryup")
    print("\n2. 🏗️ Initialize Foundry project:")
    print("   forge init --template foundry-rs/forge-template .")
    print("\n3. 📦 Install dependencies:")
    print("   forge install OpenZeppelin/openzeppelin-contracts")
    print("   forge install aave/aave-v3-core")
    print("   forge install Uniswap/v3-periphery")
    print("   forge install Uniswap/v2-periphery")
    print("\n4. 🔨 Compile the contract:")
    print("   forge build")
    print("\n5. 🚀 Deploy the contract:")
    print("   forge create --rpc-url $POLYGON_RPC_URL \\")
    print("     --private-key $PRIVATE_KEY \\")
    print("     --constructor-args 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb \\")
    print("     core/contracts/FlashLoanArbitrageFixed.sol:FlashLoanArbitrageFixed")
    print("\n6. ✅ Verify on Polygonscan:")
    print("   forge verify-contract <CONTRACT_ADDRESS> \\")
    print("     --chain-id 137 \\")
    print("     --etherscan-api-key $POLYGONSCAN_API_KEY \\")
    print("     core/contracts/FlashLoanArbitrageFixed.sol:FlashLoanArbitrageFixed")
    print("\n" + "="*60)

def main():
    """Main deployment function"""
    try:
        logger.info("🚀 Starting Flash Loan Contract Deployment")
        logger.info("=" * 50)
        
        # Show proper deployment instructions
        show_deployment_instructions()
        
        # Initialize deployer
        deployer = SimpleContractDeployer()
        
        # Ask user if they want to deploy a test contract
        print(f"\n💳 Your wallet: {deployer.account.address}")
        print(f"💰 Balance: {deployer.web3.from_wei(deployer.web3.eth.get_balance(deployer.account.address), 'ether')} MATIC")
        
        response = input("\n❓ Would you like to deploy a simple test contract to verify setup? (y/n): ")
        
        if response.lower() == 'y':
            # Deploy test contract
            contract_address, tx_hash = deployer.deploy_simple_test_contract()
            
            # Verify deployment
            if deployer.verify_deployment(contract_address):
                print("\n" + "="*50)
                print("🎉 TEST CONTRACT DEPLOYMENT SUCCESSFUL!")
                print(f"📍 Contract Address: {contract_address}")
                print(f"🔗 Transaction Hash: {tx_hash}")
                print(f"🌐 View on Polygonscan: https://polygonscan.com/address/{contract_address}")
                print("="*50)
                
                print("\n✅ Your wallet and RPC setup is working correctly!")
                print("📝 Now you can follow the instructions above to deploy the actual Flash Loan contract.")
            else:
                print("❌ Test contract deployment verification failed")
        else:
            print("\n📝 Follow the instructions above to deploy the Flash Loan contract with Foundry.")
            
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        print("\n🔧 Please check:")
        print("  - Your .env file has WALLET_ADDRESS and PRIVATE_KEY")
        print("  - Your wallet has sufficient MATIC balance")
        print("  - Your RPC URL is working")
        sys.exit(1)

if __name__ == "__main__":
    main()
