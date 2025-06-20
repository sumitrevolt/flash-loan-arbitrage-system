#!/usr/bin/env python3
"""
Create Final Unified MCP Manager
===============================

This script creates the definitive unified_mcp_manager.py by merging
the best features from all existing versions.
"""

import os
import json
from pathlib import Path
from datetime import datetime

def create_final_unified_mcp_manager():
    """Create the final, consolidated unified_mcp_manager.py"""
    
    final_mcp_manager = '''#!/usr/bin/env python3
"""
Unified MCP Manager - Final Consolidated Version
===============================================

This is the definitive MCP server manager that consolidates all previous versions.
It manages all MCP servers for the Flash Loan Arbitrage System.
"""

import asyncio
import subprocess
import sys
import time
import logging
import psutil
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_mcp_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    name: str
    script: str
    port: int
    host: str = "0.0.0.0"
    status: str = "stopped"
    process_id: Optional[int] = None
    server_type: str = "python"

class UnifiedMCPManager:
    """Manages all MCP servers for the arbitrage system"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.config_file = self.base_path / "unified_mcp_config.json"
        self.servers = self._load_server_configs()
        
    def _load_server_configs(self) -> Dict[str, MCPServerConfig]:
        """Load server configurations"""
        default_servers = {            'foundry': MCPServerConfig(
                name='Foundry MCP Server',
                script='foundry-mcp-server/working_enhanced_foundry_mcp_server.py',
                port=8001
            ),
            'evm': MCPServerConfig(
                name='EVM MCP Server', 
                script='mcp/evm-mcp-server/evm_mcp_server.py',
                port=8002
            ),
            'matic': MCPServerConfig(
                name='Matic MCP Server',
                script='mcp/matic-mcp-server/matic_mcp_server.py', 
                port=8003
            ),
            'arbitrage': MCPServerConfig(
                name='Arbitrage Trading MCP Server',
                script='core/arbitrage_trading_mcp_server.py',
                port=8004
            ),
            'copilot': MCPServerConfig(
                name='Enhanced Copilot MCP Server',
                script='core/enhanced_copilot_mcp_server.py',
                port=8005
            ),
            'data_integrator': MCPServerConfig(
                name='Real-time Data Integrator',
                script='core/real_time_mcp_data_integrator.py',
                port=8006
            ),
            'taskmanager': MCPServerConfig(
                name='Task Manager MCP',
                script='mcp/mcp-taskmanager/index.ts',
                port=8007,
                server_type='typescript'
            )
        }
        
        # Try to load from config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    # Update defaults with config data
                    for server_id, server_config in config_data.get('mcp_servers', {}).items():
                        if server_id in default_servers:
                            default_servers[server_id].port = server_config.get('port', default_servers[server_id].port)
                            default_servers[server_id].script = server_config.get('script', default_servers[server_id].script)
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")
        
        return default_servers
        
    def check_port_usage(self, port: int) -> bool:
        """Check if a port is in use"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except:
            return False
    
    def find_running_servers(self):
        """Find already running MCP servers"""
        logger.info("🔍 Checking for running MCP servers...")
        
        for server_id, server in self.servers.items():
            if self.check_port_usage(server.port):
                server.status = "running"
                logger.info(f"  ✅ {server.name} is running on port {server.port}")
            else:
                server.status = "stopped"
                logger.info(f"  ⭕ {server.name} is not running on port {server.port}")
    
    async def start_server(self, server_id: str) -> bool:
        """Start a specific MCP server"""
        server = self.servers[server_id]
        
        if server.status == "running":
            logger.info(f"  ⚠️ {server.name} is already running")
            return True
        
        try:
            script_path = self.base_path / server.script
            
            if not script_path.exists():
                logger.error(f"  ❌ Script not found: {script_path}")
                return False
            
            # Determine command based on file type
            if server.server_type == 'typescript' or script_path.suffix == '.ts':
                cmd = ['node', str(script_path)]
            else:
                cmd = [sys.executable, str(script_path)]
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=script_path.parent
            )
            
            server.process_id = process.pid
            server.status = "starting"
            
            # Wait a moment and check if it started
            await asyncio.sleep(3)
            
            if self.check_port_usage(server.port):
                server.status = "running"
                logger.info(f"  ✅ Started {server.name} on port {server.port} (PID: {process.pid})")
                return True
            else:
                server.status = "failed"
                logger.error(f"  ❌ Failed to start {server.name}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Error starting {server.name}: {e}")
            server.status = "failed"
            return False
    
    async def start_all_servers(self):
        """Start all MCP servers"""
        logger.info("🚀 Starting all MCP servers...")
        
        # Start servers in order of dependency
        server_order = ['foundry', 'evm', 'matic', 'arbitrage', 'copilot', 'data_integrator', 'taskmanager']
        
        started_count = 0
        for server_id in server_order:
            if server_id in self.servers:
                if await self.start_server(server_id):
                    started_count += 1
                
                # Stagger startup to avoid conflicts
                await asyncio.sleep(2)
        
        logger.info(f"📊 Started {started_count}/{len(server_order)} MCP servers")
        return started_count
    
    def stop_server(self, server_id: str) -> bool:
        """Stop a specific MCP server"""
        server = self.servers[server_id]
        
        try:
            if server.process_id:
                process = psutil.Process(server.process_id)
                process.terminate()
                process.wait(timeout=10)
                server.status = "stopped"
                logger.info(f"  ✅ Stopped {server.name}")
                return True
        except:
            pass
        
        # Try to kill by port
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == server.port:
                    process = psutil.Process(conn.pid)
                    process.terminate()
                    server.status = "stopped"
                    logger.info(f"  ✅ Stopped {server.name} (by port)")
                    return True
        except:
            pass
        
        logger.warning(f"  ⚠️ Could not stop {server.name}")
        return False
    
    def stop_all_servers(self):
        """Stop all MCP servers"""
        logger.info("🛑 Stopping all MCP servers...")
        
        stopped_count = 0
        for server_id in self.servers.keys():
            if self.stop_server(server_id):
                stopped_count += 1
        
        logger.info(f"📊 Stopped {stopped_count}/{len(self.servers)} MCP servers")
    
    def status_report(self):
        """Generate status report of all servers"""
        logger.info("📋 MCP Server Status Report:")
        logger.info("=" * 50)
        
        for server_id, server in self.servers.items():
            status_emoji = {
                "running": "✅",
                "stopped": "⭕", 
                "starting": "🔄",
                "failed": "❌"
            }.get(server.status, "❓")
            
            logger.info(f"  {status_emoji} {server.name}")
            logger.info(f"     Port: {server.port}")
            logger.info(f"     Status: {server.status}")
            logger.info(f"     Script: {server.script}")
            if server.process_id:
                logger.info(f"     PID: {server.process_id}")
            logger.info("")
    
    async def health_check(self):
        """Perform health check on all servers"""
        logger.info("🏥 Performing health check on all MCP servers...")
        
        healthy_count = 0
        for server_id, server in self.servers.items():
            if self.check_port_usage(server.port):
                server.status = "running"
                healthy_count += 1
            else:
                server.status = "stopped"
        
        logger.info(f"📊 Health check: {healthy_count}/{len(self.servers)} servers healthy")
        return healthy_count
    
    async def restart_failed_servers(self):
        """Restart any failed servers"""
        logger.info("🔄 Restarting failed servers...")
        
        failed_servers = [sid for sid, server in self.servers.items() if server.status in ["stopped", "failed"]]
        
        if not failed_servers:
            logger.info("  ✅ No failed servers to restart")
            return
        
        restarted = 0
        for server_id in failed_servers:
            if await self.start_server(server_id):
                restarted += 1
        
        logger.info(f"📊 Restarted {restarted}/{len(failed_servers)} failed servers")
    
    def save_config(self):
        """Save current configuration to file"""
        config = {
            "system": {
                "name": "Flash Loan Arbitrage System",
                "version": "2.0.0",
                "manager": "Unified MCP Manager",
                "last_updated": datetime.now().isoformat()
            },
            "mcp_servers": {}
        }
        
        for server_id, server in self.servers.items():
            config["mcp_servers"][server_id] = {
                "name": server.name,
                "port": server.port,
                "script": server.script,
                "type": server.server_type,
                "status": server.status
            }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"💾 Configuration saved to {self.config_file}")

async def main():
    """Main function"""
    manager = UnifiedMCPManager()
    
    try:
        # Check current status
        manager.find_running_servers()
        manager.status_report()
        
        # Start all servers
        await manager.start_all_servers()
        
        # Save configuration
        manager.save_config()
        
        # Final status check
        await asyncio.sleep(5)
        await manager.health_check()
        manager.status_report()
        
        logger.info("✅ All MCP servers are now managed and running!")
        logger.info("🔧 Use Ctrl+C to stop all servers")
        
        # Keep running and monitoring
        try:
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                await manager.health_check()
                await manager.restart_failed_servers()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
    
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
    
    finally:
        manager.stop_all_servers()
        logger.info("👋 MCP Manager shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Write the final unified MCP manager
    output_path = Path("unified_mcp_manager.py")
    with open(output_path, 'w') as f:
        f.write(final_mcp_manager)
    
    print(f"✅ Created final unified MCP manager: {output_path}")
    
    # Create accompanying config file
    config = {
        "system": {
            "name": "Flash Loan Arbitrage System",
            "version": "2.0.0",
            "description": "Unified MCP server management system",
            "created": datetime.now().isoformat()
        },
        "mcp_servers": {
            "foundry": {
                "name": "Foundry MCP Server",
                "port": 8001,
                "script": "foundry_mcp_server.py",
                "type": "python",
                "status": "stopped"
            },
            "evm": {
                "name": "EVM MCP Server",
                "port": 8002,                "script": "mcp/evm-mcp-server/evm_mcp_server.py", 
                "type": "python",
                "status": "stopped"
            },
            "matic": {
                "name": "Matic MCP Server",
                "port": 8003,
                "script": "mcp/matic-mcp-server/matic_mcp_server.py",
                "type": "python", 
                "status": "stopped"
            },
            "arbitrage": {
                "name": "Arbitrage Trading MCP Server",
                "port": 8004,
                "script": "core/arbitrage_trading_mcp_server.py",
                "type": "python",
                "status": "stopped"
            },
            "copilot": {
                "name": "Enhanced Copilot MCP Server", 
                "port": 8005,
                "script": "core/enhanced_copilot_mcp_server.py",
                "type": "python",
                "status": "stopped"
            },
            "data_integrator": {
                "name": "Real-time Data Integrator",
                "port": 8006, 
                "script": "core/real_time_mcp_data_integrator.py",
                "type": "python",
                "status": "stopped"
            },
            "taskmanager": {
                "name": "Task Manager MCP",
                "port": 8007,
                "script": "mcp/mcp-taskmanager/index.ts",
                "type": "typescript",
                "status": "stopped"
            }
        }
    }
    
    config_path = Path("unified_mcp_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created configuration file: {config_path}")

if __name__ == "__main__":
    create_final_unified_mcp_manager()
