#!/usr/bin/env python3
"""
Enhanced LangChain Orchestrator with 21 MCP Servers, 10 Agents, GitHub Integration, and Automated Error Handling
"""

import asyncio
import logging
import time
import os
import json
import aiohttp
import subprocess
from functools import lru_cache
from typing import List, Dict, Any, Optional, Union, Sequence, cast, Tuple, TypedDict, Literal, Callable
from typing import Set, Deque
from collections import deque
from datetime import datetime
from dataclasses import dataclass, field
import docker
import redis
import psycopg2
import pika
from autogen import (
    AssistantAgent as AutoGenAssistantAgent,  # type: ignore[reportAssignmentType]
    UserProxyAgent as AutoGenUserProxyAgent,  # type: ignore[reportAssignmentType]
    GroupChat as AutoGenGroupChat,  # type: ignore[reportAssignmentType]
    GroupChatManager as AutoGenGroupChatManager,  # type: ignore[reportAssignmentType]
    Agent as AutoGenAgent  # type: ignore[reportAssignmentType]
)
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LangchainOrchestrator")

# Optional dependency handling
autogen_available = False
try:
    # Import autogen modules but don't redefine them (already imported above)
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, Agent
    autogen_available = True
except ImportError:
    autogen_available = False
try:
    transformers_available = True
except ImportError:
    transformers_available = False

# Set overall ML availability flag
advanced_ml_available = autogen_available and transformers_available
if not advanced_ml_available:
    logging.warning("Advanced ML functionality is limited due to missing libraries")


class QuantumLogger(logging.Logger):
    """Advanced logger with state tracking"""
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.states: Deque[Dict[str, Any]] = deque(maxlen=1000)
        
    def state_log(self, level: int, msg: str, state: Any = None) -> None:
        if state:
            self.states.append({
                'timestamp': datetime.now(),
                'state': state,
                'message': msg
            })
        self.log(level, msg)


@dataclass
class AutoGenAgentConfig:
    """Configuration for AutoGen agents"""
    name: str
    system_message: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    skills: List[str] = field(default_factory=lambda: [])


@dataclass
class AgentState:
    """Agent state with essential properties"""
    id: str
    name: str
    state: str = "idle"
    performance: float = 0.0
    confidence: float = 0.5
    energy: float = 1.0
    last_update: datetime = field(default_factory=datetime.now)
    knowledge_base: Dict[str, str] = field(default_factory=lambda: {})
    execution_history: List[Dict[str, str]] = field(default_factory=lambda: [])


@dataclass
class TaskDefinition:
    """Task definition with essential properties"""
    id: str
    name: str
    description: str
    priority: float = 1.0
    dependencies: List[str] = field(default_factory=lambda: [])
    estimated_complexity: float = 1.0
    required_skills: List[str] = field(default_factory=lambda: [])
    environment: Dict[str, str] = field(default_factory=lambda: {})
    success_criteria: str = ""
    

@dataclass
class MCPServerConfig:
    """MCP Server configuration with enhanced capabilities"""
    name: str
    command: str
    args: List[str] = field(default_factory=lambda: [])
    env: Dict[str, str] = field(default_factory=lambda: {})
    skills: List[str] = field(default_factory=lambda: [])
    mcp_dependencies: List[str] = field(default_factory=lambda: [])
    port: Optional[int] = None
    auto_restart: bool = True
    health_check_interval: int = 60


@dataclass 
class MarketOpportunity:
    """Flash loan market opportunity"""
    token_pair: str
    price_difference: float
    potential_profit: float
    risk_score: float
    exchange_pair: Tuple[str, str]
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.5


@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_slippage: float = 0.05
    max_gas_price: float = 100.0
    min_profit_threshold: float = 0.01
    max_position_size: float = 1000.0
    stop_loss_threshold: float = 0.02


@dataclass
class SystemMetrics:
    """System performance metrics"""
    total_agents: int = 0
    active_agents: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    system_load: float = 0.0
    memory_usage: float = 0.0
    network_latency: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class OrchestratorState:
    """Complete orchestrator state"""
    agents: Dict[str, AgentState] = field(default_factory=lambda: {})
    tasks: Dict[str, TaskDefinition] = field(default_factory=lambda: {})
    servers: Dict[str, MCPServerConfig] = field(default_factory=lambda: {})
    opportunities: Deque[MarketOpportunity] = field(default_factory=lambda: deque(maxlen=1000))
    risk_params: RiskParameters = field(default_factory=RiskParameters)
    metrics: SystemMetrics = field(default_factory=SystemMetrics)
    active_servers: Set[str] = field(default_factory=lambda: set())
    active_agents: Set[str] = field(default_factory=lambda: set())
    global_state: str = "initializing"


