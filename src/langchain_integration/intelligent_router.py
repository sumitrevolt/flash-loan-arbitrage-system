# -*- coding: utf-8 -*-
"""
Intelligent Router for Flash Loan Arbitrage System

This module implements intelligent load balancing and routing across server tiers
with performance-based optimization and circuit breaker patterns.
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import asyncio
import logging
import random
import time

from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategies for different request types"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    FASTEST_RESPONSE = "fastest_response"
    HEALTH_WEIGHTED = "health_weighted"
    CAPABILITY_BASED = "capability_based"


class ServerHealth(Enum):
    """Server health states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServerMetrics:
    """Server performance and health metrics"""
    server_name: str
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    active_connections: int = 0
    max_connections: int = 100
    last_health_check: Optional[datetime] = None
    health_status: ServerHealth = ServerHealth.UNKNOWN
    circuit_breaker_open: bool = False
    weight: float = 1.0
    tier: str = "unknown"
    capabilities: Set[str] = field(default_factory=set)


@dataclass
class RoutingRequest:
    """Request routing information"""
    request_id: str
    request_type: str
    priority: str = "medium"
    required_capabilities: List[str] = field(default_factory=list)
    data_requirements: List[str] = field(default_factory=list)
    preferred_tier: Optional[str] = None
    timeout: int = 30
    affinity_key: Optional[str] = None  # For session affinity


@dataclass
class RoutingResult:
    """Result of routing decision"""
    selected_servers: List[str]
    routing_strategy: str
    selection_reason: str
    estimated_response_time: float
    backup_servers: List[str] = field(default_factory=list)


