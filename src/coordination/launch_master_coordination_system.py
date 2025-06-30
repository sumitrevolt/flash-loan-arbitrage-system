# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
            import shutil
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import time
"""
Master Flash Loan Arbitrage System Launcher
==========================================

This script launches the complete flash loan arbitrage system with:
- 80+ MCP Servers
- 10+ AI Agents
- LangChain coordination
- AutoGen multi-agent systems
- Self-healing capabilities
- Real-time monitoring and dashboard
- Docker orchestration

Author: AI Assistant
Version: 1.0.0
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
        logging.FileHandler('master_coordination_launcher.log'),
        logging.StreamHandler()
    

logger = logging.getLogger(__name__)

class MasterCoordinationLauncher:
    """Master launcher for the complete flash loan arbitrage system"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.docker_dir = self.base_dir / "docker"
        self.is_running = False
        self.launched_services = []
        self.system_status = {}
        
        # Service URLs for monitoring
        self.service_urls = {}
            'master_orchestrator': 'http://localhost:8000',
            'dashboard': 'http://localhost:8080',
            'langchain_coordinator': 'http://localhost:8001',
            'autogen_system': 'http://localhost:8002',
            'mcp_price_feed': 'http://localhost:8100',
            'mcp_arbitrage': 'http://localhost:8101',
            'mcp_flash_loan': 'http://localhost:8102',
            'ai_arbitrage_detector': 'http://localhost:9001',
            'ai_risk_manager': 'http://localhost:9002',
            'self_healing_agent': 'http://localhost:8300',
            'health_monitor': 'http://localhost:8400'
        
        
    def display_banner(self):
        """Display system banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        [INIT] MASTER FLASH LOAN ARBITRAGE COORDINATION SYSTEM [INIT]                ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  💎 80+ MCP Servers    🤖 10+ AI Agents    🧠 LangChain/AutoGen     │    ║
║  │  [SETUP] Self-Healing       [METRICS] Real-time Dashboard   🛡️ Security          │    ║
║  │  [FAST] Flash Loans        💰 Arbitrage Trading     [SYNC] 24/7 Operation     │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  [TASK] Autonomous Multi-Chain Arbitrage with Advanced AI Coordination          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def check_system_requirements(self) -> bool:
        """Check if system requirements are met"""
        print("\n[SEARCH] CHECKING SYSTEM REQUIREMENTS")
        print("=" * 80)
        
        requirements_met = True
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] Docker: {result.stdout.strip()}")
            else:
                print("[ERROR] Docker not found or not working")
                requirements_met = False
        except FileNotFoundError:
            print("[ERROR] Docker not installed")
            requirements_met = False
            
        # Check Docker Compose
        try:
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] Docker Compose: {result.stdout.strip()}")
            else:
                print("[ERROR] Docker Compose not found or not working")
                requirements_met = False
        except FileNotFoundError:
            print("[ERROR] Docker Compose not available")
            requirements_met = False
            
        # Check Python version
        python_version = sys.version.split()[0]
        if sys.version_info >= (3, 11):
            print(f"[OK] Python: {python_version}")
        else:
            print(f"[WARN]  Python: {python_version} (Recommended: 3.11+)")
            
        # Check available disk space
        try:
            total, used, free = shutil.disk_usage('.')
            free_gb = free // (1024**3)
            if free_gb >= 10:
                print(f"[OK] Disk Space: {free_gb}GB available")
            else:
                print(f"[WARN]  Disk Space: {free_gb}GB available (Recommended: 10GB+)")
        except:
            print("[WARN]  Could not check disk space")
            
        # Check required files
        required_files = []
            'docker/docker-compose-master.yml',
            'docker/Dockerfile.mcp-enhanced',
            'docker/Dockerfile.agent',
            'docker/Dockerfile.coordination',
            'requirements-coordination-fixed.txt'
        
        
        for file_path in required_files:
            if (self.base_dir / file_path).exists():
                print(f"[OK] {file_path}")
            else:
                print(f"[ERROR] Missing: {file_path}")
                requirements_met = False
                
        if requirements_met:
            print("\n[CELEBRATE] All system requirements met!")
        else:
            print("\n[ERROR] Some requirements not met. Please install missing dependencies.")
            
        return requirements_met
        
    def create_environment_file(self):
        """Create .env file with default values"""
        env_file = self.base_dir / ".env"
        
        env_content = f"""# Flash Loan Arbitrage System Environment Variables
# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}

# Blockchain Configuration
POLYGON_RPC_URL=https://polygon-rpc.com
ETHEREUM_RPC_URL=https://eth.llamarpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
OPTIMISM_RPC_URL=https://mainnet.optimism.io

# Trading Configuration  
ARBITRAGE_PRIVATE_KEY=
CONTRACT_ADDRESS=0x35791D283Ec6eeF6C7687026CaF026C5F84C7c15
MIN_PROFIT_USD=3.0
MAX_PROFIT_USD=30.0
MAX_GAS_PRICE_GWEI=50.0

# API Keys (Optional - for enhanced features)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
COINGECKO_API_KEY=
ETHERSCAN_API_KEY=
POLYGONSCAN_API_KEY=

# GitHub Token for enhanced coordination
GITHUB_TOKEN=

# Database Configuration (Optional - uses Docker defaults if not set)
POSTGRES_URL=
REDIS_URL=
RABBITMQ_URL=

# Monitoring Configuration
GRAFANA_ADMIN_PASSWORD=admin
PROMETHEUS_RETENTION=15d

# System Configuration
LOG_LEVEL=INFO
SYSTEM_ENV=production
DEBUG=false
"""
        
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write(env_content)
            print(f"[OK] Created environment file: {env_file}")
        else:
            print(f"[OK] Environment file exists: {env_file}")
            
    def setup_directories(self):
        """Setup required directories"""
        directories = []
            'docker/volumes/postgres_data',
            'docker/volumes/redis_data', 
            'docker/volumes/rabbitmq_data',
            'docker/volumes/grafana_data',
            'docker/volumes/prometheus_data',
            'docker/volumes/ollama_data',
            'logs',
            'data'
        
        
        print("\n📁 SETTING UP DIRECTORIES")
        print("=" * 80)
        
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"[OK] {directory}")
            
    async def start_docker_services(self):
        """Start Docker services using docker-compose"""
        print("\n🐳 STARTING DOCKER SERVICES")
        print("=" * 80)
        
        compose_file = self.docker_dir / "docker-compose-master.yml"
        
        if not compose_file.exists():
            print(f"[ERROR] Docker compose file not found: {compose_file}")
            return False
            
        try:
            # Stop any existing services
            print("[STOP] Stopping existing services...")
            subprocess.run([)]
                'docker', 'compose', '-f', str(compose_file), 'down'
            ], cwd=self.base_dir, capture_output=True
            
            # Pull latest images
            print("📥 Pulling latest images...")
            result = subprocess.run([)]
                'docker', 'compose', '-f', str(compose_file), 'pull'
            ], cwd=self.base_dir, capture_output=True, text=True
            
            # Build custom images
            print("🔨 Building custom images...")
            result = subprocess.run([)]
                'docker', 'compose', '-f', str(compose_file), 'build'
            ], cwd=self.base_dir, capture_output=True, text=True
            
            if result.returncode != 0:
                print(f"[WARN]  Build warnings: {result.stderr}")
            
            # Start services
            print("[INIT] Starting all services...")
            result = subprocess.run([)]
                'docker', 'compose', '-f', str(compose_file), 'up', '-d'
            ], cwd=self.base_dir, capture_output=True, text=True
            
            if result.returncode == 0:
                print("[OK] Docker services started successfully")
                self.is_running = True
                return True
            else:
                print(f"[ERROR] Failed to start services: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error starting Docker services: {e}")
            return False
            
    async def wait_for_services(self):
        """Wait for all services to be healthy"""
        print("\n⏳ WAITING FOR SERVICES TO BE READY")
        print("=" * 80)
        
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        services_to_check = []
            ('Infrastructure', ['redis', 'rabbitmq', 'postgres']),
            ('MCP Servers', ['mcp_price_feed', 'mcp_arbitrage', 'mcp_flash_loan']),
            ('AI Agents', ['ai_arbitrage_detector', 'ai_risk_manager']),
            ('Coordination', ['master_orchestrator', 'langchain_coordinator'])
        
        
        while time.time() - start_time < max_wait_time:
            all_healthy = True
            
            for category, services in services_to_check:
                print(f"\n[SEARCH] Checking {category}:")
                for service in services:
                    if await self.check_service_health(service):
                        print(f"  [OK] {service}")
                    else:
                        print(f"  ⏳ {service} (starting...)")
                        all_healthy = False
                        
            if all_healthy:
                print(f"\n[CELEBRATE] All services are healthy! (took {time.time() - start_time:.1f}s)")
                return True
                
            await asyncio.sleep(10)
            
        print(f"\n[WARN]  Timeout waiting for services (after {max_wait_time}s)")
        return False
        
    async def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            # Use docker health check
            result = subprocess.run([)]
                'docker', 'ps', '--filter', f'name={service_name}', 
                '--format', 'table {{.Names}}\t{{.Status}}'
            ], capture_output=True, text=True
            
            if service_name in result.stdout and 'healthy' in result.stdout:
                return True
            elif service_name in result.stdout and 'Up' in result.stdout:
                return True  # Service is up but may not have health check
                
        except Exception as e:
            logger.debug(str(f"Health check error for {service_name}: {e}")
            
        return False
        
    def display_service_status(self):
        """Display current service status"""
        print("\n[METRICS] SERVICE STATUS OVERVIEW")
        print("=" * 80)
        
        try:
            result = subprocess.run([)]
                'docker', 'ps', '--format', 
                'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
            ], capture_output=True, text=True
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'flashloan_' in line or 'mcp_' in line or 'ai_agent_' in line:
                        print(f"  {line}")
            else:
                print("[ERROR] Could not retrieve service status")
                
        except Exception as e:
            print(f"[ERROR] Error checking service status: {e}")
            
    def display_access_urls(self):
        """Display access URLs for the system"""
        print("\n[NETWORK] SYSTEM ACCESS URLS")
        print("=" * 80)
        
        urls = {}
            '🎛️  Master Dashboard': 'http://localhost:8080',
            '[INIT] Master Orchestrator': 'http://localhost:8000',
            '🧠 LangChain Coordinator': 'http://localhost:8001',
            '🤝 AutoGen System': 'http://localhost:8002',
            '💰 Price Feed Server': 'http://localhost:8100',
            '[FAST] Arbitrage Server': 'http://localhost:8101',
            '💸 Flash Loan Server': 'http://localhost:8102',
            '[SETUP] Self-Healing Agent': 'http://localhost:8300',
            '[METRICS] Health Monitor': 'http://localhost:8400',
            '🐰 RabbitMQ Management': 'http://localhost:15672',
            '[GROWTH] Grafana Dashboard': 'http://localhost:3000',
            '[METRICS] Prometheus Metrics': 'http://localhost:9090'
        
        
        for name, url in urls.items():
            print(f"  {name}: {url}")
            
    def display_usage_instructions(self):
        """Display usage instructions"""
        instructions = """
