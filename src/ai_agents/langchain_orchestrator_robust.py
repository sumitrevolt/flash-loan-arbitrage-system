#!/usr/bin/env python3
"""
Robust LangChain Orchestrator with comprehensive error handling and dependency management
"""

import asyncio
import logging
import time
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import aiohttp

# Attempt a relative import first, then an absolute one if needed.
# This depends on how the project is structured and PYTHONPATH.
try:
    from .code_analyzer_agent import CodeAnalyzerAgent
except ImportError:
    from ai_agents.code_analyzer_agent import CodeAnalyzerAgent # Fallback if src is in PYTHONPATH

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/logs/orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RobustLangChainOrchestrator")

# Safe imports with fallbacks
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis not available - using in-memory storage")
    REDIS_AVAILABLE = False
    redis = None

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    logger.warning("PostgreSQL not available - using file storage")
    POSTGRES_AVAILABLE = False
    psycopg2 = None

try:
    from langchain.llms import OpenAI
    from langchain.agents import initialize_agent, AgentType
    from langchain.memory import ConversationBufferMemory
    from langchain.tools import Tool
    from langchain.schema import BaseMessage, HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
    logger.info("LangChain modules loaded successfully")
except ImportError as e:
    logger.warning(f"LangChain not fully available: {e} - using fallback implementation")
    LANGCHAIN_AVAILABLE = False

try:
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
    logger.info("AutoGen modules loaded successfully")
except ImportError as e:
    logger.warning(f"AutoGen not available: {e} - using LangChain only")
    AUTOGEN_AVAILABLE = False

try:
    import docker
    DOCKER_AVAILABLE = True
    docker_client = docker.from_env()
except ImportError:
    logger.warning("Docker client not available")
    DOCKER_AVAILABLE = False
    docker_client = None

# Environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://localhost:5432/flashloan')
LLM_CODE_SUGGESTION_MCP_URL = os.getenv("LLM_CODE_SUGGESTION_MCP_URL", "http://localhost:8022/call_tool")

@dataclass
class SystemState:
    """System state tracking"""
    total_agents: int = 0
    active_agents: int = 0
    mcp_servers: int = 21
    active_servers: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    uptime_start: datetime = field(default_factory=datetime.now)
    last_health_check: datetime = field(default_factory=datetime.now)
    errors: List[str] = field(default_factory=list)
    status: str = "initializing"

@dataclass
class MCPServerConfig:
    """MCP Server configuration"""
    name: str
    port: int
    status: str = "stopped"
    container_name: str = ""
    health_endpoint: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    last_log_timestamp: Optional[datetime] = None

@dataclass
class AgentConfig:
    """Agent configuration"""
    name: str
    role: str
    skills: List[str] = field(default_factory=list)
    status: str = "idle"
    container_name: str = ""
    last_activity: datetime = field(default_factory=datetime.now)

