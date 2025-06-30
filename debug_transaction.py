#!/usr/bin/env python3
"""
Debug script to examine actual transaction events
"""
import json
from web3 import Web3, HTTPProvider
from web3.middleware.geth_poa import geth_poa_middleware

# Initialize Web3
w3 = Web3(HTTPProvider('https://rpc-amoy.polygon.technology'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Recent transaction hash from your output
tx_hash = "0x52636dbb06374d7c3d8c6cc9cfe5d0a4fd7da46f422f20d3838f91c1ea803626"

print(f"🔍 Examining transaction: {tx_hash}")
print("=" * 60)

try:
    # Get transaction receipt
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    
    print(f"✅ Transaction Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
    print(f"📊 Gas Used: {receipt['gasUsed']:,}")
    print(f"🏷️  Contract Address: {receipt['to']}")
    print(f"📝 Log Count: {len(receipt['logs'])}")
    print()
    
    # Examine each log entry
    for i, log in enumerate(receipt['logs']):
        print(f"📋 Log #{i}:")
        print(f"   Address: {log['address']}")
        print(f"   Topics: {[topic.hex() for topic in log['topics']]}")
        print(f"   Data: {log['data'].hex()}")
        
        # Try to decode the first topic (event signature)
        if log['topics']:
            event_sig = log['topics'][0].hex()
            print(f"   Event Signature: {event_sig}")
            
            # Calculate expected ArbitrageExecuted signature
            arbitrage_sig = w3.keccak(text="ArbitrageExecuted(address,uint256,address,address,address,uint256,uint256,uint256,uint256)").hex()
            debug_sig = w3.keccak(text="DebugLog(string,uint256)").hex()
            
            print(f"   Expected ArbitrageExecuted: {arbitrage_sig}")
            print(f"   Expected DebugLog: {debug_sig}")
            
            if event_sig == arbitrage_sig:
                print("   🎯 This is an ArbitrageExecuted event!")
            elif event_sig == debug_sig:
                print("   🔧 This is a DebugLog event!")
            else:
                print("   ❓ Unknown event signature")
        print()
    
    # Try to get the actual contract ABI for comparison
    print("🔍 Checking if this matches our expected events...")
    
except Exception as e:
    print(f"❌ Error examining transaction: {e}") 