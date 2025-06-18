#!/usr/bin/env python3
"""
Real-Time Multi-DEX Price Feed System
===================================

Provides real-time price data for 15 tokens across 5 DEXes with no fallback,
using simulated market data for demonstration.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import random
import websockets
import aiohttp
from dataclasses import dataclass

@dataclass
class PriceData:
    """Price data structure"""
    token: str
    dex: str
    price_usd: float
    liquidity_usd: float
    volume_24h: float
    timestamp: str
    change_24h: float

class RealTimePriceFeed:
    """Real-time price feed for multiple DEXes"""
    
    def __init__(self):
        # 15 Popular tokens
        self.tokens = [
            'WMATIC', 'USDC', 'USDT', 'WETH', 'WBTC',
            'LINK', 'UNI', 'AAVE', 'SUSHI', 'CRV',
            'QUICK', 'BAL', 'COMP', 'YFI', 'SNX'
        ]
        
        # 5 Major DEXes on Polygon
        self.dexes = [
            'QuickSwap',
            'SushiSwap', 
            'Uniswap V3',
            'Balancer',
            'Curve'
        ]
        
        # Base prices (simulated realistic prices)
        self.base_prices = {
            'WMATIC': 0.45,
            'USDC': 1.00,
            'USDT': 0.999,
            'WETH': 1850.0,
            'WBTC': 26500.0,
            'LINK': 6.80,
            'UNI': 5.20,
            'AAVE': 92.0,
            'SUSHI': 0.78,
            'CRV': 0.35,
            'QUICK': 0.045,
            'BAL': 3.80,
            'COMP': 34.5,
            'YFI': 6200.0,
            'SNX': 1.85
        }
        
        # Current prices (will fluctuate)
        self.current_prices = {}
        self.price_history = {}
        self.arbitrage_opportunities = []
        
        # Initialize current prices
        for token in self.tokens:
            self.current_prices[token] = {}
            self.price_history[token] = {}
            for dex in self.dexes:
                # Add small random variation per DEX
                variation = random.uniform(0.995, 1.005)
                self.current_prices[token][dex] = self.base_prices[token] * variation
                self.price_history[token][dex] = []
    
    async def start_price_feed(self):
        """Start the real-time price feed"""
        print("🚀 Starting Real-Time Multi-DEX Price Feed")
        print("="*80)
        print(f"📊 Tracking {len(self.tokens)} tokens across {len(self.dexes)} DEXes")
        print("🔄 Updating prices every 2 seconds")
        print("💡 Press Ctrl+C to stop")
        print("="*80)
        
        try:
            # Start price update loop
            price_task = asyncio.create_task(self.price_update_loop())
            
            # Start arbitrage detection
            arb_task = asyncio.create_task(self.arbitrage_detection_loop())
            
            # Start display loop
            display_task = asyncio.create_task(self.display_loop())
            
            # Run all tasks
            await asyncio.gather(price_task, arb_task, display_task)
            
        except KeyboardInterrupt:
            print("\n👋 Stopping price feed...")
    
    async def price_update_loop(self):
        """Continuously update prices"""
        while True:
            try:
                await self.update_all_prices()
                await asyncio.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"❌ Price update error: {e}")
                await asyncio.sleep(1)
    
    async def update_all_prices(self):
        """Update prices for all tokens and DEXes"""
        timestamp = datetime.now().isoformat()
        
        for token in self.tokens:
            for dex in self.dexes:
                # Simulate realistic price movement
                current_price = self.current_prices[token][dex]
                
                # Random price change (-0.5% to +0.5%)
                change_pct = random.uniform(-0.005, 0.005)
                
                # Occasional larger movements for volatility
                if random.random() < 0.05:  # 5% chance
                    change_pct = random.uniform(-0.02, 0.02)
                
                # Apply change
                new_price = current_price * (1 + change_pct)
                
                # Ensure prices don't drift too far from base
                max_deviation = 0.05  # 5% max deviation
                base_price = self.base_prices[token]
                if abs(new_price - base_price) / base_price > max_deviation:
                    # Pull back towards base price
                    new_price = base_price + (new_price - base_price) * 0.8
                
                self.current_prices[token][dex] = new_price
                
                # Add to history
                if len(self.price_history[token][dex]) > 100:
                    self.price_history[token][dex].pop(0)
                
                self.price_history[token][dex].append({
                    'price': new_price,
                    'timestamp': timestamp,
                    'change': change_pct
                })
    
    async def arbitrage_detection_loop(self):
        """Detect arbitrage opportunities"""
        while True:
            try:
                await self.detect_arbitrage_opportunities()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"❌ Arbitrage detection error: {e}")
                await asyncio.sleep(2)
    
    async def detect_arbitrage_opportunities(self):
        """Detect arbitrage opportunities between DEXes"""
        self.arbitrage_opportunities = []
        
        for token in self.tokens:
            prices = []
            for dex in self.dexes:
                prices.append((dex, self.current_prices[token][dex]))
            
            # Sort by price
            prices.sort(key=lambda x: x[1])
            
            # Check if there's a profitable spread
            lowest_dex, lowest_price = prices[0]
            highest_dex, highest_price = prices[-1]
            
            spread_pct = (highest_price - lowest_price) / lowest_price
            
            # If spread > 0.1% (accounting for fees), it's an opportunity
            if spread_pct > 0.001:
                profit_usd = (highest_price - lowest_price) * 1000  # Assume 1000 token trade
                
                self.arbitrage_opportunities.append({
                    'token': token,
                    'buy_dex': lowest_dex,
                    'sell_dex': highest_dex,
                    'buy_price': lowest_price,
                    'sell_price': highest_price,
                    'spread_pct': spread_pct,
                    'profit_usd': profit_usd,
                    'timestamp': datetime.now().isoformat()
                })
    
    async def display_loop(self):
        """Display prices and opportunities"""
        while True:
            try:
                # Clear screen
                print("\033[2J\033[H", end="")
                
                # Display header
                print("🔥 REAL-TIME MULTI-DEX PRICE FEED")
                print("="*100)
                print(f"⏰ Last Update: {datetime.now().strftime('%H:%M:%S')}")
                print("")
                
                # Display prices in a nice table
                await self.display_price_table()
                
                # Display arbitrage opportunities
                await self.display_arbitrage_opportunities()
                
                await asyncio.sleep(3)  # Update display every 3 seconds
                
            except Exception as e:
                print(f"❌ Display error: {e}")
                await asyncio.sleep(1)
    
    async def display_price_table(self):
        """Display prices in a table format"""
        print("💰 TOKEN PRICES (USD)")
        print("-"*100)
        
        # Header
        header = f"{'TOKEN':<8}"
        for dex in self.dexes:
            header += f"{dex:<15}"
        header += f"{'SPREAD':<10}{'BEST ARB':<12}"
        print(header)
        print("-"*100)
        
        # Display each token
        for token in self.tokens:
            row = f"{token:<8}"
            
            prices = []
            for dex in self.dexes:
                price = self.current_prices[token][dex]
                prices.append(price)
                
                # Color coding for price
                if price == min(prices) and len(prices) == len(self.dexes):
                    row += f"\033[92m${price:<14.4f}\033[0m"  # Green for lowest
                elif price == max(prices) and len(prices) == len(self.dexes):
                    row += f"\033[91m${price:<14.4f}\033[0m"  # Red for highest
                else:
                    row += f"${price:<14.4f}"
            
            # Calculate spread
            min_price = min(prices)
            max_price = max(prices)
            spread = ((max_price - min_price) / min_price) * 100
            
            row += f"{spread:<9.3f}%"
            
            # Best arbitrage for this token
            token_arbs = [arb for arb in self.arbitrage_opportunities if arb['token'] == token]
            if token_arbs:
                best_arb = max(token_arbs, key=lambda x: x['profit_usd'])
                row += f"${best_arb['profit_usd']:<11.2f}"
            else:
                row += f"${'0.00':<11}"
            
            print(row)
    
    async def display_arbitrage_opportunities(self):
        """Display current arbitrage opportunities"""
        print(f"\n🎯 ARBITRAGE OPPORTUNITIES ({len(self.arbitrage_opportunities)} found)")
        print("-"*100)
        
        if not self.arbitrage_opportunities:
            print("📭 No profitable opportunities at the moment")
            return
        
        # Sort by profit
        sorted_opps = sorted(self.arbitrage_opportunities, key=lambda x: x['profit_usd'], reverse=True)
        
        # Display header
        print(f"{'TOKEN':<8}{'BUY DEX':<15}{'SELL DEX':<15}{'BUY PRICE':<12}{'SELL PRICE':<12}{'SPREAD':<10}{'PROFIT':<10}")
        print("-"*100)
        
        # Display top 10 opportunities
        for opp in sorted_opps[:10]:
            print(f"{opp['token']:<8}"
                  f"{opp['buy_dex']:<15}"
                  f"{opp['sell_dex']:<15}"
                  f"${opp['buy_price']:<11.4f}"
                  f"${opp['sell_price']:<11.4f}"
                  f"{opp['spread_pct']*100:<9.3f}%"
                  f"${opp['profit_usd']:<9.2f}")
    
    def get_token_price(self, token: str, dex: str) -> Optional[float]:
        """Get current price for a specific token on a specific DEX"""
        return self.current_prices.get(token, {}).get(dex)
    
    def get_all_prices(self) -> Dict:
        """Get all current prices"""
        return self.current_prices
    
    def get_arbitrage_opportunities(self) -> List[Dict]:
        """Get current arbitrage opportunities"""
        return self.arbitrage_opportunities
    
    async def save_price_data(self, filename: str = "price_data.json"):
        """Save current price data to file"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'prices': self.current_prices,
            'arbitrage_opportunities': self.arbitrage_opportunities
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Price data saved to {filename}")

