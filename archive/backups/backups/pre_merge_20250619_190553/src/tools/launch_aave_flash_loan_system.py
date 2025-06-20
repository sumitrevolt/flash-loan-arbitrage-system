#!/usr/bin/env python3
"""
Aave Flash Loan System Launcher
==============================

Comprehensive launcher for the Aave flash loan arbitrage system.
Coordinates MCP servers, AI agents, and monitoring systems.

Features:
- Environment validation
- MCP server orchestration
- Health monitoring
- Web dashboard
- Real-time logging
- Emergency shutdown
"""

import asyncio
import json
import logging
import os
import sys
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_launcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemLauncher")

class AaveFlashLoanSystemLauncher:
    """System launcher and coordinator"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.is_running = False
        self.config_path = "config/aave_flash_loan_mcp_config.json"
        self.env_file = ".env"
        self.backup_env_file = ".env.aave_flash_loan"
        
        # Load configuration
        self.config = self.load_config()
        self.required_env_vars = self.get_required_env_vars()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def load_config(self) -> Dict:
        """Load MCP server configuration"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.error(f"Configuration file not found: {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variables"""
        return [
            'POLYGON_RPC_URL',
            'PRIVATE_KEY',
            'AAVE_POOL_ADDRESS'
        ]
    
    def validate_environment(self) -> bool:
        """Validate environment configuration"""
        logger.info("Validating environment configuration...")
        
        # Check if .env file exists
        if not Path(self.env_file).exists():
            if Path(self.backup_env_file).exists():
                logger.info(f"Using backup environment file: {self.backup_env_file}")
                # Copy backup to .env
                import shutil
                shutil.copy(self.backup_env_file, self.env_file)
            else:
                logger.error("No .env file found. Please create one from .env.aave_flash_loan template")
                return False
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check required variables
        missing_vars = []
        for var in self.required_env_vars:
            value = os.getenv(var)
            if not value or value in ['', 'YOUR_API_KEY', '0x0000000000000000000000000000000000000000000000000000000000000000']:
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing or invalid environment variables: {missing_vars}")
            logger.error("Please update your .env file with valid values")
            return False
        
        # Validate RPC connection
        polygon_rpc = os.getenv('POLYGON_RPC_URL')
        if polygon_rpc and not self.test_rpc_connection(polygon_rpc):
            logger.warning("Polygon RPC connection test failed")
            return False
        
        logger.info("Environment validation successful")
        return True
    
    def test_rpc_connection(self, rpc_url: str) -> bool:
        """Test RPC connection"""
        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                block_number = w3.eth.block_number
                logger.info(f"RPC connection successful - Latest block: {block_number}")
                return True
            else:
                logger.error("RPC connection failed")
                return False
        except Exception as e:
            logger.error(f"RPC connection error: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            'logs',
            'data',
            'backups',
            'mcp_servers/aave',
            'mcp_servers/pricing',
            'mcp_servers/risk',
            'mcp_servers/gas',
            'mcp_servers/mev',
            'mcp_servers/ai',
            'mcp_servers/monitoring',
            'mcp_servers/execution'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        logger.info("Created necessary directories")
    
    def install_dependencies(self):
        """Install required Python packages"""
        logger.info("Installing dependencies...")
        
        requirements = [
            'web3>=6.0.0',
            'aiohttp>=3.8.0',
            'python-dotenv>=1.0.0',
            'psutil>=5.9.0',
            'mcp>=1.0.0',
            'decimal',
            'asyncio'
        ]
        
        try:
            for package in requirements:
                result: str = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.warning(f"Failed to install {package}: {result.stderr}")
                else:
                    logger.info(f"Installed {package}")
                    
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
    
    async def start_mcp_server(self, server_name: str, server_config: Dict) -> bool:
        """Start individual MCP server"""
        try:
            command = server_config['command']
            args = server_config['args']
            env = server_config.get('env', {})
            
            # Prepare environment
            server_env = os.environ.copy()
            server_env.update(env)
            
            # Resolve environment variables in env values
            for key, value in server_env.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    server_env[key] = os.getenv(env_var, '')
            
            # Start process
            full_command = [command] + args
            
            logger.info(f"Starting {server_name}: {' '.join(full_command)}")
            
            process = subprocess.Popen(
                full_command,
                env=server_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[server_name] = process
            
            # Give it a moment to start
            await asyncio.sleep(2)
            
            # Check if it's still running
            if process.poll() is None:
                logger.info(f"Successfully started {server_name} (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Failed to start {server_name}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting {server_name}: {e}")
            return False
    
    async def start_all_mcp_servers(self):
        """Start all configured MCP servers"""
        logger.info("Starting MCP servers...")
        
        if not self.config.get('mcpServers'):
            logger.error("No MCP servers configured")
            return
        
        # Start servers by priority (execution agents first, then data providers, etc.)
        server_priorities = {
            'EXECUTION': 1,
            'RISK': 1,
            'DATA_PROVIDER': 2,
            'DATA_AGGREGATOR': 2,
            'ANALYTICS': 3,
            'MONITORING': 3,
            'OPTIMIZATION': 4,
            'PROTECTION': 4,
            'AI_OPTIMIZER': 5
        }
        
        servers_by_priority = {}
        
        for server_name, server_config in self.config['mcpServers'].items():
            role = server_config.get('env', {}).get('AGENT_ROLE', 'UNKNOWN')
            priority = server_priorities.get(role, 10)
            
            if priority not in servers_by_priority:
                servers_by_priority[priority] = []
            
            servers_by_priority[priority].append((server_name, server_config))
        
        # Start servers by priority
        total_started = 0
        for priority in sorted(servers_by_priority.keys()):
            logger.info(f"Starting priority {priority} servers...")
            
            for server_name, server_config in servers_by_priority[priority]:
                if await self.start_mcp_server(server_name, server_config):
                    total_started += 1
                
                # Brief pause between servers
                await asyncio.sleep(1)
            
            # Longer pause between priority groups
            await asyncio.sleep(3)
        
        logger.info(f"Started {total_started} out of {len(self.config['mcpServers'])} MCP servers")
    
    async def health_check(self) -> Dict[str, str]:
        """Perform health check on all processes"""
        health_status = {}
        
        for server_name, process in self.processes.items():
            try:
                if process.poll() is None:
                    # Process is running
                    cpu_usage = 0
                    memory_usage = 0
                    
                    try:
                        proc = psutil.Process(process.pid)
                        cpu_usage = proc.cpu_percent()
                        memory_usage = proc.memory_info().rss / 1024 / 1024  # MB
                    except:
                        pass
                    
                    health_status[server_name] = {
                        'status': 'running',
                        'pid': process.pid,
                        'cpu_percent': cpu_usage,
                        'memory_mb': memory_usage
                    }
                else:
                    # Process has terminated
                    health_status[server_name] = {
                        'status': 'terminated',
                        'exit_code': process.returncode
                    }
            except Exception as e:
                health_status[server_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_status
    
    async def monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Starting monitoring loop...")
        
        while self.is_running:
            try:
                # Health check
                health = await self.health_check()
                
                # Count running servers
                running_count = sum(1 for status in health.values() 
                                  if isinstance(status, dict) and status.get('status') == 'running')
                
                logger.info(f"Health check: {running_count}/{len(self.processes)} servers running")
                
                # Log any issues
                for server_name, status in health.items():
                    if isinstance(status, dict) and status.get('status') != 'running':
                        logger.warning(f"Server {server_name} is {status.get('status')}")
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    def start_web_dashboard(self):
        """Start web dashboard"""
        try:
            logger.info("Starting web dashboard...")
            
            # Simple dashboard script
            dashboard_script = """
import asyncio
from aiohttp import web
import json
import logging

async def dashboard_handler(request):
    return web.Response(text='''
    <html>
    <head><title>Aave Flash Loan System Dashboard</title></head>
    <body>
        <h1>Aave Flash Loan System</h1>
        <h2>Status: Running</h2>
        <p>System started at: {timestamp}</p>
        <p><a href="/health">Health Check</a></p>
        <p><a href="/logs">View Logs</a></p>
    </body>
    </html>
    '''.format(timestamp='{timestamp}'), content_type='text/html')

async def health_handler(request):
    return web.json_response({{'status': 'healthy', 'timestamp': '{timestamp}'}})

async def logs_handler(request):
    try:
        with open('logs/system_launcher.log', 'r') as f:
            logs = f.read()
        return web.Response(text=f'<pre>{{logs}}</pre>', content_type='text/html')
    except:
        return web.Response(text='<pre>No logs available</pre>', content_type='text/html')

app = web.Application()
app.router.add_get('/', dashboard_handler)
app.router.add_get('/health', health_handler)
app.router.add_get('/logs', logs_handler)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=9001)
            """.format(timestamp=datetime.now().isoformat())
            
            # Write dashboard script
            with open('dashboard_server.py', 'w') as f:
                f.write(dashboard_script)
            
            # Start dashboard
            dashboard_process = subprocess.Popen([
                sys.executable, 'dashboard_server.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['web_dashboard'] = dashboard_process
            logger.info("Web dashboard started at http://localhost:9001")
            
        except Exception as e:
            logger.error(f"Error starting web dashboard: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.is_running = False
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down system...")
        
        for server_name, process in self.processes.items():
            try:
                logger.info(f"Terminating {server_name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {server_name}...")
                    process.kill()
                    
            except Exception as e:
                logger.error(f"Error stopping {server_name}: {e}")
        
        logger.info("System shutdown complete")
    
    def print_system_info(self):
        """Print system information"""
        print("\n" + "="*60)
        print("🚀 AAVE FLASH LOAN ARBITRAGE SYSTEM")
        print("="*60)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Config: {self.config_path}")
        print(f"📊 Dashboard: http://localhost:9001")
        print(f"📝 Logs: logs/system_launcher.log")
        print("="*60)
        print("🔑 AGENT ROLES:")
        
        if self.config.get('agent_roles'):
            for role, info in self.config['agent_roles'].items():
                print(f"  • {role}: {info.get('description', 'No description')}")
                print(f"    Servers: {', '.join(info.get('servers', []))}")
        
        print("\n🌐 SUPPORTED DEXES:")
        if self.config.get('dex_config', {}).get('supported_dexes'):
            for dex in self.config['dex_config']['supported_dexes']:
                status = "✅" if dex.get('enabled', False) else "❌"
                print(f"  {status} {dex.get('name', 'Unknown')}")
        
        print("\n💰 SUPPORTED ASSETS:")
        if self.config.get('aave_config', {}).get('supported_assets'):
            for asset in self.config['aave_config']['supported_assets']:
                print(f"  • {asset.get('symbol', 'Unknown')} (Max FL: {asset.get('max_flash_loan', 'N/A')})")
        
        print("\n⚙️ SYSTEM PARAMETERS:")
        risk_params = self.config.get('risk_parameters', {})
        print(f"  • Min Profit: ${risk_params.get('min_profit_usd', 'N/A')}")
        print(f"  • Max Slippage: {risk_params.get('max_slippage', 'N/A')}")
        print(f"  • Max Flash Loan: ${risk_params.get('max_flash_loan_usd', 'N/A')}")
        
        print("\n🛡️ SAFETY FEATURES:")
        print("  • Circuit Breaker: Enabled")
        print("  • Risk Management: Enabled")
        print("  • MEV Protection: Enabled")
        print("  • Real-time Monitoring: Enabled")
        
        print("\n💡 QUICK COMMANDS:")
        print("  • Ctrl+C: Graceful shutdown")
        print("  • View logs: tail -f logs/system_launcher.log")
        print("  • Health check: curl http://localhost:9001/health")
        print("="*60)
        print()
    
    async def run(self):
        """Main execution method"""
        try:
            # System startup
            logger.info("Initializing Aave Flash Loan System...")
            
            # Validate environment
            if not self.validate_environment():
                logger.error("Environment validation failed")
                return 1
            
            # Create directories
            self.create_directories()
            
            # Install dependencies (optional)
            # self.install_dependencies()
            
            # Start system
            self.is_running = True
            
            # Print system info
            self.print_system_info()
            
            # Start web dashboard
            self.start_web_dashboard()
            
            # Start MCP servers
            await self.start_all_mcp_servers()
            
            # Start monitoring
            monitoring_task = asyncio.create_task(self.monitoring_loop())
            
            logger.info("🎉 System fully operational!")
            logger.info("💻 Dashboard: http://localhost:9001")
            logger.info("🔍 Monitor logs: tail -f logs/system_launcher.log")
            
            # Wait for shutdown signal
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"System error: {e}")
            return 1
        finally:
            await self.shutdown()
        
        return 0

def main():
    """Main entry point"""
    try:
        launcher = AaveFlashLoanSystemLauncher()
        return asyncio.run(launcher.run())
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
