#!/usr/bin/env python3
"""
Quick MCP Server Launcher
Easy way to start your 21 containerized MCP servers
"""

import subprocess
import time
import sys
from pathlib import Path

def run_command(cmd, capture=True):
    """Run a command"""
    try:
        if capture:
            result: str = subprocess.run(cmd, capture_output=True, text=True, check=False)
        else:
            result: str = subprocess.run(cmd, check=False)
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🚀 MCP Server Docker Launcher")
    print("=" * 50)
    
    base_dir = Path(__file__).parent.parent
    compose_file = "docker/docker-compose.mcp-servers.yml"
    
    print("📋 Available Commands:")
    print("  1. Build images")
    print("  2. Start infrastructure only")
    print("  3. Start all servers")
    print("  4. Check status")
    print("  5. Check health")
    print("  6. Stop all")
    print("  7. View logs")
    print("  8. Cleanup")
    print("  0. Exit")
    
    while True:
        choice = input("\n🎯 Enter your choice (0-8): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        
        elif choice == "1":
            print("\n🔨 Building MCP server images...")
            cmd = ["docker", "compose", "-f", compose_file, "build", "--parallel"]
            result: str = run_command(cmd, capture=False)
            if result and result.returncode == 0:
                print("✅ Images built successfully!")
            else:
                print("❌ Failed to build images")
        
        elif choice == "2":
            print("\n🚀 Starting infrastructure services...")
            services = ["redis", "postgres", "rabbitmq"]
            for service in services:
                print(f"   Starting {service}...")
                cmd = ["docker", "compose", "-f", compose_file, "up", "-d", service]
                run_command(cmd, capture=False)
            
            print("⏳ Waiting for services to be ready...")
            time.sleep(10)
            print("✅ Infrastructure started!")
        
        elif choice == "3":
            print("\n🚀 Starting all MCP servers...")
            cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]
            result: str = run_command(cmd, capture=False)
            if result and result.returncode == 0:
                print("✅ All servers started!")
                print("\n📊 Access points:")
                print("   - Dashboard: http://localhost:8080")
                print("   - Grafana: http://localhost:3002")
                print("   - Prometheus: http://localhost:9090")
                print("   - RabbitMQ: http://localhost:15672")
            else:
                print("❌ Failed to start servers")
        
        elif choice == "4":
            print("\n📊 Checking container status...")
            cmd = ["docker", "compose", "-f", compose_file, "ps"]
            run_command(cmd, capture=False)
        
        elif choice == "5":
            print("\n🏥 Checking server health...")
            # Use the manager script
            manager_cmd = [sys.executable, "docker/mcp_server_manager.py", "health"]
            run_command(manager_cmd, capture=False)
        
        elif choice == "6":
            print("\n🛑 Stopping all servers...")
            cmd = ["docker", "compose", "-f", compose_file, "down"]
            result: str = run_command(cmd, capture=False)
            if result and result.returncode == 0:
                print("✅ All servers stopped!")
            else:
                print("❌ Failed to stop servers")
        
        elif choice == "7":
            service = input("📋 Enter service name to view logs: ").strip()
            if service:
                print(f"\n📋 Showing logs for {service}...")
                cmd = ["docker", "compose", "-f", compose_file, "logs", "--tail", "100", service]
                run_command(cmd, capture=False)
        
        elif choice == "8":
            confirm = input("🧹 Are you sure you want to cleanup? (y/N): ").lower()
            if confirm == 'y':
                print("\n🧹 Cleaning up containers and volumes...")
                cmd = ["docker", "compose", "-f", compose_file, "down", "--volumes"]
                result: str = run_command(cmd, capture=False)
                if result and result.returncode == 0:
                    print("✅ Cleanup completed!")
                else:
                    print("❌ Cleanup failed")
        
        else:
            print("❌ Invalid choice. Please enter 0-8.")

if __name__ == "__main__":
    main()
