#!/usr/bin/env python3
"""
Unified AI Agent System
=======================
Comprehensive agent framework combining role-specific capabilities with base functionality.
Consolidates ai_agent/agent.py and agents/base_agent.py into a single unified system.
"""

import os
import asyncio
import json
import logging
import threading
import time
import random
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import redis
from prometheus_client import Counter, Gauge, Histogram, generate_latest
import aiohttp

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Prometheus metrics
agent_status_gauge = Gauge('agent_status', 'Agent status (1=healthy, 0=unhealthy)', ['agent_name'])
task_counter = Counter('agent_tasks_total', 'Total tasks processed', ['agent_name', 'task_type'])
task_duration_histogram = Histogram('agent_task_duration_seconds', 'Task duration', ['agent_name', 'task_type'])

# Agent Configuration
ROLE = os.getenv('AGENT_ROLE', 'general')
AGENT_ID = os.getenv('AGENT_ID', '1')
AGENT_PORT = int(os.getenv('AGENT_PORT', '5000'))
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
MCP_COORDINATOR_URL = os.getenv('MCP_COORDINATOR_URL', 'http://localhost:9000')

# Role-specific capabilities
CAPABILITIES = {
    'code_indexer': [
        "code_analysis",
        "repo_understanding", 
        "pattern_recognition",
        "dependency_mapping",
        "architecture_analysis"
    ],
    'builder': [
        "project_compilation",
        "dependency_resolution",
        "build_optimization",
        "error_handling",
        "multi_language_support"
    ],
    'executor': [
        "trade_execution",
        "transaction_management",
        "risk_assessment",
        "performance_monitoring",
        "error_recovery"
    ],
    'coordinator': [
        "system_coordination",
        "task_distribution",
        "resource_management",
        "performance_optimization",
        "failure_handling"
    ],
    'planner': [
        "strategic_planning",
        "risk_analysis",
        "opportunity_identification",
        "resource_allocation",
        "performance_prediction"
    ]
}

# Claude API integration function
def call_claude(prompt):
    api_key = os.getenv("CLAUDE_API_KEY")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json"
    }
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

class AgentState:
    """Unified agent state management"""
    def __init__(self):
        self.is_running = True
        self.tasks = []
        self.connected_mcp_servers = {}
        self.last_heartbeat = datetime.now()
        self.health_status = "healthy"
        self.capabilities = CAPABILITIES.get(ROLE, [])
        self.active_tasks = {}
        self.task_history = []
        self.tasks_processed = 0

