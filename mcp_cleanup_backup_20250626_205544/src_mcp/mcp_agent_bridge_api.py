# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import json
import logging

    import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from mcp_agent_connection_bridge import MCPAgentBridge
from pydantic import BaseModel
"""
MCP-Agent Bridge API
===================

FastAPI-based API for monitoring and controlling the MCP-Agent bridge.
Provides endpoints for status monitoring, connection management, and task coordination.

Features:
- Status monitoring dashboard
- Connection health checks
- Task routing control
- Real-time metrics
- Manual connection management

Author: GitHub Copilot Assistant
Date: June 18, 2025
"""


# Configure logging

# Unicode-safe logging setup
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
    title="MCP-Agent Bridge API",
    description="API for monitoring and controlling MCP-Agent connections",
    version="1.0.0"


# Global bridge instance
bridge: Optional[MCPAgentBridge] = None
bridge_task: Optional[asyncio.Task] = None

class ConnectionRequest(BaseModel):
    agent_name: str
    server_name: str
    
class TaskRequest(BaseModel):
    task_type: str
    source: str
    target: str
    data: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize the bridge on startup"""
    global bridge, bridge_task
    
    logger.info("[INIT] Starting MCP-Agent Bridge API...")
    
    try:
        bridge = MCPAgentBridge()
        
        # Start the bridge in the background
        bridge_task = asyncio.create_task(bridge.start())
        
        # Give it a moment to initialize
        await asyncio.sleep(2)
        
        logger.info("[OK] MCP-Agent Bridge API started successfully")
        
    except Exception as e:
        logger.error(str(f"[ERROR] Failed to start bridge: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global bridge, bridge_task
    
    logger.info("[STOP] Shutting down MCP-Agent Bridge API...")
    
    if bridge:
        bridge.running = False
    
    if bridge_task:
        bridge_task.cancel()
        
    logger.info("👋 MCP-Agent Bridge API shutdown complete")

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {}
        "service": "MCP-Agent Bridge",
        "version": "1.0.0",
        "status": "running" if bridge and bridge.running else "stopped",
        "timestamp": datetime.now().isoformat()
    

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    return {}
        "status": "healthy" if bridge.running else "unhealthy",
        "timestamp": datetime.now().isoformat()
    

@app.get("/status")
async def get_status():
    """Get comprehensive status report"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    return bridge.get_status_report()

@app.get("/services")
async def get_services():
    """Get all discovered services"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    return {}
        "mcp_servers": {}
            name: {}
                "name": service.name,
                "host": service.host,
                "port": service.port,
                "status": service.status,
                "capabilities": service.capabilities,
                "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None
            
            for name, service in bridge.mcp_servers.items()
        },
        "ai_agents": {}
            name: {}
                "name": service.name,
                "host": service.host,
                "port": service.port,
                "status": service.status,
                "capabilities": service.capabilities,
                "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None
            
            for name, service in bridge.ai_agents.items()
        
    

@app.get("/connections")
async def get_connections():
    """Get current connections between agents and MCP servers"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    connection_details = {}
    
    for agent_name, server_names in bridge.connections.items():
        if agent_name in bridge.ai_agents:
            agent = bridge.ai_agents[agent_name]
            connection_details[agent_name] = {}
                "agent_info": {}
                    "name": agent.name,
                    "status": agent.status,
                    "capabilities": agent.capabilities
                },
                "connected_servers": []
            
            
            for server_name in server_names:
                if server_name in bridge.mcp_servers:
                    server = bridge.mcp_servers[server_name]
                    connection_details[agent_name]["connected_servers"].append({)}
                        "name": server.name,
                        "status": server.status,
                        "capabilities": server.capabilities
                    
    
    return connection_details

