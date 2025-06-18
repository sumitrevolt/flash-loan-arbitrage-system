#!/usr/bin/env python3
"""
Enhanced Interaction System for Existing Docker Arbitrage Orchestrator
=====================================================================

This module enhances your existing docker_arbitrage_orchestrator.py with 
advanced interaction capabilities between all your MCP servers and AI agents.
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from queue import PriorityQueue
import uuid

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels for the interaction system"""
    CRITICAL = 1    # Emergency situations, security alerts
    HIGH = 2        # Time-sensitive arbitrage opportunities
    MEDIUM = 3      # Regular market analysis
    LOW = 4         # Background maintenance tasks

@dataclass
class InteractionTask:
    """Task for the interaction system"""
    id: str
    type: str
    source: str
    target: Optional[str]
    priority: TaskPriority
    data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        return self.priority.value < other.priority.value

@dataclass
class SystemEvent:
    """System event for the event bus"""
    id: str
    type: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    targets: Optional[List[str]] = None

class InteractionSystemEnhancer:
    """Enhances the existing orchestrator with interaction capabilities"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.task_queue = PriorityQueue()
        self.event_subscribers: Dict[str, Set[str]] = {}
        self.active_tasks: Dict[str, InteractionTask] = {}
        self.task_results: Dict[str, Any] = {}
        self.running = False
        
        # Enhanced mapping of your existing services with interaction capabilities
        self.enhanced_service_map = {
            # Core MCP Servers with specialized capabilities
            'mcp_price_feed_server': {
                'url': self.orchestrator.mcp_services['price_feed'],
                'capabilities': ['real_time_pricing', 'multi_dex_comparison', 'price_alerts'],
                'event_types': ['price_update', 'price_spike', 'liquidity_change'],
                'priority': 1
            },
            'mcp_arbitrage_server': {
                'url': self.orchestrator.mcp_services['arbitrage'],
                'capabilities': ['opportunity_detection', 'profit_calculation', 'risk_assessment'],
                'event_types': ['arbitrage_opportunity', 'profit_threshold_met'],
                'priority': 1
            },
            'mcp_flash_loan_server': {
                'url': self.orchestrator.mcp_services['flash_loan'],
                'capabilities': ['flash_loan_execution', 'multi_protocol_access', 'loan_optimization'],
                'event_types': ['loan_available', 'loan_executed', 'loan_failed'],
                'priority': 1
            },
            'mcp_blockchain_server': {
                'url': self.orchestrator.mcp_services['blockchain'],
                'capabilities': ['multichain_interaction', 'transaction_monitoring', 'gas_optimization'],
                'event_types': ['transaction_confirmed', 'gas_price_update', 'network_congestion'],
                'priority': 1
            },
            'mcp_liquidity_server': {
                'url': self.orchestrator.mcp_services['liquidity'],
                'capabilities': ['liquidity_monitoring', 'pool_analysis', 'impermanent_loss_calc'],
                'event_types': ['liquidity_added', 'liquidity_removed', 'pool_imbalance'],
                'priority': 1
            },
            'mcp_risk_manager_server': {
                'url': self.orchestrator.mcp_services['risk_manager'],
                'capabilities': ['risk_assessment', 'portfolio_analysis', 'exposure_monitoring'],
                'event_types': ['risk_threshold_exceeded', 'portfolio_rebalance_needed'],
                'priority': 1
            },
            'mcp_defi_analyzer_server': {
                'url': self.orchestrator.mcp_services['defi_analyzer'],
                'capabilities': ['protocol_analysis', 'yield_farming_optimization', 'tvl_monitoring'],
                'event_types': ['protocol_update', 'yield_opportunity', 'tvl_change'],
                'priority': 2
            },
            'mcp_data_analyzer_server': {
                'url': self.orchestrator.mcp_services['data_analyzer'],
                'capabilities': ['pattern_recognition', 'predictive_modeling', 'quantum_analysis'],
                'event_types': ['pattern_detected', 'prediction_update', 'anomaly_detected'],
                'priority': 2
            },
            'mcp_security_server': {
                'url': self.orchestrator.mcp_services['security'],
                'capabilities': ['vulnerability_scanning', 'threat_detection', 'audit_analysis'],
                'event_types': ['security_alert', 'vulnerability_found', 'audit_complete'],
                'priority': 1
            },
            'mcp_monitoring_server': {
                'url': self.orchestrator.mcp_services['monitoring'],
                'capabilities': ['system_monitoring', 'performance_tracking', 'health_checks'],
                'event_types': ['system_alert', 'performance_degradation', 'service_down'],
                'priority': 2
            }
        }
        
        # Enhanced mapping of your existing AI agents
        self.enhanced_agent_map = {
            'flash_loan_optimizer': {
                'url': self.orchestrator.ai_agents['flash_loan_optimizer'],
                'capabilities': ['loan_strategy_optimization', 'profit_maximization', 'cost_minimization'],
                'task_types': ['optimize_flash_loan', 'calculate_optimal_amount', 'strategy_planning']
            },
            'risk_manager': {
                'url': self.orchestrator.ai_agents['risk_manager'],
                'capabilities': ['risk_calculation', 'portfolio_management', 'exposure_control'],
                'task_types': ['assess_risk', 'calculate_var', 'portfolio_analysis']
            },
            'arbitrage_detector': {
                'url': self.orchestrator.ai_agents['arbitrage_detector'],
                'capabilities': ['cross_dex_analysis', 'opportunity_identification', 'profit_estimation'],
                'task_types': ['detect_arbitrage', 'compare_prices', 'estimate_profit']
            },
            'transaction_executor': {
                'url': self.orchestrator.ai_agents['transaction_executor'],
                'capabilities': ['transaction_execution', 'batch_processing', 'failure_handling'],
                'task_types': ['execute_transaction', 'batch_execute', 'retry_failed']
            },
            'market_analyzer': {
                'url': self.orchestrator.ai_agents['market_analyzer'],
                'capabilities': ['market_trend_analysis', 'sentiment_analysis', 'prediction'],
                'task_types': ['analyze_trends', 'predict_movement', 'sentiment_analysis']
            },
            'data_collector': {
                'url': self.orchestrator.ai_agents['data_collector'],
                'capabilities': ['data_aggregation', 'source_verification', 'real_time_feeds'],
                'task_types': ['collect_data', 'verify_sources', 'aggregate_feeds']
            },
            'arbitrage_bot': {
                'url': self.orchestrator.ai_agents['arbitrage_bot'],
                'capabilities': ['automated_trading', 'opportunity_execution', 'performance_optimization'],
                'task_types': ['execute_arbitrage', 'optimize_performance', 'monitor_execution']
            },
            'liquidity_manager': {
                'url': self.orchestrator.ai_agents['liquidity_manager'],
                'capabilities': ['liquidity_optimization', 'pool_management', 'yield_maximization'],
                'task_types': ['manage_liquidity', 'optimize_pools', 'maximize_yield']
            },
            'reporter': {
                'url': self.orchestrator.ai_agents['reporter'],
                'capabilities': ['report_generation', 'data_visualization', 'alert_management'],
                'task_types': ['generate_report', 'create_dashboard', 'send_alert']
            },
            'healer': {
                'url': self.orchestrator.ai_agents['healer'],
                'capabilities': ['error_recovery', 'system_repair', 'auto_healing'],
                'task_types': ['diagnose_issue', 'repair_system', 'prevent_failure']
            }
        }
        
        # Initialize interaction statistics
        self.interaction_stats = {
            'tasks_processed': 0,
            'events_published': 0,
            'services_coordinated': 0,
            'agents_activated': 0,
            'interactions_per_minute': 0,
            'last_interaction': None
        }
    
    async def enhance_orchestrator(self):
        """Enhance the existing orchestrator with interaction capabilities"""
        logger.info("🔧 Enhancing orchestrator with interaction system...")
        
        # Add interaction methods to orchestrator
        self.orchestrator.submit_task = self.submit_task
        self.orchestrator.publish_event = self.publish_event
        self.orchestrator.subscribe_to_events = self.subscribe_to_events
        self.orchestrator.get_interaction_stats = self.get_interaction_stats
        
        # Start interaction loops
        self.running = True
        interaction_tasks = [
            asyncio.create_task(self._task_processing_loop()),
            asyncio.create_task(self._event_bus_loop()),
            asyncio.create_task(self._service_coordination_loop()),
            asyncio.create_task(self._health_interaction_loop())
        ]
        
        logger.info("✅ Interaction system enhancement complete")
        return interaction_tasks
    
    async def submit_task(self, task_type: str, data: Dict, priority: TaskPriority = TaskPriority.MEDIUM, 
                         target: str = None, expires_in_minutes: int = 30) -> str:
        """Submit a task to the interaction system"""
        task_id = str(uuid.uuid4())
        
        task = InteractionTask(
            id=task_id,
            type=task_type,
            source='orchestrator',
            target=target,
            priority=priority,
            data=data,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=expires_in_minutes)
        )
        
        self.task_queue.put(task)
        self.active_tasks[task_id] = task
        
        logger.info(f"📋 Task submitted: {task_type} (ID: {task_id[:8]}) - Priority: {priority.name}")
        return task_id
    
    async def publish_event(self, event_type: str, data: Dict, targets: List[str] = None):
        """Publish an event to the event bus"""
        event = SystemEvent(
            id=str(uuid.uuid4()),
            type=event_type,
            source='orchestrator',
            data=data,
            timestamp=datetime.now(),
            targets=targets
        )
        
        # Send to subscribers
        subscribers = self.event_subscribers.get(event_type, set())
        if targets:
            subscribers.update(targets)
        
        for subscriber in subscribers:
            await self._send_event_to_service(subscriber, event)
        
        self.interaction_stats['events_published'] += 1
        logger.debug(f"📡 Event published: {event_type} to {len(subscribers)} subscribers")
    
    async def subscribe_to_events(self, service_name: str, event_types: List[str]):
        """Subscribe a service to event types"""
        for event_type in event_types:
            if event_type not in self.event_subscribers:
                self.event_subscribers[event_type] = set()
            self.event_subscribers[event_type].add(service_name)
        
        logger.info(f"🔔 {service_name} subscribed to {len(event_types)} event types")
    
    async def _task_processing_loop(self):
        """Process tasks from the task queue"""
        while self.running:
            try:
                if not self.task_queue.empty():
                    task = self.task_queue.get()
                    
                    # Check if task has expired
                    if task.expires_at and datetime.now() > task.expires_at:
                        logger.warning(f"⏰ Task {task.id[:8]} expired, skipping")
                        self.active_tasks.pop(task.id, None)
                        continue
                    
                    # Find suitable service/agent for the task
                    target = await self._find_task_executor(task)
                    
                    if target:
                        await self._execute_task(task, target)
                    else:
                        # Retry with backoff
                        if task.retries < task.max_retries:
                            task.retries += 1
                            await asyncio.sleep(2 ** task.retries)  # Exponential backoff
                            self.task_queue.put(task)
                        else:
                            logger.error(f"❌ Task {task.id[:8]} failed after {task.max_retries} retries")
                            self.active_tasks.pop(task.id, None)
                
                await asyncio.sleep(0.1)  # Prevent busy waiting
                
            except Exception as e:
                logger.error(f"Task processing error: {e}")
                await asyncio.sleep(1)
    
    async def _find_task_executor(self, task: InteractionTask) -> Optional[str]:
        """Find the best service/agent to execute a task"""
        if task.target:
            # Direct target specified
            return task.target
        
        # Task type to capability mapping
        task_capability_map = {
            'price_analysis': ['real_time_pricing', 'market_trend_analysis'],
            'arbitrage_detection': ['opportunity_detection', 'cross_dex_analysis'],
            'risk_assessment': ['risk_calculation', 'portfolio_analysis'],
            'flash_loan_execution': ['flash_loan_execution', 'loan_strategy_optimization'],
            'liquidity_analysis': ['liquidity_monitoring', 'pool_analysis'],
            'transaction_execution': ['transaction_execution', 'automated_trading'],
            'market_analysis': ['market_trend_analysis', 'sentiment_analysis'],
            'data_collection': ['data_aggregation', 'real_time_feeds'],
            'system_monitoring': ['system_monitoring', 'health_checks'],
            'security_scan': ['vulnerability_scanning', 'threat_detection']
        }
        
        required_capabilities = task_capability_map.get(task.type, [])
        
        # Check MCP servers first (for data and system tasks)
        for service_name, service_info in self.enhanced_service_map.items():
            if any(cap in service_info['capabilities'] for cap in required_capabilities):
                return service_name
        
        # Check AI agents second (for decision and execution tasks)
        for agent_name, agent_info in self.enhanced_agent_map.items():
            if (task.type in agent_info.get('task_types', []) or 
                any(cap in agent_info['capabilities'] for cap in required_capabilities)):
                return agent_name
        
        return None
    
    async def _execute_task(self, task: InteractionTask, target: str):
        """Execute a task on the target service/agent"""
        try:
            # Determine target URL
            target_url = None
            if target in self.enhanced_service_map:
                target_url = self.enhanced_service_map[target]['url']
            elif target in self.enhanced_agent_map:
                target_url = self.enhanced_agent_map[target]['url']
            
            if not target_url:
                logger.error(f"❌ No URL found for target: {target}")
                return
            
            # Send task to target
            task_payload = {
                'task_id': task.id,
                'task_type': task.type,
                'data': task.data,
                'priority': task.priority.name,
                'source': task.source
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{target_url}/process_task", 
                                      json=task_payload, 
                                      timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.task_results[task.id] = result
                        self.active_tasks.pop(task.id, None)
                        self.interaction_stats['tasks_processed'] += 1
                        
                        logger.info(f"✅ Task {task.id[:8]} completed by {target}")
                        
                        # Publish completion event
                        await self.publish_event('task_completed', {
                            'task_id': task.id,
                            'task_type': task.type,
                            'executor': target,
                            'result': result
                        })
                    else:
                        logger.warning(f"⚠️ Task {task.id[:8]} failed on {target}: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"Task execution error for {task.id[:8]} on {target}: {e}")
    
    async def _event_bus_loop(self):
        """Event bus processing loop"""
        while self.running:
            try:
                # Process orchestrator events and relay them
                await self._process_orchestrator_events()
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Event bus error: {e}")
                await asyncio.sleep(5)
    
    async def _process_orchestrator_events(self):
        """Process events from the orchestrator and relay them to subscribers"""
        # Check for new arbitrage opportunities
        if hasattr(self.orchestrator, 'stats') and self.orchestrator.stats.get('last_opportunity'):
            await self.publish_event('arbitrage_opportunity_found', {
                'opportunity': self.orchestrator.stats['last_opportunity'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Check for system health changes
        if hasattr(self.orchestrator, 'stats'):
            health_data = {
                'uptime_hours': self.orchestrator.stats.get('uptime_hours', 0),
                'success_rate': self._calculate_success_rate(),
                'error_count': self.orchestrator.stats.get('errors', 0)
            }
            
            await self.publish_event('system_health_update', health_data)
    
    async def _service_coordination_loop(self):
        """Coordinate services for complex multi-step operations"""
        while self.running:
            try:
                # Coordinate flash loan arbitrage workflow
                await self._coordinate_arbitrage_workflow()
                
                # Coordinate risk management workflow
                await self._coordinate_risk_management()
                
                # Coordinate data collection and analysis
                await self._coordinate_data_analysis()
                
                await asyncio.sleep(30)  # Coordinate every 30 seconds
                
            except Exception as e:
                logger.error(f"Service coordination error: {e}")
                await asyncio.sleep(10)
    
    async def _coordinate_arbitrage_workflow(self):
        """Coordinate the complete arbitrage detection and execution workflow"""
        try:
            # Step 1: Request price data
            price_task_id = await self.submit_task('price_analysis', {
                'tokens': list(self.orchestrator.tokens.keys()),
                'dexs': list(self.orchestrator.dexs.keys())
            }, TaskPriority.HIGH)
            
            # Step 2: Detect arbitrage opportunities
            arbitrage_task_id = await self.submit_task('arbitrage_detection', {
                'price_data_task_id': price_task_id,
                'min_profit': self.orchestrator.min_profit_usd,
                'max_profit': self.orchestrator.max_profit_usd
            }, TaskPriority.HIGH)
            
            # Step 3: Risk assessment
            risk_task_id = await self.submit_task('risk_assessment', {
                'arbitrage_task_id': arbitrage_task_id
            }, TaskPriority.HIGH)
            
            self.interaction_stats['services_coordinated'] += 1
            
        except Exception as e:
            logger.error(f"Arbitrage workflow coordination error: {e}")
    
    async def _coordinate_risk_management(self):
        """Coordinate risk management across all operations"""
        try:
            # Monitor portfolio exposure
            await self.submit_task('risk_assessment', {
                'assessment_type': 'portfolio_exposure',
                'current_positions': await self._get_current_positions()
            }, TaskPriority.MEDIUM)
            
            # Check gas price risks
            await self.submit_task('risk_assessment', {
                'assessment_type': 'gas_price_risk',
                'current_gas_price': self.orchestrator.w3.eth.gas_price / 1e9
            }, TaskPriority.MEDIUM)
            
        except Exception as e:
            logger.error(f"Risk management coordination error: {e}")
    
    async def _coordinate_data_analysis(self):
        """Coordinate data collection and analysis"""
        try:
            # Collect market data
            await self.submit_task('data_collection', {
                'sources': ['dex_prices', 'liquidity_pools', 'gas_prices'],
                'frequency': 'real_time'
            }, TaskPriority.LOW)
            
            # Analyze trends
            await self.submit_task('market_analysis', {
                'analysis_type': 'trend_detection',
                'timeframe': '1h'
            }, TaskPriority.LOW)
            
        except Exception as e:
            logger.error(f"Data analysis coordination error: {e}")
    
    async def _health_interaction_loop(self):
        """Monitor health of all services and coordinate healing"""
        while self.running:
            try:
                # Check service health
                unhealthy_services = await self._check_all_service_health()
                
                if unhealthy_services:
                    # Coordinate healing
                    await self.submit_task('system_healing', {
                        'unhealthy_services': unhealthy_services
                    }, TaskPriority.CRITICAL, target='healer')
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health interaction error: {e}")
                await asyncio.sleep(30)
    
    async def _check_all_service_health(self) -> List[str]:
        """Check health of all services and return unhealthy ones"""
        unhealthy = []
        
        # Check MCP servers
        for service_name, service_info in self.enhanced_service_map.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{service_info['url']}/health", timeout=5) as response:
                        if response.status != 200:
                            unhealthy.append(service_name)
            except:
                unhealthy.append(service_name)
        
        # Check AI agents
        for agent_name, agent_info in self.enhanced_agent_map.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{agent_info['url']}/health", timeout=5) as response:
                        if response.status != 200:
                            unhealthy.append(agent_name)
            except:
                unhealthy.append(agent_name)
        
        return unhealthy
    
    async def _send_event_to_service(self, service_name: str, event: SystemEvent):
        """Send an event to a specific service"""
        try:
            service_url = None
            if service_name in self.enhanced_service_map:
                service_url = self.enhanced_service_map[service_name]['url']
            elif service_name in self.enhanced_agent_map:
                service_url = self.enhanced_agent_map[service_name]['url']
            
            if service_url:
                event_payload = asdict(event)
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{service_url}/receive_event", 
                                          json=event_payload, 
                                          timeout=10) as response:
                        if response.status == 200:
                            logger.debug(f"📡 Event {event.type} sent to {service_name}")
                        
        except Exception as e:
            logger.debug(f"Failed to send event to {service_name}: {e}")
    
    async def _get_current_positions(self) -> Dict:
        """Get current trading positions"""
        # This would integrate with your position tracking
        return {
            'total_value_usd': 0,
            'positions': [],
            'exposure_by_token': {}
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of operations"""
        stats = self.orchestrator.stats
        total_trades = stats.get('successful_trades', 0) + stats.get('failed_trades', 0)
        if total_trades == 0:
            return 0.0
        return stats.get('successful_trades', 0) / total_trades * 100
    
    def get_interaction_stats(self) -> Dict:
        """Get interaction system statistics"""
        self.interaction_stats['last_interaction'] = datetime.now().isoformat()
        return self.interaction_stats

# Enhanced orchestrator methods to add interaction capabilities
async def add_interaction_capabilities_to_orchestrator(orchestrator):
    """Add interaction capabilities to existing orchestrator"""
    
    # Create and initialize interaction enhancer
    enhancer = InteractionSystemEnhancer(orchestrator)
    
    # Start interaction system
    interaction_tasks = await enhancer.enhance_orchestrator()
    
    logger.info("🚀 Interaction system fully integrated with orchestrator")
    
    return enhancer, interaction_tasks
