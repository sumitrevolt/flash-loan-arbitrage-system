#!/usr/bin/env python3
"""
Simple contract existence check
"""
from web3 import Web3, HTTPProvider
from web3.middleware.geth_poa import geth_poa_middleware
from hexbytes import HexBytes
from typing import Dict, Any, cast

# Initialize Web3
w3 = Web3(HTTPProvider('https://rpc-amoy.polygon.technology'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

contract_address = "0x35791D283Ec6eeF6C7687026CaF026C5F84C7c15"

print(f"🔍 Checking contract: {contract_address}")
print("=" * 50)

try:
    # Check if address has code
    code = w3.eth.get_code(w3.to_checksum_address(contract_address))
    print(f"📦 Contract Code Length: {len(code)} bytes")
    
    if len(code) > 2:  # More than just "0x"
        print("✅ Contract exists and has code")
        print(f"📝 Code Preview: {code[:100].hex()}...")
    else:
        print("❌ No contract code found - contract may not be deployed")
    
    # Check balance
    balance = w3.eth.get_balance(w3.to_checksum_address(contract_address))
    print(f"💰 Contract Balance: {w3.from_wei(balance, 'ether')} MATIC")
    
    # Try a simple call with minimal ABI
    simple_abi = [
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=simple_abi)
    owner = contract.functions.owner().call()
    print(f"👤 Contract Owner: {owner}")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Let's also check the latest transaction to this contract
print(f"\n🔍 Checking recent transaction to contract...")
try:
    latest_block = w3.eth.block_number
    print(f"📊 Latest Block: {latest_block}")
    
    # Look for transactions to our contract in recent blocks
    for i in range(10):  # Check last 10 blocks
        block_num = latest_block - i
        block = w3.eth.get_block(block_num, full_transactions=True)
        
        # Access transactions safely using proper typing
        block_dict = cast(Dict[str, Any], block)
        transactions = block_dict.get("transactions", [])
        
        for tx in transactions:
            # Cast transaction to dict for proper access
            tx_dict = cast(Dict[str, Any], tx)
            to_address = tx_dict.get("to")
            
            if to_address and isinstance(to_address, str) and to_address.lower() == contract_address.lower():
                # Get transaction hash
                tx_hash = tx_dict.get("hash")
                if tx_hash:
                    # Ensure tx_hash is HexBytes
                    if not isinstance(tx_hash, HexBytes):
                        tx_hash = HexBytes(tx_hash)
                    
                    receipt = w3.eth.get_transaction_receipt(tx_hash)
                    print(f"🎯 Found TX: {tx_hash.hex()}")
                    print(f"   Block: {block_num}")
                    print(f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
                    print(f"   Gas Used: {receipt['gasUsed']:,}")
                    
                    # Get input data
                    input_data = tx_dict.get("input")
                    if input_data:
                        # Handle both HexBytes and string
                        if hasattr(input_data, "hex"):
                            input_hex = input_data.hex()
                        elif isinstance(input_data, str):
                            input_hex = input_data
                        else:
                            input_hex = str(input_data)
                        
                        # Ensure we have 0x prefix
                        if not input_hex.startswith("0x"):
                            input_hex = f"0x{input_hex}"
                        
                        print(f"   Input Data: {input_hex[:50]}...")
                break
        else:
            continue
        break
    else:
        print("❓ No recent transactions found to contract")
        
except Exception as e:
    print(f"❌ Error checking transactions: {e}") 