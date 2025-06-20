#!/usr/bin/env python3
"""
Orchestrator Integration Enhancement
===================================

This module integrates the interaction system with your existing docker_arbitrage_orchestrator.py
without modifying the original file. Simply import and use this to enhance your orchestrator.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.interaction_system_enhancer import add_interaction_capabilities_to_orchestrator
from docker_arbitrage_orchestrator import DockerArbitrageOrchestrator

class EnhancedDockerOrchestrator(DockerArbitrageOrchestrator):
    """Enhanced version of your existing orchestrator with interaction capabilities"""
    
    def __init__(self):
        super().__init__()
        self.interaction_enhancer = None
        self.interaction_tasks = []
        
        # Extended statistics for interaction tracking
        self.interaction_stats = {
            'total_interactions': 0,
            'successful_coordinations': 0,
            'failed_coordinations': 0,
            'avg_response_time': 0.0,
            'active_workflows': 0
        }
    
    async def start_enhanced_system(self):
        """Start the enhanced system with interaction capabilities"""
        print("🚀 Starting Enhanced Docker-based 24/7 Flash Loan Arbitrage System")
        print("=" * 80)
        
        try:
            # Initialize base system first
            await self._initialize_system()
            
            # Add interaction capabilities
            await self._initialize_interaction_system()
            
            # Start enhanced orchestration loop
            await self._run_enhanced_orchestration_loop()
            
        except KeyboardInterrupt:
            print("👋 Shutdown signal received")
            await self._shutdown_enhanced_system()
        except Exception as e:
            print(f"❌ System error: {e}")
            await self._handle_enhanced_system_error(e)
    
    async def _initialize_interaction_system(self):
        """Initialize the interaction system enhancement"""
        print("🔧 Initializing interaction system...")
        
        try:
            # Add interaction capabilities to this orchestrator
            self.interaction_enhancer, self.interaction_tasks = await add_interaction_capabilities_to_orchestrator(self)
            
            print("✅ Interaction system initialized successfully")
            
            # Subscribe to key events
            await self._setup_event_subscriptions()
            
            # Initialize multi-agent workflows
            await self._initialize_workflows()
            
        except Exception as e:
            print(f"❌ Failed to initialize interaction system: {e}")
            raise
    
    async def _setup_event_subscriptions(self):
        """Setup event subscriptions for the orchestrator"""
        if self.interaction_enhancer:
            # Subscribe orchestrator to important events
            await self.interaction_enhancer.subscribe_to_events('orchestrator', [
                'arbitrage_opportunity_found',
                'risk_threshold_exceeded',
                'system_health_update',
                'task_completed',
                'service_failure'
            ])
    
    async def _initialize_workflows(self):
        """Initialize multi-agent workflows"""
        print("🤖 Initializing multi-agent workflows...")
        
        # Workflow 1: Enhanced Price Monitoring with Multi-Agent Coordination
        await self._setup_price_monitoring_workflow()
        
        # Workflow 2: Advanced Arbitrage Detection and Execution
        await self._setup_arbitrage_workflow()
        
        # Workflow 3: Risk Management and Portfolio Monitoring
        await self._setup_risk_management_workflow()
        
        # Workflow 4: System Health and Auto-Healing
        await self._setup_health_monitoring_workflow()
    
    async def _setup_price_monitoring_workflow(self):
        """Setup enhanced price monitoring workflow"""
        if self.interaction_enhancer:
            # Coordinate multiple agents for comprehensive price monitoring
            await self.interaction_enhancer.submit_task('coordinate_price_monitoring', {
                'agents': ['market_analyzer', 'data_collector'],
                'mcp_servers': ['mcp_price_feed_server', 'mcp_defi_analyzer_server'],
                'monitoring_frequency': 5,  # seconds
                'alert_thresholds': {
                    'price_change_percent': 2.0,
                    'volume_spike_multiplier': 3.0,
                    'liquidity_drop_percent': 15.0
                }
            })
    
    async def _setup_arbitrage_workflow(self):
        """Setup advanced arbitrage detection and execution workflow"""
        if self.interaction_enhancer:
            # Multi-stage arbitrage workflow
            await self.interaction_enhancer.submit_task('setup_arbitrage_workflow', {
                'detection_agents': ['arbitrage_detector', 'arbitrage_bot'],
                'execution_agents': ['transaction_executor', 'flash_loan_optimizer'],
                'risk_agents': ['risk_manager'],
                'mcp_servers': ['mcp_arbitrage_server', 'mcp_flash_loan_server', 'mcp_risk_manager_server'],
                'workflow_stages': [
                    'price_analysis',
                    'opportunity_detection',
                    'risk_assessment',
                    'execution_planning',
                    'transaction_execution',
                    'result_monitoring'
                ],
                'execution_criteria': {
                    'min_profit_usd': self.min_profit_usd,
                    'max_profit_usd': self.max_profit_usd,
                    'max_risk_score': 7.0,
                    'max_slippage_percent': 1.0
                }
            })
    
    async def _setup_risk_management_workflow(self):
        """Setup comprehensive risk management workflow"""
        if self.interaction_enhancer:
            await self.interaction_enhancer.submit_task('setup_risk_workflow', {
                'risk_agents': ['risk_manager'],
                'monitoring_agents': ['liquidity_manager', 'market_analyzer'],
                'mcp_servers': ['mcp_risk_manager_server', 'mcp_portfolio_server', 'mcp_monitoring_server'],
                'risk_parameters': {
                    'max_position_size_usd': 10000,
                    'max_total_exposure_usd': 50000,
                    'volatility_threshold': 0.05,
                    'correlation_limit': 0.8
                },
                'monitoring_frequency': 30  # seconds
            })
    
    async def _setup_health_monitoring_workflow(self):
        """Setup system health monitoring and auto-healing workflow"""
        if self.interaction_enhancer:
            await self.interaction_enhancer.submit_task('setup_health_workflow', {
                'monitoring_agents': ['healer', 'reporter'],
                'mcp_servers': ['mcp_monitoring_server', 'mcp_notification_server'],
                'health_checks': [
                    'service_availability',
                    'response_times',
                    'error_rates',
                    'resource_usage',
                    'network_connectivity'
                ],
                'auto_healing_enabled': True,
                'alert_thresholds': {
                    'service_downtime_seconds': 60,
                    'error_rate_percent': 5.0,
                    'response_time_ms': 5000
                }
            })
    
    async def _run_enhanced_orchestration_loop(self):
        """Enhanced orchestration loop with interaction capabilities"""
        print("🎯 Starting enhanced orchestration loop...")
        self.is_running = True
        
        # Original orchestration tasks
        base_tasks = [
            asyncio.create_task(self._enhanced_price_monitoring_loop()),
            asyncio.create_task(self._enhanced_opportunity_detection_loop()),
            asyncio.create_task(self._enhanced_execution_coordination_loop()),
            asyncio.create_task(self._enhanced_statistics_reporting_loop()),
            asyncio.create_task(self._admin_control_loop())
        ]
        
        # Add interaction system tasks
        all_tasks = base_tasks + self.interaction_tasks
        
        try:
            await asyncio.gather(*all_tasks)
        except Exception as e:
            print(f"❌ Enhanced orchestration error: {e}")
            self.is_running = False
    
    async def _enhanced_price_monitoring_loop(self):
        """Enhanced price monitoring with multi-agent coordination"""
        print("📊 Starting enhanced price monitoring...")
        
        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(10)
                    continue
                
                # Check gas price first
                gas_price_gwei = self.w3.eth.gas_price / 1e9
                
                if gas_price_gwei > self.max_gas_price_gwei:
                    # Publish high gas price event for agents to react
                    if self.interaction_enhancer:
                        await self.interaction_enhancer.publish_event('high_gas_price', {
                            'gas_price_gwei': gas_price_gwei,
                            'threshold_gwei': self.max_gas_price_gwei
                        })
                    
                    await asyncio.sleep(30)
                    continue
                
                # Enhanced price monitoring with agent coordination
                if self.interaction_enhancer:
                    # Submit coordinated price monitoring task
                    await self.interaction_enhancer.submit_task('enhanced_price_monitoring', {
                        'tokens': list(self.tokens.keys()),
                        'dexs': list(self.dexs.keys()),
                        'gas_price_gwei': gas_price_gwei,
                        'include_predictions': True,
                        'include_sentiment': True
                    })
                else:
                    # Fallback to original price monitoring
                    await self._request_price_updates()
                    await self._update_liquidity_data()
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Enhanced price monitoring error: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(10)
    
    async def _enhanced_opportunity_detection_loop(self):
        """Enhanced opportunity detection with AI agent coordination"""
        print("🔍 Starting enhanced opportunity detection...")
        
        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(10)
                    continue
                
                if self.interaction_enhancer:
                    # Coordinate multiple agents for opportunity detection
                    await self.interaction_enhancer.submit_task('multi_agent_arbitrage_detection', {
                        'primary_detector': 'arbitrage_detector',
                        'secondary_detector': 'arbitrage_bot',
                        'market_analyzer': 'market_analyzer',
                        'risk_assessor': 'risk_manager',
                        'min_profit_usd': self.min_profit_usd,
                        'max_profit_usd': self.max_profit_usd,
                        'analysis_depth': 'comprehensive'
                    })
                    
                    self.interaction_stats['total_interactions'] += 1
                else:
                    # Fallback to original detection
                    opportunities = await self._detect_opportunities()
                    if opportunities:
                        self.stats['opportunities_found'] += len(opportunities)
                        filtered_ops = await self._filter_opportunities(opportunities)
                        if filtered_ops:
                            await self._queue_opportunities(filtered_ops)
                
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"Enhanced opportunity detection error: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(15)
    
    async def _enhanced_execution_coordination_loop(self):
        """Enhanced execution coordination with multi-agent workflows"""
        print("⚡ Starting enhanced execution coordination...")
        
        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(10)
                    continue
                
                if self.interaction_enhancer:
                    # Check for completed arbitrage detection tasks
                    completed_tasks = [task_id for task_id, result in self.interaction_enhancer.task_results.items()
                                     if result.get('task_type') == 'multi_agent_arbitrage_detection']
                    
                    for task_id in completed_tasks:
                        result = self.interaction_enhancer.task_results[task_id]
                        opportunities = result.get('opportunities', [])
                        
                        if opportunities:
                            # Coordinate execution with multiple agents
                            await self.interaction_enhancer.submit_task('coordinate_arbitrage_execution', {
                                'opportunities': opportunities,
                                'executor_agent': 'transaction_executor',
                                'optimizer_agent': 'flash_loan_optimizer',
                                'monitor_agent': 'reporter'
                            })
                        
                        # Clean up processed task result
                        del self.interaction_enhancer.task_results[task_id]
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Enhanced execution coordination error: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(10)
    
    async def _enhanced_statistics_reporting_loop(self):
        """Enhanced statistics reporting with comprehensive metrics"""
        print("📈 Starting enhanced statistics reporting...")
        
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Report every 5 minutes
                
                # Calculate enhanced metrics
                uptime = (datetime.now() - self.system_start_time).total_seconds() / 3600
                
                # Get interaction statistics
                interaction_stats = {}
                if self.interaction_enhancer:
                    interaction_stats = self.interaction_enhancer.get_interaction_stats()
                
                # Enhanced report
                enhanced_stats = {
                    **self.stats,
                    'uptime_hours': uptime,
                    'interaction_stats': interaction_stats,
                    'system_health': await self._calculate_system_health(),
                    'agent_performance': await self._get_agent_performance_metrics()
                }
                
                print("\n" + "="*80)
                print("📊 ENHANCED SYSTEM STATISTICS")
                print("="*80)
                print(f"⏱️  Uptime: {uptime:.2f} hours")
                print(f"💰 Opportunities Found: {enhanced_stats['opportunities_found']}")
                print(f"⚡ Opportunities Executed: {enhanced_stats['opportunities_executed']}")
                print(f"✅ Success Rate: {self._calculate_success_rate():.1f}%")
                print(f"💵 Total Profit: ${enhanced_stats['total_profit_usd']:.2f}")
                print(f"⛽ Total Gas Spent: {enhanced_stats['total_gas_spent']:.4f} ETH")
                print(f"🤖 Agent Interactions: {interaction_stats.get('tasks_processed', 0)}")
                print(f"📡 Events Published: {interaction_stats.get('events_published', 0)}")
                print(f"🏥 System Health: {enhanced_stats['system_health']:.1f}%")
                print("="*80)
                
                # Report to monitoring agent
                if self.interaction_enhancer:
                    await self.interaction_enhancer.submit_task('generate_system_report', {
                        'stats': enhanced_stats,
                        'report_type': 'comprehensive',
                        'include_predictions': True
                    }, target='reporter')
                
            except Exception as e:
                print(f"Enhanced statistics reporting error: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_system_health(self) -> float:
        """Calculate overall system health score"""
        try:
            health_factors = []
            
            # Service availability
            if self.interaction_enhancer:
                unhealthy_services = await self.interaction_enhancer._check_all_service_health()
                total_services = len(self.interaction_enhancer.enhanced_service_map) + len(self.interaction_enhancer.enhanced_agent_map)
                healthy_services = total_services - len(unhealthy_services)
                service_health = (healthy_services / total_services) * 100 if total_services > 0 else 0
                health_factors.append(service_health)
            
            # Success rate
            success_rate = self._calculate_success_rate()
            health_factors.append(success_rate)
            
            # Error rate (inverted)
            total_operations = self.stats.get('opportunities_executed', 1)
            error_rate = (self.stats.get('errors', 0) / total_operations) * 100
            error_health = max(0, 100 - error_rate)
            health_factors.append(error_health)
            
            # Return average health score
            return sum(health_factors) / len(health_factors) if health_factors else 0
            
        except Exception as e:
            print(f"Error calculating system health: {e}")
            return 0
    
    async def _get_agent_performance_metrics(self) -> Dict:
        """Get performance metrics for all agents"""
        try:
            if not self.interaction_enhancer:
                return {}
            
            agent_metrics = {}
            for agent_name in self.interaction_enhancer.enhanced_agent_map.keys():
                # Get agent-specific metrics (this would be implemented by each agent)
                agent_metrics[agent_name] = {
                    'tasks_completed': 0,
                    'avg_response_time': 0,
                    'success_rate': 100,
                    'status': 'active'
                }
            
            return agent_metrics
            
        except Exception as e:
            print(f"Error getting agent performance metrics: {e}")
            return {}
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of operations"""
        total_trades = self.stats.get('successful_trades', 0) + self.stats.get('failed_trades', 0)
        if total_trades == 0:
            return 100.0
        return (self.stats.get('successful_trades', 0) / total_trades) * 100
    
    async def _shutdown_enhanced_system(self):
        """Shutdown the enhanced system gracefully"""
        print("🔄 Shutting down enhanced system...")
        
        self.is_running = False
        
        # Stop interaction system
        if self.interaction_enhancer:
            self.interaction_enhancer.running = False
        
        # Cancel all tasks
        for task in self.interaction_tasks:
            task.cancel()
        
        print("✅ Enhanced system shutdown complete")
    
    async def _handle_enhanced_system_error(self, error):
        """Handle system errors with enhanced recovery"""
        print(f"🚨 Enhanced system error: {error}")
        
        if self.interaction_enhancer:
            # Submit healing task
            await self.interaction_enhancer.submit_task('system_error_recovery', {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'recovery_level': 'full_system'
            }, target='healer')
        
        await self._shutdown_enhanced_system()

if __name__ == "__main__":
    import datetime
    
    async def main():
        # Create and run enhanced orchestrator
        orchestrator = EnhancedDockerOrchestrator()
        
        try:
            await orchestrator.start_enhanced_system()
        except KeyboardInterrupt:
            print("System interrupted by user")
        except Exception as e:
            print(f"System error: {e}")
    
    # Run the enhanced system
    asyncio.run(main())
