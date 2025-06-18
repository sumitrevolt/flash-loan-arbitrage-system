#!/usr/bin/env python3
"""
DEX Prices and Arbitrage Calculations Display
Shows current prices across DEXes and calculates potential profits
"""

import asyncio
import json
import time
from decimal import Decimal
from datetime import datetime
import requests

async def get_polygon_gas_price():
    """Get current Polygon gas price"""
    try:
        response = requests.get("https://gasstation-mainnet.matic.network/v2", timeout=5)
        data = response.json()
        return data.get('fast', {}).get('maxFee', 30)  # Default to 30 Gwei
    except:
        return 30  # Fallback

async def get_real_dex_price(dex_name, token_pair):
    """Get real DEX price from actual market data"""
    try:
        # Import the real price fetcher
        from dex_price_fetcher import MultiDexPriceFetcher
        from web3 import Web3
        from decimal import Decimal
        
        # Initialize Web3 connection
        web3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
        
        # Load tokens and DEX configuration
        with open('production_config.json', 'r') as f:
            config = json.load(f)
        
        tokens = config.get('tokens', {})
        dexes = config.get('dexes', {})
        
        # Create price fetcher
        fetcher = MultiDexPriceFetcher(web3, tokens, dexes)
        
        # Parse token pair (e.g., "WMATIC/USDC" -> token_a="WMATIC", token_b="USDC")
        token_a, token_b = token_pair.split('/')
        
        # Get token addresses
        token_a_address = tokens.get(token_a, {}).get('address', '')
        token_b_address = tokens.get(token_b, {}).get('address', '')
        
        if not token_a_address or not token_b_address:
            print(f"⚠️ Missing token addresses for {token_pair}")
            raise Exception(f"Missing token addresses")
        
        # Get real price using correct method signature
        amount = Decimal('1')  # Get price for 1 unit
        price_data = await fetcher.get_dex_price(dex_name, token_a_address, token_b_address, amount)
        
        if price_data:
            return float(price_data.price)
        else:
            # Fallback to CoinGecko API for base price
            response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids=usd-coin,wmatic&vs_currencies=usd", timeout=5)
            data = response.json()
            usdc_price = data.get('usd-coin', {}).get('usd', 1.0)
            matic_price = data.get('wmatic', {}).get('usd', 0.8)
            
            if 'USDC' in token_pair and 'WMATIC' in token_pair:
                return usdc_price / matic_price
            return 1.0
            
    except Exception as e:
        print(f"⚠️ Error fetching real price for {dex_name}/{token_pair}: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        # Fallback to basic market price
        try:
            response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids=usd-coin,wmatic&vs_currencies=usd", timeout=5)
            data = response.json()
            usdc_price = data.get('usd-coin', {}).get('usd', 1.0)
            matic_price = data.get('wmatic', {}).get('usd', 0.8)
              # For WMATIC/USDC pair, return appropriate price
            if 'USDC' in token_pair and 'WMATIC' in token_pair:
                return usdc_price / matic_price
            return 1.0
        except:
            return 1.0
    
    return 1.0

async def show_dex_prices():
    """Display current DEX prices and arbitrage calculations"""
    
    print("\n" + "="*80)
    print("🔥 FLASH LOAN ARBITRAGE BOT - DEX PRICES & CALCULATIONS")
    print("="*80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    try:
        with open('production_config.json', 'r') as f:
            config = json.load(f)
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Get current gas price
    gas_price_gwei = await get_polygon_gas_price()
    print(f"⛽ Current Gas Price: {gas_price_gwei:.1f} Gwei")
    print("-" * 80)
    
    # Sample token pairs with realistic prices (USD)
    token_pairs = [
        ("WMATIC", "USDC", 0.8234),
        ("WETH", "USDC", 3420.50),
        ("WBTC", "USDC", 67890.25),
        ("DAI", "USDC", 0.9998),
        ("USDT", "USDC", 1.0001),
        ("LINK", "USDC", 14.67),
        ("AAVE", "USDC", 89.45),
        ("UNI", "USDC", 12.34),
        ("CRV", "USDC", 0.456),
        ("SUSHI", "USDC", 1.789)
    ]
    
    dexes = ['QuickSwap', 'Uniswap V3', 'SushiSwap', 'Curve', 'Balancer', 'DODO']
    
    profitable_opportunities = []
    
    for token_a, token_b, base_price in token_pairs:
        print(f"\n💰 {token_a}/{token_b} PAIR ANALYSIS")
        print("-" * 50)
          # Get prices from each DEX
        dex_prices = {}
        for dex in dexes:
            price = await get_real_dex_price(dex.lower().replace(' ', '_'), f"{token_a}/{token_b}")
            dex_prices[dex] = price
            print(f"  {dex:<12}: ${price:.6f}")
        
        # Find best buy and sell prices
        best_buy_dex = min(dex_prices.keys(), key=lambda k: Any: dex_prices[k])
        best_sell_dex = max(dex_prices.keys(), key=lambda k: Any: dex_prices[k])
        
        best_buy_price = dex_prices[best_buy_dex]
        best_sell_price = dex_prices[best_sell_dex]
        
        # Calculate spread
        spread_usd = best_sell_price - best_buy_price
        spread_percent = (spread_usd / best_buy_price) * 100
        
        print(f"\n📊 SPREAD ANALYSIS:")
        print(f"  Best Buy:  {best_buy_dex} @ ${best_buy_price:.6f}")
        print(f"  Best Sell: {best_sell_dex} @ ${best_sell_price:.6f}")
        print(f"  Spread:    ${spread_usd:.6f} ({spread_percent:.3f}%)")
        
        # Calculate arbitrage profit for $1000 trade
        trade_amount = 1000
        
        # Fees calculation
        aave_fee = trade_amount * 0.0005  # 0.05% AAVE flash loan fee
        dex_fees = trade_amount * 0.006   # 0.6% total DEX fees (0.3% each)
        gas_cost_usd = (gas_price_gwei * 500000 * 1e-9 * 0.82 * base_price) if token_a == "WMATIC" else 15  # Gas cost in USD
        
        gross_profit = spread_usd * (trade_amount / best_buy_price)
        total_costs = aave_fee + dex_fees + gas_cost_usd
        net_profit = gross_profit - total_costs
        
        print(f"\n💡 PROFIT CALCULATION (${trade_amount} trade):")
        print(f"  Gross Profit:    ${gross_profit:.2f}")
        print(f"  AAVE Fee:        ${aave_fee:.2f}")
        print(f"  DEX Fees:        ${dex_fees:.2f}")
        print(f"  Gas Cost:        ${gas_cost_usd:.2f}")
        print(f"  Total Costs:     ${total_costs:.2f}")
        print(f"  Net Profit:      ${net_profit:.2f}")
        
        # Profitability assessment
        min_profit = 5.0  # $5 minimum profit threshold
        if net_profit > min_profit:
            status = "🟢 PROFITABLE"
            profitable_opportunities.append((token_a, token_b, net_profit, best_buy_dex, best_sell_dex))
        elif net_profit > 0:
            status = "🟡 MARGINAL"
        else:
            status = "🔴 NOT PROFITABLE"
        
        print(f"  Status:          {status}")
        
        if net_profit > min_profit:
            confidence = min(95, int(spread_percent * 20))  # Confidence based on spread
            print(f"  Confidence:      {confidence}%")
            print(f"  ROI:             {(net_profit/trade_amount)*100:.2f}%")
    
    # Summary
    print("\n" + "="*80)
    print("📈 ARBITRAGE OPPORTUNITIES SUMMARY")
    print("="*80)
    
    if profitable_opportunities:
        print(f"✅ Found {len(profitable_opportunities)} profitable opportunities:")
        for i, (token_a, token_b, profit, buy_dex, sell_dex) in enumerate(profitable_opportunities, 1):
            print(f"  {i}. {token_a}/{token_b}: ${profit:.2f} profit ({buy_dex} → {sell_dex})")
    else:
        print("❌ No profitable opportunities found at current prices")
        print("   Reasons:")
        print("   • DEX prices are tightly aligned (efficient market)")
        print("   • Transaction costs exceed potential profits")
        print("   • High gas prices reducing profitability")
    
    print(f"\n💼 TRADING PARAMETERS:")
    print(f"   • Minimum Profit Threshold: ${min_profit}")
    print(f"   • Flash Loan Fee: 0.05%")
    print(f"   • DEX Trading Fees: 0.6% total")
    print(f"   • Current Gas: {gas_price_gwei:.1f} Gwei")
    
    print(f"\n⏰ Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)

async def continuous_monitoring():
    """Run continuous price monitoring"""
    print("🚀 Starting continuous DEX price monitoring...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            await show_dex_prices()
            print("\n⏳ Waiting 10 seconds for next update...\n")
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    print("DEX Price Monitor - Choose mode:")
    print("1. Single scan")
    print("2. Continuous monitoring")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "2":
            asyncio.run(continuous_monitoring())
        else:
            asyncio.run(show_dex_prices())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
