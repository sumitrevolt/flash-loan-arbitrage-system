#!/usr/bin/env python3
"""
Real Trading Data Collector for MCP System
Collects live market data for continuous learning and model refinement
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from dataclasses import dataclass
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_trading_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Structure for market data points"""
    timestamp: datetime
    symbol: str
    price: float
    volume: float
    exchange: str
    bid: float
    ask: float
    spread: float
    volatility: float
    arbitrage_opportunity: Optional[float] = None

class RealTradingDataCollector:
    """Collects real trading data from multiple sources"""
    
    def __init__(self):
        self.db_path = "real_trading_data.db"
        self.session = None
        self.data_sources = {
            'binance': 'https://api.binance.com/api/v3',
            'coinbase': 'https://api.exchange.coinbase.com',
            'kraken': 'https://api.kraken.com/0/public',
            'uniswap': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        }
        self.target_pairs = [
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
            'UNIUSDT', 'AAVEUSDT', 'SUSHIUSDT', 'COMPUSDT', 'MATICUSDT'
        ]
        self.collection_interval = 30  # seconds
        self.running = False
        
    async def initialize_database(self):
        """Initialize SQLite database for storing real trading data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    exchange TEXT NOT NULL,
                    bid REAL,
                    ask REAL,
                    spread REAL,
                    volatility REAL,
                    arbitrage_opportunity REAL,
                    raw_data TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    exchange_a TEXT NOT NULL,
                    exchange_b TEXT NOT NULL,
                    price_a REAL NOT NULL,
                    price_b REAL NOT NULL,
                    profit_percentage REAL NOT NULL,
                    volume_available REAL,
                    status TEXT DEFAULT 'detected'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start DATETIME NOT NULL,
                    session_end DATETIME,
                    total_opportunities INTEGER DEFAULT 0,
                    successful_trades INTEGER DEFAULT 0,
                    total_profit REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON market_data(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON market_data(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange ON market_data(exchange)')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def start_session(self):
        """Start HTTP session for API calls"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={'User-Agent': 'MCP-Trading-System/1.0'}
            )
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_binance_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Binance API"""
        try:
            # Get ticker data
            ticker_url = f"{self.data_sources['binance']}/ticker/24hr?symbol={symbol}"
            orderbook_url = f"{self.data_sources['binance']}/depth?symbol={symbol}&limit=5"
            
            async with self.session.get(ticker_url) as ticker_response:
                if ticker_response.status == 200:
                    ticker_data = await ticker_response.json()
                    
                    async with self.session.get(orderbook_url) as orderbook_response:
                        if orderbook_response.status == 200:
                            orderbook_data = await orderbook_response.json()
                            
                            return {
                                'exchange': 'binance',
                                'symbol': symbol,
                                'price': float(ticker_data['lastPrice']),
                                'volume': float(ticker_data['volume']),
                                'bid': float(orderbook_data['bids'][0][0]) if orderbook_data['bids'] else 0,
                                'ask': float(orderbook_data['asks'][0][0]) if orderbook_data['asks'] else 0,
                                'volatility': float(ticker_data['priceChangePercent']) / 100,
                                'raw_data': json.dumps({
                                    'ticker': ticker_data,
                                    'orderbook': orderbook_data
                                })
                            }
        except Exception as e:
            logger.warning(f"Failed to fetch Binance data for {symbol}: {e}")
            return None
    
    async def fetch_coinbase_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Coinbase API"""
        try:
            # Convert symbol format (BTCUSDT -> BTC-USD)
            if symbol.endswith('USDT'):
                cb_symbol = f"{symbol[:-4]}-USD"
            else:
                return None
                
            ticker_url = f"{self.data_sources['coinbase']}/products/{cb_symbol}/ticker"
            
            async with self.session.get(ticker_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'exchange': 'coinbase',
                        'symbol': symbol,
                        'price': float(data['price']),
                        'volume': float(data['volume']),
                        'bid': float(data['bid']),
                        'ask': float(data['ask']),
                        'volatility': 0.0,  # Calculate separately if needed
                        'raw_data': json.dumps(data)
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch Coinbase data for {symbol}: {e}")
            return None
    
    async def detect_arbitrage_opportunities(self, market_data: List[Dict]) -> List[Dict]:
        """Detect arbitrage opportunities across exchanges"""
        opportunities = []
        
        # Group by symbol
        symbol_data = {}
        for data in market_data:
            symbol = data['symbol']
            if symbol not in symbol_data:
                symbol_data[symbol] = []
            symbol_data[symbol].append(data)
        
        # Find arbitrage opportunities
        for symbol, data_points in symbol_data.items():
            if len(data_points) < 2:
                continue
                
            # Sort by price
            data_points.sort(key=lambda x: x['price'])
            
            lowest = data_points[0]
            highest = data_points[-1]
            
            if lowest['exchange'] != highest['exchange']:
                profit_percentage = ((highest['price'] - lowest['price']) / lowest['price']) * 100
                
                # Only consider opportunities with > 0.1% profit potential
                if profit_percentage > 0.1:
                    opportunities.append({
                        'symbol': symbol,
                        'exchange_a': lowest['exchange'],
                        'exchange_b': highest['exchange'],
                        'price_a': lowest['price'],
                        'price_b': highest['price'],
                        'profit_percentage': profit_percentage,
                        'volume_available': min(lowest.get('volume', 0), highest.get('volume', 0))
                    })
        
        return opportunities
    
    async def store_market_data(self, market_data_list: List[Dict]):
        """Store market data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for data in market_data_list:
                spread = data.get('ask', 0) - data.get('bid', 0)
                
                cursor.execute('''
                    INSERT INTO market_data 
                    (timestamp, symbol, price, volume, exchange, bid, ask, spread, volatility, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    data['symbol'],
                    data['price'],
                    data['volume'],
                    data['exchange'],
                    data.get('bid', 0),
                    data.get('ask', 0),
                    spread,
                    data.get('volatility', 0),
                    data.get('raw_data', '{}')
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"Stored {len(market_data_list)} market data points")
            
        except Exception as e:
            logger.error(f"Failed to store market data: {e}")
    
    async def store_arbitrage_opportunities(self, opportunities: List[Dict]):
        """Store arbitrage opportunities in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for opp in opportunities:
                cursor.execute('''
                    INSERT INTO arbitrage_opportunities 
                    (timestamp, symbol, exchange_a, exchange_b, price_a, price_b, profit_percentage, volume_available)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    opp['symbol'],
                    opp['exchange_a'],
                    opp['exchange_b'],
                    opp['price_a'],
                    opp['price_b'],
                    opp['profit_percentage'],
                    opp.get('volume_available', 0)
                ))
            
            conn.commit()
            conn.close()
            
            if opportunities:
                logger.info(f"Detected and stored {len(opportunities)} arbitrage opportunities")
                for opp in opportunities:
                    logger.info(f"  {opp['symbol']}: {opp['profit_percentage']:.2f}% profit "
                              f"({opp['exchange_a']} -> {opp['exchange_b']})")
            
        except Exception as e:
            logger.error(f"Failed to store arbitrage opportunities: {e}")
    
    async def collect_data_cycle(self):
        """Single data collection cycle"""
        logger.info("Starting data collection cycle...")
        
        all_market_data = []
        
        # Collect data from all exchanges for all symbols
        tasks = []
        for symbol in self.target_pairs:
            tasks.append(self.fetch_binance_data(symbol))
            tasks.append(self.fetch_coinbase_data(symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if result and not isinstance(result, Exception):
                all_market_data.append(result)
        
        if all_market_data:
            # Store market data
            await self.store_market_data(all_market_data)
            
            # Detect and store arbitrage opportunities
            opportunities = await self.detect_arbitrage_opportunities(all_market_data)
            if opportunities:
                await self.store_arbitrage_opportunities(opportunities)
            
            logger.info(f"Collection cycle completed: {len(all_market_data)} data points, "
                       f"{len(opportunities)} opportunities")
        else:
            logger.warning("No market data collected in this cycle")
    
    async def start_collection(self):
        """Start continuous data collection"""
        logger.info("Starting real trading data collection...")
        
        await self.initialize_database()
        await self.start_session()
        
        self.running = True
        
        try:
            while self.running:
                await self.collect_data_cycle()
                await asyncio.sleep(self.collection_interval)
                
        except KeyboardInterrupt:
            logger.info("Collection stopped by user")
        except Exception as e:
            logger.error(f"Collection error: {e}")
        finally:
            await self.close_session()
            self.running = False
    
    def stop_collection(self):
        """Stop data collection"""
        self.running = False
        logger.info("Stopping data collection...")
    
    def get_recent_data(self, hours: int = 24) -> pd.DataFrame:
        """Get recent market data for analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT * FROM market_data 
                WHERE timestamp >= datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            '''.format(hours)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent data: {e}")
            return pd.DataFrame()
    
    def get_arbitrage_summary(self, hours: int = 24) -> Dict:
        """Get arbitrage opportunity summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_opportunities,
                    AVG(profit_percentage) as avg_profit,
                    MAX(profit_percentage) as max_profit,
                    SUM(volume_available) as total_volume
                FROM arbitrage_opportunities 
                WHERE timestamp >= datetime('now', '-{} hours')
            '''.format(hours))
            
            result = cursor.fetchone()
            conn.close()
            
            return {
                'total_opportunities': result[0] if result[0] else 0,
                'average_profit_percentage': result[1] if result[1] else 0,
                'maximum_profit_percentage': result[2] if result[2] else 0,
                'total_volume_available': result[3] if result[3] else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get arbitrage summary: {e}")
            return {}

async def main():
    """Main function to run the data collector"""
    collector = RealTradingDataCollector()
    
    try:
        await collector.start_collection()
    except KeyboardInterrupt:
        logger.info("Data collection stopped")
    finally:
        await collector.close_session()

if __name__ == "__main__":
    asyncio.run(main())
