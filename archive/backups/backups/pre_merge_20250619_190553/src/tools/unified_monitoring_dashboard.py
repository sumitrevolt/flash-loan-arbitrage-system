#!/usr/bin/env python3
"""
Unified Monitoring Dashboard - Consolidated Version
==================================================

This file consolidates the functionality from:
- live_arbitrage_monitor.py (281 lines, real-time monitoring)
- comprehensive_arbitrage_dashboard.py (394 lines, full dashboard)
- live_arbitrage_dashboard.py (similar functionality)

Features:
- Real-time DEX price monitoring and arbitrage calculation
- MCP servers status monitoring
- Live arbitrage opportunity display
- System health monitoring
- Performance metrics and statistics
- Interactive web dashboard
- Colored console output
"""

import asyncio
import sys
import platform

# Windows compatibility
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import aiohttp
import json
import time
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal, getcontext
from dataclasses import dataclass, asdict
from pathlib import Path
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import colorama
from colorama import Fore, Back, Style
from web3 import Web3
from dotenv import load_dotenv

# Initialize colorama for colored output
colorama.init(autoreset=True)
getcontext().prec = 50

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MCPServerStatus:
    """MCP server status information"""
    name: str
    port: int
    url: str
    status: bool
    last_check: datetime
    response_time: float = 0.0
    error_count: int = 0

@dataclass
class TokenInfo:
    """Token information"""
    symbol: str
    address: str
    decimals: int
    price_usd: float = 0.0

