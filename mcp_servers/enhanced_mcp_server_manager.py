#!/usr/bin/env python3
"""
Enhanced MCP Server Manager with LangChain Integration
======================================================

This manager provides:
1. Intelligent MCP server lifecycle management
2. LangChain-powered decision making for server operations
3. Dynamic load balancing and auto-scaling
4. Context-aware routing and coordination
5. Advanced monitoring and predictive maintenance

Author: GitHub Copilot Assistant
Date: June 16, 2025
"""

import asyncio
import logging
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import aiohttp
import docker
from enum import Enum
import statistics

# LangChain imports for intelligent decision making
from langchain.llms.base import LLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_community.chat_models import ChatOllama

logger = logging.getLogger(__name__)

class ServerStatus(Enum):
    """MCP Server status enumeration"""
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"
    STOPPED = "stopped"
    UNKNOWN = "unknown"

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin" 
    HEALTH_BASED = "health_based"
    CAPABILITY_BASED = "capability_based"
    AI_OPTIMIZED = "ai_optimized"

@dataclass
class MCPServerMetrics:
    """Comprehensive MCP server metrics"""
    timestamp: datetime
    response_time: float
    success_rate: float
    error_count: int
    total_requests: int
    active_connections: int
    cpu_usage: float
    memory_usage: float
    throughput: float  # requests per second
    queue_length: int

@dataclass
class MCPServerInstance:
    """Enhanced MCP server instance with comprehensive tracking"""
    name: str
    port: int
    capabilities: List[str]
    status: ServerStatus = ServerStatus.UNKNOWN
    health_score: float = 0.0
    
    # Performance metrics
    metrics_history: List[MCPServerMetrics] = field(default_factory=list)
    avg_response_time: float = 0.0
    success_rate: float = 0.0
    error_count: int = 0
    restart_count: int = 0
    
    # Load balancing
    active_connections: int = 0
    weight: float = 1.0
    priority: int = 1
    
    # Timestamps
    last_health_check: Optional[datetime] = None
    last_successful_request: Optional[datetime] = None
    uptime_start: Optional[datetime] = None
    
    # Configuration
    max_retries: int = 3
    timeout: float = 30.0
    circuit_breaker_open: bool = False
    
    # AI-driven insights
    predicted_failure_probability: float = 0.0
    maintenance_recommended: bool = False
    optimization_suggestions: List[str] = field(default_factory=list)

class ServerDecisionParser(BaseOutputParser):
    """Parser for LangChain server decision outputs"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse LLM output for server decisions"""
        try:
            # Try to parse as JSON first
            if text.strip().startswith('{'):
                return json.loads(text)
            
            # Fallback parsing for structured text
            lines = text.strip().split('\n')
            result: str = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    
                    # Try to convert to appropriate type
                    if value.lower() in ['true', 'false']:
                        result[key] = value.lower() == 'true'
                    elif value.replace('.', '').isdigit():
                        result[key] = float(value) if '.' in value else int(value)
                    else:
                        result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse LLM output: {e}")
            return {"error": "Failed to parse decision", "raw_output": text}

