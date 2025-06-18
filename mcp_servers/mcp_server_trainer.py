#!/usr/bin/env python3
"""
MCP Server Training and Management System
=========================================

Advanced system for training and managing Multiple MCP servers
with AI agent coordination and performance optimization.
"""

import asyncio
import logging
import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import threading
import queue
import psutil
import aiohttp
import aiofiles

logger = logging.getLogger(__name__)

class MCPServerStatus(Enum):
    """MCP Server status types"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    TRAINING = "training"
    UPDATING = "updating"

@dataclass
class MCPServerConfig:
    """Configuration for MCP servers"""
    name: str
    port: int
    script_path: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    auto_restart: bool = True
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    training_enabled: bool = True
    health_check_interval: int = 30

@dataclass
class TrainingData:
    """Training data for MCP servers"""
    data_id: str
    server_name: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    feedback_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServerMetrics:
    """Performance metrics for MCP servers"""
    server_name: str
    cpu_usage: float
    memory_usage: float
    request_count: int
    response_time_avg: float
    error_rate: float
    uptime: timedelta
    last_updated: datetime = field(default_factory=datetime.now)

class MCPServerManager:
    """Advanced MCP Server training and management system"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.mcp_servers_path = self.project_root / "mcp_servers"
        self.training_data_path = self.project_root / "training_data" / "mcp"
        self.logs_path = self.project_root / "logs" / "mcp"
        
        # Create directories
        self.training_data_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Server management
        self.servers = {}
        self.processes = {}
        self.metrics = {}
        self.training_sessions = {}
        
        # Initialize server configurations
        self._initialize_server_configs()
        
        # Background tasks
        self.monitoring_task = None
        self.training_task = None
    
    def _initialize_server_configs(self):
        """Initialize MCP server configurations"""
        logger.info("🔧 Initializing MCP server configurations...")
        
        # Define your MCP servers
        server_configs = [
            MCPServerConfig(
                name="copilot_mcp",
                port=8001,
                script_path="working_enhanced_copilot_mcp_server.py",
                description="GitHub Copilot integration MCP server",
                capabilities=["code_assistance", "code_generation", "code_review"],
                dependencies=["requests", "openai", "langchain"]
            ),
            MCPServerConfig(
                name="flash_loan_mcp",
                port=8002,
                script_path="working_flash_loan_mcp.py",
                description="Flash loan arbitrage MCP server",
                capabilities=["arbitrage_detection", "price_monitoring", "trade_execution"],
                dependencies=["web3", "requests", "pandas"]
            ),
            MCPServerConfig(
                name="context7_mcp",
                port=8003,
                script_path="clean_context7_mcp_server.py",
                description="Context7 library integration MCP server",
                capabilities=["context_retrieval", "documentation", "api_integration"],
                dependencies=["requests", "beautifulsoup4"]
            ),
            MCPServerConfig(
                name="real_time_price_mcp",
                port=8004,
                script_path="real_time_price_mcp_server.py",
                description="Real-time price monitoring MCP server",
                capabilities=["price_monitoring", "market_data", "alerts"],
                dependencies=["websockets", "requests", "pandas"]
            ),
            MCPServerConfig(
                name="aave_flash_loan_mcp",
                port=8005,
                script_path="aave_flash_loan_mcp_server.py",
                description="AAVE flash loan MCP server",
                capabilities=["aave_integration", "flash_loans", "defi_protocols"],
                dependencies=["web3", "eth-brownie"]
            ),
            MCPServerConfig(
                name="foundry_mcp",
                port=8006,
                script_path="foundry_mcp_mcp_server.py",
                description="Foundry development tools MCP server",
                capabilities=["smart_contracts", "testing", "deployment"],
                dependencies=["foundry"]
            ),
            MCPServerConfig(
                name="evm_mcp",
                port=8007,
                script_path="evm_mcp_server.py",
                description="EVM blockchain integration MCP server",
                capabilities=["blockchain_interaction", "transaction_monitoring", "contract_calls"],
                dependencies=["web3", "eth-utils"]
            )
        ]
        
        for config in server_configs:
            self.servers[config.name] = {
                "config": config,
                "status": MCPServerStatus.STOPPED,
                "process": None,
                "last_health_check": None,
                "restart_count": 0,
                "training_data": []
            }
        
        logger.info(f"✅ Initialized {len(server_configs)} MCP server configurations")
    
    async def start_server(self, server_name: str) -> Dict[str, Any]:
        """Start an MCP server"""
        if server_name not in self.servers:
            return {"success": False, "error": f"Server {server_name} not found"}
        
        server_info = self.servers[server_name]
        config = server_info["config"]
        
        if server_info["status"] == MCPServerStatus.RUNNING:
            return {"success": False, "error": f"Server {server_name} is already running"}
        
        logger.info(f"🚀 Starting MCP server: {server_name}")
        
        try:
            # Update status
            server_info["status"] = MCPServerStatus.STARTING
            
            # Construct command
            script_path = self.mcp_servers_path / config.script_path
            if not script_path.exists():
                return {"success": False, "error": f"Script not found: {script_path}"}
            
            # Start process
            cmd = [
                "python",
                str(script_path),
                "--port", str(config.port),
                "--name", server_name
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.mcp_servers_path
            )
            
            # Store process
            server_info["process"] = process
            self.processes[server_name] = process
            
            # Wait a moment for startup
            await asyncio.sleep(2)
            
            # Check if process is still running
            if process.returncode is None:
                server_info["status"] = MCPServerStatus.RUNNING
                server_info["last_health_check"] = datetime.now()
                
                logger.info(f"✅ MCP server {server_name} started successfully on port {config.port}")
                return {
                    "success": True,
                    "server": server_name,
                    "port": config.port,
                    "status": "running"
                }
            else:
                server_info["status"] = MCPServerStatus.ERROR
                stdout, stderr = await process.communicate()
                
                error_msg = f"Process exited with code {process.returncode}"
                if stderr:
                    error_msg += f". Error: {stderr.decode()}"
                
                logger.error(f"❌ Failed to start MCP server {server_name}: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            server_info["status"] = MCPServerStatus.ERROR
            logger.error(f"❌ Exception starting server {server_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_server(self, server_name: str) -> Dict[str, Any]:
        """Stop an MCP server"""
        if server_name not in self.servers:
            return {"success": False, "error": f"Server {server_name} not found"}
        
        server_info = self.servers[server_name]
        
        if server_info["status"] == MCPServerStatus.STOPPED:
            return {"success": False, "error": f"Server {server_name} is already stopped"}
        
        logger.info(f"🛑 Stopping MCP server: {server_name}")
        
        try:
            process = server_info["process"]
            if process and process.returncode is None:
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ Force killing server {server_name}")
                    process.kill()
                    await process.wait()
            
            # Update status
            server_info["status"] = MCPServerStatus.STOPPED
            server_info["process"] = None
            
            if server_name in self.processes:
                del self.processes[server_name]
            
            logger.info(f"✅ MCP server {server_name} stopped successfully")
            return {"success": True, "server": server_name, "status": "stopped"}
            
        except Exception as e:
            logger.error(f"❌ Error stopping server {server_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def restart_server(self, server_name: str) -> Dict[str, Any]:
        """Restart an MCP server"""
        logger.info(f"🔄 Restarting MCP server: {server_name}")
        
        # Stop server
        stop_result = await self.stop_server(server_name)
        if not stop_result["success"] and "already stopped" not in stop_result["error"]:
            return stop_result
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Start server
        start_result = await self.start_server(server_name)
        
        if start_result["success"]:
            self.servers[server_name]["restart_count"] += 1
        
        return start_result
    
    async def start_all_servers(self) -> Dict[str, Any]:
        """Start all MCP servers"""
        logger.info("🚀 Starting all MCP servers...")
        
        results = {}
        
        for server_name in self.servers.keys():
            result = await self.start_server(server_name)
            results[server_name] = result
            
            # Small delay between starts
            await asyncio.sleep(1)
        
        successful_starts = sum(1 for r in results.values() if r["success"])
        
        logger.info(f"✅ Started {successful_starts}/{len(results)} MCP servers")
        
        return {
            "success": True,
            "total_servers": len(results),
            "successful_starts": successful_starts,
            "results": results
        }
    
    async def stop_all_servers(self) -> Dict[str, Any]:
        """Stop all MCP servers"""
        logger.info("🛑 Stopping all MCP servers...")
        
        results = {}
        
        for server_name in self.servers.keys():
            result = await self.stop_server(server_name)
            results[server_name] = result
        
        successful_stops = sum(1 for r in results.values() if r["success"])
        
        logger.info(f"✅ Stopped {successful_stops}/{len(results)} MCP servers")
        
        return {
            "success": True,
            "total_servers": len(results),
            "successful_stops": successful_stops,
            "results": results
        }
    
    async def check_server_health(self, server_name: str) -> Dict[str, Any]:
        """Check health of an MCP server"""
        if server_name not in self.servers:
            return {"success": False, "error": f"Server {server_name} not found"}
        
        server_info = self.servers[server_name]
        config = server_info["config"]
        
        try:
            # Check if process is running
            process = server_info["process"]
            process_running = process and process.returncode is None
            
            # Try to connect to server
            health_check_url = f"http://localhost:{config.port}/health"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                try:
                    async with session.get(health_check_url) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            health_status = "healthy"
                        else:
                            health_status = f"unhealthy (HTTP {response.status})"
                            response_data = {}
                except Exception:
                    health_status = "unreachable"
                    response_data = {}
            
            # Get system metrics if process is running
            metrics = {}
            if process_running:
                try:
                    proc = psutil.Process(process.pid)
                    metrics = {
                        "cpu_percent": proc.cpu_percent(),
                        "memory_mb": proc.memory_info().rss / 1024 / 1024,
                        "status": proc.status()
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    metrics = {"error": "Could not access process metrics"}
            
            # Update last health check
            server_info["last_health_check"] = datetime.now()
            
            return {
                "success": True,
                "server": server_name,
                "process_running": process_running,
                "health_status": health_status,
                "metrics": metrics,
                "response_data": response_data,
                "last_check": server_info["last_health_check"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed for {server_name}: {e}")
            return {
                "success": False,
                "server": server_name,
                "error": str(e)
            }
    
    async def check_all_servers_health(self) -> Dict[str, Any]:
        """Check health of all MCP servers"""
        results = {}
        
        for server_name in self.servers.keys():
            results[server_name] = await self.check_server_health(server_name)
        
        healthy_servers = sum(1 for r in results.values() if r.get("success") and r.get("health_status") == "healthy")
        
        return {
            "total_servers": len(results),
            "healthy_servers": healthy_servers,
            "health_percentage": (healthy_servers / len(results) * 100) if results else 0,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def add_training_data(self, server_name: str, input_data: Dict, expected_output: Dict, feedback_score: float = 0.0) -> str:
        """Add training data for an MCP server"""
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not found")
        
        training_data = TrainingData(
            data_id=str(uuid.uuid4()),
            server_name=server_name,
            input_data=input_data,
            expected_output=expected_output,
            feedback_score=feedback_score
        )
        
        # Add to server's training data
        self.servers[server_name]["training_data"].append(training_data)
        
        # Save to file
        await self._save_training_data(training_data)
        
        logger.info(f"📊 Added training data for {server_name}: {training_data.data_id}")
        return training_data.data_id
    
    async def _save_training_data(self, training_data: TrainingData):
        """Save training data to file"""
        file_path = self.training_data_path / f"{training_data.server_name}_training_data.jsonl"
        
        data_line = {
            "data_id": training_data.data_id,
            "server_name": training_data.server_name,
            "input_data": training_data.input_data,
            "expected_output": training_data.expected_output,
            "feedback_score": training_data.feedback_score,
            "timestamp": training_data.timestamp.isoformat(),
            "metadata": training_data.metadata
        }
        
        async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
            await f.write(json.dumps(data_line) + '\n')
    
    async def train_server(self, server_name: str, training_data: List[TrainingData] = None) -> Dict[str, Any]:
        """Train an MCP server with provided or collected data"""
        if server_name not in self.servers:
            return {"success": False, "error": f"Server {server_name} not found"}
        
        server_info = self.servers[server_name]
        
        # Use provided data or server's collected data
        if training_data is None:
            training_data = server_info["training_data"]
        
        if not training_data:
            return {"success": False, "error": f"No training data available for {server_name}"}
        
        logger.info(f"🎓 Starting training for MCP server: {server_name} with {len(training_data)} samples")
        
        try:
            # Update server status
            server_info["status"] = MCPServerStatus.TRAINING
            
            # Create training session
            session_id = str(uuid.uuid4())
            training_session = {
                "session_id": session_id,
                "server_name": server_name,
                "start_time": datetime.now(),
                "total_samples": len(training_data),
                "processed_samples": 0,
                "success_rate": 0.0,
                "status": "running"
            }
            
            self.training_sessions[session_id] = training_session
            
            # Process training data (simulate training)
            processed_samples = 0
            successful_samples = 0
            
            for i, data in enumerate(training_data):
                try:
                    # Simulate training process
                    await asyncio.sleep(0.1)  # Simulate processing time
                    
                    # Simulate success/failure based on feedback score
                    if data.feedback_score > 0.5:
                        successful_samples += 1
                    
                    processed_samples += 1
                    
                    if i % 10 == 0:
                        logger.info(f"📊 Training progress: {i+1}/{len(training_data)} samples processed")
                
                except Exception as e:
                    logger.error(f"❌ Error processing training sample {i}: {e}")
            
            # Calculate results
            success_rate = successful_samples / processed_samples if processed_samples > 0 else 0
            
            # Update training session
            training_session.update({
                "end_time": datetime.now(),
                "processed_samples": processed_samples,
                "success_rate": success_rate,
                "status": "completed"
            })
            
            # Update server status
            server_info["status"] = MCPServerStatus.RUNNING
            
            # Save training results
            await self._save_training_session(training_session)
            
            logger.info(f"✅ Training completed for {server_name}. Success rate: {success_rate:.2%}")
            
            return {
                "success": True,
                "session_id": session_id,
                "server_name": server_name,
                "processed_samples": processed_samples,
                "success_rate": success_rate,
                "duration": str(training_session["end_time"] - training_session["start_time"])
            }
            
        except Exception as e:
            server_info["status"] = MCPServerStatus.ERROR
            logger.error(f"❌ Training failed for {server_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _save_training_session(self, session: Dict[str, Any]):
        """Save training session results"""
        file_path = self.training_data_path / f"training_session_{session['session_id']}.json"
        
        # Convert datetime objects to strings for JSON serialization
        session_copy = session.copy()
        for key, value in session_copy.items():
            if isinstance(value, datetime):
                session_copy[key] = value.isoformat()
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(session_copy, indent=2))
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "total_servers": len(self.servers),
            "servers": {}
        }
        
        for server_name, server_info in self.servers.items():
            config = server_info["config"]
            status["servers"][server_name] = {
                "name": server_name,
                "port": config.port,
                "status": server_info["status"].value,
                "description": config.description,
                "capabilities": config.capabilities,
                "restart_count": server_info["restart_count"],
                "training_data_count": len(server_info["training_data"]),
                "last_health_check": server_info["last_health_check"].isoformat() if server_info["last_health_check"] else None
            }
        
        return status
    
    async def start_monitoring(self):
        """Start background monitoring of servers"""
        logger.info("🔍 Starting MCP server monitoring...")
        
        while True:
            try:
                # Check health of all servers
                health_results = await self.check_all_servers_health()
                
                # Restart unhealthy servers if auto-restart is enabled
                for server_name, result in health_results["results"].items():
                    if not result.get("success") or result.get("health_status") != "healthy":
                        server_info = self.servers[server_name]
                        config = server_info["config"]
                        
                        if config.auto_restart and server_info["status"] == MCPServerStatus.RUNNING:
                            logger.warning(f"⚠️ Server {server_name} is unhealthy, attempting restart...")
                            await self.restart_server(server_name)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        health_check = await self.check_all_servers_health()
        status = await self.get_server_status()
        
        # Calculate aggregate metrics
        total_training_samples = sum(
            len(server_info["training_data"]) 
            for server_info in self.servers.values()
        )
        
        total_restarts = sum(
            server_info["restart_count"]
            for server_info in self.servers.values()
        )
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_servers": len(self.servers),
                "healthy_servers": health_check["healthy_servers"],
                "health_percentage": health_check["health_percentage"],
                "total_training_samples": total_training_samples,
                "total_restarts": total_restarts,
                "training_sessions": len(self.training_sessions)
            },
            "server_details": status["servers"],
            "health_check_results": health_check["results"],
            "training_sessions": list(self.training_sessions.keys())
        }
        
        return report

async def main():
    """Main function for testing"""
    manager = MCPServerManager()
    
    try:
        # Start all servers
        logger.info("🚀 Starting MCP Server Manager demo...")
        
        start_results = await manager.start_all_servers()
        print(f"Started {start_results['successful_starts']} servers")
        
        # Wait a moment
        await asyncio.sleep(5)
        
        # Check health
        health_results = await manager.check_all_servers_health()
        print(f"Health check: {health_results['healthy_servers']}/{health_results['total_servers']} servers healthy")
        
        # Add some training data
        await manager.add_training_data(
            "copilot_mcp",
            {"code": "def hello():", "language": "python"},
            {"suggestion": "Add proper documentation and error handling"},
            0.8
        )
        
        # Generate report
        report = await manager.generate_performance_report()
        print("Performance Report:")
        print(json.dumps(report, indent=2, default=str))
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    finally:
        await manager.stop_all_servers()

if __name__ == "__main__":
    asyncio.run(main())