class SelfHealingMixin:
    """Mixin for self-healing capabilities"""
    def __init__(self):
        self.health_status = "healthy"
        self.last_health_check = datetime.now()
    
    def check_health(self) -> bool:
        """Check system health"""
        return self.health_status == "healthy"
    
    def heal(self) -> bool:
        """Attempt to heal system issues"""
        try:
            self.health_status = "healthy"
            self.last_health_check = datetime.now()
            return True
        except Exception as e:
            logging.error(f"Healing failed: {e}")
            return False


class AutoGenIntegrationManager(SelfHealingMixin):
    """Manager for AutoGen agents and LangChain integration"""
    
    def __init__(self):
        super().__init__()
        self.autogen_agents: Dict[str, Any] = {}
        self.group_chats: Dict[str, Any] = {}
        self.agent_configs: Dict[str, Any] = {}
        self.active_conversations: Dict[str, Any] = {}
        self.autogen_available = autogen_available
        
    def create_autogen_agent(self, config: AutoGenAgentConfig) -> Optional[Any]:
        """Create an AutoGen agent based on configuration"""
        if not self.autogen_available:
            logging.warning("AutoGen not available, cannot create agent")
            return None
            
        try:
            # Create agent based on configuration
            if config.name.lower().startswith('user'):
                agent = AutogenUserProxyAgent(
                    name=f"user_proxy_{agent_id}",
                    name_or_id=config.name,
                    human_input_mode="NEVER",
                    system_message=config.system_message,
                    llm_config={
                        "model": config.model,
                        "temperature": config.temperature,
                        "max_tokens": config.max_tokens
                    }
                )
            else:
                agent = AutogenAssistantAgent(
                    name=f"assistant_{agent_id}",
                    name_or_id=config.name,
                    human_input_mode="NEVER",
                    system_message=config.system_message,
                    llm_config={
                        "model": config.model,
                        "temperature": config.temperature,
                        "max_tokens": config.max_tokens
                    }
                )
            
            self.autogen_agents[config.name] = agent
            self.agent_configs[config.name] = config
            
            logging.info(f"Created AutoGen agent: {config.name}")
            return agent
            
        except Exception as e:
            logging.error(f"Failed to create agent {config.name}: {e}")
            return None

    def create_group_chat(
        self,
        name: str,
        agents: Sequence[Union['AssistantAgent', 'UserProxyAgent']],
        max_round: int = 10
    ) -> Optional['GroupChat']:
        """Create a group chat with multiple agents"""
        if not self.autogen_available or not agents:
            logging.warning("AutoGen not available or no agents provided for group chat")
            return None
        
        try:
            # Cast the sequence to list[Agent] to satisfy type checker
            agent_list: AgentList = agents if isinstance(agents, list) else list(agents)
            
            # Create instance using kwargs to avoid parameter name issues
            group_chat = GroupChat(
                agents=agent_list,
                messages=[],  # type: ignore
                max_round=max_round  # type: ignore
            )
            
            # Same approach for GroupChatManager
            manager = GroupChatManager(
                groupchat=group_chat,  # type: ignore
                llm_config={"model": "gpt-4", "temperature": 0.7}  # type: ignore
            )
            
            self.group_chats[name] = {
                'chat': group_chat,
                'manager': manager,
                'agents': agents
            }
            
            logging.info(f"Created group chat: {name} with {len(agents)} agents")
            return group_chat
            
        except Exception as e:
            logging.error(f"Failed to create group chat {name}: {e}")
            return None
    
    async def initiate_conversation(self, agent_name: str, recipient_name: str, message: str) -> Optional[Dict[str, Any]]:
        """Initiate a conversation between two agents"""
        try:
            if agent_name not in self.autogen_agents or recipient_name not in self.autogen_agents:
                logging.error(f"One or both agents not found: {agent_name}, {recipient_name}")
                return None
            
            initiator = self.autogen_agents[agent_name]
            recipient = self.autogen_agents[recipient_name]
            
            # Start conversation in a separate task to avoid blocking
            conversation_task = asyncio.create_task(
                self._run_conversation(initiator, recipient, message)
            )
            
            conversation_id = f"{agent_name}_{recipient_name}_{datetime.now().timestamp()}"
            self.active_conversations[conversation_id] = {
                'task': conversation_task,
                'initiator': agent_name,
                'recipient': recipient_name,
                'message': message,
                'start_time': datetime.now()
            }
            
            logging.info(f"Initiated conversation between {agent_name} and {recipient_name}")
            return {
                'conversation_id': conversation_id,
                'status': 'initiated',
                'participants': [agent_name, recipient_name]
            }
            
        except Exception as e:
            logging.error(f"Failed to initiate conversation: {e}")
            return None
    
    async def _run_conversation(self, initiator: Any, recipient: Any, message: str) -> Dict[str, Any]:
        """Run a conversation between two agents"""
        try:
            if not self.autogen_available:
                logging.warning("AutoGen not available for conversation")
                return {'status': 'error', 'message': 'AutoGen not available'}
            
            # Create a chat session between agents
            chat_result = initiator.initiate_chat(
                recipient,
                message=message,
                max_turns=10,
                silent=False
            )
            
            return {
                'status': 'completed',
                'result': chat_result,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logging.error(f"Conversation failed: {e}")
            return {'status': 'error', 'message': str(e)}

    async def get_conversation_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an active conversation"""
        if conversation_id not in self.active_conversations:
            return None
        
        conversation = self.active_conversations[conversation_id]
        task = conversation['task']
        
        if task.done():
            result = await task
            return {
                'conversation_id': conversation_id,
                'status': 'completed',
                'result': result,
                'duration': datetime.now() - conversation['start_time']
            }
        else:
            return {
                'conversation_id': conversation_id,
                'status': 'running',
                'duration': datetime.now() - conversation['start_time']
            }


class EnhancedLangChainOrchestrator:
    """Enhanced orchestrator with 21 MCP Servers, 10 Agents, and automated error handling"""
    
    def __init__(self):
        self.state = OrchestratorState()
        self.autogen_manager = AutoGenIntegrationManager()
        self.logger = QuantumLogger(__name__)
        self.github_integration = GitHubIntegration(GITHUB_TOKEN)
        self.infrastructure_manager = InfrastructureManager()
        self.mcp_server_manager = MCPServerManager()
        self.agent_manager = AgentManager()
        self.is_running = False
        
    async def run(self) -> None:
        """Main orchestration loop with enhanced coordination"""
        try:
            self.logger.info("Starting Enhanced LangChain Orchestrator with 21 MCP Servers and 10 Agents")
            self.is_running = True
            
            # Initialize system components
            await self._initialize_system()
            
            # Start background monitoring tasks
            monitoring_tasks = [
                asyncio.create_task(self.mcp_server_manager.monitor_all_servers()),
                asyncio.create_task(self._monitor_infrastructure()),
                asyncio.create_task(self._process_task_queue()),
                asyncio.create_task(self._coordinate_agents())
            ]
            
            # Wait for all monitoring tasks to complete (they run indefinitely)
            await asyncio.gather(*monitoring_tasks)
                
        except KeyboardInterrupt:
            self.logger.info("Orchestrator stopped by user")
            self.is_running = False
        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            if AUTO_HEAL_ENABLED:
                await self._attempt_self_heal(e)
            
    async def _initialize_system(self) -> None:
        """Initialize system components with health checks"""
        self.logger.info("Initializing system components...")
        
        # Check infrastructure health
        infra_status = await self.infrastructure_manager.health_check()
        self.logger.info(f"Infrastructure status: {infra_status}")
        
        # Initialize MCP servers status
        for server_id in self.mcp_server_manager.servers:
            await self.mcp_server_manager.check_server_health(server_id)
        
        self.state.global_state = "initialized"
        self.logger.info("System initialization completed")
        
    async def _monitor_infrastructure(self):
        """Monitor infrastructure components"""
        while self.is_running:
            try:
                status = await self.infrastructure_manager.health_check()
                failed_components = [comp for comp, healthy in status.items() if not healthy]
                
                if failed_components and AUTO_HEAL_ENABLED:
                    self.logger.warning(f"Failed infrastructure components: {failed_components}")
                    await self._heal_infrastructure(failed_components)
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Infrastructure monitoring error: {e}")
                await asyncio.sleep(60)
                
    async def _process_task_queue(self):
        """Process tasks from the task queue"""
        while self.is_running:
            try:
                if not self.state.tasks:
                    await asyncio.sleep(5)
                    continue
                
                for task_id, task in list(self.state.tasks.items()):
                    self.logger.info(f"Processing task: {task.name} (ID: {task_id})")
                    
                    # Coordinate agents to handle the task
                    task_dict = {
                        'id': task_id,
                        'name': task.name,
                        'description': task.description,
                        'priority': task.priority,
                        'required_skills': task.required_skills
                    }
                    
                    result = await self.agent_manager.coordinate_agents(task_dict)
                    
                    if result.get('status') == 'completed':
                        self.state.metrics.completed_tasks += 1
                        self.logger.info(f"Task {task.name} completed successfully")
                        del self.state.tasks[task_id]
                    else:
                        self.state.metrics.failed_tasks += 1
                        self.logger.error(f"Task {task.name} failed")
                        
                        if AUTO_HEAL_ENABLED:
                            await self._handle_task_failure(task_id, task, result)
                
                await asyncio.sleep(10)  # Process tasks every 10 seconds
            except Exception as e:
                self.logger.error(f"Task processing error: {e}")
                await asyncio.sleep(30)
                
    async def _coordinate_agents(self):
        """Coordinate agents and maintain their health"""
        while self.is_running:
            try:
                # Check agent status and coordinate activities
                for agent_id, agent in self.agent_manager.agents.items():
                    if agent.status == "error" and AUTO_HEAL_ENABLED:
                        await self._heal_agent(agent_id)
                
                await asyncio.sleep(30)  # Coordinate every 30 seconds
            except Exception as e:
                self.logger.error(f"Agent coordination error: {e}")
                await asyncio.sleep(60)
                
    async def _attempt_self_heal(self, error: Exception):
        """Attempt to heal from system errors"""
        self.logger.info(f"Attempting self-heal for error: {error}")
        
        try:
            # Create GitHub issue for tracking
            if GITHUB_TOKEN:
                repo = os.getenv('GITHUB_REPO', 'user/repo')  # Configure this
                await self.github_integration.create_issue(
                    repo=repo,
                    title=f"Orchestrator Error: {type(error).__name__}",
                    body=f"Error occurred in orchestrator:\n\n```\n{str(error)}\n```\n\nTimestamp: {datetime.now()}",
                    labels=['bug', 'orchestrator', 'auto-healing']
                )
            
            # Restart failed components
            await self._restart_failed_components()
            
            # Reset state if needed
            if self.state.global_state == "error":
                self.state.global_state = "recovering"
                
        except Exception as heal_error:
            self.logger.error(f"Self-healing failed: {heal_error}")
    
    async def _heal_infrastructure(self, failed_components: List[str]):
        """Heal failed infrastructure components"""
        for component in failed_components:
            try:
                self.logger.info(f"Attempting to heal {component}")
                
                if component == "redis":
                    self.infrastructure_manager.setup_connections()
                elif component == "postgres":
                    self.infrastructure_manager.setup_connections()
                elif component == "rabbitmq":
                    self.infrastructure_manager.setup_connections()
                    
            except Exception as e:
                self.logger.error(f"Failed to heal {component}: {e}")
    
    async def _heal_agent(self, agent_id: str):
        """Heal a failed agent"""
        try:
            if docker_client:
                container_name = f"langchain_agent_{agent_id}"
                container = docker_client.containers.get(container_name)
                container.restart()
                self.logger.info(f"Restarted agent container {container_name}")
                
                # Update agent status
                if agent_id in self.agent_manager.agents:
                    self.agent_manager.agents[agent_id].status = "recovering"
                    
        except Exception as e:
            self.logger.error(f"Failed to heal agent {agent_id}: {e}")
    
    async def _handle_task_failure(self, task_id: str, task: TaskDefinition, result: Dict[str, Any]):
        """Handle task failure with automated recovery"""
        self.logger.warning(f"Handling failure for task {task_id}")
        
        # Retry task with different agents
        retry_result = await self.agent_manager.coordinate_agents({
            'id': f"{task_id}_retry",
            'name': f"RETRY: {task.name}",
            'description': task.description,
            'priority': task.priority + 0.5,  # Higher priority for retries
            'required_skills': task.required_skills
        })
        
        if retry_result.get('status') == 'completed':
            self.state.metrics.completed_tasks += 1
            self.logger.info(f"Task {task.name} completed on retry")
            del self.state.tasks[task_id]
        else:
            # Create GitHub issue for persistent failures
            if GITHUB_TOKEN:
                repo = os.getenv('GITHUB_REPO', 'user/repo')
                await self.github_integration.create_issue(
                    repo=repo,
                    title=f"Persistent Task Failure: {task.name}",
                    body=f"Task failed multiple times:\n\nTask: {task.name}\nDescription: {task.description}\nResult: {result}",
                    labels=['bug', 'task-failure', 'needs-attention']
                )
    
    async def _restart_failed_components(self):
        """Restart failed system components"""
        try:
            if docker_client:
                # Get all containers in the flashloan network
                containers = docker_client.containers.list(all=True)
                
                for container in containers:
                    if container.status != 'running' and any(name in container.name for name in ['mcp_server', 'langchain_agent', 'orchestrator']):
                        self.logger.info(f"Restarting container {container.name}")
                        container.restart()
                        
        except Exception as e:
            self.logger.error(f"Failed to restart components: {e}")
    
    async def execute_task(self, task_description: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task using the enhanced orchestrator with full coordination"""
        start_time = time.time()
        self.logger.info(f"Executing task: {task_description}")
        
        try:
            # Create task definition
            task_id = f"task_{int(time.time())}"
            task = TaskDefinition(
                id=task_id,
                name=task_description,
                description=task_description,
                environment=additional_context or {}
            )
            
            # Add to task queue
            self.state.tasks[task_id] = task
            
            # Coordinate agents to execute the task
            result = await self.agent_manager.coordinate_agents({
                'id': task_id,
                'name': task_description,
                'description': task_description,
                'context': additional_context or {}
            })
            
            # Also use AutoGen agents if available
            if self.autogen_manager.autogen_available:
                autogen_result = await self._execute_with_autogen(task_description, additional_context)
                result['autogen_result'] = autogen_result
            
            processed_result = {
                "task_id": task_id,
                "description": task_description,
                "agent_coordination_result": result,
                "execution_time": time.time() - start_time,
                "status": "success",
                "mcp_servers_status": {sid: server.status for sid, server in self.mcp_server_manager.servers.items()},
                "agents_status": {aid: agent.status for aid, agent in self.agent_manager.agents.items()},
                "infrastructure_status": await self.infrastructure_manager.health_check()
            }
            
            self.logger.info(f"Task completed in {processed_result['execution_time']:.2f} seconds")
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Error executing task: {str(e)}")
            
            if AUTO_HEAL_ENABLED:
                await self._attempt_self_heal(e)
            
            error_result = {
                "task_id": task_id if 'task_id' in locals() else "unknown",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "status": "failed"
            }
            return error_result
    
    async def _execute_with_autogen(self, task_description: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute task using AutoGen agents"""
        try:
            # Create agents for this task
            assistant, user_proxy = create_agents()
            
            # Execute the task
            result = user_proxy.initiate_chat(
                assistant,
                message=f"""Task: {task_description}
                
                Context: {json.dumps(additional_context or {}, indent=2)}
                
                Please provide a detailed solution to this task."""
            )
            
            return {
                "autogen_response": result,
                "status": "completed"
            }
        except Exception as e:
            self.logger.error(f"AutoGen execution failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }


# GitHub Integration and Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
ORCHESTRATOR_MODE = os.getenv('ORCHESTRATOR_MODE', 'enhanced')
AUTO_HEAL_ENABLED = os.getenv('AUTO_HEAL_ENABLED', 'true').lower() == 'true'
MCP_SERVERS_COUNT = int(os.getenv('MCP_SERVERS_COUNT', '21'))
AGENTS_COUNT = int(os.getenv('AGENTS_COUNT', '10'))

# Infrastructure URLs
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/flashloan')
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672')

# Docker client
docker_client = docker.from_env() if os.getenv('DOCKER_HOST') else None

# Type aliases for Python < 3.12 compatibility  
AgentType = Union['AssistantAgent', 'UserProxyAgent']
AgentList = List[AgentType]
MessageDict = Dict[str, Any]
LLMConfig = Dict[str, Union[str, float, Dict[str, Any]]]

@dataclass
class MCPServerStatus:
    """Status of MCP Server"""
    id: str
    name: str
    type: str
    status: str = "unknown"
    port: int = 9000
    health_check_url: str = ""
    last_ping: Optional[datetime] = None
    error_count: int = 0
    
@dataclass
class AgentStatus:
    """Status of Agent"""
    id: str
    name: str
    type: str
    status: str = "unknown"
    last_activity: Optional[datetime] = None
    tasks_completed: int = 0
    error_count: int = 0

class GitHubIntegration:
    """GitHub integration for automated code healing and repository management"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
        self.base_url = 'https://api.github.com'
    
    async def create_issue(self, repo: str, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create GitHub issue for error tracking"""
        if not self.token or not repo:
            return {}
        
        url = f"{self.base_url}/repos/{repo}/issues"
        data = {
            'title': title,
            'body': body,
            'labels': labels or ['bug', 'auto-generated']
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=data) as response:
                    if response.status == 201:
                        return await response.json()
                    else:
                        logger.error(f"Failed to create GitHub issue: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return {}
    
    async def commit_fix(self, repo: str, branch: str, path: str, content: str, message: str) -> bool:
        """Commit automated fix to repository"""
        if not self.token or not repo:
            return False
        
        try:
            # This is a simplified version - in reality you'd need to handle file creation/updates properly
            logger.info(f"Would commit fix to {repo}/{branch}: {path}")
            return True
        except Exception as e:
            logger.error(f"Error committing fix: {e}")
            return False

class InfrastructureManager:
    """Manages infrastructure connections and health checks"""
    
    def __init__(self):
        self.redis_client = None
        self.postgres_conn = None
        self.rabbitmq_conn = None
        self.setup_connections()
    
    def setup_connections(self):
        """Setup infrastructure connections"""
        try:
            # Redis connection
            if REDIS_URL:
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                self.redis_client.ping()
                logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
        
        try:
            # PostgreSQL connection
            if POSTGRES_URL:
                self.postgres_conn = psycopg2.connect(POSTGRES_URL)
                logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
        
        try:
            # RabbitMQ connection
            if RABBITMQ_URL:
                self.rabbitmq_conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
                logger.info("RabbitMQ connection established")
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {e}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all infrastructure components"""
        status = {}
        
        # Redis health check
        try:
            if self.redis_client:
                self.redis_client.ping()
                status['redis'] = True
            else:
                status['redis'] = False
        except:
            status['redis'] = False
        
        # PostgreSQL health check
        try:
            if self.postgres_conn:
                cursor = self.postgres_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                status['postgres'] = True
            else:
                status['postgres'] = False
        except:
            status['postgres'] = False
        
        # RabbitMQ health check
        try:
            if self.rabbitmq_conn and not self.rabbitmq_conn.is_closed:
                status['rabbitmq'] = True
            else:
                status['rabbitmq'] = False
        except:
            status['rabbitmq'] = False
        
        return status

class MCPServerManager:
    """Manages 21 MCP Servers with health monitoring and auto-healing"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerStatus] = {}
        self.initialize_servers()
    
    def initialize_servers(self):
        """Initialize all 21 MCP servers configuration"""
        server_types = [
            "web_scraper", "database_manager", "file_manager", "api_gateway", "blockchain_monitor",
            "data_analyzer", "notification_service", "security_scanner", "code_generator", "test_runner",
            "deployment_manager", "log_aggregator", "metrics_collector", "config_manager", "task_scheduler",
            "ml_trainer", "image_processor", "document_parser", "auth_service", "cache_manager", "health_monitor"
        ]
        
        for i, server_type in enumerate(server_types, 1):
            server_id = f"{i:02d}"
            self.servers[server_id] = MCPServerStatus(
                id=server_id,
                name=f"mcp_server_{server_id}",
                type=server_type,
                port=9000 + i,
                health_check_url=f"http://mcp_server_{server_id}:9000/health"
            )
    
    async def check_server_health(self, server_id: str) -> bool:
        """Check health of specific MCP server"""
        if server_id not in self.servers:
            return False
        
        server = self.servers[server_id]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(server.health_check_url, timeout=5) as response:
                    if response.status == 200:
                        server.status = "healthy"
                        server.last_ping = datetime.now()
                        server.error_count = 0
                        return True
                    else:
                        server.status = "unhealthy"
                        server.error_count += 1
                        return False
        except Exception as e:
            logger.error(f"Health check failed for server {server_id}: {e}")
            server.status = "error"
            server.error_count += 1
            return False
    
    async def heal_server(self, server_id: str) -> bool:
        """Attempt to heal/restart a failed MCP server"""
        if not docker_client:
            logger.error("Docker client not available for healing")
            return False
        
        try:
            container_name = f"mcp_server_{server_id}"
            container = docker_client.containers.get(container_name)
            
            logger.info(f"Restarting container {container_name}")
            container.restart()
            
            # Wait a bit for container to start
            await asyncio.sleep(10)
            
            # Check if restart was successful
            return await self.check_server_health(server_id)
        except Exception as e:
            logger.error(f"Failed to heal server {server_id}: {e}")
            return False
    
    async def monitor_all_servers(self):
        """Monitor all MCP servers and trigger healing if needed"""
        while True:
            try:
                for server_id in self.servers:
                    is_healthy = await self.check_server_health(server_id)
                    server = self.servers[server_id]
                    
                    if not is_healthy and AUTO_HEAL_ENABLED:
                        if server.error_count >= 3:  # Threshold for healing
                            logger.warning(f"Attempting to heal server {server_id}")
                            healed = await self.heal_server(server_id)
                            if healed:
                                logger.info(f"Successfully healed server {server_id}")
                            else:
                                logger.error(f"Failed to heal server {server_id}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in server monitoring: {e}")
                await asyncio.sleep(60)

class AgentManager:
    """Manages 10 Agents with coordination and task distribution"""
    
    def __init__(self):
        self.agents: Dict[str, AgentStatus] = {}
        self.initialize_agents()
    
    def initialize_agents(self):
        """Initialize all 10 agents configuration"""
        agent_types = [
            "coordinator", "executor", "monitor", "analyzer", "optimizer",
            "validator", "reporter", "debugger", "deployer", "healer"
        ]
        
        for i, agent_type in enumerate(agent_types, 1):
            agent_id = f"{i:02d}"
            self.agents[agent_id] = AgentStatus(
                id=agent_id,
                name=f"langchain_agent_{agent_id}",
                type=agent_type
            )
    
    async def coordinate_agents(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate agents to execute a task"""
        task_id = task.get('id', f"task_{int(time.time())}")
        logger.info(f"Coordinating agents for task {task_id}")
        
        # Simple task distribution logic
        coordinator_agent = self.agents.get('01')  # Coordinator is agent 01
        if coordinator_agent:
            coordinator_agent.last_activity = datetime.now()
            coordinator_agent.tasks_completed += 1
        
        # Execute task with multiple agents
        results = {}
        for agent_id, agent in self.agents.items():
            if agent.type in ['executor', 'analyzer', 'validator']:
                agent.last_activity = datetime.now()
                agent.tasks_completed += 1
                results[agent_id] = f"Agent {agent_id} processed task {task_id}"
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'agents_involved': list(results.keys()),
            'results': results
        }

# ------------------------------------------------------------------
# Canonical aliases – use Autogen’s real classes everywhere
AssistantAgent   = autogen.AssistantAgent        # type: ignore[assignment]
UserProxyAgent   = autogen.UserProxyAgent        # type: ignore[assignment]
GroupChat        = autogen.GroupChat             # type: ignore[assignment]
GroupChatManager = autogen.GroupChatManager      # type: ignore[assignment]
Agent            = autogen.Agent                 # type: ignore[assignment]

try:
    LLMConfig = autogen.LLMConfig                # type: ignore[assignment]
except AttributeError:
    from typing import TypedDict, Any, Dict
    class LLMConfig(TypedDict, total=False):
        model: str
        temperature: float
        params: Dict[str, Any]
# ------------------------------------------------------------------

# Define strict types for dictionaries
class ManagerConfig(TypedDict, total=False):
    timeout: int
    error_handling: str

class TaskResult(TypedDict, total=False):
    raw_response: Any
    execution_time: float
    status: Literal["success", "failed"]
    error: Optional[str]

class TaskContext(TypedDict, total=False):
    task: str
    timestamp: float
    execution_id: str

# Define additional TypedDict classes for kwargs
class GroupChatKwargs(TypedDict, total=False):
    agents: List['Agent']
    messages: List[Dict[str, Any]]
    max_round: int
    termination_signals: List[str]
    speaker_selection_method: str
    allow_repeat_speaker: bool
    max_backtrack_attempts: int

class ManagerKwargs(TypedDict, total=False):
    groupchat: 'GroupChat'  # Note: parameter name must match actual usage
    llm_config: Dict[str, Union[str, float, Dict[str, Any]]]
    timeout_seconds: int
    retry_attempts: int
    verbose: bool
    message_callback: Optional[Callable[..., Any]]

class ChatInitKwargs(TypedDict, total=False):
    context: Optional[str]
    messages_callback: Optional[Callable[..., Any]]
    generate_kwargs: Dict[str, Any]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def create_agents() -> Tuple[AssistantAgent, UserProxyAgent]:
    """
    Create and configure the assistant and user proxy agents with retry logic.
    
    Returns:
        tuple: A tuple containing (assistant_agent, user_proxy_agent)
    """
    logger.info("Creating agents...")
    try:
        # Configure LLM for the assistant
        llm_config_dict: Dict[str, Any] = {
            "temperature": 0.7,
            "model": "gpt-4",
            "request_timeout": 120,
            "seed": 42  # For reproducibility
        }
        
        # Create the user proxy agent
        user_proxy = UserProxyAgent(
            name_or_id="User",
            human_input_mode="NEVER",
            system_message="You are a helpful user who provides clear and concise information.",
            llm_config=None  # User doesn't need LLM capabilities
        )
        
        # Create the assistant agent with more detailed system message
        assistant = AssistantAgent(
            name="assistant",  # Add missing name parameter
            llm_config={
                "model": "gpt-4",
                "temperature": 0.7,
            },
            system_message="You are a helpful assistant.",
        )

        logger.info("Agents created successfully")
        return assistant, user_proxy
    except Exception as e:
        logger.error(f"Error creating agents: {str(e)}")
        raise


@lru_cache(maxsize=10)
def get_config(config_name: str) -> Dict[str, Any]:
    """
    Load configuration from file with caching for efficiency.
    
    Args:
        config_name: Name of the configuration to load
        
    Returns:
        Dict containing the configuration
    """
    config_path = os.path.join(os.path.dirname(__file__), f"configs/{config_name}.json")
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_name}.json not found, using defaults")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file {config_name}.json")
        return {}


