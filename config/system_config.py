"""
Centralized Configuration Management for Flash Loan Arbitrage System
================================================================

This module provides centralized configuration management with:
- Environment variable handling
- Type validation
- Default values
- Configuration profiles (dev/prod)
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class BlockchainConfig:
    """Blockchain connection configuration"""
    polygon_rpc: str = ""
    ethereum_rpc: str = ""
    bsc_rpc: str = ""
    arbitrum_rpc: str = ""
    private_key: str = ""
    gas_price_gwei: float = 20.0
    max_gas_limit: int = 500000

@dataclass 
class TradingConfig:
    """Trading parameters configuration"""
    max_trade_size_usd: float = 10000.0
    min_profit_usd: float = 5.0
    slippage_tolerance: float = 0.005
    max_concurrent_trades: int = 3
    risk_tolerance: float = 0.1
    auto_execute: bool = False

@dataclass
class MCPConfig:
    """MCP Server configuration"""
    base_port: int = 8000
    health_check_interval: int = 30
    max_retries: int = 3
    timeout_seconds: int = 10
    enabled_servers: List[str] = field(default_factory=lambda: [
        "arbitrage", "price-feed", "risk-manager", "liquidity",
        "blockchain", "flash-loan", "defi-analyzer", "monitoring"
    ])

@dataclass
class AIAgentConfig:
    """AI Agent configuration"""
    model_path: str = "models/"
    prediction_interval: int = 60
    training_enabled: bool = False
    confidence_threshold: float = 0.7
    learning_rate: float = 0.001

@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    enable_prometheus: bool = True
    enable_discord_alerts: bool = False
    enable_email_alerts: bool = False
    discord_webhook: str = ""
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "max_loss_usd": 1000.0,
        "min_success_rate": 0.8,
        "max_response_time_ms": 2000.0
    })

@dataclass
class SystemConfig:
    """Main system configuration"""
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "data/"
    
    # Component configurations
    blockchain: BlockchainConfig = field(default_factory=BlockchainConfig)
    trading: TradingConfig = field(default_factory=TradingConfig) 
    mcp: MCPConfig = field(default_factory=MCPConfig)
    ai_agents: AIAgentConfig = field(default_factory=AIAgentConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/system_config.json"
        self.config = SystemConfig()
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment and files"""
        # Load from environment variables
        self._load_from_env()
        
        # Load from JSON config file if exists
        if os.path.exists(self.config_file):
            self._load_from_file()
        else:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            self.save_config()  # Save default config
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # System settings
        self.config.environment = os.getenv("ENVIRONMENT", "development")
        self.config.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.config.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Blockchain configuration
        self.config.blockchain.polygon_rpc = os.getenv("POLYGON_RPC_URL", "")
        self.config.blockchain.ethereum_rpc = os.getenv("ETHEREUM_RPC_URL", "")
        self.config.blockchain.bsc_rpc = os.getenv("BSC_RPC_URL", "")
        self.config.blockchain.arbitrum_rpc = os.getenv("ARBITRUM_RPC_URL", "")
        self.config.blockchain.private_key = os.getenv("PRIVATE_KEY", "")
        
        # Trading configuration
        self.config.trading.max_trade_size_usd = float(
            os.getenv("MAX_TRADE_SIZE_USD", "10000")
        )
        self.config.trading.min_profit_usd = float(
            os.getenv("MIN_PROFIT_USD", "5")
        )
        self.config.trading.slippage_tolerance = float(
            os.getenv("SLIPPAGE_TOLERANCE", "0.005")
        )
        self.config.trading.auto_execute = os.getenv("AUTO_EXECUTE", "false").lower() == "true"
        
        # MCP configuration
        self.config.mcp.base_port = int(os.getenv("MCP_BASE_PORT", "8000"))
        
        # Monitoring configuration
        self.config.monitoring.discord_webhook = os.getenv("DISCORD_WEBHOOK", "")
        self.config.monitoring.enable_discord_alerts = bool(self.config.monitoring.discord_webhook)
    
    def _load_from_file(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update configuration with file data
            self._update_config_from_dict(config_data)
            logger.info(f"Loaded configuration from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load config from file: {e}")
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary"""
        # Simple recursive update - in production, use a proper config library
        for key, value in config_data.items():
            if hasattr(self.config, key):
                if isinstance(value, dict):
                    current_attr = getattr(self.config, key)
                    for sub_key, sub_value in value.items():
                        if hasattr(current_attr, sub_key):
                            setattr(current_attr, sub_key, sub_value)
                else:
                    setattr(self.config, key, value)
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Convert dataclass to dict for JSON serialization
            config_dict = self._dataclass_to_dict(self.config)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Saved configuration to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Convert dataclass to dictionary for JSON serialization"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_def in obj.__dataclass_fields__.items():
                field_value = getattr(obj, field_name)
                if hasattr(field_value, '__dataclass_fields__'):
                    result[field_name] = self._dataclass_to_dict(field_value)
                else:
                    result[field_name] = field_value
            return result
        return obj
    
    def get_blockchain_config(self) -> BlockchainConfig:
        """Get blockchain configuration"""
        return self.config.blockchain
    
    def get_trading_config(self) -> TradingConfig:
        """Get trading configuration"""
        return self.config.trading
    
    def get_mcp_config(self) -> MCPConfig:
        """Get MCP configuration"""
        return self.config.mcp
    
    def get_ai_config(self) -> AIAgentConfig:
        """Get AI agent configuration"""
        return self.config.ai_agents
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        return self.config.monitoring
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.config.environment.lower() == "production"
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required blockchain settings
        if not self.config.blockchain.private_key:
            issues.append("PRIVATE_KEY environment variable not set")
        
        if not any([
            self.config.blockchain.polygon_rpc,
            self.config.blockchain.ethereum_rpc,
            self.config.blockchain.bsc_rpc,
            self.config.blockchain.arbitrum_rpc
        ]):
            issues.append("No blockchain RPC URLs configured")
        
        # Check trading limits
        if self.config.trading.max_trade_size_usd <= 0:
            issues.append("MAX_TRADE_SIZE_USD must be positive")
        
        if self.config.trading.min_profit_usd <= 0:
            issues.append("MIN_PROFIT_USD must be positive")
        
        # Check slippage tolerance
        if not 0 < self.config.trading.slippage_tolerance < 1:
            issues.append("SLIPPAGE_TOLERANCE must be between 0 and 1")
        
        return issues

# Global configuration instance
config_manager = ConfigManager()

def get_config() -> SystemConfig:
    """Get the global configuration instance"""
    return config_manager.config

def reload_config():
    """Reload configuration from files and environment"""
    config_manager.load_config()

# Convenience functions
def get_blockchain_config() -> BlockchainConfig:
    return config_manager.get_blockchain_config()

def get_trading_config() -> TradingConfig:
    return config_manager.get_trading_config()

def get_mcp_config() -> MCPConfig:
    return config_manager.get_mcp_config()

def is_production() -> bool:
    return config_manager.is_production()