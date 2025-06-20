#!/usr/bin/env python3
"""
Unified MCP Orchestration Manager
Combines Docker orchestration and MCP coordination functionality
Merged from: manage_mcp_orchestration.py + unified_mcp_coordinator.py
"""

import asyncio
import aiohttp
import json
import subprocess
import sys
import time
import os
import logging
import signal
import platform
import socket
import psutil
import threading
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask, jsonify, request
from flask_cors import CORS
from types import FrameType
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Windows-specific asyncio event loop fix
if platform.system() == 'Windows':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure comprehensive logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/unified_orchestration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DeploymentMode(Enum):
    """Deployment modes for the orchestration system"""
    DOCKER = "docker"
    PROCESS = "process"
    HYBRID = "hybrid"

class AgentRole(Enum):
    """Specialized agent roles for multi-agent coordination"""
    RISK = "Risk"
    EXECUTION = "Execution" 
    ANALYTICS = "Analytics"
    QA = "QA"
    LOGS = "Logs"
    COORDINATION = "Coordination"
    TRADING = "Trading"
    MONITORING = "Monitoring"

@dataclass
class MCPServerConfig:
    """Enhanced configuration for individual MCP server"""
    name: str
    category: str
    path: str
    port: int
    command: List[str]
    health_endpoint: str
    required: bool
    startup_delay: int = 0
    max_restarts: int = 3
    dependencies: Optional[List[str]] = None
    process: Optional[Any] = None
    agent_role: Optional[AgentRole] = None
    docker_image: Optional[str] = None
    docker_ports: Optional[Dict[str, int]] = None
    environment: Optional[Dict[str, str]] = None
    deployment_mode: DeploymentMode = DeploymentMode.PROCESS

@dataclass
class ServerStatus:
    """Enhanced runtime status of MCP server"""
    name: str
    category: str
    status: str
    port: int
    health: bool
    last_check: datetime
    uptime: timedelta
    restart_count: int
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_count: int = 0
    agent_role: Optional[AgentRole] = None
    deployment_mode: DeploymentMode = DeploymentMode.PROCESS

@dataclass
class TaskContext:
    """Task context for cross-file coordination"""
    task_id: str
    goal: str
    status: str
    agent_assignments: Dict[AgentRole, List[str]]
    progress: Dict[str, Any]
    dependencies: List[str]
    created_at: datetime
    updated_at: datetime

