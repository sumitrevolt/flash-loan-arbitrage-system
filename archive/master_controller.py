#!/usr/bin/env python3
"""
🚀 MASTER LANGCHAIN MCP SYSTEM CONTROLLER 🚀
==========================================

This is the ULTIMATE command center for your LangChain-powered
MCP server and AI agent ecosystem. 

Features:
✅ Intelligent system analysis and organization
✅ Duplicate detection and removal
✅ Docker orchestration with health monitoring  
✅ LangChain multi-agent coordination
✅ Real-time performance optimization
✅ Enhanced GitHub Copilot integration

Commands:
    organize    - Analyze and organize the entire system
    deploy      - Deploy optimized MCP servers and agents
    status      - Check comprehensive system status
    monitor     - Real-time system monitoring
    stop        - Gracefully stop all services
    restart     - Restart the entire system
    logs        - View system logs
    health      - Comprehensive health check

Author: GitHub Copilot Multi-Agent System
Date: June 16, 2025
"""

import asyncio
import argparse
import sys
import os
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

class MasterLangChainController:
    """Master controller for the entire LangChain MCP system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.start_time = datetime.now()
        
    def print_banner(self):
        """Print the master system banner"""
        print("""
🚀 MASTER LANGCHAIN MCP SYSTEM CONTROLLER 🚀
==========================================

🧠 LangChain Multi-Agent Intelligence
📡 21+ MCP Server Coordination  
🤖 AI Agent Orchestration
🐳 Advanced Docker Management
⚡ Real-time Performance Monitoring
🔧 Self-Healing Architecture

Powered by GitHub Copilot Multi-Agent System
Date: June 16, 2025
""")
    
    def print_help(self):
        """Print detailed help information"""
        help_text = """
📚 AVAILABLE COMMANDS:

🎯 SYSTEM ORGANIZATION:
   organize    - Analyze entire system, remove duplicates, optimize structure
   
🚀 DEPLOYMENT & MANAGEMENT:
   deploy      - Deploy optimized MCP servers and AI agents with monitoring
   status      - Show comprehensive system status and metrics
   monitor     - Real-time system monitoring with auto-refresh
   
🔧 CONTROL OPERATIONS:
   stop        - Gracefully stop all services and containers
   restart     - Restart entire system with optimization
   health      - Comprehensive health check of all components
   
📊 MONITORING & LOGS:
   logs        - View system logs (specify service name for specific logs)
   metrics     - Show detailed performance metrics
   
💡 EXAMPLES:
   python master_controller.py organize              # Organize entire system
   python master_controller.py deploy               # Deploy optimized system
   python master_controller.py status               # Check system status
   python master_controller.py monitor              # Real-time monitoring
   python master_controller.py logs redis           # View Redis logs
   python master_controller.py health               # Health check
   python master_controller.py stop                 # Stop all services

🎯 WORKFLOW:
   1. Run 'organize' first to analyze and optimize your system
   2. Run 'deploy' to start the optimized system
   3. Use 'monitor' for real-time tracking
   4. Use 'health' for comprehensive diagnostics
