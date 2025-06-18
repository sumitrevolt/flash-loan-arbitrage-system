#!/usr/bin/env python3
"""
Real-Time Price MCP Server
==========================

Provides real-time pricing data from multiple DEXes for arbitrage opportunities.
Simulates price feeds for demonstration purposes with realistic fluctuations.

Features:
- Multi-DEX price simulations
- Arbitrage opportunity detection
- Price validation and confidence scoring
- Historical price tracking
- Complete MCP Coordinator integration
"""

import asyncio
import json
import sys
import logging
import os
import time
import random
import requests
from decimal import Decimal, getcontext
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from web3 import Web3

# Type definitions
from typing import TypedDict

class DexConfigDict(TypedDict):
    name: str
    base_price_multiplier: float
    volatility: float
    liquidity_base: int
    volume_base: int

class TokenConfigDict(TypedDict):
    price: float
    decimals: int
    symbol: str
    volatility: float

ToolSchema = Dict[str, Any]

# Set precision for financial calculations
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(os.path.join("logs", "real_time_price_mcp.log"))
    ]
)
logger = logging.getLogger("real-time-price-mcp")

@dataclass
class PricePoint:
    """Individual price data point"""
    dex: str
    token_pair: str
    price: Decimal
    liquidity: Decimal
    volume_24h: Decimal
    timestamp: datetime
    confidence: float
    source: str  # 'simulated' or 'web3'
    
