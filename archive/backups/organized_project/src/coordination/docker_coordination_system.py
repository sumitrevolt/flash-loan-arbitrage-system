#!/usr/bin/env python3
"""
Docker-based MCP Server and Agent Coordination System
====================================================

This system orchestrates coordination between:
1. MCP Servers (21 specialized servers)
2. AI Agents (10 specialized agents)
3. LangChain agents for intelligent coordination
4. AutoGen multi-agent conversations

All components run in Docker containers with advanced networking and communication.
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
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import websockets
import redis
import pika

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
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
        logging.FileHandler('docker_coordination_system.log'),
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
    enabled: bool = True

class DockerCoordinationSystem:
    """Main coordination system for Docker-based services"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.is_running = False
        self.services: Dict[str, ServiceConfig] = {}
        self.container_health: Dict[str, bool] = {}
        
        # Communication infrastructure
        self.redis_client = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        
        # LangChain setup
        self.langchain_agents: Dict[str, Any] = {}
        self.langchain_memory = ConversationBufferWindowMemory(k=10)
        
        # AutoGen setup
        self.autogen_agents: Dict[str, Any] = {}
        self.group_chat = None
        self.group_chat_manager = None
        
        # Load configurations
        self._load_service_configurations()
        
    def _load_service_configurations(self):
        """Load service configurations from JSON files"""
        try:
            # Load MCP server configurations
            with open('unified_mcp_config.json', 'r') as f:
                mcp_config = json.load(f)
                
            for server_name, config in mcp_config.get('servers', {}).items():
                if config.get('enabled', True):
                    self.services[server_name] = ServiceConfig(
                        name=server_name,
                        service_type=ServiceType.MCP_SERVER,
                        container_name=f"mcp_{server_name}",
                        port=config.get('port', 8000),
                        health_endpoint="/health",
                        dependencies=[],
                        environment={
                            'SERVER_TYPE': server_name,
                            'PORT': str(config.get('port', 8000))
                        }
                    )
                    
            # Load AI agent configurations
            with open('ai_agents_config.json', 'r') as f:
                agent_config = json.load(f)
                
            for agent_name, config in agent_config.get('agents', {}).items():
                self.services[agent_name] = ServiceConfig(
                    name=agent_name,
                    service_type=ServiceType.AI_AGENT,
                    container_name=f"agent_{agent_name}",
                    port=config.get('port', 9000),
                    health_endpoint="/health",
                    dependencies=['redis', 'rabbitmq'],
                    environment={
                        'AGENT_TYPE': agent_name,
                        'AGENT_ROLE': config.get('role', ''),
                        'PORT': str(config.get('port', 9000))
                    }
                )
                
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            
    async def initialize_infrastructure(self):
        """Initialize Redis, RabbitMQ, and other infrastructure"""
        try:
            # Start infrastructure containers
            await self._start_infrastructure_containers()
            
            # Wait for infrastructure to be ready
            await asyncio.sleep(10)
            
            # Initialize Redis connection
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Initialize RabbitMQ connection
            connection_params = pika.ConnectionParameters('localhost')
            self.rabbitmq_connection = pika.BlockingConnection(connection_params)
            self.rabbitmq_channel = self.rabbitmq_connection.channel()
            
            # Declare exchanges and queues
            self.rabbitmq_channel.exchange_declare(exchange='coordination', exchange_type='topic')
            self.rabbitmq_channel.queue_declare(queue='mcp_commands', durable=True)
            self.rabbitmq_channel.queue_declare(queue='agent_responses', durable=True)
            self.rabbitmq_channel.queue_declare(queue='langchain_tasks', durable=True)
            self.rabbitmq_channel.queue_declare(queue='autogen_conversations', durable=True)
            
            logger.info("Infrastructure initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing infrastructure: {e}")
            raise
            
    async def _start_infrastructure_containers(self):
        """Start Redis, RabbitMQ, and PostgreSQL containers"""
        infrastructure_services = [
            {
                'name': 'redis',
                'image': 'redis:7-alpine',
                'ports': {'6379/tcp': 6379},
                'healthcheck': {
                    'test': ['CMD', 'redis-cli', 'ping'],
                    'interval': 30000000000,  # 30s in nanoseconds
                    'timeout': 10000000000,   # 10s in nanoseconds
                    'retries': 3
                }
            },
            {
                'name': 'rabbitmq',
                'image': 'rabbitmq:3-management',
                'ports': {'5672/tcp': 5672, '15672/tcp': 15672},
                'environment': {
                    'RABBITMQ_DEFAULT_USER': 'flashloan',
                    'RABBITMQ_DEFAULT_PASS': 'flashloan_pass'
                }
            },
            {
                'name': 'postgres',
                'image': 'postgres:15-alpine',
                'ports': {'5432/tcp': 5432},
                'environment': {
                    'POSTGRES_DB': 'flashloan',
                    'POSTGRES_USER': 'flashloan',
                    'POSTGRES_PASSWORD': 'flashloan_pass'
                }
            }
        ]
        
        for service in infrastructure_services:
            try:
                container = self.docker_client.containers.run(
                    service['image'],
                    name=f"fl_{service['name']}",
                    ports=service.get('ports', {}),
                    environment=service.get('environment', {}),
                    detach=True,
                    remove=True,
                    network_mode='bridge'
                )
                logger.info(f"Started {service['name']} container: {container.id[:12]}")
                
            except docker.errors.APIError as e:
                if "Conflict" in str(e):
                    logger.info(f"{service['name']} container already running")
                else:
                    logger.error(f"Error starting {service['name']}: {e}")
                    
    async def initialize_langchain_agents(self):
        """Initialize LangChain agents for intelligent coordination"""
        try:
            # Define LangChain tools for MCP server interaction
            mcp_tools = [
                Tool(
                    name="query_mcp_server",
                    description="Query a specific MCP server for information",
                    func=self._query_mcp_server
                ),
                Tool(
                    name="coordinate_agents",
                    description="Coordinate multiple AI agents for a task",
                    func=self._coordinate_agents
                ),
                Tool(
                    name="analyze_arbitrage_opportunity",
                    description="Analyze arbitrage opportunities using MCP data",
                    func=self._analyze_arbitrage_opportunity
                ),
                Tool(
                    name="execute_flash_loan",
                    description="Execute a flash loan transaction",
                    func=self._execute_flash_loan
                )
            ]
            
            # Create LangChain agents
            llm = ChatOllama(model="llama2", temperature=0.1)
            
            # Coordinator Agent
            coordinator_prompt = PromptTemplate(
                input_variables=["input", "agent_scratchpad", "chat_history"],
                template="""You are the Coordinator Agent responsible for orchestrating MCP servers and AI agents.
                
Available tools: {tools}
Chat history: {chat_history}

Current task: {input}
{agent_scratchpad}

Coordinate the appropriate services to complete this task efficiently."""
            )
            
            coordinator_agent = create_react_agent(llm, mcp_tools, coordinator_prompt)
            self.langchain_agents['coordinator'] = AgentExecutor(
                agent=coordinator_agent,
                tools=mcp_tools,
                memory=self.langchain_memory,
                verbose=True,
                handle_parsing_errors=True
            )
            
            # Analyzer Agent
            analyzer_prompt = PromptTemplate(
                input_variables=["input", "agent_scratchpad", "chat_history"],
                template="""You are the Analyzer Agent specialized in market analysis and opportunity detection.
                
Available tools: {tools}
Chat history: {chat_history}

Analysis request: {input}
{agent_scratchpad}

Provide detailed analysis using MCP server data and AI agent insights."""
            )
            
            analyzer_agent = create_react_agent(llm, mcp_tools, analyzer_prompt)
            self.langchain_agents['analyzer'] = AgentExecutor(
                agent=analyzer_agent,
                tools=mcp_tools,
                memory=self.langchain_memory,
                verbose=True,
                handle_parsing_errors=True
            )
            
            logger.info("LangChain agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LangChain agents: {e}")
            
    async def initialize_autogen_agents(self):
        """Initialize AutoGen agents for multi-agent conversations"""
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen not available, skipping AutoGen agent initialization")
            return
            
        try:
            # Configuration for AutoGen agents
            config_list = [
                {
                    "model": "gpt-4",
                    "api_key": os.getenv("OPENAI_API_KEY", "dummy_key"),
                    "api_type": "open_ai",
                    "api_base": "http://localhost:11434/v1",  # Ollama endpoint
                }
            ]
            
            # Create AutoGen agents
            self.autogen_agents['coordinator'] = AssistantAgent(
                name="Coordinator",
                system_message="""You are a Coordinator agent responsible for orchestrating MCP servers and AI agents.
                You coordinate between different services to achieve optimal arbitrage execution.""",
                llm_config={"config_list": config_list}
            )
            
            self.autogen_agents['analyzer'] = AssistantAgent(
                name="Analyzer",
                system_message="""You are an Analyzer agent specialized in market analysis.
                You analyze price data, liquidity, and arbitrage opportunities from MCP servers.""",
                llm_config={"config_list": config_list}
            )
            
            self.autogen_agents['executor'] = AssistantAgent(
                name="Executor",
                system_message="""You are an Executor agent responsible for transaction execution.
                You handle flash loan execution and risk management.""",
                llm_config={"config_list": config_list}
            )
            
            self.autogen_agents['risk_manager'] = AssistantAgent(
                name="RiskManager",
                system_message="""You are a Risk Manager agent responsible for risk assessment.
                You evaluate risks and provide safety recommendations.""",
                llm_config={"config_list": config_list}
            )
            
            # Create user proxy agent
            self.autogen_agents['user_proxy'] = UserProxyAgent(
                name="UserProxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=10,
                code_execution_config=False
            )
            
            # Create group chat
            self.group_chat = GroupChat(
                agents=list(self.autogen_agents.values()),
                messages=[],
                max_round=20
            )
            
            self.group_chat_manager = GroupChatManager(
                groupchat=self.group_chat,
                llm_config={"config_list": config_list}
            )
            
            logger.info("AutoGen agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AutoGen agents: {e}")
            
    async def start_mcp_servers(self):
        """Start all MCP server containers"""
        mcp_servers = [service for service in self.services.values() 
                      if service.service_type == ServiceType.MCP_SERVER]
        
        for server in mcp_servers:
            try:
                # Create Dockerfile content for MCP server
                dockerfile_content = f"""
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY mcp_servers/{server.name}.py .
COPY mcp_servers/ ./mcp_servers/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT={server.port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{server.port}/health || exit 1

# Expose port
EXPOSE {server.port}

# Run the server
CMD ["python", "{server.name}.py"]
"""
                
                # Build and run container
                container = self.docker_client.containers.run(
                    "python:3.11-slim",
                    name=server.container_name,
                    ports={f'{server.port}/tcp': server.port},
                    environment=server.environment,
                    detach=True,
                    remove=True,
                    network_mode='bridge'
                )
                
                logger.info(f"Started MCP server {server.name}: {container.id[:12]}")
                
            except Exception as e:
                logger.error(f"Error starting MCP server {server.name}: {e}")
                
    async def start_ai_agents(self):
        """Start all AI agent containers"""
        ai_agents = [service for service in self.services.values() 
                    if service.service_type == ServiceType.AI_AGENT]
        
        for agent in ai_agents:
            try:
                # Create Dockerfile content for AI agent
                dockerfile_content = f"""
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy AI agent code
COPY src/ai_agents/ ./ai_agents/
COPY advanced_agentic_coordination.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT={agent.port}
ENV AGENT_TYPE={agent.name}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{agent.port}/health || exit 1

# Expose port
EXPOSE {agent.port}

# Run the agent
CMD ["python", "advanced_agentic_coordination.py"]
"""
                
                # Build and run container
                container = self.docker_client.containers.run(
                    "python:3.11-slim",
                    name=agent.container_name,
                    ports={f'{agent.port}/tcp': agent.port},
                    environment=agent.environment,
                    detach=True,
                    remove=True,
                    network_mode='bridge'
                )
                
                logger.info(f"Started AI agent {agent.name}: {container.id[:12]}")
                
            except Exception as e:
                logger.error(f"Error starting AI agent {agent.name}: {e}")
                
    async def coordinate_task(self, task_description: str) -> Dict[str, Any]:
        """Coordinate a task across MCP servers and agents"""
        try:
            coordination_result = {
                'task': task_description,
                'timestamp': datetime.now().isoformat(),
                'langchain_result': None,
                'autogen_result': None,
                'mcp_responses': [],
                'agent_responses': []
            }
            
            # 1. Use LangChain coordinator for initial analysis
            if 'coordinator' in self.langchain_agents:
                langchain_result = await self.langchain_agents['coordinator'].ainvoke({
                    'input': task_description
                })
                coordination_result['langchain_result'] = langchain_result
                
            # 2. Use AutoGen for multi-agent discussion
            if AUTOGEN_AVAILABLE and self.group_chat_manager:
                autogen_result = await self._run_autogen_conversation(task_description)
                coordination_result['autogen_result'] = autogen_result
                
            # 3. Query relevant MCP servers
            mcp_responses = await self._query_relevant_mcp_servers(task_description)
            coordination_result['mcp_responses'] = mcp_responses
            
            # 4. Coordinate AI agents
            agent_responses = await self._coordinate_relevant_agents(task_description)
            coordination_result['agent_responses'] = agent_responses
            
            # 5. Publish coordination results to message queue
            await self._publish_coordination_result(coordination_result)
            
            logger.info(f"Task coordination completed: {task_description}")
            return coordination_result
            
        except Exception as e:
            logger.error(f"Error coordinating task: {e}")
            return {'error': str(e)}
            
    async def _run_autogen_conversation(self, topic: str) -> Dict[str, Any]:
        """Run an AutoGen multi-agent conversation"""
        if not AUTOGEN_AVAILABLE:
            return {'error': 'AutoGen not available'}
            
        try:
            # Start conversation
            initial_message = f"""
            Task: {topic}
            
            Please coordinate to analyze this arbitrage opportunity and provide recommendations.
            Each agent should contribute their expertise:
            - Coordinator: Overall strategy
            - Analyzer: Market analysis
            - Executor: Implementation plan
            - RiskManager: Risk assessment
            """
            
            # This would typically be run synchronously in AutoGen
            # For async compatibility, we'll simulate the conversation
            conversation_log = []
            
            # Simulate multi-agent conversation flow
            agents_order = ['analyzer', 'coordinator', 'risk_manager', 'executor']
            
            for agent_name in agents_order:
                if agent_name in self.autogen_agents:
                    # Simulate agent response (in real implementation, use AutoGen's chat)
                    response = f"Agent {agent_name} analyzing: {topic}"
                    conversation_log.append({
                        'agent': agent_name,
                        'message': response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
            return {
                'conversation_log': conversation_log,
                'participants': len(agents_order),
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error in AutoGen conversation: {e}")
            return {'error': str(e)}
            
    async def _query_relevant_mcp_servers(self, task_description: str) -> List[Dict[str, Any]]:
        """Query relevant MCP servers based on task description"""
        responses = []
        
        # Determine relevant MCP servers based on task keywords
        relevant_servers = []
        
        if 'price' in task_description.lower() or 'arbitrage' in task_description.lower():
            relevant_servers.extend(['enhanced_mcp_price_feed_server', 'dex_aggregator_mcp_server'])
            
        if 'flash loan' in task_description.lower():
            relevant_servers.extend(['aave_flash_loan_mcp_server', 'flash_loan_mcp_mcp_server'])
            
        if 'risk' in task_description.lower():
            relevant_servers.extend(['evm_mcp_server'])
            
        # Query each relevant server
        for server_name in relevant_servers:
            if server_name in self.services:
                try:
                    server_config = self.services[server_name]
                    async with aiohttp.ClientSession() as session:
                        url = f"http://localhost:{server_config.port}/query"
                        async with session.post(url, json={'query': task_description}) as response:
                            if response.status == 200:
                                result = await response.json()
                                responses.append({
                                    'server': server_name,
                                    'response': result,
                                    'status': 'success'
                                })
                            else:
                                responses.append({
                                    'server': server_name,
                                    'error': f"HTTP {response.status}",
                                    'status': 'error'
                                })
                                
                except Exception as e:
                    responses.append({
                        'server': server_name,
                        'error': str(e),
                        'status': 'error'
                    })
                    
        return responses
        
    async def _coordinate_relevant_agents(self, task_description: str) -> List[Dict[str, Any]]:
        """Coordinate with relevant AI agents"""
        responses = []
        
        # Determine relevant agents based on task keywords
        relevant_agents = []
        
        if 'arbitrage' in task_description.lower():
            relevant_agents.extend(['arbitrage_detector', 'route_optimizer'])
            
        if 'risk' in task_description.lower():
            relevant_agents.extend(['risk_manager', 'security_analyst'])
            
        if 'gas' in task_description.lower() or 'cost' in task_description.lower():
            relevant_agents.extend(['gas_optimizer'])
            
        if 'liquidity' in task_description.lower():
            relevant_agents.extend(['liquidity_monitor'])
            
        # Coordinate with each relevant agent
        for agent_name in relevant_agents:
            if agent_name in self.services:
                try:
                    agent_config = self.services[agent_name]
                    async with aiohttp.ClientSession() as session:
                        url = f"http://localhost:{agent_config.port}/coordinate"
                        async with session.post(url, json={'task': task_description}) as response:
                            if response.status == 200:
                                result = await response.json()
                                responses.append({
                                    'agent': agent_name,
                                    'response': result,
                                    'status': 'success'
                                })
                            else:
                                responses.append({
                                    'agent': agent_name,
                                    'error': f"HTTP {response.status}",
                                    'status': 'error'
                                })
                                
                except Exception as e:
                    responses.append({
                        'agent': agent_name,
                        'error': str(e),
                        'status': 'error'
                    })
                    
        return responses
        
    async def _publish_coordination_result(self, result: Dict[str, Any]):
        """Publish coordination results to message queue"""
        try:
            if self.rabbitmq_channel:
                self.rabbitmq_channel.basic_publish(
                    exchange='coordination',
                    routing_key='task.completed',
                    body=json.dumps(result)
                )
                
            if self.redis_client:
                self.redis_client.setex(
                    f"coordination:result:{result['timestamp']}", 
                    3600,  # 1 hour TTL
                    json.dumps(result)
                )
                
        except Exception as e:
            logger.error(f"Error publishing coordination result: {e}")
            
    # Tool functions for LangChain agents
    def _query_mcp_server(self, server_query: str) -> str:
        """Tool function to query MCP server"""
        try:
            # Parse server name and query from input
            parts = server_query.split(':', 1)
            if len(parts) == 2:
                server_name, query = parts
                # Implementation would query the actual server
                return f"Queried {server_name} with: {query}"
            else:
                return f"Invalid query format. Use 'server_name:query'"
        except Exception as e:
            return f"Error querying MCP server: {e}"
            
    def _coordinate_agents(self, coordination_request: str) -> str:
        """Tool function to coordinate agents"""
        try:
            # Implementation would coordinate with actual agents
            return f"Coordinating agents for: {coordination_request}"
        except Exception as e:
            return f"Error coordinating agents: {e}"
            
    def _analyze_arbitrage_opportunity(self, opportunity_data: str) -> str:
        """Tool function to analyze arbitrage opportunity"""
        try:
            # Implementation would perform actual analysis
            return f"Analyzing arbitrage opportunity: {opportunity_data}"
        except Exception as e:
            return f"Error analyzing opportunity: {e}"
            
    def _execute_flash_loan(self, execution_params: str) -> str:
        """Tool function to execute flash loan"""
        try:
            # Implementation would execute actual flash loan
            return f"Flash loan execution requested: {execution_params}"
        except Exception as e:
            return f"Error executing flash loan: {e}"
            
    async def health_check_all_services(self) -> Dict[str, bool]:
        """Check health of all services"""
        health_status = {}
        
        for service_name, service_config in self.services.items():
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"http://localhost:{service_config.port}{service_config.health_endpoint}"
                    async with session.get(url, timeout=5) as response:
                        health_status[service_name] = response.status == 200
                        
            except Exception as e:
                health_status[service_name] = False
                logger.error(f"Health check failed for {service_name}: {e}")
                
        return health_status
        
    async def recover_unhealthy_services(self, health_status: Dict[str, bool]):
        """Attempt to recover unhealthy services"""
        unhealthy_services = [name for name, healthy in health_status.items() if not healthy]
        
        for service_name in unhealthy_services:
            try:
                service_config = self.services.get(service_name)
                if service_config:
                    logger.info(f"Attempting recovery for {service_name}")
                    container = self.docker_client.containers.get(service_config.container_name)
                    container.restart()
                    logger.info(f"Restarted container for {service_name}")
                    
                    # Wait for a brief period before rechecking health
                    await asyncio.sleep(10)
                    async with aiohttp.ClientSession() as session:
                        url = f"http://localhost:{service_config.port}{service_config.health_endpoint}"
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                logger.info(f"Recovery successful for {service_name}")
                            else:
                                logger.error(f"Recovery failed for {service_name}: Still unhealthy after restart")
            except Exception as e:
                logger.error(f"Error during recovery of {service_name}: {e}")
                
    async def run_coordination_system(self):
        """Main coordination system loop"""
        try:
            logger.info("Starting Docker Coordination System...")
            
            # Initialize infrastructure
            await self.initialize_infrastructure()
            
            # Initialize agents
            await self.initialize_langchain_agents()
            await self.initialize_autogen_agents()
            
            # Start services
            await self.start_mcp_servers()
            await self.start_ai_agents()
            
            # Wait for services to be ready
            await asyncio.sleep(30)
            
            self.is_running = True
            logger.info("Docker Coordination System is running")
            
            # Main coordination loop
            while self.is_running:
                try:
                    # Check service health
                    health_status = await self.health_check_all_services()
                    unhealthy_services = [name for name, healthy in health_status.items() if not healthy]
                    
                    if unhealthy_services:
                        logger.warning(f"Unhealthy services detected: {unhealthy_services}")
                        await self.recover_unhealthy_services(health_status)
                        
                    # Example coordination task
                    if datetime.now().minute % 5 == 0:  # Every 5 minutes
                        await self.coordinate_task(
                            "Analyze current arbitrage opportunities across all DEXes and recommend optimal flash loan strategies"
                        )
                        
                    await asyncio.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error in coordination loop: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Error in coordination system: {e}")
            raise
        finally:
            await self.cleanup()
            
    async def cleanup(self):
        """Cleanup resources"""
        try:
            self.is_running = False
            
            # Close connections
            if self.rabbitmq_connection:
                self.rabbitmq_connection.close()
                
            # Stop containers
            for service_name, service_config in self.services.items():
                try:
                    container = self.docker_client.containers.get(service_config.container_name)
                    container.stop()
                    logger.info(f"Stopped container: {service_config.container_name}")
                except Exception as e:
                    logger.error(f"Error stopping container {service_config.container_name}: {e}")
                    
            logger.info("Coordination system cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main function"""
    coordination_system = DockerCoordinationSystem()
    
    try:
        await coordination_system.run_coordination_system()
    except KeyboardInterrupt:
        logger.info("Coordination system interrupted by user")
    except Exception as e:
        logger.error(f"Coordination system error: {e}")
    finally:
        await coordination_system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