class UnifiedAgent:
    """Unified AI Agent combining all functionality"""
    
    def __init__(self, role: str = None, agent_id: str = None, port: int = None):
        self.role = role or ROLE
        self.agent_id = agent_id or AGENT_ID
        self.port = port or AGENT_PORT
        self.agent_name = f"{self.role}-{self.agent_id}"
        
        # Initialize state
        self.state = AgentState()
        self.logger = logging.getLogger(f"unified-agent-{self.role}-{self.agent_id}")
        
        # Flask app setup
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Redis and HTTP session
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        self.http_session = None
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup all Flask routes"""
        
        @self.app.route('/', methods=['GET'])
        def status():
            """Get agent status"""
            agent_status_gauge.labels(agent_name=self.agent_name).set(1 if self.state.is_running else 0)
            return jsonify({
                "status": "running" if self.state.is_running else "stopped",
                "role": self.role,
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "health": self.state.health_status,
                "capabilities": self.state.capabilities,
                "active_tasks": len(self.state.active_tasks),
                "pending_tasks": len(self.state.tasks),
                "tasks_processed": self.state.tasks_processed,
                "last_heartbeat": self.state.last_heartbeat.isoformat(),
                "connected_mcp_servers": list(self.state.connected_mcp_servers.keys())
            })

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": self.state.health_status,
                "timestamp": datetime.now().isoformat(),
                "role": self.role,
                "agent_id": self.agent_id,
                "is_running": self.state.is_running
            })

        @self.app.route('/capabilities', methods=['GET'])
        def get_capabilities():
            """Get agent capabilities"""
            return jsonify({
                "role": self.role,
                "agent_id": self.agent_id,
                "capabilities": self.state.capabilities
            })

        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Prometheus metrics endpoint"""
            return Response(generate_latest(), mimetype='text/plain')

        @self.app.route('/task/<task_id>', methods=['GET'])
        def get_task_status(task_id):
            """Get status of a specific task"""
            if task_id in self.state.active_tasks:
                return jsonify(self.state.active_tasks[task_id])
            else:
                # Check task history
                for task in self.state.task_history:
                    if task["task_id"] == task_id:
                        return jsonify(task)
                
                return jsonify({"error": "Task not found"}), 404

        @self.app.route('/tasks', methods=['GET'])
        def get_tasks():
            """Get all active and historical tasks"""
            return jsonify({
                "active_tasks": self.state.active_tasks,
                "pending_tasks": len(self.state.tasks),
                "task_history": self.state.task_history[-10:] if self.state.task_history else []
            })

        @self.app.route('/action', methods=['POST'])
        def action():
            """Handle action requests from MCP servers"""
            data = request.json
            action = data.get('action')
            task_id = data.get('task_id', f"task-{int(time.time())}")
            
            # Add timestamp to the task
            data['timestamp'] = datetime.now().isoformat()
            data['task_id'] = task_id
            
            result: str = self._handle_role_specific_action(action, data, task_id)
            return jsonify(result)

        @self.app.route('/command', methods=['POST'])
        def execute_command():
            """Execute a command"""
            data = request.get_json()
            command = data.get('command')
            
            if not command:
                return jsonify({'error': 'Command required'}), 400
                
            result: str = self._handle_command(command, data)
            
            return jsonify({
                'agent': self.agent_name,
                'command': command,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/task', methods=['POST'])
        def execute_task():
            """Execute a task"""
            data = request.get_json()
            task_type = data.get('type')
            task_data = data.get('data', {})
            
            if not task_type:
                return jsonify({'error': 'Task type required'}), 400
                
            with task_duration_histogram.labels(agent_name=self.agent_name, task_type=task_type).time():
                result: str = self._handle_task(task_type, task_data)
                
            task_counter.labels(agent_name=self.agent_name, task_type=task_type).inc()
            self.state.tasks_processed += 1
            
            return jsonify({
                'agent': self.agent_name,
                'task_type': task_type,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/connect', methods=['POST'])
        def connect_mcp_server():
            """Connect to an MCP server"""
            data = request.json
            server_type = data.get('server_type')
            server_url = data.get('server_url')
            
            if not server_type or not server_url:
                return jsonify({"error": "Missing server_type or server_url"}), 400
            
            self.state.connected_mcp_servers[server_type] = server_url
            self.logger.info(f"Connected to MCP server: {server_type} at {server_url}")
            
            return jsonify({
                "status": "connected",
                "server_type": server_type,
                "server_url": server_url,
                "connected_at": datetime.now().isoformat()
            })

        @self.app.route('/disconnect', methods=['POST'])
        def disconnect_mcp_server():
            """Disconnect from an MCP server"""
            data = request.json
            server_type = data.get('server_type')
            
            if not server_type:
                return jsonify({"error": "Missing server_type"}), 400
            
            if server_type in self.state.connected_mcp_servers:
                server_url = self.state.connected_mcp_servers.pop(server_type)
                self.logger.info(f"Disconnected from MCP server: {server_type} at {server_url}")
                
                return jsonify({
                    "status": "disconnected",
                    "server_type": server_type,
                    "disconnected_at": datetime.now().isoformat()
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Not connected to MCP server: {server_type}"
                }), 404

    def _handle_role_specific_action(self, action: str, data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Handle role-specific actions"""
        
        # Role-specific action handling
        if self.role == 'code_indexer':
            if action in ['index_project', 'analyze_code']:
                self.logger.info(f"Received {action} action: {data}")
                self.state.tasks.append(data)
                return {
                    "status": "accepted",
                    "task_id": task_id,
                    "message": f"Code {action.replace('_', ' ')} task added to queue"
                }
        
        elif self.role == 'builder':
            if action in ['build_project', 'compile_code']:
                self.logger.info(f"Received {action} action: {data}")
                self.state.tasks.append(data)
                return {
                    "status": "accepted", 
                    "task_id": task_id,
                    "message": f"{action.replace('_', ' ').title()} task added to queue"
                }
        
        elif self.role == 'executor':
            if action in ['execute_transaction', 'monitor_transaction']:
                self.logger.info(f"Received {action} action: {data}")
                self.state.tasks.append(data)
                return {
                    "status": "accepted",
                    "task_id": task_id,
                    "message": f"Transaction {action.split('_')[1]} task added to queue"
                }
        
        elif self.role == 'coordinator':
            if action in ['coordinate_workflow', 'distribute_tasks']:
                self.logger.info(f"Received {action} action: {data}")
                self.state.tasks.append(data)
                return {
                    "status": "accepted",
                    "task_id": task_id,
                    "message": f"{action.replace('_', ' ').title()} added to queue"
                }
        
        elif self.role == 'planner':
            if action in ['create_plan', 'optimize_strategy']:
                self.logger.info(f"Received {action} action: {data}")
                self.state.tasks.append(data)
                return {
                    "status": "accepted",
                    "task_id": task_id,
                    "message": f"{action.replace('_', ' ').title()} task added to queue"
                }
        
        # Handle generic or unknown actions
        self.logger.info(f"Received action {action} for role {self.role}: {data}")
        self.state.tasks.append(data)
        return {
            "status": "accepted",
            "task_id": task_id,
            "message": f"Task for action '{action}' added to queue"
        }

    def _handle_command(self, command: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle commands"""
        if command == 'restart':
            return self._restart()
        elif command == 'shutdown':
            return self._shutdown()
        elif command == 'status':
            return self._get_detailed_status()
        else:
            return {'message': f"Command '{command}' processed", 'status': 'success'}

    def _handle_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks"""
        # Add to task queue for processing
        task_id = f"task-{int(time.time())}"
        task = {
            'task_id': task_id,
            'type': task_type,
            'data': task_data,
            'timestamp': datetime.now().isoformat()
        }
        # Claude code analysis/generation integration
        if task_type in ['code_analysis', 'code_generation']:
            prompt = task_data.get('prompt', '')
            claude_result: str = call_claude(prompt)
            return {'message': f"Claude result for '{task_type}'", 'result': claude_result, 'task_id': task_id}
        self.state.tasks.append(task)
        return {'message': f"Task '{task_type}' added to queue", 'task_id': task_id}

    def _restart(self) -> Dict[str, Any]:
        """Restart agent"""
        self.logger.info(f"Restarting agent {self.agent_name}")
        self.state.is_running = False
        time.sleep(2)
        self.state.is_running = True
        return {'status': 'restarted', 'agent': self.agent_name}

    def _shutdown(self) -> Dict[str, Any]:
        """Shutdown agent"""
        self.logger.info(f"Shutting down agent {self.agent_name}")
        self.state.is_running = False
        return {'status': 'shutdown', 'agent': self.agent_name}

    def _get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed agent status"""
        return {
            'agent_name': self.agent_name,
            'role': self.role,
            'agent_id': self.agent_id,
            'port': self.port,
            'is_running': self.state.is_running,
            'tasks_processed': self.state.tasks_processed,
            'active_tasks': len(self.state.active_tasks),
            'pending_tasks': len(self.state.tasks),
            'last_heartbeat': self.state.last_heartbeat.isoformat(),
            'capabilities': self.state.capabilities,
            'connected_servers': list(self.state.connected_mcp_servers.keys()),
            'health_status': self.state.health_status
        }

    def register_with_coordinator(self):
        """Register with MCP coordinator"""
        try:
            response = requests.post(
                f"{MCP_COORDINATOR_URL}/register_agent", 
                json={
                    "role": self.role,
                    "agent_id": self.agent_id,
                    "agent_name": self.agent_name,
                    "port": self.port,
                    "status": "ready",
                    "capabilities": self.state.capabilities
                },
                timeout=5
            )
            if response.status_code == 200:
                self.logger.info(f"Successfully registered with MCP coordinator")
                self.state.connected_mcp_servers["coordinator"] = MCP_COORDINATOR_URL
                return True
            else:
                self.logger.warning(f"Failed to register with coordinator: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error registering with coordinator: {e}")
            return False

    def heartbeat_thread(self):
        """Heartbeat thread to keep connection with coordinator alive"""
        while self.state.is_running:
            try:
                if MCP_COORDINATOR_URL in self.state.connected_mcp_servers.values():
                    response = requests.post(
                        f"{MCP_COORDINATOR_URL}/agent_heartbeat", 
                        json={
                            "role": self.role,
                            "agent_id": self.agent_id,
                            "agent_name": self.agent_name,
                            "status": self.state.health_status,
                            "active_tasks": len(self.state.active_tasks)
                        },
                        timeout=5
                    )
                    if response.status_code == 200:
                        self.state.last_heartbeat = datetime.now()
                        self.logger.debug(f"Heartbeat sent to coordinator")
                        
                        # Store heartbeat in Redis
                        heartbeat_key = f"agent:heartbeat:{self.agent_name}"
                        heartbeat_data = {
                            'timestamp': self.state.last_heartbeat.isoformat(),
                            'tasks_processed': self.state.tasks_processed,
                            'status': 'running'
                        }
                        
                        self.redis_client.setex(
                            heartbeat_key,
                            60,  # TTL 60 seconds
                            json.dumps(heartbeat_data)
                        )
                    else:
                        self.logger.warning(f"Heartbeat failed: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Error in heartbeat: {e}")
            
            time.sleep(30)  # Send heartbeat every 30 seconds

    def run_agent_work(self):
        """Main agent work loop based on role"""
        
        work_functions = {
            'code_indexer': self._run_code_indexer,
            'builder': self._run_builder,
            'executor': self._run_executor,
            'coordinator': self._run_coordinator,
            'planner': self._run_planner
        }
        
        work_function = work_functions.get(self.role, self._run_generic_agent)
        work_function()

    def _run_code_indexer(self):
        """Code indexer specific work"""
        self.logger.info(f"Starting code indexer agent ({self.agent_id})...")
        while self.state.is_running:
            if self.state.tasks:
                task = self.state.tasks.pop(0)
                self.logger.info(f"Processing code indexing task: {task}")
                
                # Simulate processing time
                time.sleep(random.randint(2, 5))
                
                task_id = task.get("task_id")
                if task_id:
                    self.state.active_tasks[task_id] = {
                        "status": "completed",
                        "result": "Code indexed successfully",
                        "timestamp": datetime.now().isoformat()
                    }
                    self._add_to_task_history(task_id, "code_indexing", "completed")
            
            time.sleep(1)

    def _run_builder(self):
        """Builder specific work"""
        self.logger.info(f"Starting builder agent ({self.agent_id})...")
        while self.state.is_running:
            if self.state.tasks:
                task = self.state.tasks.pop(0)
                self.logger.info(f"Processing build task: {task}")
                
                # Simulate processing time
                time.sleep(random.randint(3, 8))
                
                task_id = task.get("task_id")
                if task_id:
                    self.state.active_tasks[task_id] = {
                        "status": "completed",
                        "result": "Build completed successfully",
                        "timestamp": datetime.now().isoformat()
                    }
                    self._add_to_task_history(task_id, "build", "completed")
            
            time.sleep(1)

    def _run_executor(self):
        """Executor specific work"""
        self.logger.info(f"Starting executor agent ({self.agent_id})...")
        while self.state.is_running:
            if self.state.tasks:
                task = self.state.tasks.pop(0)
                self.logger.info(f"Processing execution task: {task}")
                
                # Simulate processing time
                time.sleep(random.randint(1, 3))
                
                task_id = task.get("task_id")
                if task_id:
                    self.state.active_tasks[task_id] = {
                        "status": "completed",
                        "result": "Transaction executed successfully",
                        "timestamp": datetime.now().isoformat(),
                        "transaction_hash": "0x" + "".join([random.choice("0123456789abcdef") for _ in range(64)])
                    }
                    self._add_to_task_history(task_id, "execution", "completed")
            
            time.sleep(1)

    def _run_coordinator(self):
        """Coordinator specific work"""
        self.logger.info(f"Starting coordinator agent ({self.agent_id})...")
        while self.state.is_running:
            if self.state.tasks:
                task = self.state.tasks.pop(0)
                self.logger.info(f"Processing coordination task: {task}")
                
                # Simulate processing time
                time.sleep(random.randint(1, 2))
                
                task_id = task.get("task_id")
                if task_id:
                    self.state.active_tasks[task_id] = {
                        "status": "completed",
                        "result": "Coordination task completed",
                        "timestamp": datetime.now().isoformat()
                    }
                    self._add_to_task_history(task_id, "coordination", "completed")
            
            time.sleep(1)

    def _run_planner(self):
        """Planner specific work"""
        self.logger.info(f"Starting planner agent ({self.agent_id})...")
        while self.state.is_running:
            if self.state.tasks:
                task = self.state.tasks.pop(0)
                self.logger.info(f"Processing planning task: {task}")
                
                # Simulate processing time
                time.sleep(random.randint(2, 7))
                
                task_id = task.get("task_id")
                if task_id:
                    self.state.active_tasks[task_id] = {
                        "status": "completed",
                        "result": "Planning completed successfully",
                        "timestamp": datetime.now().isoformat(),
                        "plan": {
                            "steps": ["step1", "step2", "step3"],
                            "estimated_completion_time": "2025-06-14T23:59:59Z",
                            "resource_requirements": ["cpu", "memory", "disk"]
                        }
                    }
                    self._add_to_task_history(task_id, "planning", "completed")
            
            time.sleep(1)

    def _run_generic_agent(self):
        """Generic agent work"""
        self.logger.info(f"Starting generic agent ({self.agent_id})...")
        while self.state.is_running:
            if self.state.tasks:
                task = self.state.tasks.pop(0)
                self.logger.info(f"Processing task: {task}")
                
                # Simulate processing time
                time.sleep(random.randint(1, 3))
                
                task_id = task.get("task_id", "unknown")
                task_type = task.get("type", "unknown")
                
                self.state.active_tasks[task_id] = {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                
                self._add_to_task_history(task_id, task_type, "completed")
            
            time.sleep(1)

    def _add_to_task_history(self, task_id: str, task_type: str, status: str):
        """Add task to history"""
        self.state.task_history.append({
            "task_id": task_id,
            "type": task_type,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 tasks in history
        if len(self.state.task_history) > 100:
            self.state.task_history = self.state.task_history[-100:]

    def run(self):
        """Run the unified agent"""
        self.logger.info(f"Starting unified agent {self.agent_name} on port {self.port}")
        
        # Start the agent work thread
        agent_thread = threading.Thread(target=self.run_agent_work)
        agent_thread.daemon = True
        agent_thread.start()
        
        # Start the heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_thread)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        # Register with MCP coordinator
        register_thread = threading.Thread(target=self.register_with_coordinator)
        register_thread.daemon = True
        register_thread.start()
        
        # Run the Flask app
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

if __name__ == '__main__':
    # Create and run unified agent
    agent = UnifiedAgent()
    agent.run()
