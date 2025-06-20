#!/usr/bin/env python3
"""
Docker Coordination System Entrypoint
Main orchestrator for MCP servers and AI agents
"""

import asyncio
import os
import sys
import logging
import signal
from pathlib import Path
from typing import Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from docker_coordination_system import DockerCoordinationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/coordination.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

class CoordinationEntrypoint:
    def __init__(self):
        self.coordination_system: Optional[DockerCoordinationSystem] = None
        self.shutdown_event = asyncio.Event()
        
    async def initialize(self) -> bool:
        """Initialize the coordination system"""
        try:
            # Ensure log directory exists
            os.makedirs('/app/logs', exist_ok=True)
            
            # Initialize coordination system
            self.coordination_system = DockerCoordinationSystem()
            
            logger.info("Docker Coordination System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize coordination system: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the coordination system"""
        try:
            if not self.coordination_system:
                logger.error("Coordination system not initialized")
                return False
                
            # Start the coordination system
            await self.coordination_system.run_coordination_system()
            logger.info("Docker Coordination System started")
            
            return True
            
        except Exception as e:
            logger.error(f"Error running coordination system: {e}")
            return False
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down coordination system...")
        self.shutdown_event.set()
        
        if self.coordination_system:
            await self.coordination_system.cleanup()
            
        logger.info("Coordination system shutdown complete")
    
    def handle_signal(self, signum: int, frame: Any):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.shutdown())

async def main():
    """Main entrypoint function"""
    entrypoint = CoordinationEntrypoint()
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, entrypoint.handle_signal)
    signal.signal(signal.SIGINT, entrypoint.handle_signal)
    
    try:
        # Initialize system
        if not await entrypoint.initialize():
            logger.error("Failed to initialize, exiting...")
            sys.exit(1)
        
        # Start system
        logger.info("Starting Docker Coordination System...")
        success = await entrypoint.start()
        
        if not success:
            logger.error("System failed to start properly")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await entrypoint.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
