#!/usr/bin/env python3
"""
Risk Manager AI Agent
====================

Advanced risk management for arbitrage opportunities.
Provides intelligent risk assessment and position sizing.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import logging
import json
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskManagerAgent:
    def __init__(self):
        self.max_position_size = 50000  # $50k max
        self.max_gas_price_gwei = 100
        self.min_liquidity_ratio = 0.1
        self.max_slippage_tolerance = 0.5  # 0.5%
        
    def assess_opportunity(self, opportunity_data):
        """Comprehensive risk assessment"""
        try:
            risk_score = 0
            risk_factors = []
            
            # Gas price risk
            gas_price = opportunity_data.get('gas_cost_usd', 0)
            profit = opportunity_data.get('net_profit_usd', 0)
            
            if gas_price > profit * 0.3:  # Gas > 30% of profit
                risk_score += 30
                risk_factors.append("High gas cost relative to profit")
                
            # Market volatility risk
            price_diff = opportunity_data.get('price_diff_pct', 0)
            if price_diff > 5:  # > 5% price difference might be stale
                risk_score += 20
                risk_factors.append("High price difference - potential stale data")
                
            # Liquidity risk
            trade_size = opportunity_data.get('trade_size_usd', 0)
            if trade_size > self.max_position_size:
                risk_score += 40
                risk_factors.append("Trade size exceeds maximum")
                
            # Time-based risk
            timestamp = opportunity_data.get('timestamp', '')
            if timestamp:
                try:
                    opp_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    age_seconds = (datetime.now() - opp_time.replace(tzinfo=None)).total_seconds()
                    if age_seconds > 30:  # Opportunity older than 30 seconds
                        risk_score += 25
                        risk_factors.append("Opportunity data is stale")
                except:
                    pass
            
            # Overall risk assessment
            approved = risk_score < 50  # Approve if risk score < 50
            
            return {
                'approved': approved,
                'risk_score': risk_score,
                'risk_factors': risk_factors,
                'confidence': max(0, (100 - risk_score) / 100),
                'recommended_position_size': min(trade_size, self.max_position_size * 0.8) if approved else 0
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {
                'approved': False,
                'risk_score': 100,
                'risk_factors': ['Risk assessment failed'],
                'confidence': 0,
                'recommended_position_size': 0
            }

risk_manager = RiskManagerAgent()

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'agent': 'risk_manager',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/assess', methods=['POST'])
def assess_opportunity():
    try:
        opportunity_data = request.json
        assessment = risk_manager.assess_opportunity(opportunity_data)
        return jsonify(assessment)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def risk_config():
    if request.method == 'GET':
        return jsonify({
            'max_position_size': risk_manager.max_position_size,
            'max_gas_price_gwei': risk_manager.max_gas_price_gwei,
            'min_liquidity_ratio': risk_manager.min_liquidity_ratio,
            'max_slippage_tolerance': risk_manager.max_slippage_tolerance
        })
    else:
        config = request.json
        if 'max_position_size' in config:
            risk_manager.max_position_size = config['max_position_size']
        if 'max_gas_price_gwei' in config:
            risk_manager.max_gas_price_gwei = config['max_gas_price_gwei']
        return jsonify({'status': 'updated'})

if __name__ == '__main__':
    logger.info("Starting Risk Manager AI Agent on port 9002")
    app.run(host='0.0.0.0', port=9002)
