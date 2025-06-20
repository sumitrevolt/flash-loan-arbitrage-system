#!/usr/bin/env python3
"""
Comprehensive LangChain Flash Loan System Builder & Launcher
Clean version with proper encoding and error handling
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from typing import List
from datetime import datetime

class LangChainSystemBuilder:
    """Complete system builder with cleanup, build, and deployment"""
    
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.containers_dir = self.project_root / "containers"
        self.logs_dir = self.project_root / "logs"
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.log_file = self.logs_dir / f"langchain_builder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str, level: str = "INFO"):
        """Log message to both console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {level} - {message}"
        print(log_entry)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, command: List[str], description: str, ignore_errors: bool = False) -> bool:
        """Execute a command with proper error handling"""
        self.log(f"Running {description}...")
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
                self.log(f"Success: {description}")
                if result.stdout.strip():
                    self.log(f"Output: {result.stdout.strip()}")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                if ignore_errors:
                    self.log(f"Warning: {description} failed (ignored): {error_msg}", "WARNING")
                    return True
                else:
                    self.log(f"Error: {description} failed: {error_msg}", "ERROR")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.log(f"Timeout: {description} timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Exception: {description} raised: {str(e)}", "ERROR")
            return False
    
    def complete_cleanup(self) -> bool:
        """Clean up all existing containers and resources"""
        self.log("Starting complete cleanup...")
        
        # Stop and remove all flashloan containers
        containers = subprocess.run(
            ["docker", "ps", "-aq", "--filter", "name=flashloan"],
            capture_output=True, text=True
        )
        if containers.stdout.strip():
            self.run_command(
                ["docker", "stop"] + containers.stdout.strip().split(),
                "Stopping flashloan containers", ignore_errors=True
            )
            self.run_command(
                ["docker", "rm", "-f"] + containers.stdout.strip().split(),
                "Removing flashloan containers", ignore_errors=True
            )
        
        # Remove network
        self.run_command(
            ["docker", "network", "rm", "flashloan-network"],
            "Removing flashloan network", ignore_errors=True
        )
        
        # Clean up volumes and system
        self.run_command(["docker", "volume", "prune", "-f"], "Cleaning volumes", ignore_errors=True)
        self.run_command(["docker", "system", "prune", "-f"], "Cleaning system", ignore_errors=True)
        
        self.log("Cleanup completed")
        return True
    
    def setup_directories(self) -> bool:
        """Set up the directory structure"""
        self.log("Setting up directory structure...")
        
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
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            self.log(f"Created: {dir_name}")
        
        self.log("Directory structure created")
        return True
    
    def create_orchestrator_files(self) -> bool:
        """Create orchestrator container files"""
        self.log("Creating orchestrator files...")
        
        orchestrator_dir = self.containers_dir / "orchestrator"
        
        # Main orchestrator Python file
        orchestrator_content = '''#!/usr/bin/env python3
"""
Robust Flash Loan Orchestrator with Auto-Healing
"""

import asyncio
import logging
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any
import docker
import requests

class RobustOrchestrator:
    """Main orchestrator with health monitoring and auto-healing"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.services = {}
        self.health_check_interval = 30
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/logs/orchestrator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Start the orchestrator"""
        self.logger.info("Starting Flash Loan Orchestrator...")
        
        # Initialize services
        await self.initialize_services()
        
        # Start health monitoring
        await self.start_health_monitoring()
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            self.logger.info("Orchestrator running...")
    
    async def initialize_services(self):
        """Initialize all services"""
        self.logger.info("Initializing services...")
        
        # Register services
        self.services = {
            'mcp-servers': {'health_endpoint': 'http://mcp-servers:8000/health'},
            'agents': {'health_endpoint': 'http://agents:8001/health'}
        }
        
        self.logger.info(f"Registered {len(self.services)} services")
    
    async def start_health_monitoring(self):
        """Start health monitoring loop"""
        asyncio.create_task(self.health_monitor_loop())
        
    async def health_monitor_loop(self):
        """Main health monitoring loop"""
        while True:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)
    
    async def check_all_services(self):
        """Check health of all services"""
        for service_name, config in self.services.items():
            try:
                response = requests.get(config['health_endpoint'], timeout=10)
                if response.status_code == 200:
                    self.logger.debug(f"Service {service_name} is healthy")
                else:
                    self.logger.warning(f"Service {service_name} returned {response.status_code}")
                    await self.heal_service(service_name)
            except Exception as e:
                self.logger.error(f"Service {service_name} health check failed: {e}")
                await self.heal_service(service_name)
    
    async def heal_service(self, service_name: str):
        """Attempt to heal a failed service"""
        self.logger.info(f"Attempting to heal service: {service_name}")
        
        try:
            # Try to restart the container
            container = self.client.containers.get(f"flashloan-{service_name}")
            container.restart()
            self.logger.info(f"Restarted container for {service_name}")
            
            # Wait and check again
            await asyncio.sleep(10)
            
        except Exception as e:
            self.logger.error(f"Failed to heal service {service_name}: {e}")

if __name__ == "__main__":
    orchestrator = RobustOrchestrator()
    asyncio.run(orchestrator.start())
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
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run the orchestrator
CMD ["python", "robust_orchestrator.py"]
"""
        
        with open(orchestrator_dir / "Dockerfile", "w", encoding="utf-8") as f:
            f.write(dockerfile_content)
        
        # Create requirements.txt
        requirements_content = """docker==6.1.3
requests==2.31.0
aiohttp==3.9.1
asyncio-mqtt==0.16.1
fastapi==0.104.1
uvicorn==0.24.0
"""
        
        with open(orchestrator_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
        
        self.log("Orchestrator files created")
        return True
    
    def create_mcp_server_files(self) -> bool:
        """Create MCP server container files"""
        self.log("Creating MCP server files...")
        
        mcp_dir = self.containers_dir / "mcp_servers"
        
        # Create requirements.txt
        requirements_content = """langchain==0.1.0
langchain-community==0.0.10
langchain-core==0.1.10
openai==1.6.1
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2
requests==2.31.0
python-dotenv==1.0.0
"""
        
        with open(mcp_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
        
        # Create MCP server Python file
        server_content = '''#!/usr/bin/env python3
