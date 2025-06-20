#!/usr/bin/env python3
"""
AI Agents Master Coordinator
============================

Coordinates all AI agents in the flash loan arbitrage system with:
- Multi-agent task distribution
- LangChain integration for intelligent coordination
- Real-time communication between agents
- Performance monitoring and optimization
- Integration with MCP servers

Author: GitHub Copilot Assistant
Date: June 17, 2025
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
import aiohttp
from queue import Queue, Empty

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# LangChain imports (with fallback)
try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import initialize_agent, AgentType, Tool
    from langchain.memory import ConversationBufferMemory
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.schema import AgentAction, AgentFinish
    langchain_available = True
except ImportError:
    logger.warning("LangChain not available, using basic coordination")
    langchain_available = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent status enumeration"""
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

@dataclass
class AgentConfig:
    """Configuration for an AI agent"""
    name: str
    role: str
    capabilities: List[str]
    port: int
    file_path: str
    max_concurrent_tasks: int = 3
    specializations: List[str] = field(default_factory=list)
    performance_weight: float = 1.0
    availability_schedule: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Task:
    """Task definition"""
    id: str
    type: str
    description: str
    data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    timeout: int = 300  # 5 minutes default

@dataclass
class AgentInstance:
    """Running agent instance"""
    config: AgentConfig
    status: AgentStatus = AgentStatus.INACTIVE
    current_tasks: List[str] = field(default_factory=list)
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_activity: Optional[datetime] = None
    performance_score: float = 1.0
    response_time_avg: float = 0.0
    health_check_url: Optional[str] = None

