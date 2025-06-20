#!/usr/bin/env python3
"""
Comprehensive Monitoring Script for Flash Loan Arbitrage System
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3


This script monitors the flash loan arbitrage system and restarts components if needed.
It also provides detailed status information and can be run as a standalone process.
"""

import os
import sys
import time
import json
import asyncio
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Union
# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/system_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("system_monitor")

# Ensure we're in the project root directory
project_root = Path(__file__).resolve().parent
os.chdir(project_root)

# Add the project root to the Python path
sys.path.append(str(project_root))

class SystemMonitor:
    """Comprehensive system monitor for flash loan arbitrage system"""

    def __init__(self):
        """Initialize system monitor"""
        self.processes = {}
        self.last_check = {}
        self.status_history = []
        self.max_history = 100
        self.check_interval = 60  # seconds
        self.restart_attempts = {}
        self.max_restart_attempts = 3
        self.restart_cooldown = 300  # seconds
        self.components = [
            "dex_integration",
            "arbitrage_strategy",
            "auto_executor",
            "transaction_executor",
            "workflow_manager",
            "message_bus"
        ]

    async def initialize(self):
        """Initialize the system monitor"""
        try:
            # Import components with proper error handling
            try:
                from src.flash_loan.core import dex_integration_singleton as dex_integration
                self.dex_integration = dex_integration
            except ImportError:
                logger.warning("DEX integration module not found, skipping DEX integration checks")
                self.dex_integration = None

            try:
                from src.flash_loan.core.arbitrage_strategy import arbitrage_strategy
                self.arbitrage_strategy = arbitrage_strategy
            except ImportError:
                logger.warning("Arbitrage strategy module not found, skipping arbitrage strategy checks")
                self.arbitrage_strategy = None

            try:
                from src.flash_loan.agents.auto_executor import auto_executor
                self.auto_executor = auto_executor
            except ImportError:
                logger.warning("Auto executor module not found, skipping auto executor checks")
                self.auto_executor = None

            try:
                from src.flash_loan.core.transaction_executor import transaction_executor
                self.transaction_executor = transaction_executor
            except ImportError:
                logger.warning("Transaction executor module not found, skipping transaction executor checks")
                self.transaction_executor = None

            # Check if message_bus module exists
            try:
                from src.flash_loan.core.message_bus import message_bus
                self.message_bus = message_bus
                self.has_message_bus = True
            except ImportError:
                logger.warning("Message bus module not found, skipping message bus checks")
                self.has_message_bus = False
                self.message_bus = None

            # Check if workflow module exists
            try:
                from src.flash_loan.core.workflow import workflow_manager
                self.workflow_manager = workflow_manager
                self.has_workflow = True
            except ImportError:
                logger.warning("Workflow module not found, skipping workflow checks")
                self.has_workflow = False
                self.workflow_manager = None

            # Components are already stored in the try/except blocks above

            # Initialize last check times
            for component in self.components:
                self.last_check[component] = 0
                self.restart_attempts[component] = 0

            logger.info("System monitor initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing system monitor: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def check_system_status(self) -> Dict[str, Any]:
        """Check the status of all system components"""
        try:
            status = {
                "timestamp": time.time(),
                "components": {},
                "processes": {},
                "opportunities": [],
                "executions": [],
                "overall_status": "unknown"
            }

            # Check DEX integration
            dex_status = await self._check_dex_integration()
            status["components"]["dex_integration"] = dex_status

            # Check arbitrage strategy
            strategy_status = await self._check_arbitrage_strategy()
            status["components"]["arbitrage_strategy"] = strategy_status

            # Check auto executor
            executor_status = await self._check_auto_executor()
            status["components"]["auto_executor"] = executor_status

            # Check transaction executor
            tx_status = await self._check_transaction_executor()
            status["components"]["transaction_executor"] = tx_status

            # Check workflow manager
            workflow_status = await self._check_workflow_manager()
            status["components"]["workflow_manager"] = workflow_status

            # Check message bus
            message_bus_status = await self._check_message_bus()
            status["components"]["message_bus"] = message_bus_status

            # Check running processes
            status["processes"] = self._check_processes()

            # Check recent opportunities
            status["opportunities"] = await self._check_recent_opportunities()

            # Check recent executions
            status["executions"] = await self._check_recent_executions()

            # Determine overall status
            component_statuses = [
                comp.get("status", "unknown")
                for comp in status["components"].values()
            ]

            if all(s == "ok" for s in component_statuses):
                status["overall_status"] = "ok"
            elif any(s == "error" for s in component_statuses):
                status["overall_status"] = "error"
            elif any(s == "warning" for s in component_statuses):
                status["overall_status"] = "warning"
            else:
                status["overall_status"] = "unknown"

            # Add to history
            self.status_history.append(status)
            if len(self.status_history) > self.max_history:
                self.status_history = self.status_history[-self.max_history:]

            return status
        except Exception as e:
            logger.error(f"Error checking system status: {e}")
            import traceback
            traceback.print_exc()
            return {
                "timestamp": time.time(),
                "error": str(e),
                "overall_status": "error"
            }

    async def _check_dex_integration(self) -> Dict[str, Any]:
        """Check DEX integration status"""
        try:
            self.last_check["dex_integration"] = time.time()

            status = {
                "initialized": getattr(self.dex_integration, 'initialized', False),
                "connected": False,
                "status": "unknown",
                "details": {}
            }

            # Check if initialized
            if not status["initialized"]:
                status["status"] = "error"
                status["message"] = "DEX integration not initialized"
                return status

            # Check Web3 connection
            if hasattr(self.dex_integration, 'w3'):
                w3_instance = getattr(self.dex_integration, 'w3', None)
                if w3_instance:
                    from core.web3_utils import is_connected
                    if is_connected(w3_instance.provider):
                        status["connected"] = True
                        status["details"]["chain_id"] = w3_instance.eth.chain_id
                        status["details"]["block_number"] = w3_instance.eth.block_number
                        status["details"]["provider"] = str(w3_instance.provider)
                        status["status"] = "ok"
                    else:
                        status["connected"] = False
                        status["status"] = "error"
                        status["message"] = "Web3 not connected"
            else:
                status["status"] = "error"
                status["message"] = "Web3 instance is None"

            return status
        except Exception as e:
            logger.error(f"Error checking DEX integration: {e}")
            return {
                "initialized": False,
                "connected": False,
                "status": "error",
                "message": str(e)
            }

    async def _check_arbitrage_strategy(self) -> Dict[str, Any]:
        """Check arbitrage strategy status"""
        try:
            self.last_check["arbitrage_strategy"] = time.time()

            status = {
                "initialized": getattr(self.arbitrage_strategy, 'initialized', False),
                "status": "unknown",
                "details": {}
            }

            # Check if initialized
            if not status["initialized"]:
                status["status"] = "error"
                status["message"] = "Arbitrage strategy not initialized"
                return status

            # Check if can scan for opportunities
            if hasattr(self.arbitrage_strategy, 'scan_for_opportunities'):
                status["details"]["can_scan"] = True
                status["status"] = "ok"
            else:
                status["details"]["can_scan"] = False
                status["status"] = "warning"
                status["message"] = "Arbitrage strategy cannot scan for opportunities"

            return status
        except Exception as e:
            logger.error(f"Error checking arbitrage strategy: {e}")
            return {
                "initialized": False,
                "status": "error",
                "message": str(e)
            }

    async def _check_auto_executor(self) -> Dict[str, Any]:
        """Check auto executor status"""
        try:
            self.last_check["auto_executor"] = time.time()

            # Create a default status dictionary
            status_dict = {
                "enabled": False,
                "running": False,
                "status": "unknown",
                "details": {}
            }

            # Check if auto_executor exists and has the necessary attributes
            if self.auto_executor is not None:
                # Check if auto_executor has get_status method
                if hasattr(self.auto_executor, 'get_status') and callable(getattr(self.auto_executor, 'get_status')):
                    # Get auto executor status from the instance
                    try:
                        executor_status = self.auto_executor.get_status()
                        # Copy values from executor_status to our status_dict
                        if isinstance(executor_status, dict):
                            status_dict.update(executor_status)
                        else:
                            # If it's not a dict, try to extract common attributes
                            status_dict["enabled"] = getattr(executor_status, "enabled", False)
                            status_dict["running"] = getattr(executor_status, "running", False)
                    except Exception as status_error:
                        logger.error(f"Error getting auto executor status: {status_error}")
                else:
                    # Fallback if get_status method doesn't exist
                    config = getattr(self.auto_executor, 'config', {})
                    if isinstance(config, dict):
                        status_dict["enabled"] = config.get("auto_execute", False)
                    else:
                        status_dict["enabled"] = getattr(config, "auto_execute", False)
                    status_dict["running"] = True  # Assume it's running if we can access it

            # Determine status based on enabled and running flags
            if not status_dict.get("enabled", False):
                status_dict["status"] = "warning"
                status_dict["message"] = "Auto executor is disabled"
            elif not status_dict.get("running", False):
                status_dict["status"] = "error"
                status_dict["message"] = "Auto executor is not running"
            else:
                status_dict["status"] = "ok"

            return status_dict
        except Exception as e:
            logger.error(f"Error checking auto executor: {e}")
            return {
                "enabled": False,
                "running": False,
                "status": "error",
                "message": str(e)
            }

    async def _check_transaction_executor(self) -> Dict[str, Any]:
        """Check transaction executor status"""
        try:
            self.last_check["transaction_executor"] = time.time()

            status = {
                "initialized": getattr(self.transaction_executor, '_initialized', False),
                "status": "unknown",
                "details": {}
            }

            # Check if initialized
            if not status["initialized"]:
                status["status"] = "error"
                status["message"] = "Transaction executor not initialized"
                return status

            # Check Web3 connection
            if hasattr(self.transaction_executor, 'w3'):
                w3_instance = getattr(self.transaction_executor, 'w3', None)
                if w3_instance:
                    from core.web3_utils import is_connected
                    if is_connected(w3_instance.provider):
                        status["details"]["connected"] = True
                        status["details"]["provider"] = str(w3_instance.provider)
                        status["status"] = "ok"
                    else:
                        status["details"]["connected"] = False
                        status["status"] = "error"
                        status["message"] = "Web3 not connected"
                else:
                    status["details"]["connected"] = False
                    status["status"] = "error"
                    status["message"] = "Web3 instance is None"
            else:
                status["details"]["connected"] = False
                status["status"] = "error"
                status["message"] = "Web3 not available"

            return status
        except Exception as e:
            logger.error(f"Error checking transaction executor: {e}")
            return {
                "initialized": False,
                "status": "error",
                "message": str(e)
            }

    async def _check_workflow_manager(self) -> Dict[str, Any]:
        """Check workflow manager status"""
        try:
            self.last_check["workflow_manager"] = time.time()

            # Skip if workflow manager is not available
            if not self.has_workflow or self.workflow_manager is None:
                return {
                    "available": False,
                    "status": "warning",
                    "message": "Workflow manager not available",
                    "details": {}
                }

            status = {
                "available": True,
                "running": getattr(self.workflow_manager, 'running', False),
                "status": "unknown",
                "details": {}
            }

            # Check if running
            if not status["running"]:
                status["status"] = "error"
                status["message"] = "Workflow manager not running"
                return status

            # Check agents
            if hasattr(self.workflow_manager, 'agents'):
                status["details"]["agent_count"] = len(self.workflow_manager.agents)
                status["status"] = "ok"
            else:
                status["details"]["agent_count"] = 0
                status["status"] = "warning"
                status["message"] = "No agents found in workflow manager"

            return status
        except Exception as e:
            logger.error(f"Error checking workflow manager: {e}")
            return {
                "available": True,
                "running": False,
                "status": "error",
                "message": str(e)
            }

    async def _check_message_bus(self) -> Dict[str, Any]:
        """Check message bus status"""
        try:
            self.last_check["message_bus"] = time.time()

            # Skip if message bus is not available
            if not self.has_message_bus or self.message_bus is None:
                return {
                    "available": False,
                    "status": "warning",
                    "message": "Message bus not available",
                    "details": {}
                }

            status = {
                "available": True,
                "initialized": getattr(self.message_bus, 'initialized', False),
                "status": "unknown",
                "details": {}
            }

            # Check if initialized
            if not status["initialized"]:
                status["status"] = "error"
                status["message"] = "Message bus not initialized"
                return status

            # Check if running
            if hasattr(self.message_bus, 'running') and getattr(self.message_bus, 'running', False):
                status["details"]["running"] = True
                status["status"] = "ok"
            else:
                status["details"]["running"] = False
                status["status"] = "error"
                status["message"] = "Message bus not running"

            return status
        except Exception as e:
            logger.error(f"Error checking message bus: {e}")
            return {
                "available": True,
                "initialized": False,
                "status": "error",
                "message": str(e)
            }

    def _check_processes(self) -> Dict[str, Any]:
        """Check running processes"""
        try:
            processes = {}

            # Check Python processes
            python_processes = self._get_python_processes()
            processes["python"] = python_processes

            return processes
        except Exception as e:
            logger.error(f"Error checking processes: {e}")
            return {"error": str(e)}

    def _get_python_processes(self) -> List[Dict[str, Any]]:
        """Get running Python processes"""
        try:
            result: str = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                capture_output=True,
                text=True
            )

            processes = []
            lines = result.stdout.strip().split("\n")[1:]  # Skip header

            for line in lines:
                if not line:
                    continue

                parts = line.strip('"').split('","')
                if len(parts) >= 5:
                    processes.append({
                        "name": parts[0],
                        "pid": int(parts[1]),
                        "session": parts[2],
                        "memory": parts[4].strip('"')
                    })

            return processes
        except Exception as e:
            logger.error(f"Error getting Python processes: {e}")
            return []

    async def _check_recent_opportunities(self) -> List[Dict[str, Any]]:
        """Check recent arbitrage opportunities"""
        try:
            # Check if arbitrage_strategy exists
            if self.arbitrage_strategy is None:
                logger.warning("Arbitrage strategy is not available")
                return []

            # Check if it has the get_recent_opportunities method
            if hasattr(self.arbitrage_strategy, 'get_recent_opportunities'):
                # Get the method
                get_opportunities = getattr(self.arbitrage_strategy, 'get_recent_opportunities')

                # Check if it's callable
                if callable(get_opportunities):
                    # Call the method
                    opportunities = get_opportunities()

                    # Ensure we return a list
                    if opportunities is None:
                        return []
                    elif isinstance(opportunities, list):
                        return opportunities
                    else:
                        logger.warning(f"get_recent_opportunities returned non-list: {type(opportunities)}")
                        return []
                else:
                    logger.warning("get_recent_opportunities is not callable")
                    return []
            else:
                logger.warning("Arbitrage strategy does not have 'get_recent_opportunities' method.")
                return []
        except Exception as e:
            logger.error(f"Error checking recent opportunities: {e}")
            return []

    async def _check_recent_executions(self) -> List[Dict[str, Any]]:
        """Check recent executions"""
        try:
            from core.database import db

            # Check if get_recent_executions method exists
            if hasattr(db, 'get_recent_executions'):
                executions = await db.get_recent_executions(limit=5)
                return executions
            else:
                # Try to get executions from the database directly
                try:
                    # Check if we can access the executions table
                    if hasattr(db, 'conn'):
                        cursor = await db.conn.execute("SELECT * FROM executions ORDER BY timestamp DESC LIMIT 5")
                        rows = await cursor.fetchall()
                        executions = []
                        for row in rows:
                            executions.append(dict(row))
                        return executions
                except Exception as inner_e:
                    logger.error(f"Error querying executions table: {inner_e}")

                # Check execution log files as fallback
                execution_logs = list(Path("logs/debug").glob("execution_*.json"))
                executions = []

                for log_file in sorted(execution_logs, key=lambda p: Any: p.stat().st_mtime, reverse=True)[:5]:
                    try:
                        with open(log_file, "r") as f:
                            execution_data = json.load(f)
                            executions.append(execution_data)
                    except Exception as file_e:
                        logger.error(f"Error reading execution log file {log_file}: {file_e}")

                return executions
        except Exception as e:
            logger.error(f"Error checking recent executions: {e}")
            return []

    async def restart_component(self, component: str) -> bool:
        """Restart a system component"""
        try:
            # Check if we've exceeded max restart attempts
            current_time = time.time()
            if component in self.restart_attempts:
                if self.restart_attempts[component] >= self.max_restart_attempts:
                    last_attempt = self.last_check.get(component, 0)
                    if current_time - last_attempt < self.restart_cooldown:
                        logger.warning(f"Too many restart attempts for {component}, cooling down")
                        return False
                    else:
                        # Reset counter after cooldown
                        self.restart_attempts[component] = 0

            logger.info(f"Restarting component: {component}")

            if component == "dex_integration":
                # Check if dex_integration exists and has initialize method
                if self.dex_integration is not None and hasattr(self.dex_integration, 'initialize'):
                    try:
                        # Check if it's an async method
                        init_method = getattr(self.dex_integration, 'initialize')
                        if asyncio.iscoroutinefunction(init_method):
                            await init_method()
                        else:
                            init_method()
                        logger.info("DEX integration restarted")
                    except Exception as e:
                        logger.error(f"Error initializing DEX integration: {e}")
                        return False
                else:
                    logger.info("DEX integration restarted (no initialization needed)")

            elif component == "arbitrage_strategy":
                # Check if arbitrage_strategy exists and has initialize method
                if self.arbitrage_strategy is not None and hasattr(self.arbitrage_strategy, 'initialize'):
                    try:
                        # Check if it's an async method
                        init_method = getattr(self.arbitrage_strategy, 'initialize')
                        if asyncio.iscoroutinefunction(init_method):
                            await init_method()
                        else:
                            init_method()
                        logger.info("Arbitrage strategy restarted")
                    except Exception as e:
                        logger.error(f"Error initializing arbitrage strategy: {e}")
                        return False
                else:
                    logger.warning("Arbitrage strategy not available or has no initialize method")
                    return False

            elif component == "auto_executor":
                try:
                    # Import auto_executor directly
                    from core.auto_executor import auto_executor

                    # Enable auto_executor if it has an enable method
                    if hasattr(auto_executor, 'enable') and callable(getattr(auto_executor, 'enable')):
                        getattr(auto_executor, 'enable')()

                    # Start the auto_executor if it has a start method
                    if hasattr(auto_executor, 'start') and callable(getattr(auto_executor, 'start')):
                        # Check if it's an async method
                        start_method = getattr(auto_executor, 'start')
                        if asyncio.iscoroutinefunction(start_method):
                            await start_method()
                        else:
                            start_method()

                    logger.info("Auto executor restarted")
                except Exception as auto_ex:
                    logger.error(f"Error restarting auto executor: {auto_ex}")
                    return False

            elif component == "transaction_executor":
                # Check if transaction_executor exists
                if self.transaction_executor is None:
                    logger.warning("Transaction executor not available")
                    return False

                # Initialize transaction executor if it has initialize method
                if hasattr(self.transaction_executor, 'initialize'):
                    try:
                        # Get the initialize method
                        init_method = getattr(self.transaction_executor, 'initialize')

                        # Check if it's an async method
                        if asyncio.iscoroutinefunction(init_method):
                            await init_method()
                        else:
                            init_method()

                        logger.info("Transaction executor restarted")
                    except Exception as e:
                        logger.error(f"Error initializing transaction executor: {e}")
                        return False
                else:
                    logger.info("Transaction executor restarted (no initialization needed)")

            elif component == "workflow_manager":
                if not self.has_workflow or self.workflow_manager is None:
                    logger.warning("Workflow manager not available, skipping restart")
                    return False

                # Check if workflow_manager has start method
                if hasattr(self.workflow_manager, 'start'):
                    try:
                        # Get the start method
                        start_method = getattr(self.workflow_manager, 'start')

                        # Check if it's an async method
                        if asyncio.iscoroutinefunction(start_method):
                            await start_method()
                        else:
                            start_method()

                        logger.info("Workflow manager restarted")
                    except Exception as e:
                        logger.error(f"Error starting workflow manager: {e}")
                        return False
                else:
                    logger.warning("Workflow manager has no start method")
                    return False

            elif component == "message_bus":
                if not self.has_message_bus or self.message_bus is None:
                    logger.warning("Message bus not available, skipping restart")
                    return False

                # Check if message_bus has initialize method
                if hasattr(self.message_bus, 'initialize'):
                    try:
                        # Get the initialize method
                        init_method = getattr(self.message_bus, 'initialize')

                        # Check if it's an async method
                        if asyncio.iscoroutinefunction(init_method):
                            await init_method()
                        else:
                            init_method()

                        logger.info("Message bus restarted")
                    except Exception as e:
                        logger.error(f"Error initializing message bus: {e}")
                        return False
                else:
                    logger.warning("Message bus has no initialize method")
                    return False

            else:
                logger.warning(f"Unknown component: {component}")
                return False

            # Update restart attempts
            self.restart_attempts[component] += 1
            self.last_check[component] = current_time

            return True
        except Exception as e:
            logger.error(f"Error restarting component {component}: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def restart_system(self) -> bool:
        """Restart the entire system"""
        try:
            logger.info("Restarting the entire system")

            # Stop all components
            if self.has_workflow and self.workflow_manager is not None:
                try:
                    logger.info("Stopping workflow manager...")
                    # Check if workflow_manager has stop method
                    if hasattr(self.workflow_manager, 'stop'):
                        # Get the stop method
                        stop_method = getattr(self.workflow_manager, 'stop')

                        # Check if it's an async method
                        if asyncio.iscoroutinefunction(stop_method):
                            await stop_method()
                        else:
                            stop_method()
                    else:
                        logger.warning("Workflow manager does not have a 'stop' method.")
                except Exception as e:
                    logger.error(f"Error stopping workflow manager: {e}")
            else:
                logger.info("Workflow manager not available, skipping stop")

            if self.has_message_bus and self.message_bus is not None:
                try:
                    logger.info("Stopping message bus...")
                    # Check if message_bus has shutdown method
                    if hasattr(self.message_bus, 'shutdown') and callable(getattr(self.message_bus, 'shutdown')):
                        # Get the shutdown method
                        shutdown_method = getattr(self.message_bus, 'shutdown')

                        # Check if it's an async method
                        if asyncio.iscoroutinefunction(shutdown_method):
                            await shutdown_method()
                        else:
                            shutdown_method()
                    else:
                        logger.warning("Message bus does not have a 'shutdown' method.")
                except Exception as e:
                    logger.error(f"Error stopping message bus: {e}")
            else:
                logger.info("Message bus not available, skipping shutdown")

            # Restart all components
            components_to_restart = [
                "dex_integration",
                "arbitrage_strategy",
                "transaction_executor",
                "message_bus",
                "workflow_manager",
                "auto_executor"
            ]

            for component in components_to_restart:
                await self.restart_component(component)

            logger.info("System restart complete")
            return True
        except Exception as e:
            logger.error(f"Error restarting system: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def monitor_loop(self):
        """Main monitoring loop"""
        try:
            logger.info("Starting system monitoring loop")

            while True:
                try:
                    # Check system status
                    status = await self.check_system_status()

                    # Log status summary
                    logger.info(f"System status: {status['overall_status']}")

                    # Check if any components need to be restarted
                    for component, comp_status in status["components"].items():
                        if comp_status["status"] == "error":
                            logger.warning(f"Component {component} has errors, attempting to restart")
                            await self.restart_component(component)

                    # Save status to file
                    self._save_status_to_file(status)

                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    import traceback
                    traceback.print_exc()

                # Wait for next check
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Monitoring loop failed: {e}")
            import traceback
            traceback.print_exc()

    def _save_status_to_file(self, status: Dict[str, Any]):
        """Save status to file"""
        try:
            # Create data directory if it doesn't exist
            data_dir = Path("data/monitoring")
            data_dir.mkdir(parents=True, exist_ok=True)

            # Save current status
            with open(data_dir / "current_status.json", "w") as f:
                json.dump(status, f, indent=2, default=str)

            # Save status history
            with open(data_dir / "status_history.json", "w") as f:
                json.dump(self.status_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving status to file: {e}")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Flash Loan System Monitor")
    parser.add_argument("--check", action="store_true", help="Check system status and exit")
    parser.add_argument("--restart", action="store_true", help="Restart the entire system")
    parser.add_argument("--restart-component", type=str, help="Restart a specific component")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring loop")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds")
    args = parser.parse_args()

    # Create and initialize monitor
    monitor = SystemMonitor()
    if not await monitor.initialize():
        logger.error("Failed to initialize system monitor")
        return 1

    # Set monitoring interval
    monitor.check_interval = args.interval

    if args.check:
        # Check system status
        status = await monitor.check_system_status()
        print(json.dumps(status, indent=2, default=str))
    elif args.restart:
        # Restart the entire system
        success = await monitor.restart_system()
        if success:
            logger.info("System restart successful")
        else:
            logger.error("System restart failed")
    elif args.restart_component:
        # Restart a specific component
        component = args.restart_component
        success = await monitor.restart_component(component)
        if success:
            logger.info(f"Component {component} restart successful")
        else:
            logger.error(f"Component {component} restart failed")
    elif args.monitor:
        # Start monitoring loop
        await monitor.monitor_loop()
    else:
        # Default: check status and start monitoring
        status = await monitor.check_system_status()
        print(json.dumps(status, indent=2, default=str))
        await monitor.monitor_loop()

    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
