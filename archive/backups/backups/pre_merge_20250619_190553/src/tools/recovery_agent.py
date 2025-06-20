"""
Simple Recovery Agent for MCP Flash Loan System
Monitors service health with Docker orchestration support for 121 MCP agents
"""

import asyncio
import logging
import psutil
from typing import Dict, List, Set, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceHealth:
    service_id: str
    name: str
    status: str
    health_status: str
    restart_count: int
    cpu_percent: float
    memory_percent: float
    last_check: datetime
    error_logs: List[str]

class RecoveryAction(BaseModel):
    service_name: str
    action: str  # restart, recreate, scale
    reason: str
    priority: int = 5

class HealthCheckConfig(BaseModel):
    check_interval: int = 30
    max_cpu_threshold: float = 80.0
    max_memory_threshold: float = 85.0
    max_restart_count: int = 5
    unhealthy_threshold: int = 3

class SimpleRecoveryAgent:
    def __init__(self):
        self.config = HealthCheckConfig()
        self.monitored_services: Set[str] = set()
        self.health_history: Dict[str, List[ServiceHealth]] = {}
        self.recovery_queue: List[RecoveryAction] = []
        self.running = False
        
        # Recovery actions
        self.recovery_actions = {
            "restart": self._restart_service,
            "recreate": self._recreate_service,
            "scale": self._scale_service,
            "rollback": self._rollback_service
        }
        
    async def initialize(self) -> None:
        """Initialize and discover services"""
        try:
            # Get list of services to monitor
            await self._discover_services()
            logger.info("Recovery agent initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize recovery agent: {e}")
            raise

    async def _discover_services(self) -> None:
        """Discover MCP services to monitor"""
        try:
            # Monitor Python processes that look like MCP servers
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    cmdline: List[str] = proc.info['cmdline'] or []
                    cmdline_str = ' '.join(cmdline)
                    
                    if any(keyword in cmdline_str.lower() for keyword in ['mcp', 'flash-loan', 'arbitrage', 'coordinator']):
                        service_name = f"mcp_service_{proc.info['pid']}"
                        self.monitored_services.add(service_name)
                        logger.info(f"Monitoring service: {service_name} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            
    async def start_monitoring(self) -> None:
        """Start the monitoring loop"""
        self.running = True
        logger.info("Starting recovery agent monitoring...")
        
        while self.running:
            try:
                # Check health of all monitored services
                for service_name in list(self.monitored_services):
                    await self._check_service_health(service_name)
                
                # Process recovery queue
                await self._process_recovery_queue()
                
                # Wait for next check interval
                await asyncio.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short wait before retrying

    async def _check_service_health(self, service_name: str) -> None:
        """Check health of a specific service"""
        try:
            pid = int(service_name.split('_')[-1])
            
            if not psutil.pid_exists(pid):
                logger.warning(f"Service {service_name} (PID: {pid}) no longer exists")
                self.monitored_services.discard(service_name)
                return
                
            proc = psutil.Process(pid)
            
            # Get process stats
            cpu_percent = proc.cpu_percent()
            memory_percent = proc.memory_percent()
            
            # Get process status
            status = proc.status()
            
            # Create health record
            health = ServiceHealth(
                service_id=str(pid),
                name=service_name,
                status=status,
                health_status="healthy" if status == psutil.STATUS_RUNNING else "unhealthy",
                restart_count=0,  # Would need to track this separately
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                last_check=datetime.now(timezone.utc),
                error_logs=[]  # Would need to check log files
            )
            
            # Store health record
            if service_name not in self.health_history:
                self.health_history[service_name] = []
            self.health_history[service_name].append(health)
            
            # Keep only recent history
            if len(self.health_history[service_name]) > 50:
                self.health_history[service_name] = self.health_history[service_name][-50:]
            
            # Check if recovery is needed
            await self._evaluate_recovery_need(service_name, health)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            logger.warning(f"Cannot access service {service_name}")
            self.monitored_services.discard(service_name)
        except Exception as e:
            logger.error(f"Failed to check health for {service_name}: {e}")

    async def _evaluate_recovery_need(self, service_name: str, current_health: ServiceHealth) -> None:
        """Evaluate if recovery action is needed"""
        try:
            # Check resource thresholds
            if current_health.cpu_percent > self.config.max_cpu_threshold:
                await self._queue_recovery_action(
                    service_name, "restart", 
                    f"High CPU usage: {current_health.cpu_percent}%", 8
                )
                
            if current_health.memory_percent > self.config.max_memory_threshold:
                await self._queue_recovery_action(
                    service_name, "restart",
                    f"High memory usage: {current_health.memory_percent}%", 8
                )
                
            # Check if service is unhealthy
            if current_health.health_status != "healthy":
                await self._queue_recovery_action(
                    service_name, "restart",
                    f"Service unhealthy: {current_health.status}", 9
                )
                
        except Exception as e:
            logger.error(f"Error evaluating recovery need: {e}")

    async def _queue_recovery_action(self, service_name: str, action: str, reason: str, priority: int) -> None:
        """Queue a recovery action"""
        recovery_action = RecoveryAction(
            service_name=service_name,
            action=action,
            reason=reason,
            priority=priority
        )
        
        # Avoid duplicate actions
        existing = [r for r in self.recovery_queue if r.service_name == service_name and r.action == action]
        if not existing:
            self.recovery_queue.append(recovery_action)
            logger.info(f"Queued recovery action: {action} for {service_name} - {reason}")

    async def _process_recovery_queue(self) -> None:
        """Process queued recovery actions"""
        if not self.recovery_queue:
            return
            
        # Sort by priority (higher priority first)
        self.recovery_queue.sort(key=lambda x: Any: Any: x.priority, reverse=True)
        
        # Process one action at a time
        action = self.recovery_queue.pop(0)
        
        try:
            if action.action in self.recovery_actions:
                logger.info(f"Executing recovery action: {action.action} for {action.service_name}")
                await self.recovery_actions[action.action](action.service_name, action.reason)
            else:
                logger.warning(f"Unknown recovery action: {action.action}")
                
        except Exception as e:
            logger.error(f"Failed to execute recovery action {action.action} for {action.service_name}: {e}")

    async def _restart_service(self, service_name: str, reason: str) -> None:
        """Restart a service (simplified)"""
        logger.info(f"Would restart service {service_name} - {reason}")
        # In a real implementation, this would restart the actual service

    async def _recreate_service(self, service_name: str, reason: str) -> None:
        """Recreate a service (simplified)"""
        logger.info(f"Would recreate service {service_name} - {reason}")

    async def _scale_service(self, service_name: str, reason: str) -> None:
        """Scale a service (simplified)"""
        logger.info(f"Would scale service {service_name} - {reason}")

    async def _rollback_service(self, service_name: str, reason: str) -> None:
        """Rollback a service (simplified)"""
        logger.info(f"Would rollback service {service_name} - {reason}")

    async def stop(self) -> None:
        """Stop the recovery agent"""
        self.running = False
        logger.info("Recovery agent stopped")

# FastAPI app for health checks and API
app = FastAPI(title="Simple Recovery Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: Optional[SimpleRecoveryAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = SimpleRecoveryAgent()
    monitoring_task = None
    
    try:
        await agent.initialize()
        # Start monitoring in background
        monitoring_task = asyncio.create_task(agent.start_monitoring())
        yield
    finally:
        if agent:
            await agent.stop()
        if monitoring_task:
            monitoring_task.cancel()

app.router.lifespan_context = lifespan

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Simple Recovery Agent", "status": "running"}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    if not agent:
        return {"status": "error", "message": "Agent not initialized"}
    
    return {
        "status": "healthy",
        "monitored_services": str(len(agent.monitored_services)),
        "recovery_queue_size": str(len(agent.recovery_queue)),
        "uptime": "running"
    }

@app.get("/services")
async def get_monitored_services() -> Dict[str, List[str]]:
    if not agent:
        return {"services": []}
    
    return {"services": list(agent.monitored_services)}

@app.get("/services/{service_name}/health")
async def get_service_health(service_name: str) -> Dict[str, str]:
    if not agent or service_name not in agent.health_history:
        return {"error": "Service not found"}
    
    recent_health = agent.health_history[service_name][-1] if agent.health_history[service_name] else None
    if not recent_health:
        return {"error": "No health data available"}
    
    return {
        "service_id": recent_health.service_id,
        "name": recent_health.name,
        "status": recent_health.status,
        "health_status": recent_health.health_status,
        "cpu_percent": str(recent_health.cpu_percent),
        "memory_percent": str(recent_health.memory_percent),
        "last_check": recent_health.last_check.isoformat()
    }

if __name__ == "__main__":
    # Run the FastAPI app
    uvicorn.run(
        "recovery_agent:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )
