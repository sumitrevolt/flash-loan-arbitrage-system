#!/usr/bin/env python3
"""
Debug script to examine ALL events from recent transactions to understand arbitrage failures
"""
import json
from web3 import Web3, HTTPProvider
from web3.middleware.geth_poa import geth_poa_middleware
from hexbytes import HexBytes
from eth_abi.abi import decode

# Initialize Web3
w3 = Web3(HTTPProvider('https://rpc-amoy.polygon.technology'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Recent transaction hashes from your output
tx_hashes = [
    "0x52636dbb06374d7c3d8c6cc9cfe5d0a4fd7da46f422f20d3838f91c1ea803626",
    "0x9769723a16800653f0f4e1dfa9fe4bff7d8c333aeaacbba4ddfcfcf33e3bf739",
    "0x48e2df97c49476c1224888491fae7dda70401bad3bcba0f981a1e49d2f585ed0"
]

# Contract address
contract_address = "0x35791D283Ec6eeF6C7687026CaF026C5F84C7c15"

# Known event signatures
arbitrage_executed_sig = w3.keccak(text="ArbitrageExecuted(address,uint256,address,address,address,uint256,uint256,uint256,uint256)").hex()
debug_log_sig = w3.keccak(text="DebugLog(string,uint256)").hex()
arbitrage_failed_sig = w3.keccak(text="ArbitrageFailed(address,uint256,string,uint256)").hex()
swap_executed_sig = w3.keccak(text="SwapExecuted(address,address,address,uint256,uint256,uint256)").hex()

print(f"🔍 Debugging recent arbitrage transactions")
print("=" * 60)
print(f"Contract: {contract_address}")
print(f"ArbitrageExecuted sig: {arbitrage_executed_sig}")
print(f"DebugLog sig: {debug_log_sig}")
print(f"ArbitrageFailed sig: {arbitrage_failed_sig}")
print(f"SwapExecuted sig: {swap_executed_sig}")
print("=" * 60)

for i, tx_hash in enumerate(tx_hashes):
    print(f"\n📊 Transaction #{i+1}: {tx_hash}")
    print("-" * 50)
    try:
        receipt = w3.eth.get_transaction_receipt(HexBytes(tx_hash))
        
        print(f"✅ Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print(f"📊 Gas Used: {receipt['gasUsed']:,}")
        print(f"📝 Total Logs: {len(receipt['logs'])}")
        
        # Find logs from our contract
        contract_logs = [log for log in receipt['logs'] if log['address'].lower() == contract_address.lower()]
        print(f"🎯 Contract Logs: {len(contract_logs)}")
        
        if contract_logs:
            for j, log in enumerate(contract_logs):
                if log['topics']:
                    event_sig = log['topics'][0].hex()
                    print(f"   Log #{j}: ", end="")
                    
                    if event_sig == arbitrage_executed_sig:
                        print("🎉 ArbitrageExecuted - SUCCESS!")
                        # Try to decode
                        try:
                            # Decode the event data
                            decoded = decode(
                                ['uint256', 'address', 'address', 'address', 'uint256', 'uint256', 'uint256', 'uint256'],
                                log['data']
                            )
                            token = '0x' + log['topics'][1].hex()[26:]  # Extract address from indexed topic
                            amount, dex1, dex2, intermediate, profit, fee, gas_used, timestamp = decoded
                            print(f"       Token: {token}")
                            print(f"       Amount: {amount}")
                            print(f"       Profit: {profit}")
                            print(f"       Fee: {fee}")
                        except Exception as e:
                            print(f"       (decode error: {e})")
                    
                    elif event_sig == debug_log_sig:
                        print("🔧 DebugLog")
                        try:
                            # Decode debug log
                            decoded = decode(['string', 'uint256'], log['data'])
                            message, value = decoded
                            print(f"       Message: {message}")
                            print(f"       Value: {value}")
                        except Exception as e:
                            print(f"       (decode error: {e})")
                    
                    elif event_sig == arbitrage_failed_sig:
                        print("❌ ArbitrageFailed")
                        try:
                            decoded = decode(['uint256', 'string', 'uint256'], log['data'])
                            token = '0x' + log['topics'][1].hex()[26:]
                            amount, reason, gas_used = decoded
                            print(f"       Token: {token}")
                            print(f"       Amount: {amount}")
                            print(f"       Reason: {reason}")
                        except Exception as e:
                            print(f"       (decode error: {e})")
                    
                    elif event_sig == swap_executed_sig:
                        print("🔄 SwapExecuted")
                        try:
                            decoded = decode(['uint256', 'uint256', 'uint256'], log['data'])
                            token_in = '0x' + log['topics'][1].hex()[26:]
                            token_out = '0x' + log['topics'][2].hex()[26:]
                            dex = '0x' + log['topics'][3].hex()[26:]
                            amount_in, amount_out, timestamp = decoded
                            print(f"       TokenIn: {token_in}")
                            print(f"       TokenOut: {token_out}")
                            print(f"       DEX: {dex}")
                            print(f"       AmountIn: {amount_in}")
                            print(f"       AmountOut: {amount_out}")
                        except Exception as e:
                            print(f"       (decode error: {e})")
                    
                    else:
                        print(f"❓ Unknown event: {event_sig}")
        else:
            print("⚠️  No contract events found - this suggests the flash loan may have failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n🔍 Summary: Look for DebugLog events to see where execution stops") 