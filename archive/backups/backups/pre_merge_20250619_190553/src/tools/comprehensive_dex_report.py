#!/usr/bin/env python3
"""
Comprehensive DEX Approval Status Report
Shows all approved DEX addresses across different configurations
"""

import json
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

# Contract configuration
CONTRACT_ADDRESS = "0x153dDf13D58397740c40E9D1a6e183A8c0F36c32"
POLYGON_RPC_URL = "https://polygon-rpc.com"

# All DEX addresses from different configurations
ALL_DEX_ADDRESSES = {
    "QuickSwap": [
        "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"  # From all scripts
    ],
    "Uniswap V3": [
        "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",  # From quick_approve and advanced server
        "0xE592427A0AEce92De3Edee1F18E0157C05861564"   # From quick_dex_check
    ],
    "SushiSwap": [
        "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"   # From all scripts
    ],
    "Curve": [
        "0x445FE580eF8d70FF569aB36e80c647af338db351",  # From quick_approve
        "0x094d12e5b541784701FD8d65F11fc0598FBC6332",  # From quick_dex_check
        "0x8f942C20D02bEfc377D41445793068908E2250D0"   # From dex_manager_utility
    ],
    "Balancer": [
        "0xBA12222222228d8Ba445958a75a0704d566BF2C8"   # From all scripts
    ],
    "DODO": [
        "0xa222f0c183AFA73a8Bc1AFb48D34C88c9Bf7A174",  # From quick_approve
        "0x6D310348d5c12009854DFCf72e0DF9027e8cb4f4",  # From quick_dex_check
        "0xa222f9c040d7E29b5B9c4bC24d7a8Ba83e7bd47b"   # From dex_manager_utility
    ]
}

# Contract ABI for checking approvals
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "approvedDexes",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def main():
    """Check approval status for all DEX addresses"""
    print("🔍 Comprehensive DEX Approval Status Report")
    print("=" * 70)
    print(f"📋 Contract: {CONTRACT_ADDRESS}")
    print(f"🌐 Network: Polygon Mainnet")
    print()
    
    # Connect to Web3
    web3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))
    if not web3.is_connected():
        print("❌ Failed to connect to Polygon")
        return
    
    # Load contract
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=CONTRACT_ABI
    )
    
    total_addresses = 0
    approved_addresses = 0
    
    for dex_name, addresses in ALL_DEX_ADDRESSES.items():
        print(f"\n📊 {dex_name}")
        print("-" * 50)
        
        for i, address in enumerate(addresses):
            total_addresses += 1
            
            try:
                is_approved = contract.functions.approvedDexes(
                    Web3.to_checksum_address(address)
                ).call()
                
                status = "✅ APPROVED" if is_approved else "❌ NOT APPROVED"
                config_source = ""
                if i == 0:
                    config_source = " (Primary)"
                elif len(addresses) > 1:
                    config_source = f" (Alt #{i})"
                
                print(f"  {address}{config_source}")
                print(f"    Status: {status}")
                
                if is_approved:
                    approved_addresses += 1
                    
            except Exception as e:
                print(f"  {address}")
                print(f"    Status: ❌ ERROR - {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Summary:")
    print(f"   Total DEX addresses checked: {total_addresses}")
    print(f"   Approved addresses: {approved_addresses}")
    print(f"   Not approved: {total_addresses - approved_addresses}")
    print(f"   Approval rate: {(approved_addresses/total_addresses)*100:.1f}%")
    
    # Check unique DEX coverage
    approved_dexes = set()
    for dex_name, addresses in ALL_DEX_ADDRESSES.items():
        for address in addresses:
            try:
                is_approved = contract.functions.approvedDexes(
                    Web3.to_checksum_address(address)
                ).call()
                if is_approved:
                    approved_dexes.add(dex_name)
                    break
            except:
                continue
    
    print(f"\n🎯 DEX Protocol Coverage:")
    print(f"   Unique DEXes with at least one approved address: {len(approved_dexes)}")
    print(f"   Total DEX protocols: {len(ALL_DEX_ADDRESSES)}")
    
    if len(approved_dexes) == len(ALL_DEX_ADDRESSES):
        print("   ✅ All DEX protocols have approved addresses!")
    else:
        missing = set(ALL_DEX_ADDRESSES.keys()) - approved_dexes
        print(f"   ❌ Missing protocols: {', '.join(missing)}")

if __name__ == "__main__":
    main()