# WebSocket server for real-time data streaming
class PriceFeedWebSocketServer:
    """WebSocket server for streaming price data"""
    
    def __init__(self, price_feed: RealTimePriceFeed):
        self.price_feed = price_feed
        self.clients = set()
    
    async def start_server(self, port: int = 8890):
        """Start WebSocket server"""
        try:
            server = await websockets.serve(
                self.handle_client,
                "localhost",
                port
            )
            print(f"🔌 WebSocket server started on ws://localhost:{port}")
            return server
        except Exception as e:
            print(f"❌ Failed to start WebSocket server: {e}")
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        try:
            self.clients.add(websocket)
            print(f"🔗 Client connected ({len(self.clients)} total)")
            
            # Send initial data
            await self.send_price_data(websocket)
            
            # Keep connection alive and send updates
            async for message in websocket:
                try:
                    data = json.loads(message)
                    command = data.get('command', '')
                    
                    if command == 'get_prices':
                        await self.send_price_data(websocket)
                    elif command == 'get_arbitrage':
                        await self.send_arbitrage_data(websocket)
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'error': 'Invalid JSON format'
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"🔌 Client disconnected ({len(self.clients)} total)")
    
    async def send_price_data(self, websocket):
        """Send current price data to client"""
        data = {
            'type': 'price_update',
            'timestamp': datetime.now().isoformat(),
            'prices': self.price_feed.get_all_prices()
        }
        await websocket.send(json.dumps(data))
    
    async def send_arbitrage_data(self, websocket):
        """Send arbitrage opportunities to client"""
        data = {
            'type': 'arbitrage_update',
            'timestamp': datetime.now().isoformat(),
            'opportunities': self.price_feed.get_arbitrage_opportunities()
        }
        await websocket.send(json.dumps(data))
    
    async def broadcast_updates(self):
        """Broadcast updates to all connected clients"""
        while True:
            try:
                if self.clients:
                    # Send price updates
                    price_data = {
                        'type': 'price_update',
                        'timestamp': datetime.now().isoformat(),
                        'prices': self.price_feed.get_all_prices()
                    }
                    
                    # Send arbitrage updates
                    arb_data = {
                        'type': 'arbitrage_update',
                        'timestamp': datetime.now().isoformat(),
                        'opportunities': self.price_feed.get_arbitrage_opportunities()
                    }
                    
                    # Broadcast to all clients
                    disconnected = []
                    for client in self.clients:
                        try:
                            await client.send(json.dumps(price_data))
                            await asyncio.sleep(0.1)
                            await client.send(json.dumps(arb_data))
                        except websockets.exceptions.ConnectionClosed:
                            disconnected.append(client)
                    
                    # Remove disconnected clients
                    for client in disconnected:
                        self.clients.discard(client)
                
                await asyncio.sleep(5)  # Broadcast every 5 seconds
                
            except Exception as e:
                print(f"❌ Broadcast error: {e}")
                await asyncio.sleep(2)

async def main():
    """Main entry point"""
    print("🚀 Multi-DEX Real-Time Price Feed System")
    print("="*80)
    
    # Create price feed
    price_feed = RealTimePriceFeed()
    
    # Create WebSocket server
    ws_server = PriceFeedWebSocketServer(price_feed)
    
    try:
        # Start WebSocket server
        server = await ws_server.start_server()
        
        # Start broadcasting
        broadcast_task = asyncio.create_task(ws_server.broadcast_updates())
        
        # Start price feed
        price_feed_task = asyncio.create_task(price_feed.start_price_feed())
        
        # Run both tasks
        await asyncio.gather(broadcast_task, price_feed_task)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down price feed system...")
    except Exception as e:
        print(f"❌ System error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
