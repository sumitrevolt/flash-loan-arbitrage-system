#!/usr/bin/env python3
"""
Consolidated Pricing MCP Server
==============================
Unified pricing server combining functionality from multiple pricing servers
Real-time DEX price feeds, arbitrage detection, and opportunity scoring
"""

import asyncio
import json
import logging
import time
import random
import requests
from decimal import Decimal, getcontext
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from web3 import Web3
from flask import Flask, jsonify, request

# Set precision for financial calculations
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    """Price data structure"""
    token_pair: str
    dex: str
    price: Decimal
    liquidity: Decimal
    volume_24h: Decimal
    timestamp: datetime
    confidence: float  # 0.0 to 1.0

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity structure"""
    token_pair: str
    buy_dex: str
    sell_dex: str
    buy_price: Decimal
    sell_price: Decimal
    price_diff: Decimal
    profit_percentage: Decimal
    min_amount: Decimal
    max_amount: Decimal
    gas_cost: Decimal
    estimated_profit: Decimal
    confidence_score: float

class ConsolidatedPricingServer:
    """
    Consolidated pricing server for all DEX integrations
    Replaces multiple duplicate pricing servers
    """
    
    def __init__(self):
        self.app = Flask(__name__)
        self.price_cache: Dict[str, PriceData] = {}
        self.arbitrage_opportunities: List[ArbitrageOpportunity] = []
        self.supported_dexes = [
            "Uniswap_V2", "Uniswap_V3", "SushiSwap", "QuickSwap",
            "PancakeSwap", "Curve", "Balancer", "1inch"
        ]
        self.supported_tokens = [
            "WETH/USDC", "WETH/USDT", "WETH/DAI", "WMATIC/USDC",
            "WMATIC/USDT", "LINK/USDC", "UNI/USDC", "AAVE/USDC",
            "CRV/USDC", "COMP/USDC", "MKR/USDC"
        ]
        self.setup_routes()
        self.start_price_updates()
        
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health')
        def health():
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_feeds": len(self.price_cache),
                "arbitrage_opportunities": len(self.arbitrage_opportunities)
            })
            
        @self.app.route('/prices')
        def get_prices():
            """Get all current prices"""
            prices = {}
            for key, data in self.price_cache.items():
                prices[key] = {
                    "price": float(data.price),
                    "dex": data.dex,
                    "liquidity": float(data.liquidity),
                    "volume_24h": float(data.volume_24h),
                    "timestamp": data.timestamp.isoformat(),
                    "confidence": data.confidence
                }
            return jsonify(prices)
            
        @self.app.route('/prices/<token_pair>')
        def get_token_prices(token_pair):
            """Get prices for a specific token pair across all DEXes"""
            token_prices = {}
            for key, data in self.price_cache.items():
                if data.token_pair == token_pair:
                    token_prices[data.dex] = {
                        "price": float(data.price),
                        "liquidity": float(data.liquidity),
                        "volume_24h": float(data.volume_24h),
                        "timestamp": data.timestamp.isoformat(),
                        "confidence": data.confidence
                    }
            return jsonify(token_prices)
            
        @self.app.route('/arbitrage')
        def get_arbitrage_opportunities():
            """Get current arbitrage opportunities"""
            opportunities = []
            for opp in self.arbitrage_opportunities:
                opportunities.append({
                    "token_pair": opp.token_pair,
                    "buy_dex": opp.buy_dex,
                    "sell_dex": opp.sell_dex,
                    "buy_price": float(opp.buy_price),
                    "sell_price": float(opp.sell_price),
                    "price_diff": float(opp.price_diff),
                    "profit_percentage": float(opp.profit_percentage),
                    "estimated_profit": float(opp.estimated_profit),
                    "confidence_score": opp.confidence_score,
                    "min_amount": float(opp.min_amount),
                    "max_amount": float(opp.max_amount)
                })
            return jsonify(opportunities)
            
        @self.app.route('/arbitrage/best')
        def get_best_arbitrage():
            """Get the best arbitrage opportunity"""
            if not self.arbitrage_opportunities:
                return jsonify({"message": "No opportunities found"})
                
            best = max(self.arbitrage_opportunities, 
                      key=lambda x: Any: Any: x.estimated_profit * x.confidence_score)
            return jsonify({
                "token_pair": best.token_pair,
                "buy_dex": best.buy_dex,
                "sell_dex": best.sell_dex,
                "estimated_profit": float(best.estimated_profit),
                "profit_percentage": float(best.profit_percentage),
                "confidence_score": best.confidence_score
            })
            
    def start_price_updates(self):
        """Start background price update tasks"""
        asyncio.create_task(self.update_prices_loop())
        asyncio.create_task(self.detect_arbitrage_loop())
        
    async def update_prices_loop(self):
        """Continuously update prices from all DEXes"""
        while True:
            try:
                await self.update_all_prices()
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error updating prices: {e}")
                await asyncio.sleep(10)
                
    async def update_all_prices(self):
        """Update prices for all token pairs and DEXes"""
        for token_pair in self.supported_tokens:
            for dex in self.supported_dexes:
                price_data = await self.fetch_price_data(token_pair, dex)
                if price_data:
                    key = f"{token_pair}_{dex}"
                    self.price_cache[key] = price_data
                    
    async def fetch_price_data(self, token_pair: str, dex: str) -> Optional[PriceData]:
        """Fetch price data for a token pair from a specific DEX"""
        try:
            # For demo purposes, simulate realistic price data
            # In production, this would make actual API calls to DEXes
            base_price = self.get_base_price(token_pair)
            dex_multiplier = self.get_dex_multiplier(dex)
            volatility = random.uniform(0.98, 1.02)
            
            price = Decimal(str(base_price * dex_multiplier * volatility))
            liquidity = Decimal(str(random.uniform(100000, 1000000)))
            volume_24h = Decimal(str(random.uniform(50000, 500000)))
            confidence = random.uniform(0.85, 0.99)
            
            return PriceData(
                token_pair=token_pair,
                dex=dex,
                price=price,
                liquidity=liquidity,
                volume_24h=volume_24h,
                timestamp=datetime.now(),
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error fetching price for {token_pair} from {dex}: {e}")
            return None
            
    def get_base_price(self, token_pair: str) -> float:
        """Get base price for token pair"""
        base_prices = {
            "WETH/USDC": 2000.0,
            "WETH/USDT": 1998.0,
            "WETH/DAI": 2001.0,
            "WMATIC/USDC": 0.85,
            "WMATIC/USDT": 0.84,
            "LINK/USDC": 15.0,
            "UNI/USDC": 8.5,
            "AAVE/USDC": 120.0,
            "CRV/USDC": 0.95,
            "COMP/USDC": 45.0,
            "MKR/USDC": 1200.0
        }
        return base_prices.get(token_pair, 100.0)
        
    def get_dex_multiplier(self, dex: str) -> float:
        """Get price multiplier for DEX (simulates price differences)"""
        multipliers = {
            "Uniswap_V2": 1.0,
            "Uniswap_V3": 0.999,
            "SushiSwap": 1.001,
            "QuickSwap": 0.998,
            "PancakeSwap": 1.002,
            "Curve": 0.997,
            "Balancer": 1.003,
            "1inch": 0.996
        }
        return multipliers.get(dex, 1.0)
        
    async def detect_arbitrage_loop(self):
        """Continuously detect arbitrage opportunities"""
        while True:
            try:
                await self.detect_arbitrage_opportunities()
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error detecting arbitrage: {e}")
                await asyncio.sleep(15)
                
    async def detect_arbitrage_opportunities(self):
        """Detect arbitrage opportunities across DEXes"""
        self.arbitrage_opportunities.clear()
        
        for token_pair in self.supported_tokens:
            # Get all prices for this token pair
            token_prices = {}
            for key, data in self.price_cache.items():
                if data.token_pair == token_pair:
                    token_prices[data.dex] = data
                    
            if len(token_prices) < 2:
                continue
                
            # Find arbitrage opportunities
            dexes = list(token_prices.keys())
            for i in range(len(dexes)):
                for j in range(i + 1, len(dexes)):
                    dex1, dex2 = dexes[i], dexes[j]
                    price1, price2 = token_prices[dex1], token_prices[dex2]
                    
                    # Determine buy/sell DEXes
                    if price1.price < price2.price:
                        buy_dex, sell_dex = dex1, dex2
                        buy_price, sell_price = price1.price, price2.price
                        buy_liquidity = price1.liquidity
                    else:
                        buy_dex, sell_dex = dex2, dex1
                        buy_price, sell_price = price2.price, price1.price
                        buy_liquidity = price2.liquidity
                        
                    # Calculate profit metrics
                    price_diff = sell_price - buy_price
                    profit_percentage = (price_diff / buy_price) * 100
                    
                    # Only consider opportunities with >0.1% profit
                    if profit_percentage > 0.1:
                        # Estimate gas costs (simplified)
                        gas_cost = Decimal("5.0")  # $5 in gas
                        
                        # Calculate optimal trade amount
                        max_amount = min(buy_liquidity * Decimal("0.1"), Decimal("10000"))
                        min_amount = Decimal("100")
                        
                        estimated_profit = (price_diff * max_amount) - gas_cost
                        
                        if estimated_profit > 0:
                            confidence_score = min(
                                price1.confidence * price2.confidence,
                                0.99
                            )
                            
                            opportunity = ArbitrageOpportunity(
                                token_pair=token_pair,
                                buy_dex=buy_dex,
                                sell_dex=sell_dex,
                                buy_price=buy_price,
                                sell_price=sell_price,
                                price_diff=price_diff,
                                profit_percentage=profit_percentage,
                                min_amount=min_amount,
                                max_amount=max_amount,
                                gas_cost=gas_cost,
                                estimated_profit=estimated_profit,
                                confidence_score=confidence_score
                            )
                            
                            self.arbitrage_opportunities.append(opportunity)
                            
        # Sort by estimated profit
        self.arbitrage_opportunities.sort(
            key=lambda x: Any: Any: x.estimated_profit * x.confidence_score,
            reverse=True
        )
        
        # Keep only top 20 opportunities
        self.arbitrage_opportunities = self.arbitrage_opportunities[:20]
        
        if self.arbitrage_opportunities:
            best = self.arbitrage_opportunities[0]
            logger.info(f"Best opportunity: {best.token_pair} - "
                       f"{float(best.profit_percentage):.2f}% profit "
                       f"(${float(best.estimated_profit):.2f})")
                       
    def run(self, host='0.0.0.0', port=8001):
        """Run the pricing server"""
        logger.info(f"🚀 Starting Consolidated Pricing MCP Server on {host}:{port}")
        logger.info(f"Monitoring {len(self.supported_tokens)} token pairs across {len(self.supported_dexes)} DEXes")
        
        self.app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True
        )

def main():
    """Main entry point"""
    server = ConsolidatedPricingServer()
    server.run()

if __name__ == "__main__":
    main()
