#!/usr/bin/env python3
"""
Main system runner for flash loan arbitrage system.
"""

import asyncio
import logging
from typing import Optional

from src.flash_loan.core.dex_integration_singleton import dex_integration
from src.flash_loan.agents.auto_executor import AutoExecutor

logger = logging.getLogger(__name__)

class FlashLoanSystem:
    """Main system orchestrator."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.auto_executor: Optional[AutoExecutor] = None
        self.dex_integration = dex_integration
        
    async def initialize(self):
        """Initialize the system components."""
        try:
            # Initialize DEX integration (not awaitable, just call it)
            if hasattr(self.dex_integration, 'initialize'):
                init_result: str = self.dex_integration.initialize()
                if asyncio.iscoroutine(init_result):
                    await init_result
            
            # Initialize auto executor
            self.auto_executor = AutoExecutor()
            if hasattr(self.auto_executor, 'initialize'):
                await self.auto_executor.initialize()
            
            self.logger.info("System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing system: {e}")
            return False
    
    async def start(self):
        """Start the system."""
        try:
            if not await self.initialize():
                return False
                
            self.logger.info("Flash loan system started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting system: {e}")
            return False

# Global system instance
flash_loan_system = FlashLoanSystem()

