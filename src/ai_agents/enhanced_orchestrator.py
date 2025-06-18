#!/usr/bin/env python3
"""
Enhanced Flash Loan Orchestrator
Coordinates 21 MCP servers + 10 agents + orchestrator (32 total containers)
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
import aiohttp

class EnhancedOrchestrator:
    """Enhanced orchestrator with coordination for all containers"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.services = {}
        self.health_check_interval = 30
        self.coordination_tasks = []
        
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
          # Initialize service registry (will be populated by the builder)
        self.mcp_servers = []
        self.agents = []
        
    async def start(self):
        """Start the enhanced orchestrator"""
        self.logger.info("Starting Enhanced Flash Loan Orchestrator...")
        self.logger.info(f"Managing {len(self.mcp_servers)} MCP servers and {len(self.agents)} agents")
        
        # Initialize services
        await self.initialize_services()
        
        # Start coordination tasks
        await self.start_coordination()
        
        # Start health monitoring
        await self.start_health_monitoring()
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            self.logger.info("Enhanced Orchestrator running...")
    
    async def initialize_services(self):
        """Initialize all services with enhanced coordination"""
        self.logger.info("Initializing enhanced services...")
        
        # Register MCP servers
        for server_name, description, port in self.mcp_servers:
            self.services[server_name] = {
                'type': 'mcp_server',
                'description': description,
                'health_endpoint': f'http://{server_name}:{port}/health',
                'api_endpoint': f'http://{server_name}:{port}',
                'port': port,
                'status': 'unknown'
            }
        
        # Register agents
        for agent_name, description, port in self.agents:
            self.services[agent_name] = {
                'type': 'agent',
                'description': description,
                'health_endpoint': f'http://{agent_name}:{port}/health',
                'api_endpoint': f'http://{agent_name}:{port}',
                'port': port,
                'status': 'unknown'
            }
        
        self.logger.info(f"Registered {len(self.services)} services for coordination")
    
    async def start_coordination(self):
        """Start coordination tasks between all services"""
        self.logger.info("Starting service coordination...")
        
        # Start coordination loops
        asyncio.create_task(self.mcp_coordination_loop())
        asyncio.create_task(self.agent_coordination_loop())
        asyncio.create_task(self.cross_service_coordination())
        
    async def mcp_coordination_loop(self):
        """Coordinate between MCP servers"""
        while True:
            try:
                self.logger.debug("Running MCP server coordination...")
                
                # Coordinate data flow between MCP servers
                await self.coordinate_mcp_data_flow()
                
                await asyncio.sleep(10)  # Coordinate every 10 seconds
            except Exception as e:
                self.logger.error(f"MCP coordination error: {e}")
                await asyncio.sleep(5)
    
    async def agent_coordination_loop(self):
        """Coordinate between agents"""
        while True:
            try:
                self.logger.debug("Running agent coordination...")
                
                # Coordinate agent tasks
                await self.coordinate_agent_tasks()
                
                await asyncio.sleep(15)  # Coordinate every 15 seconds
            except Exception as e:
                self.logger.error(f"Agent coordination error: {e}")
                await asyncio.sleep(5)
    
    async def cross_service_coordination(self):
        """Coordinate between MCP servers and agents"""
        while True:
            try:
                self.logger.debug("Running cross-service coordination...")
                
                # Coordinate between MCP servers and agents
                await self.coordinate_mcp_agent_interaction()
                
                await asyncio.sleep(20)  # Coordinate every 20 seconds
            except Exception as e:
                self.logger.error(f"Cross-service coordination error: {e}")
                await asyncio.sleep(5)
    
    async def coordinate_mcp_data_flow(self):
        """Coordinate data flow between MCP servers"""
        # Example: Coordinate price feed -> risk manager -> portfolio
        try:
            # Get active MCP servers
            active_mcps = [name for name, config in self.services.items() 
                          if config['type'] == 'mcp_server' and config['status'] == 'healthy']
            
            if len(active_mcps) >= 2:
                # Coordinate data flow between servers
                self.logger.debug(f"Coordinating data flow between {len(active_mcps)} MCP servers")
                
        except Exception as e:
            self.logger.error(f"MCP data flow coordination error: {e}")
    
    async def coordinate_agent_tasks(self):
        """Coordinate tasks between agents"""
        try:
            # Get active agents
            active_agents = [name for name, config in self.services.items() 
                           if config['type'] == 'agent' and config['status'] == 'healthy']
            
            if len(active_agents) >= 2:
                # Coordinate agent tasks
                self.logger.debug(f"Coordinating tasks between {len(active_agents)} agents")
                
        except Exception as e:
            self.logger.error(f"Agent task coordination error: {e}")
    
    async def coordinate_mcp_agent_interaction(self):
        """Coordinate interaction between MCP servers and agents"""
        try:
            # Get healthy services
            healthy_mcps = [name for name, config in self.services.items() 
                          if config['type'] == 'mcp_server' and config['status'] == 'healthy']
            healthy_agents = [name for name, config in self.services.items() 
                            if config['type'] == 'agent' and config['status'] == 'healthy']
            
            if healthy_mcps and healthy_agents:
                # Coordinate MCP-Agent interactions
                self.logger.debug(f"Coordinating {len(healthy_mcps)} MCPs with {len(healthy_agents)} agents")
                
        except Exception as e:
            self.logger.error(f"MCP-Agent coordination error: {e}")
    
    async def start_health_monitoring(self):
        """Start health monitoring loop for all services"""
        asyncio.create_task(self.health_monitor_loop())
        
    async def health_monitor_loop(self):
        """Main health monitoring loop for all services"""
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
                async with aiohttp.ClientSession() as session:
                    async with session.get(config['health_endpoint'], timeout=10) as response:
                        if response.status == 200:
                            config['status'] = 'healthy'
                            self.logger.debug(f"Service {service_name} is healthy")
                        else:
                            config['status'] = 'unhealthy'
                            self.logger.warning(f"Service {service_name} returned {response.status}")
                            await self.heal_service(service_name)
            except Exception as e:
                config['status'] = 'unhealthy'
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
    orchestrator = EnhancedOrchestrator()
    asyncio.run(orchestrator.start())
