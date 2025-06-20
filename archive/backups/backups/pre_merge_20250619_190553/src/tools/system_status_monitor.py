#!/usr/bin/env python3
"""
LangChain System Status Monitor
==============================
Monitor the status of all MCP servers and AI agents after coordination
"""

import asyncio
import docker
from docker.models.containers import Container
from docker.client import DockerClient
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemStatusMonitor:
    def __init__(self) -> None:
        self.docker_client: Optional[DockerClient] = None
        self.services_status: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> bool:
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            if self.docker_client:
                self.docker_client.ping()
                logger.info("✅ Docker client connected successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Docker: {e}")
            return False
        return False
    
    async def check_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Check status of all services"""
        if not self.docker_client:
            await self.initialize()
        
        services_status: Dict[str, Dict[str, Any]] = {
            'infrastructure': {},
            'mcp_servers': {},
            'ai_agents': {},
            'monitoring': {}
        }
        
        try:
            if self.docker_client:
                containers: List[Container] = self.docker_client.containers.list(all=True)
                
                for container in containers:
                    name: str = container.name
                    status: str = container.status
                    container_attrs: Dict[str, Any] = container.attrs
                    
                    # Get ports safely
                    network_settings = container_attrs.get('NetworkSettings', {})
                    ports_dict = network_settings.get('Ports', {})
                    ports = list(ports_dict.keys()) if ports_dict else []
                    
                    # Get image safely
                    image_tags = container.image.tags if hasattr(container, 'image') and container.image else []
                    image = image_tags[0] if image_tags else 'unknown'
                    
                    service_info = {
                        'status': status,
                        'ports': ports,
                        'image': image
                    }
                    
                    # Categorize services
                    name_lower = name.lower()
                    if any(infra in name_lower for infra in ['redis', 'postgres', 'rabbitmq', 'etcd', 'coordinator']):
                        services_status['infrastructure'][name] = service_info
                    elif 'mcp' in name_lower:
                        services_status['mcp_servers'][name] = service_info
                    elif any(agent in name_lower for agent in ['agent', 'executor', 'indexer', 'builder', 'planner']):
                        services_status['ai_agents'][name] = service_info
                    else:
                        services_status['monitoring'][name] = service_info
            
            self.services_status = services_status
            return services_status
            
        except Exception as e:
            logger.error(f"❌ Failed to check services: {e}")
            return {}
    
    def print_status_report(self, services_status: Dict[str, Dict[str, Any]]) -> None:
        """Print a formatted status report"""
        print("\n" + "="*80)
        print("🎮 LANGCHAIN MASTER COORDINATION - SYSTEM STATUS REPORT")
        print("="*80)
        print(f"📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Infrastructure Services
        print("🏗️ INFRASTRUCTURE SERVICES:")
        print("-" * 40)
        infra = services_status.get('infrastructure', {})
        if infra:
            for name, info in infra.items():
                status_emoji = "✅" if info['status'] == 'running' else "❌"
                ports_str = ', '.join(info['ports']) if info['ports'] else 'none'
                print(f"{status_emoji} {name:<30} | {info['status']:<10} | {ports_str}")
        else:
            print("❌ No infrastructure services found")
        
        print()
        
        # MCP Servers
        print("📦 MCP SERVERS:")
        print("-" * 40)
        mcp = services_status.get('mcp_servers', {})
        if mcp:
            running_count = sum(1 for info in mcp.values() if info['status'] == 'running')
            total_count = len(mcp)
            print(f"📊 Status: {running_count}/{total_count} MCP servers running")
            print()
            
            for name, info in mcp.items():
                status_emoji = "✅" if info['status'] == 'running' else "❌"
                ports_str = ', '.join(info['ports']) if info['ports'] else 'none'
                print(f"{status_emoji} {name:<30} | {info['status']:<10} | {ports_str}")
        else:
            print("❌ No MCP servers found")
        
        print()
        
        # AI Agents
        print("🤖 AI AGENTS:")
        print("-" * 40)
        agents = services_status.get('ai_agents', {})
        if agents:
            running_count = sum(1 for info in agents.values() if info['status'] == 'running')
            total_count = len(agents)
            print(f"📊 Status: {running_count}/{total_count} AI agents running")
            print()
            
            for name, info in agents.items():
                status_emoji = "✅" if info['status'] == 'running' else "❌"
                ports_str = ', '.join(info['ports']) if info['ports'] else 'none'
                print(f"{status_emoji} {name:<30} | {info['status']:<10} | {ports_str}")
        else:
            print("❌ No AI agents found")
        
        print()
        
        # Monitoring Services
        print("📊 MONITORING SERVICES:")
        print("-" * 40)
        monitoring = services_status.get('monitoring', {})
        if monitoring:
            for name, info in monitoring.items():
                status_emoji = "✅" if info['status'] == 'running' else "❌"
                ports_str = ', '.join(info['ports']) if info['ports'] else 'none'
                print(f"{status_emoji} {name:<30} | {info['status']:<10} | {ports_str}")
        else:
            print("❌ No monitoring services found")
        
        print()
        
        # Summary
        total_services = sum(len(category) for category in services_status.values())
        running_services = sum(
            sum(1 for info in category.values() if info['status'] == 'running')
            for category in services_status.values()
        )
        
        print("📈 SYSTEM SUMMARY:")
        print("-" * 40)
        print(f"🎯 Total Services: {total_services}")
        print(f"✅ Running Services: {running_services}")
        print(f"❌ Failed Services: {total_services - running_services}")
        print(f"📊 Success Rate: {(running_services/total_services)*100:.1f}%" if total_services > 0 else "0%")
        
        print("\n" + "="*80)
        
        # Access Points
        print("🌐 SERVICE ACCESS POINTS:")
        print("-" * 40)
        print("• Master Coordinator: http://localhost:3000")
        print("• Dashboard UI: http://localhost:8080") 
        print("• Grafana Monitoring: http://localhost:3001")
        print("• Prometheus Metrics: http://localhost:9090")
        print("• RabbitMQ Management: http://localhost:15672")
        print("• Redis: localhost:6379")
        print("• PostgreSQL: localhost:5432")
        print("="*80)
    
    async def save_status_json(self, services_status: Dict[str, Dict[str, Any]]) -> None:
        """Save status to JSON file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'services_status': services_status,
            'summary': {
                'total_services': sum(len(category) for category in services_status.values()),
                'running_services': sum(
                    sum(1 for info in category.values() if info['status'] == 'running')
                    for category in services_status.values()
                )
            }
        }
        
        with open('system_status_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("💾 Status report saved to system_status_report.json")

async def main() -> None:
    """Main monitoring function"""
    monitor = SystemStatusMonitor()
    
    print("🔍 Initializing LangChain System Status Monitor...")
    
    if not await monitor.initialize():
        print("❌ Failed to initialize Docker connection")
        return
    
    print("📊 Checking all services status...")
    services_status = await monitor.check_all_services()
    
    if services_status:
        monitor.print_status_report(services_status)
        await monitor.save_status_json(services_status)
    else:
        print("❌ Failed to retrieve services status")

if __name__ == "__main__":
    asyncio.run(main())
