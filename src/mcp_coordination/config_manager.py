# -*- coding: utf-8 -*-
"""
Configuration Manager for MCP Coordination System

This module provides centralized configuration management, validation,
and dynamic updates for all MCP servers and coordination components.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import json
import logging
import os

from dataclasses import dataclass, field
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """Supported configuration formats"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"


class ConfigSource(Enum):
    """Configuration sources"""
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    REMOTE = "remote"
    DEFAULT = "default"


@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    name: str
    description: str
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, type] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    default_values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigEntry:
    """Individual configuration entry"""
    key: str
    value: Any
    source: ConfigSource
    format: ConfigFormat
    last_updated: datetime
    schema: Optional[ConfigSchema] = None
    is_sensitive: bool = False
    validation_errors: List[str] = field(default_factory=list)


class ConfigManager:
    """
    Centralized configuration management for the MCP coordination system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.config_settings = config.get("configuration", {})
        
        # Configuration storage
        self.configurations: Dict[str, ConfigEntry] = {}
        self.schemas: Dict[str, ConfigSchema] = {}
        
        # Configuration files and paths
        self.config_paths = {
            "main": "config/mcp_coordination.yaml",
            "servers": "config/mcp_servers.yaml",
            "langchain": "config/langchain_config.yaml",
            "autogen": "config/autogen_config.yaml",
            "deployment": "config/deployment.yaml",
            "monitoring": "config/monitoring.yaml"

        
        # Environment configuration
        self.env_prefix = self.config_settings.get("env_prefix", "MCP_")
        self.config_dir = Path(self.config_settings.get("config_dir", "config"))
        
        # Configuration watching
        self.watch_configs = self.config_settings.get("watch_configs", True)
        self.reload_interval = self.config_settings.get("reload_interval", 300)  # 5 minutes
        
        # Background tasks
        self.config_watcher_task: Optional[asyncio.Task] = None
        self.validation_task: Optional[asyncio.Task] = None
        
        # Change callbacks
        self.change_callbacks: Dict[str, List[callable]] = {}
        
        # Configuration statistics
        self.stats = {
            "total_configs": 0,
            "valid_configs": 0,
            "invalid_configs": 0,
            "last_reload": None,
            "reload_count": 0,
            "validation_errors": 0

        
        logger.info("[INIT] Configuration Manager initialized")
    
    async def initialize(self):
        """Initialize the configuration manager"""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Load configuration schemas
            await self._load_schemas()
            
            # Load all configurations
            await self.load_all_configurations()
            
            # Start background tasks
            if self.watch_configs:
                self.config_watcher_task = asyncio.create_task(self._config_watcher_loop())
            
            self.validation_task = asyncio.create_task(self._validation_loop())
            
            logger.info("[OK] Configuration Manager initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] Configuration Manager initialization failed: {e}")
            raise
    
    async def _load_schemas(self):
        """Load configuration schemas"""
        
        # MCP Server Registry Schema
        self.schemas["mcp_servers"] = ConfigSchema(
            name="mcp_servers",
            description="MCP Server registry configuration",
            required_fields=["servers"],
            optional_fields=["discovery", "health_monitoring"],
            field_types={
                "servers": dict,
                "discovery": dict,
                "health_monitoring": dict
            },
            default_values={
                "discovery": {"auto_discover": True, "scan_interval": 300},
                "health_monitoring": {"enabled": True, "interval": 30}


        
        # Health Monitoring Schema
        self.schemas["health_monitoring"] = ConfigSchema(
            name="health_monitoring",
            description="Health monitoring configuration",
            required_fields=["timeout", "intervals"],
            optional_fields=["alerts", "circuit_breaker"],
            field_types={
                "timeout": int,
                "intervals": dict,
                "alerts": dict,
                "circuit_breaker": dict
            },
            default_values={
                "timeout": 10,
                "intervals": {"critical": 10, "integration": 30, "specialized": 60},
                "circuit_breaker": {"failure_threshold": 5, "recovery_timeout": 60}


        
        # Deployment Schema
        self.schemas["deployment"] = ConfigSchema(
            name="deployment",
            description="Deployment configuration",
            required_fields=["mode"],
            optional_fields=["auto_start", "restart_policy", "resource_limits"],
            field_types={
                "mode": str,
                "auto_start": bool,
                "restart_policy": str,
                "resource_limits": dict
            },
            default_values={
                "mode": "development",
                "auto_start": True,
                "restart_policy": "on-failure",
                "resource_limits": {"memory": "256MB", "cpu": "0.5"}


        
        # Dashboard Schema
        self.schemas["dashboard"] = ConfigSchema(
            name="dashboard",
            description="Dashboard server configuration",
            required_fields=["host", "port"],
            optional_fields=["debug", "auth", "ssl"],
            field_types={
                "host": str,
                "port": int,
                "debug": bool,
                "auth": dict,
                "ssl": dict
            },
            default_values={
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False


        
        # LangChain Integration Schema
        self.schemas["langchain"] = ConfigSchema(
            name="langchain",
            description="LangChain integration configuration",
            required_fields=["mcp_servers"],
            optional_fields=["workflows", "memory", "llm_config"],
            field_types={
                "mcp_servers": dict,
                "workflows": dict,
                "memory": dict,
                "llm_config": dict


        
        # AutoGen Integration Schema
        self.schemas["autogen"] = ConfigSchema(
            name="autogen",
            description="AutoGen integration configuration",
            required_fields=["agents", "mcp_servers"],
            optional_fields=["conversation_config", "decision_algorithms"],
            field_types={
                "agents": dict,
                "mcp_servers": dict,
                "conversation_config": dict,
                "decision_algorithms": dict


        
        logger.info(f"[OK] Loaded {len(self.schemas)} configuration schemas")
    
    async def load_all_configurations(self):
        """Load all configuration files"""
        try:
            loaded_count = 0
            
            for config_name, config_path in self.config_paths.items():
                try:
                    await self.load_configuration(config_name, config_path)
                    loaded_count += 1
                except Exception as e:
                    logger.warning(f"[WARNING] Failed to load config {config_name}: {e}")
            
            # Load environment variables
            await self._load_environment_config()
            
            # Update statistics
            self.stats["total_configs"] = len(self.configurations)
            self.stats["last_reload"] = datetime.now()
            self.stats["reload_count"] += 1
            
            logger.info(f"[OK] Loaded {loaded_count} configuration files")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load configurations: {e}")
            raise
    
    async def load_configuration(self, name: str, file_path: str) -> bool:
        """Load a specific configuration file"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"[WARNING] Configuration file not found: {file_path}")
                return False
            
            # Determine format from file extension
            format_map = {
                '.json': ConfigFormat.JSON,
                '.yaml': ConfigFormat.YAML,
                '.yml': ConfigFormat.YAML,
                '.toml': ConfigFormat.TOML

            
            config_format = format_map.get(path.suffix.lower(), ConfigFormat.YAML)
            
            # Load configuration data
            with open(path, 'r', encoding='utf-8') as f:
                if config_format == ConfigFormat.JSON:
                    data = json.load(f)
                elif config_format == ConfigFormat.YAML:
                    data = yaml.safe_load(f)
                elif config_format == ConfigFormat.TOML:
                    import tomli
                    data = tomli.load(f)
                else:
                    raise ValueError(f"Unsupported configuration format: {config_format}")
            
            # Create configuration entry
            config_entry = ConfigEntry(
                key=name,
                value=data,
                source=ConfigSource.FILE,
                format=config_format,
                last_updated=datetime.fromtimestamp(path.stat().st_mtime),
                schema=self.schemas.get(name)

            
            # Validate configuration
            await self._validate_configuration(config_entry)
            
            # Store configuration
            self.configurations[name] = config_entry
            
            logger.debug(f"[CONFIG] Loaded configuration: {name}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load configuration {name} from {file_path}: {e}")
            return False
    
    async def _load_environment_config(self):
        """Load configuration from environment variables"""
        try:
            env_config = {}
            
            for key, value in os.environ.items():
                if key.startswith(self.env_prefix):
                    # Convert environment variable to config key
                    config_key = key[len(self.env_prefix):].lower().replace('_', '.')
                    
                    # Try to parse as JSON, otherwise keep as string
                    try:
                        parsed_value = json.loads(value)
                    except json.JSONDecodeError:
                        parsed_value = value
                    
                    env_config[config_key] = parsed_value
            
            if env_config:
                config_entry = ConfigEntry(
                    key="environment",
                    value=env_config,
                    source=ConfigSource.ENVIRONMENT,
                    format=ConfigFormat.ENV,
                    last_updated=datetime.now()

                
                self.configurations["environment"] = config_entry
                logger.info(f"[CONFIG] Loaded {len(env_config)} environment configurations")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load environment configuration: {e}")
    
    async def _validate_configuration(self, config_entry: ConfigEntry):
        """Validate a configuration entry against its schema"""
        if not config_entry.schema:
            return  # No schema to validate against
        
        schema = config_entry.schema
        data = config_entry.value
        errors = []
        
        try:
            # Check required fields
            for field in schema.required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            # Check field types
            for field, expected_type in schema.field_types.items():
                if field in data and not isinstance(data[field], expected_type):
                    errors.append(f"Field '{field}' should be of type {expected_type.__name__}, got {type(data[field]).__name__}")
            
            # Apply validation rules
            for field, rules in schema.validation_rules.items():
                if field in data:
                    value = data[field]
                    
                    # Range validation
                    if 'min' in rules and value < rules['min']:
                        errors.append(f"Field '{field}' value {value} is below minimum {rules['min']}")
                    if 'max' in rules and value > rules['max']:
                        errors.append(f"Field '{field}' value {value} is above maximum {rules['max']}")
                    
                    # Choice validation
                    if 'choices' in rules and value not in rules['choices']:
                        errors.append(f"Field '{field}' value '{value}' not in allowed choices: {rules['choices']}")
                    
                    # Pattern validation
                    if 'pattern' in rules:
                        import re
                        if not re.match(rules['pattern'], str(value)):
                            errors.append(f"Field '{field}' value '{value}' does not match pattern: {rules['pattern']}")
            
            config_entry.validation_errors = errors
            
            if errors:
                self.stats["invalid_configs"] += 1
                self.stats["validation_errors"] += len(errors)
                logger.warning(f"[VALIDATION] Configuration '{config_entry.key}' has {len(errors)} validation errors")
            else:
                self.stats["valid_configs"] += 1
                logger.debug(f"[VALIDATION] Configuration '{config_entry.key}' validated successfully")
            
        except Exception as e:
            error_msg = f"Validation failed: {e}"
            config_entry.validation_errors = [error_msg]
            logger.error(f"[ERROR] Configuration validation error for '{config_entry.key}': {e}")
    
    async def get_configuration(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        try:
            if key in self.configurations:
                return self.configurations[key].value
            
            # Try nested key (e.g., "servers.critical.filesystem")
            keys = key.split('.')
            current = None
            
            for config_entry in self.configurations.values():
                current = config_entry.value
                try:
                    for k in keys:
                        current = current[k]
                    return current
                except (KeyError, TypeError):
                    continue
            
            return default
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get configuration '{key}': {e}")
            return default
    
    async def set_configuration(self, key: str, value: Any, source: ConfigSource = ConfigSource.DEFAULT) -> bool:
        """Set a configuration value"""
        try:
            # Create or update configuration entry
            config_entry = ConfigEntry(
                key=key,
                value=value,
                source=source,
                format=ConfigFormat.JSON,  # Default format for programmatic updates
                last_updated=datetime.now()

            
            # Validate if schema exists
            schema_name = key.split('.')[0]
            if schema_name in self.schemas:
                config_entry.schema = self.schemas[schema_name]
                await self._validate_configuration(config_entry)
            
            self.configurations[key] = config_entry
            
            # Trigger change callbacks
            await self._trigger_change_callbacks(key, value)
            
            logger.debug(f"[CONFIG] Set configuration: {key}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to set configuration '{key}': {e}")
            return False
    
    async def update_configuration_file(self, config_name: str, updates: Dict[str, Any]) -> bool:
        """Update a configuration file with new values"""
        try:
            if config_name not in self.config_paths:
                logger.error(f"[ERROR] Unknown configuration: {config_name}")
                return False
            
            file_path = Path(self.config_paths[config_name])
            
            # Load current configuration
            current_config = await self.get_configuration(config_name, {})
            if isinstance(current_config, dict):
                # Merge updates
                merged_config = self._deep_merge_dict(current_config, updates)
            else:
                merged_config = updates
            
            # Write updated configuration back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(merged_config, f, default_flow_style=False, indent=2)
                elif file_path.suffix.lower() == '.json':
                    json.dump(merged_config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            # Reload the configuration
            await self.load_configuration(config_name, str(file_path))
            
            logger.info(f"[CONFIG] Updated configuration file: {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to update configuration file '{config_name}': {e}")
            return False
    
    def _deep_merge_dict(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value
        
        return result
    
    async def register_change_callback(self, config_key: str, callback: callable):
        """Register a callback for configuration changes"""
        if config_key not in self.change_callbacks:
            self.change_callbacks[config_key] = []
        
        self.change_callbacks[config_key].append(callback)
        logger.debug(f"[CONFIG] Registered change callback for: {config_key}")
    
    async def _trigger_change_callbacks(self, key: str, new_value: Any):
        """Trigger callbacks for configuration changes"""
        try:
            # Direct key callbacks
            if key in self.change_callbacks:
                for callback in self.change_callbacks[key]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(key, new_value)
                        else:
                            callback(key, new_value)
                    except Exception as e:
                        logger.error(f"[ERROR] Configuration change callback failed for '{key}': {e}")
            
            # Wildcard callbacks (e.g., "servers.*")
            for callback_key in self.change_callbacks:
                if callback_key.endswith('.*') and key.startswith(callback_key[:-1]):
                    for callback in self.change_callbacks[callback_key]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(key, new_value)
                            else:
                                callback(key, new_value)
                        except Exception as e:
                            logger.error(f"[ERROR] Wildcard configuration callback failed for '{key}': {e}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to trigger change callbacks for '{key}': {e}")
    
    async def _config_watcher_loop(self):
        """Background task to watch for configuration file changes"""
        while True:
            try:
                await asyncio.sleep(self.reload_interval)
                
                # Check if any configuration files have been modified
                for config_name, config_path in self.config_paths.items():
                    path = Path(config_path)
                    if path.exists():
                        file_mtime = datetime.fromtimestamp(path.stat().st_mtime)
                        
                        if config_name in self.configurations:
                            stored_mtime = self.configurations[config_name].last_updated
                            
                            if file_mtime > stored_mtime:
                                logger.info(f"[CONFIG] Reloading modified configuration: {config_name}")
                                await self.load_configuration(config_name, config_path)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Configuration watcher failed: {e}")
    
    async def _validation_loop(self):
        """Background task for periodic configuration validation"""
        while True:
            try:
                await asyncio.sleep(3600)  # Validate every hour
                
                logger.debug("[VALIDATION] Starting periodic configuration validation")
                
                for config_entry in self.configurations.values():
                    await self._validate_configuration(config_entry)
                
                logger.debug("[VALIDATION] Periodic validation completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Periodic validation failed: {e}")
    
    async def export_configurations(self, format: ConfigFormat = ConfigFormat.YAML) -> str:
        """Export all configurations to a string"""
        try:
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "total_configs": len(self.configurations),
                    "format": format.value
                },
                "configurations": {}

            
            for name, config_entry in self.configurations.items():
                export_data["configurations"][name] = {
                    "value": config_entry.value,
                    "source": config_entry.source.value,
                    "last_updated": config_entry.last_updated.isoformat(),
                    "validation_errors": config_entry.validation_errors

            
            if format == ConfigFormat.YAML:
                return yaml.dump(export_data, default_flow_style=False, indent=2)
            elif format == ConfigFormat.JSON:
                return json.dumps(export_data, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to export configurations: {e}")
            return ""
    
    async def get_configuration_status(self) -> Dict[str, Any]:
        """Get comprehensive configuration status"""
        valid_configs = len([c for c in self.configurations.values() if not c.validation_errors])
        invalid_configs = len(self.configurations) - valid_configs
        
        return {
            "configuration_manager_status": "operational",
            "total_configurations": len(self.configurations),
            "valid_configurations": valid_configs,
            "invalid_configurations": invalid_configs,
            "schemas_loaded": len(self.schemas),
            "statistics": self.stats,
            "configuration_sources": {
                source.value: len([c for c in self.configurations.values() if c.source == source])
                for source in ConfigSource
            },
            "validation_summary": {
                config_name: {
                    "valid": len(config.validation_errors) == 0,
                    "errors": config.validation_errors,
                    "last_updated": config.last_updated.isoformat()

                for config_name, config in self.configurations.items()
            },
            "watched_files": list(self.config_paths.keys()),
            "background_tasks": {
                "config_watcher": self.config_watcher_task is not None and not self.config_watcher_task.done(),
                "validation": self.validation_task is not None and not self.validation_task.done()


    
    async def validate_all_configurations(self) -> Dict[str, List[str]]:
        """Validate all configurations and return errors"""
        validation_results = {}
        
        for name, config_entry in self.configurations.items():
            await self._validate_configuration(config_entry)
            validation_results[name] = config_entry.validation_errors
        
        return validation_results
    
    async def create_default_configurations(self):
        """Create default configuration files if they don't exist"""
        try:
            default_configs = {
                "mcp_coordination": {
                    "coordination": {
                        "discovery": {"auto_discover": True, "scan_interval": 300},
                        "health_monitoring": {"enabled": True, "timeout": 10},
                        "deployment": {"mode": "development", "auto_start": True},
                        "dashboard": {"host": "0.0.0.0", "port": 8080, "debug": False}

                },
                "mcp_servers": {
                    "critical": {},
                    "integration": {},
                    "specialized": {}
                },
                "deployment": {
                    "mode": "development",
                    "auto_start": True,
                    "restart_policy": "on-failure",
                    "resource_limits": {
                        "memory": "256MB",
                        "cpu": "0.5"

                },
                "monitoring": {
                    "health_checks": {
                        "timeout": 10,
                        "intervals": {
                            "critical": 10,
                            "integration": 30,
                            "specialized": 60

                    },
                    "alerts": {
                        "enabled": True,
                        "severity_threshold": "warning"



            
            created_count = 0
            for config_name, default_data in default_configs.items():
                if config_name in self.config_paths:
                    config_path = Path(self.config_paths[config_name])
                    
                    if not config_path.exists():
                        # Create directory if it doesn't exist
                        config_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Write default configuration
                        with open(config_path, 'w') as f:
                            yaml.dump(default_data, f, default_flow_style=False, indent=2)
                        
                        created_count += 1
                        logger.info(f"[CONFIG] Created default configuration: {config_path}")
            
            if created_count > 0:
                logger.info(f"[CONFIG] Created {created_count} default configuration files")
                await self.load_all_configurations()
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to create default configurations: {e}")
    
    async def shutdown(self):
        """Shutdown the configuration manager"""
        logger.info("[SHUTDOWN] Shutting down Configuration Manager...")
        
        # Cancel background tasks
        if self.config_watcher_task:
            self.config_watcher_task.cancel()
            try:
                await self.config_watcher_task
            except asyncio.CancelledError:
                pass
        
        if self.validation_task:
            self.validation_task.cancel()
            try:
                await self.validation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[SHUTDOWN] Configuration Manager shutdown complete")