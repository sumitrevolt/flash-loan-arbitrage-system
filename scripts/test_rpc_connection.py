#!/usr/bin/env python3
"""Test RPC connections"""

import requests
from web3 import Web3

# Test different RPC endpoints
rpcs = [
    "https://rpc.ankr.com/polygon",
    "https://polygon-mainnet.public.blastapi.io",
    "https://polygon.llamarpc.com",
    "https://polygon-bor-rpc.publicnode.com"
]

print("Testing RPC connections...\n")

for rpc in rpcs:
    print(f"Testing {rpc}...")
    try:
        # Test HTTP connection
        response = requests.get(rpc, timeout=5)
        print(f"  HTTP Status: {response.status_code}")
        
        # Test Web3 connection
        w3 = Web3(Web3.HTTPProvider(rpc))
        if w3.is_connected():
            chain_id = w3.eth.chain_id
            latest_block = w3.eth.block_number
            print(f"  ✓ Connected! Chain ID: {chain_id}, Latest Block: {latest_block}")
        else:
            print(f"  ✗ Web3 connection failed")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
    print()

print("\nIf all connections fail, please check:")
print("1. Your internet connection")
print("2. Firewall/antivirus settings")
print("3. VPN if you're using one") 