#!/usr/bin/env python3
"""
Self-Healing AI Agent for Docker Coordination System
====================================================

This agent monitors the entire system and provides self-healing capabilities:
- Container health monitoring
- Automatic restart of failed services
- Resource optimization
- Performance monitoring
- Error recovery
- System diagnostics
"""

import asyncio
import docker
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
import uvicorn
import psutil
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/self_healing.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

class SelfHealingAgent:
    """AI Agent for system self-healing and monitoring"""
    
    def __init__(self):
        self.app = FastAPI(title="Self-Healing AI Agent")
        self.docker_client = docker.from_env()
        self.redis_client: Optional[redis.Redis] = None
        self.port = int(os.getenv('PORT', 8300))
        
        # Health monitoring state
        self.service_health = {}
        self.error_counts = {}
        self.last_restart_times = {}
        self.system_metrics = {}
        
        # Self-healing configuration
        self.max_restart_attempts = 3
        self.restart_cooldown = 300  # 5 minutes
        self.health_check_interval = 30  # 30 seconds
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent": "self_healing_agent",
                "port": self.port,
                "monitoring": len(self.service_health),
                "active_healings": sum(1 for h in self.service_health.values() if not h)
            }
        
        @self.app.get("/system-status")
        async def get_system_status():
            return {
                "system_health": await self.get_system_health(),
                "resource_usage": await self.get_resource_usage(),
                "service_status": self.service_health,
                "recent_healings": await self.get_recent_healings()
            }
        
        @self.app.post("/heal-service")
        async def heal_service(request: dict):
            service_name = request.get('service_name')
            if not service_name:
                raise HTTPException(status_code=400, detail="service_name required")
            
            result = await self.heal_service_by_name(service_name)
            return {"status": "success", "result": result}
        
        @self.app.post("/emergency-healing")
        async def emergency_healing():
            """Emergency healing for critical system issues"""
            result = await self.emergency_system_recovery()
            return {"status": "success", "result": result}
    
    async def initialize(self):
        """Initialize the self-healing agent"""
        try:
            # Setup Redis connection
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.from_url(redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis for coordination")
            
            # Start monitoring tasks
            asyncio.create_task(self.continuous_health_monitoring())
            asyncio.create_task(self.resource_monitoring())
            asyncio.create_task(self.log_analysis_task())
            
            logger.info("Self-healing agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize self-healing agent: {e}")
            
    async def continuous_health_monitoring(self):
        """Continuously monitor system health"""
        while True:
            try:
                await self.check_all_services_health()
                await self.auto_heal_failed_services()
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(5)
    
    async def check_all_services_health(self):
        """Check health of all services"""
        try:
            containers = self.docker_client.containers.list()
            
            for container in containers:
                container_name = container.name
                
                # Skip infrastructure containers for now
                if container_name in ['coordination_redis', 'coordination_postgres', 'coordination_rabbitmq']:
                    continue
                
                is_healthy = await self.check_container_health(container)
                self.service_health[container_name] = is_healthy
                
                if not is_healthy:
                    logger.warning(f"Service {container_name} is unhealthy")
                    
        except Exception as e:
            logger.error(f"Error checking services health: {e}")
    
    async def check_container_health(self, container) -> bool:
        """Check if a container is healthy"""
        try:
            # Check container status
            container.reload()
            if container.status != 'running':
                return False
            
            # Try to get container port mapping
            port_mappings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            
            # Look for HTTP health endpoints
            for port_spec, port_mappings_list in port_mappings.items():
                if port_mappings_list:
                    host_port = port_mappings_list[0]['HostPort']
                    health_url = f"http://localhost:{host_port}/health"
                    
                    try:
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                            async with session.get(health_url) as response:
                                return response.status == 200
                    except:
                        pass
            
            # If no HTTP endpoint, check if container is running
            return container.status == 'running'
            
        except Exception as e:
            logger.error(f"Error checking container {container.name} health: {e}")
            return False
    
    async def auto_heal_failed_services(self):
        """Automatically heal failed services"""
        for service_name, is_healthy in self.service_health.items():
            if not is_healthy:
                await self.heal_service_by_name(service_name)
    
    async def heal_service_by_name(self, service_name: str) -> Dict[str, Any]:
        """Heal a specific service"""
        try:
            # Check restart attempts
            error_count = self.error_counts.get(service_name, 0)
            last_restart = self.last_restart_times.get(service_name, 0)
            
            # Check cooldown period
            if time.time() - last_restart < self.restart_cooldown:
                return {
                    "action": "skipped",
                    "reason": "cooldown_period",
                    "next_attempt_in": self.restart_cooldown - (time.time() - last_restart)
                }
            
            # Check max restart attempts
            if error_count >= self.max_restart_attempts:
                logger.error(f"Service {service_name} exceeded max restart attempts")
                return {
                    "action": "failed",
                    "reason": "max_attempts_exceeded",
                    "error_count": error_count
                }
            
            # Attempt to heal the service
            healing_result = await self.perform_healing_actions(service_name)
            
            # Update tracking
            self.error_counts[service_name] = error_count + 1
            self.last_restart_times[service_name] = time.time()
            
            # Log healing action
            await self.log_healing_action(service_name, healing_result)
            
            return healing_result
            
        except Exception as e:
            logger.error(f"Error healing service {service_name}: {e}")
            return {"action": "error", "error": str(e)}
    
    async def perform_healing_actions(self, service_name: str) -> Dict[str, Any]:
        """Perform actual healing actions on a service"""
        try:
            container = self.docker_client.containers.get(service_name)
            
            logger.info(f"Attempting to heal service: {service_name}")
            
            # Step 1: Try to restart the container
            container.restart()
            
            # Step 2: Wait for restart and check health
            await asyncio.sleep(10)
            
            container.reload()
            if container.status == 'running':
                # Step 3: Check if service responds to health checks
                await asyncio.sleep(20)  # Give time for service to initialize
                
                is_healthy = await self.check_container_health(container)
                
                if is_healthy:
                    logger.info(f"Successfully healed service: {service_name}")
                    # Reset error count on successful healing
                    self.error_counts[service_name] = 0
                    
                    return {
                        "action": "healed",
                        "method": "container_restart",
                        "status": "healthy"
                    }
                else:
                    return {
                        "action": "partial_heal",
                        "method": "container_restart",
                        "status": "running_but_unhealthy"
                    }
            else:
                return {
                    "action": "failed",
                    "method": "container_restart",
                    "status": container.status
                }
                
        except docker.errors.NotFound:
            return {
                "action": "failed",
                "error": "container_not_found",
                "suggestion": "recreate_container"
            }
        except Exception as e:
            logger.error(f"Error performing healing actions on {service_name}: {e}")
            return {
                "action": "error",
                "error": str(e)
            }
    
    async def emergency_system_recovery(self) -> Dict[str, Any]:
        """Emergency recovery for critical system failures"""
        logger.warning("Initiating emergency system recovery")
        
        recovery_actions = []
        
        try:
            # Step 1: Restart all unhealthy containers
            for service_name, is_healthy in self.service_health.items():
                if not is_healthy:
                    result = await self.perform_healing_actions(service_name)
                    recovery_actions.append({
                        "service": service_name,
                        "action": result
                    })
            
            # Step 2: Check system resources
            resource_status = await self.get_resource_usage()
            if resource_status.get('memory_percent', 0) > 90:
                logger.warning("High memory usage detected during emergency recovery")
                recovery_actions.append({
                    "action": "memory_cleanup",
                    "result": "initiated"
                })
            
            # Step 3: Verify coordination system
            coordination_healthy = await self.verify_coordination_system()
            recovery_actions.append({
                "action": "coordination_check",
                "result": "healthy" if coordination_healthy else "unhealthy"
            })
            
            return {
                "emergency_recovery": "completed",
                "actions": recovery_actions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during emergency recovery: {e}")
            return {
                "emergency_recovery": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def resource_monitoring(self):
        """Monitor system resources"""
        while True:
            try:
                self.system_metrics = await self.get_resource_usage()
                
                # Check for resource issues
                if self.system_metrics.get('memory_percent', 0) > 85:
                    logger.warning(f"High memory usage: {self.system_metrics['memory_percent']}%")
                    await self.handle_high_memory_usage()
                
                if self.system_metrics.get('cpu_percent', 0) > 80:
                    logger.warning(f"High CPU usage: {self.system_metrics['cpu_percent']}%")
                    await self.handle_high_cpu_usage()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(10)
    
    async def get_resource_usage(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        healthy_services = sum(1 for h in self.service_health.values() if h)
        total_services = len(self.service_health)
        
        return {
            "healthy_services": healthy_services,
            "total_services": total_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
            "system_status": "healthy" if healthy_services == total_services else "degraded",
            "timestamp": datetime.now().isoformat()
        }
    
    async def log_healing_action(self, service_name: str, result: Dict[str, Any]):
        """Log healing actions for analysis"""
        log_entry = {
            "service": service_name,
            "healing_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.redis_client:
            await self.redis_client.lpush("healing_logs", json.dumps(log_entry))
            await self.redis_client.ltrim("healing_logs", 0, 1000)  # Keep last 1000 logs
    
    async def get_recent_healings(self) -> List[Dict[str, Any]]:
        """Get recent healing actions"""
        if not self.redis_client:
            return []
        
        try:
            logs = await self.redis_client.lrange("healing_logs", 0, 10)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting recent healings: {e}")
            return []
    
    async def handle_high_memory_usage(self):
        """Handle high memory usage situations"""
        logger.info("Handling high memory usage")
        # Implementation for memory optimization
        pass
    
    async def handle_high_cpu_usage(self):
        """Handle high CPU usage situations"""
        logger.info("Handling high CPU usage")
        # Implementation for CPU optimization
        pass
    
    async def verify_coordination_system(self) -> bool:
        """Verify the main coordination system is working"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://coordination_system:8000/health") as response:
                    return response.status == 200
        except:
            return False
    
    async def log_analysis_task(self):
        """Analyze logs for patterns and issues"""
        while True:
            try:
                # Placeholder for log analysis
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Error in log analysis: {e}")
                await asyncio.sleep(60)

# Global instance
self_healing_agent = SelfHealingAgent()

@self_healing_agent.app.on_event("startup")
async def startup_event():
    await self_healing_agent.initialize()

@self_healing_agent.app.on_event("shutdown")
async def shutdown_event():
    if self_healing_agent.redis_client:
        await self_healing_agent.redis_client.close()

def run_agent():
    """Run the self-healing agent"""
    try:
        uvicorn.run(
            self_healing_agent.app,
            host="0.0.0.0",
            port=self_healing_agent.port,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start self-healing agent: {e}")

if __name__ == "__main__":
    run_agent()
