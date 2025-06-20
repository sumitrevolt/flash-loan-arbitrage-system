#!/usr/bin/env python3
"""
Simplified MCP Server Coordinator (Docker Orchestration Support for 121 MCP Agents)
=========================================================

A simplified version of the MCP coordinator that manages servers
using Docker orchestration.
"""

import asyncio
import logging
import os
import sys
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_coordinator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """Configuration for individual MCP server"""
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

@dataclass
class ServerStatus:
    """Runtime status of MCP server"""
    name: str
    status: str
    port: int
    pid: Optional[int]
    last_heartbeat: Optional[datetime]
    restart_count: int

class SimplifiedMCPCoordinator:
    """Simplified MCP Server Coordinator without Docker"""
    
    def __init__(self) -> None:
        self.base_path = Path("C:/Users/Ratanshila/Documents/flash loan")
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.server_stats: Dict[str, ServerStatus] = {}
        
        # Define simplified server architecture
        self.servers = {
            'task_manager': MCPServerConfig(
                name='Task Manager MCP',
                category='task_management',
                path='mcp_servers/task_management/mcp-taskmanager/index.ts',
                port=8009,
                command=['node', 'mcp_servers/task_management/mcp-taskmanager/index.ts'],
                health_endpoint='/health',
                required=True,
                dependencies=[]
            ),
            'flash_loan_executor': MCPServerConfig(
                name='Flash Loan Executor MCP',
                category='execution',
                path='mcp_servers/execution/working_unified_flash_loan_mcp_server.py',
                port=8005,
                command=['python', 'mcp_servers/execution/working_unified_flash_loan_mcp_server.py'],
                health_endpoint='/health',
                required=True,
                dependencies=[]
            ),
            'price_oracle': MCPServerConfig(
                name='Price Oracle MCP',
                category='data_providers',
                path='mcp_servers/data_providers/price-oracle-mcp-server/price_oracle_mcp_server.py',
                port=8006,
                command=['python', 'mcp_servers/data_providers/price-oracle-mcp-server/price_oracle_mcp_server.py'],
                health_endpoint='/health',
                required=True,
                dependencies=[]
            )
        }

    async def initialize_infrastructure(self) -> bool:
        """Initialize basic infrastructure"""
        try:
            logger.info("🔧 Initializing infrastructure...")
            
            # Initialize HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            logger.info("✅ Infrastructure initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Infrastructure initialization failed: {e}")
            return False

    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all MCP servers"""
        logger.info("🚀 Starting Simplified MCP Architecture")
        logger.info("=" * 50)
        
        if not await self.initialize_infrastructure():
            logger.error("❌ Infrastructure initialization failed")
            return {}
        
        results: Dict[str, bool] = {}
        self.running = True
        
        for server_key, config in self.servers.items():
            if config.required:
                logger.info(f"🚀 Starting {config.name} (Port {config.port})...")
                
                if config.startup_delay > 0:
                    logger.info(f"⏳ Waiting {config.startup_delay}s...")
                    await asyncio.sleep(config.startup_delay)
                
                success = await self._start_server_process(server_key, config)
                results[server_key] = success
                
                if success:
                    logger.info(f"✅ {config.name} started successfully")
                else:
                    logger.error(f"❌ Failed to start {config.name}")
        
        # Start health monitoring
        asyncio.create_task(self._health_monitoring_loop())
        
        # Final health check
        await asyncio.sleep(5)
        health_results = await self._comprehensive_health_check()
        
        self._print_startup_summary(results, health_results)
        return results

    async def _start_server_process(self, server_key: str, config: MCPServerConfig) -> bool:
        """Start server as a subprocess"""
        try:
            # Check if port is already in use
            if self._is_port_in_use(config.port):
                logger.warning(f"Port {config.port} already in use for {config.name}")
                if await self._check_server_health(server_key, config):
                    logger.info(f"{config.name} already running")
                    return True
                else:
                    self._kill_process_on_port(config.port)
                    await asyncio.sleep(2)
            
            # Start the server process
            logger.info(f"Executing: {' '.join(config.command)}")
            
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
                *config.command,
                cwd=self.base_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict(os.environ), 'PORT': str(config.port)}
            )
            
            config.process = process
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Check if process is still running
            if process.returncode is not None:
                _, stderr = await process.communicate()
                logger.error(f"{config.name} process died. STDERR: {stderr.decode()}")
                return False
            
            # Initialize server status
            self.server_stats[server_key] = ServerStatus(
                name=config.name,
                status='starting',
                port=config.port,
                pid=process.pid,
                last_heartbeat=datetime.now(),
                restart_count=0
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {config.name}: {e}")
            return False

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use"""
        for conn in psutil.net_connections():
            if (hasattr(conn, 'laddr') and 
                hasattr(conn.laddr, 'port') and 
                getattr(conn.laddr, 'port', None) == port):  # type: ignore
                return True
        return False
    
    def _kill_process_on_port(self, port: int) -> None:
        """Kill process using specific port"""
        for conn in psutil.net_connections():
            if (hasattr(conn, 'laddr') and 
                hasattr(conn.laddr, 'port') and 
                getattr(conn.laddr, 'port', None) == port and  # type: ignore
                hasattr(conn, 'pid') and conn.pid):
                try:
                    process = psutil.Process(conn.pid)
                    process.terminate()
                    logger.info(f"Killed process {conn.pid} on port {port}")
                except Exception as e:
                    logger.warning(f"Could not kill process on port {port}: {e}")

    async def _check_server_health(self, server_key: str, config: MCPServerConfig) -> bool:
        """Health check for individual server"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"http://localhost:{config.port}{config.health_endpoint}"
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    if server_key in self.server_stats:
                        self.server_stats[server_key].status = 'running'
                        self.server_stats[server_key].last_heartbeat = datetime.now()
                    return True
                return False
                    
        except Exception as e:
            logger.debug(f"{config.name} health check failed: {e}")
            return False

    async def _comprehensive_health_check(self) -> Dict[str, bool]:
        """Comprehensive health check of all servers"""
        results: Dict[str, bool] = {}
        
        for server_key, config in self.servers.items():
            if config.required:
                healthy = await self._check_server_health(server_key, config)
                results[server_key] = healthy
        
        return results

    async def _health_monitoring_loop(self) -> None:
        """Continuous health monitoring"""
        logger.info("💓 Starting health monitoring loop")
        
        while self.running:
            try:
                for server_key, config in self.servers.items():
                    if config.required and server_key in self.server_stats:
                        healthy = await self._check_server_health(server_key, config)
                        
                        if not healthy:
                            logger.warning(f"⚠️ {config.name} is unhealthy")
                        
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)

    def _print_startup_summary(self, start_results: Dict[str, bool], health_results: Dict[str, bool]) -> None:
        """Print startup summary"""
        logger.info("📊 STARTUP SUMMARY")
        logger.info("=" * 40)
        
        for server_key, config in self.servers.items():
            start_status = "✅" if start_results.get(server_key, False) else "❌"
            health_status = "🟢" if health_results.get(server_key, False) else "🔴"
            logger.info(f"  {start_status} {health_status} {config.name} (Port {config.port})")
        
        successful_starts = sum(start_results.values())
        total_servers = len([s for s in self.servers.values() if s.required])
        
        logger.info(f"\n📈 SYSTEM STATUS: {successful_starts}/{total_servers} servers operational")

    async def stop_all_servers(self) -> None:
        """Stop all MCP servers gracefully"""
        logger.info("🛑 Stopping all MCP servers...")
        self.running = False
        
        for config in self.servers.values():
            if hasattr(config, 'process') and config.process:
                try:
                    config.process.terminate()
                    await asyncio.wait_for(config.process.wait(), timeout=10)
                    logger.info(f"✅ Stopped {config.name}")
                except Exception as e:
                    logger.error(f"Error stopping {config.name}: {e}")
        
        if self.session:
            await self.session.close()

async def main() -> None:
    """Main entry point"""
    coordinator = SimplifiedMCPCoordinator()
    
    try:
        await coordinator.start_all_servers()
        
        # Keep running
        while coordinator.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await coordinator.stop_all_servers()

if __name__ == "__main__":
    asyncio.run(main())
