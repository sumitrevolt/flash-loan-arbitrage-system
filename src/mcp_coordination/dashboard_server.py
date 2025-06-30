# -*- coding: utf-8 -*-
"""
Dashboard Server for MCP Coordination System

This module provides a web-based dashboard for monitoring, managing, and
coordinating all MCP servers in the unified system.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Coroutine
import asyncio
import logging
import time

from .deployment_manager import DeploymentManager
from .health_monitor import HealthMonitor
from .mcp_server_registry import MCPServerRegistry
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

logger = logging.getLogger(__name__)


class DashboardServer:
    """
    Web dashboard for MCP server coordination and monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config: Dict[str, Any] = config
        self.dashboard_config: Dict[str, Any] = config.get("dashboard", {})
        
        # Core components (will be injected)
        self.server_registry: Optional[MCPServerRegistry] = None
        self.health_monitor: Optional[HealthMonitor] = None
        self.deployment_manager: Optional[DeploymentManager] = None
        
        # FastAPI app
        self.app: FastAPI = FastAPI(
            title="MCP Coordination Dashboard",
            description="Unified monitoring and management for MCP servers",
            version="1.0.0"

        
        # Dashboard configuration
        self.host: str = self.dashboard_config.get("host", "0.0.0.0")
        self.port: int = self.dashboard_config.get("port", 8080)
        self.debug: bool = self.dashboard_config.get("debug", False)
        
        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []
        
        # Background tasks
        self.metrics_broadcast_task: Optional[asyncio.Task[None]] = None
        self.server_task: Optional[asyncio.Task[None]] = None
        
        # Setup FastAPI app
        self._setup_app()
        
        logger.info("[INIT] Dashboard Server initialized")
    
    def _setup_app(self):
        """Setup FastAPI application with routes and middleware"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],

        
        # Setup static files and templates
        self._setup_static_files()
        
        # Setup routes
        self._setup_routes()
        
        # Setup WebSocket endpoints
        self._setup_websockets()
    
    def _setup_static_files(self):
        """Setup static files and templates"""
        # Create dashboard assets directory if it doesn't exist
        dashboard_dir = Path("src/mcp_coordination/dashboard")
        dashboard_dir.mkdir(exist_ok=True)
        
        static_dir = dashboard_dir / "static"
        static_dir.mkdir(exist_ok=True)
        
        templates_dir = dashboard_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Setup templates
        self.templates: Jinja2Templates = Jinja2Templates(directory=str(templates_dir))
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request) -> HTMLResponse:
            """Main dashboard page"""
            return await self._render_dashboard(request)
        
        @self.app.get("/api/status")
        async def get_system_status() -> Coroutine[Any, Any, Dict[str, Any]]:
            """Get overall system status"""
            return await self._get_system_status()
        
        @self.app.get("/api/servers")
        async def get_all_servers() -> Coroutine[Any, Any, List[Dict[str, Any]]]:
            """Get all registered servers"""
            return await self._get_all_servers()
        
        @self.app.get("/api/servers/{server_id}")
        async def get_server_details(server_id: str) -> Coroutine[Any, Any, Dict[str, Any]]:
            """Get detailed information about a specific server"""
            return await self._get_server_details(server_id)
        
        @self.app.get("/api/servers/{server_id}/health")
        async def get_server_health(server_id: str) -> Coroutine[Any, Any, Dict[str, Any]]:
            """Get health information for a specific server"""
            return await self._get_server_health(server_id)
        
        @self.app.post("/api/servers/{server_id}/start")
        async def start_server(server_id: str) -> Coroutine[Any, Any, Dict[str, Any]]:
            """Start a specific server"""
            return await self._start_server(server_id)
        
        @self.app.post("/api/servers/{server_id}/stop")
        async def stop_server(server_id: str) -> Coroutine[Any, Any, Dict[str, Any]]:
            """Stop a specific server"""
            return await self._stop_server(server_id)
        
        @self.app.post("/api/servers/{server_id}/restart")
        async def restart_server(server_id: str) -> Coroutine[Any, Any, Dict[str, Any]]:
            """Restart a specific server"""
            return await self._restart_server(server_id)
        
        @self.app.post("/api/deployment/start-all")
        async def start_all_servers() -> Coroutine[Any, Any, Dict[str, Any]]:
            """Start all servers"""
            return await self._start_all_servers()
        
        @self.app.post("/api/deployment/stop-all")
        async def stop_all_servers() -> Coroutine[Any, Any, Dict[str, Any]]:
            """Stop all servers"""
            return await self._stop_all_servers()
        
        @self.app.get("/api/health/alerts")
        async def get_active_alerts() -> Coroutine[Any, Any, List[Dict[str, Any]]]:
            """Get active health alerts"""
            return await self._get_active_alerts()
        
        @self.app.post("/api/health/circuit-breaker/{server_id}/reset")
        async def reset_circuit_breaker(server_id: str) -> Coroutine[Any, Any, Dict[str, Any]]:
            """Reset circuit breaker for a server"""
            return await self._reset_circuit_breaker(server_id)
        
        @self.app.get("/api/metrics/system")
        async def get_system_metrics() -> Coroutine[Any, Any, Dict[str, Any]]:
            """Get system-wide metrics"""
            return await self._get_system_metrics()
        
        @self.app.get("/api/metrics/servers")
        async def get_server_metrics() -> Coroutine[Any, Any, Dict[str, Any]]:
            """Get metrics for all servers"""
            return await self._get_server_metrics()
        
        @self.app.get("/api/discovery/scan")
        async def trigger_discovery() -> Coroutine[Any, Any, Dict[str, Any]]:
            """Trigger server discovery scan"""
            return await self._trigger_discovery()
        
        @self.app.get("/api/config/export")
        async def export_configuration() -> Coroutine[Any, Any, Dict[str, Any]]:
            """Export complete system configuration"""
            return await self._export_configuration()
    
    def _setup_websockets(self):
        """Setup WebSocket endpoints for real-time updates"""
        
        @self.app.websocket("/ws/metrics")
        async def websocket_metrics(websocket: WebSocket):
            """WebSocket endpoint for real-time metrics"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
            except Exception as e:
                logger.error(f"[WS] Metrics websocket error: {e}")
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
        
        @self.app.websocket("/ws/logs")
        async def websocket_logs(websocket: WebSocket):
            """WebSocket endpoint for real-time logs"""
            await websocket.accept()
            
            try:
                # Send recent logs and keep connection for real-time updates
                while True:
                    await asyncio.sleep(5)
                    # In a real implementation, you'd stream actual logs
                    log_data = {
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "message": "System operational",
                        "source": "dashboard"

                    await websocket.send_json(log_data)
                    
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"[WS] Logs websocket error: {e}")
    
    async def initialize(self, server_registry: MCPServerRegistry, health_monitor: HealthMonitor, deployment_manager: DeploymentManager) -> None:
        """Initialize dashboard with core components"""
        try:
            self.server_registry = server_registry
            self.health_monitor = health_monitor
            self.deployment_manager = deployment_manager
            
            # Create dashboard template
            await self._create_dashboard_template()
            
            # Start background tasks
            self.metrics_broadcast_task = asyncio.create_task(self._metrics_broadcast_loop())
            
            logger.info("[OK] Dashboard Server initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] Dashboard Server initialization failed: {e}")
            raise
    
    async def start_server(self) -> None:
        """Start the dashboard web server"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info" if self.debug else "warning",
                access_log=self.debug

            
            server = uvicorn.Server(config)
            self.server_task = asyncio.create_task(server.serve())
            
            logger.info(f"[OK] Dashboard server started at http://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to start dashboard server: {e}")
            raise
    
    async def _create_dashboard_template(self) -> None:
        """Create the main dashboard HTML template"""
        template_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Coordination Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 1rem 2rem; }
        .header h1 { margin: 0; }
        .dashboard { display: grid; grid-template-columns: 250px 1fr; min-height: calc(100vh - 80px); }
        .sidebar { background: white; border-right: 1px solid #ddd; padding: 1rem; }
        .main-content { padding: 2rem; }
        .nav-link { display: block; padding: 0.5rem; margin: 0.25rem 0; text-decoration: none; color: #333; border-radius: 4px; }
        .nav-link:hover, .nav-link.active { background: #3498db; color: white; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .metric-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2rem; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; margin-top: 0.5rem; }
        .server-grid { display: grid; gap: 1rem; }
        .server-card { background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .server-header { display: flex; justify-content: between; align-items: center; margin-bottom: 1rem; }
        .server-name { font-weight: bold; font-size: 1.1rem; }
        .status-badge { padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
        .status-healthy { background: #d4edda; color: #155724; }
        .status-unhealthy { background: #f8d7da; color: #721c24; }
        .status-unknown { background: #fff3cd; color: #856404; }
        .btn { padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }
        .btn-primary { background: #3498db; color: white; }
        .btn-success { background: #27ae60; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-warning { background: #f39c12; color: white; }
        .btn:hover { opacity: 0.9; }
        .alert { padding: 1rem; margin-bottom: 1rem; border-radius: 4px; }
        .alert-warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
        .alert-danger { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .loading { text-align: center; padding: 2rem; color: #7f8c8d; }
        .real-time { position: fixed; top: 20px; right: 20px; background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .connection-status { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 0.5rem; }
        .connected { background: #27ae60; }
        .disconnected { background: #e74c3c; }
    </style>
</head>
<body>
    <div class="header">
        <h1>MCP Coordination Dashboard</h1>
        <div style="float: right; margin-top: -2rem;">
            <span id="current-time"></span>
        </div>
    </div>

    <div class="dashboard">
        <div class="sidebar">
            <nav>
                <a href="#overview" class="nav-link active" onclick="showSection('overview')">Overview</a>
                <a href="#servers" class="nav-link" onclick="showSection('servers')">Servers</a>
                <a href="#health" class="nav-link" onclick="showSection('health')">Health & Alerts</a>
                <a href="#deployment" class="nav-link" onclick="showSection('deployment')">Deployment</a>
                <a href="#metrics" class="nav-link" onclick="showSection('metrics')">Metrics</a>
                <a href="#logs" class="nav-link" onclick="showSection('logs')">Logs</a>
            </nav>
        </div>

        <div class="main-content">
            <div id="overview-section" class="section">
                <h2>System Overview</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="total-servers">-</div>
                        <div class="metric-label">Total Servers</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="healthy-servers">-</div>
                        <div class="metric-label">Healthy Servers</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="running-servers">-</div>
                        <div class="metric-label">Running Servers</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="active-alerts">-</div>
                        <div class="metric-label">Active Alerts</div>
                    </div>
                </div>
                <div id="system-alerts"></div>
            </div>

            <div id="servers-section" class="section" style="display: none;">
                <h2>Server Management</h2>
                <div style="margin-bottom: 1rem;">
                    <button class="btn btn-success" onclick="startAllServers()">Start All</button>
                    <button class="btn btn-danger" onclick="stopAllServers()">Stop All</button>
                    <button class="btn btn-primary" onclick="refreshServers()">Refresh</button>
                </div>
                <div id="servers-grid" class="server-grid">
                    <div class="loading">Loading servers...</div>
                </div>
            </div>

            <div id="health-section" class="section" style="display: none;">
                <h2>Health Monitoring & Alerts</h2>
                <div id="health-alerts"></div>
                <div id="health-metrics"></div>
            </div>

            <div id="deployment-section" class="section" style="display: none;">
                <h2>Deployment Management</h2>
                <div id="deployment-status"></div>
            </div>

            <div id="metrics-section" class="section" style="display: none;">
                <h2>System Metrics</h2>
                <div id="metrics-content"></div>
            </div>

            <div id="logs-section" class="section" style="display: none;">
                <h2>System Logs</h2>
                <div id="logs-content" style="background: #000; color: #00ff00; padding: 1rem; border-radius: 4px; font-family: monospace; height: 400px; overflow-y: scroll;"></div>
            </div>
        </div>
    </div>

    <div class="real-time">
        <div>
            <span class="connection-status" id="ws-status"></span>
            Real-time: <span id="connection-text">Connecting...</span>
        </div>
    </div>

    <script>
        let ws = null;
        let wsReconnectInterval = 5000;

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            updateTime();
            setInterval(updateTime, 1000);
            connectWebSocket();
            loadInitialData();
            setInterval(refreshData, 30000); // Refresh every 30 seconds
        });

        function updateTime() {
            document.getElementById('current-time').textContent = new Date().toLocaleString();


        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/metrics`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                document.getElementById('ws-status').className = 'connection-status connected';
                document.getElementById('connection-text').textContent = 'Connected';
            };
            
            ws.onclose = function() {
                document.getElementById('ws-status').className = 'connection-status disconnected';
                document.getElementById('connection-text').textContent = 'Disconnected';
                setTimeout(connectWebSocket, wsReconnectInterval);
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateRealTimeData(data);
            };


        function showSection(sectionName) {
            // Hide all sections
            document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            
            // Show selected section
            document.getElementById(sectionName + '-section').style.display = 'block';
            event.target.classList.add('active');
            
            // Load section-specific data
            loadSectionData(sectionName);


        async function loadInitialData() {
            await Promise.all([
                loadSystemStatus(),
                loadServers()
            ]);


        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('total-servers').textContent = data.total_servers || 0;
                document.getElementById('healthy-servers').textContent = data.healthy_servers || 0;
                document.getElementById('running-servers').textContent = data.running_servers || 0;
                document.getElementById('active-alerts').textContent = data.active_alerts || 0;
                
                // Show system alerts if any
                if (data.alerts && data.alerts.length > 0) {
                    const alertsHtml = data.alerts.map(alert => 
                        `<div class="alert alert-${alert.severity}">${alert.message}</div>`
                    ).join('');
                    document.getElementById('system-alerts').innerHTML = alertsHtml;

                
            } catch (error) {
                console.error('Failed to load system status:', error);



        async function loadServers() {
            try {
                const response = await fetch('/api/servers');
                const servers = await response.json();
                
                const serversGrid = document.getElementById('servers-grid');
                serversGrid.innerHTML = servers.map(server => `
                    <div class="server-card">
                        <div class="server-header">
                            <div class="server-name">${server.name}</div>
                            <span class="status-badge status-${server.status}">${server.status}</span>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <strong>Tier:</strong> ${server.tier}<br>
                            <strong>Protocol:</strong> ${server.protocol}<br>
                            <strong>URL:</strong> ${server.base_url}
                        </div>
                        <div>
                            <button class="btn btn-success" onclick="startServer('${server.server_id}')">Start</button>
                            <button class="btn btn-danger" onclick="stopServer('${server.server_id}')">Stop</button>
                            <button class="btn btn-warning" onclick="restartServer('${server.server_id}')">Restart</button>
                        </div>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Failed to load servers:', error);
                document.getElementById('servers-grid').innerHTML = '<div class="alert alert-danger">Failed to load servers</div>';



        function loadSectionData(section) {
            switch(section) {
                case 'health':
                    loadHealthData();
                    break;
                case 'deployment':
                    loadDeploymentData();
                    break;
                case 'metrics':
                    loadMetricsData();
                    break;
                case 'logs':
                    connectLogsWebSocket();
                    break;



        async function loadHealthData() {
            try {
                const response = await fetch('/api/health/alerts');
                const alerts = await response.json();
                
                const alertsHtml = alerts.map(alert => `
                    <div class="alert alert-${alert.severity}">
                        <strong>${alert.server_name}:</strong> ${alert.message}
                        <small style="float: right;">${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                `).join('');
                
                document.getElementById('health-alerts').innerHTML = alertsHtml || '<p>No active alerts</p>';
                
            } catch (error) {
                console.error('Failed to load health data:', error);



        async function startServer(serverId) {
            try {
                const response = await fetch(`/api/servers/${serverId}/start`, { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    refreshServers();
                } else {
                    alert(`Failed to start server: ${result.message}`);

            } catch (error) {
                alert(`Error starting server: ${error.message}`);



        async function stopServer(serverId) {
            try {
                const response = await fetch(`/api/servers/${serverId}/stop`, { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    refreshServers();
                } else {
                    alert(`Failed to stop server: ${result.message}`);

            } catch (error) {
                alert(`Error stopping server: ${error.message}`);



        async function restartServer(serverId) {
            try {
                const response = await fetch(`/api/servers/${serverId}/restart`, { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    refreshServers();
                } else {
                    alert(`Failed to restart server: ${result.message}`);

            } catch (error) {
                alert(`Error restarting server: ${error.message}`);



        async function startAllServers() {
            try {
                const response = await fetch('/api/deployment/start-all', { method: 'POST' });
                const result = await response.json();
                refreshServers();
                alert(`Deployment completed: ${result.successful}/${result.total} servers started`);
            } catch (error) {
                alert(`Error starting all servers: ${error.message}`);



        async function stopAllServers() {
            if (confirm('Are you sure you want to stop all servers?')) {
                try {
                    const response = await fetch('/api/deployment/stop-all', { method: 'POST' });
                    const result = await response.json();
                    refreshServers();
                    alert(`Shutdown completed: ${result.successful}/${result.total} servers stopped`);
                } catch (error) {
                    alert(`Error stopping all servers: ${error.message}`);




        function refreshServers() {
            loadServers();
            loadSystemStatus();


        function refreshData() {
            loadSystemStatus();
            // Refresh current section data
            const activeSection = document.querySelector('.nav-link.active').getAttribute('href').substring(1);
            loadSectionData(activeSection);


        function updateRealTimeData(data) {
            // Update real-time metrics from WebSocket
            if (data.total_servers) document.getElementById('total-servers').textContent = data.total_servers;
            if (data.healthy_servers) document.getElementById('healthy-servers').textContent = data.healthy_servers;
            if (data.running_servers) document.getElementById('running-servers').textContent = data.running_servers;
            if (data.active_alerts) document.getElementById('active-alerts').textContent = data.active_alerts;


        function connectLogsWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
            const logsWs = new WebSocket(wsUrl);
            
            logsWs.onmessage = function(event) {
                const logData = JSON.parse(event.data);
                const logsContent = document.getElementById('logs-content');
                const logLine = `[${logData.timestamp}] ${logData.level}: ${logData.message}\\n`;
                logsContent.textContent += logLine;
                logsContent.scrollTop = logsContent.scrollHeight;
            };

    </script>
</body>
</html>
        '''
        
        templates_dir = Path("src/mcp_coordination/dashboard/templates")
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_file = templates_dir / "dashboard.html"
        with open(template_file, 'w') as f:
            f.write(template_content)
    
    async def _render_dashboard(self, request: Request) -> HTMLResponse:
        """Render the main dashboard page"""
        return self.templates.TemplateResponse("dashboard.html", {"request": request})
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            if not self.health_monitor or not self.deployment_manager:
                return {"error": "Core components not initialized"}
            
            health_status = await self.health_monitor.get_overall_health_status()
            deployment_status = await self.deployment_manager.get_deployment_status()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": health_status.get("overall_status", "unknown"),
                "total_servers": health_status.get("total_servers", 0),
                "healthy_servers": health_status.get("healthy_servers", 0),
                "running_servers": deployment_status.get("running_servers", 0),
                "active_alerts": health_status.get("active_alerts", 0),
                "health_percentage": health_status.get("health_percentage", 0),
                "deployment_percentage": deployment_status.get("deployment_percentage", 0),
                "tier_health": health_status.get("tier_health", {}),
                "circuit_breakers_open": health_status.get("circuit_breakers_open", 0)

            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get system status: {e}")
            return {"error": str(e)}
    
    async def _get_all_servers(self) -> List[Dict[str, Any]]:
        """Get all registered servers with status"""
        try:
            if not self.server_registry:
                return [{"error": "Server registry not initialized"}]
            
            servers_data: List[Dict[str, Any]] = []
            for server_id, server_info in self.server_registry.servers.items():
                servers_data.append({
                    "server_id": server_id,
                    "name": server_info.name,
                    "description": server_info.description,
                    "tier": server_info.tier.value,
                    "protocol": server_info.protocol.value,
                    "status": server_info.status.value,
                    "host": server_info.host,
                    "port": server_info.port,
                    "base_url": server_info.get_base_url(),
                    "health_url": server_info.get_health_url(),
                    "capabilities": [cap.name for cap in server_info.capabilities],
                    "last_health_check": server_info.last_health_check.isoformat() if server_info.last_health_check else None,
                    "version": server_info.version

            
            return servers_data
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get servers: {e}")
            return [{"error": str(e)}]
    
    async def _get_server_details(self, server_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific server"""
        try:
            if not self.server_registry or not self.health_monitor:
                return {"error": "Core components not initialized"}
            
            server_info = await self.server_registry.get_server_by_id(server_id)
            if not server_info:
                raise HTTPException(status_code=404, detail="Server not found")
            
            health_summary = await self.health_monitor.get_server_health_summary(server_id)
            
            return {
                "server_info": {
                    "server_id": server_id,
                    "name": server_info.name,
                    "description": server_info.description,
                    "tier": server_info.tier.value,
                    "protocol": server_info.protocol.value,
                    "status": server_info.status.value,
                    "host": server_info.host,
                    "port": server_info.port,
                    "base_url": server_info.get_base_url(),
                    "capabilities": [cap.name for cap in server_info.capabilities],
                    "dependencies": server_info.dependencies,
                    "version": server_info.version,
                    "startup_command": server_info.startup_command,
                    "config_file": server_info.config_file
                },
                "health_summary": health_summary

            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get server details for {server_id}: {e}")
            return {"error": str(e)}
    
    async def _get_server_health(self, server_id: str) -> Dict[str, Any]:
        """Get health information for a specific server"""
        try:
            if not self.health_monitor:
                return {"error": "Health monitor not initialized"}
            
            health_summary = await self.health_monitor.get_server_health_summary(server_id)
            return health_summary
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get server health for {server_id}: {e}")
            return {"error": str(e)}
    
    async def _start_server(self, server_id: str) -> Dict[str, Any]:
        """Start a specific server"""
        try:
            if not self.deployment_manager:
                return {"error": "Deployment manager not initialized", "success": False}
            
            result = await self.deployment_manager.deploy_server(server_id)
            return {
                "success": result.success,
                "message": result.message,
                "status": result.status.value,
                "process_id": result.process_id,
                "container_id": result.container_id

            
        except Exception as e:
            logger.error(f"[ERROR] Failed to start server {server_id}: {e}")
            return {"error": str(e), "success": False}
    
    async def _stop_server(self, server_id: str) -> Dict[str, Any]:
        """Stop a specific server"""
        try:
            if not self.deployment_manager:
                return {"error": "Deployment manager not initialized", "success": False}
            
            success = await self.deployment_manager.stop_server(server_id)
            return {
                "success": success,
                "message": "Server stopped successfully" if success else "Failed to stop server"

            
        except Exception as e:
            logger.error(f"[ERROR] Failed to stop server {server_id}: {e}")
            return {"error": str(e), "success": False}
    
    async def _restart_server(self, server_id: str) -> Dict[str, Any]:
        """Restart a specific server"""
        try:
            if not self.deployment_manager:
                return {"error": "Deployment manager not initialized", "success": False}
            
            result = await self.deployment_manager.restart_server(server_id)
            return {
                "success": result.success,
                "message": result.message,
                "status": result.status.value

            
        except Exception as e:
            logger.error(f"[ERROR] Failed to restart server {server_id}: {e}")
            return {"error": str(e), "success": False}
    
    async def _start_all_servers(self) -> Dict[str, Any]:
        """Start all servers"""
        try:
            if not self.deployment_manager:
                return {"error": "Deployment manager not initialized", "success": False}
            
            results = await self.deployment_manager.deploy_all_servers()
            successful = len([r for r in results.values() if r.success])
            
            return {
                "success": True,
                "total": len(results),
                "successful": successful,
                "failed": len(results) - successful,
                "results": {
                    server_id: {
                        "success": result.success,
                        "message": result.message,
                        "status": result.status.value

                    for server_id, result in results.items()


            
        except Exception as e:
            logger.error(f"[ERROR] Failed to start all servers: {e}")
            return {"error": str(e), "success": False}
    
    async def _stop_all_servers(self) -> Dict[str, Any]:
        """Stop all servers"""
        try:
            if not self.deployment_manager:
                return {"error": "Deployment manager not initialized", "success": False}
            
            results = await self.deployment_manager.stop_all_servers()
            successful = len([r for r in results.values() if r])
            
            return {
                "success": True,
                "total": len(results),
                "successful": successful,
                "failed": len(results) - successful,
                "results": results

            
        except Exception as e:
            logger.error(f"[ERROR] Failed to stop all servers: {e}")
            return {"error": str(e), "success": False}
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active health alerts"""
        try:
            if not self.health_monitor:
                return [{"error": "Health monitor not initialized"}]
            
            alerts: List[Dict[str, Any]] = await self.health_monitor.get_active_alerts()
            return alerts
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get active alerts: {e}")
            return [{"error": str(e)}]
    
    async def _reset_circuit_breaker(self, server_id: str) -> Dict[str, Any]:
        """Reset circuit breaker for a server"""
        try:
            if not self.health_monitor:
                return {"error": "Health monitor not initialized", "success": False}
            
            success = await self.health_monitor.force_circuit_breaker_reset(server_id)
            return {
                "success": success,
                "message": "Circuit breaker reset successfully" if success else "Failed to reset circuit breaker"

            
        except Exception as e:
            logger.error(f"[ERROR] Failed to reset circuit breaker for {server_id}: {e}")
            return {"error": str(e), "success": False}
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        try:
            if not self.health_monitor or not self.deployment_manager:
                return {"error": "Core components not initialized"}
            
            health_status = await self.health_monitor.get_overall_health_status()
            deployment_status = await self.deployment_manager.get_deployment_status()
            
            return {
                "health_metrics": health_status.get("monitoring_stats", {}),
                "deployment_metrics": deployment_status.get("deployment_stats", {}),
                "system_uptime": time.time() - (deployment_status.get("deployment_stats", {}).get("last_deployment_time", time.time())),
                "timestamp": datetime.now().isoformat()

            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get system metrics: {e}")
            return {"error": str(e)}
    
    async def _get_server_metrics(self) -> Dict[str, Any]:
        """Get metrics for all servers"""
        try:
            if not self.health_monitor:
                return {"error": "Health monitor not initialized"}
            
            server_metrics = {}
            for server_id in self.server_registry.servers.keys():
                health_summary = await self.health_monitor.get_server_health_summary(server_id)
                server_metrics[server_id] = health_summary
            
            return server_metrics
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get server metrics: {e}")
            return {"error": str(e)}
    
    async def _trigger_discovery(self) -> Dict[str, Any]:
        """Trigger server discovery scan"""
        try:
            if not self.server_registry:
                return {"error": "Server registry not initialized", "success": False}
            
            discovered_servers = await self.server_registry.discover_servers()
            
            return {
                "success": True,
                "discovered_count": len(discovered_servers),
                "message": f"Discovery completed: {len(discovered_servers)} servers found",
                "servers": [
                    {
                        "server_id": server.server_id,
                        "name": server.name,
                        "tier": server.tier.value

                    for server in discovered_servers


            
        except Exception as e:
            logger.error(f"[ERROR] Failed to trigger discovery: {e}")
            return {"error": str(e), "success": False}
    
    async def _export_configuration(self) -> Dict[str, Any]:
        """Export complete system configuration"""
        try:
            config_data = {
                "timestamp": datetime.now().isoformat(),
                "server_registry": await self.server_registry.export_server_catalog() if self.server_registry else {},
                "deployment_manifest": await self.deployment_manager.export_deployment_manifest() if self.deployment_manager else {},
                "health_status": await self.health_monitor.get_overall_health_status() if self.health_monitor else {}

            
            return config_data
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to export configuration: {e}")
            return {"error": str(e)}
    
    async def _metrics_broadcast_loop(self) -> None:
        """Background task to broadcast real-time metrics via WebSocket"""
        while True:
            try:
                if self.websocket_connections:
                    # Get current metrics
                    metrics = await self._get_system_status()
                    
                    # Broadcast to all connected clients
                    disconnected = []
                    for ws in self.websocket_connections:
                        try:
                            await ws.send_json(metrics)
                        except:
                            disconnected.append(ws)
                    
                    # Remove disconnected clients
                    for ws in disconnected:
                        self.websocket_connections.remove(ws)
                
                await asyncio.sleep(5)  # Broadcast every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Metrics broadcast failed: {e}")
                await asyncio.sleep(5)
    
    async def shutdown(self) -> None:
        """Shutdown the dashboard server"""
        logger.info("[SHUTDOWN] Shutting down Dashboard Server...")
        
        # Cancel background tasks
        if self.metrics_broadcast_task:
            self.metrics_broadcast_task.cancel()
            try:
                await self.metrics_broadcast_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket connections
        for ws in self.websocket_connections:
            try:
                await ws.close()
            except:
                pass
        
        # Stop web server
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[SHUTDOWN] Dashboard Server shutdown complete")