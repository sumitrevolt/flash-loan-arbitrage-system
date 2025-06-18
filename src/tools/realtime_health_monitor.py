#!/usr/bin/env python3
"""
Real-time Flash Loan System Health Monitor
Continuously monitors system health and provides live updates
"""

import time
import os
import sys
import json
import requests
import socket
from datetime import datetime
from typing import Dict, List
import threading
from concurrent.futures import ThreadPoolExecutor

class RealTimeHealthMonitor:
    """Real-time system health monitoring"""
    
    def __init__(self):
        self.running = True
        self.last_results = {}
        self.service_definitions = self.get_service_definitions()
        
    def get_service_definitions(self) -> Dict[str, List[tuple]]:
        """Define services to monitor"""
        return {
            'Infrastructure': [
                ('PostgreSQL', 5432, 'tcp'),
                ('Redis', 6379, 'tcp'), 
                ('RabbitMQ', 5672, 'tcp'),
                ('RabbitMQ Mgmt', 15672, 'tcp')
            ],
            'MCP Servers': [
                ('Flash Loan MCP', 4001, 'http'),
                ('Web3 Provider', 4002, 'http'),
                ('DEX Price Server', 4003, 'http'),
                ('Arbitrage Detector', 4004, 'http'),
                ('GitHub MCP', 4008, 'http'),
                ('Context7 MCP', 4009, 'http'),
                ('Enhanced Copilot', 4010, 'http'),
                ('Health Checker', 4021, 'http'),
            ],
            'AI Agents': [
                ('Coordinator Agent', 5001, 'http'),
                ('Arbitrage Agent', 5002, 'http'),
                ('Monitoring Agent', 5003, 'http'),
                ('Builder Agent', 5004, 'http'),
                ('AAVE Executor', 5005, 'http'),
                ('Contract Executor', 5006, 'http'),
            ]
        }
    
    def test_tcp_port(self, port: int, timeout: int = 2) -> bool:
        """Test TCP port connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result: str = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def test_http_health(self, port: int, timeout: int = 3) -> tuple:
        """Test HTTP health endpoint"""
        try:
            response = requests.get(f'http://localhost:{port}/health', timeout=timeout)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return True, data.get('service', 'unknown')
                except:
                    return True, 'responding'
            return False, 'http_error'
        except:
            return False, 'no_response'
    
    def check_service(self, name: str, port: int, check_type: str) -> Dict:
        """Check individual service"""
        if check_type == 'tcp':
            is_healthy = self.test_tcp_port(port)
            service_info = 'N/A'
        else:  # http
            is_healthy, service_info = self.test_http_health(port)
        
        return {
            'name': name,
            'port': port,
            'healthy': is_healthy,
            'service_info': service_info,
            'check_type': check_type
        }
    
    def monitor_cycle(self) -> Dict:
        """Run one monitoring cycle"""
        results = {'categories': {}, 'summary': {}}
        total_services = 0
        healthy_services = 0
        
        for category, services in self.service_definitions.items():
            category_results = []
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(self.check_service, name, port, check_type)
                    for name, port, check_type in services
                ]
                
                for future in futures:
                    try:
                        result: str = future.result(timeout=5)
                        category_results.append(result)
                        total_services += 1
                        if result['healthy']:
                            healthy_services += 1
                    except Exception as e:
                        print(f"Error checking service: {e}")
            
            results['categories'][category] = category_results
        
        # Calculate summary
        health_percentage = (healthy_services / total_services * 100) if total_services > 0 else 0
        results['summary'] = {
            'total': total_services,
            'healthy': healthy_services,
            'percentage': round(health_percentage, 1),
            'status': 'HEALTHY' if health_percentage >= 80 else 'DEGRADED' if health_percentage >= 50 else 'CRITICAL'
        }
        
        return results
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        # WARNING: This is a security risk
        # WARNING: This is a security risk
    
    def print_header(self):
        """Print monitoring header"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("🏦 Flash Loan System - Real-Time Health Monitor")
        print("=" * 65)
        print(f"⏰ Last Update: {now}")
        print(f"🔄 Press Ctrl+C to stop monitoring")
        print()
    
    def print_results(self, results: Dict):
        """Print monitoring results"""
        summary = results['summary']
        
        # Print summary
        status_icon = "🟢" if summary['status'] == 'HEALTHY' else "🟡" if summary['status'] == 'DEGRADED' else "🔴"
        print(f"📊 SYSTEM STATUS: {status_icon} {summary['status']}")
        print(f"   Total: {summary['total']} | Healthy: {summary['healthy']} | {summary['percentage']}%")
        print()
        
        # Print detailed results by category
        for category, services in results['categories'].items():
            print(f"📋 {category}:")
            for service in services:
                icon = "✅" if service['healthy'] else "❌"
                port_info = f":{service['port']}"
                
                if service['check_type'] == 'http' and service['healthy']:
                    service_info = f" ({service['service_info']})"
                else:
                    service_info = ""
                
                print(f"   {icon} {service['name']}{port_info}{service_info}")
            print()
    
    def run(self, update_interval: int = 10):
        """Run the monitoring loop"""
        print("🚀 Starting Flash Loan System Health Monitor...")
        print(f"📱 Update interval: {update_interval} seconds")
        print("⏳ Performing initial health check...")
        
        try:
            while self.running:
                self.clear_screen()
                self.print_header()
                
                # Run monitoring cycle
                results = self.monitor_cycle()
                self.print_results(results)
                
                # Show next update time
                next_update = datetime.now()
                next_update = next_update.replace(second=next_update.second + update_interval)
                print(f"⏳ Next update: {next_update.strftime('%H:%M:%S')}")
                
                # Wait for next cycle
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            self.running = False
        except Exception as e:
            print(f"\n\n❌ Monitoring error: {e}")
    
    def single_check(self):
        """Run a single health check"""
        print("🔍 Running single health check...")
        results = self.monitor_cycle()
        self.print_results(results)
        return results

def main():
    """Main function"""
    monitor = RealTimeHealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Single check mode
        results = monitor.single_check()
        return 0 if results['summary']['percentage'] >= 80 else 1
    else:
        # Continuous monitoring mode
        update_interval = 15  # seconds
        if len(sys.argv) > 1:
            try:
                update_interval = int(sys.argv[1])
            except ValueError:
                print("Invalid interval, using default 15 seconds")
        
        monitor.run(update_interval)
        return 0

if __name__ == "__main__":
    exit(main())
