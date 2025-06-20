"""
Configuration Management
========================

Centralized configuration management for the LangChain multi-agent system.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "postgres"
    port: int = 5432
    database: str = "flash_loan_db"
    username: str = "flash_loan_user"
    password: str = "flash_loan_secure_2025"
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "redis"
    port: int = 6379
    password: str = "flash_loan_redis_2025"
    db: int = 0
    
    @property
    def url(self) -> str:
        return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"

@dataclass
class LLMConfig:
    """LLM configuration"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    model_name: str = "gpt-4-turbo-preview"
    temperature: float = 0.1
    max_tokens: int = 2000

@dataclass
class VectorStoreConfig:
    """Vector store configuration"""
    provider: str = "chroma"  # chroma, pinecone, weaviate
    collection_name: str = "flash_loan_knowledge"
    persist_directory: str = "/app/vector_store"
    embedding_model: str = "text-embedding-ada-002"

@dataclass
class AgentConfig:
    """Agent configuration"""
    max_concurrent_tasks: int = 5
    task_timeout: int = 300  # seconds
    retry_attempts: int = 3
    enable_memory: bool = True
    enable_tools: bool = True

@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_code_execution: bool = True
    execution_timeout: int = 30
    allowed_imports: Optional[List[str]] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    def __post_init__(self):
        if self.allowed_imports is None:
            self.allowed_imports = [
                'math', 'numpy', 'pandas', 'matplotlib', 'seaborn',
                'requests', 'json', 'datetime', 'time', 'os',
                'web3', 'eth_account', 'eth_utils'
            ]

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_metrics: bool = True
    metrics_port: int = 8080
    health_check_interval: int = 30
    log_level: str = "INFO"

class Config:
    """
    Main configuration class that aggregates all configuration sections.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv("CONFIG_FILE", "/app/config.json")
        
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.llm = LLMConfig()
        self.vector_store = VectorStoreConfig()
        self.agent = AgentConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        
        # Load configuration
        self.load_config()
        self.load_environment_variables()

    def load_config(self):
        """Load configuration from file if it exists"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update configuration sections
                if 'database' in config_data:
                    self._update_dataclass(self.database, config_data['database'])
                
                if 'redis' in config_data:
                    self._update_dataclass(self.redis, config_data['redis'])
                
                if 'llm' in config_data:
                    self._update_dataclass(self.llm, config_data['llm'])
                
                if 'vector_store' in config_data:
                    self._update_dataclass(self.vector_store, config_data['vector_store'])
                
                if 'agent' in config_data:
                    self._update_dataclass(self.agent, config_data['agent'])
                
                if 'security' in config_data:
                    self._update_dataclass(self.security, config_data['security'])
                
                if 'monitoring' in config_data:
                    self._update_dataclass(self.monitoring, config_data['monitoring'])
                
                print(f"✅ Configuration loaded from {self.config_file}")
            else:
                print(f"ℹ️ Configuration file {self.config_file} not found, using defaults")
                
        except Exception as e:
            print(f"⚠️ Error loading configuration: {e}")

    def load_environment_variables(self):
        """Load configuration from environment variables"""
        # Database
        self.database.host = os.getenv("POSTGRES_HOST", self.database.host)
        self.database.port = int(os.getenv("POSTGRES_PORT", str(self.database.port)))
        self.database.database = os.getenv("POSTGRES_DB", self.database.database)
        self.database.username = os.getenv("POSTGRES_USER", self.database.username)
        self.database.password = os.getenv("POSTGRES_PASSWORD", self.database.password)
        
        # Redis
        self.redis.host = os.getenv("REDIS_HOST", self.redis.host)
        self.redis.port = int(os.getenv("REDIS_PORT", str(self.redis.port)))
        self.redis.password = os.getenv("REDIS_PASSWORD", self.redis.password)
        
        # LLM
        self.llm.openai_api_key = os.getenv("OPENAI_API_KEY", self.llm.openai_api_key)
        self.llm.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.llm.anthropic_api_key)
        self.llm.google_api_key = os.getenv("GOOGLE_API_KEY", self.llm.google_api_key)
        self.llm.model_name = os.getenv("LLM_MODEL", self.llm.model_name)
        
        # Vector Store
        self.vector_store.provider = os.getenv("VECTOR_STORE_PROVIDER", self.vector_store.provider)
        self.vector_store.persist_directory = os.getenv("VECTOR_STORE_DIR", self.vector_store.persist_directory)
        
        # Monitoring
        self.monitoring.log_level = os.getenv("LOG_LEVEL", self.monitoring.log_level)

    def _update_dataclass(self, dataclass_instance, config_dict: Dict[str, Any]):
        """Update a dataclass instance with values from a dictionary"""
        for key, value in config_dict.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)

    def save_config(self, config_file: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        try:
            file_path = config_file or self.config_file
            
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Prepare configuration data
            config_data = {
                'database': asdict(self.database),
                'redis': asdict(self.redis),
                'llm': asdict(self.llm),
                'vector_store': asdict(self.vector_store),
                'agent': asdict(self.agent),
                'security': asdict(self.security),
                'monitoring': asdict(self.monitoring)
            }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"✅ Configuration saved to {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
            return False

    def validate_config(self) -> Dict[str, Any]:
        """Validate the current configuration"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate API keys
        if not self.llm.openai_api_key:
            validation_results["warnings"].append("OpenAI API key not set")
        
        # Validate database connection
        if not all([self.database.host, self.database.username, self.database.password]):
            validation_results["errors"].append("Database configuration incomplete")
            validation_results["valid"] = False
        
        # Validate Redis connection
        if not all([self.redis.host, str(self.redis.port)]):
            validation_results["errors"].append("Redis configuration incomplete")
            validation_results["valid"] = False
        
        # Validate vector store
        if not self.vector_store.persist_directory:
            validation_results["errors"].append("Vector store persist directory not set")
            validation_results["valid"] = False
        
        return validation_results

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration (without sensitive data)"""
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "username": self.database.username
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "db": self.redis.db
            },
            "llm": {
                "model_name": self.llm.model_name,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "has_openai_key": bool(self.llm.openai_api_key),
                "has_anthropic_key": bool(self.llm.anthropic_api_key)
            },
            "vector_store": {
                "provider": self.vector_store.provider,
                "collection_name": self.vector_store.collection_name,
                "embedding_model": self.vector_store.embedding_model
            },
            "agent": asdict(self.agent),
            "security": {
                "enable_code_execution": self.security.enable_code_execution,
                "execution_timeout": self.security.execution_timeout,
                "allowed_imports_count": len(self.security.allowed_imports)
            },
            "monitoring": asdict(self.monitoring)
        }

# Singleton instance
_config_instance = None

def get_config() -> Config:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
