"""
LangChain Multi-Agent Flash Loan System
=====================================

Main application entry point for the multi-agent system supporting:
- Multi-agent coordination with LangGraph
- RAG (Retrieval-Augmented Generation) 
- Tool use and code interpretation
- Memory management
- Real-time monitoring
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel

# LangChain imports
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# LangGraph imports for multi-agent coordination
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langgraph.checkpoint.memory import MemorySaver

# Custom imports
from agents.coordinator import AgentCoordinator
from agents.arbitrage_agent import ArbitrageAgent
from agents.risk_agent import RiskAgent
from agents.execution_agent import ExecutionAgent
from agents.monitoring_agent import MonitoringAgent
from agents.rag_agent import RAGAgent
from agents.code_interpreter_agent import CodeInterpreterAgent
from services.vector_store import VectorStoreService
from services.memory_manager import MemoryManager
from services.tool_registry import ToolRegistry
from utils.config import Config
from utils.logger import setup_logger

# Initialize logging
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LangChain Multi-Agent Flash Loan System",
    description="Advanced multi-agent system for flash loan arbitrage with RAG and code interpretation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class SystemState:
    def __init__(self):
        self.coordinator: Optional[AgentCoordinator] = None
        self.agents: Dict[str, object] = {}
        self.graph: Optional[StateGraph] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.vector_store: Optional[VectorStoreService] = None
        self.tool_registry: Optional[ToolRegistry] = None
        self.is_running: bool = False

system_state = SystemState()

# Pydantic models
class AgentRequest(BaseModel):
    agent_type: str
    message: str
    context: Optional[Dict] = None
    session_id: Optional[str] = None

class AgentResponse(BaseModel):
    agent_type: str
    response: str
    confidence: float
    metadata: Dict
    timestamp: datetime

class SystemStatus(BaseModel):
    status: str
    uptime: str
    active_agents: List[str]
    memory_usage: Dict
    last_update: datetime

async def initialize_system():
    """Initialize the multi-agent system"""
    try:
        logger.info("🚀 Initializing LangChain Multi-Agent System...")
        
        # Initialize configuration
        config = Config()
        
        # Initialize memory manager
        system_state.memory_manager = MemoryManager()
        await system_state.memory_manager.initialize()
        
        # Initialize vector store
        system_state.vector_store = VectorStoreService()
        await system_state.vector_store.initialize()
        
        # Initialize tool registry
        system_state.tool_registry = ToolRegistry()
        await system_state.tool_registry.initialize()
        
        # Initialize agents
        await initialize_agents()
        
        # Initialize agent coordination graph
        await initialize_coordination_graph()
        
        system_state.is_running = True
        logger.info("✅ System initialization completed successfully")
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {e}")
        raise

async def initialize_agents():
    """Initialize all AI agents"""
    try:
        logger.info("🧠 Initializing AI agents...")
        
        # Initialize coordinator
        system_state.coordinator = AgentCoordinator(
            memory_manager=system_state.memory_manager,
            vector_store=system_state.vector_store,
            tool_registry=system_state.tool_registry
        )
        
        # Initialize specialized agents
        system_state.agents = {
            "arbitrage": ArbitrageAgent(
                name="ArbitrageAgent",
                memory_manager=system_state.memory_manager,
                tool_registry=system_state.tool_registry
            ),
            "risk": RiskAgent(
                name="RiskAgent", 
                memory_manager=system_state.memory_manager,
                tool_registry=system_state.tool_registry
            ),
            "execution": ExecutionAgent(
                name="ExecutionAgent",
                memory_manager=system_state.memory_manager,
                tool_registry=system_state.tool_registry
            ),
            "monitoring": MonitoringAgent(
                name="MonitoringAgent",
                memory_manager=system_state.memory_manager,
                tool_registry=system_state.tool_registry
            ),
            "rag": RAGAgent(
                name="RAGAgent",
                memory_manager=system_state.memory_manager,
                vector_store=system_state.vector_store,
                tool_registry=system_state.tool_registry
            ),
            "code_interpreter": CodeInterpreterAgent(
                name="CodeInterpreterAgent",
                memory_manager=system_state.memory_manager,
                tool_registry=system_state.tool_registry
            )
        }
        
        # Initialize all agents
        for agent_name, agent in system_state.agents.items():
            await agent.initialize()
            logger.info(f"✅ Initialized {agent_name} agent")
            
        logger.info("✅ All agents initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Agent initialization failed: {e}")
        raise

async def initialize_coordination_graph():
    """Initialize the LangGraph coordination system"""
    try:
        logger.info("🔗 Initializing agent coordination graph...")
        
        # Define the state structure
        from typing import TypedDict, Annotated
        from langgraph.graph.message import add_messages
        
        class AgentState(TypedDict):
            messages: Annotated[List[BaseMessage], add_messages]
            current_agent: str
            context: Dict
            result: Optional[Dict]
            
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("coordinator", system_state.coordinator.process)
        workflow.add_node("arbitrage", system_state.agents["arbitrage"].process)
        workflow.add_node("risk", system_state.agents["risk"].process)
        workflow.add_node("execution", system_state.agents["execution"].process)
        workflow.add_node("monitoring", system_state.agents["monitoring"].process)
        workflow.add_node("rag", system_state.agents["rag"].process)
        workflow.add_node("code_interpreter", system_state.agents["code_interpreter"].process)
        
        # Define routing logic
        def route_agent(state: AgentState) -> str:
            """Route to appropriate agent based on coordinator decision"""
            if "next_agent" in state.get("context", {}):
                return state["context"]["next_agent"]
            return END
            
        # Set up the workflow
        workflow.set_entry_point("coordinator")
        workflow.add_conditional_edges("coordinator", route_agent)
        workflow.add_edge("arbitrage", "coordinator")
        workflow.add_edge("risk", "coordinator") 
        workflow.add_edge("execution", "coordinator")
        workflow.add_edge("monitoring", "coordinator")
        workflow.add_edge("rag", "coordinator")
        workflow.add_edge("code_interpreter", "coordinator")
        
        # Compile the graph
        checkpointer = MemorySaver()
        system_state.graph = workflow.compile(checkpointer=checkpointer)
        
        logger.info("✅ Agent coordination graph initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Coordination graph initialization failed: {e}")
        raise

# API Routes
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    await initialize_system()

@app.on_event("shutdown") 
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🔄 Shutting down system...")
    system_state.is_running = False
    
    # Cleanup resources
    if system_state.memory_manager:
        await system_state.memory_manager.cleanup()
    if system_state.vector_store:
        await system_state.vector_store.cleanup()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LangChain Multi-Agent Flash Loan System",
        "version": "1.0.0",
        "status": "running" if system_state.is_running else "initializing",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        status = {
            "status": "healthy" if system_state.is_running else "initializing",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "coordinator": system_state.coordinator is not None,
                "memory_manager": system_state.memory_manager is not None,
                "vector_store": system_state.vector_store is not None,
                "tool_registry": system_state.tool_registry is not None,
                "graph": system_state.graph is not None
            },
            "agents": {
                name: agent is not None 
                for name, agent in system_state.agents.items()
            }
        }
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get detailed system status"""
    try:
        # Calculate uptime (simplified)
        uptime = "running" if system_state.is_running else "stopped"
        
        # Get active agents
        active_agents = [
            name for name, agent in system_state.agents.items()
            if agent is not None
        ]
        
        # Get memory usage (simplified)
        memory_usage = {
            "total_agents": len(system_state.agents),
            "active_agents": len(active_agents),
            "memory_manager_status": "active" if system_state.memory_manager else "inactive"
        }
        
        return SystemStatus(
            status="running" if system_state.is_running else "stopped",
            uptime=uptime,
            active_agents=active_agents,
            memory_usage=memory_usage,
            last_update=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/process", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    """Process a request through the multi-agent system"""
    try:
        if not system_state.is_running:
            raise HTTPException(status_code=503, detail="System is not ready")
            
        if not system_state.graph:
            raise HTTPException(status_code=503, detail="Agent coordination graph not initialized")
        
        # Prepare the state
        from langchain.schema import HumanMessage
        
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "current_agent": "coordinator",
            "context": request.context or {},
            "result": None
        }
        
        # Process through the graph
        config = {"configurable": {"thread_id": request.session_id or "default"}}
        result = await system_state.graph.ainvoke(initial_state, config)
        
        # Extract response
        response_data = result.get("result", {})
        
        return AgentResponse(
            agent_type=request.agent_type,
            response=response_data.get("response", "No response generated"),
            confidence=response_data.get("confidence", 0.5),
            metadata=response_data.get("metadata", {}),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to process agent request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/{agent_name}/direct")
async def direct_agent_request(agent_name: str, request: AgentRequest):
    """Send a direct request to a specific agent"""
    try:
        if not system_state.is_running:
            raise HTTPException(status_code=503, detail="System is not ready")
            
        if agent_name not in system_state.agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = system_state.agents[agent_name]
        
        # Process request directly
        result = await agent.process_direct(request.message, request.context or {})
        
        return AgentResponse(
            agent_type=agent_name,
            response=result.get("response", "No response generated"),
            confidence=result.get("confidence", 0.5),
            metadata=result.get("metadata", {}),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to process direct agent request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    try:
        agents_info = {}
        for name, agent in system_state.agents.items():
            if agent:
                agents_info[name] = {
                    "name": getattr(agent, 'name', name),
                    "status": "active",
                    "capabilities": getattr(agent, 'capabilities', []),
                    "last_active": datetime.now().isoformat()
                }
            else:
                agents_info[name] = {
                    "name": name,
                    "status": "inactive",
                    "capabilities": [],
                    "last_active": None
                }
        
        return agents_info
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    system_state.is_running = False
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configure server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 1))
    
    logger.info(f"🚀 Starting LangChain Multi-Agent System on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        reload=False
    )
