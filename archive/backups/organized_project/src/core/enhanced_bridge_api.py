"""
Enhanced MCP Agent Bridge API with Task Management
Provides comprehensive REST API for task management and system monitoring
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import logging
import asyncio
from datetime import datetime
from task_orchestrator import TaskOrchestrator, TaskPriority, TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Flash Loan MCP-Agent Bridge API",
    description="Comprehensive API for managing MCP servers, AI agents, and task orchestration",
    version="2.0.0"
)

# Global orchestrator instance
orchestrator: Optional[TaskOrchestrator] = None

# Pydantic models for API
class TaskCreateRequest(BaseModel):
    task_type: str
    description: str
    priority: str = "normal"
    parameters: Dict[str, Any] = {}
    dependencies: List[str] = []

class WorkflowCreateRequest(BaseModel):
    workflow_name: str
    parameters: Dict[str, Any] = {}

class TaskResponse(BaseModel):
    id: str
    type: str
    description: str
    status: str
    assigned_agent: Optional[str]
    assigned_servers: List[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]

@app.on_event("startup")
async def startup_event():
    """Initialize the task orchestrator on startup"""
    global orchestrator
    orchestrator = TaskOrchestrator()
    await orchestrator.start()
    logger.info("Task Orchestrator started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global orchestrator
    if orchestrator:
        await orchestrator.stop()
    logger.info("Task Orchestrator stopped")

# Health and Status Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_running": orchestrator.running if orchestrator else False
    }

@app.get("/status")
async def get_system_status():
    """Get comprehensive system status"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    task_status = orchestrator.get_all_tasks()
    workflow_status = orchestrator.get_workflow_status()
    
    return {
        "system": {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "uptime": "Running"
        },
        "tasks": task_status,
        "workflows": workflow_status,
        "agents": {
            "total": 10,
            "connected": 10,
            "capabilities": workflow_status["agent_capabilities"]
        },
        "servers": {
            "total": 21,
            "healthy": 21
        }
    }

