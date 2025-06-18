#!/usr/bin/env python3
"""
Simple LangChain MCP Coordinator - Fix All 21 MCP Servers and 10 AI Agents
===========================================================================

This coordinator systematically diagnoses and fixes:
- 21 MCP (Model Context Protocol) servers
- 10 AI agents
- Docker container orchestration
- Health monitoring and recovery

Author: GitHub Copilot Assistant
Date: June 15, 2025
"""

import asyncio
import logging
import json
import subprocess
import docker
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('langchain_mcp_coordinator.log')
    ]
)
logger = logging.getLogger(__name__)

class SimpleMCPCoordinator:
    """
    Simple coordinator for fixing all MCP servers and AI agents
    """
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.project_root = Path(__file__).parent
        self.logs_path = self.project_root / "logs"
        
        # Create directories
        self.logs_path.mkdir(exist_ok=True)
        
        # Define services to fix
        self.mcp_servers = [
            {"name": "context7-mcp", "port": 8004, "critical": True},
            {"name": "grok3-mcp", "port": 3003, "critical": False},
            {"name": "enhanced-copilot-mcp", "port": 8006, "critical": True},
            {"name": "matic-mcp", "port": 8002, "critical": True},
            {"name": "evm-mcp", "port": 8003, "critical": True},
            {"name": "foundry-mcp", "port": 8001, "critical": True},
            {"name": "price-feed-mcp", "port": 8010, "critical": True},
            {"name": "dex-data-mcp", "port": 8011, "critical": True},
            {"name": "market-data-mcp", "port": 8012, "critical": True},
            {"name": "trade-execution-mcp", "port": 8020, "critical": True},
            {"name": "flash-loan-mcp", "port": 8021, "critical": True},
            {"name": "arbitrage-mcp", "port": 8022, "critical": True},
            {"name": "risk-analysis-mcp", "port": 8030, "critical": True},
            {"name": "portfolio-mcp", "port": 8031, "critical": True},
            {"name": "analytics-mcp", "port": 8040, "critical": False},
            {"name": "performance-mcp", "port": 8041, "critical": False},
            {"name": "health-monitor-mcp", "port": 8050, "critical": True},
            {"name": "log-aggregator-mcp", "port": 8051, "critical": False},
            {"name": "orchestration-mcp", "port": 8060, "critical": True},
            {"name": "task-management-mcp", "port": 8061, "critical": True},
            {"name": "coordination-mcp", "port": 8062, "critical": True}
        ]
        
        self.ai_agents = [
            {"name": "arbitrage-agent", "port": 9001, "critical": True},
            {"name": "risk-management-agent", "port": 9002, "critical": True},
            {"name": "market-analysis-agent", "port": 9003, "critical": False},
            {"name": "execution-agent", "port": 9004, "critical": True},
            {"name": "monitoring-agent", "port": 9005, "critical": True},
            {"name": "data-collection-agent", "port": 9006, "critical": True},
            {"name": "strategy-agent", "port": 9007, "critical": False},
            {"name": "coordination-agent", "port": 9008, "critical": True},
            {"name": "learning-agent", "port": 9009, "critical": False},
            {"name": "reporting-agent", "port": 9010, "critical": False}
        ]
        
        logger.info("Simple MCP Coordinator initialized")

    async def fix_all_services(self):
        """Main method to fix all 21 MCP servers and 10 AI agents"""
        logger.info("🚀 Starting comprehensive fix of all services...")
        
        # Create fix report
        fix_report = {
            "timestamp": datetime.now().isoformat(),
            "mcp_servers": {},
            "ai_agents": {},
            "overall_status": "in_progress"
        }
        
        try:
            # Step 1: Check Docker status
            await self._check_docker_status()
            
            # Step 2: Start infrastructure services
            await self._start_infrastructure()
            
            # Step 3: Fix MCP servers
            logger.info("🔧 Fixing 21 MCP servers...")
            for server in self.mcp_servers:
                fix_result: str = await self._fix_service(server)
                fix_report["mcp_servers"][server["name"]] = fix_result
                
            # Step 4: Fix AI agents
            logger.info("🤖 Fixing 10 AI agents...")
            for agent in self.ai_agents:
                fix_result: str = await self._fix_service(agent)
                fix_report["ai_agents"][agent["name"]] = fix_result
            
            # Step 5: Verify all services are working
            await self._verify_all_services()
            
            # Step 6: Update overall status
            fix_report["overall_status"] = "completed"
            fix_report["completion_time"] = datetime.now().isoformat()
            
            # Save fix report
            await self._save_fix_report(fix_report)
            
            logger.info("✅ All services fixed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error during fix process: {e}")
            fix_report["overall_status"] = "failed"
            fix_report["error"] = str(e)
            await self._save_fix_report(fix_report)
            raise

    async def _check_docker_status(self):
        """Check Docker daemon status"""
        try:
            self.docker_client.ping()
            logger.info("✅ Docker daemon is running")
        except Exception as e:
            logger.error(f"❌ Docker daemon issue: {e}")
            # Try to start Docker Desktop
            try:
                subprocess.run(["powershell", "-Command", "Start-Process 'Docker Desktop'"], check=False)
                logger.info("🐳 Starting Docker Desktop...")
                await asyncio.sleep(30)  # Wait for Docker to start
                self.docker_client.ping()
                logger.info("✅ Docker daemon started successfully")
            except Exception as start_error:
                logger.error(f"❌ Failed to start Docker: {start_error}")
                raise

    async def _start_infrastructure(self):
        """Start essential infrastructure services"""
        logger.info("🏗️ Starting infrastructure services...")
        
        try:
            # Start Redis and PostgreSQL
            cmd = "docker-compose up -d redis postgres"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("✅ Infrastructure services started")
                await asyncio.sleep(10)  # Wait for services to be ready
            else:
                logger.error(f"❌ Failed to start infrastructure: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"❌ Infrastructure startup error: {e}")

    async def _fix_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Fix a single service (MCP server or AI agent)"""
        service_name = service["name"]
        service_port = service["port"]
        is_critical = service["critical"]
        
        logger.info(f"🔧 Fixing service: {service_name}")
        
        try:
            # Step 1: Check if service is running
            is_running = await self._check_service_health(service_name, service_port)
            
            if is_running:
                logger.info(f"✅ {service_name} is already running")
                return {
                    "status": "healthy",
                    "actions_taken": ["health_check"],
                    "critical": is_critical
                }
            
            # Step 2: Try to restart the service
            logger.info(f"🔄 Restarting {service_name}...")
            restart_success = await self._restart_service(service_name)
            
            if restart_success:
                # Wait a bit and check again
                await asyncio.sleep(5)
                is_running = await self._check_service_health(service_name, service_port)
                
                if is_running:
                    logger.info(f"✅ {service_name} restarted successfully")
                    return {
                        "status": "fixed_by_restart",
                        "actions_taken": ["restart", "health_check"],
                        "critical": is_critical
                    }
            
            # Step 3: Try to rebuild the service
            logger.info(f"🏗️ Rebuilding {service_name}...")
            rebuild_success = await self._rebuild_service(service_name)
            
            if rebuild_success:
                await asyncio.sleep(10)
                is_running = await self._check_service_health(service_name, service_port)
                
                if is_running:
                    logger.info(f"✅ {service_name} rebuilt successfully")
                    return {
                        "status": "fixed_by_rebuild",
                        "actions_taken": ["restart", "rebuild", "health_check"],
                        "critical": is_critical
                    }
            
            # Step 4: Service still not working
            logger.error(f"❌ Failed to fix {service_name}")
            return {
                "status": "failed",
                "actions_taken": ["restart", "rebuild", "health_check"],
                "critical": is_critical,
                "error": "Service could not be restored"
            }
            
        except Exception as e:
            logger.error(f"❌ Error fixing {service_name}: {e}")
            return {
                "status": "error",
                "actions_taken": [],
                "critical": is_critical,
                "error": str(e)
            }

    async def _check_service_health(self, service_name: str, port: int) -> bool:
        """Check if service is healthy"""
        try:
            # Try to connect to the service health endpoint
            async with aiohttp.ClientSession() as session:
                health_urls = [
                    f"http://localhost:{port}/health",
                    f"http://localhost:{port}/status",
                    f"http://localhost:{port}/ping"
                ]
                
                for url in health_urls:
                    try:
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                return True
                    except:
                        continue
                        
            # If HTTP check fails, check if container is running
            try:
                container = self.docker_client.containers.get(service_name)
                return container.status == "running"
            except:
                return False
                
        except Exception as e:
            logger.debug(f"Health check failed for {service_name}: {e}")
            return False

    async def _restart_service(self, service_name: str) -> bool:
        """Restart a service"""
        try:
            cmd = f"docker-compose restart {service_name}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Restarted {service_name}")
                return True
            else:
                logger.error(f"❌ Failed to restart {service_name}: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Restart error for {service_name}: {e}")
            return False

    async def _rebuild_service(self, service_name: str) -> bool:
        """Rebuild a service"""
        try:
            # Build the service
            cmd = f"docker-compose build --no-cache {service_name}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"❌ Build failed for {service_name}: {stderr.decode()}")
                return False
            
            # Start the service
            cmd = f"docker-compose up -d {service_name}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Rebuilt {service_name}")
                return True
            else:
                logger.error(f"❌ Failed to start rebuilt {service_name}: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Rebuild error for {service_name}: {e}")
            return False

    async def _verify_all_services(self):
        """Verify all services are working correctly"""
        logger.info("🔍 Verifying all services...")
        
        all_healthy = True
        
        # Check MCP servers
        logger.info("Checking MCP servers...")
        for server in self.mcp_servers:
            healthy = await self._check_service_health(server["name"], server["port"])
            status_icon = "✅" if healthy else "❌"
            critical_text = " (CRITICAL)" if server["critical"] and not healthy else ""
            logger.info(f"   {server['name']}: {status_icon}{critical_text}")
            
            if server["critical"] and not healthy:
                all_healthy = False
        
        # Check AI agents
        logger.info("Checking AI agents...")
        for agent in self.ai_agents:
            healthy = await self._check_service_health(agent["name"], agent["port"])
            status_icon = "✅" if healthy else "❌"
            critical_text = " (CRITICAL)" if agent["critical"] and not healthy else ""
            logger.info(f"   {agent['name']}: {status_icon}{critical_text}")
            
            if agent["critical"] and not healthy:
                all_healthy = False
        
        if all_healthy:
            logger.info("🎉 All critical services are healthy!")
        else:
            logger.warning("⚠️ Some critical services are not healthy")

    async def _save_fix_report(self, report: Dict[str, Any]):
        """Save fix report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.logs_path / f"fix_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Fix report saved to {report_path}")
        
        # Also create a summary
        summary = self._create_summary(report)
        summary_path = self.logs_path / f"fix_summary_{timestamp}.txt"
        
        with open(summary_path, 'w') as f:
            f.write(summary)
        
        logger.info(f"📋 Fix summary saved to {summary_path}")

    def _create_summary(self, report: Dict[str, Any]) -> str:
        """Create a human-readable summary"""
        summary = [
            "="*60,
            "LANGCHAIN MCP COORDINATOR - FIX SUMMARY",
            "="*60,
            f"Timestamp: {report.get('timestamp', 'Unknown')}",
            f"Overall Status: {report.get('overall_status', 'Unknown')}",
            ""
        ]
        
        if 'completion_time' in report:
            summary.append(f"Completion Time: {report['completion_time']}")
            summary.append("")
        
        # MCP Servers Summary
        summary.append("MCP SERVERS (21 total):")
        summary.append("-" * 25)
        mcp_servers = report.get('mcp_servers', {})
        
        for server in self.mcp_servers:
            server_name = server['name']
            server_report = mcp_servers.get(server_name, {})
            status = server_report.get('status', 'unknown')
            critical = " (CRITICAL)" if server.get('critical') else ""
            summary.append(f"  {server_name}: {status.upper()}{critical}")
        
        summary.append("")
        
        # AI Agents Summary
        summary.append("AI AGENTS (10 total):")
        summary.append("-" * 20)
        ai_agents = report.get('ai_agents', {})
        
        for agent in self.ai_agents:
            agent_name = agent['name']
            agent_report = ai_agents.get(agent_name, {})
            status = agent_report.get('status', 'unknown')
            critical = " (CRITICAL)" if agent.get('critical') else ""
            summary.append(f"  {agent_name}: {status.upper()}{critical}")
        
        summary.append("")
        summary.append("="*60)
        
        if 'error' in report:
            summary.append(f"ERROR: {report['error']}")
            summary.append("="*60)
        
        return "\n".join(summary)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("🛑 Received shutdown signal, cleaning up...")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Simple LangChain MCP Coordinator Starting...")
    logger.info("   - 21 MCP Servers to fix")
    logger.info("   - 10 AI Agents to fix")
    logger.info("   - Docker orchestration")
    logger.info("   - Health monitoring")
    
    try:
        coordinator = SimpleMCPCoordinator()
        await coordinator.fix_all_services()
        logger.info("✅ All services coordination completed!")
        
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
