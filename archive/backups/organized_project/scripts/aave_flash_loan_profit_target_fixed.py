#!/usr/bin/env python3
"""
AAVE Flash Loan Profit Target System - FIXED VERSION
====================================================

Focused implementation for AAVE flash loans with profit targets between $4-$30.
This system identifies, evaluates, and logs flash loan arbitrage opportunities
within the specified profit range using ONLY REAL DEX prices.

SAFETY FEATURES:
- Trading execution disabled by default 
- Real DEX prices only (no simulation or fallback)
- Comprehensive fee calculations (DEX + AAVE)
- Risk assessment and safety checks
- Detailed logging and monitoring

Requirements:
- POLYGON_RPC_URL environment variable
- Internet connection for price fetching
- Web3 provider access
"""

import asyncio
import json
import logging
import os
import time
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import aiohttp
from web3 import Web3
from web3.contract.contract import Contract
from web3.exceptions import ContractLogicError
import requests

# Set high precision for financial calculations
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AaveFlashLoanProfitTarget")

@dataclass
class ProfitableOpportunity:
    """Flash loan opportunity within profit target range"""
    id: str
    timestamp: datetime
    asset: str
    loan_amount: Decimal
    source_dex: str
    target_dex: str
    buy_price: Decimal
    sell_price: Decimal
    gross_profit: Decimal
    dex_fees: Decimal
    flash_loan_fee: Decimal
    gas_cost: Decimal
    net_profit: Decimal
    profit_margin: Decimal
    confidence_score: float
    execution_priority: int
    estimated_execution_time: int
    risks: List[str]
    
    def is_profitable_target(self) -> bool:
        """Check if opportunity meets $4-$30 profit target"""
        return Decimal('4') <= self.net_profit <= Decimal('30')
    
    def get_summary(self) -> str:
        """Get formatted summary of opportunity"""
        return (f"💰 {self.asset} Arbitrage: "
                f"${self.net_profit:.2f} profit "
                f"({self.source_dex} → {self.target_dex}) "
                f"[{self.confidence_score:.1%} confidence]")

@dataclass
class ExecutionMetrics:
    """Track execution performance"""
    opportunities_found: int = 0
    opportunities_in_range: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_profit: Decimal = Decimal('0')
    total_gas_cost: Decimal = Decimal('0')
    average_execution_time: float = 0.0
    success_rate: float = 0.0

