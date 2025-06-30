# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
            import socket
from pathlib import Path
from typing import List, Dict, Any
import asyncio
import json
import logging
import platform
import subprocess
import sys

            from complete_langchain_mcp_integration import CompleteLangChainMCPSystem
import yaml
"""
Enhanced LangChain MCP System Launcher
======================================

This script provides an easy way to launch the complete LangChain MCP integration system
with proper dependency checking, environment setup, and configuration validation.

Author: GitHub Copilot Assistant
Date: June 16, 2025
"""


# Configure logging

# Unicode-safe logging setup
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

logging.basicConfig()
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'

logger = logging.getLogger(__name__)

class SystemLauncher:
    """Enhanced system launcher with dependency checking and setup"""
    
    def __init__(self):
        self.python_executable = sys.executable
        self.is_windows = platform.system() == "Windows"
        self.project_root = Path(__file__).parent
        
    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        if sys.version_info < (3, 8):
            logger.error("[ERROR] Python 3.8+ is required. Current version: %s", sys.version)
            return False
        
        logger.info("[OK] Python version check passed: %s", sys.version.split([0])
        return True
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        logger.info("[SEARCH] Checking dependencies...")
        
        required_packages = []
            'langchain',
            'langchain-community',
            'docker',
            'redis',
            'psycopg2',
            'aiohttp',
            'websockets',
            'pyyaml',
            'psutil',
            'sqlalchemy'
        
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.debug(str(f"[OK] {package} - Found")
            except ImportError:
                missing_packages.append(package)
                logger.warning(str(f"[ERROR] {package} - Missing")
        
        if missing_packages:
            logger.error("[ERROR] Missing required packages: %s", ', '.join(missing_packages)
            logger.info("[INFO] Run: pip install -r requirements.txt")
            return False
        
        logger.info("[OK] All dependencies check passed")
        return True
    
    def check_docker(self) -> bool:
        """Check if Docker is available and running"""
        logger.info("🐳 Checking Docker...")
        
        try:
            result: str = subprocess.run(['docker', '--version'], )
                                  capture_output=True, text=True, timeout=10
            if result.returncode == 0:
                logger.info("[OK] Docker is available: %s", result.stdout.strip()
                
                # Check if Docker daemon is running
                result: str = subprocess.run(['docker', 'info'], )
                                      capture_output=True, text=True, timeout=10
                if result.returncode == 0:
                    logger.info("[OK] Docker daemon is running")
                    return True
                else:
                    logger.error("[ERROR] Docker daemon is not running")
                    logger.info("[INFO] Please start Docker Desktop or Docker service")
                    return False
            else:
                logger.error("[ERROR] Docker command failed")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("[ERROR] Docker command timed out")
            return False
        except FileNotFoundError:
            logger.error("[ERROR] Docker is not installed or not in PATH")
            logger.info("[INFO] Please install Docker: https://docs.docker.com/get-docker/")
            return False
    
    def check_services(self) -> Dict[str, bool]:
        """Check if required services are available"""
        logger.info("[SETUP] Checking required services...")
        
        services = {}
            'redis': self._check_service('redis', 6379),
            'postgres': self._check_service('postgres', 5432),
            'rabbitmq': self._check_service('rabbitmq', 5672)
        
        
        return services
    
    def _check_service(self, service_name: str, port: int) -> bool:
        """Check if a specific service is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result: str = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                logger.info(str(f"[OK] {service_name} service is available on port {port}")
                return True
            else:
                logger.warning(str(f"[WARN] {service_name} service is not available on port {port}")
                return False
                
        except Exception as e:
            logger.warning(str(f"[WARN] Could not check {service_name} service: {e}")
            return False
    
    async def start_services(self) -> bool:
        """Start required services using Docker"""
        logger.info("[INIT] Starting required services...")
        
        try:
            # Start services using the simple docker-compose
            compose_file = self.project_root / "docker-compose.simple.yml"
            
            if not compose_file.exists():
                logger.info("[LOG] Creating simple docker-compose file...")
                await self._create_simple_compose()
            
            # Start services
            cmd = ['docker', 'compose', '-f', str(compose_file), 'up', '-d']
            result: str = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("[OK] Services started successfully")
                
                # Wait for services to be ready
                logger.info("⏳ Waiting for services to be ready...")
                await asyncio.sleep(15)
                
                return True
            else:
                logger.error("[ERROR] Failed to start services: %s", result.stderr)
                return False
                
        except Exception as e:
            logger.error("[ERROR] Error starting services: %s", e)
            return False
    
    async def _create_simple_compose(self):
        """Create a simple docker-compose file for essential services"""
        compose_content = """version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: langchain-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
    command: redis-server --appendonly yes
    
  postgres:
    image: postgres:15-alpine
    container_name: langchain-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=langchain_mcp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  rabbitmq:
    image: rabbitmq:3-management
    container_name: langchain-rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=langchain
      - RABBITMQ_DEFAULT_PASS=langchain123
    restart: unless-stopped
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

volumes:
  postgres_data:
  rabbitmq_data:
"""
        
        compose_file = self.project_root / "docker-compose.simple.yml"
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        
        logger.info("[LOG] Simple docker-compose file created")
    
    def check_configuration(self) -> bool:
        """Check if configuration files exist and are valid"""
        logger.info("⚙️ Checking configuration...")
        
        config_file = self.project_root / "enhanced_coordinator_config.yaml"
        
        if not config_file.exists():
            logger.info("[LOG] Creating default configuration...")
            self._create_default_config()
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required sections
            required_sections = ['mcp_servers', 'llm', 'memory', 'monitoring']
            for section in required_sections:
                if section not in config:
                    logger.error(str(f"[ERROR] Missing configuration section: {section}")
                    return False
            
            logger.info("[OK] Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error("[ERROR] Configuration validation failed: %s", e)
            return False
    
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = {}
            'mcp_servers': {}
                'context7-mcp': {'port': 8001, 'capabilities': ['context', 'search']},
                'enhanced-copilot-mcp': {'port': 8002, 'capabilities': ['code', 'generation']},
                'blockchain-mcp': {'port': 8003, 'capabilities': ['blockchain', 'web3']},
                'price-oracle-mcp': {'port': 8004, 'capabilities': ['prices', 'market_data']},
                'dex-services-mcp': {'port': 8005, 'capabilities': ['dex', 'trading']},
                'flash-loan-mcp': {'port': 8006, 'capabilities': ['flash_loans', 'arbitrage']}
            },
            'llm': {'model': 'llama2', 'temperature': 0.7},
            'memory': {'type': 'summary_buffer', 'max_token_limit': 2000},
            'embeddings': {'model': 'sentence-transformers/all-MiniLM-L6-v2'},
            'monitoring': {'health_check_interval': 30, 'auto_restart_on_failure': True}
        
        
        config_file = self.project_root / "enhanced_coordinator_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        logger.info("[LOG] Default configuration created")
    
    async def launch_system(self) -> bool:
        """Launch the complete system"""
        logger.info("[INIT] Launching Enhanced LangChain MCP System...")
        
        try:
            # Import and run the complete integration system
            
            system = CompleteLangChainMCPSystem()
            
            # Initialize and start
            if await system.initialize():
                logger.info("[OK] System initialized successfully!")
                logger.info("[NETWORK] Dashboard will be available at: http://localhost:8000")
                logger.info("[SETUP] Press Ctrl+C to shutdown gracefully")
                
                await system.start_system()
                return True
            else:
                logger.error("[ERROR] System initialization failed")
                return False
                
        except Exception as e:
            logger.error("[ERROR] System launch failed: %s", e)
            return False
    
    async def run_checks_and_launch(self):
        """Run all checks and launch the system"""
        print("[INIT] Enhanced LangChain MCP System Launcher")
        print("=" * 50)
        
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Check dependencies
        if not self.check_dependencies():
            print("\n[INFO] Installing dependencies...")
            try:
                subprocess.run([self.python_executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], )
                             check=True
                logger.info("[OK] Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error("[ERROR] Failed to install dependencies: %s", e)
                return False
        
        # Check Docker
        if not self.check_docker():
            return False
        
        # Check services
        services = self.check_services()
        if not all(services.values()):
            logger.info("[INIT] Starting missing services...")
            if not await self.start_services():
                return False
            
            # Re-check services
            services = self.check_services()
            if not all(services.values()):
                logger.warning("[WARN] Some services are still not available, continuing anyway...")
        
        # Check configuration
        if not self.check_configuration():
            return False
        
        print("\n[OK] All checks passed! Launching system...")
        print("=" * 50)
        
        # Launch system
        return await self.launch_system()

async def main():
    """Main launcher function"""
    launcher = SystemLauncher()
    
    try:
        success = await launcher.run_checks_and_launch()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("[STOP] Launch cancelled by user")
        return 0
    except Exception as e:
        logger.error("[ERROR] Launcher error: %s", e)
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))