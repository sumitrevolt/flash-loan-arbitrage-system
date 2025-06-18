#!/usr/bin/env python3
"""
Real-time Data Connector for Flash Loan Arbitrage System
Connects to Foundry MCP Server and provides real-time price feeds
"""

import asyncio
import json
import logging
import platform
import aiohttp
import websockets
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

# Setup Windows-compatible event loop
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@dataclass
class PriceUpdate:
    """Real-time price update data"""
    token_pair: str
    dex: str
    price: float
    timestamp: datetime
    volume_24h: float = 0.0
    liquidity: float = 0.0

class RealTimeDataConnector:
    """Real-time data connector for MCP server integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger("RealTimeConnector")
        self.config = config
        
        # Connection settings
        mcp_config = config.get('foundry_mcp_server', {})
        self.host = mcp_config.get('host', '127.0.0.1')
        self.port = mcp_config.get('port', 8001)
        self.health_url = f"http://{self.host}:{self.port}/health"
        self.ws_url = f"ws://{self.host}:{self.port}/ws/prices"
        
        # Connection state
        self.connected = False
        self.websocket = None
        self.session = None
        
        # Data management
        self.price_cache = {}
        self.last_update = {}
        self.subscribers = {}
        
        # Reconnection settings
        self.reconnect_interval = mcp_config.get('reconnect_interval', 5)
        self.max_reconnect_attempts = mcp_config.get('max_reconnect_attempts', 10)
        self.reconnect_attempts = 0
          # Running state
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start the real-time data connector"""
        if self.running:
            return
            
        self.logger.info("Starting real-time data connector...")
        self.running = True
        
        # Create Windows-compatible HTTP session to avoid aiodns issues
        connector = aiohttp.TCPConnector(use_dns_cache=False)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        # Start connection and data tasks
        connection_task = asyncio.create_task(self._maintain_connection())
        self.tasks.append(connection_task)
        
        self.logger.info("Real-time data connector started")
    
    async def stop(self):
        """Stop the real-time data connector"""
        if not self.running:
            return
            
        self.logger.info("Stopping real-time data connector...")
        self.running = False
        
        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # Close HTTP session
        if self.session:
            await self.session.close()
            self.session = None
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        self.connected = False
        
        self.logger.info("Real-time data connector stopped")
    
    async def _maintain_connection(self):
        """Maintain connection to MCP server"""
        while self.running:
            try:
                # Check server health first
                if await self._check_server_health():
                    # Try to establish WebSocket connection
                    await self._connect_websocket()
                else:
                    self.logger.warning("MCP server health check failed")
                    await asyncio.sleep(self.reconnect_interval)
                    continue
                    
            except Exception as e:
                self.logger.error(f"Connection error: {e}")
                self.connected = False
                self.reconnect_attempts += 1
                
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    self.logger.error("Max reconnection attempts reached")
                    break
                    
                await asyncio.sleep(self.reconnect_interval)
    
    async def _check_server_health(self) -> bool:
        """Check if MCP server is healthy"""
        try:
            async with self.session.get(self.health_url, timeout=5) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return health_data.get('status') == 'healthy'
        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            return False
        
        return False
    
    async def _connect_websocket(self):
        """Connect to WebSocket for real-time data"""
        try:
            self.logger.info(f"Connecting to WebSocket: {self.ws_url}")
            
            # For now, we'll use HTTP polling since WebSocket might not be implemented
            # TODO: Replace with actual WebSocket when available
            await self._start_http_polling()
            
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def _start_http_polling(self):
        """Start HTTP polling for price data (fallback method)"""
        self.logger.info("Starting HTTP polling for real-time data")
        self.connected = True
        self.reconnect_attempts = 0
        
        while self.running and self.connected:
            try:
                # Poll for price data
                await self._poll_price_data()
                
                # Wait for next poll interval
                poll_interval = self.config.get('data_sources', {}).get('price_update_interval', 1)
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                self.logger.error(f"Polling error: {e}")
                self.connected = False
                break
    
    async def _poll_price_data(self):
        """Poll for price data from MCP server"""
        try:
            # Get price data from MCP server (using mock data for now)
            # TODO: Replace with actual MCP server API call
            price_data = await self._get_mock_price_data()
            
            # Process and update price cache
            for update in price_data:
                await self._process_price_update(update)
                
        except Exception as e:
            self.logger.error(f"Failed to poll price data: {e}")
            raise
    
    async def _get_mock_price_data(self) -> List[PriceUpdate]:
        """Get mock price data (replace with real MCP server call)"""
        # Mock data for testing
        current_time = datetime.now()
        
        mock_data = [
            PriceUpdate(
                token_pair="WMATIC/USDC",
                dex="quickswap",
                price=0.85 + (time.time() % 10) * 0.01,  # Slight price variation
                timestamp=current_time,
                volume_24h=1000000.0,
                liquidity=5000000.0
            ),
            PriceUpdate(
                token_pair="WMATIC/USDC",
                dex="uniswap_v3",
                price=0.85 + (time.time() % 8) * 0.012,  # Different variation
                timestamp=current_time,
                volume_24h=800000.0,
                liquidity=4500000.0
            ),
            PriceUpdate(
                token_pair="WETH/USDC",
                dex="quickswap",
                price=2450.0 + (time.time() % 20) * 2.0,
                timestamp=current_time,
                volume_24h=2000000.0,
                liquidity=10000000.0
            )
        ]
        
        return mock_data
    
    async def _process_price_update(self, update: PriceUpdate):
        """Process incoming price update"""
        key = f"{update.token_pair}_{update.dex}"
        
        # Update cache
        self.price_cache[key] = update
        self.last_update[key] = update.timestamp
        
        # Notify subscribers
        if key in self.subscribers:
            for callback in self.subscribers[key]:
                try:
                    await callback(update)
                except Exception as e:
                    self.logger.error(f"Subscriber callback error: {e}")
    
    def subscribe_to_pair(self, token_pair: str, dex: str, callback: Callable):
        """Subscribe to price updates for a specific token pair and DEX"""
        key = f"{token_pair}_{dex}"
        
        if key not in self.subscribers:
            self.subscribers[key] = []
        
        self.subscribers[key].append(callback)
        self.logger.info(f"Subscribed to {key}")
    
    def unsubscribe_from_pair(self, token_pair: str, dex: str, callback: Callable):
        """Unsubscribe from price updates"""
        key = f"{token_pair}_{dex}"
        
        if key in self.subscribers and callback in self.subscribers[key]:
            self.subscribers[key].remove(callback)
            self.logger.info(f"Unsubscribed from {key}")
    
    def get_latest_price(self, token_pair: str, dex: str) -> Optional[PriceUpdate]:
        """Get the latest price for a token pair and DEX"""
        key = f"{token_pair}_{dex}"
        return self.price_cache.get(key)
    
    def get_all_prices(self, token_pair: str) -> Dict[str, PriceUpdate]:
        """Get latest prices across all DEXes for a token pair"""
        prices = {}
        for key, update in self.price_cache.items():
            if update.token_pair == token_pair:
                prices[update.dex] = update
        return prices
    
    def is_connected(self) -> bool:
        """Check if connector is connected and receiving data"""
        return self.connected
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "connected": self.connected,
            "reconnect_attempts": self.reconnect_attempts,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "cached_pairs": len(self.price_cache),
            "subscribers": len(self.subscribers),
            "last_update": max(self.last_update.values()) if self.last_update else None
        }