"""
Model Context Protocol Server for Flash Loan System
"""

import asyncio
import logging
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
import uvicorn
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Flash Loan MCP Server", version="1.0.0")

class MCPServer:
    """Model Context Protocol Server"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        self.is_healthy = True
        
    async def initialize(self):
        """Initialize the MCP server"""
        logger.info("Initializing MCP Server...")
        # Add initialization logic here
        
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process MCP request"""
        try:
            # Process the request
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": request
            }
            return result
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Global MCP server instance
mcp_server = MCPServer()

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    await mcp_server.initialize()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if mcp_server.is_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "service": "mcp-server"
    }

@app.post("/mcp/request")
async def handle_mcp_request(request: Dict[str, Any]):
    """Handle MCP request"""
    return await mcp_server.process_request(request)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Flash Loan MCP Server", "status": "running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        
        with open(mcp_dir / "mcp_server.py", "w", encoding="utf-8") as f:
            f.write(server_content)
        
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
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the MCP server
CMD ["python", "mcp_server.py"]
"""
        
        with open(mcp_dir / "Dockerfile", "w", encoding="utf-8") as f:
            f.write(dockerfile_content)
        
        self.log("MCP server files created")
        return True
    
    def create_agent_files(self) -> bool:
        """Create agent container files"""
        self.log("Creating agent files...")
        
        agent_dir = self.containers_dir / "agents"
        
        # Create requirements.txt
        requirements_content = """langchain==0.1.0
langchain-community==0.0.10
langchain-core==0.1.10
openai==1.6.1
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2
requests==2.31.0
python-dotenv==1.0.0
web3==6.11.3
"""
        
        with open(agent_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
        
        # Create agent Python file
        agent_content = '''#!/usr/bin/env python3
"""
Multi-Agent System for Flash Loan Operations
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Flash Loan Agent System", version="1.0.0")

