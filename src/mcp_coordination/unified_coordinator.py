# -*- coding: utf-8 -*-
"""
Unified MCP Coordination System

This is the main coordinator that brings together all MCP coordination components
to provide a unified system for managing LangChain and AutoGen integrations.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import logging
import signal
import sys

from .config_manager import ConfigManager
from .dashboard_server import DashboardServer
from .deployment_manager import DeploymentManager
from .health_monitor import HealthMonitor
from .log_aggregator import LogAggregator, LogLevel, LogSource
from .mcp_server_registry import MCPServerRegistry

logger = logging.getLogger(__name__)


class UnifiedCoordinator:
    """
    Main coordinator for the unified MCP system
    
    This class orchestrates all components:
    - Server discovery and registry
    - Health monitoring and alerting
    - Deployment management
    - Configuration management
    - Log aggregation
    - Web dashboard
    """
    
    def __init__(self, config_file: Optional[str] = None):
        # Load configuration
        self.config = self._load_configuration(config_file)
        
        # Core components
        self.config_manager: Optional[ConfigManager] = None
        self.log_aggregator: Optional[LogAggregator] = None
        self.server_registry: Optional[MCPServerRegistry] = None
        self.health_monitor: Optional[HealthMonitor] = None
        self.deployment_manager: Optional[DeploymentManager] = None
        self.dashboard_server: Optional[DashboardServer] = None
        
        # System state
        self.is_running = False
        self.startup_time: Optional[datetime] = None
        self.shutdown_requested = False
        
        # Integration points
        self.langchain_integration = None
        self.autogen_integration = None
        
        # Background tasks
        self.system_monitor_task: Optional[asyncio.Task] = None
        self.integration_sync_task: Optional[asyncio.Task] = None
        
        # System metrics
        self.metrics = {
            "system_uptime": 0,
            "total_servers_managed": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "health_checks_performed": 0,
            "alerts_generated": 0,
            "configurations_loaded": 0,
            "log_entries_processed": 0

        
        logger.info("[INIT] Unified MCP Coordinator initialized")
    
    def _load_configuration(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load system configuration"""
        try:
            if config_file:
                config_path = Path(config_file)
            else:
                # Try default locations
                default_paths = [
                    "config/mcp_coordination.yaml",
                    "config/unified_config.yaml",
                    "mcp_coordination_config.yaml"

                
                config_path = None
                for path in default_paths:
                    if Path(path).exists():
                        config_path = Path(path)
                        break
            
            if config_path and config_path.exists():
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"[CONFIG] Loaded configuration from {config_path}")
                return config
            else:
                logger.warning("[CONFIG] No configuration file found, using defaults")
                return self._get_default_configuration()
                
        except Exception as e:
            logger.error(f"[ERROR] Failed to load configuration: {e}")
            return self._get_default_configuration()
    
    def _get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "coordination": {
                "system_name": "MCP Unified Coordination System",
                "version": "1.0.0",
                "environment": "development"
            },
            "logging": {
                "level": "INFO",
                "log_dir": "logs",
                "max_log_size": 100 * 1024 * 1024,  # 100MB
                "backup_count": 10,
                "compress_logs": True
            },
            "configuration": {
                "config_dir": "config",
                "watch_configs": True,
                "reload_interval": 300,
                "env_prefix": "MCP_"
            },
            "discovery": {
                "auto_discover": True,
                "scan_interval": 300,
                "discovery_paths": [
                    "mcp_servers/",
                    "src/mcp_coordination/",
                    "src/langchain_integration/",
                    "src/autogen_integration/"

            },
            "health_monitoring": {
                "enabled": True,
                "timeout": 10,
                "max_history": 1000,
                "intervals": {
                    "critical": 10,
                    "integration": 30,
                    "specialized": 60
                },
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "recovery_timeout": 60

            },
            "deployment": {
                "mode": "development",
                "auto_start": True,
                "restart_policy": "on-failure",
                "max_restarts": 3,
                "startup_timeout": 120,
                "shutdown_timeout": 30
            },
            "dashboard": {
                "enabled": True,
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False
            },
            "integrations": {
                "langchain": {
                    "enabled": True,
                    "auto_connect": True
                },
                "autogen": {
                    "enabled": True,
                    "auto_connect": True



    
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("[INIT] Starting Unified MCP Coordinator initialization...")
            self.startup_time = datetime.now()
            
            # 1. Initialize Configuration Manager first
            logger.info("[INIT] Initializing Configuration Manager...")
            self.config_manager = ConfigManager(self.config)
            await self.config_manager.initialize()
            
            # Create default configurations if they don't exist
            await self.config_manager.create_default_configurations()
            
            # 2. Initialize Log Aggregator
            logger.info("[INIT] Initializing Log Aggregator...")
            self.log_aggregator = LogAggregator(self.config)
            await self.log_aggregator.initialize()
            
            # Start logging to aggregator
            await self._setup_logging_integration()
            
            # 3. Initialize Server Registry
            logger.info("[INIT] Initializing MCP Server Registry...")
            self.server_registry = MCPServerRegistry(self.config)
            await self.server_registry.initialize()
            
            # 4. Initialize Health Monitor
            logger.info("[INIT] Initializing Health Monitor...")
            self.health_monitor = HealthMonitor(self.config)
            await self.health_monitor.initialize(self.server_registry)
            
            # 5. Initialize Deployment Manager
            logger.info("[INIT] Initializing Deployment Manager...")
            self.deployment_manager = DeploymentManager(self.config)
            await self.deployment_manager.initialize(self.server_registry, self.health_monitor)
            
            # 6. Initialize Dashboard Server
            if self.config.get("dashboard", {}).get("enabled", True):
                logger.info("[INIT] Initializing Dashboard Server...")
                self.dashboard_server = DashboardServer(self.config)
                await self.dashboard_server.initialize(
                    self.server_registry,
                    self.health_monitor,
                    self.deployment_manager

                await self.dashboard_server.start_server()
            
            # 7. Initialize integrations
            await self._initialize_integrations()
            
            # 8. Start background tasks
            await self._start_background_tasks()
            
            # 9. Setup signal handlers
            self._setup_signal_handlers()
            
            self.is_running = True
            logger.info("[OK] Unified MCP Coordinator initialization completed successfully")
            
            # Log successful initialization
            await self.log_aggregator.log(
                LogLevel.INFO,
                LogSource.SYSTEM,
                "unified_coordinator",
                "System initialization completed successfully",
                metadata={
                    "startup_time": self.startup_time.isoformat(),
                    "components_initialized": [
                        "config_manager", "log_aggregator", "server_registry",
                        "health_monitor", "deployment_manager", "dashboard_server"



            
        except Exception as e:
            logger.error(f"[ERROR] Unified Coordinator initialization failed: {e}")
            await self._cleanup_on_error()
            raise
    
    async def _setup_logging_integration(self):
        """Setup integration with the logging system"""
        class LogAggregatorHandler(logging.Handler):
            def __init__(self, log_aggregator):
                super().__init__()
                self.log_aggregator = log_aggregator
            
            def emit(self, record):
                try:
                    level_map = {
                        logging.DEBUG: LogLevel.DEBUG,
                        logging.INFO: LogLevel.INFO,
                        logging.WARNING: LogLevel.WARNING,
                        logging.ERROR: LogLevel.ERROR,
                        logging.CRITICAL: LogLevel.CRITICAL

                    
                    # Determine source from logger name
                    source_map = {
                        "mcp_server": LogSource.MCP_SERVER,
                        "health_monitor": LogSource.HEALTH_MONITOR,
                        "deployment_manager": LogSource.DEPLOYMENT_MANAGER,
                        "dashboard": LogSource.DASHBOARD,
                        "config_manager": LogSource.CONFIG_MANAGER,
                        "langchain": LogSource.LANGCHAIN,
                        "autogen": LogSource.AUTOGEN

                    
                    source = LogSource.SYSTEM
                    for key, src in source_map.items():
                        if key in record.name:
                            source = src
                            break
                    
                    # Create async task to log
                    asyncio.create_task(
                        self.log_aggregator.log(
                            level_map.get(record.levelno, LogLevel.INFO),
                            source,
                            record.name,
                            record.getMessage(),
                            metadata={
                                "filename": record.filename,
                                "lineno": record.lineno,
                                "funcName": record.funcName
                            },
                            stack_trace=self.format(record) if record.exc_info else None


                except:
                    pass  # Don't break logging if aggregator fails
        
        # Add handler to root logger
        handler = LogAggregatorHandler(self.log_aggregator)
        logging.getLogger().addHandler(handler)
    
    async def _initialize_integrations(self):
        """Initialize LangChain and AutoGen integrations"""
        try:
            integrations_config = self.config.get("integrations", {})
            
            # Initialize LangChain integration
            if integrations_config.get("langchain", {}).get("enabled", True):
                try:
                    from ..langchain_integration.langchain_master_orchestrator import LangChainMasterOrchestrator
                    
                    # Create integration bridge
                    self.langchain_integration = LangChainMasterOrchestrator(
                        await self.config_manager.get_configuration("langchain", {})

                    
                    # Connect to our systems
                    await self._connect_langchain_integration()
                    
                    logger.info("[INTEGRATION] LangChain integration initialized")
                    
                except ImportError:
                    logger.warning("[INTEGRATION] LangChain integration not available")
                except Exception as e:
                    logger.error(f"[INTEGRATION] Failed to initialize LangChain: {e}")
            
            # Initialize AutoGen integration
            if integrations_config.get("autogen", {}).get("enabled", True):
                try:
                    from ..autogen_integration.autogen_coordinator import AutoGenCoordinator
                    
                    # Create integration bridge
                    self.autogen_integration = AutoGenCoordinator(
                        await self.config_manager.get_configuration("autogen", {})

                    
                    # Connect to our systems
                    await self._connect_autogen_integration()
                    
                    logger.info("[INTEGRATION] AutoGen integration initialized")
                    
                except ImportError:
                    logger.warning("[INTEGRATION] AutoGen integration not available")
                except Exception as e:
                    logger.error(f"[INTEGRATION] Failed to initialize AutoGen: {e}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize integrations: {e}")
    
    async def _connect_langchain_integration(self):
        """Connect LangChain integration to coordination system"""
        if not self.langchain_integration:
            return
        
        # Provide access to our systems
        self.langchain_integration.server_registry = self.server_registry
        self.langchain_integration.health_monitor = self.health_monitor
        self.langchain_integration.deployment_manager = self.deployment_manager
        
        # Register for configuration changes
        await self.config_manager.register_change_callback(
            "langchain.*",
            self._on_langchain_config_change

    
    async def _connect_autogen_integration(self):
        """Connect AutoGen integration to coordination system"""
        if not self.autogen_integration:
            return
        
        # Provide access to our systems
        self.autogen_integration.server_registry = self.server_registry
        self.autogen_integration.health_monitor = self.health_monitor
        self.autogen_integration.deployment_manager = self.deployment_manager
        
        # Register for configuration changes
        await self.config_manager.register_change_callback(
            "autogen.*",
            self._on_autogen_config_change

    
    async def _on_langchain_config_change(self, key: str, value: Any):
        """Handle LangChain configuration changes"""
        try:
            if self.langchain_integration:
                await self.langchain_integration.reload_configuration(value)
                logger.info(f"[INTEGRATION] LangChain configuration updated: {key}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to update LangChain configuration: {e}")
    
    async def _on_autogen_config_change(self, key: str, value: Any):
        """Handle AutoGen configuration changes"""
        try:
            if self.autogen_integration:
                await self.autogen_integration.reload_configuration(value)
                logger.info(f"[INTEGRATION] AutoGen configuration updated: {key}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to update AutoGen configuration: {e}")
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        self.system_monitor_task = asyncio.create_task(self._system_monitor_loop())
        self.integration_sync_task = asyncio.create_task(self._integration_sync_loop())
    
    async def _system_monitor_loop(self):
        """Background task for system monitoring"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Monitor every minute
                
                # Update system metrics
                if self.startup_time:
                    self.metrics["system_uptime"] = (datetime.now() - self.startup_time).total_seconds()
                
                # Collect metrics from components
                if self.server_registry:
                    registry_status = await self.server_registry.get_registry_status()
                    self.metrics["total_servers_managed"] = registry_status.get("server_statistics", {}).get("total", 0)
                
                if self.deployment_manager:
                    deployment_status = await self.deployment_manager.get_deployment_status()
                    deployment_stats = deployment_status.get("deployment_stats", {})
                    self.metrics["successful_deployments"] = deployment_stats.get("successful_deployments", 0)
                    self.metrics["failed_deployments"] = deployment_stats.get("failed_deployments", 0)
                
                if self.health_monitor:
                    health_status = await self.health_monitor.get_overall_health_status()
                    monitoring_stats = health_status.get("monitoring_stats", {})
                    self.metrics["health_checks_performed"] = monitoring_stats.get("total_checks", 0)
                    self.metrics["alerts_generated"] = monitoring_stats.get("alerts_generated", 0)
                
                if self.config_manager:
                    config_status = await self.config_manager.get_configuration_status()
                    self.metrics["configurations_loaded"] = config_status.get("total_configurations", 0)
                
                if self.log_aggregator:
                    log_stats = await self.log_aggregator.get_log_statistics()
                    total_stats = log_stats.get("total_statistics", {})
                    self.metrics["log_entries_processed"] = total_stats.get("total_logs", 0)
                
                # Log system status periodically
                if int(self.metrics["system_uptime"]) % 3600 == 0:  # Every hour
                    await self.log_aggregator.log(
                        LogLevel.INFO,
                        LogSource.SYSTEM,
                        "unified_coordinator",
                        "System status report",
                        metadata=self.metrics

                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] System monitor loop failed: {e}")
    
    async def _integration_sync_loop(self):
        """Background task for integration synchronization"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Sync every 5 minutes
                
                # Sync server registry with integrations
                if self.langchain_integration and hasattr(self.langchain_integration, 'sync_server_registry'):
                    await self.langchain_integration.sync_server_registry(self.server_registry)
                
                if self.autogen_integration and hasattr(self.autogen_integration, 'sync_server_registry'):
                    await self.autogen_integration.sync_server_registry(self.server_registry)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Integration sync loop failed: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"[SIGNAL] Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True
            
            # Create shutdown task
            if not self.is_running:
                return
            
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Handle SIGHUP for configuration reload
        if hasattr(signal, 'SIGHUP'):
            def reload_handler(signum, frame):
                logger.info("[SIGNAL] Received SIGHUP, reloading configuration...")
                asyncio.create_task(self.reload_configuration())
            
            signal.signal(signal.SIGHUP, reload_handler)
    
    async def run(self):
        """Main run loop"""
        try:
            if not self.is_running:
                await self.initialize()
            
            logger.info("[RUN] Unified MCP Coordinator is now running")
            
            # Main event loop
            while self.is_running and not self.shutdown_requested:
                await asyncio.sleep(1)
                
                # Check component health
                if not await self._check_component_health():
                    logger.error("[RUN] Critical component failure detected")
                    break
            
        except KeyboardInterrupt:
            logger.info("[RUN] Keyboard interrupt received")
        except Exception as e:
            logger.error(f"[ERROR] Run loop failed: {e}")
        finally:
            if self.is_running:
                await self.shutdown()
    
    async def _check_component_health(self) -> bool:
        """Check health of critical components"""
        try:
            # Check if critical components are still running
            critical_components = [
                ("server_registry", self.server_registry),
                ("health_monitor", self.health_monitor),
                ("deployment_manager", self.deployment_manager),
                ("config_manager", self.config_manager),
                ("log_aggregator", self.log_aggregator)

            
            for name, component in critical_components:
                if component is None:
                    logger.error(f"[HEALTH] Critical component {name} is None")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Component health check failed: {e}")
            return False
    
    async def reload_configuration(self):
        """Reload system configuration"""
        try:
            logger.info("[RELOAD] Reloading system configuration...")
            
            if self.config_manager:
                await self.config_manager.load_all_configurations()
            
            # Notify integrations
            if self.langchain_integration:
                langchain_config = await self.config_manager.get_configuration("langchain", {})
                await self._on_langchain_config_change("langchain", langchain_config)
            
            if self.autogen_integration:
                autogen_config = await self.config_manager.get_configuration("autogen", {})
                await self._on_autogen_config_change("autogen", autogen_config)
            
            logger.info("[RELOAD] Configuration reload completed")
            
        except Exception as e:
            logger.error(f"[ERROR] Configuration reload failed: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                "system": {
                    "name": self.config.get("coordination", {}).get("system_name", "MCP Coordination System"),
                    "version": self.config.get("coordination", {}).get("version", "1.0.0"),
                    "environment": self.config.get("coordination", {}).get("environment", "development"),
                    "status": "running" if self.is_running else "stopped",
                    "uptime": self.metrics["system_uptime"],
                    "startup_time": self.startup_time.isoformat() if self.startup_time else None
                },
                "metrics": self.metrics,
                "components": {}

            
            # Get component statuses
            if self.server_registry:
                status["components"]["server_registry"] = await self.server_registry.get_registry_status()
            
            if self.health_monitor:
                status["components"]["health_monitor"] = await self.health_monitor.get_overall_health_status()
            
            if self.deployment_manager:
                status["components"]["deployment_manager"] = await self.deployment_manager.get_deployment_status()
            
            if self.config_manager:
                status["components"]["config_manager"] = await self.config_manager.get_configuration_status()
            
            if self.log_aggregator:
                status["components"]["log_aggregator"] = await self.log_aggregator.get_log_statistics()
            
            # Integration statuses
            status["integrations"] = {
                "langchain": {
                    "enabled": self.langchain_integration is not None,
                    "status": "connected" if self.langchain_integration else "disabled"
                },
                "autogen": {
                    "enabled": self.autogen_integration is not None,
                    "status": "connected" if self.autogen_integration else "disabled"


            
            return status
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get system status: {e}")
            return {"error": str(e)}
    
    async def _cleanup_on_error(self):
        """Cleanup resources on initialization error"""
        try:
            components = [
                self.dashboard_server,
                self.deployment_manager,
                self.health_monitor,
                self.server_registry,
                self.log_aggregator,
                self.config_manager

            
            for component in components:
                if component and hasattr(component, 'shutdown'):
                    try:
                        await component.shutdown()
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"[ERROR] Cleanup on error failed: {e}")
    
    async def shutdown(self):
        """Graceful shutdown of all components"""
        try:
            logger.info("[SHUTDOWN] Starting graceful shutdown...")
            self.is_running = False
            
            # Log shutdown
            if self.log_aggregator:
                await self.log_aggregator.log(
                    LogLevel.INFO,
                    LogSource.SYSTEM,
                    "unified_coordinator",
                    "System shutdown initiated",
                    metadata={"uptime": self.metrics["system_uptime"]}

            
            # Cancel background tasks
            tasks = [self.system_monitor_task, self.integration_sync_task]
            for task in tasks:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Shutdown components in reverse order
            components = [
                ("dashboard_server", self.dashboard_server),
                ("deployment_manager", self.deployment_manager),
                ("health_monitor", self.health_monitor),
                ("server_registry", self.server_registry),
                ("log_aggregator", self.log_aggregator),
                ("config_manager", self.config_manager)

            
            for name, component in components:
                if component:
                    try:
                        logger.info(f"[SHUTDOWN] Shutting down {name}...")
                        await component.shutdown()
                    except Exception as e:
                        logger.error(f"[SHUTDOWN] Failed to shutdown {name}: {e}")
            
            logger.info("[SHUTDOWN] Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"[ERROR] Shutdown failed: {e}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified MCP Coordination System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--daemonize", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    
    # Create and run coordinator
    coordinator = UnifiedCoordinator(args.config)
    
    try:
        await coordinator.run()
    except Exception as e:
        logger.error(f"[FATAL] System failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())