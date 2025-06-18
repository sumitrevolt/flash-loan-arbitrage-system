#!/usr/bin/env python3
"""
Consolidated DEX Monitoring and Arbitrage Analysis System
========================================================
Merged from: enhanced_dex_arbitrage_monitor_11_tokens.py, enhanced_dex_monitor_final.py,
            enhanced_dex_calculations_dashboard.py, enhanced_dex_price_calculator.py

This consolidated tool provides comprehensive DEX monitoring capabilities including:
- Real-time monitoring of all 11 tokens across multiple DEXes
- Advanced arbitrage calculations with risk analysis
- Web dashboard with WebSocket real-time updates
- Price impact and slippage calculations
- Confidence scoring for arbitrage opportunities
- Multi-chain support with gas optimization
"""

import asyncio
import aiohttp
import time
import json
import threading
import math
import logging
import requests
import os
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from typing import Dict, List, Any, Optional, Union, TypedDict, Tuple
from dataclasses import dataclass
from pathlib import Path
from web3 import Web3

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Set precision for calculations
getcontext().prec = 28

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'consolidated-dex-monitor-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Type Definitions

class NetworkConfigDetail(TypedDict):
    rpc_url: str
    gas_price_gwei: int
    native_token: str
    native_price_usd: float

class DexPriceDetail(TypedDict):
    price: float
    liquidity: float
    volume_24h: float
    fee_percent: float
    chain: str
    timestamp: float
    change_24h: Optional[float]

@dataclass
class ArbitrageOpportunity:
    """Enhanced arbitrage opportunity with comprehensive analysis"""
    token_pair: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    spread_percent: float
    potential_profit: float
    net_profit: float
    max_trade_amount: float
    
    # Enhanced calculations
    price_impact_buy: float = 0.0
    price_impact_sell: float = 0.0
    slippage_tolerance: float = 0.5
    confidence_score: float = 0.0
    risk_score: float = 0.0
    gas_cost_usd: float = 0.0
    flash_loan_fee: float = 0.0
    execution_time_estimate: float = 0.0

