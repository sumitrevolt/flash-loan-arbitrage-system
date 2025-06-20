#!/usr/bin/env python3
"""
Docker Service Health Checker
============================

Monitors the health of all Docker-based MCP servers and AI agents.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List

class DockerHealthChecker:
    """Health checker for Docker-based services"""
    
    def __init__(self):
        # Docker MCP Services - Using actual running containers
        self.mcp_services = {
            'auth-manager': 'http://localhost:8100',
            'blockchain': 'http://localhost:8101',
            'defi-analyzer': 'http://localhost:8102',
            'flash-loan': 'http://localhost:8103',
            'arbitrage': 'http://localhost:8104',
            'liquidity': 'http://localhost:8105',
            'price-feed': 'http://localhost:8106',
            'risk-manager': 'http://localhost:8107',
            'portfolio': 'http://localhost:8108',
            'api-client': 'http://localhost:8109',
            'database': 'http://localhost:8110',
            'cache-manager': 'http://localhost:8111',
            'file-processor': 'http://localhost:8112',
            'notification': 'http://localhost:8113',
            'monitoring': 'http://localhost:8114',
            'security': 'http://localhost:8115',
            'data-analyzer': 'http://localhost:8116',
            'web-scraper': 'http://localhost:8117',
            'task-queue': 'http://localhost:8118',
            'filesystem': 'http://localhost:8119',
            'coordinator': 'http://localhost:8120'
        }
        
        # AI Agents - Using actual running containers
        self.ai_agents = {
            'analyzer': 'http://localhost:8201',
            'executor': 'http://localhost:8202',
            'risk-manager': 'http://localhost:8203',
            'monitor': 'http://localhost:8204',
            'data-collector': 'http://localhost:8205',
            'arbitrage-bot': 'http://localhost:8206',
            'liquidity-manager': 'http://localhost:8207',
            'reporter': 'http://localhost:8208',
            'healer': 'http://localhost:8209',
            'coordinator': 'http://localhost:8200'
        }
    
    async def check_service_health(self, name: str, url: str) -> Dict:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=5) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return {
                                'name': name,
                                'url': url,
                                'status': 'healthy',
                                'response_time_ms': round(response_time, 2),
                                'details': data
                            }
                        except:
                            return {
                                'name': name,
                                'url': url,
                                'status': 'healthy',
                                'response_time_ms': round(response_time, 2),
                                'details': {'message': 'OK'}
                            }
                    else:
                        return {
                            'name': name,
                            'url': url,
                            'status': 'unhealthy',
                            'response_time_ms': round(response_time, 2),
                            'error': f"HTTP {response.status}"
                        }
                        
        except asyncio.TimeoutError:
            return {
                'name': name,
                'url': url,
                'status': 'timeout',
                'response_time_ms': 5000,
                'error': 'Request timeout'
            }
        except Exception as e:
            return {
                'name': name,
                'url': url,
                'status': 'unreachable',
                'response_time_ms': (time.time() - start_time) * 1000,
                'error': str(e)
            }
    
    async def check_all_services(self) -> Dict:
        """Check health of all services"""
        print(f"\n🔍 Health Check Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Prepare tasks for concurrent health checks
        tasks = []
        
        # Add MCP service tasks
        for name, url in self.mcp_services.items():
            tasks.append(self.check_service_health(f"MCP-{name}", url))
        
        # Add AI agent tasks
        for name, url in self.ai_agents.items():
            tasks.append(self.check_service_health(f"Agent-{name}", url))
        
        # Execute all health checks concurrently
        results = await asyncio.gather(*tasks)
        
        # Categorize results
        healthy = [r for r in results if r['status'] == 'healthy']
        unhealthy = [r for r in results if r['status'] in ['unhealthy', 'timeout', 'unreachable']]
        
        # Print results
        print(f"\n✅ HEALTHY SERVICES ({len(healthy)}):")
        print("-" * 40)
        for service in sorted(healthy, key=lambda x: x['name']):
            print(f"  {service['name']:<25} | {service['response_time_ms']:>6.1f}ms | {service['url']}")
        
        if unhealthy:
            print(f"\n❌ UNHEALTHY SERVICES ({len(unhealthy)}):")
            print("-" * 40)
            for service in sorted(unhealthy, key=lambda x: x['name']):
                print(f"  {service['name']:<25} | {service['status']:<12} | {service.get('error', 'Unknown error')}")
        
        # Summary
        total_services = len(results)
        healthy_count = len(healthy)
        health_percentage = (healthy_count / total_services) * 100 if total_services > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print("-" * 40)
        print(f"  Total Services:     {total_services}")
        print(f"  Healthy Services:   {healthy_count}")
        print(f"  Unhealthy Services: {len(unhealthy)}")
        print(f"  Health Percentage:  {health_percentage:.1f}%")
        
        # Average response time for healthy services
        if healthy:
            avg_response_time = sum(s['response_time_ms'] for s in healthy) / len(healthy)
            print(f"  Avg Response Time:  {avg_response_time:.1f}ms")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_services': total_services,
            'healthy_services': healthy_count,
            'unhealthy_services': len(unhealthy),
            'health_percentage': health_percentage,
            'healthy': healthy,
            'unhealthy': unhealthy
        }
    
    async def test_arbitrage_endpoints(self):
        """Test specific arbitrage-related endpoints"""
        print(f"\n🎯 Testing Arbitrage Endpoints")
        print("=" * 80)
        
        # Test critical services for arbitrage
        critical_services = {
            'price-feed': self.mcp_services['price-feed'],
            'arbitrage': self.mcp_services['arbitrage'],
            'flash-loan': self.mcp_services['flash-loan'],
            'liquidity': self.mcp_services['liquidity'],
            'risk-manager': self.mcp_services['risk-manager'],
            'arbitrage-bot': self.ai_agents['arbitrage-bot'],
            'executor': self.ai_agents['executor']
        }
        
        for name, url in critical_services.items():
            try:
                async with aiohttp.ClientSession() as session:
                    # Test health endpoint
                    async with session.get(f"{url}/health", timeout=3) as response:
                        if response.status == 200:
                            print(f"  ✅ {name:<20} | Health: OK")
                            
                            # Test specific endpoints based on service type
                            if 'price' in name:
                                # Test price endpoint
                                test_data = {'tokens': ['WMATIC', 'USDC']}
                                async with session.post(f"{url}/get_prices", json=test_data, timeout=5) as test_response:
                                    if test_response.status == 200:
                                        print(f"     {' '*20} | Price API: OK")
                                    else:
                                        print(f"     {' '*20} | Price API: Error {test_response.status}")
                            
                            elif 'arbitrage' in name and 'mcp' in url:
                                # Test arbitrage scanning
                                test_data = {
                                    'tokens': ['WMATIC', 'USDC'],
                                    'dexs': ['QuickSwap', 'SushiSwap'],
                                    'min_profit_usd': 3.0
                                }
                                async with session.post(f"{url}/scan_opportunities", json=test_data, timeout=10) as test_response:
                                    if test_response.status == 200:
                                        print(f"     {' '*20} | Scan API: OK")
                                    else:
                                        print(f"     {' '*20} | Scan API: Error {test_response.status}")
                        else:
                            print(f"  ❌ {name:<20} | Health: Error {response.status}")
                            
            except Exception as e:
                print(f"  ❌ {name:<20} | Error: {str(e)[:50]}")
    
    async def continuous_monitoring(self, interval_seconds: int = 60):
        """Continuously monitor services"""
        print(f"🔄 Starting continuous monitoring (every {interval_seconds}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                await self.check_all_services()
                print(f"\n⏱️  Next check in {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")

async def main():
    """Main entry point"""
    import sys
    
    checker = DockerHealthChecker()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'monitor':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            await checker.continuous_monitoring(interval)
        elif command == 'test':
            await checker.test_arbitrage_endpoints()
        elif command == 'quick':
            # Quick health check of critical services only
            critical = ['flash-loan', 'arbitrage', 'price-feed', 'arbitrage-bot']
            print("🚀 Quick Health Check - Critical Services Only")
            print("=" * 50)
            
            for service in critical:
                if service in checker.mcp_services:
                    result = await checker.check_service_health(f"MCP-{service}", checker.mcp_services[service])
                elif service in checker.ai_agents:
                    result = await checker.check_service_health(f"Agent-{service}", checker.ai_agents[service])
                else:
                    continue
                
                status_icon = "✅" if result['status'] == 'healthy' else "❌"
                print(f"  {status_icon} {result['name']:<25} | {result['status']}")
        else:
            print("Usage:")
            print("  python docker_health_checker.py              # Single health check")
            print("  python docker_health_checker.py monitor [60] # Continuous monitoring")
            print("  python docker_health_checker.py test         # Test arbitrage endpoints")
            print("  python docker_health_checker.py quick        # Quick check critical services")
            return
    else:
        # Single comprehensive health check
        result = await checker.check_all_services()
        
        # Save results to file
        with open('health_check_results.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Results saved to health_check_results.json")

if __name__ == "__main__":
    asyncio.run(main())
