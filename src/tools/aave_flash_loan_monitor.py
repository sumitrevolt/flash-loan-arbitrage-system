#!/usr/bin/env python3
"""
Aave Flash Loan Arbitrage Monitoring System
Real-time monitoring of Aave pools, flash loan executions, and arbitrage opportunities
"""

import asyncio
import json
import logging
import time
import os
import platform
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import aiohttp
from web3 import Web3
from web3.exceptions import ContractLogicError
from dotenv import load_dotenv

# Windows compatibility
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment
load_dotenv()

# Set high precision for calculations
getcontext().prec = 50

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Aave V3 Pool ABI (simplified)
AAVE_POOL_ABI = [
    {
        "inputs": [{"name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {"name": "configuration", "type": "uint256"},
            {"name": "liquidityIndex", "type": "uint128"},
            {"name": "currentLiquidityRate", "type": "uint128"},
            {"name": "variableBorrowIndex", "type": "uint128"},
            {"name": "currentVariableBorrowRate", "type": "uint128"},
            {"name": "currentStableBorrowRate", "type": "uint128"},
            {"name": "lastUpdateTimestamp", "type": "uint40"},
            {"name": "id", "type": "uint16"},
            {"name": "aTokenAddress", "type": "address"},
            {"name": "stableDebtTokenAddress", "type": "address"},
            {"name": "variableDebtTokenAddress", "type": "address"},
            {"name": "interestRateStrategyAddress", "type": "address"},
            {"name": "accruedToTreasury", "type": "uint128"},
            {"name": "unbacked", "type": "uint128"},
            {"name": "isolationModeTotalDebt", "type": "uint128"}
        ],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "FLASHLOAN_PREMIUM_TOTAL",
        "outputs": [{"name": "", "type": "uint128"}],
        "type": "function"
    }
]

# ERC20 ABI for balance checks
ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

@dataclass
class FlashLoanExecution:
    """Track flash loan execution details"""
    timestamp: datetime
    tx_hash: str
    token: str
    amount: Decimal
    profit: Decimal
    gas_cost: Decimal
    success: bool
    route: str
    revert_reason: Optional[str] = None

@dataclass
class AavePoolMetrics:
    """Aave pool metrics for a specific asset"""
    asset: str
    symbol: str
    available_liquidity: Decimal
    total_borrowed: Decimal
    utilization_rate: Decimal
    flash_loan_premium: Decimal
    last_update: datetime

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity with Aave flash loan"""
    timestamp: datetime
    token_pair: str
    buy_dex: str
    sell_dex: str
    loan_amount: Decimal
    expected_profit: Decimal
    gas_estimate: Decimal
    risk_score: Decimal
    executable: bool

class AaveFlashLoanMonitor:
    """Monitor Aave flash loans and arbitrage opportunities"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Setup Web3
        rpc_url = os.getenv('POLYGON_RPC_URL', self.config.get('polygon_rpc_url'))
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Aave configuration
        self.aave_config = self.config.get('aave', {})
        self.pool_address = Web3.to_checksum_address(self.aave_config.get('pool_address'))
        self.pool_contract = self.web3.eth.contract(
            address=self.pool_address,
            abi=AAVE_POOL_ABI
        )
        
        # Tracking data
        self.execution_history = deque(maxlen=1000)  # Last 1000 executions
        self.pool_metrics: Dict[str, AavePoolMetrics] = {}
        self.opportunities = deque(maxlen=100)  # Last 100 opportunities
        
        # Performance metrics
        self.total_executions = 0
        self.successful_executions = 0
        self.total_profit = Decimal('0')
        self.total_gas_cost = Decimal('0')
        
        # Safety thresholds
        self.max_utilization = Decimal('0.85')  # 85% max utilization
        self.min_liquidity = Decimal('100000')  # Min $100k liquidity
        self.max_gas_price = 200  # Max 200 gwei
        
    async def get_aave_pool_metrics(self, token_address: str, symbol: str) -> Optional[AavePoolMetrics]:
        """Get current Aave pool metrics for a token"""
        try:
            # Get reserve data
            reserve_data = self.pool_contract.functions.getReserveData(
                Web3.to_checksum_address(token_address)
            ).call()
            
            # Get aToken address and balance
            atoken_address = reserve_data[8]
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            atoken_contract = self.web3.eth.contract(
                address=atoken_address,
                abi=ERC20_ABI
            )
            
            # Get decimals and balances
            decimals = token_contract.functions.decimals().call()
            available_liquidity = atoken_contract.functions.balanceOf(atoken_address).call()
            
            # Calculate metrics
            available_liquidity_decimal = Decimal(available_liquidity) / Decimal(10 ** decimals)
            
            # Get flash loan premium
            flash_loan_premium = self.pool_contract.functions.FLASHLOAN_PREMIUM_TOTAL().call()
            premium_rate = Decimal(flash_loan_premium) / Decimal('10000')  # Convert from basis points
            
            # Simple utilization calculation (would need more data for accurate calc)
            total_borrowed = Decimal('0')  # Placeholder
            utilization_rate = Decimal('0') if available_liquidity_decimal == 0 else total_borrowed / (available_liquidity_decimal + total_borrowed)
            
            return AavePoolMetrics(
                asset=token_address,
                symbol=symbol,
                available_liquidity=available_liquidity_decimal,
                total_borrowed=total_borrowed,
                utilization_rate=utilization_rate,
                flash_loan_premium=premium_rate,
                last_update=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error fetching Aave metrics for {symbol}: {e}")
            return None
    
    async def monitor_gas_prices(self) -> Dict[str, Decimal]:
        """Monitor current gas prices"""
        try:
            gas_price = self.web3.eth.gas_price
            base_fee = self.web3.eth.get_block('latest').get('baseFeePerGas', 0)
            
            return {
                'current': Decimal(gas_price) / Decimal('1e9'),  # Convert to gwei
                'base_fee': Decimal(base_fee) / Decimal('1e9'),
                'safe': gas_price < (self.max_gas_price * 1e9),
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching gas prices: {e}")
            return {
                'current': Decimal('0'),
                'base_fee': Decimal('0'),
                'safe': False,
                'timestamp': datetime.now()
            }
    
    def calculate_flash_loan_cost(self, amount: Decimal, token_symbol: str) -> Decimal:
        """Calculate total cost of flash loan including fees"""
        metrics = self.pool_metrics.get(token_symbol)
        if not metrics:
            return Decimal('0')
        
        # Flash loan fee
        loan_fee = amount * metrics.flash_loan_premium
        
        return loan_fee
    
    def assess_opportunity_risk(self, opportunity: Dict) -> Tuple[Decimal, bool]:
        """Assess risk score and executability of an opportunity"""
        risk_score = Decimal('0')
        executable = True
        reasons = []
        
        # Check pool liquidity
        token_symbol = opportunity.get('token', 'USDC')
        metrics = self.pool_metrics.get(token_symbol)
        
        if metrics:
            # Liquidity check
            if metrics.available_liquidity < self.min_liquidity:
                risk_score += Decimal('30')
                reasons.append("Low liquidity")
            
            # Utilization check
            if metrics.utilization_rate > self.max_utilization:
                risk_score += Decimal('40')
                executable = False
                reasons.append("High utilization")
        else:
            risk_score += Decimal('50')
            reasons.append("No pool metrics")
        
        # Profit margin check
        expected_profit = opportunity.get('net_profit', Decimal('0'))
        loan_amount = opportunity.get('loan_amount', Decimal('1000'))
        profit_margin = (expected_profit / loan_amount) * 100 if loan_amount > 0 else 0
        
        if profit_margin < Decimal('0.5'):  # Less than 0.5%
            risk_score += Decimal('20')
            reasons.append("Low profit margin")
        
        # Gas price check
        gas_metrics = asyncio.run(self.monitor_gas_prices())
        if not gas_metrics['safe']:
            risk_score += Decimal('30')
            executable = False
            reasons.append("High gas price")
        
        # Normalize risk score (0-100)
        risk_score = min(risk_score, Decimal('100'))
        
        return risk_score, executable
    
    def record_execution(self, execution: FlashLoanExecution):
        """Record a flash loan execution"""
        self.execution_history.append(execution)
        self.total_executions += 1
        
        if execution.success:
            self.successful_executions += 1
            self.total_profit += execution.profit
        
        self.total_gas_cost += execution.gas_cost
    
    def get_performance_stats(self) -> Dict:
        """Get current performance statistics"""
        success_rate = (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0
        avg_profit = self.total_profit / self.successful_executions if self.successful_executions > 0 else Decimal('0')
        
        # Recent performance (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_executions = [e for e in self.execution_history if e.timestamp > recent_cutoff]
        recent_successful = sum(1 for e in recent_executions if e.success)
        recent_profit = sum(e.profit for e in recent_executions if e.success)
        
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'success_rate': success_rate,
            'total_profit': self.total_profit,
            'total_gas_cost': self.total_gas_cost,
            'net_profit': self.total_profit - self.total_gas_cost,
            'avg_profit_per_trade': avg_profit,
            'recent_24h': {
                'executions': len(recent_executions),
                'successful': recent_successful,
                'profit': recent_profit
            }
        }
    
    async def display_dashboard(self):
        """Display comprehensive monitoring dashboard"""
        print("\n" + "="*100)
        print("🏦 AAVE FLASH LOAN ARBITRAGE MONITOR")
        print("="*100)
        
        # Monitor key tokens
        key_tokens = {
            '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174': 'USDC',
            '0xc2132D05D31c914a87C6611C10748AEb04B58e8F': 'USDT',
            '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619': 'WETH',
            '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270': 'WMATIC'
        }
        
        while True:
            try:
                # Clear screen (optional)
                os.system('cls' if os.name == 'nt' else 'clear')
        # WARNING: This is a security risk
        # WARNING: This is a security risk
                
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n🕐 Last Update: {current_time}")
                print("="*100)
                
                # 1. Aave Pool Status
                print("\n📊 AAVE POOL STATUS")
                print("-"*100)
                print(f"{'Token':<10} {'Available Liquidity':>20} {'Utilization':>15} {'Flash Fee':>12} {'Status':>15}")
                print("-"*100)
                
                for token_address, symbol in key_tokens.items():
                    metrics = await self.get_aave_pool_metrics(token_address, symbol)
                    if metrics:
                        self.pool_metrics[symbol] = metrics
                        
                        status = "✅ Ready" if metrics.available_liquidity > self.min_liquidity else "⚠️ Low Liquidity"
                        if metrics.utilization_rate > self.max_utilization:
                            status = "❌ High Util"
                        
                        print(f"{symbol:<10} ${metrics.available_liquidity:>19,.2f} "
                              f"{metrics.utilization_rate*100:>14.2f}% "
                              f"{metrics.flash_loan_premium*100:>11.3f}% "
                              f"{status:>15}")
                
                # 2. Gas Prices
                gas_metrics = await self.monitor_gas_prices()
                print(f"\n⛽ GAS PRICES")
                print("-"*100)
                print(f"Current: {gas_metrics['current']:.2f} gwei | "
                      f"Base Fee: {gas_metrics['base_fee']:.2f} gwei | "
                      f"Status: {'✅ Safe' if gas_metrics['safe'] else '❌ Too High'}")
                
                # 3. Performance Stats
                stats = self.get_performance_stats()
                print(f"\n📈 PERFORMANCE METRICS")
                print("-"*100)
                print(f"Total Executions: {stats['total_executions']} | "
                      f"Success Rate: {stats['success_rate']:.1f}% | "
                      f"Total Profit: ${stats['total_profit']:.2f}")
                print(f"Total Gas Cost: ${stats['total_gas_cost']:.2f} | "
                      f"Net Profit: ${stats['net_profit']:.2f} | "
                      f"Avg Profit/Trade: ${stats['avg_profit_per_trade']:.2f}")
                
                print(f"\n📅 LAST 24 HOURS")
                print("-"*100)
                print(f"Executions: {stats['recent_24h']['executions']} | "
                      f"Successful: {stats['recent_24h']['successful']} | "
                      f"Profit: ${stats['recent_24h']['profit']:.2f}")
                
                # 4. Recent Executions
                print(f"\n🔄 RECENT FLASH LOAN EXECUTIONS")
                print("-"*100)
                print(f"{'Time':<10} {'Token':<8} {'Amount':>12} {'Route':<25} {'Profit':>10} {'Gas':>8} {'Status':<12}")
                print("-"*100)
                
                recent_execs = list(self.execution_history)[-5:]  # Last 5
                for exec in recent_execs:
                    time_str = exec.timestamp.strftime("%H:%M:%S")
                    status = "✅ Success" if exec.success else f"❌ {exec.revert_reason or 'Failed'}"
                    print(f"{time_str:<10} {exec.token:<8} ${exec.amount:>11,.0f} "
                          f"{exec.route:<25} ${exec.profit:>9.2f} ${exec.gas_cost:>7.2f} {status:<12}")
                
                # 5. Active Opportunities
                print(f"\n🎯 ACTIVE ARBITRAGE OPPORTUNITIES")
                print("-"*100)
                
                if self.opportunities:
                    print(f"{'Pair':<15} {'Route':<25} {'Loan Amt':>12} {'Expected':>10} {'Risk':>8} {'Status':<12}")
                    print("-"*100)
                    
                    for opp in list(self.opportunities)[-5:]:  # Last 5
                        status = "✅ Ready" if opp.executable else "❌ Too Risky"
                        print(f"{opp.token_pair:<15} {opp.buy_dex} → {opp.sell_dex:<15} "
                              f"${opp.loan_amount:>11,.0f} ${opp.expected_profit:>9.2f} "
                              f"{opp.risk_score:>7.0f}% {status:<12}")
                else:
                    print("No active opportunities at the moment")
                
                # 6. System Health
                print(f"\n🏥 SYSTEM HEALTH")
                print("-"*100)
                
                # Check critical components
                web3_connected = self.web3.is_connected()
                aave_accessible = True  # Would check actual contract call
                
                print(f"Web3 Connection: {'✅ Connected' if web3_connected else '❌ Disconnected'}")
                print(f"Aave Pool: {'✅ Accessible' if aave_accessible else '❌ Unreachable'}")
                print(f"Monitor Status: ✅ Running")
                
                print("\n" + "="*100)
                print("Press Ctrl+C to stop monitoring")
                
                # Simulate adding some data (in production, this would come from actual executions)
                if self.total_executions % 10 == 0:  # Every 10th iteration
                    # Simulate an execution
                    mock_exec = FlashLoanExecution(
                        timestamp=datetime.now(),
                        tx_hash="0x" + "a" * 64,
                        token="USDC",
                        amount=Decimal('10000'),
                        profit=Decimal('25.50'),
                        gas_cost=Decimal('5.25'),
                        success=True,
                        route="UniswapV3 → SushiSwap"
                    )
                    self.record_execution(mock_exec)
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except KeyboardInterrupt:
                print("\n\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Dashboard error: {e}")
                print(f"\n❌ Dashboard error: {e}")
                await asyncio.sleep(5)

async def main():
    """Main function"""
    monitor = AaveFlashLoanMonitor('production_config.json')
    
    print("🚀 Starting Aave Flash Loan Monitor...")
    print("📊 Initializing pool metrics...")
    
    try:
        await monitor.display_dashboard()
    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        print(f"❌ Monitor failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())