class AIAgentsMasterCoordinator:
    """Master coordinator for all AI agents"""
    
    def __init__(self, config_path: str = "config/ai_agents_config.json"):
        self.config_path = Path(config_path)
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.task_queue: Queue = Queue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=20)
        
        # LangChain components
        self.llm = None
        self.coordination_agent = None
        self.task_analyzer = None
        
        # Performance tracking
        self.performance_metrics = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "average_response_time": 0.0,
            "system_efficiency": 1.0
        }
        
        # Load configuration
        self._load_configuration()
          # Initialize LangChain if available
        if langchain_available:
            self._initialize_langchain()
    
    def _load_configuration(self):
        """Load AI agents configuration"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Configuration file not found: {self.config_path}")
                self._create_default_configuration()
                return
            
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            # Load agent configurations
            agents_config = config_data.get('agents', {})
            for agent_name, agent_data in agents_config.items():
                try:
                    config = AgentConfig(
                        name=agent_data['name'],
                        role=agent_data.get('role', 'general'),
                        capabilities=agent_data.get('capabilities', []),
                        port=agent_data['port'],
                        file_path=agent_data['file'],
                        max_concurrent_tasks=agent_data.get('max_concurrent_tasks', 3),
                        specializations=agent_data.get('specializations', []),
                        performance_weight=agent_data.get('performance_weight', 1.0)
                    )
                    
                    self.agent_configs[agent_name] = config
                    self.agents[agent_name] = AgentInstance(
                        config=config,
                        health_check_url=f"http://localhost:{config.port}/health"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to load config for agent {agent_name}: {e}")
            
            logger.info(f"Loaded configuration for {len(self.agent_configs)} AI agents")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """Create default AI agents configuration"""
        logger.info("Creating default AI agents configuration...")
        
        default_config = {
            "coordination": {
                "master_coordinator": "src/ai_agents/master_coordinator.py",
                "communication_protocol": "http",
                "task_distribution": "intelligent",
                "load_balancing": True
            },
            "agents": {
                "arbitrage_analyzer": {
                    "name": "Arbitrage Analyzer",
                    "role": "analysis",
                    "capabilities": ["arbitrage_detection", "market_analysis", "profit_calculation"],
                    "specializations": ["defi_protocols", "price_comparison"],
                    "port": 5001,
                    "file": "src/ai_agents/arbitrage_analyzer.py",
                    "max_concurrent_tasks": 5,
                    "performance_weight": 1.2
                },
                "risk_assessor": {
                    "name": "Risk Assessor",
                    "role": "risk_management",
                    "capabilities": ["risk_analysis", "portfolio_assessment", "compliance_check"],
                    "specializations": ["smart_contract_risks", "market_volatility"],
                    "port": 5002,
                    "file": "src/ai_agents/risk_assessor.py",
                    "max_concurrent_tasks": 3,
                    "performance_weight": 1.5
                },
                "execution_coordinator": {
                    "name": "Execution Coordinator",
                    "role": "execution",
                    "capabilities": ["trade_execution", "transaction_monitoring", "order_management"],
                    "specializations": ["flash_loans", "dex_routing"],
                    "port": 5003,
                    "file": "src/ai_agents/execution_coordinator.py",
                    "max_concurrent_tasks": 2,
                    "performance_weight": 2.0
                },
                "market_monitor": {
                    "name": "Market Monitor",
                    "role": "monitoring",
                    "capabilities": ["price_monitoring", "liquidity_tracking", "alert_management"],
                    "specializations": ["real_time_data", "trend_analysis"],
                    "port": 5004,
                    "file": "src/ai_agents/market_monitor.py",
                    "max_concurrent_tasks": 10,
                    "performance_weight": 0.8
                },
                "strategy_planner": {
                    "name": "Strategy Planner",
                    "role": "planning",
                    "capabilities": ["strategy_development", "optimization", "scenario_analysis"],
                    "specializations": ["multi_step_arbitrage", "capital_allocation"],
                    "port": 5005,
                    "file": "src/ai_agents/strategy_planner.py",
                    "max_concurrent_tasks": 2,
                    "performance_weight": 1.3
                }
            }
        }
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Default configuration saved to {self.config_path}")
        
        # Create agent scripts
        self._create_agent_scripts(default_config['agents'])
        
        # Load the default configuration
        self._load_configuration()
    
    def _create_agent_scripts(self, agents_config: Dict[str, Any]):
        """Create basic agent scripts if they don't exist"""
        for agent_name, agent_data in agents_config.items():
            script_path = Path(agent_data['file'])
            
            if not script_path.exists():
                script_path.parent.mkdir(parents=True, exist_ok=True)
                
                template = f'''#!/usr/bin/env python3
"""
{agent_data['name']} AI Agent
Role: {agent_data['role']}
Port: {agent_data['port']}
"""

import os
import json
import time
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Agent configuration
AGENT_NAME = "{agent_data['name']}"
AGENT_PORT = {agent_data['port']}
AGENT_ROLE = "{agent_data['role']}"
CAPABILITIES = {json.dumps(agent_data['capabilities'])}

# Agent state
agent_status = {{
    "agent": AGENT_NAME,
    "port": AGENT_PORT,
    "role": AGENT_ROLE,
    "status": "healthy",
    "timestamp": datetime.now().isoformat(),
    "tasks_completed": 0,
    "active_tasks": 0,
    "capabilities": CAPABILITIES
}}

start_time = time.time()
tasks_completed = 0
active_tasks = 0

def update_agent_status():
    """Update agent status"""
    global agent_status
    agent_status["timestamp"] = datetime.now().isoformat()
    agent_status["tasks_completed"] = tasks_completed
    agent_status["active_tasks"] = active_tasks
    agent_status["uptime"] = int(time.time() - start_time)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    update_agent_status()
    return jsonify(agent_status)

@app.route('/status', methods=['GET'])
def status():
    """Detailed status endpoint"""
    update_agent_status()
    return jsonify({{
        **agent_status,
        "capabilities": CAPABILITIES,
        "performance": {{
            "success_rate": 0.95,
            "average_response_time": 1.2,
            "load": active_tasks / {agent_data.get('max_concurrent_tasks', 3)}
        }}
    }})

@app.route('/task', methods=['POST'])
def handle_task():
    """Handle incoming task"""
    global active_tasks, tasks_completed
    
    try:
        task_data = request.get_json()
        task_id = task_data.get('id', 'unknown')
        task_type = task_data.get('type', 'unknown')
        
        logger.info(f"Received task {{task_id}}: {{task_type}}")
        
        active_tasks += 1
        
        # Simulate task processing
        time.sleep(1)
        
        # Mock response based on agent role
        result = process_task(task_data)
        
        active_tasks -= 1
        tasks_completed += 1
        
        return jsonify({{
            "status": "completed",
            "task_id": task_id,
            "result": result,
            "agent": AGENT_NAME
        }})
        
    except Exception as e:
        active_tasks = max(0, active_tasks - 1)
        logger.error(f"Task processing error: {{e}}")
        return jsonify({{
            "status": "error",
            "error": str(e),
            "agent": AGENT_NAME
        }}), 500

def process_task(task_data):
    """Process task based on agent capabilities"""
    task_type = task_data.get('type', '')
    
    if AGENT_ROLE == 'analysis' and 'arbitrage' in task_type:
        return {{
            "opportunities_found": 3,
            "estimated_profit": 0.05,
            "confidence": 0.85,
            "analysis_time": 1.2
        }}
    elif AGENT_ROLE == 'risk_management':
        return {{
            "risk_score": 0.3,
            "max_position_size": 1000,
            "recommendations": ["limit_exposure", "diversify_trades"],
            "compliance_status": "approved"
        }}
    elif AGENT_ROLE == 'execution':
        return {{
            "execution_plan": ["approve_tokens", "execute_flash_loan", "swap_tokens"],
            "estimated_gas": 350000,
            "execution_time": 15,
            "status": "ready"
        }}
    elif AGENT_ROLE == 'monitoring':
        return {{
            "price_updates": 25,
            "liquidity_changes": 3,
            "alerts_generated": 1,
            "monitoring_active": True
        }}
    else:
        return {{
            "processed": True,
            "result": "task_completed",
            "agent_role": AGENT_ROLE
        }}

def main():
    """Main agent function"""
    logger.info(f"Starting {{AGENT_NAME}} on port {{AGENT_PORT}}")
    app.run(host='localhost', port=AGENT_PORT, debug=False)

if __name__ == "__main__":
    main()
'''
                
                with open(script_path, 'w') as f:
                    f.write(template)
                
                logger.info(f"Created agent script: {script_path}")
    
    def _initialize_langchain(self):
        """Initialize LangChain components for intelligent coordination"""
        try:
            # Initialize LLM
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('GITHUB_TOKEN')
            if api_key:
                self.llm = ChatOpenAI(
                    api_key=api_key,
                    model="gpt-3.5-turbo",
                    temperature=0.7
                )
                
                # Create coordination tools
                coordination_tools = self._create_coordination_tools()
                
                # Initialize coordination agent
                self.coordination_agent = initialize_agent(
                    coordination_tools,
                    self.llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True),
                    verbose=True
                )
                
                logger.info("✅ LangChain coordination agent initialized")
            else:
                logger.warning("No API key found, using basic coordination")
                
        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {e}")
    
    def _create_coordination_tools(self) -> List[Tool]:
        """Create tools for the coordination agent"""
        tools = [
            Tool(
                name="assign_task",
                description="Assign a task to the most suitable agent",
                func=self._tool_assign_task
            ),
            Tool(
                name="get_agent_status",
                description="Get current status of all agents",
                func=self._tool_get_agent_status
            ),
            Tool(
                name="analyze_performance",
                description="Analyze system performance and suggest optimizations",
                func=self._tool_analyze_performance
            ),
            Tool(
                name="balance_load",
                description="Balance task load across agents",
                func=self._tool_balance_load
            )
        ]
        return tools
    
    def _tool_assign_task(self, task_description: str) -> str:
        """Tool to assign tasks intelligently"""
        # Analyze task requirements and assign to best agent
        best_agent = self._select_best_agent_for_task(task_description)
        return f"Task assigned to {best_agent}"
    
    def _tool_get_agent_status(self, query: str) -> str:
        """Tool to get agent status"""
        status_summary = []
        for agent_name, agent in self.agents.items():
            status_summary.append(f"{agent_name}: {agent.status.value} ({len(agent.current_tasks)} tasks)")
        return "\\n".join(status_summary)
    
    def _tool_analyze_performance(self, query: str) -> str:
        """Tool to analyze system performance"""
        total_tasks = self.performance_metrics["tasks_processed"]
        failed_tasks = self.performance_metrics["tasks_failed"]
        success_rate = (total_tasks - failed_tasks) / max(total_tasks, 1) * 100
        
        return f"Performance: {success_rate:.1f}% success rate, {total_tasks} tasks processed"
    
    def _tool_balance_load(self, query: str) -> str:
        """Tool to balance load across agents"""
        # Simple load balancing logic
        agent_loads = {name: len(agent.current_tasks) for name, agent in self.agents.items()}
        avg_load = sum(agent_loads.values()) / len(agent_loads) if agent_loads else 0
        
        overloaded = [name for name, load in agent_loads.items() if load > avg_load + 2]
        underloaded = [name for name, load in agent_loads.items() if load < avg_load - 1]
        
        return f"Load analysis: {len(overloaded)} overloaded, {len(underloaded)} underloaded agents"
    
    async def start_all_agents(self):
        """Start all AI agents"""
        logger.info("🤖 Starting AI agents coordination system...")
        
        self.running = True
        
        # Start agent monitoring
        asyncio.create_task(self._monitor_agents())
        
        # Start task processing
        asyncio.create_task(self._process_task_queue())
        
        # Start performance monitoring
        asyncio.create_task(self._monitor_performance())
        
        logger.info("✅ AI agents coordination system active")
    
    async def _monitor_agents(self):
        """Monitor agent health and status"""
        while self.running:
            try:
                for agent_name, agent in self.agents.items():
                    await self._check_agent_health(agent_name)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Agent monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _check_agent_health(self, agent_name: str):
        """Check health of a specific agent"""
        agent = self.agents[agent_name]
        
        if not agent.health_check_url:
            return
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(agent.health_check_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        agent.status = AgentStatus.ACTIVE
                        agent.last_activity = datetime.now()
                        
                        # Update performance metrics
                        if 'tasks_completed' in data:
                            agent.completed_tasks = data['tasks_completed']
                        
                        logger.debug(f"✅ Agent {agent_name} health check passed")
                    else:
                        logger.warning(f"⚠️  Agent {agent_name} health check failed: HTTP {response.status}")
                        agent.status = AgentStatus.ERROR
                        
        except Exception as e:
            logger.warning(f"⚠️  Agent {agent_name} health check failed: {e}")
            agent.status = AgentStatus.ERROR
    
    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while self.running:
            try:
                # Check for pending tasks
                if not self.task_queue.empty():
                    try:
                        task = self.task_queue.get_nowait()
                        await self._assign_and_execute_task(task)
                    except Empty:
                        pass
                
                # Check for completed tasks
                await self._check_task_completion()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Task processing error: {e}")
                await asyncio.sleep(5)
    
    async def _assign_and_execute_task(self, task: Task):
        """Assign and execute a task"""
        try:
            # Select best agent for the task
            best_agent_name = self._select_best_agent_for_task(task.description, task.type)
            
            if not best_agent_name:
                logger.error(f"No suitable agent found for task {task.id}")
                task.status = TaskStatus.FAILED
                task.error_message = "No suitable agent available"
                return
            
            agent = self.agents[best_agent_name]
            
            # Check if agent can handle more tasks
            if len(agent.current_tasks) >= agent.config.max_concurrent_tasks:
                # Put task back in queue
                self.task_queue.put(task)
                return
            
            # Assign task
            task.assigned_to = best_agent_name
            task.status = TaskStatus.ASSIGNED
            agent.current_tasks.append(task.id)
            self.active_tasks[task.id] = task
            
            logger.info(f"📋 Assigned task {task.id} to {best_agent_name}")
            
            # Execute task
            await self._execute_task_on_agent(task, agent)
            
        except Exception as e:
            logger.error(f"Task assignment error: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
    
    def _select_best_agent_for_task(self, task_description: str, task_type: str = "") -> Optional[str]:
        """Select the best agent for a task using intelligent matching"""
        
        # If LangChain is available, use AI for selection
        if self.coordination_agent:
            try:
                prompt = f"Select the best agent for this task: {task_description} (type: {task_type})"
                response = self.coordination_agent.run(prompt)
                
                # Extract agent name from response
                for agent_name in self.agents.keys():
                    if agent_name in response.lower():
                        return agent_name
            except Exception as e:
                logger.warning(f"AI agent selection failed: {e}")
        
        # Fallback to rule-based selection
        candidates = []
        
        for agent_name, agent in self.agents.items():
            if agent.status != AgentStatus.ACTIVE:
                continue
            
            if len(agent.current_tasks) >= agent.config.max_concurrent_tasks:
                continue
            
            # Score based on capabilities
            score = 0
            
            # Check capabilities match
            for capability in agent.config.capabilities:
                if capability.lower() in task_description.lower() or capability.lower() in task_type.lower():
                    score += 10
            
            # Check specializations
            for specialization in agent.config.specializations:
                if specialization.lower() in task_description.lower():
                    score += 5
            
            # Consider performance weight
            score *= agent.config.performance_weight
            
            # Consider current load
            load_factor = 1 - (len(agent.current_tasks) / agent.config.max_concurrent_tasks)
            score *= load_factor
            
            if score > 0:
                candidates.append((score, agent_name))
        
        if candidates:
            # Return agent with highest score
            candidates.sort(reverse=True)
            return candidates[0][1]
        
        return None
    
    async def _execute_task_on_agent(self, task: Task, agent: AgentInstance):
        """Execute task on specific agent"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            
            # Prepare task data
            task_payload = {
                "id": task.id,
                "type": task.type,
                "description": task.description,
                "data": task.data,
                "priority": task.priority.value
            }
            
            # Send task to agent
            url = f"http://localhost:{agent.config.port}/task"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=task_payload, timeout=task.timeout) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        
                        task.result = result_data.get('result', {})
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now()
                        
                        logger.info(f"✅ Task {task.id} completed by {agent.config.name}")
                        
                        # Update agent statistics
                        agent.completed_tasks += 1
                        
                    else:
                        error_msg = f"Agent returned HTTP {response.status}"
                        task.status = TaskStatus.FAILED
                        task.error_message = error_msg
                        agent.failed_tasks += 1
                        
                        logger.error(f"❌ Task {task.id} failed: {error_msg}")
        
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error_message = "Task timeout"
            agent.failed_tasks += 1
            logger.error(f"❌ Task {task.id} timed out")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            agent.failed_tasks += 1
            logger.error(f"❌ Task {task.id} execution error: {e}")
        
        finally:
            # Remove task from agent's current tasks
            if task.id in agent.current_tasks:
                agent.current_tasks.remove(task.id)
            
            # Move to completed tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
                self.completed_tasks[task.id] = task
    
    async def _check_task_completion(self):
        """Check and clean up completed tasks"""
        # Clean up old completed tasks (keep last 1000)
        if len(self.completed_tasks) > 1000:
            oldest_tasks = sorted(
                self.completed_tasks.items(),
                key=lambda x: x[1].completed_at or datetime.min
            )[:100]
            
            for task_id, _ in oldest_tasks:
                del self.completed_tasks[task_id]
    
    async def _monitor_performance(self):
        """Monitor system performance"""
        while self.running:
            try:
                # Update performance metrics
                total_completed = sum(agent.completed_tasks for agent in self.agents.values())
                total_failed = sum(agent.failed_tasks for agent in self.agents.values())
                
                self.performance_metrics["tasks_processed"] = total_completed
                self.performance_metrics["tasks_failed"] = total_failed
                
                if total_completed > 0:
                    success_rate = (total_completed - total_failed) / total_completed
                    self.performance_metrics["system_efficiency"] = success_rate
                
                # Log performance summary every 5 minutes
                logger.info(f"📊 Performance: {total_completed} tasks completed, "
                           f"{total_failed} failed, {len(self.active_tasks)} active")
                
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)
    
    def submit_task(self, task_type: str, description: str, data: Dict[str, Any] = None, 
                   priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Submit a new task to the system"""
        task_id = f"task_{int(time.time())}_{len(self.active_tasks)}"
        
        task = Task(
            id=task_id,
            type=task_type,
            description=description,
            data=data or {},
            priority=priority
        )
        
        self.task_queue.put(task)
        logger.info(f"📝 Submitted task {task_id}: {description}")
        
        return task_id
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "coordinator": {
                "running": self.running,
                "total_agents": len(self.agents),
                "active_agents": sum(1 for agent in self.agents.values() if agent.status == AgentStatus.ACTIVE),
                "langchain_enabled": langchain_available and self.coordination_agent is not None
            },
            "agents": {
                name: {
                    "name": agent.config.name,
                    "role": agent.config.role,
                    "status": agent.status.value,
                    "port": agent.config.port,
                    "current_tasks": len(agent.current_tasks),
                    "completed_tasks": agent.completed_tasks,
                    "failed_tasks": agent.failed_tasks,
                    "performance_score": agent.performance_score,
                    "capabilities": agent.config.capabilities
                }
                for name, agent in self.agents.items()
            },
            "tasks": {
                "queue_size": self.task_queue.qsize(),
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks)
            },
            "performance": self.performance_metrics
        }
    
    async def stop_all_agents(self):
        """Stop the coordination system"""
        logger.info("🛑 Stopping AI agents coordination system...")
        
        self.running = False
        
        # Wait for current tasks to complete
        timeout = 30
        start_time = time.time()
        
        while self.active_tasks and (time.time() - start_time) < timeout:
            await asyncio.sleep(1)
        
        # Cancel remaining tasks
        for task in self.active_tasks.values():
            task.status = TaskStatus.CANCELLED
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ AI agents coordination system stopped")


async def main():
    """Main entry point"""
    coordinator = AIAgentsMasterCoordinator()
    
    try:
        await coordinator.start_all_agents()
        
        # Example: Submit some test tasks
        coordinator.submit_task(
            "arbitrage_analysis",
            "Analyze arbitrage opportunities between Uniswap and SushiSwap",
            {"token_pair": "USDC/WETH", "amount": 1000},
            TaskPriority.HIGH
        )
        
        coordinator.submit_task(
            "risk_assessment",
            "Assess risk for flash loan strategy",
            {"strategy": "triangle_arbitrage", "capital": 50000},
            TaskPriority.NORMAL
        )
        
        # Keep running
        while coordinator.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Coordinator error: {e}")
    finally:
        await coordinator.stop_all_agents()


if __name__ == "__main__":
    asyncio.run(main())