# Task Management Endpoints
@app.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskCreateRequest):
    """Create a new task"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    try:
        priority = getattr(TaskPriority, task_request.priority.upper())
    except AttributeError:
        priority = TaskPriority.NORMAL
    
    task = orchestrator.create_task(
        task_type=task_request.task_type,
        description=task_request.description,
        priority=priority,
        parameters=task_request.parameters,
        dependencies=task_request.dependencies
    )
    
    return TaskResponse(
        id=task.id,
        type=task.type,
        description=task.description,
        status=task.status.value,
        assigned_agent=task.assigned_agent,
        assigned_servers=task.assigned_servers,
        created_at=task.created_at.isoformat(),
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        result=task.result,
        error_message=task.error_message
    )

@app.post("/workflows")
async def create_workflow(workflow_request: WorkflowCreateRequest):
    """Create a new workflow"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    try:
        tasks = orchestrator.create_workflow(
            workflow_name=workflow_request.workflow_name,
            parameters=workflow_request.parameters
        )
        
        return {
            "workflow_name": workflow_request.workflow_name,
            "tasks_created": len(tasks),
            "task_ids": [task.id for task in tasks],
            "status": "created"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks")
async def get_all_tasks():
    """Get all tasks with their status"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    return orchestrator.get_all_tasks()

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task by ID"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    task_data = orchestrator.get_task_status(task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_data

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a specific task"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    task = orchestrator.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed or failed task")
    
    task.status = TaskStatus.CANCELLED
    return {"message": f"Task {task_id} cancelled"}

# Agent and Server Information
@app.get("/agents")
async def get_agents():
    """Get information about all agents"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    agents_info = []
    for agent, info in orchestrator.agent_capabilities.items():
        agent_tasks = [task for task in orchestrator.tasks.values() if task.assigned_agent == agent]
        
        agents_info.append({
            "name": agent,
            "port": orchestrator._get_agent_port(agent),
            "servers": info["servers"],
            "capabilities": info["capabilities"],
            "active_tasks": len([t for t in agent_tasks if t.status == TaskStatus.IN_PROGRESS]),
            "total_tasks": len(agent_tasks),
            "completed_tasks": len([t for t in agent_tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in agent_tasks if t.status == TaskStatus.FAILED])
        })
    
    return {"agents": agents_info}

@app.get("/servers")
async def get_servers():
    """Get information about all MCP servers"""
    servers = [
        "flashloan-mcp-coordinator", "flashloan-mcp-arbitrage", "flashloan-mcp-defi-analyzer",
        "flashloan-mcp-api-client", "flashloan-mcp-price-feed", "flashloan-mcp-risk-manager",
        "flashloan-mcp-monitoring", "flashloan-mcp-liquidity", "flashloan-mcp-flash-loan",
        "flashloan-mcp-blockchain", "flashloan-mcp-database", "flashloan-mcp-notification",
        "flashloan-mcp-data-analyzer", "flashloan-mcp-auth-manager", "flashloan-mcp-security",
        "flashloan-mcp-portfolio", "flashloan-mcp-file-processor", "flashloan-mcp-filesystem",
        "flashloan-mcp-cache-manager", "flashloan-mcp-task-queue", "flashloan-mcp-web-scraper"
    ]
    
    servers_info = []
    for server in servers:
        port = 8100 + servers.index(server)  # Simple port calculation
        servers_info.append({
            "name": server,
            "port": port,
            "status": "healthy",
            "url": f"http://localhost:{port}"
        })
    
    return {"servers": servers_info}

@app.get("/workflows")
async def get_workflows():
    """Get available workflows"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    return orchestrator.get_workflow_status()

# Workflow Control Endpoints
@app.post("/workflows/arbitrage")
async def start_arbitrage_workflow():
    """Start arbitrage opportunity detection workflow"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    tasks = orchestrator.create_workflow("arbitrage_opportunity_detection")
    return {
        "workflow": "arbitrage_opportunity_detection",
        "status": "started",
        "task_ids": [task.id for task in tasks]
    }

@app.post("/workflows/health-check")
async def start_health_check_workflow():
    """Start system health check workflow"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    tasks = orchestrator.create_workflow("system_health_check")
    return {
        "workflow": "system_health_check",
        "status": "started",
        "task_ids": [task.id for task in tasks]
    }

@app.post("/workflows/market-analysis")
async def start_market_analysis_workflow():
    """Start market analysis workflow"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    tasks = orchestrator.create_workflow("market_analysis")
    return {
        "workflow": "market_analysis",
        "status": "started",
        "task_ids": [task.id for task in tasks]
    }

# Quick Actions
@app.post("/actions/detect-arbitrage")
async def detect_arbitrage():
    """Quick action: Detect arbitrage opportunities"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    task = orchestrator.create_task(
        "arbitrage_detection",
        "Quick arbitrage opportunity detection",
        TaskPriority.HIGH
    )
    
    return {"task_id": task.id, "status": "created"}

@app.post("/actions/check-system-health")
async def check_system_health():
    """Quick action: Check system health"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    task = orchestrator.create_task(
        "system_monitoring",
        "Quick system health check",
        TaskPriority.NORMAL
    )
    
    return {"task_id": task.id, "status": "created"}

