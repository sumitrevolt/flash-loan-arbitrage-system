"""
Flash Loan Task Orchestrator
A comprehensive task assignment and orchestration system for MCP servers and AI agents
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aioredis
import requests
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    id: str
    type: str
    description: str
    priority: TaskPriority
    assigned_agent: Optional[str] = None
    assigned_servers: List[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parameters: Dict[str, Any] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    dependencies: List[str] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.assigned_servers is None:
            self.assigned_servers = []
        if self.parameters is None:
            self.parameters = {}
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class WorkflowStep:
    task_type: str
    agent: str
    servers: List[str]
    parameters: Dict[str, Any]
    depends_on: List[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []

class TaskOrchestrator:
    def __init__(self, bridge_client=None):
        self.bridge_client = bridge_client
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        self.redis = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running = False
        
        # Agent capabilities mapping
        self.agent_capabilities = {
            "flashloan-agent-coordinator": {
                "servers": ["flashloan-mcp-coordinator"],
                "capabilities": ["coordination", "workflow_management", "agent_coordination"]
            },
            "flashloan-agent-arbitrage-bot": {
                "servers": ["flashloan-mcp-arbitrage", "flashloan-mcp-defi-analyzer"],
                "capabilities": ["arbitrage_detection", "price_analysis", "profit_calculation", "trade_execution"]
            },
            "flashloan-agent-data-collector": {
                "servers": ["flashloan-mcp-api-client", "flashloan-mcp-price-feed"],
                "capabilities": ["data_collection", "price_monitoring", "market_data", "api_integration"]
            },
            "flashloan-agent-risk-manager": {
                "servers": ["flashloan-mcp-risk-manager"],
                "capabilities": ["risk_assessment", "risk_monitoring", "compliance_check", "safety_analysis"]
            },
            "flashloan-agent-healer": {
                "servers": ["flashloan-mcp-monitoring"],
                "capabilities": ["system_healing", "error_recovery", "health_monitoring", "auto_repair"]
            },
            "flashloan-agent-liquidity-manager": {
                "servers": ["flashloan-mcp-liquidity"],
                "capabilities": ["liquidity_analysis", "pool_monitoring", "liquidity_optimization"]
            },
            "flashloan-agent-executor": {
                "servers": ["flashloan-mcp-flash-loan", "flashloan-mcp-blockchain"],
                "capabilities": ["transaction_execution", "blockchain_interaction", "flash_loan_execution"]
            },
            "flashloan-agent-reporter": {
                "servers": ["flashloan-mcp-database", "flashloan-mcp-notification"],
                "capabilities": ["reporting", "data_storage", "notification_sending", "analytics"]
            },
            "flashloan-agent-monitor": {
                "servers": ["flashloan-mcp-monitoring"],
                "capabilities": ["system_monitoring", "performance_tracking", "alert_generation"]
            },
            "flashloan-agent-analyzer": {
                "servers": ["flashloan-mcp-data-analyzer", "flashloan-mcp-price-feed"],
                "capabilities": ["data_analysis", "pattern_recognition", "trend_analysis", "market_analysis"]
            }
        }

        # Predefined workflows
        self.workflows = {
            "arbitrage_opportunity_detection": [
                WorkflowStep("collect_market_data", "flashloan-agent-data-collector", 
                           ["flashloan-mcp-price-feed", "flashloan-mcp-api-client"], {}),
                WorkflowStep("analyze_arbitrage", "flashloan-agent-arbitrage-bot", 
                           ["flashloan-mcp-arbitrage", "flashloan-mcp-defi-analyzer"], 
                           {}, depends_on=["collect_market_data"]),
                WorkflowStep("assess_risk", "flashloan-agent-risk-manager", 
                           ["flashloan-mcp-risk-manager"], 
                           {}, depends_on=["analyze_arbitrage"]),
                WorkflowStep("check_liquidity", "flashloan-agent-liquidity-manager", 
                           ["flashloan-mcp-liquidity"], 
                           {}, depends_on=["assess_risk"]),
                WorkflowStep("execute_arbitrage", "flashloan-agent-executor", 
                           ["flashloan-mcp-flash-loan", "flashloan-mcp-blockchain"], 
                           {}, depends_on=["check_liquidity"]),
                WorkflowStep("report_results", "flashloan-agent-reporter", 
                           ["flashloan-mcp-database", "flashloan-mcp-notification"], 
                           {}, depends_on=["execute_arbitrage"])
            ],
            "system_health_check": [
                WorkflowStep("monitor_system", "flashloan-agent-monitor", 
                           ["flashloan-mcp-monitoring"], {}),
                WorkflowStep("analyze_performance", "flashloan-agent-analyzer", 
                           ["flashloan-mcp-data-analyzer"], 
                           {}, depends_on=["monitor_system"]),
                WorkflowStep("heal_issues", "flashloan-agent-healer", 
                           ["flashloan-mcp-monitoring"], 
                           {}, depends_on=["analyze_performance"]),
                WorkflowStep("report_health", "flashloan-agent-reporter", 
                           ["flashloan-mcp-database", "flashloan-mcp-notification"], 
                           {}, depends_on=["heal_issues"])
            ],
            "market_analysis": [
                WorkflowStep("collect_market_data", "flashloan-agent-data-collector", 
                           ["flashloan-mcp-price-feed", "flashloan-mcp-api-client"], {}),
                WorkflowStep("analyze_trends", "flashloan-agent-analyzer", 
                           ["flashloan-mcp-data-analyzer", "flashloan-mcp-price-feed"], 
                           {}, depends_on=["collect_market_data"]),
                WorkflowStep("assess_opportunities", "flashloan-agent-arbitrage-bot", 
                           ["flashloan-mcp-defi-analyzer"], 
                           {}, depends_on=["analyze_trends"]),
                WorkflowStep("generate_report", "flashloan-agent-reporter", 
                           ["flashloan-mcp-database", "flashloan-mcp-notification"], 
                           {}, depends_on=["assess_opportunities"])
            ]
        }

    async def initialize(self):
        """Initialize the task orchestrator"""
        try:
            self.redis = aioredis.from_url("redis://localhost:6379", decode_responses=True)
            await self.redis.ping()
            logger.info("Connected to Redis for task management")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis = None

    async def start(self):
        """Start the task orchestrator"""
        await self.initialize()
        self.running = True
        
        # Start background tasks
        asyncio.create_task(self._task_processor())
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._workflow_scheduler())
        
        logger.info("Task Orchestrator started successfully")

    async def stop(self):
        """Stop the task orchestrator"""
        self.running = False
        if self.redis:
            await self.redis.close()
        self.executor.shutdown(wait=True)
        logger.info("Task Orchestrator stopped")

    def create_task(self, task_type: str, description: str, priority: TaskPriority = TaskPriority.NORMAL,
                    parameters: Dict[str, Any] = None, dependencies: List[str] = None) -> Task:
        """Create a new task"""
        task = Task(
            id=str(uuid.uuid4()),
            type=task_type,
            description=description,
            priority=priority,
            parameters=parameters or {},
            dependencies=dependencies or []
        )
        
        # Auto-assign agent based on task type and capabilities
        agent, servers = self._find_best_agent_for_task(task_type)
        if agent:
            task.assigned_agent = agent
            task.assigned_servers = servers
            task.status = TaskStatus.ASSIGNED
        
        self.tasks[task.id] = task
        self.task_queue.append(task.id)
        
        logger.info(f"Created task {task.id}: {task.description}")
        return task

    def create_workflow(self, workflow_name: str, parameters: Dict[str, Any] = None) -> List[Task]:
        """Create a workflow with multiple tasks"""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow {workflow_name} not found")
        
        workflow_id = str(uuid.uuid4())
        tasks = []
        step_to_task_id = {}
        
        for i, step in enumerate(self.workflows[workflow_name]):
            task_id = f"{workflow_id}_step_{i}"
            
            # Map dependencies to actual task IDs
            dependencies = []
            for dep_step in step.depends_on:
                for j, prev_step in enumerate(self.workflows[workflow_name][:i]):
                    if prev_step.task_type == dep_step or f"step_{j}" == dep_step:
                        dependencies.append(f"{workflow_id}_step_{j}")
                        break
            
            task = Task(
                id=task_id,
                type=step.task_type,
                description=f"Workflow {workflow_name} - Step {i+1}: {step.task_type}",
                priority=TaskPriority.NORMAL,
                assigned_agent=step.agent,
                assigned_servers=step.servers,
                status=TaskStatus.ASSIGNED,
                parameters={**step.parameters, **(parameters or {})},
                dependencies=dependencies
            )
            
            self.tasks[task.id] = task
            tasks.append(task)
            step_to_task_id[f"step_{i}"] = task_id
        
        # Add ready tasks to queue
        for task in tasks:
            if not task.dependencies:
                self.task_queue.append(task.id)
        
        logger.info(f"Created workflow {workflow_name} with {len(tasks)} tasks")
        return tasks

    def _find_best_agent_for_task(self, task_type: str) -> tuple[Optional[str], List[str]]:
        """Find the best agent for a given task type"""
        for agent, info in self.agent_capabilities.items():
            if any(capability in task_type.lower() for capability in info["capabilities"]):
                return agent, info["servers"]
        return None, []

    async def _task_processor(self):
        """Background task processor"""
        while self.running:
            try:
                if self.task_queue:
                    task_id = self.task_queue.pop(0)
                    task = self.tasks.get(task_id)
                    
                    if task and self._can_execute_task(task):
                        await self._execute_task(task)
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in task processor: {e}")

    def _can_execute_task(self, task: Task) -> bool:
        """Check if a task can be executed (dependencies met)"""
        if task.status != TaskStatus.ASSIGNED:
            return False
        
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True

    async def _execute_task(self, task: Task):
        """Execute a single task"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            self.active_tasks[task.id] = task
            
            logger.info(f"Executing task {task.id}: {task.description}")
            
            # Execute the task based on its type
            result = await self._dispatch_task(task)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            # Move to completed tasks
            self.completed_tasks[task.id] = task
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            # Check for dependent tasks that can now run
            await self._check_dependent_tasks(task.id)
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            task.error_message = str(e)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            self.failed_tasks[task.id] = task
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            # Retry if possible
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.ASSIGNED
                self.task_queue.append(task.id)
                logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")
            else:
                logger.error(f"Task {task.id} failed permanently: {e}")

    async def _dispatch_task(self, task: Task) -> Dict[str, Any]:
        """Dispatch task to appropriate agent/server"""
        if not task.assigned_agent:
            raise ValueError(f"No agent assigned for task {task.id}")
        
        # Simulate task execution by calling agent endpoints
        agent_url = f"http://localhost:{self._get_agent_port(task.assigned_agent)}"
        
        task_data = {
            "task_id": task.id,
            "task_type": task.type,
            "parameters": task.parameters,
            "servers": task.assigned_servers
        }
        
        try:
            # Try to send task to agent
            response = requests.post(f"{agent_url}/execute_task", 
                                   json=task_data, 
                                   timeout=task.timeout_seconds)
            
            if response.status_code == 200:
                return response.json()
            else:
                # Simulate task execution if agent doesn't have endpoint
                return await self._simulate_task_execution(task)
                
        except requests.exceptions.RequestException:
            # Simulate task execution if agent is not reachable
            return await self._simulate_task_execution(task)

    async def _simulate_task_execution(self, task: Task) -> Dict[str, Any]:
        """Simulate task execution for demonstration"""
        # Simulate processing time
        await asyncio.sleep(2)
        
        return {
            "status": "success",
            "task_id": task.id,
            "result": f"Simulated execution of {task.type}",
            "timestamp": datetime.now().isoformat(),
            "agent": task.assigned_agent,
            "servers": task.assigned_servers,
            "parameters": task.parameters
        }

    def _get_agent_port(self, agent_name: str) -> int:
        """Get the port number for an agent"""
        port_mapping = {
            "flashloan-agent-coordinator": 8200,
            "flashloan-agent-arbitrage-bot": 8206,
            "flashloan-agent-data-collector": 8205,
            "flashloan-agent-risk-manager": 8203,
            "flashloan-agent-healer": 8209,
            "flashloan-agent-liquidity-manager": 8207,
            "flashloan-agent-executor": 8202,
            "flashloan-agent-reporter": 8208,
            "flashloan-agent-monitor": 8204,
            "flashloan-agent-analyzer": 8201
        }
        return port_mapping.get(agent_name, 8200)

    async def _check_dependent_tasks(self, completed_task_id: str):
        """Check if any tasks can now be executed due to dependency completion"""
        for task_id, task in self.tasks.items():
            if (task.status == TaskStatus.ASSIGNED and 
                completed_task_id in task.dependencies and
                self._can_execute_task(task) and
                task_id not in self.task_queue):
                self.task_queue.append(task_id)

    async def _health_monitor(self):
        """Monitor system health and create health check tasks"""
        while self.running:
            try:
                # Create periodic health check workflow
                self.create_workflow("system_health_check")
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)

    async def _workflow_scheduler(self):
        """Schedule periodic workflows"""
        while self.running:
            try:
                # Schedule market analysis every 10 minutes
                self.create_workflow("market_analysis")
                await asyncio.sleep(600)
            except Exception as e:
                logger.error(f"Error in workflow scheduler: {e}")
                await asyncio.sleep(60)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific task"""
        task = self.tasks.get(task_id)
        if task:
            return asdict(task)
        return None

    def get_all_tasks(self) -> Dict[str, Any]:
        """Get all tasks with their current status"""
        return {
            "total_tasks": len(self.tasks),
            "pending": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "assigned": len([t for t in self.tasks.values() if t.status == TaskStatus.ASSIGNED]),
            "in_progress": len(self.active_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "tasks": {task_id: asdict(task) for task_id, task in self.tasks.items()}
        }

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get status of all workflows"""
        return {
            "available_workflows": list(self.workflows.keys()),
            "agent_capabilities": self.agent_capabilities,
            "active_tasks": len(self.active_tasks),
            "queue_length": len(self.task_queue)
        }

# Example usage
async def main():
    orchestrator = TaskOrchestrator()
    await orchestrator.start()
    
    try:
        # Create some example tasks
        task1 = orchestrator.create_task(
            "arbitrage_detection", 
            "Detect arbitrage opportunities",
            TaskPriority.HIGH
        )
        
        # Create a workflow
        workflow_tasks = orchestrator.create_workflow("arbitrage_opportunity_detection")
        
        # Let it run for a while
        await asyncio.sleep(30)
        
        # Print status
        print("Task Status:", orchestrator.get_all_tasks())
        
    finally:
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
