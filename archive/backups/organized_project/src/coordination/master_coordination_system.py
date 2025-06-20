#!/usr/bin/env python3
"""
Master Coordination System for Flash Loan Arbitrage Bot
======================================================

This system coordinates:
1. 80+ MCP Servers (specialized blockchain services)
2. 10 AI Agents (specialized trading agents)
3. LangChain agents (intelligent coordination)
4. AutoGen multi-agent conversations
5. Docker orchestration and health monitoring
6. Real-time arbitrage execution
"""

import asyncio
import aiohttp
import json
import logging
import os
import time
import docker
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import redis
import pika
from pathlib import Path

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool, BaseTool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_community.chat_models import ChatOllama

# AutoGen imports
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logging.warning("AutoGen not available. Install with: pip install pyautogen")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_coordination_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Types of services in the coordination system"""
    MCP_SERVER = "mcp_server"
    AI_AGENT = "ai_agent"
    LANGCHAIN_AGENT = "langchain_agent"
    AUTOGEN_AGENT = "autogen_agent"
    INFRASTRUCTURE = "infrastructure"
    COORDINATION = "coordination"

class ServiceStatus(Enum):
    """Service status enumeration"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    service_type: ServiceType
    container_name: str
    port: int
    health_endpoint: str
    dependencies: List[str]
    environment: Dict[str, str]
    dockerfile: str
    enabled: bool = True
    priority: int = 5
    restart_policy: str = "unless-stopped"

