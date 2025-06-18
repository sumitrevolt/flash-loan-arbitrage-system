#!/usr/bin/env python3
"""
DEX Management Utility
Standalone utility for managing DEX approvals without the WebSocket server
"""
import os
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
from typing import Dict, Any, Tuple, Optional

# Load environment variables
load_dotenv()

class DEXManagerUtility:
    """Standalone DEX manager for direct contract interaction"""
    
    def __init__(self):
        self.contract_address = "0x153dDf13D58397740c40E9D1a6e183A8c0F36c32"
        self.polygon_rpc = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
        self.private_key = os.getenv("PRIVATE_KEY")
        
        # DEX configurations
        self.supported_dexes: Dict[str, Dict[str, str]] = {
            "quickswap": {
                "name": "QuickSwap",
                "address": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
            },
            "uniswap_v3": {
                "name": "Uniswap V3",
                "address": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
            },
            "sushiswap": {
                "name": "SushiSwap",
                "address": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
            },
            "curve": {
                "name": "Curve Finance",
                "address": "0x8f942C20D02bEfc377D41445793068908E2250D0"
            },
            "balancer": {
                "name": "Balancer",
                "address": "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
            },
            "dodo": {
                "name": "DODO",
                "address": "0xa222f9c040d7E29b5B9c4bC24d7a8Ba83e7bd47b"
            }
        }
        
        # Contract ABI
        self.contract_abi: list[dict[str, Any]] = [
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
        
        self.web3: Optional[Web3] = None
        self.contract = None
        self.account = None
    
    def initialize(self) -> bool:
        """Initialize Web3 connection and contract"""
        try:
            print("🔧 Initializing DEX Manager...")
            
            # Setup Web3
            self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
            if not self.web3.is_connected():
                print("❌ Failed to connect to Polygon network")
                return False
            
            print(f"✅ Connected to Polygon (Chain ID: {self.web3.eth.chain_id})")
            
            # Setup contract
            self.contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.contract_abi
            )
            
            # Setup account
            if self.private_key:
                self.account = Account.from_key(self.private_key)
                print(f"✅ Account loaded: {self.account.address}")
                
                # Check if user is owner
                owner = self.contract.functions.owner().call()
                is_owner = owner.lower() == self.account.address.lower()
                print(f"🔑 Contract owner: {owner}")
                print(f"👤 User is owner: {'Yes' if is_owner else 'No'}")
                
                if not is_owner:
                    print("⚠️ Warning: You are not the contract owner. DEX approval will fail.")
            else:
                print("⚠️ No private key provided - read-only mode")
            
            print("✅ DEX Manager initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def check_dex_statuses(self) -> Tuple[int, int]:
        """Check approval status of all DEXes"""
        print("\n📊 Checking DEX approval statuses...")
        print("=" * 60)
        
        approved_count = 0
        total_count = len(self.supported_dexes)
        
        for dex_key, dex_info in self.supported_dexes.items():
            try:
                is_approved = self.contract.functions.approvedDexes(
                    Web3.to_checksum_address(dex_info["address"])
                ).call()
                
                status = "✅ APPROVED" if is_approved else "❌ NOT APPROVED"
                print(f"{dex_info['name']:15} | {status}")
                
                if is_approved:
                    approved_count += 1
                    
            except Exception as e:
                print(f"{dex_info['name']:15} | ❌ ERROR: {e}")
        
        print("=" * 60)
        print(f"📈 Summary: {approved_count}/{total_count} DEXes approved")
        
        return approved_count, total_count
    
    def approve_dex(self, dex_key: str, status: bool = True) -> bool:
        """Approve or disapprove a specific DEX"""
        if not self.account:
            print("❌ No private key provided - cannot send transactions")
            return False
        
        if dex_key not in self.supported_dexes:
            print(f"❌ Unknown DEX: {dex_key}")
            return False
        
        dex_info = self.supported_dexes[dex_key]
        
        try:
            # Check current status
            current_status = self.contract.functions.approvedDexes(
                Web3.to_checksum_address(dex_info["address"])
            ).call()
            
            if current_status == status:
                action = "approved" if status else "disapproved"
                print(f"✅ {dex_info['name']} is already {action}")
                return True
            
            print(f"🚀 {'Approving' if status else 'Disapproving'} {dex_info['name']}...")
            
            # Build transaction
            gas_price = self.web3.eth.gas_price
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            
            txn = self.contract.functions.approveDex(
                Web3.to_checksum_address(dex_info["address"]),
                status
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': 137
            })
            
            # Sign and send
            signed_txn = self.web3.eth.account.sign_transaction(txn, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            print(f"📝 Transaction sent: {tx_hash.hex()}")
            print("⏳ Waiting for confirmation...")
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt["status"] == 1:
                action = "approved" if status else "disapproved"
                print(f"✅ {dex_info['name']} {action} successfully!")
                print(f"⛽ Gas used: {receipt['gasUsed']:,}")
                return True
            else:
                print("❌ Transaction failed")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def approve_all_unapproved(self) -> bool:
        """Approve all unapproved DEXes"""
        print("\n🔧 Approving all unapproved DEXes...")
        
        if not self.account:
            print("❌ No private key provided - cannot send transactions")
            return False
        
        success_count = 0
        
        for dex_key, dex_info in self.supported_dexes.items():
            try:
                is_approved = self.contract.functions.approvedDexes(
                    Web3.to_checksum_address(dex_info["address"])
                ).call()
                
                if not is_approved:
                    print(f"\n📡 Processing {dex_info['name']}...")
                    if self.approve_dex(dex_key, True):
                        success_count += 1
                    
                    # Small delay between transactions
                    import time
                    time.sleep(2)
                else:
                    print(f"✅ {dex_info['name']} already approved")
                    success_count += 1
                    
            except Exception as e:
                print(f"❌ Error with {dex_info['name']}: {e}")
        
        print(f"\n📊 Results: {success_count}/{len(self.supported_dexes)} DEXes approved")
        return success_count == len(self.supported_dexes)

def main():
    """Main function"""
    print("🏗️  Flash Loan Arbitrage DEX Manager Utility")
    print("=" * 60)
    print(f"📋 Contract: 0x153dDf13D58397740c40E9D1a6e183A8c0F36c32")
    print(f"🌐 Network: Polygon Mainnet")
    print("")
    
    try:
        print("Creating DEX manager instance...")
        manager = DEXManagerUtility()
        print("DEX manager created successfully")
        
        print("Initializing...")
        if not manager.initialize():
            print("❌ Failed to initialize DEX manager")
            return
        print("Initialization successful")

        # Check current status
        print("Checking DEX status...")
        approved_count, total_count = manager.check_dex_statuses()
        print(f"Status check complete: {approved_count}/{total_count}")
        
        if approved_count < total_count:
            print(f"\n🔔 Found {total_count - approved_count} unapproved DEXes")
            
            if manager.account:
                user_input = input("\nDo you want to approve all unapproved DEXes? (y/n): ").lower().strip()
                
                if user_input == 'y':
                    success = manager.approve_all_unapproved()
                    
                    if success:
                        print("\n🎉 All DEXes approved successfully!")
                        print("\n📋 Final Status:")
                        manager.check_dex_statuses()
                    else:
                        print("\n❌ Some DEX approvals failed. Check the output above.")
                else:
                    print("❌ Operation cancelled by user")
            else:
                print("\n⚠️ Cannot approve DEXes - no private key provided")
        else:
            print("\n✅ All DEXes are already approved!")
        
        print("\n🎯 DEX Management completed")
        
    except Exception as e:
        print(f"❌ Error in main: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
