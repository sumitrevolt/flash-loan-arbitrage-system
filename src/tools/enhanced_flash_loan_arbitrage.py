#!/usr/bin/env python3
"""
ENHANCED FLASH LOAN ARBITRAGE EXECUTION SYSTEM
==============================================

Complete integration of:
- Real DEX price monitoring
- Flash loan smart contract execution
- Risk management and circuit breakers
- Performance optimization
- Comprehensive logging and monitoring
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Any, Set
import json
import os
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

# Configure decimal precision
getcontext().prec = 28

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flash_loan_arbitrage.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""
    token_pair: str
    buy_dex: str
    sell_dex: str
    buy_price: Decimal
    sell_price: Decimal
    amount: Decimal
    estimated_profit: Decimal
    price_impact: Decimal
    confidence_score: float
    timestamp: datetime
    gas_cost_estimate: Decimal = Decimal('0')
    net_profit: Decimal = Decimal('0')
    
    def __post_init__(self):
        self.net_profit = self.estimated_profit - self.gas_cost_estimate

@dataclass
class RiskMetrics:
    """Risk management metrics"""
    max_position_size: Decimal = Decimal('10.0')  # ETH
    max_price_impact: Decimal = Decimal('0.05')   # 5%
    min_profit_threshold: Decimal = Decimal('0.01')  # 1%
    max_gas_cost: Decimal = Decimal('0.005')      # ETH
    circuit_breaker_loss: Decimal = Decimal('0.1')  # 10% loss triggers pause
    max_daily_trades: int = 100
    max_consecutive_failures: int = 5

class EnhancedFlashLoanArbitrage:
    """
    Enhanced Flash Loan Arbitrage System
    
    Features:
    - Real DEX integrations
    - Smart contract execution
    - Advanced risk management
    - Performance optimization
    - Circuit breakers
    """
    
    def __init__(self, config_file: str = "arbitrage_config.json"):
        """Initialize the enhanced arbitrage system"""
        self.config_file = config_file
        self.config = self._load_config()
        
        # Core components
        self.dex_integrations = None
        self.flash_loan_contract = None
        
        # Risk management
        self.risk_metrics = RiskMetrics()
        self.circuit_breaker_active = False
        self.consecutive_failures = 0
        self.daily_trades = 0
        self.daily_pnl = Decimal('0')
        self.last_reset_date = datetime.now().date()
        
        # Performance tracking
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = Decimal('0')
        self.total_gas_spent = Decimal('0')
        
        # Operating state
        self.is_running = False
        self.pause_until = None
        
        # Opportunity tracking
        self.recent_opportunities: List[ArbitrageOpportunity] = []
        self.executed_opportunities: List[ArbitrageOpportunity] = []
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "networks": {
                "ethereum": {
                    "rpc_url": "https://eth-mainnet.alchemyapi.io/v2/your-key",
                    "flash_loan_contract": "0x742d35Cc6634C0532925a3b8D1bc9d54be6b21ff"
                }
            },
            "trading": {
                "enabled_dexes": ["uniswap_v3", "sushiswap", "balancer_v2", "1inch"],
                "token_pairs": ["ETH/USDC", "ETH/USDT", "WBTC/ETH", "WBTC/USDC"],
                "min_profit_usd": 50.0,
                "max_position_size_eth": 10.0,
                "max_slippage": 0.005
            },
            "risk_management": {
                "circuit_breaker_enabled": True,
                "max_consecutive_failures": 5,
                "max_daily_loss": 1.0,
                "pause_duration_minutes": 30
            },
            "monitoring": {
                "price_update_interval": 5.0,
                "opportunity_check_interval": 2.0,
                "health_check_interval": 60.0
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # Create default config file
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return default_config
    
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing Enhanced Flash Loan Arbitrage System...")
            
            # Initialize DEX integrations
            from dex_integrations import RealDEXIntegrations
            self.dex_integrations = RealDEXIntegrations()
            await self.dex_integrations.initialize()
            
            # Initialize flash loan contract
            from flash_loan_contract import FlashLoanContractFactory
            
            network_config = self.config['networks']['ethereum']
            private_key = os.getenv('PRIVATE_KEY')
            
            if private_key:
                self.flash_loan_contract = FlashLoanContractFactory.create_contract(
                    'ethereum', 
                    network_config['rpc_url'], 
                    private_key
                )
                logger.info("Flash loan contract initialized")
            else:
                logger.warning("No private key found - running in simulation mode")
            
            # Reset daily metrics if needed
            self._reset_daily_metrics_if_needed()
            
            logger.info("System initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise
    
    def _reset_daily_metrics_if_needed(self):
        """Reset daily trading metrics at midnight"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = Decimal('0')
            self.last_reset_date = current_date
            self.consecutive_failures = 0
            logger.info("Daily metrics reset")
    
    async def find_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """Find profitable arbitrage opportunities"""
        opportunities = []
        
        try:
            token_pairs = self.config['trading']['token_pairs']
            enabled_dexes = self.config['trading']['enabled_dexes']
            
            # Fetch prices from all DEXes
            all_prices = await self.dex_integrations.fetch_all_dex_prices_parallel(token_pairs)
            
            for token_pair in token_pairs:
                if token_pair not in all_prices:
                    continue
                
                dex_prices = all_prices[token_pair]
                
                # Find arbitrage opportunities between DEX pairs
                for buy_dex in enabled_dexes:
                    for sell_dex in enabled_dexes:
                        if buy_dex == sell_dex:
                            continue
                        
                        if buy_dex not in dex_prices or sell_dex not in dex_prices:
                            continue
                        
                        buy_price_data = dex_prices[buy_dex]
                        sell_price_data = dex_prices[sell_dex]
                        
                        # Calculate potential profit
                        opportunity = await self._calculate_arbitrage_opportunity(
                            token_pair, buy_dex, sell_dex, buy_price_data, sell_price_data
                        )
                        
                        if opportunity and self._is_opportunity_profitable(opportunity):
                            opportunities.append(opportunity)
            
            # Sort by net profit
            opportunities.sort(key=lambda x: Any: Any: x.net_profit, reverse=True)
            
            # Store recent opportunities for analysis
            self.recent_opportunities = opportunities[:10]
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error finding arbitrage opportunities: {e}")
            return []
    
    async def _calculate_arbitrage_opportunity(self, 
                                            token_pair: str, 
                                            buy_dex: str, 
                                            sell_dex: str, 
                                            buy_price_data, 
                                            sell_price_data) -> Optional[ArbitrageOpportunity]:
        """Calculate detailed arbitrage opportunity metrics"""
        try:
            buy_price = buy_price_data.price
            sell_price = sell_price_data.price
            
            # Only consider if sell price > buy price
            if sell_price <= buy_price:
                return None
            
            # Calculate price difference percentage
            price_diff_pct = (sell_price - buy_price) / buy_price
            
            # Estimate optimal trade size based on liquidity
            min_liquidity = min(buy_price_data.liquidity, sell_price_data.liquidity)
            max_trade_size = min(
                self.risk_metrics.max_position_size,
                Decimal(str(min_liquidity)) * Decimal('0.1')  # 10% of available liquidity
            )
            
            # Calculate price impact (simplified)
            price_impact = price_diff_pct * Decimal('0.5')  # Estimate
            
            # Calculate estimated profit
            estimated_profit = max_trade_size * price_diff_pct
            
            # Estimate gas cost
            gas_cost_estimate = await self._estimate_gas_cost()
            
            # Calculate confidence score based on multiple factors
            confidence_score = self._calculate_confidence_score(
                price_diff_pct, min_liquidity, buy_price_data, sell_price_data
            )
            
            return ArbitrageOpportunity(
                token_pair=token_pair,
                buy_dex=buy_dex,
                sell_dex=sell_dex,
                buy_price=buy_price,
                sell_price=sell_price,
                amount=max_trade_size,
                estimated_profit=estimated_profit,
                price_impact=price_impact,
                confidence_score=confidence_score,
                timestamp=datetime.now(),
                gas_cost_estimate=gas_cost_estimate
            )
            
        except Exception as e:
            logger.error(f"Error calculating opportunity: {e}")
            return None
    
    async def _estimate_gas_cost(self) -> Decimal:
        """Estimate gas cost for flash loan transaction"""
        try:
            # Simplified gas cost estimation
            gas_price_gwei = Decimal('20')  # 20 gwei
            gas_limit = Decimal('400000')   # 400k gas limit
            eth_price = Decimal('2000')     # $2000 per ETH
            
            gas_cost_eth = (gas_price_gwei * gas_limit) / Decimal('1e9')
            return gas_cost_eth
            
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}")
            return Decimal('0.005')  # Default 0.005 ETH
    
    def _calculate_confidence_score(self, price_diff_pct, min_liquidity, buy_data, sell_data) -> float:
        """Calculate confidence score for opportunity (0-1)"""
        score = 0.0
        
        # Price difference factor (higher is better)
        if price_diff_pct > Decimal('0.01'):  # > 1%
            score += 0.3
        elif price_diff_pct > Decimal('0.005'):  # > 0.5%
            score += 0.2
        elif price_diff_pct > Decimal('0.002'):  # > 0.2%
            score += 0.1
        
        # Liquidity factor
        if min_liquidity > 1000000:  # $1M+
            score += 0.3
        elif min_liquidity > 100000:  # $100k+
            score += 0.2
        elif min_liquidity > 10000:   # $10k+
            score += 0.1
        
        # Data freshness factor
        current_time = datetime.now().timestamp()
        buy_age = current_time - buy_data.timestamp
        sell_age = current_time - sell_data.timestamp
        
        if max(buy_age, sell_age) < 30:  # < 30 seconds old
            score += 0.3
        elif max(buy_age, sell_age) < 60:  # < 1 minute old
            score += 0.2
        elif max(buy_age, sell_age) < 120:  # < 2 minutes old
            score += 0.1
        
        # Volume factor (if available)
        score += 0.1  # Base score for having data
        
        return min(score, 1.0)
    
    def _is_opportunity_profitable(self, opportunity: ArbitrageOpportunity) -> bool:
        """Check if opportunity meets profitability criteria"""
        try:
            # Check minimum profit threshold
            min_profit_usd = Decimal(str(self.config['trading']['min_profit_usd']))
            min_profit_eth = min_profit_usd / Decimal('2000')  # Assume $2000 ETH
            
            if opportunity.net_profit < min_profit_eth:
                return False
            
            # Check price impact
            if opportunity.price_impact > self.risk_metrics.max_price_impact:
                return False
            
            # Check confidence score
            if opportunity.confidence_score < 0.5:
                return False
            
            # Check position size
            if opportunity.amount > self.risk_metrics.max_position_size:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking profitability: {e}")
            return False
    
    def _check_risk_limits(self) -> bool:
        """Check if trading should continue based on risk limits"""
        # Check circuit breaker
        if self.circuit_breaker_active:
            if self.pause_until and datetime.now() < self.pause_until:
                return False
            else:
                self.circuit_breaker_active = False
                self.consecutive_failures = 0
                logger.info("Circuit breaker reset")
        
        # Check daily trade limit
        if self.daily_trades >= self.risk_metrics.max_daily_trades:
            logger.warning("Daily trade limit reached")
            return False
        
        # Check daily loss limit
        daily_loss_limit = self.risk_metrics.circuit_breaker_loss
        if self.daily_pnl < -daily_loss_limit:
            logger.warning("Daily loss limit exceeded, activating circuit breaker")
            self._activate_circuit_breaker()
            return False
        
        # Check consecutive failures
        if self.consecutive_failures >= self.risk_metrics.max_consecutive_failures:
            logger.warning("Too many consecutive failures, activating circuit breaker")
            self._activate_circuit_breaker()
            return False
        
        return True
    
    def _activate_circuit_breaker(self):
        """Activate circuit breaker to pause trading"""
        self.circuit_breaker_active = True
        pause_duration = self.config['risk_management']['pause_duration_minutes']
        self.pause_until = datetime.now() + timedelta(minutes=pause_duration)
        logger.warning(f"Circuit breaker activated until {self.pause_until}")
    
    async def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Execute a profitable arbitrage opportunity"""
        try:
            logger.info(f"Executing arbitrage: {opportunity.token_pair} "
                       f"{opportunity.buy_dex}->{opportunity.sell_dex} "
                       f"Profit: ${float(opportunity.net_profit * 2000):.2f}")
            
            if not self.flash_loan_contract:
                logger.warning("No flash loan contract - using simulation")
                return await self._simulate_execution(opportunity)
            
            # Execute flash loan arbitrage
            result: str = await self.dex_integrations.execute_flash_loan_arbitrage(
                token_pair=opportunity.token_pair,
                buy_dex=opportunity.buy_dex,
                sell_dex=opportunity.sell_dex,
                amount=opportunity.amount,
                min_profit=opportunity.estimated_profit
            )
            
            # Update metrics
            self._update_execution_metrics(opportunity, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Arbitrage execution failed: {e}")
            self.consecutive_failures += 1
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _simulate_execution(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Simulate arbitrage execution for testing"""
        await asyncio.sleep(0.5)  # Simulate execution time
        
        # Simulate 95% success rate
        import random
        success = random.random() > 0.05
        
        if success:
            actual_profit = opportunity.estimated_profit * Decimal('0.95')
            self.consecutive_failures = 0
            return {
                'status': 'success',
                'transaction_hash': f"0x{'simulation'*8}",
                'gas_used': 350000,
                'profit_realized': str(actual_profit),
                'execution_time': 0.5,
                'simulation': True
            }
        else:
            self.consecutive_failures += 1
            return {
                'status': 'failed',
                'error': 'Simulation failure',
                'simulation': True
            }
    
    def _update_execution_metrics(self, opportunity: ArbitrageOpportunity, result: Dict[str, Any]):
        """Update trading metrics after execution"""
        self.total_trades += 1
        self.daily_trades += 1
        
        if result.get('status') == 'success':
            self.successful_trades += 1
            self.consecutive_failures = 0
            
            profit = Decimal(str(result.get('profit_realized', 0)))
            gas_cost = Decimal(str(result.get('gas_used', 0))) * Decimal('0.00000002')  # Rough estimate
            
            net_profit = profit - gas_cost
            self.total_profit += net_profit
            self.daily_pnl += net_profit
            self.total_gas_spent += gas_cost
            
            # Store executed opportunity
            opportunity.net_profit = net_profit
            self.executed_opportunities.append(opportunity)
            
            logger.info(f"Successful execution - Profit: ${float(net_profit * 2000):.2f}")
        else:
            self.consecutive_failures += 1
            logger.warning(f"Failed execution: {result.get('error', 'Unknown error')}")
    
    async def run_monitoring_cycle(self):
        """Run continuous monitoring and execution cycle"""
        logger.info("Starting monitoring cycle...")
        
        opportunity_interval = self.config['monitoring']['opportunity_check_interval']
        health_check_interval = self.config['monitoring']['health_check_interval']
        
        last_health_check = datetime.now()
        
        while self.is_running:
            try:
                # Reset daily metrics if needed
                self._reset_daily_metrics_if_needed()
                
                # Check risk limits
                if not self._check_risk_limits():
                    await asyncio.sleep(opportunity_interval)
                    continue
                
                # Find arbitrage opportunities
                opportunities = await self.find_arbitrage_opportunities()
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} arbitrage opportunities")
                    
                    # Execute the best opportunity
                    best_opportunity = opportunities[0]
                    result: str = await self.execute_arbitrage(best_opportunity)
                    
                    # Log result
                    if result.get('status') == 'success':
                        logger.info("Arbitrage executed successfully")
                    else:
                        logger.warning(f"Arbitrage failed: {result.get('error')}")
                
                # Health check
                if datetime.now() - last_health_check > timedelta(seconds=health_check_interval):
                    await self._perform_health_check()
                    last_health_check = datetime.now()
                
                # Wait before next cycle
                await asyncio.sleep(opportunity_interval)
                
            except Exception as e:
                logger.error(f"Monitoring cycle error: {e}")
                await asyncio.sleep(opportunity_interval)
    
    async def _perform_health_check(self):
        """Perform system health check"""
        try:
            # Check DEX connectivity
            if self.dex_integrations:
                health_status = await self._check_dex_health()
                
            # Check success rate
            if self.total_trades > 0:
                success_rate = self.successful_trades / self.total_trades
                if success_rate < 0.5:
                    logger.warning(f"Low success rate: {success_rate:.2%}")
            
            # Log performance metrics
            logger.info(f"Health Check - Trades: {self.total_trades}, "
                       f"Success Rate: {self.successful_trades/max(self.total_trades, 1):.1%}, "
                       f"Total Profit: ${float(self.total_profit * 2000):.2f}, "
                       f"Daily P&L: ${float(self.daily_pnl * 2000):.2f}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _check_dex_health(self) -> Dict[str, bool]:
        """Check health of DEX connections"""
        health_status = {}
        
        try:
            # Test fetch from each DEX
            test_pairs = ['ETH/USDC']
            prices = await self.dex_integrations.fetch_all_dex_prices_parallel(test_pairs)
            
            enabled_dexes = self.config['trading']['enabled_dexes']
            for dex in enabled_dexes:
                health_status[dex] = bool(prices.get('ETH/USDC', {}).get(dex))
            
        except Exception as e:
            logger.error(f"DEX health check failed: {e}")
        
        return health_status
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Enhanced Flash Loan Arbitrage System...")
        self.is_running = False
        
        # Close DEX integrations
        if self.dex_integrations:
            await self.dex_integrations.close()
        
        # Save final metrics
        await self._save_performance_report()
        
        logger.info("Shutdown completed")
    
    async def _save_performance_report(self):
        """Save performance report to file"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_trades': self.total_trades,
                'successful_trades': self.successful_trades,
                'success_rate': self.successful_trades / max(self.total_trades, 1),
                'total_profit_eth': str(self.total_profit),
                'total_gas_spent_eth': str(self.total_gas_spent),
                'daily_pnl_eth': str(self.daily_pnl),
                'circuit_breaker_activations': 0,  # Track this
                'recent_opportunities': len(self.recent_opportunities),
                'executed_opportunities': len(self.executed_opportunities)
            }
            
            with open('performance_report.json', 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info("Performance report saved")
            
        except Exception as e:
            logger.error(f"Failed to save performance report: {e}")

# Main execution
async def main():
    """Main execution function"""
    # Setup signal handlers
    arbitrage_system = None
    
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")
        if arbitrage_system:
            arbitrage_system.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize system
        arbitrage_system = EnhancedFlashLoanArbitrage()
        await arbitrage_system.initialize()
        
        # Start monitoring
        arbitrage_system.is_running = True
        await arbitrage_system.run_monitoring_cycle()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        if arbitrage_system:
            await arbitrage_system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
