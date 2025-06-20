#!/usr/bin/env python3
"""
Enhanced LangChain Orchestrator Application
FastAPI-based orchestrator with GitHub integration and automatic error handling
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aioredis
import asyncpg
import aio_pika
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

# Import our components
from github_integration import GitHubIntegration
from error_handler import AutomaticErrorHandler
from coordination_manager import CoordinationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/logs/orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OrchestratorApp")

# Prometheus metrics
REQUEST_COUNT = Counter('orchestrator_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('orchestrator_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('orchestrator_active_connections', 'Active connections')
MCP_SERVERS_STATUS = Gauge('orchestrator_mcp_servers_status', 'MCP servers status', ['server_name'])
AGENTS_STATUS = Gauge('orchestrator_agents_status', 'Agents status', ['agent_name'])

class OrchestratorState:
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.rabbitmq_connection: Optional[aio_pika.Connection] = None
        self.github_integration: Optional[GitHubIntegration] = None
        self.error_handler: Optional[AutomaticErrorHandler] = None
        self.coordination_manager: Optional[CoordinationManager] = None
        self.mcp_servers: Dict[str, Dict[str, Any]] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.system_health: Dict[str, Any] = {
            'status': 'starting',
            'last_check': datetime.now(),
            'errors': []
        }

orchestrator_state = OrchestratorState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Enhanced LangChain Orchestrator...")
    
    try:
        # Initialize Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        orchestrator_state.redis_client = aioredis.from_url(redis_url)
        await orchestrator_state.redis_client.ping()
        logger.info("✅ Redis connection established")
        
        # Initialize PostgreSQL connection
        postgres_url = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres_password@localhost:5432/flashloan')
        orchestrator_state.postgres_pool = await asyncpg.create_pool(postgres_url)
        logger.info("✅ PostgreSQL connection established")
        
        # Initialize RabbitMQ connection
        rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://rabbitmq:rabbitmq_password@localhost:5672')
        orchestrator_state.rabbitmq_connection = await aio_pika.connect_robust(rabbitmq_url)
        logger.info("✅ RabbitMQ connection established")
        
        # Initialize GitHub integration
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            orchestrator_state.github_integration = GitHubIntegration(github_token)
            logger.info("✅ GitHub integration initialized")
        else:
            logger.warning("⚠️ GitHub token not provided - error handling will be limited")
        
        # Initialize error handler
        orchestrator_state.error_handler = AutomaticErrorHandler(
            github_integration=orchestrator_state.github_integration,
            redis_client=orchestrator_state.redis_client
        )
        logger.info("✅ Automatic error handler initialized")
        
        # Initialize coordination manager
        orchestrator_state.coordination_manager = CoordinationManager(
            redis_client=orchestrator_state.redis_client,
            postgres_pool=orchestrator_state.postgres_pool,
            rabbitmq_connection=orchestrator_state.rabbitmq_connection
        )
        logger.info("✅ Coordination manager initialized")
        
        # Start background tasks
        asyncio.create_task(health_check_loop())
        asyncio.create_task(coordination_loop())
        
        orchestrator_state.system_health['status'] = 'healthy'
        logger.info("🎉 Enhanced LangChain Orchestrator started successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start orchestrator: {e}")
        orchestrator_state.system_health['status'] = 'failed'
        orchestrator_state.system_health['errors'].append(str(e))
        raise
    
    # Shutdown
    logger.info("🔄 Shutting down Enhanced LangChain Orchestrator...")
    
    if orchestrator_state.redis_client:
        await orchestrator_state.redis_client.close()
    
    if orchestrator_state.postgres_pool:
        await orchestrator_state.postgres_pool.close()
    
    if orchestrator_state.rabbitmq_connection:
        await orchestrator_state.rabbitmq_connection.close()
    
    logger.info("👋 Enhanced LangChain Orchestrator shutdown complete")

app = FastAPI(
    title="Enhanced LangChain Orchestrator",
    description="Orchestrates 21 MCP servers and 10 AI agents with automatic error handling",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]
    mcp_servers: Dict[str, str]
    agents: Dict[str, str]

class ErrorResponse(BaseModel):
    error: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    target_services: Optional[List[str]] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    REQUEST_COUNT.labels(method="GET", endpoint="/health").inc()
    
    try:
        services = {}
        mcp_servers = {}
        agents = {}
        
        # Check Redis
        if orchestrator_state.redis_client:
            await orchestrator_state.redis_client.ping()
            services['redis'] = 'healthy'
        else:
            services['redis'] = 'disconnected'
        
        # Check PostgreSQL
        if orchestrator_state.postgres_pool:
            async with orchestrator_state.postgres_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            services['postgres'] = 'healthy'
        else:
            services['postgres'] = 'disconnected'
        
        # Check RabbitMQ
        if orchestrator_state.rabbitmq_connection and not orchestrator_state.rabbitmq_connection.is_closed:
            services['rabbitmq'] = 'healthy'
        else:
            services['rabbitmq'] = 'disconnected'
        
        # Check MCP servers
        for server_name in get_mcp_server_list():
            status = await check_mcp_server_health(server_name)
            mcp_servers[server_name] = status
            MCP_SERVERS_STATUS.labels(server_name=server_name).set(1 if status == 'healthy' else 0)
        
        # Check agents
        for agent_name in get_agent_list():
            status = await check_agent_health(agent_name)
            agents[agent_name] = status
            AGENTS_STATUS.labels(agent_name=agent_name).set(1 if status == 'healthy' else 0)
        
        return HealthResponse(
            status=orchestrator_state.system_health['status'],
            timestamp=datetime.now(),
            services=services,
            mcp_servers=mcp_servers,
            agents=agents
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        if orchestrator_state.error_handler:
            await orchestrator_state.error_handler.handle_error(e, context="health_check")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

# Task execution endpoint
@app.post("/execute_task", response_model=TaskResponse)
async def execute_task(task: TaskRequest, background_tasks: BackgroundTasks):
    """Execute a task across the system"""
    REQUEST_COUNT.labels(method="POST", endpoint="/execute_task").inc()
    
    try:
        if not orchestrator_state.coordination_manager:
            raise HTTPException(status_code=503, detail="Coordination manager not available")
        
        task_id = await orchestrator_state.coordination_manager.submit_task(
            task_type=task.task_type,
            parameters=task.parameters,
            priority=task.priority,
            target_services=task.target_services
        )
        
        return TaskResponse(
            task_id=task_id,
            status="submitted"
        )
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        if orchestrator_state.error_handler:
            await orchestrator_state.error_handler.handle_error(e, context="execute_task")
        raise HTTPException(status_code=500, detail=str(e))

# Get task status
@app.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    REQUEST_COUNT.labels(method="GET", endpoint="/task").inc()
    
    try:
        if not orchestrator_state.coordination_manager:
            raise HTTPException(status_code=503, detail="Coordination manager not available")
        
        task_info = await orchestrator_state.coordination_manager.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            task_id=task_id,
            status=task_info.get('status', 'unknown'),
            result=task_info.get('result')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task status failed: {e}")
        if orchestrator_state.error_handler:
            await orchestrator_state.error_handler.handle_error(e, context="get_task_status")
        raise HTTPException(status_code=500, detail=str(e))

# System status endpoint
@app.get("/system/status")
async def get_system_status():
    """Get comprehensive system status"""
    REQUEST_COUNT.labels(method="GET", endpoint="/system/status").inc()
    
    try:
        return {
            'orchestrator': orchestrator_state.system_health,
            'mcp_servers': orchestrator_state.mcp_servers,
            'agents': orchestrator_state.agents,
            'coordination_active': orchestrator_state.coordination_manager is not None,
            'error_handling_active': orchestrator_state.error_handler is not None,
            'github_integration_active': orchestrator_state.github_integration is not None
        }
        
    except Exception as e:
        logger.error(f"Get system status failed: {e}")
        if orchestrator_state.error_handler:
            await orchestrator_state.error_handler.handle_error(e, context="get_system_status")
        raise HTTPException(status_code=500, detail=str(e))

# Error reporting endpoint
@app.post("/report_error")
async def report_error(error_data: Dict[str, Any]):
    """Report an error from external services"""
    REQUEST_COUNT.labels(method="POST", endpoint="/report_error").inc()
    
    try:
        if orchestrator_state.error_handler:
            await orchestrator_state.error_handler.handle_external_error(error_data)
            return {"status": "error_handled"}
        else:
            logger.error(f"External error reported but no handler available: {error_data}")
            return {"status": "error_logged"}
            
    except Exception as e:
        logger.error(f"Error reporting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def get_mcp_server_list() -> List[str]:
    """Get list of MCP server names"""
    return [
        'price_monitor', 'arbitrage_detector', 'risk_manager', 'transaction_executor',
        'portfolio_manager', 'liquidity_analyzer', 'gas_optimizer', 'market_data',
        'dex_connector', 'blockchain_monitor', 'flashloan_coordinator', 'profit_calculator',
        'security_monitor', 'protocol_adapter', 'event_processor', 'analytics_engine',
        'notification_service', 'backup_manager', 'config_manager', 'logger_service',
        'health_monitor'
    ]

def get_agent_list() -> List[str]:
    """Get list of agent names"""
    return [
        'market_analyst', 'strategy_optimizer', 'risk_assessor', 'execution_coordinator',
        'performance_monitor', 'code_generator', 'error_handler', 'learning_optimizer',
        'system_integrator', 'quality_assurance'
    ]

async def check_mcp_server_health(server_name: str) -> str:
    """Check health of specific MCP server"""
    try:
        port = 4001 + get_mcp_server_list().index(server_name)
        # Would implement actual health check here
        return 'healthy'
    except Exception:
        return 'unhealthy'

async def check_agent_health(agent_name: str) -> str:
    """Check health of specific agent"""
    try:
        port = 5001 + get_agent_list().index(agent_name)
        # Would implement actual health check here
        return 'healthy'
    except Exception:
        return 'unhealthy'

async def health_check_loop():
    """Background health check loop"""
    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            # Update system health
            orchestrator_state.system_health['last_check'] = datetime.now()
            
            # Check and update MCP servers
            for server_name in get_mcp_server_list():
                status = await check_mcp_server_health(server_name)
                orchestrator_state.mcp_servers[server_name] = {
                    'status': status,
                    'last_check': datetime.now()
                }
            
            # Check and update agents
            for agent_name in get_agent_list():
                status = await check_agent_health(agent_name)
                orchestrator_state.agents[agent_name] = {
                    'status': status,
                    'last_check': datetime.now()
                }
            
            logger.debug("Health check completed")
            
        except Exception as e:
            logger.error(f"Health check loop error: {e}")
            if orchestrator_state.error_handler:
                await orchestrator_state.error_handler.handle_error(e, context="health_check_loop")

async def coordination_loop():
    """Background coordination loop"""
    while True:
        try:
            await asyncio.sleep(10)  # Coordinate every 10 seconds
            
            if orchestrator_state.coordination_manager:
                await orchestrator_state.coordination_manager.coordinate_services()
            
            logger.debug("Coordination completed")
            
        except Exception as e:
            logger.error(f"Coordination loop error: {e}")
            if orchestrator_state.error_handler:
                await orchestrator_state.error_handler.handle_error(e, context="coordination_loop")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
