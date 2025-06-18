#!/usr/bin/env python3
"""
Real-time DEX Price Monitor and Arbitrage Calculator
Shows live prices, calculations, and potential opportunities
"""

import asyncio
import json
import logging
import time
import os
import platform
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Dict, List, Optional
from web3 import Web3
from dotenv import load_dotenv

# Windows compatibility
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment
load_dotenv()

# Set high precision
getcontext().prec = 50

# Import modules
try:
    from dex_price_fetcher import MultiDexPriceFetcher
    DEX_FETCHER_AVAILABLE = True
except ImportError:
    print("❌ DEX price fetcher not available")
    DEX_FETCHER_AVAILABLE = False

class ArbitrageCalculator:
    """Calculate arbitrage opportunities with detailed output"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Setup Web3
        rpc_url = os.getenv('POLYGON_RPC_URL')
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        self.tokens = self.config['tokens']
        self.dexes = self.config['dexes']
        self.price_fetcher = None
        
        # Trading parameters
        self.min_profit = Decimal(str(self.config['trading']['min_profit_usd']))
        self.trade_size = Decimal(str(self.config['trading']['min_trade_size_usd']))
        self.flash_loan_fee = Decimal(str(self.config['aave']['flash_loan_fee']))
        
    async def initialize(self):
        """Initialize price fetcher"""
        if DEX_FETCHER_AVAILABLE:
            self.price_fetcher = MultiDexPriceFetcher(self.web3, self.tokens, self.dexes)
            await self.price_fetcher.start()
            return True
        return False
    
    async def get_all_dex_prices(self, token_a: str, token_b: str) -> Dict:
        """Get prices from all DEXes for a token pair"""
        prices = {}
        
        for dex_name, dex_info in self.dexes.items():
            if not dex_info.get('enabled', True):
                continue
                
            try:
                price_data = await self.price_fetcher.get_dex_price(
                    dex_name=dex_name.lower(),
                    token_a=token_a,
                    token_b=token_b,
                    amount=self.trade_size
                )
                
                if price_data and hasattr(price_data, 'price') and price_data.price > 0:
                    prices[dex_name] = {
                        'price': price_data.price,
                        'fee': Decimal(str(dex_info.get('fee_tier', 0.003))),
                        'liquidity': getattr(price_data, 'liquidity', Decimal('0')),
                        'source': getattr(price_data, 'source', 'unknown')
                    }
                    
            except Exception as e:
                prices[dex_name] = {
                    'error': str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
                }
        
        return prices
    
    def calculate_arbitrage(self, token_a: str, token_b: str, dex_prices: Dict) -> Dict:
        """Calculate arbitrage opportunity with detailed breakdown"""
        
        # Filter valid prices
        valid_prices = {k: v for k, v in dex_prices.items() if 'price' in v}
        
        if len(valid_prices) < 2:
            return {'status': 'insufficient_prices', 'valid_dexes': len(valid_prices)}
        
        # Find best buy and sell
        best_buy_dex = min(valid_prices.keys(), key=lambda k: Any: valid_prices[k]['price'])
        best_sell_dex = max(valid_prices.keys(), key=lambda k: Any: valid_prices[k]['price'])
        
        if best_buy_dex == best_sell_dex:
            return {'status': 'same_dex', 'dex': best_buy_dex}
        
        buy_price = valid_prices[best_buy_dex]['price']
        sell_price = valid_prices[best_sell_dex]['price']
        
        # Calculate fees
        aave_fee = self.trade_size * self.flash_loan_fee
        buy_fee = self.trade_size * valid_prices[best_buy_dex]['fee']
        sell_fee = self.trade_size * valid_prices[best_sell_dex]['fee']
        gas_cost = Decimal('2.0')  # Estimate
        
        # Calculate profit
        gross_profit = (sell_price - buy_price) * self.trade_size
        total_fees = aave_fee + buy_fee + sell_fee + gas_cost
        net_profit = gross_profit - total_fees
        
        # Calculate spread
        price_spread_pct = ((sell_price - buy_price) / buy_price) * 100
        
        return {
            'status': 'calculated',
            'token_pair': f"{token_a}/{token_b}",
            'best_buy': {
                'dex': best_buy_dex,
                'price': buy_price,
                'fee_pct': float(valid_prices[best_buy_dex]['fee'] * 100)
            },
            'best_sell': {
                'dex': best_sell_dex,
                'price': sell_price,
                'fee_pct': float(valid_prices[best_sell_dex]['fee'] * 100)
            },
            'calculations': {
                'trade_size': self.trade_size,
                'gross_profit': gross_profit,
                'aave_fee': aave_fee,
                'buy_fee': buy_fee,
                'sell_fee': sell_fee,
                'gas_cost': gas_cost,
                'total_fees': total_fees,
                'net_profit': net_profit,
                'price_spread_pct': price_spread_pct
            },
            'profitable': net_profit > self.min_profit,
            'all_prices': valid_prices
        }

    async def display_live_prices(self):
        """Display live prices and calculations"""
        
        # Popular pairs to monitor
        monitor_pairs = [
            ('WMATIC', 'USDC'),
            ('WETH', 'USDC'),
            ('WBTC', 'USDT'),
            ('USDC', 'USDT'),
            ('WMATIC', 'WETH')
        ]
        
        print("\n" + "="*80)
        print("🚀 REAL-TIME DEX ARBITRAGE MONITOR")
        print("="*80)
        print(f"Trade Size: ${self.trade_size} | Min Profit: ${self.min_profit} | Flash Loan Fee: {self.flash_loan_fee*100:.2f}%")
        print("="*80)
        
        while True:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n🕐 UPDATE: {current_time}")
                print("-" * 80)
                
                opportunities_found = 0
                
                for token_a, token_b in monitor_pairs:
                    print(f"\n📊 {token_a}/{token_b}:")
                    
                    # Get prices from all DEXes
                    dex_prices = await self.get_all_dex_prices(token_a, token_b)
                    
                    # Display individual DEX prices
                    print("   DEX Prices:")
                    for dex_name in self.dexes.keys():
                        if dex_name in dex_prices:
                            if 'price' in dex_prices[dex_name]:
                                price = dex_prices[dex_name]['price']
                                fee = dex_prices[dex_name]['fee'] * 100
                                print(f"      {dex_name:12} ${price:8.4f} (fee: {fee:.2f}%)")
                            else:
                                error = dex_prices[dex_name].get('error', 'No data')
                                print(f"      {dex_name:12} ❌ {error}")
                        else:
                            print(f"      {dex_name:12} ⏸️  Disabled")
                    
                    # Calculate arbitrage
                    calc = self.calculate_arbitrage(token_a, token_b, dex_prices)
                    
                    if calc['status'] == 'calculated':
                        buy_info = calc['best_buy']
                        sell_info = calc['best_sell']
                        calcs = calc['calculations']
                        
                        print(f"   🔄 Best Route: {buy_info['dex']} → {sell_info['dex']}")
                        print(f"      Buy:  ${buy_info['price']:.4f} on {buy_info['dex']}")
                        print(f"      Sell: ${sell_info['price']:.4f} on {sell_info['dex']}")
                        print(f"      Spread: {calcs['price_spread_pct']:.3f}%")
                        
                        print(f"   💰 Profit Calculation:")
                        print(f"      Gross Profit:    ${calcs['gross_profit']:7.2f}")
                        print(f"      AAVE Fee:        ${calcs['aave_fee']:7.2f}")
                        print(f"      Buy DEX Fee:     ${calcs['buy_fee']:7.2f}")
                        print(f"      Sell DEX Fee:    ${calcs['sell_fee']:7.2f}")
                        print(f"      Gas Cost:        ${calcs['gas_cost']:7.2f}")
                        print(f"      Total Fees:      ${calcs['total_fees']:7.2f}")
                        print(f"      NET PROFIT:      ${calcs['net_profit']:7.2f}")
                        
                        if calc['profitable']:
                            print(f"      🎉 PROFITABLE! (≥${self.min_profit})")
                            opportunities_found += 1
                        else:
                            print(f"      ❌ Not profitable (need ≥${self.min_profit})")
                    
                    elif calc['status'] == 'insufficient_prices':
                        print(f"   ⚠️  Only {calc['valid_dexes']} DEX(es) have prices")
                    
                    elif calc['status'] == 'same_dex':
                        print(f"   ⚠️  Best buy/sell on same DEX: {calc['dex']}")
                
                print("\n" + "="*80)
                print(f"📈 SUMMARY: {opportunities_found} profitable opportunities found at {current_time}")
                if opportunities_found > 0:
                    print("🚨 ARBITRAGE OPPORTUNITIES AVAILABLE!")
                else:
                    print("⏳ Waiting for profitable opportunities...")
                print("="*80)
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except KeyboardInterrupt:
                print("\n👋 Monitor stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(2)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.price_fetcher:
            await self.price_fetcher.stop()

async def main():
    """Main function"""
    calculator = ArbitrageCalculator('production_config.json')
    
    print("🔄 Initializing DEX price monitor...")
    
    if not await calculator.initialize():
        print("❌ Failed to initialize price fetcher")
        return
    
    print("✅ Price fetcher initialized")
    print("🎯 Starting live price monitoring...")
    print("   Press Ctrl+C to stop")
    
    try:
        await calculator.display_live_prices()
    finally:
        await calculator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
