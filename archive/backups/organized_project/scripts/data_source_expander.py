#!/usr/bin/env python3
"""
Data Source Expander for MCP System
Integrates additional data feeds and sources for enhanced training
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
import websockets
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import os
import yfinance as yf  # pip install yfinance
from web3 import Web3  # pip install web3
import ccxt  # pip install ccxt
import feedparser  # pip install feedparser
import requests
from bs4 import BeautifulSoup  # pip install beautifulsoup4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_source_expander.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Data source configuration"""
    source_id: str
    source_type: str  # 'api', 'websocket', 'rss', 'web3', 'traditional'
    endpoint: str
    update_frequency: int  # seconds
    data_format: str
    enabled: bool = True
    last_update: Optional[datetime] = None
    error_count: int = 0

class DataSourceExpander:
    """Expands available data sources for MCP training"""
    
    def __init__(self):
        self.db_path = "expanded_data_sources.db"
        self.session = None
        
        # Traditional financial data sources
        self.traditional_symbols = [
            'SPY', 'QQQ', 'IWM', 'GLD', 'SLV', 'TLT', 'VIX',
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA'
        ]
        
        # DeFi/Crypto data sources
        self.defi_sources = {
            'uniswap_v3': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
            'aave': 'https://api.thegraph.com/subgraphs/name/aave/protocol-v2',
            'compound': 'https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2',
            'dydx': 'https://api.dydx.exchange/v3',
            'paraswap': 'https://apiv5.paraswap.io',
            'defipulse': 'https://data-api.defipulse.com/api/v1'
        }
        
        # News and sentiment sources
        self.news_sources = {
            'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'cointelegraph': 'https://cointelegraph.com/rss',
            'bitcoinnews': 'https://news.bitcoin.com/feed/',
            'theblock': 'https://www.theblockcrypto.com/rss.xml',
            'decrypt': 'https://decrypt.co/feed'
        }
        
        # Social media and sentiment
        self.sentiment_sources = {
            'reddit_api': 'https://oauth.reddit.com',
            'twitter_api': 'https://api.twitter.com/2',
            'fear_greed_index': 'https://api.alternative.me/fng/',
            'crypto_fear_greed': 'https://api.alternative.me/fng/?limit=100'
        }
        
        # On-chain analytics
        self.onchain_sources = {
            'etherscan': 'https://api.etherscan.io/api',
            'bscscan': 'https://api.bscscan.com/api',
            'polygonscan': 'https://api.polygonscan.com/api',
            'dune_analytics': 'https://api.dune.xyz/api/v1',
            'nansen': 'https://api.nansen.ai/v1',
            'messari': 'https://data.messari.io/api/v1'
        }
        
        # Exchange-specific APIs
        self.exchange_apis = {
            'binance': ccxt.binance(),
            'coinbase': ccxt.coinbasepro(),
            'kraken': ccxt.kraken(),
            'huobi': ccxt.huobi(),
            'okex': ccxt.okx(),
            'bybit': ccxt.bybit()
        }
        
        # Macro economic data
        self.macro_sources = {
            'fred': 'https://api.stlouisfed.org/fred',  # Federal Reserve Economic Data
            'alpha_vantage': 'https://www.alphavantage.co/query',
            'quandl': 'https://www.quandl.com/api/v3',
            'world_bank': 'https://api.worldbank.org/v2'
        }
        
        self.running = False
        self.data_sources = []
    
    async def initialize_database(self):
        """Initialize expanded data sources database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Data sources registry
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT UNIQUE NOT NULL,
                    source_type TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    update_frequency INTEGER NOT NULL,
                    data_format TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    last_update DATETIME,
                    error_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Traditional financial data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traditional_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL,
                    change_percent REAL,
                    market_cap REAL,
                    pe_ratio REAL,
                    volatility REAL,
                    raw_data TEXT
                )
            ''')
            
            # DeFi protocol data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS defi_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    protocol TEXT NOT NULL,
                    tvl REAL,
                    volume_24h REAL,
                    fees_24h REAL,
                    yield_rate REAL,
                    token_price REAL,
                    utilization_rate REAL,
                    raw_data TEXT
                )
            ''')
            
            # News and sentiment data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    sentiment_score REAL,
                    category TEXT,
                    keywords TEXT,
                    url TEXT,
                    raw_data TEXT
                )
            ''')
            
            # Social media sentiment
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    platform TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sentiment_score REAL,
                    engagement_score REAL,
                    author_influence REAL,
                    keywords TEXT,
                    raw_data TEXT
                )
            ''')
            
            # On-chain metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS onchain_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    blockchain TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    transaction_count INTEGER,
                    active_addresses INTEGER,
                    gas_price REAL,
                    network_hashrate REAL,
                    raw_data TEXT
                )
            ''')
            
            # Macro economic indicators
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS macro_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    indicator_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    country TEXT,
                    frequency TEXT,
                    source TEXT,
                    raw_data TEXT
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_traditional_symbol ON traditional_data(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_traditional_timestamp ON traditional_data(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_defi_protocol ON defi_data(protocol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news_sentiment(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_social_platform ON social_sentiment(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_onchain_blockchain ON onchain_metrics(blockchain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_macro_indicator ON macro_indicators(indicator_name)')
            
            conn.commit()
            conn.close()
            logger.info("Expanded data sources database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def start_session(self):
        """Start HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'MCP-DataExpander/1.0'}
            )
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_traditional_data(self):
        """Fetch traditional financial market data"""
        logger.info("Fetching traditional financial data...")
        
        try:
            for symbol in self.traditional_symbols:
                try:
                    # Use yfinance to get data
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    hist = ticker.history(period="1d", interval="1m")
                    
                    if not hist.empty:
                        latest = hist.iloc[-1]
                        
                        # Calculate volatility
                        returns = hist['Close'].pct_change().dropna()
                        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
                        
                        # Store data
                        await self.store_traditional_data({
                            'symbol': symbol,
                            'price': float(latest['Close']),
                            'volume': float(latest['Volume']),
                            'change_percent': ((latest['Close'] - latest['Open']) / latest['Open']) * 100,
                            'market_cap': info.get('marketCap', 0),
                            'pe_ratio': info.get('forwardPE', 0),
                            'volatility': volatility,
                            'raw_data': json.dumps({
                                'info': {k: v for k, v in info.items() if isinstance(v, (int, float, str, bool))},
                                'latest_price': {
                                    'open': float(latest['Open']),
                                    'high': float(latest['High']),
                                    'low': float(latest['Low']),
                                    'close': float(latest['Close']),
                                    'volume': float(latest['Volume'])
                                }
                            })
                        })
                        
                        logger.info(f"Stored traditional data for {symbol}: ${latest['Close']:.2f}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch traditional data for {symbol}: {e}")
                    continue
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Traditional data collection failed: {e}")
    
    async def fetch_defi_data(self):
        """Fetch DeFi protocol data"""
        logger.info("Fetching DeFi protocol data...")
        
        try:
            # Fetch from DeFiPulse (example)
            url = "https://data-api.defipulse.com/api/v1/defipulse/api/MarketData"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for protocol in data:
                        await self.store_defi_data({
                            'protocol': protocol.get('name', 'unknown'),
                            'tvl': protocol.get('value', {}).get('tvl', {}).get('USD', 0),
                            'volume_24h': protocol.get('value', {}).get('volume_24h', 0),
                            'fees_24h': protocol.get('value', {}).get('fees_24h', 0),
                            'yield_rate': protocol.get('value', {}).get('yield', 0),
                            'token_price': protocol.get('value', {}).get('token_price', 0),
                            'utilization_rate': protocol.get('value', {}).get('utilization', 0),
                            'raw_data': json.dumps(protocol)
                        })
                    
                    logger.info(f"Stored DeFi data for {len(data)} protocols")
                
        except Exception as e:
            logger.error(f"DeFi data collection failed: {e}")
    
    async def fetch_news_sentiment(self):
        """Fetch news and calculate sentiment scores"""
        logger.info("Fetching news and sentiment data...")
        
        try:
            for source_name, rss_url in self.news_sources.items():
                try:
                    # Parse RSS feed
                    feed = feedparser.parse(rss_url)
                    
                    for entry in feed.entries[:10]:  # Limit to recent 10 articles
                        # Simple sentiment analysis (in practice, use proper NLP)
                        content = entry.get('summary', '') + ' ' + entry.get('title', '')
                        sentiment_score = self.calculate_simple_sentiment(content)
                        
                        await self.store_news_sentiment({
                            'source': source_name,
                            'title': entry.get('title', ''),
                            'content': entry.get('summary', ''),
                            'sentiment_score': sentiment_score,
                            'category': self.categorize_news(entry.get('title', '')),
                            'keywords': self.extract_keywords(content),
                            'url': entry.get('link', ''),
                            'raw_data': json.dumps(dict(entry))
                        })
                    
                    logger.info(f"Stored news from {source_name}: {len(feed.entries)} articles")
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch news from {source_name}: {e}")
                    continue
                
                await asyncio.sleep(2)  # Rate limiting
                
        except Exception as e:
            logger.error(f"News sentiment collection failed: {e}")
    
    def calculate_simple_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (replace with proper NLP in production)"""
        positive_words = ['bullish', 'surge', 'moon', 'pump', 'gains', 'rally', 'breakout', 'positive', 'growth']
        negative_words = ['bearish', 'crash', 'dump', 'drop', 'fall', 'decline', 'negative', 'loss', 'bear']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def categorize_news(self, title: str) -> str:
        """Categorize news articles"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['bitcoin', 'btc']):
            return 'bitcoin'
        elif any(word in title_lower for word in ['ethereum', 'eth']):
            return 'ethereum'
        elif any(word in title_lower for word in ['defi', 'yield', 'liquidity']):
            return 'defi'
        elif any(word in title_lower for word in ['nft', 'token']):
            return 'nft'
        elif any(word in title_lower for word in ['regulation', 'sec', 'government']):
            return 'regulation'
        else:
            return 'general'
    
    def extract_keywords(self, text: str) -> str:
        """Extract keywords from text"""
        crypto_keywords = [
            'bitcoin', 'ethereum', 'defi', 'yield', 'liquidity', 'staking',
            'governance', 'dao', 'nft', 'metaverse', 'web3', 'blockchain'
        ]
        
        text_lower = text.lower()
        found_keywords = [keyword for keyword in crypto_keywords if keyword in text_lower]
        
        return ','.join(found_keywords)
    
    async def fetch_onchain_metrics(self):
        """Fetch on-chain metrics"""
        logger.info("Fetching on-chain metrics...")
        
        try:
            # Example: Ethereum gas prices and network stats
            etherscan_url = "https://api.etherscan.io/api"
            
            # Gas price
            params = {
                'module': 'gastracker',
                'action': 'gasoracle',
                'apikey': 'YourApiKeyToken'  # Replace with actual API key
            }
            
            async with self.session.get(etherscan_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['status'] == '1':
                        gas_data = data['result']
                        
                        await self.store_onchain_metrics({
                            'blockchain': 'ethereum',
                            'metric_name': 'gas_price_gwei',
                            'metric_value': float(gas_data['SafeGasPrice']),
                            'transaction_count': 0,  # Would fetch separately
                            'active_addresses': 0,   # Would fetch separately
                            'gas_price': float(gas_data['SafeGasPrice']),
                            'network_hashrate': 0,   # Would fetch separately
                            'raw_data': json.dumps(gas_data)
                        })
                        
                        logger.info(f"Stored Ethereum gas price: {gas_data['SafeGasPrice']} Gwei")
            
            # Add more on-chain metrics as needed
            # BSC, Polygon, etc.
            
        except Exception as e:
            logger.error(f"On-chain metrics collection failed: {e}")
    
    async def fetch_macro_indicators(self):
        """Fetch macro economic indicators"""
        logger.info("Fetching macro economic indicators...")
        
        try:
            # Example: Fear & Greed Index
            url = "https://api.alternative.me/fng/"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and data['data']:
                        fng_data = data['data'][0]
                        
                        await self.store_macro_indicator({
                            'indicator_name': 'crypto_fear_greed_index',
                            'value': float(fng_data['value']),
                            'country': 'global',
                            'frequency': 'daily',
                            'source': 'alternative.me',
                            'raw_data': json.dumps(fng_data)
                        })
                        
                        logger.info(f"Stored Fear & Greed Index: {fng_data['value']} ({fng_data['value_classification']})")
            
            # Add more macro indicators (VIX, DXY, etc.)
            
        except Exception as e:
            logger.error(f"Macro indicators collection failed: {e}")
    
    async def store_traditional_data(self, data: Dict):
        """Store traditional financial data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO traditional_data 
                (symbol, price, volume, change_percent, market_cap, pe_ratio, volatility, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['symbol'], data['price'], data['volume'], data['change_percent'],
                data['market_cap'], data['pe_ratio'], data['volatility'], data['raw_data']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store traditional data: {e}")
    
    async def store_defi_data(self, data: Dict):
        """Store DeFi protocol data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO defi_data 
                (protocol, tvl, volume_24h, fees_24h, yield_rate, token_price, utilization_rate, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['protocol'], data['tvl'], data['volume_24h'], data['fees_24h'],
                data['yield_rate'], data['token_price'], data['utilization_rate'], data['raw_data']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store DeFi data: {e}")
    
    async def store_news_sentiment(self, data: Dict):
        """Store news sentiment data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO news_sentiment 
                (source, title, content, sentiment_score, category, keywords, url, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['source'], data['title'], data['content'], data['sentiment_score'],
                data['category'], data['keywords'], data['url'], data['raw_data']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store news sentiment: {e}")
    
    async def store_onchain_metrics(self, data: Dict):
        """Store on-chain metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO onchain_metrics 
                (blockchain, metric_name, metric_value, transaction_count, active_addresses, 
                 gas_price, network_hashrate, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['blockchain'], data['metric_name'], data['metric_value'],
                data['transaction_count'], data['active_addresses'],
                data['gas_price'], data['network_hashrate'], data['raw_data']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store on-chain metrics: {e}")
    
    async def store_macro_indicator(self, data: Dict):
        """Store macro economic indicator"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO macro_indicators 
                (indicator_name, value, country, frequency, source, raw_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['indicator_name'], data['value'], data['country'],
                data['frequency'], data['source'], data['raw_data']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store macro indicator: {e}")
    
    async def data_collection_cycle(self):
        """Single data collection cycle"""
        logger.info("Starting expanded data collection cycle...")
        
        try:
            # Collect from all sources
            await asyncio.gather(
                self.fetch_traditional_data(),
                self.fetch_defi_data(),
                self.fetch_news_sentiment(),
                self.fetch_onchain_metrics(),
                self.fetch_macro_indicators(),
                return_exceptions=True
            )
            
            logger.info("Expanded data collection cycle completed")
            
        except Exception as e:
            logger.error(f"Data collection cycle failed: {e}")
    
    async def start_data_expansion(self):
        """Start expanded data collection"""
        logger.info("Starting expanded data collection system...")
        
        await self.initialize_database()
        await self.start_session()
        
        self.running = True
        
        try:
            while self.running:
                await self.data_collection_cycle()
                
                # Wait 15 minutes between cycles
                await asyncio.sleep(900)
                
        except KeyboardInterrupt:
            logger.info("Data expansion stopped by user")
        except Exception as e:
            logger.error(f"Data expansion error: {e}")
        finally:
            await self.close_session()
            self.running = False
    
    def stop_expansion(self):
        """Stop data expansion"""
        self.running = False
        logger.info("Stopping data expansion...")
    
    async def get_expanded_data_summary(self) -> Dict:
        """Get summary of expanded data collection"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Count data points from each source
            traditional_count = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM traditional_data WHERE timestamp >= datetime('now', '-24 hours')",
                conn
            ).iloc[0]['count']
            
            defi_count = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM defi_data WHERE timestamp >= datetime('now', '-24 hours')",
                conn
            ).iloc[0]['count']
            
            news_count = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM news_sentiment WHERE timestamp >= datetime('now', '-24 hours')",
                conn
            ).iloc[0]['count']
            
            onchain_count = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM onchain_metrics WHERE timestamp >= datetime('now', '-24 hours')",
                conn
            ).iloc[0]['count']
            
            macro_count = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM macro_indicators WHERE timestamp >= datetime('now', '-24 hours')",
                conn
            ).iloc[0]['count']
            
            # Get sentiment summary
            sentiment_summary = pd.read_sql_query('''
                SELECT AVG(sentiment_score) as avg_sentiment, COUNT(*) as total_articles
                FROM news_sentiment 
                WHERE timestamp >= datetime('now', '-24 hours')
            ''', conn)
            
            conn.close()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'traditional_data_points': traditional_count,
                'defi_data_points': defi_count,
                'news_articles': news_count,
                'onchain_metrics': onchain_count,
                'macro_indicators': macro_count,
                'total_data_points': traditional_count + defi_count + news_count + onchain_count + macro_count,
                'average_sentiment': float(sentiment_summary.iloc[0]['avg_sentiment']) if sentiment_summary.iloc[0]['avg_sentiment'] else 0.0,
                'total_news_articles': int(sentiment_summary.iloc[0]['total_articles'])
            }
            
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return {}

async def main():
    """Main function"""
    expander = DataSourceExpander()
    
    try:
        await expander.start_data_expansion()
    except KeyboardInterrupt:
        logger.info("Data source expander stopped")
    finally:
        expander.stop_expansion()

if __name__ == "__main__":
    asyncio.run(main())
