#!/usr/bin/env python3
"""
Quick MCP Docker System Status Checker
Monitors all your MCP containers and services
"""

import subprocess
import json
import requests
import time
from datetime import datetime
from pathlib import Path

def run_command(cmd):
    """Run a command and return output"""
    try:
        result: str = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        # WARNING: This is a security risk
        # WARNING: This is a security risk
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False

def check_container_status():
    """Check Docker container status"""
    print("🐳 DOCKER CONTAINER STATUS")
    print("=" * 50)
    
    cmd = 'docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}" | findstr mcp-'
    output, success = run_command(cmd)
    
    if success and output:
        lines = output.split('\n')
        running_containers = len(lines)
        print(f"✅ {running_containers} MCP containers running")
        for line in lines:
            if line.strip():
                print(f"   {line}")
    else:
        print("❌ No MCP containers found or Docker not running")
    
    print()

def check_service_health():
    """Check service health endpoints"""
    print("🏥 SERVICE HEALTH CHECKS")
    print("=" * 50)
    
    services = [
        {"name": "MCP Coordinator", "url": "http://localhost:3000/health"},
        {"name": "Enhanced Coordinator", "url": "http://localhost:3001/health"},
        {"name": "Token Scanner", "url": "http://localhost:3003/health"},
        {"name": "Grafana", "url": "http://localhost:3030/api/health"},
        {"name": "Prometheus", "url": "http://localhost:9090/-/healthy"},
    ]
    
    for service in services:
        try:
            response = requests.get(service["url"], timeout=3)
            if response.status_code == 200:
                print(f"✅ {service['name']} - Healthy")
            else:
                print(f"⚠️  {service['name']} - Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {service['name']} - Not reachable")
        except Exception as e:
            print(f"❌ {service['name']} - Error: {str(e)[:50]}")
    
    print()

def check_infrastructure():
    """Check infrastructure services"""
    print("🏗️  INFRASTRUCTURE STATUS")
    print("=" * 50)
    
    # Check Redis
    redis_cmd = 'docker exec mcp-redis redis-cli ping 2>nul'
    output, success = run_command(redis_cmd)
    if success and "PONG" in output:
        print("✅ Redis - Connected")
    else:
        print("❌ Redis - Not responding")
    
    # Check PostgreSQL
    pg_cmd = 'docker exec mcp-postgres pg_isready -U postgres 2>nul'
    output, success = run_command(pg_cmd)
    if success and "accepting connections" in output:
        print("✅ PostgreSQL - Connected")
    else:
        print("❌ PostgreSQL - Not responding")
    
    # Check RabbitMQ
    rabbit_cmd = 'docker exec mcp-rabbitmq rabbitmq-diagnostics check_running 2>nul'
    output, success = run_command(rabbit_cmd)
    if success:
        print("✅ RabbitMQ - Running")
    else:
        print("❌ RabbitMQ - Not running")
    
    print()

def show_quick_stats():
    """Show quick system statistics"""
    print("📊 QUICK SYSTEM STATS")
    print("=" * 50)
    
    # Container count
    cmd = 'docker ps --filter "name=mcp-" --format "{{.Names}}"'
    output, success = run_command(cmd)
    if success:
        mcp_count = len([line for line in output.split('\n') if line.strip()])
        print(f"🤖 MCP Containers: {mcp_count}")
    
    # Infrastructure count
    cmd = 'docker ps --filter "name=redis" --filter "name=postgres" --filter "name=rabbitmq" --format "{{.Names}}"'
    output, success = run_command(cmd)
    if success:
        infra_count = len([line for line in output.split('\n') if line.strip()])
        print(f"🏗️  Infrastructure: {infra_count}")
    
    # System resources
    cmd = 'docker stats --no-stream --format "table {{.Container}}\\t{{.CPUPerc}}\\t{{.MemUsage}}" | findstr mcp-'
    output, success = run_command(cmd)
    if success and output:
        print(f"💾 Resource usage available via: docker stats")
    
    print()

def show_access_points():
    """Show access points for services"""
    print("🌐 ACCESS POINTS")
    print("=" * 50)
    print("🎯 Main Services:")
    print("   • MCP Coordinator: http://localhost:3000")
    print("   • Dashboard: http://localhost:8080")
    print("   • Enhanced Coordinator: http://localhost:3001")
    print()
    print("📊 Monitoring:")
    print("   • Grafana: http://localhost:3030 (admin/admin)")
    print("   • Prometheus: http://localhost:9090")
    print("   • RabbitMQ: http://localhost:15672 (mcp_admin/mcp_secure_2025)")
    print()
    print("🔧 Management:")
    print("   • View all containers: docker ps")
    print("   • View logs: docker logs <container_name>")
    print("   • Stop system: docker-compose down")
    print()

def main():
    """Main status check function"""
    print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀 MCP DOCKER SYSTEM STATUS CHECK")
    print("=" * 60)
    print()
    
    check_container_status()
    check_infrastructure()
    check_service_health()
    show_quick_stats()
    show_access_points()
    
    print("✅ Status check complete!")
    print()
    print("💡 Tip: Run this script periodically to monitor system health")

if __name__ == "__main__":
    main()
