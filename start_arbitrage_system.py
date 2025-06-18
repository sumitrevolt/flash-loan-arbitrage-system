#!/usr/bin/env python3
"""
24/7 Arbitrage System Launcher
==============================

Simple launcher script to start the complete arbitrage system with all components.
"""

import os
import sys
import time
import subprocess
import asyncio
import signal
from pathlib import Path

def print_banner():
    """Print startup banner"""
    banner = """
🚀 24/7 ARBITRAGE SYSTEM LAUNCHER 🚀
===================================

Starting complete arbitrage system with:
✅ Production arbitrage engine
✅ MCP servers for coordination  
✅ AI agents for intelligence
✅ Admin dashboard for control

Press Ctrl+C to stop all services
"""
    print(banner)

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment...")
    
    # Check for required files
    required_files = [
        '.env',
        'abi/aave_pool.json',
        'production_arbitrage_system.py'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing required file: {file}")
            return False
        else:
            print(f"✅ Found: {file}")
    
    # Check environment variables
    required_env_vars = ['ARBITRAGE_PRIVATE_KEY', 'POLYGON_RPC_URL']
    
    # Load .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    for var in required_env_vars:
        if not os.getenv(var):
            print(f"❌ Missing environment variable: {var}")
            return False
        else:
            print(f"✅ Environment variable set: {var}")
    
    print("✅ Environment check passed!")
    return True

def start_component(name, command, wait_time=2):
    """Start a system component"""
    print(f"🚀 Starting {name}...")
    try:
        process = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        time.sleep(wait_time)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ {name} started successfully (PID: {process.pid})")
            return process
        else:
            print(f"❌ {name} failed to start")
            return None
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return None

def main():
    """Main launcher function"""
    print_banner()
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Store all processes for cleanup
    processes = []
    
    try:
        # Start MCP servers
        print("\n📡 Starting MCP servers...")
        mcp_servers = [
            ("Real-Time Price MCP", "python mcp_servers/real_time_price_mcp_server.py"),
            ("Profit Optimizer MCP", "python mcp_servers/profit_optimizer_mcp_server.py"),
            ("Aave Integration MCP", "python mcp_servers/aave_flash_loan_mcp_server.py"),
            ("DEX Aggregator MCP", "python mcp_servers/dex_aggregator_mcp_server.py"),
            ("Risk Management MCP", "python mcp_servers/risk_management_mcp_server.py"),
            ("Monitoring MCP", "python mcp_servers/monitoring_mcp_server.py"),
        ]
        
        for name, command in mcp_servers:
            if os.path.exists(command.split()[1]):  # Check if file exists
                process = start_component(name, command)
                if process:
                    processes.append(process)
            else:
                print(f"⚠️ Skipping {name} - file not found")
        
        # Start AI agents
        print("\n🤖 Starting AI agents...")
        ai_agents = [
            ("Arbitrage Detector", "python ai_agents/arbitrage_detector.py"),
            ("Risk Manager", "python ai_agents/risk_manager.py"),
            ("Route Optimizer", "python ai_agents/route_optimizer.py"),
            ("Market Analyzer", "python ai_agents/market_analyzer.py"),
        ]
        
        for name, command in ai_agents:
            if os.path.exists(command.split()[1]):  # Check if file exists
                process = start_component(name, command)
                if process:
                    processes.append(process)
            else:
                print(f"⚠️ Skipping {name} - file not found")
        
        # Start admin dashboard
        print("\n📊 Starting admin dashboard...")
        if os.path.exists('admin_dashboard.py'):
            dashboard_process = start_component("Admin Dashboard", "python admin_dashboard.py")
            if dashboard_process:
                processes.append(dashboard_process)
                print("🌐 Admin dashboard available at: http://localhost:5000")
        
        # Start main arbitrage system
        print("\n🎯 Starting main arbitrage system...")
        main_process = start_component("Production Arbitrage System", "python production_arbitrage_system.py", wait_time=5)
        if main_process:
            processes.append(main_process)
        
        print("\n✅ System startup complete!")
        print("=" * 50)
        print("📊 Admin Dashboard: http://localhost:5000")
        print("🎯 Arbitrage System: Active")
        print("📡 MCP Servers: Running")
        print("🤖 AI Agents: Running")
        print("=" * 50)
        print("\n🔧 System Controls:")
        print("  - View dashboard: http://localhost:5000")
        print("  - Pause system: Create admin_controls.json with {'pause': true}")
        print("  - Stop system: Press Ctrl+C or create admin_controls.json with {'stop': true}")
        print("\n⏳ System is now running 24/7. Press Ctrl+C to stop all services.")
        
        # Keep the launcher running
        while True:
            time.sleep(10)
            
            # Check if any processes have died
            active_processes = []
            for process in processes:
                if process.poll() is None:  # Still running
                    active_processes.append(process)
                else:
                    print(f"⚠️ Process {process.pid} has stopped")
            
            processes = active_processes
            
            if not processes:
                print("❌ All processes have stopped. Exiting.")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received...")
        
    except Exception as e:
        print(f"\n❌ Launcher error: {e}")
        
    finally:
        # Cleanup all processes
        print("🧹 Cleaning up processes...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Process {process.pid} terminated")
            except:
                try:
                    process.kill()
                    print(f"🔨 Process {process.pid} killed")
                except:
                    pass
        
        print("✅ Cleanup complete. System stopped.")

if __name__ == "__main__":
    main()
