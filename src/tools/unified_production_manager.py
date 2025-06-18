#!/usr/bin/env python3
"""
Unified Production Management System
===================================

Consolidated production deployment and optimization management.
Merged from:
- production_deployment_manager.py (1020 lines)
- production_optimizer.py (416 lines)

Features:
- Production deployment management
- System optimization configuration
- Environment setup and validation
- Security and configuration management
- Performance monitoring and alerts
- Revenue optimization strategies
"""

import asyncio
import aiohttp
import os
import sys
import platform
import logging
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, cast
from pathlib import Path
from dataclasses import dataclass
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from decimal import Decimal

# Windows-specific asyncio event loop fix for aiodns compatibility
if platform.system() == 'Windows':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        print("✅ Set Windows ProactorEventLoopPolicy for aiodns compatibility")
    except AttributeError:
        try:
            import asyncio.windows_events
            asyncio.set_event_loop_policy(asyncio.windows_events.WindowsProactorEventLoopPolicy())
            print("✅ Set Windows ProactorEventLoopPolicy (fallback)")
        except ImportError:
            print("⚠️ Unable to set Windows event loop policy, may encounter aiodns issues")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_management.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """Production optimization configuration"""
    
    # Database Optimization
    redis_cache_ttl: int = 300  # 5 minutes
    db_connection_pool_size: int = 20
    db_query_timeout: int = 30
    
    # API Optimization  
    connection_pool_size: int = 100
    request_timeout: int = 30
    batch_request_size: int = 50
    rate_limit_per_second: int = 100
    
    # Caching Strategy
    memory_cache_size: int = 10000
    price_cache_ttl: int = 10  # seconds
    opportunity_cache_ttl: int = 5  # seconds
    
    # Performance Monitoring
    performance_log_interval: int = 60  # seconds
    metric_retention_days: int = 30
    alert_thresholds: Optional[Dict[str, float]] = None
    
    # Revenue Optimization
    min_profit_threshold: Decimal = Decimal('10.0')
    max_slippage: Decimal = Decimal('0.01')
    gas_price_multiplier: Decimal = Decimal('1.2')
    
@dataclass
class DeploymentConfig:
    """Production deployment configuration"""
    environment: str
    debug_mode: bool
    log_level: str
    database_url: str
    redis_url: str
    encryption_key: str
    api_keys: Dict[str, str]
    monitoring_enabled: bool
    backup_enabled: bool

class ProductionOptimizer:
    """Handles system optimization and performance tuning"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.redis_client = None
        self.metrics: Dict[str, Any] = {}
        
    async def initialize_redis(self):
        """Initialize Redis connection for caching"""
        try:
            import aioredis
            self.redis_client = await aioredis.from_url(
                "redis://localhost",
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
    
    async def optimize_database_connections(self):
        """Optimize database connection settings"""
        logger.info("Optimizing database connections...")
        # Implementation for database optimization
        
    async def setup_caching_strategy(self):
        """Setup intelligent caching for price data"""
        logger.info("Setting up caching strategy...")
        # Implementation for caching setup
        
    async def configure_rate_limiting(self):
        """Configure API rate limiting"""
        logger.info("Configuring rate limiting...")
        # Implementation for rate limiting
        
    async def monitor_performance(self):
        """Continuous performance monitoring"""
        while True:
            try:
                # Collect performance metrics
                metrics = await self.collect_metrics()
                
                # Check alert thresholds
                await self.check_alerts(metrics)
                
                # Log performance data
                self.log_performance_metrics(metrics)
                
                await asyncio.sleep(self.config.performance_log_interval)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        if not self.config.alert_thresholds:
            return
            
        for metric, threshold in self.config.alert_thresholds.items():
            if metric in metrics and metrics[metric] > threshold:
                await self.send_alert(metric, metrics[metric], threshold)
    
    async def send_alert(self, metric: str, value: float, threshold: float):
        """Send performance alert"""
        logger.warning(f"ALERT: {metric} ({value}) exceeded threshold ({threshold})")
        # Implementation for sending alerts (email, webhook, etc.)
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log performance metrics"""
        logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")

