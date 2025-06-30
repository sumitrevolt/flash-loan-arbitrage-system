# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Dict, List, Any
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
"""
Docker Coordination System Launcher
===================================

This script launches the complete coordination system with:
- MCP Servers (21 servers)
- AI Agents (10 agents)
- LangChain coordination
- AutoGen multi-agent conversations
- Infrastructure services
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[]
        logging.FileHandler('coordination_launcher.log'),
        logging.StreamHandler()
    

logger = logging.getLogger(__name__)

class CoordinationSystemLauncher:
    """Launcher for the complete coordination system"""
    
    def __init__(self):
        self.docker_compose_file = "docker/docker-compose-self-healing.yml"
        self.env_file = ".env"
        self.services_status = {}
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        try:
            # Check if Docker is installed and running
            result = subprocess.run(['docker', '--version'], )
                                  capture_output=True, text=True
            if result.returncode != 0:
                logger.error("Docker is not installed or not running")
                return False
                
            # Check if Docker Compose is available
            result = subprocess.run(['docker', 'compose', 'version'], )
                                  capture_output=True, text=True
            if result.returncode != 0:
                logger.error("Docker Compose is not available")
                return False
                
            # Check if required files exist
            required_files = []
                self.docker_compose_file,
                'docker_coordination_system.py',
                'unified_mcp_config.json',
                'ai_agents_config.json',
                'requirements-coordination.txt'
            
            
            missing_files = []
            for file_path in required_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
                    
            if missing_files:
                logger.error(str(f"Missing required files: {missing_files}")
                return False
                
            logger.info("All prerequisites met")
            return True
            
        except Exception as e:
            logger.error(str(f"Error checking prerequisites: {e}")
            return False
            
    def create_environment_file(self):
        """Create or update the environment file"""
        try:
            env_content = """# Docker Coordination System Environment Variables

# Infrastructure
REDIS_URL=redis://coordination_redis:6379
RABBITMQ_URL=amqp://coordination:coordination_pass@coordination_rabbitmq:5672/coordination
POSTGRES_URL=postgresql://coordination:coordination_pass@coordination_postgres:5432/coordination

# Blockchain Configuration
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRAGE_PRIVATE_KEY=your_private_key_here
CONTRACT_ADDRESS=0x35791D283Ec6eeF6C7687026CaF026C5F84C7c15

# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OLLAMA_HOST=http://coordination_ollama:11434

# System Configuration
MIN_PROFIT_USD=3.0
MAX_PROFIT_USD=30.0
MAX_GAS_PRICE_GWEI=50.0
LOG_LEVEL=INFO

# Feature Flags
LANGCHAIN_ENABLED=true
AUTOGEN_ENABLED=true
MCP_SERVERS_COUNT=21
AI_AGENTS_COUNT=10

