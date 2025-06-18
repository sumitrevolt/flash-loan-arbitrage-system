#!/usr/bin/env python3
"""
Unified Project Launcher
Manages all components of the flash loan arbitrage system
"""

import asyncio
import sys
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import argparse

class ProjectLauncher:
    """Unified launcher for all project components"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.processes: Dict[str, subprocess.Popen[bytes]] = {}
        self.running = False
        
        # Set up logging
        self.logger = logging.getLogger('ProjectLauncher')
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Component configurations with proper type annotations
        self.components: Dict[str, Dict[str, Any]] = {
            'flash_loan_mcp': {
                'script': 'working_flash_loan_mcp.py',
                'port': 8001,
                'description': 'Main Flash Loan MCP Server',
                'required': True
            },
            'monitoring': {
                'script': 'monitoring/unified_monitoring_dashboard.py',
                'port': 8080,
                'description': 'Monitoring Dashboard',
                'required': False
            },
            'price_monitor': {
                'script': 'monitoring/live_blockchain_verification.py',
                'port': None,
                'description': 'Price Monitoring Service',
                'required': False
            }
        }

    async def check_dependencies(self) -> List[str]:
        """Check if all required dependencies are installed"""
        missing: List[str] = []
        
        # Check Python packages
        required_packages = [
            'flask',
            'fastapi',
            'uvicorn',
            'websockets',
            'ccxt',
            'pandas',
            'numpy',
            'redis',
            'psutil'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        return missing

    async def check_environment(self) -> List[str]:
        """Check environment variables and configurations"""
        issues: List[str] = []
        
        # Check required environment variables
        required_vars = ['POLYGON_RPC_URL']
        
        for var in required_vars:
            if not os.getenv(var):
                issues.append(f"Missing environment variable: {var}")
        
        # Check for .env file
        env_file = self.base_dir / '.env'
        if not env_file.exists():
            issues.append(".env file not found")
        
        return issues

    async def start_component(self, name: str, config: Dict[str, Any]) -> bool:
        """Start a single component"""
        try:
            script_path = self.base_dir / config['script']
            if not script_path.exists():
                self.logger.error(f"❌ Script not found: {script_path}")
                return False
            
            # Prepare command based on script type
            if script_path.suffix == '.py':
                cmd = [sys.executable, str(script_path)]
            else:
                cmd = [str(script_path)]
            
            self.logger.info(f"🚀 Starting {config['description']}...")
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ,
                shell=(platform.system() == 'Windows')
            )
            
            self.processes[name] = process
            
            # Wait a bit and check if process is still running
            await asyncio.sleep(2)
            if process.poll() is not None:
                _, stderr = process.communicate()
                self.logger.error(f"❌ Component {name} failed to start: {stderr.decode()}")
                return False
            
            self.logger.info(f"✅ {config['description']} started successfully")
            if config['port']:
                self.logger.info(f"   Available on http://localhost:{config['port']}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Failed to start {name}: {str(e)}")
            return False

    async def stop_component(self, name: str) -> None:
        """Stop a single component"""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:
                self.logger.info(f"🛑 Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            del self.processes[name]

    async def start_all(self, components: Optional[List[str]] = None) -> None:
        """Start all or specified components"""
        components_to_start = components or list(self.components.keys())
        
        self.logger.info("🚀 Starting Flash Loan Arbitrage System")
        self.logger.info("=" * 50)
        
        self.running = True
        success_count = 0
        
        for name in components_to_start:
            if name not in self.components:
                self.logger.warning(f"⚠️ Unknown component: {name}")
                continue
            
            config = self.components[name]
            success = await self.start_component(name, config)
            
            if success:
                success_count += 1
            elif config['required']:
                self.logger.error(f"❌ Required component {name} failed to start. Stopping...")
                await self.stop_all()
                return
        
        self.logger.info("=" * 50)
        self.logger.info(f"✅ System started: {success_count}/{len(components_to_start)} components running")
        
        if success_count > 0:
            self.logger.info("\n📊 Available Services:")
            for name, config in self.components.items():
                if name in self.processes and config['port']:
                    self.logger.info(f"   {config['description']}: http://localhost:{config['port']}")
            
            self.logger.info("\n🎯 Quick Start:")
            self.logger.info("   - Main MCP Server: http://localhost:8001/health")
            self.logger.info("   - Press Ctrl+C to stop all services")

    async def stop_all(self) -> None:
        """Stop all running components"""
        self.logger.info("🛑 Stopping all components...")
        self.running = False
        
        for name in list(self.processes.keys()):
            await self.stop_component(name)
        
        self.logger.info("✅ All components stopped")

    async def monitor_processes(self) -> None:
        """Monitor running processes and restart if needed"""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    self.logger.warning(f"⚠️ Component {name} has stopped unexpectedly")
                    del self.processes[name]
                    
                    # Attempt to restart if configured
                    if name in self.components and self.components[name].get('restart_on_failure', True):
                        self.logger.info(f"🔄 Attempting to restart {name}")
                        await self.start_component(name, self.components[name])
            
            await asyncio.sleep(5)  # Check every 5 seconds

    async def run_interactive(self) -> None:
        """Run in interactive mode"""
        try:
            await self.start_all()
            
            if self.processes:
                # Start monitoring task
                _ = asyncio.create_task(self.monitor_processes())
                
                # Wait for interrupt
                while self.running:
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Shutdown signal received")
        finally:
            await self.stop_all()

    async def run(self):
        """Main run loop"""
        try:
            self.running = True
            
            # Check missing dependencies
            missing_deps = await self.check_dependencies()
            if missing_deps:
                self.logger.warning(f"Missing dependencies: {', '.join(missing_deps)}")
                print("\nWould you like to install missing dependencies? (y/n): ", end='')
                if input().lower() == 'y':
                    print("Please run: pip install " + " ".join(missing_deps))
                    return
            
            # Check environment
            env_issues = await self.check_environment()
            if env_issues:
                self.logger.warning("Environment issues found:")
                for issue in env_issues:
                    self.logger.warning(f"  - {issue}")
            
            # Start monitor task
            asyncio.create_task(self.monitor_processes())
            
            # Show component menu
            print("\n=== Flash Loan Project Launcher ===")
            print("\nAvailable components:")
            for i, (name, config) in enumerate(self.components.items()):
                print(f"{i+1}. {name}: {config.get('description', 'No description')}")
            
            print("\nSelect components to start (comma-separated numbers, or 'all'): ", end='')
            choice = input().strip()
            
            if choice.lower() == 'all':
                await self.start_all()
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split(',')]
                    selected: List[str] = []
                    for idx in indices:
                        if 0 <= idx < len(self.components):
                            name = list(self.components.keys())[idx]
                            selected.append(name)
                    
                    if selected:
                        await self.start_selected_components(selected)
                    else:
                        print("No valid components selected")
                        return
                except ValueError:
                    print("Invalid input")
                    return
            
            # Wait for user input to stop
            await asyncio.get_event_loop().run_in_executor(None, input, "\nPress Enter to stop all services...")
            
        except KeyboardInterrupt:
            self.logger.info("\nShutdown requested...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop all components gracefully"""
        self.running = False
        
        self.logger.info("Stopping all components...")
        
        # Stop all processes
        for name, process in self.processes.items():
            self.logger.info(f"Stopping {name}")
            try:
                process.terminate()
                # Give process time to terminate gracefully
                await asyncio.sleep(1)
                if process.poll() is None:
                    process.kill()
            except Exception as e:
                self.logger.error(f"Error stopping {name}: {e}")
        
        self.processes.clear()
        self.logger.info("All components stopped")

    async def start_selected_components(self, selected: List[str]):
        """Start selected components by name"""
        self.logger.info(f"🚀 Starting selected components: {', '.join(selected)}")
        
        success_count = 0
        for name in selected:
            if name in self.components:
                config = self.components[name]
                success = await self.start_component(name, config)
                
                if success:
                    success_count += 1
            else:
                self.logger.warning(f"⚠️ Unknown component: {name}")
        
        self.logger.info(f"✅ Started {success_count}/{len(selected)} components")

def main():
    parser = argparse.ArgumentParser(description='Flash Loan Project Launcher')
    parser.add_argument('--list', action='store_true', help='List available components')
    parser.add_argument('--check', action='store_true', help='Check dependencies and environment')
    parser.add_argument('--components', nargs='+', help='Start specific components')
    
    args = parser.parse_args()
    
    launcher = ProjectLauncher()
    
    if args.list:
        print("\nAvailable components:")
        for name, config in launcher.components.items():
            print(f"  - {name}: {config.get('description', 'No description')}")
        return
    
    if args.check:
        asyncio.run(launcher.check_dependencies())
        asyncio.run(launcher.check_environment())
        return
    
    if args.components:
        asyncio.run(launcher.start_selected_components(args.components))
    else:
        asyncio.run(launcher.run())

if __name__ == "__main__":
    main()