class IntelligentRouter:
    """
    Intelligent router for load balancing and optimal server selection
    across multiple tiers with performance optimization and fault tolerance.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Server metrics and state
        self.server_metrics: Dict[str, ServerMetrics] = {}
        self.tier_servers: Dict[str, List[str]] = {
            "critical": [],
            "integration": [],
            "specialized": []

        
        # Routing state
        self.round_robin_counters: Dict[str, int] = defaultdict(int)
        self.affinity_mappings: Dict[str, str] = {}  # affinity_key -> server_name
        
        # Performance tracking
        self.routing_history: deque = deque(maxlen=1000)
        self.performance_stats = {
            "total_routes": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "avg_selection_time": 0.0

        
        # Circuit breaker configuration
        self.circuit_breaker_config = {
            "failure_threshold": config.get("circuit_breaker", {}).get("failure_threshold", 5),
            "recovery_timeout": config.get("circuit_breaker", {}).get("recovery_timeout", 60),
            "half_open_max_calls": config.get("circuit_breaker", {}).get("half_open_max_calls", 3)

        
        # Health monitoring
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.metrics_cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("[INIT] Intelligent Router initialized")
    
    async def initialize(self):
        """Initialize the intelligent router"""
        try:
            # Load server configuration
            await self._load_server_configuration()
            
            # Start health monitoring
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
            
            # Start metrics cleanup
            self.metrics_cleanup_task = asyncio.create_task(self._metrics_cleanup_loop())
            
            logger.info(f"[OK] Intelligent Router initialized with {len(self.server_metrics)} servers")
            
        except Exception as e:
            logger.error(f"[ERROR] Intelligent Router initialization failed: {e}")
            raise
    
    async def _load_server_configuration(self):
        """Load server configuration and initialize metrics"""
        server_config = self.config.get("server_tiers", {})
        
        # Load critical servers (Tier 1)
        critical_servers = server_config.get("critical", [])
        for server_name in critical_servers:
            self.server_metrics[server_name] = ServerMetrics(
                server_name=server_name,
                tier="critical",
                weight=1.0,
                max_connections=100,
                capabilities=set(["filesystem", "context", "memory", "tasks"])

            self.tier_servers["critical"].append(server_name)
        
        # Load integration servers (Tier 2)
        integration_servers = server_config.get("integration", [])
        for server_name in integration_servers:
            self.server_metrics[server_name] = ServerMetrics(
                server_name=server_name,
                tier="integration",
                weight=0.8,
                max_connections=50,
                capabilities=set(["langchain", "autogen", "coordination"])

            self.tier_servers["integration"].append(server_name)
        
        # Load specialized servers (Tier 3)
        specialized_servers = server_config.get("specialized", [])
        for server_name in specialized_servers:
            self.server_metrics[server_name] = ServerMetrics(
                server_name=server_name,
                tier="specialized",
                weight=0.6,
                max_connections=25,
                capabilities=set(["flash_loan", "arbitrage", "risk_management"])

            self.tier_servers["specialized"].append(server_name)
        
        logger.info(f"[OK] Loaded configuration for {len(self.server_metrics)} servers")
    
    async def select_optimal_servers(
        self,
        request_type: str,
        count: int = 1,
        required_capabilities: Optional[List[str]] = None,
        data_requirements: Optional[List[str]] = None,
        priority: str = "medium",
        preferred_tier: Optional[str] = None,
        affinity_key: Optional[str] = None
    ) -> List[str]:
        """
        Select optimal servers for a request based on multiple criteria
        
        Args:
            request_type: Type of request (analytics, risk_management, etc.)
            count: Number of servers to select
            required_capabilities: Required server capabilities
            data_requirements: Data requirements for the request
            priority: Request priority (critical, high, medium, low)
            preferred_tier: Preferred server tier
            affinity_key: Key for session affinity
            
        Returns:
            List of selected server names
        """
        start_time = time.time()
        
        try:
            routing_request = RoutingRequest(
                request_id=f"route_{int(time.time() * 1000)}",
                request_type=request_type,
                priority=priority,
                required_capabilities=required_capabilities or [],
                data_requirements=data_requirements or [],
                preferred_tier=preferred_tier,
                affinity_key=affinity_key

            
            # Select routing strategy
            strategy = self._select_routing_strategy(routing_request)
            
            # Get candidate servers
            candidates = self._get_candidate_servers(routing_request)
            
            # Apply routing strategy
            selected_servers = await self._apply_routing_strategy(
                strategy, candidates, routing_request, count

            
            # Update performance metrics
            selection_time = time.time() - start_time
            self._update_routing_metrics(selected_servers, selection_time, "success")
            
            logger.info(f"[ROUTE] Selected {len(selected_servers)} servers using {strategy.value}")
            return selected_servers
            
        except Exception as e:
            selection_time = time.time() - start_time
            self._update_routing_metrics([], selection_time, "failure")
            logger.error(f"[ERROR] Server selection failed: {e}")
            raise
    
    def _select_routing_strategy(self, request: RoutingRequest) -> RoutingStrategy:
        """Select appropriate routing strategy based on request characteristics"""
        
        # Critical priority requests use fastest response
        if request.priority == "critical":
            return RoutingStrategy.FASTEST_RESPONSE
        
        # Requests with affinity use capability-based routing
        if request.affinity_key:
            return RoutingStrategy.CAPABILITY_BASED
        
        # Analytics requests benefit from health-weighted routing
        if request.request_type in ["analytics", "market_analysis"]:
            return RoutingStrategy.HEALTH_WEIGHTED
        
        # Execution requests use least connections
        if request.request_type in ["flash_loan_execution", "trade_execution"]:
            return RoutingStrategy.LEAST_CONNECTIONS
        
        # Default to weighted round robin
        return RoutingStrategy.WEIGHTED_ROUND_ROBIN
    
    def _get_candidate_servers(self, request: RoutingRequest) -> List[str]:
        """Get candidate servers based on request requirements"""
        candidates = []
        
        # Filter by preferred tier
        if request.preferred_tier and request.preferred_tier in self.tier_servers:
            tier_servers = self.tier_servers[request.preferred_tier]
        else:
            # Get servers from all tiers if no preference
            tier_servers = []
            for tier_list in self.tier_servers.values():
                tier_servers.extend(tier_list)
        
        # Filter by capabilities
        for server_name in tier_servers:
            metrics = self.server_metrics.get(server_name)
            if not metrics:
                continue
            
            # Check health status
            if metrics.health_status == ServerHealth.UNHEALTHY:
                continue
            
            # Check circuit breaker
            if metrics.circuit_breaker_open:
                continue
            
            # Check capabilities
            if request.required_capabilities:
                if not all(cap in metrics.capabilities for cap in request.required_capabilities):
                    continue
            
            # Check connection capacity
            if metrics.active_connections >= metrics.max_connections:
                continue
            
            candidates.append(server_name)
        
        return candidates
    
    async def _apply_routing_strategy(
        self,
        strategy: RoutingStrategy,
        candidates: List[str],
        request: RoutingRequest,
        count: int
    ) -> List[str]:
        """Apply the selected routing strategy to choose servers"""
        
        if not candidates:
            raise Exception("No healthy servers available")
        
        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(candidates, count)
        
        elif strategy == RoutingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(candidates, count)
        
        elif strategy == RoutingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(candidates, count)
        
        elif strategy == RoutingStrategy.FASTEST_RESPONSE:
            return self._fastest_response_selection(candidates, count)
        
        elif strategy == RoutingStrategy.HEALTH_WEIGHTED:
            return self._health_weighted_selection(candidates, count)
        
        elif strategy == RoutingStrategy.CAPABILITY_BASED:
            return self._capability_based_selection(candidates, request, count)
        
        else:
            # Fallback to round robin
            return self._round_robin_selection(candidates, count)
    
    def _round_robin_selection(self, candidates: List[str], count: int) -> List[str]:
        """Round robin server selection"""
        if not candidates:
            return []
        
        selected = []
        strategy_key = "round_robin"
        
        for _ in range(min(count, len(candidates))):
            index = self.round_robin_counters[strategy_key] % len(candidates)
            selected.append(candidates[index])
            self.round_robin_counters[strategy_key] += 1
        
        return selected
    
    def _weighted_round_robin_selection(self, candidates: List[str], count: int) -> List[str]:
        """Weighted round robin selection based on server weights"""
        if not candidates:
            return []
        
        # Calculate weighted choices
        weights = []
        for server_name in candidates:
            metrics = self.server_metrics.get(server_name)
            if metrics:
                # Weight based on health and performance
                weight = metrics.weight
                if metrics.health_status == ServerHealth.HEALTHY:
                    weight *= 1.2
                elif metrics.health_status == ServerHealth.DEGRADED:
                    weight *= 0.8
                
                # Adjust for response time
                if metrics.response_times:
                    avg_response = sum(metrics.response_times) / len(metrics.response_times)
                    weight *= max(0.1, 1.0 - (avg_response / 10.0))  # Penalize slow servers
                
                weights.append(weight)
            else:
                weights.append(1.0)
        
        # Select servers based on weights
        selected = []
        for _ in range(min(count, len(candidates))):
            if weights:
                # Weighted random selection
                total_weight = sum(weights)
                if total_weight > 0:
                    r = random.uniform(0, total_weight)
                    cumulative = 0
                    for i, weight in enumerate(weights):
                        cumulative += weight
                        if r <= cumulative:
                            selected.append(candidates[i])
                            # Remove selected server to avoid duplicates
                            candidates.pop(i)
                            weights.pop(i)
                            break
                else:
                    # Fallback to random selection
                    selected.append(candidates.pop(random.randint(0, len(candidates) - 1)))
            else:
                break
        
        return selected
    
    def _least_connections_selection(self, candidates: List[str], count: int) -> List[str]:
        """Select servers with least active connections"""
        if not candidates:
            return []
        
        # Sort by active connections
        candidate_metrics = [
            (server_name, self.server_metrics.get(server_name, ServerMetrics(server_name)))
            for server_name in candidates

        
        candidate_metrics.sort(key=lambda x: x[1].active_connections)
        
        selected = [server_name for server_name, _ in candidate_metrics[:count]]
        return selected
    
    def _fastest_response_selection(self, candidates: List[str], count: int) -> List[str]:
        """Select servers with fastest average response times"""
        if not candidates:
            return []
        
        # Calculate average response times
        server_avg_times = []
        for server_name in candidates:
            metrics = self.server_metrics.get(server_name)
            if metrics and metrics.response_times:
                avg_time = sum(metrics.response_times) / len(metrics.response_times)
            else:
                avg_time = float('inf')  # Unknown performance
            
            server_avg_times.append((server_name, avg_time))
        
        # Sort by response time
        server_avg_times.sort(key=lambda x: x[1])
        
        selected = [server_name for server_name, _ in server_avg_times[:count]]
        return selected
    
    def _health_weighted_selection(self, candidates: List[str], count: int) -> List[str]:
        """Select servers weighted by health score"""
        if not candidates:
            return []
        
        # Calculate health scores
        health_scores = []
        for server_name in candidates:
            metrics = self.server_metrics.get(server_name)
            score = 0.0
            
            if metrics:
                # Base score from health status
                if metrics.health_status == ServerHealth.HEALTHY:
                    score += 1.0
                elif metrics.health_status == ServerHealth.DEGRADED:
                    score += 0.5
                
                # Success rate score
                if metrics.request_count > 0:
                    success_rate = metrics.success_count / metrics.request_count
                    score += success_rate
                
                # Response time score (inverse)
                if metrics.response_times:
                    avg_response = sum(metrics.response_times) / len(metrics.response_times)
                    score += max(0, 1.0 - (avg_response / 5.0))  # 5s max for full score
                
                # Connection availability score
                connection_ratio = metrics.active_connections / metrics.max_connections
                score += (1.0 - connection_ratio)
            
            health_scores.append((server_name, score))
        
        # Sort by health score (descending)
        health_scores.sort(key=lambda x: x[1], reverse=True)
        
        selected = [server_name for server_name, _ in health_scores[:count]]
        return selected
    
    def _capability_based_selection(
        self, 
        candidates: List[str], 
        request: RoutingRequest, 
        count: int
    ) -> List[str]:
        """Select servers based on specific capabilities and affinity"""
        if not candidates:
            return []
        
        # Check for session affinity
        if request.affinity_key and request.affinity_key in self.affinity_mappings:
            affinity_server = self.affinity_mappings[request.affinity_key]
            if affinity_server in candidates:
                selected = [affinity_server]
                # Fill remaining slots if needed
                remaining_candidates = [s for s in candidates if s != affinity_server]
                selected.extend(self._health_weighted_selection(remaining_candidates, count - 1))
                return selected[:count]
        
        # Score servers based on capability match
        capability_scores = []
        for server_name in candidates:
            metrics = self.server_metrics.get(server_name)
            score = 0.0
            
            if metrics:
                # Score based on required capabilities
                if request.required_capabilities:
                    matched_caps = len(set(request.required_capabilities) & metrics.capabilities)
                    total_caps = len(request.required_capabilities)
                    score += (matched_caps / total_caps) if total_caps > 0 else 0
                
                # Bonus for specialized servers matching request type
                if request.request_type in metrics.capabilities:
                    score += 0.5
                
                # Health bonus
                if metrics.health_status == ServerHealth.HEALTHY:
                    score += 0.3
            
            capability_scores.append((server_name, score))
        
        # Sort by capability score (descending)
        capability_scores.sort(key=lambda x: x[1], reverse=True)
        
        selected = [server_name for server_name, _ in capability_scores[:count]]
        
        # Set affinity for future requests
        if request.affinity_key and selected:
            self.affinity_mappings[request.affinity_key] = selected[0]
        
        return selected
    
    async def record_request_result(
        self, 
        server_name: str, 
        response_time: float, 
        success: bool
    ):
        """Record the result of a request for metrics tracking"""
        metrics = self.server_metrics.get(server_name)
        if not metrics:
            return
        
        # Update metrics
        metrics.request_count += 1
        metrics.response_times.append(response_time)
        
        if success:
            metrics.success_count += 1
            # Reset circuit breaker on success
            if metrics.circuit_breaker_open:
                metrics.circuit_breaker_open = False
                logger.info(f"[CIRCUIT_BREAKER] Closed for {server_name}")
        else:
            metrics.failure_count += 1
            # Check circuit breaker threshold
            if metrics.failure_count >= self.circuit_breaker_config["failure_threshold"]:
                metrics.circuit_breaker_open = True
                logger.warning(f"[CIRCUIT_BREAKER] Opened for {server_name}")
    
    def _update_routing_metrics(self, selected_servers: List[str], selection_time: float, status: str):
        """Update routing performance metrics"""
        self.performance_stats["total_routes"] += 1
        
        if status == "success":
            self.performance_stats["successful_routes"] += 1
        else:
            self.performance_stats["failed_routes"] += 1
        
        # Update average selection time
        total_routes = self.performance_stats["total_routes"]
        current_avg = self.performance_stats["avg_selection_time"]
        self.performance_stats["avg_selection_time"] = (
            (current_avg * (total_routes - 1) + selection_time) / total_routes

        
        # Store routing history
        self.routing_history.append({
            "timestamp": datetime.now(),
            "selected_servers": selected_servers,
            "selection_time": selection_time,
            "status": status

    
    async def _health_monitor_loop(self):
        """Health monitoring loop for updating server health status"""
        while True:
            try:
                await self._update_server_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Health monitoring failed: {e}")
                await asyncio.sleep(30)
    
    async def _update_server_health(self):
        """Update health status for all servers"""
        for server_name, metrics in self.server_metrics.items():
            # Calculate health score based on recent performance
            health_score = self._calculate_health_score(metrics)
            
            # Update health status
            if health_score >= 0.8:
                metrics.health_status = ServerHealth.HEALTHY
            elif health_score >= 0.5:
                metrics.health_status = ServerHealth.DEGRADED
            else:
                metrics.health_status = ServerHealth.UNHEALTHY
            
            metrics.last_health_check = datetime.now()
    
    def _calculate_health_score(self, metrics: ServerMetrics) -> float:
        """Calculate health score for a server"""
        score = 1.0
        
        # Success rate factor
        if metrics.request_count > 0:
            success_rate = metrics.success_count / metrics.request_count
            score *= success_rate
        
        # Response time factor
        if metrics.response_times:
            avg_response = sum(metrics.response_times) / len(metrics.response_times)
            # Penalize slow responses (>2s)
            if avg_response > 2.0:
                score *= max(0.1, 1.0 - ((avg_response - 2.0) / 10.0))
        
        # Connection utilization factor
        connection_ratio = metrics.active_connections / metrics.max_connections
        if connection_ratio > 0.8:
            score *= (1.0 - connection_ratio)
        
        # Circuit breaker factor
        if metrics.circuit_breaker_open:
            score *= 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _metrics_cleanup_loop(self):
        """Cleanup old metrics and routing history"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean up old routing history
                cutoff_time = datetime.now() - timedelta(hours=24)
                while (self.routing_history and 
                       self.routing_history[0]["timestamp"] < cutoff_time):
                    self.routing_history.popleft()
                
                # Reset circuit breakers if recovery timeout has passed
                for metrics in self.server_metrics.values():
                    if (metrics.circuit_breaker_open and 
                        time.time() - metrics.failure_count > self.circuit_breaker_config["recovery_timeout"]):
                        metrics.circuit_breaker_open = False
                        metrics.failure_count = 0
                        logger.info(f"[CIRCUIT_BREAKER] Reset for {metrics.server_name}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Metrics cleanup failed: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get router status and metrics"""
        server_health = {}
        for server_name, metrics in self.server_metrics.items():
            avg_response_time = (
                sum(metrics.response_times) / len(metrics.response_times)
                if metrics.response_times else 0

            
            server_health[server_name] = {
                "health_status": metrics.health_status.value,
                "tier": metrics.tier,
                "active_connections": metrics.active_connections,
                "max_connections": metrics.max_connections,
                "request_count": metrics.request_count,
                "success_rate": (
                    metrics.success_count / metrics.request_count
                    if metrics.request_count > 0 else 0
                ),
                "avg_response_time": avg_response_time,
                "circuit_breaker_open": metrics.circuit_breaker_open,
                "weight": metrics.weight

        
        return {
            "router_status": "healthy",
            "total_servers": len(self.server_metrics),
            "healthy_servers": sum(
                1 for m in self.server_metrics.values() 
                if m.health_status == ServerHealth.HEALTHY
            ),
            "performance_stats": self.performance_stats,
            "server_health": server_health,
            "affinity_mappings": len(self.affinity_mappings),
            "routing_history_size": len(self.routing_history)

    
    async def shutdown(self):
        """Shutdown the intelligent router"""
        logger.info("[SHUTDOWN] Shutting down Intelligent Router...")
        
        # Cancel monitoring tasks
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass
        
        if self.metrics_cleanup_task:
            self.metrics_cleanup_task.cancel()
            try:
                await self.metrics_cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[SHUTDOWN] Intelligent Router shutdown complete")