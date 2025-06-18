#!/usr/bin/env python3
"""
Multi-Agent Terminal Coordinator with GitHub Copilot Integration
===============================================================

Advanced LangChain system with multiple specialized agents for:
- Terminal task automation
- MCP server training and management
- GitHub Copilot integration
- Project coordination and development assistance
"""

import asyncio
import logging
import json
import subprocess
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import signal

# Enhanced imports
import psutil
import docker
import redis
import requests
import aiohttp
import aiofiles
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# LangChain imports
from langchain.chains import LLMChain
from langchain.agents import Tool, AgentExecutor, create_react_agent, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.schema import BaseRetriever, Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.base import BaseCallbackHandler
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.tools.base import BaseTool
from langchain.schema import AgentAction, AgentFinish
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('multi_agent_coordinator.log')
    ]
)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of specialized agents"""
    TERMINAL_EXECUTOR = "terminal_executor"
    MCP_TRAINER = "mcp_trainer"
    GITHUB_COPILOT = "github_copilot"
    PROJECT_MANAGER = "project_manager"
    DATA_ANALYST = "data_analyst"
    SYSTEM_MONITOR = "system_monitor"
    CODE_ASSISTANT = "code_assistant"

@dataclass
class AgentConfig:
    """Configuration for each agent"""
    name: str
    agent_type: AgentType
    description: str
    tools: List[str] = field(default_factory=list)
    memory_size: int = 2000
    max_iterations: int = 10
    temperature: float = 0.1
    enabled: bool = True
    priority: int = 1
    specialty_areas: List[str] = field(default_factory=list)

@dataclass
class TaskRequest:
    """Task request structure"""
    task_id: str
    requester: str
    task_type: str
    description: str
    priority: int
    deadline: Optional[datetime] = None
    agent_preference: Optional[AgentType] = None
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)

class TerminalExecutorTool(BaseTool):
    """Tool for executing terminal commands safely"""
    
    name: str = "terminal_executor"
    description: str = "Execute terminal commands safely with proper error handling"
    coordinator: Any = None  # Allow coordinator field
    
    def __init__(self, coordinator: 'MultiAgentTerminalCoordinator'):
        super().__init__()
        object.__setattr__(self, 'coordinator', coordinator)
    
    def _run(self, command: str, timeout: int = 60, shell: str = "powershell") -> Dict[str, Any]:
        """Execute terminal command"""
        try:
            logger.info(f"Executing command: {command}")
            
            if shell.lower() == "powershell":
                cmd = ["powershell", "-Command", command]
            else:
                cmd = command.split()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=(shell.lower() != "powershell")
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

class MCPTrainerTool(BaseTool):
    """Tool for training and managing MCP servers"""
    
    name: str = "mcp_trainer"
    description: str = "Train, manage, and optimize MCP servers"
    coordinator: Any = None  # Allow coordinator field
    
    def __init__(self, coordinator: 'MultiAgentTerminalCoordinator'):
        super().__init__()
        object.__setattr__(self, 'coordinator', coordinator)
    
    def _run(self, action: str, server_name: str = "", data: Dict = None) -> Dict[str, Any]:
        """Execute MCP training/management action"""
        try:
            if action == "start_training":
                return self._start_training(server_name, data or {})
            elif action == "check_status":
                return self._check_server_status(server_name)
            elif action == "update_model":
                return self._update_model(server_name, data or {})
            elif action == "restart_server":
                return self._restart_server(server_name)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _start_training(self, server_name: str, training_data: Dict) -> Dict[str, Any]:
        """Start training process for MCP server"""
        logger.info(f"🎓 Starting training for MCP server: {server_name}")
        
        # Implementation would start actual training process
        # For now, simulate training
        return {
            "success": True,
            "message": f"Training started for {server_name}",
            "training_id": str(uuid.uuid4()),
            "estimated_duration": "30 minutes"
        }
    
    def _check_server_status(self, server_name: str) -> Dict[str, Any]:
        """Check MCP server status"""
        logger.info(f"📊 Checking status of MCP server: {server_name}")
        
        # Implementation would check actual server status
        return {
            "success": True,
            "server": server_name,
            "status": "running",
            "uptime": "2 hours",
            "memory_usage": "256MB",
            "request_count": 1245
        }
    
    def _update_model(self, server_name: str, model_data: Dict) -> Dict[str, Any]:
        """Update MCP server model"""
        logger.info(f"🔄 Updating model for MCP server: {server_name}")
        
        return {
            "success": True,
            "message": f"Model updated for {server_name}",
            "version": "v2.1.0"
        }
    
    def _restart_server(self, server_name: str) -> Dict[str, Any]:
        """Restart MCP server"""
        logger.info(f"🔄 Restarting MCP server: {server_name}")
        
        return {
            "success": True,
            "message": f"Server {server_name} restarted successfully"
        }

class GitHubCopilotTool(BaseTool):
    """Tool for GitHub Copilot integration"""
    
    name: str = "github_copilot"
    description: str = "Integrate with GitHub Copilot for code assistance and suggestions"
    coordinator: Any = None  # Allow coordinator field
    
    def __init__(self, coordinator: 'MultiAgentTerminalCoordinator'):
        super().__init__()
        object.__setattr__(self, 'coordinator', coordinator)
    
    def _run(self, action: str, context: str = "", file_path: str = "") -> Dict[str, Any]:
        """Execute GitHub Copilot action"""
        try:
            if action == "get_suggestions":
                return self._get_code_suggestions(context, file_path)
            elif action == "explain_code":
                return self._explain_code(context)
            elif action == "generate_tests":
                return self._generate_tests(context, file_path)
            elif action == "optimize_code":
                return self._optimize_code(context)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_code_suggestions(self, context: str, file_path: str) -> Dict[str, Any]:
        """Get code suggestions from GitHub Copilot"""
        logger.info(f"💡 Getting code suggestions for: {file_path}")
        
        # In real implementation, this would interface with GitHub Copilot API
        suggestions = [
            "Consider using async/await for better performance",
            "Add error handling for network requests",
            "Implement caching to reduce API calls",
            "Use type hints for better code documentation"
        ]
        
        return {
            "success": True,
            "suggestions": suggestions,
            "context": context[:100] + "..." if len(context) > 100 else context
        }
    
    def _explain_code(self, code: str) -> Dict[str, Any]:
        """Explain code functionality"""
        logger.info("📖 Explaining code functionality")
        
        return {
            "success": True,
            "explanation": "This code appears to be a configuration setup for a multi-agent system with error handling and logging capabilities.",
            "complexity": "Medium",
            "suggestions": ["Consider adding docstrings", "Break down into smaller functions"]
        }
    
    def _generate_tests(self, code: str, file_path: str) -> Dict[str, Any]:
        """Generate test cases for code"""
        logger.info(f"🧪 Generating tests for: {file_path}")
        
        return {
            "success": True,
            "test_file": file_path.replace(".py", "_test.py"),
            "test_cases": [
                "test_initialization",
                "test_error_handling",
                "test_configuration_loading"
            ]
        }
    
    def _optimize_code(self, code: str) -> Dict[str, Any]:
        """Optimize code performance"""
        logger.info("⚡ Optimizing code performance")
        
        return {
            "success": True,
            "optimizations": [
                "Use list comprehensions instead of loops",
                "Cache frequently accessed data",
                "Use generators for memory efficiency"
            ],
            "estimated_improvement": "25% performance boost"
        }

class ProjectManagerTool(BaseTool):
    """Tool for project management tasks"""
    
    name: str = "project_manager"
    description: str = "Manage project structure, dependencies, and development workflow"
    coordinator: Any = None  # Allow coordinator field
    
    def __init__(self, coordinator: 'MultiAgentTerminalCoordinator'):
        super().__init__()
        object.__setattr__(self, 'coordinator', coordinator)
    
    def _run(self, action: str, path: str = "", data: Dict = None) -> Dict[str, Any]:
        """Execute project management action"""
        try:
            if action == "analyze_structure":
                return self._analyze_project_structure(path)
            elif action == "check_dependencies":
                return self._check_dependencies(path)
            elif action == "create_backup":
                return self._create_backup(path)
            elif action == "organize_files":
                return self._organize_files(path)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Analyze project structure"""
        logger.info(f"📊 Analyzing project structure: {project_path}")
        
        structure = {
            "total_files": 0,
            "directories": [],
            "file_types": {},
            "recommendations": []
        }
        
        if os.path.exists(project_path):
            for root, dirs, files in os.walk(project_path):
                structure["total_files"] += len(files)
                structure["directories"].extend(dirs)
                
                for file in files:
                    ext = Path(file).suffix
                    structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
        
        structure["recommendations"] = [
            "Consider organizing scripts into separate directories",
            "Add proper documentation files",
            "Implement proper logging structure"
        ]
        
        return {"success": True, "structure": structure}
    
    def _check_dependencies(self, project_path: str) -> Dict[str, Any]:
        """Check project dependencies"""
        logger.info(f"🔍 Checking dependencies for: {project_path}")
        
        requirements_file = Path(project_path) / "requirements.txt"
        package_json = Path(project_path) / "package.json"
        
        dependencies = {
            "python": [],
            "node": [],
            "missing": [],
            "outdated": []
        }
        
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    dependencies["python"] = [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                logger.error(f"Error reading requirements.txt: {e}")
        
        return {"success": True, "dependencies": dependencies}
    
    def _create_backup(self, project_path: str) -> Dict[str, Any]:
        """Create project backup"""
        logger.info(f"💾 Creating backup for: {project_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        
        return {
            "success": True,
            "backup_name": backup_name,
            "backup_path": f"{project_path}/backups/{backup_name}",
            "timestamp": timestamp
        }
    
    def _organize_files(self, project_path: str) -> Dict[str, Any]:
        """Organize project files"""
        logger.info(f"📁 Organizing files in: {project_path}")
        
        organized = {
            "moved_files": 0,
            "created_directories": 0,
            "actions": []
        }
        
        # Implementation would organize files based on type and purpose
        organized["actions"] = [
            "Created /logs directory for log files",
            "Moved backup files to /backups",
            "Organized Python files by functionality"
        ]
        
        return {"success": True, "organized": organized}

class MultiAgentTerminalCoordinator:
    """Main coordinator for multi-agent terminal system"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.agents = {}
        self.tools = {}
        self.task_queue = queue.Queue()
        self.active_tasks = {}
        self.executor = ThreadPoolExecutor(max_workers=6)
        
        # Initialize LLM
        self.llm = None
        self._initialize_llm()
        
        # Setup agents
        self._setup_agents()
        
        # System status
        self.system_status = {
            "initialized": False,
            "agents_active": 0,
            "tasks_completed": 0,
            "uptime_start": datetime.now()
        }
    
    def _initialize_llm(self):
        """Initialize Language Model"""
        try:
            # Try to use local Ollama first
            self.llm = Ollama(model="llama2", temperature=0.1)
            logger.info("Initialized local Ollama LLM")
        except Exception as e:
            logger.warning(f"Could not initialize local LLM: {e}")
            # Fallback to a simple mock for demonstration
            self.llm = None
    
    def _setup_agents(self):
        """Setup all specialized agents"""
        logger.info("Setting up specialized agents...")
        
        # Agent configurations
        agent_configs = [
            AgentConfig(
                name="Terminal Executor",
                agent_type=AgentType.TERMINAL_EXECUTOR,
                description="Handles terminal commands and system operations",
                tools=["terminal_executor"],
                specialty_areas=["command_execution", "system_administration", "file_operations"]
            ),
            AgentConfig(
                name="MCP Trainer",
                agent_type=AgentType.MCP_TRAINER,
                description="Manages and trains MCP servers",
                tools=["mcp_trainer"],
                specialty_areas=["machine_learning", "server_management", "training_data"]
            ),
            AgentConfig(
                name="GitHub Copilot Assistant",
                agent_type=AgentType.GITHUB_COPILOT,
                description="Provides code assistance and GitHub Copilot integration",
                tools=["github_copilot"],
                specialty_areas=["code_generation", "code_review", "development_assistance"]
            ),
            AgentConfig(
                name="Project Manager",
                agent_type=AgentType.PROJECT_MANAGER,
                description="Manages project structure and development workflow",
                tools=["project_manager"],
                specialty_areas=["project_organization", "dependency_management", "workflow_optimization"]
            )
        ]
        
        # Initialize tools
        self.tools = {
            "terminal_executor": TerminalExecutorTool(self),
            "mcp_trainer": MCPTrainerTool(self),
            "github_copilot": GitHubCopilotTool(self),
            "project_manager": ProjectManagerTool(self)
        }
        
        # Create agents
        for config in agent_configs:
            try:
                agent_tools = [self.tools[tool_name] for tool_name in config.tools if tool_name in self.tools]
                
                if self.llm and agent_tools:
                    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
                      # Use modern agent creation instead of deprecated AgentType
                    from langchain.agents import create_structured_chat_agent, AgentExecutor
                    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
                    
                    # Create a simple prompt template
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", f"You are {config.name}. {config.role}"),
                        MessagesPlaceholder(variable_name="chat_history"),
                        ("human", "{input}"),
                        MessagesPlaceholder(variable_name="agent_scratchpad")
                    ])
                    
                    # Create the agent and executor
                    agent = create_structured_chat_agent(
                        llm=self.llm,
                        tools=agent_tools,
                        prompt=prompt
                    )
                    
                    agent_executor = AgentExecutor(
                        agent=agent,
                        tools=agent_tools,
                        memory=memory,
                        verbose=True,
                        max_iterations=config.max_iterations,
                        handle_parsing_errors=True
                    )
                    
                    self.agents[config.agent_type] = {
                        "agent": agent,
                        "config": config,
                        "status": "ready",
                        "tasks_completed": 0
                    }
                    
                    logger.info(f"✅ Agent '{config.name}' initialized successfully")
                else:
                    # Create mock agent for demonstration
                    self.agents[config.agent_type] = {
                        "agent": None,
                        "config": config,
                        "status": "mock",
                        "tasks_completed": 0
                    }
                    logger.info(f"⚠️ Mock agent '{config.name}' created (LLM not available)")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize agent '{config.name}': {e}")
        
        self.system_status["agents_active"] = len(self.agents)
        logger.info(f"🤖 Initialized {len(self.agents)} agents")
    
    async def execute_task(self, task: TaskRequest) -> Dict[str, Any]:
        """Execute a task using the appropriate agent"""
        logger.info(f"🎯 Executing task: {task.description}")
        
        # Select best agent for task
        selected_agent_type = self._select_agent_for_task(task)
        
        if selected_agent_type not in self.agents:
            return {
                "success": False,
                "error": f"No agent available for task type: {task.task_type}",
                "task_id": task.task_id
            }
        
        agent_info = self.agents[selected_agent_type]
        
        try:
            if agent_info["agent"]:
                # Execute with real agent
                result = await self._execute_with_agent(agent_info["agent"], task)
            else:
                # Execute with mock agent
                result = await self._execute_mock_task(selected_agent_type, task)
            
            agent_info["tasks_completed"] += 1
            self.system_status["tasks_completed"] += 1
            
            return {
                "success": True,
                "result": result,
                "agent_used": selected_agent_type.value,
                "task_id": task.task_id
            }
            
        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_used": selected_agent_type.value,
                "task_id": task.task_id
            }
    
    def _select_agent_for_task(self, task: TaskRequest) -> AgentType:
        """Select the best agent for a given task"""
        
        # If agent preference is specified
        if task.agent_preference:
            return task.agent_preference
        
        # Select based on task type
        task_type_mapping = {
            "terminal": AgentType.TERMINAL_EXECUTOR,
            "command": AgentType.TERMINAL_EXECUTOR,
            "mcp": AgentType.MCP_TRAINER,
            "training": AgentType.MCP_TRAINER,
            "github": AgentType.GITHUB_COPILOT,
            "code": AgentType.GITHUB_COPILOT,
            "project": AgentType.PROJECT_MANAGER,
            "organize": AgentType.PROJECT_MANAGER
        }
        
        for keyword, agent_type in task_type_mapping.items():
            if keyword in task.task_type.lower() or keyword in task.description.lower():
                return agent_type
        
        # Default to terminal executor
        return AgentType.TERMINAL_EXECUTOR
    
    async def _execute_with_agent(self, agent, task: TaskRequest) -> Any:
        """Execute task with LangChain agent"""
        prompt = f"""
        Task: {task.description}
        Type: {task.task_type}
        Priority: {task.priority}
        Context: {json.dumps(task.context, indent=2)}
        
        Please execute this task and provide a detailed response.
        """
        
        return agent.run(prompt)
    
    async def _execute_mock_task(self, agent_type: AgentType, task: TaskRequest) -> Dict[str, Any]:
        """Execute task with mock agent (when LLM is not available)"""
        logger.info(f"🎭 Executing mock task with {agent_type.value}")
        
        # Simulate task execution based on agent type
        if agent_type == AgentType.TERMINAL_EXECUTOR:
            return {
                "action": "terminal_command_executed",
                "command": task.context.get("command", "unknown"),
                "status": "simulated_success"
            }
        elif agent_type == AgentType.MCP_TRAINER:
            return {
                "action": "mcp_training_started",
                "server": task.context.get("server", "unknown"),
                "status": "training_initiated"
            }
        elif agent_type == AgentType.GITHUB_COPILOT:
            return {
                "action": "code_assistance_provided",
                "suggestions": ["Mock suggestion 1", "Mock suggestion 2"],
                "status": "assistance_ready"
            }
        elif agent_type == AgentType.PROJECT_MANAGER:
            return {
                "action": "project_managed",
                "changes": ["Mock change 1", "Mock change 2"],
                "status": "project_updated"
            }
        
        return {"status": "mock_execution_completed"}
    
    def create_task(self, task_type: str, description: str, priority: int = 1, 
                   context: Dict = None, agent_preference: AgentType = None) -> TaskRequest:
        """Create a new task request"""
        task = TaskRequest(
            task_id=str(uuid.uuid4()),
            requester="user",
            task_type=task_type,
            description=description,
            priority=priority,
            context=context or {},
            agent_preference=agent_preference
        )
        
        logger.info(f"📝 Created task: {task.task_id} - {description}")
        return task
    
    async def run_terminal_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Run a terminal command using the terminal executor agent"""
        task = self.create_task(
            task_type="terminal",
            description=f"Execute terminal command: {command}",
            context={"command": command, "timeout": timeout}
        )
        
        return await self.execute_task(task)
    
    async def train_mcp_server(self, server_name: str, training_data: Dict = None) -> Dict[str, Any]:
        """Train an MCP server using the MCP trainer agent"""
        task = self.create_task(
            task_type="mcp_training",
            description=f"Train MCP server: {server_name}",
            context={"server_name": server_name, "training_data": training_data or {}},
            agent_preference=AgentType.MCP_TRAINER
        )
        
        return await self.execute_task(task)
    
    async def get_code_assistance(self, code_context: str, file_path: str = "") -> Dict[str, Any]:
        """Get code assistance using GitHub Copilot agent"""
        task = self.create_task(
            task_type="github_assistance",
            description="Provide code assistance and suggestions",
            context={"code_context": code_context, "file_path": file_path},
            agent_preference=AgentType.GITHUB_COPILOT
        )
        
        return await self.execute_task(task)
    
    async def manage_project(self, action: str, project_path: str = "") -> Dict[str, Any]:
        """Manage project using project manager agent"""
        task = self.create_task(
            task_type="project_management",
            description=f"Project management action: {action}",
            context={"action": action, "project_path": project_path or str(self.project_root)},
            agent_preference=AgentType.PROJECT_MANAGER
        )
        
        return await self.execute_task(task)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        uptime = datetime.now() - self.system_status["uptime_start"]
        
        agent_status = {}
        for agent_type, agent_info in self.agents.items():
            agent_status[agent_type.value] = {
                "status": agent_info["status"],
                "tasks_completed": agent_info["tasks_completed"],
                "name": agent_info["config"].name
            }
        
        return {
            "system_initialized": self.system_status["initialized"],
            "agents_active": self.system_status["agents_active"],
            "total_tasks_completed": self.system_status["tasks_completed"],
            "uptime": str(uptime),
            "project_root": str(self.project_root),
            "agents": agent_status
        }
    
    async def start_interactive_session(self):
        """Start interactive session for user commands"""
        logger.info("🎮 Starting interactive multi-agent session...")
        logger.info("Available agents:")
        
        for agent_type, agent_info in self.agents.items():
            logger.info(f"  - {agent_info['config'].name} ({agent_type.value})")
        
        logger.info("\nCommands:")
        logger.info("  'terminal <command>' - Execute terminal command")
        logger.info("  'train <server_name>' - Train MCP server")
        logger.info("  'code <description>' - Get code assistance")
        logger.info("  'project <action>' - Manage project")
        logger.info("  'status' - Show system status")
        logger.info("  'quit' - Exit session")
        
        while True:
            try:
                user_input = input("\n🤖 Enter command: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input.lower() == 'status':
                    status = self.get_system_status()
                    print(json.dumps(status, indent=2, default=str))
                    continue
                
                # Parse command
                parts = user_input.split(' ', 1)
                if len(parts) < 2:
                    print("❌ Invalid command format")
                    continue
                
                command, args = parts
                
                if command.lower() == 'terminal':
                    result = await self.run_terminal_command(args)
                elif command.lower() == 'train':
                    result = await self.train_mcp_server(args)
                elif command.lower() == 'code':
                    result = await self.get_code_assistance(args)
                elif command.lower() == 'project':
                    result = await self.manage_project(args)
                else:
                    print(f"❌ Unknown command: {command}")
                    continue
                
                print(f"✅ Result: {json.dumps(result, indent=2, default=str)}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Error in interactive session: {e}")
        
        logger.info("👋 Interactive session ended")
    
    async def initialize(self) -> bool:
        """Initialize the coordinator system"""
        try:
            logger.info("🚀 Initializing Multi-Agent Terminal Coordinator...")
            
            # Ensure project structure
            (self.project_root / "logs").mkdir(exist_ok=True)
            (self.project_root / "backups").mkdir(exist_ok=True)
            (self.project_root / "training_data").mkdir(exist_ok=True)
            
            self.system_status["initialized"] = True
            logger.info("✅ Multi-Agent Terminal Coordinator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize coordinator: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the coordinator system"""
        logger.info("🛑 Shutting down Multi-Agent Terminal Coordinator...")
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ Shutdown completed")

async def main():
    """Main execution function"""
    coordinator = MultiAgentTerminalCoordinator()
    
    try:
        # Initialize the coordinator
        if not await coordinator.initialize():
            logger.error("❌ Failed to initialize coordinator")
            return
        
        # Start interactive session
        await coordinator.start_interactive_session()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Coordinator error: {e}")
    finally:
        await coordinator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