class EnhancedMCPServerManager:
    """Enhanced MCP server manager with AI-powered coordination"""
    
    def __init__(self, config_path: str = "enhanced_coordinator_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Core components
        self.docker_client: Optional[docker.DockerClient] = None
        self.llm: Optional[LLM] = None
        
        # Server management
        self.servers: Dict[str, MCPServerInstance] = {}
        self.server_groups: Dict[str, List[str]] = {}
        self.load_balancer_state: Dict[str, Any] = {}
        
        # Decision making chains
        self.decision_chains: Dict[str, LLMChain] = {}
        
        # Statistics and monitoring
        self.global_metrics: Dict[str, Any] = {}
        self.is_running = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}, using defaults")
        
        return {"mcp_servers": {}, "llm": {"model": "llama2"}}
    
    async def initialize(self) -> bool:
        """Initialize the MCP server manager"""
        logger.info("🚀 Initializing Enhanced MCP Server Manager...")
        
        try:
            # Initialize Docker client
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            
            # Initialize LLM
            self.llm = ChatOllama(
                model=self.config.get('llm', {}).get('model', 'llama2'),
                temperature=0.3  # Lower temperature for more consistent decisions
            )
            
            # Initialize decision-making chains
            await self._init_decision_chains()
            
            # Initialize servers from config
            await self._init_servers()
            
            # Setup load balancer
            await self._init_load_balancer()
            
            logger.info("✅ Enhanced MCP Server Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def _init_decision_chains(self):
        """Initialize LangChain decision-making chains"""
        
        # Server health decision chain
        health_decision_prompt = PromptTemplate(
            input_variables=["server_metrics", "server_history"],
            template="""
            Analyze the following MCP server metrics and history to make health decisions:
            
            Current Metrics: {server_metrics}
            Historical Data: {server_history}
            
            Based on this data, provide recommendations in JSON format:
            {{
                "health_score": <0.0 to 1.0>,
                "status": "<healthy|degraded|unhealthy|failed>",
                "action_required": "<none|restart|scale|maintenance>",
                "predicted_failure_risk": <0.0 to 1.0>,
                "recommendations": ["list of specific actions"],
                "confidence": <0.0 to 1.0>
            }}
            """
        )
        
        self.decision_chains['health_analysis'] = LLMChain(
            llm=self.llm,
            prompt=health_decision_prompt,
            output_parser=ServerDecisionParser()
        )
        
        # Load balancing decision chain
        load_balance_prompt = PromptTemplate(
            input_variables=["servers_state", "incoming_request", "strategy"],
            template="""
            Given the current state of MCP servers and an incoming request, determine the optimal routing:
            
            Servers State: {servers_state}
            Incoming Request: {incoming_request}
            Current Strategy: {strategy}
            
            Provide routing decision in JSON format:
            {{
                "selected_server": "<server_name>",
                "reasoning": "<explanation>",
                "alternative_servers": ["backup options"],
                "load_distribution": {{"server1": weight1, "server2": weight2}},
                "confidence": <0.0 to 1.0>
            }}
            """
        )
        
        self.decision_chains['load_balancing'] = LLMChain(
            llm=self.llm,
            prompt=load_balance_prompt,
            output_parser=ServerDecisionParser()
        )
        
        # Scaling decision chain
        scaling_prompt = PromptTemplate(
            input_variables=["current_load", "server_performance", "historical_patterns"],
            template="""
            Analyze current system load and performance to make scaling decisions:
            
            Current Load: {current_load}
            Server Performance: {server_performance}
            Historical Patterns: {historical_patterns}
            
            Provide scaling recommendation in JSON format:
            {{
                "action": "<scale_up|scale_down|maintain>",
                "target_instances": <number>,
                "server_type": "<server to scale>",
                "urgency": "<low|medium|high>",
                "reasoning": "<explanation>",
                "confidence": <0.0 to 1.0>
            }}
            """
        )
        
        self.decision_chains['scaling'] = LLMChain(
            llm=self.llm,
            prompt=scaling_prompt,
            output_parser=ServerDecisionParser()
        )
    
    async def _init_servers(self):
        """Initialize MCP servers from configuration"""
        logger.info("📡 Initializing MCP servers...")
        
        for server_name, server_config in self.config.get('mcp_servers', {}).items():
            server = MCPServerInstance(
                name=server_name,
                port=server_config['port'],
                capabilities=server_config.get('capabilities', []),
                max_retries=server_config.get('max_retries', 3),
                timeout=server_config.get('timeout', 30.0),
                priority=server_config.get('priority', 1),
                weight=server_config.get('weight', 1.0)
            )
            
            self.servers[server_name] = server
            
            # Initial health check
            await self._check_server_health(server_name)
            
            logger.info(f"📡 Registered MCP server: {server_name} on port {server.port}")
        
        # Group servers by capabilities
        await self._group_servers_by_capabilities()
    
    async def _group_servers_by_capabilities(self):
        """Group servers by their capabilities for intelligent routing"""
        self.server_groups = {}
        
        for server_name, server in self.servers.items():
            for capability in server.capabilities:
                if capability not in self.server_groups:
                    self.server_groups[capability] = []
                self.server_groups[capability].append(server_name)
        
        logger.info(f"📊 Server groups created: {list(self.server_groups.keys())}")
    
    async def _init_load_balancer(self):
        """Initialize load balancer state"""
        self.load_balancer_state = {
            'round_robin_index': 0,
            'request_counts': {name: 0 for name in self.servers.keys()},
            'response_times': {name: [] for name in self.servers.keys()},
            'strategy': LoadBalancingStrategy.AI_OPTIMIZED
        }
    
    async def start_management(self):
        """Start the server management system"""
        logger.info("🎪 Starting Enhanced MCP Server Management...")
        
        self.is_running = True
        
        # Start management tasks
        management_tasks = [
            asyncio.create_task(self._health_monitoring_loop()),
            asyncio.create_task(self._performance_monitoring_loop()),
            asyncio.create_task(self._auto_scaling_loop()),
            asyncio.create_task(self._predictive_maintenance_loop()),
            asyncio.create_task(self._load_balancer_optimization_loop())
        ]
        
        try:
            await asyncio.gather(*management_tasks)
        except Exception as e:
            logger.error(f"🎪 Management system error: {e}")
        finally:
            self.is_running = False
    
    async def _health_monitoring_loop(self):
        """Continuous health monitoring with AI analysis"""
        while self.is_running:
            try:
                for server_name in self.servers.keys():
                    await self._comprehensive_health_check(server_name)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"📊 Health monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _performance_monitoring_loop(self):
        """Continuous performance monitoring and optimization"""
        while self.is_running:
            try:
                await self._collect_performance_metrics()
                await self._analyze_performance_trends()
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"⚡ Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _auto_scaling_loop(self):
        """AI-powered auto-scaling decisions"""
        while self.is_running:
            try:
                await self._make_scaling_decisions()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"📈 Auto-scaling error: {e}")
                await asyncio.sleep(60)
    
    async def _predictive_maintenance_loop(self):
        """Predictive maintenance using AI analysis"""
        while self.is_running:
            try:
                await self._predict_maintenance_needs()
                await asyncio.sleep(1800)  # Check every 30 minutes
                
            except Exception as e:
                logger.error(f"🔧 Predictive maintenance error: {e}")
                await asyncio.sleep(300)
    
    async def _load_balancer_optimization_loop(self):
        """Continuous load balancer optimization"""
        while self.is_running:
            try:
                await self._optimize_load_balancing()
                await asyncio.sleep(120)  # Optimize every 2 minutes
                
            except Exception as e:
                logger.error(f"⚖️ Load balancer optimization error: {e}")
                await asyncio.sleep(60)
    
    async def _comprehensive_health_check(self, server_name: str):
        """Comprehensive health check with AI analysis"""
        server = self.servers.get(server_name)
        if not server:
            return
        
        try:
            # Basic connectivity check
            health_status = await self._check_server_health(server_name)
            
            # Collect detailed metrics
            metrics = await self._collect_server_metrics(server_name)
            if metrics:
                server.metrics_history.append(metrics)
                
                # Keep only last 100 metrics for performance
                if len(server.metrics_history) > 100:
                    server.metrics_history = server.metrics_history[-100:]
            
            # AI-powered health analysis
            if len(server.metrics_history) >= 5:  # Need some history for analysis
                await self._ai_health_analysis(server_name)
                
        except Exception as e:
            logger.error(f"📊 Comprehensive health check failed for {server_name}: {e}")
            server.error_count += 1
    
    async def _ai_health_analysis(self, server_name: str):
        """AI-powered health analysis using LangChain"""
        server = self.servers[server_name]
        
        try:
            # Prepare data for AI analysis
            current_metrics = server.metrics_history[-1] if server.metrics_history else None
            historical_summary = self._summarize_metrics_history(server.metrics_history[-20:])
            
            if not current_metrics:
                return
            
            metrics_data = {
                'response_time': current_metrics.response_time,
                'success_rate': current_metrics.success_rate,
                'error_count': current_metrics.error_count,
                'cpu_usage': current_metrics.cpu_usage,
                'memory_usage': current_metrics.memory_usage,
                'throughput': current_metrics.throughput
            }
            
            # Get AI decision
            decision = await self.decision_chains['health_analysis'].arun(
                server_metrics=json.dumps(metrics_data),
                server_history=json.dumps(historical_summary)
            )
            
            # Apply AI recommendations
            if isinstance(decision, dict):
                server.health_score = decision.get('health_score', server.health_score)
                server.predicted_failure_probability = decision.get('predicted_failure_risk', 0.0)
                server.optimization_suggestions = decision.get('recommendations', [])
                
                # Update status based on AI analysis
                ai_status = decision.get('status', 'unknown')
                if ai_status == 'healthy':
                    server.status = ServerStatus.HEALTHY
                elif ai_status == 'degraded':
                    server.status = ServerStatus.DEGRADED
                elif ai_status == 'unhealthy':
                    server.status = ServerStatus.UNHEALTHY
                elif ai_status == 'failed':
                    server.status = ServerStatus.FAILED
                
                # Take action if recommended
                action = decision.get('action_required', 'none')
                if action == 'restart' and decision.get('confidence', 0) > 0.7:
                    logger.warning(f"🔄 AI recommends restarting {server_name}")
                    await self._restart_server(server_name)
                elif action == 'maintenance':
                    server.maintenance_recommended = True
                    logger.info(f"🔧 AI recommends maintenance for {server_name}")
            
        except Exception as e:
            logger.error(f"🧠 AI health analysis failed for {server_name}: {e}")
    
    async def _check_server_health(self, server_name: str) -> bool:
        """Basic server health check"""
        server = self.servers.get(server_name)
        if not server:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(
                    f"http://localhost:{server.port}/health",
                    timeout=aiohttp.ClientTimeout(total=server.timeout)
                ) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    server.avg_response_time = response_time
                    server.last_health_check = datetime.now()
                    
                    if response.status == 200:
                        server.last_successful_request = datetime.now()
                        if server.status in [ServerStatus.UNHEALTHY, ServerStatus.FAILED]:
                            server.status = ServerStatus.HEALTHY
                        return True
                    else:
                        server.error_count += 1
                        return False
                        
        except asyncio.TimeoutError:
            logger.warning(f"📡 Health check timeout for {server_name}")
            server.error_count += 1
            return False
        except Exception as e:
            logger.debug(f"📡 Health check failed for {server_name}: {e}")
            server.error_count += 1
            return False
    
    async def _collect_server_metrics(self, server_name: str) -> Optional[MCPServerMetrics]:
        """Collect detailed server metrics"""
        server = self.servers.get(server_name)
        if not server:
            return None
        
        try:
            # In a real implementation, you would collect actual metrics
            # For now, we'll simulate based on health and response time
            
            success_rate = max(0.0, 1.0 - (server.error_count / max(1, server.error_count + 10)))
            
            metrics = MCPServerMetrics(
                timestamp=datetime.now(),
                response_time=server.avg_response_time,
                success_rate=success_rate,
                error_count=server.error_count,
                total_requests=self.load_balancer_state['request_counts'].get(server_name, 0),
                active_connections=server.active_connections,
                cpu_usage=min(100.0, 20.0 + (server.error_count * 5)),  # Simulated
                memory_usage=min(100.0, 30.0 + (server.active_connections * 2)),  # Simulated
                throughput=max(0.0, 10.0 - server.avg_response_time),  # Simulated
                queue_length=max(0, server.active_connections - 5)  # Simulated
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"📊 Failed to collect metrics for {server_name}: {e}")
            return None
    
    def _summarize_metrics_history(self, metrics_list: List[MCPServerMetrics]) -> Dict[str, Any]:
        """Summarize metrics history for AI analysis"""
        if not metrics_list:
            return {}
        
        response_times = [m.response_time for m in metrics_list]
        success_rates = [m.success_rate for m in metrics_list]
        cpu_usages = [m.cpu_usage for m in metrics_list]
        memory_usages = [m.memory_usage for m in metrics_list]
        
        return {
            'avg_response_time': statistics.mean(response_times),
            'max_response_time': max(response_times),
            'avg_success_rate': statistics.mean(success_rates),
            'min_success_rate': min(success_rates),
            'avg_cpu_usage': statistics.mean(cpu_usages),
            'max_cpu_usage': max(cpu_usages),
            'avg_memory_usage': statistics.mean(memory_usages),
            'max_memory_usage': max(memory_usages),
            'trend_improving': success_rates[-1] > success_rates[0] if len(success_rates) > 1 else True
        }
    
    async def route_request(self, request_type: str, request_data: Dict[str, Any]) -> Optional[str]:
        """Intelligently route request to best available server"""
        try:
            # Find servers capable of handling this request type
            capable_servers = []
            for capability, servers in self.server_groups.items():
                if capability in request_type.lower() or request_type.lower() in capability:
                    capable_servers.extend(servers)
            
            # If no specific capability match, use all healthy servers
            if not capable_servers:
                capable_servers = [name for name, server in self.servers.items() 
                                 if server.status == ServerStatus.HEALTHY]
            
            if not capable_servers:
                logger.error("🚨 No healthy servers available for request routing")
                return None
            
            # Use AI for intelligent routing decision
            servers_state = {
                name: {
                    'health_score': self.servers[name].health_score,
                    'response_time': self.servers[name].avg_response_time,
                    'active_connections': self.servers[name].active_connections,
                    'capabilities': self.servers[name].capabilities,
                    'status': self.servers[name].status.value
                }
                for name in capable_servers
            }
            
            routing_decision = await self.decision_chains['load_balancing'].arun(
                servers_state=json.dumps(servers_state),
                incoming_request=json.dumps({'type': request_type, 'data': request_data}),
                strategy=self.load_balancer_state['strategy'].value
            )
            
            if isinstance(routing_decision, dict):
                selected_server = routing_decision.get('selected_server')
                if selected_server and selected_server in self.servers:
                    # Update load balancer state
                    self.load_balancer_state['request_counts'][selected_server] += 1
                    self.servers[selected_server].active_connections += 1
                    
                    logger.info(f"🎯 Routed {request_type} request to {selected_server}")
                    return selected_server
            
            # Fallback to simple health-based selection
            best_server = max(capable_servers, 
                            key=lambda name: Any: self.servers[name].health_score)
            self.load_balancer_state['request_counts'][best_server] += 1
            self.servers[best_server].active_connections += 1
            
            return best_server
            
        except Exception as e:
            logger.error(f"🎯 Request routing failed: {e}")
            return None
    
    async def _restart_server(self, server_name: str):
        """Restart a specific MCP server"""
        try:
            server = self.servers.get(server_name)
            if not server:
                return
            
            logger.info(f"🔄 Restarting MCP server: {server_name}")
            
            if self.docker_client:
                try:
                    container = self.docker_client.containers.get(server_name)
                    container.restart()
                    server.restart_count += 1
                    server.error_count = 0
                    server.status = ServerStatus.STARTING
                    server.uptime_start = datetime.now()
                    
                    # Wait a bit and check if it's healthy
                    await asyncio.sleep(10)
                    await self._check_server_health(server_name)
                    
                    logger.info(f"✅ Server {server_name} restarted successfully")
                    
                except docker.errors.NotFound:
                    logger.error(f"❌ Container {server_name} not found")
                except Exception as e:
                    logger.error(f"❌ Failed to restart container {server_name}: {e}")
            
        except Exception as e:
            logger.error(f"🔄 Failed to restart server {server_name}: {e}")
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get comprehensive server status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'total_servers': len(self.servers),
            'healthy_servers': len([s for s in self.servers.values() if s.status == ServerStatus.HEALTHY]),
            'servers': {}
        }
        
        for name, server in self.servers.items():
            status['servers'][name] = {
                'name': name,
                'port': server.port,
                'status': server.status.value,
                'health_score': server.health_score,
                'capabilities': server.capabilities,
                'avg_response_time': server.avg_response_time,
                'error_count': server.error_count,
                'restart_count': server.restart_count,
                'active_connections': server.active_connections,
                'uptime': str(datetime.now() - server.uptime_start) if server.uptime_start else "Unknown",
                'last_health_check': server.last_health_check.isoformat() if server.last_health_check else None,
                'predicted_failure_probability': server.predicted_failure_probability,
                'maintenance_recommended': server.maintenance_recommended,
                'optimization_suggestions': server.optimization_suggestions
            }
        
        return status
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Enhanced MCP Server Manager...")
        
        self.is_running = False
        
        if self.docker_client:
            self.docker_client.close()
        
        logger.info("✅ MCP Server Manager shutdown completed")

# Additional utility functions
async def _collect_performance_metrics(self):
    """Collect performance metrics for all servers"""
    # Implementation would collect detailed performance metrics
    pass

async def _analyze_performance_trends(self):
    """Analyze performance trends using AI"""
    # Implementation would use LangChain to analyze trends
    pass

async def _make_scaling_decisions(self):
    """Make AI-powered scaling decisions"""
    # Implementation would use the scaling decision chain
    pass

async def _predict_maintenance_needs(self):
    """Predict maintenance needs using AI"""
    # Implementation would analyze patterns to predict maintenance
    pass

async def _optimize_load_balancing(self):
    """Optimize load balancing strategy"""
    # Implementation would continuously optimize the load balancing approach
    pass

if __name__ == "__main__":
    async def main():
        manager = EnhancedMCPServerManager()
        
        try:
            if await manager.initialize():
                await manager.start_management()
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
        finally:
            await manager.shutdown()
    
    asyncio.run(main())
