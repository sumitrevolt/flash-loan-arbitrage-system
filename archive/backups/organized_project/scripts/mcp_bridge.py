#!/usr/bin/env python3
"""
MCP Bridge for GitHub Copilot Integration
This script creates a bridge between GitHub Copilot and Docker-based MCP servers.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, Set
import aiohttp
import websockets
from websockets.server import serve, WebSocketServerProtocol
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPBridge:
    def __init__(self, port: int = 8888):
        self.port = port
        self.mcp_servers = {
            "flash_loan_blockchain": "http://localhost:8101",
            "defi_analyzer": "http://localhost:8102", 
            "flash_loan": "http://localhost:8103",
            "arbitrage": "http://localhost:8104",
            "liquidity": "http://localhost:8105",
            "price_feed": "http://localhost:8106",
            "risk_manager": "http://localhost:8107",
            "portfolio": "http://localhost:8108",
            "api_client": "http://localhost:8109",
            "database": "http://localhost:8110",
            "cache_manager": "http://localhost:8111",
            "file_processor": "http://localhost:8112",
            "notification": "http://localhost:8113",
            "monitoring": "http://localhost:8114",
            "security": "http://localhost:8115",
            "data_analyzer": "http://localhost:8116",
            "web_scraper": "http://localhost:8117",
            "task_queue": "http://localhost:8118",
            "filesystem": "http://localhost:8119",
            "coordinator": "http://localhost:8120"
        }
        self.active_connections: Set[WebSocketServerProtocol] = set()
        
    async def check_server_health(self, server_name: str, endpoint: str) -> bool:
        """Check if an MCP server is healthy and responsive."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/health", timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Health check failed for {server_name}: {e}")
            return False
    async def get_available_servers(self) -> Dict[str, str]:
        """Get list of available and healthy MCP servers."""
        available_servers: Dict[str, str] = {}
        
        for server_name, endpoint in self.mcp_servers.items():
            if await self.check_server_health(server_name, endpoint):
                available_servers[server_name] = endpoint
                logger.info(f"✓ {server_name} is available at {endpoint}")
            else:
                logger.warning(f"✗ {server_name} is not available at {endpoint}")
                
        return available_servers
    
    async def proxy_request(self, server_name: str, endpoint: str, method: str, path: str, data: Any = None) -> Dict[str, Any]:
        """Proxy a request to an MCP server."""
        try:
            url = f"{endpoint}{path}"
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, timeout=30) as response:
                        result = await response.json()
                        return {"status": "success", "data": result}
                elif method.upper() == "POST":
                    async with session.post(url, json=data, timeout=30) as response:
                        result = await response.json()
                        return {"status": "success", "data": result}
                else:
                    return {"status": "error", "message": f"Unsupported method: {method}"}
        except Exception as e:
            logger.error(f"Error proxying request to {server_name}: {e}")
            return {"status": "error", "message": str(e)}
    async def handle_websocket_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle WebSocket connections from GitHub Copilot or other clients."""
        self.active_connections.add(websocket)
        logger.info(f"New connection from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(str(message))
                    response = await self.handle_message(data)
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    error_response = {"status": "error", "message": "Invalid JSON"}
                    await websocket.send(json.dumps(error_response))
                except Exception as e:
                    error_response = {"status": "error", "message": str(e)}
                    await websocket.send(json.dumps(error_response))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {websocket.remote_address}")
        finally:
            self.active_connections.discard(websocket)
    
    async def handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages and route them to appropriate MCP servers."""
        action = data.get("action")
        
        if action == "list_servers":
            available_servers = await self.get_available_servers()
            return {
                "status": "success",
                "action": "list_servers",
                "servers": available_servers
            }
        
        elif action == "proxy_request":
            server_name = data.get("server")
            method = data.get("method", "GET")
            path = data.get("path", "/")
            request_data = data.get("data")
            
            if server_name not in self.mcp_servers:
                return {"status": "error", "message": f"Unknown server: {server_name}"}
            
            endpoint = self.mcp_servers[server_name]
            result = await self.proxy_request(server_name, endpoint, method, path, request_data)
            
            return {
                "status": result["status"],
                "action": "proxy_request",
                "server": server_name,
                "data": result.get("data"),
                "message": result.get("message")
            }
        
        elif action == "ping":
            return {"status": "success", "action": "pong", "timestamp": asyncio.get_event_loop().time()}
        
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
    
    async def start_server(self):
        """Start the MCP bridge WebSocket server."""
        logger.info(f"Starting MCP Bridge on port {self.port}")
        
        # Check initial server availability
        available_servers = await self.get_available_servers()
        logger.info(f"Found {len(available_servers)} available MCP servers")
        
        # Start WebSocket server
        async with serve(self.handle_websocket_connection, "localhost", self.port):
            logger.info(f"MCP Bridge running on ws://localhost:{self.port}")
            logger.info("Available endpoints:")
            logger.info("  - list_servers: Get available MCP servers")
            logger.info("  - proxy_request: Proxy requests to MCP servers")
            logger.info("  - ping: Health check")
            
            # Keep the server running
            await asyncio.Future()  # Run forever

def main():
    parser = argparse.ArgumentParser(description="MCP Bridge for GitHub Copilot")
    parser.add_argument("--port", type=int, default=8888, help="Port to run the bridge server on")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    bridge = MCPBridge(port=args.port)
    
    try:
        asyncio.run(bridge.start_server())
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Bridge...")
    except Exception as e:
        logger.error(f"Error running MCP Bridge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
