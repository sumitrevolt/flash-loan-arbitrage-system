# -*- coding: utf-8 -*-
"""
Deployment Manager for MCP Servers

This module provides unified deployment, startup, shutdown, and lifecycle management
for all MCP servers with dependency management and load balancing coordination.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import logging
import os
import subprocess

from .mcp_server_registry import MCPServerInfo, ServerStatus, ServerTier
from dataclasses import dataclass, field
from enum import Enum
import docker

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status of servers"""
    NOT_DEPLOYED = "not_deployed"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RESTARTING = "restarting"


class DeploymentMode(Enum):
    """Deployment modes"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DeploymentConfig:
    """Configuration for server deployment"""
    server_id: str
    deployment_mode: DeploymentMode
    auto_start: bool = True
    restart_policy: str = "on-failure"
    max_restarts: int = 3
    health_check_grace_period: int = 30
    startup_timeout: int = 120
    shutdown_timeout: int = 30
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    server_id: str
    success: bool
    status: DeploymentStatus
    message: str
    process_id: Optional[int] = None
    container_id: Optional[str] = None
    startup_time: Optional[datetime] = None
    error_details: Optional[str] = None


@dataclass
class ServerProcess:
    """Information about a running server process"""
    server_id: str
    process: Optional[subprocess.Popen] = None
    container_id: Optional[str] = None
    pid: Optional[int] = None
    status: DeploymentStatus = DeploymentStatus.NOT_DEPLOYED
    started_at: Optional[datetime] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None


class DeploymentManager:
    """
    Unified deployment and lifecycle management for all MCP servers
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.deployment_config = config.get("deployment", {})
        
        # Core components
        self.server_registry = None  # Will be injected
        self.health_monitor = None   # Will be injected
        
        # Deployment tracking
        self.server_processes: Dict[str, ServerProcess] = {}
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        
        # Docker client for containerized deployments
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"[WARNING] Docker not available: {e}")
        
        # Deployment orchestration
        self.deployment_order: List[List[str]] = []  # Ordered by dependency tiers
        self.shutdown_order: List[List[str]] = []    # Reverse order for shutdown
        
        # Background tasks
        self.process_monitor_task: Optional[asyncio.Task] = None
        self.auto_restart_task: Optional[asyncio.Task] = None
        
        # Deployment statistics
        self.deployment_stats = {
            "total_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "auto_restarts": 0,
            "total_uptime": 0,
            "last_deployment_time": None

        
        logger.info("[INIT] Deployment Manager initialized")
    
    async def initialize(self, server_registry, health_monitor):
        """Initialize deployment manager with registry and health monitor"""
        try:
            self.server_registry = server_registry
            self.health_monitor = health_monitor
            
            # Generate deployment configurations
            await self._generate_deployment_configs()
            
            # Calculate deployment order based on dependencies
            await self._calculate_deployment_order()
            
            # Start background monitoring
            self.process_monitor_task = asyncio.create_task(self._process_monitoring_loop())
            self.auto_restart_task = asyncio.create_task(self._auto_restart_loop())
            
            logger.info("[OK] Deployment Manager initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] Deployment Manager initialization failed: {e}")
            raise
    
    async def _generate_deployment_configs(self):
        """Generate deployment configurations for all servers"""
        deployment_mode = DeploymentMode(self.deployment_config.get("mode", "development"))
        
        for server_id, server_info in self.server_registry.servers.items():
            # Create deployment config based on server tier and mode
            config = DeploymentConfig(
                server_id=server_id,
                deployment_mode=deployment_mode,
                auto_start=server_info.tier != ServerTier.SPECIALIZED,  # Auto-start critical and integration
                restart_policy="always" if server_info.tier == ServerTier.CRITICAL else "on-failure",
                max_restarts=5 if server_info.tier == ServerTier.CRITICAL else 3,
                health_check_grace_period=15 if server_info.tier == ServerTier.CRITICAL else 30,
                startup_timeout=60 if server_info.tier == ServerTier.CRITICAL else 120,
                shutdown_timeout=15 if server_info.tier == ServerTier.CRITICAL else 30,
                dependencies=server_info.dependencies,
                environment_variables=server_info.environment_vars

            
            # Add resource limits based on tier
            if server_info.tier == ServerTier.CRITICAL:
                config.resource_limits = {
                    "memory": "512MB",
                    "cpu": "0.5"

            elif server_info.tier == ServerTier.INTEGRATION:
                config.resource_limits = {
                    "memory": "256MB", 
                    "cpu": "0.3"

            else:
                config.resource_limits = {
                    "memory": "128MB",
                    "cpu": "0.2"

            
            self.deployment_configs[server_id] = config
            
            # Initialize process tracking
            self.server_processes[server_id] = ServerProcess(server_id=server_id)
        
        logger.info(f"[OK] Generated deployment configs for {len(self.deployment_configs)} servers")
    
    async def _calculate_deployment_order(self):
        """Calculate optimal deployment order based on dependencies and tiers"""
        # Group servers by tier (critical first, then integration, then specialized)
        tier_groups = {
            ServerTier.CRITICAL: [],
            ServerTier.INTEGRATION: [],
            ServerTier.SPECIALIZED: []

        
        for server_id, server_info in self.server_registry.servers.items():
            tier_groups[server_info.tier].append(server_id)
        
        # For each tier, resolve dependencies
        self.deployment_order = []
        
        for tier in [ServerTier.CRITICAL, ServerTier.INTEGRATION, ServerTier.SPECIALIZED]:
            tier_servers = tier_groups[tier]
            if not tier_servers:
                continue
            
            # Simple dependency resolution within tier
            ordered_servers = self._resolve_dependencies(tier_servers)
            self.deployment_order.extend(ordered_servers)
        
        # Create shutdown order (reverse of startup)
        self.shutdown_order = list(reversed(self.deployment_order))
        
        logger.info(f"[OK] Calculated deployment order: {len(self.deployment_order)} groups")
    
    def _resolve_dependencies(self, servers: List[str]) -> List[List[str]]:
        """Resolve dependencies within a tier and return deployment groups"""
        # Simple implementation - can be enhanced with proper topological sort
        remaining = set(servers)
        resolved_groups = []
        
        while remaining:
            # Find servers with no unresolved dependencies
            ready = []
            for server_id in remaining:
                server_info = self.server_registry.servers[server_id]
                dependencies = set(server_info.dependencies) & remaining
                if not dependencies:
                    ready.append(server_id)
            
            if not ready:
                # Circular dependency or unknown dependency - deploy remaining in arbitrary order
                ready = list(remaining)
            
            resolved_groups.append(ready)
            remaining -= set(ready)
        
        return resolved_groups
    
    async def deploy_all_servers(self) -> Dict[str, DeploymentResult]:
        """Deploy all servers in the correct order"""
        logger.info("[DEPLOY] Starting unified deployment of all servers...")
        
        deployment_results = {}
        start_time = datetime.now()
        
        try:
            for group in self.deployment_order:
                # Deploy servers in parallel within each group
                group_tasks = []
                for server_id in group:
                    if isinstance(server_id, list):
                        # Handle nested groups
                        for srv_id in server_id:
                            task = asyncio.create_task(self.deploy_server(srv_id))
                            group_tasks.append((srv_id, task))
                    else:
                        task = asyncio.create_task(self.deploy_server(server_id))
                        group_tasks.append((server_id, task))
                
                # Wait for all servers in group to complete
                for server_id, task in group_tasks:
                    try:
                        result = await task
                        deployment_results[server_id] = result
                        
                        if not result.success:
                            logger.error(f"[DEPLOY] Failed to deploy {server_id}: {result.message}")
                    except Exception as e:
                        logger.error(f"[DEPLOY] Exception deploying {server_id}: {e}")
                        deployment_results[server_id] = DeploymentResult(
                            server_id=server_id,
                            success=False,
                            status=DeploymentStatus.FAILED,
                            message=f"Deployment exception: {e}"

                
                # Small delay between groups
                await asyncio.sleep(2)
            
            # Update statistics
            total_time = (datetime.now() - start_time).total_seconds()
            successful = len([r for r in deployment_results.values() if r.success])
            
            self.deployment_stats["total_deployments"] += len(deployment_results)
            self.deployment_stats["successful_deployments"] += successful
            self.deployment_stats["failed_deployments"] += len(deployment_results) - successful
            self.deployment_stats["last_deployment_time"] = datetime.now()
            
            logger.info(f"[DEPLOY] Deployment completed: {successful}/{len(deployment_results)} successful in {total_time:.1f}s")
            
        except Exception as e:
            logger.error(f"[ERROR] Unified deployment failed: {e}")
            raise
        
        return deployment_results
    
    async def deploy_server(self, server_id: str) -> DeploymentResult:
        """Deploy a single server"""
        try:
            server_info = await self.server_registry.get_server_by_id(server_id)
            if not server_info:
                return DeploymentResult(
                    server_id=server_id,
                    success=False,
                    status=DeploymentStatus.FAILED,
                    message="Server not found in registry"

            
            config = self.deployment_configs.get(server_id)
            if not config:
                return DeploymentResult(
                    server_id=server_id,
                    success=False,
                    status=DeploymentStatus.FAILED,
                    message="Deployment configuration not found"

            
            process_info = self.server_processes[server_id]
            process_info.status = DeploymentStatus.DEPLOYING
            
            logger.info(f"[DEPLOY] Deploying server: {server_info.name}")
            
            # Check if already running
            if await self._is_server_running(server_id):
                logger.info(f"[DEPLOY] Server {server_info.name} already running")
                return DeploymentResult(
                    server_id=server_id,
                    success=True,
                    status=DeploymentStatus.RUNNING,
                    message="Server already running"

            
            # Deploy based on server type
            if server_info.executable_path and server_info.executable_path.endswith('.py'):
                result = await self._deploy_python_server(server_info, config)
            elif server_info.executable_path and 'docker' in server_info.startup_command.lower():
                result = await self._deploy_docker_server(server_info, config)
            elif server_info.executable_path and server_info.executable_path.endswith(('.js', '.ts')):
                result = await self._deploy_nodejs_server(server_info, config)
            else:
                result = await self._deploy_generic_server(server_info, config)
            
            # Update process info
            if result.success:
                process_info.status = DeploymentStatus.RUNNING
                process_info.started_at = datetime.now()
                process_info.pid = result.process_id
                process_info.container_id = result.container_id
                
                # Update server status in registry
                server_info.status = ServerStatus.STARTING
                server_info.startup_time = datetime.now()
            else:
                process_info.status = DeploymentStatus.FAILED
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to deploy server {server_id}: {e}")
            return DeploymentResult(
                server_id=server_id,
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Deployment failed: {e}",
                error_details=str(e)

    
    async def _deploy_python_server(self, server_info: MCPServerInfo, config: DeploymentConfig) -> DeploymentResult:
        """Deploy a Python-based MCP server"""
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(config.environment_variables)
            
            # Add Python path
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{os.getcwd()}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = os.getcwd()
            
            # Prepare command
            cmd = [
                'python',
                server_info.executable_path,
                '--port', str(server_info.port),
                '--host', server_info.host

            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=os.getcwd()

            
            # Wait briefly to check if process starts successfully
            await asyncio.sleep(2)
            
            if process.poll() is not None:
                # Process has already terminated
                stdout, stderr = process.communicate()
                return DeploymentResult(
                    server_id=server_info.server_id,
                    success=False,
                    status=DeploymentStatus.FAILED,
                    message=f"Process terminated immediately: {stderr.decode()}"

            
            # Store process
            self.server_processes[server_info.server_id].process = process
            
            return DeploymentResult(
                server_id=server_info.server_id,
                success=True,
                status=DeploymentStatus.RUNNING,
                message="Python server deployed successfully",
                process_id=process.pid,
                startup_time=datetime.now()

            
        except Exception as e:
            return DeploymentResult(
                server_id=server_info.server_id,
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Python deployment failed: {e}"

    
    async def _deploy_nodejs_server(self, server_info: MCPServerInfo, config: DeploymentConfig) -> DeploymentResult:
        """Deploy a Node.js-based MCP server"""
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(config.environment_variables)
            
            # Determine command
            if server_info.startup_command:
                cmd = server_info.startup_command.split()
            elif server_info.executable_path.endswith('.ts'):
                cmd = ['npx', 'ts-node', server_info.executable_path]
            else:
                cmd = ['node', server_info.executable_path]
            
            # Add port and host if not in command
            if '--port' not in cmd:
                cmd.extend(['--port', str(server_info.port)])
            if '--host' not in cmd:
                cmd.extend(['--host', server_info.host])
            
            # Start process
            cwd = str(Path(server_info.executable_path).parent) if server_info.executable_path else os.getcwd()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=cwd

            
            # Wait briefly to check if process starts
            await asyncio.sleep(3)
            
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return DeploymentResult(
                    server_id=server_info.server_id,
                    success=False,
                    status=DeploymentStatus.FAILED,
                    message=f"Node.js process terminated: {stderr.decode()}"

            
            # Store process
            self.server_processes[server_info.server_id].process = process
            
            return DeploymentResult(
                server_id=server_info.server_id,
                success=True,
                status=DeploymentStatus.RUNNING,
                message="Node.js server deployed successfully",
                process_id=process.pid,
                startup_time=datetime.now()

            
        except Exception as e:
            return DeploymentResult(
                server_id=server_info.server_id,
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Node.js deployment failed: {e}"

    
    async def _deploy_docker_server(self, server_info: MCPServerInfo, config: DeploymentConfig) -> DeploymentResult:
        """Deploy a Docker-based MCP server"""
        if not self.docker_client:
            return DeploymentResult(
                server_id=server_info.server_id,
                success=False,
                status=DeploymentStatus.FAILED,
                message="Docker not available"

        
        try:
            # Build image if Dockerfile exists
            dockerfile_path = Path(server_info.executable_path)
            if dockerfile_path.exists():
                image_name = f"mcp-{server_info.name.lower()}"
                
                # Build image
                logger.info(f"[DOCKER] Building image {image_name}...")
                image, build_logs = self.docker_client.images.build(
                    path=str(dockerfile_path.parent),
                    dockerfile=dockerfile_path.name,
                    tag=image_name

            else:
                # Use pre-built image
                image_name = server_info.name
            
            # Prepare container configuration
            container_config = {
                'image': image_name,
                'ports': {f'{server_info.port}/tcp': server_info.port},
                'environment': config.environment_variables,
                'name': f"mcp-{server_info.name.lower()}",
                'detach': True,
                'remove': True  # Auto-remove when stopped

            
            # Add resource limits
            if config.resource_limits:
                container_config['mem_limit'] = config.resource_limits.get('memory', '128MB')
                container_config['cpu_quota'] = int(float(config.resource_limits.get('cpu', '0.1')) * 100000)
            
            # Start container
            container = self.docker_client.containers.run(**container_config)
            
            # Store container info
            self.server_processes[server_info.server_id].container_id = container.id
            
            return DeploymentResult(
                server_id=server_info.server_id,
                success=True,
                status=DeploymentStatus.RUNNING,
                message="Docker container deployed successfully",
                container_id=container.id,
                startup_time=datetime.now()

            
        except Exception as e:
            return DeploymentResult(
                server_id=server_info.server_id,
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Docker deployment failed: {e}"

    
    async def _deploy_generic_server(self, server_info: MCPServerInfo, config: DeploymentConfig) -> DeploymentResult:
        """Deploy a generic server using startup command"""
        try:
            if not server_info.startup_command:
                return DeploymentResult(
                    server_id=server_info.server_id,
                    success=False,
                    status=DeploymentStatus.FAILED,
                    message="No startup command specified"

            
            # Prepare environment
            env = os.environ.copy()
            env.update(config.environment_variables)
            
            # Parse and execute command
            cmd = server_info.startup_command.split()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=os.getcwd()

            
            # Wait briefly to check startup
            await asyncio.sleep(2)
            
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return DeploymentResult(
                    server_id=server_info.server_id,
                    success=False,
                    status=DeploymentStatus.FAILED,
                    message=f"Generic process terminated: {stderr.decode()}"

            
            # Store process
            self.server_processes[server_info.server_id].process = process
            
            return DeploymentResult(
                server_id=server_info.server_id,
                success=True,
                status=DeploymentStatus.RUNNING,
                message="Generic server deployed successfully",
                process_id=process.pid,
                startup_time=datetime.now()

            
        except Exception as e:
            return DeploymentResult(
                server_id=server_info.server_id,
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Generic deployment failed: {e}"

    
    async def _is_server_running(self, server_id: str) -> bool:
        """Check if a server is currently running"""
        process_info = self.server_processes.get(server_id)
        if not process_info:
            return False
        
        # Check process
        if process_info.process:
            return process_info.process.poll() is None
        
        # Check container
        if process_info.container_id and self.docker_client:
            try:
                container = self.docker_client.containers.get(process_info.container_id)
                return container.status == 'running'
            except:
                return False
        
        return False
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """Stop all servers in reverse order"""
        logger.info("[SHUTDOWN] Starting unified shutdown of all servers...")
        
        stop_results = {}
        
        try:
            for group in self.shutdown_order:
                # Stop servers in parallel within each group
                group_tasks = []
                for server_id in group:
                    if isinstance(server_id, list):
                        for srv_id in server_id:
                            task = asyncio.create_task(self.stop_server(srv_id))
                            group_tasks.append((srv_id, task))
                    else:
                        task = asyncio.create_task(self.stop_server(server_id))
                        group_tasks.append((server_id, task))
                
                # Wait for all servers in group to stop
                for server_id, task in group_tasks:
                    try:
                        result = await task
                        stop_results[server_id] = result
                    except Exception as e:
                        logger.error(f"[SHUTDOWN] Exception stopping {server_id}: {e}")
                        stop_results[server_id] = False
                
                # Small delay between groups
                await asyncio.sleep(1)
            
            successful = len([r for r in stop_results.values() if r])
            logger.info(f"[SHUTDOWN] Shutdown completed: {successful}/{len(stop_results)} successful")
            
        except Exception as e:
            logger.error(f"[ERROR] Unified shutdown failed: {e}")
            raise
        
        return stop_results
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop a single server"""
        try:
            server_info = await self.server_registry.get_server_by_id(server_id)
            if not server_info:
                return False
            
            process_info = self.server_processes.get(server_id)
            if not process_info:
                return True  # Already stopped
            
            process_info.status = DeploymentStatus.STOPPING
            logger.info(f"[SHUTDOWN] Stopping server: {server_info.name}")
            
            success = False
            
            # Stop process
            if process_info.process:
                success = await self._stop_process(process_info.process)
                process_info.process = None
                process_info.pid = None
            
            # Stop container
            if process_info.container_id and self.docker_client:
                success = await self._stop_container(process_info.container_id)
                process_info.container_id = None
            
            if success:
                process_info.status = DeploymentStatus.STOPPED
                server_info.status = ServerStatus.STOPPED
                logger.info(f"[SHUTDOWN] Stopped server: {server_info.name}")
            else:
                process_info.status = DeploymentStatus.FAILED
                
            return success
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to stop server {server_id}: {e}")
            return False
    
    async def _stop_process(self, process: subprocess.Popen) -> bool:
        """Stop a subprocess gracefully"""
        try:
            # Try graceful termination first
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
                return True
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                process.kill()
                process.wait(timeout=5)
                return True
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to stop process {process.pid}: {e}")
            return False
    
    async def _stop_container(self, container_id: str) -> bool:
        """Stop a Docker container gracefully"""
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to stop container {container_id}: {e}")
            return False
    
    async def restart_server(self, server_id: str) -> DeploymentResult:
        """Restart a specific server"""
        logger.info(f"[RESTART] Restarting server: {server_id}")
        
        # Stop first
        await self.stop_server(server_id)
        
        # Wait briefly
        await asyncio.sleep(2)
        
        # Start again
        result = await self.deploy_server(server_id)
        
        if result.success:
            process_info = self.server_processes[server_id]
            process_info.restart_count += 1
            process_info.last_restart = datetime.now()
            self.deployment_stats["auto_restarts"] += 1
        
        return result
    
    async def _process_monitoring_loop(self):
        """Background task to monitor all server processes"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                for server_id, process_info in self.server_processes.items():
                    if process_info.status == DeploymentStatus.RUNNING:
                        if not await self._is_server_running(server_id):
                            logger.warning(f"[MONITOR] Server {server_id} has stopped unexpectedly")
                            process_info.status = DeploymentStatus.STOPPED
                            
                            # Update server status in registry
                            server_info = await self.server_registry.get_server_by_id(server_id)
                            if server_info:
                                server_info.status = ServerStatus.STOPPED
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Process monitoring failed: {e}")
    
    async def _auto_restart_loop(self):
        """Background task for automatic restart of failed servers"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                for server_id, process_info in self.server_processes.items():
                    config = self.deployment_configs.get(server_id)
                    if not config or not config.auto_start:
                        continue
                    
                    # Check if server should be restarted
                    if (process_info.status == DeploymentStatus.STOPPED and 
                        config.restart_policy in ["always", "on-failure"] and
                        process_info.restart_count < config.max_restarts):
                        
                        # Check if enough time has passed since last restart
                        if (not process_info.last_restart or 
                            (datetime.now() - process_info.last_restart).total_seconds() > 60):
                            
                            logger.info(f"[AUTO_RESTART] Restarting failed server: {server_id}")
                            await self.restart_server(server_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Auto-restart loop failed: {e}")
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get comprehensive deployment status"""
        total_servers = len(self.server_processes)
        running_count = len([
            p for p in self.server_processes.values() 
            if p.status == DeploymentStatus.RUNNING

        
        return {
            "deployment_manager_status": "operational",
            "total_servers": total_servers,
            "running_servers": running_count,
            "deployment_percentage": (running_count / total_servers * 100) if total_servers > 0 else 0,
            "server_statuses": {
                server_id: {
                    "status": process.status.value,
                    "pid": process.pid,
                    "container_id": process.container_id,
                    "started_at": process.started_at.isoformat() if process.started_at else None,
                    "restart_count": process.restart_count,
                    "last_restart": process.last_restart.isoformat() if process.last_restart else None

                for server_id, process in self.server_processes.items()
            },
            "deployment_stats": self.deployment_stats,
            "deployment_order": self.deployment_order,
            "background_tasks": {
                "process_monitor": self.process_monitor_task is not None and not self.process_monitor_task.done(),
                "auto_restart": self.auto_restart_task is not None and not self.auto_restart_task.done()


    
    async def export_deployment_manifest(self) -> Dict[str, Any]:
        """Export deployment manifest for external orchestration"""
        manifest = {
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "deployment_mode": self.deployment_config.get("mode", "development"),
            "deployment_order": self.deployment_order,
            "servers": {}

        
        for server_id, config in self.deployment_configs.items():
            server_info = await self.server_registry.get_server_by_id(server_id)
            if server_info:
                manifest["servers"][server_id] = {
                    "name": server_info.name,
                    "tier": server_info.tier.value,
                    "protocol": server_info.protocol.value,
                    "host": server_info.host,
                    "port": server_info.port,
                    "startup_command": server_info.startup_command,
                    "auto_start": config.auto_start,
                    "restart_policy": config.restart_policy,
                    "resource_limits": config.resource_limits,
                    "dependencies": config.dependencies

        
        return manifest
    
    async def shutdown(self):
        """Shutdown the deployment manager"""
        logger.info("[SHUTDOWN] Shutting down Deployment Manager...")
        
        # Stop all servers first
        await self.stop_all_servers()
        
        # Cancel background tasks
        if self.process_monitor_task:
            self.process_monitor_task.cancel()
            try:
                await self.process_monitor_task
            except asyncio.CancelledError:
                pass
        
        if self.auto_restart_task:
            self.auto_restart_task.cancel()
            try:
                await self.auto_restart_task
            except asyncio.CancelledError:
                pass
        
        # Close Docker client if available
        if self.docker_client:
            self.docker_client.close()
        
        logger.info("[SHUTDOWN] Deployment Manager shutdown complete")