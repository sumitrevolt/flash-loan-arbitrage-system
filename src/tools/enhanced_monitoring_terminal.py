#!/usr/bin/env python3
"""
Enhanced Monitoring Terminal for Flash Loan Arbitrage System
Real-time monitoring using all MCP servers with DEX prices and calculations
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal, getcontext
from dataclasses import dataclass
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for colored output
colorama.init(autoreset=True)

# Set high precision for calculations
getcontext().prec = 50

@dataclass
class TokenPrice:
    symbol: str
    address: str
    price_usd: Decimal
    dex: str
    timestamp: datetime
    
@dataclass
class ArbitrageOpportunity:
    token_pair: tuple
    buy_dex: str
    sell_dex: str
    buy_price: Decimal
    sell_price: Decimal
    price_difference: Decimal
    profit_estimate: Decimal
    confidence: float

class EnhancedMonitoringTerminal:
    """Real-time monitoring terminal with MCP integration"""
    
    def __init__(self):
        self.mcp_servers = {
            'foundry': {'port': 8001, 'url': 'http://localhost:8001'},
            'evm': {'port': 8002, 'url': 'http://localhost:8002'},
            'matic': {'port': 8003, 'url': 'http://localhost:8003'}
        }
        
        # Token configuration
        self.tokens = {
            'WMATIC': {
                'address': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
                'decimals': 18,
                'symbol': 'WMATIC'
            },
            'USDC': {
                'address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
                'decimals': 6,
                'symbol': 'USDC'
            },
            'USDT': {
                'address': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
                'decimals': 6,
                'symbol': 'USDT'
            },
            'DAI': {
                'address': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
                'decimals': 18,
                'symbol': 'DAI'
            },
            'WETH': {
                'address': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
                'decimals': 18,
                'symbol': 'WETH'
            }
        }
        
        # DEX configuration
        self.dexes = {
            'QuickSwap': {
                'router': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                'factory': '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
                'fee': '0.003'
            },
            'SushiSwap': {
                'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                'fee': '0.003'
            },
            'UniswapV3': {
                'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
                'fee': '0.003'
            },
            'Curve': {
                'router': '0x094d12e5b541784701FD8d65F11fc0598FBC6332',
                'factory': '0x0000000000000000000000000000000000000000',
                'fee': '0.0004'
            }
        }
        
        # Performance metrics
        self.metrics = {
            'total_opportunities': 0,
            'profitable_opportunities': 0,
            'avg_profit_potential': Decimal('0'),
            'max_profit_seen': Decimal('0'),
            'start_time': datetime.now(),
            'last_update': datetime.now()
        }
        
        # Price history for trending
        self.price_history = {}
        
    async def check_mcp_server_health(self) -> Dict[str, bool]:
        """Check health of all MCP servers"""
        health_status = {}
        
        async with aiohttp.ClientSession() as session:
            for server_name, config in self.mcp_servers.items():
                try:
                    async with session.get(f"{config['url']}/health", 
                                         timeout=aiohttp.ClientTimeout(total=2)) as response:
                        if response.status == 200:
                            data = await response.json()
                            health_status[server_name] = data.get('status') == 'healthy'
                        else:
                            health_status[server_name] = False
                except Exception:
                    health_status[server_name] = False
                    
        return health_status
    
    async def get_gas_estimates(self) -> Optional[Dict[str, Any]]:
        """Get gas estimates from Matic MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mcp_servers['matic']['url']}/gas/estimates") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception:
            pass
        return None
    
    async def get_network_status(self) -> Optional[Dict[str, Any]]:
        """Get network status from Matic MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mcp_servers['matic']['url']}/network/status") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception:
            pass
        return None
    
    async def simulate_token_price(self, token_symbol: str, dex_name: str) -> Optional[Decimal]:
        """Simulate token price for demonstration (replace with real price feeds)"""
        try:
            # Base prices in USD for simulation
            base_prices = {
                'WMATIC': Decimal('0.45'),
                'USDC': Decimal('1.00'),
                'USDT': Decimal('1.00'),
                'DAI': Decimal('1.00'),
                'WETH': Decimal('1800.00')
            }
            
            # Add some variation based on DEX and time
            base_price = base_prices.get(token_symbol, Decimal('1.00'))
            time_factor = (time.time() % 100) / 1000  # Small time-based variation
            dex_factor = hash(dex_name) % 100 / 10000  # Small DEX-based variation
            
            variation = Decimal(str(time_factor + dex_factor))
            return base_price * (Decimal('1') + variation)
            
        except Exception:
            return None
    
    async def get_all_token_prices(self) -> Dict[str, Dict[str, Decimal]]:
        """Get prices for all tokens from all DEXes"""
        prices = {}
        
        for token_symbol in self.tokens.keys():
            prices[token_symbol] = {}
            for dex_name in self.dexes.keys():
                price = await self.simulate_token_price(token_symbol, dex_name)
                if price:
                    prices[token_symbol][dex_name] = price
                    
        return prices
    
    def find_arbitrage_opportunities(self, prices: Dict[str, Dict[str, Decimal]]) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities from price data"""
        opportunities = []
        
        for token_symbol, token_prices in prices.items():
            if len(token_prices) < 2:
                continue
                
            # Find min and max prices
            min_dex = min(token_prices.keys(), key=lambda x: Any: Any: token_prices[x])
            max_dex = max(token_prices.keys(), key=lambda x: Any: Any: token_prices[x])
            
            buy_price = token_prices[min_dex]
            sell_price = token_prices[max_dex]
            
            price_diff = (sell_price - buy_price) / buy_price
            
            # Only consider if price difference > 0.1%
            if price_diff > Decimal('0.001'):
                profit_estimate = price_diff * Decimal('1000')  # Estimate with $1000
                
                opportunities.append(ArbitrageOpportunity(
                    token_pair=(token_symbol, 'USD'),
                    buy_dex=min_dex,
                    sell_dex=max_dex,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    price_difference=price_diff,
                    profit_estimate=profit_estimate,
                    confidence=0.8
                ))
                
        return sorted(opportunities, key=lambda x: Any: Any: x.profit_estimate, reverse=True)
    
    def update_price_history(self, prices: Dict[str, Dict[str, Decimal]]):
        """Update price history for trending analysis"""
        current_time = datetime.now()
        
        for token_symbol, token_prices in prices.items():
            if token_symbol not in self.price_history:
                self.price_history[token_symbol] = []
                
            # Keep only last 10 price points
            self.price_history[token_symbol].append({
                'timestamp': current_time,
                'prices': token_prices.copy()
            })
            
            if len(self.price_history[token_symbol]) > 10:
                self.price_history[token_symbol].pop(0)
    
    def get_price_trend(self, token_symbol: str, dex_name: str) -> str:
        """Get price trend indicator for a token on a specific DEX"""
        if (token_symbol not in self.price_history or 
            len(self.price_history[token_symbol]) < 2):
            return "━"
            
        history = self.price_history[token_symbol]
        if dex_name not in history[-1]['prices'] or dex_name not in history[-2]['prices']:
            return "━"
            
        current_price = history[-1]['prices'][dex_name]
        previous_price = history[-2]['prices'][dex_name]
        
        if current_price > previous_price:
            return f"{Fore.GREEN}↗{Style.RESET_ALL}"
        elif current_price < previous_price:
            return f"{Fore.RED}↘{Style.RESET_ALL}"
        else:
            return "━"
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        # WARNING: This is a security risk
        # WARNING: This is a security risk
    
    def display_header(self, health_status: Dict[str, bool]):
        """Display the monitoring terminal header"""
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}")
        print(f"  FLASH LOAN ARBITRAGE MONITORING TERMINAL - MCP INTEGRATED")
        print(f"{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        
        # MCP Server Status
        print(f"\n{Fore.CYAN}MCP Server Status:{Style.RESET_ALL}")
        for server_name, is_healthy in health_status.items():
            status_color = Fore.GREEN if is_healthy else Fore.RED
            status_text = "HEALTHY" if is_healthy else "OFFLINE"
            port = self.mcp_servers[server_name]['port']
            print(f"  {server_name.upper()} MCP (:{port}): {status_color}{status_text}{Style.RESET_ALL}")
    
    def display_gas_and_network_info(self, gas_data: Dict[str, Any], network_data: Dict[str, Any]):
        """Display gas and network information"""
        print(f"\n{Fore.CYAN}Network Information:{Style.RESET_ALL}")
        
        if network_data:
            block_number = network_data.get('latest_block', 'N/A')
            print(f"  Latest Block: {Fore.GREEN}{block_number}{Style.RESET_ALL}")
        
        if gas_data:
            gas_price = gas_data.get('gas_price_gwei', 'N/A')
            gas_color = Fore.GREEN if isinstance(gas_price, (int, float)) and gas_price < 30 else Fore.YELLOW
            print(f"  Gas Price: {gas_color}{gas_price} Gwei{Style.RESET_ALL}")
    
    def display_token_prices(self, prices: Dict[str, Dict[str, Decimal]]):
        """Display token prices across all DEXes"""
        print(f"\n{Fore.CYAN}Token Prices Across DEXes:{Style.RESET_ALL}")
        print(f"{'Token':<8} {'QuickSwap':<12} {'SushiSwap':<12} {'UniswapV3':<12} {'Curve':<12}")
        print("-" * 60)
        
        for token_symbol, token_prices in prices.items():
            row = f"{token_symbol:<8}"
            for dex_name in ['QuickSwap', 'SushiSwap', 'UniswapV3', 'Curve']:
                if dex_name in token_prices:
                    price = token_prices[dex_name]
                    trend = self.get_price_trend(token_symbol, dex_name)
                    row += f" ${price:<9.4f}{trend:<2}"
                else:
                    row += f" {'N/A':<12}"
            print(row)
    
    def display_arbitrage_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """Display current arbitrage opportunities"""
        print(f"\n{Fore.CYAN}Arbitrage Opportunities:{Style.RESET_ALL}")
        
        if not opportunities:
            print(f"  {Fore.YELLOW}No profitable opportunities found{Style.RESET_ALL}")
            return
            
        print(f"{'Token':<8} {'Buy DEX':<12} {'Sell DEX':<12} {'Price Diff':<12} {'Est. Profit':<12}")
        print("-" * 70)
        
        for i, opp in enumerate(opportunities[:5]):  # Show top 5
            token = opp.token_pair[0]
            price_diff_pct = opp.price_difference * 100
            
            # Color code by profitability
            if opp.profit_estimate > 10:
                profit_color = Fore.GREEN + Style.BRIGHT
            elif opp.profit_estimate > 5:
                profit_color = Fore.GREEN
            else:
                profit_color = Fore.YELLOW
                
            print(f"{token:<8} {opp.buy_dex:<12} {opp.sell_dex:<12} "
                  f"{price_diff_pct:>6.2f}%     {profit_color}${opp.profit_estimate:>7.2f}{Style.RESET_ALL}")
    
    def display_performance_metrics(self):
        """Display performance metrics"""
        print(f"\n{Fore.CYAN}Performance Metrics:{Style.RESET_ALL}")
        uptime = datetime.now() - self.metrics['start_time']
        
        print(f"  Uptime: {Fore.GREEN}{str(uptime).split('.')[0]}{Style.RESET_ALL}")
        print(f"  Total Opportunities: {Fore.GREEN}{self.metrics['total_opportunities']}{Style.RESET_ALL}")
        print(f"  Profitable Ops: {Fore.GREEN}{self.metrics['profitable_opportunities']}{Style.RESET_ALL}")
        print(f"  Max Profit Seen: {Fore.GREEN}${self.metrics['max_profit_seen']:.2f}{Style.RESET_ALL}")
        print(f"  Last Update: {Fore.YELLOW}{self.metrics['last_update'].strftime('%H:%M:%S')}{Style.RESET_ALL}")
    
    def update_metrics(self, opportunities: List[ArbitrageOpportunity]):
        """Update performance metrics"""
        self.metrics['total_opportunities'] += len(opportunities)
        profitable = [op for op in opportunities if op.profit_estimate > 1]
        self.metrics['profitable_opportunities'] += len(profitable)
        
        if opportunities:
            max_profit = max(op.profit_estimate for op in opportunities)
            if max_profit > self.metrics['max_profit_seen']:
                self.metrics['max_profit_seen'] = max_profit
                
        self.metrics['last_update'] = datetime.now()
    
    async def run_monitoring_loop(self):
        """Main monitoring loop"""
        print(f"{Fore.GREEN}Starting Enhanced Monitoring Terminal...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        try:
            while True:
                # Clear screen and display header
                self.clear_screen()
                
                # Check MCP server health
                health_status = await self.check_mcp_server_health()
                self.display_header(health_status)
                
                # Get gas and network data
                gas_data = await self.get_gas_estimates()
                network_data = await self.get_network_status()
                self.display_gas_and_network_info(gas_data or {}, network_data or {})
                
                # Get token prices
                prices = await self.get_all_token_prices()
                self.update_price_history(prices)
                self.display_token_prices(prices)
                
                # Find arbitrage opportunities
                opportunities = self.find_arbitrage_opportunities(prices)
                self.display_arbitrage_opportunities(opportunities)
                
                # Update and display metrics
                self.update_metrics(opportunities)
                self.display_performance_metrics()
                
                # Status line
                active_servers = sum(1 for status in health_status.values() if status)
                print(f"\n{Fore.GREEN}● MONITORING ACTIVE{Style.RESET_ALL} - "
                      f"{Fore.CYAN}{active_servers}/3 MCP Servers Online{Style.RESET_ALL} - "
                      f"{Fore.YELLOW}Refreshing in 3s...{Style.RESET_ALL}")
                
                # Wait before next update
                await asyncio.sleep(3)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Monitoring stopped by user{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Error in monitoring loop: {e}{Style.RESET_ALL}")

async def main():
    """Main entry point"""
    try:
        # Install colorama if not available
        try:
            import colorama
        except ImportError:
            print("Installing colorama for colored output...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
            import colorama
        
        monitor = EnhancedMonitoringTerminal()
        await monitor.run_monitoring_loop()
        
    except Exception as e:
        print(f"Failed to start monitoring terminal: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