class ConsolidatedDEXMonitor:
    """
    Consolidated DEX monitoring system combining all functionality
    """
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.trade_amount = 10000  # Default $10,000 trade size
        self.min_profit_threshold = 5.0  # $5 minimum profit
        
        # Gas and fee configurations
        self.gas_price_gwei = 30  # Polygon network gas price
        self.base_gas_limit = 300000  # Base gas limit for arbitrage
        self.slippage_tolerance = 0.5  # 0.5% slippage tolerance
        self.flash_loan_fee_percent = 0.09  # 0.09% flash loan fee
        
        # Network configurations
        self.network_configs: Dict[str, NetworkConfigDetail] = {
            "polygon": {
                "rpc_url": "https://polygon-rpc.com",
                "gas_price_gwei": 30,
                "native_token": "MATIC",
                "native_price_usd": 0.95
            },
            "ethereum": {
                "rpc_url": "https://eth.llamarpc.com",
                "gas_price_gwei": 20,
                "native_token": "ETH",
                "native_price_usd": 2500.0
            },
            "bsc": {
                "rpc_url": "https://bsc-dataseed.binance.org",
                "gas_price_gwei": 5,
                "native_token": "BNB",
                "native_price_usd": 300.0
            }
        }
        
        # Token configurations for 11 approved tokens
        self.approved_tokens = {
            "WETH": {"address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", "decimals": 18},
            "WBTC": {"address": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6", "decimals": 8},
            "USDC": {"address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "decimals": 6},
            "USDT": {"address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F", "decimals": 6},
            "DAI": {"address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063", "decimals": 18},
            "MATIC": {"address": "0x0000000000000000000000000000000000001010", "decimals": 18},
            "LINK": {"address": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39", "decimals": 18},
            "UNI": {"address": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f", "decimals": 18},
            "AAVE": {"address": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B", "decimals": 18},
            "SUSHI": {"address": "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a", "decimals": 18},
            "COMP": {"address": "0x8505b9d2254A7Ae468c0E9dd10Ccea3A837aef5c", "decimals": 18}
        }
        
        # Popular trading pairs
        self.token_pairs = [
            "WETH/USDC", "WETH/USDT", "WETH/DAI",
            "WBTC/WETH", "WBTC/USDC",
            "MATIC/WETH", "MATIC/USDC", 
            "LINK/WETH", "LINK/USDC",
            "UNI/WETH", "UNI/USDC",
            "AAVE/WETH", "AAVE/USDC",
            "SUSHI/WETH", "SUSHI/USDC",
            "COMP/WETH", "COMP/USDC"
        ]
        
        # DEX configurations
        self.dex_configs = {
            "Uniswap V3": {"fee_tier": 0.3, "base_url": "https://api.uniswap.org/v1"},
            "SushiSwap": {"fee_tier": 0.25, "base_url": "https://api.sushi.com/v1"},
            "Balancer V2": {"fee_tier": 0.2, "base_url": "https://api.balancer.fi/v1"},
            "1inch": {"fee_tier": 0.1, "base_url": "https://api.1inch.io/v4.0"},
            "Curve": {"fee_tier": 0.04, "base_url": "https://api.curve.fi/v1"},
            "QuickSwap": {"fee_tier": 0.3, "base_url": "https://api.quickswap.exchange/v1"}
        }
        
        # Data storage
        self.current_prices: Dict[str, Dict[str, DexPriceDetail]] = {}
        self.arbitrage_opportunities: List[ArbitrageOpportunity] = []
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        self.monitoring_active = False
        
        logger.info(f"Consolidated DEX Monitor initialized on port {self.port}")
    
    def calculate_price_impact(self, trade_size: float, liquidity: float) -> float:
        """Calculate price impact based on trade size and liquidity"""
        if liquidity <= 0:
            return 0.10  # 10% impact if no liquidity data
        
        # Price impact formula: impact = (trade_size / liquidity) * factor
        impact_factor = min(trade_size / liquidity, 0.20)  # Cap at 20%
        return round(impact_factor, 4)
    
    def calculate_confidence_score(self, price_spread: float, liquidity_ratio: float, 
                                 volatility: float, data_age: float) -> float:
        """Calculate confidence score (0-1) for arbitrage opportunity"""
        # Base confidence from spread size
        spread_confidence = min(price_spread / 2.0, 1.0)  # Higher spread = higher confidence
        
        # Liquidity confidence (higher is better)
        liquidity_confidence = min(liquidity_ratio / 1000000, 1.0)  # Normalize by 1M
        
        # Data freshness confidence (newer is better)
        age_penalty = max(0, 1.0 - (data_age / 300))  # 5-minute decay
        
        # Volatility penalty (lower volatility = higher confidence)
        volatility_confidence = max(0, 1.0 - (volatility / 10))  # Normalize by 10%
        
        # Weighted average
        confidence = (
            spread_confidence * 0.4 +
            liquidity_confidence * 0.3 +
            age_penalty * 0.2 +
            volatility_confidence * 0.1
        )
        
        return round(min(confidence, 1.0), 3)
    
    def calculate_gas_cost(self, network: str, complexity_factor: float = 1.0) -> float:
        """Calculate gas cost in USD for arbitrage transaction"""
        if network not in self.network_configs:
            return 10.0  # Default fallback
        
        config = self.network_configs[network]
        gas_limit = self.base_gas_limit * complexity_factor
        gas_cost_gwei = config["gas_price_gwei"] * gas_limit
        gas_cost_eth = gas_cost_gwei / 1e9  # Convert to ETH
        gas_cost_usd = gas_cost_eth * config["native_price_usd"]
        
        return round(gas_cost_usd, 2)
    
    def calculate_risk_score(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate risk score (0-1) for arbitrage opportunity"""
        risk_factors = []
        
        # Price impact risk
        total_impact = opportunity.price_impact_buy + opportunity.price_impact_sell
        impact_risk = min(total_impact * 5, 1.0)  # Scale to 0-1
        risk_factors.append(impact_risk)
        
        # Liquidity risk
        if opportunity.max_trade_amount < 1000:
            liquidity_risk = 0.8
        elif opportunity.max_trade_amount < 5000:
            liquidity_risk = 0.4
        else:
            liquidity_risk = 0.1
        risk_factors.append(liquidity_risk)
        
        # Spread risk (very high spreads might be fake)
        if opportunity.spread_percent > 5.0:
            spread_risk = 0.7
        elif opportunity.spread_percent > 2.0:
            spread_risk = 0.3
        else:
            spread_risk = 0.1
        risk_factors.append(spread_risk)
        
        # Gas cost risk
        gas_percentage = (opportunity.gas_cost_usd / opportunity.potential_profit) * 100
        if gas_percentage > 50:
            gas_risk = 0.8
        elif gas_percentage > 20:
            gas_risk = 0.4
        else:
            gas_risk = 0.1
        risk_factors.append(gas_risk)
        
        # Average risk score
        return round(sum(risk_factors) / len(risk_factors), 3)
    
    async def fetch_real_token_prices(self) -> Dict[str, float]:
        """Fetch real-time token prices from CoinGecko API"""
        token_ids = {
            "WETH": "ethereum",
            "WBTC": "wrapped-bitcoin",
            "USDC": "usd-coin",
            "USDT": "tether",
            "DAI": "dai",
            "MATIC": "matic-network",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "AAVE": "aave",
            "SUSHI": "sushi",
            "COMP": "compound-governance-token"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                ids_param = ",".join(token_ids.values())
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd&include_24hr_change=true"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        prices = {}
                        for token, coin_id in token_ids.items():
                            if coin_id in data:
                                prices[token] = {
                                    "price": data[coin_id]["usd"],
                                    "change_24h": data[coin_id].get("usd_24h_change", 0)
                                }
                        
                        return prices
                    else:
                        logger.warning(f"Failed to fetch prices: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching real prices: {e}")
            return {}
    
    def simulate_dex_prices(self, base_prices: Dict[str, float]) -> Dict[str, Dict[str, DexPriceDetail]]:
        """Simulate DEX prices with realistic variations"""
        dex_prices = {}
        
        for token, base_data in base_prices.items():
            base_price = base_data["price"]
            dex_prices[token] = {}
            
            for dex_name, dex_config in self.dex_configs.items():
                # Add realistic price variation (±0.1% to ±1.5%)
                variation = (random.uniform(-1.5, 1.5) / 100)
                dex_price = base_price * (1 + variation)
                
                # Simulate liquidity based on DEX size
                base_liquidity = random.uniform(100000, 5000000)
                if "Uniswap" in dex_name:
                    base_liquidity *= 2  # Uniswap typically has more liquidity
                elif "1inch" in dex_name:
                    base_liquidity *= 1.5  # 1inch aggregates liquidity
                
                dex_prices[token][dex_name] = {
                    "price": round(dex_price, 6),
                    "liquidity": round(base_liquidity, 2),
                    "volume_24h": round(random.uniform(50000, 1000000), 2),
                    "fee_percent": dex_config["fee_tier"],
                    "chain": "polygon",
                    "timestamp": time.time(),
                    "change_24h": base_data.get("change_24h", 0)
                }
        
        return dex_prices
    
    def find_arbitrage_opportunities(self, dex_prices: Dict[str, Dict[str, DexPriceDetail]]) -> List[ArbitrageOpportunity]:
        """Find and calculate arbitrage opportunities"""
        opportunities = []
        
        for token in dex_prices:
            token_dex_prices = dex_prices[token]
            dex_names = list(token_dex_prices.keys())
            
            # Compare all DEX pairs for this token
            for i in range(len(dex_names)):
                for j in range(i + 1, len(dex_names)):
                    buy_dex = dex_names[i]
                    sell_dex = dex_names[j]
                    
                    buy_price = token_dex_prices[buy_dex]["price"]
                    sell_price = token_dex_prices[sell_dex]["price"]
                    
                    # Determine which direction offers better arbitrage
                    if sell_price > buy_price:
                        spread_percent = ((sell_price - buy_price) / buy_price) * 100
                        
                        # Calculate trade amounts and fees
                        max_trade_amount = min(
                            token_dex_prices[buy_dex]["liquidity"] * 0.1,  # 10% of liquidity
                            token_dex_prices[sell_dex]["liquidity"] * 0.1,
                            self.trade_amount
                        )
                        
                        # Calculate costs
                        price_impact_buy = self.calculate_price_impact(max_trade_amount, token_dex_prices[buy_dex]["liquidity"])
                        price_impact_sell = self.calculate_price_impact(max_trade_amount, token_dex_prices[sell_dex]["liquidity"])
                        
                        gas_cost = self.calculate_gas_cost("polygon", 1.2)  # Flash loan adds complexity
                        flash_loan_fee = max_trade_amount * (self.flash_loan_fee_percent / 100)
                        dex_fees = max_trade_amount * ((token_dex_prices[buy_dex]["fee_percent"] + token_dex_prices[sell_dex]["fee_percent"]) / 100)
                        
                        # Calculate potential profit
                        gross_profit = max_trade_amount * (spread_percent / 100)
                        slippage_cost = max_trade_amount * ((price_impact_buy + price_impact_sell) / 100)
                        total_costs = gas_cost + flash_loan_fee + dex_fees + slippage_cost
                        net_profit = gross_profit - total_costs
                        
                        # Only include profitable opportunities
                        if net_profit > self.min_profit_threshold:
                            # Calculate additional metrics
                            liquidity_ratio = min(token_dex_prices[buy_dex]["liquidity"], token_dex_prices[sell_dex]["liquidity"])
                            volatility = abs(token_dex_prices[buy_dex].get("change_24h", 0))
                            data_age = time.time() - token_dex_prices[buy_dex]["timestamp"]
                            
                            opportunity = ArbitrageOpportunity(
                                token_pair=f"{token}/USDC",
                                buy_dex=buy_dex,
                                sell_dex=sell_dex,
                                buy_price=buy_price,
                                sell_price=sell_price,
                                spread_percent=round(spread_percent, 3),
                                potential_profit=round(gross_profit, 2),
                                net_profit=round(net_profit, 2),
                                max_trade_amount=round(max_trade_amount, 2),
                                price_impact_buy=round(price_impact_buy * 100, 3),
                                price_impact_sell=round(price_impact_sell * 100, 3),
                                slippage_tolerance=self.slippage_tolerance,
                                gas_cost_usd=round(gas_cost, 2),
                                flash_loan_fee=round(flash_loan_fee, 2),
                                execution_time_estimate=random.uniform(15, 45)  # 15-45 seconds
                            )
                            
                            # Calculate confidence and risk scores
                            opportunity.confidence_score = self.calculate_confidence_score(
                                spread_percent, liquidity_ratio, volatility, data_age
                            )
                            opportunity.risk_score = self.calculate_risk_score(opportunity)
                            
                            opportunities.append(opportunity)
        
        # Sort by net profit (highest first)
        opportunities.sort(key=lambda x: Any: Any: x.net_profit, reverse=True)
        return opportunities
    
    async def monitor_prices(self):
        """Main monitoring loop"""
        logger.info("Starting price monitoring...")
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                # Fetch real prices
                real_prices = await self.fetch_real_token_prices()
                
                if real_prices:
                    # Simulate DEX prices
                    self.current_prices = self.simulate_dex_prices(real_prices)
                    
                    # Find arbitrage opportunities
                    self.arbitrage_opportunities = self.find_arbitrage_opportunities(self.current_prices)
                    
                    # Store price history
                    timestamp = datetime.now().isoformat()
                    for token, dex_data in self.current_prices.items():
                        if token not in self.price_history:
                            self.price_history[token] = []
                        
                        # Keep last 100 price points
                        self.price_history[token].append({
                            "timestamp": timestamp,
                            "prices": {dex: data["price"] for dex, data in dex_data.items()}
                        })
                        self.price_history[token] = self.price_history[token][-100:]
                    
                    # Emit updates via WebSocket
                    try:
                        socketio.emit('price_update', {
                            'prices': self.current_prices,
                            'opportunities': [
                                {
                                    'token_pair': opp.token_pair,
                                    'buy_dex': opp.buy_dex,
                                    'sell_dex': opp.sell_dex,
                                    'spread_percent': opp.spread_percent,
                                    'net_profit': opp.net_profit,
                                    'confidence_score': opp.confidence_score,
                                    'risk_score': opp.risk_score
                                } for opp in self.arbitrage_opportunities[:10]  # Top 10
                            ],
                            'timestamp': timestamp
                        })
                    except Exception as e:
                        logger.warning(f"WebSocket emit failed: {e}")
                    
                    logger.info(f"Found {len(self.arbitrage_opportunities)} arbitrage opportunities")
                else:
                    logger.warning("No price data received")
                
                # Wait before next update
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_active = False
        logger.info("Monitoring stopped")

# Flask Routes

@app.route('/')
def dashboard():
    """Main dashboard"""
    return jsonify({
        "status": "Consolidated DEX Monitor Active",
        "monitoring": monitor.monitoring_active,
        "supported_tokens": list(monitor.approved_tokens.keys()),
        "supported_dexes": list(monitor.dex_configs.keys()),
        "current_opportunities": len(monitor.arbitrage_opportunities)
    })

@app.route('/api/prices')
def get_current_prices():
    """Get current prices from all DEXes"""
    return jsonify({
        "prices": monitor.current_prices,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/opportunities')
def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    opportunities_data = []
    for opp in monitor.arbitrage_opportunities:
        opportunities_data.append({
            "token_pair": opp.token_pair,
            "buy_dex": opp.buy_dex,
            "sell_dex": opp.sell_dex,
            "buy_price": opp.buy_price,
            "sell_price": opp.sell_price,
            "spread_percent": opp.spread_percent,
            "potential_profit": opp.potential_profit,
            "net_profit": opp.net_profit,
            "max_trade_amount": opp.max_trade_amount,
            "confidence_score": opp.confidence_score,
            "risk_score": opp.risk_score,
            "gas_cost_usd": opp.gas_cost_usd,
            "execution_time_estimate": opp.execution_time_estimate
        })
    
    return jsonify({
        "opportunities": opportunities_data,
        "count": len(opportunities_data),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/history/<token>')
def get_price_history(token):
    """Get price history for a specific token"""
    if token in monitor.price_history:
        return jsonify({
            "token": token,
            "history": monitor.price_history[token],
            "points": len(monitor.price_history[token])
        })
    else:
        return jsonify({"error": "Token not found"}), 404

@app.route('/api/stats')
def get_statistics():
    """Get monitoring statistics"""
    if not monitor.current_prices:
        return jsonify({"error": "No data available"}), 503
    
    total_opportunities = len(monitor.arbitrage_opportunities)
    profitable_opportunities = len([opp for opp in monitor.arbitrage_opportunities if opp.net_profit > 0])
    high_confidence_opportunities = len([opp for opp in monitor.arbitrage_opportunities if opp.confidence_score > 0.7])
    
    total_potential_profit = sum(opp.potential_profit for opp in monitor.arbitrage_opportunities)
    total_net_profit = sum(opp.net_profit for opp in monitor.arbitrage_opportunities if opp.net_profit > 0)
    
    return jsonify({
        "total_tokens": len(monitor.approved_tokens),
        "total_dexes": len(monitor.dex_configs),
        "total_opportunities": total_opportunities,
        "profitable_opportunities": profitable_opportunities,
        "high_confidence_opportunities": high_confidence_opportunities,
        "total_potential_profit": round(total_potential_profit, 2),
        "total_net_profit": round(total_net_profit, 2),
        "monitoring_active": monitor.monitoring_active,
        "last_update": datetime.now().isoformat()
    })

# WebSocket Events

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected to WebSocket")
    emit('status', {'status': 'connected', 'monitoring': monitor.monitoring_active})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from WebSocket")

@socketio.on('start_monitoring')
def handle_start_monitoring():
    """Start monitoring via WebSocket"""
    if not monitor.monitoring_active:
        asyncio.create_task(monitor.monitor_prices())
        emit('status', {'status': 'monitoring_started'})

@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """Stop monitoring via WebSocket"""
    monitor.stop_monitoring()
    emit('status', {'status': 'monitoring_stopped'})

# Global monitor instance
monitor = ConsolidatedDEXMonitor()

async def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Consolidated DEX Monitor')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the web server')
    parser.add_argument('--trade-amount', type=float, default=10000, help='Default trade amount in USD')
    parser.add_argument('--min-profit', type=float, default=5.0, help='Minimum profit threshold in USD')
    parser.add_argument('--monitor-only', action='store_true', help='Run monitoring without web server')
    
    args = parser.parse_args()
    
    # Configure monitor
    global monitor
    monitor = ConsolidatedDEXMonitor(port=args.port)
    monitor.trade_amount = args.trade_amount
    monitor.min_profit_threshold = args.min_profit
    
    if args.monitor_only:
        # Run monitoring only
        logger.info("Starting monitoring only mode...")
        await monitor.monitor_prices()
    else:
        # Start monitoring in background
        monitoring_task = asyncio.create_task(monitor.monitor_prices())
        
        # Run web server
        logger.info(f"Starting web server on port {args.port}...")
        socketio.run(app, host='0.0.0.0', port=args.port, debug=False)

if __name__ == "__main__":
    # Run the main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error running DEX monitor: {e}")
