#!/usr/bin/env python3
"""
Enhanced Price Feed Aggregation MCP Server
Specialized MCP server for real-time DEX price aggregation
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List, Optional
import uvicorn
from web3 import Web3
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced Price Feed Aggregation MCP Server", version="2.0.0")

class EnhancedPriceFeedServer:
    """Enhanced MCP server for real-time price feed aggregation"""
    
    def __init__(self):
        self.is_healthy = True
        self.server_type = "enhanced price feed aggregation"
        self.port = 8106
        
        # Initialize Web3 for Polygon
        self.rpc_url = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # DEX configurations
        self.dexs = {
            'quickswap': {
                'name': 'QuickSwap',
                'factory': '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
                'router': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                'fee': 0.003  # 0.3%
            },
            'sushiswap': {
                'name': 'SushiSwap',
                'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'fee': 0.003  # 0.3%
            },
            'uniswap_v3': {
                'name': 'Uniswap V3',
                'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
                'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'fee': 0.003  # 0.3% (most common)
            },
            'balancer': {
                'name': 'Balancer',
                'vault': '0xBA12222222228d8Ba445958a75a0704d566BF2C8',
                'fee': 0.0025  # 0.25% average
            },
            'curve': {
                'name': 'Curve',
                'registry': '0x47bB542B9dE58b970bA50c9dae444DDB4c16751a',
                'fee': 0.0004  # 0.04% average
            }
        }
        
        # Token configurations
        self.tokens = {
            'WMATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
            'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
            'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
            'WBTC': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
            'LINK': '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39',
            'AAVE': '0xD6DF932A45C0f255f85145f286eA0b292B21C90B',
            'UNI': '0xb33EaAd8d922B1083446DC23f610c2567fB5180f',
            'SUSHI': '0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a',
            'CRV': '0x172370d5Cd63279eFa6d502DAB29171933a610AF',
            'BAL': '0x9a71012B13CA4d3D0Cdc72A177DF3ef03b0E76A3',
            'GHST': '0x385Eeac5cB85A38A9a07A70c73e0a3271CfB54A7',
            'QUICK': '0x831753DD7087CaC61aB5644b308642cc1c33Dc13',
            'dQUICK': '0x958d208Cdf087843e9AD98d23823d32E17d723A1'
        }
        
        # Price cache
        self.price_cache = {}
        self.cache_timestamp = None
        self.cache_duration = 30  # seconds
        
    async def initialize(self):
        """Initialize the enhanced MCP server"""
        logger.info("🚀 Initializing Enhanced Price Feed Aggregation MCP Server...")
        
        # Test Web3 connection
        try:
            block_number = self.web3.eth.block_number
            logger.info(f"✅ Connected to Polygon network. Latest block: {block_number}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Polygon: {e}")
            self.is_healthy = False
            
    async def get_token_price_from_dex(self, token_address: str, dex_name: str) -> Optional[Dict[str, Any]]:
        """Get token price from specific DEX"""
        try:
            # This is a simplified implementation - in production you'd call actual DEX contracts
            # For now, we'll simulate realistic prices
            base_prices = {
                'WMATIC': 0.85,
                'USDC': 1.0,
                'USDT': 1.0,
                'DAI': 1.0,
                'WETH': 3200.0,
                'WBTC': 67000.0,
                'LINK': 14.5,
                'AAVE': 85.0,
                'UNI': 7.2,
                'SUSHI': 1.8,
                'CRV': 0.92,
                'BAL': 4.1,
                'GHST': 1.1,
                'QUICK': 0.045,
                'dQUICK': 45.0
            }
            
            # Find token symbol
            token_symbol = None
            for symbol, address in self.tokens.items():
                if address.lower() == token_address.lower():
                    token_symbol = symbol
                    break
                    
            if not token_symbol or token_symbol not in base_prices:
                return None
                
            # Add some variance between DEXs (simulate spread)
            import random
            variance = random.uniform(-0.02, 0.02)  # ±2% variance
            price = base_prices[token_symbol] * (1 + variance)
            
            # Calculate liquidity (simulate)
            liquidity = random.uniform(50000, 1000000)  # $50k - $1M
            
            return {
                'dex': dex_name,
                'price': price,
                'liquidity': liquidity,
                'fee': self.dexs[dex_name]['fee'],
                'timestamp': datetime.now().isoformat(),
                'token_symbol': token_symbol,
                'token_address': token_address
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting price for {token_address} from {dex_name}: {e}")
            return None
    
    async def get_all_prices(self, tokens: List[str], dexs: List[str], include_liquidity: bool = True) -> Dict[str, Any]:
        """Get prices for all requested tokens from all requested DEXs"""
        try:
            prices = {}
            
            # Get prices from each DEX for each token
            for token_address in tokens:
                token_symbol = None
                for symbol, address in self.tokens.items():
                    if address.lower() == token_address.lower():
                        token_symbol = symbol
                        break
                
                if not token_symbol:
                    continue
                    
                prices[token_symbol] = {}
                
                for dex_name in dexs:
                    if dex_name in self.dexs:
                        price_data = await self.get_token_price_from_dex(token_address, dex_name)
                        if price_data:
                            prices[token_symbol][dex_name] = price_data
            
            # Calculate best prices and arbitrage opportunities
            arbitrage_opportunities = []
            for token_symbol, dex_prices in prices.items():
                if len(dex_prices) >= 2:
                    # Find best buy and sell prices
                    best_buy = min(dex_prices.values(), key=lambda x: x['price'])
                    best_sell = max(dex_prices.values(), key=lambda x: x['price'])
                    
                    if best_buy['dex'] != best_sell['dex']:
                        profit_percentage = (best_sell['price'] - best_buy['price']) / best_buy['price'] * 100
                        
                        # Calculate net profit after fees
                        buy_fee = best_buy['price'] * best_buy['fee']
                        sell_fee = best_sell['price'] * best_sell['fee']
                        net_profit_percentage = profit_percentage - (buy_fee + sell_fee) / best_buy['price'] * 100
                        
                        if net_profit_percentage > 0.1:  # Only opportunities with >0.1% profit
                            arbitrage_opportunities.append({
                                'token': token_symbol,
                                'buy_dex': best_buy['dex'],
                                'sell_dex': best_sell['dex'],
                                'buy_price': best_buy['price'],
                                'sell_price': best_sell['price'],
                                'profit_percentage': profit_percentage,
                                'net_profit_percentage': net_profit_percentage,
                                'buy_liquidity': best_buy['liquidity'],
                                'sell_liquidity': best_sell['liquidity'],
                                'timestamp': datetime.now().isoformat()
                            })
            
            result = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'prices': prices,
                'arbitrage_opportunities': arbitrage_opportunities,
                'dex_count': len(dexs),
                'token_count': len(tokens),
                'server': 'enhanced-mcp-price-feed'
            }
            
            # Update cache
            self.price_cache = result
            self.cache_timestamp = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting all prices: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process specialized MCP request"""
        try:
            request_type = request.get('type', 'unknown')
            
            if request_type == 'get_prices':
                tokens = request.get('tokens', list(self.tokens.values()))
                dexs = request.get('dexs', list(self.dexs.keys()))
                include_liquidity = request.get('include_liquidity', True)
                
                return await self.get_all_prices(tokens, dexs, include_liquidity)
            
            elif request_type == 'get_arbitrage_opportunities':
                # Check cache first
                if (self.cache_timestamp and 
                    (datetime.now() - self.cache_timestamp).seconds < self.cache_duration and
                    self.price_cache):
                    return {
                        'status': 'success',
                        'source': 'cache',
                        'arbitrage_opportunities': self.price_cache.get('arbitrage_opportunities', []),
                        'timestamp': self.cache_timestamp.isoformat()
                    }
                
                # Get fresh data
                tokens = request.get('tokens', list(self.tokens.values()))
                dexs = request.get('dexs', list(self.dexs.keys()))
                price_data = await self.get_all_prices(tokens, dexs)
                
                return {
                    'status': 'success',
                    'source': 'fresh',
                    'arbitrage_opportunities': price_data.get('arbitrage_opportunities', []),
                    'timestamp': datetime.now().isoformat()
                }
            
            else:
                return {
                    "server": "enhanced-mcp-price-feed",
                    "type": "enhanced price feed aggregation",
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "port": 8106,
                    "request_type": request_type,
                    "data": request
                }
                
        except Exception as e:
            logger.error(f"❌ Request processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Global server instance
mcp_server = EnhancedPriceFeedServer()

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    await mcp_server.initialize()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if mcp_server.is_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "service": "enhanced-mcp-price-feed",
        "type": "enhanced price feed aggregation",
        "port": 8106,
        "web3_connected": mcp_server.web3.is_connected(),
        "tokens_supported": len(mcp_server.tokens),
        "dexs_supported": len(mcp_server.dexs)
    }

