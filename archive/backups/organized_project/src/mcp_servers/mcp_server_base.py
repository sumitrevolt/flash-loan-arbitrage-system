#!/usr/bin/env python3
"""
Base MCP Server Implementation
Provides common functionality for all MCP servers
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aioredis  # type: ignore
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/logs/mcp_server.log"),
        logging.StreamHandler()
    ]
)

class MCPServerBase(ABC):
    """Base class for all MCP servers"""
    
    def __init__(self, server_name: str, server_port: int):
        self.server_name = server_name
        self.server_port = server_port
        self.redis_client: Optional[aioredis.Redis] = None
        self.orchestrator_url = os.getenv('ORCHESTRATOR_URL', 'http://localhost:3000')
        
        # Metrics
        self.request_counter = Counter(f'mcp_{server_name}_requests_total', 'Total requests', ['method', 'endpoint'])
        self.request_duration = Histogram(f'mcp_{server_name}_request_duration_seconds', 'Request duration')
        self.active_connections = Gauge(f'mcp_{server_name}_active_connections', 'Active connections')
        
        # Server state
        self.is_healthy = True
        self.last_heartbeat = datetime.now()
        self.error_count = 0
        
        # FastAPI app
        self.app = FastAPI(
            title=f"MCP Server - {server_name}",
            description=f"Model Context Protocol server for {server_name}",
            version="1.0.0"
        )
        
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup common routes"""
        
        @self.app.get("/health")
        async def health_check() -> Dict[str, Any]:  # noqa
            """Health check endpoint"""
            self.request_counter.labels(method="GET", endpoint="/health").inc()
            return {
                "status": "healthy" if self.is_healthy else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "server_name": self.server_name,
                "error_count": self.error_count,
                "last_heartbeat": self.last_heartbeat.isoformat()
            }
        
        @self.app.get("/metrics")
        async def metrics() -> Response:  # noqa
            """Prometheus metrics endpoint"""
            return Response(generate_latest(), media_type="text/plain")
        
        @self.app.get("/status")
        async def get_status() -> Dict[str, Any]:  # noqa
            """Get detailed server status"""
            self.request_counter.labels(method="GET", endpoint="/status").inc()
            return {
                "server_name": self.server_name,
                "server_type": self.get_server_type(),
                "capabilities": self.get_capabilities(),
                "is_healthy": self.is_healthy,
                "uptime": (datetime.now() - self.last_heartbeat).total_seconds(),
                "error_count": self.error_count
            }
        
        @self.app.post("/execute")
        async def execute_task(task_data: Dict[str, Any]) -> Dict[str, Any]:  # noqa
            """Execute a task"""
            self.request_counter.labels(method="POST", endpoint="/execute").inc()
            try:
                result = await self.execute_mcp_task(task_data)
                return {"status": "success", "result": result}
            except Exception as e:
                self.error_count += 1
                logging.error(f"Task execution failed: {e}")
                await self.report_error_to_orchestrator(e, "execute_task")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def initialize(self):
        """Initialize the MCP server"""
        try:
            # Initialize Redis connection
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = aioredis.from_url(redis_url)  # type: ignore
            await self.redis_client.ping()
            logging.info(f"✅ {self.server_name}: Redis connection established")
            
            # Register with orchestrator
            await self.register_with_orchestrator()
            
            # Start heartbeat
            asyncio.create_task(self.heartbeat_loop())
            
            # Server-specific initialization
            await self.initialize_server()
            
            logging.info(f"🚀 {self.server_name} initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ {self.server_name} initialization failed: {e}")
            self.is_healthy = False
            raise
    
    async def register_with_orchestrator(self):
        """Register this server with the orchestrator"""
        try:
            registration_data: Dict[str, Any] = {
                "name": self.server_name,
                "service_type": "mcp_server",
                "capabilities": self.get_capabilities(),
                "endpoint": f"http://{self.server_name}:{self.server_port}",
                "server_type": self.get_server_type()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.orchestrator_url}/register_service",
                    json=registration_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        logging.info(f"✅ {self.server_name} registered with orchestrator")
                    else:
                        logging.warning(f"⚠️ Failed to register {self.server_name}: {response.status}")
                        
        except Exception as e:
            logging.error(f"Failed to register with orchestrator: {e}")
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats to orchestrator"""
        while True:
            try:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                heartbeat_data: Dict[str, Any] = {
                    "service_name": self.server_name,
                    "timestamp": datetime.now().isoformat(),
                    "load": self.get_load_metric(),
                    "health_score": 1.0 if self.is_healthy else 0.0,
                    "error_count": self.error_count
                }
                
                # Update local state
                self.last_heartbeat = datetime.now()
                
                # Send to orchestrator
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.orchestrator_url}/heartbeat",
                        json=heartbeat_data,
                        timeout=5
                    ) as response:
                        if response.status != 200:
                            logging.warning(f"Heartbeat failed: {response.status}")
                
                # Store in Redis
                if self.redis_client:
                    await self.redis_client.setex(
                        f"heartbeat:{self.server_name}",
                        60,  # Expire in 60 seconds
                        json.dumps(heartbeat_data)
                    )
                
            except Exception as e:
                logging.error(f"Heartbeat error: {e}")
                self.error_count += 1
    
    async def report_error_to_orchestrator(self, error: Exception, context: str):
        """Report error to orchestrator for automatic handling"""
        try:
            error_data: Dict[str, Any] = {
                "service_name": self.server_name,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "server_type": self.get_server_type()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.orchestrator_url}/report_error",
                    json=error_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        logging.info(f"📤 Error reported to orchestrator")
                    else:
                        logging.warning(f"Failed to report error: {response.status}")
                        
        except Exception as report_error:
            logging.error(f"Failed to report error to orchestrator: {report_error}")
    
    def get_load_metric(self) -> float:
        """Get current load metric (0.0 to 1.0)"""
        # Basic implementation - can be overridden by specific servers
        return min(self.error_count / 100.0, 1.0)
    
    @abstractmethod
    async def initialize_server(self):
        """Initialize server-specific components"""
        pass
    
    @abstractmethod
    async def execute_mcp_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP-specific task"""
        pass
    
    @abstractmethod
    def get_server_type(self) -> str:
        """Get the server type identifier"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of server capabilities"""
        pass
    
    async def run(self):
        """Run the MCP server"""
        import uvicorn
        
        # Initialize first
        await self.initialize()
        
        # Run the server
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.server_port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()

# Pydantic models for common use
class MCPRequest(BaseModel):
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 1

class MCPResponse(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