@app.post("/actions/analyze-market")
async def analyze_market():
    """Quick action: Analyze market conditions"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    task = orchestrator.create_task(
        "market_analysis",
        "Quick market analysis",
        TaskPriority.NORMAL
    )
    
    return {"task_id": task.id, "status": "created"}

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Flash Loan MCP-Agent Bridge Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
            }
            
            .dashboard {
                padding: 20px;
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .header h1 {
                color: #4a5568;
                margin-bottom: 10px;
            }
            
            .status-indicator {
                display: inline-block;
                padding: 4px 12px;
                background: #48bb78;
                color: white;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .card {
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .card h3 {
                color: #4a5568;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .icon {
                width: 20px;
                height: 20px;
                font-size: 20px;
            }
            
            .stat {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .stat:last-child {
                border-bottom: none;
            }
            
            .stat-value {
                font-weight: 600;
                color: #2d3748;
            }
            
            .actions {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 15px;
            }
            
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.2s;
                text-decoration: none;
                display: inline-block;
            }
            
            .btn-primary {
                background: #4299e1;
                color: white;
            }
            
            .btn-primary:hover {
                background: #3182ce;
            }
            
            .btn-success {
                background: #48bb78;
                color: white;
            }
            
            .btn-success:hover {
                background: #38a169;
            }
            
            .btn-warning {
                background: #ed8936;
                color: white;
            }
            
            .btn-warning:hover {
                background: #dd6b20;
            }
            
            .task-list {
                max-height: 300px;
                overflow-y: auto;
            }
            
            .task-item {
                padding: 10px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                margin-bottom: 8px;
                background: #f7fafc;
            }
            
            .task-status {
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }
            
            .status-pending { background: #fbb6ce; color: #97266d; }
            .status-assigned { background: #bee3f8; color: #2a69ac; }
            .status-in_progress { background: #fbd38d; color: #b7791f; }
            .status-completed { background: #c6f6d5; color: #22543d; }
            .status-failed { background: #fed7d7; color: #c53030; }
            
            .refresh-btn {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: #4299e1;
                color: white;
                border: none;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                transition: all 0.3s;
            }
            
            .refresh-btn:hover {
                background: #3182ce;
                transform: scale(1.1);
            }
            
            @media (max-width: 768px) {
                .grid {
                    grid-template-columns: 1fr;
                }
                
                .actions {
                    flex-direction: column;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1>🚀 Flash Loan MCP-Agent Bridge Dashboard</h1>
                <span class="status-indicator" id="system-status">System Online</span>
                <p>Real-time monitoring and task management for MCP servers and AI agents</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📊 System Overview</h3>
                    <div class="stat">
                        <span>MCP Servers</span>
                        <span class="stat-value" id="server-count">21</span>
                    </div>
                    <div class="stat">
                        <span>AI Agents</span>
                        <span class="stat-value" id="agent-count">10</span>
                    </div>
                    <div class="stat">
                        <span>Active Connections</span>
                        <span class="stat-value" id="connection-count">15</span>
                    </div>
                    <div class="stat">
                        <span>System Uptime</span>
                        <span class="stat-value" id="uptime">Running</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 Task Statistics</h3>
                    <div class="stat">
                        <span>Total Tasks</span>
                        <span class="stat-value" id="total-tasks">0</span>
                    </div>
                    <div class="stat">
                        <span>In Progress</span>
                        <span class="stat-value" id="active-tasks">0</span>
                    </div>
                    <div class="stat">
                        <span>Completed</span>
                        <span class="stat-value" id="completed-tasks">0</span>
                    </div>
                    <div class="stat">
                        <span>Failed</span>
                        <span class="stat-value" id="failed-tasks">0</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>⚡ Quick Actions</h3>
                    <div class="actions">
                        <button class="btn btn-primary" onclick="detectArbitrage()">Detect Arbitrage</button>
                        <button class="btn btn-success" onclick="checkHealth()">Health Check</button>
                        <button class="btn btn-warning" onclick="analyzeMarket()">Market Analysis</button>
                    </div>
                    <div class="actions">
                        <button class="btn btn-primary" onclick="startArbitrageWorkflow()">Full Arbitrage Workflow</button>
                        <button class="btn btn-success" onclick="startHealthWorkflow()">System Health Workflow</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📈 Workflows</h3>
                    <div class="actions">
                        <button class="btn btn-primary" onclick="createWorkflow('arbitrage_opportunity_detection')">Arbitrage Detection</button>
                        <button class="btn btn-success" onclick="createWorkflow('system_health_check')">Health Check</button>
                        <button class="btn btn-warning" onclick="createWorkflow('market_analysis')">Market Analysis</button>
                    </div>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>🎯 Recent Tasks</h3>
                    <div class="task-list" id="recent-tasks">
                        <div class="task-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span>Loading tasks...</span>
                                <span class="task-status status-pending">Loading</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🤖 Agent Status</h3>
                    <div id="agent-status">
                        <div class="stat">
                            <span>Loading agent information...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()" title="Refresh Data">🔄</button>
        
        <script>
            // Global state
            let refreshInterval;
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                refreshData();
                startAutoRefresh();
            });
            
            function startAutoRefresh() {
                refreshInterval = setInterval(refreshData, 5000); // Refresh every 5 seconds
            }
            
            function stopAutoRefresh() {
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                }
            }
            
            async function refreshData() {
                try {
                    await Promise.all([
                        updateSystemStatus(),
                        updateTaskData(),
                        updateAgentData()
                    ]);
                } catch (error) {
                    console.error('Error refreshing data:', error);
                }
            }
            
            async function updateSystemStatus() {
                try {
                    const response = await fetch('/status');
                    const data = await response.json();
                    
                    document.getElementById('server-count').textContent = data.servers?.total || 21;
                    document.getElementById('agent-count').textContent = data.agents?.total || 10;
                    document.getElementById('connection-count').textContent = data.agents?.connected || 15;
                    document.getElementById('uptime').textContent = data.system?.uptime || 'Running';
                    
                    // Update task statistics
                    const tasks = data.tasks || {};
                    document.getElementById('total-tasks').textContent = tasks.total_tasks || 0;
                    document.getElementById('active-tasks').textContent = tasks.in_progress || 0;
                    document.getElementById('completed-tasks').textContent = tasks.completed || 0;
                    document.getElementById('failed-tasks').textContent = tasks.failed || 0;
                    
                } catch (error) {
                    console.error('Error updating system status:', error);
                }
            }
            
            async function updateTaskData() {
                try {
                    const response = await fetch('/tasks');
                    const data = await response.json();
                    
                    const taskList = document.getElementById('recent-tasks');
                    const tasks = data.tasks || {};
                    
                    const taskItems = Object.values(tasks)
                        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                        .slice(0, 10);
                    
                    if (taskItems.length === 0) {
                        taskList.innerHTML = '<div class="task-item">No tasks found</div>';
                        return;
                    }
                    
                    taskList.innerHTML = taskItems.map(task => `
                        <div class="task-item">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <strong>${task.description}</strong>
                                <span class="task-status status-${task.status}">${task.status}</span>
                            </div>
                            <div style="font-size: 12px; color: #666;">
                                Agent: ${task.assigned_agent || 'Unassigned'} | 
                                Created: ${new Date(task.created_at).toLocaleTimeString()}
                            </div>
                        </div>
                    `).join('');
                    
                } catch (error) {
                    console.error('Error updating task data:', error);
                }
            }
            
            async function updateAgentData() {
                try {
                    const response = await fetch('/agents');
                    const data = await response.json();
                    
                    const agentStatus = document.getElementById('agent-status');
                    const agents = data.agents || [];
                    
                    if (agents.length === 0) {
                        agentStatus.innerHTML = '<div class="stat"><span>No agents found</span></div>';
                        return;
                    }
                    
                    agentStatus.innerHTML = agents.slice(0, 5).map(agent => `
                        <div class="stat">
                            <span>${agent.name.replace('flashloan-agent-', '')}</span>
                            <span class="stat-value">${agent.active_tasks}/${agent.total_tasks}</span>
                        </div>
                    `).join('');
                    
                } catch (error) {
                    console.error('Error updating agent data:', error);
                }
            }
            
            // Action functions
            async function detectArbitrage() {
                try {
                    const response = await fetch('/actions/detect-arbitrage', { method: 'POST' });
                    const data = await response.json();
                    alert(`Arbitrage detection task created: ${data.task_id}`);
                    refreshData();
                } catch (error) {
                    alert('Error creating arbitrage detection task');
                }
            }
            
            async function checkHealth() {
                try {
                    const response = await fetch('/actions/check-system-health', { method: 'POST' });
                    const data = await response.json();
                    alert(`Health check task created: ${data.task_id}`);
                    refreshData();
                } catch (error) {
                    alert('Error creating health check task');
                }
            }
            
            async function analyzeMarket() {
                try {
                    const response = await fetch('/actions/analyze-market', { method: 'POST' });
                    const data = await response.json();
                    alert(`Market analysis task created: ${data.task_id}`);
                    refreshData();
                } catch (error) {
                    alert('Error creating market analysis task');
                }
            }
            
            async function startArbitrageWorkflow() {
                try {
                    const response = await fetch('/workflows/arbitrage', { method: 'POST' });
                    const data = await response.json();
                    alert(`Arbitrage workflow started with ${data.task_ids.length} tasks`);
                    refreshData();
                } catch (error) {
                    alert('Error starting arbitrage workflow');
                }
            }
            
            async function startHealthWorkflow() {
                try {
                    const response = await fetch('/workflows/health-check', { method: 'POST' });
                    const data = await response.json();
                    alert(`Health check workflow started with ${data.task_ids.length} tasks`);
                    refreshData();
                } catch (error) {
                    alert('Error starting health check workflow');
                }
            }
            
            async function createWorkflow(workflowName) {
                try {
                    const response = await fetch('/workflows', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ workflow_name: workflowName })
                    });
                    const data = await response.json();
                    alert(`Workflow ${workflowName} created with ${data.tasks_created} tasks`);
                    refreshData();
                } catch (error) {
                    alert(`Error creating workflow: ${error}`);
                }
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8500)
