#!/usr/bin/env python3
"""
Coordination Manager for MCP Servers and AI Agents
Manages communication and task distribution across all services
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field  # type: ignore
from enum import Enum  # type: ignore

# Suppressed unresolved imports
import aioredis  # type: ignore
import asyncpg  # type: ignore
import aio_pika  # type: ignore
from aio_pika import Message, DeliveryMode  # type: ignore

logger = logging.getLogger("CoordinationManager")

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned" 
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ServiceType(Enum):
    MCP_SERVER = "mcp_server"
    AI_AGENT = "ai_agent"
    ORCHESTRATOR = "orchestrator"

@dataclass
class ServiceInfo:
    """Information about a service"""
    name: str
    service_type: ServiceType
    status: str
    last_heartbeat: datetime
    capabilities: List[str] = field(default_factory=list)
    load: float = 0.0
    health_score: float = 1.0
    endpoint: str = ""

@dataclass 
class Task:
    """Task definition"""
    id: str
    task_type: str
    parameters: Dict[str, Any]
    priority: int
    status: TaskStatus
    assigned_to: Optional[str]
    created_at: datetime
    target_services: Optional[List[str]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CoordinationManager:
    """Manages coordination between all services in the system"""
    
    def __init__(self, redis_client: aioredis.Redis, postgres_pool: asyncpg.Pool, rabbitmq_connection: aio_pika.Connection):
        self.redis = redis_client
        self.postgres = postgres_pool
        self.rabbitmq = rabbitmq_connection
        
        self.services: Dict[str, ServiceInfo] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.PriorityQueue[Any] = asyncio.PriorityQueue()
        
        # RabbitMQ components
        self.channel: Optional[aio_pika.Channel] = None  # type: ignore
        self.coordination_exchange: Optional[aio_pika.Exchange] = None  # type: ignore
        
        # Task distribution settings
        self.max_tasks_per_service = 5
        self.heartbeat_timeout = 300  # 5 minutes
        
        # Initialize async components
        asyncio.create_task(self._initialize_rabbitmq())
        asyncio.create_task(self._initialize_database())
        asyncio.create_task(self._start_coordination_loops())
    
    async def _initialize_rabbitmq(self):
        """Initialize RabbitMQ components"""
        try:
            self.channel = await self.rabbitmq.channel()
            
            # Declare coordination exchange
            self.coordination_exchange = await self.channel.declare_exchange(
                "coordination",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare task queue
            task_queue = await self.channel.declare_queue(
                "system_tasks",
                durable=True
            )
            
            # Declare heartbeat queue
            heartbeat_queue = await self.channel.declare_queue(
                "service_heartbeats",
                durable=False
            )
            
            # Set up consumers
            await task_queue.consume(self._handle_task_message)
            await heartbeat_queue.consume(self._handle_heartbeat_message)
            
            logger.info("✅ RabbitMQ coordination components initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RabbitMQ: {e}")
    
    async def _initialize_database(self):
        """Initialize database tables"""
        try:
            async with self.postgres.acquire() as conn:
                # Create services table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS services (
                        name TEXT PRIMARY KEY,
                        service_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        last_heartbeat TIMESTAMP DEFAULT NOW(),
                        capabilities JSONB DEFAULT '[]',
                        load_value FLOAT DEFAULT 0.0,
                        health_score FLOAT DEFAULT 1.0,
                        endpoint TEXT DEFAULT ''
                    )
                """)
                
                # Create tasks table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS coordination_tasks (
                        id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        parameters JSONB NOT NULL,
                        priority INTEGER DEFAULT 1,
                        status TEXT NOT NULL,
                        assigned_to TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        target_services JSONB,
                        result JSONB,
                        error TEXT
                    )
                """)
                
                # Create task history table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS task_history (
                        id SERIAL PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        status_change TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT NOW(),
                        details JSONB
                    )
                """)
                
                logger.info("✅ Database tables initialized")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
    
    async def _start_coordination_loops(self):
        """Start background coordination loops"""
        await asyncio.sleep(5)  # Wait for initialization
        
        asyncio.create_task(self._service_discovery_loop())
        asyncio.create_task(self._task_distribution_loop())
        asyncio.create_task(self._health_monitoring_loop())
        asyncio.create_task(self._cleanup_loop())
        
        logger.info("✅ Coordination loops started")
    
    async def submit_task(self, task_type: str, parameters: Dict[str, Any], 
                         priority: int = 1, target_services: Optional[List[str]] = None) -> str:
        """Submit a new task for execution"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            task_type=task_type,
            parameters=parameters,
            priority=priority,
            status=TaskStatus.PENDING,
            assigned_to=None,
            created_at=datetime.now(),
            target_services=target_services
        )
        
        self.tasks[task_id] = task
        
        # Store in database
        await self._store_task_in_db(task)
        
        # Add to priority queue (negative priority for max-heap behavior)
        await self.task_queue.put((-priority, task_id))
        
        # Publish task notification
        if self.coordination_exchange:
            message = Message(
                json.dumps({
                    "type": "new_task",
                    "task_id": task_id,
                    "task_type": task_type,
                    "priority": priority
                }).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            )
            
            await self.coordination_exchange.publish(
                message,
                routing_key="tasks.new"
            )
        
        logger.info(f"📋 Submitted task {task_id}: {task_type}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                "id": task.id,
                "type": task.task_type,
                "status": task.status.value,
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
                "result": task.result,
                "error": task.error
            }
        
        # Check database
        try:
            async with self.postgres.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM coordination_tasks WHERE id = $1",
                    task_id
                )
                
                if row:
                    return {
                        "id": row["id"],
                        "type": row["task_type"],
                        "status": row["status"],
                        "assigned_to": row["assigned_to"],
                        "created_at": row["created_at"].isoformat(),
                        "result": row["result"],
                        "error": row["error"]
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get task status from DB: {e}")
        
        return None
    
    async def register_service(self, name: str, service_type: ServiceType, capabilities: List[str], endpoint: str = ""):
        """Register a service with the coordinator"""
        service = ServiceInfo(
            name=name,
            service_type=service_type,
            status="active",
            last_heartbeat=datetime.now(),
            capabilities=capabilities,
            endpoint=endpoint
        )
        
        self.services[name] = service
        
        # Store in database
        await self._store_service_in_db(service)
        
        # Store in Redis for fast access
        service_data = {
            "service_type": service_type.value,
            "status": service.status,
            "capabilities": capabilities,
            "endpoint": endpoint,
            "last_heartbeat": service.last_heartbeat.isoformat()
        }
        
        await self.redis.hset(f"service:{name}", mapping=service_data)
        
        logger.info(f"📝 Registered service: {name} ({service_type.value})")
    
    async def update_service_heartbeat(self, service_name: str, load: float = 0.0, health_score: float = 1.0):
        """Update service heartbeat"""
        if service_name in self.services:
            service = self.services[service_name]
            service.last_heartbeat = datetime.now()
            service.load = load
            service.health_score = health_score
            
            # Update in Redis
            await self.redis.hset(
                f"service:{service_name}",
                mapping={
                    "last_heartbeat": service.last_heartbeat.isoformat(),
                    "load": str(load),
                    "health_score": str(health_score)
                }
            )
        
        logger.debug(f"💓 Heartbeat updated for {service_name}")
    
    async def coordinate_services(self):
        """Main coordination logic called periodically"""
        try:
            # Update service statuses
            await self._update_service_statuses()
            
            # Balance load across services
            await self._balance_service_load()
            
            # Check for stuck tasks
            await self._handle_stuck_tasks()
            
            # Optimize task distribution
            await self._optimize_task_distribution()
            
        except Exception as e:
            logger.error(f"Coordination error: {e}")
    
    async def _service_discovery_loop(self):
        """Discover and monitor services"""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                
                # Discover MCP servers
                for i in range(1, 22):  # 21 MCP servers
                    server_name = f"mcp_server_{i:02d}"
                    if server_name not in self.services:
                        # Try to discover service
                        if await self._ping_service(f"http://fl_{server_name}:400{i}"):
                            await self.register_service(
                                server_name,
                                ServiceType.MCP_SERVER,
                                [f"mcp_capability_{i}"],
                                f"http://fl_{server_name}:400{i}"
                            )
                
                # Discover AI agents
                for i in range(1, 11):  # 10 AI agents
                    agent_name = f"agent_{i:02d}"
                    if agent_name not in self.services:
                        # Try to discover service
                        if await self._ping_service(f"http://fl_agent_{agent_name}:500{i}"):
                            await self.register_service(
                                agent_name,
                                ServiceType.AI_AGENT,
                                [f"ai_capability_{i}"],
                                f"http://fl_agent_{agent_name}:500{i}"
                            )
                
                logger.debug("🔍 Service discovery completed")
                
            except Exception as e:
                logger.error(f"Service discovery error: {e}")
    
    async def _task_distribution_loop(self):
        """Distribute tasks to available services"""
        while True:
            try:
                if not self.task_queue.empty():
                    _, task_id = await self.task_queue.get()
                    
                    if task_id in self.tasks:
                        task = self.tasks[task_id]
                        
                        if task.status == TaskStatus.PENDING:
                            assigned_service = await self._find_best_service_for_task(task)
                            
                            if assigned_service:
                                await self._assign_task_to_service(task, assigned_service)
                            else:
                                # Put back in queue with lower priority
                                await self.task_queue.put((-task.priority + 1, task_id))
                                await asyncio.sleep(5)  # Wait before retry
                
                await asyncio.sleep(1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Task distribution error: {e}")
    
    async def _health_monitoring_loop(self):
        """Monitor service health"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                current_time = datetime.now()
                unhealthy_services = []
                
                for name, service in self.services.items():
                    time_since_heartbeat = current_time - service.last_heartbeat
                    
                    if time_since_heartbeat.total_seconds() > self.heartbeat_timeout:
                        service.status = "unhealthy"
                        unhealthy_services.append(name)
                        logger.warning(f"⚠️ Service {name} is unhealthy (no heartbeat for {time_since_heartbeat})")
                    elif service.status == "unhealthy" and time_since_heartbeat.total_seconds() <= 60:
                        service.status = "active"
                        logger.info(f"✅ Service {name} is healthy again")
                
                # Update unhealthy services in Redis
                if unhealthy_services:
                    await self.redis.sadd("unhealthy_services", *unhealthy_services)
                else:
                    await self.redis.delete("unhealthy_services")
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
    
    async def _cleanup_loop(self):
        """Clean up old tasks and data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Clean up completed tasks older than 24 hours
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                completed_tasks = [
                    task_id for task_id, task in self.tasks.items()
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                    and task.created_at < cutoff_time
                ]
                
                for task_id in completed_tasks:
                    del self.tasks[task_id]
                
                # Clean up database
                async with self.postgres.acquire() as conn:
                    await conn.execute(
                        "DELETE FROM coordination_tasks WHERE created_at < $1 AND status IN ('completed', 'failed', 'cancelled')",
                        cutoff_time
                    )
                
                logger.info(f"🧹 Cleaned up {len(completed_tasks)} old tasks")
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def _service_can_handle_task(self, service: ServiceInfo, task: Task) -> bool:
        """Check if a service can handle a specific task"""
        # This would contain logic to match task types with service capabilities
        # For now, return True for all active services
        return True
    
    def _find_best_service_for_task(self, task: Task) -> Optional[str]:
        """Find the best service to handle a task"""
        candidate_services = []
        
        # Filter services based on target services if specified
        if task.target_services:
            candidate_services = [
                name for name, service in self.services.items()
                if name in task.target_services and service.status == "active"
            ]
        else:
            # Find services with relevant capabilities
            candidate_services = [
                name for name, service in self.services.items()
                if service.status == "active" and self._service_can_handle_task(service, task)
            ]
        
        if not candidate_services:
            return None
        
        # Sort by load and health score
        candidate_services.sort(key=lambda name: (
            self.services[name].load,
            -self.services[name].health_score
        ))
        
        return candidate_services[0]
    
    async def _assign_task_to_service(self, task: Task, service_name: str):
        """Assign a task to a specific service"""
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = service_name
        
        # Update in database
        await self._update_task_in_db(task)
        
        # Send task to service via RabbitMQ
        if self.coordination_exchange:
            message = Message(
                json.dumps({
                    "task_id": task.id,
                    "task_type": task.task_type,
                    "parameters": task.parameters,
                    "priority": task.priority
                }).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            )
            
            await self.coordination_exchange.publish(
                message,
                routing_key=f"tasks.{service_name}"
            )
        
        logger.info(f"📤 Assigned task {task.id} to {service_name}")
    
    async def _handle_task_message(self, message: aio_pika.IncomingMessage):  # type: ignore
        """Handle incoming task messages"""
        async with message.process():  # type: ignore
            try:
                data = json.loads(message.body.decode())  # type: ignore
                # Handle task status updates, results, etc.
                logger.debug(f"Received task message: {data}")
                
            except Exception as e:
                logger.error(f"Failed to process task message: {e}")
    
    async def _handle_heartbeat_message(self, message: aio_pika.IncomingMessage):  # type: ignore
        """Handle incoming heartbeat messages"""
        async with message.process():  # type: ignore
            try:
                data = json.loads(message.body.decode())  # type: ignore
                service_name = data.get("service_name")
                load = data.get("load", 0.0)
                health_score = data.get("health_score", 1.0)
                
                if service_name:
                    await self.update_service_heartbeat(service_name, load, health_score)
                
            except Exception as e:
                logger.error(f"Failed to process heartbeat message: {e}")
    
    async def _store_task_in_db(self, task: Task):
        """Store task in database"""
        try:
            async with self.postgres.acquire() as conn:
                await conn.execute("""
                    INSERT INTO coordination_tasks 
                    (id, task_type, parameters, priority, status, assigned_to, created_at, target_services)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    assigned_to = EXCLUDED.assigned_to
                """, 
                task.id, task.task_type, json.dumps(task.parameters), task.priority,
                task.status.value, task.assigned_to, task.created_at, 
                json.dumps(task.target_services) if task.target_services else None)
                
        except Exception as e:
            logger.error(f"Failed to store task in DB: {e}")
    
    async def _update_task_in_db(self, task: Task):
        """Update task in database"""
        try:
            async with self.postgres.acquire() as conn:
                await conn.execute("""
                    UPDATE coordination_tasks 
                    SET status = $2, assigned_to = $3, result = $4, error = $5
                    WHERE id = $1
                """, 
                task.id, task.status.value, task.assigned_to,
                json.dumps(task.result) if task.result else None,
                task.error)
                
        except Exception as e:
            logger.error(f"Failed to update task in DB: {e}")
    
    async def _store_service_in_db(self, service: ServiceInfo):
        """Store service in database"""
        try:
            async with self.postgres.acquire() as conn:
                await conn.execute("""
                    INSERT INTO services 
                    (name, service_type, status, last_heartbeat, capabilities, load_value, health_score, endpoint)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (name) DO UPDATE SET
                    status = EXCLUDED.status,
                    last_heartbeat = EXCLUDED.last_heartbeat,
                    load_value = EXCLUDED.load_value,
                    health_score = EXCLUDED.health_score
                """, 
                service.name, service.service_type.value, service.status,
                service.last_heartbeat, json.dumps(service.capabilities),
                service.load, service.health_score, service.endpoint)
                
        except Exception as e:
            logger.error(f"Failed to store service in DB: {e}")
    
    async def _ping_service(self, endpoint: str) -> bool:
        """Ping a service to check if it's available"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/health", timeout=5) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _update_service_statuses(self):
        """Update service statuses"""
        # Implementation for updating service statuses
        pass
    
    async def _balance_service_load(self):
        """Balance load across services"""
        # Implementation for load balancing
        pass
    
    async def _handle_stuck_tasks(self):
        """Handle tasks that are stuck"""
        # Implementation for handling stuck tasks
        pass
    
    async def _optimize_task_distribution(self):
        """Optimize task distribution"""
        # Implementation for optimization
        pass
