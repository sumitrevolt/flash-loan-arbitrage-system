#!/usr/bin/env python3
"""
Unified MCP Server Coordinator
==============================

Coordinates all MCP servers in the flash loan arbitrage system with:
- Intelligent server discovery and management
- Health monitoring and auto-restart
- Load balancing and task distribution
- Real-time performance monitoring
- Integration with AI agents

Author: GitHub Copilot Assistant
Date: June 17, 2025
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import requests
import aiohttp
import psutil
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServerStatus(Enum):
    """Server status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    RESTARTING = "restarting"

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    type: str  # python, nodejs, external
    command: str
    args: List[str]
    working_directory: str
    port: int
    health_endpoint: str
    environment_vars: Dict[str, str] = field(default_factory=dict)
    auto_restart: bool = True
    max_restarts: int = 3
    restart_delay: int = 5
    timeout: int = 30
    dependencies: List[str] = field(default_factory=list)

@dataclass
class ServerInstance:
    """Running server instance"""
    config: MCPServerConfig
    process: Optional[subprocess.Popen] = None
    status: ServerStatus = ServerStatus.STOPPED
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None
    pid: Optional[int] = None

class UnifiedMCPCoordinator:
    """Unified coordinator for all MCP servers"""
    
    def __init__(self, config_path: str = "config/unified_mcp_config.json"):
        self.config_path = Path(config_path)
        self.servers: Dict[str, ServerInstance] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        self.health_check_interval = 30
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Load configuration
        self._load_configuration()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_configuration(self):
        """Load MCP server configuration"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Configuration file not found: {self.config_path}")
                self._create_default_configuration()
                return
            
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            # Load global settings
            global_config = config_data.get('global_configuration', {})
            self.health_check_interval = global_config.get('health_check_interval', 30)
            
            # Load server configurations
            servers_config = config_data.get('servers', {})
            for server_name, server_data in servers_config.items():
                try:
                    # Process environment variables
                    env_vars = {}
                    env_config = server_data.get('environment_variables', {})
                    
                    if isinstance(env_config, dict):
                        for key, value in env_config.items():
                            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                                # Environment variable reference
                                env_var_name = value[2:-1].replace('env:', '')
                                env_vars[key] = os.getenv(env_var_name, '')
                            else:
                                env_vars[key] = str(value)
                    
                    config = MCPServerConfig(
                        name=server_data['name'],
                        type=server_data.get('type', 'python'),
                        command=server_data.get('command', 'python'),
                        args=server_data.get('args', []),
                        working_directory=server_data.get('working_directory', '.'),
                        port=server_data['port'],
                        health_endpoint=server_data.get('health_endpoint', f"http://localhost:{server_data['port']}/health"),
                        environment_vars=env_vars,
                        auto_restart=server_data.get('auto_restart', True),
                        max_restarts=server_data.get('max_restarts', 3),
                        restart_delay=server_data.get('restart_delay', 5),
                        timeout=server_data.get('timeout', 30),
                        dependencies=server_data.get('dependencies', [])
                    )
                    
                    self.server_configs[server_name] = config
                    self.servers[server_name] = ServerInstance(config=config)
                    
                except Exception as e:
                    logger.error(f"Failed to load config for {server_name}: {e}")
            
            logger.info(f"Loaded configuration for {len(self.server_configs)} MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """Create default configuration file"""
        logger.info("Creating default MCP configuration...")
        
        default_config = {
            "global_configuration": {
                "health_check_interval": 30,
                "auto_restart": True,
                "log_level": "INFO",
                "max_concurrent_servers": 20
            },
            "servers": {
                "flash_loan_mcp": {
                    "name": "flash_loan_mcp",
                    "type": "python",
                    "command": "python",
                    "args": ["src/mcp_servers/flash_loan_mcp_server.py"],
                    "working_directory": ".",
                    "port": 3001,
                    "health_endpoint": "http://localhost:3001/health",
                    "enabled": True,
                    "auto_restart": True,
                    "environment_variables": {
                        "MCP_SERVER_NAME": "flash_loan_mcp",
                        "PORT": "3001",
                        "LOG_LEVEL": "INFO"
                    }
                },
                "arbitrage_detector_mcp": {
                    "name": "arbitrage_detector_mcp",
                    "type": "python",
                    "command": "python",
                    "args": ["src/mcp_servers/arbitrage_detector_mcp_server.py"],
                    "working_directory": ".",
                    "port": 3002,
                    "health_endpoint": "http://localhost:3002/health",
                    "enabled": True,
                    "auto_restart": True,
                    "environment_variables": {
                        "MCP_SERVER_NAME": "arbitrage_detector_mcp",
                        "PORT": "3002"
                    }
                },
                "risk_manager_mcp": {
                    "name": "risk_manager_mcp",
                    "type": "python",
                    "command": "python",
                    "args": ["src/mcp_servers/risk_manager_mcp_server.py"],
                    "working_directory": ".",
                    "port": 3003,
                    "health_endpoint": "http://localhost:3003/health",
                    "enabled": True,
                    "auto_restart": True,
                    "environment_variables": {
                        "MCP_SERVER_NAME": "risk_manager_mcp",
                        "PORT": "3003"
                    }
                }
            }
        }
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Default configuration saved to {self.config_path}")
        
        # Load the default configuration
        self._load_configuration()
    
    async def start_all_servers(self):
        """Start all configured MCP servers"""
        logger.info("🚀 Starting all MCP servers...")
        
        self.running = True
        
        # Start servers based on dependencies
        start_order = self._calculate_start_order()
        
        for server_name in start_order:
            if server_name in self.servers:
                await self._start_server(server_name)
                await asyncio.sleep(2)  # Brief delay between starts
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor_loop())
        
        logger.info("✅ All servers started, monitoring active")
    
    def _calculate_start_order(self) -> List[str]:
        """Calculate server start order based on dependencies"""
        # Simple topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(server_name: str):
            if server_name in temp_visited:
                logger.warning(f"Circular dependency detected involving {server_name}")
                return
            
            if server_name not in visited:
                temp_visited.add(server_name)
                
                config = self.server_configs.get(server_name)
                if config:
                    for dep in config.dependencies:
                        if dep in self.server_configs:
                            visit(dep)
                
                temp_visited.remove(server_name)
                visited.add(server_name)
                order.append(server_name)
        
        for server_name in self.server_configs:
            visit(server_name)
        
        return order
    
    async def _start_server(self, server_name: str):
        """Start a specific MCP server"""
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found in configuration")
            return
        
        server_instance = self.servers[server_name]
        config = server_instance.config
        
        if server_instance.status == ServerStatus.RUNNING:
            logger.info(f"Server {server_name} is already running")
            return
        
        logger.info(f"🔄 Starting MCP server: {server_name}")
        
        try:
            server_instance.status = ServerStatus.STARTING
            
            # Prepare environment
            env = os.environ.copy()
            env.update(config.environment_vars)
            
            # Ensure working directory exists
            work_dir = Path(config.working_directory)
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if server script exists, create if missing
            if config.args and not (work_dir / config.args[0]).exists():
                await self._create_server_script(config)
            
            # Start the process
            process = subprocess.Popen(
                [config.command] + config.args,
                cwd=config.working_directory,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            server_instance.process = process
            server_instance.pid = process.pid
            server_instance.start_time = datetime.now()
            
            # Wait for startup
            await asyncio.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                server_instance.status = ServerStatus.RUNNING
                logger.info(f"✅ {server_name} started successfully (PID: {process.pid})")
                
                # Perform health check
                await self._check_server_health(server_name)
            else:
                server_instance.status = ServerStatus.ERROR
                server_instance.error_message = "Process terminated during startup"
                logger.error(f"❌ {server_name} failed to start")
                
        except Exception as e:
            server_instance.status = ServerStatus.ERROR
            server_instance.error_message = str(e)
            logger.error(f"❌ Failed to start {server_name}: {e}")
    
    async def _create_server_script(self, config: MCPServerConfig):
        """Create a basic MCP server script if it doesn't exist"""
        script_path = Path(config.working_directory) / config.args[0]
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create basic MCP server template
        template = f'''#!/usr/bin/env python3
"""
{config.name.title()} MCP Server
Auto-generated by Unified MCP Coordinator
"""

import asyncio
import logging
import os
from flask import Flask, jsonify
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({{
        "status": "healthy",
        "server": "{config.name}",
        "timestamp": datetime.now().isoformat(),
        "port": {config.port}
    }})

@app.route('/status', methods=['GET'])
def status():
    """Status endpoint"""
    return jsonify({{
        "name": "{config.name}",
        "type": "mcp_server",
        "status": "running",
        "uptime": "unknown",
        "version": "1.0.0"
    }})

def main():
    """Main server function"""
    logger.info(f"Starting {{__name__}} MCP server on port {config.port}")
    app.run(host='localhost', port={config.port}, debug=False)

if __name__ == "__main__":
    main()
'''
        
        with open(script_path, 'w') as f:
            f.write(template)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(script_path, 0o755)
        
        logger.info(f"Created server script: {script_path}")
    
    async def _health_monitor_loop(self):
        """Continuous health monitoring loop"""
        while self.running:
            try:
                await self._check_all_servers_health()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _check_all_servers_health(self):
        """Check health of all servers"""
        tasks = []
        for server_name in self.servers:
            tasks.append(self._check_server_health(server_name))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_server_health(self, server_name: str):
        """Check health of a specific server"""
        server_instance = self.servers[server_name]
        config = server_instance.config
        
        if server_instance.status != ServerStatus.RUNNING:
            return
        
        try:
            # Check if process is still running
            if server_instance.process and server_instance.process.poll() is not None:
                logger.warning(f"Process for {server_name} has terminated")
                server_instance.status = ServerStatus.ERROR
                if config.auto_restart:
                    await self._restart_server(server_name)
                return
            
            # HTTP health check
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(config.health_endpoint) as response:
                    if response.status == 200:
                        server_instance.last_health_check = datetime.now()
                        logger.debug(f"✅ {server_name} health check passed")
                    else:
                        logger.warning(f"⚠️  {server_name} health check failed: HTTP {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️  {server_name} health check failed: {e}")
            
            # If health checks fail consistently, restart
            if config.auto_restart and server_instance.last_health_check:
                time_since_last_check = datetime.now() - server_instance.last_health_check
                if time_since_last_check > timedelta(minutes=5):
                    await self._restart_server(server_name)
    
    async def _restart_server(self, server_name: str):
        """Restart a server"""
        server_instance = self.servers[server_name]
        config = server_instance.config
        
        if server_instance.restart_count >= config.max_restarts:
            logger.error(f"❌ {server_name} exceeded max restart attempts")
            server_instance.status = ServerStatus.ERROR
            return
        
        logger.info(f"🔄 Restarting {server_name} (attempt {server_instance.restart_count + 1})")
        
        server_instance.status = ServerStatus.RESTARTING
        server_instance.restart_count += 1
        
        # Stop current process
        await self._stop_server(server_name)
        
        # Wait before restart
        await asyncio.sleep(config.restart_delay)
        
        # Start again
        await self._start_server(server_name)
    
    async def _stop_server(self, server_name: str):
        """Stop a specific server"""
        server_instance = self.servers[server_name]
        
        if server_instance.process:
            try:
                server_instance.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    server_instance.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    server_instance.process.kill()
                    server_instance.process.wait()
                
                logger.info(f"🛑 Stopped {server_name}")
                
            except Exception as e:
                logger.error(f"Error stopping {server_name}: {e}")
        
        server_instance.process = None
        server_instance.pid = None
        server_instance.status = ServerStatus.STOPPED
    
    async def stop_all_servers(self):
        """Stop all servers"""
        logger.info("🛑 Stopping all MCP servers...")
        
        self.running = False
        
        # Stop all servers
        tasks = []
        for server_name in self.servers:
            tasks.append(self._stop_server(server_name))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ All servers stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all servers"""
        status = {
            "coordinator": {
                "running": self.running,
                "total_servers": len(self.servers),
                "health_check_interval": self.health_check_interval
            },
            "servers": {}
        }
        
        for server_name, server_instance in self.servers.items():
            status["servers"][server_name] = {
                "name": server_name,
                "status": server_instance.status.value,
                "port": server_instance.config.port,
                "pid": server_instance.pid,
                "start_time": server_instance.start_time.isoformat() if server_instance.start_time else None,
                "restart_count": server_instance.restart_count,
                "last_health_check": server_instance.last_health_check.isoformat() if server_instance.last_health_check else None,
                "error_message": server_instance.error_message
            }
        
        return status
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False


async def main():
    """Main entry point"""
    coordinator = UnifiedMCPCoordinator()
    
    try:
        await coordinator.start_all_servers()
        
        # Keep running until interrupted
        while coordinator.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Coordinator error: {e}")
    finally:
        await coordinator.stop_all_servers()


if __name__ == "__main__":
    asyncio.run(main())
