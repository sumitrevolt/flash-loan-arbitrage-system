#!/usr/bin/env python3
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
                        body=f"Container {container_name} was restarted automatically.\nRestart count: {restart_count + 1}\nTimestamp: {datetime.now()}",
                        labels=['auto-restart', 'container-issue']
                    )
                    
                else:
                    logger.error(f"Container {container_name} has failed too many times")
                    
                    # Create critical GitHub issue
                    await self.github.create_issue(
                        title=f"Critical: Container {container_name} Failed Multiple Times",
                        body=f"Container {container_name} has failed {restart_count} times and requires manual intervention.\nLast status: {container_info['status']}\nTimestamp: {datetime.now()}",
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
                        f.write(json.dumps(task_result) + '\n')
                        
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
                        body=f"System Status Report:\n\nUptime: {uptime}\nTasks Completed: {self.task_count}\nContainers: {len(self.coordinator.containers)}\nComponents: {COMPONENTS}\n\nTimestamp: {datetime.now()}",
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