@dataclass
class DexInfo:
    """DEX information"""
    name: str
    router: str
    fee: float
    volume_24h: float = 0.0

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity display data"""
    token_pair: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    price_diff: float
    price_diff_pct: float
    potential_profit: float
    confidence: float
    timestamp: datetime

class UnifiedMonitoringDashboard:
    """Comprehensive monitoring dashboard for the arbitrage system"""
    
    def __init__(self):
        self.logger = logging.getLogger("MonitoringDashboard")
        self.running = False
        
        # MCP servers to monitor
        self.mcp_servers = {
            'coordinator': MCPServerStatus('Coordinator', 9000, 'http://localhost:9000', False, datetime.now()),
            'arbitrage': MCPServerStatus('Arbitrage System', 8001, 'http://localhost:8001', False, datetime.now()),
            'risk_manager': MCPServerStatus('Risk Manager', 8002, 'http://localhost:8002', False, datetime.now()),
            'analytics': MCPServerStatus('Analytics Engine', 8003, 'http://localhost:8003', False, datetime.now())
        }
        
        # Token configurations
        self.tokens = {
            'WMATIC': TokenInfo('WMATIC', '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 18),
            'USDC': TokenInfo('USDC', '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 6),
            'USDT': TokenInfo('USDT', '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 6),
            'DAI': TokenInfo('DAI', '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', 18),
            'WETH': TokenInfo('WETH', '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', 18)
        }
        
        # DEX configurations
        self.dexes = {
            'QuickSwap': DexInfo('QuickSwap', '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff', 0.003),
            'SushiSwap': DexInfo('SushiSwap', '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506', 0.003),
            'UniswapV3': DexInfo('UniswapV3', '0xE592427A0AEce92De3Edee1F18E0157C05861564', 0.003),
            'Curve': DexInfo('Curve', '0x094d12e5b541784701FD8d65F11fc0598FBC6332', 0.0004)
        }
        
        # Current data
        self.current_prices = {}
        self.current_opportunities = []
        self.system_stats = {
            'uptime_start': datetime.now(),
            'opportunities_found': 0,
            'total_volume_monitored': 0,
            'avg_response_time': 0,
            'error_count': 0
        }
        
        # Web3 connection
        self._initialize_web3()
        
        # Flask app for web interface
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_web_routes()
    
    def _initialize_web3(self):
        """Initialize Web3 connection"""
        rpc_url = os.getenv('POLYGON_RPC_URL')
        if rpc_url:
            self.web3 = Web3(Web3.HTTPProvider(rpc_url))
            if self.web3.is_connected():
                logger.info("Connected to Polygon network")
            else:
                logger.warning("Failed to connect to Polygon network")
        else:
            logger.warning("No RPC URL configured")
            self.web3 = None
    
    async def check_mcp_server_status(self, server_name: str) -> bool:
        """Check status of individual MCP server"""
        server = self.mcp_servers[server_name]
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{server.url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        server.status = True
                        server.response_time = response_time
                        server.last_check = datetime.now()
                        return True
                    else:
                        server.status = False
                        server.error_count += 1
                        return False
        except Exception as e:
            server.status = False
            server.error_count += 1
            server.last_check = datetime.now()
            self.logger.debug(f"Health check failed for {server_name}: {e}")
            return False
    
    async def monitor_all_servers(self):
        """Monitor all MCP servers"""
        while self.running:
            try:
                # Check all servers concurrently
                tasks = [self.check_mcp_server_status(name) for name in self.mcp_servers.keys()]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update system stats
                active_servers = sum(1 for r in results if r is True)
                total_servers = len(self.mcp_servers)
                
                # Calculate average response time
                response_times = [s.response_time for s in self.mcp_servers.values() if s.status]
                if response_times:
                    self.system_stats['avg_response_time'] = sum(response_times) / len(response_times)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring servers: {e}")
                await asyncio.sleep(5)
    
    async def fetch_arbitrage_opportunities(self):
        """Fetch arbitrage opportunities from the arbitrage system"""
        try:
            arbitrage_server = self.mcp_servers.get('arbitrage')
            if not arbitrage_server or not arbitrage_server.status:
                return []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{arbitrage_server.url}/opportunities") as response:
                    if response.status == 200:
                        data = await response.json()
                        opportunities = []
                        
                        for opp_data in data.get('opportunities', []):
                            opportunity = ArbitrageOpportunity(
                                token_pair=opp_data['token_pair'],
                                buy_dex=opp_data['dex_buy'],
                                sell_dex=opp_data['dex_sell'],
                                buy_price=float(opp_data['buy_price']),
                                sell_price=float(opp_data['sell_price']),
                                price_diff=float(opp_data['sell_price']) - float(opp_data['buy_price']),
                                price_diff_pct=float(opp_data['profit_percentage']),
                                potential_profit=float(opp_data['net_profit']),
                                confidence=float(opp_data['confidence']),
                                timestamp=datetime.now()
                            )
                            opportunities.append(opportunity)
                        
                        self.current_opportunities = opportunities
                        self.system_stats['opportunities_found'] += len(opportunities)
                        return opportunities
                    
        except Exception as e:
            self.logger.debug(f"Error fetching opportunities: {e}")
        
        return []
    
    def display_console_dashboard(self):
        """Display real-time dashboard in console"""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        # WARNING: This is a security risk
        # WARNING: This is a security risk
        
        # Header
        print(f"{Fore.CYAN}{Style.BRIGHT}╔══════════════════════════════════════════════════════════════╗")
        print(f"{Fore.CYAN}{Style.BRIGHT}║               UNIFIED MONITORING DASHBOARD                   ║")
        print(f"{Fore.CYAN}{Style.BRIGHT}╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        print()
        
        # System Overview
        uptime = datetime.now() - self.system_stats['uptime_start']
        print(f"{Fore.YELLOW}{Style.BRIGHT}📊 SYSTEM OVERVIEW{Style.RESET_ALL}")
        print(f"Uptime: {str(uptime).split('.')[0]}")
        print(f"Opportunities Found: {self.system_stats['opportunities_found']}")
        print(f"Average Response Time: {self.system_stats['avg_response_time']:.3f}s")
        print()
        
        # MCP Servers Status
        print(f"{Fore.YELLOW}{Style.BRIGHT}🔧 MCP SERVERS STATUS{Style.RESET_ALL}")
        print("┌─────────────────┬──────┬──────────┬─────────────┬────────────────┐")
        print("│ Server          │ Port │ Status   │ Response    │ Last Check     │")
        print("├─────────────────┼──────┼──────────┼─────────────┼────────────────┤")
        
        for name, server in self.mcp_servers.items():
            status_color = Fore.GREEN if server.status else Fore.RED
            status_text = "✓ Online" if server.status else "✗ Offline"
            response_time = f"{server.response_time:.3f}s" if server.status else "N/A"
            last_check = server.last_check.strftime("%H:%M:%S")
            
            print(f"│ {name:<15} │ {server.port:<4} │ {status_color}{status_text:<8}{Style.RESET_ALL} │ {response_time:<11} │ {last_check:<14} │")
        
        print("└─────────────────┴──────┴──────────┴─────────────┴────────────────┘")
        print()
        
        # Arbitrage Opportunities
        print(f"{Fore.YELLOW}{Style.BRIGHT}💰 LIVE ARBITRAGE OPPORTUNITIES{Style.RESET_ALL}")
        
        if self.current_opportunities:
            print("┌────────────────┬─────────────┬─────────────┬──────────┬──────────┬─────────────┐")
            print("│ Token Pair     │ Buy DEX     │ Sell DEX    │ Profit % │ Profit $ │ Confidence  │")
            print("├────────────────┼─────────────┼─────────────┼──────────┼──────────┼─────────────┤")
            
            for opp in self.current_opportunities[:10]:  # Show top 10
                profit_color = Fore.GREEN if opp.potential_profit > 0 else Fore.RED
                confidence_color = Fore.GREEN if opp.confidence > 0.8 else Fore.YELLOW if opp.confidence > 0.5 else Fore.RED
                
                print(f"│ {opp.token_pair:<14} │ {opp.buy_dex:<11} │ {opp.sell_dex:<11} │ "
                      f"{profit_color}{opp.price_diff_pct:>7.2f}%{Style.RESET_ALL} │ "
                      f"{profit_color}${opp.potential_profit:>7.2f}{Style.RESET_ALL} │ "
                      f"{confidence_color}{opp.confidence:>9.2f}{Style.RESET_ALL} │")
            
            print("└────────────────┴─────────────┴─────────────┴──────────┴──────────┴─────────────┘")
        else:
            print(f"{Fore.YELLOW}No arbitrage opportunities found at the moment.{Style.RESET_ALL}")
        
        print()
        
        # Token Prices (if available)
        print(f"{Fore.YELLOW}{Style.BRIGHT}💎 TOKEN PRICES{Style.RESET_ALL}")
        if self.current_prices:
            print("┌─────────┬─────────────────┬────────────────────┐")
            print("│ Token   │ Price USD       │ 24h Change         │")
            print("├─────────┼─────────────────┼────────────────────┤")
            
            for symbol, price_data in self.current_prices.items():
                price = price_data.get('usd', 0)
                change_24h = price_data.get('usd_24h_change', 0)
                change_color = Fore.GREEN if change_24h >= 0 else Fore.RED
                change_symbol = "+" if change_24h >= 0 else ""
                
                print(f"│ {symbol:<7} │ ${price:>13.6f} │ {change_color}{change_symbol}{change_24h:>7.2f}%{Style.RESET_ALL}          │")
            
            print("└─────────┴─────────────────┴────────────────────┘")
        else:
            print(f"{Fore.YELLOW}Price data not available.{Style.RESET_ALL}")
        
        print()
        print(f"{Fore.CYAN}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Press Ctrl+C to exit{Style.RESET_ALL}")
    
    async def fetch_token_prices(self):
        """Fetch current token prices"""
        try:
            # Use CoinGecko API for price data
            token_ids = {
                'WMATIC': 'matic-network',
                'USDC': 'usd-coin',
                'USDT': 'tether',
                'DAI': 'dai',
                'WETH': 'weth'
            }
            
            ids_str = ','.join(token_ids.values())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Map back to our token symbols
                        prices = {}
                        for symbol, coin_id in token_ids.items():
                            if coin_id in data:
                                prices[symbol] = data[coin_id]
                        
                        self.current_prices = prices
                        
        except Exception as e:
            self.logger.debug(f"Error fetching token prices: {e}")
    
    async def run_console_dashboard(self):
        """Run console-based dashboard"""
        self.logger.info("Starting console dashboard...")
        
        while self.running:
            try:
                # Fetch data
                await asyncio.gather(
                    self.fetch_arbitrage_opportunities(),
                    self.fetch_token_prices(),
                    return_exceptions=True
                )
                
                # Display dashboard
                self.display_console_dashboard()
                
                # Wait before next update
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in console dashboard: {e}")
                await asyncio.sleep(2)
    
    def _setup_web_routes(self):
        """Setup Flask routes for web dashboard"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                'servers': {name: asdict(server) for name, server in self.mcp_servers.items()},
                'stats': self.system_stats,
                'opportunities': [asdict(opp) for opp in self.current_opportunities],
                'prices': self.current_prices,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/opportunities')
        def api_opportunities():
            return jsonify({
                'opportunities': [asdict(opp) for opp in self.current_opportunities],
                'count': len(self.current_opportunities),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/servers')
        def api_servers():
            return jsonify({
                'servers': {name: asdict(server) for name, server in self.mcp_servers.items()},
                'timestamp': datetime.now().isoformat()
            })
    
    async def run_web_dashboard(self):
        """Run web-based dashboard"""
        self.logger.info("Starting web dashboard on http://localhost:5000")
        
        # Start Flask app in thread
        import threading
        
        def run_flask():
            self.app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # Keep updating data
        while self.running:
            try:
                await asyncio.gather(
                    self.fetch_arbitrage_opportunities(),
                    self.fetch_token_prices(),
                    return_exceptions=True
                )
                
                await asyncio.sleep(10)  # Update every 10 seconds for web
                
            except Exception as e:
                self.logger.error(f"Error in web dashboard: {e}")
                await asyncio.sleep(5)
    
    async def run(self, mode: str = "console"):
        """Main run method"""
        self.running = True
        
        try:
            # Start server monitoring
            monitor_task = asyncio.create_task(self.monitor_all_servers())
            
            if mode == "console":
                dashboard_task = asyncio.create_task(self.run_console_dashboard())
            elif mode == "web":
                dashboard_task = asyncio.create_task(self.run_web_dashboard())
            else:
                # Run both
                console_task = asyncio.create_task(self.run_console_dashboard())
                web_task = asyncio.create_task(self.run_web_dashboard())
                dashboard_task = asyncio.gather(console_task, web_task)
            
            # Wait for tasks
            await asyncio.gather(monitor_task, dashboard_task)
            
        except KeyboardInterrupt:
            self.logger.info("Dashboard stopped by user")
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")
        finally:
            self.running = False
            self.logger.info("Dashboard shutdown complete")

def create_dashboard_template():
    """Create basic HTML template for web dashboard"""
    template_dir = Path('templates')
    template_dir.mkdir(exist_ok=True)
    
    template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Monitoring Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }
        .header { text-align: center; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #333; padding: 20px; border-radius: 8px; text-align: center; }
        .servers { margin-bottom: 30px; }
        .server { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #555; }
        .server.online { color: #4CAF50; }
        .server.offline { color: #f44336; }
        .opportunities { margin-bottom: 30px; }
        .opportunity { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; padding: 10px; border-bottom: 1px solid #555; }
        .profitable { color: #4CAF50; }
        .unprofitable { color: #f44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Unified Monitoring Dashboard</h1>
        <p>Real-time monitoring of arbitrage system</p>
    </div>
    
    <div id="content">
        <div class="stats">
            <div class="stat-card">
                <h3>Uptime</h3>
                <p id="uptime">Loading...</p>
            </div>
            <div class="stat-card">
                <h3>Opportunities Found</h3>
                <p id="opportunities-count">Loading...</p>
            </div>
            <div class="stat-card">
                <h3>Avg Response Time</h3>
                <p id="response-time">Loading...</p>
            </div>
        </div>
        
        <div class="servers">
            <h2>MCP Servers Status</h2>
            <div id="servers-list">Loading...</div>
        </div>
        
        <div class="opportunities">
            <h2>Live Arbitrage Opportunities</h2>
            <div id="opportunities-list">Loading...</div>
        </div>
    </div>
    
    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update stats
                document.getElementById('uptime').textContent = formatUptime(data.stats.uptime_start);
                document.getElementById('opportunities-count').textContent = data.stats.opportunities_found;
                document.getElementById('response-time').textContent = data.stats.avg_response_time.toFixed(3) + 's';
                
                // Update servers
                const serversList = document.getElementById('servers-list');
                serversList.innerHTML = '';
                for (const [name, server] of Object.entries(data.servers)) {
                    const serverDiv = document.createElement('div');
                    serverDiv.className = `server ${server.status ? 'online' : 'offline'}`;
                    serverDiv.innerHTML = `
                        <span>${name}</span>
                        <span>Port: ${server.port}</span>
                        <span>${server.status ? '✓ Online' : '✗ Offline'}</span>
                        <span>${server.status ? server.response_time.toFixed(3) + 's' : 'N/A'}</span>
                    `;
                    serversList.appendChild(serverDiv);
                }
                
                // Update opportunities
                const opportunitiesList = document.getElementById('opportunities-list');
                opportunitiesList.innerHTML = '';
                data.opportunities.slice(0, 10).forEach(opp => {
                    const oppDiv = document.createElement('div');
                    oppDiv.className = `opportunity ${opp.potential_profit > 0 ? 'profitable' : 'unprofitable'}`;
                    oppDiv.innerHTML = `
                        <span>${opp.token_pair}</span>
                        <span>${opp.buy_dex}</span>
                        <span>${opp.sell_dex}</span>
                        <span>${opp.price_diff_pct.toFixed(2)}%</span>
                        <span>$${opp.potential_profit.toFixed(2)}</span>
                        <span>${opp.confidence.toFixed(2)}</span>
                    `;
                    opportunitiesList.appendChild(oppDiv);
                });
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }
        
        function formatUptime(startTime) {
            const start = new Date(startTime);
            const now = new Date();
            const diff = now - start;
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
            return `${hours}h ${minutes}m ${seconds}s`;
        }
        
        // Update every 5 seconds
        setInterval(updateDashboard, 5000);
        updateDashboard(); // Initial load
    </script>
</body>
</html>
"""
    
    with open(template_dir / 'dashboard.html', 'w') as f:
        f.write(template_content)

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Monitoring Dashboard')
    parser.add_argument('--mode', choices=['console', 'web', 'both'], 
                       default='console', help='Dashboard mode')
    
    args = parser.parse_args()
    
    # Create HTML template if running web mode
    if args.mode in ['web', 'both']:
        create_dashboard_template()
    
    # Create and run dashboard
    dashboard = UnifiedMonitoringDashboard()
    
    try:
        await dashboard.run(args.mode)
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Dashboard failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
