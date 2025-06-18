#!/usr/bin/env python3
"""
AAVE Flash Loan Integration Script
=================================

Integration script that connects the AAVE Flash Loan Profit Target system
with the existing MCP server infrastructure and ensures proper coordination
for profit targeting between $4-$30.

This script:
1. Starts the AAVE profit targeting system
2. Integrates with existing MCP servers
3. Provides monitoring and coordination
4. Ensures profit targets are met
5. Handles execution coordination
"""

import asyncio
import json
import logging
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Add the project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our profit targeting system
from aave_flash_loan_profit_target import AaveFlashLoanProfitTarget, ProfitableOpportunity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AaveFlashLoanIntegration")

class AaveFlashLoanIntegration:
    """Integration coordinator for AAVE flash loan profit targeting"""
    
    def __init__(self):
        self.profit_target_system = AaveFlashLoanProfitTarget()
        self.mcp_servers = {}
        self.coordination_data = {
            'total_opportunities': 0,
            'executed_today': 0,
            'profit_today': 0.0,
            'target_range_hits': 0,
            'success_rate': 0.0
        }
        
        # Integration settings
        self.enable_mcp_coordination = True
        self.enable_real_execution = False  # Set to True for real trading
        self.profit_target_min = 4.0
        self.profit_target_max = 30.0
        
    async def check_mcp_servers(self) -> Dict[str, bool]:
        """Check status of related MCP servers"""
        servers_to_check = [
            ('localhost', 8002, 'flash_loan_mcp'),
            ('localhost', 8005, 'aave_flash_loan_mcp'),
            ('localhost', 8003, 'dex_aggregator_mcp'),
            ('localhost', 8004, 'price_monitor_mcp')
        ]
        
        server_status = {}
        
        for host, port, name in servers_to_check:
            try:
                # Simple HTTP health check
                import aiohttp
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    url = f"http://{host}:{port}/health"
                    async with session.get(url) as response:
                        server_status[name] = response.status == 200
            except:
                server_status[name] = False
        
        return server_status
    
    async def coordinate_with_mcp_servers(self, opportunity: ProfitableOpportunity) -> Dict[str, Any]:
        """Coordinate execution with MCP servers"""
        coordination_result = {
            'flash_loan_server': False,
            'dex_aggregator': False,
            'price_monitor': False,
            'risk_assessment': False,
            'execution_approved': False
        }
        
        try:
            if self.enable_mcp_coordination:
                # Check server availability
                server_status = await self.check_mcp_servers()
                
                # Flash loan server coordination
                if server_status.get('aave_flash_loan_mcp', False):
                    coordination_result['flash_loan_server'] = True
                    logger.info("✅ Flash loan MCP server available")
                
                # DEX aggregator coordination
                if server_status.get('dex_aggregator_mcp', False):
                    coordination_result['dex_aggregator'] = True
                    logger.info("✅ DEX aggregator MCP server available")
                
                # Price monitor coordination
                if server_status.get('price_monitor_mcp', False):
                    coordination_result['price_monitor'] = True
                    logger.info("✅ Price monitor MCP server available")
                
                # Risk assessment
                if opportunity.confidence_score > 0.7 and len(opportunity.risks) <= 2:
                    coordination_result['risk_assessment'] = True
                    logger.info("✅ Risk assessment passed")
                
                # Overall execution approval
                if (coordination_result['flash_loan_server'] and 
                    coordination_result['dex_aggregator'] and
                    coordination_result['risk_assessment']):
                    coordination_result['execution_approved'] = True
                    logger.info("✅ Execution approved by coordination")
            else:
                # Standalone mode
                coordination_result['execution_approved'] = True
                logger.info("🔧 Running in standalone mode")
        
        except Exception as e:
            logger.error(f"Error in MCP coordination: {e}")
        
        return coordination_result
    
    async def validate_profit_target(self, opportunity: ProfitableOpportunity) -> bool:
        """Validate that opportunity meets profit target requirements"""
        
        net_profit = float(opportunity.net_profit)
        
        # Check profit range
        if not (self.profit_target_min <= net_profit <= self.profit_target_max):
            logger.warning(f"❌ Opportunity profit ${net_profit:.2f} outside target range (${self.profit_target_min}-${self.profit_target_max})")
            return False
        
        # Check profit margin
        profit_margin = float(opportunity.profit_margin)
        if profit_margin < 0.5:  # Less than 0.5% margin
            logger.warning(f"❌ Profit margin {profit_margin:.2f}% too low")
            return False
        
        # Check confidence score
        if opportunity.confidence_score < 0.6:
            logger.warning(f"❌ Confidence score {opportunity.confidence_score:.2f} too low")
            return False
        
        logger.info(f"✅ Opportunity validated: ${net_profit:.2f} profit, {profit_margin:.2f}% margin")
        return True
    
    async def execute_coordinated_flash_loan(self, opportunity: ProfitableOpportunity) -> Dict[str, Any]:
        """Execute flash loan with full coordination"""
        
        logger.info(f"🎯 Starting coordinated flash loan execution")
        logger.info(f"   Target: ${float(opportunity.net_profit):.2f} profit")
        logger.info(f"   Asset: {opportunity.asset}")
        logger.info(f"   Route: {opportunity.source_dex} → {opportunity.target_dex}")
        
        execution_start = time.time()
        
        try:
            # Step 1: Validate profit target
            if not await self.validate_profit_target(opportunity):
                return {
                    'success': False,
                    'error': 'Profit target validation failed',
                    'stage': 'validation'
                }
            
            # Step 2: Coordinate with MCP servers
            coordination = await self.coordinate_with_mcp_servers(opportunity)
            
            if not coordination['execution_approved']:
                return {
                    'success': False,
                    'error': 'MCP coordination failed',
                    'stage': 'coordination',
                    'coordination_details': coordination
                }
            
            # Step 3: Execute the flash loan
            if self.enable_real_execution:
                # Real execution through profit target system
                result = await self.profit_target_system.execute_flash_loan(opportunity)
            else:
                # Simulation mode
                result = await self.simulate_execution(opportunity)
            
            execution_time = time.time() - execution_start
            
            # Step 4: Update coordination data
            self.coordination_data['total_opportunities'] += 1
            if result['success']:
                self.coordination_data['executed_today'] += 1
                self.coordination_data['profit_today'] += result.get('actual_profit', 0)
                if self.profit_target_min <= result.get('actual_profit', 0) <= self.profit_target_max:
                    self.coordination_data['target_range_hits'] += 1
            
            # Update success rate
            total_executed = self.coordination_data['executed_today']
            if total_executed > 0:
                success_count = self.coordination_data['target_range_hits']
                self.coordination_data['success_rate'] = (success_count / total_executed) * 100
            
            # Step 5: Log results
            if result['success']:
                actual_profit = result.get('actual_profit', 0)
                logger.info(f"🎉 Flash loan executed successfully!")
                logger.info(f"   Actual profit: ${actual_profit:.2f}")
                logger.info(f"   Execution time: {execution_time:.2f}s")
                logger.info(f"   In target range: {'✅ Yes' if self.profit_target_min <= actual_profit <= self.profit_target_max else '❌ No'}")
            else:
                logger.error(f"❌ Flash loan execution failed: {result.get('error_message', 'Unknown error')}")
            
            result['coordination'] = coordination
            result['execution_time'] = execution_time
            result['profit_target_met'] = (
                result['success'] and 
                self.profit_target_min <= result.get('actual_profit', 0) <= self.profit_target_max
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in coordinated execution: {e}")
            return {
                'success': False,
                'error': str(e),
                'stage': 'execution',
                'execution_time': time.time() - execution_start
            }
    
    async def simulate_execution(self, opportunity: ProfitableOpportunity) -> Dict[str, Any]:
        """Simulate flash loan execution for testing"""
        
        # Simulate execution delay
        await asyncio.sleep(1.5)
        
        # Simulate success based on confidence and target range
        in_target_range = opportunity.is_profitable_target()
        high_confidence = opportunity.confidence_score > 0.7
        
        success = in_target_range and high_confidence
        
        if success:
            # Simulate actual profit with some variance
            variance = 0.95 + (0.1 * opportunity.confidence_score)  # 95-105% of expected
            actual_profit = float(opportunity.net_profit) * variance
            
            return {
                'success': True,
                'transaction_hash': f"0x{'a' * 64}",  # Mock hash
                'actual_profit': actual_profit,
                'expected_profit': float(opportunity.net_profit),
                'gas_used': 420000,
                'simulation': True
            }
        else:
            return {
                'success': False,
                'error_message': 'Simulated execution failure based on confidence/target',
                'simulation': True
            }
    
    def display_integration_dashboard(self):
        """Display integration dashboard"""
        
        print("\n" + "="*100)
        print("🏦 AAVE FLASH LOAN INTEGRATION DASHBOARD - TARGET: $4-$30 PROFIT")
        print("="*100)
        
        # Current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🕐 Time: {current_time}")
        
        # System status
        print(f"\n🔧 SYSTEM STATUS")
        print(f"   Integration Mode: {'🔗 MCP Coordinated' if self.enable_mcp_coordination else '🔧 Standalone'}")
        print(f"   Execution Mode: {'🔴 Real Trading' if self.enable_real_execution else '🔵 Simulation'}")
        print(f"   Profit Target: ${self.profit_target_min}-${self.profit_target_max}")
        
        # Performance metrics
        print(f"\n📊 TODAY'S PERFORMANCE")
        print(f"   Opportunities Found: {self.coordination_data['total_opportunities']}")
        print(f"   Executions: {self.coordination_data['executed_today']}")
        print(f"   Target Range Hits: {self.coordination_data['target_range_hits']}")
        print(f"   Success Rate: {self.coordination_data['success_rate']:.1f}%")
        print(f"   Total Profit: ${self.coordination_data['profit_today']:.2f}")
        
        # Profit target analysis
        avg_profit = (self.coordination_data['profit_today'] / max(1, self.coordination_data['target_range_hits']))
        print(f"\n🎯 PROFIT TARGET ANALYSIS")
        print(f"   Average Profit/Trade: ${avg_profit:.2f}")
        print(f"   Target Achievement: {self.coordination_data['target_range_hits']}/{self.coordination_data['executed_today']}")
        
        if self.coordination_data['target_range_hits'] > 0:
            target_rate = (self.coordination_data['target_range_hits'] / self.coordination_data['executed_today']) * 100
            print(f"   Target Range Hit Rate: {target_rate:.1f}%")
        
        print("="*100)
    
    async def run_integration_cycle(self):
        """Run one complete integration cycle"""
        
        try:
            # Find opportunities using the profit target system
            opportunities = await self.profit_target_system.find_arbitrage_opportunities()
            
            # Filter for target range
            target_opportunities = self.profit_target_system.filter_opportunities_by_profit_target(opportunities)
            
            logger.info(f"Found {len(target_opportunities)} opportunities in $4-$30 range")
            
            # Execute the best opportunities with coordination
            executed_count = 0
            for opportunity in target_opportunities[:2]:  # Execute top 2
                if opportunity.confidence_score > 0.6:
                    result = await self.execute_coordinated_flash_loan(opportunity)
                    executed_count += 1
                    
                    # Small delay between executions
                    await asyncio.sleep(3)
            
            # Display dashboard
            self.display_integration_dashboard()
            
            return executed_count
            
        except Exception as e:
            logger.error(f"Error in integration cycle: {e}")
            return 0
    
    async def run_continuous_integration(self, interval: int = 45):
        """Run continuous integration monitoring"""
        
        logger.info("🚀 Starting AAVE Flash Loan Integration System")
        logger.info(f"   Profit Target: ${self.profit_target_min}-${self.profit_target_max}")
        logger.info(f"   Integration Mode: {'MCP Coordinated' if self.enable_mcp_coordination else 'Standalone'}")
        logger.info(f"   Execution Mode: {'Real Trading' if self.enable_real_execution else 'Simulation'}")
        logger.info(f"   Monitoring Interval: {interval} seconds")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"\n🔄 Starting integration cycle #{cycle_count}")
                
                executed = await self.run_integration_cycle()
                
                if executed > 0:
                    logger.info(f"✅ Cycle #{cycle_count} completed: {executed} executions")
                else:
                    logger.info(f"⏭️  Cycle #{cycle_count} completed: No suitable opportunities")
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️  Integration system stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous integration: {e}")
                await asyncio.sleep(15)  # Wait before retrying

async def main():
    """Main entry point"""
    
    integration = AaveFlashLoanIntegration()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'single':
            # Run single cycle
            await integration.run_integration_cycle()
        elif sys.argv[1] == 'dashboard':
            # Just show dashboard
            integration.display_integration_dashboard()
        elif sys.argv[1] == 'real':
            # Enable real execution
            integration.enable_real_execution = True
            await integration.run_continuous_integration()
        else:
            print("Usage: python aave_integration.py [single|dashboard|real]")
    else:
        # Run continuous simulation
        await integration.run_continuous_integration()

if __name__ == "__main__":
    asyncio.run(main())
