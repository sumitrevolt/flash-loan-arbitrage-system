# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional
import asyncio
import json
import logging
import os

from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import ()
import httpx
"""
Supermemory MCP Server - Universal Memory across LLMs
Based on the Supermemory API for fast and scalable memory management.
"""


    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,


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
logger = logging.getLogger("supermemory-mcp")

# Configuration
SUPERMEMORY_API_BASE = "https://api.supermemory.ai"
SUPERMEMORY_API_KEY = os.getenv("SUPERMEMORY_API_KEY", "")

class SupermemoryMCPServer:
    def __init__(self):
        self.server = Server("supermemory-mcp")
        self.http_client = httpx.AsyncClient()
            timeout=30.0,
            headers={}
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SUPERMEMORY_API_KEY}" if SUPERMEMORY_API_KEY else "",
            
        
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available Supermemory tools."""
            return ListToolsResult()
                tools=[]
                    Tool()
                        name="add_memory",
                        description="Add a new memory to Supermemory for universal access across LLMs",
                        inputSchema={}
                            "type": "object",
                            "properties": {}
                                "content": {}
                                    "type": "string",
                                    "description": "The content to store as a memory"
                                },
                                "title": {}
                                    "type": "string",
                                    "description": "Optional title for the memory"
                                },
                                "tags": {}
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional tags for the memory"
                                
                            },
                            "required": ["content"]
                        
                    ),
                    Tool()
                        name="search_memories",
                        description="Search through stored memories using semantic search",
                        inputSchema={}
                            "type": "object",
                            "properties": {}
                                "query": {}
                                    "type": "string",
                                    "description": "Search query to find relevant memories"
                                },
                                "limit": {}
                                    "type": "integer",
                                    "description": "Maximum number of results to return (default: 10)",
                                    "default": 10
                                
                            },
                            "required": ["query"]
                        
                    ),
                    Tool()
                        name="get_memory",
                        description="Retrieve a specific memory by ID",
                        inputSchema={}
                            "type": "object",
                            "properties": {}
                                "memory_id": {}
                                    "type": "string",
                                    "description": "The ID of the memory to retrieve"
                                
                            },
                            "required": ["memory_id"]
                        
                    ),
                    Tool()
                        name="list_memories",
                        description="List all stored memories with pagination",
                        inputSchema={}
                            "type": "object",
                            "properties": {}
                                "page": {}
                                    "type": "integer",
                                    "description": "Page number (default: 1)",
                                    "default": 1
                                },
                                "limit": {}
                                    "type": "integer",
                                    "description": "Number of results per page (default: 20)",
                                    "default": 20
                                
                            
                        
                    ),
                    Tool()
                        name="delete_memory",
                        description="Delete a specific memory by ID",
                        inputSchema={}
                            "type": "object",
                            "properties": {}
                                "memory_id": {}
                                    "type": "string",
                                    "description": "The ID of the memory to delete"
                                
                            },
                            "required": ["memory_id"]
                        
                    
                
            

        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls."""
            try:
                if request.params.name == "add_memory":
                    return await self._add_memory(request.params.arguments)
                elif request.params.name == "search_memories":
                    return await self._search_memories(request.params.arguments)
                elif request.params.name == "get_memory":
                    return await self._get_memory(request.params.arguments)
                elif request.params.name == "list_memories":
                    return await self._list_memories(request.params.arguments)
                elif request.params.name == "delete_memory":
                    return await self._delete_memory(request.params.arguments)
                else:
                    return CallToolResult()
                        content=[TextContent(type="text", text=f"Unknown tool: {request.params.name}")],
                        isError=True
                    
            except Exception as e:
                logger.error(str(f"Error in tool call {request.params.name}: {e}")
                return CallToolResult()
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                

    async def _add_memory(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Add a new memory."""
        content = arguments.get("content", "")
        title = arguments.get("title", "")
        tags = arguments.get("tags", [])

        if not content:
            return CallToolResult()
                content=[TextContent(type="text", text="Error: Content is required")],
                isError=True
            

        payload = {}
            "content": content,
            "title": title,
            "tags": tags
        

        if not SUPERMEMORY_API_KEY:
            # Demo mode - simulate API response
            memory_id = f"mem_{hash(content) % 10000}"
            result = {}
                "id": memory_id,
                "content": content,
                "title": title,
                "tags": tags,
                "created_at": "2024-01-01T00:00:00Z",
                "status": "Demo mode - no API key provided"
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Memory added successfully (Demo Mode):\n{json.dumps(result, indent=2, ensure_ascii=True, default=str)}")]
            

        try:
            response = await self.http_client.post(f"{SUPERMEMORY_API_BASE}/memories", json=payload)
            response.raise_for_status()
            result = response.json()
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Memory added successfully:\n{json.dumps(result, indent=2, ensure_ascii=True, default=str)}")]
            
        except httpx.HTTPError as e:
            return CallToolResult()
                content=[TextContent(type="text", text=f"Failed to add memory: {str(e)}")],
                isError=True
            

    async def _search_memories(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search memories."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)

        if not query:
            return CallToolResult()
                content=[TextContent(type="text", text="Error: Query is required")],
                isError=True
            

        if not SUPERMEMORY_API_KEY:
            # Demo mode
            results = []
                {}
                    "id": f"mem_{i}",
                    "content": f"Demo memory {i} matching '{query}'",
                    "title": f"Demo Memory {i}",
                    "relevance_score": 0.9 - (i * 0.1),
                    "created_at": "2024-01-01T00:00:00Z"
                
                for i in range(min(3, limit))
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Search results (Demo Mode):\n{json.dumps(results, indent=2, ensure_ascii=True, default=str)}")]
            

        try:
            params = {"q": query, "limit": limit}
            response = await self.http_client.get(f"{SUPERMEMORY_API_BASE}/memories/search", params=params)
            response.raise_for_status()
            results = response.json()
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Search results:\n{json.dumps(results, indent=2, ensure_ascii=True, default=str)}")]
            
        except httpx.HTTPError as e:
            return CallToolResult()
                content=[TextContent(type="text", text=f"Failed to search memories: {str(e)}")],
                isError=True
            

    async def _get_memory(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get a specific memory."""
        memory_id = arguments.get("memory_id", "")

        if not memory_id:
            return CallToolResult()
                content=[TextContent(type="text", text="Error: Memory ID is required")],
                isError=True
            

        if not SUPERMEMORY_API_KEY:
            # Demo mode
            result = {}
                "id": memory_id,
                "content": f"Demo memory content for {memory_id}",
                "title": f"Demo Memory {memory_id}",
                "tags": ["demo", "example"],
                "created_at": "2024-01-01T00:00:00Z",
                "status": "Demo mode - no API key provided"
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Memory retrieved (Demo Mode):\n{json.dumps(result, indent=2, ensure_ascii=True, default=str)}")]
            

        try:
            response = await self.http_client.get(f"{SUPERMEMORY_API_BASE}/memories/{memory_id}")
            response.raise_for_status()
            result = response.json()
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Memory retrieved:\n{json.dumps(result, indent=2, ensure_ascii=True, default=str)}")]
            
        except httpx.HTTPError as e:
            return CallToolResult()
                content=[TextContent(type="text", text=f"Failed to get memory: {str(e)}")],
                isError=True
            

    async def _list_memories(self, arguments: Dict[str, Any]) -> CallToolResult:
        """List memories."""
        page = arguments.get("page", 1)
        limit = arguments.get("limit", 20)

        if not SUPERMEMORY_API_KEY:
            # Demo mode
            results = {}
                "memories": []
                    {}
                        "id": f"mem_{i}",
                        "content": f"Demo memory content {i}",
                        "title": f"Demo Memory {i}",
                        "created_at": "2024-01-01T00:00:00Z"
                    
                    for i in range(1, min(6, limit + 1))
                ],
                "total": 5,
                "page": page,
                "limit": limit,
                "status": "Demo mode - no API key provided"
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Memories list (Demo Mode):\n{json.dumps(results, indent=2, ensure_ascii=True, default=str)}")]
            

        try:
            params = {"page": page, "limit": limit}
            response = await self.http_client.get(f"{SUPERMEMORY_API_BASE}/memories", params=params)
            response.raise_for_status()
            results = response.json()
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Memories list:\n{json.dumps(results, indent=2, ensure_ascii=True, default=str)}")]
            
        except httpx.HTTPError as e:
            return CallToolResult()
                content=[TextContent(type="text", text=f"Failed to list memories: {str(e)}")],
                isError=True
            

    async def _delete_memory(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Delete a memory."""
        memory_id = arguments.get("memory_id", "")

        if not memory_id:
            return CallToolResult()
                content=[TextContent(type="text", text="Error: Memory ID is required")],
                isError=True
            

        if not SUPERMEMORY_API_KEY:
            # Demo mode
            return CallToolResult()
                content=[TextContent(type="text", text=f"Memory {memory_id} deleted successfully (Demo Mode)")]
            

        try:
            response = await self.http_client.delete(f"{SUPERMEMORY_API_BASE}/memories/{memory_id}")
            response.raise_for_status()
            
            return CallToolResult()
                content=[TextContent(type="text", text=f"Memory {memory_id} deleted successfully")]
            
        except httpx.HTTPError as e:
            return CallToolResult()
                content=[TextContent(type="text", text=f"Failed to delete memory: {str(e)}")],
                isError=True
            

async def main():
    """Main entry point."""
    logger.info("Starting Supermemory MCP Server...")
    
    # Check for API key
    if not SUPERMEMORY_API_KEY:
        logger.warning("No SUPERMEMORY_API_KEY found. Running in demo mode.")
        logger.info("To use full functionality, get an API key from https://console.supermemory.ai")
    else:
        logger.info("SUPERMEMORY_API_KEY found. Running with full API access.")
    
    server_instance = SupermemoryMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run()
            read_stream,
            write_stream,
            InitializationOptions()
                server_name="supermemory-mcp",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities()
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        

if __name__ == "__main__":
    asyncio.run(main())