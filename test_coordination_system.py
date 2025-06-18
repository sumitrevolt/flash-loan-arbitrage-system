#!/usr/bin/env python3
"""
Coordination System Test Suite
==============================

Test the coordination between MCP servers, AI agents, LangChain, and AutoGen.
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoordinationSystemTester:
    """Test suite for the coordination system"""
    
    def __init__(self):
        self.base_urls = {
            'orchestrator': 'http://localhost:8000',
            'langchain': 'http://localhost:8001',
            'autogen': 'http://localhost:8002',
            'dashboard': 'http://localhost:8080'
        }
        
        self.mcp_servers = {
            'price_feed': 'http://localhost:8100',
            'flash_loan': 'http://localhost:8101',
            'dex_aggregator': 'http://localhost:8102',
            'evm_interaction': 'http://localhost:8103'
        }
        
        self.ai_agents = {
            'arbitrage_detector': 'http://localhost:9001',
            'risk_manager': 'http://localhost:9002',
            'flash_loan_optimizer': 'http://localhost:9003',
            'transaction_executor': 'http://localhost:9004',
            'market_analyzer': 'http://localhost:9005',
            'route_optimizer': 'http://localhost:9006',
            'gas_optimizer': 'http://localhost:9007',
            'liquidity_monitor': 'http://localhost:9008',
            'security_analyst': 'http://localhost:9009',
            'compliance_checker': 'http://localhost:9010'
        }
        
        self.test_results = []
        
    async def test_service_health(self, name: str, url: str) -> Dict[str, Any]:
        """Test if a service is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=5) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'service': name,
                            'status': 'healthy',
                            'url': url,
                            'response': result
                        }
                    else:
                        return {
                            'service': name,
                            'status': 'unhealthy',
                            'url': url,
                            'http_status': response.status
                        }
        except Exception as e:
            return {
                'service': name,
                'status': 'error',
                'url': url,
                'error': str(e)
            }
            
    async def test_coordination_task(self, task_description: str) -> Dict[str, Any]:
        """Test coordination task execution"""
        try:
            task_data = {
                'description': task_description,
                'timestamp': datetime.now().isoformat(),
                'test_mode': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['orchestrator']}/coordinate",
                    json=task_data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'task': task_description,
                            'status': 'success',
                            'result': result
                        }
                    else:
                        return {
                            'task': task_description,
                            'status': 'failed',
                            'http_status': response.status,
                            'error': await response.text()
                        }
        except Exception as e:
            return {
                'task': task_description,
                'status': 'error',
                'error': str(e)
            }
            
    async def test_langchain_coordination(self) -> Dict[str, Any]:
        """Test LangChain coordinator"""
        try:
            task_data = {
                'input': 'Test LangChain coordination with MCP servers',
                'test_mode': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['langchain']}/coordinate",
                    json=task_data,
                    timeout=20
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'service': 'langchain_coordinator',
                            'status': 'success',
                            'result': result
                        }
                    else:
                        return {
                            'service': 'langchain_coordinator',
                            'status': 'failed',
                            'http_status': response.status
                        }
        except Exception as e:
            return {
                'service': 'langchain_coordinator',
                'status': 'error',
                'error': str(e)
            }
            
    async def test_autogen_system(self) -> Dict[str, Any]:
        """Test AutoGen multi-agent system"""
        try:
            task_data = {
                'description': 'Test AutoGen multi-agent conversation',
                'agents': ['coordinator', 'analyzer', 'executor'],
                'test_mode': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['autogen']}/coordinate",
                    json=task_data,
                    timeout=20
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'service': 'autogen_system',
                            'status': 'success',
                            'result': result
                        }
                    else:
                        return {
                            'service': 'autogen_system',
                            'status': 'failed',
                            'http_status': response.status
                        }
        except Exception as e:
            return {
                'service': 'autogen_system',
                'status': 'error',
                'error': str(e)
            }
            
    async def test_mcp_server_interaction(self, server_name: str, url: str) -> Dict[str, Any]:
        """Test MCP server interaction"""
        try:
            test_query = {
                'query': f'Test query for {server_name}',
                'test_mode': True
            }
            
            async with aiohttp.ClientSession() as session:
                # Try both /query and /test endpoints
                endpoints = ['/query', '/test', '/status']
                
                for endpoint in endpoints:
                    try:
                        async with session.post(
                            f"{url}{endpoint}",
                            json=test_query,
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                return {
                                    'server': server_name,
                                    'status': 'success',
                                    'endpoint': endpoint,
                                    'result': result
                                }
                    except:
                        continue
                        
                return {
                    'server': server_name,
                    'status': 'no_valid_endpoint',
                    'url': url
                }
                
        except Exception as e:
            return {
                'server': server_name,
                'status': 'error',
                'error': str(e)
            }
            
    async def test_agent_coordination(self, agent_name: str, url: str) -> Dict[str, Any]:
        """Test AI agent coordination"""
        try:
            task_data = {
                'task': f'Test coordination for {agent_name}',
                'type': 'test',
                'description': f'Testing {agent_name} agent functionality'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{url}/coordinate",
                    json=task_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'agent': agent_name,
                            'status': 'success',
                            'result': result
                        }
                    else:
                        return {
                            'agent': agent_name,
                            'status': 'failed',
                            'http_status': response.status
                        }
        except Exception as e:
            return {
                'agent': agent_name,
                'status': 'error',
                'error': str(e)
            }
            
    async def run_comprehensive_tests(self):
        """Run comprehensive test suite"""
        logger.info("Starting comprehensive coordination system tests...")
        
        # Test 1: Health checks for all services
        logger.info("🏥 Testing service health...")
        health_tests = []
        
        # Test main services
        for name, url in self.base_urls.items():
            health_tests.append(self.test_service_health(name, url))
            
        # Test MCP servers
        for name, url in self.mcp_servers.items():
            health_tests.append(self.test_service_health(name, url))
            
        # Test AI agents
        for name, url in self.ai_agents.items():
            health_tests.append(self.test_service_health(name, url))
            
        health_results = await asyncio.gather(*health_tests, return_exceptions=True)
        self.test_results.extend(health_results)
        
        # Test 2: Coordination tasks
        logger.info("🎯 Testing coordination tasks...")
        coordination_tasks = [
            "Analyze arbitrage opportunities between QuickSwap and SushiSwap",
            "Optimize flash loan parameters for USDC-WETH arbitrage",
            "Assess risk factors for $5000 flash loan on Polygon",
            "Monitor liquidity changes in major DEX pools"
        ]
        
        coordination_tests = []
        for task in coordination_tasks:
            coordination_tests.append(self.test_coordination_task(task))
            
        coordination_results = await asyncio.gather(*coordination_tests, return_exceptions=True)
        self.test_results.extend(coordination_results)
        
        # Test 3: LangChain coordination
        logger.info("🧠 Testing LangChain coordination...")
        langchain_result = await self.test_langchain_coordination()
        self.test_results.append(langchain_result)
        
        # Test 4: AutoGen system
        logger.info("🤖 Testing AutoGen system...")
        autogen_result = await self.test_autogen_system()
        self.test_results.append(autogen_result)
        
        # Test 5: MCP server interactions
        logger.info("🔧 Testing MCP server interactions...")
        mcp_tests = []
        for name, url in self.mcp_servers.items():
            mcp_tests.append(self.test_mcp_server_interaction(name, url))
            
        mcp_results = await asyncio.gather(*mcp_tests, return_exceptions=True)
        self.test_results.extend(mcp_results)
        
        # Test 6: Agent coordination
        logger.info("🎭 Testing AI agent coordination...")
        agent_tests = []
        for name, url in self.ai_agents.items():
            agent_tests.append(self.test_agent_coordination(name, url))
            
        agent_results = await asyncio.gather(*agent_tests, return_exceptions=True)
        self.test_results.extend(agent_results)
        
        logger.info("✅ All tests completed!")
        
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if isinstance(r, dict) and r.get('status') in ['success', 'healthy']])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Categorize results
        categorized_results = {
            'health_checks': [],
            'coordination_tasks': [],
            'langchain_tests': [],
            'autogen_tests': [],
            'mcp_server_tests': [],
            'agent_tests': []
        }
        
        for result in self.test_results:
            if isinstance(result, dict):
                if 'service' in result:
                    if result['service'] == 'langchain_coordinator':
                        categorized_results['langchain_tests'].append(result)
                    elif result['service'] == 'autogen_system':
                        categorized_results['autogen_tests'].append(result)
                    else:
                        categorized_results['health_checks'].append(result)
                elif 'task' in result:
                    categorized_results['coordination_tasks'].append(result)
                elif 'server' in result:
                    categorized_results['mcp_server_tests'].append(result)
                elif 'agent' in result:
                    categorized_results['agent_tests'].append(result)
                else:
                    categorized_results['health_checks'].append(result)
                    
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': f"{success_rate:.1f}%",
                'timestamp': datetime.now().isoformat()
            },
            'categorized_results': categorized_results,
            'recommendations': self._generate_recommendations(categorized_results)
        }
        
        return report
        
    def _generate_recommendations(self, results: Dict[str, List]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check health status
        health_issues = [r for r in results['health_checks'] if r.get('status') != 'healthy']
        if health_issues:
            recommendations.append("Some services are not responding properly. Check Docker containers and logs.")
            
        # Check coordination tasks
        coord_failures = [r for r in results['coordination_tasks'] if r.get('status') != 'success']
        if coord_failures:
            recommendations.append("Coordination tasks are failing. Verify MCP server and agent connectivity.")
            
        # Check LangChain
        langchain_issues = [r for r in results['langchain_tests'] if r.get('status') != 'success']
        if langchain_issues:
            recommendations.append("LangChain coordinator has issues. Check Ollama service and model availability.")
            
        # Check AutoGen
        autogen_issues = [r for r in results['autogen_tests'] if r.get('status') != 'success']
        if autogen_issues:
            recommendations.append("AutoGen system has issues. Verify API keys and service configuration.")
            
        if not recommendations:
            recommendations.append("All systems are functioning properly! 🎉")
            
        return recommendations
        
    def print_test_report(self):
        """Print formatted test report"""
        report = self.generate_test_report()
        
        print("\n" + "="*80)
        print("DOCKER COORDINATION SYSTEM - TEST REPORT")
        print("="*80)
        
        summary = report['test_summary']
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Successful: {summary['successful_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Success Rate: {summary['success_rate']}")
        print(f"   Timestamp: {summary['timestamp']}")
        
        # Print category results
        categories = {
            'health_checks': '🏥 Health Checks',
            'coordination_tasks': '🎯 Coordination Tasks',
            'langchain_tests': '🧠 LangChain Tests',
            'autogen_tests': '🤖 AutoGen Tests',
            'mcp_server_tests': '🔧 MCP Server Tests',
            'agent_tests': '🎭 Agent Tests'
        }
        
        for category, title in categories.items():
            results = report['categorized_results'][category]
            if results:
                print(f"\n{title}:")
                for result in results:
                    status_icon = "✅" if result.get('status') in ['success', 'healthy'] else "❌"
                    name = result.get('service', result.get('agent', result.get('server', result.get('task', 'Unknown'))))
                    print(f"   {status_icon} {name}")
                    
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
            
        print("\n" + "="*80)
        
        # Save report to file
        with open(f'coordination_test_report_{int(time.time())}.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"📁 Detailed report saved to coordination_test_report_{int(time.time())}.json")

async def main():
    """Main test function"""
    tester = CoordinationSystemTester()
    
    try:
        await tester.run_comprehensive_tests()
        tester.print_test_report()
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Error running tests: {e}")

if __name__ == "__main__":
    print("🧪 Docker Coordination System Test Suite")
    print("=========================================")
    print("Testing coordination between MCP servers, AI agents, LangChain, and AutoGen...")
    print()
    
    asyncio.run(main())