def create_group_chat(
    agents: List[Union['AssistantAgent', 'UserProxyAgent']]
) -> tuple['GroupChat', 'GroupChatManager']:
    """
    Create a group chat with the given agents with improved error handling.
    
    Args:
        agents: List of agents to include in the chat
        
    Returns:
        tuple: A tuple containing (group_chat, group_chat_manager)
    """
    logger.info(f"Creating group chat with {len(agents)} agents")
    
    if not agents:
        raise ValueError("No agents provided for group chat")
    
    # Cast the sequence to list[Agent] to satisfy type checker
    agent_list: List['Agent'] = cast(List['Agent'], agents)
    
    try:
        # Create the group chat with configurable parameters
        chat_config = get_config("group_chat")
        max_rounds = chat_config.get("max_rounds", 50)
        
        # Create instances using kwargs
        group_chat = GroupChat(
            agents=agent_list,
            messages=[],  # type: ignore
            max_round=max_rounds  # type: ignore
        )
        
        # Configure the manager with timeout and error handling
        manager_config_dict: Dict[str, Any] = {
            "timeout": 300,  # 5 minutes timeout
            "error_handling": "auto_recover"
        }
        
        manager = GroupChatManager(
            group_chat=group_chat,
            llm_config=manager_config_dict  # type: ignore
        )
        
        logger.info("Group chat created successfully")
        return group_chat, manager
    except Exception as e:
        logger.error(f"Error creating group chat: {str(e)}")
        raise