@app.post("/rediscover")
async def rediscover_services(background_tasks: BackgroundTasks):
    """Rediscover services and re-establish connections"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    async def rediscover():
        await bridge.discover_services()
        await bridge.establish_connections()
    
    background_tasks.add_task(rediscover)
    
    return {"message": "Service rediscovery initiated"}

@app.post("/connect")
async def create_connection(request: ConnectionRequest):
    """Manually create a connection between an agent and MCP server"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    agent_name = request.agent_name
    server_name = request.server_name
    
    if agent_name not in bridge.ai_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    if server_name not in bridge.mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP server {server_name} not found")
    
    agent = bridge.ai_agents[agent_name]
    server = bridge.mcp_servers[server_name]
    
    if agent.status != "healthy":
        raise HTTPException(status_code=400, detail=f"Agent {agent_name} is not healthy")
    
    if server.status != "healthy":
        raise HTTPException(status_code=400, detail=f"MCP server {server_name} is not healthy")
    
    # Add connection
    if agent_name not in bridge.connections:
        bridge.connections[agent_name] = set()
    
    bridge.connections[agent_name].add(server_name)
    
    # Notify agent
    await bridge._notify_agent_connections(agent, bridge.connections[agent_name])
    
    return {}
        "message": f"Connection established between {agent_name} and {server_name}",
        "timestamp": datetime.now().isoformat()
    

