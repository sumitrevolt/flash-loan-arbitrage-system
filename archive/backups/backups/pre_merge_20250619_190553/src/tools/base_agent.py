#!/usr/bin/env python3
"""
Base Agent Framework
====================
Foundation class for all specialized agents in the MCP system.
"""

import os
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

import aiohttp
from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
agent_status_gauge = Gauge('agent_status', 'Agent status (1=healthy, 0=unhealthy)', ['agent_name'])
task_counter = Counter('agent_tasks_total', 'Total tasks processed', ['agent_name', 'task_type'])
task_duration_histogram = Histogram('agent_task_duration_seconds', 'Task duration', ['agent_name', 'task_type'])

class BaseAgent(ABC):
    """Base class for all MCP agents"""
    
    def __init__(self, agent_name: str, agent_port: int, agent_role: str):
        self.agent_name = agent_name
        self.agent_port = agent_port
        self.agent_role = agent_role
        
        # Flask app for HTTP endpoints
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Async HTTP session
        self.session = None
        
        # Redis connection
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        
        # MCP coordinator URL
        self.coordinator_url = os.getenv('MASTER_COORDINATOR_URL', 'http://localhost:4000')
        
        # Agent state
        self.is_running = False
        self.tasks_processed = 0
        self.last_heartbeat = None
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            agent_status_gauge.labels(agent_name=self.agent_name).set(1 if self.is_running else 0)
            return jsonify({
                'status': 'healthy' if self.is_running else 'starting',
                'agent': self.agent_name,
                'role': self.agent_role,
                'port': self.agent_port,
                'tasks_processed': self.tasks_processed,
                'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        @self.app.route('/command', methods=['POST'])
        def execute_command():
            """Execute a command"""
            data = request.get_json()
            command = data.get('command')
            
            if not command:
                return jsonify({'error': 'Command required'}), 400
                
            # Process command asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result: str = loop.run_until_complete(self.handle_command(command, data))
            
            return jsonify({
                'agent': self.agent_name,
                'command': command,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        @self.app.route('/task', methods=['POST'])
        def execute_task():
            """Execute a task"""
            data = request.get_json()
            task_type = data.get('type')
            task_data = data.get('data', {})
            
            if not task_type:
                return jsonify({'error': 'Task type required'}), 400
                
            # Process task asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            with task_duration_histogram.labels(agent_name=self.agent_name, task_type=task_type).time():
                result: str = loop.run_until_complete(self.handle_task(task_type, task_data))
                
            task_counter.labels(agent_name=self.agent_name, task_type=task_type).inc()
            self.tasks_processed += 1
            
            return jsonify({
                'agent': self.agent_name,
                'task_type': task_type,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Prometheus metrics endpoint"""
            return generate_latest()
            
        @self.app.route('/status', methods=['GET'])
        def status():
            """Detailed status endpoint"""
            return jsonify(self.get_status())
            
    async def initialize(self):
        """Initialize the agent"""
        self.session = aiohttp.ClientSession()
        self.is_running = True
        
        # Register with coordinator
        await self.register_with_coordinator()
        
        # Start heartbeat
        asyncio.create_task(self.heartbeat_loop())
        
        # Initialize agent-specific resources
        await self.on_initialize()
        
        logger.info(f"Agent {self.agent_name} initialized on port {self.agent_port}")
        
    async def register_with_coordinator(self):
        """Register this agent with the master coordinator"""
        try:
            registration_data = {
                'agent_name': self.agent_name,
                'agent_role': self.agent_role,
                'agent_port': self.agent_port,
                'capabilities': self.get_capabilities(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            async with self.session.post(
                f"{self.coordinator_url}/agents/register",
                json=registration_data
            ) as response:
                if response.status == 200:
                    logger.info(f"Agent {self.agent_name} registered with coordinator")
                else:
                    logger.error(f"Failed to register agent: {response.status}")
                    
        except Exception as e:
            logger.error(f"Registration error: {e}")
            
    async def heartbeat_loop(self):
        """Send periodic heartbeats to coordinator"""
        while self.is_running:
            try:
                self.last_heartbeat = datetime.utcnow()
                
                # Store heartbeat in Redis
                heartbeat_key = f"agent:heartbeat:{self.agent_name}"
                heartbeat_data = {
                    'timestamp': self.last_heartbeat.isoformat(),
                    'tasks_processed': self.tasks_processed,
                    'status': 'running'
                }
                
                self.redis_client.setex(
                    heartbeat_key,
                    60,  # TTL 60 seconds
                    json.dumps(heartbeat_data)
                )
                
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)
                
    async def handle_command(self, command: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a command"""
        logger.info(f"Agent {self.agent_name} handling command: {command}")
        
        # Common commands
        if command == 'restart':
            return await self.restart()
        elif command == 'shutdown':
            return await self.shutdown()
        elif command == 'status':
            return self.get_status()
        else:
            # Delegate to agent-specific handler
            return await self.on_command(command, data)
            
    async def handle_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a task"""
        logger.info(f"Agent {self.agent_name} handling task: {task_type}")
        
        # Delegate to agent-specific handler
        return await self.on_task(task_type, task_data)
        
    async def restart(self) -> Dict[str, Any]:
        """Restart the agent"""
        logger.info(f"Restarting agent {self.agent_name}")
        
        # Shutdown
        await self.on_shutdown()
        self.is_running = False
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Reinitialize
        await self.on_initialize()
        self.is_running = True
        
        return {'status': 'restarted', 'agent': self.agent_name}
        
    async def shutdown(self) -> Dict[str, Any]:
        """Shutdown the agent"""
        logger.info(f"Shutting down agent {self.agent_name}")
        
        self.is_running = False
        await self.on_shutdown()
        
        if self.session:
            await self.session.close()
            
        return {'status': 'shutdown', 'agent': self.agent_name}
        
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_name': self.agent_name,
            'agent_role': self.agent_role,
            'agent_port': self.agent_port,
            'is_running': self.is_running,
            'tasks_processed': self.tasks_processed,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'capabilities': self.get_capabilities(),
            'custom_status': self.get_custom_status()
        }
        
    @abstractmethod
    async def on_initialize(self):
        """Initialize agent-specific resources"""
        pass
        
    @abstractmethod
    async def on_shutdown(self):
        """Cleanup agent-specific resources"""
        pass
        
    @abstractmethod
    async def on_command(self, command: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent-specific commands"""
        pass
        
    @abstractmethod
    async def on_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent-specific tasks"""
        pass
        
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        pass
        
    @abstractmethod
    def get_custom_status(self) -> Dict[str, Any]:
        """Get agent-specific status"""
        pass
        
    def run(self):
        """Run the agent"""
        # Initialize in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.initialize())
        
        # Run Flask app
        self.app.run(host='0.0.0.0', port=self.agent_port, debug=False)


# Example implementation for testing
class ExampleAgent(BaseAgent):
    """Example agent implementation"""
    
    async def on_initialize(self):
        """Initialize agent-specific resources"""
        logger.info(f"Initializing {self.agent_name}")
        
    async def on_shutdown(self):
        """Cleanup agent-specific resources"""
        logger.info(f"Shutting down {self.agent_name}")
        
    async def on_command(self, command: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent-specific commands"""
        return {'message': f"Command '{command}' processed"}
        
    async def on_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent-specific tasks"""
        return {'message': f"Task '{task_type}' completed"}
        
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return ['example', 'test', 'demo']
        
    def get_custom_status(self) -> Dict[str, Any]:
        """Get agent-specific status"""
        return {'mode': 'example'}


if __name__ == '__main__':
    # Get configuration from environment
    agent_name = os.getenv('AGENT_NAME', 'example-agent')
    agent_port = int(os.getenv('AGENT_PORT', 5000))
    agent_role = os.getenv('AGENT_ROLE', 'example')
    
    # Create and run agent
    agent = ExampleAgent(agent_name, agent_port, agent_role)
    agent.run()