class UnifiedMCPOrchestrationManager:
    """Unified MCP Orchestration Manager combining Docker and process management"""
    
    def __init__(self, deployment_mode: DeploymentMode = DeploymentMode.HYBRID):
        self.deployment_mode = deployment_mode
        self.project_root = Path.cwd()
        self.agent_manifest_path = self.project_root / "config" / "agent_manifest.json"
        self.mcp_config_path = self.project_root / "config" / "mcp_servers.json"
        self.compose_file = self.project_root / "docker-compose.yml"
        
        # Server management
        self.servers: Dict[str, MCPServerConfig] = {}
        self.status: Dict[str, ServerStatus] = {}
        self.tasks: Dict[str, TaskContext] = {}
        self.agents: Dict[AgentRole, List[str]] = {role: [] for role in AgentRole}
        
        # Runtime state
        self.running = False
        self.health_check_interval = 30
        self.restart_cooldown = 60
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Flask app for web interface
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_routes()
        
        # Message bus for agent coordination
        self.message_bus: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info(f"Unified MCP Orchestration Manager initialized in {deployment_mode.value} mode")

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed"""
        logger.info("🔍 Checking prerequisites...")
        
        prerequisites = [
            ("python", "Python is required"),
        ]
        
        # Add Docker prerequisites if using Docker mode
        if self.deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
            prerequisites.extend([
                ("docker", "Docker is required"),
                ("docker-compose", "Docker Compose is required")
            ])
        
        missing = []
        for cmd, description in prerequisites:
            try:
                result: str = subprocess.run([cmd, "--version"], 
                                      capture_output=True, text=True, check=True)
                logger.info(f"✅ {cmd}: {result.stdout.strip().split()[0]} available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(description)
                logger.error(f"❌ {cmd} not found")
        
        if missing:
            logger.error("❌ Missing prerequisites:")
            for item in missing:
                logger.error(f"   • {item}")
            return False
        
        # Check if Docker daemon is running (if needed)
        if self.deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
            try:
                subprocess.run(["docker", "info"], 
                             capture_output=True, check=True)
                logger.info("✅ Docker daemon is running")
            except subprocess.CalledProcessError:
                logger.error("❌ Docker daemon is not running")
                return False
        
        return True

    def load_server_configs(self):
        """Load server configurations from file"""
        try:
            if self.mcp_config_path.exists():
                with open(self.mcp_config_path, 'r') as f:
                    config_data = json.load(f)
                    
                for server_data in config_data.get('servers', []):
                    # Convert string agent_role to enum if present
                    if 'agent_role' in server_data and isinstance(server_data['agent_role'], str):
                        try:
                            server_data['agent_role'] = AgentRole[server_data['agent_role']]
                        except KeyError:
                            logger.warning(f"Unknown agent role: {server_data['agent_role']}")
                            server_data['agent_role'] = None
                    
                    # Set deployment mode if not specified
                    if 'deployment_mode' not in server_data:
                        server_data['deployment_mode'] = self.deployment_mode
                    elif isinstance(server_data['deployment_mode'], str):
                        server_data['deployment_mode'] = DeploymentMode(server_data['deployment_mode'])
                    
                    server_config = MCPServerConfig(**server_data)
                    self.servers[server_config.name] = server_config
                    
                    # Assign to agent role if specified
                    if server_config.agent_role:
                        self.agents[server_config.agent_role].append(server_config.name)
                        
                logger.info(f"Loaded {len(self.servers)} server configurations")
            else:
                logger.warning(f"Config file not found: {self.mcp_config_path}, creating default config")
                self._create_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load server configs: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """Create default server configuration"""
        default_servers = [
            {
                "name": "arbitrage_trading",
                "category": "trading",
                "path": "mcp_servers/trading/arbitrage_trading_mcp_server.py",
                "port": 8001,
                "command": ["python", "mcp_servers/trading/arbitrage_trading_mcp_server.py"],
                "health_endpoint": "/health",
                "required": True,
                "agent_role": AgentRole.EXECUTION,
                "deployment_mode": self.deployment_mode
            },
            {
                "name": "risk_manager",
                "category": "risk",
                "path": "mcp_servers/risk_management/mcp_risk_manager_server.py",
                "port": 8002,
                "command": ["python", "mcp_servers/risk_management/mcp_risk_manager_server.py"],
                "health_endpoint": "/health",
                "required": True,
                "agent_role": AgentRole.RISK,
                "deployment_mode": self.deployment_mode
            },
            {
                "name": "analytics_engine",
                "category": "analytics",
                "path": "mcp_servers/analytics/analytics_mcp_server.py",
                "port": 8003,
                "command": ["python", "mcp_servers/analytics/analytics_mcp_server.py"],
                "health_endpoint": "/health",
                "required": True,
                "agent_role": AgentRole.ANALYTICS,
                "deployment_mode": self.deployment_mode
            },
            {
                "name": "coordinator_hub",
                "category": "coordination",
                "path": "mcp_servers/coordination/coordinator_hub.py",
                "port": 8000,
                "command": ["python", "mcp_servers/coordination/coordinator_hub.py"],
                "health_endpoint": "/health",
                "required": True,
                "agent_role": AgentRole.COORDINATION,
                "deployment_mode": self.deployment_mode
            }
        ]
        
        for server_data in default_servers:
            server_config = MCPServerConfig(**server_data)
            self.servers[server_config.name] = server_config
            
            if server_config.agent_role:
                self.agents[server_config.agent_role].append(server_config.name)

    def generate_orchestration_files(self) -> bool:
        """Generate all required orchestration files"""
        logger.info("📝 Generating orchestration files...")
        
        try:
            # Generate agent manifest
            agent_manifest = {
                "total_agents": len(self.servers),
                "agent_roles": {},
                "deployment_mode": self.deployment_mode.value,
                "generated_at": datetime.now().isoformat()
            }
            
            # Group servers by agent role
            for role in AgentRole:
                role_servers = self.agents.get(role, [])
                if role_servers:
                    agent_manifest["agent_roles"][role.value.lower() + "s"] = {
                        "count": len(role_servers),
                        "agents": [
                            {
                                "name": server_name,
                                "container_name": f"mcp-{server_name}",
                                "port": self.servers[server_name].port,
                                "role": role.value
                            }
                            for server_name in role_servers
                        ]
                    }
            
            # Save agent manifest
            self.agent_manifest_path.parent.mkdir(exist_ok=True)
            with open(self.agent_manifest_path, 'w') as f:
                json.dump(agent_manifest, f, indent=2)
            
            # Generate Docker Compose if needed
            if self.deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
                self._generate_docker_compose()
            
            logger.info("✅ Generated orchestration files successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to generate orchestration files: {e}")
            return False

    def _generate_docker_compose(self):
        """Generate Docker Compose configuration"""
        compose_config = {
            "version": "3.8",
            "services": {},
            "networks": {
                "mcp_network": {
                    "driver": "bridge"
                }
            },
            "volumes": {
                "redis_data": {},
                "postgres_data": {},
                "logs_data": {}
            }
        }
        
        # Infrastructure services
        infrastructure_services = {
            "redis": {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"],
                "volumes": ["redis_data:/data"],
                "networks": ["mcp_network"],
                "restart": "unless-stopped"
            },
            "postgres": {
                "image": "postgres:15-alpine",
                "environment": {
                    "POSTGRES_DB": "mcp_coordination",
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_PASSWORD": "mcp_password_2025"
                },
                "ports": ["5432:5432"],
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "networks": ["mcp_network"],
                "restart": "unless-stopped"
            },
            "rabbitmq": {
                "image": "rabbitmq:3-management-alpine",
                "environment": {
                    "RABBITMQ_DEFAULT_USER": "mcp_admin",
                    "RABBITMQ_DEFAULT_PASS": "mcp_secure_2025"
                },
                "ports": ["5672:5672", "15672:15672"],
                "networks": ["mcp_network"],
                "restart": "unless-stopped"
            }
        }
        
        compose_config["services"].update(infrastructure_services)
        
        # MCP Server services
        for server_name, config in self.servers.items():
            if config.deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
                service_config = {
                    "build": {
                        "context": ".",
                        "dockerfile": f"docker/Dockerfile.{config.category}"
                    },
                    "container_name": f"mcp-{server_name}",
                    "ports": [f"{config.port}:{config.port}"],
                    "networks": ["mcp_network"],
                    "restart": "unless-stopped",
                    "depends_on": ["redis", "postgres", "rabbitmq"]
                }
                
                if config.environment:
                    service_config["environment"] = config.environment
                
                if config.dependencies:
                    service_config["depends_on"].extend(config.dependencies)
                
                compose_config["services"][f"mcp-{server_name}"] = service_config
        
        # Save Docker Compose file
        with open(self.compose_file, 'w') as f:
            import yaml
            yaml.dump(compose_config, f, default_flow_style=False, indent=2)

    def build_images(self) -> bool:
        """Build Docker images for coordinator and agents"""
        if self.deployment_mode == DeploymentMode.PROCESS:
            logger.info("Skipping image build for process deployment mode")
            return True
            
        logger.info("🏗️ Building Docker images...")
        
        # Get unique categories for building
        categories = set(config.category for config in self.servers.values() 
                        if config.deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID])
        
        for category in categories:
            dockerfile = f"docker/Dockerfile.{category}"
            image_name = f"mcp-{category}"
            
            if Path(dockerfile).exists():
                logger.info(f"Building {image_name}...")
                try:
                    cmd = [
                        "docker", "build",
                        "-f", dockerfile,
                        "-t", image_name,
                        "."
                    ]
                    
                    result: str = subprocess.run(cmd, check=True)
                    logger.info(f"✅ Built {image_name} successfully")
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ Failed to build {image_name}: {e}")
                    return False
            else:
                logger.warning(f"Dockerfile not found: {dockerfile}")
        
        return True

    async def start_infrastructure(self) -> bool:
        """Start infrastructure services"""
        if self.deployment_mode == DeploymentMode.PROCESS:
            logger.info("Infrastructure management not needed for process deployment")
            return True
            
        logger.info("🚀 Starting infrastructure services...")
        
        infrastructure_services = [
            "redis", "postgres", "rabbitmq"
        ]
        
        try:
            for service in infrastructure_services:
                logger.info(f"Starting {service}...")
        # TODO: Replace # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
                process = await asyncio.create_subprocess_exec(
                    "docker-compose", "up", "-d", service,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                
                if process.returncode != 0:
                    logger.error(f"Failed to start {service}")
                    return False
                    
                await asyncio.sleep(2)  # Brief pause between services
            
            logger.info("✅ Infrastructure services started successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start infrastructure: {e}")
            return False

    async def start_server(self, server_name: str) -> bool:
        """Start individual MCP server"""
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found in configuration")
            return False
            
        server_config = self.servers[server_name]
        
        try:
            # Check dependencies first
            if server_config.dependencies:
                for dep in server_config.dependencies:
                    if dep not in self.status or not self.status[dep].health:
                        logger.warning(f"Dependency {dep} not ready for {server_name}")
                        return False
            
            # Apply startup delay
            if server_config.startup_delay > 0:
                await asyncio.sleep(server_config.startup_delay)
            
            # Start the server based on deployment mode
            if server_config.deployment_mode == DeploymentMode.DOCKER:
                process = await self._start_docker_server(server_config)
            elif server_config.deployment_mode == DeploymentMode.PROCESS:
                process = await self._start_process_server(server_config)
            else:  # HYBRID - prefer Docker if available, fallback to process
                try:
                    process = await self._start_docker_server(server_config)
                except Exception as e:
                    logger.warning(f"Docker start failed for {server_name}, falling back to process: {e}")
                    process = await self._start_process_server(server_config)
            
            server_config.process = process
            
            # Initialize status
            self.status[server_name] = ServerStatus(
                name=server_name,
                category=server_config.category,
                status="starting",
                port=server_config.port,
                health=False,
                last_check=datetime.now(),
                uptime=timedelta(0),
                restart_count=0,
                agent_role=server_config.agent_role,
                deployment_mode=server_config.deployment_mode
            )
            
            logger.info(f"Started MCP server: {server_name} on port {server_config.port} ({server_config.deployment_mode.value} mode)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server {server_name}: {e}")
            return False

    async def _start_docker_server(self, server_config: MCPServerConfig):
        """Start server using Docker Compose"""
        container_name = f"mcp-{server_config.name}"
        
        cmd = ["docker-compose", "up", "-d", container_name]
        
        # TODO: Replace # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.wait()
        
        if process.returncode != 0:
            raise Exception(f"Docker start failed with return code {process.returncode}")
        
        return process

    async def _start_process_server(self, server_config: MCPServerConfig):
        """Start server as a direct process"""
        # TODO: Replace # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        process = await asyncio.create_subprocess_exec(
            *server_config.command,
            cwd=Path(server_config.path).parent if Path(server_config.path).exists() else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **(server_config.environment or {})}
        )
        
        return process

    async def stop_server(self, server_name: str) -> bool:
        """Stop individual MCP server"""
        if server_name not in self.servers:
            return False
            
        server_config = self.servers[server_name]
        
        try:
            if server_config.deployment_mode == DeploymentMode.DOCKER:
                # Stop Docker container
        # TODO: Replace # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
                process = await asyncio.create_subprocess_exec(
                    "docker-compose", "stop", f"mcp-{server_name}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
            else:
                # Stop process
                if server_config.process:
                    server_config.process.terminate()
                    try:
                        await asyncio.wait_for(server_config.process.wait(), timeout=10.0)
                    except asyncio.TimeoutError:
                        server_config.process.kill()
                        await server_config.process.wait()
            
            server_config.process = None
            
            if server_name in self.status:
                self.status[server_name].status = "stopped"
                self.status[server_name].health = False
                
            logger.info(f"Stopped MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop server {server_name}: {e}")
            return False

    async def health_check(self, server_name: str) -> bool:
        """Perform health check on server"""
        if server_name not in self.servers:
            return False
            
        server_config = self.servers[server_name]
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"http://localhost:{server_config.port}{server_config.health_endpoint}"
                async with session.get(url) as response:
                    is_healthy = response.status == 200
                    
                    if server_name in self.status:
                        self.status[server_name].health = is_healthy
                        self.status[server_name].last_check = datetime.now()
                        if is_healthy:
                            self.status[server_name].status = "running"
                        else:
                            self.status[server_name].status = "unhealthy"
                            self.status[server_name].error_count += 1
                    
                    return is_healthy
                    
        except Exception as e:
            logger.debug(f"Health check failed for {server_name}: {e}")
            if server_name in self.status:
                self.status[server_name].health = False
                self.status[server_name].status = "unhealthy"
                self.status[server_name].error_count += 1
            return False

    async def monitor_servers(self):
        """Continuous monitoring of all servers"""
        while self.running:
            try:
                for server_name in self.servers:
                    await self.health_check(server_name)
                    
                    # Auto-restart unhealthy servers
                    status = self.status.get(server_name)
                    config = self.servers[server_name]
                    
                    if (status and not status.health and 
                        status.restart_count < config.max_restarts and
                        config.required):
                        
                        logger.warning(f"Attempting to restart unhealthy server: {server_name}")
                        await self.stop_server(server_name)
                        await asyncio.sleep(self.restart_cooldown)
                        if await self.start_server(server_name):
                            status.restart_count += 1
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in server monitoring: {e}")
                await asyncio.sleep(5)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Basic status
            status = {
                "infrastructure": [],
                "coordinator": [],
                "agents": {role.value.lower(): [] for role in AgentRole},
                "monitoring": [],
                "deployment_mode": self.deployment_mode.value,
                "total_servers": len(self.servers),
                "healthy_servers": sum(1 for s in self.status.values() if s.health),
                "timestamp": datetime.now().isoformat()
            }
            
            # Categorize servers by role and status
            for server_name, server_status in self.status.items():
                server_info = {
                    'name': server_name,
                    'status': server_status.status,
                    'health': server_status.health,
                    'port': server_status.port,
                    'uptime': str(server_status.uptime),
                    'restart_count': server_status.restart_count,
                    'deployment_mode': server_status.deployment_mode.value
                }
                
                if server_status.agent_role:
                    role_key = server_status.agent_role.value.lower()
                    status['agents'][role_key].append(server_info)
                elif server_status.category == 'coordination':
                    status['coordinator'].append(server_info)
                elif server_status.category in ['infrastructure', 'database', 'messaging']:
                    status['infrastructure'].append(server_info)
                else:
                    status['monitoring'].append(server_info)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

    def show_status(self):
        """Display system status in a readable format"""
        status = self.get_system_status()
        
        if "error" in status:
            logger.error(f"❌ Could not retrieve system status: {status['error']}")
            return
        
        print("\n" + "="*80)
        print("🐳 UNIFIED MCP ORCHESTRATION SYSTEM STATUS")
        print(f"Deployment Mode: {status['deployment_mode'].upper()}")
        print("="*80)
        
        # Overall health
        total_servers = status['total_servers']
        healthy_servers = status['healthy_servers']
        health_percentage = (healthy_servers / total_servers * 100) if total_servers > 0 else 0
        
        print(f"\n📊 OVERALL HEALTH: {healthy_servers}/{total_servers} servers healthy ({health_percentage:.1f}%)")
        
        # Infrastructure
        if status['infrastructure']:
            print(f"\n📡 INFRASTRUCTURE ({len(status['infrastructure'])} services)")
            for service in status['infrastructure']:
                state_emoji = "🟢" if service['health'] else "🔴"
                print(f"   {state_emoji} {service['name']} - {service['status']} (:{service['port']})")
        
        # Coordinator
        if status['coordinator']:
            print(f"\n🎯 COORDINATOR ({len(status['coordinator'])} service)")
            for service in status['coordinator']:
                state_emoji = "🟢" if service['health'] else "🔴"
                print(f"   {state_emoji} {service['name']} - {service['status']} (:{service['port']})")
        
        # Agents
        print(f"\n🤖 MCP AGENTS")
        total_agents = 0
        running_agents = 0
        
        for role, agents in status['agents'].items():
            if agents:
                total_agents += len(agents)
                running_count = sum(1 for a in agents if a['health'])
                running_agents += running_count
                
                print(f"   📋 {role.replace('_', ' ').title()}: {running_count}/{len(agents)} healthy")
                for agent in agents:
                    state_emoji = "🟢" if agent['health'] else "🔴"
                    mode_emoji = "🐳" if agent['deployment_mode'] == 'docker' else "⚙️"
                    print(f"      {state_emoji}{mode_emoji} {agent['name']} - {agent['status']} (:{agent['port']})")
        
        if total_agents > 0:
            print(f"\n   🔢 Total Agents: {running_agents}/{total_agents} healthy")
        
        # Access URLs
        print(f"\n🌐 ACCESS URLS")
        print(f"   • Orchestration API: http://localhost:9000/status")
        print(f"   • Coordinator Dashboard: http://localhost:8000")
        if self.deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
            print(f"   • RabbitMQ Management: http://localhost:15672 (mcp_admin/mcp_secure_2025)")
            print(f"   • PostgreSQL: localhost:5432 (postgres/mcp_password_2025)")
            print(f"   • Redis: localhost:6379")
        
        print("\n" + "="*80 + "\n")

    def _setup_routes(self):
        """Setup Flask routes for web interface"""
        
        @self.app.route('/status')
        def get_status():
            return jsonify(self.get_system_status())
        
        @self.app.route('/servers')
        def get_servers():
            return jsonify({
                'servers': {name: asdict(config) for name, config in self.servers.items()},
                'status': {name: asdict(status) for name, status in self.status.items()}
            })
        
        @self.app.route('/servers/<server_name>/start', methods=['POST'])
        def start_server_endpoint(server_name):
            asyncio.create_task(self.start_server(server_name))
            return jsonify({'status': 'starting', 'server': server_name})
        
        @self.app.route('/servers/<server_name>/stop', methods=['POST'])
        def stop_server_endpoint(server_name):
            asyncio.create_task(self.stop_server(server_name))
            return jsonify({'status': 'stopping', 'server': server_name})
        
        @self.app.route('/tasks', methods=['POST'])
        def create_task():
            task_data = request.get_json()
            task = TaskContext(
                task_id=task_data['task_id'],
                goal=task_data['goal'],
                status='created',
                agent_assignments=task_data.get('agent_assignments', {}),
                progress={},
                dependencies=task_data.get('dependencies', []),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.tasks[task.task_id] = task
            return jsonify({'status': 'created', 'task_id': task.task_id})

    async def start_all_servers(self):
        """Start all configured servers"""
        logger.info("Starting all MCP servers...")
        
        # Start infrastructure first (if using Docker)
        if self.deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
            if not await self.start_infrastructure():
                logger.error("Failed to start infrastructure")
                return False
        
        # Group servers by priority (dependencies first)
        servers_to_start = []
        started_servers = set()
        
        # Start servers without dependencies first
        for name, config in self.servers.items():
            if not config.dependencies:
                servers_to_start.append(name)
        
        # Start remaining servers based on dependencies
        max_iterations = len(self.servers) * 2  # Prevent infinite loops
        iteration = 0
        
        while len(started_servers) < len(self.servers) and iteration < max_iterations:
            iteration += 1
            
            for name, config in self.servers.items():
                if name in started_servers or name in servers_to_start:
                    continue
                    
                if config.dependencies and all(dep in started_servers for dep in config.dependencies):
                    servers_to_start.append(name)
            
            if not servers_to_start:
                break
                
            # Start next batch
            tasks = [self.start_server(name) for name in servers_to_start]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if result and not isinstance(result, Exception):
                    started_servers.add(servers_to_start[i])
            
            servers_to_start.clear()
            await asyncio.sleep(2)  # Brief pause between batches
        
        logger.info(f"Started {len(started_servers)} out of {len(self.servers)} servers")
        return len(started_servers) > 0

    async def stop_all_servers(self):
        """Stop all servers"""
        logger.info("Stopping all MCP servers...")
        
        tasks = [self.stop_server(name) for name in self.servers.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop infrastructure if using Docker
        if self.deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
            try:
        # TODO: Replace # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # TODO: Replace # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
        # TODO: Replace process = await asyncio.create_subprocess_exec( with safer alternative
        # WARNING: This is a security risk
                process = await asyncio.create_subprocess_exec(
                    "docker-compose", "down", "-v",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
            except Exception as e:
                logger.error(f"Failed to stop Docker infrastructure: {e}")
        
        logger.info("All servers stopped")

    async def run(self):
        """Main orchestration loop"""
        self.running = True
        
        try:
            # Load configurations
            self.load_server_configs()
            
            # Generate orchestration files
            if not self.generate_orchestration_files():
                logger.error("Failed to generate orchestration files")
                return
            
            # Build images if needed
            if not self.build_images():
                logger.error("Failed to build Docker images")
                return
            
            # Start all servers
            if not await self.start_all_servers():
                logger.error("Failed to start servers")
                return
            
            # Start monitoring
            monitoring_task = asyncio.create_task(self.monitor_servers())
            
            # Start web interface
            web_task = asyncio.create_task(
                asyncio.to_thread(self.app.run, host='0.0.0.0', port=9000, debug=False)
            )
            
            logger.info("Unified MCP Orchestration Manager is running...")
            logger.info("Web interface available at http://localhost:9000/status")
            
            # Show initial status
            await asyncio.sleep(5)  # Wait for services to initialize
            self.show_status()
            
            # Wait for shutdown signal
            await asyncio.gather(monitoring_task, web_task)
            
        except Exception as e:
            logger.error(f"Error in orchestration main loop: {e}")
        finally:
            self.running = False
            await self.stop_all_servers()

    def shutdown(self, signum: int, frame: FrameType):
        """Graceful shutdown handler"""
        logger.info("Received shutdown signal, stopping orchestration...")
        self.running = False

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Unified MCP Orchestration Management")
    parser.add_argument("command", choices=[
        "check", "generate", "build", "start", "stop", "status", "logs",
        "start-infra", "start-servers"
    ], help="Command to execute")
    
    parser.add_argument("--mode", choices=["docker", "process", "hybrid"], 
                       default="hybrid", help="Deployment mode")
    parser.add_argument("--server", help="Specific server for operations")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")
    
    args = parser.parse_args()
    
    # Convert mode string to enum
    deployment_mode = DeploymentMode(args.mode)
    manager = UnifiedMCPOrchestrationManager(deployment_mode)
    
    if args.command == "check":
        success = manager.check_prerequisites()
        sys.exit(0 if success else 1)
    
    elif args.command == "generate":
        manager.load_server_configs()
        success = manager.generate_orchestration_files()
        sys.exit(0 if success else 1)
    
    elif args.command == "build":
        if not manager.check_prerequisites():
            sys.exit(1)
        manager.load_server_configs()
        success = manager.build_images()
        sys.exit(0 if success else 1)
    
    elif args.command == "start-infra":
        async def start_infra():
            return await manager.start_infrastructure()
        success = asyncio.run(start_infra())
        sys.exit(0 if success else 1)
    
    elif args.command == "start-servers":
        async def start_servers():
            manager.load_server_configs()
            return await manager.start_all_servers()
        success = asyncio.run(start_servers())
        sys.exit(0 if success else 1)
    
    elif args.command == "start":
        if not manager.check_prerequisites():
            sys.exit(1)
        
        logger.info("🚀 Starting unified MCP orchestration system...")
        try:
            asyncio.run(manager.run())
        except KeyboardInterrupt:
            logger.info("System stopped by user")
        except Exception as e:
            logger.error(f"System failed: {e}")
            sys.exit(1)
    
    elif args.command == "stop":
        async def stop_all():
            manager.load_server_configs()
            await manager.stop_all_servers()
        asyncio.run(stop_all())
    
    elif args.command == "status":
        manager.load_server_configs()
        # Try to get status from running instance
        try:
            import requests
            response = requests.get("http://localhost:9000/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                print(f"\n📊 System Status (from running instance):")
                print(f"   • Total Servers: {status_data.get('total_servers', 0)}")
                print(f"   • Healthy Servers: {status_data.get('healthy_servers', 0)}")
                print(f"   • Deployment Mode: {status_data.get('deployment_mode', 'unknown')}")
            else:
                print("❌ Could not connect to running orchestration instance")
        except Exception:
            print("❌ No running orchestration instance found")
            manager.show_status()
    
    elif args.command == "logs":
        if deployment_mode in [DeploymentMode.DOCKER, DeploymentMode.HYBRID]:
            cmd = ["docker-compose", "logs"]
            if args.follow:
                cmd.append("-f")
            if args.server:
                cmd.append(f"mcp-{args.server}")
            
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                logger.info("Stopped following logs")
        else:
            logger.info("Log viewing not implemented for process mode")

if __name__ == "__main__":
    main()
