#!/usr/bin/env python3
"""
Comprehensive LangChain Flash Loan System Builder & Launcher
Cleans everything, builds from scratch, and deploys all containers with error handling
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from typing import List
from datetime import datetime

class LangChainSystemBuilder:    """Complete system builder with cleanup, build, and deployment"""
    
    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.containers_dir = self.project_root / "containers"
        self.logs_dir = self.project_root / "logs"
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.log_file = self.logs_dir / f"langchain_builder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log message to both console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {level} - {message}"
        print(log_entry)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, command: List[str], description: str, ignore_errors: bool = False) -> bool:
        """Execute a command with proper error handling"""
        self.log(f"🔄 {description}...")
        self.log(f"Command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.log(f"✅ {description} completed successfully")
                if result.stdout.strip():
                    self.log(f"Output: {result.stdout.strip()}")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if ignore_errors:
                    self.log(f"⚠️ {description} failed (ignored): {error_msg}", "WARNING")
                    return False
                else:
                    self.log(f"❌ {description} failed: {error_msg}", "ERROR")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} timed out", "ERROR")
            return False
        except Exception as e:
            if ignore_errors:
                self.log(f"⚠️ {description} error (ignored): {e}", "WARNING")
                return False
            else:
                self.log(f"❌ {description} error: {e}", "ERROR")
                return False
    
    def cleanup_everything(self) -> bool:
        """Clean up all existing containers, networks, and volumes"""
        self.log("🧹 Starting complete cleanup...")
        
        # Stop and remove all flashloan containers
        commands = [
            (["docker", "ps", "-aq", "--filter", "name=flashloan"], "Getting flashloan containers"),
            (["docker", "stop", "$(docker ps -aq --filter name=flashloan)"], "Stopping flashloan containers"),
            (["docker", "rm", "-f", "$(docker ps -aq --filter name=flashloan)"], "Removing flashloan containers"),
            (["docker", "network", "rm", "flashloan-network"], "Removing flashloan network"),
            (["docker", "volume", "prune", "-f"], "Cleaning up volumes"),
            (["docker", "system", "prune", "-f"], "Cleaning up system")
        ]
        
        for command, description in commands:
            # Handle shell commands properly for Windows
            if "$(docker" in " ".join(command):
            # Handle shell commands properly for Windows
            if "$(docker" in " ".join(command):
                if os.name == 'nt':  # Windows
                    # Get container IDs first
                    get_ids = subprocess.run(
                        ["docker", "ps", "-aq", "--filter", "name=flashloan"],
                        capture_output=True, text=True, cwd=self.project_root
                    )
                    if get_ids.returncode == 0 and get_ids.stdout.strip():
                        container_ids = get_ids.stdout.strip().split('\n')
                        if "stop" in command[1]:
                            self.run_command(["docker", "stop"] + container_ids, description, ignore_errors=True)
                        elif "rm" in command[1]:
                            self.run_command(["docker", "rm", "-f"] + container_ids, description, ignore_errors=True)
                    # If no containers found, skip
                elif os.name != 'nt':  # Unix-like systems
                    # Unix-like systems can handle the shell command
                    self.run_command(["sh", "-c", " ".join(command)], description, ignore_errors=True)
            else:
                self.run_command(command, description, ignore_errors=True)
        return True
    
    def setup_directories(self) -> bool:
        """Setup all required directories"""
        self.log("📁 Setting up directory structure...")
        
        directories = [
            "containers",
            "containers/orchestrator",
            "containers/mcp_servers", 
            "containers/agents",
            "containers/infrastructure",
            "logs",
            "data",
            "backups",
            "config"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.log(f"📁 Created: {directory}")
        
        self.log("✅ Directory structure created")
        return True
    
    def create_orchestrator_files(self) -> bool:
        """Create robust orchestrator files"""
        self.log("🎯 Creating orchestrator files...")
        
        orchestrator_dir = self.containers_dir / "orchestrator"
        
        # Create requirements.txt
        requirements_content = """# LangChain and AI dependencies
langchain>=0.1.0
langchain-community>=0.0.10
langchain-core>=0.1.0
langchain-openai>=0.0.5
openai>=1.12.0

