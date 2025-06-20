#!/usr/bin/env python3
"""
MCP Server - AI Agent Connection Bridge
======================================

This script creates a bridge between MCP servers and AI agents running in Docker containers.
It facilitates communication, task coordination, and data exchange between the two systems.

Features:
- Auto-discovery of active MCP servers and AI agents
- Real-time connection management
- Task routing and coordination
- Health monitoring
- Event broadcasting
- Error handling and recovery

Author: GitHub Copilot Assistant
Date: June 18, 2025
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import aiohttp
import docker
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
import websockets
from queue import Queue
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_agent_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceEndpoint:
    """Represents an MCP server or AI agent endpoint"""
    name: str
    service_type: str  # 'mcp_server' or 'ai_agent'
    host: str
    port: int
    container_name: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "unknown"
    last_health_check: Optional[datetime] = None
    error_count: int = 0

class MCPAgentBridge:
    """Bridge between MCP servers and AI agents"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.mcp_servers: Dict[str, ServiceEndpoint] = {}
        self.ai_agents: Dict[str, ServiceEndpoint] = {}
        self.connections: Dict[str, Set[str]] = {}  # agent_name -> set of mcp_server_names
        self.task_queue = Queue()
        self.running = False
        
        # Redis for inter-service communication
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Connected to Redis for inter-service communication")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
            self.redis_client = None
    
    async def discover_services(self) -> None:
        """Discover running MCP servers and AI agents from Docker containers"""
        logger.info("🔍 Discovering MCP servers and AI agents...")
        
        try:
            containers = self.docker_client.containers.list(filters={'status': 'running'})
            
            for container in containers:
                name = container.name
                labels = container.labels or {}
                
                # Check if it's an MCP server
                if name.startswith('flashloan-mcp-') or 'mcp' in name.lower():
                    await self._register_mcp_server(container)
                
                # Check if it's an AI agent
                elif name.startswith('flashloan-agent-') or 'agent' in name.lower():
                    await self._register_ai_agent(container)
            
            logger.info(f"📊 Discovered {len(self.mcp_servers)} MCP servers and {len(self.ai_agents)} AI agents")
            
        except Exception as e:
            logger.error(f"❌ Error discovering services: {e}")
    
    async def _register_mcp_server(self, container) -> None:
        """Register an MCP server"""
        try:
            name = container.name
            # Extract port from container configuration
            ports = container.ports
            port = None
            host = 'localhost'
            
            for port_mapping in ports.values():
                if port_mapping:
                    port = int(port_mapping[0]['HostPort'])
                    break
            
            if port is None:
                logger.warning(f"⚠️ No port found for MCP server {name}")
                return
            
            # Determine capabilities based on server name
            capabilities = self._determine_mcp_capabilities(name)
            
            endpoint = ServiceEndpoint(
                name=name,
                service_type='mcp_server',
                host=host,
                port=port,
                container_name=name,
                capabilities=capabilities
            )
            
            # Check health
            health_status = await self._check_service_health(endpoint)
            endpoint.status = health_status
            endpoint.last_health_check = datetime.now()
            
            self.mcp_servers[name] = endpoint
            logger.info(f"📡 Registered MCP server: {name} on port {port} ({health_status})")
            
        except Exception as e:
            logger.error(f"❌ Error registering MCP server {container.name}: {e}")
    
    async def _register_ai_agent(self, container) -> None:
        """Register an AI agent"""
        try:
            name = container.name
            # Extract port from container configuration
            ports = container.ports
            port = None
            host = 'localhost'
            
            for port_mapping in ports.values():
                if port_mapping:
                    port = int(port_mapping[0]['HostPort'])
                    break
            
            if port is None:
                logger.warning(f"⚠️ No port found for AI agent {name}")
                return
            
            # Determine capabilities based on agent name
            capabilities = self._determine_agent_capabilities(name)
            
            endpoint = ServiceEndpoint(
                name=name,
                service_type='ai_agent',
                host=host,
                port=port,
                container_name=name,
                capabilities=capabilities
            )
            
            # Check health
            health_status = await self._check_service_health(endpoint)
            endpoint.status = health_status
            endpoint.last_health_check = datetime.now()
            
            self.ai_agents[name] = endpoint
            logger.info(f"🤖 Registered AI agent: {name} on port {port} ({health_status})")
            
        except Exception as e:
            logger.error(f"❌ Error registering AI agent {container.name}: {e}")
    
    def _determine_mcp_capabilities(self, name: str) -> List[str]:
        """Determine MCP server capabilities based on name"""
        capabilities = []
        
        if 'price-feed' in name or 'price' in name:
            capabilities.extend(['price_data', 'market_data', 'dex_prices'])
        if 'arbitrage' in name:
            capabilities.extend(['arbitrage_detection', 'opportunity_analysis'])
        if 'flash-loan' in name:
            capabilities.extend(['flash_loan_execution', 'loan_management'])
        if 'risk' in name:
            capabilities.extend(['risk_assessment', 'portfolio_analysis'])
        if 'blockchain' in name:
            capabilities.extend(['transaction_execution', 'smart_contracts'])
        if 'monitoring' in name:
            capabilities.extend(['system_monitoring', 'health_checks'])
        if 'data-analyzer' in name:
            capabilities.extend(['data_analysis', 'market_analysis'])
        if 'security' in name:
            capabilities.extend(['security_analysis', 'vulnerability_scanning'])
        if 'coordinator' in name:
            capabilities.extend(['task_coordination', 'workflow_management'])
        if 'portfolio' in name:
            capabilities.extend(['portfolio_management', 'position_tracking'])
        if 'notification' in name:
            capabilities.extend(['notifications', 'alerts', 'reporting'])
        if 'database' in name:
            capabilities.extend(['data_storage', 'data_retrieval'])
        if 'cache' in name:
            capabilities.extend(['caching', 'performance_optimization'])
        if 'liquidity' in name:
            capabilities.extend(['liquidity_analysis', 'pool_management'])
        if 'defi' in name:
            capabilities.extend(['defi_protocols', 'yield_farming'])
        if 'filesystem' in name:
            capabilities.extend(['file_operations', 'data_persistence'])
        if 'task-queue' in name:
            capabilities.extend(['task_management', 'job_scheduling'])
        if 'auth' in name:
            capabilities.extend(['authentication', 'authorization'])
        if 'api-client' in name:
            capabilities.extend(['external_apis', 'data_integration'])
        if 'file-processor' in name:
            capabilities.extend(['file_processing', 'data_transformation'])
        
        return capabilities
    
    def _determine_agent_capabilities(self, name: str) -> List[str]:
        """Determine AI agent capabilities based on name"""
        capabilities = []
        
        if 'analyzer' in name:
            capabilities.extend(['data_analysis', 'pattern_recognition', 'decision_making'])
        if 'executor' in name:
            capabilities.extend(['transaction_execution', 'trade_execution'])
        if 'risk-manager' in name:
            capabilities.extend(['risk_assessment', 'position_sizing', 'stop_loss'])
        if 'arbitrage-bot' in name:
            capabilities.extend(['arbitrage_execution', 'profit_optimization'])
        if 'monitor' in name:
            capabilities.extend(['system_monitoring', 'performance_tracking'])
        if 'data-collector' in name:
            capabilities.extend(['data_collection', 'market_data_gathering'])
        if 'coordinator' in name:
            capabilities.extend(['task_coordination', 'agent_management'])
        if 'liquidity-manager' in name:
            capabilities.extend(['liquidity_management', 'pool_optimization'])
        if 'reporter' in name:
            capabilities.extend(['report_generation', 'analytics', 'visualization'])
        if 'healer' in name:
            capabilities.extend(['system_recovery', 'error_handling', 'self_healing'])
        
        return capabilities
    
    async def _check_service_health(self, endpoint: ServiceEndpoint) -> str:
        """Check health of a service endpoint"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                health_url = f"http://{endpoint.host}:{endpoint.port}/health"
                async with session.get(health_url) as response:
                    if response.status == 200:
                        return "healthy"
                    else:
                        return f"unhealthy_http_{response.status}"
        except Exception as e:
            return f"unhealthy_{str(e)[:20]}"
    
    async def establish_connections(self) -> None:
        """Establish logical connections between AI agents and MCP servers"""
        logger.info("🔗 Establishing connections between AI agents and MCP servers...")
        
        for agent_name, agent in self.ai_agents.items():
            if agent.status != "healthy":
                continue
            
            connected_servers = set()
            
            # Match agent capabilities with MCP server capabilities
            for server_name, server in self.mcp_servers.items():
                if server.status != "healthy":
                    continue
                
                # Check if agent and server have complementary capabilities
                if self._are_capabilities_compatible(agent.capabilities, server.capabilities):
                    connected_servers.add(server_name)
                    logger.info(f"🔗 Connected {agent_name} to {server_name}")
            
            self.connections[agent_name] = connected_servers
            
            # Notify agent about available MCP servers
            await self._notify_agent_connections(agent, connected_servers)
        
        logger.info(f"✅ Established {sum(len(servers) for servers in self.connections.values())} connections")
    
    def _are_capabilities_compatible(self, agent_caps: List[str], server_caps: List[str]) -> bool:
        """Check if agent and server capabilities are compatible"""
        # Define compatibility rules
        compatibility_map = {
            'data_analysis': ['price_data', 'market_data', 'data_analysis'],
            'arbitrage_execution': ['arbitrage_detection', 'opportunity_analysis'],
            'transaction_execution': ['flash_loan_execution', 'transaction_execution'],
            'risk_assessment': ['risk_assessment', 'portfolio_analysis'],
            'system_monitoring': ['system_monitoring', 'health_checks'],
            'data_collection': ['price_data', 'market_data', 'external_apis'],
            'task_coordination': ['task_coordination', 'workflow_management'],
            'liquidity_management': ['liquidity_analysis', 'pool_management'],
            'pattern_recognition': ['data_analysis', 'market_analysis'],
            'profit_optimization': ['arbitrage_detection', 'yield_farming'],
            'system_recovery': ['system_monitoring', 'health_checks'],
            'report_generation': ['data_storage', 'notifications'],
        }
        
        for agent_cap in agent_caps:
            if agent_cap in compatibility_map:
                compatible_server_caps = compatibility_map[agent_cap]
                if any(server_cap in compatible_server_caps for server_cap in server_caps):
                    return True
        
        return False
    
    async def _notify_agent_connections(self, agent: ServiceEndpoint, connected_servers: Set[str]) -> None:
        """Notify an AI agent about its connected MCP servers"""
        try:
            server_info = []
            for server_name in connected_servers:
                server = self.mcp_servers[server_name]
                server_info.append({
                    'name': server.name,
                    'host': server.host,
                    'port': server.port,
                    'capabilities': server.capabilities,
                    'status': server.status
                })
            
            notification_data = {
                'type': 'mcp_servers_connected',
                'servers': server_info,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send notification to agent
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                notify_url = f"http://{agent.host}:{agent.port}/mcp_connection"
                async with session.post(notify_url, json=notification_data) as response:
                    if response.status == 200:
                        logger.info(f"✅ Notified {agent.name} about {len(connected_servers)} MCP servers")
                    else:
                        logger.warning(f"⚠️ Failed to notify {agent.name}: HTTP {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Error notifying agent {agent.name}: {e}")
    
    async def start_health_monitoring(self) -> None:
        """Start health monitoring for all services"""
        logger.info("💓 Starting health monitoring...")
        
        while self.running:
            try:
                # Check MCP servers
                for server_name, server in self.mcp_servers.items():
                    old_status = server.status
                    new_status = await self._check_service_health(server)
                    server.status = new_status
                    server.last_health_check = datetime.now()
                    
                    if old_status != new_status:
                        logger.info(f"🔄 {server_name} status changed: {old_status} -> {new_status}")
                        if new_status == "healthy" and old_status != "healthy":
                            # Re-establish connections if server becomes healthy
                            await self.establish_connections()
                
                # Check AI agents
                for agent_name, agent in self.ai_agents.items():
                    old_status = agent.status
                    new_status = await self._check_service_health(agent)
                    agent.status = new_status
                    agent.last_health_check = datetime.now()
                    
                    if old_status != new_status:
                        logger.info(f"🔄 {agent_name} status changed: {old_status} -> {new_status}")
                        if new_status == "healthy" and old_status != "healthy":
                            # Re-establish connections if agent becomes healthy
                            await self.establish_connections()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in health monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def start_task_router(self) -> None:
        """Start task routing between agents and MCP servers"""
        logger.info("🚀 Starting task router...")
        
        while self.running:
            try:
                # Check Redis for inter-service messages
                if self.redis_client:
                    try:
                        # Subscribe to task routing channels
                        pubsub = self.redis_client.pubsub()
                        pubsub.subscribe('agent_to_mcp', 'mcp_to_agent', 'task_coordination')
                        
                        for message in pubsub.listen():
                            if message['type'] == 'message':
                                await self._handle_routing_message(message)
                    except Exception as e:
                        logger.warning(f"⚠️ Redis routing error: {e}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error in task router: {e}")
                await asyncio.sleep(5)
    
    async def _handle_routing_message(self, message) -> None:
        """Handle routing messages between services"""
        try:
            data = json.loads(message['data'])
            channel = message['channel']
            
            if channel == 'agent_to_mcp':
                # Route message from agent to appropriate MCP server
                await self._route_agent_to_mcp(data)
            elif channel == 'mcp_to_agent':
                # Route message from MCP server to appropriate agent
                await self._route_mcp_to_agent(data)
            elif channel == 'task_coordination':
                # Handle task coordination
                await self._handle_task_coordination(data)
                
        except Exception as e:
            logger.error(f"❌ Error handling routing message: {e}")
    
    async def _route_agent_to_mcp(self, data: Dict[str, Any]) -> None:
        """Route message from agent to MCP server"""
        try:
            source_agent = data.get('source_agent')
            target_capability = data.get('target_capability')
            message_data = data.get('message')
            
            # Find appropriate MCP server
            target_servers = []
            for server_name, server in self.mcp_servers.items():
                if (server.status == "healthy" and 
                    target_capability in server.capabilities and
                    server_name in self.connections.get(source_agent, set())):
                    target_servers.append(server)
            
            # Send to best available server
            if target_servers:
                target_server = target_servers[0]  # Simple selection, could be improved
                
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    url = f"http://{target_server.host}:{target_server.port}/agent_message"
                    async with session.post(url, json=message_data) as response:
                        if response.status == 200:
                            logger.info(f"📤 Routed message from {source_agent} to {target_server.name}")
                        else:
                            logger.warning(f"⚠️ Failed to route message: HTTP {response.status}")
            
        except Exception as e:
            logger.error(f"❌ Error routing agent to MCP: {e}")
    
    async def _route_mcp_to_agent(self, data: Dict[str, Any]) -> None:
        """Route message from MCP server to agent"""
        try:
            source_server = data.get('source_server')
            target_agent = data.get('target_agent')
            message_data = data.get('message')
            
            if target_agent in self.ai_agents:
                agent = self.ai_agents[target_agent]
                if agent.status == "healthy":
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        url = f"http://{agent.host}:{agent.port}/mcp_message"
                        async with session.post(url, json=message_data) as response:
                            if response.status == 200:
                                logger.info(f"📤 Routed message from {source_server} to {target_agent}")
                            else:
                                logger.warning(f"⚠️ Failed to route message: HTTP {response.status}")
            
        except Exception as e:
            logger.error(f"❌ Error routing MCP to agent: {e}")
    
    async def _handle_task_coordination(self, data: Dict[str, Any]) -> None:
        """Handle task coordination between services"""
        try:
            task_type = data.get('task_type')
            
            if task_type == 'arbitrage_opportunity':
                # Coordinate arbitrage opportunity handling
                await self._coordinate_arbitrage_task(data)
            elif task_type == 'risk_assessment':
                # Coordinate risk assessment
                await self._coordinate_risk_task(data)
            elif task_type == 'data_analysis':
                # Coordinate data analysis
                await self._coordinate_analysis_task(data)
            
        except Exception as e:
            logger.error(f"❌ Error in task coordination: {e}")
    
    async def _coordinate_arbitrage_task(self, data: Dict[str, Any]) -> None:
        """Coordinate arbitrage opportunity task"""
        # Find arbitrage detection MCP server and arbitrage bot agent
        arbitrage_servers = [s for s in self.mcp_servers.values() 
                           if 'arbitrage_detection' in s.capabilities and s.status == "healthy"]
        arbitrage_agents = [a for a in self.ai_agents.values() 
                          if 'arbitrage_execution' in a.capabilities and a.status == "healthy"]
        
        if arbitrage_servers and arbitrage_agents:
            logger.info("🎯 Coordinating arbitrage opportunity task")
            # Implementation would involve coordinating between the services
    
    async def _coordinate_risk_task(self, data: Dict[str, Any]) -> None:
        """Coordinate risk assessment task"""
        # Implementation for risk coordination
        pass
    
    async def _coordinate_analysis_task(self, data: Dict[str, Any]) -> None:
        """Coordinate data analysis task"""
        # Implementation for analysis coordination
        pass
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get current status report"""
        healthy_mcp = sum(1 for s in self.mcp_servers.values() if s.status == "healthy")
        healthy_agents = sum(1 for a in self.ai_agents.values() if a.status == "healthy")
        total_connections = sum(len(servers) for servers in self.connections.values())
        
        return {
            'mcp_servers': {
                'total': len(self.mcp_servers),
                'healthy': healthy_mcp,
                'unhealthy': len(self.mcp_servers) - healthy_mcp
            },
            'ai_agents': {
                'total': len(self.ai_agents),
                'healthy': healthy_agents,
                'unhealthy': len(self.ai_agents) - healthy_agents
            },
            'connections': {
                'total': total_connections,
                'active_agents': len([a for a in self.connections.keys() 
                                    if self.ai_agents[a].status == "healthy"])
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def start(self) -> None:
        """Start the MCP-Agent bridge"""
        logger.info("🚀 Starting MCP-Agent Bridge...")
        self.running = True
        
        # Discover services
        await self.discover_services()
        
        # Establish connections
        await self.establish_connections()
        
        # Start monitoring and routing
        tasks = [
            asyncio.create_task(self.start_health_monitoring()),
            asyncio.create_task(self.start_task_router())
        ]
        
        logger.info("✅ MCP-Agent Bridge started successfully")
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down MCP-Agent Bridge...")
            self.running = False
            for task in tasks:
                task.cancel()
        except Exception as e:
            logger.error(f"❌ Critical error in bridge: {e}")
            self.running = False

async def main():
    """Main function to run the bridge"""
    bridge = MCPAgentBridge()
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("👋 Bridge shutdown requested")
    except Exception as e:
        logger.error(f"❌ Failed to start bridge: {e}")
    finally:
        logger.info("🏁 MCP-Agent Bridge stopped")

if __name__ == "__main__":
    asyncio.run(main())
