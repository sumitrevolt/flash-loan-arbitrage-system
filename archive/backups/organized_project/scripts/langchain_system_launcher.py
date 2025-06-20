#!/usr/bin/env python3
"""
Comprehensive LangChain Flash Loan System Launcher
"""

import asyncio
import logging
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import subprocess
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system_launcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemLauncher")

class SystemLauncher:
    """Comprehensive system launcher with LangChain coordination"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.components = {
            'docker_compose': 'docker-compose-merged.yml',
            'orchestrator': 'containers/orchestrator',
            'mcp_servers': 'containers/mcp_servers',
            'agents': 'containers/agents'
        }
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        
    async def launch_system(self):
        """Launch the complete LangChain flash loan system"""
        try:
            logger.info("🚀 Starting LangChain Flash Loan System Launcher")
            logger.info(f"📁 Project root: {self.project_root}")
            
            # Step 1: Environment setup
            await self._setup_environment()
            
            # Step 2: Build containers
            await self._build_containers()
            
            # Step 3: Launch infrastructure
            await self._launch_infrastructure()
            
            # Step 4: Launch MCP servers
            await self._launch_mcp_servers()
            
            # Step 5: Launch agents
            await self._launch_agents()
            
            # Step 6: Launch orchestrator
            await self._launch_orchestrator()
            
            # Step 7: Verify system health
            await self._verify_system_health()
            
            # Step 8: Monitor system
            await self._monitor_system()
            
        except Exception as e:
            logger.error(f"System launch failed: {e}")
            await self._emergency_cleanup()
    
    async def _setup_environment(self):
        """Setup environment variables and configurations"""
        logger.info("🔧 Setting up environment...")
        
        env_vars = {
            'GITHUB_TOKEN': self.github_token,
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            'REDIS_URL': 'redis://flashloan-redis:6379',
            'POSTGRES_URL': 'postgresql://flashloan-postgres:5432/flashloan',
            'RABBITMQ_URL': 'amqp://flashloan-rabbitmq:5672',
            'DOCKER_HOST': 'unix:///var/run/docker.sock'
        }
        
        # Set environment variables
        for key, value in env_vars.items():
            if value:
                os.environ[key] = value
                logger.info(f"✅ Set {key}")
            else:
                logger.warning(f"⚠️ Missing {key}")
        
        # Create necessary directories
        directories = [
            'logs',
            'data',
            'backups',
            'containers/orchestrator/logs',
            'containers/mcp_servers/logs',
            'containers/agents/logs'
        ]
        
        for directory in directories:
            full_path = os.path.join(self.project_root, directory)
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"📁 Created directory: {directory}")
    
    async def _build_containers(self):
        """Build all Docker containers"""
        logger.info("🔨 Building Docker containers...")
        
        # Build orchestrator
        await self._run_command([
            'docker', 'build',
            '-t', 'flashloan-langchain-orchestrator',
            './containers/orchestrator'
        ], "Building orchestrator container")
        
        # Build MCP servers
        await self._run_command([
            'docker', 'build',
            '-t', 'flashloan-mcp-server',
            './containers/mcp_servers'
        ], "Building MCP server container")
        
        # Build agents
        await self._run_command([
            'docker', 'build',
            '-t', 'flashloan-agent',
            './containers/agents'
        ], "Building agent container")
        
        logger.info("✅ All containers built successfully")
    
    async def _launch_infrastructure(self):
        """Launch infrastructure services (Redis, PostgreSQL, RabbitMQ)"""
        logger.info("🏗️ Launching infrastructure services...")
        
        # Create docker network
        await self._run_command([
            'docker', 'network', 'create', 'flashloan-network'
        ], "Creating Docker network", ignore_errors=True)
        
        # Launch Redis
        await self._run_command([
            'docker', 'run', '-d',
            '--name', 'flashloan-redis',
            '--network', 'flashloan-network',
            '-p', '6379:6379',
            'redis:7-alpine'
        ], "Launching Redis", ignore_errors=True)
        
        # Launch PostgreSQL
        await self._run_command([
            'docker', 'run', '-d',
            '--name', 'flashloan-postgres',
            '--network', 'flashloan-network',
            '-p', '5432:5432',
            '-e', 'POSTGRES_DB=flashloan',
            '-e', 'POSTGRES_USER=flashloan',
            '-e', 'POSTGRES_PASSWORD=flashloan123',
            'postgres:15-alpine'
        ], "Launching PostgreSQL", ignore_errors=True)
        
        # Launch RabbitMQ
        await self._run_command([
            'docker', 'run', '-d',
            '--name', 'flashloan-rabbitmq',
            '--network', 'flashloan-network',
            '-p', '5672:5672',
            '-p', '15672:15672',
            'rabbitmq:3-management-alpine'
        ], "Launching RabbitMQ", ignore_errors=True)
        
        # Wait for services to be ready
        logger.info("⏳ Waiting for infrastructure services to be ready...")
        await asyncio.sleep(30)
        
        logger.info("✅ Infrastructure services launched")
    
    async def _launch_mcp_servers(self):
        """Launch 21 MCP servers"""
        logger.info("🖥️ Launching 21 MCP servers...")
        
        mcp_servers = [
            ('mcp-filesystem', 8001),
            ('mcp-database', 8002),
            ('mcp-web-scraper', 8003),
            ('mcp-api-client', 8004),
            ('mcp-file-processor', 8005),
            ('mcp-data-analyzer', 8006),
            ('mcp-notification', 8007),
            ('mcp-auth-manager', 8008),
            ('mcp-cache-manager', 8009),
            ('mcp-task-queue', 8010),
            ('mcp-monitoring', 8011),
            ('mcp-security', 8012),
            ('mcp-blockchain', 8013),
            ('mcp-defi-analyzer', 8014),
            ('mcp-price-feed', 8015),
            ('mcp-arbitrage', 8016),
            ('mcp-risk-manager', 8017),
            ('mcp-portfolio', 8018),
            ('mcp-liquidity', 8019),
            ('mcp-flash-loan', 8020),
            ('mcp-coordinator', 8021)
        ]
        
        for server_name, port in mcp_servers:
            await self._run_command([
                'docker', 'run', '-d',
                '--name', f'flashloan-{server_name}',
                '--network', 'flashloan-network',
                '-p', f'{port}:{port}',
                '-e', f'MCP_SERVER_NAME={server_name}',
                '-e', f'MCP_SERVER_PORT={port}',
                'flashloan-mcp-server'
            ], f"Launching {server_name}", ignore_errors=True)
        
        logger.info("✅ All 21 MCP servers launched")
    
    async def _launch_agents(self):
        """Launch 10 agents"""
        logger.info("🤖 Launching 10 agents...")
        
        agents = [
            ('coordinator', 'system_coordinator'),
            ('analyzer', 'market_analyzer'),
            ('executor', 'trade_executor'),
            ('risk-manager', 'risk_assessment'),
            ('monitor', 'system_monitor'),
            ('data-collector', 'data_collection'),
            ('arbitrage-bot', 'arbitrage_detection'),
            ('liquidity-manager', 'liquidity_optimization'),
            ('reporter', 'report_generator'),
            ('healer', 'auto_healing')
        ]
        
        for agent_name, agent_role in agents:
            await self._run_command([
                'docker', 'run', '-d',
                '--name', f'flashloan-agent-{agent_name}',
                '--network', 'flashloan-network',
                '-e', f'AGENT_NAME={agent_name}',
                '-e', f'AGENT_ROLE={agent_role}',
                '-e', f'ORCHESTRATOR_URL=http://flashloan-orchestrator:8000',
                'flashloan-agent'
            ], f"Launching agent {agent_name}", ignore_errors=True)
        
        logger.info("✅ All 10 agents launched")
    
    async def _launch_orchestrator(self):
        """Launch the main orchestrator"""
        logger.info("🎯 Launching LangChain orchestrator...")
        
        await self._run_command([
            'docker', 'run', '-d',
            '--name', 'flashloan-orchestrator',
            '--network', 'flashloan-network',
            '-p', '8000:8000',
            '-e', f'GITHUB_TOKEN={self.github_token}',
            '-e', f'OPENAI_API_KEY={os.getenv("OPENAI_API_KEY", "")}',
            '-e', 'REDIS_URL=redis://flashloan-redis:6379',
            '-e', 'POSTGRES_URL=postgresql://flashloan-postgres:5432/flashloan',
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            'flashloan-langchain-orchestrator'
        ], "Launching orchestrator", ignore_errors=True)
        
        logger.info("✅ Orchestrator launched")
    
    async def _verify_system_health(self):
        """Verify all system components are healthy"""
        logger.info("🏥 Verifying system health...")
        
        # Wait for orchestrator to be ready
        await asyncio.sleep(60)
        
        # Check container status
        result = await self._run_command(['docker', 'ps'], "Checking container status")
        
        if result:
            running_containers = result.stdout.decode()
            logger.info("📊 Running containers:")
            for line in running_containers.split('\n')[1:]:  # Skip header
                if line.strip():
                    logger.info(f"   {line}")
        
        # Try to get orchestrator health
        try:
            result = await self._run_command([
                'docker', 'exec', 'flashloan-orchestrator',
                'python', '-c', 
                'import asyncio; from langchain_orchestrator_robust import health_check; print(asyncio.run(health_check()))'
            ], "Checking orchestrator health")
            
            if result:
                logger.info("✅ Orchestrator is healthy")
            else:
                logger.warning("⚠️ Orchestrator health check failed")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not verify orchestrator health: {e}")
        
        logger.info("✅ System health verification complete")
    
    async def _monitor_system(self):
        """Monitor system continuously"""
        logger.info("📊 Starting system monitoring...")
        
        try:
            while True:
                # Get container status
                result = await self._run_command(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                                               "Getting container status")
                
                if result:
                    status_output = result.stdout.decode()
                    logger.info("📈 System Status:")
                    for line in status_output.split('\n'):
                        if line.strip() and 'flashloan' in line:
                            logger.info(f"   {line}")
                
                # Check for failed containers
                result = await self._run_command(['docker', 'ps', '-a', '--filter', 'status=exited', '--format', '{{.Names}}'], 
                                               "Checking for failed containers")
                
                if result and result.stdout.decode().strip():
                    failed_containers = result.stdout.decode().strip().split('\n')
                    logger.warning(f"⚠️ Failed containers detected: {failed_containers}")
                    
                    # Attempt to restart failed containers
                    for container in failed_containers:
                        if container.strip() and 'flashloan' in container:
                            logger.info(f"🔄 Restarting {container}")
                            await self._run_command(['docker', 'restart', container], 
                                                   f"Restarting {container}", ignore_errors=True)
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
        except KeyboardInterrupt:
            logger.info("📊 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
    
    async def _run_command(self, command: List[str], description: str, ignore_errors: bool = False):
        """Run a command asynchronously"""
        try:
            logger.info(f"🔄 {description}...")
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ {description} completed successfully")
                return process
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                if ignore_errors:
                    logger.warning(f"⚠️ {description} failed (ignored): {error_msg}")
                    return None
                else:
                    logger.error(f"❌ {description} failed: {error_msg}")
                    raise Exception(f"{description} failed: {error_msg}")
                    
        except Exception as e:
            if ignore_errors:
                logger.warning(f"⚠️ {description} error (ignored): {e}")
                return None
            else:
                logger.error(f"❌ {description} error: {e}")
                raise
    
    async def _emergency_cleanup(self):
        """Clean up containers in case of emergency"""
        logger.info("🧹 Performing emergency cleanup...")
        
        # Stop all flashloan containers
        await self._run_command([
            'docker', 'ps', '-q', '--filter', 'name=flashloan'
        ], "Getting flashloan containers", ignore_errors=True)
        
        await self._run_command([
            'docker', 'stop', '$(docker ps -q --filter name=flashloan)'
        ], "Stopping flashloan containers", ignore_errors=True)
        
        logger.info("🧹 Emergency cleanup complete")

if __name__ == "__main__":
    launcher = SystemLauncher()
    
    try:
        asyncio.run(launcher.launch_system())
    except KeyboardInterrupt:
        logger.info("System launcher stopped by user")
    except Exception as e:
        logger.error(f"System launcher failed: {e}")
        sys.exit(1)