"""
        print(help_text)
    
    async def organize_system(self):
        """Organize and optimize the entire system"""
        print("🎪 ORGANIZING LANGCHAIN MCP SYSTEM")
        print("=" * 50)
        
        try:
            # Check if organizer exists
            organizer_script = self.project_root / "master_langchain_mcp_organizer.py"
            if not organizer_script.exists():
                print("❌ Organizer script not found. Please ensure master_langchain_mcp_organizer.py exists.")
                return 1
            
            print("🔍 Running comprehensive system analysis and organization...")
            print("   📡 Discovering MCP servers")
            print("   🤖 Cataloging AI agents") 
            print("   🔍 Detecting duplicates")
            print("   🧹 Removing duplicates")
            print("   🐳 Optimizing Docker configurations")
            print("   📝 Generating organized structure")
            
            # Run the organizer
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(organizer_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print("✅ System organization completed successfully!")
                
                # Show results if available
                await self._show_organization_results()
                
                print("\n🎯 Next Steps:")
                print("   1. Review generated reports (system_analysis_report.json)")
                print("   2. Check optimized Docker configuration (docker/docker-compose.optimized.yml)")
                print("   3. Run 'python master_controller.py deploy' to start optimized system")
                
                return 0
            else:
                print(f"❌ Organization failed with exit code {process.returncode}")
                if stderr:
                    print(f"Error: {stderr.decode()}")
                return process.returncode
                
        except Exception as e:
            print(f"❌ Organization error: {e}")
            return 1
    
    async def deploy_system(self):
        """Deploy the optimized system"""
        print("🚀 DEPLOYING LANGCHAIN MCP SYSTEM")
        print("=" * 50)
        
        try:
            # Import and use the orchestrator
            from langchain_docker_orchestrator import LangChainDockerOrchestrator
            
            orchestrator = LangChainDockerOrchestrator()
            
            print("🏗️ Initializing orchestrator...")
            if not await orchestrator.initialize():
                print("❌ Failed to initialize orchestrator")
                return 1
            
            print("🚀 Deploying system components...")
            if not await orchestrator.deploy_system():
                print("❌ Failed to deploy system")
                return 1
            
            print("✅ System deployed successfully!")
            
            # Show status
            status = await orchestrator.get_system_status()
            self._print_system_status(status)
            
            print("\n🎯 System is now running!")
            print("   • Use 'python master_controller.py monitor' for real-time monitoring")
            print("   • Use 'python master_controller.py health' for health checks")
            print("   • Use 'python master_controller.py logs' to view logs")
            
            return 0
            
        except ImportError:
            print("❌ LangChain Docker Orchestrator not available")
            print("💡 Try running 'python master_controller.py organize' first")
            return 1
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return 1
    
    async def check_status(self):
        """Check comprehensive system status"""
        print("📊 SYSTEM STATUS CHECK")
        print("=" * 50)
        
        try:
            from langchain_docker_orchestrator import LangChainDockerOrchestrator
            
            orchestrator = LangChainDockerOrchestrator()
            
            if not await orchestrator.initialize():
                print("❌ Failed to initialize orchestrator")
                return 1
            
            status = await orchestrator.get_system_status()
            self._print_system_status(status)
            
            return 0
            
        except ImportError:
            print("❌ System not available - run organize and deploy first")
            return 1
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return 1
    
    async def monitor_system(self):
        """Real-time system monitoring"""
        print("📊 REAL-TIME SYSTEM MONITORING")
        print("=" * 50)
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            from langchain_docker_orchestrator import LangChainDockerOrchestrator
            
            orchestrator = LangChainDockerOrchestrator()
            
            if not await orchestrator.initialize():
                print("❌ Failed to initialize orchestrator")
                return 1
            
            while True:
                # Clear screen (works on most terminals)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("📊 REAL-TIME SYSTEM MONITORING")
                print("=" * 50)
                print(f"🕐 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
                status = await orchestrator.get_system_status()
                self._print_system_status(status)
                
                print("\nPress Ctrl+C to stop monitoring...")
                
                # Wait before next update
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped")
            return 0
        except ImportError:
            print("❌ System not available - run organize and deploy first")
            return 1
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            return 1
    
    async def stop_system(self):
        """Stop the entire system"""
        print("⏹️ STOPPING LANGCHAIN MCP SYSTEM")
        print("=" * 50)
        
        try:
            from langchain_docker_orchestrator import LangChainDockerOrchestrator
            
            orchestrator = LangChainDockerOrchestrator()
            
            if not await orchestrator.initialize():
                print("❌ Failed to initialize orchestrator")
                return 1
            
            print("🛑 Stopping all services...")
            if await orchestrator.stop_system():
                print("✅ System stopped successfully!")
                return 0
            else:
                print("❌ Failed to stop system completely")
                return 1
                
        except ImportError:
            print("⚠️ Orchestrator not available, trying direct Docker commands...")
            # Fallback to direct docker-compose
            return await self._direct_docker_stop()
        except Exception as e:
            print(f"❌ Stop error: {e}")
            return 1
    
    async def restart_system(self):
        """Restart the entire system"""
        print("🔄 RESTARTING LANGCHAIN MCP SYSTEM")
        print("=" * 50)
        
        # Stop first
        result = await self.stop_system()
        if result != 0:
            print("⚠️ Stop operation had issues, continuing with restart...")
        
        print("\n⏳ Waiting 5 seconds before restart...")
        await asyncio.sleep(5)
        
        # Deploy again
        return await self.deploy_system()
    
    async def health_check(self):
        """Comprehensive health check"""
        print("🔍 COMPREHENSIVE HEALTH CHECK")
        print("=" * 50)
        
        health_score = 0
        total_checks = 0
        
        # Check Docker
        print("🐳 Checking Docker...")
        try:
            import docker
            client = docker.from_env()
            client.ping()
            print("   ✅ Docker daemon is running")
            health_score += 1
        except Exception as e:
            print(f"   ❌ Docker issue: {e}")
        total_checks += 1
        
        # Check Docker Compose files
        print("\n📄 Checking Docker Compose files...")
        compose_files = [
            "docker-compose.yml",
            "docker/docker-compose.yml", 
            "docker/docker-compose.optimized.yml"
        ]
        
        for compose_file in compose_files:
            compose_path = self.project_root / compose_file
            if compose_path.exists():
                print(f"   ✅ {compose_file} exists")
                health_score += 1
            else:
                print(f"   ❌ {compose_file} missing")
            total_checks += 1
        
        # Check Python dependencies
        print("\n🐍 Checking Python dependencies...")
        required_packages = [
            "langchain", "docker", "redis", "aiohttp", "pyyaml"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package} available")
                health_score += 1
            except ImportError:
                print(f"   ❌ {package} missing")
            total_checks += 1
        
        # Check system resources
        print("\n💾 Checking system resources...")
        try:
            import psutil
            
            # Memory check
            memory = psutil.virtual_memory()
            if memory.percent < 80:
                print(f"   ✅ Memory usage: {memory.percent:.1f}%")
                health_score += 1
            else:
                print(f"   ⚠️ High memory usage: {memory.percent:.1f}%")
            
            # Disk check
            disk = psutil.disk_usage('/')
            if disk.percent < 90:
                print(f"   ✅ Disk usage: {disk.percent:.1f}%")
                health_score += 1
            else:
                print(f"   ⚠️ High disk usage: {disk.percent:.1f}%")
                
            total_checks += 2
            
        except ImportError:
            print("   ⚠️ psutil not available for resource monitoring")
        
        # Calculate final score
        health_percentage = (health_score / total_checks) * 100 if total_checks > 0 else 0
        
        print(f"\n📊 HEALTH SUMMARY:")
        print(f"   Score: {health_score}/{total_checks} ({health_percentage:.1f}%)")
        
        if health_percentage >= 80:
            print("   ✅ System health is GOOD")
            return 0
        elif health_percentage >= 60:
            print("   ⚠️ System health needs ATTENTION")
            return 1
        else:
            print("   ❌ System health is POOR")
            return 2
    
    async def view_logs(self, service_name: Optional[str] = None):
        """View system logs"""
        print(f"📄 VIEWING LOGS{f' FOR {service_name}' if service_name else ''}")
        print("=" * 50)
        
        try:
            if service_name:
                cmd = ["docker", "logs", "-f", "--tail", "100", service_name]
                print(f"Showing logs for {service_name} (Press Ctrl+C to stop)...")
            else:
                # Try to find a compose file
                compose_file = None
                possible_files = [
                    "docker/docker-compose.optimized.yml",
                    "docker/docker-compose.yml", 
                    "docker-compose.yml"
                ]
                
                for file_path in possible_files:
                    if (self.project_root / file_path).exists():
                        compose_file = file_path
                        break
                
                if compose_file:
                    cmd = ["docker-compose", "-f", compose_file, "logs", "-f", "--tail", "100"]
                    print(f"Showing all logs from {compose_file} (Press Ctrl+C to stop)...")
                else:
                    print("❌ No Docker Compose file found")
                    return 1
            
            subprocess.run(cmd, cwd=self.project_root)
            
        except KeyboardInterrupt:
            print("\n⏹️ Stopped viewing logs")
        except FileNotFoundError:
            print("❌ Docker or docker-compose not found in PATH")
            return 1
        except Exception as e:
            print(f"❌ Error viewing logs: {e}")
            return 1
        
        return 0
    
    async def _show_organization_results(self):
        """Show organization results if available"""
        report_file = self.project_root / "system_analysis_report.json"
        
        if report_file.exists():
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                
                print("\n📊 ORGANIZATION RESULTS:")
                overview = report.get('system_overview', {})
                print(f"   📡 Total MCP Servers: {overview.get('total_mcp_servers', 0)}")
                print(f"   🤖 Total AI Agents: {overview.get('total_ai_agents', 0)}")
                print(f"   🔍 Duplicates Found: {overview.get('duplicates_found', 0)}")
                print(f"   🔧 Health Issues: {overview.get('health_issues', 0)}")
                
            except Exception as e:
                print(f"⚠️ Could not read organization report: {e}")
    
    def _print_system_status(self, status: Dict[str, Any]):
        """Print formatted system status"""
        metrics = status.get('system_metrics', {})
        
        print("📈 SYSTEM METRICS:")
        print(f"   Total Services: {metrics.get('total_services', 0)}")
        print(f"   Running: {metrics.get('running_services', 0)} ✅")
        print(f"   Failed: {metrics.get('failed_services', 0)} ❌") 
        print(f"   Total Restarts: {metrics.get('total_restarts', 0)}")
        print(f"   Average CPU: {metrics.get('average_cpu_usage', 0):.1f}%")
        print(f"   Average Memory: {metrics.get('average_memory_usage', 0):.1f}%")
        print(f"   Uptime: {metrics.get('uptime', 'Unknown')}")
        
        # Show service details
        services = status.get('services', {})
        if services:
            print(f"\n🔍 SERVICE STATUS:")
            
            running_services = []
            failed_services = []
            
            for name, service in services.items():
                if service['status'] == 'running':
                    running_services.append(f"{name} (:{service['port']})")
                else:
                    failed_services.append(f"{name} ({service['status']})")
            
            if running_services:
                print("   ✅ Running Services:")
                for service in running_services[:10]:  # Show first 10
                    print(f"      • {service}")
                if len(running_services) > 10:
                    print(f"      ... and {len(running_services) - 10} more")
            
            if failed_services:
                print("   ❌ Failed Services:")
                for service in failed_services[:5]:  # Show first 5
                    print(f"      • {service}")
                if len(failed_services) > 5:
                    print(f"      ... and {len(failed_services) - 5} more")
    
    async def _direct_docker_stop(self):
        """Direct Docker stop as fallback"""
        try:
            print("🐳 Using docker-compose to stop services...")
            
            compose_files = [
                "docker/docker-compose.optimized.yml",
                "docker/docker-compose.yml",
                "docker-compose.yml"
            ]
            
            for compose_file in compose_files:
                compose_path = self.project_root / compose_file
                if compose_path.exists():
                    cmd = ["docker-compose", "-f", compose_file, "down"]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=self.project_root
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        print(f"✅ Stopped services using {compose_file}")
                        return 0
                    else:
                        print(f"⚠️ Issues stopping with {compose_file}: {stderr.decode()}")
            
            print("❌ Could not stop services with any compose file")
            return 1
            
        except Exception as e:
            print(f"❌ Direct Docker stop error: {e}")
            return 1


async def main():
    """Main controller function"""
    controller = MasterLangChainController()
    
    parser = argparse.ArgumentParser(
        description="Master LangChain MCP System Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'command',
        choices=['organize', 'deploy', 'status', 'monitor', 'stop', 'restart', 'health', 'logs', 'help'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'service',
        nargs='?',
        help='Service name (for logs command)'
    )
    
    args = parser.parse_args()
    
    controller.print_banner()
    
    if args.command == 'help':
        controller.print_help()
        return 0
    
    try:
        if args.command == 'organize':
            return await controller.organize_system()
        elif args.command == 'deploy':
            return await controller.deploy_system()
        elif args.command == 'status':
            return await controller.check_status()
        elif args.command == 'monitor':
            return await controller.monitor_system()
        elif args.command == 'stop':
            return await controller.stop_system()
        elif args.command == 'restart':
            return await controller.restart_system()
        elif args.command == 'health':
            return await controller.health_check()
        elif args.command == 'logs':
            return await controller.view_logs(args.service)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Controller error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
