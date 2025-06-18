#!/usr/bin/env python3
"""
AAVE Flash Loan System Startup
==============================

Starts all MCP servers and agents for the AAVE flash loan system.
Monitors system health and provides centralized control.
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List, Any
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_startup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("AaveSystemStartup")

class AaveSystemManager:
    """Manages the complete AAVE flash loan system"""
    
    def __init__(self):
        self.servers = {
            "aave_flash_loan": {
                "script": "mcp_servers/aave_flash_loan_mcp_server.py",
                "port": 8000,
                "process": None,
                "priority": 1,
                "description": "Primary AAVE flash loan execution server"
            },
            "dex_aggregator": {
                "script": "mcp_servers/dex_aggregator_mcp_server.py", 
                "port": 8001,
                "process": None,
                "priority": 2,
                "description": "DEX price aggregation server"
            },
            "risk_management": {
                "script": "mcp_servers/risk_management_mcp_server.py",
                "port": 8002,
                "process": None,
                "priority": 3,
                "description": "Risk assessment server"
            },
            "profit_optimizer": {
                "script": "mcp_servers/profit_optimizer_mcp_server.py",
                "port": 8003,
                "process": None,
                "priority": 4,
                "description": "Profit optimization server"
            },
            "monitoring": {
                "script": "mcp_servers/monitoring_mcp_server.py",
                "port": 8004,
                "process": None,
                "priority": 5,
                "description": "System monitoring server"
            }
        }
        
        self.running = False
        self.startup_time = None
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Load environment
        self.load_env()
    
    def load_env(self):
        """Load environment variables from .env file"""
        env_path = project_root / ".env"
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    def print_startup_banner(self):
        """Print system startup banner"""
        print("=" * 70)
        print("🚀 AAVE FLASH LOAN SYSTEM STARTUP")
        print("=" * 70)
        print(f"⏰ Startup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 Profit Target: ${os.getenv('MIN_PROFIT_USD', '4')}-${os.getenv('MAX_PROFIT_USD', '30')}")
        print(f"🔧 Execution Mode: {'🔴 LIVE' if os.getenv('ENABLE_REAL_EXECUTION', 'false').lower() == 'true' else '🟡 TEST'}")
        print(f"🌐 Network: Polygon")
        print(f"📊 Servers to Start: {len(self.servers)}")
        print("=" * 70)
    
    async def start_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Start a single MCP server"""
        try:
            script_path = project_root / server_config["script"]
            
            if not script_path.exists():
                logger.error(f"Server script not found: {script_path}")
                return False
            
            logger.info(f"Starting {server_name} ({server_config['description']})...")
            
            # Start the server process
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(project_root)
            )
            
            server_config["process"] = process
            
            # Give it a moment to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info(f"✅ {server_name} started successfully on port {server_config['port']}")
                return True
            else:
                # Process terminated, get error output
                stdout, stderr = process.communicate()
                logger.error(f"❌ {server_name} failed to start:")
                if stderr:
                    logger.error(f"Error: {stderr[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting {server_name}: {e}")
            return False
    
    async def start_all_servers(self):
        """Start all MCP servers in priority order"""
        logger.info("Starting MCP servers...")
        
        # Sort servers by priority
        sorted_servers = sorted(
            self.servers.items(),
            key=lambda x: x[1]["priority"]
        )
        
        started_count = 0
        failed_servers = []
        
        for server_name, server_config in sorted_servers:
            success = await self.start_server(server_name, server_config)
            
            if success:
                started_count += 1
            else:
                failed_servers.append(server_name)
            
            # Brief pause between server starts
            await asyncio.sleep(1)
        
        # Summary
        logger.info(f"Server startup complete: {started_count}/{len(self.servers)} started")
        
        if failed_servers:
            logger.warning(f"Failed to start: {', '.join(failed_servers)}")
        
        return started_count, failed_servers
    
    def check_server_health(self) -> Dict[str, str]:
        """Check health of all running servers"""
        health_status = {}
        
        for server_name, server_config in self.servers.items():
            process = server_config.get("process")
            
            if process is None:
                health_status[server_name] = "not_started"
            elif process.poll() is None:
                health_status[server_name] = "running"
            else:
                health_status[server_name] = "terminated"
        
        return health_status
    
    def stop_all_servers(self):
        """Stop all running servers"""
        logger.info("Stopping all MCP servers...")
        
        for server_name, server_config in self.servers.items():
            process = server_config.get("process")
            
            if process and process.poll() is None:
                logger.info(f"Stopping {server_name}...")
                try:
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                        logger.info(f"✅ {server_name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        # Force kill if necessary
                        process.kill()
                        logger.warning(f"⚠️ {server_name} force killed")
                        
                except Exception as e:
                    logger.error(f"Error stopping {server_name}: {e}")
    
    async def monitor_system(self):
        """Monitor system health during runtime"""
        logger.info("System monitoring started...")
        
        try:
            while self.running:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                health_status = self.check_server_health()
                running_count = sum(1 for status in health_status.values() if status == "running")
                
                if running_count == len(self.servers):
                    logger.info(f"System healthy: {running_count}/{len(self.servers)} servers running")
                else:
                    logger.warning(f"System degraded: {running_count}/{len(self.servers)} servers running")
                    
                    # Log individual server statuses
                    for server_name, status in health_status.items():
                        if status != "running":
                            logger.warning(f"  {server_name}: {status}")
                
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
    
    async def start_system(self):
        """Start the complete AAVE flash loan system"""
        self.startup_time = datetime.now()
        self.running = True
        
        # Print banner
        self.print_startup_banner()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start all servers
            started_count, failed_servers = await self.start_all_servers()
            
            if started_count == 0:
                logger.error("❌ No servers started successfully. Exiting.")
                return False
            
            # Display system status
            print("\n" + "=" * 50)
            print("🎯 SYSTEM STATUS")
            print("=" * 50)
            
            health_status = self.check_server_health()
            for server_name, server_config in self.servers.items():
                status = health_status[server_name]
                emoji = "✅" if status == "running" else "❌"
                print(f"{emoji} {server_name}: {status} - {server_config['description']}")
            
            print("=" * 50)
            
            if started_count == len(self.servers):
                print("🚀 ALL SYSTEMS GO! AAVE Flash Loan System Ready")
                print(f"💰 Monitoring for ${os.getenv('MIN_PROFIT_USD', '4')}-${os.getenv('MAX_PROFIT_USD', '30')} opportunities")
                print("🔍 Use Ctrl+C to shutdown gracefully")
            else:
                print(f"⚠️ PARTIAL SYSTEM START: {started_count}/{len(self.servers)} servers running")
                print("🔧 Check logs for failed server details")
            
            print("=" * 50)
            
            # Start monitoring
            await self.monitor_system()
            
        except Exception as e:
            logger.error(f"System startup error: {e}")
            return False
        
        finally:
            # Cleanup
            self.stop_all_servers()
            
            runtime = datetime.now() - self.startup_time if self.startup_time else "unknown"
            logger.info(f"System shutdown complete. Runtime: {runtime}")
        
        return True

async def main():
    """Main startup function"""
    system = AaveSystemManager()
    
    try:
        success = await system.start_system()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        return 0
    except Exception as e:
        logger.error(f"Startup error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
