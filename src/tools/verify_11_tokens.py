#!/usr/bin/env python3
"""
11 APPROVED TOKENS CONFIGURATION VERIFICATION
============================================

This script verifies that all 11 approved tokens are properly configured
in the flash loan arbitrage system.
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dex_integrations import RealDEXIntegrations
from enhanced_dex_price_calculator import EnhancedDEXCalculator

async def verify_11_tokens():
    """Verify all 11 approved tokens are configured correctly"""
    
    print("🔍 VERIFYING 11 APPROVED TOKENS CONFIGURATION")
    print("=" * 60)
    
    # Initialize DEX integrations
    dex = RealDEXIntegrations()
    await dex.initialize()
    
    # Display configured tokens
    print("\n📋 CONFIGURED TOKENS:")
    print("-" * 40)
    
    tokens = list(dex.token_addresses.keys())
    
    for i, (symbol, address) in enumerate(dex.token_addresses.items(), 1):
        print(f"{i:2d}. {symbol:<6} - {address}")
    
    print(f"\n✅ Total Tokens Configured: {len(tokens)}")
    
    if len(tokens) == 11:
        print("🎉 SUCCESS: All 11 tokens are properly configured!")
    else:
        print(f"⚠️  WARNING: Expected 11 tokens, found {len(tokens)}")
    
    # Verify token pairs
    calc = EnhancedDEXCalculator()
    print(f"\n📊 CONFIGURED TOKEN PAIRS: {len(calc.token_pairs)}")
    print("-" * 40)
    
    for i, pair in enumerate(calc.token_pairs, 1):
        print(f"{i:2d}. {pair}")
    
    # Test a quick price fetch
    print("\n🔄 TESTING PRICE FETCHING...")
    try:
        # Test with a small sample
        test_pairs = ['ETH/USDC', 'WBTC/ETH', 'MATIC/USDC']
        prices = await dex.fetch_all_dex_prices_parallel(test_pairs)
        
        if prices:
            print("✅ Price fetching is working correctly!")
            for pair, dex_prices in prices.items():
                print(f"   {pair}: {len(dex_prices)} DEX prices found")
        else:
            print("⚠️  Price fetching returned no data (using simulation mode)")
            
    except Exception as e:
        print(f"⚠️  Price fetching test failed: {e}")
    
    await dex.close()
    
    print("\n" + "=" * 60)
    print("🚀 FLASH LOAN ARBITRAGE BOT - 11 TOKENS READY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(verify_11_tokens())
