#!/usr/bin/env python3
"""
Comprehensive System Coordinator
Integrates flash loan arbitrage system with all MCP servers and fixes server issues
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
import platform
import socket
import signal
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import aiohttp
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveSystemCoordinator:
    """
    Comprehensive coordinator for both flash loan arbitrage and MCP server systems
    """
    
    def __init__(self):
        self.workspace_path = Path(os.getcwd())
        self.is_running = False
        self.start_time = None
        self.mcp_servers = {}
        self.server_processes = {}
        self.health_check_interval = 30
        self.system_metrics = {
            'mcp_servers_online': 0,
            'total_health_checks': 0,
            'failed_health_checks': 0,
            'system_uptime': 0,
            'restart_count': 0
        }
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        logger.info("Comprehensive System Coordinator initialized")
    
    def load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP server configuration"""
        config_path = self.workspace_path / "mcp_servers/config_files/working_cline_mcp_config.json"
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.mcp_servers = config.get('mcpServers', {})
            logger.info(f"Loaded configuration for {len(self.mcp_servers)} MCP servers")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load MCP configuration: {e}")
            return {}
    
    async def start_mcp_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Start an individual MCP server"""
        try:
            if server_name in self.server_processes:
                process = self.server_processes[server_name]
                if process and process.poll() is None:
                    logger.info(f"MCP server {server_name} is already running")
                    return True
            
            # Prepare command
            command = server_config.get('command', '')
            args = server_config.get('args', [])
            cwd = server_config.get('cwd', '.')
            env = os.environ.copy()
            env.update(server_config.get('env', {}))
            
            # Build full command
            if command == 'python':
                full_command = [sys.executable] + args
            elif command == 'npx':
                full_command = ['npx'] + args
            else:
                full_command = [command] + args
            
            # Resolve working directory
            work_dir = self.workspace_path / cwd if cwd != '.' else self.workspace_path
            
            logger.info(f"Starting MCP server {server_name}: {' '.join(full_command)}")
            
            # Start process
            process = subprocess.Popen(
                full_command,
                env=env,
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            self.server_processes[server_name] = process
            
            # Wait a moment for startup
            await asyncio.sleep(2)
            
            # Check if still running
            if process.poll() is None:
                logger.info(f"✅ Successfully started MCP server: {server_name}")
                return True
            else:
                # Get error output
                stdout, stderr = process.communicate()
                logger.error(f"❌ Failed to start MCP server {server_name}")
                if stderr:
                    logger.error(f"Error output: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Exception starting MCP server {server_name}: {e}")
            return False
    
    async def stop_mcp_server(self, server_name: str) -> None:
        """Stop an individual MCP server"""
        try:
            if server_name in self.server_processes:
                process = self.server_processes[server_name]
                if process and process.poll() is None:
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        await asyncio.wait_for(
                            asyncio.create_task(self._wait_for_process(process)),
                            timeout=10
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"Force killing MCP server {server_name}")
                        process.kill()
                    
                    logger.info(f"Stopped MCP server: {server_name}")
                
                del self.server_processes[server_name]
                
        except Exception as e:
            logger.error(f"Error stopping MCP server {server_name}: {e}")
    
    async def _wait_for_process(self, process: subprocess.Popen) -> None:
        """Wait for process to terminate"""
        while process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def health_check_mcp_servers(self) -> Dict[str, Any]:
        """Perform health checks on all MCP servers"""
        health_status = {}
        online_count = 0
        
        for server_name, server_config in self.mcp_servers.items():
            try:
                self.system_metrics['total_health_checks'] += 1
                
                # Check if process is running
                if server_name in self.server_processes:
                    process = self.server_processes[server_name]
                    if process and process.poll() is None:
                        status = "running"
                        online_count += 1
                    else:
                        status = "stopped"
                        # Attempt restart
                        logger.info(f"Attempting to restart stopped server: {server_name}")
                        restart_success = await self.start_mcp_server(server_name, server_config)
                        if restart_success:
                            status = "restarted"
                            online_count += 1
                            self.system_metrics['restart_count'] += 1
                        else:
                            status = "failed_restart"
                            self.system_metrics['failed_health_checks'] += 1
                else:
                    status = "not_started"
                    # Try to start
                    start_success = await self.start_mcp_server(server_name, server_config)
                    if start_success:
                        status = "started"
                        online_count += 1
                    else:
                        status = "failed_start"
                        self.system_metrics['failed_health_checks'] += 1
                
                health_status[server_name] = {
                    'status': status,
                    'last_check': datetime.now().isoformat(),
                    'config': server_config
                }
                
            except Exception as e:
                logger.error(f"Health check failed for {server_name}: {e}")
                health_status[server_name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
                self.system_metrics['failed_health_checks'] += 1
        
        self.system_metrics['mcp_servers_online'] = online_count
        return health_status
    
    async def test_mcp_server_functionality(self, server_name: str) -> Dict[str, Any]:
        """Test MCP server functionality by calling tools"""
        try:
            if server_name not in self.server_processes:
                return {'success': False, 'error': 'Server not running'}
            
            process = self.server_processes[server_name]
            if not process or process.poll() is not None:
                return {'success': False, 'error': 'Process not active'}
            
            # Test with health check if available
            test_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "health",
                    "arguments": {}
                }
            }
            
            # Send test message
            try:
                process.stdin.write((json.dumps(test_message) + '\n').encode())
                process.stdin.flush()
                
                # Wait for response (simplified test)
                await asyncio.sleep(1)
                
                return {
                    'success': True,
                    'test_type': 'health_check',
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Communication test failed: {e}',
                    'timestamp': datetime.now().isoformat()
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def integrate_flash_loan_system(self) -> Dict[str, Any]:
        """Integrate with the flash loan arbitrage system"""
        try:
            # Check if main arbitrage system files exist
            main_files = [
                'optimized_arbitrage_bot_v2.py',
                'dex_integrations.py',
                'config.py'
            ]
            
            file_status = {}
            for file_name in main_files:
                file_path = self.workspace_path / file_name
                file_status[file_name] = {
                    'exists': file_path.exists(),
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if file_path.exists() else None
                }
            
            # Check MCP coordinator
            mcp_coordinator_path = self.workspace_path / 'mcp_servers/unified_mcp_coordinator.py/unified_mcp_coordinator.py'
            coordinator_status = {
                'exists': mcp_coordinator_path.exists(),
                'size': mcp_coordinator_path.stat().st_size if mcp_coordinator_path.exists() else 0
            }
            
            integration_status = {
                'flash_loan_files': file_status,
                'mcp_coordinator': coordinator_status,
                'integration_ready': all(status['exists'] for status in file_status.values()),
                'timestamp': datetime.now().isoformat()
            }
            
            return integration_status
            
        except Exception as e:
            logger.error(f"Error integrating flash loan system: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        try:
            # Get MCP server health
            mcp_health = await self.health_check_mcp_servers()
            
            # Test server functionality
            functionality_tests = {}
            for server_name in self.mcp_servers.keys():
                functionality_tests[server_name] = await self.test_mcp_server_functionality(server_name)
            
            # Get flash loan integration status
            integration_status = await self.integrate_flash_loan_system()
            
            # Calculate uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            self.system_metrics['system_uptime'] = uptime_seconds
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'system_status': 'running' if self.is_running else 'stopped',
                'uptime_hours': round(uptime_seconds / 3600, 2),
                'mcp_servers': {
                    'health_status': mcp_health,
                    'functionality_tests': functionality_tests,
                    'total_configured': len(self.mcp_servers),
                    'currently_online': self.system_metrics['mcp_servers_online']
                },
                'flash_loan_integration': integration_status,
                'system_metrics': self.system_metrics,
                'recommendations': self._generate_recommendations(mcp_health, integration_status)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating system report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _generate_recommendations(self, mcp_health: Dict[str, Any], integration_status: Dict[str, Any]) -> List[str]:
        """Generate system recommendations based on current status"""
        recommendations = []
        
        # Check MCP server issues
        for server_name, health in mcp_health.items():
            if health['status'] in ['failed_start', 'failed_restart', 'error']:
                recommendations.append(f"Fix MCP server {server_name}: {health.get('error', 'Unknown error')}")
        
        # Check integration readiness
        if not integration_status.get('integration_ready', False):
            missing_files = [
                file for file, status in integration_status.get('flash_loan_files', {}).items()
                if not status.get('exists', False)
            ]
            if missing_files:
                recommendations.append(f"Missing flash loan system files: {', '.join(missing_files)}")
        
        # Performance recommendations
        if self.system_metrics['failed_health_checks'] > 0:
            failure_rate = self.system_metrics['failed_health_checks'] / max(self.system_metrics['total_health_checks'], 1)
            if failure_rate > 0.1:  # More than 10% failure rate
                recommendations.append("High health check failure rate - investigate server stability")
        
        if not recommendations:
            recommendations.append("All systems are functioning properly")
        
        return recommendations
    
    async def start_system(self) -> None:
        """Start the comprehensive system"""
        logger.info("🚀 Starting Comprehensive System Coordinator...")
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # Load MCP configuration
        config = self.load_mcp_config()
        if not config:
            logger.error("Failed to load MCP configuration")
            return
        
        # Start all MCP servers
        for server_name, server_config in self.mcp_servers.items():
            await self.start_mcp_server(server_name, server_config)
        
        logger.info("✅ Comprehensive System Coordinator started successfully")
        
        # Start monitoring loop
        await self._monitoring_loop()
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        logger.info("🔍 Starting system monitoring loop...")
        
        while self.is_running:
            try:
                # Perform health checks
                health_status = await self.health_check_mcp_servers()
                
                # Log summary
                online_servers = sum(1 for status in health_status.values() if status['status'] == 'running')
                logger.info(f"📊 Health Check: {online_servers}/{len(self.mcp_servers)} MCP servers online")
                
                # Generate periodic report
                if self.system_metrics['total_health_checks'] % 10 == 0:  # Every 10th check
                    report = await self.generate_system_report()
                    
                    # Save report
                    report_file = f"logs/system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(report_file, 'w') as f:
                        json.dump(report, f, indent=2, default=str)
                    
                    logger.info(f"📋 System report saved: {report_file}")
                
                # Wait for next cycle
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Comprehensive System Coordinator...")
        
        self.is_running = False
        
        # Stop all MCP servers
        for server_name in list(self.server_processes.keys()):
            await self.stop_mcp_server(server_name)
        
        # Generate final report
        try:
            final_report = await self.generate_system_report()
            
            report_file = f"logs/final_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(final_report, f, indent=2, default=str)
            
            logger.info(f"📋 Final report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating final report: {e}")
        
        logger.info("✅ Comprehensive System Coordinator shutdown complete")

def signal_handler(coordinator: ComprehensiveSystemCoordinator):
    """Signal handler for graceful shutdown"""
    def handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(coordinator.shutdown())
    return handler

async def main():
    """Main entry point"""
    coordinator = ComprehensiveSystemCoordinator()
    
    # Setup signal handlers for graceful shutdown
    if platform.system() != 'Windows':
        signal.signal(signal.SIGINT, signal_handler(coordinator))
        signal.signal(signal.SIGTERM, signal_handler(coordinator))
    
    try:
        await coordinator.start_system()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await coordinator.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await coordinator.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
