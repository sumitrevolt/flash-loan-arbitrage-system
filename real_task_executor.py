"""
Real Task Executor for MCP Servers and AI Agents
Implements actual task execution against running Docker containers
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    logs: Optional[List[str]] = None

    def __post_init__(self):
        if self.logs is None:
            self.logs = []

class RealTaskExecutor:
    """Executes tasks on real MCP servers and AI agents"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        if self.session:
            await self.session.close()
    
    async def execute_on_agent(self, agent_endpoint: str, task_type: str, parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute a task on an AI agent"""
        start_time = time.time()
        logs = []
        
        try:
            # Map task types to agent-specific endpoints
            endpoint_map = {
                "analyze_arbitrage": "/analyze_opportunity",
                "execute_arbitrage": "/execute_arbitrage",
                "risk_assessment": "/assess_risk",
                "collect_data": "/collect_market_data",
                "coordinate_workflow": "/coordinate",
                "monitor_system": "/monitor",
                "manage_liquidity": "/manage_liquidity",
                "generate_report": "/generate_report",
                "heal_system": "/heal",
                "health_check": "/health"
            }
            
            endpoint = endpoint_map.get(task_type, "/execute_task")
            url = f"http://{agent_endpoint}{endpoint}"
            
            logs.append(f"Executing {task_type} on agent {agent_endpoint}")
            
            # Prepare the request payload
            payload = {
                "task_type": task_type,
                "parameters": parameters,
                "timestamp": datetime.now().isoformat()
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    execution_time = time.time() - start_time
                    logs.append(f"Task completed successfully in {execution_time:.2f}s")
                    
                    return ExecutionResult(
                        success=True,
                        result=result,
                        execution_time=execution_time,
                        logs=logs
                    )
                else:
                    error_text = await response.text()
                    logs.append(f"Agent returned error: {response.status} - {error_text}")
                    
                    return ExecutionResult(
                        success=False,
                        error=f"HTTP {response.status}: {error_text}",
                        execution_time=time.time() - start_time,
                        logs=logs
                    )
                    
        except aiohttp.ClientError as e:
            logs.append(f"Network error: {str(e)}")
            return ExecutionResult(
                success=False,
                error=f"Network error: {str(e)}",
                execution_time=time.time() - start_time,
                logs=logs
            )
        except Exception as e:
            logs.append(f"Unexpected error: {str(e)}")
            return ExecutionResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                execution_time=time.time() - start_time,
                logs=logs
            )
    
    async def execute_on_mcp_server(self, server_endpoint: str, operation: str, parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute an operation on an MCP server"""
        start_time = time.time()
        logs = []
        
        try:
            # Map operations to MCP server-specific endpoints
            endpoint_map = {
                "get_price_data": "/prices",
                "analyze_defi": "/analyze",
                "get_blockchain_data": "/blockchain/data",
                "execute_arbitrage": "/arbitrage/execute",
                "manage_portfolio": "/portfolio/manage",
                "assess_risk": "/risk/assess",
                "get_liquidity": "/liquidity/info",
                "send_notification": "/notify",
                "store_data": "/data/store",
                "retrieve_data": "/data/retrieve",
                "cache_data": "/cache/set",
                "get_cached_data": "/cache/get",
                "process_file": "/file/process",
                "authenticate": "/auth/verify",
                "monitor_system": "/monitor",
                "queue_task": "/task/queue",
                "filesystem_operation": "/fs/operation",
                "coordinate_services": "/coordinate",
                "health_check": "/health"
            }
            
            endpoint = endpoint_map.get(operation, "/execute")
            url = f"http://{server_endpoint}{endpoint}"
            
            logs.append(f"Executing {operation} on MCP server {server_endpoint}")
            
            # Prepare the request payload
            payload = {
                "operation": operation,
                "parameters": parameters,
                "timestamp": datetime.now().isoformat()
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    execution_time = time.time() - start_time
                    logs.append(f"Operation completed successfully in {execution_time:.2f}s")
                    
                    return ExecutionResult(
                        success=True,
                        result=result,
                        execution_time=execution_time,
                        logs=logs
                    )
                else:
                    error_text = await response.text()
                    logs.append(f"MCP server returned error: {response.status} - {error_text}")
                    
                    return ExecutionResult(
                        success=False,
                        error=f"HTTP {response.status}: {error_text}",
                        execution_time=time.time() - start_time,
                        logs=logs
                    )
                    
        except aiohttp.ClientError as e:
            logs.append(f"Network error: {str(e)}")
            return ExecutionResult(
                success=False,
                error=f"Network error: {str(e)}",
                execution_time=time.time() - start_time,
                logs=logs
            )
        except Exception as e:
            logs.append(f"Unexpected error: {str(e)}")
            return ExecutionResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                execution_time=time.time() - start_time,
                logs=logs
            )
    
    async def execute_complex_workflow(self, workflow_steps: List[Dict[str, Any]]) -> List[ExecutionResult]:
        """Execute a complex workflow with multiple steps"""
        results = []
        context = {}  # Shared context between steps
        
        for i, step in enumerate(workflow_steps):
            step_start = time.time()
            logs = [f"Starting workflow step {i+1}/{len(workflow_steps)}: {step.get('description', 'Unknown step')}"]
            
            try:
                # Replace context variables in parameters
                parameters = self._resolve_context_variables(step.get('parameters', {}), context)
                
                if step['type'] == 'agent_task':
                    result = await self.execute_on_agent(
                        step['endpoint'], 
                        step['task_type'], 
                        parameters
                    )
                elif step['type'] == 'mcp_operation':
                    result = await self.execute_on_mcp_server(
                        step['endpoint'], 
                        step['operation'], 
                        parameters
                    )
                else:
                    result = ExecutionResult(
                        success=False,
                        error=f"Unknown step type: {step['type']}",
                        execution_time=time.time() - step_start,
                        logs=logs
                    )
                
                # Update context with result
                if result.success and result.result:
                    context[f"step_{i}_result"] = result.result
                    context[f"step_{i}_success"] = True
                else:
                    context[f"step_{i}_success"] = False
                    context[f"step_{i}_error"] = result.error
                
                results.append(result)
                
                # Stop execution on failure if step is marked as critical
                if not result.success and step.get('critical', False):
                    logs.append(f"Critical step {i+1} failed, stopping workflow")
                    break
                    
            except Exception as e:
                error_result = ExecutionResult(
                    success=False,
                    error=f"Workflow step error: {str(e)}",
                    execution_time=time.time() - step_start,
                    logs=logs + [f"Step {i+1} failed with exception: {str(e)}"]
                )
                results.append(error_result)
                
                if step.get('critical', False):
                    break
        
        return results
    
    def _resolve_context_variables(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Replace context variables in parameters"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                resolved[key] = context.get(var_name, value)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_context_variables(value, context)
            else:
                resolved[key] = value
                
        return resolved

    async def test_agent_connectivity(self, agent_endpoint: str) -> ExecutionResult:
        """Test connectivity to an agent"""
        return await self.execute_on_agent(agent_endpoint, "health_check", {})
    
    async def test_mcp_server_connectivity(self, server_endpoint: str) -> ExecutionResult:
        """Test connectivity to an MCP server"""
        return await self.execute_on_mcp_server(server_endpoint, "health_check", {})
