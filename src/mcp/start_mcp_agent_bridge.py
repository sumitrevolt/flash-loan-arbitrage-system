#!/usr/bin/env python3
"""
Start MCP-Agent Connection Bridge
===============================

This script starts the MCP-Agent connection bridge to facilitate communication
between MCP servers and AI agents running in Docker containers.

Features:
- Automatic service discovery
- Connection establishment
- Health monitoring
- Task coordination
- Web dashboard

Usage:
    python start_mcp_agent_bridge.py
    python start_mcp_agent_bridge.py --api-only
    python start_mcp_agent_bridge.py --bridge-only

Author: GitHub Copilot Assistant
Date: June 18, 2025
"""

import argparse
import asyncio
import logging
import sys
import signal
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from mcp_agent_connection_bridge import MCPAgentBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_agent_bridge_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BridgeStarter:
    """Manages the startup of the MCP-Agent bridge components"""
    
    def __init__(self):
        self.bridge: Optional[MCPAgentBridge] = None
        self.api_process: Optional[subprocess.Popen] = None
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"📞 Received signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        try:
            # Check if Docker is running
            import docker
            client = docker.from_env()
            containers = client.containers.list()
            
            mcp_containers = [c for c in containers if 'mcp' in c.name.lower()]
            agent_containers = [c for c in containers if 'agent' in c.name.lower()]
            
            if not mcp_containers:
                logger.error("❌ No MCP server containers found running")
                return False
            
            if not agent_containers:
                logger.error("❌ No AI agent containers found running")
                return False
            
            logger.info(f"✅ Found {len(mcp_containers)} MCP containers and {len(agent_containers)} agent containers")
            
            # Check if Redis is available (optional)
            try:
                import redis
                redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                redis_client.ping()
                logger.info("✅ Redis is available for inter-service communication")
            except Exception as e:
                logger.warning(f"⚠️ Redis not available: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking prerequisites: {e}")
            return False
    
    def start_api_server(self):
        """Start the API server in a separate process"""
        logger.info("🚀 Starting API server...")
        
        try:
            # Start the API server
            self.api_process = subprocess.Popen([
                sys.executable, "mcp_agent_bridge_api.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if it's still running
            if self.api_process.poll() is None:
                logger.info("✅ API server started successfully on port 8500")
                logger.info("🌐 Dashboard available at: http://localhost:8500/dashboard")
                return True
            else:
                logger.error("❌ API server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting API server: {e}")
            return False
    
    async def start_bridge(self):
        """Start the bridge"""
        logger.info("🌉 Starting MCP-Agent Bridge...")
        
        try:
            self.bridge = MCPAgentBridge()
            self.running = True
            
            await self.bridge.start()
            
        except Exception as e:
            logger.error(f"❌ Error starting bridge: {e}")
            self.running = False
    
    def run_bridge_only(self):
        """Run only the bridge (no API server)"""
        logger.info("🚀 Starting bridge-only mode...")
        
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites not met, exiting")
            return False
        
        self.setup_signal_handlers()
        
        try:
            asyncio.run(self.start_bridge())
            return True
        except KeyboardInterrupt:
            logger.info("🛑 Bridge stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ Bridge failed: {e}")
            return False
    
    def run_api_only(self):
        """Run only the API server"""
        logger.info("🚀 Starting API-only mode...")
        
        self.setup_signal_handlers()
        
        if self.start_api_server():
            try:
                # Keep the main process alive
                while True:
                    if self.api_process.poll() is not None:
                        logger.error("❌ API server stopped unexpectedly")
                        break
                    time.sleep(1)
                return True
            except KeyboardInterrupt:
                logger.info("🛑 API server stopped by user")
                return True
        else:
            return False
    
    def run_full_system(self):
        """Run both bridge and API server"""
        logger.info("🚀 Starting full system (bridge + API)...")
        
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites not met, exiting")
            return False
        
        self.setup_signal_handlers()
        
        # Start API server
        if not self.start_api_server():
            logger.error("❌ Failed to start API server")
            return False
        
        # Start bridge
        try:
            asyncio.run(self.start_bridge())
            return True
        except KeyboardInterrupt:
            logger.info("🛑 System stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ System failed: {e}")
            return False
    
    def shutdown(self):
        """Shutdown all components"""
        logger.info("🛑 Shutting down MCP-Agent Bridge...")
        
        # Stop bridge
        if self.bridge:
            self.bridge.running = False
        
        # Stop API server
        if self.api_process:
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=10)
                logger.info("✅ API server stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ API server didn't stop gracefully, forcing...")
                self.api_process.kill()
            except Exception as e:
                logger.error(f"❌ Error stopping API server: {e}")
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("👋 Shutdown complete")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Start MCP-Agent Connection Bridge")
    parser.add_argument("--bridge-only", action="store_true", 
                       help="Start only the bridge (no API server)")
    parser.add_argument("--api-only", action="store_true", 
                       help="Start only the API server")
    parser.add_argument("--check-only", action="store_true", 
                       help="Only check prerequisites and exit")
    
    args = parser.parse_args()
    
    starter = BridgeStarter()
    
    if args.check_only:
        if starter.check_prerequisites():
            logger.info("✅ All prerequisites are met")
            sys.exit(0)
        else:
            logger.error("❌ Prerequisites not met")
            sys.exit(1)
    
    success = False
    
    try:
        if args.bridge_only:
            success = starter.run_bridge_only()
        elif args.api_only:
            success = starter.run_api_only()
        else:
            success = starter.run_full_system()
    
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        success = True
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        success = False
    finally:
        starter.shutdown()
    
    if success:
        logger.info("🏁 MCP-Agent Bridge exited successfully")
        sys.exit(0)
    else:
        logger.error("💥 MCP-Agent Bridge exited with errors")
        sys.exit(1)

if __name__ == "__main__":
    main()
