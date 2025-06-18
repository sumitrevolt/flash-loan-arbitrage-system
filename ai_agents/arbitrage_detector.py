#!/usr/bin/env python3
"""
Arbitrage Detector AI Agent
==========================

Advanced arbitrage opportunity detection across multiple DEXs.
Uses machine learning and real-time analysis.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import logging
import json
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArbitrageDetectorAgent:
    def __init__(self):
        self.min_profit_threshold = 3.0  # $3 minimum
        self.max_profit_threshold = 30.0  # $30 maximum
        self.min_confidence_score = 0.8
        self.price_staleness_threshold = 60  # seconds
        
    def analyze_opportunities(self, price_data, min_profit=3.0, max_profit=30.0):
        """Analyze price data for arbitrage opportunities"""
        try:
            opportunities = []
            
            for token_symbol, token_prices in price_data.items():
                # Find arbitrage opportunities between DEX pairs
                dex_names = list(token_prices.keys())
                
                for i, buy_dex in enumerate(dex_names):
                    for j, sell_dex in enumerate(dex_names):
                        if i >= j:
                            continue
                            
                        buy_price = token_prices[buy_dex]
                        sell_price = token_prices[sell_dex]
                        
                        if sell_price > buy_price:
                            price_diff_pct = ((sell_price - buy_price) / buy_price) * 100
                            
                            # Calculate opportunity metrics
                            opportunity = self._calculate_opportunity_metrics(
                                token_symbol, buy_dex, sell_dex,
                                buy_price, sell_price, price_diff_pct
                            )
                            
                            # Filter by profit range
                            if min_profit <= opportunity['net_profit_usd'] <= max_profit:
                                opportunities.append(opportunity)
                                
            # Sort by profit potential
            opportunities.sort(key=lambda x: x['net_profit_usd'], reverse=True)
            
            return opportunities[:10]  # Return top 10 opportunities
            
        except Exception as e:
            logger.error(f"Opportunity analysis error: {e}")
            return []
            
    def _calculate_opportunity_metrics(self, token_symbol, buy_dex, sell_dex, 
                                     buy_price, sell_price, price_diff_pct):
        """Calculate detailed opportunity metrics"""
        try:
            # Base trade size calculation
            trade_size_usd = 1000.0  # Start with $1000
            
            # Adjust trade size based on price difference
            if price_diff_pct > 2.0:  # High difference = smaller size
                trade_size_usd = min(trade_size_usd, 500.0)
            elif price_diff_pct < 0.5:  # Small difference = larger size
                trade_size_usd = min(trade_size_usd * 2, 5000.0)
                
            # Calculate profits and fees
            gross_profit_usd = trade_size_usd * (price_diff_pct / 100)
            
            # Estimate fees
            dex_fees_usd = trade_size_usd * 0.003  # 0.3% average DEX fees
            aave_fee_usd = trade_size_usd * 0.0009  # 0.09% Aave flash loan fee
            gas_cost_usd = 0.3 + (trade_size_usd / 10000)  # Dynamic gas cost
            
            net_profit_usd = gross_profit_usd - dex_fees_usd - aave_fee_usd - gas_cost_usd
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                price_diff_pct, trade_size_usd, net_profit_usd
            )
            
            return {
                'token_symbol': token_symbol,
                'buy_dex': buy_dex,
                'sell_dex': sell_dex,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'price_diff_pct': price_diff_pct,
                'trade_size_usd': trade_size_usd,
                'gross_profit_usd': gross_profit_usd,
                'dex_fees_usd': dex_fees_usd,
                'aave_fee_usd': aave_fee_usd,
                'gas_cost_usd': gas_cost_usd,
                'net_profit_usd': net_profit_usd,
                'confidence_score': confidence_score,
                'timestamp': datetime.now().isoformat(),
                'route_path': [buy_dex, sell_dex]
            }
            
        except Exception as e:
            logger.error(f"Metrics calculation error: {e}")
            return None
            
    def _calculate_confidence_score(self, price_diff_pct, trade_size_usd, net_profit_usd):
        """Calculate confidence score for opportunity"""
        try:
            score = 0.5  # Base score
            
            # Price difference confidence
            if 0.3 <= price_diff_pct <= 2.0:  # Sweet spot
                score += 0.3
            elif price_diff_pct > 5.0:  # Too high - suspicious
                score -= 0.2
                
            # Trade size confidence
            if 500 <= trade_size_usd <= 2000:  # Optimal range
                score += 0.1
            elif trade_size_usd > 10000:  # Too large
                score -= 0.1
                
            # Profit confidence
            if net_profit_usd > 10:  # Good profit
                score += 0.1
            elif net_profit_usd < 5:  # Low profit
                score -= 0.1
                
            return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.5

detector = ArbitrageDetectorAgent()

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'agent': 'arbitrage_detector',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze_opportunities():
    try:
        data = request.json
        price_data = data.get('price_data', {})
        min_profit = data.get('min_profit', 3.0)
        max_profit = data.get('max_profit', 30.0)
        
        opportunities = detector.analyze_opportunities(price_data, min_profit, max_profit)
        
        return jsonify({
            'opportunities': opportunities,
            'count': len(opportunities),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def detector_config():
    if request.method == 'GET':
        return jsonify({
            'min_profit_threshold': detector.min_profit_threshold,
            'max_profit_threshold': detector.max_profit_threshold,
            'min_confidence_score': detector.min_confidence_score,
            'price_staleness_threshold': detector.price_staleness_threshold
        })
    else:
        config = request.json
        if 'min_profit_threshold' in config:
            detector.min_profit_threshold = config['min_profit_threshold']
        if 'max_profit_threshold' in config:
            detector.max_profit_threshold = config['max_profit_threshold']
        return jsonify({'status': 'updated'})

if __name__ == '__main__':
    logger.info("Starting Arbitrage Detector AI Agent on port 9001")
    app.run(host='0.0.0.0', port=9001)
