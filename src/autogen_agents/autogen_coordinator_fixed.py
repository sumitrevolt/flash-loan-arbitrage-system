# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
    import locale
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import asyncio
import json
import logging
import os
import re
import sys
import time
import traceback

    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    import autogen
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import redis
import uvicorn
"""
AutoGen Multi-Agent Coordinator for Flash Loan Arbitrage
Unicode-safe version with proper encoding handling
"""


# Ensure UTF-8 encoding
if sys.version_info >= (3, 7):
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass  # Use system default

# Unicode-safe logging setup
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

# Try to import autogen, fall back to mock if not available
try:
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logging.warning("AutoGen not available - using mock implementation")

# Setup logging with Unicode safety
logging.basicConfig()
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[]
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('autogen_coordinator.log', encoding='utf-8', mode='a')
    

logger = logging.getLogger(__name__)

# Unicode-safe symbols
SYMBOLS = {}
    'rocket': '[INIT]',
    'check': '[OK]',
    'cross': '[ERROR]',
    'target': '[TASK]',
    'wrench': '[SETUP]',
    'info': '[INFO]',
    'warning': '[WARN]'


app = FastAPI()
    title="AutoGen Multi-Agent System",
    version="1.0.0",
    description="Advanced AutoGen coordination system for flash loan arbitrage",
    docs_url="/docs",
    redoc_url="/redoc"


# Add CORS middleware
app.add_middleware()
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],


