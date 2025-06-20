#!/usr/bin/env python3
"""
Comprehensive Flash Loan System Status Verification
Tests all MCP servers and AI agents regardless of Docker health check status
"""

import requests
import socket
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlashLoanSystemVerifier:
    """Comprehensive system status verification"""
    
    def __init__(self):
        self.results = {}
        self.total_services = 0
        self.healthy_services = 0
        
    def test_port_connectivity(self, host: str = 'localhost', port: int = None, timeout: int = 5) -> bool:
        """Test if a port is accepting connections"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result: str = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"Port {port} connection failed: {e}")
            return False
    
    def test_http_health(self, url: str, timeout: int = 10) -> Tuple[bool, Optional[Dict]]:
        """Test HTTP health endpoint"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return True, data
                except:
                    return True, {"status": "responding"}
            return False, None
        except Exception as e:
            logger.debug(f"HTTP health check failed for {url}: {e}")
            return False, None
    
    def verify_service(self, service_name: str, port: int, service_type: str) -> Dict:
        """Verify a single service"""
        result: str = {
            'name': service_name,
            'port': port,
            'type': service_type,
            'port_open': False,
            'http_healthy': False,
            'response_data': None,
            'status': 'unknown'
        }
        
        # Test port connectivity
        result['port_open'] = self.test_port_connectivity(port=port)
        
        if result['port_open']:
            # Test HTTP health endpoint
            health_url = f"http://localhost:{port}/health"
            http_ok, response_data = self.test_http_health(health_url)
            result['http_healthy'] = http_ok
            result['response_data'] = response_data
            
            if http_ok:
                result['status'] = 'healthy'
            else:
                result['status'] = 'port_open_no_http'
        else:
            result['status'] = 'port_closed'
        
        return result
    
    def get_service_definitions(self) -> Dict[str, List[Tuple[str, int]]]:
        """Define all services to verify"""
        return {
            'infrastructure': [
                ('PostgreSQL', 5432),
                ('Redis', 6379),
                ('RabbitMQ', 5672),
                ('RabbitMQ Management', 15672)
            ],
            'mcp_servers': [
                ('Flash Loan MCP', 4001),
                ('Web3 Provider MCP', 4002),
                ('DEX Price Server', 4003),
                ('Arbitrage Detector MCP', 4004),
                ('Foundry Integration MCP', 4005),
                ('EVM MCP Server', 4006),
                ('Matic MCP Server', 4007),
                ('GitHub MCP Server', 4008),
                ('Context7 MCP Server', 4009),
                ('Enhanced Copilot MCP', 4010),
                ('Price Oracle MCP', 4011),
                ('DEX Services MCP', 4012),
                ('Notification Service', 4013),
                ('Audit Logger', 4014),
                ('Liquidity Monitor', 4015),
                ('Market Data Feed', 4016),
                ('Risk Manager', 4017),
                ('Performance Monitor', 4018),
                ('Analytics Engine', 4019),
                ('Code Indexer', 4020),
                ('Health Checker', 4021)
            ],
            'ai_agents': [
                ('Coordinator Agent', 5001),
                ('Arbitrage Agent', 5002),
                ('Monitoring Agent', 5003),
                ('Builder Agent', 5004),
                ('AAVE Executor', 5005),
                ('Contract Executor', 5006)
            ]
        }
    
    def verify_all_services(self, max_workers: int = 10) -> Dict:
        """Verify all services concurrently"""
        print("🔍 Flash Loan System Comprehensive Verification")
        print("=" * 60)
        
        service_definitions = self.get_service_definitions()
        all_services = []
        
        # Flatten all services for concurrent processing
        for service_type, services in service_definitions.items():
            for service_name, port in services:
                all_services.append((service_name, port, service_type))
        
        self.total_services = len(all_services)
        
        # Verify services concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_service = {
                executor.submit(self.verify_service, name, port, stype): (name, port, stype)
                for name, port, stype in all_services
            }
            
            for future in as_completed(future_to_service):
                service_name, port, service_type = future_to_service[future]
                try:
                    result: str = future.result()
                    self.results[service_name] = result
                    if result['status'] == 'healthy':
                        self.healthy_services += 1
                except Exception as e:
                    logger.error(f"Service verification failed for {service_name}: {e}")
                    self.results[service_name] = {
                        'name': service_name,
                        'port': port,
                        'type': service_type,
                        'status': 'error',
                        'error': str(e)
                    }
        
        return self.results
    
    def print_detailed_report(self):
        """Print detailed verification report"""
        service_definitions = self.get_service_definitions()
        
        for service_type, services in service_definitions.items():
            print(f"\n📊 {service_type.replace('_', ' ').title()}:")
            print("-" * 50)
            
            for service_name, port in services:
                if service_name in self.results:
                    result: str = self.results[service_name]
                    status = result['status']
                    
                    if status == 'healthy':
                        icon = "✅"
                        status_text = "HEALTHY"
                    elif status == 'port_open_no_http':
                        icon = "🟡"
                        status_text = "PORT OPEN (No HTTP)"
                    elif status == 'port_closed':
                        icon = "❌"
                        status_text = "PORT CLOSED"
                    else:
                        icon = "❓"
                        status_text = "UNKNOWN"
                    
                    print(f"  {icon} {service_name} (:{port}) - {status_text}")
                    
                    # Show response data if available
                    if result.get('response_data'):
                        response = result['response_data']
                        if isinstance(response, dict) and 'service' in response:
                            print(f"     └─ Service: {response.get('service', 'N/A')}")
                else:
                    print(f"  ❓ {service_name} (:{port}) - NOT TESTED")
    
    def generate_summary_report(self) -> Dict:
        """Generate summary report"""
        health_percentage = (self.healthy_services / self.total_services * 100) if self.total_services > 0 else 0
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_services': self.total_services,
            'healthy_services': self.healthy_services,
            'health_percentage': round(health_percentage, 1),
            'status': 'operational' if health_percentage >= 80 else 'degraded' if health_percentage >= 50 else 'critical'
        }
        
        return summary
    
    def save_detailed_report(self, filename: str = 'system_verification_report.json'):
        """Save detailed report to JSON file"""
        report = {
            'verification_time': datetime.now().isoformat(),
            'summary': self.generate_summary_report(),
            'detailed_results': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {filename}")

def main():
    """Main verification function"""
    verifier = FlashLoanSystemVerifier()
    
    print("🚀 Starting Flash Loan System Verification...")
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verify all services
    results = verifier.verify_all_services()
    
    # Print detailed report
    verifier.print_detailed_report()
    
    # Generate and print summary
    summary = verifier.generate_summary_report()
    print(f"\n📊 SYSTEM SUMMARY:")
    print("=" * 40)
    print(f"🎯 Total Services: {summary['total_services']}")
    print(f"✅ Healthy Services: {summary['healthy_services']}")
    print(f"📈 Health Percentage: {summary['health_percentage']}%")
    print(f"🏥 System Status: {summary['status'].upper()}")
    
    # Status interpretation
    if summary['health_percentage'] >= 95:
        print("🎉 EXCELLENT: System is performing optimally!")
    elif summary['health_percentage'] >= 80:
        print("👍 GOOD: System is operational with minor issues.")
    elif summary['health_percentage'] >= 50:
        print("⚠️  CAUTION: System is degraded, some services need attention.")
    else:
        print("🚨 CRITICAL: System requires immediate attention!")
    
    # Save detailed report
    verifier.save_detailed_report()
    
    # Return status code for automation
    return 0 if summary['health_percentage'] >= 80 else 1

if __name__ == "__main__":
    exit(main())
