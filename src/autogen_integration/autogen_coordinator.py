# -*- coding: utf-8 -*-
"""
AutoGen Coordinator for Flash Loan Arbitrage System

This module implements the main AutoGen coordinator that integrates with the
LangChain orchestrator for sophisticated multi-agent decision making.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import json
import logging
import uuid

from .agent_registry import AgentRegistry
from .conversation_orchestrator import ConversationOrchestrator
from .decision_engine import ConsensusDecisionEngine
from .mcp_bridge import MCPBridge
from .specialized_agents import FlashLoanAgentFactory
from autogen import GroupChat, GroupChatManager
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CoordinationMode(Enum):
    """Coordination modes for different scenarios"""
    ARBITRAGE_ANALYSIS = "arbitrage_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    EXECUTION_PLANNING = "execution_planning"
    STRATEGY_OPTIMIZATION = "strategy_optimization"
    EMERGENCY_RESPONSE = "emergency_response"


class ConversationStatus(Enum):
    """AutoGen conversation status"""
    INITIALIZING = "initializing"
    ACTIVE = "active" 
    CONSENSUS_REACHED = "consensus_reached"
    CONSENSUS_FAILED = "consensus_failed"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class AutoGenSession:
    """AutoGen conversation session data"""
    session_id: str
    mode: CoordinationMode
    participants: List[str]
    group_chat: Optional[GroupChat] = None
    manager: Optional[GroupChatManager] = None
    status: ConversationStatus = ConversationStatus.INITIALIZING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    consensus_result: Optional[Dict[str, Any]] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class AutoGenCoordinator:
    """
    Main AutoGen coordinator that orchestrates multi-agent conversations
    for flash loan arbitrage decision making.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.autogen_config = config.get("autogen", {})
        
        # Initialize components
        self.agent_factory = FlashLoanAgentFactory(config)
        self.conversation_orchestrator = ConversationOrchestrator(config)
        self.decision_engine = ConsensusDecisionEngine(config)
        self.mcp_bridge = MCPBridge(config)
        self.agent_registry = AgentRegistry(config)
        
        # Session management
        self.active_sessions: Dict[str, AutoGenSession] = {}
        self.session_history: Dict[str, AutoGenSession] = {}
        
        # Performance tracking
        self.metrics = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "avg_session_duration": 0.0,
            "avg_consensus_rounds": 0.0,
            "active_sessions": 0,
            "agent_performance": {}

        
        # Conversation templates
        self.conversation_templates = self._load_conversation_templates()
        
        # Circuit breaker for stability
        self.circuit_breaker = {
            "failure_count": 0,
            "last_failure": None,
            "is_open": False,
            "failure_threshold": self.config.get("circuit_breaker", {}).get("failure_threshold", 5)

        
        logger.info("[INIT] AutoGen Coordinator initialized")
    
    async def initialize(self):
        """Initialize the AutoGen coordinator"""
        try:
            # Initialize sub-components
            await self.agent_factory.initialize()
            await self.conversation_orchestrator.initialize()
            await self.decision_engine.initialize()
            await self.mcp_bridge.initialize()
            await self.agent_registry.initialize()
            
            # Validate AutoGen configuration
            await self._validate_autogen_config()
            
            logger.info("[OK] AutoGen Coordinator fully initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] AutoGen Coordinator initialization failed: {e}")
            raise
    
    async def coordinate_arbitrage_decision(
        self,
        opportunity_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
        consensus_algorithm: str = "weighted_consensus"
    ) -> Dict[str, Any]:
        """
        Coordinate multi-agent decision making for arbitrage opportunities
        
        Args:
            opportunity_data: Arbitrage opportunity details
            context: Additional context for decision making
            timeout: Session timeout in seconds
            consensus_algorithm: Algorithm for reaching consensus
            
        Returns:
            Decision result with consensus and execution plan
        """
        session_id = f"arb_{uuid.uuid4().hex[:8]}"
        
        try:
            # Check circuit breaker
            if self._is_circuit_breaker_open():
                return await self._handle_circuit_breaker_open(session_id, opportunity_data)
            
            # Create session
            session = await self._create_arbitrage_session(
                session_id, opportunity_data, context, timeout

            
            # Execute conversation
            result = await self._execute_arbitrage_conversation(session, consensus_algorithm)
            
            # Update circuit breaker on success
            self._reset_circuit_breaker()
            
            return result
            
        except Exception as e:
            # Update circuit breaker on failure
            self._increment_circuit_breaker()
            
            logger.error(f"[ERROR] Arbitrage coordination failed for {session_id}: {e}")
            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e),
                "consensus": {"approved": False, "reason": f"Coordination failed: {e}"},
                "timestamp": datetime.now().isoformat()

    
    async def coordinate_risk_assessment(
        self,
        trade_data: Dict[str, Any],
        market_context: Dict[str, Any],
        timeout: int = 180
    ) -> Dict[str, Any]:
        """
        Coordinate multi-agent risk assessment
        
        Args:
            trade_data: Trade parameters and data
            market_context: Market analysis context
            timeout: Session timeout in seconds
            
        Returns:
            Risk assessment result with recommendations
        """
        session_id = f"risk_{uuid.uuid4().hex[:8]}"
        
        try:
            # Create risk assessment session
            session = await self._create_risk_assessment_session(
                session_id, trade_data, market_context, timeout

            
            # Execute risk assessment conversation
            result = await self._execute_risk_assessment_conversation(session)
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Risk assessment coordination failed for {session_id}: {e}")
            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e),
                "risk_assessment": {"risk_level": "high", "reason": f"Assessment failed: {e}"},
                "timestamp": datetime.now().isoformat()

    
    async def coordinate_execution_planning(
        self,
        execution_context: Dict[str, Any],
        constraints: Dict[str, Any],
        timeout: int = 240
    ) -> Dict[str, Any]:
        """
        Coordinate execution planning with specialized agents
        
        Args:
            execution_context: Execution context and parameters
            constraints: Execution constraints and limits
            timeout: Session timeout in seconds
            
        Returns:
            Execution plan with optimized parameters
        """
        session_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        try:
            # Create execution planning session
            session = await self._create_execution_session(
                session_id, execution_context, constraints, timeout

            
            # Execute planning conversation
            result = await self._execute_execution_conversation(session)
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Execution planning coordination failed for {session_id}: {e}")
            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e),
                "execution_plan": {"approved": False, "reason": f"Planning failed: {e}"},
                "timestamp": datetime.now().isoformat()

    
    async def _create_arbitrage_session(
        self,
        session_id: str,
        opportunity_data: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        timeout: int
    ) -> AutoGenSession:
        """Create arbitrage decision session"""
        
        # Determine required agents based on opportunity complexity
        required_agents = await self._determine_required_agents(opportunity_data)
        
        # Create agents
        agents = []
        for agent_type in required_agents:
            agent = await self.agent_factory.create_agent(agent_type, session_id)
            agents.append(agent)
        
        # Create group chat
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=self.autogen_config.get("conversation_config", {}).get("max_rounds", 10),
            speaker_selection_method="auto"

        
        # Create manager
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=self._get_llm_config()

        
        # Create session
        session = AutoGenSession(
            session_id=session_id,
            mode=CoordinationMode.ARBITRAGE_ANALYSIS,
            participants=required_agents,
            group_chat=group_chat,
            manager=manager,
            start_time=datetime.now(),
            context={
                "opportunity_data": opportunity_data,
                "additional_context": context or {},
                "timeout": timeout


        
        # Register session
        self.active_sessions[session_id] = session
        self.metrics["active_sessions"] += 1
        
        # Register agents
        for agent_type, agent in zip(required_agents, agents):
            await self.agent_registry.register_agent(session_id, agent_type, agent)
        
        logger.info(f"[SESSION] Created arbitrage session {session_id} with agents: {required_agents}")
        
        return session
    
    async def _execute_arbitrage_conversation(
        self,
        session: AutoGenSession,
        consensus_algorithm: str
    ) -> Dict[str, Any]:
        """Execute arbitrage decision conversation"""
        session.status = ConversationStatus.ACTIVE
        
        try:
            # Prepare initial message
            initial_message = self._create_arbitrage_initial_message(session.context)
            
            # Start conversation with timeout
            conversation_task = asyncio.create_task(
                self._run_group_conversation(session, initial_message)

            
            # Wait with timeout
            timeout = session.context.get("timeout", 300)
            conversation_result = await asyncio.wait_for(conversation_task, timeout=timeout)
            
            # Extract conversation history
            session.conversation_history = self._extract_conversation_history(session.group_chat)
            
            # Apply consensus algorithm
            consensus = await self.decision_engine.apply_consensus_algorithm(
                consensus_algorithm,
                session.conversation_history,
                session.context

            
            # Update session
            session.status = ConversationStatus.CONSENSUS_REACHED if consensus.get("approved") else ConversationStatus.CONSENSUS_FAILED
            session.end_time = datetime.now()
            session.consensus_result = consensus
            
            # Calculate performance metrics
            session.performance_metrics = self._calculate_session_metrics(session)
            
            # Update global metrics
            self._update_session_metrics(session, "success")
            
            # Move to history
            self._finalize_session(session)
            
            logger.info(f"[OK] Arbitrage conversation completed for {session.session_id}")
            
            return {
                "session_id": session.session_id,
                "status": "completed",
                "mode": session.mode.value,
                "participants": session.participants,
                "conversation_rounds": len(session.conversation_history),
                "consensus": consensus,
                "execution_plan": consensus.get("execution_plan", {}),
                "performance_metrics": session.performance_metrics,
                "timestamp": datetime.now().isoformat()

            
        except asyncio.TimeoutError:
            session.status = ConversationStatus.TERMINATED
            session.end_time = datetime.now()
            self._update_session_metrics(session, "timeout")
            self._finalize_session(session)
            
            return {
                "session_id": session.session_id,
                "status": "timeout",
                "error": "Conversation timed out",
                "consensus": {"approved": False, "reason": "Timeout"},
                "timestamp": datetime.now().isoformat()

            
        except Exception:
            session.status = ConversationStatus.ERROR
            session.end_time = datetime.now()
            self._update_session_metrics(session, "error")
            self._finalize_session(session)
            
            raise
    
    async def _create_risk_assessment_session(
        self,
        session_id: str,
        trade_data: Dict[str, Any],
        market_context: Dict[str, Any],
        timeout: int
    ) -> AutoGenSession:
        """Create risk assessment session"""
        
        # Risk assessment specific agents
        required_agents = ["risk_analyst", "market_analyst", "compliance_validator"]
        
        # Create agents
        agents = []
        for agent_type in required_agents:
            agent = await self.agent_factory.create_agent(agent_type, session_id)
            agents.append(agent)
        
        # Create group chat
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=8,  # Risk assessment is more focused
            speaker_selection_method="round_robin"

        
        # Create manager
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=self._get_llm_config()

        
        # Create session
        session = AutoGenSession(
            session_id=session_id,
            mode=CoordinationMode.RISK_ASSESSMENT,
            participants=required_agents,
            group_chat=group_chat,
            manager=manager,
            start_time=datetime.now(),
            context={
                "trade_data": trade_data,
                "market_context": market_context,
                "timeout": timeout


        
        # Register session
        self.active_sessions[session_id] = session
        self.metrics["active_sessions"] += 1
        
        return session
    
    async def _execute_risk_assessment_conversation(self, session: AutoGenSession) -> Dict[str, Any]:
        """Execute risk assessment conversation"""
        session.status = ConversationStatus.ACTIVE
        
        try:
            # Prepare risk assessment message
            initial_message = self._create_risk_assessment_initial_message(session.context)
            
            # Start conversation
            conversation_task = asyncio.create_task(
                self._run_group_conversation(session, initial_message)

            
            # Wait with timeout
            timeout = session.context.get("timeout", 180)
            await asyncio.wait_for(conversation_task, timeout=timeout)
            
            # Extract and analyze conversation
            session.conversation_history = self._extract_conversation_history(session.group_chat)
            
            # Apply risk-specific consensus
            risk_consensus = await self.decision_engine.apply_risk_consensus(
                session.conversation_history,
                session.context

            
            # Update session
            session.status = ConversationStatus.CONSENSUS_REACHED
            session.end_time = datetime.now()
            session.consensus_result = risk_consensus
            
            # Calculate metrics
            session.performance_metrics = self._calculate_session_metrics(session)
            self._update_session_metrics(session, "success")
            self._finalize_session(session)
            
            return {
                "session_id": session.session_id,
                "status": "completed",
                "mode": session.mode.value,
                "participants": session.participants,
                "conversation_rounds": len(session.conversation_history),
                "risk_assessment": risk_consensus,
                "performance_metrics": session.performance_metrics,
                "timestamp": datetime.now().isoformat()

            
        except Exception:
            session.status = ConversationStatus.ERROR
            session.end_time = datetime.now()
            self._update_session_metrics(session, "error")
            self._finalize_session(session)
            
            raise
    
    async def _create_execution_session(
        self,
        session_id: str,
        execution_context: Dict[str, Any],
        constraints: Dict[str, Any],
        timeout: int
    ) -> AutoGenSession:
        """Create execution planning session"""
        
        # Execution planning specific agents
        required_agents = ["execution_specialist", "gas_optimizer", "timing_analyst"]
        
        # Create agents
        agents = []
        for agent_type in required_agents:
            agent = await self.agent_factory.create_agent(agent_type, session_id)
            agents.append(agent)
        
        # Create group chat with execution focus
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=6,  # Execution planning is more direct
            speaker_selection_method="auto"

        
        # Create manager
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=self._get_llm_config()

        
        # Create session
        session = AutoGenSession(
            session_id=session_id,
            mode=CoordinationMode.EXECUTION_PLANNING,
            participants=required_agents,
            group_chat=group_chat,
            manager=manager,
            start_time=datetime.now(),
            context={
                "execution_context": execution_context,
                "constraints": constraints,
                "timeout": timeout


        
        # Register session
        self.active_sessions[session_id] = session
        self.metrics["active_sessions"] += 1
        
        return session
    
    async def _execute_execution_conversation(self, session: AutoGenSession) -> Dict[str, Any]:
        """Execute execution planning conversation"""
        session.status = ConversationStatus.ACTIVE
        
        try:
            # Prepare execution planning message
            initial_message = self._create_execution_initial_message(session.context)
            
            # Start conversation
            conversation_task = asyncio.create_task(
                self._run_group_conversation(session, initial_message)

            
            # Wait with timeout
            timeout = session.context.get("timeout", 240)
            await asyncio.wait_for(conversation_task, timeout=timeout)
            
            # Extract and analyze conversation
            session.conversation_history = self._extract_conversation_history(session.group_chat)
            
            # Apply execution-specific consensus
            execution_consensus = await self.decision_engine.apply_execution_consensus(
                session.conversation_history,
                session.context

            
            # Update session
            session.status = ConversationStatus.CONSENSUS_REACHED
            session.end_time = datetime.now()
            session.consensus_result = execution_consensus
            
            # Calculate metrics
            session.performance_metrics = self._calculate_session_metrics(session)
            self._update_session_metrics(session, "success")
            self._finalize_session(session)
            
            return {
                "session_id": session.session_id,
                "status": "completed",
                "mode": session.mode.value,
                "participants": session.participants,
                "conversation_rounds": len(session.conversation_history),
                "execution_plan": execution_consensus,
                "performance_metrics": session.performance_metrics,
                "timestamp": datetime.now().isoformat()

            
        except Exception:
            session.status = ConversationStatus.ERROR
            session.end_time = datetime.now()
            self._update_session_metrics(session, "error")
            self._finalize_session(session)
            
            raise
    
    async def _run_group_conversation(self, session: AutoGenSession, initial_message: str):
        """Run the AutoGen group conversation"""
        try:
            # Start the conversation
            user_proxy = session.group_chat.agents[0]  # Use first agent as proxy
            
            # Initiate conversation
            await user_proxy.a_initiate_chat(
                session.manager,
                message=initial_message,
                clear_history=True

            
        except Exception as e:
            logger.error(f"[ERROR] Group conversation failed for {session.session_id}: {e}")
            raise
    
    def _extract_conversation_history(self, group_chat: GroupChat) -> List[Dict[str, Any]]:
        """Extract conversation history from GroupChat"""
        history = []
        
        for msg in group_chat.messages:
            history.append({
                "role": msg.get("role", "unknown"),
                "name": msg.get("name", "unknown"),
                "content": msg.get("content", ""),
                "timestamp": datetime.now().isoformat()

        
        return history
    
    def _create_arbitrage_initial_message(self, context: Dict[str, Any]) -> str:
        """Create initial message for arbitrage decision"""
        opportunity = context.get("opportunity_data", {})
        
        return f"""
        ARBITRAGE OPPORTUNITY ANALYSIS

        We need to make a decision on the following arbitrage opportunity:

        Token Pair: {opportunity.get('token_pair', 'Unknown')}
        Potential Profit: {opportunity.get('profit_estimate', 'Unknown')} ETH
        DEX Route: {opportunity.get('dex_route', 'Unknown')}
        Gas Estimate: {opportunity.get('gas_estimate', 'Unknown')} gwei
        
        Market Conditions: {opportunity.get('market_conditions', 'Unknown')}
        Liquidity: {opportunity.get('liquidity_info', 'Unknown')}
        
        Please analyze this opportunity and provide your recommendations.
        Consider:
        1. Profit potential vs. risks
        2. Market conditions and timing
        3. Execution feasibility
        4. Gas costs and optimization
        5. Safety and compliance factors
        
        After discussion, we need to reach a consensus on whether to proceed.
        """
    
    def _create_risk_assessment_initial_message(self, context: Dict[str, Any]) -> str:
        """Create initial message for risk assessment"""
        trade_data = context.get("trade_data", {})
        market_context = context.get("market_context", {})
        
        return f"""
        RISK ASSESSMENT REQUEST

        Please conduct a comprehensive risk assessment for the following trade:

        Trade Parameters:
        {json.dumps(trade_data, indent=2)}

        Market Context:
        {json.dumps(market_context, indent=2)}

        Focus Areas:
        1. Liquidity Risk - Assess available liquidity and slippage potential
        2. Market Risk - Volatility, price impact, timing risks
        3. Technical Risk - Smart contract risks, gas price volatility
        4. Operational Risk - Execution risks, MEV protection
        5. Regulatory Risk - Compliance considerations

        Provide risk scores (0-1), mitigation strategies, and recommendations.
        """
    
    def _create_execution_initial_message(self, context: Dict[str, Any]) -> str:
        """Create initial message for execution planning"""
        execution_context = context.get("execution_context", {})
        constraints = context.get("constraints", {})
        
        return f"""
        EXECUTION PLANNING SESSION

        Plan the execution for the approved arbitrage opportunity:

        Execution Context:
        {json.dumps(execution_context, indent=2)}

        Constraints:
        {json.dumps(constraints, indent=2)}

        Planning Requirements:
        1. Optimal execution sequence and timing
        2. Gas optimization strategy
        3. Slippage protection measures
        4. MEV protection implementation
        5. Fallback and recovery procedures
        6. Performance monitoring setup

        Develop a detailed execution plan with specific parameters.
        """
    
    async def _determine_required_agents(self, opportunity_data: Dict[str, Any]) -> List[str]:
        """Determine which agents are required based on opportunity complexity"""
        base_agents = ["arbitrage_coordinator", "market_analyst", "risk_analyst"]
        
        # Add specialized agents based on opportunity characteristics
        if opportunity_data.get("complexity", "medium") == "high":
            base_agents.append("execution_specialist")
        
        if opportunity_data.get("gas_sensitivity", False):
            base_agents.append("gas_optimizer")
        
        if opportunity_data.get("multi_chain", False):
            base_agents.append("bridge_specialist")
        
        return base_agents
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for AutoGen agents"""
        return {
            "model": self.autogen_config.get("model", "gpt-4"),
            "api_key": self.autogen_config.get("api_key"),
            "temperature": self.autogen_config.get("temperature", 0.1),
            "timeout": self.autogen_config.get("timeout", 60)

    
    def _calculate_session_metrics(self, session: AutoGenSession) -> Dict[str, Any]:
        """Calculate performance metrics for session"""
        if not session.start_time or not session.end_time:
            return {}
        
        duration = (session.end_time - session.start_time).total_seconds()
        
        return {
            "duration_seconds": duration,
            "conversation_rounds": len(session.conversation_history),
            "agents_count": len(session.participants),
            "consensus_reached": session.status == ConversationStatus.CONSENSUS_REACHED,
            "messages_per_round": len(session.conversation_history) / max(len(session.participants), 1)

    
    def _update_session_metrics(self, session: AutoGenSession, status: str):
        """Update global session metrics"""
        self.metrics["total_sessions"] += 1
        self.metrics["active_sessions"] -= 1
        
        if status == "success":
            self.metrics["successful_sessions"] += 1
        else:
            self.metrics["failed_sessions"] += 1
        
        # Update averages
        if session.performance_metrics:
            duration = session.performance_metrics.get("duration_seconds", 0)
            rounds = session.performance_metrics.get("conversation_rounds", 0)
            
            total = self.metrics["total_sessions"]
            
            # Update average duration
            current_avg_duration = self.metrics["avg_session_duration"]
            self.metrics["avg_session_duration"] = (
                (current_avg_duration * (total - 1) + duration) / total

            
            # Update average rounds
            current_avg_rounds = self.metrics["avg_consensus_rounds"]
            self.metrics["avg_consensus_rounds"] = (
                (current_avg_rounds * (total - 1) + rounds) / total

    
    def _finalize_session(self, session: AutoGenSession):
        """Move session to history and cleanup"""
        # Move to history
        self.session_history[session.session_id] = session
        
        # Remove from active sessions
        if session.session_id in self.active_sessions:
            del self.active_sessions[session.session_id]
        
        # Cleanup agents
        asyncio.create_task(
            self.agent_registry.cleanup_session_agents(session.session_id)

    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_breaker["is_open"]:
            return False
        
        # Check if recovery time has passed
        if self.circuit_breaker["last_failure"]:
            recovery_timeout = self.config.get("circuit_breaker", {}).get("recovery_timeout", 60)
            time_since_failure = (datetime.now() - self.circuit_breaker["last_failure"]).total_seconds()
            
            if time_since_failure > recovery_timeout:
                self.circuit_breaker["is_open"] = False
                self.circuit_breaker["failure_count"] = 0
                logger.info("[CIRCUIT_BREAKER] Circuit breaker closed - recovery timeout reached")
        
        return self.circuit_breaker["is_open"]
    
    def _increment_circuit_breaker(self):
        """Increment circuit breaker failure count"""
        self.circuit_breaker["failure_count"] += 1
        self.circuit_breaker["last_failure"] = datetime.now()
        
        if self.circuit_breaker["failure_count"] >= self.circuit_breaker["failure_threshold"]:
            self.circuit_breaker["is_open"] = True
            logger.warning(f"[CIRCUIT_BREAKER] Circuit breaker opened after {self.circuit_breaker['failure_count']} failures")
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker on successful operation"""
        if self.circuit_breaker["failure_count"] > 0:
            self.circuit_breaker["failure_count"] = 0
            logger.info("[CIRCUIT_BREAKER] Circuit breaker reset after successful operation")
    
    async def _handle_circuit_breaker_open(self, session_id: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests when circuit breaker is open"""
        logger.warning(f"[CIRCUIT_BREAKER] Request blocked for {session_id} - circuit breaker is open")
        
        return {
            "session_id": session_id,
            "status": "circuit_breaker_open",
            "error": "AutoGen coordination temporarily unavailable",
            "consensus": {
                "approved": False,
                "reason": "Service temporarily unavailable - please try again later"
            },
            "timestamp": datetime.now().isoformat()

    
    def _load_conversation_templates(self) -> Dict[str, str]:
        """Load conversation templates for different scenarios"""
        return {
            "arbitrage_analysis": "Analyze arbitrage opportunity and provide recommendation",
            "risk_assessment": "Conduct comprehensive risk assessment",
            "execution_planning": "Develop optimal execution plan",
            "strategy_optimization": "Optimize arbitrage strategy parameters",
            "emergency_response": "Handle emergency situation with immediate action plan"

    
    async def _validate_autogen_config(self):
        """Validate AutoGen configuration"""
        required_config = ["model", "api_key"]
        
        for key in required_config:
            if not self.autogen_config.get(key):
                logger.warning(f"[CONFIG] Missing AutoGen config: {key}")
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific session"""
        # Check active sessions
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "status": session.status.value,
                "mode": session.mode.value,
                "participants": session.participants,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "conversation_rounds": len(session.conversation_history),
                "is_active": True

        
        # Check history
        if session_id in self.session_history:
            session = self.session_history[session_id]
            return {
                "session_id": session_id,
                "status": session.status.value,
                "mode": session.mode.value,
                "participants": session.participants,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "conversation_rounds": len(session.conversation_history),
                "consensus_result": session.consensus_result,
                "performance_metrics": session.performance_metrics,
                "is_active": False

        
        return None
    
    async def get_coordinator_status(self) -> Dict[str, Any]:
        """Get comprehensive coordinator status"""
        return {
            "coordinator_status": "healthy",
            "active_sessions": len(self.active_sessions),
            "total_sessions": self.metrics["total_sessions"],
            "performance_metrics": self.metrics,
            "circuit_breaker": self.circuit_breaker,
            "component_status": {
                "agent_factory": await self.agent_factory.get_status(),
                "conversation_orchestrator": await self.conversation_orchestrator.get_status(),
                "decision_engine": await self.decision_engine.get_status(),
                "mcp_bridge": await self.mcp_bridge.get_status(),
                "agent_registry": await self.agent_registry.get_status()


    
    async def shutdown(self):
        """Graceful shutdown of coordinator"""
        logger.info("[SHUTDOWN] Shutting down AutoGen Coordinator...")
        
        # Complete active sessions
        if self.active_sessions:
            logger.info(f"[SHUTDOWN] Waiting for {len(self.active_sessions)} active sessions...")
            await asyncio.sleep(5)  # Grace period
        
        # Shutdown components
        await self.agent_factory.shutdown()
        await self.conversation_orchestrator.shutdown()
        await self.decision_engine.shutdown()
        await self.mcp_bridge.shutdown()
        await self.agent_registry.shutdown()
        
        logger.info("[SHUTDOWN] AutoGen Coordinator shutdown complete")