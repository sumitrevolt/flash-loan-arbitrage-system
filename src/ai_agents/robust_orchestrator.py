#!/usr/bin/env python3
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
