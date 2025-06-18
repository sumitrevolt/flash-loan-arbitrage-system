#!/usr/bin/env python3
"""
Clean Context7 MCP Server
Simplified Context7 MCP server for documentation lookup with coordinator integration
"""

import asyncio
import json
import sys
import logging
import os
import time
import requests
from typing import Any, Dict, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(os.path.join("logs", "context7_mcp_server.log"))
    ]
)
logger = logging.getLogger("context7-mcp-server")

class CleanContext7MCPServer:
    """Clean Context7 MCP Server with coordinator integration"""
    
    def __init__(self):
        self.name: str = "context7-mcp-server"
        self.server_type: str = "ai_integration"
        self.version: str = "1.0.0"
        self.tools: List[Dict[str, Any]] = []
        self.active_requests: Dict[str, Any] = {}
        self.request_history: List[Any] = []
        self.coordinator_url: str = os.getenv("MCP_COORDINATOR_URL", "http://localhost:9000")
        self.status: str = "operational"
        self.start_time: float = 0.0  # Will be set in run() method
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup available tools"""
        self.tools = [
            {
                "name": "search_docs",
                "description": "Search documentation for a library or framework",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "library": {
                            "type": "string",
                            "description": "Library or framework name to search"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query for documentation"
                        }
                    },
                    "required": ["library", "query"]
                }
            },
            {
                "name": "get_library_info",
                "description": "Get information about a library or framework",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "library": {
                            "type": "string",
                            "description": "Library or framework name"
                        }
                    },
                    "required": ["library"]
                }
            },
            {
                "name": "health_check",
                "description": "Check server health",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "register_with_coordinator",
                "description": "Register this server with the MCP coordinator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "coordinator_url": {"type": "string", "description": "URL of the coordinator"},
                        "capabilities": {"type": "array", "items": {"type": "string"}, "description": "Server capabilities"}
                    }
                }
            }
        ]
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages"""
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
        """Handle tool calls"""
        if name == "search_docs":
            library = args.get("library", "")
            query = args.get("query", "")
            return json.dumps({
                "library": library,
                "query": query,
                "results": [
                    {
                        "title": f"{library} Documentation",
                        "content": f"Documentation for {query} in {library}",
                        "url": f"https://docs.{library.lower()}.com/",
                        "note": "This is a mock response - implement actual search"
                    }
                ]
            }, indent=2)
        
        elif name == "get_library_info":
            library = args.get("library", "")
            return json.dumps({
                "library": library,
                "description": f"Information about {library}",
                "version": "latest",
                "documentation_url": f"https://docs.{library.lower()}.com/",
                "note": "This is a mock response - implement actual library lookup"
            }, indent=2)
        
        elif name == "health_check":
            return await self._health_check(args)
        
        elif name == "register_with_coordinator":
            return await self._register_with_coordinator(args)
        
        return json.dumps({            "error": f"Unknown tool: {name}",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _health_check(self, args: Dict[str, Any]) -> str:
        """Check the health of the server"""
        health_data: Dict[str, Any] = {
            "status": self.status,
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "name": self.name,
                "type": self.server_type,
                "version": self.version
            },
            "active_requests": len(self.active_requests),
            "request_history": len(self.request_history),
            "capabilities": ["doc_search", "library_info"]
        }
        
        return json.dumps(health_data, indent=2)
    
    def _get_default_capabilities(self) -> List[str]:
        """Get default capabilities for this server type"""
        return [
            "doc_search",
            "library_info",
            "documentation_assistance"
        ]
    
    async def _register_with_coordinator(self, args: Dict[str, Any]) -> str:
        """Register this server with the MCP coordinator"""
        coordinator_url = args.get("coordinator_url") or self.coordinator_url
        capabilities = args.get("capabilities", [])
        
        if not capabilities:
            capabilities = self._get_default_capabilities()
        
        logger.info(f"Registering with coordinator at {coordinator_url}")
        
        try:
            server_port = os.getenv("MCP_PORT", "8001")
            server_url = f"http://localhost:{server_port}"
            
            response = requests.post(
                f"{coordinator_url}/register_server",
                json={
                    "server_name": self.name,
                    "server_type": self.server_type,
                    "server_url": server_url,
                    "capabilities": capabilities
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result: str = response.json()
                logger.info(f"Successfully registered with coordinator: {result}")
                return json.dumps({
                    "success": True,
                    "coordinator_url": coordinator_url,
                    "registration_result": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.warning(f"Failed to register with coordinator: {response.status_code} - {response.text}")
                return json.dumps({
                    "success": False,
                    "error": f"Coordinator returned status {response.status_code}",
                    "response": response.text,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error registering with coordinator: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _heartbeat_loop(self):
        """Send regular heartbeats to the coordinator"""
        while True:
            try:
                response = requests.post(
                    f"{self.coordinator_url}/server_heartbeat",
                    json={
                        "server_name": self.name,
                        "status": self.status,
                        "stats": {
                            "active_requests": len(self.active_requests),
                            "uptime_seconds": int(time.time() - self.start_time)
                        }
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.debug(f"Heartbeat sent successfully")
                else:
                    logger.warning(f"Failed to send heartbeat: {response.status_code}")
                    
                    # If we got a 404, try to re-register
                    if response.status_code == 404:
                        logger.info("Server not registered, attempting to re-register")
                        await self._register_with_coordinator({})
                
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
            
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
    
    async def run(self):
        """Run the MCP server"""
        self.start_time = time.time()
        logger.info(f"Starting {self.name} v{self.version} (stdio mode)")
        
        # Register with coordinator
        await self._register_with_coordinator({})
        
        # Start the heartbeat loop
        asyncio.create_task(self._heartbeat_loop())
        
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
                    error_response: Dict[str, Any] = {
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

def main():
    """Main entry point"""
    server = CleanContext7MCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Clean Context7 MCP Server shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
