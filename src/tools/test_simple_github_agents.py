#!/usr/bin/env python3
"""
Test GitHub Copilot Multi-Agent System (Simple Version)
Lightweight test without database dependency
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from simple_github_coordinator import SimpleCoordinator, AgentRole

async def test_github_copilot_simple():
    """Test the simple GitHub Copilot multi-agent system"""
    print("🚀 Testing Simple GitHub Copilot Multi-Agent System")
    print("=" * 55)
    
    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        print("💡 Please set your GitHub token in the environment:")
        print("   $env:GITHUB_TOKEN='your_github_token_here'")
        return False
    
    print(f"✅ GitHub Token found: {github_token[:12]}...")
    
    try:
        # Initialize the simple coordinator
        coordinator = SimpleCoordinator()
        
        # Initialize the system
        print("\n🔧 Initializing Simple GitHub Copilot Coordinator...")
        if not await coordinator.initialize():
            print("❌ Coordinator initialization failed")
            return False
        
        print("✅ Coordinator initialized successfully!")
        
        # Test multi-agent coordination
        if coordinator.multi_agent_llm:
            print("\n🤖 Testing Multi-Agent Flash Loan Analysis...")
            
            # Test a flash loan analysis task
            task = """
            Analyze this flash loan arbitrage opportunity for profitability and implementation:
            
            Scenario:
            - ETH price on Uniswap: $1800
            - ETH price on SushiSwap: $1820  
            - Gas price: 25 gwei
            - Available liquidity: $10M ETH on both exchanges
            - Flash loan fee: 0.09% (Aave)
            
            Requirements:
            1. Calculate exact profitability including all costs
            2. Generate Solidity smart contract code for the arbitrage
            3. Design the system architecture 
            4. Perform security audit of the approach
            5. Optimize for gas efficiency
            6. Provide implementation recommendations
            """
            
            print("   📋 Coordinating specialist agents...")
            
            result: str = await coordinator.multi_agent_llm.coordinate_agents(
                task=task,
                required_roles=[
                    AgentRole.CODE_ANALYST,
                    AgentRole.CODE_GENERATOR, 
                    AgentRole.ARCHITECTURE_DESIGNER,
                    AgentRole.SECURITY_AUDITOR,
                    AgentRole.PERFORMANCE_OPTIMIZER,
                    AgentRole.COORDINATOR
                ]
            )
            
            print("\n🎯 Multi-Agent Coordination Results:")
            print("=" * 40)
            print(f"📝 Task: {result['task'][:100]}...")
            print(f"🤖 Agents Involved: {', '.join(result['agents_involved'])}")
            print(f"⏱️  Execution Time: {result['execution_time']}")
            print(f"📊 Phases Completed: {len(result['phases'])}")
            
            # Show each phase result
            for i, phase in enumerate(result['phases']):
                print(f"\n📋 Phase {i+1}: {phase['phase']}")
                print(f"   🤖 Agent: {phase['agent']}")
                print(f"   📄 Result Preview: {phase['result'][:200]}...")
                print("   " + "─" * 50)
            
            # Show final coordinated result
            if result['final_result']:
                print(f"\n🏆 FINAL COORDINATED RECOMMENDATION:")
                print("=" * 50)
                print(result['final_result'])
                print("=" * 50)
            
            # Show agent status
            status = coordinator.multi_agent_llm.get_agent_status()
            print(f"\n📊 Multi-Agent System Status:")
            print(f"   Total Specialist Agents: {status['total_agents']}")
            for agent_id, agent_info in status['agents'].items():
                expertise_preview = ', '.join(agent_info['expertise'][:3])
                print(f"   🤖 {agent_info['role']}: {expertise_preview}...")
        
        await coordinator.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_github_models():
    """Test direct GitHub Models API"""
    print("\n🔗 Testing Direct GitHub Models Integration")
    print("-" * 45)
    
    import requests
    
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN not found")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": "Briefly explain what makes a flash loan arbitrage profitable in DeFi. Keep it under 100 words."
                }
            ],
            "max_tokens": 150,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            json=data,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            result: str = response.json()
            content = result["choices"][0]["message"]["content"]
            print("✅ GitHub Models API Response:")
            print(f"   💡 {content}")
            return True
        else:
            print(f"❌ GitHub Models API Error: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct API test failed: {str(e)}")
        return False

def show_system_info():
    """Show system information and capabilities"""
    print("\n📊 GitHub Copilot Multi-Agent Flash Loan System")
    print("=" * 50)
    print("""
🎯 System Capabilities:
   ✅ GitHub Models API Integration (GPT-4, Claude, Llama)
   ✅ Multi-Agent Coordination (6 specialist agents)
   ✅ Flash Loan Analysis & Code Generation
   ✅ Security Auditing & Performance Optimization
   ✅ Real-time Arbitrage Opportunity Assessment

🤖 Specialist Agents:
   📊 Code Analyst: Reviews code for bugs and improvements
   💻 Code Generator: Creates Solidity smart contracts
   🏗️  Architecture Designer: Designs scalable DeFi systems  
   🔒 Security Auditor: Identifies vulnerabilities
   ⚡ Performance Optimizer: Optimizes gas costs
   🎯 Coordinator: Synthesizes all expert input

💰 Benefits:
   ✅ FREE with GitHub Copilot subscription
   ✅ No additional API costs
   ✅ Advanced multi-model AI capabilities
   ✅ Specialized domain expertise
   ✅ Coordinated problem-solving approach
    """)

async def main():
    """Main test function"""
    print("🏦 GitHub Copilot Multi-Agent Flash Loan System Test")
    print("=" * 60)
    
    # Show system capabilities
    show_system_info()
    
    # Test direct GitHub Models integration first
    github_success = await test_direct_github_models()
    
    if github_success:
        print("\n🎉 GitHub Models integration confirmed!")
        
        # Test multi-agent coordination
        agent_success = await test_github_copilot_simple()
        
        if agent_success:
            print("\n🚀 SUCCESS! GitHub Copilot Multi-Agent System is fully operational!")
            print("\n🎯 System is ready for:")
            print("   💰 Flash loan arbitrage analysis")
            print("   🔍 Smart contract code generation") 
            print("   🔒 Security auditing")
            print("   ⚡ Gas optimization")
            print("   🏗️  Architecture design")
            print("   📊 Multi-agent coordination")
            
            print("\n💡 Next Steps:")
            print("   1. Integrate with your existing flash loan contracts")
            print("   2. Set up continuous arbitrage monitoring")
            print("   3. Configure custom agent specializations")
            print("   4. Deploy automated trading strategies")
        else:
            print("\n⚠️  Multi-agent coordination needs attention")
    else:
        print("\n❌ GitHub Models integration failed")
        print("Please check your GITHUB_TOKEN and try again")

if __name__ == "__main__":
    asyncio.run(main())