class BaseAgent:
    """Base agent class"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.is_active = True
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent task"""
        logger.info(f"Agent {self.name} processing: {self.role}")
        return {
            "agent": self.name,
            "role": self.role,
            "status": "processed",
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

class FlashLoanAgentSystem:
    """Multi-agent coordinator"""
    
    def __init__(self):
        self.agents = {}
        self.is_healthy = True
        self.initialize_agents()
        
    def initialize_agents(self):
        """Initialize all agents"""
        agent_configs = [
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
        
        for name, role in agent_configs:
            self.agents[name] = BaseAgent(name, role)
            logger.info(f"Initialized agent: {name} ({role})")
    
    async def coordinate_agents(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Coordinate multiple agents for a task"""
        results = []
        
        for agent_name, agent in self.agents.items():
            if agent.is_active:
                try:
                    result = await agent.process(task)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Agent {agent_name} error: {e}")
                    results.append({
                        "agent": agent_name,
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
        
        return results

# Global agent system
agent_system = FlashLoanAgentSystem()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if agent_system.is_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "service": "agent-system",
        "active_agents": len([a for a in agent_system.agents.values() if a.is_active])
    }

@app.post("/agents/coordinate")
async def coordinate_task(task: Dict[str, Any]):
    """Coordinate a task across agents"""
    results = await agent_system.coordinate_agents(task)
    return {
        "task_id": task.get("id", "unknown"),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    return {
        "agents": {
            name: {
                "role": agent.role,
                "active": agent.is_active
            }
            for name, agent in agent_system.agents.items()
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Flash Loan Agent System", "status": "running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''
        
        with open(agent_dir / "agent.py", "w", encoding="utf-8") as f:
            f.write(agent_content)
        
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
COPY . .

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8001/health || exit 1

# Run the agent system
CMD ["python", "agent.py"]
"""
        
        with open(agent_dir / "Dockerfile", "w", encoding="utf-8") as f:
            f.write(dockerfile_content)
        
        self.log("Agent files created")
        return True
    
    def create_docker_compose(self) -> bool:
        """Create docker-compose.yml file"""
        self.log("Creating docker-compose.yml...")
        
        compose_content = f"""version: '3.8'

networks:
  flashloan-network:
    driver: bridge

volumes:
  flashloan-logs:
  flashloan-data:

services:
  # Main Orchestrator
  orchestrator:
    build: ./containers/orchestrator
    container_name: flashloan-orchestrator
    networks:
      - flashloan-network
    environment:
      - GITHUB_TOKEN={self.github_token}
      - OPENAI_API_KEY={self.openai_key}
    ports:
      - "8080:8080"
    volumes:
      - flashloan-logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock
    restart: unless-stopped
    depends_on:
      - mcp-servers
      - agents
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MCP Servers
  mcp-servers:
    build: ./containers/mcp_servers
    container_name: flashloan-mcp-servers
    networks:
      - flashloan-network
    environment:
      - GITHUB_TOKEN={self.github_token}
      - OPENAI_API_KEY={self.openai_key}
    ports:
      - "8000:8000"
    volumes:
      - flashloan-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Agent System
  agents:
    build: ./containers/agents
    container_name: flashloan-agents
    networks:
      - flashloan-network
    environment:
      - GITHUB_TOKEN={self.github_token}
      - OPENAI_API_KEY={self.openai_key}
    ports:
      - "8001:8001"
    volumes:
      - flashloan-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
"""
        
        with open(self.project_root / "docker-compose.yml", "w", encoding="utf-8") as f:
            f.write(compose_content)
        
        self.log("Docker compose file created")
        return True
    
    def build_and_deploy(self) -> bool:
        """Build and deploy all containers"""
        self.log("Building and deploying containers...")
        
        # Build containers
        if not self.run_command(
            ["docker", "compose", "build", "--no-cache"],
            "Building all containers"
        ):
            return False
        
        # Deploy containers
        if not self.run_command(
            ["docker", "compose", "up", "-d"],
            "Deploying all containers"
        ):
            return False
        
        # Wait a bit for containers to start
        self.log("Waiting for containers to start...")
        time.sleep(10)
        
        # Check container status
        self.run_command(
            ["docker", "compose", "ps"],
            "Checking container status"
        )
        
        self.log("Build and deployment completed")
        return True
    
    def run_build_command(self) -> bool:
        """Run the complete build process"""
        self.log("Starting complete LangChain system build...")
        
        steps = [
            ("Complete cleanup", self.complete_cleanup),
            ("Directory setup", self.setup_directories),
            ("Orchestrator creation", self.create_orchestrator_files),
            ("MCP server creation", self.create_mcp_server_files),
            ("Agent creation", self.create_agent_files),
            ("Docker compose creation", self.create_docker_compose),
            ("Build and deploy", self.build_and_deploy)
        ]
        
        for step_name, step_func in steps:
            self.log(f"Step: {step_name}")
            if not step_func():
                self.log(f"Failed at step: {step_name}", "ERROR")
                return False
            self.log(f"Completed: {step_name}")
        
        self.log("All steps completed successfully!")
        return True
    
    def monitor_system(self) -> bool:
        """Monitor the running system"""
        self.log("Starting system monitoring...")
        
        while True:
            try:
                # Check container status
                self.run_command(
                    ["docker", "compose", "ps"],
                    "Checking container status"
                )
                
                # Check logs
                self.run_command(
                    ["docker", "compose", "logs", "--tail=10"],
                    "Checking recent logs"
                )
                
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.log("Monitoring stopped by user")
                break
            except Exception as e:
                self.log(f"Monitoring error: {e}", "ERROR")
                time.sleep(10)
        
        return True

def main():
    parser = argparse.ArgumentParser(description="LangChain Flash Loan System Builder")
    parser.add_argument("command", choices=["build", "monitor", "cleanup"])
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    builder = LangChainSystemBuilder(args.project_root)
    
    if args.command == "build":
        success = builder.run_build_command()
        sys.exit(0 if success else 1)
    elif args.command == "monitor":
        builder.monitor_system()
    elif args.command == "cleanup":
        builder.complete_cleanup()

if __name__ == "__main__":
    main()
