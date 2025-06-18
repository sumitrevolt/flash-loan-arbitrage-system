"""
Enhanced Tool Registry for Enterprise MCP Server

Manages registration, discovery, and execution of all MCP tools including:
- Advanced risk management tools
- Multi-chain deployment tools  
- Contract analysis and security tools
- MEV protection and optimization tools
- AI-powered contract optimization tools
- Real-time monitoring and alerting tools
- Circuit breaker and failover mechanisms
"""

import asyncio
import importlib
import inspect
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import traceback


async def run_with_timeout(coro, timeout_seconds: float):
    """Helper function to run a coroutine with timeout"""
    return await asyncio.wait_for(coro, timeout=timeout_seconds)

try:
    from mcp.types import Tool
    from pydantic import BaseModel
except ImportError:
    # Fallback for when MCP types aren't available
    class Tool:
        pass
    class BaseModel:
        pass


@dataclass
class ToolExecutionMetrics:
    """Metrics for tool execution tracking"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time_ms: float = 0.0
    last_execution_time: Optional[datetime] = None
    last_error: Optional[str] = None
    execution_history: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.execution_history is None:
            self.execution_history = []


class ToolSchema(BaseModel):
    """Enhanced schema for tool definitions with enterprise features."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    category: str = "general"
    tags: List[str] = []
    timeout: int = 30  # seconds
    requires_foundry: bool = False
    requires_network: bool = False
    enterprise_features: Dict[str, Any] = {}
    risk_level: str = "low"  # low, medium, high, critical
    audit_logging: bool = True


