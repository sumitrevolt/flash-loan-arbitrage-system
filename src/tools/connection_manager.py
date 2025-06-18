"""
Connection Manager for Foundry MCP Server

Handles MCP transport connections, session management, and communication
with clients using stdio, websocket, or other transport protocols.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, List
from pathlib import Path

from ..utils.async_utils import AsyncLock, safe_cancel_task


class ConnectionManager:
    """
    Manages MCP server connections and transport protocols.
    
    Supports stdio, websocket, and other transport mechanisms
    for communicating with MCP clients.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize connection manager.
        
        Args:
            config: Server configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Connection state
        self._connections: Dict[str, Any] = {}
        self._connection_lock = AsyncLock()
        self._message_handlers: Dict[str, Callable] = {}
        self._running = False
        
        # Transport configuration
        self.transport_type = config.get("server", {}).get("transport", {}).get("type", "stdio")
        self.host = config.get("server", {}).get("host", "localhost")
        self.port = config.get("server", {}).get("port", 8080)
        
        # Message queues and tasks
        self._message_tasks: List[asyncio.Task] = []
        
    async def initialize(self) -> bool:
        """
        Initialize the connection manager.
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info(f"Initializing connection manager with transport: {self.transport_type}")
            
            # Setup message handlers
            self._setup_message_handlers()
            
            # Initialize transport-specific components
            if self.transport_type == "stdio":
                await self._initialize_stdio()
            elif self.transport_type == "websocket":
                await self._initialize_websocket()
            else:
                self.logger.warning(f"Unknown transport type: {self.transport_type}")
                return False
            
            self.logger.info("Connection manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize connection manager: {e}", exc_info=True)
            return False
    
    def _setup_message_handlers(self) -> None:
        """Setup default message handlers."""
        self._message_handlers = {
            "initialize": self._handle_initialize,
            "list_tools": self._handle_list_tools,
            "call_tool": self._handle_call_tool,
            "ping": self._handle_ping,
            "shutdown": self._handle_shutdown,
        }
    
    async def _initialize_stdio(self) -> None:
        """Initialize stdio transport."""
        self.logger.debug("Initializing stdio transport")
        # Stdio transport is handled by the MCP server directly
        pass
    
    async def _initialize_websocket(self) -> None:
        """Initialize websocket transport."""
        self.logger.debug(f"Initializing websocket transport on {self.host}:{self.port}")
        # WebSocket initialization would go here
        # This is a placeholder for future WebSocket support
        pass
    
    async def register_connection(self, connection_id: str, connection: Any) -> bool:
        """
        Register a new connection.
        
        Args:
            connection_id: Unique connection identifier
            connection: Connection object
            
        Returns:
            True if registration successful
        """
        try:
            async with self._connection_lock:
                if connection_id in self._connections:
                    self.logger.warning(f"Connection {connection_id} already registered")
                    return False
                
                self._connections[connection_id] = {
                    "connection": connection,
                    "created_at": asyncio.get_event_loop().time(),
                    "last_activity": asyncio.get_event_loop().time(),
                    "message_count": 0
                }
                
                self.logger.info(f"Registered connection: {connection_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error registering connection {connection_id}: {e}")
            return False
    
    async def unregister_connection(self, connection_id: str) -> bool:
        """
        Unregister a connection.
        
        Args:
            connection_id: Connection identifier to remove
            
        Returns:
            True if unregistration successful
        """
        try:
            async with self._connection_lock:
                if connection_id not in self._connections:
                    self.logger.warning(f"Connection {connection_id} not found")
                    return False
                
                connection_info = self._connections.pop(connection_id)
                
                # Close connection if needed
                connection = connection_info.get("connection")
                if hasattr(connection, "close"):
                    try:
                        await connection.close()
                    except Exception as e:
                        self.logger.warning(f"Error closing connection {connection_id}: {e}")
                
                self.logger.info(f"Unregistered connection: {connection_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error unregistering connection {connection_id}: {e}")
            return False
    
    async def send_message(
        self, 
        connection_id: str, 
        message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: Target connection identifier
            message: Message to send
            
        Returns:
            True if message sent successfully
        """
        try:
            async with self._connection_lock:
                if connection_id not in self._connections:
                    self.logger.error(f"Connection {connection_id} not found")
                    return False
                
                connection_info = self._connections[connection_id]
                connection = connection_info["connection"]
                
                # Update activity timestamp
                connection_info["last_activity"] = asyncio.get_event_loop().time()
                connection_info["message_count"] += 1
                
                # Send message (implementation depends on transport type)
                if hasattr(connection, "send"):
                    await connection.send(message)
                else:
                    # Default JSON serialization for stdio
                    import json
                    import sys
                    print(json.dumps(message), file=sys.stdout, flush=True)
                
                self.logger.debug(f"Sent message to {connection_id}: {message.get('method', 'unknown')}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error sending message to {connection_id}: {e}")
            return False
    
    async def broadcast_message(self, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all connections.
        
        Args:
            message: Message to broadcast
            
        Returns:
            Number of connections that received the message
        """
        sent_count = 0
        
        async with self._connection_lock:
            connection_ids = list(self._connections.keys())
        
        for connection_id in connection_ids:
            if await self.send_message(connection_id, message):
                sent_count += 1
        
        self.logger.debug(f"Broadcast message to {sent_count} connections")
        return sent_count
    
    async def _handle_initialize(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle client initialization request."""
        self.logger.info(f"Handling initialize request from {connection_id}")
        
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "logging": {},
                    "prompts": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": self.config["server"]["name"],
                    "version": self.config["server"]["version"]
                }
            }
        }
    
    async def _handle_list_tools(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list tools request."""
        self.logger.debug(f"Handling list_tools request from {connection_id}")
        
        # This would be handled by the tool registry
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "tools": []  # Placeholder - actual tools from registry
            }
        }
    
    async def _handle_call_tool(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution request."""
        params = message.get("params", {})
        tool_name = params.get("name")
        
        self.logger.info(f"Handling call_tool request for {tool_name} from {connection_id}")
        
        # This would be handled by the tool registry
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool {tool_name} executed successfully (placeholder)"
                    }
                ]
            }
        }
    
    async def _handle_ping(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request."""
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {"pong": True}
        }
    
    async def _handle_shutdown(self, connection_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shutdown request."""
        self.logger.info(f"Handling shutdown request from {connection_id}")
        
        # Initiate graceful shutdown
        asyncio.create_task(self._graceful_shutdown())
        
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {"shutdown": True}
        }
    
    async def _graceful_shutdown(self) -> None:
        """Perform graceful shutdown of all connections."""
        self.logger.info("Starting graceful shutdown of connection manager")
        
        # Send shutdown notifications to all connections
        shutdown_message = {
            "jsonrpc": "2.0",
            "method": "notifications/shutdown",
            "params": {}
        }
        
        await self.broadcast_message(shutdown_message)
        
        # Wait a bit for messages to be sent
        await asyncio.sleep(1.0)
        
        # Close all connections
        async with self._connection_lock:
            connection_ids = list(self._connections.keys())
        
        for connection_id in connection_ids:
            await self.unregister_connection(connection_id)
        
        self._running = False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        current_time = asyncio.get_event_loop().time()
        
        stats = {
            "total_connections": len(self._connections),
            "transport_type": self.transport_type,
            "connections": {}
        }
        
        for conn_id, conn_info in self._connections.items():
            stats["connections"][conn_id] = {
                "created_at": conn_info["created_at"],
                "last_activity": conn_info["last_activity"],
                "message_count": conn_info["message_count"],
                "idle_time": current_time - conn_info["last_activity"]
            }
        
        return stats
    
    async def cleanup_idle_connections(self, max_idle_time: float = 3600.0) -> int:
        """
        Clean up idle connections.
        
        Args:
            max_idle_time: Maximum idle time in seconds
            
        Returns:
            Number of connections cleaned up
        """
        current_time = asyncio.get_event_loop().time()
        cleaned_up = 0
        
        async with self._connection_lock:
            idle_connections = []
            
            for conn_id, conn_info in self._connections.items():
                idle_time = current_time - conn_info["last_activity"]
                if idle_time > max_idle_time:
                    idle_connections.append(conn_id)
        
        # Clean up idle connections
        for conn_id in idle_connections:
            if await self.unregister_connection(conn_id):
                cleaned_up += 1
                self.logger.info(f"Cleaned up idle connection: {conn_id}")
        
        return cleaned_up
    
    async def shutdown(self) -> None:
        """Shutdown the connection manager."""
        try:
            self.logger.info("Shutting down connection manager...")
            
            # Cancel all message tasks
            for task in self._message_tasks:
                await safe_cancel_task(task)
            
            # Perform graceful shutdown
            await self._graceful_shutdown()
            
            self.logger.info("Connection manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during connection manager shutdown: {e}", exc_info=True)