@dataclass
class CoordinationTask:
    """Task for coordination system"""
    task_id: str
    task_type: str
    priority: int
    assigned_services: List[str]
    parameters: Dict[str, Any]
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MasterCoordinationSystem:
    """Master coordination system for all services"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.is_running = False
        self.services: Dict[str, ServiceConfig] = {}
        self.service_health: Dict[str, ServiceStatus] = {}
        self.coordination_tasks: List[CoordinationTask] = []
        
        # Communication infrastructure
        self.redis_client = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        
        # Agent systems
        self.langchain_agents: Dict[str, Any] = {}
        self.autogen_agents: Dict[str, Any] = {}
        self.ai_agents: Dict[str, Any] = {}
        
        # Performance metrics
        self.metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_response_time': 0.0,
            'revenue_generated': 0.0,
            'arbitrage_opportunities': 0,
            'system_uptime': 0
        }
        
        # Load all configurations
        self._load_all_configurations()
        
    def _load_all_configurations(self):
        """Load all service configurations"""
        try:
            # Load MCP server configurations
            self._load_mcp_server_configs()
            
            # Load AI agent configurations
            self._load_ai_agent_configs()
            
            # Add infrastructure services
            self._add_infrastructure_services()
            
            # Add coordination services
            self._add_coordination_services()
            
            logger.info(f"✅ Loaded {len(self.services)} service configurations")
            
        except Exception as e:
            logger.error(f"❌ Error loading configurations: {e}")
            
    def _load_mcp_server_configs(self):
        """Load MCP server configurations"""
        try:
            with open('unified_mcp_config.json', 'r') as f:
                mcp_config = json.load(f)
                
            for server_name, config in mcp_config.get('servers', {}).items():
                if config.get('enabled', True):
                    self.services[f"mcp_{server_name}"] = ServiceConfig(
                        name=server_name,
                        service_type=ServiceType.MCP_SERVER,
                        container_name=f"mcp_{server_name}",
                        port=config.get('port', 8000),
                        health_endpoint="/health",
                        dependencies=['redis', 'rabbitmq'],
                        environment={
                            'SERVER_TYPE': server_name,
                            'PORT': str(config.get('port', 8000)),
                            'REDIS_URL': 'redis://coordination_redis:6379',
                            'RABBITMQ_URL': 'amqp://coordination:coordination_pass@coordination_rabbitmq:5672/coordination'
                        },
                        dockerfile="docker/Dockerfile.mcp-enhanced",
                        priority=3
                    )
                    
        except Exception as e:
            logger.error(f"❌ Error loading MCP server configs: {e}")
            
    def _load_ai_agent_configs(self):
        """Load AI agent configurations"""
        try:
            with open('ai_agents_config.json', 'r') as f:
                agent_config = json.load(f)
                
            for agent_name, config in agent_config.get('agents', {}).items():
                self.services[f"agent_{agent_name}"] = ServiceConfig(
                    name=agent_name,
                    service_type=ServiceType.AI_AGENT,
                    container_name=f"agent_{agent_name}",
                    port=config.get('port', 9000),
                    health_endpoint="/health",
                    dependencies=['redis', 'rabbitmq'],
                    environment={
                        'AGENT_TYPE': agent_name,
                        'AGENT_ROLE': config.get('role', ''),
                        'PORT': str(config.get('port', 9000)),
                        'REDIS_URL': 'redis://coordination_redis:6379',
                        'RABBITMQ_URL': 'amqp://coordination:coordination_pass@coordination_rabbitmq:5672/coordination'
                    },
                    dockerfile="docker/Dockerfile.agent",
                    priority=2
                )
                
        except Exception as e:
            logger.error(f"❌ Error loading AI agent configs: {e}")
            
    def _add_infrastructure_services(self):
        """Add infrastructure services"""
        infrastructure_services = {
            'redis': ServiceConfig(
                name='redis',
                service_type=ServiceType.INFRASTRUCTURE,
                container_name='coordination_redis',
                port=6379,
                health_endpoint='/',
                dependencies=[],
                environment={},
                dockerfile="redis:7-alpine",
                priority=1
            ),
            'rabbitmq': ServiceConfig(
                name='rabbitmq',
                service_type=ServiceType.INFRASTRUCTURE,
                container_name='coordination_rabbitmq',
                port=5672,
                health_endpoint='/',
                dependencies=[],
                environment={
                    'RABBITMQ_DEFAULT_USER': 'coordination',
                    'RABBITMQ_DEFAULT_PASS': 'coordination_pass',
                    'RABBITMQ_DEFAULT_VHOST': 'coordination'
                },
                dockerfile="rabbitmq:3-management",
                priority=1
            ),
            'postgres': ServiceConfig(
                name='postgres',
                service_type=ServiceType.INFRASTRUCTURE,
                container_name='coordination_postgres',
                port=5432,
                health_endpoint='/',
                dependencies=[],
                environment={
                    'POSTGRES_DB': 'coordination',
                    'POSTGRES_USER': 'coordination',
                    'POSTGRES_PASSWORD': 'coordination_pass'
                },
                dockerfile="postgres:15-alpine",
                priority=1
            )
        }
        
        self.services.update(infrastructure_services)
        
    def _add_coordination_services(self):
        """Add coordination services"""
        coordination_services = {
            'langchain_coordinator': ServiceConfig(
                name='langchain_coordinator',
                service_type=ServiceType.LANGCHAIN_AGENT,
                container_name='langchain_coordinator',
                port=8001,
                health_endpoint="/health",
                dependencies=['redis', 'rabbitmq'],
                environment={
                    'COORDINATOR_TYPE': 'langchain',
                    'PORT': '8001',
                    'REDIS_URL': 'redis://coordination_redis:6379',
                    'RABBITMQ_URL': 'amqp://coordination:coordination_pass@coordination_rabbitmq:5672/coordination'
                },
                dockerfile="docker/Dockerfile.langchain",
                priority=2
            ),
            'autogen_system': ServiceConfig(
                name='autogen_system',
                service_type=ServiceType.AUTOGEN_AGENT,
                container_name='autogen_system',
                port=8002,
                health_endpoint="/health",
                dependencies=['redis', 'rabbitmq'],
                environment={
                    'AUTOGEN_TYPE': 'multi_agent',
                    'PORT': '8002',
                    'REDIS_URL': 'redis://coordination_redis:6379',
                    'RABBITMQ_URL': 'amqp://coordination:coordination_pass@coordination_rabbitmq:5672/coordination'
                },
                dockerfile="docker/Dockerfile.autogen",
                priority=2
            ),
            'master_orchestrator': ServiceConfig(
                name='master_orchestrator',
                service_type=ServiceType.COORDINATION,
                container_name='master_orchestrator',
                port=8000,
                health_endpoint="/health",
                dependencies=['redis', 'rabbitmq', 'postgres'],
                environment={
                    'ORCHESTRATOR_TYPE': 'master',
                    'PORT': '8000',
                    'REDIS_URL': 'redis://coordination_redis:6379',
                    'RABBITMQ_URL': 'amqp://coordination:coordination_pass@coordination_rabbitmq:5672/coordination',
                    'POSTGRES_URL': 'postgresql://coordination:coordination_pass@coordination_postgres:5432/coordination'
                },
                dockerfile="docker/Dockerfile.coordination",
                priority=1
            )
        }
        
        self.services.update(coordination_services)
        
    async def initialize_infrastructure(self):
        """Initialize communication infrastructure"""
        try:
            logger.info("🚀 Initializing infrastructure...")
            
            # Start infrastructure services in priority order
            infrastructure_services = [
                service for service in self.services.values() 
                if service.service_type == ServiceType.INFRASTRUCTURE
            ]
            
            for service in sorted(infrastructure_services, key=lambda x: x.priority):
                await self._start_service(service)
                
            # Wait for infrastructure to be ready
            await asyncio.sleep(15)
            
            # Initialize connections
            await self._initialize_connections()
            
            logger.info("✅ Infrastructure initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Infrastructure initialization failed: {e}")
            raise
            
    async def _initialize_connections(self):
        """Initialize Redis and RabbitMQ connections"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Test Redis connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
            # Initialize RabbitMQ
            connection_params = pika.ConnectionParameters(
                host='localhost',
                port=5672,
                virtual_host='coordination',
                credentials=pika.PlainCredentials('coordination', 'coordination_pass')
            )
            
            self.rabbitmq_connection = pika.BlockingConnection(connection_params)
            self.rabbitmq_channel = self.rabbitmq_connection.channel()
            
            # Declare exchanges and queues
            self._setup_message_queues()
            
            logger.info("✅ RabbitMQ connection established")
            
        except Exception as e:
            logger.error(f"❌ Connection initialization failed: {e}")
            raise
            
    def _setup_message_queues(self):
        """Setup RabbitMQ exchanges and queues"""
        try:
            # Declare exchanges
            self.rabbitmq_channel.exchange_declare(
                exchange='coordination', 
                exchange_type='topic',
                durable=True
            )
            
            # Declare queues
            queues = [
                'mcp_commands',
                'agent_responses', 
                'langchain_tasks',
                'autogen_conversations',
                'arbitrage_opportunities',
                'system_alerts',
                'performance_metrics'
            ]
            
            for queue in queues:
                self.rabbitmq_channel.queue_declare(queue=queue, durable=True)
                
            logger.info("✅ Message queues configured")
            
        except Exception as e:
            logger.error(f"❌ Message queue setup failed: {e}")
            
    async def start_all_services(self):
        """Start all services in dependency order"""
        try:
            logger.info("🚀 Starting all services...")
            
            # Group services by priority
            service_groups = {}
            for service in self.services.values():
                if service.enabled:
                    priority = service.priority
                    if priority not in service_groups:
                        service_groups[priority] = []
                    service_groups[priority].append(service)
            
            # Start services by priority
            for priority in sorted(service_groups.keys()):
                logger.info(f"🔄 Starting priority {priority} services...")
                
                # Start services in parallel within same priority
                tasks = []
                for service in service_groups[priority]:
                    if service.service_type != ServiceType.INFRASTRUCTURE:  # Already started
                        tasks.append(self._start_service(service))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                # Wait between priority groups
                await asyncio.sleep(10)
                
            logger.info("✅ All services started")
            
        except Exception as e:
            logger.error(f"❌ Service startup failed: {e}")
            
    async def _start_service(self, service: ServiceConfig):
        """Start a single service"""
        try:
            logger.info(f"🔄 Starting {service.name}...")
            
            # Check if container already exists
            try:
                existing_container = self.docker_client.containers.get(service.container_name)
                if existing_container.status == 'running':
                    logger.info(f"✅ {service.name} already running")
                    self.service_health[service.name] = ServiceStatus.RUNNING
                    return
                else:
                    existing_container.remove(force=True)
            except docker.errors.NotFound:
                pass
            
            # Start the service based on type
            if service.service_type == ServiceType.INFRASTRUCTURE:
                await self._start_infrastructure_service(service)
            else:
                await self._start_application_service(service)
                
            self.service_health[service.name] = ServiceStatus.RUNNING
            logger.info(f"✅ {service.name} started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start {service.name}: {e}")
            self.service_health[service.name] = ServiceStatus.ERROR
            
    async def _start_infrastructure_service(self, service: ServiceConfig):
        """Start an infrastructure service"""
        try:
            if service.name == 'redis':
                container = self.docker_client.containers.run(
                    'redis:7-alpine',
                    name=service.container_name,
                    ports={'6379/tcp': service.port},
                    detach=True,
                    restart_policy={"Name": service.restart_policy},
                    healthcheck={
                        'test': ['CMD', 'redis-cli', 'ping'],
                        'interval': 30000000000,
                        'timeout': 10000000000,
                        'retries': 3
                    }
                )
            elif service.name == 'rabbitmq':
                container = self.docker_client.containers.run(
                    'rabbitmq:3-management',
                    name=service.container_name,
                    ports={'5672/tcp': 5672, '15672/tcp': 15672},
                    environment=service.environment,
                    detach=True,
                    restart_policy={"Name": service.restart_policy}
                )
            elif service.name == 'postgres':
                container = self.docker_client.containers.run(
                    'postgres:15-alpine',
                    name=service.container_name,
                    ports={'5432/tcp': service.port},
                    environment=service.environment,
                    detach=True,
                    restart_policy={"Name": service.restart_policy}
                )
                
        except Exception as e:
            logger.error(f"❌ Infrastructure service start failed: {e}")
            raise
            
    async def _start_application_service(self, service: ServiceConfig):
        """Start an application service"""
        try:
            # Build the Docker image if it doesn't exist
            if not service.dockerfile.startswith(('redis:', 'rabbitmq:', 'postgres:')):
                await self._build_service_image(service)
            
            # Start the container
            container = self.docker_client.containers.run(
                service.dockerfile if service.dockerfile.startswith(('redis:', 'rabbitmq:', 'postgres:')) else f"{service.name}:latest",
                name=service.container_name,
                ports={f'{service.port}/tcp': service.port},
                environment=service.environment,
                detach=True,
                restart_policy={"Name": service.restart_policy}
            )
            
        except Exception as e:
            logger.error(f"❌ Application service start failed: {e}")
            raise
            
    async def _build_service_image(self, service: ServiceConfig):
        """Build Docker image for a service"""
        try:
            # Check if image already exists
            try:
                self.docker_client.images.get(f"{service.name}:latest")
                logger.info(f"📦 Image {service.name}:latest already exists")
                return
            except docker.errors.ImageNotFound:
                pass
            
            # Build the image
            logger.info(f"🔨 Building image for {service.name}...")
            
            # Create a simple Dockerfile content based on service type
            dockerfile_content = self._generate_dockerfile_content(service)
            
            # Build the image
            image, build_logs = self.docker_client.images.build(
                fileobj=dockerfile_content,
                tag=f"{service.name}:latest",
                rm=True
            )
            
            logger.info(f"✅ Built image for {service.name}")
            
        except Exception as e:
            logger.error(f"❌ Image build failed for {service.name}: {e}")
            raise
            
    def _generate_dockerfile_content(self, service: ServiceConfig) -> bytes:
        """Generate Dockerfile content for a service"""
        if service.service_type == ServiceType.MCP_SERVER:
            dockerfile = f"""
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

COPY requirements-coordination.txt .
RUN pip install --no-cache-dir -r requirements-coordination.txt

COPY mcp_servers/ ./mcp_servers/
COPY enhanced_mcp_price_feed_server.py .
COPY compatible_enhanced_mcp_price_feed_server.py .

ENV PYTHONPATH=/app
ENV PORT={service.port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{service.port}/health || exit 1

EXPOSE {service.port}

CMD ["python", "-c", "from mcp_servers.{service.name} import main; main()"]
"""
        elif service.service_type == ServiceType.AI_AGENT:
            dockerfile = f"""
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

COPY requirements-coordination.txt .
RUN pip install --no-cache-dir -r requirements-coordination.txt

COPY ai_agents/ ./ai_agents/
COPY advanced_agentic_coordination.py .

ENV PYTHONPATH=/app
ENV PORT={service.port}
ENV AGENT_TYPE={service.name}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{service.port}/health || exit 1

EXPOSE {service.port}

CMD ["python", "advanced_agentic_coordination.py"]
"""
        elif service.service_type == ServiceType.LANGCHAIN_AGENT:
            dockerfile = f"""
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

COPY requirements-coordination.txt .
RUN pip install --no-cache-dir -r requirements-coordination.txt

COPY langchain_command_system.py .
COPY advanced_agentic_coordination.py .

ENV PYTHONPATH=/app
ENV PORT={service.port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{service.port}/health || exit 1

EXPOSE {service.port}

CMD ["python", "langchain_command_system.py"]
"""
        elif service.service_type == ServiceType.AUTOGEN_AGENT:
            dockerfile = f"""
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

COPY requirements-coordination.txt .
RUN pip install --no-cache-dir -r requirements-coordination.txt

COPY advanced_agentic_coordination.py .

ENV PYTHONPATH=/app
ENV PORT={service.port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{service.port}/health || exit 1

EXPOSE {service.port}

CMD ["python", "-c", "import advanced_agentic_coordination; advanced_agentic_coordination.run_autogen_system()"]
"""
        else:  # COORDINATION
            dockerfile = f"""
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl gcc && rm -rf /var/lib/apt/lists/*

COPY requirements-coordination.txt .
RUN pip install --no-cache-dir -r requirements-coordination.txt

COPY docker_coordination_system.py .
COPY master_coordination_system.py .

ENV PYTHONPATH=/app
ENV PORT={service.port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{service.port}/health || exit 1

EXPOSE {service.port}

CMD ["python", "master_coordination_system.py"]
"""
        
        return dockerfile.encode('utf-8')
        
    async def health_check_all_services(self) -> Dict[str, ServiceStatus]:
        """Check health of all services"""
        health_status = {}
        
        for service_name, service_config in self.services.items():
            if service_config.enabled:
                try:
                    # Check container status
                    container = self.docker_client.containers.get(service_config.container_name)
                    if container.status == 'running':
                        # Check application health if it has health endpoint
                        if service_config.health_endpoint and service_config.service_type != ServiceType.INFRASTRUCTURE:
                            async with aiohttp.ClientSession() as session:
                                url = f"http://localhost:{service_config.port}{service_config.health_endpoint}"
                                try:
                                    async with session.get(url, timeout=5) as response:
                                        if response.status == 200:
                                            health_status[service_name] = ServiceStatus.RUNNING
                                        else:
                                            health_status[service_name] = ServiceStatus.ERROR
                                except:
                                    health_status[service_name] = ServiceStatus.ERROR
                        else:
                            health_status[service_name] = ServiceStatus.RUNNING
                    else:
                        health_status[service_name] = ServiceStatus.STOPPED
                        
                except docker.errors.NotFound:
                    health_status[service_name] = ServiceStatus.STOPPED
                except Exception as e:
                    health_status[service_name] = ServiceStatus.ERROR
                    logger.error(f"❌ Health check failed for {service_name}: {e}")
                    
        return health_status
        
    async def coordinate_arbitrage_task(self, task_description: str) -> Dict[str, Any]:
        """Coordinate an arbitrage task across all systems"""
        try:
            task_id = f"arb_{int(datetime.now().timestamp())}"
            
            # Create coordination task
            task = CoordinationTask(
                task_id=task_id,
                task_type="arbitrage_coordination",
                priority=1,
                assigned_services=["mcp_arbitrage_server", "agent_arbitrage_detector", "langchain_coordinator"],
                parameters={"description": task_description},
                status="executing",
                created_at=datetime.now()
            )
            
            self.coordination_tasks.append(task)
            
            # Execute coordination across all systems
            results = {}
            
            # 1. MCP Server Analysis
            mcp_result = await self._query_mcp_servers(task_description)
            results['mcp_analysis'] = mcp_result
            
            # 2. AI Agent Coordination
            agent_result = await self._coordinate_ai_agents(task_description)
            results['agent_coordination'] = agent_result
            
            # 3. LangChain Intelligence
            langchain_result = await self._execute_langchain_task(task_description)
            results['langchain_intelligence'] = langchain_result
            
            # 4. AutoGen Multi-Agent Discussion
            autogen_result = await self._run_autogen_discussion(task_description)
            results['autogen_discussion'] = autogen_result
            
            # Update task
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = results
            
            # Update metrics
            self.metrics['total_tasks'] += 1
            self.metrics['successful_tasks'] += 1
            
            # Publish results
            await self._publish_coordination_result(task)
            
            return {
                'task_id': task_id,
                'status': 'success',
                'results': results,
                'execution_time': (task.completed_at - task.created_at).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"❌ Task coordination failed: {e}")
            self.metrics['failed_tasks'] += 1
            return {'status': 'error', 'error': str(e)}
            
    async def _query_mcp_servers(self, query: str) -> Dict[str, Any]:
        """Query relevant MCP servers"""
        try:
            # Determine relevant MCP servers
            relevant_servers = []
            
            if 'arbitrage' in query.lower():
                relevant_servers.extend(['mcp_arbitrage_server', 'mcp_price_feed_server'])
            if 'price' in query.lower():
                relevant_servers.extend(['mcp_price_feed_server', 'mcp_dex_aggregator_server'])
            if 'flash' in query.lower():
                relevant_servers.extend(['mcp_flash_loan_server', 'mcp_aave_flash_loan_server'])
            
            # Default to core servers if none specified
            if not relevant_servers:
                relevant_servers = ['mcp_arbitrage_server', 'mcp_price_feed_server']
            
            results = {}
            for server_name in relevant_servers:
                if server_name in self.services:
                    service = self.services[server_name]
                    try:
                        async with aiohttp.ClientSession() as session:
                            url = f"http://localhost:{service.port}/query"
                            async with session.post(url, json={'query': query}, timeout=10) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    results[server_name] = result
                                else:
                                    results[server_name] = {'error': f'HTTP {response.status}'}
                    except Exception as e:
                        results[server_name] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"❌ MCP server query failed: {e}")
            return {'error': str(e)}
            
    async def _coordinate_ai_agents(self, task: str) -> Dict[str, Any]:
        """Coordinate AI agents for a task"""
        try:
            # Determine relevant agents
            relevant_agents = []
            
            if 'arbitrage' in task.lower():
                relevant_agents.extend(['agent_arbitrage_detector', 'agent_route_optimizer'])
            if 'risk' in task.lower():
                relevant_agents.extend(['agent_risk_manager', 'agent_security_analyst'])
            if 'gas' in task.lower():
                relevant_agents.extend(['agent_gas_optimizer'])
            
            # Default agents
            if not relevant_agents:
                relevant_agents = ['agent_arbitrage_detector', 'agent_risk_manager']
            
            results = {}
            for agent_name in relevant_agents:
                if agent_name in self.services:
                    service = self.services[agent_name]
                    try:
                        async with aiohttp.ClientSession() as session:
                            url = f"http://localhost:{service.port}/coordinate"
                            async with session.post(url, json={'task': task}, timeout=15) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    results[agent_name] = result
                                else:
                                    results[agent_name] = {'error': f'HTTP {response.status}'}
                    except Exception as e:
                        results[agent_name] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"❌ AI agent coordination failed: {e}")
            return {'error': str(e)}
            
    async def _execute_langchain_task(self, task: str) -> Dict[str, Any]:
        """Execute task through LangChain coordinator"""
        try:
            if 'langchain_coordinator' in self.services:
                service = self.services['langchain_coordinator']
                async with aiohttp.ClientSession() as session:
                    url = f"http://localhost:{service.port}/execute"
                    async with session.post(url, json={'task': task}, timeout=20) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {'error': f'HTTP {response.status}'}
            else:
                return {'error': 'LangChain coordinator not available'}
                
        except Exception as e:
            logger.error(f"❌ LangChain task execution failed: {e}")
            return {'error': str(e)}
            
    async def _run_autogen_discussion(self, task: str) -> Dict[str, Any]:
        """Run AutoGen multi-agent discussion"""
        try:
            if 'autogen_system' in self.services:
                service = self.services['autogen_system']
                async with aiohttp.ClientSession() as session:
                    url = f"http://localhost:{service.port}/discuss"
                    async with session.post(url, json={'topic': task}, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {'error': f'HTTP {response.status}'}
            else:
                return {'error': 'AutoGen system not available'}
                
        except Exception as e:
            logger.error(f"❌ AutoGen discussion failed: {e}")
            return {'error': str(e)}
            
    async def _publish_coordination_result(self, task: CoordinationTask):
        """Publish coordination results to message queue"""
        try:
            if self.rabbitmq_channel:
                message = {
                    'task_id': task.task_id,
                    'task_type': task.task_type,
                    'status': task.status,
                    'result': task.result,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.rabbitmq_channel.basic_publish(
                    exchange='coordination',
                    routing_key='task.completed',
                    body=json.dumps(message)
                )
                
                logger.info(f"📢 Published result for task {task.task_id}")
                
        except Exception as e:
            logger.error(f"❌ Result publishing failed: {e}")
            
    async def start_monitoring_loop(self):
        """Start the monitoring and coordination loop"""
        try:
            logger.info("🔄 Starting monitoring loop...")
            self.is_running = True
            
            while self.is_running:
                try:
                    # Health check all services
                    health_status = await self.health_check_all_services()
                    
                    # Count healthy vs unhealthy services
                    healthy_count = sum(1 for status in health_status.values() if status == ServiceStatus.RUNNING)
                    total_count = len(health_status)
                    
                    logger.info(f"📊 System Health: {healthy_count}/{total_count} services running")
                    
                    # Restart failed services
                    failed_services = [
                        name for name, status in health_status.items() 
                        if status in [ServiceStatus.STOPPED, ServiceStatus.ERROR]
                    ]
                    
                    if failed_services:
                        logger.warning(f"⚠️ Restarting failed services: {failed_services}")
                        for service_name in failed_services:
                            if service_name in self.services:
                                await self._restart_service(self.services[service_name])
                    
                    # Update metrics
                    self.metrics['system_uptime'] = time.time()
                    
                    # Check for arbitrage opportunities every 30 seconds
                    if int(time.time()) % 30 == 0:
                        await self.coordinate_arbitrage_task(
                            "Scan for arbitrage opportunities across all DEXes and execute optimal strategies"
                        )
                    
                    await asyncio.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    logger.error(f"❌ Monitoring loop error: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"❌ Monitoring loop failed: {e}")
            
    async def _restart_service(self, service: ServiceConfig):
        """Restart a failed service"""
        try:
            logger.info(f"🔄 Restarting {service.name}...")
            
            # Stop existing container
            try:
                container = self.docker_client.containers.get(service.container_name)
                container.stop()
                container.remove()
            except:
                pass
            
            # Start the service again
            await self._start_service(service)
            
            logger.info(f"✅ {service.name} restarted successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to restart {service.name}: {e}")
            
    async def run_master_coordination_system(self):
        """Run the complete master coordination system"""
        try:
            print("\n" + "="*120)
            print("🚀 MASTER COORDINATION SYSTEM FOR FLASH LOAN ARBITRAGE BOT")
            print("="*120)
            print(f"📊 Total Services: {len(self.services)}")
            print(f"🤖 MCP Servers: {len([s for s in self.services.values() if s.service_type == ServiceType.MCP_SERVER])}")
            print(f"🎯 AI Agents: {len([s for s in self.services.values() if s.service_type == ServiceType.AI_AGENT])}")
            print(f"🧠 LangChain Agents: {len([s for s in self.services.values() if s.service_type == ServiceType.LANGCHAIN_AGENT])}")
            print(f"🤝 AutoGen Agents: {len([s for s in self.services.values() if s.service_type == ServiceType.AUTOGEN_AGENT])}")
            print("="*120)
            
            # Initialize infrastructure
            await self.initialize_infrastructure()
            
            # Start all services
            await self.start_all_services()
            
            # Wait for services to stabilize
            logger.info("⏳ Waiting for services to stabilize...")
            await asyncio.sleep(30)
            
            # Start monitoring
            await self.start_monitoring_loop()
            
        except Exception as e:
            logger.error(f"❌ Master coordination system failed: {e}")
            raise
            
    async def stop_all_services(self):
        """Stop all services gracefully"""
        try:
            logger.info("🛑 Stopping all services...")
            self.is_running = False
            
            # Stop all containers
            for service_name, service_config in self.services.items():
                try:
                    container = self.docker_client.containers.get(service_config.container_name)
                    container.stop(timeout=10)
                    container.remove()
                    logger.info(f"✅ Stopped {service_name}")
                except Exception as e:
                    logger.error(f"❌ Error stopping {service_name}: {e}")
            
            # Close connections
            if self.rabbitmq_connection:
                self.rabbitmq_connection.close()
                
            logger.info("✅ All services stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping services: {e}")

async def main():
    """Main function"""
    coordination_system = MasterCoordinationSystem()
    
    try:
        await coordination_system.run_master_coordination_system()
    except KeyboardInterrupt:
        logger.info("👋 Shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
    finally:
        await coordination_system.stop_all_services()

if __name__ == "__main__":
    asyncio.run(main())
