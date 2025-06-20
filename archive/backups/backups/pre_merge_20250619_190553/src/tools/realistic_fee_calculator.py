#!/usr/bin/env python3
"""
Realistic Fee Calculator for Arbitrage Opportunities
Calculates all fees involved in flash loan arbitrage including:
- DEX trading fees
- Gas costs
- Flash loan fees
- Slippage
"""

import asyncio
import aiohttp
from typing import Optional
import logging

class RealisticFeeCalculator:
    def __init__(self):
        # Fee configurations
        self.dex_fees = {
            'QuickSwap': 0.003,      # 0.3%
            'SushiSwap': 0.003,      # 0.3%
            'Uniswap V3': 0.0025,    # 0.25% average
            'Balancer': 0.0025,      # 0.25%
            'Curve': 0.0004          # 0.04%
        }
        
        # Aave flash loan fee
        self.flash_loan_fee = 0.0009  # 0.09%
        
        # Gas estimates (in gas units)
        self.gas_estimates = {
            'flash_loan': 350000,     # Flash loan + arbitrage execution
            'approve': 50000,         # Token approval
            'swap': 150000           # Single swap
        }
        
        # Slippage settings
        self.default_slippage = 0.005  # 0.5%
        
        # Real-time price fetching
        self.matic_price_usd = 0.6  # Fallback MATIC price
        self.last_price_update = 0
        self.price_cache_duration = 300  # 5 minutes
        self.logger = logging.getLogger(__name__)
    
    async def update_matic_price(self) -> Optional[float]:
        """Fetch real-time MATIC price from CoinGecko API"""
        import time
        
        # Check if cache is still valid
        current_time = time.time()
        if current_time - self.last_price_update < self.price_cache_duration:
            return self.matic_price_usd
        
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=matic-network&vs_currencies=usd"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        new_price = data.get('matic-network', {}).get('usd')
                        
                        if new_price and isinstance(new_price, (int, float)):
                            self.matic_price_usd = float(new_price)
                            self.last_price_update = current_time
                            self.logger.info(f"Updated MATIC price: ${self.matic_price_usd:.4f}")
                            return self.matic_price_usd
                        
        except Exception as e:
            self.logger.warning(f"Failed to fetch MATIC price, using cached value: {e}")
            
        return self.matic_price_usd
    
    async def is_arbitrage_profitable(self, trade_amount_usd, price_diff_pct, buy_dex, sell_dex, gas_price_gwei, min_roi_threshold):
        """
        Check if an arbitrage opportunity is profitable after all fees
        
        Args:
            trade_amount_usd: Trade size in USD
            price_diff_pct: Price difference percentage
            buy_dex: DEX to buy from
            sell_dex: DEX to sell to
            gas_price_gwei: Current gas price in Gwei
            min_roi_threshold: Minimum ROI threshold percentage
        
        Returns:
            tuple: (is_profitable: bool, analysis: dict)
        """
        
        # Update MATIC price for accurate gas cost calculation
        await self.update_matic_price()
        
        # Calculate gross profit
        gross_profit = trade_amount_usd * (price_diff_pct / 100)
        
        # Calculate DEX fees
        buy_fee_rate = self.dex_fees.get(buy_dex, 0.003)
        sell_fee_rate = self.dex_fees.get(sell_dex, 0.003)
        total_dex_fee_rate = buy_fee_rate + sell_fee_rate
        dex_fees = trade_amount_usd * total_dex_fee_rate
        
        # Calculate slippage cost
        slippage_cost = trade_amount_usd * self.default_slippage
        
        # Calculate gas costs with real-time MATIC price
        total_gas_units = self.gas_estimates['flash_loan']
        gas_cost_matic = (gas_price_gwei * total_gas_units) / 1e9
        gas_cost_usd = gas_cost_matic * self.matic_price_usd
        
        # Calculate flash loan fee
        flash_loan_fee = trade_amount_usd * self.flash_loan_fee
        
        # Calculate total costs
        total_costs = dex_fees + slippage_cost + gas_cost_usd + flash_loan_fee
        
        # Calculate net profit
        net_profit = gross_profit - total_costs
        
        # Calculate actual ROI
        actual_roi = (net_profit / trade_amount_usd) * 100
        
        # Check profitability
        is_profitable = net_profit > 0 and actual_roi >= min_roi_threshold
        
        # Return analysis
        analysis = {
            'gross_profit': gross_profit,
            'total_costs': total_costs,
            'net_profit': net_profit,
            'actual_roi': actual_roi,
            'dex_fees': dex_fees,
            'slippage_cost': slippage_cost,
            'gas_cost_usd': gas_cost_usd,
            'flash_loan_fee': flash_loan_fee,
            'cost_breakdown': {
                'dex_fees': dex_fees,
                'slippage': slippage_cost,
                'gas_fees': gas_cost_usd,
                'flash_loan_fee': flash_loan_fee
            }
        }
        
        return is_profitable, analysis
    
    def is_arbitrage_profitable_sync(self, trade_amount_usd, price_diff_pct, buy_dex, sell_dex, gas_price_gwei, min_roi_threshold):
        """
        Synchronous wrapper for backwards compatibility
        Note: This will use cached MATIC price, for real-time price use async version
        """
        return asyncio.run(self.is_arbitrage_profitable(
            trade_amount_usd, price_diff_pct, buy_dex, sell_dex, gas_price_gwei, min_roi_threshold
        ))
    
    def calculate_minimum_profit_threshold(self, gas_price_gwei):
        """
        Calculate minimum profit needed to cover all fixed costs
        
        Args:
            gas_price_gwei: Current gas price in Gwei
        
        Returns:
            float: Minimum profit threshold in USD
        """
        # Calculate fixed gas cost
        total_gas_units = self.gas_estimates['flash_loan']
        gas_cost_matic = (gas_price_gwei * total_gas_units) / 1e9
        gas_cost_usd = gas_cost_matic * self.matic_price_usd
        
        # Add buffer for safety (20%)
        safety_buffer = 1.2
        
        return gas_cost_usd * safety_buffer
    
    def calculate_optimal_trade_size(self, price_diff_pct, buy_dex, sell_dex, gas_price_gwei):
        """
        Calculate optimal trade size for maximum profit
        
        Args:
            price_diff_pct: Price difference percentage
            buy_dex: DEX to buy from
            sell_dex: DEX to sell to
            gas_price_gwei: Current gas price in Gwei
        
        Returns:
            float: Optimal trade size in USD
        """
        # Get fee rates
        buy_fee_rate = self.dex_fees.get(buy_dex, 0.003)
        sell_fee_rate = self.dex_fees.get(sell_dex, 0.003)
        total_fee_rate = buy_fee_rate + sell_fee_rate + self.flash_loan_fee + self.default_slippage
        
        # Calculate gas cost
        total_gas_units = self.gas_estimates['flash_loan']
        gas_cost_matic = (gas_price_gwei * total_gas_units) / 1e9
        gas_cost_usd = gas_cost_matic * self.matic_price_usd
        
        # Calculate optimal size
        # Formula: optimal_size = gas_cost / (price_diff% - total_fees%)
        net_profit_rate = (price_diff_pct / 100) - total_fee_rate
        
        if net_profit_rate <= 0:
            return 0  # Not profitable at any size
        
        # Optimal size where profit is maximized
        optimal_size = gas_cost_usd / (net_profit_rate * 0.1)  # 10% of net profit for gas
        
        # Cap at reasonable limits
        min_size = 500  # $500 minimum
        max_size = 10000  # $10,000 maximum
        
        return max(min_size, min(optimal_size, max_size))