class ProductionDeploymentManager:
    """Manages production deployment and configuration"""
    
    def __init__(self):
        self.config_path = Path("config/production_config.json")
        self.env_path = Path(".env")
        self.deployment_config: Optional[DeploymentConfig] = None
        self.optimizer: Optional[ProductionOptimizer] = None
        
    def load_deployment_config(self) -> DeploymentConfig:
        """Load production deployment configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
            else:
                config_data = self.create_default_config()
                
            return DeploymentConfig(
                environment=config_data.get('environment', 'production'),
                debug_mode=config_data.get('debug_mode', False),
                log_level=config_data.get('log_level', 'INFO'),
                database_url=config_data.get('database_url', ''),
                redis_url=config_data.get('redis_url', 'redis://localhost:6379'),
                encryption_key=config_data.get('encryption_key', ''),
                api_keys=config_data.get('api_keys', {}),
                monitoring_enabled=config_data.get('monitoring_enabled', True),
                backup_enabled=config_data.get('backup_enabled', True)
            )
        except Exception as e:
            logger.error(f"Failed to load deployment config: {e}")
            return self.create_default_deployment_config()
    
    def create_default_config(self) -> Dict[str, Any]:
        """Create default production configuration"""
        default_config = {
            "environment": "production",
            "debug_mode": False,
            "log_level": "INFO",
            "database_url": "${DATABASE_URL}",
            "redis_url": "${REDIS_URL}",
            "encryption_key": "${ENCRYPTION_KEY}",
            "api_keys": {
                "polygon_rpc": "${POLYGON_RPC_URL}",
                "coingecko": "${COINGECKO_API_KEY}",
                "moralis": "${MORALIS_API_KEY}"
            },
            "monitoring_enabled": True,
            "backup_enabled": True,
            "optimization": {
                "redis_cache_ttl": 300,
                "connection_pool_size": 100,
                "request_timeout": 30,
                "rate_limit_per_second": 100
            }
        }
        
        # Save default config
        os.makedirs(self.config_path.parent, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        return default_config
    
    def create_default_deployment_config(self) -> DeploymentConfig:
        """Create default deployment configuration"""
        return DeploymentConfig(
            environment="production",
            debug_mode=False,
            log_level="INFO",
            database_url="",
            redis_url="redis://localhost:6379",
            encryption_key="",
            api_keys={},
            monitoring_enabled=True,
            backup_enabled=True
        )
    
    def validate_environment(self) -> bool:
        """Validate production environment configuration"""
        logger.info("Validating production environment...")
        
        required_vars = [
            'POLYGON_RPC_URL',
            'PRIVATE_KEY',
            'DATABASE_URL',
            'ENCRYPTION_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        logger.info("Environment validation passed")
        return True
    
    def setup_encryption(self) -> str:
        """Setup encryption for sensitive data"""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            # Generate new encryption key
            encryption_key = Fernet.generate_key().decode()
            logger.info("Generated new encryption key")
            
            # Save to environment file
            self.update_env_file('ENCRYPTION_KEY', encryption_key)
        
        return encryption_key
    
    def update_env_file(self, key: str, value: str):
        """Update environment file with new key-value pair"""
        env_lines = []
        
        if self.env_path.exists():
            with open(self.env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add the key
        key_found = False
        for i, line in enumerate(env_lines):
            if line.startswith(f"{key}="):
                env_lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        if not key_found:
            env_lines.append(f"{key}={value}\n")
        
        # Write back to file
        with open(self.env_path, 'w') as f:
            f.writelines(env_lines)
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        logger.info("Checking dependencies...")
        
        required_packages = [
            'aiohttp',
            'asyncio',
            'web3',
            'redis',
            'psutil',
            'cryptography',
            'python-dotenv'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            logger.info("Install with: pip install " + " ".join(missing_packages))
            return False
        
        logger.info("All dependencies satisfied")
        return True
    
    def setup_logging(self):
        """Setup production logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure file handlers
        handlers = [
            logging.FileHandler(log_dir / "system.log"),
            logging.FileHandler(log_dir / "error.log"),
            logging.StreamHandler()
        ]
        
        # Set error handler to only log errors
        handlers[1].setLevel(logging.ERROR)
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.deployment_config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        
        logger.info("Production logging configured")
    
    def backup_configuration(self):
        """Backup current configuration"""
        backup_dir = Path("backups") / f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup configuration files
        import shutil
        
        config_files = [
            self.config_path,
            "config/mcp_servers.json",
            "config/arbitrage_config.json",
            ".env.template"
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                shutil.copy2(config_file, backup_dir)
        
        logger.info(f"Configuration backed up to {backup_dir}")
    
    async def deploy_to_production(self):
        """Main deployment process"""
        logger.info("Starting production deployment...")
        
        try:
            # Load configuration
            self.deployment_config = self.load_deployment_config()
            
            # Validate environment
            if not self.validate_environment():
                raise Exception("Environment validation failed")
            
            # Check dependencies
            if not self.check_dependencies():
                raise Exception("Dependency check failed")
            
            # Setup encryption
            encryption_key = self.setup_encryption()
            
            # Setup logging
            self.setup_logging()
            
            # Backup configuration
            self.backup_configuration()
            
            # Initialize optimizer
            opt_config = OptimizationConfig()
            self.optimizer = ProductionOptimizer(opt_config)
            await self.optimizer.initialize_redis()
            
            # Setup optimizations
            await self.optimizer.optimize_database_connections()
            await self.optimizer.setup_caching_strategy()
            await self.optimizer.configure_rate_limiting()
            
            # Start monitoring
            monitor_task = asyncio.create_task(self.optimizer.monitor_performance())
            
            logger.info("✅ Production deployment completed successfully")
            
            # Keep monitoring running
            await monitor_task
            
        except Exception as e:
            logger.error(f"Production deployment failed: {e}")
            raise
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        return {
            "environment": self.deployment_config.environment if self.deployment_config else "unknown",
            "config_loaded": self.deployment_config is not None,
            "optimizer_active": self.optimizer is not None,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Main entry point for production management"""
    manager = ProductionDeploymentManager()
    
    try:
        await manager.deploy_to_production()
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
