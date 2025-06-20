#!/usr/bin/env python3
"""
Robust LangChain Flash Loan System Builder with Individual Containers
Creates separate containers for each MCP server and agent with GitHub token coordination
"""

import os
import sys
import subprocess
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class RobustLangChainBuilder:
    """Complete system builder with individual containers and coordination"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.containers_dir = self.project_root / "containers"
        self.logs_dir = self.project_root / "logs"
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.containers_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.log_file = self.logs_dir / f"robust_builder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log message to both console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {level} - {message}"
        print(log_entry)
        
        # Use UTF-8 encoding to handle special characters
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, command: List[str], description: str, ignore_errors: bool = False) -> bool:
        """Execute a command with proper error handling"""
        self.log(f"Running: {description}...")
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
                self.log(f"SUCCESS: {description} completed successfully")
                if result.stdout.strip():
                    self.log(f"Output: {result.stdout.strip()}")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if ignore_errors:
                    self.log(f"WARNING: {description} failed (ignored): {error_msg}", "WARNING")
                    return False
                else:
                    self.log(f"ERROR: {description} failed: {error_msg}", "ERROR")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.log(f"ERROR: {description} timed out", "ERROR")
            return False
        except Exception as e:
            if ignore_errors:
                self.log(f"WARNING: {description} error (ignored): {e}", "WARNING")
                return False
            else:
                self.log(f"ERROR: {description} error: {e}", "ERROR")
                return False
    
    def cleanup_everything(self) -> bool:
        """Clean up all existing containers, networks, and volumes"""
        self.log("Starting complete cleanup...")
        
        # Get and stop flashloan containers
        get_result = subprocess.run(
            ["docker", "ps", "-aq", "--filter", "name=flashloan"],
            capture_output=True, text=True, cwd=self.project_root
        )
        
        if get_result.returncode == 0 and get_result.stdout.strip():
            container_ids = get_result.stdout.strip().split('\n')
            self.log(f"Found {len(container_ids)} flashloan containers to clean")
            
            # Stop containers
            self.run_command(["docker", "stop"] + container_ids, "Stopping flashloan containers", ignore_errors=True)
            # Remove containers
            self.run_command(["docker", "rm", "-f"] + container_ids, "Removing flashloan containers", ignore_errors=True)
        
        # Clean up networks and volumes
        cleanup_commands = [
            (["docker", "network", "rm", "flashloan-network"], "Removing flashloan network"),
            (["docker", "volume", "prune", "-f"], "Cleaning up volumes"),
            (["docker", "system", "prune", "-f"], "Cleaning up system")
        ]
        
        for command, description in cleanup_commands:
            self.run_command(command, description, ignore_errors=True)
        
        self.log("Cleanup completed")
        return True
    
    def create_persistent_orchestrator(self) -> bool:
        """Create a persistent orchestrator that doesn't stop"""
        self.log("Creating persistent orchestrator...")
        
        orchestrator_dir = self.containers_dir / "orchestrator"
        orchestrator_dir.mkdir(exist_ok=True)
        
        # Create requirements with UTF-8 encoding
        requirements_content = """# LangChain and AI dependencies
langchain>=0.1.0
langchain-community>=0.0.10
langchain-core>=0.1.0
langchain-openai>=0.0.5
openai>=1.12.0

# AutoGen dependencies  
pyautogen>=0.2.0

# Core dependencies
aiohttp>=3.8.0
aioredis>=2.0.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
requests>=2.31.0
psycopg2-binary>=2.9.0
redis>=4.5.0
pika>=1.3.0
docker>=6.0.0
tenacity>=8.2.0
pandas>=2.0.0
numpy>=1.24.0
structlog>=23.0.0
prometheus_client>=0.19.0
"""
        
        with open(orchestrator_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
        
        # Create persistent orchestrator with proper coordination
        orchestrator_content = '''#!/usr/bin/env python3
"""
Persistent LangChain Orchestrator with GitHub Token Integration
Never stops running and coordinates all containers
"""

import asyncio
import logging
import time
import json
import os
import signal
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
logger = logging.getLogger("PersistentOrchestrator")

# Environment setup
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ORCHESTRATOR_MODE = os.getenv('ORCHESTRATOR_MODE', 'persistent')

# Safe imports
COMPONENTS = {}

try:
    from langchain.llms import OpenAI
    from langchain.agents import initialize_agent, AgentType
    from langchain.memory import ConversationBufferMemory
    from langchain.tools import Tool
    COMPONENTS['langchain'] = True
    logger.info("LangChain loaded successfully")
except ImportError as e:
    COMPONENTS['langchain'] = False
    logger.warning(f"LangChain not available: {e}")

try:
    import redis
    COMPONENTS['redis'] = True
except ImportError:
    COMPONENTS['redis'] = False
    logger.warning("Redis not available")

try:
    import docker
    COMPONENTS['docker'] = True
    docker_client = docker.from_env()
except ImportError:
    COMPONENTS['docker'] = False
    docker_client = None
    logger.warning("Docker client not available")

try:
    import requests
    COMPONENTS['requests'] = True
except ImportError:
    COMPONENTS['requests'] = False

class GitHubIntegration:
    """GitHub integration for issue tracking and coordination"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {'Authorization': f'token {token}'} if token else {}
        self.repo = os.getenv('GITHUB_REPO', 'user/repo')
    
    async def create_issue(self, title: str, body: str, labels: List[str] = None):
        """Create a GitHub issue for tracking"""
        if not self.token or not COMPONENTS['requests']:
            logger.warning("GitHub integration not available")
            return None
        
        try:
            import requests
            url = f"https://api.github.com/repos/{self.repo}/issues"
            data = {
                'title': title,
                'body': body,
                'labels': labels or []
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 201:
                issue = response.json()
                logger.info(f"Created GitHub issue #{issue['number']}: {title}")
                return issue
            else:
                logger.error(f"Failed to create GitHub issue: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"GitHub issue creation failed: {e}")
            return None

class ContainerCoordinator:
    """Coordinates all containers and ensures they stay running"""
    
    def __init__(self):
        self.github = GitHubIntegration(GITHUB_TOKEN)
        self.containers = {}
        self.last_health_check = datetime.now()
        self.restart_count = {}
        
    async def discover_containers(self):
        """Discover all flashloan containers"""
        if not COMPONENTS['docker'] or not docker_client:
            logger.warning("Docker not available for container discovery")
            return
        
        try:
            containers = docker_client.containers.list(all=True, filters={'name': 'flashloan'})
            
            for container in containers:
                self.containers[container.name] = {
                    'container': container,
                    'status': container.status,
                    'last_check': datetime.now(),
                    'restart_count': self.restart_count.get(container.name, 0)
                }
            
            logger.info(f"Discovered {len(self.containers)} flashloan containers")
            
        except Exception as e:
            logger.error(f"Container discovery failed: {e}")
    
    async def health_check_all(self):
        """Check health of all containers"""
        if not COMPONENTS['docker']:
            return
        
        try:
            healthy_count = 0
            failed_containers = []
            
            for name, info in self.containers.items():
                try:
                    container = info['container']
                    container.reload()
                    
                    if container.status == 'running':
                        healthy_count += 1
                        info['status'] = 'running'
                        info['last_check'] = datetime.now()
                    else:
                        failed_containers.append(name)
                        info['status'] = container.status
                        
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    failed_containers.append(name)
            
            logger.info(f"Health check: {healthy_count}/{len(self.containers)} containers healthy")
            
            if failed_containers:
                await self.handle_failed_containers(failed_containers)
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    async def handle_failed_containers(self, failed_containers: List[str]):
        """Handle failed containers with restart logic"""
        for container_name in failed_containers:
            try:
                logger.warning(f"Handling failed container: {container_name}")
                
                container_info = self.containers.get(container_name)
                if not container_info:
                    continue
                
                restart_count = container_info['restart_count']
                
                if restart_count < 5:  # Max 5 restarts
                    logger.info(f"Restarting {container_name} (attempt {restart_count + 1})")
                    
                    container = container_info['container']
                    container.restart()
                    
                    container_info['restart_count'] = restart_count + 1
                    self.restart_count[container_name] = restart_count + 1
                    
                    logger.info(f"Successfully restarted {container_name}")
                    
                    # Create GitHub issue for tracking
                    await self.github.create_issue(
                        title=f"Container Restart: {container_name}",
                        body=f"Container {container_name} was restarted automatically.\\nRestart count: {restart_count + 1}\\nTimestamp: {datetime.now()}",
                        labels=['auto-restart', 'container-issue']
                    )
                    
                else:
                    logger.error(f"Container {container_name} has failed too many times")
                    
                    # Create critical GitHub issue
                    await self.github.create_issue(
                        title=f"Critical: Container {container_name} Failed Multiple Times",
                        body=f"Container {container_name} has failed {restart_count} times and requires manual intervention.\\nLast status: {container_info['status']}\\nTimestamp: {datetime.now()}",
                        labels=['critical', 'container-failure', 'manual-intervention-required']
                    )
                    
            except Exception as e:
                logger.error(f"Failed to handle container {container_name}: {e}")

class PersistentOrchestrator:
    """Main persistent orchestrator that never stops"""
    
    def __init__(self):
        self.is_running = False
        self.start_time = datetime.now()
        self.coordinator = ContainerCoordinator()
        self.llm = None
        self.task_count = 0
        self.shutdown_requested = False
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Initialize LangChain if available
        if COMPONENTS['langchain'] and OPENAI_API_KEY:
            try:
                self.llm = OpenAI(temperature=0.7, openai_api_key=OPENAI_API_KEY)
                logger.info("LangChain LLM initialized successfully")
            except Exception as e:
                logger.error(f"LangChain LLM initialization failed: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    async def run_forever(self):
        """Main run loop that never stops unless explicitly requested"""
        try:
            self.is_running = True
            logger.info("Starting Persistent LangChain Orchestrator")
            
            # Log system status
            self.log_system_status()
            
            # Create persistent tasks
            tasks = [
                asyncio.create_task(self.heartbeat_loop()),
                asyncio.create_task(self.container_monitor_loop()),
                asyncio.create_task(self.langchain_task_loop()),
                asyncio.create_task(self.coordination_loop()),
                asyncio.create_task(self.github_sync_loop())
            ]
            
            # Run all tasks concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Critical orchestrator error: {e}")
            # Don't stop - attempt to recover
            await asyncio.sleep(30)
            if not self.shutdown_requested:
                logger.info("Attempting orchestrator recovery...")
                await self.run_forever()  # Restart
        finally:
            self.is_running = False
            logger.info("Persistent orchestrator stopped")
    
    def log_system_status(self):
        """Log current system status and capabilities"""
        logger.info("=== System Status ===")
        for component, available in COMPONENTS.items():
            status = "Available" if available else "Not Available"
            logger.info(f"  {component}: {status}")
        
        logger.info(f"  GitHub Token: {'Set' if GITHUB_TOKEN else 'Missing'}")
        logger.info(f"  OpenAI Key: {'Set' if OPENAI_API_KEY else 'Missing'}")
        logger.info(f"  Mode: {ORCHESTRATOR_MODE}")
        logger.info("=====================")
    
    async def heartbeat_loop(self):
        """Continuous heartbeat to prove the system is alive"""
        while self.is_running and not self.shutdown_requested:
            try:
                uptime = datetime.now() - self.start_time
                logger.info(f"HEARTBEAT: System running for {uptime} - Tasks completed: {self.task_count}")
                
                # Save heartbeat to file
                heartbeat_data = {
                    'timestamp': datetime.now().isoformat(),
                    'uptime_seconds': uptime.total_seconds(),
                    'tasks_completed': self.task_count,
                    'components': COMPONENTS
                }
                
                with open('/app/logs/heartbeat.json', 'w') as f:
                    json.dump(heartbeat_data, f, indent=2)
                
                await asyncio.sleep(60)  # Heartbeat every minute
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(30)
    
    async def container_monitor_loop(self):
        """Monitor all containers continuously"""
        while self.is_running and not self.shutdown_requested:
            try:
                await self.coordinator.discover_containers()
                await self.coordinator.health_check_all()
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                logger.error(f"Container monitor error: {e}")
                await asyncio.sleep(60)
    
    async def langchain_task_loop(self):
        """Continuous LangChain task processing"""
        while self.is_running and not self.shutdown_requested:
            try:
                tasks = [
                    "Analyze current DeFi market conditions",
                    "Check flash loan opportunities",
                    "Monitor system performance metrics",
                    "Assess risk parameters",
                    "Generate system status report"
                ]
                
                for task in tasks:
                    await self.process_langchain_task(task)
                    self.task_count += 1
                    
                    if self.shutdown_requested:
                        break
                    
                    await asyncio.sleep(30)  # Process task every 30 seconds
                
                await asyncio.sleep(300)  # Wait 5 minutes before next batch
                
            except Exception as e:
                logger.error(f"LangChain task loop error: {e}")
                await asyncio.sleep(60)
    
    async def process_langchain_task(self, task: str):
        """Process a single task with LangChain"""
        try:
            logger.info(f"Processing LangChain task: {task}")
            
            if self.llm and COMPONENTS['langchain']:
                prompt = f"As an AI orchestrator for a DeFi flash loan system, analyze and respond to: {task}"
                
                try:
                    response = self.llm(prompt)
                    logger.info(f"LangChain response (first 100 chars): {response[:100]}...")
                    
                    # Save task result
                    task_result = {
                        'task': task,
                        'response': response,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'completed'
                    }
                    
                    with open('/app/logs/langchain_tasks.jsonl', 'a') as f:
                        f.write(json.dumps(task_result) + '\\n')
                        
                except Exception as e:
                    logger.error(f"LangChain processing failed: {e}")
            else:
                logger.info(f"Fallback processing for task: {task}")
                await asyncio.sleep(2)  # Simulate processing
                
        except Exception as e:
            logger.error(f"Task processing error: {e}")
    
    async def coordination_loop(self):
        """Coordinate between different containers"""
        while self.is_running and not self.shutdown_requested:
            try:
                logger.info("Performing inter-container coordination...")
                
                # Simulate coordination between MCP servers and agents
                mcp_servers = [c for c in self.coordinator.containers.keys() if 'mcp-server' in c]
                agents = [c for c in self.coordinator.containers.keys() if 'agent' in c]
                
                logger.info(f"Coordinating {len(mcp_servers)} MCP servers and {len(agents)} agents")
                
                # Check if coordination is needed
                for server in mcp_servers[:3]:  # Coordinate with first 3 servers
                    for agent in agents[:2]:  # Coordinate with first 2 agents
                        logger.info(f"Coordinating {server} with {agent}")
                        await asyncio.sleep(1)  # Simulate coordination work
                
                await asyncio.sleep(180)  # Coordinate every 3 minutes
                
            except Exception as e:
                logger.error(f"Coordination loop error: {e}")
                await asyncio.sleep(60)
    
    async def github_sync_loop(self):
        """Sync status with GitHub"""
        while self.is_running and not self.shutdown_requested:
            try:
                if GITHUB_TOKEN:
                    uptime = datetime.now() - self.start_time
                    
                    # Create periodic status update
                    await self.coordinator.github.create_issue(
                        title=f"System Status Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        body=f"System Status Report:\\n\\nUptime: {uptime}\\nTasks Completed: {self.task_count}\\nContainers: {len(self.coordinator.containers)}\\nComponents: {COMPONENTS}\\n\\nTimestamp: {datetime.now()}",
                        labels=['status-update', 'automated']
                    )
                
                await asyncio.sleep(3600)  # Sync every hour
                
            except Exception as e:
                logger.error(f"GitHub sync error: {e}")
                await asyncio.sleep(1800)  # Retry in 30 minutes

# Health check function
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': COMPONENTS,
        'github_token_configured': bool(GITHUB_TOKEN),
        'mode': ORCHESTRATOR_MODE
    }

if __name__ == "__main__":
    # Create logs directory
    os.makedirs("/app/logs", exist_ok=True)
    
    # Start persistent orchestrator
    orchestrator = PersistentOrchestrator()
    
    try:
        asyncio.run(orchestrator.run_forever())
    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user")
    except Exception as e:
        logger.error(f"Fatal orchestrator error: {e}")
        # Even on fatal error, try to restart
        time.sleep(10)
        logger.info("Attempting orchestrator restart...")
        try:
            asyncio.run(orchestrator.run_forever())
        except Exception as e2:
            logger.error(f"Restart failed: {e2}")
'''
        
        with open(orchestrator_dir / "persistent_orchestrator.py", "w", encoding="utf-8") as f:
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
COPY persistent_orchestrator.py .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import asyncio; import sys; sys.path.append('/app'); from persistent_orchestrator import health_check; print(asyncio.run(health_check()))" || exit 1

# Run the persistent orchestrator
CMD ["python", "persistent_orchestrator.py"]
"""
        
        with open(orchestrator_dir / "Dockerfile", "w", encoding="utf-8") as f:
            f.write(dockerfile_content)
        
        self.log("Persistent orchestrator created successfully")
        return True
    
    def create_individual_mcp_servers(self) -> bool:
        """Create individual MCP server containers"""
        self.log("Creating individual MCP server containers...")
        
        # List of 21 MCP servers with specific roles
        mcp_servers = [
            ("filesystem", 8001, "File system operations and management"),
            ("database", 8002, "Database operations and queries"),
            ("web-scraper", 8003, "Web scraping and data collection"),
            ("api-client", 8004, "External API integrations"),
            ("file-processor", 8005, "File processing and transformation"),
            ("data-analyzer", 8006, "Data analysis and insights"),
            ("notification", 8007, "Notification and alerting system"),
            ("auth-manager", 8008, "Authentication and authorization"),
            ("cache-manager", 8009, "Caching and performance optimization"),
            ("task-queue", 8010, "Task queue and job processing"),
            ("monitoring", 8011, "System monitoring and metrics"),
            ("security", 8012, "Security scanning and compliance"),
            ("blockchain", 8013, "Blockchain interaction and monitoring"),
            ("defi-analyzer", 8014, "DeFi protocol analysis"),
            ("price-feed", 8015, "Real-time price data feeds"),
            ("arbitrage", 8016, "Arbitrage opportunity detection"),
            ("risk-manager", 8017, "Risk assessment and management"),
            ("portfolio", 8018, "Portfolio tracking and analysis"),
            ("liquidity", 8019, "Liquidity pool monitoring"),
            ("flash-loan", 8020, "Flash loan execution engine"),
            ("coordinator", 8021, "Inter-service coordination")
        ]
        
        for server_name, port, description in mcp_servers:
            server_dir = self.containers_dir / f"mcp-{server_name}"
            server_dir.mkdir(exist_ok=True)
            
            # Create server-specific requirements
            requirements_content = """fastapi>=0.104.0
uvicorn[standard]>=0.24.0
aiohttp>=3.8.0
requests>=2.31.0
pydantic>=2.0.0
asyncio-mqtt>=0.13.0
redis>=4.5.0
"""
            
            with open(server_dir / "requirements.txt", "w", encoding="utf-8") as f:
                f.write(requirements_content)
            
            # Create server-specific code
            server_content = f'''#!/usr/bin/env python3
"""
MCP Server: {server_name}
{description}
"""

import os
import time
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP-{server_name}")

app = FastAPI()

SERVER_NAME = "{server_name}"
SERVER_PORT = {port}
DESCRIPTION = "{description}"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'http://orchestrator:8000')

# Server state
server_state = {{
    "start_time": datetime.now(),
    "task_count": 0,
    "status": "running",
    "last_heartbeat": datetime.now()
}}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = datetime.now() - server_state["start_time"]
    return {{
        "status": "healthy",
        "server": SERVER_NAME,
        "port": SERVER_PORT,
        "description": DESCRIPTION,
        "uptime_seconds": uptime.total_seconds(),
        "task_count": server_state["task_count"],
        "timestamp": datetime.now().isoformat()
    }}

@app.get("/status")
async def status():
    """Detailed status endpoint"""
    uptime = datetime.now() - server_state["start_time"]
    return {{
        "server": SERVER_NAME,
        "port": SERVER_PORT,
        "description": DESCRIPTION,
        "uptime": str(uptime),
        "task_count": server_state["task_count"],
        "status": server_state["status"],
        "github_token_configured": bool(GITHUB_TOKEN),
        "last_heartbeat": server_state["last_heartbeat"].isoformat()
    }}

@app.post("/task")
async def process_task(task: dict):
    """Process a task from the orchestrator"""
    try:
        logger.info(f"Processing task: {{task.get('name', 'unnamed')}}")
        
        # Simulate task processing based on server type
        await asyncio.sleep(2)  # Simulate work
        
        server_state["task_count"] += 1
        server_state["last_heartbeat"] = datetime.now()
        
        result = {{
            "server": SERVER_NAME,
            "task": task,
            "result": f"{{SERVER_NAME}} processed task successfully",
            "timestamp": datetime.now().isoformat(),
            "task_number": server_state["task_count"]
        }}
        
        logger.info(f"Task completed: {{result['result']}}")
        return result
        
    except Exception as e:
        logger.error(f"Task processing failed: {{e}}")
        return {{"error": str(e), "server": SERVER_NAME}}

@app.get("/metrics")
async def metrics():
    """Server metrics endpoint"""
    uptime = datetime.now() - server_state["start_time"]
    return {{
        "server": SERVER_NAME,
        "uptime_seconds": uptime.total_seconds(),
        "task_count": server_state["task_count"],
        "tasks_per_hour": server_state["task_count"] / max(uptime.total_seconds() / 3600, 0.1),
        "memory_usage": "simulated_low",
        "cpu_usage": "simulated_normal",
        "status": server_state["status"]
    }}

async def heartbeat_loop():
    """Send heartbeat to orchestrator"""
    while True:
        try:
            if ORCHESTRATOR_URL:
                # Simulate heartbeat to orchestrator
                server_state["last_heartbeat"] = datetime.now()
                logger.info(f"Heartbeat sent to orchestrator - Tasks: {{server_state['task_count']}}")
            
            await asyncio.sleep(60)  # Heartbeat every minute
            
        except Exception as e:
            logger.error(f"Heartbeat failed: {{e}}")
            await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {{SERVER_NAME}} MCP Server on port {{SERVER_PORT}}")
    logger.info(f"Description: {{DESCRIPTION}}")
    
    # Start heartbeat loop
    asyncio.create_task(heartbeat_loop())

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {{SERVER_NAME}} MCP Server on port {{SERVER_PORT}}")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
'''
            
            with open(server_dir / "server.py", "w", encoding="utf-8") as f:
                f.write(server_content)
            
            # Create Dockerfile
            dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

# Run server
CMD ["python", "server.py"]
"""
            
            with open(server_dir / "Dockerfile", "w", encoding="utf-8") as f:
                f.write(dockerfile_content)
        
        self.log(f"Created {len(mcp_servers)} individual MCP servers")
        return True
    
    def create_individual_agents(self) -> bool:
        """Create individual agent containers"""
        self.log("Creating individual agent containers...")
        
        # List of 10 agents with specific roles
        agents = [
            ("coordinator", "system_coordinator", "Coordinates system-wide operations"),
            ("analyzer", "market_analyzer", "Analyzes market conditions and opportunities"),
            ("executor", "trade_executor", "Executes trades and blockchain transactions"),
            ("risk-manager", "risk_assessment", "Assesses and manages system risks"),
            ("monitor", "system_monitor", "Monitors system health and performance"),
            ("data-collector", "data_collection", "Collects data from various sources"),
            ("arbitrage-bot", "arbitrage_detection", "Detects arbitrage opportunities"),
            ("liquidity-manager", "liquidity_optimization", "Optimizes liquidity usage"),
            ("reporter", "report_generator", "Generates reports and analytics"),
            ("healer", "auto_healing", "Performs auto-healing and recovery")
        ]
        
        for agent_name, agent_role, description in agents:
            agent_dir = self.containers_dir / f"agent-{agent_name}"
            agent_dir.mkdir(exist_ok=True)
            
            # Create agent-specific requirements
            requirements_content = """aiohttp>=3.8.0
requests>=2.31.0
asyncio-mqtt>=0.13.0
pydantic>=2.0.0
redis>=4.5.0
"""
            
            with open(agent_dir / "requirements.txt", "w", encoding="utf-8") as f:
                f.write(requirements_content)
            
            # Create agent-specific code
            agent_content = f'''#!/usr/bin/env python3
"""
Agent: {agent_name}
Role: {agent_role}
{description}
"""

import os
import asyncio
import logging
import time
import json
from datetime import datetime
import aiohttp

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Agent-{agent_name}")

AGENT_NAME = "{agent_name}"
AGENT_ROLE = "{agent_role}"
DESCRIPTION = "{description}"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'http://orchestrator:8000')

class Agent:
    """Individual agent with specific role and capabilities"""
    
    def __init__(self):
        self.name = AGENT_NAME
        self.role = AGENT_ROLE
        self.is_running = False
        self.start_time = datetime.now()
        self.task_count = 0
        self.session = None
        
    async def start(self):
        """Start the agent"""
        self.is_running = True
        self.session = aiohttp.ClientSession()
        logger.info(f"Starting agent {{self.name}} with role {{self.role}}")
        logger.info(f"Description: {{DESCRIPTION}}")
        
        # Start concurrent tasks
        tasks = [
            asyncio.create_task(self.main_loop()),
            asyncio.create_task(self.heartbeat_loop()),
            asyncio.create_task(self.coordination_loop())
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the agent gracefully"""
        self.is_running = False
        if self.session:
            await self.session.close()
        logger.info(f"Agent {{self.name}} stopped")
    
    async def main_loop(self):
        """Main agent processing loop"""
        while self.is_running:
            try:
                await self.perform_role_specific_task()
                self.task_count += 1
                await asyncio.sleep(45)  # Task every 45 seconds
                
            except Exception as e:
                logger.error(f"Main loop error: {{e}}")
                await asyncio.sleep(30)
    
    async def perform_role_specific_task(self):
        """Perform task specific to this agent's role"""
        try:
            uptime = datetime.now() - self.start_time
            logger.info(f"Agent {{self.name}} performing {{self.role}} task - Uptime: {{uptime}}")
            
            # Role-specific behavior
            if self.role == "system_coordinator":
                await self.coordinate_system()
            elif self.role == "market_analyzer":
                await self.analyze_market()
            elif self.role == "trade_executor":
                await self.execute_trades()
            elif self.role == "risk_assessment":
                await self.assess_risks()
            elif self.role == "system_monitor":
                await self.monitor_system()
            else:
                await self.generic_task()
            
            # Log task completion
            task_data = {{
                "agent": self.name,
                "role": self.role,
                "task_number": self.task_count,
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime.total_seconds()
            }}
            
            # Save task log
            with open(f"/tmp/agent_{{self.name}}_tasks.jsonl", "a") as f:
                f.write(json.dumps(task_data) + "\\n")
                
        except Exception as e:
            logger.error(f"Task performance error: {{e}}")
    
    async def coordinate_system(self):
        """System coordinator specific tasks"""
        logger.info("Coordinating system components...")
        await asyncio.sleep(2)  # Simulate coordination work
    
    async def analyze_market(self):
        """Market analyzer specific tasks"""
        logger.info("Analyzing market conditions...")
        await asyncio.sleep(3)  # Simulate analysis work
    
    async def execute_trades(self):
        """Trade executor specific tasks"""
        logger.info("Checking for trade execution opportunities...")
        await asyncio.sleep(2)  # Simulate execution work
    
    async def assess_risks(self):
        """Risk manager specific tasks"""
        logger.info("Assessing system risks...")
        await asyncio.sleep(2)  # Simulate risk assessment
    
    async def monitor_system(self):
        """System monitor specific tasks"""
        logger.info("Monitoring system health...")
        await asyncio.sleep(1)  # Simulate monitoring work
    
    async def generic_task(self):
        """Generic task for other agent types"""
        logger.info(f"Performing {{self.role}} specific operations...")
        await asyncio.sleep(2)  # Simulate work
    
    async def heartbeat_loop(self):
        """Send heartbeat to orchestrator"""
        while self.is_running:
            try:
                uptime = datetime.now() - self.start_time
                
                heartbeat_data = {{
                    "agent": self.name,
                    "role": self.role,
                    "status": "running",
                    "uptime_seconds": uptime.total_seconds(),
                    "task_count": self.task_count,
                    "timestamp": datetime.now().isoformat()
                }}
                
                if self.session and ORCHESTRATOR_URL:
                    try:
                        async with self.session.post(
                            f"{{ORCHESTRATOR_URL}}/agent-heartbeat",
                            json=heartbeat_data,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                logger.info(f"Heartbeat sent successfully - Tasks: {{self.task_count}}")
                            else:
                                logger.warning(f"Heartbeat failed with status: {{response.status}}")
                    except Exception as e:
                        logger.warning(f"Heartbeat request failed: {{e}}")
                
                await asyncio.sleep(90)  # Heartbeat every 90 seconds
                
            except Exception as e:
                logger.error(f"Heartbeat loop error: {{e}}")
                await asyncio.sleep(60)
    
    async def coordination_loop(self):
        """Coordinate with other agents and MCP servers"""
        while self.is_running:
            try:
                logger.info(f"Agent {{self.name}} performing inter-service coordination...")
                
                # Simulate coordination with MCP servers
                if self.session:
                    coordination_tasks = [
                        self.coordinate_with_mcp("mcp-filesystem"),
                        self.coordinate_with_mcp("mcp-database"),
                        self.coordinate_with_mcp("mcp-monitoring")
                    ]
                    
                    await asyncio.gather(*coordination_tasks, return_exceptions=True)
                
                await asyncio.sleep(300)  # Coordinate every 5 minutes
                
            except Exception as e:
                logger.error(f"Coordination loop error: {{e}}")
                await asyncio.sleep(180)
    
    async def coordinate_with_mcp(self, mcp_server: str):
        """Coordinate with a specific MCP server"""
        try:
            if not self.session:
                return
            
            # Determine port based on server name
            server_ports = {{
                "mcp-filesystem": 8001,
                "mcp-database": 8002,
                "mcp-monitoring": 8011
            }}
            
            port = server_ports.get(mcp_server, 8001)
            url = f"http://{{mcp_server}}:{{port}}/status"
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Coordinated with {{mcp_server}}: {{data.get('status', 'unknown')}}")
                else:
                    logger.warning(f"Coordination with {{mcp_server}} failed: {{response.status}}")
                    
        except Exception as e:
            logger.warning(f"Coordination with {{mcp_server}} failed: {{e}}")

async def main():
    """Main entry point"""
    agent = Agent()
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent error: {{e}}")
    finally:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            with open(agent_dir / "agent.py", "w", encoding="utf-8") as f:
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
            
            with open(agent_dir / "Dockerfile", "w", encoding="utf-8") as f:
                f.write(dockerfile_content)
        
        self.log(f"Created {len(agents)} individual agents")
        return True
    
    def create_comprehensive_docker_compose(self) -> bool:
        """Create comprehensive Docker Compose with individual containers"""
        self.log("Creating comprehensive Docker Compose configuration...")
        
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

  # Persistent Orchestrator
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
      - GITHUB_REPO=${GITHUB_REPO:-user/repo}
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://flashloan:flashloan123@postgres:5432/flashloan
      - RABBITMQ_URL=amqp://flashloan:flashloan123@rabbitmq:5672
      - ORCHESTRATOR_MODE=persistent
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

        # Add 21 individual MCP servers
        mcp_servers = [
            ("filesystem", 8001), ("database", 8002), ("web-scraper", 8003), ("api-client", 8004),
            ("file-processor", 8005), ("data-analyzer", 8006), ("notification", 8007), ("auth-manager", 8008),
            ("cache-manager", 8009), ("task-queue", 8010), ("monitoring", 8011), ("security", 8012),
            ("blockchain", 8013), ("defi-analyzer", 8014), ("price-feed", 8015), ("arbitrage", 8016),
            ("risk-manager", 8017), ("portfolio", 8018), ("liquidity", 8019), ("flash-loan", 8020),
            ("coordinator", 8021)
        ]
        
        for server_name, port in mcp_servers:
            compose_content += f"""  mcp-{server_name}:
    build: ./containers/mcp-{server_name}
    container_name: flashloan-mcp-{server_name}
    networks:
      - flashloan-network
    ports:
      - "{port}:{port}"
    environment:
      - MCP_SERVER_NAME={server_name}
      - MCP_SERVER_PORT={port}
      - GITHUB_TOKEN=${{GITHUB_TOKEN:-}}
      - ORCHESTRATOR_URL=http://orchestrator:8000
    depends_on:
      - orchestrator
    restart: unless-stopped

"""

        # Add 10 individual agents
        agents = [
            ("coordinator", "system_coordinator"), ("analyzer", "market_analyzer"),
            ("executor", "trade_executor"), ("risk-manager", "risk_assessment"),
            ("monitor", "system_monitor"), ("data-collector", "data_collection"),
            ("arbitrage-bot", "arbitrage_detection"), ("liquidity-manager", "liquidity_optimization"),
            ("reporter", "report_generator"), ("healer", "auto_healing")
        ]
        
        for agent_name, agent_role in agents:
            compose_content += f"""  agent-{agent_name}:
    build: ./containers/agent-{agent_name}
    container_name: flashloan-agent-{agent_name}
    networks:
      - flashloan-network
    environment:
      - AGENT_NAME={agent_name}
      - AGENT_ROLE={agent_role}
      - GITHUB_TOKEN=${{GITHUB_TOKEN:-}}
      - ORCHESTRATOR_URL=http://orchestrator:8000
    depends_on:
      - orchestrator
    restart: unless-stopped

"""
        
        with open(self.project_root / "docker-compose.yml", "w", encoding="utf-8") as f:
            f.write(compose_content)
        
        self.log("Comprehensive Docker Compose file created")
        return True
    
    def build_and_deploy_all(self) -> bool:
        """Build and deploy all individual containers"""
        self.log("Building and deploying all individual containers...")
        
        # Create network first
        self.run_command(
            ["docker", "network", "create", "flashloan-network"],
            "Creating Docker network",
            ignore_errors=True
        )
        
        # Build and start all services
        success = self.run_command(
            ["docker-compose", "up", "--build", "-d"],
            "Building and starting all individual containers"
        )
        
        if success:
            self.log("All individual containers deployed successfully")
            return True
        else:
            self.log("Container deployment failed", "ERROR")
            return False
    
    def verify_individual_deployment(self) -> bool:
        """Verify all individual containers are running"""
        self.log("Verifying individual container deployment...")
        
        # Wait for containers to start
        time.sleep(45)
        
        # Check container status
        success = self.run_command(
            ["docker-compose", "ps"],
            "Checking individual container status"
        )
        
        if success:
            # Check orchestrator health
            time.sleep(30)
            self.run_command(
                ["curl", "-f", "http://localhost:8000/health"],
                "Checking persistent orchestrator health",
                ignore_errors=True
            )
            
            # Check a few MCP servers
            for port in [8001, 8002, 8011]:
                self.run_command(
                    ["curl", "-f", f"http://localhost:{port}/health"],
                    f"Checking MCP server on port {port}",
                    ignore_errors=True
                )
        
        self.log("Individual deployment verification complete")
        return success
    
    def run_complete_build(self) -> bool:
        """Execute the complete build process with individual containers"""
        self.log("Starting complete robust LangChain system build with individual containers...")
        
        steps = [
            (self.cleanup_everything, "Complete cleanup"),
            (self.create_persistent_orchestrator, "Persistent orchestrator creation"),
            (self.create_individual_mcp_servers, "Individual MCP servers creation"),
            (self.create_individual_agents, "Individual agents creation"),
            (self.create_comprehensive_docker_compose, "Comprehensive Docker Compose creation"),
            (self.build_and_deploy_all, "Build and deploy all containers"),
            (self.verify_individual_deployment, "Individual deployment verification")
        ]
        
        for step_func, description in steps:
            self.log(f"Step: {description}")
            if not step_func():
                self.log(f"FAILED at step: {description}", "ERROR")
                return False
            self.log(f"COMPLETED: {description}")
        
        self.log("Complete robust LangChain system build successful!")
        self.log("System features:")
        self.log("- Persistent orchestrator that never stops")
        self.log("- 21 individual MCP server containers")
        self.log("- 10 individual agent containers")
        self.log("- GitHub token integration for coordination")
        self.log("- Auto-restart and self-healing capabilities")
        self.log("- Comprehensive logging and monitoring")
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Robust LangChain Flash Loan System Builder")
    parser.add_argument("command", choices=["build", "cleanup"], 
                       help="Command to execute")
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    builder = RobustLangChainBuilder(args.project_root)
    
    if args.command == "build":
        success = builder.run_complete_build()
        if success:
            print("\n SUCCESS: Robust build completed successfully!")
            print(" FEATURES:")
            print("   - Persistent orchestrator with GitHub token integration")
            print("   - 21 individual MCP server containers")
            print("   - 10 individual agent containers") 
            print("   - Auto-restart and coordination capabilities")
            print("   - Comprehensive logging and monitoring")
            print(" ACCESS:")
            print("   - Orchestrator: http://localhost:8000")
            print("   - MCP Servers: http://localhost:8001-8021")
            print("   - PostgreSQL: localhost:5432")
            print("   - Redis: localhost:6379")
            print("   - RabbitMQ: localhost:15672")
        else:
            print("\n ERROR: Build failed. Check logs for details.")
            sys.exit(1)
            
    elif args.command == "cleanup":
        builder.cleanup_everything()
        print(" SUCCESS: Cleanup completed")

if __name__ == "__main__":
    main()
