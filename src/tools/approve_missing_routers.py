# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import json
import os

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3
"""
Target Missing DEX Router Approval Script
Specifically approves the 2 missing routers identified in the comprehensive report
"""


# Load environment variables
load_dotenv()

# Configuration
POLYGON_RPC_URL = "https://polygon-rpc.com"
CONTRACT_ADDRESS = "0x153dDf13D58397740c40E9D1a6e183A8c0F36c32"
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Missing DEX routers that need approval (from comprehensive report)
MISSING_ROUTERS = {}
    "Curve Primary Router": "0x445FE580eF8d70FF569aB36e80c647af338db351",
    "DODO Primary Router": "0xa222f0c183AFA73a8Bc1AFb48D34C88c9Bf7A174"


# Contract ABI (minimal for approveDex function)
CONTRACT_ABI = []
    {}
        "inputs": []
            {"name": "dex", "type": "address"},
            {"name": "status", "type": "bool"}
        ],
        "name": "approveDex",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {}
        "inputs": [{"name": "", "type": "address"}],
        "name": "approvedDexes", 
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    


def main():
    print("[TASK] Target Missing DEX Router Approval")
    print("=" * 50)
    
    # Connect to Polygon
    print("🔗 Connecting to Polygon...")
    web3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))
    
    if not web3.is_connected():
        print("[ERROR] Failed to connect to Polygon")
        return
    
    print("[OK] Connected to Polygon")
    
    # Setup account
    account = Account.from_key(PRIVATE_KEY)
    print(f"[KEY] Account: {account.address}")
    
    # Get contract
    contract = web3.eth.contract()
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=CONTRACT_ABI
    
    print(f"📋 Contract: {CONTRACT_ADDRESS}")
    
    # Check and approve missing routers
    approved_count = 0
    total_count = len(MISSING_ROUTERS)
    
    for name, router_address in MISSING_ROUTERS.items():
        print(f"\n[SETUP] Processing {name}...")
        router_checksum = Web3.to_checksum_address(router_address)
        
        # Check current approval status
        try:
            is_approved = contract.functions.approvedDexes(router_checksum).call()
            
            if is_approved:
                print(f"[OK] {name} is already approved!")
                approved_count += 1
            else:
                print(f"[ERROR] {name} needs approval. Approving...")
                
                # Build transaction
                transaction = contract.functions.approveDex()
                    router_checksum, 
                    True
                ).build_transaction({}
                    'from': account.address,
                    'gas': 100000,
                    'gasPrice': web3.to_wei('30', 'gwei'),
                    'nonce': web3.eth.get_transaction_count(account.address),
                    'chainId': 137
                
                
                # Sign and send transaction
                signed_txn = web3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                print(f"📤 Transaction sent: {tx_hash.hex()}")
                
                # Wait for confirmation
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                if receipt.status == 1:
                    print(f"[OK] {name} approved successfully!")
                    approved_count += 1
                else:
                    print(f"[ERROR] {name} approval failed!")
                    
        except Exception as e:
            print(f"[ERROR] Error processing {name}: {str(e)}")
    
    print(f"\n[METRICS] Results: {approved_count}/{total_count} routers approved")
    
    if approved_count == total_count:
        print("[CELEBRATE] All missing routers are now approved!")
        print("[INIT] Your system now has 100% DEX router coverage!")
    else:
        print(f"[WARN] {total_count - approved_count} routers still need manual approval")
    
    print("\n[SYNC] Run comprehensive_dex_report.py to verify the new status")

if __name__ == "__main__":
    main()