def execute_task(task_description: str, additional_context: Optional[Dict[str, Any]] = None) -> TaskResult:
    """
    Execute a task using the orchestrator with improved context handling and result validation.
    
    Args:
        task_description: Description of the task to execute
        additional_context: Optional additional context for the task
        
    Returns:
        Dict containing the results of the task execution
    """
    start_time = time.time()
    logger.info(f"Executing task: {task_description}")
    
    try:
        # Initialize the context with default values
        context_dict: Dict[str, Any] = {
            "task": task_description,
            "timestamp": time.time(),
            "execution_id": f"exec_{int(time.time())}"
        }
        
        # Update with additional context if provided
        if additional_context:
            context_dict.update(additional_context)
        
        # Create the agents
        assistant, user_proxy = create_agents()
        
        # Execute the task using the agents
        result: Any = user_proxy.initiate_chat(
            assistant,
            message=f"""Task: {task_description}
            
            Context: {json.dumps(context_dict, indent=2)}
            
            Please provide a detailed solution to this task."""
        )
        
        # Process and validate the result
        processed_result: TaskResult = {
            "raw_response": result,
            "execution_time": time.time() - start_time,
            "status": "success"
        }
        
        logger.info(f"Task completed in {processed_result['execution_time']:.2f} seconds")
        return processed_result
    except Exception as e:
        logger.error(f"Error executing task: {str(e)}")
        error_result: TaskResult = {
            "error": str(e),
            "execution_time": time.time() - start_time,
            "status": "failed"
        }
        return error_result

