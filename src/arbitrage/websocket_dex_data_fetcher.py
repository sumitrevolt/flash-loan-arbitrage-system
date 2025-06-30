#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket-based Real-time DEX Data Fetcher for Flash Loan Arbitrage Bot
This script establishes WebSocket connections to DEX APIs for continuous price data streaming.
"""

from typing import Dict, Any, Optional
import asyncio
import json
import logging
import sys

import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)


logger = logging.getLogger("WebSocketDEXFetcher")

# Configuration - Update with actual DEX WebSocket endpoints and subscription details
# Note: Uniswap and Sushiswap may not provide public WebSocket APIs for price feeds.
# You may need to use alternative data providers like The Graph, Alchemy, or Infura WebSocket APIs
# or other DEX-specific WebSocket services. Configure the URLs accordingly.
DEX_WEBSOCKET_URLS = {
    "uniswap": "wss://your-uniswap-data-provider.com/websocket",  # Configure with actual data provider WebSocket URL for Uniswap data
    "sushiswap": "wss://your-sushiswap-data-provider.com/websocket"  # Configure with actual data provider WebSocket URL for Sushiswap data


SUBSCRIPTION_PAYLOADS = {
    "uniswap": {
        "type": "subscribe",
        "channel": "price_feed",
        "pairs": ["ETH/USDT", "WBTC/USDT"]  # Example trading pairs
    },
    "sushiswap": {
        "type": "subscribe",
        "channel": "price_feed",
        "pairs": ["ETH/USDT", "WBTC/USDT"]



# Global state to store latest price data
latest_prices: Dict[str, Dict[str, float]] = {
    "uniswap": {},
    "sushiswap": {}


class WebSocketDEXFetcher:
    def __init__(self, dex_name: str, url: str, subscription_payload: Dict[str, Any]):
        self.dex_name = dex_name
        self.url = url
        self.subscription_payload = subscription_payload
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False

    async def connect(self) -> None:
        """Establish WebSocket connection to DEX API."""
        try:
            self.websocket = await websockets.connect(self.url)
            logger.info(f"Connected to {self.dex_name} WebSocket at {self.url}")
            await self.subscribe()
            self.is_running = True
        except Exception as e:
            logger.error(f"Failed to connect to {self.dex_name} WebSocket: {e}")
            self.is_running = False

    async def subscribe(self) -> None:
        """Send subscription payload to receive price feed data."""
        if self.websocket:
            await self.websocket.send(json.dumps(self.subscription_payload))
            logger.info(f"Subscribed to {self.dex_name} price feed with payload: {self.subscription_payload}")

    async def listen(self) -> None:
        """Listen for incoming price data and update global state."""
        if not self.websocket or not self.is_running:
            await self.connect()
        
        while self.is_running:
            try:
                data = await self.websocket.recv()
                price_data = json.loads(data)
                self.process_price_data(price_data)
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"{self.dex_name} WebSocket connection closed. Reconnecting...")
                self.is_running = False
                await self.connect()
            except Exception as e:
                logger.error(f"Error in {self.dex_name} WebSocket listener: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    def process_price_data(self, data: Dict[str, Any]) -> None:
        """Process received price data and update global state."""
        try:
            # Assuming data format: {"pair": "ETH/USDT", "price": 1234.56, ...}
            pair = data.get("pair")
            price = data.get("price")
            if pair and price:
                latest_prices[self.dex_name][pair] = float(price)
                logger.info(f"Updated {self.dex_name} price for {pair}: {price}")
        except Exception as e:
            logger.error(f"Error processing {self.dex_name} price data: {e}")

    async def close(self) -> None:
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            logger.info(f"Closed {self.dex_name} WebSocket connection")
            self.is_running = False

async def run_fetchers() -> None:
    """Run WebSocket fetchers for all configured DEXs."""
    fetchers = [
        WebSocketDEXFetcher(dex_name, url, SUBSCRIPTION_PAYLOADS[dex_name])
        for dex_name, url in DEX_WEBSOCKET_URLS.items()

    
    # Connect all fetchers
    for fetcher in fetchers:
        await fetcher.connect()
    
    # Start listening tasks
    tasks = [asyncio.create_task(fetcher.listen()) for fetcher in fetchers]
    
    # Keep running until interrupted
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Shutting down WebSocket fetchers...")
        for fetcher in fetchers:
            await fetcher.close()
        raise

def get_latest_prices() -> Dict[str, Dict[str, float]]:
    """Return the latest price data from all DEXs."""
    return latest_prices

if __name__ == "__main__":
    logger.info("Starting WebSocket DEX Data Fetcher...")
    try:
        asyncio.run(run_fetchers())
    except KeyboardInterrupt:
        logger.info("WebSocket DEX Data Fetcher stopped by user.")
    except Exception as e:
        logger.error(f"WebSocket DEX Data Fetcher terminated due to error: {e}")
