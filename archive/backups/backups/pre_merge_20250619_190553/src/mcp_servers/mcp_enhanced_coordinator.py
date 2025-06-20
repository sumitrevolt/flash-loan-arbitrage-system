#!/usr/bin/env python3
"""
MCP Enhanced Coordinator
Robust coordination between MCP servers and AI agents

Key capabilities:
- Multi-server registration and health monitoring
- AI agent task distribution and management
- Cross-system communication facilitation
- Robust failure handling and recovery
"""

import asyncio
import json
import sys
import logging
import os
import time
import random
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(os.path.join("logs", "mcp_enhanced_coordinator.log"))
    ]
)
logger = logging.getLogger("mcp-enhanced-coordinator")

class MCPEnhancedCoordinator:
    """Enhanced Coordinator for MCP Servers and AI Agents"""
    
    def __init__(self):
        self.name = "mcp-enhanced-coordinator"
        self.version = "1.0.0"
        self.tools = []
        self.registered_servers = {}
        self.registered_agents = {}
        self.active_tasks = {}
        self.task_history = []
        self.system_status = "operational"
        self.last_health_check = datetime.now()
        self.config = self._load_config()
        self._setup_tools()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load coordinator configuration"""
        config_path = os.getenv("MCP_CONFIG_PATH", "config/unified_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found at {config_path}, using defaults")
                return {
                    "coordinator_port": 9000,
                    "required_servers": [
                        "ai_integration_context7",
                        "ai_integration_copilot",
                        "blockchain_integration_matic",
                        "blockchain_integration_evm",
                        "blockchain_integration_foundry",
                        "flash_loan_aave",
                        "execution_contract",
                        "execution_flash_loan",
                        "data_provider_price",
                        "data_provider_dex",
                        "data_provider_events",
                        "coordination_bridge",
                        "pricing_real_time",
                        "quality_checker",
                        "recovery_manager",
                        "market_analysis",
                        "dex_services",
                        "risk_management",
                        "production_manager",
                        "monitoring_status",
                        "task_management"
                    ],
                    "required_agent_roles": [
                        "code_indexer",
                        "builder",
                        "executor",
                        "coordinator",
                        "planner"
                    ],
                    "heartbeat_interval_sec": 30,
                    "server_timeout_sec": 120,
                    "agent_timeout_sec": 180
                }
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {
                "coordinator_port": 9000,
                "required_servers": [],
                "required_agent_roles": [],
                "heartbeat_interval_sec": 30,
                "server_timeout_sec": 120,
                "agent_timeout_sec": 180
            }
    
    def _setup_tools(self):
        """Setup available tools for the coordinator"""
        self.tools = [
            {
                "name": "register_server",
                "description": "Register an MCP server with the coordinator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string"},
                        "server_type": {"type": "string"},
                        "server_url": {"type": "string"},
                        "capabilities": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["server_name", "server_type", "server_url"]
                }
            },
            {
                "name": "register_agent",
                "description": "Register an AI agent with the coordinator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "port": {"type": "integer"},
                        "status": {"type": "string"},
                        "capabilities": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["role", "agent_id", "port", "status"]
                }
            },
            {
                "name": "server_heartbeat",
                "description": "MCP server heartbeat to maintain active status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string"},
                        "status": {"type": "string"},
                        "stats": {"type": "object"}
                    },
                    "required": ["server_name", "status"]
                }
            },
            {
                "name": "agent_heartbeat",
                "description": "AI agent heartbeat to maintain active status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "status": {"type": "string"},
                        "active_tasks": {"type": "integer"}
                    },
                    "required": ["role", "agent_id", "status"]
                }
            },
            {
                "name": "create_task",
                "description": "Create a new task in the system",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_type": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "assign_to": {"type": "string", "description": "Server or agent to assign to"},
                        "parameters": {"type": "object"}
                    },
                    "required": ["task_type", "title", "description"]
                }
            },
            {
                "name": "get_task_status",
                "description": "Get status of a specific task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "update_task",
                "description": "Update task status or details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "status": {"type": "string"},
                        "progress": {"type": "integer"},
                        "result": {"type": "object"}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "get_system_status",
                "description": "Get overall system status and health",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "find_available_server",
                "description": "Find an available server for a specific task type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_type": {"type": "string"},
                        "required_capabilities": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["server_type"]
                }
            },
            {
                "name": "find_available_agent",
                "description": "Find an available agent for a specific role and task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "required_capabilities": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["role"]
                }
            },
            {
                "name": "health_check",
                "description": "Perform health check on all components",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "check_servers": {"type": "boolean"},
                        "check_agents": {"type": "boolean"}
                    }
                }
            }
        ]
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP JSON-RPC messages"""
        method = message.get("method")
        params = message.get("params", {})
        id_val = message.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": id_val,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", 
                "id": id_val,
                "result": {
                    "tools": self.tools
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            result: str = await self.call_tool(tool_name, tool_args)
            
            return {
                "jsonrpc": "2.0",
                "id": id_val,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
        
        # Handle HTTP-style requests for backward compatibility
        elif method == "POST" and "path" in params:
            path = params.get("path", "")
            body = params.get("body", {})
            
            if path == "/register_server":
                tool_args = body
                result: str = await self.call_tool("register_server", tool_args)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/register_agent":
                tool_args = body
                result: str = await self.call_tool("register_agent", tool_args)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/server_heartbeat":
                tool_args = body
                result: str = await self.call_tool("server_heartbeat", tool_args)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/agent_heartbeat":
                tool_args = body
                result: str = await self.call_tool("agent_heartbeat", tool_args)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/create_task":
                tool_args = body
                result: str = await self.call_tool("create_task", tool_args)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path.startswith("/task/"):
                task_id = path.split("/")[-1]
                tool_args = {"task_id": task_id}
                result: str = await self.call_tool("get_task_status", tool_args)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/system_status":
                result: str = await self.call_tool("get_system_status", {})
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": id_val,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Handle tool calls for the coordinator"""
        logger.info(f"Tool call: {name} with args {args}")
        
        if name == "register_server":
            return await self._register_server(args)
        
        elif name == "register_agent":
            return await self._register_agent(args)
        
        elif name == "server_heartbeat":
            return await self._server_heartbeat(args)
        
        elif name == "agent_heartbeat":
            return await self._agent_heartbeat(args)
        
        elif name == "create_task":
            return await self._create_task(args)
        
        elif name == "get_task_status":
            return await self._get_task_status(args)
        
        elif name == "update_task":
            return await self._update_task(args)
        
        elif name == "get_system_status":
            return await self._get_system_status(args)
        
        elif name == "find_available_server":
            return await self._find_available_server(args)
        
        elif name == "find_available_agent":
            return await self._find_available_agent(args)
        
        elif name == "health_check":
            return await self._health_check(args)
        
        return json.dumps({
            "error": f"Unknown tool: {name}",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _register_server(self, args: Dict[str, Any]) -> str:
        """Register an MCP server with the coordinator"""
        server_name = args.get("server_name")
        server_type = args.get("server_type")
        server_url = args.get("server_url")
        capabilities = args.get("capabilities", [])
        
        if not server_name or not server_type or not server_url:
            return json.dumps({
                "success": False,
                "error": "Missing required parameters",
                "timestamp": datetime.now().isoformat()
            })
        
        self.registered_servers[server_name] = {
            "name": server_name,
            "type": server_type,
            "url": server_url,
            "capabilities": capabilities,
            "status": "active",
            "last_heartbeat": datetime.now(),
            "registered_at": datetime.now()
        }
        
        logger.info(f"Server registered: {server_name} ({server_type}) at {server_url}")
        
        return json.dumps({
            "success": True,
            "server_name": server_name,
            "server_type": server_type,
            "server_url": server_url,
            "registered_at": datetime.now().isoformat(),
            "status": "active",
            "message": f"Server {server_name} successfully registered"
        })
    
    async def _register_agent(self, args: Dict[str, Any]) -> str:
        """Register an AI agent with the coordinator"""
        role = args.get("role")
        agent_id = args.get("agent_id")
        port = args.get("port")
        status = args.get("status", "ready")
        capabilities = args.get("capabilities", [])
        
        if not role or not agent_id or not port:
            return json.dumps({
                "success": False,
                "error": "Missing required parameters",
                "timestamp": datetime.now().isoformat()
            })
        
        agent_key = f"{role}_{agent_id}"
        self.registered_agents[agent_key] = {
            "role": role,
            "agent_id": agent_id,
            "port": port,
            "url": f"http://localhost:{port}",
            "capabilities": capabilities,
            "status": status,
            "last_heartbeat": datetime.now(),
            "registered_at": datetime.now(),
            "active_tasks": 0
        }
        
        logger.info(f"Agent registered: {role} (ID: {agent_id}) on port {port}")
        
        return json.dumps({
            "success": True,
            "role": role,
            "agent_id": agent_id,
            "registered_at": datetime.now().isoformat(),
            "status": status,
            "message": f"Agent {role} (ID: {agent_id}) successfully registered"
        })
    
    async def _server_heartbeat(self, args: Dict[str, Any]) -> str:
        """Process MCP server heartbeat"""
        server_name = args.get("server_name")
        status = args.get("status", "active")
        stats = args.get("stats", {})
        
        if not server_name:
            return json.dumps({
                "success": False,
                "error": "Missing server_name",
                "timestamp": datetime.now().isoformat()
            })
        
        if server_name in self.registered_servers:
            self.registered_servers[server_name].update({
                "status": status,
                "last_heartbeat": datetime.now(),
                "stats": stats
            })
            
            logger.debug(f"Heartbeat from server: {server_name} (status: {status})")
            
            return json.dumps({
                "success": True,
                "server_name": server_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.warning(f"Heartbeat from unregistered server: {server_name}")
            
            return json.dumps({
                "success": False,
                "error": "Server not registered",
                "server_name": server_name,
                "timestamp": datetime.now().isoformat(),
                "action_required": "register"
            })
    
    async def _agent_heartbeat(self, args: Dict[str, Any]) -> str:
        """Process AI agent heartbeat"""
        role = args.get("role")
        agent_id = args.get("agent_id")
        status = args.get("status", "ready")
        active_tasks = args.get("active_tasks", 0)
        
        if not role or not agent_id:
            return json.dumps({
                "success": False,
                "error": "Missing role or agent_id",
                "timestamp": datetime.now().isoformat()
            })
        
        agent_key = f"{role}_{agent_id}"
        if agent_key in self.registered_agents:
            self.registered_agents[agent_key].update({
                "status": status,
                "last_heartbeat": datetime.now(),
                "active_tasks": active_tasks
            })
            
            logger.debug(f"Heartbeat from agent: {role} (ID: {agent_id}, status: {status})")
            
            return json.dumps({
                "success": True,
                "role": role,
                "agent_id": agent_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.warning(f"Heartbeat from unregistered agent: {role} (ID: {agent_id})")
            
            return json.dumps({
                "success": False,
                "error": "Agent not registered",
                "role": role,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "action_required": "register"
            })
    
    async def _create_task(self, args: Dict[str, Any]) -> str:
        """Create a new task in the system"""
        task_type = args.get("task_type")
        title = args.get("title")
        description = args.get("description")
        priority = args.get("priority", "medium")
        assign_to = args.get("assign_to")
        parameters = args.get("parameters", {})
        
        if not task_type or not title or not description:
            return json.dumps({
                "success": False,
                "error": "Missing required parameters",
                "timestamp": datetime.now().isoformat()
            })
        
        # Generate a unique task ID
        task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Create the task
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "created",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "assigned_to": assign_to,
            "parameters": parameters,
            "result": None
        }
        
        # Store the task
        self.active_tasks[task_id] = task
        
        # If assigned, try to notify the assignee
        if assign_to:
            await self._notify_assignee(task_id, assign_to)
        
        logger.info(f"Task created: {task_id} - {title} ({task_type})")
        
        return json.dumps({
            "success": True,
            "task_id": task_id,
            "status": "created",
            "message": f"Task '{title}' created successfully",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _notify_assignee(self, task_id: str, assignee: str) -> None:
        """Notify an assignee about a new task"""
        task = self.active_tasks.get(task_id)
        if not task:
            logger.warning(f"Cannot notify about non-existent task: {task_id}")
            return
        
        # Check if it's a server or agent
        if assignee in self.registered_servers:
            server = self.registered_servers[assignee]
            try:
                # Try to notify the server
                async with asyncio.timeout(5):
                    response = requests.post(
                        f"{server['url']}/assign_task",
                        json={"task_id": task_id, "task": task},
                        timeout=5
                    )
                    if response.status_code == 200:
                        logger.info(f"Server {assignee} notified about task {task_id}")
                        self.active_tasks[task_id]["notification_sent"] = True
                    else:
                        logger.warning(f"Failed to notify server {assignee} about task {task_id}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error notifying server {assignee} about task {task_id}: {e}")
        
        elif assignee in self.registered_agents:
            agent = self.registered_agents[assignee]
            try:
                # Try to notify the agent
                async with asyncio.timeout(5):
                    response = requests.post(
                        f"{agent['url']}/action",
                        json={
                            "action": "assign_task",
                            "task_id": task_id,
                            "task_type": task["task_type"],
                            "title": task["title"],
                            "description": task["description"],
                            "parameters": task["parameters"]
                        },
                        timeout=5
                    )
                    if response.status_code == 200:
                        logger.info(f"Agent {assignee} notified about task {task_id}")
                        self.active_tasks[task_id]["notification_sent"] = True
                    else:
                        logger.warning(f"Failed to notify agent {assignee} about task {task_id}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error notifying agent {assignee} about task {task_id}: {e}")
        
        else:
            logger.warning(f"Assignee not found: {assignee} for task {task_id}")
    
    async def _get_task_status(self, args: Dict[str, Any]) -> str:
        """Get status of a specific task"""
        task_id = args.get("task_id")
        
        if not task_id:
            return json.dumps({
                "success": False,
                "error": "Missing task_id",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check active tasks
        if task_id in self.active_tasks:
            return json.dumps({
                "success": True,
                "task": self.active_tasks[task_id],
                "timestamp": datetime.now().isoformat()
            })
        
        # Check task history
        for task in self.task_history:
            if task["task_id"] == task_id:
                return json.dumps({
                    "success": True,
                    "task": task,
                    "timestamp": datetime.now().isoformat(),
                    "archived": True
                })
        
        return json.dumps({
            "success": False,
            "error": "Task not found",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _update_task(self, args: Dict[str, Any]) -> str:
        """Update task status or details"""
        task_id = args.get("task_id")
        status = args.get("status")
        progress = args.get("progress")
        result: str = args.get("result")
        
        if not task_id:
            return json.dumps({
                "success": False,
                "error": "Missing task_id",
                "timestamp": datetime.now().isoformat()
            })
        
        if task_id not in self.active_tasks:
            return json.dumps({
                "success": False,
                "error": "Task not found",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            })
        
        task = self.active_tasks[task_id]
        
        # Update the task
        if status:
            task["status"] = status
        
        if progress is not None:
            task["progress"] = progress
        
        if result:
            task["result"] = result
        
        task["updated_at"] = datetime.now().isoformat()
        
        # If task is completed, failed, or cancelled, move to history
        if status in ["completed", "failed", "cancelled"]:
            self.task_history.append(task.copy())
            del self.active_tasks[task_id]
            logger.info(f"Task {task_id} marked as {status} and archived")
        else:
            logger.info(f"Task {task_id} updated - status: {status}, progress: {progress}")
        
        return json.dumps({
            "success": True,
            "task_id": task_id,
            "status": status or task["status"],
            "updated_at": task["updated_at"],
            "message": f"Task {task_id} updated successfully"
        })
    
    async def _get_system_status(self, args: Dict[str, Any]) -> str:
        """Get overall system status and health"""
        # Count servers by status
        server_status_counts = {}
        for server in self.registered_servers.values():
            status = server.get("status", "unknown")
            server_status_counts[status] = server_status_counts.get(status, 0) + 1
        
        # Count agents by role and status
        agent_counts = {
            "by_role": {},
            "by_status": {}
        }
        
        for agent in self.registered_agents.values():
            role = agent.get("role", "unknown")
            status = agent.get("status", "unknown")
            
            if role not in agent_counts["by_role"]:
                agent_counts["by_role"][role] = 0
            agent_counts["by_role"][role] += 1
            
            if status not in agent_counts["by_status"]:
                agent_counts["by_status"][status] = 0
            agent_counts["by_status"][status] += 1
        
        # Task statistics
        task_stats = {
            "active": len(self.active_tasks),
            "completed": len([t for t in self.task_history if t.get("status") == "completed"]),
            "failed": len([t for t in self.task_history if t.get("status") == "failed"]),
            "cancelled": len([t for t in self.task_history if t.get("status") == "cancelled"]),
            "by_type": {}
        }
        
        # Count tasks by type
        for task in list(self.active_tasks.values()) + self.task_history:
            task_type = task.get("task_type", "unknown")
            if task_type not in task_stats["by_type"]:
                task_stats["by_type"][task_type] = 0
            task_stats["by_type"][task_type] += 1
        
        # Check if we have the required servers and agents
        required_servers = self.config.get("required_servers", [])
        required_agent_roles = self.config.get("required_agent_roles", [])
        
        server_types_present = set(server["type"] for server in self.registered_servers.values())
        agent_roles_present = set(agent["role"] for agent in self.registered_agents.values())
        
        missing_servers = [server for server in required_servers if server not in server_types_present]
        missing_agent_roles = [role for role in required_agent_roles if role not in agent_roles_present]
        
        # Determine overall system status
        if len(missing_servers) > len(required_servers) // 2 or len(missing_agent_roles) > 0:
            overall_status = "degraded"
        elif len(missing_servers) > 0:
            overall_status = "partial"
        else:
            overall_status = "operational"
        
        self.system_status = overall_status
        
        return json.dumps({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "last_health_check": self.last_health_check.isoformat(),
            "overall_status": overall_status,
            "servers": {
                "total": len(self.registered_servers),
                "by_status": server_status_counts,
                "missing": missing_servers
            },
            "agents": {
                "total": len(self.registered_agents),
                "counts": agent_counts,
                "missing_roles": missing_agent_roles
            },
            "tasks": task_stats,
            "coordinator": {
                "name": self.name,
                "version": self.version,
                "uptime": str(datetime.now() - self.last_health_check)
            }
        }, indent=2)
    
    async def _find_available_server(self, args: Dict[str, Any]) -> str:
        """Find an available server for a specific task type"""
        server_type = args.get("server_type")
        required_capabilities = args.get("required_capabilities", [])
        
        if not server_type:
            return json.dumps({
                "success": False,
                "error": "Missing server_type",
                "timestamp": datetime.now().isoformat()
            })
        
        # Find servers of the requested type
        matching_servers = []
        for name, server in self.registered_servers.items():
            if server["type"] == server_type and server["status"] == "active":
                # Check capabilities if required
                if required_capabilities:
                    server_capabilities = set(server.get("capabilities", []))
                    if not all(cap in server_capabilities for cap in required_capabilities):
                        continue
                
                # Calculate a score based on last heartbeat and active tasks
                time_since_heartbeat = (datetime.now() - server["last_heartbeat"]).total_seconds()
                active_tasks = server.get("stats", {}).get("active_tasks", 0)
                
                score = 100 - min(time_since_heartbeat, 60) - active_tasks * 5
                
                matching_servers.append({
                    "name": name,
                    "url": server["url"],
                    "score": score,
                    "last_heartbeat": server["last_heartbeat"].isoformat(),
                    "capabilities": server.get("capabilities", [])
                })
        
        if not matching_servers:
            return json.dumps({
                "success": False,
                "error": f"No available servers of type: {server_type}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Sort by score (highest first)
        matching_servers.sort(key=lambda s: Any: s["score"], reverse=True)
        best_server = matching_servers[0]
        
        return json.dumps({
            "success": True,
            "server": best_server["name"],
            "url": best_server["url"],
            "score": best_server["score"],
            "timestamp": datetime.now().isoformat(),
            "alternatives": matching_servers[1:3] if len(matching_servers) > 1 else []
        })
    
    async def _find_available_agent(self, args: Dict[str, Any]) -> str:
        """Find an available agent for a specific role and task"""
        role = args.get("role")
        required_capabilities = args.get("required_capabilities", [])
        
        if not role:
            return json.dumps({
                "success": False,
                "error": "Missing role",
                "timestamp": datetime.now().isoformat()
            })
        
        # Find agents of the requested role
        matching_agents = []
        for key, agent in self.registered_agents.items():
            if agent["role"] == role and agent["status"] in ["ready", "active"]:
                # Check capabilities if required
                if required_capabilities:
                    agent_capabilities = set(agent.get("capabilities", []))
                    if not all(cap in agent_capabilities for cap in required_capabilities):
                        continue
                
                # Calculate a score based on last heartbeat and active tasks
                time_since_heartbeat = (datetime.now() - agent["last_heartbeat"]).total_seconds()
                active_tasks = agent.get("active_tasks", 0)
                
                score = 100 - min(time_since_heartbeat, 60) - active_tasks * 10
                
                matching_agents.append({
                    "key": key,
                    "agent_id": agent["agent_id"],
                    "url": agent["url"],
                    "score": score,
                    "last_heartbeat": agent["last_heartbeat"].isoformat(),
                    "active_tasks": active_tasks,
                    "capabilities": agent.get("capabilities", [])
                })
        
        if not matching_agents:
            return json.dumps({
                "success": False,
                "error": f"No available agents for role: {role}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Sort by score (highest first)
        matching_agents.sort(key=lambda a: Any: a["score"], reverse=True)
        best_agent = matching_agents[0]
        
        return json.dumps({
            "success": True,
            "agent_key": best_agent["key"],
            "agent_id": best_agent["agent_id"],
            "url": best_agent["url"],
            "score": best_agent["score"],
            "active_tasks": best_agent["active_tasks"],
            "timestamp": datetime.now().isoformat(),
            "alternatives": matching_agents[1:3] if len(matching_agents) > 1 else []
        })
    
    async def _health_check(self, args: Dict[str, Any]) -> str:
        """Perform health check on all components"""
        check_servers = args.get("check_servers", True)
        check_agents = args.get("check_agents", True)
        
        logger.info("Performing system health check")
        self.last_health_check = datetime.now()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "servers": {},
            "agents": {},
            "overall_status": "operational"
        }
        
        # Check server health
        if check_servers:
            server_timeout = self.config.get("server_timeout_sec", 120)
            for name, server in list(self.registered_servers.items()):
                time_since_heartbeat = (datetime.now() - server["last_heartbeat"]).total_seconds()
                
                if time_since_heartbeat > server_timeout:
                    server["status"] = "offline"
                    results["servers"][name] = {
                        "status": "offline",
                        "last_heartbeat": server["last_heartbeat"].isoformat(),
                        "seconds_since_heartbeat": time_since_heartbeat
                    }
                else:
                    results["servers"][name] = {
                        "status": server["status"],
                        "last_heartbeat": server["last_heartbeat"].isoformat(),
                        "seconds_since_heartbeat": time_since_heartbeat
                    }
        
        # Check agent health
        if check_agents:
            agent_timeout = self.config.get("agent_timeout_sec", 180)
            for key, agent in list(self.registered_agents.items()):
                time_since_heartbeat = (datetime.now() - agent["last_heartbeat"]).total_seconds()
                
                if time_since_heartbeat > agent_timeout:
                    agent["status"] = "offline"
                    results["agents"][key] = {
                        "status": "offline",
                        "last_heartbeat": agent["last_heartbeat"].isoformat(),
                        "seconds_since_heartbeat": time_since_heartbeat
                    }
                else:
                    results["agents"][key] = {
                        "status": agent["status"],
                        "last_heartbeat": agent["last_heartbeat"].isoformat(),
                        "seconds_since_heartbeat": time_since_heartbeat
                    }
        
        # Calculate overall system status
        offline_servers = sum(1 for status in results["servers"].values() if status["status"] == "offline")
        offline_agents = sum(1 for status in results["agents"].values() if status["status"] == "offline")
        
        total_servers = len(self.registered_servers)
        total_agents = len(self.registered_agents)
        
        if total_servers > 0 and offline_servers >= total_servers // 2:
            results["overall_status"] = "critical"
        elif total_agents > 0 and offline_agents >= total_agents // 2:
            results["overall_status"] = "degraded"
        elif offline_servers > 0 or offline_agents > 0:
            results["overall_status"] = "partial"
        
        self.system_status = results["overall_status"]
        
        return json.dumps(results, indent=2)
    
    async def run(self):
        """Run the MCP coordinator server"""
        logger.info(f"Starting {self.name} v{self.version} (stdio mode)")
        
        # Start the health check loop
        asyncio.create_task(self._health_check_loop())
        
        # Start the server
        while True:
            try:
                line: str = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                    
                line: str = line.strip()
                if not line:
                    continue
                
                try:
                    message = json.loads(line)
                    response = await self.handle_message(message)
                    
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
            except Exception as e:
                logger.error(f"Server error: {str(e)}")
                break
    
    async def _health_check_loop(self):
        """Periodic health check loop"""
        health_check_interval = self.config.get("health_check_interval_sec", 60)
        
        while True:
            try:
                await asyncio.sleep(health_check_interval)
                
                # Perform a health check
                await self._health_check({"check_servers": True, "check_agents": True})
                
                logger.debug(f"Health check completed. System status: {self.system_status}")
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

def main():
    """Main entry point"""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Create and run the coordinator
    coordinator = MCPEnhancedCoordinator()
    try:
        asyncio.run(coordinator.run())
    except KeyboardInterrupt:
        logger.info(f"{coordinator.name} shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()