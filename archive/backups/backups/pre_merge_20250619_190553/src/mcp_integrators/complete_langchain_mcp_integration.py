#!/usr/bin/env python3
"""
Complete LangChain MCP Integration System
========================================

This is the master integration script that:
1. Launches the enhanced LangChain coordinator
2. Starts the intelligent MCP server manager
3. Provides a unified interface for all operations
4. Implements advanced monitoring and self-healing
5. Offers web dashboard and API endpoints

Author: GitHub Copilot Assistant
Date: June 16, 2025
"""

import asyncio
import logging
import json
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable # Union removed
from pathlib import Path
from types import FrameType
from aiohttp import web, WSMsgType
# BaseRequest removed
# from aiohttp.web_response import Response # Remove unused Response alias
import weakref

# Import our enhanced components
from enhanced_langchain_coordinator import EnhancedLangChainCoordinator
from enhanced_mcp_server_manager import EnhancedMCPServerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('complete_integration.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class CompleteLangChainMCPSystem:
    """Complete integration system for LangChain and MCP servers"""
    
    def __init__(self, config_path: str = "enhanced_coordinator_config.yaml"):
        self.config_path = config_path
        
        # Core components
        self.coordinator: Optional[EnhancedLangChainCoordinator] = None
        self.server_manager: Optional[EnhancedMCPServerManager] = None
        
        # Web interface
        self.app: Optional[web.Application] = None
        self.web_runner: Optional[web.AppRunner] = None
        self.websocket_connections: weakref.WeakSet[web.WebSocketResponse] = weakref.WeakSet() # Explicitly aiohttp.web.WebSocketResponse
        
        # System state
        self.is_running = False
        self.start_time = datetime.now()
        self.system_metrics = {
            'requests_processed': 0,
            'errors_encountered': 0,
            'uptime_seconds': 0,
            'active_connections': 0
        }
        
        # Shutdown handling
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame: Optional[FrameType]) -> None:
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    async def initialize(self) -> bool:
        """Initialize all system components"""
        logger.info("🚀 Initializing Complete LangChain MCP Integration System...")
        
        try:
            # Initialize LangChain coordinator
            logger.info("🧠 Initializing LangChain coordinator...")
            self.coordinator = EnhancedLangChainCoordinator(self.config_path)
            if not await self.coordinator.initialize():
                logger.error("❌ Failed to initialize LangChain coordinator")
                return False
            
            # Initialize MCP server manager
            logger.info("📡 Initializing MCP server manager...")
            self.server_manager = EnhancedMCPServerManager(self.config_path)
            if not await self.server_manager.initialize():
                logger.error("❌ Failed to initialize MCP server manager")
                return False
            
            # Initialize web interface
            logger.info("🌐 Initializing web interface...")
            await self._init_web_interface()
            
            logger.info("✅ Complete LangChain MCP Integration System initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def _init_web_interface(self):
        """Initialize web interface and API endpoints"""
        self.app = web.Application()
        
        # Add CORS middleware
        async def cors_middleware(request: web.Request, handler: Callable[[web.Request], Awaitable[web.StreamResponse]]) -> web.StreamResponse:
            response: web.StreamResponse = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        self.app.middlewares.append(cors_middleware)
        
        # API routes
        self.app.router.add_get('/', self.dashboard_handler)
        self.app.router.add_get('/api/status', self.status_api)
        self.app.router.add_get('/api/servers', self.servers_api)
        self.app.router.add_post('/api/execute', self.execute_api)
        self.app.router.add_post('/api/query', self.query_api)
        self.app.router.add_get('/api/metrics', self.metrics_api)
        self.app.router.add_post('/api/restart/{server_name}', self.restart_server_api)
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # Serve static files (if dashboard exists)
        dashboard_path = Path('dashboard')
        if dashboard_path.exists():
            self.app.router.add_static('/', dashboard_path, name='static')
    
    async def start_system(self):
        """Start the complete integration system"""
        logger.info("🎪 Starting Complete LangChain MCP Integration System...")
        
        self.is_running = True
        
        try:
            # Start web server
            if self.app is None:
                logger.error("Web application not initialized. Cannot start web server.")
                raise RuntimeError("Web application not initialized.")
            self.web_runner = web.AppRunner(self.app)
            await self.web_runner.setup()
            site = web.TCPSite(self.web_runner, 'localhost', 8000)
            await site.start()
            logger.info("🌐 Web interface started on http://localhost:8000")
            
            # Start core system tasks
            assert self.coordinator is not None, "Coordinator not initialized before starting tasks"
            assert self.server_manager is not None, "Server manager not initialized before starting tasks"
            system_tasks = [
                asyncio.create_task(self.coordinator.start_coordination()),
                asyncio.create_task(self.server_manager.start_management()),
                asyncio.create_task(self._metrics_update_loop()),
                asyncio.create_task(self._websocket_broadcast_loop()),
                asyncio.create_task(self._system_health_monitor())
            ]
            
            # Wait for shutdown signal or task completion
            _, pending = await asyncio.wait( # Changed 'done' to '_'
                system_tasks + [asyncio.create_task(self.shutdown_event.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            logger.error(f"❌ System error: {e}")
        finally:
            await self.cleanup()
    
    async def _metrics_update_loop(self):
        """Update system metrics periodically"""
        while self.is_running:
            try:
                uptime = (datetime.now() - self.start_time).total_seconds()
                self.system_metrics['uptime_seconds'] = int(uptime) # Cast to int
                self.system_metrics['active_connections'] = len(self.websocket_connections)
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"📊 Metrics update error: {e}")
                await asyncio.sleep(30)
    
    async def _websocket_broadcast_loop(self):
        """Broadcast system updates via WebSocket"""
        while self.is_running:
            try:
                if self.websocket_connections:
                    # Get current system status
                    status_data = await self._get_complete_status()
                    
                    # Broadcast to all connected clients
                    from typing import List # Add List import for type hint
                    disconnected: List[web.WebSocketResponse] = []
                    for ws in list(self.websocket_connections): # Iterate over a copy for safe removal
                        try:
                            # Removed isinstance check, assuming ws is web.WebSocketResponse
                            await ws.send_str(json.dumps({
                                'type': 'status_update',
                                'data': status_data,
                                'timestamp': datetime.now().isoformat() # Correctly include timestamp
                            }))
                        except Exception as e_ws: # Catch exception for this specific WebSocket
                            logger.warning(f"Failed to send to WebSocket {ws}: {e_ws}")
                            disconnected.append(ws)
                    
                    # Remove disconnected clients
                    for ws_to_remove in disconnected:
                        self.websocket_connections.discard(ws_to_remove)
                
                await asyncio.sleep(5)  # Broadcast every 5 seconds
                
            except Exception as e:
                logger.error(f"📡 WebSocket broadcast error: {e}")
                await asyncio.sleep(10)
    
    async def _system_health_monitor(self):
        """Monitor overall system health"""
        while self.is_running:
            try:
                # Check coordinator health
                coordinator_healthy = self.coordinator and self.coordinator.is_running
                
                # Check server manager health
                manager_healthy = self.server_manager and self.server_manager.is_running
                
                # Log health status
                if coordinator_healthy and manager_healthy:
                    logger.debug("💚 System health: All components operational")
                else:
                    logger.warning(f"⚠️ System health: Coordinator={coordinator_healthy}, Manager={manager_healthy}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"🏥 Health monitor error: {e}")
                await asyncio.sleep(30)
    
    # Web API Handlers
    
    async def dashboard_handler(self, request: web.Request) -> web.Response:
        """Serve main dashboard"""
        dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>LangChain MCP Integration Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .status-healthy { color: #27ae60; }
                .status-unhealthy { color: #e74c3c; }
                .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
                .metric { padding: 10px; background: #ecf0f1; border-radius: 4px; }
                #log { height: 200px; overflow-y: scroll; background: #2c3e50; color: #ecf0f1; padding: 10px; font-family: monospace; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧠 LangChain MCP Integration Dashboard</h1>
                    <p>Real-time monitoring and control of the integrated system</p>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>System Status</h3>
                        <div id="system-status">Loading...</div>
                    </div>
                    
                    <div class="card">
                        <h3>MCP Servers</h3>
                        <div id="server-status">Loading...</div>
                    </div>
                    
                    <div class="card">
                        <h3>System Metrics</h3>
                        <div class="metrics" id="metrics">Loading...</div>
                    </div>
                    
                    <div class="card">
                        <h3>Query Interface</h3>
                        <input type="text" id="query-input" placeholder="Enter your query..." style="width: 100%; margin-bottom: 10px;">
                        <button onclick="executeQuery()" style="width: 100%; padding: 10px; background: #3498db; color: white; border: none; border-radius: 4px;">Execute Query</button>
                        <div id="query-result" style="margin-top: 10px; padding: 10px; background: #ecf0f1; border-radius: 4px; display: none;"></div>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px;">
                    <h3>System Log</h3>
                    <div id="log"></div>
                </div>
            </div>
            
            <script>
                let ws = null;
                
                function connectWebSocket() {
                    ws = new WebSocket('ws://localhost:8000/ws');
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        if (data.type === 'status_update') {
                            updateDashboard(data.data);
                        }
                        logMessage('WebSocket: ' + event.data);
                    };
                    
                    ws.onclose = function() {
                        logMessage('WebSocket connection closed, reconnecting...');
                        setTimeout(connectWebSocket, 5000);
                    };
                    
                    ws.onerror = function(error) {
                        logMessage('WebSocket error: ' + error);
                    };
                }
                
                function updateDashboard(data) {
                    // Update system status
                    document.getElementById('system-status').innerHTML = 
                        '<p>Uptime: ' + Math.floor(data.system_metrics.uptime_seconds / 60) + ' minutes</p>' +
                        '<p>Active Connections: ' + data.system_metrics.active_connections + '</p>' +
                        '<p>Requests Processed: ' + data.system_metrics.requests_processed + '</p>';
                    
                    // Update server status
                    let serverHtml = '';
                    if (data.servers) {
                        for (const [name, server] of Object.entries(data.servers.servers || {})) {
                            const statusClass = server.status === 'healthy' ? 'status-healthy' : 'status-unhealthy';
                            serverHtml += '<p><span class="' + statusClass + '">●</span> ' + name + ' (' + server.status + ')</p>';
                        }
                    }
                    document.getElementById('server-status').innerHTML = serverHtml || 'No servers';
                    
                    // Update metrics
                    document.getElementById('metrics').innerHTML = 
                        '<div class="metric">CPU Usage: N/A</div>' +
                        '<div class="metric">Memory Usage: N/A</div>' +
                        '<div class="metric">Response Time: N/A</div>' +
                        '<div class="metric">Success Rate: N/A</div>';
                }
                
                function logMessage(message) {
                    const log = document.getElementById('log');
                    const timestamp = new Date().toLocaleTimeString();
                    log.innerHTML += '[' + timestamp + '] ' + message + '\\n';
                    log.scrollTop = log.scrollHeight;
                }
                
                async function executeQuery() {
                    const query = document.getElementById('query-input').value;
                    if (!query) return;
                    
                    try {
                        const response = await fetch('/api/query', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ query: query })
                        });
                        
                        const result: str = await response.json();
                        const resultDiv = document.getElementById('query-result');
                        resultDiv.innerHTML = '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
                        resultDiv.style.display = 'block';
                        
                    } catch (error) {
                        logMessage('Query error: ' + error);
                    }
                }
                
                // Initialize
                connectWebSocket();
                
                // Refresh data every 30 seconds
                setInterval(async function() {
                    try {
                        const response = await fetch('/api/status');
                        const data = await response.json();
                        updateDashboard(data);
                    } catch (error) {
                        logMessage('Status update error: ' + error);
                    }
                }, 30000);
            </script>
        </body>
        </html>
        """
        return web.Response(text=dashboard_html, content_type='text/html')
    
    async def status_api(self, request: web.Request) -> web.Response:
        """API endpoint for system status"""
        try:
            status = await self._get_complete_status()
            self.system_metrics['requests_processed'] += 1
            return web.json_response(status)
        except Exception as e:
            self.system_metrics['errors_encountered'] += 1
            logger.error(f"❌ Status API error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def servers_api(self, request: web.Request) -> web.Response:
        """API endpoint for server status"""
        try:
            if self.server_manager:
                servers = await self.server_manager.get_server_status()
                return web.json_response(servers)
            else:
                return web.json_response({'error': 'Server manager not initialized'}, status=503)
        except Exception as e:
            logger.error(f"❌ Servers API error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def execute_api(self, request: web.Request) -> web.Response:
        """API endpoint for executing MCP commands"""
        try:
            data: Dict[str, Any] = await request.json()
            server_name = data.get('server')
            command = data.get('command')
            
            if not server_name or not command:
                return web.json_response({'error': 'server and command required'}, status=400)
            
            if self.coordinator:
                result: str = await self.coordinator.execute_mcp_command(str(server_name), str(command)) # Ensure string
                self.system_metrics['requests_processed'] += 1
                return web.json_response(result)
            else:
                return web.json_response({'error': 'Coordinator not initialized'}, status=503)
                
        except Exception as e:
            self.system_metrics['errors_encountered'] += 1
            logger.error(f"❌ Execute API error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def query_api(self, request: web.Request) -> web.Response:
        """API endpoint for LangChain queries"""
        try:
            data: Dict[str, Any] = await request.json()
            query = data.get('query')
            
            if not query:
                return web.json_response({'error': 'query required'}, status=400)
            
            if self.coordinator and 'coordinator' in self.coordinator.agents:
                # Use the coordinator agent to process the query
                result: str = await self.coordinator.agents['coordinator'].arun(str(query)) # Ensure string
                self.system_metrics['requests_processed'] += 1
                return web.json_response({'result': result, 'query': query})
            else:
                return web.json_response({'error': 'Coordinator agent not available'}, status=503)
                
        except Exception as e:
            self.system_metrics['errors_encountered'] += 1
            logger.error(f"❌ Query API error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def metrics_api(self, request: web.Request) -> web.Response:
        """API endpoint for system metrics"""
        try:
            metrics: Dict[str, Any] = dict(self.system_metrics) # Corrected typo: system_etrics -> system_metrics
            metrics['timestamp'] = datetime.now().isoformat()
            return web.json_response(metrics)
        except Exception as e:
            logger.error(f"❌ Metrics API error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def restart_server_api(self, request: web.Request) -> web.Response:
        """API endpoint for restarting servers"""
        try:
            server_name = request.match_info.get('server_name')
            if not server_name:
                 return web.json_response({'error': 'server_name missing in path'}, status=400)

            if self.server_manager and hasattr(self.server_manager, 'servers') and server_name in self.server_manager.servers:
                # Use public method instead of protected _restart_server
                if hasattr(self.server_manager, 'restart_server'):
                    await self.server_manager.restart_server(server_name)
                else:
                    # Fallback to protected method if public method doesn't exist
                    await self.server_manager._restart_server(server_name)  # type: ignore
                return web.json_response({'message': f'Server {server_name} restart initiated'})
            else:
                return web.json_response({'error': 'Server not found'}, status=404)
                
        except Exception as e:
            logger.error(f"❌ Restart API error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse: # Qualified types
        """WebSocket handler for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request) # 'request' now refers to the correctly typed web.Request parameter
        
        self.websocket_connections.add(ws)
        logger.info("🔌 New WebSocket connection established")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        # Handle incoming WebSocket messages if needed
                        if data.get('type') == 'ping':
                            await ws.send_str(json.dumps({'type': 'pong'}))
                    except json.JSONDecodeError:
                        logger.warning("📡 Invalid JSON received via WebSocket")
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"📡 WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"📡 WebSocket handler error: {e}")
        finally:
            self.websocket_connections.discard(ws)
            logger.info("🔌 WebSocket connection closed")
        
        return ws
    
    async def _get_complete_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': dict(self.system_metrics),
            'coordinator_status': 'running' if self.coordinator and self.coordinator.is_running else 'stopped',
            'manager_status': 'running' if self.server_manager and self.server_manager.is_running else 'stopped'
        }
        
        # Add server status if available
        if self.server_manager:
            try:
                status['servers'] = await self.server_manager.get_server_status()
            except Exception as e:
                status['servers_error'] = str(e)
        
        # Add coordinator status if available
        if self.coordinator:
            try:
                status['coordinator_details'] = {
                    'active_agents': len(self.coordinator.agents),
                    'active_chains': len(self.coordinator.chains),
                    'memory_enabled': self.coordinator.memory is not None
                }
            except Exception as e:
                status['coordinator_error'] = str(e)
        
        return status
    
    async def cleanup(self):
        """Cleanup resources during shutdown"""
        logger.info("🧹 Cleaning up system resources...")
        
        self.is_running = False
        
        # Close WebSocket connections
        for ws in list(self.websocket_connections):
            try:
                await ws.close()
            except Exception:
                pass
        
        # Stop web server
        if self.web_runner:
            await self.web_runner.cleanup()
        
        # Shutdown coordinator
        if self.coordinator:
            await self.coordinator.shutdown()
        
        # Shutdown server manager
        if self.server_manager:
            await self.server_manager.shutdown()
        
        logger.info("✅ System cleanup completed")

async def main():
    """Main execution function"""
    system = CompleteLangChainMCPSystem()
    
    try:
        print("🚀 Starting Complete LangChain MCP Integration System")
        print("=" * 60)
        
        # Initialize system
        if not await system.initialize():
            logger.error("❌ Failed to initialize system")
            return 1
        
        print("\n✅ System initialized successfully!")
        print("\n🌐 Dashboard available at: http://localhost:8000")
        print("📊 API endpoints available at: http://localhost:8000/api/")
        print("\n🔧 Press Ctrl+C to shutdown gracefully\n")
        
        # Start system
        await system.start_system()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
        return 0
    except Exception as e:
        logger.error(f"❌ System error: {e}")
        return 1
    finally:
        await system.cleanup()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