# GitHub Integration (optional)
GITHUB_TOKEN=your_github_token_here
"""
            
            with open(self.env_file, 'w') as f:
                f.write(env_content)
                
            logger.info("Environment file created/updated")
            
        except Exception as e:
            logger.error(str(f"Error creating environment file: {e}")
            
    def build_docker_images(self) -> bool:
        """Build all Docker images"""
        try:
            logger.info("Building Docker images...")
            
            # Build images using Docker Compose
            cmd = []
                'docker', 'compose', 
                '-f', self.docker_compose_file,
                'build', '--parallel'
            
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Docker images built successfully")
                return True
            else:
                logger.error(str(f"Error building Docker images: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(str(f"Error building Docker images: {e}")
            return False
            
    def start_infrastructure(self) -> bool:
        """Start infrastructure services first"""
        try:
            logger.info("Starting infrastructure services...")
            
            infrastructure_services = []
                'redis',
                'rabbitmq', 
                'postgres',
                'ollama'
            
            
            for service in infrastructure_services:
                cmd = []
                    'docker', 'compose',
                    '-f', self.docker_compose_file,
                    'up', '-d', service
                
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(str(f"Started {service} successfully")
                    self.services_status[service] = 'running'
                else:
                    logger.error(str(f"Error starting {service}: {result.stderr}")
                    self.services_status[service] = 'failed'
                    
            # Wait for infrastructure to be ready
            logger.info("Waiting for infrastructure services to be ready...")
            time.sleep(30)
            
            return all(status == 'running' for status in self.services_status.values())
            
        except Exception as e:
            logger.error(str(f"Error starting infrastructure: {e}")
            return False
            
    def start_mcp_servers(self) -> bool:
        """Start MCP servers"""
        try:
            logger.info("Starting MCP servers...")
            
            mcp_services = []
                'mcp_price_feed',
                'mcp_flash_loan',
                'mcp_dex_aggregator',
                'mcp_evm_interaction'
            
            
            for service in mcp_services:
                cmd = []
                    'docker', 'compose',
                    '-f', self.docker_compose_file,
                    'up', '-d', service
                
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(str(f"Started {service} successfully")
                    self.services_status[service] = 'running'
                else:
                    logger.error(str(f"Error starting {service}: {result.stderr}")
                    self.services_status[service] = 'failed'
                    
            # Wait for MCP servers to initialize
            time.sleep(20)
            return True
            
        except Exception as e:
            logger.error(str(f"Error starting MCP servers: {e}")
            return False
            
    def start_ai_agents(self) -> bool:
        """Start AI agents"""
        try:
            logger.info("Starting AI agents...")
            
            agent_services = []
                'agent_arbitrage_detector',
                'agent_risk_manager',
                'agent_flash_loan_optimizer',
                'agent_transaction_executor',
                'agent_market_analyzer',
                'agent_route_optimizer',
                'agent_gas_optimizer',
                'agent_liquidity_monitor',
                'agent_security_analyst',
                'agent_compliance_checker'
            
            
            for service in agent_services:
                cmd = []
                    'docker', 'compose',
                    '-f', self.docker_compose_file,
                    'up', '-d', service
                
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(str(f"Started {service} successfully")
                    self.services_status[service] = 'running'
                else:
                    logger.error(str(f"Error starting {service}: {result.stderr}")
                    self.services_status[service] = 'failed'
                    
            # Wait for agents to initialize
            time.sleep(15)
            return True
            
        except Exception as e:
            logger.error(str(f"Error starting AI agents: {e}")
            return False
            
    def start_coordination_services(self) -> bool:
        """Start coordination services (LangChain, AutoGen, main orchestrator)"""
        try:
            logger.info("Starting coordination services...")
            
            coordination_services = []
                'langchain_coordinator',
                'autogen_system',
                'coordination_orchestrator'
            
            
            for service in coordination_services:
                cmd = []
                    'docker', 'compose',
                    '-f', self.docker_compose_file,
                    'up', '-d', service
                
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(str(f"Started {service} successfully")
                    self.services_status[service] = 'running'
                else:
                    logger.error(str(f"Error starting {service}: {result.stderr}")
                    self.services_status[service] = 'failed'
                    
            # Wait for coordination services to initialize
            time.sleep(25)
            return True
            
        except Exception as e:
            logger.error(str(f"Error starting coordination services: {e}")
            return False
            
    def start_monitoring_services(self) -> bool:
        """Start monitoring and dashboard services"""
        try:
            logger.info("Starting monitoring services...")
            
            monitoring_services = []
                'coordination_dashboard',
                'grafana',
                'prometheus',
                'health_monitor'
            
            
            for service in monitoring_services:
                cmd = []
                    'docker', 'compose',
                    '-f', self.docker_compose_file,
                    'up', '-d', service
                
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(str(f"Started {service} successfully")
                    self.services_status[service] = 'running'
                else:
                    logger.error(str(f"Error starting {service}: {result.stderr}")
                    self.services_status[service] = 'failed'
                    
            return True
            
        except Exception as e:
            logger.error(str(f"Error starting monitoring services: {e}")
            return False
            
    def check_system_health(self) -> Dict[str, Any]:
        """Check the health of all services"""
        try:
            logger.info("Checking system health...")
            
            # Get container status
            cmd = []
                'docker', 'compose',
                '-f', self.docker_compose_file,
                'ps', '--format', 'json'
            
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        containers.append(json.loads(line))
                        
                health_report = {}
                    'total_containers': len(containers),
                    'running_containers': len([c for c in containers if c.get('State') == 'running']),
                    'healthy_containers': len([c for c in containers if 'healthy' in c.get('Health', '').lower()]),
                    'services_status': self.services_status,
                    'containers': containers
                
                
                return health_report
            else:
                logger.error("Error checking system health")
                return {'error': result.stderr}
                
        except Exception as e:
            logger.error(str(f"Error checking system health: {e}")
            return {'error': str(e)}
            
    def display_system_info(self):
        """Display system information and access URLs"""
        info = f"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                          DOCKER COORDINATION SYSTEM                                  ║
║                                   STARTED                                            ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                      ║
║  [NETWORK] Web Interfaces:                                                                  ║
║     • Main Dashboard:        http://localhost:8080                                  ║
║     • Coordination API:      http://localhost:8000                                  ║
║     • LangChain Coordinator: http://localhost:8001                                  ║
║     • AutoGen System:        http://localhost:8002                                  ║
║     • Grafana Monitoring:    http://localhost:3000 (admin/admin)                   ║
║     • RabbitMQ Management:   http://localhost:15672 (coordination/coordination_pass)║
║                                                                                      ║
║  [SETUP] Infrastructure:                                                                  ║
║     • Redis:                 localhost:6379                                         ║
║     • PostgreSQL:            localhost:5432                                         ║
║     • RabbitMQ:              localhost:5672                                         ║
║     • Ollama:                localhost:11434                                        ║
║                                                                                      ║
║  🤖 MCP Servers:                                                                     ║
║     • Price Feed:            http://localhost:8100                                  ║
║     • Flash Loan:            http://localhost:8101                                  ║
║     • DEX Aggregator:        http://localhost:8102                                  ║
║     • EVM Interaction:       http://localhost:8103                                  ║
║                                                                                      ║
║  [TASK] AI Agents:                                                                       ║
║     • Arbitrage Detector:    http://localhost:9001                                  ║
║     • Risk Manager:          http://localhost:9002                                  ║
║     • Flash Loan Optimizer:  http://localhost:9003                                  ║
║     • Transaction Executor:  http://localhost:9004                                  ║
║     • Market Analyzer:       http://localhost:9005                                  ║
║     • Route Optimizer:       http://localhost:9006                                  ║
║     • Gas Optimizer:         http://localhost:9007                                  ║
║     • Liquidity Monitor:     http://localhost:9008                                  ║
║     • Security Analyst:      http://localhost:9009                                  ║
║     • Compliance Checker:    http://localhost:9010                                  ║
║                                                                                      ║
║  [METRICS] Monitoring:                                                                      ║
║     • Prometheus:            http://localhost:9090                                  ║
║                                                                                      ║
║  [LOG] Logs:                                                                            ║
║     • View logs: docker compose -f {self.docker_compose_file} logs -f              ║
║     • Health check: python coordination_launcher.py --health                       ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

📌 System is ready for coordination between MCP servers, AI agents, LangChain, and AutoGen!

To coordinate tasks, send POST requests to http://localhost:8000/coordinate with task descriptions.

Example:
curl -X POST http://localhost:8000/coordinate \\
  -H "Content-Type: application/json" \\
  -d '{{"description": "Analyze arbitrage opportunities and optimize flash loan strategy"}}'
"""
        print(info)
        
    def launch_system(self):
        """Launch the complete coordination system"""
        try:
            logger.info("Starting Docker Coordination System...")
            
            # Step 1: Check prerequisites
            if not self.check_prerequisites():
                logger.error("Prerequisites not met. Exiting.")
                return False
                
            # Step 2: Create environment file
            self.create_environment_file()
            
            # Step 3: Build Docker images
            if not self.build_docker_images():
                logger.error("Failed to build Docker images. Exiting.")
                return False
                
            # Step 4: Start infrastructure
            if not self.start_infrastructure():
                logger.error("Failed to start infrastructure. Exiting.")
                return False
                
            # Step 5: Start MCP servers
            if not self.start_mcp_servers():
                logger.error("Failed to start MCP servers. Continuing...")
                
            # Step 6: Start AI agents
            if not self.start_ai_agents():
                logger.error("Failed to start AI agents. Continuing...")
                
            # Step 7: Start coordination services
            if not self.start_coordination_services():
                logger.error("Failed to start coordination services. Continuing...")
                
            # Step 8: Start monitoring
            if not self.start_monitoring_services():
                logger.error("Failed to start monitoring services. Continuing...")
                
            # Step 9: Wait for all services to stabilize
            logger.info("Waiting for all services to stabilize...")
            time.sleep(60)
            
            # Step 10: Check system health
            health_report = self.check_system_health()
            logger.info(str(f"System health: {health_report}")
            
            # Step 11: Display system information
            self.display_system_info()
            
            logger.info("Docker Coordination System launched successfully!")
            return True
            
        except Exception as e:
            logger.error(str(f"Error launching system: {e}")
            return False
            
    def stop_system(self):
        """Stop the coordination system"""
        try:
            logger.info("Stopping Docker Coordination System...")
            
            cmd = []
                'docker', 'compose',
                '-f', self.docker_compose_file,
                'down', '-v'
            
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("System stopped successfully")
            else:
                logger.error(str(f"Error stopping system: {result.stderr}")
                
        except Exception as e:
            logger.error(str(f"Error stopping system: {e}")

def main():
    """Main function"""
    launcher = CoordinationSystemLauncher()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--health':
            health_report = launcher.check_system_health()
            print(json.dumps(health_report, indent=2, ensure_ascii=True, default=str))
            return
        elif sys.argv[1] == '--stop':
            launcher.stop_system()
            return
        elif sys.argv[1] == '--info':
            launcher.display_system_info()
            return
            
    # Launch the system
    success = launcher.launch_system()
    
    if success:
        print("\n[OK] System launched successfully!")
        print("Press Ctrl+C to stop the system")
        
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[STOP] Stopping system...")
            launcher.stop_system()
            print("[OK] System stopped")
    else:
        print("\n[ERROR] Failed to launch system")
        sys.exit(1)

if __name__ == "__main__":
    main()