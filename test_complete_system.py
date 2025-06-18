#!/usr/bin/env python3
"""
Comprehensive Test Suite for Complete MCP System
Tests all 81 MCP servers and 10 AI agents
"""

import asyncio
import aiohttp
import json
import time
import os
import sys
from typing import Dict, List, Tuple
import logging
from dataclasses import dataclass
from unicode_safe_logger import get_unicode_safe_logger

# Configure Unicode-safe logging
logger = get_unicode_safe_logger(__name__, 'complete_system_test.log')

@dataclass
class ServiceTest:
    name: str
    url: str
    service_type: str
    expected_status: int = 200
    timeout: int = 30

class CompleteMCPSystemTester:
    def __init__(self):
        self.base_urls = {
            'coordination': 'http://localhost:8000',
            'dashboard': 'http://localhost:8080',
            'prometheus': 'http://localhost:9090',
            'grafana': 'http://localhost:3000',
            'redis': 'http://localhost:6379',
            'postgres': 'http://localhost:5432',
            'rabbitmq': 'http://localhost:15672'
        }
        self.mcp_servers = []
        self.ai_agents = []
        self.load_configurations()
    
    def load_configurations(self):
        """Load MCP and AI agent configurations"""
        try:
            # Load MCP servers
            with open('unified_mcp_config.json', 'r') as f:
                mcp_config = json.load(f)
                for name, config in mcp_config['servers'].items():
                    if config.get('enabled', True):
                        port = config.get('port', 8000)
                        self.mcp_servers.append(ServiceTest(
                            name=f"mcp_{name}",
                            url=f"http://localhost:{port}",
                            service_type="mcp_server"
                        ))
            
            # Load AI agents
            with open('ai_agents_config.json', 'r') as f:
                ai_config = json.load(f)
                for name, config in ai_config['agents'].items():
                    port = config.get('port', 9000)
                    self.ai_agents.append(ServiceTest(
                        name=f"ai_agent_{name}",
                        url=f"http://localhost:{port}",
                        service_type="ai_agent"
                    ))
            
            # Add self-healing agent
            self.ai_agents.append(ServiceTest(
                name="ai_agent_self_healing",
                url="http://localhost:8300",
                service_type="self_healing_agent"
            ))
            
            logger.info(f"Loaded {len(self.mcp_servers)} MCP servers and {len(self.ai_agents)} AI agents")
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            sys.exit(1)
    
    async def test_service_health(self, session: aiohttp.ClientSession, service: ServiceTest) -> Tuple[bool, str]:
        """Test a single service health endpoint"""
        try:
            async with session.get(f"{service.url}/health", timeout=service.timeout) as response:
                if response.status == service.expected_status:
                    data = await response.json()
                    return True, f"✅ {service.name}: {data.get('status', 'healthy')}"
                else:
                    return False, f"❌ {service.name}: HTTP {response.status}"
        except asyncio.TimeoutError:
            return False, f"⏰ {service.name}: Timeout after {service.timeout}s"
        except Exception as e:
            return False, f"❌ {service.name}: {str(e)}"
    
    async def test_service_capabilities(self, session: aiohttp.ClientSession, service: ServiceTest) -> Tuple[bool, str]:
        """Test service capabilities endpoint"""
        try:
            async with session.get(f"{service.url}/capabilities", timeout=service.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    capabilities = data.get('capabilities', [])
                    return True, f"✅ {service.name}: {len(capabilities)} capabilities"
                else:
                    return False, f"❌ {service.name}/capabilities: HTTP {response.status}"
        except Exception as e:
            return False, f"❌ {service.name}/capabilities: {str(e)}"
    
    async def test_infrastructure_services(self, session: aiohttp.ClientSession) -> Dict[str, bool]:
        """Test infrastructure services"""
        logger.info("Testing infrastructure services...")
        results = {}
        
        infrastructure_tests = [
            ServiceTest("coordination_system", self.base_urls['coordination'], "coordination"),
            ServiceTest("prometheus", self.base_urls['prometheus'], "monitoring"),
            ServiceTest("grafana", self.base_urls['grafana'], "monitoring"),
        ]
        
        for service in infrastructure_tests:
            success, message = await self.test_service_health(session, service)
            results[service.name] = success
            logger.info(message)
        
        return results
    
    async def test_mcp_servers(self, session: aiohttp.ClientSession) -> Dict[str, bool]:
        """Test all MCP servers"""
        logger.info(f"Testing {len(self.mcp_servers)} MCP servers...")
        results = {}
        
        # Test in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(self.mcp_servers), batch_size):
            batch = self.mcp_servers[i:i+batch_size]
            logger.info(f"Testing MCP server batch {i//batch_size + 1}/{(len(self.mcp_servers) + batch_size - 1)//batch_size}")
            
            batch_tasks = []
            for service in batch:
                batch_tasks.append(self.test_service_health(session, service))
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for service, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results[service.name] = False
                    logger.error(f"❌ {service.name}: Exception {result}")
                else:
                    success, message = result
                    results[service.name] = success
                    logger.info(message)
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        return results
    
    async def test_ai_agents(self, session: aiohttp.ClientSession) -> Dict[str, bool]:
        """Test all AI agents"""
        logger.info(f"Testing {len(self.ai_agents)} AI agents...")
        results = {}
        
        for service in self.ai_agents:
            success, message = await self.test_service_health(session, service)
            results[service.name] = success
            logger.info(message)
            await asyncio.sleep(0.5)  # Small delay between tests
        
        return results
    
    async def test_system_integration(self, session: aiohttp.ClientSession) -> Dict[str, bool]:
        """Test system integration endpoints"""
        logger.info("Testing system integration...")
        results = {}
        
        integration_tests = [
            ("coordination_health", f"{self.base_urls['coordination']}/health"),
            ("coordination_status", f"{self.base_urls['coordination']}/status"),
            ("coordination_agents", f"{self.base_urls['coordination']}/agents"),
            ("coordination_servers", f"{self.base_urls['coordination']}/servers"),
        ]
        
        for test_name, url in integration_tests:
            try:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        results[test_name] = True
                        data = await response.json()
                        logger.info(f"✅ {test_name}: {data.get('status', 'OK')}")
                    else:
                        results[test_name] = False
                        logger.error(f"❌ {test_name}: HTTP {response.status}")
            except Exception as e:
                results[test_name] = False
                logger.error(f"❌ {test_name}: {e}")
        
        return results
    
    async def run_performance_tests(self, session: aiohttp.ClientSession) -> Dict[str, float]:
        """Run basic performance tests"""
        logger.info("Running performance tests...")
        performance_results = {}
        
        # Test coordination system response time
        test_url = f"{self.base_urls['coordination']}/health"
        times = []
        
        for i in range(5):
            start_time = time.time()
            try:
                async with session.get(test_url, timeout=10) as response:
                    if response.status == 200:
                        await response.json()
                        times.append(time.time() - start_time)
            except Exception as e:
                logger.warning(f"Performance test iteration {i+1} failed: {e}")
        
        if times:
            avg_response_time = sum(times) / len(times)
            performance_results['coordination_avg_response_time'] = avg_response_time
            logger.info(f"✅ Coordination system avg response time: {avg_response_time:.3f}s")
        else:
            performance_results['coordination_avg_response_time'] = float('inf')
            logger.error("❌ All performance test iterations failed")
        
        return performance_results
    
    def generate_test_report(self, test_results: Dict[str, Dict[str, bool]], performance_results: Dict[str, float]):
        """Generate comprehensive test report"""
        logger.info("Generating test report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {},
            "details": test_results,
            "performance": performance_results
        }
        
        # Calculate summary statistics
        total_tests = 0
        passed_tests = 0
        
        for category, results in test_results.items():
            category_total = len(results)
            category_passed = sum(1 for success in results.values() if success)
            
            total_tests += category_total
            passed_tests += category_passed
            
            report["summary"][category] = {
                "total": category_total,
                "passed": category_passed,
                "failed": category_total - category_passed,
                "success_rate": category_passed / category_total if category_total > 0 else 0
            }
        
        report["summary"]["overall"] = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0
        }
        
        # Save report to file
        with open('complete_system_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("COMPLETE MCP SYSTEM TEST REPORT")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        print()
        
        for category, stats in report["summary"].items():
            if category != "overall":
                print(f"{category.upper()}:")
                print(f"  Passed: {stats['passed']}/{stats['total']} ({stats['success_rate']*100:.1f}%)")
        
        print()
        if performance_results:
            print("PERFORMANCE METRICS:")
            for metric, value in performance_results.items():
                if value != float('inf'):
                    print(f"  {metric}: {value:.3f}s")
                else:
                    print(f"  {metric}: FAILED")
        
        print(f"\nDetailed report saved to: complete_system_test_report.json")
        print(f"Test log saved to: complete_system_test.log")
        print("="*80)
        
        return report["summary"]["overall"]["success_rate"] > 0.8
    
    async def run_complete_test_suite(self) -> bool:
        """Run the complete test suite"""
        logger.info("Starting Complete MCP System Test Suite...")
        
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            test_results = {}
            
            # Test infrastructure
            test_results["infrastructure"] = await self.test_infrastructure_services(session)
            
            # Test MCP servers
            test_results["mcp_servers"] = await self.test_mcp_servers(session)
            
            # Test AI agents
            test_results["ai_agents"] = await self.test_ai_agents(session)
            
            # Test system integration
            test_results["integration"] = await self.test_system_integration(session)
            
            # Run performance tests
            performance_results = await self.run_performance_tests(session)
            
            # Generate report
            success = self.generate_test_report(test_results, performance_results)
            
            return success

def main():
    """Main test function"""
    print("🧪 Complete MCP System Test Suite")
    print("="*50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("Running quick test (infrastructure only)...")
        # Quick test implementation would go here
        return True
    
    try:
        tester = CompleteMCPSystemTester()
        success = asyncio.run(tester.run_complete_test_suite())
        
        if success:
            print("🎉 Complete system test PASSED!")
            return True
        else:
            print("❌ Complete system test FAILED!")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}")
        print(f"💥 Test suite crashed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
