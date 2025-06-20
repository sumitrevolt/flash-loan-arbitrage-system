#!/usr/bin/env python3
"""
Enhanced DEX Calculations Dashboard
Real-time DEX price monitoring with advanced arbitrage calculations and risk analysis
Port 8005 - Enhanced DEX Calculations Dashboard
"""

import asyncio
import aiohttp
import json
import time
import threading
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'enhanced-dex-dashboard-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@dataclass
class EnhancedArbitrageCalculation:
    """Enhanced arbitrage calculation with risk metrics"""
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
    gas_cost_usd: float = 0.01
    execution_time_ms: int = 500
    confidence_score: float = 0.0
    risk_level: str = "medium"
    
    # Market data
    volume_24h_buy: float = 0.0
    volume_24h_sell: float = 0.0
    liquidity_buy: float = 0.0
    liquidity_sell: float = 0.0
    
    # Profit calculations
    gross_profit: float = 0.0
    net_profit_after_fees: float = 0.0
    roi_percent: float = 0.0
    annualized_roi: float = 0.0
    
    timestamp: datetime = None

class EnhancedDEXCalculator:
    """Advanced DEX arbitrage calculator with risk analysis"""
    
    def __init__(self):
        self.price_history: Dict[str, List[Dict]] = {}
        self.calculation_cache: Dict[str, Any] = {}
        self.market_volatility: Dict[str, float] = {}
        self.dex_performance: Dict[str, Dict] = {}
        
        # Configuration
        self.min_profit_threshold = 0.005  # 0.5%
        self.max_slippage = 0.01  # 1%
        self.gas_price_gwei = 25
        self.confidence_threshold = 0.7
        
    def calculate_enhanced_arbitrage(self, price_data: Dict) -> List[EnhancedArbitrageCalculation]:
        """Calculate enhanced arbitrage opportunities with risk analysis"""
        opportunities = []
        
        try:
            # Group prices by token pair
            pair_prices = self._group_prices_by_pair(price_data)
            
            for pair, dex_prices in pair_prices.items():
                if len(dex_prices) < 2:
                    continue
                    
                # Find arbitrage opportunities for this pair
                pair_opportunities = self._find_pair_arbitrage(pair, dex_prices)
                opportunities.extend(pair_opportunities)
            
            # Sort by net profit and return top opportunities
            opportunities.sort(key=lambda x: Any: Any: x.net_profit, reverse=True)
            return opportunities[:20]  # Top 20 opportunities
            
        except Exception as e:
            logger.error(f"Error calculating enhanced arbitrage: {e}")
            return []
    
    def _group_prices_by_pair(self, price_data: Dict) -> Dict[str, Dict]:
        """Group prices by token pair"""
        pair_prices = {}
        
        for dex, prices in price_data.get('prices', {}).items():
            for price_info in prices:
                pair = price_info['token_pair']
                if pair not in pair_prices:
                    pair_prices[pair] = {}
                pair_prices[pair][dex] = price_info
                
        return pair_prices
    
    def _find_pair_arbitrage(self, pair: str, dex_prices: Dict) -> List[EnhancedArbitrageCalculation]:
        """Find arbitrage opportunities for a specific pair"""
        opportunities = []
        dex_names = list(dex_prices.keys())
        
        for i in range(len(dex_names)):
            for j in range(i + 1, len(dex_names)):
                dex1, dex2 = dex_names[i], dex_names[j]
                price1 = dex_prices[dex1]['price']
                price2 = dex_prices[dex2]['price']
                
                if price1 <= 0 or price2 <= 0:
                    continue
                
                # Determine buy and sell DEX
                if price1 < price2:
                    buy_dex, sell_dex = dex1, dex2
                    buy_price, sell_price = price1, price2
                    buy_data, sell_data = dex_prices[dex1], dex_prices[dex2]
                else:
                    buy_dex, sell_dex = dex2, dex1
                    buy_price, sell_price = price2, price1
                    buy_data, sell_data = dex_prices[dex2], dex_prices[dex1]
                
                # Calculate spread
                spread_percent = (sell_price - buy_price) / buy_price * 100
                
                if spread_percent >= self.min_profit_threshold * 100:
                    # Enhanced calculations
                    opportunity = self._calculate_enhanced_metrics(
                        pair, buy_dex, sell_dex, buy_price, sell_price,
                        spread_percent, buy_data, sell_data
                    )
                    
                    if opportunity.net_profit > 0:
                        opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_enhanced_metrics(self, pair: str, buy_dex: str, sell_dex: str,
                                  buy_price: float, sell_price: float, spread_percent: float,
                                  buy_data: Dict, sell_data: Dict) -> EnhancedArbitrageCalculation:
        """Calculate enhanced metrics for arbitrage opportunity"""
        
        # Basic liquidity and volume
        buy_liquidity = buy_data.get('liquidity', 0)
        sell_liquidity = sell_data.get('liquidity', 0)
        buy_volume = buy_data.get('volume_24h', 0)
        sell_volume = sell_data.get('volume_24h', 0)
        
        # Calculate trade size based on liquidity
        max_trade_usd = min(buy_liquidity * 0.05, sell_liquidity * 0.05, 50000)  # Max $50k
        min_trade_usd = max(1000, max_trade_usd * 0.1)  # Min $1k
        
        # Price impact estimation
        price_impact_buy = self._estimate_price_impact(max_trade_usd, buy_liquidity)
        price_impact_sell = self._estimate_price_impact(max_trade_usd, sell_liquidity)
        
        # Adjust prices for slippage
        effective_buy_price = buy_price * (1 + price_impact_buy + self.max_slippage)
        effective_sell_price = sell_price * (1 - price_impact_sell - self.max_slippage)
        
        # Gas cost estimation (Polygon)
        gas_cost_usd = 0.01 * self.gas_price_gwei / 30  # Adjusted for current gas
        
        # Profit calculations
        gross_profit = max_trade_usd * (effective_sell_price - effective_buy_price) / effective_buy_price
        net_profit = gross_profit - gas_cost_usd
        
        # DEX fees (0.3% for most DEXs)
        dex_fees = max_trade_usd * 0.006  # 0.3% each side
        net_profit_after_fees = net_profit - dex_fees
        
        # ROI calculations
        roi_percent = (net_profit_after_fees / max_trade_usd) * 100 if max_trade_usd > 0 else 0
        annualized_roi = roi_percent * 365 * 24 * 6  # Assuming 6 trades per hour
        
        # Risk assessment
        confidence_score = self._calculate_confidence_score(
            spread_percent, buy_liquidity, sell_liquidity, buy_volume, sell_volume
        )
        
        risk_level = self._assess_risk_level(
            spread_percent, price_impact_buy + price_impact_sell, confidence_score
        )
        
        # Execution time estimation
        execution_time_ms = 500 + (1000 if max_trade_usd > 10000 else 0)
        
        return EnhancedArbitrageCalculation(
            token_pair=pair,
            buy_dex=buy_dex,
            sell_dex=sell_dex,
            buy_price=buy_price,
            sell_price=sell_price,
            spread_percent=spread_percent,
            potential_profit=gross_profit,
            net_profit=net_profit_after_fees,
            max_trade_amount=max_trade_usd,
            price_impact_buy=price_impact_buy * 100,
            price_impact_sell=price_impact_sell * 100,
            slippage_tolerance=self.max_slippage * 100,
            gas_cost_usd=gas_cost_usd,
            execution_time_ms=execution_time_ms,
            confidence_score=confidence_score,
            risk_level=risk_level,
            volume_24h_buy=buy_volume,
            volume_24h_sell=sell_volume,
            liquidity_buy=buy_liquidity,
            liquidity_sell=sell_liquidity,
            gross_profit=gross_profit,
            net_profit_after_fees=net_profit_after_fees,
            roi_percent=roi_percent,
            annualized_roi=annualized_roi,
            timestamp=datetime.now()
        )
    
    def _estimate_price_impact(self, trade_size: float, liquidity: float) -> float:
        """Estimate price impact based on trade size and liquidity"""
        if liquidity <= 0:
            return 0.1  # 10% impact if no liquidity data
        
        impact_ratio = trade_size / liquidity
        if impact_ratio < 0.01:
            return impact_ratio * 0.5  # Low impact
        elif impact_ratio < 0.05:
            return impact_ratio * 1.0  # Medium impact
        else:
            return min(impact_ratio * 2.0, 0.15)  # High impact, capped at 15%
    
    def _calculate_confidence_score(self, spread_percent: float, buy_liquidity: float,
                                  sell_liquidity: float, buy_volume: float, sell_volume: float) -> float:
        """Calculate confidence score for the opportunity"""
        score = 0.0
        
        # Spread score (higher spread = higher confidence up to a point)
        if 0.5 <= spread_percent <= 2.0:
            score += 0.3
        elif 2.0 < spread_percent <= 5.0:
            score += 0.2
        elif spread_percent > 5.0:
            score += 0.1  # Too high might be suspicious
        
        # Liquidity score
        min_liquidity = min(buy_liquidity, sell_liquidity)
        if min_liquidity > 100000:
            score += 0.3
        elif min_liquidity > 50000:
            score += 0.2
        elif min_liquidity > 10000:
            score += 0.1
        
        # Volume score
        min_volume = min(buy_volume, sell_volume)
        if min_volume > 1000000:
            score += 0.3
        elif min_volume > 500000:
            score += 0.2
        elif min_volume > 100000:
            score += 0.1
        
        # Balance score (similar liquidity on both sides)
        liquidity_ratio = min(buy_liquidity, sell_liquidity) / max(buy_liquidity, sell_liquidity) if max(buy_liquidity, sell_liquidity) > 0 else 0
        score += liquidity_ratio * 0.1
        
        return min(score, 1.0)
    
    def _assess_risk_level(self, spread_percent: float, total_price_impact: float, confidence_score: float) -> str:
        """Assess risk level for the opportunity"""
        if confidence_score > 0.8 and spread_percent > 1.0 and total_price_impact < 0.02:
            return "low"
        elif confidence_score > 0.6 and spread_percent > 0.5 and total_price_impact < 0.05:
            return "medium"
        else:
            return "high"
    
    def calculate_market_summary(self, opportunities: List[EnhancedArbitrageCalculation]) -> Dict:
        """Calculate market summary statistics"""
        if not opportunities:
            return {
                'total_opportunities': 0,
                'total_potential_profit': 0,
                'average_spread': 0,
                'best_opportunity': None,
                'risk_distribution': {'low': 0, 'medium': 0, 'high': 0},
                'dex_performance': {}
            }
        
        total_profit = sum(opp.net_profit for opp in opportunities)
        avg_spread = sum(opp.spread_percent for opp in opportunities) / len(opportunities)
        best_opp = max(opportunities, key=lambda x: Any: Any: x.net_profit)
        
        # Risk distribution
        risk_dist = {'low': 0, 'medium': 0, 'high': 0}
        for opp in opportunities:
            risk_dist[opp.risk_level] += 1
        
        # DEX performance
        dex_perf = {}
        for opp in opportunities:
            for dex in [opp.buy_dex, opp.sell_dex]:
                if dex not in dex_perf:
                    dex_perf[dex] = {'count': 0, 'total_profit': 0, 'avg_spread': 0}
                dex_perf[dex]['count'] += 1
                dex_perf[dex]['total_profit'] += opp.net_profit / 2  # Split between buy and sell
        
        return {
            'total_opportunities': len(opportunities),
            'total_potential_profit': round(total_profit, 2),
            'average_spread': round(avg_spread, 2),
            'best_opportunity': {
                'pair': best_opp.token_pair,
                'profit': round(best_opp.net_profit, 2),
                'spread': round(best_opp.spread_percent, 2),
                'risk': best_opp.risk_level
            },
            'risk_distribution': risk_dist,
            'dex_performance': dex_perf
        }

