# -*- coding: utf-8 -*-
"""
MCP Bridge for AutoGen Integration

This module provides a bridge between AutoGen agents and MCP servers,
enabling agents to access external services and data sources.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import logging
import time

from dataclasses import dataclass, field
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class MCPServiceType(Enum):
    """Types of MCP services"""
    FILESYSTEM = "filesystem"
    CONTEXT7 = "context7"
    SUPERMEMORY = "supermemory"
    TASKMANAGER = "taskmanager"
    LANGCHAIN_ORCHESTRATOR = "langchain_orchestrator"
    ENHANCED_MANAGER = "enhanced_manager"
    FLASH_LOAN_SERVICES = "flash_loan_services"
    ARBITRAGE_SERVICES = "arbitrage_services"
    RISK_MANAGEMENT = "risk_management"


class RequestPriority(Enum):
    """Request priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MCPRequest:
    """MCP service request"""
    request_id: str
    service_type: MCPServiceType
    endpoint: str
    method: str = "POST"
    data: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    priority: RequestPriority = RequestPriority.MEDIUM
    timeout: int = 30
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MCPResponse:
    """MCP service response"""
    request_id: str
    service_type: MCPServiceType
    status_code: int
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class MCPBridge:
    """
    Bridge between AutoGen agents and MCP servers, providing
    seamless integration and communication capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mcp_config = config.get("mcp_servers", {})
        
        # Service endpoints
        self.service_endpoints = self._initialize_service_endpoints()
        
        # HTTP session for MCP communication
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Request tracking
        self.active_requests: Dict[str, MCPRequest] = {}
        self.request_history: Dict[str, MCPResponse] = {}
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "service_health": {},
            "error_rates": {},
            "request_queue_size": 0

        
        # Circuit breaker for each service
        self.circuit_breakers = {}
        self._initialize_circuit_breakers()
        
        # Request queue and rate limiting
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.rate_limits = self._initialize_rate_limits()
        
        # Agent capabilities mapping
        self.agent_capabilities = self._initialize_agent_capabilities()
        
        logger.info("[INIT] MCP Bridge initialized")
    
    async def initialize(self):
        """Initialize the MCP bridge"""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                connector=aiohttp.TCPConnector(limit=100)

            
            # Test connectivity to critical MCP services
            await self._test_mcp_connectivity()
            
            # Start request processor
            asyncio.create_task(self._process_request_queue())
            
            # Start health monitoring
            asyncio.create_task(self._monitor_service_health())
            
            logger.info("[OK] MCP Bridge ready")
            
        except Exception as e:
            logger.error(f"[ERROR] MCP Bridge initialization failed: {e}")
            raise
    
    async def agent_request_market_data(
        self,
        agent_name: str,
        token_pairs: List[str],
        dex_list: Optional[List[str]] = None,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Agent request for market data
        
        Args:
            agent_name: Name of requesting agent
            token_pairs: List of token pairs to analyze
            dex_list: List of DEXs to query (optional)
            priority: Request priority
            
        Returns:
            Market data response
        """
        try:
            request = MCPRequest(
                request_id=f"market_{int(time.time() * 1000)}",
                service_type=MCPServiceType.ARBITRAGE_SERVICES,
                endpoint="/market_data",
                data={
                    "agent_name": agent_name,
                    "token_pairs": token_pairs,
                    "dex_list": dex_list or ["uniswap", "sushiswap", "curve"],
                    "include_liquidity": True,
                    "include_volume": True
                },
                priority=RequestPriority(priority),
                timeout=20

            
            response = await self._execute_mcp_request(request)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "data": response.data,
                "response_time": response.response_time,
                "timestamp": response.timestamp.isoformat()

            
        except Exception as e:
            logger.error(f"[ERROR] Market data request failed for {agent_name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "data": {}

    
    async def agent_request_risk_analysis(
        self,
        agent_name: str,
        trade_data: Dict[str, Any],
        analysis_depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Agent request for risk analysis
        
        Args:
            agent_name: Name of requesting agent
            trade_data: Trade parameters for analysis
            analysis_depth: Depth of analysis (quick, standard, comprehensive)
            
        Returns:
            Risk analysis response
        """
        try:
            request = MCPRequest(
                request_id=f"risk_{int(time.time() * 1000)}",
                service_type=MCPServiceType.RISK_MANAGEMENT,
                endpoint="/risk_analysis",
                data={
                    "agent_name": agent_name,
                    "trade_data": trade_data,
                    "analysis_depth": analysis_depth,
                    "include_scenarios": True,
                    "include_mitigations": True
                },
                priority=RequestPriority.HIGH,
                timeout=30

            
            response = await self._execute_mcp_request(request)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "risk_analysis": response.data,
                "response_time": response.response_time,
                "timestamp": response.timestamp.isoformat()

            
        except Exception as e:
            logger.error(f"[ERROR] Risk analysis request failed for {agent_name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "risk_analysis": {"risk_level": "unknown", "risk_score": 0.8}

    
    async def agent_request_gas_optimization(
        self,
        agent_name: str,
        transaction_data: Dict[str, Any],
        optimization_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Agent request for gas optimization analysis
        
        Args:
            agent_name: Name of requesting agent
            transaction_data: Transaction parameters
            optimization_level: Level of optimization (basic, standard, aggressive)
            
        Returns:
            Gas optimization response
        """
        try:
            request = MCPRequest(
                request_id=f"gas_{int(time.time() * 1000)}",
                service_type=MCPServiceType.ENHANCED_MANAGER,
                endpoint="/gas_optimization",
                data={
                    "agent_name": agent_name,
                    "transaction_data": transaction_data,
                    "optimization_level": optimization_level,
                    "include_timing": True,
                    "include_alternatives": True
                },
                priority=RequestPriority.MEDIUM,
                timeout=15

            
            response = await self._execute_mcp_request(request)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "optimization_data": response.data,
                "response_time": response.response_time,
                "timestamp": response.timestamp.isoformat()

            
        except Exception as e:
            logger.error(f"[ERROR] Gas optimization request failed for {agent_name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "optimization_data": {}

    
    async def agent_request_execution_simulation(
        self,
        agent_name: str,
        execution_plan: Dict[str, Any],
        simulation_depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Agent request for execution simulation
        
        Args:
            agent_name: Name of requesting agent
            execution_plan: Execution plan to simulate
            simulation_depth: Depth of simulation
            
        Returns:
            Simulation results
        """
        try:
            request = MCPRequest(
                request_id=f"sim_{int(time.time() * 1000)}",
                service_type=MCPServiceType.FLASH_LOAN_SERVICES,
                endpoint="/execution_simulation",
                data={
                    "agent_name": agent_name,
                    "execution_plan": execution_plan,
                    "simulation_depth": simulation_depth,
                    "include_failure_scenarios": True,
                    "include_profitability": True
                },
                priority=RequestPriority.HIGH,
                timeout=45

            
            response = await self._execute_mcp_request(request)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "simulation_results": response.data,
                "response_time": response.response_time,
                "timestamp": response.timestamp.isoformat()

            
        except Exception as e:
            logger.error(f"[ERROR] Execution simulation request failed for {agent_name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "simulation_results": {"success_probability": 0.5, "estimated_profit": 0}

    
    async def agent_store_context(
        self,
        agent_name: str,
        context_data: Dict[str, Any],
        context_type: str = "decision"
    ) -> Dict[str, Any]:
        """
        Agent request to store context data
        
        Args:
            agent_name: Name of agent storing context
            context_data: Context data to store
            context_type: Type of context (decision, analysis, execution)
            
        Returns:
            Storage response
        """
        try:
            request = MCPRequest(
                request_id=f"store_{int(time.time() * 1000)}",
                service_type=MCPServiceType.SUPERMEMORY,
                endpoint="/store_context",
                data={
                    "agent_name": agent_name,
                    "context_data": context_data,
                    "context_type": context_type,
                    "timestamp": datetime.now().isoformat(),
                    "retention_period": "24h"
                },
                priority=RequestPriority.LOW,
                timeout=10

            
            response = await self._execute_mcp_request(request)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "storage_id": response.data.get("storage_id"),
                "response_time": response.response_time

            
        except Exception as e:
            logger.error(f"[ERROR] Context storage request failed for {agent_name}: {e}")
            return {
                "status": "failed",
                "error": str(e)

    
    async def agent_retrieve_context(
        self,
        agent_name: str,
        context_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent request to retrieve context data
        
        Args:
            agent_name: Name of agent retrieving context
            context_query: Query parameters for context retrieval
            
        Returns:
            Retrieved context data
        """
        try:
            request = MCPRequest(
                request_id=f"retrieve_{int(time.time() * 1000)}",
                service_type=MCPServiceType.SUPERMEMORY,
                endpoint="/retrieve_context",
                data={
                    "agent_name": agent_name,
                    "query": context_query,
                    "max_results": 10,
                    "include_metadata": True
                },
                priority=RequestPriority.MEDIUM,
                timeout=15

            
            response = await self._execute_mcp_request(request)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "context_data": response.data.get("results", []),
                "response_time": response.response_time

            
        except Exception as e:
            logger.error(f"[ERROR] Context retrieval request failed for {agent_name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "context_data": []

    
    async def agent_request_documentation(
        self,
        agent_name: str,
        topic: str,
        library: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agent request for documentation and code examples
        
        Args:
            agent_name: Name of requesting agent
            topic: Documentation topic
            library: Specific library (optional)
            
        Returns:
            Documentation response
        """
        try:
            request = MCPRequest(
                request_id=f"docs_{int(time.time() * 1000)}",
                service_type=MCPServiceType.CONTEXT7,
                endpoint="/get_documentation",
                data={
                    "agent_name": agent_name,
                    "topic": topic,
                    "library": library,
                    "include_examples": True,
                    "max_tokens": 2000
                },
                priority=RequestPriority.LOW,
                timeout=20

            
            response = await self._execute_mcp_request(request)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "documentation": response.data,
                "response_time": response.response_time

            
        except Exception as e:
            logger.error(f"[ERROR] Documentation request failed for {agent_name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "documentation": {}

    
    async def agent_file_operations(
        self,
        agent_name: str,
        operation: str,
        file_path: str,
        data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agent request for file operations
        
        Args:
            agent_name: Name of requesting agent
            operation: Operation type (read, write, append, delete)
            file_path: Path to file
            data: Data to write (for write/append operations)
            
        Returns:
            File operation response
        """
        try:
            request = MCPRequest(
                request_id=f"file_{int(time.time() * 1000)}",
                service_type=MCPServiceType.FILESYSTEM,
                endpoint=f"/file_{operation}",
                data={
                    "agent_name": agent_name,
                    "file_path": file_path,
                    "data": data,
                    "create_dirs": True
                },
                priority=RequestPriority.MEDIUM,
                timeout=10

            
            response = await self._execute_mcp_request(request)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "file_data": response.data,
                "response_time": response.response_time

            
        except Exception as e:
            logger.error(f"[ERROR] File operation {operation} failed for {agent_name}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "file_data": {}

    
    async def _execute_mcp_request(self, request: MCPRequest) -> MCPResponse:
        """Execute MCP request with retry logic and circuit breaking"""
        start_time = time.time()
        
        try:
            # Check circuit breaker
            if self._is_circuit_breaker_open(request.service_type):
                raise Exception(f"Circuit breaker open for {request.service_type.value}")
            
            # Check rate limits
            await self._check_rate_limits(request.service_type)
            
            # Get service endpoint
            endpoint_url = self._get_service_endpoint(request.service_type, request.endpoint)
            
            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "X-Agent-Name": request.data.get("agent_name", "unknown"),
                "X-Request-ID": request.request_id,
                **request.headers

            
            # Execute HTTP request
            async with self.session.request(
                request.method,
                endpoint_url,
                json=request.data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=request.timeout)
            ) as response:
                
                response_data = {}
                try:
                    response_data = await response.json()
                except:
                    response_data = {"text": await response.text()}
                
                response_time = time.time() - start_time
                
                # Create response object
                mcp_response = MCPResponse(
                    request_id=request.request_id,
                    service_type=request.service_type,
                    status_code=response.status,
                    data=response_data,
                    response_time=response_time

                
                # Handle response
                if response.status == 200:
                    self._handle_successful_request(request.service_type, response_time)
                else:
                    mcp_response.error = f"HTTP {response.status}: {response_data.get('error', 'Unknown error')}"
                    self._handle_failed_request(request.service_type, mcp_response.error)
                
                # Store response
                self.request_history[request.request_id] = mcp_response
                
                return mcp_response
                
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            
            # Handle request failure
            self._handle_failed_request(request.service_type, error_message)
            
            # Create error response
            error_response = MCPResponse(
                request_id=request.request_id,
                service_type=request.service_type,
                status_code=500,
                error=error_message,
                response_time=response_time

            
            self.request_history[request.request_id] = error_response
            
            # Retry logic
            if request.retry_count < request.max_retries:
                request.retry_count += 1
                logger.warning(f"[RETRY] Retrying request {request.request_id} (attempt {request.retry_count})")
                await asyncio.sleep(min(2 ** request.retry_count, 10))  # Exponential backoff
                return await self._execute_mcp_request(request)
            
            return error_response
    
    def _initialize_service_endpoints(self) -> Dict[MCPServiceType, str]:
        """Initialize service endpoint mappings"""
        endpoints = {}
        
        # Critical tier services
        for tier_name, tier_services in self.mcp_config.items():
            if tier_name == "critical":
                for service_name, service_config in tier_services.items():
                    service_type = self._map_service_name_to_type(service_name)
                    if service_type:
                        base_url = f"{service_config['protocol']}://{service_config['host']}:{service_config['port']}"
                        endpoints[service_type] = base_url
            
            elif tier_name == "integration":
                for service_name, service_config in tier_services.items():
                    service_type = self._map_service_name_to_type(service_name)
                    if service_type:
                        base_url = f"{service_config['protocol']}://{service_config['host']}:{service_config['port']}"
                        endpoints[service_type] = base_url
            
            elif tier_name == "specialized":
                for service_name, service_config in tier_services.items():
                    service_type = self._map_service_name_to_type(service_name)
                    if service_type:
                        base_url = f"{service_config['protocol']}://{service_config['host']}:{service_config['port']}"
                        endpoints[service_type] = base_url
        
        return endpoints
    
    def _map_service_name_to_type(self, service_name: str) -> Optional[MCPServiceType]:
        """Map service name to MCPServiceType"""
        mapping = {
            "filesystem": MCPServiceType.FILESYSTEM,
            "context7": MCPServiceType.CONTEXT7,
            "supermemory": MCPServiceType.SUPERMEMORY,
            "taskmanager": MCPServiceType.TASKMANAGER,
            "langchain_orchestrator": MCPServiceType.LANGCHAIN_ORCHESTRATOR,
            "enhanced_manager": MCPServiceType.ENHANCED_MANAGER,
            "aave_flash_loan": MCPServiceType.FLASH_LOAN_SERVICES,
            "arbitrage_detector": MCPServiceType.ARBITRAGE_SERVICES,
            "risk_analyzer": MCPServiceType.RISK_MANAGEMENT

        
        return mapping.get(service_name)
    
    def _get_service_endpoint(self, service_type: MCPServiceType, endpoint: str) -> str:
        """Get full endpoint URL for service"""
        base_url = self.service_endpoints.get(service_type)
        if not base_url:
            raise Exception(f"No endpoint configured for service: {service_type.value}")
        
        return f"{base_url}{endpoint}"
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each service"""
        for service_type in MCPServiceType:
            self.circuit_breakers[service_type] = {
                "failure_count": 0,
                "last_failure": None,
                "is_open": False,
                "failure_threshold": 5,
                "recovery_timeout": 60

    
    def _initialize_rate_limits(self) -> Dict[MCPServiceType, Dict[str, Any]]:
        """Initialize rate limits for each service"""
        return {
            service_type: {
                "requests_per_minute": 60,
                "burst_limit": 10,
                "current_requests": 0,
                "last_reset": datetime.now()

            for service_type in MCPServiceType

    
    def _initialize_agent_capabilities(self) -> Dict[str, List[str]]:
        """Initialize agent capabilities for MCP access"""
        return {
            "arbitragecoordinator": ["market_data", "execution_simulation", "context_storage"],
            "marketanalyst": ["market_data", "documentation", "context_storage"],
            "riskanalyst": ["risk_analysis", "context_storage", "file_operations"],
            "executionspecialist": ["execution_simulation", "gas_optimization", "context_storage"],
            "gasoptimizer": ["gas_optimization", "market_data", "context_storage"],
            "compliancevalidator": ["documentation", "file_operations", "context_storage"],
            "timinganalyst": ["market_data", "context_storage"],
            "bridgespecialist": ["market_data", "documentation", "context_storage"]

    
    async def _test_mcp_connectivity(self):
        """Test connectivity to critical MCP services"""
        critical_services = [
            MCPServiceType.FILESYSTEM,
            MCPServiceType.SUPERMEMORY,
            MCPServiceType.TASKMANAGER

        
        for service_type in critical_services:
            try:
                if service_type in self.service_endpoints:
                    endpoint_url = f"{self.service_endpoints[service_type]}/health"
                    
                    async with self.session.get(endpoint_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            self.metrics["service_health"][service_type.value] = "healthy"
                            logger.info(f"[OK] {service_type.value} service is healthy")
                        else:
                            self.metrics["service_health"][service_type.value] = "unhealthy"
                            logger.warning(f"[WARNING] {service_type.value} service health check failed: {response.status}")
                else:
                    logger.warning(f"[WARNING] No endpoint configured for {service_type.value}")
                    
            except Exception as e:
                self.metrics["service_health"][service_type.value] = "unreachable"
                logger.warning(f"[WARNING] {service_type.value} service unreachable: {e}")
    
    async def _process_request_queue(self):
        """Process queued requests"""
        while True:
            try:
                # Process queue (placeholder for advanced queuing)
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Request queue processing failed: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_service_health(self):
        """Monitor service health periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._test_mcp_connectivity()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Service health monitoring failed: {e}")
                await asyncio.sleep(60)
    
    def _is_circuit_breaker_open(self, service_type: MCPServiceType) -> bool:
        """Check if circuit breaker is open for service"""
        cb = self.circuit_breakers.get(service_type, {})
        
        if not cb.get("is_open", False):
            return False
        
        # Check if recovery timeout has passed
        if cb.get("last_failure"):
            time_since_failure = (datetime.now() - cb["last_failure"]).total_seconds()
            if time_since_failure > cb.get("recovery_timeout", 60):
                cb["is_open"] = False
                cb["failure_count"] = 0
                logger.info(f"[CIRCUIT_BREAKER] {service_type.value} circuit breaker closed")
        
        return cb.get("is_open", False)
    
    async def _check_rate_limits(self, service_type: MCPServiceType):
        """Check and enforce rate limits"""
        rate_limit = self.rate_limits.get(service_type, {})
        current_time = datetime.now()
        
        # Reset counters if minute has passed
        if (current_time - rate_limit.get("last_reset", current_time)).total_seconds() >= 60:
            rate_limit["current_requests"] = 0
            rate_limit["last_reset"] = current_time
        
        # Check rate limit
        if rate_limit["current_requests"] >= rate_limit.get("requests_per_minute", 60):
            raise Exception(f"Rate limit exceeded for {service_type.value}")
        
        rate_limit["current_requests"] += 1
    
    def _handle_successful_request(self, service_type: MCPServiceType, response_time: float):
        """Handle successful request"""
        self.metrics["total_requests"] += 1
        self.metrics["successful_requests"] += 1
        
        # Update average response time
        total = self.metrics["total_requests"]
        current_avg = self.metrics["avg_response_time"]
        self.metrics["avg_response_time"] = (
            (current_avg * (total - 1) + response_time) / total

        
        # Reset circuit breaker on success
        cb = self.circuit_breakers.get(service_type, {})
        if cb.get("failure_count", 0) > 0:
            cb["failure_count"] = 0
            logger.info(f"[CIRCUIT_BREAKER] {service_type.value} failure count reset")
    
    def _handle_failed_request(self, service_type: MCPServiceType, error: str):
        """Handle failed request"""
        self.metrics["total_requests"] += 1
        self.metrics["failed_requests"] += 1
        
        # Update error rate
        service_errors = self.metrics["error_rates"].get(service_type.value, 0)
        self.metrics["error_rates"][service_type.value] = service_errors + 1
        
        # Update circuit breaker
        cb = self.circuit_breakers.get(service_type, {})
        cb["failure_count"] = cb.get("failure_count", 0) + 1
        cb["last_failure"] = datetime.now()
        
        # Open circuit breaker if threshold reached
        if cb["failure_count"] >= cb.get("failure_threshold", 5):
            cb["is_open"] = True
            logger.warning(f"[CIRCUIT_BREAKER] {service_type.value} circuit breaker opened after {cb['failure_count']} failures")
    
    async def get_agent_capabilities(self, agent_name: str) -> List[str]:
        """Get MCP capabilities for specific agent"""
        normalized_name = agent_name.lower().replace("_", "").replace(" ", "")
        return self.agent_capabilities.get(normalized_name, [])
    
    async def get_service_status(self, service_type: MCPServiceType) -> Dict[str, Any]:
        """Get status of specific MCP service"""
        cb = self.circuit_breakers.get(service_type, {})
        rate_limit = self.rate_limits.get(service_type, {})
        
        return {
            "service_type": service_type.value,
            "health": self.metrics["service_health"].get(service_type.value, "unknown"),
            "circuit_breaker_open": cb.get("is_open", False),
            "failure_count": cb.get("failure_count", 0),
            "rate_limit_remaining": rate_limit.get("requests_per_minute", 60) - rate_limit.get("current_requests", 0),
            "endpoint": self.service_endpoints.get(service_type, "not_configured")

    
    async def get_status(self) -> Dict[str, Any]:
        """Get MCP bridge status"""
        return {
            "bridge_status": "healthy",
            "services_configured": len(self.service_endpoints),
            "active_requests": len(self.active_requests),
            "request_history_size": len(self.request_history),
            "performance_metrics": self.metrics,
            "service_health": self.metrics["service_health"],
            "circuit_breakers": {
                service_type.value: cb.get("is_open", False)
                for service_type, cb in self.circuit_breakers.items()


    
    async def shutdown(self):
        """Shutdown the MCP bridge"""
        logger.info("[SHUTDOWN] Shutting down MCP Bridge...")
        
        # Complete active requests
        if self.active_requests:
            logger.info(f"[SHUTDOWN] Waiting for {len(self.active_requests)} active requests...")
            await asyncio.sleep(3)
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        # Clear state
        self.active_requests.clear()
        
        logger.info("[SHUTDOWN] MCP Bridge shutdown complete")