@app.delete("/disconnect")
async def remove_connection(request: ConnectionRequest):
    """Remove a connection between an agent and MCP server"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    agent_name = request.agent_name
    server_name = request.server_name
    
    if agent_name not in bridge.connections:
        raise HTTPException(status_code=404, detail=f"No connections found for agent {agent_name}")
    
    if server_name not in bridge.connections[agent_name]:
        raise HTTPException(status_code=404, detail=f"Connection not found between {agent_name} and {server_name}")
    
    # Remove connection
    bridge.connections[agent_name].discard(server_name)
    
    # Notify agent
    agent = bridge.ai_agents[agent_name]
    await bridge._notify_agent_connections(agent, bridge.connections[agent_name])
    
    return {}
        "message": f"Connection removed between {agent_name} and {server_name}",
        "timestamp": datetime.now().isoformat()
    

@app.post("/task")
async def route_task(request: TaskRequest):
    """Route a task between services"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    if bridge.redis_client:
        # Send task via Redis
        task_data = {}
            "task_type": request.task_type,
            "source": request.source,
            "target": request.target,
            "data": request.data,
            "timestamp": datetime.now().isoformat()
        
        
        channel = "task_coordination"
        bridge.redis_client.publish(channel, json.dumps(task_data, ensure_ascii=True, default=str))
        
        return {}
            "message": "Task routed successfully",
            "task_id": f"{request.task_type}_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat()
        
    else:
        raise HTTPException(status_code=503, detail="Redis not available for task routing")

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    if not bridge:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    # Calculate metrics
    total_mcp = len(bridge.mcp_servers)
    healthy_mcp = sum(1 for s in bridge.mcp_servers.values() if s.status == "healthy")
    
    total_agents = len(bridge.ai_agents)
    healthy_agents = sum(1 for a in bridge.ai_agents.values() if a.status == "healthy")
    
    total_connections = sum(len(servers) for servers in bridge.connections.values())
    active_connections = sum()
        len(servers) for agent_name, servers in bridge.connections.items()
        if bridge.ai_agents.get(agent_name, {}).status == "healthy"
    
    
    return {}
        "mcp_servers": {}
            "total": total_mcp,
            "healthy": healthy_mcp,
            "unhealthy": total_mcp - healthy_mcp,
            "health_percentage": (healthy_mcp / total_mcp * 100) if total_mcp > 0 else 0
        },
        "ai_agents": {}
            "total": total_agents,
            "healthy": healthy_agents,
            "unhealthy": total_agents - healthy_agents,
            "health_percentage": (healthy_agents / total_agents * 100) if total_agents > 0 else 0
        },
        "connections": {}
            "total": total_connections,
            "active": active_connections,
            "inactive": total_connections - active_connections
        },
        "system": {}
            "uptime": datetime.now().isoformat(),
            "bridge_running": bridge.running
        
    

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple HTML dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP-Agent Bridge Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .status-healthy { color: green; }
            .status-unhealthy { color: red; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .metric { background: white; padding: 15px; border-radius: 5px; text-align: center; }
            .metric h3 { margin: 0 0 10px 0; }
            .metric .value { font-size: 2em; font-weight: bold; }
            button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌉 MCP-Agent Bridge Dashboard</h1>
            
            <div class="card">
                <h2>System Status</h2>
                <p id="system-status">Loading...</p>
                <button onclick="refreshStatus()">Refresh Status</button>
                <button onclick="rediscoverServices()">Rediscover Services</button>
            </div>
            
            <div class="card">
                <h2>[METRICS] Metrics</h2>
                <div class="metrics" id="metrics">
                    Loading metrics...
                </div>
            </div>
            
            <div class="card">
                <h2>🔗 Connections</h2>
                <div id="connections">Loading connections...</div>
            </div>
            
            <div class="card">
                <h2>📡 Services</h2>
                <div id="services">Loading services...</div>
            </div>
        </div>
        
        <script>
            async function refreshStatus() {}
                try {}
                    const response = await fetch('/status');
                    const data = await response.json();
                    document.getElementById('system-status').innerHTML = 
                        `<strong>MCP Servers:</strong> ${data.mcp_servers.healthy}/${data.mcp_servers.total} healthy<br>
                         <strong>AI Agents:</strong> ${data.ai_agents.healthy}/${data.ai_agents.total} healthy<br>
                         <strong>Connections:</strong> ${data.connections.total} total, ${data.connections.active_agents} active agents<br>
                         <strong>Last Updated:</strong> ${new Date(data.timestamp).toLocaleString()}`;
                } catch (error) {
                    document.getElementById('system-status').innerHTML = 'Error loading status';
                
            
            
            async function loadMetrics() {}
                try {}
                    const response = await fetch('/metrics');
                    const data = await response.json();
                    
                    document.getElementById('metrics').innerHTML = `
                        <div class="metric">
                            <h3>MCP Servers</h3>
                            <div class="value">${data.mcp_servers.healthy}/${data.mcp_servers.total}</div>
                            <div>${data.mcp_servers.health_percentage.toFixed(1)}% healthy</div>
                        </div>
                        <div class="metric">
                            <h3>AI Agents</h3>
                            <div class="value">${data.ai_agents.healthy}/${data.ai_agents.total}</div>
                            <div>${data.ai_agents.health_percentage.toFixed(1)}% healthy</div>
                        </div>
                        <div class="metric">
                            <h3>Connections</h3>
                            <div class="value">${data.connections.active}/${data.connections.total}</div>
                            <div>Active connections</div>
                        </div>
                    `;
                } catch (error) {
                    document.getElementById('metrics').innerHTML = 'Error loading metrics';
                
            
            
            async function loadConnections() {}
                try {}
                    const response = await fetch('/connections');
                    const data = await response.json();
                    
                    let html = '';
                    for (const [agentName, details] of Object.entries(data)) {}
                        html += `<div><strong>${agentName}</strong> (${details.agent_info.status}): `;
                        html += details.connected_servers.map(s => `${s.name} (${s.status})`).join(', ');
                        html += '</div>';
                    
                    
                    document.getElementById('connections').innerHTML = html || 'No connections found';
                } catch (error) {
                    document.getElementById('connections').innerHTML = 'Error loading connections';
                
            
            
            async function loadServices() {}
                try {}
                    const response = await fetch('/services');
                    const data = await response.json();
                    
                    let html = '<h3>MCP Servers</h3>';
                    for (const [name, service] of Object.entries(data.mcp_servers)) {}
                        html += `<div><strong>${name}</strong>: ${service.host}:${service.port} (${service.status})</div>`;
                    
                    
                    html += '<h3>AI Agents</h3>';
                    for (const [name, service] of Object.entries(data.ai_agents)) {}
                        html += `<div><strong>${name}</strong>: ${service.host}:${service.port} (${service.status})</div>`;
                    
                    
                    document.getElementById('services').innerHTML = html;
                } catch (error) {
                    document.getElementById('services').innerHTML = 'Error loading services';
                
            
            
            async function rediscoverServices() {}
                try {}
                    const response = await fetch('/rediscover', { method: 'POST' });
                    const data = await response.json();
                    alert(data.message);
                    setTimeout(() => {)}
                        refreshStatus();
                        loadMetrics();
                        loadConnections();
                        loadServices();
                    }, 2000);
                } catch (error) {
                    alert('Error rediscovering services');
                
            
            
            // Load initial data
            refreshStatus();
            loadMetrics();
            loadConnections();
            loadServices();
            
            // Auto-refresh every 30 seconds
            setInterval(() => {)}
                refreshStatus();
                loadMetrics();
                loadConnections();
            }, 30000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8500)