#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the LangChain Master Orchestrator
Flash Loan Arbitrage System

This script initializes and runs the complete LangChain integration system
with all components coordinated for flash loan arbitrage operations.
"""

from pathlib import Path
from typing import Dict, Any
import asyncio
import logging
import os
import signal
import sys

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.langchain_integration.langchain_master_orchestrator import LangChainMasterOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/langchain_orchestrator.log', mode='a')


logger = logging.getLogger(__name__)


class LangChainSystemManager:
    """
    System manager for the complete LangChain integration system.
    Handles initialization, coordination, and graceful shutdown.
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.orchestrator: LangChainMasterOrchestrator = None
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Load configuration
        self._load_configuration()
        
        logger.info("[INIT] LangChain System Manager initialized")
    
    def _load_configuration(self):
        """Load system configuration from YAML file"""
        try:
            config_path = Path(project_root) / "config" / "langchain_config.yaml"
            
            if not config_path.exists():
                logger.error(f"[ERROR] Configuration file not found: {config_path}")
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # Override with environment variables
            self._apply_environment_overrides()
            
            logger.info(f"[OK] Configuration loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load configuration: {e}")
            raise
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides"""
        env_mappings = {
            'REDIS_URL': ['redis', 'url'],
            'POSTGRES_PASSWORD': ['postgres', 'password'],
            'OPENAI_API_KEY': ['autogen', 'openai_api_key'],
            'AUTOGEN_URL': ['autogen', 'url'],
            'LOG_LEVEL': ['logging', 'level'],
            'DEBUG': ['system', 'debug']

        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Navigate to the config path and set value
                current = self.config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[config_path[-1]] = env_value
                logger.info(f"[CONFIG] Override {'.'.join(config_path)} from environment")
    
    async def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("[INIT] Starting LangChain Master Orchestrator System...")
            
            # Create orchestrator with configuration
            self.orchestrator = LangChainMasterOrchestrator(self.config)
            
            # Initialize the orchestrator (this will initialize all sub-components)
            await self.orchestrator.initialize()
            
            logger.info("[OK] LangChain System fully initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] System initialization failed: {e}")
            raise
    
    async def start(self):
        """Start the system and run the main loop"""
        try:
            self.running = True
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            logger.info("[START] LangChain Master Orchestrator System is running")
            logger.info("[INFO] System is ready to handle arbitrage requests")
            
            # Print system status
            await self._print_system_status()
            
            # Main system loop
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"[ERROR] System runtime error: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def _main_loop(self):
        """Main system loop - keeps the system running"""
        try:
            while self.running:
                # Wait for shutdown signal or periodic tasks
                try:
                    await asyncio.wait_for(self.shutdown_event.wait(), timeout=60.0)
                    break  # Shutdown signal received
                except asyncio.TimeoutError:
                    # Periodic maintenance
                    await self._periodic_maintenance()
                
        except Exception as e:
            logger.error(f"[ERROR] Main loop error: {e}")
            self.running = False
    
    async def _periodic_maintenance(self):
        """Perform periodic maintenance tasks"""
        try:
            # Get system status
            if self.orchestrator:
                status = await self.orchestrator.get_system_status()
                
                # Log key metrics
                metrics = status.get("performance_metrics", {})
                logger.info(f"[METRICS] Active tasks: {status.get('active_tasks', 0)}, "
                          f"Success rate: {metrics.get('successful_tasks', 0)}/{metrics.get('total_tasks', 0)}"
                
                # Check for unhealthy components
                component_status = status.get("component_status", {})
                for component, health in component_status.items():
                    if isinstance(health, dict) and health.get("overall_status") != "healthy":
                        logger.warning(f"[WARNING] Component {component} is {health.get('overall_status')}")
                
        except Exception as e:
            logger.warning(f"[WARNING] Periodic maintenance error: {e}")
    
    async def _print_system_status(self):
        """Print comprehensive system status"""
        try:
            if self.orchestrator:
                status = await self.orchestrator.get_system_status()
                
                print("\n" + "="*80)
                print("LANGCHAIN MASTER ORCHESTRATOR - SYSTEM STATUS")
                print("="*80)
                print(f"Status: {status.get('orchestrator_status', 'unknown')}")
                print(f"Uptime: {status.get('uptime_seconds', 0):.1f} seconds")
                print(f"Active Tasks: {status.get('active_tasks', 0)}")
                
                # Component status
                component_status = status.get("component_status", {})
                print("\nComponent Status:")
                for component, health in component_status.items():
                    if isinstance(health, dict):
                        print(f"  {component}: {health.get('overall_status', 'unknown')}")
                    else:
                        print(f"  {component}: {health}")
                
                # Performance metrics
                metrics = status.get("performance_metrics", {})
                if metrics:
                    print("\nPerformance Metrics:")
                    print(f"  Total Tasks: {metrics.get('total_tasks', 0)}")
                    print(f"  Successful: {metrics.get('successful_tasks', 0)}")
                    print(f"  Failed: {metrics.get('failed_tasks', 0)}")
                    print(f"  Avg Response Time: {metrics.get('avg_response_time', 0):.3f}s")
                
                print("="*80)
                print("System ready for arbitrage operations")
                print("="*80 + "\n")
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to print system status: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"[SIGNAL] Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self._trigger_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)
    
    async def _trigger_shutdown(self):
        """Trigger graceful shutdown"""
        self.running = False
        self.shutdown_event.set()
    
    async def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("[SHUTDOWN] Initiating system shutdown...")
        
        try:
            if self.orchestrator:
                await self.orchestrator.shutdown()
            
            logger.info("[SHUTDOWN] LangChain System shutdown complete")
            
        except Exception as e:
            logger.error(f"[ERROR] Shutdown error: {e}")
    
    async def execute_arbitrage_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an arbitrage opportunity through the orchestrator
        
        Args:
            opportunity: Arbitrage opportunity data
            
        Returns:
            Execution result
        """
        if not self.orchestrator:
            raise RuntimeError("System not initialized")
        
        return await self.orchestrator.execute_arbitrage_workflow(opportunity)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        if not self.orchestrator:
            return {"status": "not_initialized"}
        
        return await self.orchestrator.get_system_status()


async def main():
    """Main entry point"""
    system_manager = None
    
    try:
        # Create and initialize system manager
        system_manager = LangChainSystemManager()
        
        # Initialize all components
        await system_manager.initialize()
        
        # Start the system
        await system_manager.start()
        
    except KeyboardInterrupt:
        logger.info("[INTERRUPT] Keyboard interrupt received")
    except Exception as e:
        logger.error(f"[ERROR] System error: {e}")
        return 1
    finally:
        if system_manager:
            await system_manager.shutdown()
    
    return 0


def run_system():
    """Synchronous entry point for running the system"""
    try:
        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Run the async main function
        return asyncio.run(main())
        
    except Exception as e:
        logger.error(f"[FATAL] Failed to start system: {e}")
        return 1


if __name__ == "__main__":
    """Script entry point"""
    exit_code = run_system()
    sys.exit(exit_code)