class BaseTool:
    """Enhanced base class for all MCP tools with enterprise features."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self._initialized = False
        self.execution_count = 0
        self.last_used = None
        self.is_active = True
        self.metrics = ToolExecutionMetrics()
    
    async def initialize(self) -> bool:
        """Initialize the tool. Should be overridden by subclasses."""
        try:
            self._initialized = True
            self.logger.info(f"✅ Tool {self.__class__.__name__} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize tool {self.__class__.__name__}: {e}")
            return False

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with enhanced monitoring. Must be implemented by subclasses."""
        raise NotImplementedError("Tool must implement execute method")
    
    def get_schema(self) -> ToolSchema:
        """Get tool schema. Must be implemented by subclasses."""
        raise NotImplementedError("Tool must implement get_schema method")
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize tool arguments."""
        return arguments


class EnterpriseToolRegistry:
    """
    Enhanced central registry for all MCP tools with enterprise features.
    
    Handles tool discovery, registration, validation, execution, monitoring,
    and advanced enterprise features like circuit breakers and failover.
    """
    
    def __init__(self, config: Dict[str, Any] = None, logger: logging.Logger = None):
        self.config = config or {}
        self.logger = logger or logging.getLogger("ToolRegistry")
        self.tools: Dict[str, BaseTool] = {}
        self._tool_schemas: Dict[str, ToolSchema] = {}
        self._tool_categories: Dict[str, List[str]] = {}
        self._tool_metrics: Dict[str, ToolExecutionMetrics] = {}
        self._initialized = False
        
        # Enterprise features
        self.circuit_breakers = {}
        self.performance_thresholds = {
            'max_execution_time_ms': 30000,
            'max_error_rate': 0.2,
            'max_consecutive_failures': 3
        }

    async def execute_tool_with_monitoring(self, tool: BaseTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with comprehensive monitoring and error handling"""
        start_time = time.time()
        execution_id = f"{tool.__class__.__name__}_{int(time.time())}"
        
        try:
            # Pre-execution validation
            if not tool._initialized:
                await tool.initialize()
            
            # Validate arguments
            validated_args = tool.validate_arguments(arguments)
            
            # Log execution start
            if tool.get_schema().audit_logging:
                self.logger.info(f"🔄 Executing {tool.__class__.__name__} with args: {json.dumps(validated_args, default=str)}")
            
            # Execute with timeout
            schema = tool.get_schema()
            result: str = await asyncio.wait_for(
                tool.execute(**validated_args),
                timeout=schema.timeout
            )
            
            # Update metrics
            execution_time = (time.time() - start_time) * 1000
            tool.metrics.total_executions += 1
            tool.metrics.successful_executions += 1
            tool.metrics.last_execution_time = datetime.now()
            tool.execution_count += 1
            tool.last_used = datetime.now()
            
            # Update average execution time
            if tool.metrics.execution_history:
                times = [h['execution_time_ms'] for h in tool.metrics.execution_history[-10:]]
                times.append(execution_time)
                tool.metrics.avg_execution_time_ms = sum(times) / len(times)
            else:
                tool.metrics.avg_execution_time_ms = execution_time
            
            # Add to execution history
            tool.metrics.execution_history.append({
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat(),
                'execution_time_ms': execution_time,
                'success': True,
                'arguments': validated_args
            })
            
            # Keep only last 50 executions
            if len(tool.metrics.execution_history) > 50:
                tool.metrics.execution_history = tool.metrics.execution_history[-50:]
            
            self.logger.info(f"✅ {tool.__class__.__name__} executed successfully in {execution_time:.1f}ms")
            
            return {
                'success': True,
                'result': result,
                'execution_time_ms': execution_time,
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Tool execution timeout after {schema.timeout}s"
            self._handle_tool_error(tool, error_msg, execution_id, start_time)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self._handle_tool_error(tool, error_msg, execution_id, start_time)
            raise e

    def _handle_tool_error(self, tool: BaseTool, error_msg: str, execution_id: str, start_time: float):
        """Handle tool execution errors with comprehensive logging"""
        execution_time = (time.time() - start_time) * 1000
        
        # Update error metrics
        tool.metrics.total_executions += 1
        tool.metrics.failed_executions += 1
        tool.metrics.last_error = error_msg
        
        # Add to execution history
        tool.metrics.execution_history.append({
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat(),
            'execution_time_ms': execution_time,
            'success': False,
            'error': error_msg
        })
        
        # Log error with context
        self.logger.error(f"❌ {tool.__class__.__name__} execution failed: {error_msg}")
        
        # Check if tool should be deactivated due to repeated failures
        recent_failures = [h for h in tool.metrics.execution_history[-10:] if not h['success']]
        if len(recent_failures) >= 5:  # 5 failures in last 10 executions
            tool.is_active = False
            self.logger.warning(f"🔴 Tool {tool.__class__.__name__} deactivated due to repeated failures")
    
    def register_tool(self, tool: BaseTool) -> bool:
        """Register a tool in the registry with enterprise validation"""
        try:
            if not isinstance(tool, BaseTool):
                raise ValueError("Tool must inherit from BaseTool")
            
            schema = tool.get_schema()
            tool_name = schema.name
            
            if tool_name in self.tools:
                self.logger.warning(f"Tool '{tool_name}' already registered, skipping")
                return False
            
            # Initialize tool
            if not tool._initialized:
                asyncio.create_task(tool.initialize())
            
            # Register tool
            self.tools[tool_name] = tool
            self._tool_schemas[tool_name] = schema
            
            # Add to category
            category = schema.category
            if category not in self._tool_categories:
                self._tool_categories[category] = []
            self._tool_categories[category].append(tool_name)
            
            # Initialize metrics
            self._tool_metrics[tool_name] = tool.metrics
            
            # Initialize circuit breaker
            self.circuit_breakers[tool_name] = {
                'enabled': True,
                'triggered': False,
                'failure_count': 0,
                'last_failure': None
            }
            
            self.logger.info(f"✅ Registered tool: {tool_name} ({category})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register tool: {e}")
            return False
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a tool with enterprise monitoring and circuit breaker protection"""
        if arguments is None:
            arguments = {}
            
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        
        # Check circuit breaker
        if self._is_circuit_breaker_triggered(tool_name):
            raise Exception(f"Circuit breaker triggered for tool {tool_name}")
        
        # Check if tool is active
        if not tool.is_active:
            raise Exception(f"Tool {tool_name} is currently deactivated")
        
        try:
            # Execute with monitoring
            result: str = await self.execute_tool_with_monitoring(tool, arguments)
            
            # Reset circuit breaker on success
            self._reset_circuit_breaker(tool_name)
            
            return result
            
        except Exception as e:
            # Update circuit breaker on failure
            self._handle_circuit_breaker_failure(tool_name)
            raise e

    async def execute_tool_with_monitoring(self, tool: BaseTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with comprehensive monitoring and error handling"""
        start_time = time.time()
        execution_id = f"{tool.__class__.__name__}_{int(time.time())}"
        
        try:
            # Pre-execution validation
            if not tool._initialized:
                await tool.initialize()
            
            # Validate arguments
            validated_args = tool.validate_arguments(arguments)
            
            # Log execution start
            if tool.get_schema().audit_logging:
                self.logger.info(f"🔄 Executing {tool.__class__.__name__} with args: {json.dumps(validated_args, default=str)}")
            
            # Execute with timeout
            schema = tool.get_schema()
            result: str = await asyncio.wait_for(
                tool.execute(**validated_args),
                timeout=schema.timeout
            )
            
            # Update metrics
            execution_time = (time.time() - start_time) * 1000
            tool.metrics.total_executions += 1
            tool.metrics.successful_executions += 1
            tool.metrics.last_execution_time = datetime.now()
            tool.execution_count += 1
            tool.last_used = datetime.now()
            
            # Update average execution time
            if tool.metrics.execution_history:
                times = [h['execution_time_ms'] for h in tool.metrics.execution_history[-10:]]
                times.append(execution_time)
                tool.metrics.avg_execution_time_ms = sum(times) / len(times)
            else:
                tool.metrics.avg_execution_time_ms = execution_time
            
            # Add to execution history
            tool.metrics.execution_history.append({
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat(),
                'execution_time_ms': execution_time,
                'success': True,
                'arguments': validated_args
            })
            
            # Keep only last 50 executions
            if len(tool.metrics.execution_history) > 50:
                tool.metrics.execution_history = tool.metrics.execution_history[-50:]
            
            self.logger.info(f"✅ {tool.__class__.__name__} executed successfully in {execution_time:.1f}ms")
            
            return {
                'success': True,
                'result': result,
                'execution_time_ms': execution_time,
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Tool execution timeout after {schema.timeout}s"
            self._handle_tool_error(tool, error_msg, execution_id, start_time)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self._handle_tool_error(tool, error_msg, execution_id, start_time)
            raise e

    def _handle_tool_error(self, tool: BaseTool, error_msg: str, execution_id: str, start_time: float):
        """Handle tool execution errors with comprehensive logging"""
        execution_time = (time.time() - start_time) * 1000
        
        # Update error metrics
        tool.metrics.total_executions += 1
        tool.metrics.failed_executions += 1
        tool.metrics.last_error = error_msg
        
        # Add to execution history
        tool.metrics.execution_history.append({
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat(),
            'execution_time_ms': execution_time,
            'success': False,
            'error': error_msg
        })
        
        # Log error with context
        self.logger.error(f"❌ {tool.__class__.__name__} execution failed: {error_msg}")
        
        # Check if tool should be deactivated due to repeated failures
        recent_failures = [h for h in tool.metrics.execution_history[-10:] if not h['success']]
        if len(recent_failures) >= 5:  # 5 failures in last 10 executions
            tool.is_active = False
            self.logger.warning(f"🔴 Tool {tool.__class__.__name__} deactivated due to repeated failures")

    def _is_circuit_breaker_triggered(self, tool_name: str) -> bool:
        """Check if circuit breaker is triggered for a tool"""
        cb = self.circuit_breakers.get(tool_name, {})
        return cb.get('triggered', False)

    def _reset_circuit_breaker(self, tool_name: str):
        """Reset circuit breaker on successful execution"""
        if tool_name in self.circuit_breakers:
            self.circuit_breakers[tool_name]['triggered'] = False
            self.circuit_breakers[tool_name]['failure_count'] = 0

    def _handle_circuit_breaker_failure(self, tool_name: str):
        """Handle circuit breaker failure"""
        if tool_name not in self.circuit_breakers:
            return
        
        cb = self.circuit_breakers[tool_name]
        cb['failure_count'] += 1
        cb['last_failure'] = datetime.now()
        
        # Trigger circuit breaker after 3 consecutive failures
        if cb['failure_count'] >= self.performance_thresholds['max_consecutive_failures']:
            cb['triggered'] = True
            self.logger.warning(f"🔴 Circuit breaker triggered for tool {tool_name}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with their schemas and metrics"""
        tools_list = []
        
        for tool_name, tool in self.tools.items():
            schema = self._tool_schemas[tool_name]
            metrics = tool.metrics
            
            tools_list.append({
                'name': tool_name,
                'description': schema.description,
                'category': schema.category,
                'tags': schema.tags,
                'risk_level': schema.risk_level,
                'is_active': tool.is_active,
                'metrics': {
                    'total_executions': metrics.total_executions,
                    'success_rate': (metrics.successful_executions / max(1, metrics.total_executions)) * 100,
                    'avg_execution_time_ms': metrics.avg_execution_time_ms,
                    'last_execution': metrics.last_execution_time.isoformat() if metrics.last_execution_time else None
                },
                'circuit_breaker': self.circuit_breakers.get(tool_name, {})
            })
        
        return tools_list

    def get_tool_metrics(self, tool_name: str = None) -> Dict[str, Any]:
        """Get comprehensive metrics for tools"""
        if tool_name:
            if tool_name not in self.tools:
                raise ValueError(f"Tool '{tool_name}' not found")
            
            tool = self.tools[tool_name]
            return {
                'tool_name': tool_name,
                'metrics': asdict(tool.metrics),
                'circuit_breaker': self.circuit_breakers.get(tool_name, {}),
                'is_active': tool.is_active,
                'last_used': tool.last_used.isoformat() if tool.last_used else None
            }
        else:
            # Return metrics for all tools
            all_metrics = {}
            for tool_name, tool in self.tools.items():
                all_metrics[tool_name] = {
                    'metrics': asdict(tool.metrics),
                    'circuit_breaker': self.circuit_breakers.get(tool_name, {}),
                    'is_active': tool.is_active
                }
            return all_metrics

    def get_tools_by_category(self, category: str) -> List[str]:
        """Get tools by category"""
        return self._tool_categories.get(category, [])

    def reset_circuit_breaker(self, tool_name: str) -> bool:
        """Manually reset a circuit breaker"""
        if tool_name not in self.circuit_breakers:
            return False
        
        self._reset_circuit_breaker(tool_name)
        self.logger.info(f"🟢 Circuit breaker reset for tool {tool_name}")
        return True

    def deactivate_tool(self, tool_name: str) -> bool:
        """Deactivate a tool"""
        if tool_name not in self.tools:
            return False
        
        self.tools[tool_name].is_active = False
        self.logger.warning(f"🔴 Tool {tool_name} deactivated")
        return True

    def activate_tool(self, tool_name: str) -> bool:
        """Activate a tool"""
        if tool_name not in self.tools:
            return False
        
        self.tools[tool_name].is_active = True
        self.logger.info(f"🟢 Tool {tool_name} activated")
        return True


# Legacy class alias for backwards compatibility
class ToolRegistry(EnterpriseToolRegistry):
    """Legacy alias for backwards compatibility"""
    pass
    
    async def _initialize_tools(self) -> None:
        """Initialize all registered tools."""
        init_tasks = []
        
        for name, tool in self._tools.items():
            task = self._initialize_single_tool(name, tool)
            init_tasks.append(task)
        
        # Initialize tools concurrently
        results = await asyncio.gather(*init_tasks, return_exceptions=True)
        
        # Log results
        successful = 0
        for i, result in enumerate(results):
            tool_name = list(self._tools.keys())[i]
            if isinstance(result, Exception):
                self.logger.error(f"Failed to initialize tool '{tool_name}': {result}")
            elif result:
                successful += 1
            else:
                self.logger.warning(f"Tool '{tool_name}' initialization returned False")
        
        self.logger.info(f"Successfully initialized {successful}/{len(self._tools)} tools")
    
    async def _initialize_single_tool(self, name: str, tool: BaseTool) -> bool:
        """Initialize a single tool with timeout and error handling."""
        try:
            schema = self._tool_schemas[name]
            timeout = schema.timeout if hasattr(schema, 'timeout') else 30
            
            result: str = await run_with_timeout(tool.initialize(), timeout)
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Tool '{name}' initialization timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error initializing tool '{name}': {e}")
            return False
    
    async def list_tools(self) -> List[Tool]:
        """Get list of all available tools in MCP format."""
        if not self._initialized:
            return []
        
        tools = []
        for name, schema in self._tool_schemas.items():
            tool = Tool(
                name=name,
                description=schema.description,
                inputSchema=schema.input_schema
            )
            tools.append(tool)
        
        return tools
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the given arguments."""
        if not self._initialized:
            raise RuntimeError("Tool registry not initialized")
        
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        
        tool = self._tools[name]
        schema = self._tool_schemas[name]
        
        try:
            # Validate arguments
            validated_args = tool.validate_arguments(arguments)
            
            # Execute with timeout
            timeout = getattr(schema, 'timeout', 30)
            result: str = await run_with_timeout(
                tool.execute(**validated_args), 
                timeout
            )
            
            self.logger.info(f"Tool '{name}' executed successfully")
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Tool '{name}' execution timed out after {timeout} seconds"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Tool '{name}' execution failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool."""
        if name not in self._tools:
            return None
        
        schema = self._tool_schemas[name]
        tool = self._tools[name]
        
        return {
            "name": schema.name,
            "description": schema.description,
            "category": schema.category,
            "tags": schema.tags,
            "input_schema": schema.input_schema,
            "initialized": tool._initialized,
            "requires_foundry": getattr(schema, 'requires_foundry', False),
            "requires_network": getattr(schema, 'requires_network', False),
        }
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """Get list of tool names in a specific category."""
        return self._tool_categories.get(category, [])
    
    def get_categories(self) -> List[str]:
        """Get list of all tool categories."""
        return list(self._tool_categories.keys())
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry."""
        total_tools = len(self._tools)
        initialized_tools = sum(1 for tool in self._tools.values() if tool._initialized)
        
        category_stats = {}
        for category, tools in self._tool_categories.items():
            category_stats[category] = {
                "count": len(tools),
                "tools": tools
            }
        
        return {
            "total_tools": total_tools,
            "initialized_tools": initialized_tools,
            "categories": category_stats,
            "initialization_rate": initialized_tools / total_tools if total_tools > 0 else 0
        }


# Tool discovery helpers
def create_tool_schema(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    category: str = "general",
    tags: List[str] = None,
    timeout: int = 30,
    requires_foundry: bool = False,
    requires_network: bool = False
) -> ToolSchema:
    """Helper function to create a tool schema."""
    return ToolSchema(
        name=name,
        description=description,
        input_schema=input_schema,
        category=category,
        tags=tags or [],
        timeout=timeout,
        requires_foundry=requires_foundry,
        requires_network=requires_network
    )