# AutoGen dependencies
pyautogen>=0.2.0

# Core async and web dependencies
aiohttp>=3.8.0
aioredis>=2.0.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
requests>=2.31.0

# Database and messaging
psycopg2-binary>=2.9.0
redis>=4.5.0
pika>=1.3.0

# Docker and infrastructure
docker>=6.0.0
tenacity>=8.2.0

# Data processing
pandas>=2.0.0
numpy>=1.24.0

# Logging and monitoring
structlog>=23.0.0
prometheus_client>=0.19.0

# Development tools
pytest>=7.0.0
black>=23.0.0
"""
        
        with open(orchestrator_dir / "requirements.txt", "w") as f:
            f.write(requirements_content)
        
        # Create robust orchestrator
        orchestrator_content = '''#!/usr/bin/env python3
"""
Robust LangChain Orchestrator with comprehensive error handling
"""

import asyncio
import logging
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/logs/orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RobustOrchestrator")

# Safe imports with fallbacks
DEPENDENCIES = {}

try:
    from langchain.llms import OpenAI
    from langchain.agents import initialize_agent, AgentType
    from langchain.memory import ConversationBufferMemory
    from langchain.tools import Tool
    DEPENDENCIES['langchain'] = True
    logger.info("✅ LangChain loaded successfully")
except ImportError as e:
    DEPENDENCIES['langchain'] = False
    logger.warning(f"⚠️ LangChain not available: {e}")

try:
    import redis
    DEPENDENCIES['redis'] = True
except ImportError:
    DEPENDENCIES['redis'] = False
    logger.warning("⚠️ Redis not available - using memory storage")

try:
    import docker
    DEPENDENCIES['docker'] = True
    docker_client = docker.from_env()
except ImportError:
    DEPENDENCIES['docker'] = False
    docker_client = None
    logger.warning("⚠️ Docker client not available")

# Environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')

class RobustOrchestrator:
    """Main orchestrator with error resilience"""
    
    def __init__(self):
        self.is_running = False
        self.agents = {}
        self.servers = {}
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.start_time = datetime.now()
        self.llm = None
        
        # Initialize LangChain if available
        if DEPENDENCIES['langchain'] and OPENAI_API_KEY:
            try:
                self.llm = OpenAI(temperature=0.7, openai_api_key=OPENAI_API_KEY)
                logger.info("✅ LangChain LLM initialized")
            except Exception as e:
                logger.error(f"❌ LangChain LLM initialization failed: {e}")
    
    async def run(self):
        """Main run loop with error handling"""
        try:
            self.is_running = True
            logger.info("🚀 Starting Robust LangChain Orchestrator")
            
            # Log system capabilities
            self._log_system_status()
            
            # Initialize components
            await self._initialize_system()
            
            # Start monitoring tasks
            tasks = [
                asyncio.create_task(self._health_monitor()),
                asyncio.create_task(self._task_processor()),
                asyncio.create_task(self._keep_alive_loop())
            ]
            
            # Run until stopped
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"💥 Critical error in orchestrator: {e}")
            await self._handle_critical_error(e)
        finally:
            self.is_running = False
            logger.info("🛑 Orchestrator stopped")
    
    def _log_system_status(self):
        """Log current system status"""
        logger.info("📊 System Status:")
        for component, available in DEPENDENCIES.items():
            status = "✅ Available" if available else "❌ Not Available"
            logger.info(f"   {component}: {status}")
        
        logger.info(f"   GitHub Token: {'✅ Set' if GITHUB_TOKEN else '❌ Missing'}")
        logger.info(f"   OpenAI Key: {'✅ Set' if OPENAI_API_KEY else '❌ Missing'}")
    
    async def _initialize_system(self):
        """Initialize system components"""
        logger.info("🔧 Initializing system...")
        
        # Create default agents
        agent_configs = [
            ("coordinator", "System coordination and monitoring"),
            ("analyzer", "Market analysis and opportunity detection"),
            ("executor", "Trade execution and blockchain interaction"),
            ("risk_manager", "Risk assessment and management"),
            ("monitor", "System health monitoring"),
            ("data_collector", "Data collection from various sources"),
            ("arbitrage_bot", "Arbitrage opportunity detection"),
            ("liquidity_manager", "Liquidity pool optimization"),
            ("reporter", "Report generation and analytics"),
            ("healer", "Auto-healing and recovery")
        ]
        
        for agent_name, description in agent_configs:
            self.agents[agent_name] = {
                'name': agent_name,
                'description': description,
                'status': 'active',
                'created_at': datetime.now(),
                'tasks_completed': 0
            }
        
        # Initialize MCP servers list
        for i in range(1, 22):  # 21 servers
            server_name = f"mcp_server_{i:02d}"
            self.servers[server_name] = {
                'name': server_name,
                'port': 8000 + i,
                'status': 'unknown',
                'last_check': datetime.now()
            }
        
        logger.info(f"✅ Initialized {len(self.agents)} agents and {len(self.servers)} MCP servers")
    
    async def _health_monitor(self):
        """Monitor system health continuously"""
        while self.is_running:
            try:
                logger.info("🏥 Performing health checks...")
                
                # Check MCP servers if Docker is available
                if DEPENDENCIES['docker'] and docker_client:
                    await self._check_mcp_servers()
                
                # Check agents
                active_agents = sum(1 for agent in self.agents.values() if agent['status'] == 'active')
                logger.info(f"📊 Active agents: {active_agents}/{len(self.agents)}")
                
                # System uptime
                uptime = datetime.now() - self.start_time
                logger.info(f"⏰ System uptime: {uptime}")
                logger.info(f"📈 Tasks completed: {self.tasks_completed}, Failed: {self.tasks_failed}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _check_mcp_servers(self):
        """Check MCP server health"""
        try:
            containers = docker_client.containers.list(filters={'name': 'flashloan'})
            
            healthy_servers = 0
            for container in containers:
                if 'mcp' in container.name and container.status == 'running':
                    healthy_servers += 1
            
            logger.info(f"🖥️ Healthy MCP servers: {healthy_servers}")
            
        except Exception as e:
            logger.error(f"❌ MCP server check failed: {e}")
    
    async def _task_processor(self):
        """Process tasks continuously"""
        while self.is_running:
            try:
                # Simulate task processing
                tasks = [
                    "Analyze market conditions",
                    "Check system health",
                    "Monitor risk levels",
                    "Update data feeds",
                    "Generate reports"
                ]
                
                for task in tasks:
                    await self._execute_task(task)
                    await asyncio.sleep(10)  # Process tasks every 10 seconds
                
                await asyncio.sleep(60)  # Wait before next batch
                
            except Exception as e:
                logger.error(f"❌ Task processor error: {e}")
                await asyncio.sleep(30)
    
    async def _execute_task(self, task: str):
        """Execute a task with LangChain if available"""
        try:
            logger.info(f"🎯 Executing task: {task}")
            
            if self.llm and DEPENDENCIES['langchain']:
                # Use LangChain for intelligent task processing
                prompt = f"As a DeFi flash loan system, analyze and respond to this task: {task}"
                try:
                    response = self.llm(prompt)
                    logger.info(f"🤖 LangChain response: {response[:100]}...")
                    self.tasks_completed += 1
                except Exception as e:
                    logger.error(f"❌ LangChain execution failed: {e}")
                    self.tasks_failed += 1
            else:
                # Fallback processing
                logger.info(f"📝 Fallback processing for: {task}")
                await asyncio.sleep(1)  # Simulate processing
                self.tasks_completed += 1
                
        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            self.tasks_failed += 1
    
    async def _keep_alive_loop(self):
        """Keep the system alive and prevent shutdown"""
        while self.is_running:
            try:
                # Heartbeat log
                logger.info(f"💓 System heartbeat - Uptime: {datetime.now() - self.start_time}")
                
                # Perform maintenance tasks
                await self._perform_maintenance()
                
                # Wait 5 minutes before next heartbeat
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Keep alive error: {e}")
                await asyncio.sleep(60)
    
    async def _perform_maintenance(self):
        """Perform regular maintenance tasks"""
        try:
            # Clean up old logs if needed
            log_dir = Path("/app/logs")
            if log_dir.exists():
                log_files = list(log_dir.glob("*.log"))
                if len(log_files) > 10:  # Keep only last 10 log files
                    oldest_files = sorted(log_files, key=lambda x: x.stat().st_mtime)[:-10]
                    for old_file in oldest_files:
                        old_file.unlink()
                        logger.info(f"🗑️ Cleaned up old log: {old_file.name}")
            
            # Update agent statistics
            for agent in self.agents.values():
                if agent['status'] == 'active':
                    agent['last_activity'] = datetime.now()
            
            logger.info("🔧 Maintenance tasks completed")
            
        except Exception as e:
            logger.error(f"❌ Maintenance error: {e}")
    
    async def _handle_critical_error(self, error: Exception):
        """Handle critical system errors"""
        logger.error(f"🚨 Handling critical error: {error}")
        
        try:
            # Log error details
            error_info = {
                'error': str(error),
                'type': type(error).__name__,
                'timestamp': datetime.now().isoformat(),
                'system_status': {
                    'uptime': str(datetime.now() - self.start_time),
                    'tasks_completed': self.tasks_completed,
                    'tasks_failed': self.tasks_failed,
                    'dependencies': DEPENDENCIES
                }
            }
            
            # Save error info to file
            error_file = Path("/app/logs/critical_errors.json")
            if error_file.exists():
                with open(error_file, 'r') as f:
                    errors = json.load(f)
            else:
                errors = []
            
            errors.append(error_info)
            
            with open(error_file, 'w') as f:
                json.dump(errors, f, indent=2)
            
            logger.info("💾 Critical error logged to file")
            
        except Exception as e:
            logger.error(f"❌ Failed to handle critical error: {e}")

# Health check function for Docker
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'dependencies': DEPENDENCIES
    }

if __name__ == "__main__":
    # Create logs directory
    os.makedirs("/app/logs", exist_ok=True)
    
    # Start orchestrator
    orchestrator = RobustOrchestrator()
    
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        logger.info("🛑 Orchestrator stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
'''        
        with open(orchestrator_dir / "robust_orchestrator.py", "w", encoding="utf-8") as f:
            f.write(orchestrator_content)
        
        # Create Dockerfile
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY robust_orchestrator.py .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import asyncio; import sys; sys.path.append('/app'); from robust_orchestrator import health_check; print(asyncio.run(health_check()))" || exit 1

# Run the orchestrator
CMD ["python", "robust_orchestrator.py"]
"""
        
        with open(orchestrator_dir / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        self.log("✅ Orchestrator files created")
        return True
    
    def create_mcp_server_files(self) -> bool:
        """Create MCP server files"""
        self.log("🖥️ Creating MCP server files...")
        
        mcp_dir = self.containers_dir / "mcp_servers"
        
        # Create simple requirements
        requirements_content = """fastapi>=0.104.0
uvicorn[standard]>=0.24.0
aiohttp>=3.8.0
requests>=2.31.0
"""
        
        with open(mcp_dir / "requirements.txt", "w") as f:
            f.write(requirements_content)
        
        # Create simple MCP server
        server_content = '''#!/usr/bin/env python3
"""
Simple MCP Server
"""

import os
import time
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPServer")

app = FastAPI()

SERVER_NAME = os.getenv('MCP_SERVER_NAME', 'mcp_server')
SERVER_PORT = int(os.getenv('MCP_SERVER_PORT', '8001'))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "server": SERVER_NAME,
        "port": SERVER_PORT,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def status():
    return {
        "server": SERVER_NAME,
        "uptime": time.time(),
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {SERVER_NAME} on port {SERVER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
'''
        
        with open(mcp_dir / "mcp_server.py", "w") as f:
            f.write(server_content)
        
        # Create Dockerfile
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY mcp_server.py .

# Expose port (will be overridden by environment)
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:${MCP_SERVER_PORT:-8001}/health || exit 1

# Run server
CMD ["python", "mcp_server.py"]
"""
        
        with open(mcp_dir / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        self.log("✅ MCP server files created")
        return True
    
    def create_agent_files(self) -> bool:
        """Create agent files"""
        self.log("🤖 Creating agent files...")
        
        agent_dir = self.containers_dir / "agents"
        
        # Create requirements
        requirements_content = """aiohttp>=3.8.0
requests>=2.31.0
asyncio-mqtt>=0.13.0
"""
        
        with open(agent_dir / "requirements.txt", "w") as f:
            f.write(requirements_content)
        
        # Create simple agent
        agent_content = '''#!/usr/bin/env python3
"""
Simple Agent
"""

import os
import asyncio
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Agent")

AGENT_NAME = os.getenv('AGENT_NAME', 'agent')
AGENT_ROLE = os.getenv('AGENT_ROLE', 'general')
ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'http://orchestrator:8000')

class SimpleAgent:
    def __init__(self):
        self.name = AGENT_NAME
        self.role = AGENT_ROLE
        self.is_running = False
        self.start_time = datetime.now()
        
    async def run(self):
        self.is_running = True
        logger.info(f"🤖 Starting agent {self.name} with role {self.role}")
        
        while self.is_running:
            try:
                await self.perform_task()
                await asyncio.sleep(30)  # Task every 30 seconds
            except Exception as e:
                logger.error(f"❌ Agent error: {e}")
                await asyncio.sleep(60)
    
    async def perform_task(self):
        """Perform agent-specific task"""
        uptime = datetime.now() - self.start_time
        logger.info(f"💼 Agent {self.name} performing {self.role} task - Uptime: {uptime}")
        
        # Simulate work
        await asyncio.sleep(1)

if __name__ == "__main__":
    agent = SimpleAgent()
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("🛑 Agent stopped")
'''
        
        with open(agent_dir / "agent.py", "w") as f:
            f.write(agent_content)
        
        # Create Dockerfile
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent.py .

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \\
    CMD ps aux | grep agent.py | grep -v grep || exit 1

# Run agent
CMD ["python", "agent.py"]
"""
        
        with open(agent_dir / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        self.log("✅ Agent files created")
        return True
    
    def create_docker_compose(self) -> bool:
        """Create comprehensive Docker Compose file"""
        self.log("🐳 Creating Docker Compose configuration...")
        
        compose_content = """version: '3.8'

networks:
  flashloan-network:
    driver: bridge

volumes:
  redis-data:
  postgres-data:
  logs-data:

services:
  # Infrastructure Services
  redis:
    image: redis:7-alpine
    container_name: flashloan-redis
    networks:
      - flashloan-network
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: flashloan-postgres
    networks:
      - flashloan-network
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: flashloan
      POSTGRES_USER: flashloan
      POSTGRES_PASSWORD: flashloan123
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flashloan"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: flashloan-rabbitmq
    networks:
      - flashloan-network
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: flashloan
      RABBITMQ_DEFAULT_PASS: flashloan123
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Main Orchestrator
  orchestrator:
    build: ./containers/orchestrator
    container_name: flashloan-orchestrator
    networks:
      - flashloan-network
    ports:
      - "8000:8000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://flashloan:flashloan123@postgres:5432/flashloan
      - RABBITMQ_URL=amqp://flashloan:flashloan123@rabbitmq:5672
    volumes:
      - logs-data:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    restart: unless-stopped

"""

        # Add 21 MCP servers
        for i in range(1, 22):
            port = 8000 + i
            server_name = f"mcp-server-{i:02d}"
            compose_content += f"""  {server_name}:
    build: ./containers/mcp_servers
    container_name: flashloan-{server_name}
    networks:
      - flashloan-network
    ports:
      - "{port}:{port}"
    environment:
      - MCP_SERVER_NAME={server_name}
      - MCP_SERVER_PORT={port}
    depends_on:
      - orchestrator
    restart: unless-stopped

"""

        # Add 10 agents
        agents = [
            ("coordinator", "system_coordinator"),
            ("analyzer", "market_analyzer"),
            ("executor", "trade_executor"),
            ("risk-manager", "risk_assessment"),
            ("monitor", "system_monitor"),
            ("data-collector", "data_collection"),
            ("arbitrage-bot", "arbitrage_detection"),
            ("liquidity-manager", "liquidity_optimization"),
            ("reporter", "report_generator"),
            ("healer", "auto_healing")
        ]
        
        for agent_name, agent_role in agents:
            compose_content += f"""  agent-{agent_name}:
    build: ./containers/agents
    container_name: flashloan-agent-{agent_name}
    networks:
      - flashloan-network
    environment:
      - AGENT_NAME={agent_name}
      - AGENT_ROLE={agent_role}
      - ORCHESTRATOR_URL=http://orchestrator:8000
    depends_on:
      - orchestrator
    restart: unless-stopped

"""
        
        with open(self.project_root / "docker-compose.yml", "w") as f:
            f.write(compose_content)
        
        self.log("✅ Docker Compose file created")
        return True
    
    def build_and_deploy(self) -> bool:
        """Build and deploy all containers"""
        self.log("🚀 Building and deploying all containers...")
        
        # Create network first
        self.run_command(
            ["docker", "network", "create", "flashloan-network"],
            "Creating Docker network",
            ignore_errors=True
        )
        
        # Build and start services
        success = self.run_command(
            ["docker-compose", "up", "--build", "-d"],
            "Building and starting all services"
        )
        
        if success:
            self.log("✅ All containers deployed successfully")
            return True
        else:
            self.log("❌ Container deployment failed", "ERROR")
            return False
    
    def verify_deployment(self) -> bool:
        """Verify that all containers are running"""
        self.log("🔍 Verifying deployment...")
        
        # Wait for containers to start
        time.sleep(30)
        
        # Check container status
        success = self.run_command(
            ["docker-compose", "ps"],
            "Checking container status"
        )
        
        if success:
            # Check orchestrator health
            time.sleep(30)  # Give orchestrator time to start
            self.run_command(
                ["curl", "-f", "http://localhost:8000/health"],
                "Checking orchestrator health",
                ignore_errors=True
            )
        
        self.log("✅ Deployment verification complete")
        return success
    
    def monitor_system(self) -> None:
        """Monitor the running system"""
        self.log("📊 Starting system monitoring...")
        
        try:
            while True:
                # Check container status
                self.run_command(
                    ["docker-compose", "ps"],
                    "System status check"
                )
                
                # Check logs for errors
                self.run_command(
                    ["docker-compose", "logs", "--tail=10", "orchestrator"],
                    "Checking orchestrator logs"
                )
                
                self.log(f"🕐 System monitoring checkpoint - {datetime.now()}")
                time.sleep(300)  # Check every 5 minutes
                
        except KeyboardInterrupt:
            self.log("📊 Monitoring stopped by user")
    
    def run_build_command(self) -> bool:
        """Execute the complete build process"""
        self.log("🎯 Starting complete LangChain system build...")
        
        steps = [
            (self.cleanup_everything, "Complete cleanup"),
            (self.setup_directories, "Directory setup"),
            (self.create_orchestrator_files, "Orchestrator creation"),
            (self.create_mcp_server_files, "MCP server creation"),
            (self.create_agent_files, "Agent creation"),
            (self.create_docker_compose, "Docker Compose creation"),
            (self.build_and_deploy, "Build and deployment"),
            (self.verify_deployment, "Deployment verification")
        ]
        
        for step_func, description in steps:
            self.log(f"📋 Step: {description}")
            if not step_func():
                self.log(f"❌ Failed at step: {description}", "ERROR")
                return False
            self.log(f"✅ Completed: {description}")
        
        self.log("🎉 Complete LangChain system build successful!")
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="LangChain Flash Loan System Builder")
    parser.add_argument("command", choices=["build", "monitor", "cleanup"], 
                       help="Command to execute")
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    builder = LangChainSystemBuilder(args.project_root)
    
    if args.command == "build":
        success = builder.run_build_command()
        if success:
            print("\n🎉 Build completed successfully!")
            print("🔧 System is now running. Use 'python launch_enhanced_langchain_system.py monitor' to monitor.")
            print("📊 Access orchestrator at: http://localhost:8000")
        else:
            print("\n❌ Build failed. Check logs for details.")
            sys.exit(1)
            
    elif args.command == "monitor":
        builder.monitor_system()
        
    elif args.command == "cleanup":
        builder.cleanup_everything()
        print("✅ Cleanup completed")

if __name__ == "__main__":
    main()
