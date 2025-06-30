# -*- coding: utf-8 -*-
"""
Health Monitor for MCP Servers

This module provides comprehensive health monitoring, circuit breaker patterns,
and performance tracking for all registered MCP servers.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import logging
import time

from .mcp_server_registry import MCPServerInfo, ServerStatus, ServerProtocol, ServerTier
from dataclasses import dataclass, field
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class HealthCheckType(Enum):
    """Types of health checks"""
    HTTP_ENDPOINT = "http_endpoint"
    WEBSOCKET_PING = "websocket_ping"
    TCP_CONNECT = "tcp_connect"
    PROCESS_CHECK = "process_check"
    CUSTOM_SCRIPT = "custom_script"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class HealthCheckResult:
    """Result of a health check operation"""
    server_id: str
    check_type: HealthCheckType
    status: ServerStatus
    response_time: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for a server"""
    server_id: str
    is_open: bool = False
    failure_count: int = 0
    failure_threshold: int = 5
    last_failure_time: Optional[datetime] = None
    recovery_timeout: int = 60  # seconds
    half_open_max_calls: int = 3
    half_open_call_count: int = 0
    state: str = "closed"  # closed, open, half_open


@dataclass
class PerformanceMetrics:
    """Performance metrics for a server"""
    server_id: str
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    success_rate: float = 100.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class HealthAlert:
    """Health alert for server issues"""
    server_id: str
    server_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class HealthMonitor:
    """
    Comprehensive health monitoring system for all MCP servers
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_config = config.get("health_monitoring", {})
        
        # Core components
        self.server_registry = None  # Will be injected
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Health check results
        self.health_results: Dict[str, List[HealthCheckResult]] = {}
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        
        # Alerting
        self.active_alerts: Dict[str, HealthAlert] = {}
        self.alert_history: List[HealthAlert] = []
        
        # Monitoring configuration
        self.check_intervals = {
            ServerTier.CRITICAL: 10,     # Every 10 seconds
            ServerTier.INTEGRATION: 30,  # Every 30 seconds
            ServerTier.SPECIALIZED: 60   # Every 60 seconds

        
        self.health_check_timeout = self.health_config.get("timeout", 10)
        self.max_history_size = self.health_config.get("max_history", 1000)
        
        # Background tasks
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.alert_cleanup_task: Optional[asyncio.Task] = None
        self.metrics_aggregation_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self.monitoring_stats = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "circuit_breaker_trips": 0,
            "alerts_generated": 0,
            "avg_check_time": 0.0

        
        logger.info("[INIT] Health Monitor initialized")
    
    async def initialize(self, server_registry):
        """Initialize the health monitor with server registry"""
        try:
            self.server_registry = server_registry
            
            # Create HTTP session for health checks
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.health_check_timeout),
                connector=aiohttp.TCPConnector(
                    limit=50,
                    limit_per_host=10,
                    keepalive_timeout=30


            
            # Initialize circuit breakers for all servers
            await self._initialize_circuit_breakers()
            
            # Start monitoring tasks
            await self._start_monitoring_tasks()
            
            # Start background maintenance tasks
            self.alert_cleanup_task = asyncio.create_task(self._alert_cleanup_loop())
            self.metrics_aggregation_task = asyncio.create_task(self._metrics_aggregation_loop())
            
            logger.info("[OK] Health Monitor initialized and monitoring started")
            
        except Exception as e:
            logger.error(f"[ERROR] Health Monitor initialization failed: {e}")
            raise
    
    async def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for all registered servers"""
        for server_id, server_info in self.server_registry.servers.items():
            # Configure circuit breaker based on server tier
            failure_threshold = 3 if server_info.tier == ServerTier.CRITICAL else 5
            recovery_timeout = 30 if server_info.tier == ServerTier.CRITICAL else 60
            
            self.circuit_breakers[server_id] = CircuitBreakerState(
                server_id=server_id,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout

            
            # Initialize performance metrics
            self.performance_metrics[server_id] = PerformanceMetrics(server_id=server_id)
            
            # Initialize health results storage
            self.health_results[server_id] = []
        
        logger.info(f"[OK] Initialized circuit breakers for {len(self.circuit_breakers)} servers")
    
    async def _start_monitoring_tasks(self):
        """Start individual monitoring tasks for each server"""
        for server_id, server_info in self.server_registry.servers.items():
            interval = self.check_intervals.get(server_info.tier, 60)
            
            task = asyncio.create_task(
                self._monitor_server_loop(server_id, interval)

            self.monitoring_tasks[server_id] = task
        
        logger.info(f"[OK] Started {len(self.monitoring_tasks)} monitoring tasks")
    
    async def _monitor_server_loop(self, server_id: str, interval: int):
        """Main monitoring loop for a specific server"""
        while True:
            try:
                await self.check_server_health(server_id)
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Monitoring loop failed for {server_id}: {e}")
                await asyncio.sleep(interval)
    
    async def check_server_health(self, server_id: str) -> HealthCheckResult:
        """
        Perform comprehensive health check on a server
        
        Args:
            server_id: ID of the server to check
            
        Returns:
            Health check result
        """
        start_time = time.time()
        
        try:
            server_info = await self.server_registry.get_server_by_id(server_id)
            if not server_info:
                raise Exception(f"Server {server_id} not found in registry")
            
            # Check circuit breaker
            if self._is_circuit_breaker_open(server_id):
                return self._create_circuit_breaker_result(server_id)
            
            # Perform appropriate health check based on protocol
            if server_info.protocol == ServerProtocol.HTTP:
                result = await self._check_http_health(server_info)
            elif server_info.protocol == ServerProtocol.WEBSOCKET:
                result = await self._check_websocket_health(server_info)
            elif server_info.protocol == ServerProtocol.STDIO:
                result = await self._check_process_health(server_info)
            else:
                result = await self._check_tcp_health(server_info)
            
            # Update circuit breaker and metrics
            await self._process_health_result(result)
            
            return result
            
        except Exception as e:
            # Create failure result
            result = HealthCheckResult(
                server_id=server_id,
                check_type=HealthCheckType.HTTP_ENDPOINT,
                status=ServerStatus.ERROR,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message=str(e)

            
            await self._process_health_result(result)
            return result
    
    async def _check_http_health(self, server_info: MCPServerInfo) -> HealthCheckResult:
        """Perform HTTP health check"""
        start_time = time.time()
        health_url = server_info.get_health_url()
        
        try:
            async with self.session.get(health_url) as response:
                response_time = time.time() - start_time
                
                # Parse response
                try:
                    data = await response.json()
                except:
                    data = {"text": await response.text()}
                
                status = ServerStatus.HEALTHY if response.status == 200 else ServerStatus.UNHEALTHY
                
                return HealthCheckResult(
                    server_id=server_info.server_id,
                    check_type=HealthCheckType.HTTP_ENDPOINT,
                    status=status,
                    response_time=response_time,
                    timestamp=datetime.now(),
                    details={
                        "http_status": response.status,
                        "response_data": data,
                        "headers": dict(response.headers)


                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                server_id=server_info.server_id,
                check_type=HealthCheckType.HTTP_ENDPOINT,
                status=ServerStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message="Health check timeout"

        except Exception as e:
            return HealthCheckResult(
                server_id=server_info.server_id,
                check_type=HealthCheckType.HTTP_ENDPOINT,
                status=ServerStatus.ERROR,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message=str(e)

    
    async def _check_websocket_health(self, server_info: MCPServerInfo) -> HealthCheckResult:
        """Perform WebSocket health check"""
        start_time = time.time()
        
        try:
            # For now, just check if we can establish a connection
            import websockets
            
            uri = f"ws://{server_info.host}:{server_info.port}{server_info.path}"
            async with websockets.connect(uri, timeout=self.health_check_timeout) as websocket:
                # Send ping
                await websocket.ping()
                response_time = time.time() - start_time
                
                return HealthCheckResult(
                    server_id=server_info.server_id,
                    check_type=HealthCheckType.WEBSOCKET_PING,
                    status=ServerStatus.HEALTHY,
                    response_time=response_time,
                    timestamp=datetime.now(),
                    details={"websocket_connected": True}

                
        except Exception as e:
            return HealthCheckResult(
                server_id=server_info.server_id,
                check_type=HealthCheckType.WEBSOCKET_PING,
                status=ServerStatus.ERROR,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message=str(e)

    
    async def _check_tcp_health(self, server_info: MCPServerInfo) -> HealthCheckResult:
        """Perform TCP connection health check"""
        start_time = time.time()
        
        try:
            # Attempt TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(server_info.host, server_info.port),
                timeout=self.health_check_timeout

            
            writer.close()
            await writer.wait_closed()
            
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                server_id=server_info.server_id,
                check_type=HealthCheckType.TCP_CONNECT,
                status=ServerStatus.HEALTHY,
                response_time=response_time,
                timestamp=datetime.now(),
                details={"tcp_connected": True}

            
        except Exception as e:
            return HealthCheckResult(
                server_id=server_info.server_id,
                check_type=HealthCheckType.TCP_CONNECT,
                status=ServerStatus.ERROR,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message=str(e)

    
    async def _check_process_health(self, server_info: MCPServerInfo) -> HealthCheckResult:
        """Perform process health check for STDIO servers"""
        start_time = time.time()
        
        try:
            # Check if process is running (placeholder implementation)
            # In a real implementation, you'd check if the process is actually running
            
            return HealthCheckResult(
                server_id=server_info.server_id,
                check_type=HealthCheckType.PROCESS_CHECK,
                status=ServerStatus.UNKNOWN,  # Can't easily check STDIO processes
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                details={"process_check": "not_implemented"}

            
        except Exception as e:
            return HealthCheckResult(
                server_id=server_info.server_id,
                check_type=HealthCheckType.PROCESS_CHECK,
                status=ServerStatus.ERROR,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message=str(e)

    
    def _create_circuit_breaker_result(self, server_id: str) -> HealthCheckResult:
        """Create result when circuit breaker is open"""
        return HealthCheckResult(
            server_id=server_id,
            check_type=HealthCheckType.HTTP_ENDPOINT,
            status=ServerStatus.UNHEALTHY,
            response_time=0.0,
            timestamp=datetime.now(),
            details={"circuit_breaker": "open"},
            error_message="Circuit breaker is open"

    
    async def _process_health_result(self, result: HealthCheckResult):
        """Process health check result and update metrics"""
        server_id = result.server_id
        
        # Store result
        if server_id not in self.health_results:
            self.health_results[server_id] = []
        
        self.health_results[server_id].append(result)
        
        # Limit history size
        if len(self.health_results[server_id]) > self.max_history_size:
            self.health_results[server_id] = self.health_results[server_id][-self.max_history_size:]
        
        # Update server status in registry
        server_info = await self.server_registry.get_server_by_id(server_id)
        if server_info:
            server_info.status = result.status
            server_info.last_health_check = result.timestamp
            if result.error_message:
                server_info.last_error = result.error_message
        
        # Update circuit breaker
        await self._update_circuit_breaker(result)
        
        # Update performance metrics
        await self._update_performance_metrics(result)
        
        # Check for alerts
        await self._check_alerts(result)
        
        # Update monitoring stats
        self.monitoring_stats["total_checks"] += 1
        if result.status in [ServerStatus.HEALTHY, ServerStatus.UNKNOWN]:
            self.monitoring_stats["successful_checks"] += 1
        else:
            self.monitoring_stats["failed_checks"] += 1
        
        # Update average check time
        total = self.monitoring_stats["total_checks"]
        current_avg = self.monitoring_stats["avg_check_time"]
        self.monitoring_stats["avg_check_time"] = (
            (current_avg * (total - 1) + result.response_time) / total

    
    async def _update_circuit_breaker(self, result: HealthCheckResult):
        """Update circuit breaker state based on health check result"""
        server_id = result.server_id
        breaker = self.circuit_breakers.get(server_id)
        
        if not breaker:
            return
        
        if result.status in [ServerStatus.HEALTHY, ServerStatus.UNKNOWN]:
            # Success - reset or update based on current state
            if breaker.state == "half_open":
                breaker.half_open_call_count += 1
                if breaker.half_open_call_count >= breaker.half_open_max_calls:
                    # Close the circuit breaker
                    breaker.state = "closed"
                    breaker.is_open = False
                    breaker.failure_count = 0
                    breaker.half_open_call_count = 0
                    logger.info(f"[CIRCUIT_BREAKER] Closed for {server_id}")
            elif breaker.state == "closed":
                # Reset failure count on success
                breaker.failure_count = 0
        else:
            # Failure - increment failure count
            breaker.failure_count += 1
            breaker.last_failure_time = datetime.now()
            
            if breaker.state == "closed" and breaker.failure_count >= breaker.failure_threshold:
                # Open the circuit breaker
                breaker.state = "open"
                breaker.is_open = True
                self.monitoring_stats["circuit_breaker_trips"] += 1
                logger.warning(f"[CIRCUIT_BREAKER] Opened for {server_id} after {breaker.failure_count} failures")
                
                # Generate alert
                await self._generate_alert(
                    server_id,
                    AlertSeverity.CRITICAL,
                    f"Circuit breaker opened after {breaker.failure_count} consecutive failures"

            elif breaker.state == "half_open":
                # Return to open state
                breaker.state = "open"
                breaker.is_open = True
                breaker.half_open_call_count = 0
    
    def _is_circuit_breaker_open(self, server_id: str) -> bool:
        """Check if circuit breaker is open for a server"""
        breaker = self.circuit_breakers.get(server_id)
        if not breaker:
            return False
        
        if breaker.state == "closed":
            return False
        elif breaker.state == "open":
            # Check if recovery timeout has passed
            if breaker.last_failure_time:
                time_since_failure = (datetime.now() - breaker.last_failure_time).total_seconds()
                if time_since_failure >= breaker.recovery_timeout:
                    # Move to half-open state
                    breaker.state = "half_open"
                    breaker.is_open = False
                    breaker.half_open_call_count = 0
                    logger.info(f"[CIRCUIT_BREAKER] Half-open for {server_id}")
                    return False
            return True
        elif breaker.state == "half_open":
            return False
        
        return breaker.is_open
    
    async def _update_performance_metrics(self, result: HealthCheckResult):
        """Update performance metrics for a server"""
        server_id = result.server_id
        metrics = self.performance_metrics.get(server_id)
        
        if not metrics:
            return
        
        # Update counters
        metrics.total_requests += 1
        if result.status in [ServerStatus.HEALTHY, ServerStatus.UNKNOWN]:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update success rate
        metrics.success_rate = (metrics.successful_requests / metrics.total_requests) * 100
        
        # Update response times
        if result.response_time > 0:
            metrics.min_response_time = min(metrics.min_response_time, result.response_time)
            metrics.max_response_time = max(metrics.max_response_time, result.response_time)
            
            # Update average response time
            total = metrics.total_requests
            current_avg = metrics.avg_response_time
            metrics.avg_response_time = (
                (current_avg * (total - 1) + result.response_time) / total

        
        metrics.last_updated = datetime.now()
    
    async def _check_alerts(self, result: HealthCheckResult):
        """Check if alerts should be generated based on health result"""
        server_id = result.server_id
        server_info = await self.server_registry.get_server_by_id(server_id)
        
        if not server_info:
            return
        
        # Check for server down alert
        if result.status == ServerStatus.ERROR:
            alert_key = f"{server_id}_down"
            if alert_key not in self.active_alerts:
                await self._generate_alert(
                    server_id,
                    AlertSeverity.CRITICAL if server_info.tier == ServerTier.CRITICAL else AlertSeverity.WARNING,
                    f"Server {server_info.name} is down: {result.error_message}"

        
        # Check for high response time alert
        if result.response_time > 5.0:  # 5 second threshold
            alert_key = f"{server_id}_slow"
            if alert_key not in self.active_alerts:
                await self._generate_alert(
                    server_id,
                    AlertSeverity.WARNING,
                    f"Server {server_info.name} has high response time: {result.response_time:.2f}s"

        
        # Check for low success rate alert
        metrics = self.performance_metrics.get(server_id)
        if metrics and metrics.total_requests >= 10 and metrics.success_rate < 80:
            alert_key = f"{server_id}_low_success"
            if alert_key not in self.active_alerts:
                await self._generate_alert(
                    server_id,
                    AlertSeverity.WARNING,
                    f"Server {server_info.name} has low success rate: {metrics.success_rate:.1f}%"

    
    async def _generate_alert(self, server_id: str, severity: AlertSeverity, message: str, details: Dict[str, Any] = None):
        """Generate a health alert"""
        server_info = await self.server_registry.get_server_by_id(server_id)
        server_name = server_info.name if server_info else server_id
        
        alert = HealthAlert(
            server_id=server_id,
            server_name=server_name,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            details=details or {}

        
        alert_key = f"{server_id}_{severity.value}"
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        self.monitoring_stats["alerts_generated"] += 1
        
        logger.warning(f"[ALERT] {severity.value.upper()}: {message}")
    
    async def _alert_cleanup_loop(self):
        """Background task to clean up resolved alerts"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.now()
                resolved_alerts = []
                
                for alert_key, alert in self.active_alerts.items():
                    # Check if alert should be auto-resolved
                    if await self._should_resolve_alert(alert):
                        alert.resolved = True
                        alert.resolved_at = current_time
                        resolved_alerts.append(alert_key)
                
                # Remove resolved alerts
                for alert_key in resolved_alerts:
                    del self.active_alerts[alert_key]
                
                # Limit alert history size
                if len(self.alert_history) > 1000:
                    self.alert_history = self.alert_history[-1000:]
                
                if resolved_alerts:
                    logger.info(f"[ALERT_CLEANUP] Resolved {len(resolved_alerts)} alerts")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Alert cleanup failed: {e}")
    
    async def _should_resolve_alert(self, alert: HealthAlert) -> bool:
        """Check if an alert should be automatically resolved"""
        # Auto-resolve alerts older than 1 hour if server is healthy
        if (datetime.now() - alert.timestamp).total_seconds() > 3600:
            recent_results = self.health_results.get(alert.server_id, [])
            if recent_results:
                # Check last 5 results
                recent_statuses = [r.status for r in recent_results[-5:]]
                if all(status in [ServerStatus.HEALTHY, ServerStatus.UNKNOWN] for status in recent_statuses):
                    return True
        
        return False
    
    async def _metrics_aggregation_loop(self):
        """Background task for metrics aggregation and cleanup"""
        while True:
            try:
                await asyncio.sleep(900)  # Run every 15 minutes
                
                # Aggregate metrics
                await self._aggregate_metrics()
                
                # Clean up old health results
                await self._cleanup_old_results()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Metrics aggregation failed: {e}")
    
    async def _aggregate_metrics(self):
        """Aggregate performance metrics across all servers"""
        total_servers = len(self.performance_metrics)
        healthy_servers = 0
        total_avg_response_time = 0.0
        total_success_rate = 0.0
        
        for metrics in self.performance_metrics.values():
            server_info = await self.server_registry.get_server_by_id(metrics.server_id)
            if server_info and server_info.status == ServerStatus.HEALTHY:
                healthy_servers += 1
            
            total_avg_response_time += metrics.avg_response_time
            total_success_rate += metrics.success_rate
        
        # Update global metrics
        if total_servers > 0:
            self.monitoring_stats["healthy_server_percentage"] = (healthy_servers / total_servers) * 100
            self.monitoring_stats["avg_response_time_all"] = total_avg_response_time / total_servers
            self.monitoring_stats["avg_success_rate_all"] = total_success_rate / total_servers
    
    async def _cleanup_old_results(self):
        """Clean up health results older than 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        cleaned_count = 0
        
        for server_id, results in self.health_results.items():
            original_count = len(results)
            self.health_results[server_id] = [
                result for result in results 
                if result.timestamp > cutoff_time

            cleaned_count += original_count - len(self.health_results[server_id])
        
        if cleaned_count > 0:
            logger.debug(f"[CLEANUP] Cleaned up {cleaned_count} old health results")
    
    async def get_server_health_summary(self, server_id: str) -> Dict[str, Any]:
        """Get comprehensive health summary for a server"""
        server_info = await self.server_registry.get_server_by_id(server_id)
        if not server_info:
            return {"error": "Server not found"}
        
        metrics = self.performance_metrics.get(server_id)
        breaker = self.circuit_breakers.get(server_id)
        recent_results = self.health_results.get(server_id, [])[-10:]  # Last 10 results
        
        return {
            "server_id": server_id,
            "server_name": server_info.name,
            "tier": server_info.tier.value,
            "current_status": server_info.status.value,
            "last_health_check": server_info.last_health_check.isoformat() if server_info.last_health_check else None,
            "last_error": server_info.last_error,
            "performance_metrics": {
                "avg_response_time": metrics.avg_response_time if metrics else 0,
                "success_rate": metrics.success_rate if metrics else 0,
                "total_requests": metrics.total_requests if metrics else 0
            } if metrics else None,
            "circuit_breaker": {
                "state": breaker.state if breaker else "unknown",
                "failure_count": breaker.failure_count if breaker else 0,
                "is_open": breaker.is_open if breaker else False
            } if breaker else None,
            "recent_checks": [
                {
                    "timestamp": result.timestamp.isoformat(),
                    "status": result.status.value,
                    "response_time": result.response_time,
                    "error": result.error_message

                for result in recent_results


    
    async def get_overall_health_status(self) -> Dict[str, Any]:
        """Get overall health status of all servers"""
        total_servers = len(self.server_registry.servers)
        healthy_count = len([
            s for s in self.server_registry.servers.values() 
            if s.status == ServerStatus.HEALTHY

        
        tier_health = {
            "critical": {"total": 0, "healthy": 0},
            "integration": {"total": 0, "healthy": 0},
            "specialized": {"total": 0, "healthy": 0}

        
        for server in self.server_registry.servers.values():
            tier_key = server.tier.value
            tier_health[tier_key]["total"] += 1
            if server.status == ServerStatus.HEALTHY:
                tier_health[tier_key]["healthy"] += 1
        
        return {
            "overall_status": "healthy" if healthy_count == total_servers else "degraded",
            "total_servers": total_servers,
            "healthy_servers": healthy_count,
            "health_percentage": (healthy_count / total_servers * 100) if total_servers > 0 else 0,
            "tier_health": tier_health,
            "active_alerts": len(self.active_alerts),
            "circuit_breakers_open": len([
                cb for cb in self.circuit_breakers.values() if cb.is_open
            ]),
            "monitoring_stats": self.monitoring_stats,
            "last_updated": datetime.now().isoformat()

    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [
            {
                "server_id": alert.server_id,
                "server_name": alert.server_name,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "details": alert.details

            for alert in self.active_alerts.values()

    
    async def force_circuit_breaker_reset(self, server_id: str) -> bool:
        """Manually reset a circuit breaker"""
        breaker = self.circuit_breakers.get(server_id)
        if not breaker:
            return False
        
        breaker.state = "closed"
        breaker.is_open = False
        breaker.failure_count = 0
        breaker.half_open_call_count = 0
        breaker.last_failure_time = None
        
        logger.info(f"[CIRCUIT_BREAKER] Manually reset for {server_id}")
        return True
    
    async def shutdown(self):
        """Shutdown the health monitor"""
        logger.info("[SHUTDOWN] Shutting down Health Monitor...")
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        
        # Cancel background tasks
        if self.alert_cleanup_task:
            self.alert_cleanup_task.cancel()
            try:
                await self.alert_cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.metrics_aggregation_task:
            self.metrics_aggregation_task.cancel()
            try:
                await self.metrics_aggregation_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        logger.info("[SHUTDOWN] Health Monitor shutdown complete")