# Global calculator instance
calculator = EnhancedDEXCalculator()
enhanced_opportunities = []
market_summary = {}

# Routes
@app.route('/')
def index():
    """Render enhanced DEX calculations dashboard"""
    return render_template('enhanced_dex_dashboard.html')

@app.route('/api/enhanced-calculations')
def get_enhanced_calculations():
    """Get enhanced arbitrage calculations"""
    global enhanced_opportunities, market_summary
    
    try:
        # Fetch price data from DEX monitor
        response = requests.get('http://localhost:8008/dashboard-data', timeout=5)
        if response.status_code == 200:
            price_data = response.json().get('data', {})
            
            # Calculate enhanced opportunities
            enhanced_opportunities = calculator.calculate_enhanced_arbitrage(price_data)
            market_summary = calculator.calculate_market_summary(enhanced_opportunities)
            
            return jsonify({
                'success': True,
                'opportunities': [
                    {
                        'token_pair': opp.token_pair,
                        'buy_dex': opp.buy_dex,
                        'sell_dex': opp.sell_dex,
                        'buy_price': round(opp.buy_price, 6),
                        'sell_price': round(opp.sell_price, 6),
                        'spread_percent': round(opp.spread_percent, 2),
                        'potential_profit': round(opp.potential_profit, 2),
                        'net_profit': round(opp.net_profit, 2),
                        'max_trade_amount': round(opp.max_trade_amount, 2),
                        'price_impact_buy': round(opp.price_impact_buy, 2),
                        'price_impact_sell': round(opp.price_impact_sell, 2),
                        'gas_cost_usd': round(opp.gas_cost_usd, 4),
                        'confidence_score': round(opp.confidence_score, 2),
                        'risk_level': opp.risk_level,
                        'roi_percent': round(opp.roi_percent, 2),
                        'annualized_roi': round(opp.annualized_roi, 2),
                        'execution_time_ms': opp.execution_time_ms,
                        'liquidity_buy': round(opp.liquidity_buy, 2),
                        'liquidity_sell': round(opp.liquidity_sell, 2),
                        'volume_24h_buy': round(opp.volume_24h_buy, 2),
                        'volume_24h_sell': round(opp.volume_24h_sell, 2),
                        'timestamp': opp.timestamp.isoformat()
                    }
                    for opp in enhanced_opportunities
                ],
                'summary': market_summary,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'success': False, 'error': 'DEX monitor unavailable'}), 503
            
    except Exception as e:
        logger.error(f"Error getting enhanced calculations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market-analysis')
def get_market_analysis():
    """Get detailed market analysis"""
    try:
        analysis = {
            'market_conditions': {
                'volatility_index': calculate_volatility_index(),
                'liquidity_index': calculate_liquidity_index(),
                'opportunity_index': len(enhanced_opportunities),
                'market_efficiency': calculate_market_efficiency()
            },
            'performance_metrics': {
                'total_volume_monitored': sum(opp.volume_24h_buy + opp.volume_24h_sell for opp in enhanced_opportunities),
                'total_liquidity_monitored': sum(opp.liquidity_buy + opp.liquidity_sell for opp in enhanced_opportunities),
                'average_execution_time': sum(opp.execution_time_ms for opp in enhanced_opportunities) / len(enhanced_opportunities) if enhanced_opportunities else 0,
                'success_probability': sum(opp.confidence_score for opp in enhanced_opportunities) / len(enhanced_opportunities) if enhanced_opportunities else 0
            },
            'risk_analysis': {
                'high_risk_opportunities': len([opp for opp in enhanced_opportunities if opp.risk_level == 'high']),
                'medium_risk_opportunities': len([opp for opp in enhanced_opportunities if opp.risk_level == 'medium']),
                'low_risk_opportunities': len([opp for opp in enhanced_opportunities if opp.risk_level == 'low']),
                'average_price_impact': sum(opp.price_impact_buy + opp.price_impact_sell for opp in enhanced_opportunities) / (2 * len(enhanced_opportunities)) if enhanced_opportunities else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error getting market analysis: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_volatility_index():
    """Calculate market volatility index"""
    if not enhanced_opportunities:
        return 0
    spreads = [opp.spread_percent for opp in enhanced_opportunities]
    avg_spread = sum(spreads) / len(spreads)
    return min(avg_spread * 10, 100)  # Scale to 0-100

def calculate_liquidity_index():
    """Calculate market liquidity index"""
    if not enhanced_opportunities:
        return 0
    avg_liquidity = sum(opp.liquidity_buy + opp.liquidity_sell for opp in enhanced_opportunities) / (2 * len(enhanced_opportunities))
    return min(avg_liquidity / 10000, 100)  # Scale to 0-100

def calculate_market_efficiency():
    """Calculate market efficiency score"""
    if not enhanced_opportunities:
        return 100
    high_spread_count = len([opp for opp in enhanced_opportunities if opp.spread_percent > 2.0])
    efficiency = max(0, 100 - (high_spread_count * 10))
    return efficiency

# Background task to update calculations
def update_calculations():
    """Background task to update enhanced calculations"""
    while True:
        try:
            time.sleep(15)  # Update every 15 seconds
            
            # Trigger calculation update
            with app.test_request_context():
                response = get_enhanced_calculations()
                if hasattr(response, 'status_code') and response.status_code == 200:
                    # Emit update to connected clients
                    socketio.emit('calculations_update', {
                        'opportunities': enhanced_opportunities[:10],  # Top 10
                        'summary': market_summary,
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Error in background calculation update: {e}")
            time.sleep(30)  # Wait longer on error

if __name__ == "__main__":
    # Start background calculation updates
    calc_thread = threading.Thread(target=update_calculations, daemon=True)
    calc_thread.start()
    
    print("🚀 Starting Enhanced DEX Calculations Dashboard on http://localhost:8005")
    print("📊 Features:")
    print("  • Advanced arbitrage calculations with risk analysis")
    print("  • Real-time profit and ROI calculations")
    print("  • Price impact and slippage analysis")
    print("  • Market efficiency and confidence scoring")
    print("  • Enhanced visualization and alerts")
    
    socketio.run(app, debug=False, port=8005, host='0.0.0.0')
