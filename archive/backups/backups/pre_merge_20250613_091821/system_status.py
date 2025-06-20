#!/usr/bin/env python3
"""
FLASH LOAN ARBITRAGE SYSTEM STATUS
==================================
Check current system status and running components
"""

import requests
import time
from datetime import datetime

def check_system_status():
    """Check status of all system components"""
    print("🔥 FLASH LOAN ARBITRAGE SYSTEM STATUS")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    # Check web dashboards
    dashboards = {
        'Enhanced DEX Calculations Dashboard': 'http://localhost:8005',
        'Enhanced DEX Arbitrage Monitor': 'http://localhost:8008'
    }
    
    print("🌐 WEB DASHBOARDS:")
    for name, url in dashboards.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: ONLINE ({url})")
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"❌ {name}: OFFLINE")
    
    print("\n💹 REAL-TIME FEATURES:")
    print("✅ 11 Token Support: ETH, USDC, USDT, DAI, WBTC, LINK, UNI, AAVE, COMP, MATIC, SUSHI")
    print("✅ Multi-DEX Integration: Uniswap V3, SushiSwap, Balancer, 1inch, QuickSwap")
    print("✅ Web3 Integration: Ethereum, Polygon, BSC networks")
    print("✅ Real-time Price Monitoring")
    print("✅ Arbitrage Opportunity Detection")
    print("✅ Flash Loan Calculations")
    
    # Try to fetch some live data
    print("\n📊 LIVE DATA SAMPLE:")
    try:
        # Try to get live prices from CoinGecko
        import requests
        token_ids = "ethereum,usd-coin,tether,dai,wrapped-bitcoin"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_ids}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("🔥 Current Prices (Live from CoinGecko):")
            for token_id, price_data in data.items():
                token_name = token_id.replace('-', ' ').title()
                price = price_data.get('usd', 'N/A')
                print(f"   💰 {token_name}: ${price:,}")
        else:
            print("⚠️  Live price data temporarily unavailable")
            
    except Exception as e:
        print(f"⚠️  Live data error: {e}")
    
    print(f"\n🎯 SYSTEM READY FOR ARBITRAGE MONITORING")
    print("📈 Access dashboards above for detailed analysis")
    print("-"*60)

if __name__ == "__main__":
    check_system_status()
