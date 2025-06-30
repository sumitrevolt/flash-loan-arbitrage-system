# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess
import sys
import time
"""
Quick MCP Server Launcher
Easy way to start your 21 containerized MCP servers
"""


def run_command(cmd, capture=True):
    """Run a command"""
    try:
        if capture:
            result: str = subprocess.run(cmd, capture_output=True, text=True, check=False)
        else:
            result: str = subprocess.run(cmd, check=False)
        return result
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return None

def main():
    print("[INIT] MCP Server Docker Launcher")
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
        choice = input("\n[TASK] Enter your choice (0-8): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        
        elif choice == "1":
            print("\n🔨 Building MCP server images...")
            cmd = ["docker", "compose", "-f", compose_file, "build", "--parallel"]
            result: str = run_command(cmd, capture=False)
            if result and result.returncode == 0:
                print("[OK] Images built successfully!")
            else:
                print("[ERROR] Failed to build images")
        
        elif choice == "2":
            print("\n[INIT] Starting infrastructure services...")
            services = ["redis", "postgres", "rabbitmq"]
            for service in services:
                print(f"   Starting {service}...")
                cmd = ["docker", "compose", "-f", compose_file, "up", "-d", service]
                run_command(cmd, capture=False)
            
            print("⏳ Waiting for services to be ready...")
            time.sleep(10)
            print("[OK] Infrastructure started!")
        
        elif choice == "3":
            print("\n[INIT] Starting all MCP servers...")
            cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]
            result: str = run_command(cmd, capture=False)
            if result and result.returncode == 0:
                print("[OK] All servers started!")
                print("\n[METRICS] Access points:")
                print("   - Dashboard: http://localhost:8080")
                print("   - Grafana: http://localhost:3002")
                print("   - Prometheus: http://localhost:9090")
                print("   - RabbitMQ: http://localhost:15672")
            else:
                print("[ERROR] Failed to start servers")
        
        elif choice == "4":
            print("\n[METRICS] Checking container status...")
            cmd = ["docker", "compose", "-f", compose_file, "ps"]
            run_command(cmd, capture=False)
        
        elif choice == "5":
            print("\n🏥 Checking server health...")
            # Use the manager script
            manager_cmd = [sys.executable, "docker/mcp_server_manager.py", "health"]
            run_command(manager_cmd, capture=False)
        
        elif choice == "6":
            print("\n[STOP] Stopping all servers...")
            cmd = ["docker", "compose", "-f", compose_file, "down"]
            result: str = run_command(cmd, capture=False)
            if result and result.returncode == 0:
                print("[OK] All servers stopped!")
            else:
                print("[ERROR] Failed to stop servers")
        
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
                    print("[OK] Cleanup completed!")
                else:
                    print("[ERROR] Cleanup failed")
        
        else:
            print("[ERROR] Invalid choice. Please enter 0-8.")

if __name__ == "__main__":
    main()