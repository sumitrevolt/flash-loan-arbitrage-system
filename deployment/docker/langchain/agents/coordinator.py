"""
Agent Coordinator
================

Central coordination system for managing multi-agent interactions,
task distribution, and decision-making in the flash loan system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from utils.logger import setup_logger

logger = setup_logger(__name__)

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(BaseModel):
    id: str
    type: str
    priority: TaskPriority
    status: TaskStatus
    assigned_agent: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    data: Dict[str, Any]
    dependencies: List[str] = []
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentCoordinator:
    """
    Central coordinator for managing multiple AI agents in the flash loan system.
    
    Responsibilities:
    - Task routing and distribution
    - Agent load balancing
    - Conflict resolution
    - Performance monitoring
    - Decision aggregation
    """
    
    def __init__(self, memory_manager, vector_store, tool_registry):
        self.memory_manager = memory_manager
        self.vector_store = vector_store
        self.tool_registry = tool_registry
        
        # LLM for coordination decisions
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            max_tokens=2000
        )
        
        # Agent registry
        self.agents: Dict[str, Any] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.agent_load: Dict[str, int] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        
        # Task management
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        
        # Coordination prompts
        self.setup_prompts()
        
        logger.info("🎯 Agent Coordinator initialized")

    def setup_prompts(self):
        """Set up coordination prompt templates"""
        
        self.routing_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the central coordinator for a multi-agent flash loan arbitrage system.
            
            Available agents and their capabilities:
            - ArbitrageAgent: Identifies arbitrage opportunities, calculates profits, analyzes market conditions
            - RiskAgent: Assesses risks, validates safety parameters, monitors exposure
            - ExecutionAgent: Executes transactions, manages gas optimization, handles failures
            - MonitoringAgent: Tracks system health, monitors performance, alerts on issues
            - RAGAgent: Retrieves relevant information, answers questions, provides context
            - CodeInterpreterAgent: Analyzes code, runs calculations, generates reports
            
            Your task is to:
            1. Analyze the incoming request
            2. Determine which agent(s) should handle it
            3. Set the priority level
            4. Provide routing instructions
            
            Respond with JSON containing:
            - primary_agent: The main agent to handle the request
            - supporting_agents: List of agents that may be needed
            - priority: LOW, MEDIUM, HIGH, or CRITICAL
            - reasoning: Brief explanation of the routing decision
            - parallel_execution: Boolean indicating if agents can work in parallel
            """),
            ("human", "Request: {request}\nContext: {context}")
        ])
        
        self.decision_aggregation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are aggregating responses from multiple AI agents in a flash loan system.
            
            Your task is to:
            1. Analyze all agent responses
            2. Identify conflicts or inconsistencies
            3. Weigh the credibility of each response
            4. Generate a final consolidated decision
            5. Provide confidence scores
            
            Consider:
            - Agent specialization and expertise
            - Data freshness and relevance
            - Risk implications
            - Profit potential
            - System safety
            
            Respond with JSON containing:
            - final_decision: The consolidated decision
            - confidence: Float between 0 and 1
            - supporting_evidence: Key points supporting the decision
            - risk_factors: Identified risks
            - action_items: Specific next steps
            """),
            ("human", "Agent Responses:\n{responses}\n\nContext: {context}")
        ])

    async def register_agent(self, agent_name: str, agent_instance: Any, capabilities: List[str]):
        """Register an agent with the coordinator"""
        try:
            self.agents[agent_name] = agent_instance
            self.agent_capabilities[agent_name] = capabilities
            self.agent_load[agent_name] = 0
            self.agent_performance[agent_name] = {
                "success_rate": 1.0,
                "avg_response_time": 0.0,
                "total_tasks": 0,
                "failed_tasks": 0
            }
            
            logger.info(f"✅ Registered agent: {agent_name} with capabilities: {capabilities}")
            
        except Exception as e:
            logger.error(f"❌ Failed to register agent {agent_name}: {e}")
            raise

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main coordination process - entry point for the LangGraph workflow
        """
        try:
            messages = state.get("messages", [])
            context = state.get("context", {})
            
            if not messages:
                return state
            
            # Get the latest message
            latest_message = messages[-1]
            request_content = latest_message.content if hasattr(latest_message, 'content') else str(latest_message)
            
            logger.info(f"🎯 Processing coordination request: {request_content[:100]}...")
            
            # Route the request
            routing_decision = await self.route_request(request_content, context)
            
            # Update context with routing decision
            context.update({
                "routing_decision": routing_decision,
                "next_agent": routing_decision.get("primary_agent", "arbitrage"),
                "supporting_agents": routing_decision.get("supporting_agents", []),
                "priority": routing_decision.get("priority", "MEDIUM")
            })
            
            # Update state
            state["context"] = context
            state["current_agent"] = routing_decision.get("primary_agent", "arbitrage")
            
            # Add coordination message
            coordination_msg = AIMessage(
                content=f"Routing to {routing_decision.get('primary_agent')} agent. "
                       f"Priority: {routing_decision.get('priority')}. "
                       f"Reasoning: {routing_decision.get('reasoning', 'Standard routing')}"
            )
            state["messages"].append(coordination_msg)
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Coordination process failed: {e}")
            error_msg = AIMessage(content=f"Coordination error: {str(e)}")
            state["messages"].append(error_msg)
            return state

    async def route_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route a request to the appropriate agent(s)"""
        try:
            # Prepare routing prompt
            routing_input = {
                "request": request,
                "context": str(context)
            }
            
            # Get routing decision from LLM
            response = await self.llm.ainvoke(
                self.routing_prompt.format_messages(**routing_input)
            )
            
            # Parse response (simplified - in production, use structured output)
            routing_decision = self.parse_routing_response(response.content)
            
            logger.info(f"🎯 Routing decision: {routing_decision}")
            return routing_decision
            
        except Exception as e:
            logger.error(f"❌ Request routing failed: {e}")
            # Fallback routing
            return {
                "primary_agent": "arbitrage",
                "supporting_agents": [],
                "priority": "MEDIUM",
                "reasoning": "Fallback routing due to error",
                "parallel_execution": False
            }

    def parse_routing_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM routing response"""
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback parsing
            primary_agent = "arbitrage"
            if "risk" in response.lower():
                primary_agent = "risk"
            elif "execution" in response.lower():
                primary_agent = "execution"
            elif "monitoring" in response.lower():
                primary_agent = "monitoring"
            elif "rag" in response.lower() or "information" in response.lower():
                primary_agent = "rag"
            elif "code" in response.lower() or "analysis" in response.lower():
                primary_agent = "code_interpreter"
            
            priority = "MEDIUM"
            if "critical" in response.lower() or "urgent" in response.lower():
                priority = "CRITICAL"
            elif "high" in response.lower():
                priority = "HIGH"
            elif "low" in response.lower():
                priority = "LOW"
            
            return {
                "primary_agent": primary_agent,
                "supporting_agents": [],
                "priority": priority,
                "reasoning": "Parsed from natural language response",
                "parallel_execution": False
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse routing response: {e}")
            return {
                "primary_agent": "arbitrage",
                "supporting_agents": [],
                "priority": "MEDIUM",
                "reasoning": "Default routing due to parsing error",
                "parallel_execution": False
            }

    async def aggregate_responses(self, responses: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate responses from multiple agents"""
        try:
            if len(responses) == 1:
                return responses[0]
            
            # Prepare aggregation prompt
            responses_text = "\n".join([
                f"Agent {i+1} ({resp.get('agent_name', 'unknown')}): {resp.get('response', '')}"
                for i, resp in enumerate(responses)
            ])
            
            aggregation_input = {
                "responses": responses_text,
                "context": str(context)
            }
            
            # Get aggregated decision
            response = await self.llm.ainvoke(
                self.decision_aggregation_prompt.format_messages(**aggregation_input)
            )
            
            # Parse aggregated response
            aggregated_decision = self.parse_aggregation_response(response.content)
            
            return aggregated_decision
            
        except Exception as e:
            logger.error(f"❌ Response aggregation failed: {e}")
            # Return the first response as fallback
            return responses[0] if responses else {
                "response": "No responses to aggregate",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    def parse_aggregation_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM aggregation response"""
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "response": parsed.get("final_decision", response),
                    "confidence": parsed.get("confidence", 0.5),
                    "metadata": {
                        "supporting_evidence": parsed.get("supporting_evidence", []),
                        "risk_factors": parsed.get("risk_factors", []),
                        "action_items": parsed.get("action_items", [])
                    }
                }
            
            # Fallback parsing
            return {
                "response": response,
                "confidence": 0.5,
                "metadata": {"parsing_method": "fallback"}
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse aggregation response: {e}")
            return {
                "response": response,
                "confidence": 0.3,
                "metadata": {"error": str(e)}
            }

    async def get_agent_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        try:
            metrics = {}
            for agent_name, perf in self.agent_performance.items():
                metrics[agent_name] = {
                    "success_rate": perf["success_rate"],
                    "avg_response_time": perf["avg_response_time"],
                    "total_tasks": perf["total_tasks"],
                    "failed_tasks": perf["failed_tasks"],
                    "current_load": self.agent_load.get(agent_name, 0),
                    "capabilities": self.agent_capabilities.get(agent_name, [])
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to get performance metrics: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Perform coordinator health check"""
        try:
            status = {
                "coordinator_status": "healthy",
                "registered_agents": len(self.agents),
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "queue_size": len(self.task_queue),
                "timestamp": datetime.now().isoformat()
            }
            
            # Check agent availability
            agent_status = {}
            for agent_name, agent in self.agents.items():
                try:
                    # Simple availability check
                    agent_status[agent_name] = {
                        "status": "available",
                        "load": self.agent_load.get(agent_name, 0)
                    }
                except Exception as e:
                    agent_status[agent_name] = {
                        "status": "unavailable",
                        "error": str(e)
                    }
            
            status["agents"] = agent_status
            return status
            
        except Exception as e:
            logger.error(f"❌ Coordinator health check failed: {e}")
            return {
                "coordinator_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
