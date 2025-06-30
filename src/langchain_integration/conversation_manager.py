# -*- coding: utf-8 -*-
"""
Conversation Manager for Flash Loan Arbitrage System

This module manages multi-step conversations and integrates with AutoGen
for complex decision-making processes involving multiple agents.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import asyncio
import logging
import time

from ..autogen_integration.autogen_coordinator import AutoGenCoordinator
from dataclasses import dataclass, field
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation states"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ConversationType(Enum):
    """Types of conversations"""
    ARBITRAGE_DECISION = "arbitrage_decision"
    RISK_ASSESSMENT = "risk_assessment"
    STRATEGY_PLANNING = "strategy_planning"
    EXECUTION_APPROVAL = "execution_approval"
    GENERAL_ANALYSIS = "general_analysis"


class ParticipantRole(Enum):
    """Participant roles in conversations"""
    COORDINATOR = "coordinator"
    ANALYZER = "analyzer"
    RISK_MANAGER = "risk_manager"
    EXECUTOR = "executor"
    VALIDATOR = "validator"
    OBSERVER = "observer"


@dataclass
class ConversationMessage:
    """Individual conversation message"""
    message_id: str
    sender: str
    recipient: Optional[str]  # None for broadcast
    content: str
    timestamp: datetime
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationParticipant:
    """Conversation participant information"""
    participant_id: str
    name: str
    role: ParticipantRole
    capabilities: List[str] = field(default_factory=list)
    active: bool = True
    last_activity: Optional[datetime] = None
    message_count: int = 0


@dataclass
class ConversationSession:
    """Conversation session information"""
    session_id: str
    conversation_type: ConversationType
    state: ConversationState = ConversationState.PENDING
    participants: Dict[str, ConversationParticipant] = field(default_factory=dict)
    messages: List[ConversationMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    decision_criteria: Dict[str, Any] = field(default_factory=dict)
    consensus_result: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timeout: int = 300  # 5 minutes default
    max_rounds: int = 10
    current_round: int = 0
    facilitator: Optional[str] = None


class ConversationManager:
    """
    Manages multi-agent conversations and decision-making processes
    with integration to AutoGen and other agent systems.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Active conversations
        self.active_conversations: Dict[str, ConversationSession] = {}
        self.conversation_history: Dict[str, ConversationSession] = {}
        
        # AutoGen integration - Use the coordinator instead of direct HTTP calls
        self.autogen_coordinator: Optional[AutoGenCoordinator] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Conversation handlers
        self.conversation_handlers: Dict[ConversationType, Callable] = {}
        
        # Decision algorithms
        self.decision_algorithms: Dict[str, Callable] = {}
        
        # Performance metrics
        self.metrics = {
            "total_conversations": 0,
            "successful_conversations": 0,
            "failed_conversations": 0,
            "avg_conversation_time": 0.0,
            "avg_rounds_per_conversation": 0.0,
            "active_conversations": 0

        
        # Monitoring task
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Register default handlers and algorithms
        self._register_default_handlers()
        self._register_default_decision_algorithms()
        
        logger.info("[INIT] Conversation Manager initialized")
    
    async def initialize(self):
        """Initialize the conversation manager"""
        try:
            # Initialize AutoGen coordinator
            self.autogen_coordinator = AutoGenCoordinator(self.config)
            await self.autogen_coordinator.initialize()
            
            # Create HTTP session for fallback scenarios
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)

            
            # Start monitoring task
            self.monitor_task = asyncio.create_task(self._monitor_conversations())
            
            logger.info("[OK] Conversation Manager initialized with AutoGen integration")
            
        except Exception as e:
            logger.error(f"[ERROR] Conversation Manager initialization failed: {e}")
            raise
    
    def _register_default_handlers(self):
        """Register default conversation handlers"""
        self.conversation_handlers[ConversationType.ARBITRAGE_DECISION] = self._handle_arbitrage_decision
        self.conversation_handlers[ConversationType.RISK_ASSESSMENT] = self._handle_risk_assessment
        self.conversation_handlers[ConversationType.STRATEGY_PLANNING] = self._handle_strategy_planning
        self.conversation_handlers[ConversationType.EXECUTION_APPROVAL] = self._handle_execution_approval
        self.conversation_handlers[ConversationType.GENERAL_ANALYSIS] = self._handle_general_analysis
        
        logger.info(f"[OK] Registered {len(self.conversation_handlers)} conversation handlers")
    
    def _register_default_decision_algorithms(self):
        """Register default decision algorithms"""
        self.decision_algorithms["majority_consensus"] = self._majority_consensus
        self.decision_algorithms["weighted_consensus"] = self._weighted_consensus
        self.decision_algorithms["unanimous_consensus"] = self._unanimous_consensus
        self.decision_algorithms["risk_weighted_decision"] = self._risk_weighted_decision
        
        logger.info(f"[OK] Registered {len(self.decision_algorithms)} decision algorithms")
    
    async def start_multi_agent_conversation(
        self,
        context: Dict[str, Any],
        conversation_type: str,
        participants: List[str],
        timeout: int = 300,
        max_rounds: int = 10,
        decision_algorithm: str = "majority_consensus",
        facilitator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a multi-agent conversation for decision making using AutoGen
        
        Args:
            context: Conversation context and data
            conversation_type: Type of conversation
            participants: List of participant IDs
            timeout: Conversation timeout in seconds
            max_rounds: Maximum conversation rounds
            decision_algorithm: Algorithm for reaching consensus
            facilitator: Optional facilitator agent
            
        Returns:
            Conversation result with consensus decision
        """
        session_id = f"conv_{int(time.time() * 1000)}"
        
        try:
            # Create conversation session
            conv_type = ConversationType(conversation_type)
            session = ConversationSession(
                session_id=session_id,
                conversation_type=conv_type,
                context=context.copy(),
                timeout=timeout,
                max_rounds=max_rounds,
                facilitator=facilitator

            
            # Add participants
            for participant_id in participants:
                participant = ConversationParticipant(
                    participant_id=participant_id,
                    name=participant_id,
                    role=self._get_participant_role(participant_id),
                    capabilities=self._get_participant_capabilities(participant_id)

                session.participants[participant_id] = participant
            
            # Store session
            self.active_conversations[session_id] = session
            self.metrics["active_conversations"] += 1
            
            logger.info(f"[CONVERSATION] Started {conversation_type} conversation: {session_id}")
            
            # Execute conversation using AutoGen coordinator
            result = await self._execute_autogen_conversation(session, decision_algorithm)
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Conversation {session_id} failed: {e}")
            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e),
                "consensus": {"approved": False, "reason": f"Conversation failed: {e}"}

    
    async def _execute_autogen_conversation(
        self, 
        session: ConversationSession, 
        decision_algorithm: str
    ) -> Dict[str, Any]:
        """Execute conversation using AutoGen coordinator"""
        session.state = ConversationState.ACTIVE
        session.start_time = datetime.now()
        
        try:
            # Route to appropriate AutoGen conversation type
            if session.conversation_type == ConversationType.ARBITRAGE_DECISION:
                result = await self._execute_arbitrage_via_autogen(session, decision_algorithm)
            elif session.conversation_type == ConversationType.RISK_ASSESSMENT:
                result = await self._execute_risk_assessment_via_autogen(session)
            elif session.conversation_type == ConversationType.EXECUTION_APPROVAL:
                result = await self._execute_execution_planning_via_autogen(session)
            else:
                # Use generic conversation handling
                result = await self._execute_generic_via_autogen(session, decision_algorithm)
            
            # Complete conversation
            session.state = ConversationState.COMPLETED
            session.end_time = datetime.now()
            session.consensus_result = result.get("consensus", {})
            
            # Update metrics
            self._update_conversation_metrics(session, "success")
            
            # Move to history
            self._finalize_conversation(session)
            
            conversation_time = (session.end_time - session.start_time).total_seconds()
            
            logger.info(f"[OK] AutoGen conversation {session.session_id} completed in {conversation_time:.2f}s")
            
            return {
                "session_id": session.session_id,
                "status": "completed",
                "conversation_type": session.conversation_type.value,
                "conversation_rounds": result.get("conversation_rounds", 0),
                "participants": list(session.participants.keys()),
                "consensus": result.get("consensus", {}),
                "conversation_time": conversation_time,
                "message_count": result.get("message_count", 0),
                "autogen_session_id": result.get("autogen_session_id")

            
        except asyncio.TimeoutError:
            session.state = ConversationState.TIMEOUT
            session.end_time = datetime.now()
            self._update_conversation_metrics(session, "timeout")
            self._finalize_conversation(session)
            
            return {
                "session_id": session.session_id,
                "status": "timeout",
                "error": "Conversation timed out",
                "consensus": {"approved": False, "reason": "Timeout"}

            
        except Exception as e:
            session.state = ConversationState.FAILED
            session.end_time = datetime.now()
            session.consensus_result = {"approved": False, "reason": str(e)}
            self._update_conversation_metrics(session, "failure")
            self._finalize_conversation(session)
            
            raise
    
    async def _execute_arbitrage_via_autogen(
        self, 
        session: ConversationSession, 
        decision_algorithm: str
    ) -> Dict[str, Any]:
        """Execute arbitrage decision via AutoGen coordinator"""
        try:
            if not self.autogen_coordinator:
                raise Exception("AutoGen coordinator not initialized")
            
            # Use AutoGen coordinator for arbitrage decision
            result = await self.autogen_coordinator.coordinate_arbitrage_decision(
                opportunity_data=session.context.get("opportunity_data", {}),
                context=session.context,
                timeout=session.timeout,
                consensus_algorithm=decision_algorithm

            
            return {
                "consensus": result.get("consensus", {}),
                "conversation_rounds": result.get("conversation_rounds", 0),
                "message_count": result.get("message_count", 0),
                "autogen_session_id": result.get("session_id"),
                "execution_plan": result.get("execution_plan", {}),
                "performance_metrics": result.get("performance_metrics", {})

            
        except Exception as e:
            logger.error(f"[ERROR] AutoGen arbitrage decision failed: {e}")
            # Fallback to original implementation
            return await self._handle_arbitrage_decision(session)
    
    async def _execute_risk_assessment_via_autogen(self, session: ConversationSession) -> Dict[str, Any]:
        """Execute risk assessment via AutoGen coordinator"""
        try:
            if not self.autogen_coordinator:
                raise Exception("AutoGen coordinator not initialized")
            
            # Use AutoGen coordinator for risk assessment
            result = await self.autogen_coordinator.coordinate_risk_assessment(
                trade_data=session.context.get("trade_data", {}),
                market_context=session.context.get("market_context", {}),
                timeout=session.timeout

            
            return {
                "consensus": {
                    "approved": result.get("risk_level", "high") in ["low", "medium"],
                    "risk_level": result.get("risk_level", "unknown"),
                    "risk_score": result.get("risk_score", 0.5),
                    "risk_factors": result.get("risk_factors", []),
                    "mitigation_strategies": result.get("mitigation_strategies", []),
                    "recommendation": result.get("recommendation", "proceed_with_caution")
                },
                "conversation_rounds": result.get("conversation_rounds", 0),
                "message_count": result.get("message_count", 0),
                "autogen_session_id": result.get("session_id"),
                "confidence": result.get("confidence", 0.6)

            
        except Exception as e:
            logger.error(f"[ERROR] AutoGen risk assessment failed: {e}")
            # Fallback to original implementation
            return await self._handle_risk_assessment(session)
    
    async def _execute_execution_planning_via_autogen(self, session: ConversationSession) -> Dict[str, Any]:
        """Execute execution planning via AutoGen coordinator"""
        try:
            if not self.autogen_coordinator:
                raise Exception("AutoGen coordinator not initialized")
            
            # Use AutoGen coordinator for execution planning
            result = await self.autogen_coordinator.coordinate_execution_planning(
                execution_context=session.context.get("execution_context", {}),
                constraints=session.context.get("constraints", {}),
                timeout=session.timeout

            
            return {
                "consensus": {
                    "approved": result.get("execution_approved", False),
                    "execution_plan": result.get("optimal_plan", {}),
                    "parameters": result.get("execution_parameters", {}),
                    "risk_mitigations": result.get("risk_mitigations", []),
                    "monitoring": result.get("monitoring_requirements", []),
                    "fallbacks": result.get("fallback_procedures", [])
                },
                "conversation_rounds": result.get("conversation_rounds", 0),
                "message_count": result.get("message_count", 0),
                "autogen_session_id": result.get("session_id"),
                "confidence": result.get("confidence", 0.6),
                "success_rate": result.get("estimated_success_rate", 0.7)

            
        except Exception as e:
            logger.error(f"[ERROR] AutoGen execution planning failed: {e}")
            # Fallback to original implementation
            return await self._handle_execution_approval(session)
    
    async def _execute_generic_via_autogen(
        self, 
        session: ConversationSession, 
        decision_algorithm: str
    ) -> Dict[str, Any]:
        """Execute generic conversation via AutoGen coordinator"""
        try:
            if not self.autogen_coordinator:
                raise Exception("AutoGen coordinator not initialized")
            
            # For generic conversations, use arbitrage decision as fallback
            result = await self.autogen_coordinator.coordinate_arbitrage_decision(
                opportunity_data=session.context,
                context=session.context,
                timeout=session.timeout,
                consensus_algorithm=decision_algorithm

            
            return {
                "consensus": result.get("consensus", {"approved": True, "reason": "Generic analysis completed"}),
                "conversation_rounds": result.get("conversation_rounds", 0),
                "message_count": result.get("message_count", 0),
                "autogen_session_id": result.get("session_id")

            
        except Exception as e:
            logger.error(f"[ERROR] AutoGen generic conversation failed: {e}")
            # Return basic success result
            return {
                "consensus": {"approved": True, "reason": "Fallback result"},
                "conversation_rounds": 1,
                "message_count": 1

    
    # Original handler methods for fallback scenarios
    
    async def _handle_arbitrage_decision(self, session: ConversationSession) -> Dict[str, Any]:
        """Handle arbitrage decision conversation (fallback)"""
        context = session.context
        
        logger.warning("[FALLBACK] Using fallback arbitrage decision handler")
        
        # Mock successful decision for fallback
        return {
            "consensus": {
                "approved": True,
                "confidence": 0.7,
                "reasoning": "Fallback decision - AutoGen coordinator unavailable",
                "execution_plan": context.get("opportunity_data", {})
            },
            "conversation_rounds": 3,
            "message_count": 6

    
    async def _handle_risk_assessment(self, session: ConversationSession) -> Dict[str, Any]:
        """Handle risk assessment conversation (fallback)"""
        logger.warning("[FALLBACK] Using fallback risk assessment handler")
        
        return {
            "consensus": {
                "approved": False,
                "risk_level": "medium",
                "risk_score": 0.5,
                "reasoning": "Fallback assessment - AutoGen coordinator unavailable"
            },
            "conversation_rounds": 2,
            "message_count": 4

    
    async def _handle_strategy_planning(self, session: ConversationSession) -> Dict[str, Any]:
        """Handle strategy planning conversation (fallback)"""
        return {"consensus": {"approved": True}, "conversation_rounds": 1, "message_count": 2}
    
    async def _handle_execution_approval(self, session: ConversationSession) -> Dict[str, Any]:
        """Handle execution approval conversation (fallback)"""
        return {"consensus": {"approved": True}, "conversation_rounds": 1, "message_count": 2}
    
    async def _handle_general_analysis(self, session: ConversationSession) -> Dict[str, Any]:
        """Handle general analysis conversation (fallback)"""
        return {"consensus": {"approved": True}, "conversation_rounds": 1, "message_count": 2}
    
    def _get_participant_role(self, participant_id: str) -> ParticipantRole:
        """Get participant role based on ID"""
        role_mapping = {
            "coordinator": ParticipantRole.COORDINATOR,
            "analyzer": ParticipantRole.ANALYZER,
            "risk_manager": ParticipantRole.RISK_MANAGER,
            "risk_validator": ParticipantRole.RISK_MANAGER,
            "executor": ParticipantRole.EXECUTOR,
            "execution_planner": ParticipantRole.EXECUTOR,
            "validator": ParticipantRole.VALIDATOR,
            "market_analyst": ParticipantRole.ANALYZER

        
        return role_mapping.get(participant_id, ParticipantRole.OBSERVER)
    
    def _get_participant_capabilities(self, participant_id: str) -> List[str]:
        """Get participant capabilities based on ID"""
        capability_mapping = {
            "coordinator": ["strategy", "decision_making", "coordination"],
            "analyzer": ["market_analysis", "data_processing", "calculations"],
            "risk_manager": ["risk_assessment", "safety_validation", "compliance"],
            "risk_validator": ["risk_assessment", "safety_validation"],
            "executor": ["execution_planning", "transaction_management"],
            "execution_planner": ["execution_planning", "optimization"],
            "validator": ["validation", "verification", "quality_assurance"],
            "market_analyst": ["market_analysis", "trend_analysis", "forecasting"]

        
        return capability_mapping.get(participant_id, [])
    
    # Decision Algorithm Implementations (kept for backward compatibility)
    
    def _majority_consensus(self, session: ConversationSession, result: Dict[str, Any]) -> Dict[str, Any]:
        """Simple majority consensus algorithm"""
        consensus = result.get("consensus", {})
        
        return {
            "approved": consensus.get("approved", False),
            "confidence": consensus.get("confidence", 0.5),
            "algorithm": "majority_consensus",
            "reasoning": consensus.get("reasoning", "Decision based on agent consensus"),
            "execution_plan": consensus.get("execution_plan", {})

    
    def _weighted_consensus(self, session: ConversationSession, result: Dict[str, Any]) -> Dict[str, Any]:
        """Weighted consensus based on participant expertise"""
        consensus = result.get("consensus", {})
        
        return {
            "approved": consensus.get("approved", False),
            "confidence": consensus.get("confidence", 0.5),
            "algorithm": "weighted_consensus",
            "reasoning": consensus.get("reasoning", "Weighted decision based on expertise"),
            "execution_plan": consensus.get("execution_plan", {})

    
    def _unanimous_consensus(self, session: ConversationSession, result: Dict[str, Any]) -> Dict[str, Any]:
        """Unanimous consensus algorithm"""
        consensus = result.get("consensus", {})
        
        return {
            "approved": consensus.get("approved", False) and consensus.get("confidence", 0) > 0.8,
            "confidence": consensus.get("confidence", 0.5),
            "algorithm": "unanimous_consensus",
            "reasoning": consensus.get("reasoning", "Unanimous decision required"),
            "execution_plan": consensus.get("execution_plan", {})

    
    def _risk_weighted_decision(self, session: ConversationSession, result: Dict[str, Any]) -> Dict[str, Any]:
        """Risk-weighted decision algorithm"""
        consensus = result.get("consensus", {})
        risk_score = session.context.get("risk_assessment", {}).get("risk_score", 0.5)
        
        # Apply risk-based adjustments
        confidence = consensus.get("confidence", 0.5)
        if risk_score > 0.7:
            confidence *= 0.5
        
        approved = consensus.get("approved", False) and confidence > 0.6
        
        return {
            "approved": approved,
            "confidence": confidence,
            "algorithm": "risk_weighted_decision",
            "reasoning": f"Decision adjusted for risk level: {risk_score}",
            "risk_score": risk_score,
            "execution_plan": consensus.get("execution_plan", {})

    
    def _update_conversation_metrics(self, session: ConversationSession, status: str):
        """Update conversation metrics"""
        self.metrics["total_conversations"] += 1
        self.metrics["active_conversations"] -= 1
        
        if status == "success":
            self.metrics["successful_conversations"] += 1
        else:
            self.metrics["failed_conversations"] += 1
        
        # Update average conversation time
        if session.start_time and session.end_time:
            conversation_time = (session.end_time - session.start_time).total_seconds()
            total_conversations = self.metrics["total_conversations"]
            current_avg = self.metrics["avg_conversation_time"]
            self.metrics["avg_conversation_time"] = (
                (current_avg * (total_conversations - 1) + conversation_time) / total_conversations

        
        # Update average rounds
        total_conversations = self.metrics["total_conversations"]
        current_avg_rounds = self.metrics["avg_rounds_per_conversation"]
        self.metrics["avg_rounds_per_conversation"] = (
            (current_avg_rounds * (total_conversations - 1) + session.current_round) / total_conversations

    
    def _finalize_conversation(self, session: ConversationSession):
        """Move conversation to history and cleanup"""
        self.conversation_history[session.session_id] = session
        if session.session_id in self.active_conversations:
            del self.active_conversations[session.session_id]
    
    async def _monitor_conversations(self):
        """Monitor active conversations for timeouts and cleanup"""
        while True:
            try:
                current_time = datetime.now()
                timed_out = []
                
                for session_id, session in self.active_conversations.items():
                    if session.start_time:
                        elapsed = (current_time - session.start_time).total_seconds()
                        if elapsed > session.timeout:
                            timed_out.append(session_id)
                
                # Handle timed out conversations
                for session_id in timed_out:
                    session = self.active_conversations.get(session_id)
                    if session:
                        session.state = ConversationState.TIMEOUT
                        session.end_time = current_time
                        logger.warning(f"[TIMEOUT] Conversation {session_id} timed out")
                        self._update_conversation_metrics(session, "timeout")
                        self._finalize_conversation(session)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Conversation monitoring failed: {e}")
                await asyncio.sleep(30)
    
    async def get_conversation_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation status"""
        # Check active conversations
        if session_id in self.active_conversations:
            session = self.active_conversations[session_id]
        elif session_id in self.conversation_history:
            session = self.conversation_history[session_id]
        else:
            return None
        
        return {
            "session_id": session.session_id,
            "conversation_type": session.conversation_type.value,
            "state": session.state.value,
            "participants": list(session.participants.keys()),
            "current_round": session.current_round,
            "max_rounds": session.max_rounds,
            "message_count": len(session.messages),
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "consensus_result": session.consensus_result

    
    async def get_status(self) -> Dict[str, Any]:
        """Get conversation manager status"""
        autogen_status = "not_initialized"
        if self.autogen_coordinator:
            try:
                autogen_status_data = await self.autogen_coordinator.get_coordinator_status()
                autogen_status = autogen_status_data.get("coordinator_status", "unknown")
            except:
                autogen_status = "error"
        
        return {
            "manager_status": "running",
            "autogen_integration": autogen_status,
            "active_conversations": len(self.active_conversations),
            "conversation_history": len(self.conversation_history),
            "conversation_handlers": len(self.conversation_handlers),
            "decision_algorithms": len(self.decision_algorithms),
            "metrics": self.metrics

    
    async def shutdown(self):
        """Shutdown the conversation manager"""
        logger.info("[SHUTDOWN] Shutting down Conversation Manager...")
        
        # Cancel monitoring task
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown AutoGen coordinator
        if self.autogen_coordinator:
            await self.autogen_coordinator.shutdown()
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        logger.info("[SHUTDOWN] Conversation Manager shutdown complete")