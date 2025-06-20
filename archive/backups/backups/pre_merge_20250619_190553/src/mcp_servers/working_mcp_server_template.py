#!/usr/bin/env python3
"""
Working MCP Server Template
A minimal MCP server implementation that follows the Model Context Protocol
"""

import asyncio
import json
import sys
from typing import Any, Dict

class MCPServer:
    """Minimal MCP Server implementation"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: list[Dict[str, Any]] = []
        
    def add_tool(self, name: str, description: str, parameters: Dict[str, Any]):
        """Add a tool to the server"""
        self.tools.append({
            "name": name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": parameters,
                "required": list(parameters.keys())
            }
        })
    
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
            
            # Handle tool calls
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
        """Override this method to handle tool calls"""
        if name == "health":
            return json.dumps({
                "status": "healthy",
                "server": self.name,
                "version": self.version            }, indent=2)
        
        return f"Tool '{name}' called with args: {json.dumps(args, indent=2)}"
    
    async def run(self):
        """Run the MCP server using stdio transport"""
        # Add default health check tool
        self.add_tool(
            "health",
            "Check server health status",
            {}
        )
        
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
                    # Send error response
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
                # Log error to stderr (won't interfere with MCP protocol)
                print(f"Server error: {str(e)}", file=sys.stderr)
                break

def main():
    """Main entry point"""
    server = MCPServer("working-mcp-server", "1.0.0")
    
    # Add some example tools
    server.add_tool(
        "echo",
        "Echo back the input message",
        {
            "message": {
                "type": "string",
                "description": "Message to echo back"
            }
        }
    )
    
    # Run the server
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Server shutting down...", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
