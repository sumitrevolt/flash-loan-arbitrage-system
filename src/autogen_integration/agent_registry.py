# -*- coding: utf-8 -*-
"""
Agent Registry for AutoGen Multi-Agent System

This module manages registration, tracking, and lifecycle of AutoGen agents
across different sessions and conversation types.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import asyncio
import logging
import uuid

from dataclasses import dataclass, field
from enum import Enum
import autogen

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status states"""
    CREATED = "created"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AgentType(Enum):
    """Types of agents in the system"""
    ARBITRAGE_COORDINATOR = "arbitrage_coordinator"
    MARKET_ANALYST = "market_analyst"
    RISK_ANALYST = "risk_analyst"
    EXECUTION_SPECIALIST = "execution_specialist"
    GAS_OPTIMIZER = "gas_optimizer"
    COMPLIANCE_VALIDATOR = "compliance_validator"
    TIMING_ANALYST = "timing_analyst"
    BRIDGE_SPECIALIST = "bridge_specialist"


@dataclass
class RegisteredAgent:
    """Information about a registered agent"""
    agent_id: str
    agent_name: str
    agent_type: AgentType
    session_id: str
    agent_instance: autogen.Agent
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    capabilities: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    conversation_count: int = 0
    total_messages: int = 0


@dataclass
class SessionAgents:
    """Agents associated with a session"""
    session_id: str
    agent_ids: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"


