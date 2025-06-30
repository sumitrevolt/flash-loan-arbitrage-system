# -*- coding: utf-8 -*-
"""
AutoGen Integration Main Module
Flash Loan Arbitrage Multi-Agent System

This module provides the main entry point for the AutoGen integration system,
allowing standalone operation or integration with the LangChain orchestrator.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import json
import logging
import os
import signal
import sys

import yaml

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .autogen_coordinator import AutoGenCoordinator
from .specialized_agents import FlashLoanAgentFactory
from .conversation_orchestrator import ConversationOrchestrator
from .decision_engine import ConsensusDecisionEngine
from .mcp_bridge import MCPBridge
from .agent_registry import AgentRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/autogen_integration.log', mode='a')


logger = logging.getLogger(__name__)


class AutoGenSystemManager:
    """
    Main system manager for the AutoGen integration system.
    Provides standalone operation and integration capabilities.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/autogen_config.yaml"
        self.config = self._load_config()
        
        # Core components
        self.coordinator: Optional[AutoGenCoordinator] = None
        self.agent_factory: Optional[FlashLoanAgentFactory] = None
        self.conversation_orchestrator: Optional[ConversationOrchestrator] = None
        self.decision_engine: Optional[ConsensusDecisionEngine] = None
        self.mcp_bridge: Optional[MCPBridge] = None
        self.agent_registry: Optional[AgentRegistry] = None
        
        # System state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            "total_sessions": 0,
            "successful_decisions": 0,
            "failed_decisions": 0,
            "avg_decision_time": 0.0,
            "uptime_seconds": 0

        
        logger.info("[INIT] AutoGen System Manager initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            # Environment variable substitution
            config = self._substitute_env_vars(config)
            
            logger.info(f"[CONFIG] Loaded configuration from {self.config_path}")
            return config
            
        except FileNotFoundError:
            logger.warning(f"[CONFIG] Config file not found: {self.config_path}, using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"[CONFIG] Error loading config: {e}")
            return self._get_default_config()
    
    def _substitute_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute environment variables in configuration"""
        import re
        
        def substitute_value(value):
            if isinstance(value, str):
                # Find ${VAR_NAME} patterns
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for match in matches:
                    env_value = os.getenv(match, "")
                    value = value.replace(f"${{{match}}}", env_value)
                return value
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value
        
        return substitute_value(config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "system": {
                "name": "AutoGen Flash Loan Arbitrage System",
                "version": "1.0.0",
                "environment": "development",
                "debug": True
            },
            "autogen": {
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "temperature": 0.1,
                "timeout": 60
            },
            "agents": {},
            "conversation_management": {
                "decision_algorithms": {
                    "default": "majority_consensus"



    
    async def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("[INIT] Initializing AutoGen system components...")
            
            # Initialize core components
            self.coordinator = AutoGenCoordinator(self.config)
            self.agent_factory = FlashLoanAgentFactory(self.config)
            self.conversation_orchestrator = ConversationOrchestrator(self.config)
            self.decision_engine = ConsensusDecisionEngine(self.config)
            self.mcp_bridge = MCPBridge(self.config)
            self.agent_registry = AgentRegistry(self.config)
            
            # Initialize components
            await self.coordinator.initialize()
            await self.agent_factory.initialize()
            await self.conversation_orchestrator.initialize()
            await self.decision_engine.initialize()
            await self.mcp_bridge.initialize()
            await self.agent_registry.initialize()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("[OK] AutoGen system fully initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] System initialization failed: {e}")
            raise
    
    async def process_arbitrage_opportunity(
        self,
        opportunity_data: Dict[str, Any],
        consensus_algorithm: str = "majority_consensus",
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Process an arbitrage opportunity through the multi-agent system
        
        Args:
            opportunity_data: Arbitrage opportunity details
            consensus_algorithm: Algorithm for reaching consensus
            timeout: Decision timeout in seconds
            
        Returns:
            Decision result with consensus and execution plan
        """
        try:
            if not self.coordinator:
                raise Exception("System not initialized")
            
            start_time = datetime.now()
            
            # Coordinate arbitrage decision
            result = await self.coordinator.coordinate_arbitrage_decision(
                opportunity_data=opportunity_data,
                consensus_algorithm=consensus_algorithm,
                timeout=timeout

            
            # Update statistics
            self.stats["total_sessions"] += 1
            if result.get("status") == "completed":
                self.stats["successful_decisions"] += 1
            else:
                self.stats["failed_decisions"] += 1
            
            # Update average decision time
            decision_time = (datetime.now() - start_time).total_seconds()
            total_decisions = self.stats["total_sessions"]
            current_avg = self.stats["avg_decision_time"]
            self.stats["avg_decision_time"] = (
                (current_avg * (total_decisions - 1) + decision_time) / total_decisions

            
            logger.info(f"[DECISION] Processed arbitrage opportunity in {decision_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to process arbitrage opportunity: {e}")
            self.stats["failed_decisions"] += 1
            return {
                "status": "failed",
                "error": str(e),
                "consensus": {"approved": False, "reason": f"Processing failed: {e}"}

    
    async def process_risk_assessment(
        self,
        trade_data: Dict[str, Any],
        market_context: Dict[str, Any],
        timeout: int = 180
    ) -> Dict[str, Any]:
        """
        Process risk assessment through specialized agents
        
        Args:
            trade_data: Trade parameters for assessment
            market_context: Market context data
            timeout: Assessment timeout in seconds
            
        Returns:
            Risk assessment result
        """
        try:
            if not self.coordinator:
                raise Exception("System not initialized")
            
            result = await self.coordinator.coordinate_risk_assessment(
                trade_data=trade_data,
                market_context=market_context,
                timeout=timeout

            
            logger.info("[RISK] Completed risk assessment")
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Risk assessment failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "risk_assessment": {"risk_level": "high", "reason": f"Assessment failed: {e}"}

    
    async def process_execution_planning(
        self,
        execution_context: Dict[str, Any],
        constraints: Dict[str, Any],
        timeout: int = 240
    ) -> Dict[str, Any]:
        """
        Process execution planning through specialized agents
        
        Args:
            execution_context: Execution context and parameters
            constraints: Execution constraints
            timeout: Planning timeout in seconds
            
        Returns:
            Execution planning result
        """
        try:
            if not self.coordinator:
                raise Exception("System not initialized")
            
            result = await self.coordinator.coordinate_execution_planning(
                execution_context=execution_context,
                constraints=constraints,
                timeout=timeout

            
            logger.info("[EXECUTION] Completed execution planning")
            
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Execution planning failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "execution_plan": {"approved": False, "reason": f"Planning failed: {e}"}

    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            self.stats["uptime_seconds"] = uptime
        
        status = {
            "system_status": "running" if self.is_running else "stopped",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "statistics": self.stats,
            "configuration": {
                "model": self.config.get("autogen", {}).get("model", "unknown"),
                "environment": self.config.get("system", {}).get("environment", "unknown")


        
        # Add component status if available
        if self.coordinator:
            try:
                coordinator_status = await self.coordinator.get_coordinator_status()
                status["coordinator_status"] = coordinator_status
            except Exception as e:
                status["coordinator_status"] = {"error": str(e)}
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            "overall_health": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}

        
        components = [
            ("coordinator", self.coordinator),
            ("agent_factory", self.agent_factory),
            ("conversation_orchestrator", self.conversation_orchestrator),
            ("decision_engine", self.decision_engine),
            ("mcp_bridge", self.mcp_bridge),
            ("agent_registry", self.agent_registry)

        
        for name, component in components:
            try:
                if component and hasattr(component, 'get_status'):
                    component_status = await component.get_status()
                    health_status["components"][name] = {
                        "status": "healthy",
                        "details": component_status

                else:
                    health_status["components"][name] = {
                        "status": "not_initialized" if not component else "no_status_method"

            except Exception as e:
                health_status["components"][name] = {
                    "status": "unhealthy",
                    "error": str(e)

                health_status["overall_health"] = "degraded"
        
        return health_status
    
    async def shutdown(self):
        """Graceful shutdown of the system"""
        logger.info("[SHUTDOWN] Shutting down AutoGen system...")
        
        self.is_running = False
        
        # Shutdown components in reverse order
        components = [
            self.coordinator,
            self.conversation_orchestrator,
            self.decision_engine,
            self.mcp_bridge,
            self.agent_registry,
            self.agent_factory

        
        for component in components:
            if component and hasattr(component, 'shutdown'):
                try:
                    await component.shutdown()
                except Exception as e:
                    logger.warning(f"[SHUTDOWN] Component shutdown error: {e}")
        
        logger.info("[SHUTDOWN] AutoGen system shutdown complete")


async def run_interactive_mode(system_manager: AutoGenSystemManager):
    """Run the system in interactive mode for testing"""
    print("\n" + "="*60)
    print("AutoGen Flash Loan Arbitrage System - Interactive Mode")
    print("="*60)
    
    while system_manager.is_running:
        print("\nAvailable commands:")
        print("1. Process arbitrage opportunity")
        print("2. Risk assessment")
        print("3. Execution planning")
        print("4. System status")
        print("5. Health check")
        print("6. Exit")
        
        try:
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == "1":
                # Mock arbitrage opportunity
                opportunity = {
                    "token_pair": "ETH/USDC",
                    "profit_estimate": 0.05,
                    "dex_route": ["Uniswap", "Sushiswap"],
                    "gas_estimate": 150000,
                    "market_conditions": "favorable",
                    "liquidity_info": {"sufficient": True, "depth": "high"}

                
                print("\nProcessing arbitrage opportunity...")
                result = await system_manager.process_arbitrage_opportunity(opportunity)
                print(f"Result: {json.dumps(result, indent=2)}")
                
            elif choice == "2":
                # Mock risk assessment
                trade_data = {
                    "amount": 1000,
                    "token": "ETH",
                    "strategy": "arbitrage"

                market_context = {
                    "volatility": "medium",
                    "liquidity": "high"

                
                print("\nPerforming risk assessment...")
                result = await system_manager.process_risk_assessment(trade_data, market_context)
                print(f"Result: {json.dumps(result, indent=2)}")
                
            elif choice == "3":
                # Mock execution planning
                execution_context = {
                    "trade_type": "arbitrage",
                    "expected_profit": 0.05

                constraints = {
                    "max_gas": 200000,
                    "max_slippage": 0.01

                
                print("\nPlanning execution...")
                result = await system_manager.process_execution_planning(execution_context, constraints)
                print(f"Result: {json.dumps(result, indent=2)}")
                
            elif choice == "4":
                print("\nGetting system status...")
                status = await system_manager.get_system_status()
                print(f"Status: {json.dumps(status, indent=2)}")
                
            elif choice == "5":
                print("\nPerforming health check...")
                health = await system_manager.health_check()
                print(f"Health: {json.dumps(health, indent=2)}")
                
            elif choice == "6":
                print("\nShutting down...")
                break
                
            else:
                print("Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\n\nReceived interrupt signal. Shutting down...")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    await system_manager.shutdown()


async def main():
    """Main entry point"""
    # Set up signal handling
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        logger.info(f"[SIGNAL] Received signal {signum}")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)
    
    # Create and initialize system
    system_manager = AutoGenSystemManager()
    
    try:
        await system_manager.initialize()
        
        # Check if running in interactive mode
        if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
            await run_interactive_mode(system_manager)
        else:
            # Regular operation mode
            logger.info("[MAIN] AutoGen system running. Press Ctrl+C to shutdown.")
            
            # Display initial status
            status = await system_manager.get_system_status()
            logger.info("[STATUS] System initialized successfully")
            logger.info(f"[STATUS] Model: {status['configuration']['model']}")
            logger.info(f"[STATUS] Environment: {status['configuration']['environment']}")
            
            # Wait for shutdown signal
            await shutdown_event.wait()
            
    except Exception as e:
        logger.error(f"[ERROR] System error: {e}")
        return 1
    finally:
        if system_manager.is_running:
            await system_manager.shutdown()
    
    return 0


if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run the system
    exit_code = asyncio.run(main())
    sys.exit(exit_code)