#!/usr/bin/env python3
"""
Demo script showing GitHub Copilot tokens integration with LangChain multi-agent system
This demonstrates the enhanced multi-agent coordination you had working yesterday
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from enhanced_langchain_coordinator import EnhancedLangChainCoordinator, AgentRole

async def test_github_copilot_agents():
    """Test the GitHub Copilot multi-agent system"""
    print("🚀 Testing GitHub Copilot Multi-Agent System")
    print("=" * 50)
    
    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        print("💡 Please set your GitHub token in the environment:")
        print("   export GITHUB_TOKEN=your_github_token_here")
        print("   Or add it to your .env file")
        return False
    
    print(f"✅ GitHub Token found: {github_token[:12]}...")
    
    try:
        # Initialize the coordinator
        coordinator = EnhancedLangChainCoordinator()
        
        # Initialize the system (this will initialize the multi-agent system)
        print("\n🔧 Initializing Enhanced LangChain Coordinator...")
        if not await coordinator.initialize():
            print("❌ Coordinator initialization failed")
            return False
        
        print("✅ Coordinator initialized successfully!")
        
        # Test multi-agent coordination
        if coordinator.multi_agent_llm:
            print("\n🤖 Testing Multi-Agent Coordination...")
            
            # Test a flash loan analysis task
            task = """
            Analyze a flash loan arbitrage opportunity:
            - ETH price on Uniswap: $1800
            - ETH price on SushiSwap: $1820
            - Gas price: 25 gwei
            - Available liquidity: $10M
            
            Determine if this is a profitable arbitrage opportunity and provide:
            1. Code analysis of the arbitrage logic
            2. Generated smart contract code
            3. Architecture recommendations
            4. Security audit findings
            """
            
            result: str = await coordinator.multi_agent_llm.coordinate_agents(
                task=task,
                required_roles=[
                    AgentRole.CODE_ANALYST,
                    AgentRole.CODE_GENERATOR,
                    AgentRole.ARCHITECTURE_DESIGNER,
                    AgentRole.SECURITY_AUDITOR,
                    AgentRole.COORDINATOR
                ]
            )
            
            print("🎯 Multi-Agent Coordination Results:")
            print(f"   Task: {result['task']}")
            print(f"   Agents Involved: {len(result['agents_involved'])}")
            print(f"   Execution Time: {result['execution_time']}")
            print(f"   Phases Completed: {len(result['phases'])}")
            
            for i, phase in enumerate(result['phases']):
                print(f"\n📋 Phase {i+1}: {phase['phase']}")
                print(f"   Agent: {phase['agent']}")
                print(f"   Result: {phase['result'][:200]}...")
            
            if result['final_result']:
                print(f"\n🏆 Final Result: {result['final_result'][:300]}...")
            
            # Test agent status
            status = coordinator.multi_agent_llm.get_agent_status()
            print(f"\n📊 Agent Status:")
            print(f"   Total Agents: {status['total_agents']}")
            for agent_id, agent_info in status['agents'].items():
                print(f"   {agent_id}: {agent_info['role']} - {agent_info['conversation_count']} conversations")
        
        await coordinator.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def demonstrate_github_models_integration():
    """Demonstrate direct GitHub Models API integration"""
    print("\n🔗 Testing Direct GitHub Models Integration")
    print("-" * 40)
    
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
                    "content": "Analyze this DeFi flash loan scenario: ETH at $1800 on Uniswap, $1820 on SushiSwap. Gas: 25 gwei. Is this profitable?"
                }
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result: str = response.json()
            content = result["choices"][0]["message"]["content"]
            print("✅ GitHub Models API Response:")
            print(f"   {content}")
            return True
        else:
            print(f"❌ GitHub Models API Error: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct API test failed: {str(e)}")
        return False

def show_configuration_guide():
    """Show configuration guide for GitHub Copilot integration"""
    print("\n📚 GitHub Copilot Integration Configuration Guide")
    print("=" * 55)
    
    print("""
🔧 Step 1: GitHub Token Setup
   1. Go to: https://github.com/settings/tokens
   2. Generate a new token with 'models' permission
   3. Add to your environment:
      export GITHUB_TOKEN=your_token_here
   
🤖 Step 2: Available Models
   - gpt-4o (Latest GPT-4 Omni)
   - gpt-4o-mini (Faster version)
   - claude-3-5-sonnet (Anthropic's Claude)
   - llama-3.1-405b (Meta's Llama)
   
⚡ Step 3: Multi-Agent Roles
   - CODE_ANALYST: Analyzes code for bugs and improvements
   - CODE_GENERATOR: Creates clean, efficient code
   - ARCHITECTURE_DESIGNER: Designs system architecture
   - SECURITY_AUDITOR: Performs security analysis
   - PERFORMANCE_OPTIMIZER: Optimizes for performance
   - COORDINATOR: Manages multi-agent collaboration
   
🎯 Step 4: Usage
   - The system uses your GitHub Copilot subscription
   - No additional API costs
   - High rate limits
   - Multiple specialized agents working together
   
💰 Benefits:
   ✅ FREE with GitHub Copilot subscription
   ✅ Multiple AI models available
   ✅ Specialized agents for different tasks
   ✅ Coordinated multi-agent problem solving
    """)

async def main():
    """Main demo function"""
    print("🏦 GitHub Copilot Multi-Agent Flash Loan System")
    print("=" * 50)
    
    # Show configuration guide
    show_configuration_guide()
    
    # Test direct GitHub Models integration
    github_success = await demonstrate_github_models_integration()
    
    if github_success:
        print("\n🎉 GitHub Models integration is working!")
        
        # Test multi-agent coordination
        agent_success = await test_github_copilot_agents()
        
        if agent_success:
            print("\n🚀 SUCCESS! Your GitHub Copilot multi-agent system is fully operational!")
            print("\n🎯 Next Steps:")
            print("   1. Integrate with your flash loan contracts")
            print("   2. Set up continuous monitoring")
            print("   3. Configure agent coordination for your specific needs")
            print("   4. Customize agent roles and capabilities")
        else:
            print("\n⚠️  Multi-agent coordination needs attention")
    else:
        print("\n❌ GitHub Models integration needs to be configured")
        print("Please check your GITHUB_TOKEN and try again")

if __name__ == "__main__":
    asyncio.run(main())
