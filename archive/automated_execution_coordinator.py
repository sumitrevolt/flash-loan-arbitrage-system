#!/usr/bin/env python3
"""
Automated Execution Coordinator for Enhanced LangChain Flash Loan System

This module provides fully automated execution and coordination of all MCP servers
and agents, ensuring seamless operation of the entire flash loan ecosystem.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
import yaml

# External imports
import aiohttp
import redis.asyncio as redis
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import docker
from docker.types import ServiceMode, RestartPolicy, Resources

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor
from langchain.memory import ConversationSummaryBufferMemory
from langchain.callbacks.base import BaseCallbackHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
execution_counter = Counter('automated_executions_total', 'Total automated executions')
active_agents_gauge = Gauge('active_agents', 'Number of active agents', ['type'])
mcp_server_health = Gauge('mcp_server_health', 'MCP server health status', ['server'])
execution_latency = Histogram('execution_latency_seconds', 'Execution latency')
profit_gauge = Gauge('cumulative_profit_usd', 'Cumulative profit in USD')

class ExecutionState(Enum):
    """Execution pipeline states"""
    IDLE = auto()
    SCANNING = auto()
    ANALYZING = auto()
    DECIDING = auto()
    EXECUTING = auto()
    MONITORING = auto()
    COMPLETED = auto()
    FAILED = auto()

class ServerType(Enum):
    """MCP Server types"""
    MARKET_DATA = "market_data"
    FLASH_LOAN = "flash_loan"
    DEX_AGGREGATOR = "dex_aggregator"
    RISK_ANALYZER = "risk_analyzer"
    GAS_OPTIMIZER = "gas_optimizer"
    MEV_PROTECTOR = "mev_protector"
    PROFIT_CALCULATOR = "profit_calculator"
    EXECUTION_ENGINE = "execution_engine"

@dataclass
class MCPServer:
    """MCP Server configuration"""
    name: str
    type: ServerType
    host: str
    port: int
    health_endpoint: str = "/health"
    capabilities: List[str] = field(default_factory=list)
    status: str = "unknown"
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionTask:
    """Automated execution task"""
    task_id: str
    opportunity_type: str
    market_data: Dict[str, Any]
    risk_assessment: Dict[str, float]
    execution_params: Dict[str, Any]
    state: ExecutionState = ExecutionState.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    profit_usd: float = 0.0

class AutomatedExecutionCoordinator:
    """
    Main coordinator for automated execution and MCP server orchestration
    """
    
    def __init__(self, config_path: str = "config/automation.yaml"):
        self.config = self._load_config(config_path)
        self.mcp_servers: Dict[str, MCPServer] = {}
        self.active_agents: Dict[str, Any] = {}
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.execution_history: deque = deque(maxlen=1000)
        self.redis_client: Optional[redis.Redis] = None
        self.docker_client: Optional[docker.DockerClient] = None
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # Performance tracking
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_profit_usd": 0.0,
            "average_execution_time": 0.0,
            "best_opportunity_type": None
        }
        
        # Agent coordination
        self.agent_assignments: Dict[str, Set[str]] = defaultdict(set)
        self.agent_workload: Dict[str, int] = defaultdict(int)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load automation configuration"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found, using defaults: {config_path}")
            return self._get_default_config()
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "execution": {
                "min_profit_threshold_usd": 100,
                "max_gas_price_gwei": 300,
                "slippage_tolerance": 0.005,
                "execution_timeout_seconds": 30,
                "max_concurrent_executions": 5
            },
            "mcp_servers": {
                "market_data": {
                    "host": "localhost",
                    "port": 8100,
                    "capabilities": ["price_feed", "liquidity_data", "volume_analysis"]
                },
                "flash_loan": {
                    "host": "localhost",
                    "port": 8101,
                    "capabilities": ["aave", "compound", "dydx", "balancer"]
                },
                "dex_aggregator": {
                    "host": "localhost",
                    "port": 8102,
                    "capabilities": ["uniswap", "sushiswap", "curve", "balancer"]
                },
                "risk_analyzer": {
                    "host": "localhost",
                    "port": 8103,
                    "capabilities": ["var_calculation", "liquidity_risk", "impermanent_loss"]
                },
                "gas_optimizer": {
                    "host": "localhost",
                    "port": 8104,
                    "capabilities": ["gas_estimation", "priority_fee", "flashbots_bundle"]
                },
                "mev_protector": {
                    "host": "localhost",
                    "port": 8105,
                    "capabilities": ["private_mempool", "flashbots", "eden_network"]
                },
                "execution_engine": {
                    "host": "localhost",
                    "port": 8106,
                    "capabilities": ["smart_routing", "atomic_execution", "rollback"]
                }
            },
            "monitoring": {
                "health_check_interval_seconds": 10,
                "metrics_port": 9090,
                "alert_webhook": None
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            }
        }
    
    async def initialize(self):
        """Initialize the coordinator"""
        logger.info("Initializing Automated Execution Coordinator...")
        
        # Start metrics server
        start_http_server(self.config["monitoring"]["metrics_port"])
        
        # Initialize Redis connection
        self.redis_client = await redis.from_url(
            f"redis://{self.config['redis']['host']}:{self.config['redis']['port']}/{self.config['redis']['db']}"
        )
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
        
        # Initialize MCP servers
        await self._initialize_mcp_servers()
        
        # Start background tasks
        self.tasks.extend([
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._execution_loop()),
            asyncio.create_task(self._monitoring_loop()),
            asyncio.create_task(self._agent_coordination_loop()),
            asyncio.create_task(self._profit_optimization_loop())
        ])
        
        self.running = True
        logger.info("Coordinator initialized successfully")
    
    async def _initialize_mcp_servers(self):
        """Initialize MCP server connections"""
        for server_type, config in self.config["mcp_servers"].items():
            server = MCPServer(
                name=server_type,
                type=ServerType(server_type),
                host=config["host"],
                port=config["port"],
                capabilities=config["capabilities"]
            )
            self.mcp_servers[server_type] = server
            
            # Check initial health
            await self._check_server_health(server)
    
    async def _check_server_health(self, server: MCPServer) -> bool:
        """Check health of an MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{server.host}:{server.port}{server.health_endpoint}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        server.status = "healthy"
                        server.last_health_check = datetime.now()
                        mcp_server_health.labels(server=server.name).set(1)
                        return True
        except Exception as e:
            logger.error(f"Health check failed for {server.name}: {e}")
        
        server.status = "unhealthy"
        mcp_server_health.labels(server=server.name).set(0)
        return False
    
    async def _health_check_loop(self):
        """Continuous health monitoring of MCP servers"""
        while self.running:
            try:
                for server in self.mcp_servers.values():
                    await self._check_server_health(server)
                
                await asyncio.sleep(self.config["monitoring"]["health_check_interval_seconds"])
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)
    
    async def _execution_loop(self):
        """Main execution loop for processing opportunities"""
        max_concurrent = self.config["execution"]["max_concurrent_executions"]
        semaphore = asyncio.Semaphore(max_concurrent)
        
        while self.running:
            try:
                # Get next execution task
                task = await self.execution_queue.get()
                
                # Process with concurrency limit
                asyncio.create_task(self._process_execution(task, semaphore))
                
            except Exception as e:
                logger.error(f"Execution loop error: {e}")
                await asyncio.sleep(1)
    
    async def _process_execution(self, task: ExecutionTask, semaphore: asyncio.Semaphore):
        """Process a single execution task"""
        async with semaphore:
            start_time = time.time()
            try:
                logger.info(f"Processing execution task: {task.task_id}")
                execution_counter.inc()
                
                # Update state
                task.state = ExecutionState.ANALYZING
                await self._update_task_state(task)
                
                # 1. Validate opportunity with latest data
                if not await self._validate_opportunity(task):
                    task.state = ExecutionState.FAILED
                    task.result = {"error": "Opportunity validation failed"}
                    return
                
                # 2. Perform risk assessment
                task.state = ExecutionState.DECIDING
                risk_approved = await self._assess_execution_risk(task)
                if not risk_approved:
                    task.state = ExecutionState.FAILED
                    task.result = {"error": "Risk assessment failed"}
                    return
                
                # 3. Optimize execution parameters
                await self._optimize_execution_params(task)
                
                # 4. Execute the trade
                task.state = ExecutionState.EXECUTING
                result = await self._execute_trade(task)
                
                if result["success"]:
                    task.state = ExecutionState.COMPLETED
                    task.profit_usd = result.get("profit_usd", 0)
                    self.execution_stats["successful_executions"] += 1
                    self.execution_stats["total_profit_usd"] += task.profit_usd
                    profit_gauge.set(self.execution_stats["total_profit_usd"])
                else:
                    task.state = ExecutionState.FAILED
                    self.execution_stats["failed_executions"] += 1
                
                task.result = result
                
            except Exception as e:
                logger.error(f"Execution error for task {task.task_id}: {e}")
                task.state = ExecutionState.FAILED
                task.result = {"error": str(e)}
                self.execution_stats["failed_executions"] += 1
            
            finally:
                # Update metrics
                execution_time = time.time() - start_time
                execution_latency.observe(execution_time)
                
                task.completed_at = datetime.now()
                self.execution_history.append(task)
                await self._update_task_state(task)
                
                # Update stats
                self.execution_stats["total_executions"] += 1
                self._update_average_execution_time(execution_time)
    
    async def _validate_opportunity(self, task: ExecutionTask) -> bool:
        """Validate opportunity with latest market data"""
        try:
            # Get fresh market data
            market_server = self.mcp_servers.get("market_data")
            if not market_server or market_server.status != "healthy":
                return False
            
            async with aiohttp.ClientSession() as session:
                url = f"http://{market_server.host}:{market_server.port}/validate"
                async with session.post(url, json=task.market_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("valid", False) and \
                               data.get("expected_profit_usd", 0) >= self.config["execution"]["min_profit_threshold_usd"]
            
        except Exception as e:
            logger.error(f"Opportunity validation error: {e}")
        
        return False
    
    async def _assess_execution_risk(self, task: ExecutionTask) -> bool:
        """Assess execution risk"""
        try:
            risk_server = self.mcp_servers.get("risk_analyzer")
            if not risk_server or risk_server.status != "healthy":
                return False
            
            async with aiohttp.ClientSession() as session:
                url = f"http://{risk_server.host}:{risk_server.port}/analyze"
                payload = {
                    "opportunity": task.market_data,
                    "execution_params": task.execution_params
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        risk_data = await response.json()
                        task.risk_assessment = risk_data
                        
                        # Check risk thresholds
                        return (risk_data.get("risk_score", 1.0) <= 0.7 and
                               risk_data.get("liquidity_risk", 1.0) <= 0.5 and
                               risk_data.get("slippage_risk", 1.0) <= 0.3)
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
        
        return False
    
    async def _optimize_execution_params(self, task: ExecutionTask):
        """Optimize execution parameters"""
        try:
            # Gas optimization
            gas_server = self.mcp_servers.get("gas_optimizer")
            if gas_server and gas_server.status == "healthy":
                async with aiohttp.ClientSession() as session:
                    url = f"http://{gas_server.host}:{gas_server.port}/optimize"
                    async with session.post(url, json=task.execution_params) as response:
                        if response.status == 200:
                            gas_data = await response.json()
                            task.execution_params.update(gas_data)
            
            # MEV protection
            mev_server = self.mcp_servers.get("mev_protector")
            if mev_server and mev_server.status == "healthy":
                async with aiohttp.ClientSession() as session:
                    url = f"http://{mev_server.host}:{mev_server.port}/protect"
                    async with session.post(url, json=task.execution_params) as response:
                        if response.status == 200:
                            mev_data = await response.json()
                            task.execution_params["mev_protection"] = mev_data
            
        except Exception as e:
            logger.error(f"Parameter optimization error: {e}")
    
    async def _execute_trade(self, task: ExecutionTask) -> Dict[str, Any]:
        """Execute the actual trade"""
        try:
            execution_server = self.mcp_servers.get("execution_engine")
            if not execution_server or execution_server.status != "healthy":
                return {"success": False, "error": "Execution engine unavailable"}
            
            async with aiohttp.ClientSession() as session:
                url = f"http://{execution_server.host}:{execution_server.port}/execute"
                payload = {
                    "task_id": task.task_id,
                    "opportunity": task.market_data,
                    "params": task.execution_params,
                    "risk_assessment": task.risk_assessment
                }
                
                timeout = aiohttp.ClientTimeout(
                    total=self.config["execution"]["execution_timeout_seconds"]
                )
                
                async with session.post(url, json=payload, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "success": False,
                            "error": f"Execution failed with status {response.status}"
                        }
            
        except asyncio.TimeoutError:
            return {"success": False, "error": "Execution timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update_task_state(self, task: ExecutionTask):
        """Update task state in Redis"""
        if self.redis_client:
            try:
                await self.redis_client.hset(
                    f"execution:{task.task_id}",
                    mapping={
                        "state": task.state.name,
                        "updated_at": datetime.now().isoformat(),
                        "profit_usd": str(task.profit_usd) if task.profit_usd else "0"
                    }
                )
            except Exception as e:
                logger.error(f"Failed to update task state: {e}")
    
    async def _monitoring_loop(self):
        """Monitor system performance and alert on issues"""
        alert_threshold_failures = 5
        consecutive_failures = 0
        
        while self.running:
            try:
                # Calculate success rate
                total = self.execution_stats["total_executions"]
                if total > 0:
                    success_rate = self.execution_stats["successful_executions"] / total
                    
                    # Alert on low success rate
                    if success_rate < 0.7:
                        consecutive_failures += 1
                        if consecutive_failures >= alert_threshold_failures:
                            await self._send_alert(
                                "Low success rate",
                                f"Success rate: {success_rate:.2%}"
                            )
                            consecutive_failures = 0
                    else:
                        consecutive_failures = 0
                
                # Monitor MCP server health
                unhealthy_servers = [
                    s.name for s in self.mcp_servers.values()
                    if s.status != "healthy"
                ]
                
                if unhealthy_servers:
                    await self._send_alert(
                        "Unhealthy MCP servers",
                        f"Servers: {', '.join(unhealthy_servers)}"
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def _agent_coordination_loop(self):
        """Coordinate agent assignments and workload"""
        while self.running:
            try:
                # Balance agent workload
                await self._balance_agent_workload()
                
                # Update agent metrics
                for agent_type, agents in self.agent_assignments.items():
                    active_agents_gauge.labels(type=agent_type).set(len(agents))
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Agent coordination error: {e}")
                await asyncio.sleep(10)
    
    async def _balance_agent_workload(self):
        """Balance workload across agents"""
        # Get current workload distribution
        workload_by_type = defaultdict(list)
        
        for agent_id, workload in self.agent_workload.items():
            agent_type = self._get_agent_type(agent_id)
            workload_by_type[agent_type].append((agent_id, workload))
        
        # Rebalance if needed
        for agent_type, agent_workloads in workload_by_type.items():
            if not agent_workloads:
                continue
            
            agent_workloads.sort(key=lambda x: x[1])  # Sort by workload
            
            # If imbalance is too high, redistribute
            min_workload = agent_workloads[0][1]
            max_workload = agent_workloads[-1][1]
            
            if max_workload - min_workload > 10:  # Threshold
                await self._redistribute_tasks(agent_type, agent_workloads)
    
    async def _redistribute_tasks(self, agent_type: str, agent_workloads: List[Tuple[str, int]]):
        """Redistribute tasks among agents"""
        logger.info(f"Redistributing tasks for {agent_type} agents")
        # Implementation depends on specific agent types and tasks
        pass
    
    async def _profit_optimization_loop(self):
        """Continuously optimize for better profit opportunities"""
        while self.running:
            try:
                # Analyze historical performance
                if len(self.execution_history) >= 10:
                    opportunity_performance = defaultdict(list)
                    
                    for task in self.execution_history:
                        if task.state == ExecutionState.COMPLETED:
                            opportunity_performance[task.opportunity_type].append(
                                task.profit_usd
                            )
                    
                    # Find best performing opportunity types
                    best_type = None
                    best_avg_profit = 0
                    
                    for opp_type, profits in opportunity_performance.items():
                        avg_profit = sum(profits) / len(profits)
                        if avg_profit > best_avg_profit:
                            best_avg_profit = avg_profit
                            best_type = opp_type
                    
                    if best_type:
                        self.execution_stats["best_opportunity_type"] = best_type
                        logger.info(f"Best opportunity type: {best_type} (${best_avg_profit:.2f} avg)")
                
                await asyncio.sleep(60)  # Analyze every minute
                
            except Exception as e:
                logger.error(f"Profit optimization error: {e}")
                await asyncio.sleep(60)
    
    def _get_agent_type(self, agent_id: str) -> str:
        """Get agent type from ID"""
        for agent_type, agents in self.agent_assignments.items():
            if agent_id in agents:
                return agent_type
        return "unknown"
    
    def _update_average_execution_time(self, execution_time: float):
        """Update average execution time"""
        total = self.execution_stats["total_executions"]
        current_avg = self.execution_stats["average_execution_time"]
        
        # Calculate new average
        new_avg = ((current_avg * (total - 1)) + execution_time) / total
        self.execution_stats["average_execution_time"] = new_avg
    
    async def _send_alert(self, title: str, message: str):
        """Send alert via webhook"""
        webhook_url = self.config["monitoring"].get("alert_webhook")
        if not webhook_url:
            logger.warning(f"Alert: {title} - {message}")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "title": title,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "severity": "high"
                }
                await session.post(webhook_url, json=payload)
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def submit_opportunity(self, opportunity: Dict[str, Any]) -> str:
        """Submit a new opportunity for execution"""
        task = ExecutionTask(
            task_id=f"task_{int(time.time() * 1000)}",
            opportunity_type=opportunity.get("type", "unknown"),
            market_data=opportunity.get("market_data", {}),
            risk_assessment={},
            execution_params=opportunity.get("params", {})
        )
        
        await self.execution_queue.put(task)
        logger.info(f"Submitted execution task: {task.task_id}")
        
        return task.task_id
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "running": self.running,
            "mcp_servers": {
                name: {
                    "status": server.status,
                    "last_health_check": server.last_health_check.isoformat() 
                    if server.last_health_check else None
                }
                for name, server in self.mcp_servers.items()
            },
            "execution_stats": self.execution_stats,
            "queue_size": self.execution_queue.qsize(),
            "active_agents": len(self.active_agents),
            "recent_executions": [
                {
                    "task_id": task.task_id,
                    "state": task.state.name,
                    "profit_usd": task.profit_usd,
                    "completed_at": task.completed_at.isoformat() 
                    if task.completed_at else None
                }
                for task in list(self.execution_history)[-10:]  # Last 10
            ]
        }
    
    async def shutdown(self):
        """Gracefully shutdown the coordinator"""
        logger.info("Shutting down Automated Execution Coordinator...")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Close connections
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Coordinator shutdown complete")


class MCPServerOrchestrator:
    """
    Orchestrates all MCP servers for the flash loan system
    """
    
    def __init__(self, docker_client: docker.DockerClient):
        self.docker = docker_client
        self.services: Dict[str, Any] = {}
        self.network_name = "flashloan_network"
    
    async def deploy_all_servers(self) -> Dict[str, str]:
        """Deploy all MCP servers"""
        logger.info("Deploying all MCP servers...")
        
        # Ensure network exists
        self._ensure_network()
        
        # Deploy each server type
        servers = {
            "market_data_server": {
                "image": "flashloan/mcp-market-data:latest",
                "replicas": 3,
                "ports": {"8100/tcp": 8100},
                "env": ["REDIS_URL=redis://redis:6379"]
            },
            "flash_loan_server": {
                "image": "flashloan/mcp-flash-loan:latest",
                "replicas": 2,
                "ports": {"8101/tcp": 8101},
                "env": ["PROTOCOLS=aave,compound,dydx"]
            },
            "dex_aggregator_server": {
                "image": "flashloan/mcp-dex-aggregator:latest",
                "replicas": 5,
                "ports": {"8102/tcp": 8102},
                "env": ["DEXS=uniswap,sushiswap,curve,balancer"]
            },
            "risk_analyzer_server": {
                "image": "flashloan/mcp-risk-analyzer:latest",
                "replicas": 2,
                "ports": {"8103/tcp": 8103},
                "env": ["ML_MODEL=advanced_risk_v2"]
            },
            "gas_optimizer_server": {
                "image": "flashloan/mcp-gas-optimizer:latest",
                "replicas": 2,
                "ports": {"8104/tcp": 8104},
                "env": ["STRATEGY=adaptive"]
            },
            "mev_protector_server": {
                "image": "flashloan/mcp-mev-protector:latest",
                "replicas": 1,
                "ports": {"8105/tcp": 8105},
                "env": ["FLASHBOTS_ENABLED=true"]
            },
            "execution_engine_server": {
                "image": "flashloan/mcp-execution-engine:latest",
                "replicas": 3,
                "ports": {"8106/tcp": 8106},
                "env": ["MODE=high_frequency"]
            }
        }
        
        deployed = {}
        for name, config in servers.items():
            try:
                service = self._deploy_service(name, config)
                self.services[name] = service
                deployed[name] = "deployed"
                logger.info(f"Deployed {name}")
            except Exception as e:
                logger.error(f"Failed to deploy {name}: {e}")
                deployed[name] = f"failed: {str(e)}"
        
        return deployed
    
    def _ensure_network(self):
        """Ensure Docker network exists"""
        try:
            self.docker.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.docker.networks.create(
                self.network_name,
                driver="overlay",
                attachable=True
            )
    
    def _deploy_service(self, name: str, config: Dict[str, Any]) -> Any:
        """Deploy a single service"""
        service_config = {
            "name": name,
            "image": config["image"],
            "networks": [self.network_name],
            "env": config.get("env", []),
            "mode": ServiceMode(
                mode="replicated",
                replicas=config.get("replicas", 1)
            ),
            "restart_policy": RestartPolicy(
                condition="on-failure",
                delay=5000000000,  # 5 seconds in nanoseconds
                max_attempts=3
            ),
            "resources": Resources(
                cpu_limit=2000000000,  # 2 CPU cores
                mem_limit=2147483648   # 2GB RAM
            )
        }
        
        # Add port mappings if specified
        if "ports" in config:
            service_config["endpoint_spec"] = {
                "ports": [
                    {
                        "Protocol": "tcp",
                        "PublishedPort": published,
                        "TargetPort": int(target.split("/")[0])
                    }
                    for target, published in config["ports"].items()
                ]
            }
        
        return self.docker.services.create(**service_config)
    
    def scale_service(self, service_name: str, replicas: int):
        """Scale a service"""
        if service_name in self.services:
            service = self.services[service_name]
            service.scale(replicas)
            logger.info(f"Scaled {service_name} to {replicas} replicas")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {}
        for name, service in self.services.items():
            try:
                service.reload()
                tasks = service.tasks()
                running = sum(1 for t in tasks if t["Status"]["State"] == "running")
                status[name] = {
                    "replicas": len(tasks),
                    "running": running,
                    "status": "healthy" if running > 0 else "unhealthy"
                }
            except Exception as e:
                status[name] = {"status": "error", "error": str(e)}
        
        return status


async def main():
    """Main entry point"""
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(coordinator.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and initialize coordinator
    coordinator = AutomatedExecutionCoordinator()
    await coordinator.initialize()
    
    # Deploy MCP servers if Docker is available
    if coordinator.docker_client:
        orchestrator = MCPServerOrchestrator(coordinator.docker_client)
        deployment_status = await orchestrator.deploy_all_servers()
        logger.info(f"MCP Server deployment status: {deployment_status}")
    
    logger.info("Automated Execution Coordinator is running...")
    
    # Keep running
    try:
        while coordinator.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await coordinator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
