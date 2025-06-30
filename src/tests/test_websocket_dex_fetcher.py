#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for WebSocket DEX Data Fetcher
This script tests the functionality of the WebSocketDEXFetcher class.
"""

import asyncio
import json
import os
import sys

from unittest.mock import AsyncMock, patch
import unittest

# Ensure the parent directory is in the path to import the fetcher
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from arbitrage.websocket_dex_data_fetcher import WebSocketDEXFetcher, latest_prices

class TestWebSocketDEXFetcher(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.dex_name = "uniswap"
        self.url = "wss://test.uniswap.org"
        self.subscription_payload = {
            "type": "subscribe",
            "channel": "price_feed",
            "pairs": ["ETH/USDT"]

        self.fetcher = WebSocketDEXFetcher(self.dex_name, self.url, self.subscription_payload)
        # Reset global state before each test
        latest_prices[self.dex_name] = {}

    @patch('websockets.connect')
    async def test_connect_success(self, mock_connect):
        """Test successful WebSocket connection."""
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        await self.fetcher.connect()
        mock_connect.assert_called_once_with(self.url)
        self.assertTrue(self.fetcher.is_running)
        mock_ws.send.assert_called_once_with(json.dumps(self.subscription_payload))

    @patch('websockets.connect')
    async def test_connect_failure(self, mock_connect):
        """Test WebSocket connection failure."""
        mock_connect.side_effect = Exception("Connection failed")
        await self.fetcher.connect()
        mock_connect.assert_called_once_with(self.url)
        self.assertFalse(self.fetcher.is_running)

    def test_process_price_data_valid(self):
        """Test processing valid price data."""
        test_data = {"pair": "ETH/USDT", "price": 2000.50}
        self.fetcher.process_price_data(test_data)
        self.assertIn("ETH/USDT", latest_prices[self.dex_name])
        self.assertEqual(latest_prices[self.dex_name]["ETH/USDT"], 2000.50)

    def test_process_price_data_invalid(self):
        """Test processing invalid price data."""
        test_data = {"invalid_key": "value"}
        self.fetcher.process_price_data(test_data)
        self.assertEqual(latest_prices[self.dex_name], {})

    @patch('websockets.connect')
    async def test_listen_reconnect_on_close(self, mock_connect):
        """Test reconnection logic when WebSocket connection closes."""
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        mock_ws.recv.side_effect = [json.dumps({"pair": "ETH/USDT", "price": 2000.50}), 
                                    websockets.exceptions.ConnectionClosed(None, None)
        
        # Run listen in a controlled async environment
        await self.fetcher.connect()
        listen_task = asyncio.create_task(self.fetcher.listen())
        await asyncio.sleep(0.1)  # Allow some iterations
        listen_task.cancel()
        
        self.assertIn("ETH/USDT", latest_prices[self.dex_name])
        self.assertEqual(latest_prices[self.dex_name]["ETH/USDT"], 2000.50)
        self.assertFalse(self.fetcher.is_running)  # Should trigger reconnect attempt

if __name__ == '__main__':
    unittest.main()