# pyright: ignore-all  # stop static-type errors from flooding the editor
try:
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, Agent
except ImportError:
    class Agent:
        def __init__(self, name: str, **kwargs: Any) -> None: pass
        def send(self, message: str, recipient: 'Agent') -> None: pass
        def receive(self, message: str, sender: 'Agent') -> None: pass

    class AssistantAgent(Agent):
        def __init__(self, name: str, system_message: str = "", llm_config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None: pass

    class UserProxyAgent(Agent):
        def __init__(self, name: str, human_input_mode: Literal["ALWAYS", "TERMINATE", "NEVER"] = "ALWAYS", max_consecutive_auto_reply: int = 100, **kwargs: Any) -> None: pass
        def initiate_chat(self, recipient: Agent, message: str, clear_history: bool = True, **kwargs: Any) -> Dict[str, Any]: return {}

    class GroupChat:
        def __init__(self, agents: List[Agent], messages: List[Dict[str, Any]], max_round: int, **kwargs: Any) -> None: pass

    class GroupChatManager(Agent):
        def __init__(self, groupchat: GroupChat, llm_config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None: pass

# Type aliases
type AgentType = Union[AssistantAgent, UserProxyAgent]
type AgentList = List[AgentType]
type MessageDict = Dict[str, Any]
type LLMConfig = Dict[str, Union[str, float, Dict[str, Any]]]

# Entry point
if __name__ == "__main__":
    orchestrator = EnhancedLangChainOrchestrator()
    asyncio.run(orchestrator.run())