[TASK] SYSTEM USAGE INSTRUCTIONS
========================================

📋 Getting Started:
  1. Open the Master Dashboard: http://localhost:8080
  2. Monitor system health and performance
  3. Check the Master Orchestrator API: http://localhost:8000
  4. View logs: docker logs -f master_orchestrator

💰 Trading Operations:
  • The system automatically detects arbitrage opportunities
  • Flash loan execution happens automatically when profitable
  • Monitor trades via the dashboard or orchestrator API
  • Adjust settings in the .env file

[SETUP] Management:
  • View all services: docker ps
  • Check logs: docker logs <service_name>
  • Restart a service: docker restart <service_name>
  • Stop system: Ctrl+C or run this script with --stop

[METRICS] Monitoring:
  • Real-time dashboard: http://localhost:8080
  • Grafana metrics: http://localhost:3000
  • RabbitMQ management: http://localhost:15672
  • System health: http://localhost:8400

🛡️  Security:
  • Set ARBITRAGE_PRIVATE_KEY in .env file
  • Use secure RPC endpoints
  • Monitor for unusual activity
  • Keep system updated

[WARN]  Important Notes:
  • Ensure sufficient funds for gas fees
  • Test with small amounts first
  • Monitor market conditions
  • Keep private keys secure
        """
        print(instructions)
        
    async def monitor_system(self):
        """Monitor system and provide real-time status"""
        print("\n[SYNC] MONITORING SYSTEM (Press Ctrl+C to stop)")
        print("=" * 80)
        
        try:
            while self.is_running:
                # Check service health
                healthy_services = 0
                total_services = len(self.service_urls)
                
                for service_name in self.service_urls:
                    if await self.check_service_health(service_name):
                        healthy_services += 1
                
                health_percentage = (healthy_services / total_services) * 100
                
                # Display status
                current_time = time.strftime('%H:%M:%S')
                print(f"\r[{current_time}] System Health: {healthy_services}/{total_services} services ({health_percentage:.1f}%)", end='', flush=True)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            print("\n\n[STOP] Monitoring stopped by user")
            
    async def stop_system(self):
        """Stop all system services"""
        print("\n[STOP] STOPPING SYSTEM")
        print("=" * 80)
        
        compose_file = self.docker_dir / "docker-compose-master.yml"
        
        try:
            result = subprocess.run([)]
                'docker', 'compose', '-f', str(compose_file), 'down'
            ], cwd=self.base_dir, capture_output=True, text=True
            
            if result.returncode == 0:
                print("[OK] All services stopped successfully")
            else:
                print(f"[WARN]  Some services may still be running: {result.stderr}")
                
            self.is_running = False
            
        except Exception as e:
            print(f"[ERROR] Error stopping services: {e}")
            
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n[STOP] Received signal {signum}, stopping system...")
            asyncio.create_task(self.stop_system())
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def run_master_system(self):
        """Run the complete master coordination system"""
        try:
            # Display banner
            self.display_banner()
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Check requirements
            if not self.check_system_requirements():
                return False
                
            # Setup environment
            self.create_environment_file()
            self.setup_directories()
            
            # Start services
            if not await self.start_docker_services():
                return False
                
            # Wait for services
            if not await self.wait_for_services():
                print("[WARN]  Some services may not be ready, but continuing...")
                
            # Display status and URLs
            self.display_service_status()
            self.display_access_urls()
            self.display_usage_instructions()
            
            # Start monitoring
            await self.monitor_system()
            
            return True
            
        except Exception as e:
            logger.error(str(f"[ERROR] System error: {e}")
            return False
        finally:
            if self.is_running:
                await self.stop_system()

async def main():
    """Main function"""
    launcher = MasterCoordinationLauncher()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--stop':
            await launcher.stop_system()
            return
        elif sys.argv[1] == '--status':
            launcher.display_service_status()
            return
        elif sys.argv[1] == '--help':
            print(""")
Flash Loan Arbitrage Master Coordination System

Usage:
  python launch_master_coordination_system.py           # Start the system
  python launch_master_coordination_system.py --stop    # Stop the system
  python launch_master_coordination_system.py --status  # Show status
  python launch_master_coordination_system.py --help    # Show this help
            """
            return
    
    # Run the system
    success = await launcher.run_master_system()
    
    if success:
        print("\n[CELEBRATE] Master coordination system completed successfully!")
    else:
        print("\n[ERROR] Master coordination system encountered errors.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 System shutdown requested by user")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        sys.exit(1)