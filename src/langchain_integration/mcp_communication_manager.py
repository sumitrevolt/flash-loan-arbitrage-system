# -*- coding: utf-8 -*-
"""
MCP Communication Manager for Flash Loan Arbitrage System

This module handles all communication with MCP servers, including
load balancing, failover, and protocol adaptation.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import time

from dataclasses import dataclass, field
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class MCPProtocol(Enum):
    """MCP communication protocols"""
    HTTP = "http"
    WEBSOCKET = "websocket"
    STDIO = "stdio"
    SSE = "sse"


class ServerTier(Enum):
    """Server tier classification"""
    CRITICAL = "critical"
    INTEGRATION = "integration"
    SPECIALIZED = "specialized"


@dataclass
class MCPServerInfo:
    """Information about an MCP server"""
    name: str
    host: str
    port: int
    protocol: MCPProtocol
    tier: ServerTier
    capabilities: List[str] = field(default_factory=list)
    health_status: str = "unknown"
    last_health_check: Optional[float] = None
    response_times: List[float] = field(default_factory=list)
    failure_count: int = 0
    max_connections: int = 100
    active_connections: int = 0


@dataclass
class MCPRequest:
    """MCP request structure"""
    request_id: str
    target_server: str
    method: str
    parameters: Dict[str, Any]
    timeout: int = 30
    priority: str = "medium"
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class MCPResponse:
    """MCP response structure"""
    request_id: str
    server_name: str
    status: str
    data: Dict[str, Any]
    response_time: float
    error: Optional[str] = None


class MCPCommunicationManager:
    """
    Manages communication with all MCP servers including load balancing,
    failover, and protocol adaptation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.servers: Dict[str, MCPServerInfo] = {}
        self.active_requests: Dict[str, MCPRequest] = {}
        
        # HTTP session for persistent connections
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Circuit breaker state
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Health monitoring
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "server_health_scores": {}

        
        logger.info("[INIT] MCP Communication Manager initialized")
    
    async def initialize(self):
        """Initialize the communication manager"""
        try:
            # Create HTTP session
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                keepalive_timeout=30

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=60)

            
            # Load server configuration
            await self._load_server_configuration()
            
            # Start health monitoring
            self.health_check_task = asyncio.create_task(self._health_monitor_loop())
            
            logger.info(f"[OK] MCP Communication Manager initialized with {len(self.servers)} servers")
            
        except Exception as e:
            logger.error(f"[ERROR] MCP Communication Manager initialization failed: {e}")
            raise
    
    async def _load_server_configuration(self):
        """Load server configuration from config"""
        try:
            server_config = self.config.get("mcp_servers", {})
            
            # Load critical servers (Tier 1)
            critical_servers = server_config.get("critical", {})
            for server_name, server_info in critical_servers.items():
                self.servers[server_name] = MCPServerInfo(
                    name=server_name,
                    host=server_info.get("host", "localhost"),
                    port=server_info.get("port", 3000),
                    protocol=MCPProtocol(server_info.get("protocol", "http")),
                    tier=ServerTier.CRITICAL,
                    capabilities=server_info.get("capabilities", []),
                    max_connections=server_info.get("max_connections", 100)

            
            # Load integration servers (Tier 2)
            integration_servers = server_config.get("integration", {})
            for server_name, server_info in integration_servers.items():
                self.servers[server_name] = MCPServerInfo(
                    name=server_name,
                    host=server_info.get("host", "localhost"),
                    port=server_info.get("port", 3000),
                    protocol=MCPProtocol(server_info.get("protocol", "http")),
                    tier=ServerTier.INTEGRATION,
                    capabilities=server_info.get("capabilities", []),
                    max_connections=server_info.get("max_connections", 50)

            
            # Load specialized servers (Tier 3)
            specialized_servers = server_config.get("specialized", {})
            for server_name, server_info in specialized_servers.items():
                self.servers[server_name] = MCPServerInfo(
                    name=server_name,
                    host=server_info.get("host", "localhost"),
                    port=server_info.get("port", 3000),
                    protocol=MCPProtocol(server_info.get("protocol", "http")),
                    tier=ServerTier.SPECIALIZED,
                    capabilities=server_info.get("capabilities", []),
                    max_connections=server_info.get("max_connections", 25)

            
            # Initialize circuit breakers
            for server_name in self.servers:
                self.circuit_breakers[server_name] = {
                    "state": "closed",  # closed, open, half-open
                    "failure_count": 0,
                    "failure_threshold": 5,
                    "recovery_timeout": 60,
                    "last_failure_time": 0

            
            logger.info(f"[OK] Loaded {len(self.servers)} MCP servers")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load server configuration: {e}")
            raise
    
    async def execute_coordinated_request(
        self,
        target_services: List[str],
        request: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a coordinated request across multiple MCP servers
        
        Args:
            target_services: List of target service names
            request: Request data
            timeout: Request timeout in seconds
            
        Returns:
            Aggregated response from all services
        """
        request_id = f"coord_{int(time.time() * 1000)}"
        
        try:
            logger.info(f"[REQUEST] Coordinated request {request_id} to {target_services}")
            
            # Create individual requests for each service
            tasks = []
            for service_name in target_services:
                if service_name in self.servers:
                    mcp_request = MCPRequest(
                        request_id=f"{request_id}_{service_name}",
                        target_server=service_name,
                        method=request.get("type", "execute"),
                        parameters=request,
                        timeout=timeout

                    tasks.append(self._execute_single_request(mcp_request))
                else:
                    logger.warning(f"[WARNING] Unknown service: {service_name}")
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results
            aggregated_result = {
                "request_id": request_id,
                "services_contacted": target_services,
                "responses": {},
                "successful_services": [],
                "failed_services": [],
                "aggregated_data": {}

            
            for i, response in enumerate(responses):
                service_name = target_services[i] if i < len(target_services) else f"unknown_{i}"
                
                if isinstance(response, Exception):
                    aggregated_result["failed_services"].append(service_name)
                    aggregated_result["responses"][service_name] = {
                        "status": "error",
                        "error": str(response)

                elif isinstance(response, MCPResponse):
                    if response.status == "success":
                        aggregated_result["successful_services"].append(service_name)
                        aggregated_result["responses"][service_name] = response.data
                        
                        # Merge data into aggregated result
                        self._merge_response_data(aggregated_result["aggregated_data"], response.data)
                    else:
                        aggregated_result["failed_services"].append(service_name)
                        aggregated_result["responses"][service_name] = {
                            "status": "error",
                            "error": response.error

            
            # Update metrics
            self.metrics["total_requests"] += 1
            if aggregated_result["successful_services"]:
                self.metrics["successful_requests"] += 1
            else:
                self.metrics["failed_requests"] += 1
            
            logger.info(f"[OK] Coordinated request {request_id} completed")
            return aggregated_result["aggregated_data"]
            
        except Exception as e:
            logger.error(f"[ERROR] Coordinated request {request_id} failed: {e}")
            self.metrics["total_requests"] += 1
            self.metrics["failed_requests"] += 1
            raise
    
    async def _execute_single_request(self, request: MCPRequest) -> MCPResponse:
        """Execute a single MCP request"""
        start_time = time.time()
        
        try:
            # Check circuit breaker
            if not self._is_circuit_breaker_closed(request.target_server):
                raise Exception(f"Circuit breaker open for {request.target_server}")
            
            # Get server info
            server = self.servers.get(request.target_server)
            if not server:
                raise Exception(f"Server {request.target_server} not found")
            
            # Check server health
            if server.health_status == "unhealthy":
                raise Exception(f"Server {request.target_server} is unhealthy")
            
            # Execute request based on protocol
            if server.protocol == MCPProtocol.HTTP:
                response_data = await self._execute_http_request(server, request)
            elif server.protocol == MCPProtocol.WEBSOCKET:
                response_data = await self._execute_websocket_request(server, request)
            else:
                raise Exception(f"Unsupported protocol: {server.protocol}")
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Update server metrics
            server.response_times.append(response_time)
            if len(server.response_times) > 100:
                server.response_times.pop(0)
            
            # Reset circuit breaker on success
            self._reset_circuit_breaker(request.target_server)
            
            return MCPResponse(
                request_id=request.request_id,
                server_name=request.target_server,
                status="success",
                data=response_data,
                response_time=response_time

            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Update circuit breaker on failure
            self._record_circuit_breaker_failure(request.target_server)
            
            logger.error(f"[ERROR] Request {request.request_id} to {request.target_server} failed: {e}")
            
            return MCPResponse(
                request_id=request.request_id,
                server_name=request.target_server,
                status="error",
                data={},
                response_time=response_time,
                error=str(e)

    
    async def _execute_http_request(self, server: MCPServerInfo, request: MCPRequest) -> Dict[str, Any]:
        """Execute HTTP request to MCP server"""
        if not self.session:
            raise Exception("HTTP session not initialized")
        
        url = f"http://{server.host}:{server.port}/mcp/{request.method}"
        
        try:
            async with self.session.post(
                url,
                json=request.parameters,
                timeout=aiohttp.ClientTimeout(total=request.timeout)
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise Exception(f"HTTP request failed: {e}")
    
    async def _execute_websocket_request(self, server: MCPServerInfo, request: MCPRequest) -> Dict[str, Any]:
        """Execute WebSocket request to MCP server"""
        # TODO: Implement WebSocket communication
        raise Exception("WebSocket protocol not yet implemented")
    
    def _merge_response_data(self, aggregated: Dict[str, Any], response_data: Dict[str, Any]):
        """Merge response data into aggregated result"""
        for key, value in response_data.items():
            if key in aggregated:
                # Handle merging of different data types
                if isinstance(aggregated[key], list) and isinstance(value, list):
                    aggregated[key].extend(value)
                elif isinstance(aggregated[key], dict) and isinstance(value, dict):
                    aggregated[key].update(value)
                elif isinstance(aggregated[key], (int, float)) and isinstance(value, (int, float)):
                    aggregated[key] = max(aggregated[key], value)  # Take maximum
                else:
                    # For other types, create a list
                    if not isinstance(aggregated[key], list):
                        aggregated[key] = [aggregated[key]]
                    aggregated[key].append(value)
            else:
                aggregated[key] = value
    
    def _is_circuit_breaker_closed(self, server_name: str) -> bool:
        """Check if circuit breaker is closed (allowing requests)"""
        breaker = self.circuit_breakers.get(server_name)
        if not breaker:
            return True
        
        if breaker["state"] == "closed":
            return True
        elif breaker["state"] == "open":
            # Check if recovery timeout has passed
            if time.time() - breaker["last_failure_time"] > breaker["recovery_timeout"]:
                breaker["state"] = "half-open"
                return True
            return False
        elif breaker["state"] == "half-open":
            return True
        
        return False
    
    def _record_circuit_breaker_failure(self, server_name: str):
        """Record a failure in the circuit breaker"""
        breaker = self.circuit_breakers.get(server_name)
        if not breaker:
            return
        
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = time.time()
        
        if breaker["failure_count"] >= breaker["failure_threshold"]:
            breaker["state"] = "open"
            logger.warning(f"[CIRCUIT_BREAKER] Opened for {server_name}")
    
    def _reset_circuit_breaker(self, server_name: str):
        """Reset circuit breaker on successful request"""
        breaker = self.circuit_breakers.get(server_name)
        if not breaker:
            return
        
        breaker["failure_count"] = 0
        breaker["state"] = "closed"
    
    async def _health_monitor_loop(self):
        """Health monitoring loop"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Health monitoring failed: {e}")
                await asyncio.sleep(30)
    
    async def _perform_health_checks(self):
        """Perform health checks on all servers"""
        health_check_tasks = []
        
        for server_name, server in self.servers.items():
            task = asyncio.create_task(self._check_server_health(server))
            health_check_tasks.append(task)
        
        await asyncio.gather(*health_check_tasks, return_exceptions=True)
    
    async def _check_server_health(self, server: MCPServerInfo):
        """Check health of a single server"""
        try:
            if server.protocol == MCPProtocol.HTTP:
                url = f"http://{server.host}:{server.port}/health"
                
                if self.session:
                    async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            server.health_status = "healthy"
                        else:
                            server.health_status = "unhealthy"
                else:
                    server.health_status = "unknown"
            else:
                # For non-HTTP protocols, assume healthy if circuit breaker is closed
                if self._is_circuit_breaker_closed(server.name):
                    server.health_status = "healthy"
                else:
                    server.health_status = "unhealthy"
            
            server.last_health_check = time.time()
            
        except Exception as e:
            server.health_status = "unhealthy"
            server.last_health_check = time.time()
            logger.debug(f"[HEALTH] {server.name} health check failed: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all servers"""
        server_status = {}
        
        for server_name, server in self.servers.items():
            avg_response_time = (
                sum(server.response_times) / len(server.response_times)
                if server.response_times else 0

            
            server_status[server_name] = {
                "health": server.health_status,
                "tier": server.tier.value,
                "protocol": server.protocol.value,
                "active_connections": server.active_connections,
                "max_connections": server.max_connections,
                "avg_response_time": avg_response_time,
                "failure_count": server.failure_count,
                "circuit_breaker": self.circuit_breakers.get(server_name, {}).get("state"),
                "last_health_check": server.last_health_check

        
        return {
            "overall_status": "healthy" if all(
                s["health"] == "healthy" for s in server_status.values()
            ) else "degraded",
            "total_servers": len(self.servers),
            "healthy_servers": sum(1 for s in server_status.values() if s["health"] == "healthy"),
            "servers": server_status,
            "metrics": self.metrics

    
    async def get_server_by_capability(self, capability: str) -> List[str]:
        """Get servers that have a specific capability"""
        matching_servers = []
        
        for server_name, server in self.servers.items():
            if capability in server.capabilities and server.health_status == "healthy":
                matching_servers.append(server_name)
        
        return matching_servers
    
    async def get_servers_by_tier(self, tier: ServerTier) -> List[str]:
        """Get servers by tier"""
        return [
            server_name for server_name, server in self.servers.items()
            if server.tier == tier and server.health_status == "healthy"

    
    async def shutdown(self):
        """Shutdown the communication manager"""
        logger.info("[SHUTDOWN] Shutting down MCP Communication Manager...")
        
        # Cancel health monitoring
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        logger.info("[SHUTDOWN] MCP Communication Manager shutdown complete")