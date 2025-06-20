#!/usr/bin/env python3
"""
Productivity WebSocket Server for IDE Integration
================================================

This server provides real-time productivity features to IDEs
through WebSocket connections.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Set
import websockets
from websockets.server import WebSocketServer
from websockets.legacy.server import WebSocketServerProtocol

from enhanced_langchain_orchestrator import (
    EnhancedLangChainOrchestrator,
    IntelligentCodeAnalyzer,
    AutoCompletionEngine
)

logger = logging.getLogger(__name__)

class ProductivityWebSocketServer:
    """WebSocket server for productivity features"""
    
    def __init__(self, host: str = "localhost", port: int = 8888):
        self.host = host
        self.port = port
        self.orchestrator = None
        self.analyzer = IntelligentCodeAnalyzer()
        self.completion_engine = AutoCompletionEngine()
        self.clients: Set[WebSocketServerProtocol] = set()
        self.client_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def start(self):
        """Start the WebSocket server"""
        logger.info(f"🚀 Starting Productivity WebSocket Server on {self.host}:{self.port}")
        
        # Initialize orchestrator
        self.orchestrator = EnhancedLangChainOrchestrator()
        await self.orchestrator.initialize()
        
        # Start WebSocket server
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"✅ Server listening on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"👤 New client connected: {client_id}")
        
        # Set timeout and message size limits
        websocket.timeout = 30.0  # 30 second timeout
        websocket.max_size = 2 * 1024 * 1024  # 2MB max message size
        
        # Register client
        self.clients.add(websocket)
        self.client_sessions[client_id] = {
            "connected_at": datetime.now(),
            "requests": 0
        }
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Flash Loan Productivity Server",
                "features": ["completion", "analysis", "metrics"],
                "version": "1.0.0"
            }))
            
            # Handle messages
            async for message in websocket:
                await self.handle_message(websocket, message, client_id)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"👤 Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"❌ Error handling client {client_id}: {e}")
        finally:
            # Cleanup
            self.clients.discard(websocket)
            if client_id in self.client_sessions:
                del self.client_sessions[client_id]
    
    async def handle_message(self, websocket: WebSocketServerProtocol, 
                           message: str, client_id: str):
        """Handle incoming messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            msg_id = data.get("id", "unknown")
            
            # Track request
            self.client_sessions[client_id]["requests"] += 1
            
            if msg_type == "completion":
                await self.handle_completion_request(websocket, data, msg_id)
            
            elif msg_type == "analysis":
                await self.handle_analysis_request(websocket, data, msg_id)
            
            elif msg_type == "metrics":
                await self.handle_metrics_request(websocket, data, msg_id)
            
            elif msg_type == "ping":
                await websocket.send(json.dumps({
                    "type": "pong",
                    "id": msg_id,
                    "timestamp": datetime.now().isoformat()
                }))
            
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "id": msg_id,
                    "error": f"Unknown message type: {msg_type}"
                }))
        
        except json.JSONDecodeError as e:
            await websocket.send(json.dumps({
                "type": "error",
                "error": f"Invalid JSON: {e}"
            }))
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "error": str(e)
            }))
    
    async def handle_completion_request(self, websocket: WebSocketServerProtocol,
                                      data: Dict, msg_id: str):
        """Handle code completion request"""
        code = data.get("code", "")
        line = data.get("line", 1)
        column = data.get("column", 0)
        file_type = data.get("fileType", "python")
        
        # Get completions
        completions = await self.completion_engine.get_completions(
            code, (line, column), file_type
        )
        
        # Send response
        await websocket.send(json.dumps({
            "type": "completion_response",
            "id": msg_id,
            "completions": completions[:10],  # Limit to 10
            "timestamp": datetime.now().isoformat()
        }))
    
    async def handle_analysis_request(self, websocket: WebSocketServerProtocol,
                                    data: Dict, msg_id: str):
        """Handle code analysis request"""
        file_path = data.get("filePath")
        code = data.get("code")
        
        if file_path:
            # Analyze file
            result = await self.analyzer.analyze_code_continuously(file_path)
        elif code:
            # Analyze code snippet
            # Create temporary file for analysis
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            result = await self.analyzer.analyze_code_continuously(temp_path)
            
            # Cleanup
            import os
            os.unlink(temp_path)
        else:
            await websocket.send(json.dumps({
                "type": "error",
                "id": msg_id,
                "error": "No file path or code provided"
            }))
            return
        
        # Send response
        await websocket.send(json.dumps({
            "type": "analysis_response",
            "id": msg_id,
            "issues": result.issues,
            "suggestions": result.suggestions,
            "complexity": result.complexity_score,
            "maintainability": result.maintainability_index,
            "timestamp": datetime.now().isoformat()
        }))
    
    async def handle_metrics_request(self, websocket: WebSocketServerProtocol,
                                   data: Dict, msg_id: str):
        """Handle metrics request"""
        if self.orchestrator:
            metrics = await self.orchestrator.get_productivity_metrics()
        else:
            metrics = {}
        
        # Add server metrics
        metrics["server"] = {
            "connected_clients": len(self.clients),
            "total_sessions": len(self.client_sessions),
            "uptime": (datetime.now() - self.client_sessions.get(
                list(self.client_sessions.keys())[0], {}
            ).get("connected_at", datetime.now())).total_seconds()
        }
        
        # Send response
        await websocket.send(json.dumps({
            "type": "metrics_response",
            "id": msg_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }))
    
    async def broadcast_update(self, update_type: str, data: Dict):
        """Broadcast update to all connected clients"""
        if self.clients:
            message = json.dumps({
                "type": f"update_{update_type}",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send to all clients
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )

def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = ProductivityWebSocketServer()
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")

if __name__ == "__main__":
    main()
