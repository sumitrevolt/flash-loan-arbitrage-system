"""
Comprehensive profit calculator for Flash Loan Arbitrage System.
Calculates net profit after all fees and costs.
"""

import logging
from typing import Dict, Any, Tuple
from decimal import Decimal

class ProfitCalculator:
    """Calculates accurate profits including all fees."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def calculate_net_profit(
        self,
        trade_amount_usd: float,
        buy_price: float,
        sell_price: float,
        gas_price_gwei: float,
        gas_used: int = 750000
    ) -> Dict[str, float]:
        """Calculate net profit after all fees."""
        
        # Price difference
        price_diff_percentage = ((sell_price - buy_price) / buy_price) * 100
        
        # Gross profit
        gross_profit = trade_amount_usd * (price_diff_percentage / 100)
        
        # Calculate all fees
        aave_fee = trade_amount_usd * 0.0009  # 0.09%
        buy_dex_fee = trade_amount_usd * 0.003  # 0.3%
        sell_dex_fee = trade_amount_usd * 0.003  # 0.3%
        
        # Gas cost (assuming MATIC at $0.85)
        gas_cost_usd = (gas_used * gas_price_gwei * 1e-9) * 0.85
        
        # Slippage cost (estimated 0.1% on each side)
        slippage_cost = trade_amount_usd * 0.002  # 0.2% total
        
        # Total costs
        total_costs = aave_fee + buy_dex_fee + sell_dex_fee + gas_cost_usd + slippage_cost
        
        # Net profit
        net_profit = gross_profit - total_costs
        
        # ROI percentage
        roi_percentage = (net_profit / trade_amount_usd) * 100
        
        return {
            "gross_profit": gross_profit,
            "aave_fee": aave_fee,
            "buy_dex_fee": buy_dex_fee,
            "sell_dex_fee": sell_dex_fee,
            "gas_cost": gas_cost_usd,
            "slippage_cost": slippage_cost,
            "total_costs": total_costs,
            "net_profit": net_profit,
            "roi_percentage": roi_percentage,
            "profitable": net_profit > 0
        }
