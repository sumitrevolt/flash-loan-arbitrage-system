#!/usr/bin/env python3
"""
Test script to demonstrate GitHub integration across all 5 agents
================================================================

This script validates that all agents are actively using the GitHub token
for their specialized operations and demonstrates their capabilities.
"""

import asyncio
import json
import os
from datetime import datetime
from advanced_agentic_coordination import AdvancedCoordinationSystem, CoordinationTask

class GitHubIntegrationTester:
    """Test GitHub integration for all agents"""
    
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.coordination_system = None
        self.test_results = {}
    
    async def run_comprehensive_test(self):
        """Run comprehensive GitHub integration tests"""
        print("🧪 GITHUB INTEGRATION TESTING SUITE")
        print("="*80)
        
        try:
            # Initialize coordination system
            self.coordination_system = AdvancedCoordinationSystem(self.github_token)
            
            # Test each agent's GitHub capabilities
            await self._test_coordinator_github_integration()
            await self._test_indexer_github_integration()
            await self._test_analyzer_github_integration()
            await self._test_executor_github_integration()
            await self._test_guardian_github_integration()
            
            # Generate test report
            self._generate_test_report()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
    
    async def _test_coordinator_github_integration(self):
        """Test CoordinatorAgent GitHub integration"""
        print("\n🎯 TESTING COORDINATOR AGENT GITHUB INTEGRATION")
        print("-" * 60)
        
        if "CoordinatorAgent" not in self.coordination_system.agents:
            print("❌ CoordinatorAgent not found")
            return
        
        agent = self.coordination_system.agents["CoordinatorAgent"]
        
        # Test GitHub project analysis
        test_task = CoordinationTask(
            task_id="test_coord_github",
            task_type="github_project_analysis",
            priority=1,
            assigned_agent="CoordinatorAgent",
            mcp_servers=["coordinator"],
            parameters={"query": "uniswap arbitrage coordination"},
            status="testing",
            created_at=datetime.now()
        )
        
        print("🔍 Testing GitHub project analysis...")
        result = await agent.execute_task(test_task)
        
        if result.get("success"):
            print("✅ CoordinatorAgent successfully used GitHub token")
            print(f"   Result: {result.get('result', 'N/A')[:100]}...")
        else:
            print("❌ CoordinatorAgent GitHub integration failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        self.test_results["CoordinatorAgent"] = result
    
    async def _test_indexer_github_integration(self):
        """Test IndexerAgent GitHub integration"""
        print("\n📚 TESTING INDEXER AGENT GITHUB INTEGRATION")
        print("-" * 60)
        
        if "IndexerAgent" not in self.coordination_system.agents:
            print("❌ IndexerAgent not found")
            return
        
        agent = self.coordination_system.agents["IndexerAgent"]
        
        # Test GitHub protocol indexing
        test_task = CoordinationTask(
            task_id="test_indexer_github",
            task_type="github_protocol_indexing",
            priority=1,
            assigned_agent="IndexerAgent",
            mcp_servers=["blockchain", "data-analyzer"],
            parameters={"protocol": "aave"},
            status="testing",
            created_at=datetime.now()
        )
        
        print("🔍 Testing GitHub protocol indexing...")
        result = await agent.execute_task(test_task)
        
        if result.get("success"):
            print("✅ IndexerAgent successfully used GitHub token")
            print(f"   Result: {result.get('result', 'N/A')[:100]}...")
        else:
            print("❌ IndexerAgent GitHub integration failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        self.test_results["IndexerAgent"] = result
    
    async def _test_analyzer_github_integration(self):
        """Test AnalyzerAgent GitHub integration"""
        print("\n📊 TESTING ANALYZER AGENT GITHUB INTEGRATION")
        print("-" * 60)
        
        if "AnalyzerAgent" not in self.coordination_system.agents:
            print("❌ AnalyzerAgent not found")
            return
        
        agent = self.coordination_system.agents["AnalyzerAgent"]
        
        # Test GitHub code analysis
        test_task = CoordinationTask(
            task_id="test_analyzer_github",
            task_type="github_code_analysis",
            priority=1,
            assigned_agent="AnalyzerAgent",
            mcp_servers=["arbitrage", "defi-analyzer"],
            parameters={"query": "flashloan arbitrage solidity"},
            status="testing",
            created_at=datetime.now()
        )
        
        print("🔍 Testing GitHub code analysis...")
        result = await agent.execute_task(test_task)
        
        if result.get("success"):
            print("✅ AnalyzerAgent successfully used GitHub token")
            print(f"   Result: {result.get('result', 'N/A')[:100]}...")
        else:
            print("❌ AnalyzerAgent GitHub integration failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        self.test_results["AnalyzerAgent"] = result
    
    async def _test_executor_github_integration(self):
        """Test ExecutorAgent GitHub integration"""
        print("\n⚡ TESTING EXECUTOR AGENT GITHUB INTEGRATION")
        print("-" * 60)
        
        if "ExecutorAgent" not in self.coordination_system.agents:
            print("❌ ExecutorAgent not found")
            return
        
        agent = self.coordination_system.agents["ExecutorAgent"]
        
        # Test GitHub contract verification
        test_task = CoordinationTask(
            task_id="test_executor_github",
            task_type="github_contract_verification",
            priority=1,
            assigned_agent="ExecutorAgent",
            mcp_servers=["flash-loan", "portfolio"],
            parameters={"contract": "uniswap v3 router"},
            status="testing",
            created_at=datetime.now()
        )
        
        print("🔍 Testing GitHub contract verification...")
        result = await agent.execute_task(test_task)
        
        if result.get("success"):
            print("✅ ExecutorAgent successfully used GitHub token")
            print(f"   Result: {result.get('result', 'N/A')[:100]}...")
        else:
            print("❌ ExecutorAgent GitHub integration failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        self.test_results["ExecutorAgent"] = result
    
    async def _test_guardian_github_integration(self):
        """Test GuardianAgent GitHub integration"""
        print("\n🛡️  TESTING GUARDIAN AGENT GITHUB INTEGRATION")
        print("-" * 60)
        
        if "GuardianAgent" not in self.coordination_system.agents:
            print("❌ GuardianAgent not found")
            return
        
        agent = self.coordination_system.agents["GuardianAgent"]
        
        # Test GitHub security scan
        test_task = CoordinationTask(
            task_id="test_guardian_github",
            task_type="github_security_scan",
            priority=1,
            assigned_agent="GuardianAgent",
            mcp_servers=["security", "risk-manager"],
            parameters={"query": "defi smart contract vulnerability"},
            status="testing",
            created_at=datetime.now()
        )
        
        print("🔍 Testing GitHub security scan...")
        result = await agent.execute_task(test_task)
        
        if result.get("success"):
            print("✅ GuardianAgent successfully used GitHub token")
            print(f"   Result: {result.get('result', 'N/A')[:100]}...")
        else:
            print("❌ GuardianAgent GitHub integration failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        self.test_results["GuardianAgent"] = result
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📊 GITHUB INTEGRATION TEST REPORT")
        print("="*80)
        
        total_agents = len(self.test_results)
        successful_agents = sum(1 for result in self.test_results.values() if result.get("success"))
        
        print(f"Total Agents Tested: {total_agents}")
        print(f"Successful GitHub Integrations: {successful_agents}")
        print(f"Success Rate: {(successful_agents/total_agents*100):.1f}%")
        
        print("\n🤖 AGENT-BY-AGENT RESULTS:")
        for agent_name, result in self.test_results.items():
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            print(f"   {agent_name}: {status}")
            if result.get("success"):
                print(f"      Execution Time: {result.get('execution_time', 0):.2f}s")
            else:
                print(f"      Error: {result.get('error', 'Unknown')}")
        
        print("\n💡 GITHUB TOKEN USAGE SUMMARY:")
        print("   • CoordinatorAgent: Project analysis and coordination")
        print("   • IndexerAgent: Protocol indexing from repositories")
        print("   • AnalyzerAgent: Smart contract code analysis")
        print("   • ExecutorAgent: Contract verification before execution")
        print("   • GuardianAgent: Security vulnerability scanning")
        
        # Save test results
        test_report = {
            "test_timestamp": datetime.now().isoformat(),
            "total_agents": total_agents,
            "successful_agents": successful_agents,
            "success_rate": successful_agents/total_agents*100,
            "detailed_results": self.test_results
        }
        
        with open("github_integration_test_report.json", "w") as f:
            json.dump(test_report, f, indent=2)
        
        print("\n✅ Test report saved to 'github_integration_test_report.json'")

async def main():
    """Main test execution"""
    print("🚀 GITHUB INTEGRATION TESTING SUITE")
    print("="*80)
    
    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        github_token = input("Enter your GitHub token for testing: ").strip()
        if not github_token:
            print("❌ GitHub token required for testing")
            return
    
    try:
        # Initialize and run tests
        tester = GitHubIntegrationTester(github_token)
        await tester.run_comprehensive_test()
        
        print("\n🎉 TESTING COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