class AutoGenCoordinator:
    """AutoGen Multi-Agent Coordinator for Flash Loan Arbitrage"""
    
    def __init__(self):
        self.redis_client = self._setup_redis()
        self.agents = {}
        self.group_chat = None
        self.group_chat_manager = None
        self.config_list = self._setup_config()
        self.task_history = {}
        self.performance_metrics = {}
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0.0,
            "active_conversations": 0
        
        self.start_time = datetime.now()
        
        if AUTOGEN_AVAILABLE:
            self._initialize_autogen_agents()
        else:
            self._initialize_mock_agents()
            
        logger.info(str(f"{SYMBOLS['rocket']} AutoGen Coordinator initialized at {self.start_time}")
    
    def _setup_redis(self) -> redis.Redis:
        """Setup Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            client = redis.from_url(redis_url, decode_responses=True, encoding='utf-8', decode_responses=True, encoding="utf-8")
            client.ping()
            logger.info(str(f"{SYMBOLS['check']} Redis connected: {redis_url}")
            return client
        except Exception as e:
            logger.error(str(f"{SYMBOLS['cross']} Redis connection failed: {e}")
            return None
    
    def _setup_config(self) -> List[Dict]:
        """Setup LLM configuration"""
        return [{]}
            "model": "gpt-3.5-turbo",
            "api_key": os.getenv("OPENAI_API_KEY", "dummy_key"),
            "api_base": os.getenv("OLLAMA_HOST", "http://localhost:11434/v1"),
        
    
    def _initialize_autogen_agents(self):
        """Initialize real AutoGen agents"""
        logger.info(str(f"{SYMBOLS['rocket']} Initializing AutoGen agents...")
        
        self.agents["coordinator"] = AssistantAgent()
            name="ArbitrageCoordinator",
            system_message="""You are the master coordinator for flash loan arbitrage strategies.
            Your role is to:
            1. Analyze market opportunities
            2. Coordinate with other agents
            3. Make strategic decisions
            4. Ensure risk management compliance""",
            llm_config={"config_list": self.config_list}
        
        
        self.agents["analyzer"] = AssistantAgent()
            name="MarketAnalyzer", 
            system_message="""You are a market data analyst specializing in DeFi protocols.
            Your responsibilities:
            1. Monitor DEX prices across multiple protocols
            2. Identify arbitrage opportunities
            3. Calculate potential profits
            4. Assess market conditions""",
            llm_config={"config_list": self.config_list}
        
        
        self.agents["executor"] = AssistantAgent()
            name="TransactionExecutor",
            system_message="""You are responsible for executing flash loan transactions.
            Your tasks:
            1. Prepare transaction parameters
            2. Execute flash loans on Aave
            3. Perform arbitrage trades
            4. Monitor transaction status""",
            llm_config={"config_list": self.config_list}
        
        
        self.agents["risk_manager"] = AssistantAgent()
            name="RiskManager",
            system_message="""You are the risk management specialist.
            Your duties:
            1. Assess transaction risks
            2. Monitor gas prices
            3. Evaluate slippage tolerance
            4. Prevent losses""",
            llm_config={"config_list": self.config_list}
        
        
        self.agents["user_proxy"] = UserProxyAgent()
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={"work_dir": "/tmp/autogen_work"}
        
        
        # Create group chat
        self.group_chat = GroupChat()
            agents=list(self.agents.values()),
            messages=[],
            max_round=int(os.getenv("MAX_ROUND", "10"))
        
        
        self.group_chat_manager = GroupChatManager()
            groupchat=self.group_chat,
            llm_config={"config_list": self.config_list}
        
        
        logger.info(str(f"{SYMBOLS['check']} AutoGen agents initialized: {list(self.agents.keys()}")))
    
    def _initialize_mock_agents(self):
        """Initialize mock agents when AutoGen is not available"""
        logger.info(str(f"{SYMBOLS['wrench']} Initializing mock agents...")
        
        self.agents = {}
            "coordinator": {"name": "ArbitrageCoordinator", "type": "mock"},
            "analyzer": {"name": "MarketAnalyzer", "type": "mock"},
            "executor": {"name": "TransactionExecutor", "type": "mock"},
            "risk_manager": {"name": "RiskManager", "type": "mock"},
            "user_proxy": {"name": "UserProxy", "type": "mock"}
        
        
        logger.info(str(f"{SYMBOLS['check']} Mock agents initialized: {list(self.agents.keys()}")))
    
    async def coordinate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate a task among agents with comprehensive monitoring"""
        start_time = time.time()
        task_id = task.get("id", f"task_{int(time.time())}")
        
        try:
            description = task.get("description", "")
            priority = task.get("priority", "medium")
            
            logger.info(str(f"{SYMBOLS['target']} Coordinating task: {task_id} - {description}")
            
            # Update metrics
            self.performance_metrics["total_tasks"] += 1
            self.performance_metrics["active_conversations"] += 1
            
            # Store task start info
            self.task_history[task_id] = {}
                "start_time": start_time,
                "description": description,
                "priority": priority,
                "status": "in_progress"
            
            
            # Choose coordination method
            if AUTOGEN_AVAILABLE and self.group_chat_manager:
                result = await self._autogen_coordinate(task)
            else:
                result = await self._mock_coordinate(task)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Update metrics
            self.performance_metrics["successful_tasks"] += 1
            self.performance_metrics["active_conversations"] -= 1
            self._update_avg_response_time(response_time)
            
            # Enhanced result with metadata
            result.update({)}
                "response_time": response_time,
                "timestamp": datetime.now().isoformat(),
                "coordinator_version": "1.0.0",
                "performance_metrics": self.performance_metrics.copy()
            
            
            # Store in Redis with TTL
            if self.redis_client:
                try:
                    result_json = json.dumps(result, ensure_ascii=True, default=str, ensure_ascii=True, default=str)
                    self.redis_client.setex()
                        f"task:{task_id}",
                        3600,  # 1 hour TTL
                        result_json
                    
                    # Store task metrics
                    metrics_json = json.dumps({)}
                        "response_time": response_time,
                        "agents_used": len(result.get("agents_involved", [], ensure_ascii=True, default=str)),
                        "success": True
                    }, ensure_ascii=True
                    self.redis_client.setex()
                        f"task_metrics:{task_id}",
                        3600,
                        metrics_json
                    
                except Exception as redis_error:
                    logger.warning(str(f"Redis storage failed: {redis_error}")
            
            # Update task history
            self.task_history[task_id].update({)}
                "status": "completed",
                "response_time": response_time,
                "result": result
            
            
            logger.info(str(f"{SYMBOLS['check']} Task {task_id} completed in {response_time:.2f}s")
            return result
            
        except Exception as e:
            error_time = time.time() - start_time
            
            # Update failure metrics
            self.performance_metrics["failed_tasks"] += 1
            self.performance_metrics["active_conversations"] -= 1
            
            # Log detailed error
            error_details = {}
                "task_id": task_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "response_time": error_time
            
            
            logger.error(str(f"{SYMBOLS['cross']} Task coordination failed: {json.dumps(error_details, indent=2, ensure_ascii=True, ensure_ascii=True, default=str}")
            
            # Store error in Redis
            if self.redis_client:
                try:
                    error_json = json.dumps(error_details, ensure_ascii=True, default=str, ensure_ascii=True, default=str)
                    self.redis_client.setex()
                        f"task_error:{task_id}",
                        3600,
                        error_json
                    
                except Exception:
                    pass
            
            # Update task history
            if task_id in self.task_history:
                self.task_history[task_id].update({)}
                    "status": "failed",
                    "error": str(e),
                    "response_time": error_time
                
            
            raise HTTPException(status_code=500, detail=error_details)
    
    def _update_avg_response_time(self, new_time: float):
        """Update average response time"""
        total_successful = self.performance_metrics["successful_tasks"]
        if total_successful == 1:
            self.performance_metrics["avg_response_time"] = new_time
        else:
            current_avg = self.performance_metrics["avg_response_time"]
            self.performance_metrics["avg_response_time"] = ()
                (current_avg * (total_successful - 1) + new_time) / total_successful
            
    
    async def _autogen_coordinate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Real AutoGen coordination using group chat"""
        try:
            task_description = task.get("description", "")
            task_id = task.get("id", "unknown")
            
            logger.info(str(f"{SYMBOLS['target']} Starting AutoGen group chat for task: {task_id}")
            
            # Prepare the initial message for the group chat
            initial_message = f"""
            Task ID: {task_id}
            Description: {task_description}
            
            Please coordinate to analyze this flash loan arbitrage opportunity:
            1. MarketAnalyzer: Assess the market conditions and identify opportunities
            2. RiskManager: Evaluate potential risks and set safety parameters
            3. TransactionExecutor: Prepare execution strategy if viable
            4. ArbitrageCoordinator: Make final decision and coordinate actions
            
            Provide a structured analysis and recommendation.
            """
            
            # Start the group chat conversation
            chat_result = await asyncio.to_thread()
                self.agents["user_proxy"].initiate_chat,
                self.group_chat_manager,
                message=initial_message
            
            
            # Extract conversation summary
            conversation_history = []
            for message in self.group_chat.messages:
                conversation_history.append({)}
                    "sender": message.get("name", "unknown"),
                    "content": str(message.get("content", "")).encode('ascii', 'ignore').decode('ascii'),
                    "timestamp": message.get("timestamp", "")
                
            
            # Analyze the final response
            final_decision = self._extract_decision_from_conversation(conversation_history)
            
            result = {}
                "task_id": task_id,
                "status": "completed",
                "agents_involved": list(self.agents.keys()),
                "coordination_type": "autogen",
                "conversation_rounds": len(conversation_history),
                "conversation_history": conversation_history,
                "final_decision": final_decision,
                "execution_ready": final_decision.get("approved", False),
                "risk_assessment": final_decision.get("risk_level", "unknown"),
                "estimated_profit": final_decision.get("profit_estimate", 0),
                "result": "AutoGen multi-agent coordination completed successfully"
            
            
            logger.info(str(f"{SYMBOLS['check']} AutoGen coordination completed for task {task_id}")
            return result
            
        except Exception as e:
            logger.error(str(f"{SYMBOLS['cross']} AutoGen coordination failed: {e}")
            return {}
                "task_id": task.get("id"),
                "status": "failed",
                "error": str(e),
                "coordination_type": "autogen",
                "result": f"AutoGen coordination failed: {e}"
            
    
    def _extract_decision_from_conversation(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Extract final decision from conversation history"""
        try:
            # Look for the final coordinator decision
            coordinator_messages = []
                msg for msg in conversation_history
                if msg.get("sender") == "ArbitrageCoordinator"
            
            
            if not coordinator_messages:
                return {"approved": False, "reason": "No coordinator decision found"}
            
            final_message = coordinator_messages[-1].get("content", "")
            
            # Simple decision extraction logic
            decision = {}
                "approved": any(keyword in final_message.lower() for keyword in)
                             ["approved", "execute", "proceed", "go ahead"]),
                "risk_level": "medium",  # Default
                "profit_estimate": 0,
                "reasoning": final_message[:200] + "..." if len(final_message) > 200 else final_message
            
            
            # Extract risk level if mentioned
            if "high risk" in final_message.lower():
                decision["risk_level"] = "high"
            elif "low risk" in final_message.lower():
                decision["risk_level"] = "low"
            
            # Try to extract profit estimates
            profit_match = re.search(r'profit.*?(\d+\.?\d*)', final_message.lower())
            if profit_match:
                decision["profit_estimate"] = float(profit_match.group(1))
            
            return decision
            
        except Exception as e:
            logger.error(str(f"Error extracting decision: {e}")
            return {"approved": False, "reason": f"Decision extraction failed: {e}"}
    
    async def _mock_coordinate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Mock coordination for testing"""
        return {}
            "task_id": task.get("id"),
            "status": "completed",
            "agents_involved": list(self.agents.keys()),
            "coordination_type": "mock",
            "result": "Mock coordination completed - AutoGen not available",
            "conversation_rounds": 3
        
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {}
            "total_agents": len(self.agents),
            "agent_names": list(self.agents.keys()),
            "autogen_available": AUTOGEN_AVAILABLE,
            "redis_connected": self.redis_client is not None,
            "group_chat_active": self.group_chat is not None
        

# Global coordinator instance
coordinator = AutoGenCoordinator()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {}
        "status": "healthy",
        "service": "autogen-coordinator",
        "agents": len(coordinator.agents),
        "autogen_available": AUTOGEN_AVAILABLE
    

@app.get("/status")
async def get_status():
    """Get detailed status"""
    return coordinator.get_agent_status()

@app.post("/coordinate")
async def coordinate_agents(task: dict):
    """Coordinate agents for a task"""
    try:
        result = await coordinator.coordinate_task(task)
        return result
    except Exception as e:
        logger.error(str(f"Coordination error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    return {}
        "agents": list(coordinator.agents.keys()),
        "count": len(coordinator.agents),
        "autogen_available": AUTOGEN_AVAILABLE,
        "group_chat_active": coordinator.group_chat is not None
    

@app.get("/metrics")
async def get_metrics():
    """Get performance metrics"""
    uptime = (datetime.now() - coordinator.start_time).total_seconds()
    return {}
        **coordinator.performance_metrics,
        "uptime_seconds": uptime,
        "uptime_formatted": str(datetime.now() - coordinator.start_time),
        "tasks_per_minute": coordinator.performance_metrics["total_tasks"] / max(uptime / 60, 1),
        "success_rate": ()
            coordinator.performance_metrics["successful_tasks"] /
            max(coordinator.performance_metrics["total_tasks"], 1) * 100
        
    

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    if task_id in coordinator.task_history:
        return coordinator.task_history[task_id]
    
    # Try Redis if not in memory
    if coordinator.redis_client:
        try:
            task_data = coordinator.redis_client.get(f"task:{task_id}")
            if task_data:
                return json.loads(task_data)
        except Exception as e:
            logger.warning(str(f"Redis task lookup failed: {e}")
    
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.get("/tasks")
async def list_recent_tasks():
    """List recent tasks"""
    return {}
        "recent_tasks": list(coordinator.task_history.keys())[-10:],
        "total_tasks": len(coordinator.task_history),
        "active_tasks": []
            task_id for task_id, task_data in coordinator.task_history.items()
            if task_data.get("status") == "in_progress"
        
    

@app.post("/agents/reset")
async def reset_agents():
    """Reset and reinitialize agents"""
    try:
        if AUTOGEN_AVAILABLE:
            coordinator._initialize_autogen_agents()
        else:
            coordinator._initialize_mock_agents()
        
        return {}
            "status": "success",
            "message": "Agents reset successfully",
            "agents": list(coordinator.agents.keys())
        
    except Exception as e:
        logger.error(str(f"Agent reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/health-check")
async def comprehensive_health_check():
    """Comprehensive system health check"""
    health_status = {}
        "overall_status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    
    
    # Check AutoGen availability
    health_status["components"]["autogen"] = {}
        "status": "healthy" if AUTOGEN_AVAILABLE else "unavailable",
        "available": AUTOGEN_AVAILABLE,
        "agents_initialized": len(coordinator.agents) > 0
    
    
    # Check Redis connection
    redis_healthy = False
    try:
        if coordinator.redis_client:
            coordinator.redis_client.ping()
            redis_healthy = True
    except Exception as e:
        logger.warning(str(f"Redis health check failed: {e}")
    
    health_status["components"]["redis"] = {}
        "status": "healthy" if redis_healthy else "unhealthy",
        "connected": redis_healthy
    
    
    # Check agent status
    agent_status = "healthy" if coordinator.agents else "no_agents"
    health_status["components"]["agents"] = {}
        "status": agent_status,
        "count": len(coordinator.agents),
        "names": list(coordinator.agents.keys())
    
    
    # Overall health determination
    if not AUTOGEN_AVAILABLE:
        health_status["overall_status"] = "degraded"
    elif not redis_healthy:
        health_status["overall_status"] = "warning"
    
    return health_status

@app.get("/system/info")
async def system_info():
    """Get detailed system information"""
    return {}
        "service": "autogen-coordinator",
        "version": "1.0.0",
        "autogen_available": AUTOGEN_AVAILABLE,
        "start_time": coordinator.start_time.isoformat(),
        "uptime": str(datetime.now() - coordinator.start_time),
        "python_version": sys.version,
        "environment": {}
            "redis_url": os.getenv("REDIS_URL", "not_set"),
            "openai_api_configured": bool(os.getenv("OPENAI_API_KEY")),
            "ollama_host": os.getenv("OLLAMA_HOST", "not_set"),
            "max_rounds": os.getenv("MAX_ROUND", "10")
        },
        "performance_metrics": coordinator.performance_metrics
    

def main():
    """Main entry point"""
    port = int(os.getenv("SERVICE_PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(str(f"{SYMBOLS['rocket']} Starting AutoGen Coordinator on {host}:{port}")
    
    uvicorn.run()
        app, 
        host=host, 
        port=port,
        log_level="info"
    

if __name__ == "__main__":
    main()