@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity between DEXes"""
    token_pair: str
    buy_dex: str
    sell_dex: str
    buy_price: Decimal
    sell_price: Decimal
    profit_percentage: Decimal
    estimated_profit_usd: Decimal
    liquidity_score: float
    confidence: float
    timestamp: datetime

class RealTimePriceMCPServer:
    """MCP Server for real-time price data"""
    
    def __init__(self):
        self.name: str = "real-time-price-mcp-server"
        self.server_type: str = "pricing"
        self.version: str = "1.0.0"
        self.tools: List[ToolSchema] = []
        self.active_requests: Dict[str, Any] = {}
        self.request_history: List[Any] = []
        self.coordinator_url: str = os.getenv("MCP_COORDINATOR_URL", "http://localhost:9000")
        self.status: str = "operational"
          # DEX configurations
        self.dex_configs: Dict[str, DexConfigDict] = {
            'uniswap': {
                'name': 'Uniswap',
                'base_price_multiplier': 1.0,
                'volatility': 0.02,
                'liquidity_base': 10000000,
                'volume_base': 5000000
            },
            'sushiswap': {
                'name': 'SushiSwap',
                'base_price_multiplier': 1.005,
                'volatility': 0.025,
                'liquidity_base': 8000000,
                'volume_base': 3000000
            },
            'quickswap': {
                'name': 'QuickSwap',
                'base_price_multiplier': 0.995,
                'volatility': 0.03,
                'liquidity_base': 5000000,
                'volume_base': 2000000
            },
            'pancakeswap': {
                'name': 'PancakeSwap',
                'base_price_multiplier': 1.01,
                'volatility': 0.02,
                'liquidity_base': 12000000,
                'volume_base': 6000000
            },
            'curve': {
                'name': 'Curve',
                'base_price_multiplier': 0.998,
                'volatility': 0.01,  # Lower volatility for stablecoin-focused DEX
                'liquidity_base': 15000000,
                'volume_base': 8000000
            }
        }          # Token configurations with base prices in USD
        self.tokens: Dict[str, TokenConfigDict] = {
            'WETH': {
                'price': 3000,
                'decimals': 18,
                'symbol': 'WETH',
                'volatility': 0.03
            },
            'WBTC': {
                'price': 50000,
                'decimals': 8,
                'symbol': 'WBTC',
                'volatility': 0.025
            },
            'USDC': {
                'price': 1,
                'decimals': 6,
                'symbol': 'USDC',
                'volatility': 0.001
            },
            'USDT': {
                'price': 1,
                'decimals': 6,
                'symbol': 'USDT',
                'volatility': 0.001
            },
            'DAI': {
                'price': 1,
                'decimals': 18,
                'symbol': 'DAI',
                'volatility': 0.002
            },
            'MATIC': {
                'price': 1.2,
                'decimals': 18,
                'symbol': 'MATIC',
                'volatility': 0.04
            },
            'LINK': {
                'price': 15,
                'decimals': 18,
                'symbol': 'LINK',
                'volatility': 0.035
            },
            'UNI': {
                'price': 7,
                'decimals': 18,
                'symbol': 'UNI',
                'volatility': 0.03
            },
            'AAVE': {
                'price': 80,
                'decimals': 18,
                'symbol': 'AAVE',
                'volatility': 0.035
            }
        }
          # Trading pairs to monitor
        self.monitored_pairs: List[str] = [
            'WETH/USDC',
            'WBTC/USDC',
            'WETH/WBTC',
            'USDC/USDT',
            'DAI/USDC',
            'MATIC/USDC',
            'LINK/USDC',
            'UNI/USDC',
            'AAVE/USDC'
        ]
        
        # Price cache
        self.price_cache: Dict[str, Dict[str, PricePoint]] = {}
        self.price_history: Dict[str, Dict[str, List[PricePoint]]] = {}  # Store historical prices
        self.cache_ttl: int = 30  # seconds
        
        # Last price update time
        self.last_price_update: datetime = datetime.now() - timedelta(minutes=5)  # Force immediate update
        self.update_interval: int = 5  # seconds
          # Base prices dictionary
        self.base_prices: Dict[str, float] = {}
        
        # Start time for uptime tracking
        self.start_time: float = 0.0
        
        # Initialize price simulation
        self._initialize_price_simulation()
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup available tools"""
        self.tools = [
            {
                "name": "fetch_price",
                "description": "Fetch real-time price from specific DEX",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dex": {"type": "string", "description": "DEX name (uniswap, sushiswap, etc.)"},
                        "token_pair": {"type": "string", "description": "Token pair (WETH/USDC, etc.)"}
                    },
                    "required": ["dex", "token_pair"]
                }
            },
            {
                "name": "fetch_all_prices",
                "description": "Fetch prices from all DEXes for specified pairs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pairs": {"type": "array", "items": {"type": "string"}, "description": "Token pairs to fetch"}
                    }
                }
            },
            {
                "name": "find_arbitrage_opportunities",
                "description": "Find arbitrage opportunities across all DEXes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "min_profit_percentage": {"type": "number", "description": "Minimum profit percentage", "default": 0.1},
                        "min_liquidity_usd": {"type": "number", "description": "Minimum liquidity in USD", "default": 10000}
                    }
                }
            },
            {
                "name": "get_token_liquidity",
                "description": "Get liquidity data for specific token pair",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dex": {"type": "string"},
                        "token_pair": {"type": "string"}
                    },
                    "required": ["dex", "token_pair"]
                }
            },
            {
                "name": "validate_price_feed",
                "description": "Validate price feed accuracy and freshness",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dex": {"type": "string"},
                        "token_pair": {"type": "string"},
                        "max_age_seconds": {"type": "number", "default": 60}
                    },
                    "required": ["dex", "token_pair"]
                }
            },
            {
                "name": "health_check",
                "description": "Check the health of the pricing server",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "register_with_coordinator",
                "description": "Register this server with the MCP coordinator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "coordinator_url": {"type": "string", "description": "URL of the coordinator"},
                        "capabilities": {"type": "array", "items": {"type": "string"}, "description": "Server capabilities"}
                    }
                }
            }
        ]
    
    def _initialize_price_simulation(self):
        """Initialize price simulation for all pairs and DEXes"""
        # Create base price mapping for each pair
        self.base_prices = {}
        
        for pair in self.monitored_pairs:
            tokens = pair.split('/')
            if len(tokens) != 2:
                continue
            
            token_a, token_b = tokens
            
            if token_a not in self.tokens or token_b not in self.tokens:
                continue
            
            # Calculate base price ratio
            self.base_prices[pair] = self.tokens[token_a]['price'] / self.tokens[token_b]['price']
            
            # Initialize cache entry
            self.price_cache[pair] = {}
            self.price_history[pair] = {}
              # Generate initial prices for each DEX
            for dex_name, _ in self.dex_configs.items():
                self.price_cache[pair][dex_name] = self._generate_price_point(dex_name, pair)
                self.price_history[pair][dex_name] = [self.price_cache[pair][dex_name]]
    
    def _get_router_info(self, dex_name):
        # Map DEX names to router addresses and ABI files
        router_info = {
            'uniswap': {
                'address': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                'abi': 'data/abi/uniswap_router.json',
                'chain': 'ethereum'
            },
            'sushiswap': {
                'address': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
                'abi': 'data/abi/sushiswap_router.json',
                'chain': 'ethereum'
            },
            'quickswap': {
                'address': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                'abi': 'data/abi/uniswap_router.json',
                'chain': 'polygon'
            }
        }
        return router_info.get(dex_name)

    def _get_web3(self, chain):
        # Map chain to RPC URL (customize as needed)
        rpc_urls = {
            'ethereum': os.getenv('ETHEREUM_RPC_URL', 'https://mainnet.infura.io/v3/YOUR_KEY'),
            'polygon': os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
        }
        return Web3(Web3.HTTPProvider(rpc_urls[chain]))

    def _fetch_real_dex_price(self, dex_name, token_pair, amount_in_wei):
        router_info = self._get_router_info(dex_name)
        if not router_info:
            return None
        try:
            w3 = self._get_web3(router_info['chain'])
            with open(router_info['abi']) as f:
                router_abi = json.load(f)
            router = w3.eth.contract(address=router_info['address'], abi=router_abi)
            token_a, token_b = token_pair.split('/')
            token_a_addr = self.tokens[token_a]['address'] if 'address' in self.tokens[token_a] else None
            token_b_addr = self.tokens[token_b]['address'] if 'address' in self.tokens[token_b] else None
            if not token_a_addr or not token_b_addr:
                return None
            path = [Web3.to_checksum_address(token_a_addr), Web3.to_checksum_address(token_b_addr)]
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
            return amounts[-1]
        except Exception as e:
            logger.warning(f"Failed to fetch real price for {dex_name} {token_pair}: {e}")
            return None

    def _generate_price_point(self, dex_name: str, token_pair: str) -> PricePoint:
        # Try real price fetch for supported DEXes
        if dex_name in ['uniswap', 'sushiswap', 'quickswap']:
            token_a, token_b = token_pair.split('/')
            token_a_decimals = self.tokens[token_a]['decimals']
            amount_in_wei = 10 ** token_a_decimals
            real_price_out = self._fetch_real_dex_price(dex_name, token_pair, amount_in_wei)
            if real_price_out:
                token_b_decimals = self.tokens[token_b]['decimals']
                price = Decimal(real_price_out) / Decimal(10 ** token_b_decimals)
                # Use dummy liquidity/volume/confidence for now
                liquidity = Decimal('1000000')
                volume_24h = Decimal('500000')
                confidence = 0.9
                return PricePoint(
                    dex=self.dex_configs[dex_name]['name'],
                    token_pair=token_pair,
                    price=price,
                    liquidity=liquidity,
                    volume_24h=volume_24h,
                    timestamp=datetime.now(),
                    confidence=confidence,
                    source='web3'
                )
        # Fallback to simulation for unsupported DEXes or errors
        return self._generate_simulated_price_point(dex_name, token_pair)

    def _generate_simulated_price_point(self, dex_name: str, token_pair: str) -> PricePoint:
        # Existing simulation logic
        dex_config = self.dex_configs[dex_name]
        base_price = self.base_prices[token_pair]
        adjusted_price = base_price * dex_config['base_price_multiplier']
        tokens = token_pair.split('/')
        token_a_volatility = self.tokens[tokens[0]]['volatility']
        token_b_volatility = self.tokens[tokens[1]]['volatility']
        combined_volatility = (token_a_volatility + token_b_volatility) / 2 + dex_config['volatility']
        variation = 1.0 + (random.random() * 2 - 1) * combined_volatility
        final_price = Decimal(str(adjusted_price * variation))
        liquidity_variation = 0.8 + random.random() * 0.4
        volume_variation = 0.7 + random.random() * 0.6
        liquidity = Decimal(str(dex_config['liquidity_base'] * liquidity_variation))
        volume_24h = Decimal(str(dex_config['volume_base'] * volume_variation))
        confidence = min(float(liquidity) / 1000000, 0.95)
        return PricePoint(
            dex=dex_config['name'],
            token_pair=token_pair,
            price=final_price,
            liquidity=liquidity,
            volume_24h=volume_24h,
            timestamp=datetime.now(),
            confidence=confidence,
            source='simulated'
        )
    
    def _update_prices(self):
        """Update all simulated prices if needed"""
        now = datetime.now()
        if (now - self.last_price_update).total_seconds() < self.update_interval:
            return
        
        self.last_price_update = now
        
        # Update prices for all pairs and DEXes
        for pair in self.monitored_pairs:
            if pair not in self.price_cache:
                continue
                
            for dex_name in self.dex_configs:
                price_point = self._generate_price_point(dex_name, pair)
                
                # Store in cache
                self.price_cache[pair][dex_name] = price_point
                
                # Add to history (limit to 100 points)
                if len(self.price_history[pair][dex_name]) >= 100:
                    self.price_history[pair][dex_name].pop(0)
                self.price_history[pair][dex_name].append(price_point)
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP JSON-RPC messages"""
        method = message.get("method")
        params = message.get("params", {})
        id_val = message.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": id_val,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", 
                "id": id_val,
                "result": {
                    "tools": self.tools
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            result: str = await self.call_tool(tool_name, tool_args)
            
            return {
                "jsonrpc": "2.0",
                "id": id_val,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": id_val,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Handle tool calls for the server"""
        self._update_prices()  # Update prices before responding
        
        logger.info(f"Tool call: {name} with args {args}")
        
        if name == "fetch_price":
            return await self._fetch_price(args)
        
        elif name == "fetch_all_prices":
            return await self._fetch_all_prices(args)
        
        elif name == "find_arbitrage_opportunities":
            return await self._find_arbitrage_opportunities(args)
        
        elif name == "get_token_liquidity":
            return await self._get_token_liquidity(args)
        
        elif name == "validate_price_feed":
            return await self._validate_price_feed(args)
        
        elif name == "health_check":
            return await self._health_check(args)
        
        elif name == "register_with_coordinator":
            return await self._register_with_coordinator(args)
        
        return json.dumps({
            "error": f"Unknown tool: {name}",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _fetch_price(self, args: Dict[str, Any]) -> str:
        """Fetch price from specific DEX"""
        try:
            dex = args.get("dex")
            token_pair = args.get("token_pair")
            
            if not dex or not token_pair:
                return json.dumps({
                    "success": False,
                    "error": "Missing dex or token_pair parameter",
                    "timestamp": datetime.now().isoformat()
                })
            
            if dex not in self.dex_configs:
                return json.dumps({
                    "success": False,
                    "error": f"Unsupported DEX: {dex}",
                    "timestamp": datetime.now().isoformat()
                })
            
            if token_pair not in self.monitored_pairs:
                return json.dumps({
                    "success": False,
                    "error": f"Unsupported token pair: {token_pair}",
                    "timestamp": datetime.now().isoformat()
                })
            
            price_point = self.price_cache[token_pair][dex]
            
            return json.dumps({
                "success": True,
                "dex": dex,
                "token_pair": token_pair,
                "price": float(price_point.price),
                "liquidity": float(price_point.liquidity),
                "volume_24h": float(price_point.volume_24h),
                "timestamp": price_point.timestamp.isoformat(),                "confidence": price_point.confidence,
                "source": price_point.source
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error in fetch_price: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _fetch_all_prices(self, args: Dict[str, Any]) -> str:
        """Fetch prices from all DEXes for specified pairs"""
        try:
            pairs = args.get("pairs", self.monitored_pairs)
            
            all_prices = {}
            
            for pair in pairs:
                if pair not in self.price_cache:
                    continue
                
                all_prices[pair] = {}
                
                for dex_name, price_point in self.price_cache[pair].items():
                    all_prices[pair][dex_name] = {
                        "price": float(price_point.price),
                        "liquidity": float(price_point.liquidity),
                        "volume_24h": float(price_point.volume_24h),
                        "timestamp": price_point.timestamp.isoformat(),
                        "confidence": price_point.confidence,
                        "source": price_point.source
                    }
            
            return json.dumps({
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "prices": all_prices,
                "total_pairs": len(pairs),
                "successful_fetches": sum(1 for pair in pairs if pair in self.price_cache)
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error in fetch_all_prices: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _find_arbitrage_opportunities(self, args: Dict[str, Any]) -> str:
        """Find arbitrage opportunities across DEXes"""
        try:
            min_profit_percentage = float(args.get("min_profit_percentage", 0.1))
            min_liquidity_usd = float(args.get("min_liquidity_usd", 10000))
            
            opportunities: List[ArbitrageOpportunity] = []
            
            for pair in self.monitored_pairs:
                if pair not in self.price_cache:
                    continue
                
                dex_prices = self.price_cache[pair]
                if len(dex_prices) < 2:
                    continue
                
                # Find arbitrage opportunities
                dex_list = list(dex_prices.items())
                
                for i, (buy_dex_name, buy_price_point) in enumerate(dex_list):
                    for j, (sell_dex_name, sell_price_point) in enumerate(dex_list):
                        if i >= j:
                            continue
                        
                        buy_price = buy_price_point.price
                        sell_price = sell_price_point.price
                        buy_liquidity = buy_price_point.liquidity
                        sell_liquidity = sell_price_point.liquidity
                        
                        # Check if there's profit potential
                        if sell_price > buy_price:
                            profit_pct = float((sell_price - buy_price) / buy_price * 100)
                            
                            if profit_pct >= min_profit_percentage:
                                # Estimate USD profit (simplified)
                                min_liquidity = min(float(buy_liquidity), float(sell_liquidity))
                                if min_liquidity >= min_liquidity_usd:
                                    
                                    trade_amount = min_liquidity * 0.1  # Use 10% of available liquidity
                                    estimated_profit = trade_amount * profit_pct / 100
                                    
                                    # Calculate scores
                                    liquidity_score = min(min_liquidity / 100000, 1.0)
                                    confidence = (buy_price_point.confidence + sell_price_point.confidence) / 2
                                    
                                    opportunity = ArbitrageOpportunity(
                                        token_pair=pair,
                                        buy_dex=buy_dex_name,
                                        sell_dex=sell_dex_name,
                                        buy_price=buy_price,
                                        sell_price=sell_price,
                                        profit_percentage=Decimal(str(profit_pct)),
                                        estimated_profit_usd=Decimal(str(estimated_profit)),
                                        liquidity_score=liquidity_score,
                                        confidence=confidence,
                                        timestamp=datetime.now()
                                    )
                                    
                                    opportunities.append(opportunity)
            
            # Sort by profit percentage descending
            opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
            
            return json.dumps({
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "opportunities": [asdict(opp) for opp in opportunities],
                "total_opportunities": len(opportunities),
                "best_profit_percentage": float(opportunities[0].profit_percentage) if opportunities else 0
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error in find_arbitrage_opportunities: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _get_token_liquidity(self, args: Dict[str, Any]) -> str:
        """Get detailed liquidity information"""
        try:
            dex = args.get("dex")
            token_pair = args.get("token_pair")
            
            if not dex or not token_pair:
                return json.dumps({
                    "success": False,
                    "error": "Missing dex or token_pair parameter",
                    "timestamp": datetime.now().isoformat()
                })
            
            if dex not in self.dex_configs:
                return json.dumps({
                    "success": False,
                    "error": f"Unsupported DEX: {dex}",
                    "timestamp": datetime.now().isoformat()
                })
            
            if token_pair not in self.monitored_pairs:
                return json.dumps({
                    "success": False,
                    "error": f"Unsupported token pair: {token_pair}",
                    "timestamp": datetime.now().isoformat()
                })
            
            price_point = self.price_cache[token_pair][dex]
            
            return json.dumps({
                "success": True,
                "dex": dex,
                "token_pair": token_pair,
                "liquidity_usd": float(price_point.liquidity),
                "volume_24h_usd": float(price_point.volume_24h),
                "price": float(price_point.price),
                "confidence": price_point.confidence,
                "source": price_point.source,
                "timestamp": price_point.timestamp.isoformat()
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error in get_token_liquidity: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _validate_price_feed(self, args: Dict[str, Any]) -> str:
        """Validate price feed accuracy and freshness"""
        try:
            dex = args.get("dex")
            token_pair = args.get("token_pair")
            max_age_seconds = int(args.get("max_age_seconds", 60))
            
            if not dex or not token_pair:
                return json.dumps({
                    "success": False,
                    "error": "Missing dex or token_pair parameter",
                    "timestamp": datetime.now().isoformat()
                })
            
            if dex not in self.dex_configs:
                return json.dumps({
                    "success": False,
                    "error": f"Unsupported DEX: {dex}",
                    "timestamp": datetime.now().isoformat()
                })
            
            if token_pair not in self.monitored_pairs:
                return json.dumps({
                    "success": False,
                    "error": f"Unsupported token pair: {token_pair}",
                    "timestamp": datetime.now().isoformat()
                })
            
            price_point = self.price_cache[token_pair][dex]
            
            # Check age
            age_seconds = (datetime.now() - price_point.timestamp).total_seconds()
            is_fresh = age_seconds <= max_age_seconds
            
            # Check confidence
            has_good_confidence = price_point.confidence >= 0.7
            
            # Check liquidity
            has_sufficient_liquidity = price_point.liquidity >= 1000  # $1k minimum
            
            is_valid = is_fresh and has_good_confidence and has_sufficient_liquidity
            
            return json.dumps({
                "success": True,
                "valid": is_valid,
                "dex": dex,
                "token_pair": token_pair,
                "checks": {
                    "is_fresh": is_fresh,
                    "age_seconds": age_seconds,
                    "max_age_seconds": max_age_seconds,
                    "has_good_confidence": has_good_confidence,
                    "confidence": price_point.confidence,
                    "has_sufficient_liquidity": has_sufficient_liquidity,
                    "liquidity_usd": float(price_point.liquidity)
                },
                "price_data": {
                    "price": float(price_point.price),
                    "source": price_point.source,
                    "timestamp": price_point.timestamp.isoformat()
                }
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error in validate_price_feed: {str(e)}")
            return json.dumps({                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _health_check(self, args: Dict[str, Any]) -> str:
        """Check the health of the server"""
        health_data: Dict[str, Any] = {
            "status": self.status,
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "name": self.name,
                "type": self.server_type,
                "version": self.version
            },
            "active_requests": len(self.active_requests),
            "request_history": len(self.request_history),
            "price_cache_stats": {
                "pairs": len(self.price_cache),
                "dexes": len(self.dex_configs),
                "total_price_points": sum(len(dexes) for dexes in self.price_cache.values()),
                "last_update": self.last_price_update.isoformat()
            },
            "capabilities": [
                "real_time_price_feeds",
                "arbitrage_detection",
                "multi_dex_support",
                "liquidity_analysis"
            ]
        }
        
        return json.dumps(health_data, indent=2)
    
    async def _register_with_coordinator(self, args: Dict[str, Any]) -> str:
        """Register this server with the MCP coordinator"""
        coordinator_url = args.get("coordinator_url") or self.coordinator_url
        capabilities = args.get("capabilities", [])
        
        if not capabilities:
            capabilities = self._get_default_capabilities()
        
        logger.info(f"Registering with coordinator at {coordinator_url}")
        
        try:
            server_port = os.getenv("MCP_PORT", "8002")
            server_url = f"http://localhost:{server_port}"
            
            response = requests.post(
                f"{coordinator_url}/register_server",
                json={
                    "server_name": self.name,
                    "server_type": self.server_type,
                    "server_url": server_url,
                    "capabilities": capabilities
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result: str = response.json()
                logger.info(f"Successfully registered with coordinator: {result}")
                return json.dumps({
                    "success": True,
                    "coordinator_url": coordinator_url,
                    "registration_result": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.warning(f"Failed to register with coordinator: {response.status_code} - {response.text}")
                return json.dumps({
                    "success": False,
                    "error": f"Coordinator returned status {response.status_code}",
                    "response": response.text,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error registering with coordinator: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _get_default_capabilities(self) -> List[str]:
        """Get default capabilities for this server type"""
        return [
            "real_time_price_feeds",
            "arbitrage_detection",
            "multi_dex_support",
            "liquidity_analysis",
            "price_validation"
        ]
    
    async def _heartbeat_loop(self):
        """Send regular heartbeats to the coordinator"""
        while True:
            try:
                response = requests.post(
                    f"{self.coordinator_url}/server_heartbeat",
                    json={
                        "server_name": self.name,
                        "status": self.status,
                        "stats": {
                            "active_requests": len(self.active_requests),
                            "uptime_seconds": int(time.time() - self.start_time)
                        }
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.debug(f"Heartbeat sent successfully")
                else:
                    logger.warning(f"Failed to send heartbeat: {response.status_code}")
                    
                    # If we got a 404, try to re-register
                    if response.status_code == 404:
                        logger.info("Server not registered, attempting to re-register")
                        await self._register_with_coordinator({})
                
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
            
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
    
    async def run(self):
        """Run the MCP server"""
        self.start_time = time.time()
        logger.info(f"Starting {self.name} v{self.version} (stdio mode)")
        
        # Register with coordinator
        await self._register_with_coordinator({})
        
        # Start the heartbeat loop
        asyncio.create_task(self._heartbeat_loop())
        
        # Start the server
        while True:
            try:
                line: str = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )                
                if not line:
                    break
                    
                line: str = line.strip()
                if not line:
                    continue
                
                try:
                    message = json.loads(line)
                    response = await self.handle_message(message)
                    
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    error_response: Dict[str, Any] = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
            except Exception as e:
                logger.error(f"Server error: {str(e)}")
                break

def main():
    """Main entry point"""
    server = RealTimePriceMCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Real-Time Price MCP Server shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
