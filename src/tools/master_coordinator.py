#!/usr/bin/env python3
"""
Master LangChain MCP Coordinator
================================
Consolidated coordinator for all MCP servers and services
Replaces multiple duplicate coordinators with a single unified system
"""

import os
import sys
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import requests
from pathlib import Path

# LangChain imports
try:
    from langchain_openai import OpenAI
    from langchain.agents import initialize_agent, AgentType
    from langchain.tools import Tool
    from langchain.memory import ConversationBufferMemory
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.schema import AgentAction, AgentFinish
    from langchain.callbacks import StdOutCallbackHandler
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available. Some features will be limited.")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_coordinator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    category: str  # 'coordinator', 'pricing', 'trading', 'monitoring'
    port: int
    docker_image: str
    dependencies: List[str]
    health_endpoint: str
    priority: int  # 1-5, 1 being highest priority
    
@dataclass
class SystemState:
    """Current system state"""
    active_servers: Set[str]
    failed_servers: Set[str]
    last_health_check: datetime
    total_operations: int
    successful_operations: int
    error_count: int

class MasterMCPCoordinator:
    """
    Master coordinator for all MCP servers
    Consolidates functionality from multiple duplicate coordinators
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self.system_state = SystemState(
            active_servers=set(),
            failed_servers=set(),
            last_health_check=datetime.now(),
            total_operations=0,
            successful_operations=0,
            error_count=0
        )
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.setup_core_servers()
        
    def setup_core_servers(self):
        """Setup core MCP servers (consolidated from 21+ to 7 essential ones)"""
        core_servers = [
            MCPServerConfig(
                name="pricing_coordinator",
                category="pricing",
                port=8001,
                docker_image="flash-loan/pricing-mcp:latest",
                dependencies=[],
                health_endpoint="/health",
                priority=1
            ),
            MCPServerConfig(
                name="trading_executor",
                category="trading", 
                port=8002,
                docker_image="flash-loan/trading-mcp:latest",
                dependencies=["pricing_coordinator"],
                health_endpoint="/health",
                priority=1
            ),
            MCPServerConfig(
                name="arbitrage_detector",
                category="trading",
                port=8003,
                docker_image="flash-loan/arbitrage-mcp:latest", 
                dependencies=["pricing_coordinator"],
                health_endpoint="/health",
                priority=2
            ),
            MCPServerConfig(
                name="monitoring_dashboard",
                category="monitoring",
                port=8004,
                docker_image="flash-loan/monitoring-mcp:latest",
                dependencies=["pricing_coordinator", "trading_executor"],
                health_endpoint="/health",
                priority=3
            ),
            MCPServerConfig(
                name="blockchain_connector",
                category="coordinator",
                port=8005,
                docker_image="flash-loan/blockchain-mcp:latest",
                dependencies=[],
                health_endpoint="/health",
                priority=1
            ),
            MCPServerConfig(
                name="dex_aggregator",
                category="trading",
                port=8006,
                docker_image="flash-loan/dex-mcp:latest",
                dependencies=["blockchain_connector"],
                health_endpoint="/health",
                priority=2
            ),
            MCPServerConfig(
                name="risk_manager",
                category="monitoring",
                port=8007,
                docker_image="flash-loan/risk-mcp:latest",
                dependencies=["trading_executor", "arbitrage_detector"],
                health_endpoint="/health",
                priority=1
            )
        ]
        
        for server in core_servers:
            self.servers[server.name] = server
            
    async def start_all_servers(self) -> bool:
        """Start all MCP servers in dependency order"""
        logger.info("🚀 Starting Master MCP Coordinator")
        logger.info(f"Starting {len(self.servers)} core MCP servers...")
        
        # Sort servers by priority and dependencies
        sorted_servers = sorted(
            self.servers.values(),
            key=lambda x: Any: Any: (x.priority, len(x.dependencies))
        )
        
        success_count = 0
        for server in sorted_servers:
            if await self.start_server(server):
                success_count += 1
                self.system_state.active_servers.add(server.name)
            else:
                self.system_state.failed_servers.add(server.name)
                
        logger.info(f"✅ Successfully started {success_count}/{len(self.servers)} servers")
        return success_count == len(self.servers)
        
    async def start_server(self, server: MCPServerConfig) -> bool:
        """Start a single MCP server"""
        try:
            logger.info(f"Starting {server.name} on port {server.port}")
            
            # Check if dependencies are running
            for dep in server.dependencies:
                if dep not in self.system_state.active_servers:
                    logger.warning(f"Dependency {dep} not active for {server.name}")
                    return False
            
            # Start Docker container
            cmd = [
                "docker", "run", "-d",
                "--name", server.name,
                "-p", f"{server.port}:{server.port}",
                "--network", "flash-loan-network",
                server.docker_image
            ]
            
            result: str = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to start {server.name}: {result.stderr}")
                return False
                
            # Wait for health check
            await asyncio.sleep(2)
            if await self.health_check(server):
                logger.info(f"✅ {server.name} started successfully")
                return True
            else:
                logger.error(f"❌ {server.name} failed health check")
                return False
                
        except Exception as e:
            logger.error(f"Error starting {server.name}: {e}")
            return False
            
    async def health_check(self, server: MCPServerConfig) -> bool:
        """Check health of a single server"""
        try:
            url = f"http://localhost:{server.port}{server.health_endpoint}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed for {server.name}: {e}")
            return False
            
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all servers"""
        logger.info("🔍 Performing system health check...")
        results = {}
        
        for name, server in self.servers.items():
            is_healthy = await self.health_check(server)
            results[name] = is_healthy
            
            if not is_healthy and name in self.system_state.active_servers:
                self.system_state.active_servers.remove(name)
                self.system_state.failed_servers.add(name)
                logger.warning(f"⚠️ {name} became unhealthy")
                
        self.system_state.last_health_check = datetime.now()
        healthy_count = sum(results.values())
        logger.info(f"📊 Health check: {healthy_count}/{len(results)} servers healthy")
        
        return results
        
    async def stop_all_servers(self):
        """Stop all MCP servers"""
        logger.info("🛑 Stopping all MCP servers...")
        
        for server_name in self.servers:
            try:
                subprocess.run(["docker", "stop", server_name], 
                             capture_output=True, text=True)
                subprocess.run(["docker", "rm", server_name], 
                             capture_output=True, text=True)
                logger.info(f"Stopped {server_name}")
            except Exception as e:
                logger.error(f"Error stopping {server_name}: {e}")
                
        self.system_state.active_servers.clear()
        self.system_state.failed_servers.clear()
        
    async def restart_failed_servers(self):
        """Restart any failed servers"""
        if not self.system_state.failed_servers:
            return
            
        logger.info(f"🔄 Restarting {len(self.system_state.failed_servers)} failed servers")
        
        failed_servers = list(self.system_state.failed_servers)
        self.system_state.failed_servers.clear()
        
        for server_name in failed_servers:
            server = self.servers[server_name]
            if await self.start_server(server):
                self.system_state.active_servers.add(server_name)
                logger.info(f"✅ Successfully restarted {server_name}")
            else:
                self.system_state.failed_servers.add(server_name)
                
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_servers": list(self.system_state.active_servers),
            "failed_servers": list(self.system_state.failed_servers),
            "total_servers": len(self.servers),
            "healthy_servers": len(self.system_state.active_servers),
            "last_health_check": self.system_state.last_health_check.isoformat(),
            "uptime_percentage": (
                len(self.system_state.active_servers) / len(self.servers) * 100
                if self.servers else 0
            ),
            "operations": {
                "total": self.system_state.total_operations,
                "successful": self.system_state.successful_operations,
                "error_count": self.system_state.error_count
            }
        }
        
    async def run_monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("🔄 Starting monitoring loop...")
        
        while True:
            try:
                # Health checks every 30 seconds
                await self.health_check_all()
                
                # Restart failed servers every 5 minutes
                if datetime.now().minute % 5 == 0:
                    await self.restart_failed_servers()
                
                # Log status every 10 minutes
                if datetime.now().minute % 10 == 0:
                    status = self.get_system_status()
                    logger.info(f"📊 System Status: {status['healthy_servers']}/{status['total_servers']} servers healthy")
                
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("Monitoring loop interrupted")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)

async def main():
    """Main entry point"""
    coordinator = MasterMCPCoordinator()
    
    try:
        # Start all servers
        if await coordinator.start_all_servers():
            logger.info("🎉 All MCP servers started successfully!")
            
            # Show initial status
            status = coordinator.get_system_status()
            print("\n" + "="*60)
            print("🚀 FLASH LOAN MCP SYSTEM - READY")
            print("="*60)
            print(f"Active Servers: {len(status['active_servers'])}")
            print(f"Failed Servers: {len(status['failed_servers'])}")
            print(f"System Health: {status['uptime_percentage']:.1f}%")
            print("="*60)
            
            # Start monitoring loop
            await coordinator.run_monitoring_loop()
            
        else:
            logger.error("❌ Failed to start all servers")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        await coordinator.stop_all_servers()
        
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
