#!/usr/bin/env python3
"""
Docker vs Application Health Check Comparison
Shows the difference between Docker health checks and actual service availability
"""

import docker
import requests
import socket
import json
from datetime import datetime
from typing import Dict, List

def get_docker_health_status():
    """Get Docker container health status"""
    try:
        client = docker.from_env()
        containers = client.containers.list()
        
        docker_status = {}
        for container in containers:
            if 'flashloan-' in container.name:
                health = container.attrs.get('State', {}).get('Health', {})
                status = health.get('Status', 'unknown')
                docker_status[container.name] = {
                    'status': status,
                    'container_status': container.status,
                    'ports': [port.get('PublicPort') for port in container.attrs['NetworkSettings']['Ports'].values() if port]
                }
        
        return docker_status
    except Exception as e:
        print(f"Error getting Docker status: {e}")
        return {}

def test_application_health(port: int) -> tuple:
    """Test application-level health"""
    # Test port connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        port_open = sock.connect_ex(('localhost', port)) == 0
        sock.close()
    except:
        port_open = False
    
    # Test HTTP health endpoint
    http_healthy = False
    service_info = None
    
    if port_open:
        try:
            response = requests.get(f'http://localhost:{port}/health', timeout=5)
            if response.status_code == 200:
                http_healthy = True
                try:
                    data = response.json()
                    service_info = data.get('service', 'responding')
                except:
                    service_info = 'responding'
        except:
            pass
    
    return port_open, http_healthy, service_info

def main():
    """Compare Docker health vs application health"""
    print("🔍 Docker vs Application Health Check Comparison")
    print("=" * 70)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get Docker health status
    print("📋 Getting Docker container health status...")
    docker_status = get_docker_health_status()
    
    # Define port mappings for key services
    service_ports = {
        'flashloan-flash-loan-mcp-1': 4001,
        'flashloan-web3-provider-mcp-1': 4002,
        'flashloan-dex-price-server-1': 4003,
        'flashloan-arbitrage-detector-mcp-1': 4004,
        'flashloan-github-mcp-server-1': 4008,
        'flashloan-context7-mcp-server-1': 4009,
        'flashloan-enhanced-copilot-mcp-server-1': 4010,
        'flashloan-coordinator-agent-1': 5001,
        'flashloan-arbitrage-agent-1': 5002,
        'flashloan-monitoring-agent-1': 5003,
    }
    
    print("📊 Comparison Results:")
    print("-" * 70)
    print(f"{'Service Name':<35} {'Docker':<12} {'App Health':<12} {'Status'}")
    print("-" * 70)
    
    discrepancies = 0
    total_services = 0
    
    for container_name, port in service_ports.items():
        total_services += 1
        
        # Get Docker status
        docker_info = docker_status.get(container_name, {})
        docker_health = docker_info.get('status', 'unknown')
        container_status = docker_info.get('container_status', 'unknown')
        
        # Get application health
        port_open, http_healthy, service_info = test_application_health(port)
        
        # Determine overall application status
        if http_healthy:
            app_status = "healthy"
            app_icon = "✅"
        elif port_open:
            app_status = "port_open"
            app_icon = "🟡"
        else:
            app_status = "down"
            app_icon = "❌"
        
        # Determine Docker status icon
        if docker_health == 'healthy':
            docker_icon = "✅"
        elif docker_health == 'unhealthy':
            docker_icon = "❌"
        elif docker_health == 'starting':
            docker_icon = "🟡"
        else:
            docker_icon = "❓"
        
        # Check for discrepancies
        discrepancy = ""
        if docker_health == 'unhealthy' and http_healthy:
            discrepancy = "⚠️  Docker unhealthy but app responding!"
            discrepancies += 1
        elif docker_health == 'healthy' and not http_healthy:
            discrepancy = "⚠️  Docker healthy but app not responding!"
            discrepancies += 1
        
        # Format service name
        service_display = container_name.replace('flashloan-', '').replace('-1', '')[:30]
        
        print(f"{service_display:<35} {docker_icon} {docker_health:<10} {app_icon} {app_status:<10} {discrepancy}")
    
    print("-" * 70)
    print(f"\n📊 Summary:")
    print(f"   Total Services Checked: {total_services}")
    print(f"   Health Check Discrepancies: {discrepancies}")
    
    if discrepancies == 0:
        print("   🎉 All health checks are consistent!")
    else:
        print(f"   ⚠️  {discrepancies} discrepancies found - Docker health checks may need adjustment")
    
    print(f"\n💡 Key Insights:")
    print(f"   • Docker health checks may timeout during startup while installing dependencies")
    print(f"   • Application-level health checks test actual service responsiveness")
    print(f"   • Services showing 'unhealthy' in Docker but responding to HTTP are actually working")
    print(f"   • Consider increasing health check start_period and timeout values")
    
    print(f"\n🔧 Recommendations:")
    if discrepancies > 0:
        print(f"   1. Use the enhanced Docker Compose configuration:")
        print(f"      docker-compose -f docker-compose.enhanced.yml up -d")
        print(f"   2. The enhanced config has longer start_period values (90-120s)")
        print(f"   3. Monitor with: python realtime_health_monitor.py")
    else:
        print(f"   ✅ Current configuration is working well!")
        print(f"   📈 Continue monitoring with: python realtime_health_monitor.py")

if __name__ == "__main__":
    main()
