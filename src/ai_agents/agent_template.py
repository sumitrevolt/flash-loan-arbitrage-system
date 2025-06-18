#!/usr/bin/env python3
"""
LangChain Agent Template
Template for agent containers with coordination capabilities
"""

import asyncio
import logging
import os
import time
import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Environment configuration
AGENT_TYPE = os.getenv('AGENT_TYPE', 'generic')
AGENT_ID = os.getenv('AGENT_ID', '01')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'http://orchestrator:8000')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=f'%(asctime)s - Agent-{AGENT_ID} - %(levelname)s - %(message)s'
)
logger = logging.getLogger(f"Agent-{AGENT_ID}")

class LangChainAgent:
    """Enhanced LangChain Agent with coordination capabilities"""
    
    def __init__(self, agent_type: str, agent_id: str):
        self.agent_type = agent_type
        self.agent_id = agent_id
        self.status = "initializing"
        self.tasks_completed = 0
        self.last_heartbeat = None
        self.is_running = False
        
    async def start(self):
        """Start the agent"""
        logger.info(f"Starting {self.agent_type} agent {self.agent_id}")
        self.is_running = True
        self.status = "running"
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._process_tasks()),
            asyncio.create_task(self._coordinate_with_orchestrator())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Agent error: {e}")
            self.status = "error"
    
    async def _heartbeat_loop(self):
        """Send heartbeat to orchestrator"""
        while self.is_running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(60)
    
    async def _send_heartbeat(self):
        """Send heartbeat to orchestrator"""
        try:
            heartbeat_data = {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'status': self.status,
                'tasks_completed': self.tasks_completed,
                'timestamp': datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ORCHESTRATOR_URL}/agent/heartbeat",
                    json=heartbeat_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        self.last_heartbeat = datetime.now()
                    else:
                        logger.warning(f"Heartbeat failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    async def _process_tasks(self):
        """Process tasks assigned to this agent"""
        while self.is_running:
            try:
                # Get tasks from orchestrator
                tasks = await self._get_assigned_tasks()
                
                for task in tasks:
                    await self._execute_task(task)
                
                await asyncio.sleep(10)  # Check for tasks every 10 seconds
            except Exception as e:
                logger.error(f"Task processing error: {e}")
                await asyncio.sleep(30)
    
    async def _get_assigned_tasks(self) -> list:
        """Get tasks assigned to this agent"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ORCHESTRATOR_URL}/agent/{self.agent_id}/tasks",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return []
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []
    
    async def _execute_task(self, task: Dict[str, Any]):
        """Execute a specific task based on agent type"""
        task_id = task.get('id', 'unknown')
        logger.info(f"Executing task {task_id}: {task.get('name', 'Unnamed task')}")
        
        try:
            result = await self._agent_specific_execution(task)
            
            # Report task completion
            await self._report_task_completion(task_id, result)
            
            self.tasks_completed += 1
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self._report_task_failure(task_id, str(e))
    
    async def _agent_specific_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task based on agent type"""
        
        if self.agent_type == "coordinator":
            return await self._coordinate_task(task)
        elif self.agent_type == "executor":
            return await self._execute_task_directly(task)
        elif self.agent_type == "monitor":
            return await self._monitor_task(task)
        elif self.agent_type == "analyzer":
            return await self._analyze_task(task)
        elif self.agent_type == "optimizer":
            return await self._optimize_task(task)
        elif self.agent_type == "validator":
            return await self._validate_task(task)
        elif self.agent_type == "reporter":
            return await self._report_task(task)
        elif self.agent_type == "debugger":
            return await self._debug_task(task)
        elif self.agent_type == "deployer":
            return await self._deploy_task(task)
        elif self.agent_type == "healer":
            return await self._heal_task(task)
        else:
            return await self._generic_task_execution(task)
    
    async def _coordinate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinator agent: Coordinate with other agents"""
        logger.info("Coordinating task execution with other agents")
        return {
            "action": "coordinated",
            "sub_tasks_created": 3,
            "agents_involved": ["executor", "validator", "reporter"]
        }
    
    async def _execute_task_directly(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Executor agent: Execute tasks directly"""
        logger.info("Executing task directly")
        await asyncio.sleep(2)  # Simulate task execution
        return {
            "action": "executed",
            "result": "Task execution completed",
            "execution_time": 2.0
        }
    
    async def _monitor_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor agent: Monitor system components"""
        logger.info("Monitoring system components")
        return {
            "action": "monitored", 
            "components_checked": 21,
            "healthy_components": 20,
            "issues_found": 1
        }
    
    async def _analyze_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzer agent: Analyze data and patterns"""
        logger.info("Analyzing task data and patterns")
        return {
            "action": "analyzed",
            "patterns_found": 5,
            "anomalies_detected": 0,
            "confidence": 0.95
        }
    
    async def _optimize_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimizer agent: Optimize performance"""
        logger.info("Optimizing task performance")
        return {
            "action": "optimized",
            "performance_improvement": "15%",
            "optimizations_applied": 3
        }
    
    async def _validate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validator agent: Validate results"""
        logger.info("Validating task results")
        return {
            "action": "validated",
            "validation_passed": True,
            "checks_performed": 10,
            "errors_found": 0
        }
    
    async def _report_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Reporter agent: Generate reports"""
        logger.info("Generating task report")
        return {
            "action": "reported",
            "report_generated": True,
            "report_type": "execution_summary",
            "metrics_included": 15
        }
    
    async def _debug_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Debugger agent: Debug issues"""
        logger.info("Debugging task issues")
        return {
            "action": "debugged",
            "issues_investigated": 2,
            "root_causes_found": 1,
            "fixes_suggested": 1
        }
    
    async def _deploy_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Deployer agent: Deploy solutions"""
        logger.info("Deploying task solutions")
        return {
            "action": "deployed",
            "deployment_successful": True,
            "services_deployed": 3,
            "rollback_plan": "available"
        }
    
    async def _heal_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Healer agent: Heal system issues"""
        logger.info("Healing system issues")
        return {
            "action": "healed",
            "components_healed": 2,
            "issues_resolved": 1,
            "system_stability": "improved"
        }
    
    async def _generic_task_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generic task execution for unknown agent types"""
        logger.info("Executing generic task")
        await asyncio.sleep(1)
        return {
            "action": "generic_execution",
            "result": "Generic task completed"
        }
    
    async def _report_task_completion(self, task_id: str, result: Dict[str, Any]):
        """Report task completion to orchestrator"""
        try:
            completion_data = {
                'agent_id': self.agent_id,
                'task_id': task_id,
                'status': 'completed',
                'result': result,
                'completion_time': datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ORCHESTRATOR_URL}/task/{task_id}/complete",
                    json=completion_data,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to report completion: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to report task completion: {e}")
    
    async def _report_task_failure(self, task_id: str, error: str):
        """Report task failure to orchestrator"""
        try:
            failure_data = {
                'agent_id': self.agent_id,
                'task_id': task_id,
                'status': 'failed',
                'error': error,
                'failure_time': datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ORCHESTRATOR_URL}/task/{task_id}/failed",
                    json=failure_data,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to report failure: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to report task failure: {e}")
    
    async def _coordinate_with_orchestrator(self):
        """Coordinate with orchestrator for advanced features"""
        while self.is_running:
            try:
                # Get coordination instructions
                instructions = await self._get_coordination_instructions()
                
                if instructions:
                    await self._execute_coordination_instructions(instructions)
                
                await asyncio.sleep(60)  # Coordinate every minute
            except Exception as e:
                logger.error(f"Coordination error: {e}")
                await asyncio.sleep(120)
    
    async def _get_coordination_instructions(self) -> Optional[Dict[str, Any]]:
        """Get coordination instructions from orchestrator"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ORCHESTRATOR_URL}/agent/{self.agent_id}/coordination",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
        except Exception as e:
            logger.error(f"Failed to get coordination instructions: {e}")
            return None
    
    async def _execute_coordination_instructions(self, instructions: Dict[str, Any]):
        """Execute coordination instructions"""
        logger.info(f"Executing coordination instructions: {instructions.get('type', 'unknown')}")
        
        instruction_type = instructions.get('type')
        
        if instruction_type == "scale_up":
            logger.info("Received scale up instruction")
        elif instruction_type == "scale_down":
            logger.info("Received scale down instruction")
        elif instruction_type == "change_strategy":
            logger.info("Received strategy change instruction")
        elif instruction_type == "emergency_mode":
            logger.warning("Entering emergency mode")
            self.status = "emergency"
        else:
            logger.info(f"Unknown coordination instruction: {instruction_type}")

async def main():
    """Main entry point for the agent"""
    logger.info(f"Starting LangChain Agent {AGENT_ID} (Type: {AGENT_TYPE})")
    
    agent = LangChainAgent(AGENT_TYPE, AGENT_ID)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        agent.is_running = False
    except Exception as e:
        logger.error(f"Agent error: {e}")
        agent.status = "error"

if __name__ == "__main__":
    asyncio.run(main())
