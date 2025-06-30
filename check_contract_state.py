#!/usr/bin/env python3
"""
Check contract state to understand why arbitrage is failing
"""
import os
from web3 import Web3, HTTPProvider
from web3.middleware.geth_poa import geth_poa_middleware

# Initialize Web3
w3 = Web3(HTTPProvider('https://rpc-amoy.polygon.technology'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Contract details
contract_address = "0x35791D283Ec6eeF6C7687026CaF026C5F84C7c15"

# Read the ABI from the artifacts
import json
with open('artifacts/contracts/FlashLoanArbitrageFixed.sol/FlashLoanArbitrageFixed.json', 'r') as f:
    contract_data = json.load(f)
    abi = contract_data['abi']

# Initialize contract
contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=abi)

print(f"🔍 Contract State Check: {contract_address}")
print("=" * 60)

try:
    # Check basic state
    print("📊 Basic State:")
    
    # Check if paused
    try:
        is_paused = contract.functions.paused().call()
        print(f"   Paused: {'YES ❌' if is_paused else 'NO ✅'}")
    except:
        print(f"   Paused: Unable to check")
    
    # Check failed transactions count
    try:
        failed_count = contract.functions.failedTransactionsCount().call()
        max_failed = contract.functions.maxFailedTransactions().call()
        print(f"   Failed Transactions: {failed_count}/{max_failed} {'❌ CIRCUIT BREAKER!' if failed_count >= max_failed else '✅'}")
    except:
        print(f"   Failed Transactions: Unable to check")
    
    # Check owner
    try:
        owner = contract.functions.owner().call()
        print(f"   Owner: {owner}")
    except:
        print(f"   Owner: Unable to check")
    
    print()
    print("🪙 Token Whitelist Status:")
    tokens_to_check = {
        'WMATIC': '0x9c3c9283d3e44854697cd22D3faA240cfB0e7582',
        'USDC': '0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582',
        'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
        'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
        'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'
    }
    
    for symbol, address in tokens_to_check.items():
        try:
            is_whitelisted = contract.functions.whitelistedTokens(address).call()
            print(f"   {symbol} ({address[:10]}...): {'✅' if is_whitelisted else '❌'}")
        except:
            print(f"   {symbol}: Unable to check")
    
    print()
    print("🏪 DEX Approval Status:")
    dexes_to_check = {
        'UniswapV3': '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45',
        'QuickSwap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
        'SushiSwap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
    }
    
    for name, address in dexes_to_check.items():
        try:
            is_approved = contract.functions.approvedDexes(address).call()
            print(f"   {name} ({address[:10]}...): {'✅' if is_approved else '❌'}")
        except:
            print(f"   {name}: Unable to check")
    
    print()
    print("📈 Contract Health Check:")
    try:
        health_result = contract.functions.healthCheck().call()
        is_healthy, status, token_count, dex_count, failed_count = health_result
        print(f"   Overall Health: {'✅' if is_healthy else '❌'} ({status})")
        print(f"   Whitelisted Tokens: {token_count}")
        print(f"   Approved DEXes: {dex_count}")
        print(f"   Failed Count: {failed_count}")
    except Exception as e:
        print(f"   Health Check Failed: {e}")
    
    print()
    print("📊 Swap Statistics:")
    try:
        stats = contract.functions.getSwapStatistics().call()
        total_swaps, successful_swaps, failed_swaps, total_profits, total_fees, last_swap_time, highest_profit, most_profitable_token = stats
        print(f"   Total Swaps: {total_swaps}")
        print(f"   Successful: {successful_swaps}")
        print(f"   Failed: {failed_swaps}")
        print(f"   Total Profits: {total_profits}")
        print(f"   Highest Profit: {highest_profit}")
        print(f"   Last Swap: {last_swap_time}")
    except Exception as e:
        print(f"   Stats Failed: {e}")

except Exception as e:
    print(f"❌ Error checking contract state: {e}") 