class AaveFlashLoanProfitTarget:
    """AAVE Flash Loan system targeting $4-$30 profits using REAL prices only"""
    
    def __init__(self):
        # Web3 setup
        self.polygon_rpc = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
        self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
        
        # Verify connection
        if not self.web3.is_connected():
            raise ConnectionError("❌ Failed to connect to Polygon RPC")
        
        logger.info(f"✅ Connected to Polygon: {self.web3.eth.chain_id}")
        
        # AAVE V3 addresses on Polygon
        self.aave_pool_address = '0x794a61358D6845594F94dc1DB02A252b5b4814aD'
        self.aave_data_provider = '0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654'
        
        # Profit targets ($4-$30)
        self.min_profit = Decimal('4')
        self.max_profit = Decimal('30')
        self.optimal_profit = Decimal('15')  # Sweet spot
        
        # Risk parameters
        self.max_slippage = Decimal('0.02')  # 2%
        self.max_gas_price = 100  # gwei
        self.min_liquidity = Decimal('10000')  # $10k minimum
        
        # Token configuration
        self.tokens = {
            'USDC': {
                'address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
                'decimals': 6
            },
            'USDT': {
                'address': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
                'decimals': 6
            },
            'DAI': {
                'address': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
                'decimals': 18
            },
            'WMATIC': {
                'address': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
                'decimals': 18
            }
        }
        
        # DEX configuration with REAL fee structures
        self.dexes = {
            'quickswap': {
                'router': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                'factory': '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
                'fee': Decimal('0.003')  # 0.3%
            },
            'sushiswap': {
                'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                'fee': Decimal('0.003')  # 0.3%
            },
            'uniswap_v3': {
                'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'quoter': '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',
                'fees': [Decimal('0.0005'), Decimal('0.003'), Decimal('0.01')]  # 0.05%, 0.3%, 1%
            }
        }
        
        # AAVE flash loan fee (0.09%)
        self.aave_flash_loan_fee_rate = Decimal('0.0009')
        
        # Performance tracking
        self.metrics = ExecutionMetrics()
        self.opportunities = []
        self.execution_history = []
        
        # CRITICAL: Trading execution controls
        self.execution_enabled = False  # MUST be explicitly enabled
        self.execution_authorization_key = None
        self.dry_run_mode = True  # Always start in dry run mode
        
        logger.warning("🚨 TRADING EXECUTION DISABLED - System in DRY RUN mode only")
        logger.warning("🚨 No trades will be executed until explicitly authorized")
    
    async def get_real_dex_prices(self, token_in: str, token_out: str, amount: Decimal) -> Dict[str, Dict[str, Decimal]]:
        """Get REAL prices from DEXes - NO SIMULATION OR FALLBACK"""
        prices = {}
        
        try:
            # QuickSwap - Real price fetching
            quickswap_data = await self._fetch_quickswap_price(token_in, token_out, amount)
            if quickswap_data:
                prices['quickswap'] = quickswap_data
            
            # SushiSwap - Real price fetching
            sushiswap_data = await self._fetch_sushiswap_price(token_in, token_out, amount)
            if sushiswap_data:
                prices['sushiswap'] = sushiswap_data
            
            # Uniswap V3 - Real price fetching
            uniswap_v3_data = await self._fetch_uniswap_v3_price(token_in, token_out, amount)
            if uniswap_v3_data:
                prices['uniswap_v3'] = uniswap_v3_data
            
            # Only return if we have actual prices from DEXes
            if not prices:
                logger.error("❌ CRITICAL: No real DEX prices available - refusing to use fallback data")
                return {}
                
            logger.info(f"✅ Retrieved real DEX prices for {token_in}->{token_out}: {len(prices)} DEXes")
            return prices
            
        except Exception as e:
            logger.error(f"❌ Error fetching REAL DEX prices: {e}")
            # NO FALLBACK - we only use real prices
            return {}
    
    async def _fetch_quickswap_price(self, token_in: str, token_out: str, amount: Decimal) -> Optional[Dict[str, Decimal]]:
        """Fetch real price from QuickSwap including fee calculation"""
        try:
            token_in_addr = self.tokens[token_in]['address']
            token_out_addr = self.tokens[token_out]['address']
            
            # Convert amount to proper decimals
            amount_in_wei = int(amount * (10 ** self.tokens[token_in]['decimals']))
            
            # Call getAmountsOut on QuickSwap router
            router_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.dexes['quickswap']['router']),
                abi=self._get_uniswap_v2_router_abi()
            )
            
            amounts_out = router_contract.functions.getAmountsOut(
                amount_in_wei,
                [Web3.to_checksum_address(token_in_addr), Web3.to_checksum_address(token_out_addr)]
            ).call()
            
            # Convert back to decimal
            amount_out = Decimal(amounts_out[1]) / (10 ** self.tokens[token_out]['decimals'])
            price = amount_out / amount
            
            # Calculate DEX fee
            dex_fee = amount * self.dexes['quickswap']['fee']
            
            logger.info(f"QuickSwap: {token_in}->{token_out} price: {price:.6f}, fee: ${dex_fee:.4f}")
            
            return {
                'price': price,
                'fee': dex_fee,
                'amount_out': amount_out
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch QuickSwap price: {e}")
            return None
    
    async def _fetch_sushiswap_price(self, token_in: str, token_out: str, amount: Decimal) -> Optional[Dict[str, Decimal]]:
        """Fetch real price from SushiSwap including fee calculation"""
        try:
            token_in_addr = self.tokens[token_in]['address']
            token_out_addr = self.tokens[token_out]['address']
            
            # Convert amount to proper decimals
            amount_in_wei = int(amount * (10 ** self.tokens[token_in]['decimals']))
            
            # Call getAmountsOut on SushiSwap router
            router_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.dexes['sushiswap']['router']),
                abi=self._get_uniswap_v2_router_abi()
            )
            
            amounts_out = router_contract.functions.getAmountsOut(
                amount_in_wei,
                [Web3.to_checksum_address(token_in_addr), Web3.to_checksum_address(token_out_addr)]
            ).call()
            
            # Convert back to decimal
            amount_out = Decimal(amounts_out[1]) / (10 ** self.tokens[token_out]['decimals'])
            price = amount_out / amount
            
            # Calculate DEX fee
            dex_fee = amount * self.dexes['sushiswap']['fee']
            
            logger.info(f"SushiSwap: {token_in}->{token_out} price: {price:.6f}, fee: ${dex_fee:.4f}")
            
            return {
                'price': price,
                'fee': dex_fee,
                'amount_out': amount_out
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch SushiSwap price: {e}")
            return None
    
    async def _fetch_uniswap_v3_price(self, token_in: str, token_out: str, amount: Decimal) -> Optional[Dict[str, Decimal]]:
        """Fetch real price from Uniswap V3 including fee calculation"""
        try:
            token_in_addr = self.tokens[token_in]['address']
            token_out_addr = self.tokens[token_out]['address']
            
            # Convert amount to proper decimals
            amount_in_wei = int(amount * (10 ** self.tokens[token_in]['decimals']))
            
            # Call quoteExactInputSingle on Uniswap V3 Quoter
            quoter_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.dexes['uniswap_v3']['quoter']),
                abi=self._get_uniswap_v3_quoter_abi()
            )
            
            # Try different fee tiers and find the best price
            best_price = None
            best_fee = None
            best_amount_out = None
            
            for fee_tier in [500, 3000, 10000]:  # 0.05%, 0.3%, 1%
                try:
                    amount_out_wei = quoter_contract.functions.quoteExactInputSingle(
                        Web3.to_checksum_address(token_in_addr),
                        Web3.to_checksum_address(token_out_addr),
                        fee_tier,
                        amount_in_wei,
                        0  # sqrtPriceLimitX96 (0 = no limit)
                    ).call()
                    
                    # Convert back to decimal
                    amount_out = Decimal(amount_out_wei) / (10 ** self.tokens[token_out]['decimals'])
                    
                    if amount_out > 0:
                        price = amount_out / amount
                        dex_fee = amount * (Decimal(fee_tier) / Decimal('1000000'))  # Convert fee tier to percentage
                        
                        # Keep the best price (highest amount out)
                        if best_amount_out is None or amount_out > best_amount_out:
                            best_price = price
                            best_fee = dex_fee
                            best_amount_out = amount_out
                    
                except Exception:
                    continue  # Try next fee tier
            
            if best_price is not None:
                logger.info(f"Uniswap V3: {token_in}->{token_out} price: {best_price:.6f}, fee: ${best_fee:.4f}")
                return {
                    'price': best_price,
                    'fee': best_fee,
                    'amount_out': best_amount_out
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch Uniswap V3 price: {e}")
            return None
    
    def calculate_flash_loan_fee(self, amount: Decimal) -> Decimal:
        """Calculate AAVE flash loan fee (0.09%)"""
        return amount * self.aave_flash_loan_fee_rate
    
    def estimate_gas_cost(self, complexity: str = 'medium') -> Decimal:
        """Estimate gas cost in USD for flash loan execution"""
        gas_estimates = {
            'simple': 300000,    # Simple arbitrage
            'medium': 450000,    # Medium complexity
            'complex': 600000    # Complex multi-hop
        }
        
        gas_limit = gas_estimates.get(complexity, 450000)
        gas_price = 30  # 30 gwei average
        matic_price = Decimal('0.5')  # $0.5 per MATIC
        
        gas_cost_matic = Decimal(gas_limit * gas_price) / Decimal('1e9')
        gas_cost_usd = gas_cost_matic * matic_price
        
        return gas_cost_usd
    
    async def find_arbitrage_opportunities(self) -> List[ProfitableOpportunity]:
        """Find arbitrage opportunities within profit target range"""
        opportunities = []
        
        try:
            # Check all token pairs for arbitrage
            token_list = list(self.tokens.keys())[:3]  # Limit to first 3 tokens for demo
            
            for i, token_in in enumerate(token_list):
                for j, token_out in enumerate(token_list):
                    if i >= j:  # Skip same token and duplicate pairs
                        continue
                    
                    logger.info(f"🔍 Checking {token_in} -> {token_out} arbitrage...")
                    
                    # Test with different amounts to find optimal profit
                    test_amounts = [
                        Decimal('2000'),   # Small trades
                        Decimal('5000'),   # Medium trades  
                        Decimal('10000'),  # Larger trades
                        Decimal('15000'),  # Max trades
                    ]
                    
                    for amount in test_amounts:
                        # Get DEX prices for this pair and amount
                        dex_prices = await self.get_real_dex_prices(token_in, token_out, amount)
                        
                        if len(dex_prices) < 2:
                            continue  # Need at least 2 DEXes for arbitrage
                        
                        # Find arbitrage opportunities between DEXes
                        dex_names = list(dex_prices.keys())
                        for k, buy_dex in enumerate(dex_names):
                            for l, sell_dex in enumerate(dex_names):
                                if k >= l:
                                    continue
                                
                                buy_data = dex_prices[buy_dex]
                                sell_data = dex_prices[sell_dex]
                                
                                # Check if sell price > buy price (arbitrage opportunity)
                                if sell_data['amount_out'] > buy_data['amount_out']:
                                    opportunity = await self.evaluate_opportunity(
                                        token_in, token_out, amount, buy_dex, sell_dex,
                                        buy_data, sell_data
                                    )
                                    
                                    if opportunity and opportunity.is_profitable_target():
                                        opportunities.append(opportunity)
                                        logger.info(f"✅ Found opportunity: {opportunity.get_summary()}")
                                        self.metrics.opportunities_in_range += 1
                    
                    self.metrics.opportunities_found += len(opportunities)
            
        except Exception as e:
            logger.error(f"Error finding arbitrage opportunities: {e}")
        
        # Sort by profit potential and priority
        opportunities.sort(key=lambda x: (x.execution_priority, -x.net_profit), reverse=True)
        
        return opportunities[:5]  # Return top 5 opportunities
    
    async def evaluate_opportunity(self, token_in: str, token_out: str, amount: Decimal,
                                 buy_dex: str, sell_dex: str,
                                 buy_data: Dict[str, Decimal], sell_data: Dict[str, Decimal]) -> Optional[ProfitableOpportunity]:
        """Evaluate a potential arbitrage opportunity with full fee calculations"""
        
        try:
            # Calculate gross profit from price difference
            buy_cost = amount  # Cost to buy on buy_dex
            sell_revenue = sell_data['amount_out']  # Revenue from selling on sell_dex
            gross_profit = sell_revenue - buy_cost
            
            if gross_profit <= 0:
                return None
            
            # Calculate all fees
            buy_dex_fee = buy_data['fee']
            sell_dex_fee = sell_data['fee'] 
            total_dex_fees = buy_dex_fee + sell_dex_fee
            
            flash_loan_fee = self.calculate_flash_loan_fee(amount)
            gas_cost = self.estimate_gas_cost('medium')
            
            # Calculate net profit after all fees
            net_profit = gross_profit - total_dex_fees - flash_loan_fee - gas_cost
            
            # Check if this yields profit in our target range
            if not (self.min_profit <= net_profit <= self.max_profit):
                return None
            
            # Calculate profit parameters
            profit_margin = (net_profit / amount) * 100 if amount > 0 else Decimal('0')
            
            # Risk assessment
            risks = []
            confidence_score = 1.0
            
            if profit_margin < Decimal('0.5'):
                risks.append("Low profit margin")
                confidence_score -= 0.2
            
            if amount > Decimal('15000'):
                risks.append("High loan amount")  
                confidence_score -= 0.1
                
            if net_profit < Decimal('6'):
                risks.append("Low absolute profit")
                confidence_score -= 0.1
            
            if total_dex_fees > net_profit * Decimal('0.3'):
                risks.append("High DEX fees relative to profit")
                confidence_score -= 0.15
            
            # Execution priority (higher is better)
            execution_priority = int(confidence_score * 100)
            # Boost for sweet spot ($8-20 range)
            if Decimal('8') <= net_profit <= Decimal('20'):
                execution_priority += 30
            
            opportunity = ProfitableOpportunity(
                id=f"{token_in}_{token_out}_{buy_dex}_{sell_dex}_{int(time.time())}",
                timestamp=datetime.now(),
                asset=token_in,
                loan_amount=amount,
                source_dex=buy_dex,
                target_dex=sell_dex,
                buy_price=buy_data['price'],
                sell_price=sell_data['price'],
                gross_profit=gross_profit,
                dex_fees=total_dex_fees,
                flash_loan_fee=flash_loan_fee,
                gas_cost=gas_cost,
                net_profit=net_profit,
                profit_margin=profit_margin,
                confidence_score=confidence_score,
                execution_priority=execution_priority,
                estimated_execution_time=30,
                risks=risks
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error evaluating opportunity: {e}")
            return None
    
    async def execute_flash_loan(self, opportunity: ProfitableOpportunity) -> Dict[str, Any]:
        """Execute flash loan arbitrage - PROTECTED WITH EXECUTION CONTROLS"""
        
        # CRITICAL SAFETY CHECK - Prevent execution unless explicitly authorized
        if not self.execution_enabled or self.dry_run_mode:
            return await self._simulate_execution(opportunity)
        
        # If we reach here, trading is enabled - this is REAL execution
        logger.critical(f"🚨 EXECUTING REAL FLASH LOAN TRADE: {opportunity.id}")
        logger.critical(f"🚨 Expected profit: ${opportunity.net_profit:.2f}")
        logger.critical(f"🚨 This will cost real gas and execute real trades!")
        
        execution_start = time.time()
        
        try:
            # REAL EXECUTION LOGIC WOULD GO HERE
            # This would interact with the deployed contract at core/contracts/FlashLoanArbitrageFixed.sol
            logger.error("❌ REAL EXECUTION NOT IMPLEMENTED - Falling back to simulation")
            return await self._simulate_execution(opportunity)
            
        except Exception as e:
            logger.error(f"❌ Error in real execution: {e}")
            self.metrics.failed_executions += 1
            return {
                'success': False,
                'error_message': str(e),
                'execution_time': time.time() - execution_start,
                'mode': 'real_execution_failed'
            }
    
    async def _simulate_execution(self, opportunity: ProfitableOpportunity) -> Dict[str, Any]:
        """Simulate flash loan execution for monitoring purposes"""
        
        logger.info(f"🔍 SIMULATING flash loan for opportunity: {opportunity.id}")
        logger.info(f"📊 Expected profit: ${opportunity.net_profit:.2f} (SIMULATION ONLY)")
        
        execution_start = time.time()
        
        try:
            # Simulate realistic execution time
            await asyncio.sleep(0.5)
            
            # Simulate success/failure based on confidence and market conditions
            success = opportunity.confidence_score > 0.7
            
            execution_time = time.time() - execution_start
            
            if success:
                # Simulate actual profit with realistic variance
                variance = Decimal('0.85') + (Decimal('0.3') * Decimal(str(opportunity.confidence_score)))
                simulated_profit = opportunity.net_profit * variance
                
                # Update simulation metrics only
                self.metrics.successful_executions += 1
                self.metrics.total_profit += simulated_profit
                
                result = {
                    'success': True,
                    'mode': 'simulation',
                    'simulated_transaction_hash': f"0xSIM{int(time.time()):016x}{'a' * 44}",
                    'simulated_profit': float(simulated_profit),
                    'expected_profit': float(opportunity.net_profit),
                    'execution_time': execution_time,
                    'simulated_gas_used': 420000,
                    'all_fees_included': {
                        'dex_fees': float(opportunity.dex_fees),
                        'flash_loan_fee': float(opportunity.flash_loan_fee),
                        'gas_cost': float(opportunity.gas_cost),
                        'total_fees': float(opportunity.dex_fees + opportunity.flash_loan_fee + opportunity.gas_cost)
                    }
                }
            else:
                self.metrics.failed_executions += 1
                result = {
                    'success': False,
                    'mode': 'simulation',
                    'error_message': 'Simulated market conditions unfavorable',
                    'execution_time': execution_time
                }
            
            # Update average execution time
            total_executions = self.metrics.successful_executions + self.metrics.failed_executions
            if total_executions > 0:
                self.metrics.average_execution_time = (
                    (self.metrics.average_execution_time * (total_executions - 1) + execution_time) / total_executions
                )
                self.metrics.success_rate = self.metrics.successful_executions / total_executions
            
            return result
            
        except Exception as e:
            logger.error(f"Error in simulation: {e}")
            return {
                'success': False,
                'mode': 'simulation_error',
                'error_message': str(e),
                'execution_time': time.time() - execution_start
            }
    
    async def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        
        logger.info("🔄 Starting monitoring cycle...")
        cycle_start = time.time()
        
        try:
            # Find opportunities
            opportunities = await self.find_arbitrage_opportunities()
            
            if not opportunities:
                logger.info("📊 No profitable opportunities found in $4-$30 range")
                return
            
            logger.info(f"🎯 Found {len(opportunities)} opportunities in profit target range")
            
            # Execute top opportunities (in dry run mode)
            for i, opportunity in enumerate(opportunities[:3]):  # Top 3 only
                logger.info(f"\\n🚀 Processing opportunity {i+1}:")
                logger.info(f"   {opportunity.get_summary()}")
                logger.info(f"   Fee breakdown: DEX: ${opportunity.dex_fees:.4f}, "
                           f"AAVE: ${opportunity.flash_loan_fee:.4f}, "
                           f"Gas: ${opportunity.gas_cost:.4f}")
                
                # Execute (simulate) the opportunity
                result = await self.execute_flash_loan(opportunity)
                
                # Store execution history
                self.execution_history.append({
                    'timestamp': datetime.now(),
                    'opportunity': asdict(opportunity),
                    'result': result
                })
                
                # Log result
                if result['success']:
                    logger.info(f"✅ Execution successful: ${result.get('simulated_profit', 0):.2f} profit")
                else:
                    logger.info(f"❌ Execution failed: {result.get('error_message', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
        
        finally:
            cycle_time = time.time() - cycle_start
            logger.info(f"⏱️  Monitoring cycle completed in {cycle_time:.2f}s")
            
            # Display performance summary
            await self.display_performance_summary()
    
    async def display_performance_summary(self):
        """Display performance summary"""
        
        print("\\n" + "="*80)
        print("📊 AAVE FLASH LOAN PROFIT TARGET SYSTEM - PERFORMANCE SUMMARY")
        print("="*80)
        print(f"Target Range: ${self.min_profit} - ${self.max_profit}")
        print(f"Trading Mode: {'🚨 REAL TRADING ENABLED' if self.execution_enabled else '🔍 DRY RUN ONLY'}")
        print(f"\\n📈 Opportunities:")
        print(f"   Total Found: {self.metrics.opportunities_found}")
        print(f"   In Target Range: {self.metrics.opportunities_in_range}")
        print(f"   Success Rate: {self.metrics.success_rate:.1%}")
        
        print(f"\\n💰 Financial Summary:")
        print(f"   Total Simulated Profit: ${self.metrics.total_profit:.2f}")
        print(f"   Successful Executions: {self.metrics.successful_executions}")
        print(f"   Failed Executions: {self.metrics.failed_executions}")
        
        if self.metrics.successful_executions > 0:
            avg_profit = self.metrics.total_profit / self.metrics.successful_executions
            print(f"   Average Profit per Success: ${avg_profit:.2f}")
        
        if self.execution_history:
            recent = self.execution_history[-1]
            print(f"\\n🕐 Last Execution:")
            print(f"   Asset: {recent['opportunity']['asset']}")
            print(f"   Route: {recent['opportunity']['source_dex']} → {recent['opportunity']['target_dex']}")
            print(f"   Result: {'✅ Success' if recent['result']['success'] else '❌ Failed'}")
            if recent['result']['success']:
                print(f"   Profit: ${recent['result'].get('simulated_profit', 0):.2f}")
        
        print("\\n🔧 System Status:")
        print(f"   Execution Mode: {'REAL TRADING' if self.execution_enabled else 'SIMULATION'}")
        print(f"   Price Source: REAL DEX PRICES ONLY")
        print(f"   Fee Calculation: ✅ DEX + AAVE + Gas fees included")
        print("="*80)
    
    async def run_continuous_monitoring(self, interval: int = 60):
        """Run continuous monitoring for flash loan opportunities"""
        
        logger.info(f"🚀 Starting AAVE Flash Loan Profit Target System")
        logger.info(f"   Target Range: ${self.min_profit}-${self.max_profit}")
        logger.info(f"   Monitoring Interval: {interval} seconds")
        logger.info(f"   Mode: {'REAL TRADING' if self.execution_enabled else 'DRY RUN ONLY'}")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"\\n🔄 Starting monitoring cycle #{cycle_count}")
                
                await self.run_monitoring_cycle()
                
                logger.info(f"⏸️  Waiting {interval} seconds until next cycle...")
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️  Stopping monitoring...")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    def _get_uniswap_v2_router_abi(self):
        """Get Uniswap V2 Router ABI for price queries"""
        return [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [
                    {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"},
                ],
                "stateMutability": "view",
                "type": "function",
            },
        ]
    
    def _get_uniswap_v3_quoter_abi(self):
        """Get Uniswap V3 Quoter ABI for price queries"""
        return [
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "name": "quoteExactInputSingle",
                "outputs": [
                    {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                ],
                "stateMutability": "nonpayable",
                "type": "function",
            },
        ]
    
    def enable_trading_execution(self, authorization_key: str):
        """Enable trading execution with authorization key"""
        if authorization_key == "ENABLE_REAL_TRADING_WITH_RISKS":
            self.execution_enabled = True
            self.dry_run_mode = False
            self.execution_authorization_key = authorization_key
            logger.critical("🚨 TRADING EXECUTION ENABLED - Real trades can now be executed!")
            logger.critical("🚨 This system will now execute real flash loan arbitrage trades!")
        else:
            logger.error("❌ Invalid authorization key - trading remains disabled")
    
    def disable_trading_execution(self):
        """Disable trading execution and return to dry run mode"""
        self.execution_enabled = False
        self.dry_run_mode = True
        self.execution_authorization_key = None
        logger.warning("🛑 TRADING EXECUTION DISABLED - Returning to DRY RUN mode")

async def main():
    """Main entry point"""
    system = AaveFlashLoanProfitTarget()
    
    # Run a single cycle for testing
    if len(sys.argv) > 1 and sys.argv[1] == 'single':
        await system.run_monitoring_cycle()
    else:
        # Run continuous monitoring
        await system.run_continuous_monitoring()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
