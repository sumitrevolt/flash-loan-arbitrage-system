# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
import os

from dataclasses import dataclass, field
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiohttp
import pika
import psycopg2
import redis
import uvicorn
"""
Master Coordination System
==========================
Unified orchestrator for managing:
- 21 MCP Servers
- 10 AI Agents
- LangChain Multi-Agent System
- AutoGen Framework
"""



# Configure logging

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

logging.basicConfig()
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[]
        logging.FileHandler('/app/logs/master_coordinator.log'),
        logging.StreamHandler()
    

logger = logging.getLogger(__name__)

app = FastAPI(title="Master Coordination System", version="1.0.0")

# Add CORS middleware
app.add_middleware()
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],


class ServiceType(Enum):
    MCP_SERVER = "mcp_server"
    AI_AGENT = "ai_agent"
    LANGCHAIN_AGENT = "langchain_agent"
    AUTOGEN_AGENT = "autogen_agent"

@dataclass
class ServiceInfo:
    id: str
    name: str
    type: ServiceType
    url: str
    status: str
    health_check_url: str
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TaskRequest(BaseModel):
    task_id: str
    task_type: str
    description: str
    priority: int = 1
    max_retries: int = 3
    timeout: int = 300
    target_services: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class MasterCoordinator:
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.redis_client: Optional[Any] = None
        self.rabbitmq_connection: Optional[Any] = None
        self.postgres_connection: Optional[Any] = None
        self.task_queue: asyncio.Queue[TaskRequest] = asyncio.Queue()
        self.is_running: bool = False
        
        # Service registries
        self.mcp_servers: Dict[str, ServiceInfo] = {}
        self.ai_agents: Dict[str, ServiceInfo] = {}
        self.langchain_agents: Dict[str, ServiceInfo] = {}
        self.autogen_agents: Dict[str, ServiceInfo] = {}
        
        # Load balancing
        self.load_balancer = LoadBalancer()
        
    async def initialize(self):
        """Initialize the master coordination system"""
        try:
            logger.info("Initializing Master Coordination System...")
            
            # Initialize connections
            await self._init_redis()
            await self._init_rabbitmq()
            await self._init_postgres()
            
            # Discover and register services
            await self._discover_services()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.is_running = True
            logger.info("Master Coordination System initialized successfully")
            
        except Exception as e:
            logger.error(str(f"Failed to initialize Master Coordinator: {e}")
            raise
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        redis_url = os.getenv("REDIS_URL", "redis://redis-master:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True, decode_responses=True, encoding="utf-8")
            await asyncio.get_event_loop().run_in_executor(None, lambda: self.redis_client.ping())
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(str(f"Failed to connect to Redis: {e}")
            raise
    
    async def _init_rabbitmq(self):
        """Initialize RabbitMQ connection"""
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq-master:5672/")
        try:
            connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            self.rabbitmq_connection = connection
            logger.info("RabbitMQ connection established")
        except Exception as e:
            logger.error(str(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        postgres_url = os.getenv("POSTGRES_URL", "postgresql://user:pass@postgres-master:5432/master_coordination")
        try:
            self.postgres_connection = psycopg2.connect(postgres_url)
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(str(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def _discover_services(self):
        """Discover and register all services"""
        logger.info("Discovering services...")
        
        # Discover MCP servers (21 servers)
        for i in range(21):
            service_id = f"mcp_server_{i+1}"
            service_info = ServiceInfo()
                id=service_id,
                name=f"MCP Server {i+1}",
                type=ServiceType.MCP_SERVER,
                url=f"http://mcp-server-pool:{9000+i}",
                status="unknown",
                health_check_url=f"http://mcp-server-pool:{9000+i}/health"
            
            self.services[service_id] = service_info
            self.mcp_servers[service_id] = service_info
        
        # Discover AI agents (10 agents)
        for i in range(10):
            service_id = f"ai_agent_{i+1}"
            service_info = ServiceInfo()
                id=service_id,
                name=f"AI Agent {i+1}",
                type=ServiceType.AI_AGENT,
                url=f"http://ai-agents-pool:{9100+i}",
                status="unknown",
                health_check_url=f"http://ai-agents-pool:{9100+i}/health"
            
            self.services[service_id] = service_info
            self.ai_agents[service_id] = service_info
        
        # Register LangChain agents
        langchain_services = []
            ("langchain_coordinator", "http://langchain-master:8000"),
            ("langchain_rag", "http://langchain-master:8002"),
            ("langchain_code_interpreter", "http://langchain-master:8004")
        
        
        for name, url in langchain_services:
            service_info = ServiceInfo()
                id=name,
                name=name.replace("_", " ").title(),
                type=ServiceType.LANGCHAIN_AGENT,
                url=url,
                status="unknown",
                health_check_url=f"{url}/health"
            
            self.services[name] = service_info
            self.langchain_agents[name] = service_info
        
        # Register AutoGen agents
        autogen_services = []
            ("autogen_coordinator", "http://autogen-master:8000"),
            ("autogen_group_chat", "http://autogen-master:8001"),
            ("autogen_code_executor", "http://autogen-master:8002")
        
        
        for name, url in autogen_services:
            service_info = ServiceInfo()
                id=name,
                name=name.replace("_", " ").title(),
                type=ServiceType.AUTOGEN_AGENT,
                url=url,
                status="unknown",
                health_check_url=f"{url}/health"
            
            self.services[name] = service_info
            self.autogen_agents[name] = service_info
        
        logger.info(str(f"Discovered {len(self.services} services")
    
    async def _start_background_tasks(self):
        """Start background monitoring and coordination tasks"""
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._task_processor())
        asyncio.create_task(self._load_balancer_monitor())
        logger.info("Background tasks started")
    
    async def _health_check_loop(self):
        """Continuous health checking of all services"""
        while self.is_running:
            try:
                for service_id, service in self.services.items():
                    health_status = await self._check_service_health(service)
                    service.status = health_status
                    service.last_health_check = datetime.now()
                    
                    # Update Redis with service status
                    self.redis_client.hset()
                        f"service:{service_id}",
                        mapping={}
                            "status": health_status,
                            "last_check": service.last_health_check.isoformat(),
                            "url": service.url
                        
                    
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(str(f"Health check error: {e}")
                await asyncio.sleep(60)
    
    async def _check_service_health(self, service: ServiceInfo) -> str:
        """Check health of a specific service"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(service.health_check_url) as response:
                    if response.status == 200:
                        return "healthy"
                    else:
                        return f"unhealthy_{response.status}"
        except Exception as e:
            return f"unreachable_{str(e)[:50]}"
    
    async def _task_processor(self):
        """Process coordination tasks"""
        while self.is_running:
            try:
                task = await self.task_queue.get()
                await self._process_task(task)
                self.task_queue.task_done()
            except Exception as e:
                logger.error(str(f"Task processing error: {e}")
    
    async def _process_task(self, task: TaskRequest):
        """Process a coordination task"""
        logger.info(str(f"Processing task: {task.task_id}")
        
        # Select appropriate services based on task type
        target_services = self._select_services_for_task(task)
        
        # Execute task across selected services
        results = await self._execute_distributed_task(task, target_services)
        
        # Store results
        await self._store_task_results(task.task_id, results)
        
        logger.info(str(f"Task {task.task_id} completed")
    
    def _select_services_for_task(self, task: TaskRequest) -> List[ServiceInfo]:
        """Select appropriate services for a task"""
        if task.target_services:
            return [self.services[sid] for sid in task.target_services if sid in self.services]
        
        # Auto-select based on task type
        if task.task_type == "mcp_operation":
            return list(self.mcp_servers.values())
        elif task.task_type == "ai_analysis":
            return list(self.ai_agents.values())
        elif task.task_type == "langchain_reasoning":
            return list(self.langchain_agents.values())
        elif task.task_type == "autogen_collaboration":
            return list(self.autogen_agents.values())
        else:
            # Default: use all healthy services
            return [s for s in self.services.values() if s.status == "healthy"]
    
    async def _execute_distributed_task(self, task: TaskRequest, services: List[ServiceInfo]) -> Dict[str, Any]:
        """Execute task across multiple services"""
        results = {}
        
        for service in services:
            if service.status != "healthy":
                continue
                
            try:
                result = await self._call_service(service, task)
                results[service.id] = result
            except Exception as e:
                logger.error(str(f"Service {service.id} failed: {e}")
                results[service.id] = {"error": str(e)}
        
        return results
    
    async def _call_service(self, service: ServiceInfo, task: TaskRequest) -> Dict[str, Any]:
        """Call a specific service with a task"""
        async with aiohttp.ClientSession() as session:
            payload = {}
                "task_id": task.task_id,
                "task_type": task.task_type,
                "description": task.description,
                "metadata": task.metadata
            
            
            async with session.post(f"{service.url}/process", json=payload) as response:
                return await response.json()
    
    async def _store_task_results(self, task_id: str, results: Dict[str, Any]):
        """Store task results in Redis"""
        self.redis_client.hset(f"task_results:{task_id}", mapping={)}
            "results": json.dumps(results, ensure_ascii=True, default=str),
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        
    
    async def _load_balancer_monitor(self):
        """Monitor and optimize load balancing"""
        while self.is_running:
            try:
                await self.load_balancer.optimize_distribution()
                await asyncio.sleep(60)  # Optimize every minute
            except Exception as e:
                logger.error(str(f"Load balancer error: {e}")
                await asyncio.sleep(60)

class LoadBalancer:
    def __init__(self):
        self.service_loads = {}
        self.optimization_strategies = ["round_robin", "least_connections", "resource_based"]
    
    async def optimize_distribution(self):
        """Optimize service load distribution"""
        # Implementation for load balancing optimization
        pass

# Global coordinator instance
coordinator = MasterCoordinator()

# API Routes
@app.on_event("startup")
async def startup_event():
    await coordinator.initialize()

@app.get("/")
async def root():
    return {}
        "service": "Master Coordination System",
        "version": "1.0.0",
        "status": "running" if coordinator.is_running else "initializing",
        "timestamp": datetime.now().isoformat()
    

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {}
        "status": "healthy" if coordinator.is_running else "initializing",
        "services_count": len(coordinator.services),
        "healthy_services": len([s for s in coordinator.services.values() if s.status == "healthy"]),
        "timestamp": datetime.now().isoformat()
    

@app.get("/services")
async def list_services():
    """List all registered services"""
    services_by_type = {}
        "mcp_servers": len(coordinator.mcp_servers),
        "ai_agents": len(coordinator.ai_agents),
        "langchain_agents": len(coordinator.langchain_agents),
        "autogen_agents": len(coordinator.autogen_agents)
    
    
    service_status = {}
    for service_id, service in coordinator.services.items():
        service_status[service_id] = {}
            "name": service.name,
            "type": service.type.value,
            "status": service.status,
            "url": service.url,
            "last_check": service.last_health_check.isoformat() if service.last_health_check else None
        
    
    return {}
        "summary": services_by_type,
        "services": service_status
    

@app.post("/coordinate")
async def coordinate_task(task: TaskRequest):
    """Submit a task for coordination"""
    try:
        await coordinator.task_queue.put(task)
        return {}
            "task_id": task.task_id,
            "status": "queued",
            "message": "Task submitted for coordination"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}/status")
async def get_task_status(task_id: str):
    """Get task status and results"""
    try:
        results = coordinator.redis_client.hgetall(f"task_results:{task_id}")
        if not results:
            return {"task_id": task_id, "status": "not_found"}
        
        return {}
            "task_id": task_id,
            "status": results.get("status", "unknown"),
            "results": json.loads(results.get("results", "{}")),
            "timestamp": results.get("timestamp")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    healthy_services = len([s for s in coordinator.services.values() if s.status == "healthy"])
    total_services = len(coordinator.services)
    
    return {}
        "total_services": total_services,
        "healthy_services": healthy_services,
        "unhealthy_services": total_services - healthy_services,
        "uptime": "running" if coordinator.is_running else "stopped",
        "load_balancer_active": True,
        "timestamp": datetime.now().isoformat()
    

if __name__ == "__main__":
    # Create logs directory
    os.makedirs("/app/logs", exist_ok=True)
    
    # Start the coordination system
    uvicorn.run()
        "master_coordinator:app",
        host="0.0.0.0",
        port=8500,
        log_level="info",
        reload=False
    

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportOptionalMemberAccess=false, reportUntypedBaseClass=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false