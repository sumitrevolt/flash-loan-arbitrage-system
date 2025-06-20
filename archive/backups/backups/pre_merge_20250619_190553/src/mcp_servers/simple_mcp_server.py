#!/usr/bin/env python3
"""
Simple Flash Loan MCP Server
Auto-generated MCP server for simple-flash-loan
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("simple-flash-loan-mcp-server")

class Simple_Flash_LoanMCPServer:
    """Auto-generated MCP Server for simple-flash-loan"""
    
    def __init__(self):
        self.name = "simple-flash-loan-mcp-server"
        self.version = "1.0.0"
        self.tools: List[Dict[str, Any]] = []
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup available tools"""
        self.tools = [
            {
                "name": "get_status",
                "description": "Get server status",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "health_check",
                "description": "Perform health check",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
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
        if name == "get_status":
            return json.dumps({
                "server": self.name,
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "capabilities": ["status", "health_check"]
            }, indent=2)
        
        elif name == "health_check":
            return json.dumps({
                "status": "healthy",
                "server": self.name,
                "version": self.version,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        
        return f"Unknown tool: {name}"
    
    async def run(self):
        """Run the MCP server"""
        logger.info(f"Starting {self.name} (stdio mode)")
        
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
    server = Simple_Flash_LoanMCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info(f"{server.name} shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
