#!/usr/bin/env python3
"""
Enhanced Container System Monitor and Health Checker
Provides real-time monitoring of all 32 containers in the flash loan system
"""

import docker
import time
import requests
import json
import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict

class FlashLoanSystemMonitor:
    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}
        self.health_data = defaultdict(list)
        self.last_update = None
        
        # Expected containers and their ports
        self.expected_containers = {
            # Orchestrator
            'flashloan-orchestrator': {'port': 8080, 'type': 'orchestrator'},
            
            # MCP Servers (21 total)
            'flashloan-mcp-auth-manager': {'port': 8100, 'type': 'mcp'},
            'flashloan-mcp-blockchain': {'port': 8101, 'type': 'mcp'},
            'flashloan-mcp-defi-analyzer': {'port': 8102, 'type': 'mcp'},
            'flashloan-mcp-flash-loan': {'port': 8103, 'type': 'mcp'},
            'flashloan-mcp-arbitrage': {'port': 8104, 'type': 'mcp'},
            'flashloan-mcp-liquidity': {'port': 8105, 'type': 'mcp'},
            'flashloan-mcp-price-feed': {'port': 8106, 'type': 'mcp'},
            'flashloan-mcp-risk-manager': {'port': 8107, 'type': 'mcp'},
            'flashloan-mcp-portfolio': {'port': 8108, 'type': 'mcp'},
            'flashloan-mcp-api-client': {'port': 8109, 'type': 'mcp'},
            'flashloan-mcp-database': {'port': 8110, 'type': 'mcp'},
            'flashloan-mcp-cache-manager': {'port': 8111, 'type': 'mcp'},
            'flashloan-mcp-file-processor': {'port': 8112, 'type': 'mcp'},
            'flashloan-mcp-notification': {'port': 8113, 'type': 'mcp'},
            'flashloan-mcp-monitoring': {'port': 8114, 'type': 'mcp'},
            'flashloan-mcp-security': {'port': 8115, 'type': 'mcp'},
            'flashloan-mcp-data-analyzer': {'port': 8116, 'type': 'mcp'},
            'flashloan-mcp-web-scraper': {'port': 8117, 'type': 'mcp'},
            'flashloan-mcp-task-queue': {'port': 8118, 'type': 'mcp'},
            'flashloan-mcp-filesystem': {'port': 8119, 'type': 'mcp'},
            'flashloan-mcp-coordinator': {'port': 8120, 'type': 'mcp'},
            
            # Agent Containers (10 total)
            'flashloan-agent-analyzer': {'port': 8201, 'type': 'agent'},
            'flashloan-agent-executor': {'port': 8202, 'type': 'agent'},
            'flashloan-agent-risk-manager': {'port': 8203, 'type': 'agent'},
            'flashloan-agent-monitor': {'port': 8204, 'type': 'agent'},
            'flashloan-agent-data-collector': {'port': 8205, 'type': 'agent'},
            'flashloan-agent-arbitrage-bot': {'port': 8206, 'type': 'agent'},
            'flashloan-agent-liquidity-manager': {'port': 8207, 'type': 'agent'},
            'flashloan-agent-reporter': {'port': 8208, 'type': 'agent'},
            'flashloan-agent-healer': {'port': 8209, 'type': 'agent'},
            'flashloan-agent-coordinator': {'port': 8200, 'type': 'agent'},
        }
    
    def check_container_health(self, container_name: str, port: int) -> Dict:
        """Check individual container health"""
        try:
            container = self.client.containers.get(container_name)
            
            # Basic container info
            status_info = {
                'name': container_name,
                'status': container.status,
                'state': container.attrs['State'],
                'port': port,
                'created': container.attrs['Created'],
                'started': container.attrs['State'].get('StartedAt', 'Unknown'),
                'image': container.image.tags[0] if container.image.tags else 'Unknown',
            }
            
            # Health check via HTTP endpoint
            health_endpoint = f"http://localhost:{port}/health"
            try:
                response = requests.get(health_endpoint, timeout=5)
                status_info['http_status'] = response.status_code
                status_info['http_healthy'] = response.status_code == 200
                if response.status_code == 200:
                    try:
                        status_info['health_data'] = response.json()
                    except:
                        status_info['health_data'] = response.text
                else:
                    status_info['health_data'] = f"HTTP {response.status_code}"
            except requests.exceptions.RequestException as e:
                status_info['http_status'] = 'ERROR'
                status_info['http_healthy'] = False
                status_info['health_data'] = str(e)
            
            # Resource usage
            try:
                stats = container.stats(stream=False)
                cpu_usage = self.calculate_cpu_percentage(stats)
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                memory_percentage = (memory_usage / memory_limit) * 100
                
                status_info['resources'] = {
                    'cpu_percentage': cpu_usage,
                    'memory_usage_mb': memory_usage / (1024 * 1024),
                    'memory_limit_mb': memory_limit / (1024 * 1024),
                    'memory_percentage': memory_percentage
                }
            except Exception as e:
                status_info['resources'] = {'error': str(e)}
            
            return status_info
            
        except docker.errors.NotFound:
            return {
                'name': container_name,
                'status': 'NOT_FOUND',
                'state': {'Status': 'not_found'},
                'port': port,
                'http_healthy': False,
                'health_data': 'Container not found'
            }
        except Exception as e:
            return {
                'name': container_name,
                'status': 'ERROR',
                'state': {'Status': 'error'},
                'port': port,
                'http_healthy': False,
                'health_data': f'Error: {str(e)}'
            }
    
    def calculate_cpu_percentage(self, stats: Dict) -> float:
        """Calculate CPU percentage from container stats"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0:
                cpu_percentage = (cpu_delta / system_delta) * \
                               len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                return round(cpu_percentage, 2)
        except (KeyError, ZeroDivisionError):
            pass
        return 0.0
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        status = {
            'timestamp': datetime.datetime.now().isoformat(),
            'total_containers': len(self.expected_containers),
            'containers': {},
            'summary': {
                'running': 0,
                'healthy': 0,
                'unhealthy': 0,
                'stopped': 0,
                'restarting': 0,
                'by_type': {
                    'orchestrator': {'total': 0, 'running': 0, 'healthy': 0},
                    'mcp': {'total': 0, 'running': 0, 'healthy': 0},
                    'agent': {'total': 0, 'running': 0, 'healthy': 0}
                }
            }
        }
        
        # Check each container with threading for speed
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_name = {
                executor.submit(self.check_container_health, name, info['port']): name
                for name, info in self.expected_containers.items()
            }
            
            for future in future_to_name:
                container_status = future.result()
                name = future_to_name[future]
                container_type = self.expected_containers[name]['type']
                
                status['containers'][name] = container_status
                
                # Update summary
                status['summary']['by_type'][container_type]['total'] += 1
                
                if container_status['status'] == 'running':
                    status['summary']['running'] += 1
                    status['summary']['by_type'][container_type]['running'] += 1
                    
                    if container_status.get('http_healthy', False):
                        status['summary']['healthy'] += 1
                        status['summary']['by_type'][container_type]['healthy'] += 1
                    else:
                        status['summary']['unhealthy'] += 1
                elif container_status['status'] == 'restarting':
                    status['summary']['restarting'] += 1
                else:
                    status['summary']['stopped'] += 1
        
        self.last_update = status['timestamp']
        return status
    
    def print_dashboard(self, status: Dict):
        """Print a formatted dashboard"""
        print("\n" + "="*80)
        print("🚀 FLASH LOAN SYSTEM - 32 CONTAINER ORCHESTRATION DASHBOARD")
        print("="*80)
        print(f"📊 Last Update: {status['timestamp']}")
        print(f"📋 Total Containers: {status['total_containers']}")
        
        # Summary
        summary = status['summary']
        print(f"\n📈 SYSTEM SUMMARY:")
        print(f"   ✅ Running: {summary['running']}")
        print(f"   💚 Healthy: {summary['healthy']}")
        print(f"   ❌ Unhealthy: {summary['unhealthy']}")
        print(f"   ⏸️  Stopped: {summary['stopped']}")
        print(f"   🔄 Restarting: {summary['restarting']}")
        
        # By Type Summary
        print(f"\n📊 BY TYPE:")
        for type_name, type_data in summary['by_type'].items():
            health_rate = (type_data['healthy'] / type_data['total'] * 100) if type_data['total'] > 0 else 0
            print(f"   {type_name.upper()}: {type_data['healthy']}/{type_data['total']} healthy ({health_rate:.1f}%)")
        
        # Container Details
        print(f"\n📋 CONTAINER DETAILS:")
        for container_type in ['orchestrator', 'mcp', 'agent']:
            type_containers = {name: data for name, data in status['containers'].items() 
                             if self.expected_containers[name]['type'] == container_type}
            
            if type_containers:
                print(f"\n   {container_type.upper()} CONTAINERS:")
                for name, data in type_containers.items():
                    status_icon = {
                        'running': '✅' if data.get('http_healthy', False) else '⚠️',
                        'restarting': '🔄',
                        'exited': '❌',
                        'created': '⏳',
                        'NOT_FOUND': '❓'
                    }.get(data['status'], '❓')
                    
                    port = data.get('port', 'N/A')
                    resources = data.get('resources', {})
                    cpu = resources.get('cpu_percentage', 0)
                    memory = resources.get('memory_percentage', 0)
                    
                    print(f"     {status_icon} {name:<35} Port:{port:<5} "
                          f"CPU:{cpu:>6.1f}% MEM:{memory:>6.1f}% {data['status']}")
        
        print("\n" + "="*80)
        
        # Health Issues
        unhealthy = [(name, data) for name, data in status['containers'].items() 
                    if data['status'] == 'running' and not data.get('http_healthy', False)]
        
        if unhealthy:
            print("⚠️  HEALTH ISSUES:")
            for name, data in unhealthy:
                print(f"   {name}: {data.get('health_data', 'Unknown issue')}")
            print()
    
    def save_status_report(self, status: Dict, filename: str = None):
        """Save status to JSON file"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_status_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(status, f, indent=2)
        
        print(f"📄 Status report saved to: {filename}")
    
    def monitor_loop(self, interval: int = 30, save_reports: bool = False):
        """Continuous monitoring loop"""
        print("🔍 Starting continuous monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                status = self.get_system_status()
                self.print_dashboard(status)
                
                if save_reports:
                    self.save_status_report(status)
                
                print(f"\n⏰ Next update in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Error in monitoring loop: {e}")
    
    def get_quick_status(self) -> str:
        """Get a quick status summary"""
        status = self.get_system_status()
        summary = status['summary']
        return (f"System Status: {summary['healthy']}/{summary['running']} containers healthy "
                f"({summary['healthy']/len(self.expected_containers)*100:.1f}% system health)")

def main():
    monitor = FlashLoanSystemMonitor()
    
    print("🔧 Flash Loan System Monitor")
    print("Options:")
    print("1. Quick Status Check")
    print("2. Detailed Status Report")
    print("3. Continuous Monitoring")
    print("4. Save Status Report")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print(monitor.get_quick_status())
    
    elif choice == "2":
        status = monitor.get_system_status()
        monitor.print_dashboard(status)
    
    elif choice == "3":
        interval = input("Monitor interval in seconds (default 30): ").strip()
        interval = int(interval) if interval.isdigit() else 30
        save_reports = input("Save reports? (y/n): ").strip().lower() == 'y'
        monitor.monitor_loop(interval, save_reports)
    
    elif choice == "4":
        status = monitor.get_system_status()
        monitor.print_dashboard(status)
        monitor.save_status_report(status)
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
