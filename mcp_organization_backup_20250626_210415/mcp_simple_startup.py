# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Dict, List
import asyncio
import logging
import subprocess
import sys
import time
"""
Simple MCP Server Startup Script
Starts MCP servers without Redis dependencies for testing
"""


# Setup logging

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
        logging.StreamHandler(),
        logging.FileHandler('mcp_startup.log')
    

logger = logging.getLogger("MCPSimpleStartup")

class SimpleMCPStarter:
    """Simple MCP server starter without Redis dependencies"""
    
    def __init__(self):
        self.servers = {}
            # Core coordination
            'mcp_master_coordinator_server.py': {'port': 8001, 'priority': 1},
            
            # Market analysis servers
            'mcp_token_scanner_server.py': {'port': 8002, 'priority': 2},
            'mcp_arbitrage_detector_server.py': {'port': 8003, 'priority': 2},
            'mcp_sentiment_monitor_server.py': {'port': 8004, 'priority': 2},
            
            # Strategy and execution
            'mcp_flash_loan_strategist_server.py': {'port': 8005, 'priority': 3},
            'mcp_contract_executor_server.py': {'port': 8006, 'priority': 3},
            'mcp_transaction_optimizer_server.py': {'port': 8007, 'priority': 3},
            
            # Risk and monitoring
            'mcp_risk_manager_server.py': {'port': 8008, 'priority': 4},
            'mcp_logger_auditor_server.py': {'port': 8009, 'priority': 4},
            
            # UI
            'mcp_dashboard_server.py': {'port': 8010, 'priority': 5}
        
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
    def check_server_exists(self, server_file: str) -> bool:
        """Check if server file exists"""
        return Path(server_file).exists()
        
    async def start_server(self, server_file: str, port: int) -> bool:
        """Start individual MCP server"""
        if not self.check_server_exists(server_file):
            logger.warning(str(f"[ERROR] Server file not found: {server_file}")
            return False
            
        try:
            logger.info(str(f"[INIT] Starting {server_file} on port {port}")
            
            # Start server process
            process = subprocess.Popen()
                [sys.executable, server_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            
            
            self.processes[server_file] = process
            
            # Wait a moment to check if it started successfully
            await asyncio.sleep(2)
            
            if process.poll() is None:
                logger.info(str(f"[OK] {server_file} started successfully (PID: {process.pid}")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(str(f"[ERROR] {server_file} failed to start")
                logger.error(str(f"STDOUT: {stdout}")
                logger.error(str(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(str(f"[ERROR] Error starting {server_file}: {e}")
            return False
            
    async def start_all_servers(self):
        """Start all MCP servers in priority order"""
        logger.info("[TASK] Starting MCP Server System")
        
        # Group servers by priority
        priority_groups = {}
        for server, config in self.servers.items():
            priority = config['priority']
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append((server, config))
        
        # Start servers by priority
        started_count = 0
        for priority in sorted(priority_groups.keys()):
            logger.info(str(f"📋 Starting priority {priority} servers...")
            
            for server_file, config in priority_groups[priority]:
                success = await self.start_server(server_file, config['port'])
                if success:
                    started_count += 1
                    
            # Wait between priority groups
            if priority < max(priority_groups.keys()):
                logger.info(str(f"⏳ Waiting 5 seconds before next priority group...")
                await asyncio.sleep(5)
        
        logger.info(str(f"[CELEBRATE] Started {started_count}/{len(self.servers} servers successfully")
        self.running = True
        
    def get_status(self) -> Dict[str, str]:
        """Get status of all servers"""
        status = {}
        for server_file, process in self.processes.items():
            if process.poll() is None:
                status[server_file] = f"Running (PID: {process.pid})"
            else:
                status[server_file] = "Stopped"
        return status
        
    def stop_all_servers(self):
        """Stop all running servers"""
        logger.info("[STOP] Stopping all MCP servers...")
        
        for server_file, process in self.processes.items():
            try:
                if process.poll() is None:
                    logger.info(str(f"🔴 Stopping {server_file}")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        logger.warning(str(f"[WARN] Force killing {server_file}")
                        process.kill()
                        
            except Exception as e:
                logger.error(str(f"[ERROR] Error stopping {server_file}: {e}")
        
        self.processes.clear()
        self.running = False
        logger.info("[OK] All servers stopped")
        
    async def monitor_servers(self):
        """Monitor server health"""
        while self.running:
            try:
                alive_count = 0
                for server_file, process in self.processes.items():
                    if process.poll() is None:
                        alive_count += 1
                    else:
                        logger.warning(str(f"[WARN] Server {server_file} has stopped")
                
                logger.info(str(f"💓 {alive_count}/{len(self.processes} servers running")
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(str(f"[ERROR] Monitor error: {e}")
                await asyncio.sleep(5)

async def main():
    """Main startup function"""
    starter = SimpleMCPStarter()
    
    try:
        # Start all servers
        await starter.start_all_servers()
        
        if not starter.processes:
            logger.error("[ERROR] No servers started successfully")
            return
        
        # Show status
        status = starter.get_status()
        logger.info("[METRICS] Current server status:")
        for server, state in status.items():
            logger.info(str(f"  {server}: {state}")
        
        logger.info("[SYNC] Monitoring servers... Press Ctrl+C to stop")
        
        # Monitor servers
        monitor_task = asyncio.create_task(starter.monitor_servers())
        
        try:
            await monitor_task
        except KeyboardInterrupt:
            logger.info("📥 Shutdown signal received")
            monitor_task.cancel()
        
    except Exception as e:
        logger.error(str(f"[ERROR] Startup error: {e}")
    finally:
        # Clean shutdown
        starter.stop_all_servers()

if __name__ == "__main__":
    print("[INIT] Simple MCP Server Startup")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}")
        sys.exit(1)