class AgentRegistry:
    """
    Registry for managing AutoGen agents across sessions and conversations.
    Provides agent lifecycle management, performance tracking, and resource optimization.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Agent storage
        self.registered_agents: Dict[str, RegisteredAgent] = {}
        self.session_agents: Dict[str, SessionAgents] = {}
        
        # Type-based grouping
        self.agents_by_type: Dict[AgentType, Set[str]] = {
            agent_type: set() for agent_type in AgentType

        
        # Performance tracking
        self.registry_metrics = {
            "total_agents_created": 0,
            "active_agents": 0,
            "sessions_managed": 0,
            "agent_reuse_count": 0,
            "cleanup_operations": 0,
            "error_count": 0

        
        # Configuration
        self.max_agents_per_session = config.get("max_agents_per_session", 10)
        self.agent_timeout_minutes = config.get("agent_timeout_minutes", 30)
        self.cleanup_interval_seconds = config.get("cleanup_interval_seconds", 300)  # 5 minutes
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("[INIT] Agent Registry initialized")
    
    async def initialize(self):
        """Initialize the agent registry"""
        try:
            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            logger.info("[OK] Agent Registry ready")
            
        except Exception as e:
            logger.error(f"[ERROR] Agent Registry initialization failed: {e}")
            raise
    
    async def register_agent(
        self,
        session_id: str,
        agent_type: str,
        agent_instance: autogen.Agent,
        capabilities: Optional[List[str]] = None
    ) -> str:
        """
        Register a new agent with the registry
        
        Args:
            session_id: Session identifier
            agent_type: Type of agent
            agent_instance: AutoGen agent instance
            capabilities: Agent capabilities list
            
        Returns:
            Agent ID for tracking
        """
        try:
            # Generate unique agent ID
            agent_id = f"{agent_type}_{session_id}_{uuid.uuid4().hex[:8]}"
            
            # Validate agent type
            try:
                agent_type_enum = AgentType(agent_type)
            except ValueError:
                logger.warning(f"[REGISTER] Unknown agent type: {agent_type}, using generic type")
                agent_type_enum = AgentType.ARBITRAGE_COORDINATOR  # Default fallback
            
            # Create registered agent
            registered_agent = RegisteredAgent(
                agent_id=agent_id,
                agent_name=getattr(agent_instance, 'name', agent_type),
                agent_type=agent_type_enum,
                session_id=session_id,
                agent_instance=agent_instance,
                status=AgentStatus.CREATED,
                capabilities=capabilities or [],
                performance_metrics={
                    "conversations_participated": 0,
                    "messages_sent": 0,
                    "average_response_time": 0.0,
                    "success_rate": 1.0,
                    "last_performance_update": datetime.now().isoformat()


            
            # Register agent
            self.registered_agents[agent_id] = registered_agent
            
            # Add to type grouping
            self.agents_by_type[agent_type_enum].add(agent_id)
            
            # Add to session grouping
            if session_id not in self.session_agents:
                self.session_agents[session_id] = SessionAgents(session_id=session_id)
                self.registry_metrics["sessions_managed"] += 1
            
            self.session_agents[session_id].agent_ids.add(agent_id)
            
            # Update metrics
            self.registry_metrics["total_agents_created"] += 1
            self.registry_metrics["active_agents"] += 1
            
            # Set agent status to active
            await self.update_agent_status(agent_id, AgentStatus.ACTIVE)
            
            logger.info(f"[REGISTER] Agent {agent_id} registered for session {session_id}")
            
            return agent_id
            
        except Exception as e:
            logger.error(f"[ERROR] Agent registration failed: {e}")
            self.registry_metrics["error_count"] += 1
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get registered agent by ID"""
        return self.registered_agents.get(agent_id)
    
    async def get_agent_instance(self, agent_id: str) -> Optional[autogen.Agent]:
        """Get AutoGen agent instance by ID"""
        registered_agent = self.registered_agents.get(agent_id)
        return registered_agent.agent_instance if registered_agent else None
    
    async def get_session_agents(self, session_id: str) -> List[RegisteredAgent]:
        """Get all agents for a specific session"""
        session_data = self.session_agents.get(session_id)
        if not session_data:
            return []
        
        agents = []
        for agent_id in session_data.agent_ids:
            agent = self.registered_agents.get(agent_id)
            if agent:
                agents.append(agent)
        
        return agents
    
    async def get_agents_by_type(self, agent_type: AgentType) -> List[RegisteredAgent]:
        """Get all agents of a specific type"""
        agent_ids = self.agents_by_type.get(agent_type, set())
        agents = []
        
        for agent_id in agent_ids:
            agent = self.registered_agents.get(agent_id)
            if agent and agent.status not in [AgentStatus.SHUTDOWN, AgentStatus.ERROR]:
                agents.append(agent)
        
        return agents
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        try:
            agent = self.registered_agents.get(agent_id)
            if not agent:
                logger.warning(f"[STATUS] Agent {agent_id} not found")
                return False
            
            old_status = agent.status
            agent.status = status
            agent.last_activity = datetime.now()
            
            # Update metrics based on status change
            if old_status == AgentStatus.ACTIVE and status != AgentStatus.ACTIVE:
                self.registry_metrics["active_agents"] -= 1
            elif old_status != AgentStatus.ACTIVE and status == AgentStatus.ACTIVE:
                self.registry_metrics["active_agents"] += 1
            
            logger.debug(f"[STATUS] Agent {agent_id} status: {old_status.value} -> {status.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to update agent status: {e}")
            return False
    
    async def update_agent_performance(
        self,
        agent_id: str,
        conversation_count: int = 0,
        message_count: int = 0,
        response_time: Optional[float] = None,
        success: bool = True
    ):
        """Update agent performance metrics"""
        try:
            agent = self.registered_agents.get(agent_id)
            if not agent:
                return
            
            # Update conversation and message counts
            agent.conversation_count += conversation_count
            agent.total_messages += message_count
            
            # Update performance metrics
            metrics = agent.performance_metrics
            metrics["conversations_participated"] += conversation_count
            metrics["messages_sent"] += message_count
            
            # Update response time
            if response_time is not None:
                current_avg = metrics.get("average_response_time", 0.0)
                message_count_total = metrics["messages_sent"]
                if message_count_total > 0:
                    metrics["average_response_time"] = (
                        (current_avg * (message_count_total - message_count) + response_time * message_count) / message_count_total

                else:
                    metrics["average_response_time"] = response_time
            
            # Update success rate
            if not success:
                agent.error_count += 1
            
            total_operations = agent.conversation_count + agent.error_count
            if total_operations > 0:
                metrics["success_rate"] = (total_operations - agent.error_count) / total_operations
            
            metrics["last_performance_update"] = datetime.now().isoformat()
            
            logger.debug(f"[PERFORMANCE] Updated metrics for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to update agent performance: {e}")
    
    async def find_available_agent(
        self,
        agent_type: AgentType,
        exclude_session: Optional[str] = None
    ) -> Optional[RegisteredAgent]:
        """Find an available agent of the specified type for reuse"""
        try:
            agents = await self.get_agents_by_type(agent_type)
            
            for agent in agents:
                # Skip agents from excluded session
                if exclude_session and agent.session_id == exclude_session:
                    continue
                
                # Check if agent is available (idle or created)
                if agent.status in [AgentStatus.IDLE, AgentStatus.CREATED]:
                    # Check if agent hasn't timed out
                    if self._is_agent_available(agent):
                        return agent
            
            return None
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to find available agent: {e}")
            return None
    
    async def reuse_agent(self, agent_id: str, new_session_id: str) -> bool:
        """Reuse an existing agent for a new session"""
        try:
            agent = self.registered_agents.get(agent_id)
            if not agent:
                return False
            
            # Remove from old session
            old_session_data = self.session_agents.get(agent.session_id)
            if old_session_data:
                old_session_data.agent_ids.discard(agent_id)
            
            # Add to new session
            if new_session_id not in self.session_agents:
                self.session_agents[new_session_id] = SessionAgents(session_id=new_session_id)
                self.registry_metrics["sessions_managed"] += 1
            
            self.session_agents[new_session_id].agent_ids.add(agent_id)
            
            # Update agent
            agent.session_id = new_session_id
            agent.status = AgentStatus.ACTIVE
            agent.last_activity = datetime.now()
            
            # Update metrics
            self.registry_metrics["agent_reuse_count"] += 1
            
            logger.info(f"[REUSE] Agent {agent_id} reused for session {new_session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Agent reuse failed: {e}")
            return False
    
    async def cleanup_session_agents(self, session_id: str):
        """Cleanup all agents for a completed session"""
        try:
            session_data = self.session_agents.get(session_id)
            if not session_data:
                return
            
            # Get agent IDs to cleanup
            agent_ids = list(session_data.agent_ids)
            
            # Cleanup each agent
            for agent_id in agent_ids:
                await self._cleanup_agent(agent_id)
            
            # Remove session
            del self.session_agents[session_id]
            
            self.registry_metrics["cleanup_operations"] += 1
            
            logger.info(f"[CLEANUP] Cleaned up {len(agent_ids)} agents for session {session_id}")
            
        except Exception as e:
            logger.error(f"[ERROR] Session cleanup failed for {session_id}: {e}")
    
    async def cleanup_agent(self, agent_id: str) -> bool:
        """Cleanup a specific agent"""
        return await self._cleanup_agent(agent_id)
    
    async def _cleanup_agent(self, agent_id: str) -> bool:
        """Internal agent cleanup"""
        try:
            agent = self.registered_agents.get(agent_id)
            if not agent:
                return False
            
            # Update status
            agent.status = AgentStatus.SHUTDOWN
            
            # Remove from type grouping
            self.agents_by_type[agent.agent_type].discard(agent_id)
            
            # Remove from session
            session_data = self.session_agents.get(agent.session_id)
            if session_data:
                session_data.agent_ids.discard(agent_id)
            
            # Update metrics
            if agent.status == AgentStatus.ACTIVE:
                self.registry_metrics["active_agents"] -= 1
            
            # Remove from registry
            del self.registered_agents[agent_id]
            
            logger.debug(f"[CLEANUP] Agent {agent_id} cleaned up")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Agent cleanup failed for {agent_id}: {e}")
            return False
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of inactive and timed-out agents"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(minutes=self.agent_timeout_minutes)
                
                # Find agents to cleanup
                agents_to_cleanup = []
                
                for agent_id, agent in self.registered_agents.items():
                    # Cleanup timed-out agents
                    if agent.last_activity and agent.last_activity < timeout_threshold:
                        if agent.status not in [AgentStatus.BUSY, AgentStatus.ACTIVE]:
                            agents_to_cleanup.append(agent_id)
                    
                    # Cleanup error agents
                    elif agent.status == AgentStatus.ERROR:
                        agents_to_cleanup.append(agent_id)
                
                # Cleanup agents
                for agent_id in agents_to_cleanup:
                    await self._cleanup_agent(agent_id)
                
                if agents_to_cleanup:
                    logger.info(f"[PERIODIC_CLEANUP] Cleaned up {len(agents_to_cleanup)} inactive agents")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Periodic cleanup failed: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def _is_agent_available(self, agent: RegisteredAgent) -> bool:
        """Check if agent is available for reuse"""
        # Check timeout
        if agent.last_activity:
            timeout_threshold = datetime.now() - timedelta(minutes=self.agent_timeout_minutes)
            if agent.last_activity < timeout_threshold:
                return False
        
        # Check status
        if agent.status not in [AgentStatus.IDLE, AgentStatus.CREATED]:
            return False
        
        # Check error rate
        if agent.error_count > 5:  # Too many errors
            return False
        
        return True
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        # Count agents by status
        status_counts = {}
        for status in AgentStatus:
            status_counts[status.value] = 0
        
        for agent in self.registered_agents.values():
            status_counts[agent.status.value] += 1
        
        # Count agents by type
        type_counts = {}
        for agent_type in AgentType:
            type_counts[agent_type.value] = len(self.agents_by_type[agent_type])
        
        # Calculate average performance
        total_agents = len(self.registered_agents)
        avg_conversations = 0
        avg_messages = 0
        avg_success_rate = 0
        
        if total_agents > 0:
            avg_conversations = sum(agent.conversation_count for agent in self.registered_agents.values()) / total_agents
            avg_messages = sum(agent.total_messages for agent in self.registered_agents.values()) / total_agents
            avg_success_rate = sum(
                agent.performance_metrics.get("success_rate", 0) for agent in self.registered_agents.values()
            ) / total_agents
        
        return {
            "total_agents": total_agents,
            "active_sessions": len(self.session_agents),
            "agents_by_status": status_counts,
            "agents_by_type": type_counts,
            "performance_averages": {
                "conversations_per_agent": avg_conversations,
                "messages_per_agent": avg_messages,
                "success_rate": avg_success_rate
            },
            "registry_metrics": self.registry_metrics

    
    async def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent"""
        agent = self.registered_agents.get(agent_id)
        if not agent:
            return None
        
        return {
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "agent_type": agent.agent_type.value,
            "session_id": agent.session_id,
            "status": agent.status.value,
            "created_at": agent.created_at.isoformat(),
            "last_activity": agent.last_activity.isoformat() if agent.last_activity else None,
            "capabilities": agent.capabilities,
            "conversation_count": agent.conversation_count,
            "total_messages": agent.total_messages,
            "error_count": agent.error_count,
            "performance_metrics": agent.performance_metrics

    
    async def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a session and its agents"""
        session_data = self.session_agents.get(session_id)
        if not session_data:
            return None
        
        agents = await self.get_session_agents(session_id)
        
        return {
            "session_id": session_id,
            "status": session_data.status,
            "created_at": session_data.created_at.isoformat(),
            "agent_count": len(agents),
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "agent_type": agent.agent_type.value,
                    "status": agent.status.value

                for agent in agents


    
    async def get_status(self) -> Dict[str, Any]:
        """Get registry status"""
        stats = await self.get_registry_stats()
        
        return {
            "registry_status": "healthy",
            "statistics": stats,
            "configuration": {
                "max_agents_per_session": self.max_agents_per_session,
                "agent_timeout_minutes": self.agent_timeout_minutes,
                "cleanup_interval_seconds": self.cleanup_interval_seconds


    
    async def shutdown(self):
        """Shutdown the agent registry"""
        logger.info("[SHUTDOWN] Shutting down Agent Registry...")
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup all agents
        agent_ids = list(self.registered_agents.keys())
        for agent_id in agent_ids:
            await self._cleanup_agent(agent_id)
        
        # Clear all data
        self.registered_agents.clear()
        self.session_agents.clear()
        
        for agent_type in AgentType:
            self.agents_by_type[agent_type].clear()
        
        logger.info("[SHUTDOWN] Agent Registry shutdown complete")