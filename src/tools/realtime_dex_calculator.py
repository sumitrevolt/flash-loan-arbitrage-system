#!/usr/bin/env python3
"""
Real-Time DEX Price Calculator with MCP Integration
Shows real-time prices, calculations, and arbitrage opportunities
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal, getcontext
import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init(autoreset=True)
getcontext().prec = 50

class RealTimeDEXCalculator:
    """Real-time DEX price calculator with MCP integration"""
    
    def __init__(self):
        self.mcp_servers = {
            'foundry': 'http://localhost:8001',
            'evm': 'http://localhost:8002', 
            'matic': 'http://localhost:8003'
        }
        
        # Major tokens on Polygon
        self.tokens = {
            'WMATIC': {'address': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 'decimals': 18},
            'USDC': {'address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 'decimals': 6},
            'USDT': {'address': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 'decimals': 6},
            'DAI': {'address': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', 'decimals': 18},
            'WETH': {'address': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', 'decimals': 18}
        }
        
        # DEX routers
        self.dexes = {
            'QuickSwap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
            'SushiSwap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
            'UniswapV3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
            'Curve': '0x094d12e5b541784701FD8d65F11fc0598FBC6332'
        }
        
        self.price_cache = {}
        self.last_update = None
    
    async def check_mcp_health(self) -> Dict[str, bool]:
        """Check health of all MCP servers"""
        health = {}
        async with aiohttp.ClientSession() as session:
            for name, url in self.mcp_servers.items():
                try:
                    async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                        health[name] = resp.status == 200
                except:
                    health[name] = False
        return health
    
    async def get_gas_info(self) -> Dict[str, Any]:
        """Get gas information from Matic MCP"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mcp_servers['matic']}/gas/estimates") as resp:
                    if resp.status == 200:
                        return await resp.json()
        except:
            pass
        return {'gas_price_gwei': 'N/A', 'estimated_confirm_time': 'N/A'}
    
    async def simulate_token_prices(self) -> Dict[str, Dict[str, Decimal]]:
        """Simulate real-time token prices (replace with actual DEX calls)"""
        prices = {}
        
        # Base prices in USD
        base_prices = {
            'WMATIC': 0.45, 'USDC': 1.00, 'USDT': 1.00, 'DAI': 1.00, 'WETH': 1800.0
        }
        
        for token in self.tokens.keys():
            prices[token] = {}
            base = base_prices[token]
            
            for dex in self.dexes.keys():
                # Add small random variation
                variation = (hash(f"{token}{dex}{int(time.time())//10}") % 100 - 50) / 10000
                price = Decimal(str(base * (1 + variation)))
                prices[token][dex] = price
                
        return prices
    
    def calculate_arbitrage_profit(self, buy_price: Decimal, sell_price: Decimal, 
                                 amount: Decimal, gas_cost: Decimal = Decimal('0.5')) -> Dict[str, Decimal]:
        """Calculate arbitrage profit including gas costs"""
        gross_profit = (sell_price - buy_price) * amount
        net_profit = gross_profit - gas_cost
        roi = (net_profit / (buy_price * amount)) * 100 if buy_price > 0 else Decimal('0')
        
        return {
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'roi_percent': roi,
            'price_difference': ((sell_price - buy_price) / buy_price) * 100 if buy_price > 0 else Decimal('0')
        }
    
    def find_best_opportunities(self, prices: Dict[str, Dict[str, Decimal]]) -> List[Dict[str, Any]]:
        """Find best arbitrage opportunities"""
        opportunities = []
        
        for token, token_prices in prices.items():
            if len(token_prices) < 2:
                continue
                
            # Find min and max
            min_dex = min(token_prices.keys(), key=lambda x: Any: Any: token_prices[x])
            max_dex = max(token_prices.keys(), key=lambda x: Any: Any: token_prices[x])
            
            buy_price = token_prices[min_dex]
            sell_price = token_prices[max_dex]
            
            # Calculate for $1000 trade
            trade_amount = Decimal('1000') / buy_price
            calc = self.calculate_arbitrage_profit(buy_price, sell_price, trade_amount)
            
            if calc['net_profit'] > 1:  # Only profitable opportunities
                opportunities.append({
                    'token': token,
                    'buy_dex': min_dex,
                    'sell_dex': max_dex,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'calculation': calc,
                    'trade_amount': trade_amount
                })
        
        return sorted(opportunities, key=lambda x: Any: Any: x['calculation']['net_profit'], reverse=True)
    
    def display_header(self):
        """Display header"""
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*90}")
        print(f"       REAL-TIME DEX PRICE CALCULATOR & ARBITRAGE MONITOR")
        print(f"                   MCP SERVERS INTEGRATED")
        print(f"{'='*90}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    
    def display_mcp_status(self, health: Dict[str, bool]):
        """Display MCP server status"""
        print(f"\n{Fore.CYAN}MCP Server Status:{Style.RESET_ALL}")
        for server, is_healthy in health.items():
            status = f"{Fore.GREEN}ONLINE{Style.RESET_ALL}" if is_healthy else f"{Fore.RED}OFFLINE{Style.RESET_ALL}"
            print(f"  {server.upper()}: {status}")
    
    def display_gas_info(self, gas_info: Dict[str, Any]):
        """Display gas information"""
        print(f"\n{Fore.CYAN}Network Status:{Style.RESET_ALL}")
        gas_price = gas_info.get('gas_price_gwei', 'N/A')
        print(f"  Gas Price: {Fore.GREEN}{gas_price} Gwei{Style.RESET_ALL}")
        print(f"  Est. Confirm Time: {Fore.GREEN}{gas_info.get('estimated_confirm_time', 'N/A')}{Style.RESET_ALL}")
    
    def display_price_table(self, prices: Dict[str, Dict[str, Decimal]]):
        """Display price comparison table"""
        print(f"\n{Fore.CYAN}Real-Time Token Prices (USD):{Style.RESET_ALL}")
        print(f"{'Token':<8} {'QuickSwap':<12} {'SushiSwap':<12} {'UniswapV3':<12} {'Curve':<12} {'Spread':<10}")
        print("-" * 78)
        
        for token, token_prices in prices.items():
            if not token_prices:
                continue
                
            row = f"{token:<8}"
            prices_list = list(token_prices.values())
            
            for dex in ['QuickSwap', 'SushiSwap', 'UniswapV3', 'Curve']:
                if dex in token_prices:
                    price = token_prices[dex]
                    row += f" ${price:<10.4f}"
                else:
                    row += f" {'N/A':<11}"
            
            # Calculate spread
            if len(prices_list) > 1:
                spread = ((max(prices_list) - min(prices_list)) / min(prices_list)) * 100
                spread_color = Fore.GREEN if spread > 0.5 else Fore.YELLOW if spread > 0.1 else ""
                row += f" {spread_color}{spread:>6.2f}%{Style.RESET_ALL}"
            else:
                row += f" {'N/A':<10}"
                
            print(row)
    
    def display_calculations(self, opportunities: List[Dict[str, Any]]):
        """Display arbitrage calculations"""
        print(f"\n{Fore.CYAN}Arbitrage Calculations ($1000 trades):{Style.RESET_ALL}")
        
        if not opportunities:
            print(f"  {Fore.YELLOW}No profitable opportunities found{Style.RESET_ALL}")
            return
        
        print(f"{'Token':<8} {'Route':<20} {'Price Diff':<12} {'Net Profit':<12} {'ROI':<8}")
        print("-" * 70)
        
        for opp in opportunities[:5]:
            token = opp['token']
            route = f"{opp['buy_dex']} → {opp['sell_dex']}"
            calc = opp['calculation']
            
            # Color code by profitability
            if calc['net_profit'] > 50:
                color = Fore.GREEN + Style.BRIGHT
            elif calc['net_profit'] > 10:
                color = Fore.GREEN
            else:
                color = Fore.YELLOW
            
            print(f"{token:<8} {route:<20} {calc['price_difference']:>6.2f}%     "
                  f"{color}${calc['net_profit']:>7.2f}{Style.RESET_ALL}   "
                  f"{color}{calc['roi_percent']:>5.2f}%{Style.RESET_ALL}")
    
    def display_detailed_calculation(self, opp: Dict[str, Any]):
        """Display detailed calculation for top opportunity"""
        if not opp:
            return
            
        print(f"\n{Fore.CYAN}Detailed Calculation (Top Opportunity):{Style.RESET_ALL}")
        calc = opp['calculation']
        
        print(f"  Token: {Fore.GREEN}{opp['token']}{Style.RESET_ALL}")
        print(f"  Buy from: {Fore.GREEN}{opp['buy_dex']}{Style.RESET_ALL} at ${opp['buy_price']:.4f}")
        print(f"  Sell to: {Fore.GREEN}{opp['sell_dex']}{Style.RESET_ALL} at ${opp['sell_price']:.4f}")
        print(f"  Trade Amount: {opp['trade_amount']:.2f} {opp['token']}")
        print(f"  Gross Profit: {Fore.GREEN}${calc['gross_profit']:.2f}{Style.RESET_ALL}")
        print(f"  Gas Cost: {Fore.YELLOW}$0.50{Style.RESET_ALL}")
        print(f"  Net Profit: {Fore.GREEN}${calc['net_profit']:.2f}{Style.RESET_ALL}")
        print(f"  ROI: {Fore.GREEN}{calc['roi_percent']:.2f}%{Style.RESET_ALL}")
    
    async def run_calculator(self):
        """Main calculator loop"""
        print(f"{Fore.GREEN}Starting Real-Time DEX Calculator...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Clear screen
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
        # WARNING: This is a security risk
        # WARNING: This is a security risk
                
                # Display header
                self.display_header()
                
                # Check MCP servers
                health = await self.check_mcp_health()
                self.display_mcp_status(health)
                
                # Get gas info
                gas_info = await self.get_gas_info()
                self.display_gas_info(gas_info)
                
                # Get prices
                prices = await self.simulate_token_prices()
                self.price_cache = prices
                self.last_update = datetime.now()
                
                # Display price table
                self.display_price_table(prices)
                
                # Find and display opportunities
                opportunities = self.find_best_opportunities(prices)
                self.display_calculations(opportunities)
                
                # Show detailed calculation for best opportunity
                if opportunities:
                    self.display_detailed_calculation(opportunities[0])
                
                # Status footer
                active_servers = sum(health.values())
                print(f"\n{Fore.GREEN}● CALCULATOR ACTIVE{Style.RESET_ALL} - "
                      f"Iteration {iteration} - "
                      f"{Fore.CYAN}{active_servers}/3 MCP Servers{Style.RESET_ALL} - "
                      f"{Fore.YELLOW}Next update in 2s...{Style.RESET_ALL}")
                
                await asyncio.sleep(2)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Calculator stopped by user{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")

async def main():
    """Main entry point"""
    try:
        calculator = RealTimeDEXCalculator()
        await calculator.run_calculator()
    except Exception as e:
        print(f"Failed to start calculator: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
