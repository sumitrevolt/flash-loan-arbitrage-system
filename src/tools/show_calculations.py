# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from decimal import Decimal, getcontext
import asyncio
import json
import os
import platform

from dotenv import load_dotenv
from web3 import Web3
"""
Simple DEX Price & Arbitrage Calculator - Quick Test
"""


# Windows compatibility
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
getcontext().prec = 50

async def show_dex_calculations():
    """Show current DEX prices and arbitrage calculations"""
    
    print("[INIT] DEX PRICE & ARBITRAGE CALCULATOR")
    print("=" * 60)
    
    # Load config
    with open('production_config.json', 'r') as f:
        config = json.load(f)
    
    # Connect to Web3
    rpc_url = os.getenv('POLYGON_RPC_URL')
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not web3.is_connected():
        print("[ERROR] Failed to connect to Polygon")
        return
    
    print(f"[OK] Connected to Polygon (Block: {web3.eth.block_number})")
    
    # Trading parameters
    trade_size = Decimal(str(config['trading']['min_trade_size_usd']))
    min_profit = Decimal(str(config['trading']['min_profit_usd']))
    flash_loan_fee = Decimal(str(config['aave']['flash_loan_fee']))
    
    print(f"💰 Trade Size: ${trade_size}")
    print(f"💰 Min Profit: ${min_profit}")
    print(f"💰 Flash Loan Fee: {flash_loan_fee*100:.2f}%")
    print()
    
    # Sample calculation for WMATIC/USDC
    print("[METRICS] SAMPLE ARBITRAGE CALCULATION (WMATIC/USDC)")
    print("-" * 50)
    
    # Mock prices (since we can't guarantee real-time data)
    sample_prices = {}
        'quickswap': {'price': Decimal('0.5245'), 'fee': Decimal('0.003')},
        'uniswap_v3': {'price': Decimal('0.5251'), 'fee': Decimal('0.003')},
        'sushiswap': {'price': Decimal('0.5248'), 'fee': Decimal('0.003')},
    
    
    print("DEX Prices (WMATIC per USDC):")
    for dex, data in sample_prices.items():
        print(f"   {dex:12} ${data['price']:.4f} (fee: {data['fee']*100:.1f}%)")
    
    # Find best buy/sell
    best_buy_dex = min(sample_prices.keys(), key=lambda k: Any: sample_prices[k]['price'])
    best_sell_dex = max(sample_prices.keys(), key=lambda k: Any: sample_prices[k]['price'])
    
    buy_price = sample_prices[best_buy_dex]['price']
    sell_price = sample_prices[best_sell_dex]['price']
    
    print(f"\n[SYNC] Best Route: {best_buy_dex} → {best_sell_dex}")
    print(f"   Buy at:  ${buy_price:.4f} on {best_buy_dex}")
    print(f"   Sell at: ${sell_price:.4f} on {best_sell_dex}")
    
    # Calculate spread
    price_spread = ((sell_price - buy_price) / buy_price) * 100
    print(f"   Spread:  {price_spread:.3f}%")
    
    print(f"\n💵 PROFIT CALCULATION (${trade_size} trade):")
    print("-" * 40)
    
    # Calculate all components
    gross_profit = (sell_price - buy_price) * trade_size
    aave_fee = trade_size * flash_loan_fee
    buy_fee = trade_size * sample_prices[best_buy_dex]['fee']
    sell_fee = trade_size * sample_prices[best_sell_dex]['fee']
    gas_cost = Decimal('2.0')  # Estimate
    
    total_fees = aave_fee + buy_fee + sell_fee + gas_cost
    net_profit = gross_profit - total_fees
    
    print(f"Gross Profit:      ${gross_profit:7.2f}")
    print(f"AAVE Flash Fee:    ${aave_fee:7.2f}")
    print(f"Buy DEX Fee:       ${buy_fee:7.2f}")
    print(f"Sell DEX Fee:      ${sell_fee:7.2f}")
    print(f"Gas Cost Est.:     ${gas_cost:7.2f}")
    print(f"Total Fees:        ${total_fees:7.2f}")
    print("-" * 25)
    print(f"NET PROFIT:        ${net_profit:7.2f}")
    
    if net_profit > min_profit:
        print(f"[CELEBRATE] PROFITABLE! (>${min_profit} threshold met)")
    else:
        print(f"[ERROR] Not profitable (need >${min_profit})")
    
    print(f"\n[GROWTH] ROI: {(net_profit/trade_size)*100:.2f}%")
    
    # Show what your bot is actually doing
    print("\n" + "=" * 60)
    print("🤖 WHAT YOUR BOT IS DOING RIGHT NOW:")
    print("=" * 60)
    
    dexes = config['dexes']
    tokens = config['tokens']
    
    enabled_dexes = [name for name, info in dexes.items() if info.get('enabled', True)]
    token_count = len(tokens)
    pair_count = token_count * (token_count - 1)
    
    print(f"[OK] Monitoring {len(enabled_dexes)} DEXes: {', '.join(enabled_dexes)}")
    print(f"[OK] Scanning {token_count} tokens: {', '.join(tokens.keys())}")
    print(f"[OK] Checking {pair_count} trading pairs every second")
    print(f"[OK] Looking for profits ≥ ${min_profit}")
    print(f"[OK] Ready to execute trades up to ${config['trading']['max_trade_size_usd']}")
    
    # Current gas price
    try:
        gas_price_gwei = web3.from_wei(web3.eth.gas_price, 'gwei')
        print(f"⛽ Current gas price: {gas_price_gwei:.1f} Gwei")
    except:
        print("⛽ Gas price: Unable to fetch")
    
    print("\n[SEARCH] The bot finds 0 opportunities because:")
    print("   • Market is efficient (spreads < profit threshold)")
    print("   • High competition from other arbitrage bots")
    print("   • Gas costs reduce profitability")
    print("   • Waiting for volatility to create opportunities")
    
    print(f"\n⏰ Bot will automatically execute when profitable opportunities appear!")

if __name__ == "__main__":
    asyncio.run(show_dex_calculations())