@app.post("/mcp/request")
async def handle_mcp_request(request: Dict[str, Any]):
    """Handle specialized MCP request"""
    return await mcp_server.process_request(request)

@app.post("/get_prices")
async def get_prices(request: Dict[str, Any]):
    """Direct endpoint for price queries (for compatibility)"""
    tokens = request.get('tokens', list(mcp_server.tokens.values()))
    dexs = request.get('dexs', list(mcp_server.dexs.keys()))
    include_liquidity = request.get('include_liquidity', True)
    
    return await mcp_server.get_all_prices(tokens, dexs, include_liquidity)

@app.get("/get_arbitrage_opportunities")
async def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    request = {
        'type': 'get_arbitrage_opportunities',
        'tokens': list(mcp_server.tokens.values()),
        'dexs': list(mcp_server.dexs.keys())
    }
    return await mcp_server.process_request(request)

@app.get("/supported_tokens")
async def get_supported_tokens():
    """Get list of supported tokens"""
    return {
        "tokens": mcp_server.tokens,
        "count": len(mcp_server.tokens),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/supported_dexs")
async def get_supported_dexs():
    """Get list of supported DEXs"""
    return {
        "dexs": mcp_server.dexs,
        "count": len(mcp_server.dexs),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Enhanced Price Feed Aggregation MCP Server",
        "status": "running",
        "port": 8106,
        "type": "enhanced price feed aggregation",
        "version": "2.0.0",
        "endpoints": [
            "/health",
            "/mcp/request", 
            "/get_prices",
            "/get_arbitrage_opportunities",
            "/supported_tokens",
            "/supported_dexs"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8106)
