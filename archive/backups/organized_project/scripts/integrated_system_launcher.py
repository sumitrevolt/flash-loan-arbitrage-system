"""
Complete MCP-Agent Task Orchestration System Launcher
===================================================

This script launches the complete system with:
1. MCP Server and AI Agent discovery
2. Task orchestration and coordination
3. Real task execution
4. Web dashboard and API
5. Health monitoring and self-healing

Usage:
    python integrated_system_launcher.py

Author: GitHub Copilot Assistant
Date: June 18, 2025
"""

import asyncio
import logging
import sys
import os
import signal
from datetime import datetime
from typing import Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_agent_connection_bridge import MCPAgentBridge
from task_orchestrator import TaskOrchestrator
from real_task_executor import RealTaskExecutor
from enhanced_bridge_api import app, orchestrator as global_orchestrator
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integrated_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegratedSystemLauncher:
    """Main system launcher that coordinates all components"""
    
    def __init__(self):
        self.bridge: Optional[MCPAgentBridge] = None
        self.orchestrator: Optional[TaskOrchestrator] = None
        self.executor: Optional[RealTaskExecutor] = None
        self.api_server: Optional[uvicorn.Server] = None
        self.running = False
        
    async def start_system(self):
        """Start the complete integrated system"""
        logger.info("🚀 Starting Flash Loan MCP-Agent Task Orchestration System")
        logger.info("=" * 70)
        
        try:
            # 1. Initialize the bridge
            logger.info("📡 Initializing MCP-Agent Bridge...")
            self.bridge = MCPAgentBridge()
            await self.bridge.start()
            
            # 2. Initialize task orchestrator with bridge
            logger.info("🎯 Initializing Task Orchestrator...")
            self.orchestrator = TaskOrchestrator(bridge_client=self.bridge)
            
            # 3. Initialize real task executor
            logger.info("⚡ Initializing Real Task Executor...")
            self.executor = RealTaskExecutor()
            
            # 4. Connect orchestrator to executor
            self.orchestrator.task_executor = self.executor
            
            # 5. Start orchestrator
            await self.orchestrator.start()
            
            # 6. Update global orchestrator for API
            global global_orchestrator
            global_orchestrator = self.orchestrator
            
            # 7. Start the API server
            logger.info("🌐 Starting Web API and Dashboard...")
            await self.start_api_server()
            
            # 8. Start predefined workflows
            logger.info("🔄 Starting predefined workflows...")
            await self.start_predefined_workflows()
            
            self.running = True
            logger.info("✅ System startup complete!")
            logger.info("📊 Dashboard available at: http://localhost:8500/dashboard")
            logger.info("🔗 API documentation at: http://localhost:8500/docs")
            
        except Exception as e:
            logger.error(f"❌ System startup failed: {str(e)}")
            await self.shutdown()
            raise
    
    async def start_api_server(self):
        """Start the FastAPI server"""
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8500,
            log_level="info",
            access_log=True
        )
        
        # Start server in background
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        
        # Wait a moment for server to start
        await asyncio.sleep(2)
    
    async def start_predefined_workflows(self):
        """Start predefined workflows for demonstration"""
        if not self.orchestrator:
            return
            
        try:
            # 1. Start health check workflow
            logger.info("🏥 Starting system health check workflow...")
            health_workflow_id = await self.orchestrator.create_workflow(
                "system_health_check",
                {"interval_minutes": 5}
            )
            
            # 2. Start arbitrage monitoring workflow
            logger.info("💰 Starting arbitrage monitoring workflow...")
            arbitrage_workflow_id = await self.orchestrator.create_workflow(
                "arbitrage_monitoring",
                {"interval_minutes": 1, "min_profit_threshold": 0.01}
            )
            
            # 3. Start market analysis workflow
            logger.info("📈 Starting market analysis workflow...")
            market_workflow_id = await self.orchestrator.create_workflow(
                "market_analysis",
                {"interval_minutes": 15, "depth": "full"}
            )
            
            # 4. Create some sample tasks
            logger.info("📝 Creating sample tasks...")
            
            # Sample risk assessment task
            risk_task_id = await self.orchestrator.create_task(
                "risk_assessment",
                "Assess current portfolio risk",
                {"portfolio_id": "main", "risk_tolerance": "medium"}
            )
            
            # Sample data collection task
            data_task_id = await self.orchestrator.create_task(
                "collect_data",
                "Collect current market data",
                {"markets": ["ETH/USDC", "BTC/USDT", "DAI/USDC"]}
            )
            
            logger.info(f"✅ Started workflows: {health_workflow_id}, {arbitrage_workflow_id}, {market_workflow_id}")
            logger.info(f"✅ Created sample tasks: {risk_task_id}, {data_task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start predefined workflows: {str(e)}")
    
    async def monitor_system(self):
        """Monitor system health and performance"""
        while self.running:
            try:
                if self.bridge and self.orchestrator:
                    # Log system stats
                    stats = {
                        "timestamp": datetime.now().isoformat(),
                        "mcp_servers": len(self.bridge.mcp_servers),
                        "ai_agents": len(self.bridge.ai_agents),
                        "active_tasks": len(self.orchestrator.active_tasks),
                        "completed_tasks": len(self.orchestrator.completed_tasks),
                        "failed_tasks": len(self.orchestrator.failed_tasks)
                    }
                    
                    logger.info(f"📊 System Stats: {stats}")
                    
                    # Perform health checks
                    await self.perform_health_checks()
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"❌ System monitoring error: {str(e)}")
                await asyncio.sleep(30)  # Wait before retry
    
    async def perform_health_checks(self):
        """Perform health checks on all components"""
        try:
            # Check bridge health
            if self.bridge:
                await self.bridge.health_check()
            
            # Check orchestrator health
            if self.orchestrator:
                await self.orchestrator.health_check()
            
            # Check executor connectivity
            if self.executor and self.bridge:
                # Test connectivity to a sample agent
                agents = list(self.bridge.ai_agents.values())
                if agents:
                    sample_agent = agents[0]
                    async with self.executor as executor:
                        result = await executor.test_agent_connectivity(f"{sample_agent.host}:{sample_agent.port}")
                        if not result.success:
                            logger.warning(f"⚠️ Agent connectivity issue: {result.error}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
    
    async def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("🛑 Shutting down system...")
        self.running = False
        
        try:
            # Stop orchestrator
            if self.orchestrator:
                await self.orchestrator.stop()
                logger.info("✅ Orchestrator stopped")
            
            # Stop bridge
            if self.bridge:
                await self.bridge.stop()
                logger.info("✅ Bridge stopped")
            
            # Close executor
            if self.executor:
                logger.info("✅ Executor closed")
            
            logger.info("✅ System shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {str(e)}")
    
    async def run(self):
        """Main run loop"""
        try:
            # Setup signal handlers
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, shutting down...")
                asyncio.create_task(self.shutdown())
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Start the system
            await self.start_system()
            
            # Run monitoring loop
            await self.monitor_system()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"❌ System error: {str(e)}")
        finally:
            await self.shutdown()

async def main():
    """Main entry point"""
    launcher = IntegratedSystemLauncher()
    await launcher.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)
