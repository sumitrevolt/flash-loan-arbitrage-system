# -*- coding: utf-8 -*-
"""
LangChain Master Orchestrator for Flash Loan Arbitrage System

This module implements the main coordination layer that manages workflow execution,
MCP server communication, and arbitrage strategy orchestration.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, TYPE_CHECKING
import asyncio
import json
import logging
import time

from dataclasses import dataclass
from enum import Enum

# Redis availability check and imports
try:
    import redis.asyncio
    from redis.asyncio import Redis as RedisClient
    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore
    RedisClient = None  # type: ignore
    REDIS_AVAILABLE = False

# Type checking imports
if TYPE_CHECKING:
    if REDIS_AVAILABLE:
        from redis.asyncio import Redis as RedisType
    else:
        RedisType = None  # type: ignore

from .mcp_communication_manager import MCPCommunicationManager
from .workflow_engine import WorkflowEngine
from .intelligent_router import IntelligentRouter
from .conversation_manager import ConversationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestrationMode(Enum):
    """Orchestration modes for different workflow types"""
    ARBITRAGE_ANALYSIS = "arbitrage_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    TRADE_EXECUTION = "trade_execution"
    MULTI_AGENT_DECISION = "multi_agent_decision"
    SYSTEM_MONITORING = "system_monitoring"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OrchestrationTask:
    """Represents a task for orchestration"""
    task_id: str
    description: str
    mode: OrchestrationMode
    priority: TaskPriority
    parameters: Dict[str, Any]
    created_at: datetime
    timeout: Optional[int] = 300  # 5 minutes default
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class OrchestrationResult:
    """Result of orchestration operation"""
    task_id: str
    status: str
    mode: str
    execution_time: float
    agents_involved: List[str]
    mcp_servers_used: List[str]
    result_data: Dict[str, Any]
    timestamp: str
    conversation_rounds: Optional[int] = None
    error: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "mode": self.mode,
            "execution_time": self.execution_time,
            "agents_involved": self.agents_involved,
            "mcp_servers_used": self.mcp_servers_used,
            "result_data": self.result_data,
            "conversation_rounds": self.conversation_rounds,
            "error": self.error,
            "timestamp": self.timestamp

    
    def json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.dict())


class LangChainMasterOrchestrator:
    """
    Master orchestrator for coordinating all flash loan arbitrage operations
    using LangChain workflows and MCP server communication.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the LangChain Master Orchestrator"""
        self.config = config or self._load_default_config()
        
        # Initialize core components
        self.mcp_manager = MCPCommunicationManager(self.config)
        self.workflow_engine = WorkflowEngine(self.config)
        self.intelligent_router = IntelligentRouter(self.config)
        self.conversation_manager = ConversationManager(self.config)
        
        # State management
        self.active_tasks: Dict[str, OrchestrationTask] = {}
        self.task_history: Dict[str, OrchestrationResult] = {}
        self.performance_metrics: Dict[str, float] = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0.0,
            "active_orchestrations": 0

        
        # Redis client for state persistence
        self.redis_client: Optional[RedisClient] = None
        
        # Circuit breaker state
        self.circuit_breaker_state: Dict[str, Any] = {}
        
        self.start_time = datetime.now()
        logger.info(f"[INIT] LangChain Master Orchestrator initialized at {self.start_time}")
    
    async def initialize(self) -> None:
        """Initialize async components"""
        try:
            # Initialize Redis connection if available
            if REDIS_AVAILABLE:
                redis_url: str = self.config.get("redis_url", "redis://localhost:6379")
                self.redis_client = redis.asyncio.from_url(redis_url, decode_responses=True)
                await self.redis_client.ping()
                logger.info(f"[OK] Redis connected: {redis_url}")
            else:
                logger.warning("[WARNING] Redis not available, using memory-only storage")
            
            # Initialize MCP manager
            await self.mcp_manager.initialize()
            
            # Initialize workflow engine
            await self.workflow_engine.initialize()
            
            # Initialize intelligent router
            await self.intelligent_router.initialize()
            
            # Initialize conversation manager
            await self.conversation_manager.initialize()
            
            logger.info("[OK] LangChain Master Orchestrator fully initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] Initialization failed: {e}")
            raise
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "redis_url": "redis://localhost:6379",
            "mcp_hub_url": "http://localhost:8000",
            "autogen_url": "http://localhost:8001",
            "timeout": 300,
            "max_retries": 3,
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_timeout": 60
            },
            "server_tiers": {
                "critical": ["filesystem", "context7", "supermemory", "taskmanager"],
                "integration": ["langchain_orchestrator", "autogen_system", "enhanced_manager"],
                "specialized": ["flash_loan_servers", "arbitrage_servers", "risk_management"]


    
    async def execute_arbitrage_workflow(self, opportunity: Dict[str, Any]) -> OrchestrationResult:
        """
        Execute complete arbitrage workflow from analysis to execution
        
        Args:
            opportunity: Arbitrage opportunity data
            
        Returns:
            OrchestrationResult with complete workflow results
        """
        task_id = f"arbitrage_{int(time.time() * 1000)}"
        
        try:
            # Create orchestration task
            task = OrchestrationTask(
                task_id=task_id,
                description=f"Arbitrage workflow for {opportunity.get('token_pair', 'unknown')}",
                mode=OrchestrationMode.ARBITRAGE_ANALYSIS,
                priority=TaskPriority.HIGH,
                parameters=opportunity,
                created_at=datetime.now()

            
            logger.info(f"[WORKFLOW] Starting arbitrage workflow: {task_id}")
            
            # Execute workflow phases
            result = await self._execute_multi_phase_workflow(task)
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Arbitrage workflow failed: {e}")
            return OrchestrationResult(
                task_id=task_id,
                status="failed",
                mode=OrchestrationMode.ARBITRAGE_ANALYSIS.value,
                execution_time=0,
                agents_involved=[],
                mcp_servers_used=[],
                result_data={"error": str(e)},
                error=str(e),
                timestamp=datetime.now().isoformat()

    
    async def _execute_multi_phase_workflow(self, task: OrchestrationTask) -> OrchestrationResult:
        """Execute multi-phase workflow with proper coordination"""
        start_time: float = time.time()
        self.active_tasks[task.task_id] = task
        self.performance_metrics["active_orchestrations"] += 1
        
        try:
            agents_involved: List[str] = []
            mcp_servers_used: List[str] = []
            result_data: Dict[str, Any] = {}
            
            # Phase 1: Market Analysis
            logger.info(f"[PHASE 1] Market analysis for {task.task_id}")
            market_analysis = await self._execute_market_analysis(task.parameters)
            agents_involved.extend(market_analysis.get("agents_used", []))
            mcp_servers_used.extend(market_analysis.get("mcp_servers", []))
            result_data["market_analysis"] = market_analysis
            
            # Phase 2: Risk Assessment via Multi-Agent Discussion
            logger.info(f"[PHASE 2] Risk assessment for {task.task_id}")
            risk_assessment: Dict[str, Any] = await self._execute_risk_assessment(
                task.parameters, market_analysis

            agents_involved.extend(risk_assessment.get("agents_used", []))
            mcp_servers_used.extend(risk_assessment.get("mcp_servers", []))
            result_data["risk_assessment"] = risk_assessment
            
            # Phase 3: Decision Making
            logger.info(f"[PHASE 3] Decision making for {task.task_id}")
            decision: Dict[str, Any] = await self._execute_decision_making(
                task.parameters, market_analysis, risk_assessment

            agents_involved.extend(decision.get("agents_used", []))
            mcp_servers_used.extend(decision.get("mcp_servers", []))
            result_data["decision"] = decision
            
            # Phase 4: Execution (if approved)
            if decision.get("approved", False):
                logger.info(f"[PHASE 4] Execution for {task.task_id}")
                execution_result: Dict[str, Any] = await self._execute_trade_execution(
                    task.parameters, decision.get("execution_plan", {})

                agents_involved.extend(execution_result.get("agents_used", []))
                mcp_servers_used.extend(execution_result.get("mcp_servers", []))
                result_data["execution"] = execution_result
            else:
                logger.info(f"[PHASE 4] Execution skipped - not approved for {task.task_id}")
                result_data["execution"] = {"status": "skipped", "reason": "Not approved"}
            
            # Calculate execution time
            execution_time: float = time.time() - start_time
            
            # Create result
            result = OrchestrationResult(
                task_id=task.task_id,
                status="completed",
                mode=task.mode.value,
                execution_time=execution_time,
                agents_involved=list(set(agents_involved)),
                mcp_servers_used=list(set(mcp_servers_used)),
                result_data=result_data,
                conversation_rounds=result_data.get("decision", {}).get("conversation_rounds"),
                timestamp=datetime.now().isoformat()

            
            # Update metrics
            self.performance_metrics["successful_tasks"] += 1
            self.performance_metrics["total_tasks"] += 1
            self.performance_metrics["active_orchestrations"] -= 1
            self._update_avg_response_time(execution_time)
            
            # Store result
            await self._store_result(result)
            
            logger.info(f"[OK] Workflow completed for {task.task_id} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Update failure metrics
            self.performance_metrics["failed_tasks"] += 1
            self.performance_metrics["total_tasks"] += 1
            self.performance_metrics["active_orchestrations"] -= 1
            
            logger.error(f"[ERROR] Workflow failed for {task.task_id}: {e}")
            
            result = OrchestrationResult(
                task_id=task.task_id,
                status="failed",
                mode=task.mode.value,
                execution_time=execution_time,
                agents_involved=[],
                mcp_servers_used=[],
                result_data={"error": str(e)},
                error=str(e),
                timestamp=datetime.now().isoformat()

            
            await self._store_result(result)
            return result
            
        finally:
            # Cleanup
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    async def _execute_market_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market analysis phase"""
        try:
            # Route to analytics agent via MCP
            request: Dict[str, Any] = {
                "type": "market_analysis",
                "data": parameters,
                "required_services": ["price_data", "liquidity_analysis", "volatility_check"]

            
            # Use intelligent router to select optimal servers
            selected_servers = await self.intelligent_router.select_optimal_servers(
                request_type="analytics",
                data_requirements=["price_feeds", "dex_data"]

            
            # Execute via MCP communication manager
            result = await self.mcp_manager.execute_coordinated_request(
                target_services=selected_servers,
                request=request,
                timeout=30

            
            return {
                "status": "completed",
                "price_data": result.get("price_data", {}),
                "liquidity_analysis": result.get("liquidity_analysis", {}),
                "volatility_metrics": result.get("volatility_metrics", {}),
                "agents_used": ["analytics_agent"],
                "mcp_servers": selected_servers,
                "profit_potential": result.get("profit_estimate", 0),
                "market_conditions": result.get("market_conditions", "unknown")

            
        except Exception as e:
            logger.error(f"[ERROR] Market analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "agents_used": [],
                "mcp_servers": []

    
    async def _execute_risk_assessment(
        self, 
        parameters: Dict[str, Any], 
        market_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute risk assessment phase"""
        try:
            # Prepare risk assessment request
            request: Dict[str, Any] = {
                "type": "risk_assessment",
                "market_data": market_analysis,
                "trade_parameters": parameters,
                "assessment_criteria": [
                    "liquidity_risk",
                    "slippage_risk", 
                    "gas_price_risk",
                    "smart_contract_risk"


            
            # Use risk management servers
            selected_servers = await self.intelligent_router.select_optimal_servers(
                request_type="risk_management",
                priority="high"

            
            # Execute risk assessment
            result = await self.mcp_manager.execute_coordinated_request(
                target_services=selected_servers,
                request=request,
                timeout=20

            
            return {
                "status": "completed",
                "risk_score": result.get("risk_score", 0.5),
                "risk_factors": result.get("risk_factors", []),
                "recommended_limits": result.get("limits", {}),
                "agents_used": ["risk_agent"],
                "mcp_servers": selected_servers,
                "assessment_confidence": result.get("confidence", 0.8)

            
        except Exception as e:
            logger.error(f"[ERROR] Risk assessment failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "agents_used": [],
                "mcp_servers": []

    
    async def _execute_decision_making(
        self,
        parameters: Dict[str, Any],
        market_analysis: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute decision making phase using multi-agent conversation"""
        try:
            # Prepare decision context
            decision_context: Dict[str, Any] = {
                "opportunity": parameters,
                "market_analysis": market_analysis,
                "risk_assessment": risk_assessment,
                "decision_type": "arbitrage_execution"

            
            # Use conversation manager for multi-agent decision
            result = await self.conversation_manager.start_multi_agent_conversation(
                context=decision_context,
                conversation_type="arbitrage_decision",
                participants=["coordinator", "risk_validator", "execution_planner"],
                timeout=60

            
            return {
                "status": "completed",
                "approved": result.get("consensus", {}).get("approved", False),
                "execution_plan": result.get("execution_plan", {}),
                "consensus_confidence": result.get("confidence", 0.0),
                "conversation_rounds": result.get("conversation_rounds", 0),
                "agents_used": result.get("participants", []),
                "mcp_servers": ["autogen_system", "supermemory"],
                "decision_reasoning": result.get("reasoning", "")

            
        except Exception as e:
            logger.error(f"[ERROR] Decision making failed: {e}")
            return {
                "status": "failed",
                "approved": False,
                "error": str(e),
                "agents_used": [],
                "mcp_servers": []

    
    async def _execute_trade_execution(
        self,
        parameters: Dict[str, Any],
        execution_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute trade execution phase"""
        try:
            # Prepare execution request
            request: Dict[str, Any] = {
                "type": "flash_loan_execution",
                "trade_parameters": parameters,
                "execution_plan": execution_plan,
                "safety_checks": True

            
            # Select flash loan servers
            selected_servers = await self.intelligent_router.select_optimal_servers(
                request_type="flash_loan_execution",
                priority="critical"

            
            # Execute via flash loan servers
            result = await self.mcp_manager.execute_coordinated_request(
                target_services=selected_servers,
                request=request,
                timeout=60

            
            return {
                "status": "completed",
                "transaction_hash": result.get("tx_hash"),
                "gas_used": result.get("gas_used"),
                "profit_realized": result.get("profit", 0),
                "execution_time": result.get("execution_time", 0),
                "agents_used": ["execution_agent"],
                "mcp_servers": selected_servers

            
        except Exception as e:
            logger.error(f"[ERROR] Trade execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "agents_used": [],
                "mcp_servers": []

    
    def _update_avg_response_time(self, new_time: float) -> None:
        """Update average response time metric"""
        total_successful: int = int(self.performance_metrics["successful_tasks"])
        if total_successful == 1:
            self.performance_metrics["avg_response_time"] = new_time
        else:
            current_avg: float = self.performance_metrics["avg_response_time"]
            self.performance_metrics["avg_response_time"] = (
                (current_avg * (total_successful - 1) + new_time) / total_successful

    
    async def _store_result(self, result: OrchestrationResult) -> None:
        """Store orchestration result"""
        try:
            # Store in memory
            self.task_history[result.task_id] = result
            
            # Store in Redis with TTL if available
            if self.redis_client is not None:
                await self.redis_client.setex(
                    f"orchestration_result:{result.task_id}",
                    3600,  # 1 hour TTL
                    result.json()

                
        except Exception as e:
            logger.warning(f"[WARNING] Failed to store result: {e}")
    
    async def get_orchestration_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of orchestration task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task: OrchestrationTask = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "active",
                "created_at": task.created_at.isoformat(),
                "mode": task.mode.value,
                "priority": task.priority.value

        
        # Check completed tasks
        if task_id in self.task_history:
            return self.task_history[task_id].dict()
        
        # Check Redis if available
        if self.redis_client is not None:
            try:
                result_data: Optional[str] = await self.redis_client.get(f"orchestration_result:{task_id}")
                if result_data:
                    return json.loads(result_data)
            except Exception as e:
                logger.warning(f"Redis lookup failed: {e}")
        
        return None
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        uptime: float = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "orchestrator_status": "healthy",
            "uptime_seconds": uptime,
            "active_tasks": len(self.active_tasks),
            "performance_metrics": self.performance_metrics,
            "component_status": {
                "mcp_manager": await self.mcp_manager.get_health_status(),
                "workflow_engine": await self.workflow_engine.get_status(),
                "intelligent_router": await self.intelligent_router.get_status(),
                "conversation_manager": await self.conversation_manager.get_status()
            },
            "redis_connected": self.redis_client is not None,
            "circuit_breaker_status": self.circuit_breaker_state

    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info("[SHUTDOWN] Shutting down LangChain Master Orchestrator...")
        
        # Wait for active tasks to complete (with timeout)
        if self.active_tasks:
            logger.info(f"[SHUTDOWN] Waiting for {len(self.active_tasks)} active tasks...")
            await asyncio.sleep(5)  # Give tasks time to complete
        
        # Shutdown components
        if self.mcp_manager:
            await self.mcp_manager.shutdown()
        
        if self.workflow_engine:
            await self.workflow_engine.shutdown()
        
        if self.intelligent_router:
            await self.intelligent_router.shutdown()
        
        if self.conversation_manager:
            await self.conversation_manager.shutdown()
        
        # Close Redis connection if available
        if self.redis_client is not None:
            await self.redis_client.close()
        
        logger.info("[SHUTDOWN] LangChain Master Orchestrator shutdown complete")