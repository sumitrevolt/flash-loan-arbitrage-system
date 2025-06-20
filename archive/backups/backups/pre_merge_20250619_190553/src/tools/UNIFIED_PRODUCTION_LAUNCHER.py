#!/usr/bin/env python3
#                     user_config = json.load(f)
#                     config.update(user_config)
#                     logger.info(f"Loaded configuration from {config_path}")
#             except Exception as e:
#                 logger.error(f"Failed to load configuration: {e}")
# 
#         return cast(ServerConfig, config)
"""
Production Flash Loan Arbitrage System Launcher
Unified launcher for all MCP servers and the enhanced arbitrage bot
"""

import asyncio
import subprocess
import sys
import time
import logging
import os
import signal
from pathlib import Path
from typing import List, Tuple, Optional, Any
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_launcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ProductionLauncher')

class ProductionLauncher:
    """Unified production launcher for the arbitrage system"""
    
    def __init__(self) -> None:
        self.base_path: Path = Path(__file__).parent
        self.processes: List[Tuple[str, subprocess.Popen[bytes]]] = []
        self.shutdown_event: asyncio.Event = asyncio.Event()
        
        # MCP servers configuration
        self.mcp_servers: List[Tuple[str, str, int]] = [
            ("Foundry MCP Server", "foundry-mcp-server/working_enhanced_foundry_mcp_server.py", 8001),
            ("EVM MCP Server", "mcp/evm-mcp-server/evm_mcp_server.py", 8002),
            ("Matic MCP Server", "mcp/matic-mcp-server/matic_mcp_server.py", 8003)
        ]
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()
      async def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            # Try to connect to the port
            _, writer = await asyncio.wait_for(
                asyncio.open_connection('localhost', port),
                timeout=1.0
            )
            writer.close()
            await writer.wait_closed()
            return False  # Port is occupied
        except (ConnectionRefusedError, OSError, asyncio.TimeoutError):
            return True  # Port is available
    
    async def wait_for_server_ready(self, port: int, timeout: int = 30) -> bool:
        """Wait for a server to be ready on the specified port"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://localhost:{port}/health', timeout=aiohttp.ClientTimeout(total=2)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status') == 'healthy':
                                return True
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        return False
    
    async def start_mcp_server(self, name: str, script: str, port: int) -> bool:
        """Start a single MCP server"""
        try:
            # Check if port is available
            if not await self.check_port_available(port):
                logger.warning(f"Port {port} is already in use for {name}")
                return False
            
            # Start the server
            script_path = self.base_path / script
            if not script_path.exists():
                logger.error(f"Script not found: {script_path}")
                return False
            
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=self.base_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            self.processes.append((name, process))
            logger.info(f"Started {name} (PID: {process.pid}) on port {port}")
            
            # Wait for server to be ready
            if await self.wait_for_server_ready(port, timeout=30):
                logger.info(f"{name} is ready and healthy")
                return True
            else:
                logger.error(f"{name} failed to become healthy within timeout")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            return False
    
    async def start_all_mcp_servers(self) -> bool:
        """Start all MCP servers"""
        logger.info("Starting MCP servers...")
        
        success_count = 0
        for name, script, port in self.mcp_servers:
            if await self.start_mcp_server(name, script, port):
                success_count += 1
                await asyncio.sleep(2)  # Allow startup time between servers
            else:
                logger.error(f"Failed to start {name}")
        
        if success_count > 0:
            logger.info(f"Successfully started {success_count}/{len(self.mcp_servers)} MCP servers")
            return True
        else:
            logger.error("Failed to start any MCP servers")
            return False
    
    async def start_arbitrage_bot(self) -> bool:
        """Start the unified arbitrage bot"""
        try:
            logger.info("Starting unified arbitrage bot...")
            
            # Wait a bit more for MCP servers to stabilize
            await asyncio.sleep(5)
            
            bot_script = self.base_path / "src" / "core" / "unified_production_arbitrage_bot.py"
            if not bot_script.exists():
                logger.error(f"Arbitrage bot script not found: {bot_script}")
                return False
            
            process = subprocess.Popen(
                [sys.executable, str(bot_script)],
                cwd=self.base_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes.append(("Unified Arbitrage Bot", process))
            logger.info(f"Started Unified Arbitrage Bot (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start arbitrage bot: {e}")
            return False
    
    async def monitor_processes(self):
        """Monitor all processes and restart if needed"""
        while not self.shutdown_event.is_set():
            try:
                for i, (name, process) in enumerate(self.processes):
                    poll_result: str = process.poll()
                    if poll_result is not None:
                        logger.warning(f"{name} has stopped with exit code {poll_result}")
                        
                        # Try to restart MCP servers
                        if "MCP Server" in name:
                            for server_name, script, port in self.mcp_servers:
                                if server_name == name:
                                    logger.info(f"Attempting to restart {name}")
                                    if await self.start_mcp_server(server_name, script, port):
                                        # Update process in list
                                        self.processes[i] = (name, self.processes[-1][1])
                                    break
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in process monitoring: {e}")
                await asyncio.sleep(5)
    
    async def shutdown_all_processes(self):
        """Shutdown all processes gracefully"""
        logger.info("Shutting down all processes...")
        
        for name, process in self.processes:
            try:
                logger.info(f"Terminating {name} (PID: {process.pid})")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    logger.info(f"{name} terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                logger.error(f"Error terminating {name}: {e}")
        
        self.processes.clear()
        logger.info("All processes stopped")
    
    async def run(self):
        """Run the complete production system"""
        try:
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            logger.info("=" * 60)
            logger.info("STARTING PRODUCTION FLASH LOAN ARBITRAGE SYSTEM")
            logger.info("=" * 60)
            
            # Start MCP servers
            if not await self.start_all_mcp_servers():
                logger.error("Failed to start MCP servers. Cannot continue.")
                return 1
            
            # Start arbitrage bot
            if not await self.start_arbitrage_bot():
                logger.error("Failed to start arbitrage bot")
                return 1
            
            logger.info("All systems started successfully!")
            logger.info("Press Ctrl+C to stop the system")
            
            # Start process monitoring
            monitor_task = asyncio.create_task(self.monitor_processes())
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
            # Cancel monitoring
            monitor_task.cancel()
            
            # Shutdown all processes
            await self.shutdown_all_processes()
            
            logger.info("Production system stopped successfully")
            return 0
            
        except Exception as e:
            logger.error(f"Unexpected error in production launcher: {e}")
            await self.shutdown_all_processes()
            return 1

async def main():
    """Main entry point"""
    launcher = ProductionLauncher()
    return await launcher.run()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
