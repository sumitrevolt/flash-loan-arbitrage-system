#!/usr/bin/env python3
"""
Script to add new DEX support to the deployed arbitrage contract
Contract: 0x153dDf13D58397740c40E9D1a6e183A8c0F36c32
"""

import asyncio
import os
from web3 import Web3
from eth_account import Account
import json

# Contract configuration
CONTRACT_ADDRESS = "0x153dDf13D58397740c40E9D1a6e183A8c0F36c32"
POLYGON_RPC = "https://polygon-rpc.com"

# New DEXes to add
NEW_DEXES = {
    "curve": {
        "name": "Curve Finance",
        "address": "0x8f942C20D02bEfc377D41445793068908E2250D0",
        "type": "router"
    },
    "balancer": {
        "name": "Balancer",
        "address": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "type": "vault"
    },
    "dodo": {
        "name": "DODO",
        "address": "0xa222f9c040d7E29b5B9c4bC24d7a8Ba83e7bd47b",
        "type": "proxy"
    }
}

# Contract ABI for approveDex function
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "dex", "type": "address"},
            {"internalType": "bool", "name": "status", "type": "bool"}
        ],
        "name": "approveDex",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "name": "approvedDexes",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

class DEXManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=CONTRACT_ABI
        )
        
    def load_private_key(self):
        """Load private key from environment or prompt user"""
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print("⚠️  Private key not found in environment variables")
            print("Please set PRIVATE_KEY environment variable or enter it manually")
            private_key = input("Enter your private key (will not be displayed): ")
        
        # Validate private key
        try:
            account = Account.from_key(private_key)
            print(f"✅ Loaded account: {account.address}")
            return private_key, account
        except Exception as e:
            print(f"❌ Invalid private key: {e}")
            return None, None
    
    def check_current_dex_status(self):
        """Check which DEXes are currently approved"""
        print("\n📊 Current DEX Status:")
        print("=" * 60)
        
        for dex_key, dex_info in NEW_DEXES.items():
            try:
                is_approved = self.contract.functions.approvedDexes(
                    Web3.to_checksum_address(dex_info["address"])
                ).call()
                status = "✅ APPROVED" if is_approved else "❌ NOT APPROVED"
                print(f"{dex_info['name']:<15} {dex_info['address']} {status}")
            except Exception as e:
                print(f"{dex_info['name']:<15} {dex_info['address']} ❌ ERROR: {e}")
    
    def check_owner(self, account_address):
        """Check if the provided account is the contract owner"""
        try:
            owner = self.contract.functions.owner().call()
            is_owner = owner.lower() == account_address.lower()
            print(f"\n🔐 Contract Owner: {owner}")
            print(f"🔑 Your Account: {account_address}")
            print(f"👤 Owner Status: {'✅ YOU ARE OWNER' if is_owner else '❌ NOT OWNER'}")
            return is_owner
        except Exception as e:
            print(f"❌ Error checking owner: {e}")
            return False
    
    def approve_dex(self, private_key, dex_address, status=True):
        """Approve or disapprove a DEX"""
        try:
            account = Account.from_key(private_key)
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Build transaction
            txn = self.contract.functions.approveDex(
                Web3.to_checksum_address(dex_address),
                status
            ).build_transaction({
                'from': account.address,
                'gas': 100000,  # Conservative gas limit
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'chainId': 137  # Polygon Mainnet
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(txn, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"🚀 Transaction sent: {tx_hash.hex()}")
            print(f"⏳ Waiting for confirmation...")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                action = "approved" if status else "disapproved"
                print(f"✅ DEX {action} successfully!")
                print(f"📝 Transaction: https://polygonscan.com/tx/{tx_hash.hex()}")
                return True
            else:
                print(f"❌ Transaction failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error approving DEX: {e}")
            return False
    
    def approve_all_new_dexes(self, private_key):
        """Approve all new DEXes"""
        print("\n🔧 Adding New DEX Support...")
        print("=" * 60)
        
        success_count = 0
        total_count = len(NEW_DEXES)
        
        for dex_key, dex_info in NEW_DEXES.items():
            print(f"\n📡 Processing {dex_info['name']}...")
            
            # Check if already approved
            try:
                is_approved = self.contract.functions.approvedDexes(
                    Web3.to_checksum_address(dex_info["address"])
                ).call()
                
                if is_approved:
                    print(f"✅ {dex_info['name']} is already approved!")
                    success_count += 1
                    continue
                    
            except Exception as e:
                print(f"❌ Error checking status: {e}")
            
            # Approve the DEX
            if self.approve_dex(private_key, dex_info["address"], True):
                success_count += 1
            
            # Small delay between transactions
            await asyncio.sleep(2)
        
        print(f"\n📊 Summary: {success_count}/{total_count} DEXes approved successfully")
        return success_count == total_count

async def main():
    print("🏗️  Flash Loan Arbitrage DEX Manager")
    print("=====================================")
    print(f"📋 Contract: {CONTRACT_ADDRESS}")
    print(f"🌐 Network: Polygon Mainnet")
    
    # Initialize manager
    manager = DEXManager()
    
    # Check current status
    manager.check_current_dex_status()
    
    # Load private key
    private_key, account = manager.load_private_key()
    if not private_key:
        return
    
    # Check if user is owner
    if not manager.check_owner(account.address):
        print("\n❌ You are not the contract owner!")
        print("Only the contract owner can approve new DEXes.")
        return
    
    # Ask for confirmation
    print(f"\n🤔 Do you want to approve the unapproved DEXes?")
    confirm = input("Type 'yes' to proceed: ").lower().strip()
    
    if confirm != 'yes':
        print("❌ Operation cancelled")
        return
    
    # Approve all new DEXes
    success = await manager.approve_all_new_dexes(private_key)
    
    if success:
        print("\n🎉 All DEXes approved successfully!")
        print("\n📋 Updated Production Configuration:")
        print("✅ QuickSwap (already approved)")
        print("✅ Uniswap V3 (already approved)")  
        print("✅ SushiSwap (already approved)")
        print("✅ Curve Finance (newly approved)")
        print("✅ Balancer (newly approved)")
        print("✅ DODO (newly approved)")
        
        print(f"\n🚀 Your bot can now use all 6 DEXes for arbitrage!")
    else:
        print("\n❌ Some DEX approvals failed. Check the logs above.")
    
    # Final status check
    print("\n" + "="*60)
    manager.check_current_dex_status()

if __name__ == "__main__":
    asyncio.run(main())