class RobustStorageManager:
    """Storage manager with multiple backends"""
    
    def __init__(self):
        self.redis_client = None
        self.storage_type = "memory"
        self.memory_store = {}
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                self.redis_client.ping()
                self.storage_type = "redis"
                logger.info("Connected to Redis storage")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory storage")
                self.storage_type = "memory"
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Set a value in storage"""
        try:
            if self.storage_type == "redis" and self.redis_client:
                self.redis_client.set(key, json.dumps(value), ex=expire)
            else:
                self.memory_store[key] = {
                    'value': value,
                    'timestamp': time.time(),
                    'expire': expire
                }
            return True
        except Exception as e:
            logger.error(f"Storage set error: {e}")
            return False
    
    async def get(self, key: str) -> Any:
        """Get a value from storage"""
        try:
            if self.storage_type == "redis" and self.redis_client:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            else:
                item = self.memory_store.get(key)
                if item:
                    if item.get('expire') and time.time() - item['timestamp'] > item['expire']:
                        del self.memory_store[key]
                        return None
                    return item['value']
                return None
        except Exception as e:
            logger.error(f"Storage get error: {e}")
            return None

class LangChainAgentManager:
    """LangChain-based agent management"""
    
    def __init__(self, storage: RobustStorageManager):
        self.storage = storage
        self.agents = {}
        self.llm = None
        self.tools = []
        
        if LANGCHAIN_AVAILABLE and OPENAI_API_KEY:
            try:
                self.llm = OpenAI(
                    temperature=0.7,
                    openai_api_key=OPENAI_API_KEY
                )
                self._setup_tools()
                logger.info("LangChain LLM initialized")
            except Exception as e:
                logger.error(f"LangChain LLM initialization failed: {e}")
    
    def _setup_tools(self):
        """Setup LangChain tools"""
        self.tools = [
            Tool(
                name="SystemStatus",
                description="Get current system status and metrics",
                func=self._get_system_status
            ),
            Tool(
                name="RestartService",
                description="Restart a failed service or container",
                func=self._restart_service
            ),
            Tool(
                name="HealthCheck",
                description="Perform health check on system components",
                func=self._health_check
            )
        ]
    
    def _get_system_status(self, query: str = "") -> str:
        """Get system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'agents': len(self.agents),
                'tools_available': len(self.tools),
                'langchain_status': LANGCHAIN_AVAILABLE,
                'autogen_status': AUTOGEN_AVAILABLE,
                'docker_status': DOCKER_AVAILABLE
            }
            return json.dumps(status, indent=2)
        except Exception as e:
            return f"Error getting system status: {e}"
    
    def _restart_service(self, service_name: str) -> str:
        """Restart a service"""
        try:
            if DOCKER_AVAILABLE and docker_client:
                container = docker_client.containers.get(service_name)
                container.restart()
                return f"Successfully restarted {service_name}"
            else:
                return f"Docker not available, cannot restart {service_name}"
        except Exception as e:
            return f"Failed to restart {service_name}: {e}"
    
    def _health_check(self, component: str = "all") -> str:
        """Perform health check"""
        results = {
            'redis': REDIS_AVAILABLE,
            'postgres': POSTGRES_AVAILABLE,
            'langchain': LANGCHAIN_AVAILABLE,
            'autogen': AUTOGEN_AVAILABLE,
            'docker': DOCKER_AVAILABLE
        }
        
        if component != "all":
            return f"{component}: {'OK' if results.get(component, False) else 'FAILED'}"
        
        return json.dumps(results, indent=2)
    
    async def create_agent(self, config: AgentConfig) -> bool:
        """Create a new agent"""
        try:
            if LANGCHAIN_AVAILABLE and self.llm:
                memory = ConversationBufferMemory(memory_key="chat_history")
                agent = initialize_agent(
                    self.tools,
                    self.llm,
                    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                    memory=memory,
                    verbose=True
                )
                
                self.agents[config.name] = {
                    'agent': agent,
                    'config': config,
                    'created_at': datetime.now(),
                    'status': 'active'
                }
                
                await self.storage.set(f"agent:{config.name}", config.__dict__)
                logger.info(f"Created LangChain agent: {config.name}")
                return True
            else:
                # Fallback: create simple agent stub
                self.agents[config.name] = {
                    'config': config,
                    'created_at': datetime.now(),
                    'status': 'active',
                    'type': 'fallback'
                }
                logger.info(f"Created fallback agent: {config.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create agent {config.name}: {e}")
            return False
    
    async def execute_task(self, agent_name: str, task: str) -> Dict[str, Any]:
        """Execute a task with an agent"""
        try:
            if agent_name not in self.agents:
                return {'status': 'error', 'message': f'Agent {agent_name} not found'}
            
            agent_data = self.agents[agent_name]
            
            if LANGCHAIN_AVAILABLE and 'agent' in agent_data:
                result = agent_data['agent'].run(task)
                return {
                    'status': 'success',
                    'result': result,
                    'agent': agent_name,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Fallback execution
                return {
                    'status': 'success',
                    'result': f"Fallback execution of task: {task}",
                    'agent': agent_name,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Task execution failed for {agent_name}: {e}")
            return {'status': 'error', 'message': str(e)}

class MCPServerManager:
    """MCP Server management"""
    
    def __init__(self, storage: RobustStorageManager):
        self.storage = storage
        self.servers = {}
        self._setup_default_servers()
    
    def _setup_default_servers(self):
        """Setup 21 default MCP servers"""
        server_configs = [
            MCPServerConfig("mcp-filesystem", 8001, health_endpoint="/health"),
            MCPServerConfig("mcp-database", 8002, health_endpoint="/health"),
            MCPServerConfig("mcp-web-scraper", 8003, health_endpoint="/health"),
            MCPServerConfig("mcp-api-client", 8004, health_endpoint="/health"),
            MCPServerConfig("mcp-file-processor", 8005, health_endpoint="/health"),
            MCPServerConfig("mcp-data-analyzer", 8006, health_endpoint="/health"),
            MCPServerConfig("mcp-notification", 8007, health_endpoint="/health"),
            MCPServerConfig("mcp-auth-manager", 8008, health_endpoint="/health"),
            MCPServerConfig("mcp-cache-manager", 8009, health_endpoint="/health"),
            MCPServerConfig("mcp-task-queue", 8010, health_endpoint="/health"),
            MCPServerConfig("mcp-monitoring", 8011, health_endpoint="/health"),
            MCPServerConfig("mcp-security", 8012, health_endpoint="/health"),
            MCPServerConfig("mcp-blockchain", 8013, health_endpoint="/health"),
            MCPServerConfig("mcp-defi-analyzer", 8014, health_endpoint="/health"),
            MCPServerConfig("mcp-price-feed", 8015, health_endpoint="/health"),
            MCPServerConfig("mcp-arbitrage", 8016, health_endpoint="/health"),
            MCPServerConfig("mcp-risk-manager", 8017, health_endpoint="/health"),
            MCPServerConfig("mcp-portfolio", 8018, health_endpoint="/health"),
            MCPServerConfig("mcp-liquidity", 8019, health_endpoint="/health"),
            MCPServerConfig("mcp-flash-loan", 8020, health_endpoint="/health"),
            MCPServerConfig("mcp-coordinator", 8021, health_endpoint="/health")
        ]
        
        for config in server_configs:
            self.servers[config.name] = config
            config.container_name = f"flashloan-{config.name.replace('_', '-')}-1"
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all MCP servers"""
        results = {}
        
        for name, config in self.servers.items():
            try:
                if DOCKER_AVAILABLE and docker_client:
                    container = docker_client.containers.get(config.container_name)
                    results[name] = container.status == 'running'
                    config.status = 'running' if results[name] else 'stopped'
                else:
                    # Fallback: assume healthy if no docker
                    results[name] = True
                    config.status = 'running'
                    
                config.last_check = datetime.now()
                await self.storage.set(f"server:{name}", config.__dict__)
                
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
                config.status = 'error'
        
        return results
    
    async def restart_server(self, server_name: str) -> bool:
        """Restart a specific MCP server"""
        try:
            if server_name not in self.servers:
                logger.error(f"Server {server_name} not found")
                return False
            
            config = self.servers[server_name]
            
            if DOCKER_AVAILABLE and docker_client:
                container = docker_client.containers.get(config.container_name)
                container.restart()
                config.status = 'restarting'
                logger.info(f"Restarted server: {server_name}")
                return True
            else:
                logger.warning(f"Docker not available, cannot restart {server_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restart server {server_name}: {e}")
            return False

class RobustLangChainOrchestrator:
    """Main orchestrator with comprehensive error handling"""
    
    def __init__(self):
        self.state = SystemState()
        self.storage = RobustStorageManager()
        self.agent_manager = LangChainAgentManager(self.storage)
        self.server_manager = MCPServerManager(self.storage)
        self.is_running = False
        self.tasks = asyncio.Queue()

        # Create an aiohttp session for the orchestrator and its agents
        try:
            self.aiohttp_session = aiohttp.ClientSession()
            logger.info("AIOHTTP client session initialized.")
            self.code_analyzer_agent = CodeAnalyzerAgent(session=self.aiohttp_session)
            logger.info("CodeAnalyzerAgent initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize aiohttp session or CodeAnalyzerAgent: {e}")
            self.aiohttp_session = None
            self.code_analyzer_agent = None
            # Depending on criticality, might want to raise an error or prevent startup
        
        logger.info("Robust LangChain Orchestrator initialized")
    
    async def run(self):
        """Main orchestration loop"""
        try:
            self.is_running = True
            self.state.status = "running"
            
            logger.info("🚀 Starting Robust LangChain Orchestrator")
            logger.info(f"📊 System capabilities:")
            logger.info(f"   - LangChain: {'✅' if LANGCHAIN_AVAILABLE else '❌'}")
            logger.info(f"   - AutoGen: {'✅' if AUTOGEN_AVAILABLE else '❌'}")
            logger.info(f"   - Redis: {'✅' if REDIS_AVAILABLE else '❌'}")
            logger.info(f"   - Docker: {'✅' if DOCKER_AVAILABLE else '❌'}")
            
            # Initialize system
            await self._initialize_system()
            
            # Start background tasks
            background_tasks = [
                asyncio.create_task(self._health_monitor()),
                asyncio.create_task(self._task_processor()),
                asyncio.create_task(self._agent_coordinator()),
                asyncio.create_task(self._server_monitor())
            ]
            
            # Run until interrupted
            await asyncio.gather(*background_tasks)
            
        except KeyboardInterrupt:
            logger.info("Orchestrator stopped by user.")
        except Exception as e:
            logger.error(f"Critical orchestrator error: {e}", exc_info=True)
            await self._handle_critical_error(e)
        finally:
            self.is_running = False
            self.state.status = "stopped"
            if hasattr(self, 'aiohttp_session') and self.aiohttp_session and not self.aiohttp_session.closed:
                await self.aiohttp_session.close()
                logger.info("AIOHTTP client session closed.")
            logger.info("Robust LangChain Orchestrator shutdown complete.") # Ensure this is the final log

    async def _call_mcp_tool(self, server_url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Helper method to call a tool on an MCP server via HTTP and parse JSON response."""
        if not hasattr(self, 'aiohttp_session') or not self.aiohttp_session or self.aiohttp_session.closed:
            logger.error(f"AIOHTTP session not available or closed. Cannot call MCP tool at {server_url}.")
            return None
        try:
            logger.debug(f"Calling MCP tool at {server_url} with payload: {json.dumps(payload)}")
            async with self.aiohttp_session.post(server_url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    data = await response.json() # Expecting JSON list from MCP server's call_tool handler
                    if isinstance(data, list) and len(data) > 0 and data[0].get("type") == "application/json" and "text" in data[0]:
                        tool_response_json_str = data[0]["text"]
                        try:
                            tool_response_dict = json.loads(tool_response_json_str)
                            logger.debug(f"Successfully called MCP tool at {server_url}. Response: {json.dumps(tool_response_dict)}")
                            return tool_response_dict
                        except json.JSONDecodeError as je:
                            logger.error(f"JSONDecodeError parsing tool response from {server_url}: {je}. Raw text: {tool_response_json_str}")
                            return {"status": "error", "message": f"Failed to parse tool JSON response: {tool_response_json_str}"}
                    else:
                        logger.error(f"Unexpected response structure from MCP tool at {server_url}. Data: {data}")
                        return {"status": "error", "message": f"Unexpected response structure: {data}"}
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status} calling MCP tool at {server_url}: {error_text}")
                    return {"status": "error", "message": f"HTTP error {response.status}: {error_text}"}
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error calling MCP tool at {server_url}: {e}")
            return {"status": "error", "message": f"Connection error: {e}"}
        except asyncio.TimeoutError: # Added asyncio.TimeoutError
            logger.error(f"Timeout calling MCP tool at {server_url}")
            return {"status": "error", "message": "Request timed out"}
        except Exception as e:
            logger.error(f"Exception calling MCP tool at {server_url}: {e}", exc_info=True)
            return {"status": "error", "message": f"Generic exception: {str(e)}"}
    
    async def _initialize_system(self):
        """Initialize all system components"""
        try:
            logger.info("🔧 Initializing system components...")
            
            # Create 10 agents
            agent_configs = [
                AgentConfig("coordinator", "system_coordinator", ["coordination", "monitoring"]),
                AgentConfig("analyzer", "market_analyzer", ["analysis", "defi"]),
                AgentConfig("executor", "trade_executor", ["execution", "blockchain"]),
                AgentConfig("risk_manager", "risk_assessment", ["risk", "security"]),
                AgentConfig("monitor", "system_monitor", ["monitoring", "alerts"]),
                AgentConfig("data_collector", "data_collection", ["data", "apis"]),
                AgentConfig("arbitrage_bot", "arbitrage_detection", ["arbitrage", "defi"]),
                AgentConfig("liquidity_manager", "liquidity_optimization", ["liquidity", "pools"]),
                AgentConfig("reporter", "report_generator", ["reporting", "analytics"]),
                AgentConfig("healer", "auto_healing", ["recovery", "maintenance"])
            ]
            
            for config in agent_configs:
                success = await self.agent_manager.create_agent(config)
                if success:
                    self.state.total_agents += 1
                    self.state.active_agents += 1
            
            # Check MCP servers
            server_health = await self.server_manager.health_check_all()
            self.state.active_servers = sum(1 for healthy in server_health.values() if healthy)
            
            logger.info(f"✅ System initialized:")
            logger.info(f"   - Agents: {self.state.active_agents}/{self.state.total_agents}")
            logger.info(f"   - MCP Servers: {self.state.active_servers}/{self.state.mcp_servers}")
            
            self.state.status = "initialized"
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            self.state.errors.append(f"Initialization error: {e}")
    
    async def _health_monitor(self):
        """Monitor system health"""
        while self.is_running:
            try:
                logger.info("🏥 Performing health checks...")
                
                # Check MCP servers
                server_health = await self.server_manager.health_check_all()
                healthy_servers = sum(1 for healthy in server_health.values() if healthy)
                
                # Update state
                self.state.active_servers = healthy_servers
                self.state.last_health_check = datetime.now()
                
                # Log status
                logger.info(f"📊 Health Status: {healthy_servers}/{self.state.mcp_servers} servers healthy")
                
                # Auto-heal if needed
                failed_servers = [name for name, healthy in server_health.items() if not healthy]
                if failed_servers:
                    logger.warning(f"⚠️ Failed servers detected: {failed_servers}")
                    await self._auto_heal_servers(failed_servers)
                
                # Store health data
                await self.storage.set("system_health", {
                    'timestamp': datetime.now().isoformat(),
                    'servers': server_health,
                    'agents': self.state.active_agents,
                    'status': self.state.status
                })
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _task_processor(self):
        """Process tasks from the queue"""
        while self.is_running:
            try:
                # Get task from queue (wait up to 10 seconds)
                try:
                    task = await asyncio.wait_for(self.tasks.get(), timeout=10.0)
                except asyncio.TimeoutError:
                    continue
                
                task_type = task.get('task_type')
                logger.info(f"🎯 Processing task: {task.get('name', task_type)}")

                if task_type == "CODE_ERROR_REPORT":
                    service_name = task.get('service_name', 'Unknown service')
                    logger.info(f"Processing CODE_ERROR_REPORT for service: {service_name}")
                    try:
                        if hasattr(self, 'code_analyzer_agent') and self.code_analyzer_agent:
                            analysis_result = await self.code_analyzer_agent.analyze_code_from_report(task)
                            logger.info(f"Code analysis for {service_name}:\n{json.dumps(analysis_result, indent=2)}")

                            # LLM Suggestion Step
                            if analysis_result and analysis_result.get("file_access_status") == "success":
                                code_snippet_for_llm = analysis_result.get("file_content_preview", "")
                                # Consider using full content if available and not too large:
                                # if 'full_content' in analysis_result: code_snippet_for_llm = analysis_result['full_content']

                                error_messages_for_llm = []
                                original_error_msg = task.get("error_details", {}).get("message", "")
                                if original_error_msg:
                                    error_messages_for_llm.append(f"Original error: {original_error_msg}")

                                linting_issues = analysis_result.get("linting_results", [])
                                if linting_issues:
                                    error_messages_for_llm.append("Linting issues found:\n" + "\n".join(linting_issues[:5]))

                                combined_error_message = "\n".join(error_messages_for_llm) if error_messages_for_llm else "No specific error message captured."

                                # Proceed if there's either a code snippet or a specific error message (not just the generic one)
                                if code_snippet_for_llm or (combined_error_message and combined_error_message != "No specific error message captured."):
                                    llm_tool_payload = {
                                        "tool_name": "get_llm_code_suggestion",
                                        "arguments": {
                                            "code_snippet": code_snippet_for_llm,
                                            "error_message": combined_error_message,
                                            "language": "python", # Assuming Python
                                            "context": f"Error occurred in service '{service_name}'. Path: '{analysis_result.get('analyzed_file_path', 'N/A')}'. Log snippet (first 500 chars): {task.get('log_snippet', '')[:500]}"
                                        }
                                    }
                                    logger.info(f"Requesting LLM code suggestion for {service_name} from {LLM_CODE_SUGGESTION_MCP_URL}")
                                    llm_suggestion_response = await self._call_mcp_tool(LLM_CODE_SUGGESTION_MCP_URL, llm_tool_payload)

                                    if llm_suggestion_response:
                                        logger.info(f"LLM Code Suggestion raw response for {service_name}:\n{json.dumps(llm_suggestion_response, indent=2)}")
                                        analysis_result["llm_suggestion_response"] = llm_suggestion_response
                                    else:
                                        logger.warning(f"Failed to get LLM suggestion or received empty response for {service_name}.")
                                        analysis_result["llm_suggestion_response"] = {"status": "error", "message": "No response or empty response from LLM server."}
                                else:
                                    logger.info(f"Skipping LLM suggestion for {service_name} due to insufficient information (no code snippet and no specific error message).")
                                    analysis_result["llm_suggestion_response"] = {"status": "skipped", "message": "Insufficient information for LLM."}
                            else:
                                logger.info(f"Skipping LLM suggestion for {service_name} as code analysis was not successful or file not accessed.")
                                if analysis_result: # Ensure analysis_result exists before trying to update it
                                   analysis_result["llm_suggestion_response"] = {"status": "skipped", "message": "Code analysis failed or file not accessed."}

                            # Log final combined analysis result if desired, or rely on individual logs
                            # logger.info(f"Final analysis with LLM attempt for {service_name}:\n{json.dumps(analysis_result, indent=2)}")
                            self.state.tasks_completed += 1
                        else:
                            logger.error("CodeAnalyzerAgent not initialized. Cannot process CODE_ERROR_REPORT.")
                            self.state.tasks_failed += 1
                    except Exception as e:
                        logger.error(f"Error during code analysis or LLM suggestion for {service_name}: {e}", exc_info=True)
                        self.state.tasks_failed += 1
                
                # Existing task processing logic (example: agent tasks)
                # This part needs to be adjusted if 'name' was the primary way to route tasks
                # For now, assuming other tasks might still use 'name' or a different task_type
                elif 'name' in task: # Keep compatibility with previous sample tasks
                    agent_name = self._select_agent_for_task(task)
                    if agent_name:
                        # Execute task
                        result = await self.agent_manager.execute_task(agent_name, task.get('description', ''))

                        if result['status'] == 'success':
                            self.state.tasks_completed += 1
                            logger.info(f"✅ Task '{task.get('name')}' completed by {agent_name}")
                        else:
                            self.state.tasks_failed += 1
                            logger.error(f"❌ Task '{task.get('name')}' failed: {result.get('message', 'Unknown error')}")
                    else:
                        logger.warning(f"⚠️ No suitable agent found for task '{task.get('name')}'")
                        self.state.tasks_failed += 1
                else:
                    logger.warning(f"Unknown task structure or type: {task}")
                    self.state.tasks_failed += 1
                
            except Exception as e:
                logger.error(f"Task processor error: {e}")
                self.state.tasks_failed += 1
                await asyncio.sleep(5)
    
    async def _agent_coordinator(self):
        """Coordinate agents and their activities"""
        while self.is_running:
            try:
                logger.info("🤝 Coordinating agents...")
                
                # Add some sample tasks to keep agents busy
                sample_tasks = [
                    {
                        'name': 'system_health_check',
                        'description': 'Perform a comprehensive system health check',
                        'priority': 'high'
                    },
                    {
                        'name': 'market_analysis',
                        'description': 'Analyze current DeFi market conditions for arbitrage opportunities',
                        'priority': 'medium'
                    },
                    {
                        'name': 'risk_assessment',
                        'description': 'Assess current system risk levels and recommend adjustments',
                        'priority': 'high'
                    }
                ]
                
                for task in sample_tasks:
                    await self.tasks.put(task)
                
                await asyncio.sleep(300)  # Coordinate every 5 minutes
                
            except Exception as e:
                logger.error(f"Agent coordinator error: {e}")
                await asyncio.sleep(60)

    async def _scan_logs_for_code_errors(self, logs_string: str) -> Optional[List[Dict[str, Any]]]:
        """Scan log string for Python code errors."""
        # Basic pattern for Python tracebacks, can be refined
        # Looking for common errors like SyntaxError, ImportError, NameError
        pattern = re.compile(
            r"Traceback \(most recent call last\):\n"  # Start of a traceback
            r"(?:  File \".*?\", line \d+, in .*?\n    .*?\n)*"  # Stack frames
            r"(?P<error_type>SyntaxError|ImportError|NameError|TypeError|ValueError|AttributeError|KeyError|IndexError|FileNotFoundError|ZeroDivisionError): (?P<error_message>.+?)\n" # Error line
            r"(?:(?!(Traceback \(most recent call last\):|^\s*$)).*\n)*", # Capture lines after error until next traceback or blank lines (for snippet)
            re.MULTILINE
        )

        found_errors = []

        for match in pattern.finditer(logs_string):
            error_type = match.group("error_type")
            error_message = match.group("error_message").strip()

            # Try to capture a snippet of the traceback
            # The match object itself gives the full traceback for this specific error
            traceback_snippet = match.group(0)

            # Basic file path and line number extraction (can be very complex)
            # This is a simplified attempt, real tracebacks can be tricky
            file_path_match = re.search(r'File "(?P<file_path>.*?)"', traceback_snippet)
            line_number_match = re.search(r'line (?P<line_number>\d+)', traceback_snippet)

            file_path = file_path_match.group("file_path") if file_path_match else "Unknown"
            line_number = int(line_number_match.group("line_number")) if line_number_match else "Unknown"

            error_details = {
                'type': error_type,
                'message': error_message,
                'file_path': file_path,
                'line_number': line_number,
            }
            found_errors.append({'details': error_details, 'snippet': traceback_snippet})

        return found_errors if found_errors else None

    async def _report_code_error(self, server_config: MCPServerConfig, error_details: Dict, log_snippet: str):
        """Report a detected code error by putting a task on the queue."""
        task_payload = {
            "task_type": "CODE_ERROR_REPORT",
            "service_name": server_config.name,
            "container_id": server_config.container_name,
            "timestamp": datetime.now().isoformat(),
            "error_details": error_details,
            "log_snippet": log_snippet  # Full traceback snippet
        }
        await self.tasks.put(task_payload)
        logger.info(f"Reported code error for {server_config.name}: {error_details.get('type')} - {error_details.get('message')}")

    async def _server_monitor(self):
        """Monitor MCP servers specifically"""
        while self.is_running:
            try:
                logger.info("🖥️ Monitoring MCP servers...")
                
                for server_name, config in self.server_manager.servers.items():
                    if config.status == 'error':
                        logger.warning(f"⚠️ Server {server_name} in error state, attempting restart...")
                        await self.server_manager.restart_server(server_name)

                    # Log fetching and error scanning
                    if DOCKER_AVAILABLE and docker_client and config.container_name:
                        try:
                            container = docker_client.containers.get(config.container_name)
                            if container.status == 'running':
                                # Fetch last 50 log lines (no timestamps for simplicity first)
                                logs_string = container.logs(tail=50, timestamps=False).decode('utf-8', errors='ignore')
                                config.last_log_timestamp = datetime.now() # Update after fetching

                                found_errors = await self._scan_logs_for_code_errors(logs_string)
                                if found_errors:
                                    logger.info(f"Found {len(found_errors)} potential code error(s) in logs for {config.name}.")
                                    for error_data in found_errors:
                                        await self._report_code_error(config, error_data['details'], error_data['snippet'])
                                elif logs_string.strip(): # Only log if there were logs but no errors
                                    logger.info(f"No code errors found in recent logs for {config.name}.")


                        except docker.errors.NotFound:
                            logger.warning(f"Container {config.container_name} not found for log fetching.")
                        except docker.errors.APIError as e:
                            logger.error(f"Docker API error when fetching logs for {config.container_name}: {e}")
                        except Exception as e:
                            logger.error(f"Unexpected error fetching logs for {config.container_name}: {e}")
                
                await asyncio.sleep(120)  # Monitor every 2 minutes
                
            except Exception as e:
                logger.error(f"Server monitor error: {e}")
                await asyncio.sleep(60)
    
    def _select_agent_for_task(self, task: Dict[str, Any]) -> Optional[str]:
        """Select the best agent for a task"""
        task_type = task.get('name', '').lower()
        
        # Simple task routing logic
        if 'health' in task_type or 'monitor' in task_type:
            return 'monitor'
        elif 'market' in task_type or 'analysis' in task_type:
            return 'analyzer'
        elif 'risk' in task_type:
            return 'risk_manager'
        elif 'execute' in task_type or 'trade' in task_type:
            return 'executor'
        else:
            return 'coordinator'  # Default to coordinator
    
    async def _auto_heal_servers(self, failed_servers: List[str]):
        """Attempt to heal failed servers"""
        for server_name in failed_servers:
            try:
                logger.info(f"🔧 Attempting to heal server: {server_name}")
                success = await self.server_manager.restart_server(server_name)
                
                if success:
                    logger.info(f"✅ Successfully healed server: {server_name}")
                else:
                    logger.error(f"❌ Failed to heal server: {server_name}")
                    
            except Exception as e:
                logger.error(f"Auto-heal error for {server_name}: {e}")
    
    async def _handle_critical_error(self, error: Exception):
        """Handle critical system errors"""
        logger.error(f"🚨 Critical error: {error}")
        
        self.state.errors.append(f"Critical: {error}")
        self.state.status = "error"
        
        # Try to save state before shutdown
        try:
            await self.storage.set("last_error", {
                'error': str(error),
                'timestamp': datetime.now().isoformat(),
                'state': self.state.__dict__
            })
        except Exception as e:
            logger.error(f"Failed to save error state: {e}")

# Health check endpoint for Docker
async def health_check():
    """Simple health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'langchain': LANGCHAIN_AVAILABLE,
            'autogen': AUTOGEN_AVAILABLE,
            'redis': REDIS_AVAILABLE,
            'docker': DOCKER_AVAILABLE
        }
    }

if __name__ == "__main__":
    # Create logs directory
    os.makedirs("/app/logs", exist_ok=True)
    
    # Start the orchestrator
    orchestrator = RobustLangChainOrchestrator()
    
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        logger.info("Orchestrator shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Orchestrator shutdown complete")
