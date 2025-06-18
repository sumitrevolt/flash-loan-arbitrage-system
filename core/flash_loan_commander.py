#!/usr/bin/env python3
"""
LangChain Flash Loan System Commander
====================================

Simple command interface to deploy all 21 MCP servers and AI agents
with LangChain coordination using GitHub Copilot intelligence.

Usage:
    python flash_loan_commander.py deploy
    python flash_loan_commander.py status  
    python flash_loan_commander.py stop
    python flash_loan_commander.py restart

Author: GitHub Copilot Multi-Agent System
Date: June 16, 2025
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional

# Import our orchestrator
from langchain_docker_orchestrator import LangChainDockerOrchestrator

def print_banner():
    """Print system banner"""
    print("""
🚀 LangChain Flash Loan System Commander
=====================================

🧠 AI-Powered MCP Server Coordination
📡 21 MCP Servers + AI Agents
🐳 Docker Orchestration  
🔧 Intelligent System Management
⚡ Enhanced Performance Monitoring

Powered by GitHub Copilot Multi-Agent System
""")

async def deploy_command():
    """Deploy all services"""
    print("🚀 Deploying LangChain MCP system...")
    
    orchestrator = LangChainDockerOrchestrator()
    
    if not await orchestrator.initialize():
        print("❌ Failed to initialize orchestrator")
        return 1
    
    if not await orchestrator.deploy_system():
        print("❌ Failed to deploy system")
        return 1
    
    print("✅ System deployed successfully!")
    
    # Show status
    status = await orchestrator.get_system_status()
    print(f"\n📊 System Status:")
    print(f"   Running Services: {status['system_metrics']['running_services']}/{status['system_metrics']['total_services']}")
    print(f"   Average CPU: {status['system_metrics']['average_cpu_usage']}%")
    print(f"   Average Memory: {status['system_metrics']['average_memory_usage']}%")
    
    print("\n🎯 System is running! Use 'python flash_loan_commander.py status' to monitor.")
    return 0

async def status_command():
    """Check status of all services"""
    print("📊 Checking system status...")
    
    orchestrator = LangChainDockerOrchestrator()
    
    if not await orchestrator.initialize():
        print("❌ Failed to initialize orchestrator")
        return 1
    
    status = await orchestrator.get_system_status()
    
    print(f"\n📈 System Metrics:")
    print(f"   Total Services: {status['system_metrics']['total_services']}")
    print(f"   Running: {status['system_metrics']['running_services']}")
    print(f"   Failed: {status['system_metrics']['failed_services']}")
    print(f"   Total Restarts: {status['system_metrics']['total_restarts']}")
    print(f"   Average CPU: {status['system_metrics']['average_cpu_usage']}%")
    print(f"   Average Memory: {status['system_metrics']['average_memory_usage']}%")
    print(f"   Uptime: {status['system_metrics']['uptime']}")
    
    print(f"\n🔍 Service Details:")
    for name, service in status['services'].items():
        status_icon = "✅" if service['status'] == "running" else "❌"
        print(f"   {status_icon} {name}: {service['status']} (Port: {service['port']})")
    
    return 0

async def stop_command():
    """Stop all services"""
    print("⏹️ Stopping LangChain MCP system...")
    
    orchestrator = LangChainDockerOrchestrator()
    
    if not await orchestrator.initialize():
        print("❌ Failed to initialize orchestrator")
        return 1
    
    if not await orchestrator.stop_system():
        print("❌ Failed to stop system")
        return 1
    
    print("✅ System stopped successfully!")
    return 0

async def restart_command():
    """Restart all services"""
    print("🔄 Restarting LangChain MCP system...")
    
    # Stop first
    await stop_command()
    
    # Wait a moment
    await asyncio.sleep(3)
    
    # Deploy again
    return await deploy_command()

async def logs_command(service_name: Optional[str] = None):
    """Show logs for services"""
    print(f"📄 Showing logs{f' for {service_name}' if service_name else ''}...")
    
    # Simple implementation - could be enhanced
    import subprocess
    
    try:
        if service_name:
            cmd = ["docker", "logs", "-f", service_name]
        else:
            cmd = ["docker-compose", "logs", "-f"]
        
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped viewing logs")
    except Exception as e:
        print(f"❌ Error viewing logs: {e}")
    
    return 0

def main():
    """Main command interface"""
    parser = argparse.ArgumentParser(
        description="LangChain Flash Loan System Commander",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python flash_loan_commander.py deploy     # Deploy all services
    python flash_loan_commander.py status     # Check system status  
    python flash_loan_commander.py stop       # Stop all services
    python flash_loan_commander.py restart    # Restart system
    python flash_loan_commander.py logs       # View all logs
    python flash_loan_commander.py logs redis # View specific service logs
        """
    )
    
    parser.add_argument(
        'command',
        choices=['deploy', 'status', 'stop', 'restart', 'logs'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'service',
        nargs='?',
        help='Service name (for logs command)'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    try:
        if args.command == 'deploy':
            return asyncio.run(deploy_command())
        elif args.command == 'status':
            return asyncio.run(status_command())
        elif args.command == 'stop':
            return asyncio.run(stop_command())
        elif args.command == 'restart':
            return asyncio.run(restart_command())
        elif args.command == 'logs':
            return asyncio.run(logs_command(args.service))
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
