7#!/usr/bin/env python3
"""
ENHANCED MULTI-CHAIN AGENTIC COORDINATION SYSTEM
===============================================
COMPLETE USAGE GUIDE

This guide shows you exactly how to use the system step-by-step.
"""

import os
import asyncio

def show_system_overview():
    """Show system overview and capabilities"""
    print("🚀 ENHANCED MULTI-CHAIN AGENTIC COORDINATION SYSTEM")
    print("="*80)
    print("This system provides 5 specialized AI agents that work together to:")
    print("• 🎯 Coordinate complex multi-chain arbitrage operations")
    print("• 📚 Index and analyze DeFi protocols from GitHub")
    print("• 📊 Detect and analyze arbitrage opportunities")
    print("• ⚡ Execute trades with GitHub-verified smart contracts")
    print("• 🛡️ Monitor security and manage risks")
    print()
    print("💡 KEY FEATURES:")
    print("• True agentic coordination between AI agents")
    print("• GitHub integration for enhanced protocol analysis")
    print("• Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism, BSC)")
    print("• Advanced chat interface for direct command management")
    print("• Real-time monitoring and optimization")

def show_quick_start():
    """Show quick start instructions"""
    print("\n⚡ QUICK START GUIDE")
    print("="*60)
    print("1️⃣ SET UP GITHUB TOKEN (Required for enhanced features)")
    print("   Option A: Set environment variable")
    print("   • Windows: set GITHUB_TOKEN=your_token_here")
    print("   • Linux/Mac: export GITHUB_TOKEN=your_token_here")
    print()
    print("   Option B: The system will prompt you for the token")
    print()
    print("2️⃣ LAUNCH THE SYSTEM")
    print("   • Run: python advanced_agentic_coordination.py")
    print("   • Or: python enhanced_system_launcher.py")
    print()
    print("3️⃣ USE THE CHAT INTERFACE")
    print("   • The system will show available commands")
    print("   • Type commands to interact with agents")
    print("   • Use 'quit' or 'exit' to shutdown")

def show_command_examples():
    """Show detailed command examples"""
    print("\n💻 COMMAND EXAMPLES")
    print("="*60)
    
    commands = [
        {
            "category": "🎯 COORDINATION COMMANDS",
            "examples": [
                ("coordinate arbitrage", "Coordinate multi-agent arbitrage analysis"),
                ("agent status", "Show performance of all agents"),
                ("system metrics", "Display advanced system metrics"),
                ("workflow start", "Start a new coordination workflow")
            ]
        },
        {
            "category": "📊 ANALYSIS COMMANDS", 
            "examples": [
                ("analyze ethereum uniswap", "Analyze Uniswap on Ethereum"),
                ("analyze polygon sushiswap", "Analyze SushiSwap on Polygon"),
                ("analyze arbitrum curve", "Analyze Curve on Arbitrum"),
                ("analyze all chains", "Comprehensive multi-chain analysis")
            ]
        },
        {
            "category": "📚 INDEXING COMMANDS",
            "examples": [
                ("index uniswap", "Index Uniswap protocol from GitHub"),
                ("index aave", "Index Aave protocol repositories"),
                ("index comprehensive", "Full multi-protocol indexing"),
                ("index defi protocols", "Index all major DeFi protocols")
            ]
        },
        {
            "category": "⚡ EXECUTION COMMANDS",
            "examples": [
                ("execute flashloan arbitrage", "Execute flashloan arbitrage strategy"),
                ("execute cross-chain swap", "Execute cross-chain arbitrage"),
                ("execute optimal strategy", "Execute AI-optimized strategy"),
                ("execute with verification", "Execute with GitHub contract verification")
            ]
        },
        {
            "category": "🛡️ SECURITY COMMANDS",
            "examples": [
                ("secure scan protocols", "Scan DeFi protocols for vulnerabilities"),
                ("secure verify contracts", "Verify smart contract security"),
                ("secure risk assessment", "Perform comprehensive risk assessment"),
                ("secure monitor threats", "Monitor for security threats")
            ]
        },
        {
            "category": "🌐 MULTI-CHAIN COMMANDS",
            "examples": [
                ("multichain opportunities", "Find cross-chain arbitrage opportunities"),
                ("multichain analysis", "Comprehensive multi-chain analysis"),
                ("multichain coordination", "Coordinate cross-chain operations"),
                ("multichain optimization", "Optimize multi-chain strategies")
            ]
        }
    ]
    
    for category_info in commands:
        print(f"\n{category_info['category']}")
        print("-" * 50)
        for command, description in category_info['examples']:
            print(f"   💡 Command: '{command}'")
            print(f"      Description: {description}")
            print()

def show_agent_details():
    """Show detailed agent information"""
    print("\n🤖 AGENT DETAILS")
    print("="*60)
    
    agents = {
        "🎯 CoordinatorAgent": {
            "purpose": "Orchestrates all other agents and manages workflows",
            "github_features": [
                "Analyzes GitHub projects for coordination opportunities",
                "Searches for multi-agent coordination patterns",
                "Manages workflow automation using GitHub data"
            ],
            "commands": ["coordinate", "workflow", "orchestrate"],
            "example": "coordinate arbitrage detection"
        },
        "📚 IndexerAgent": {
            "purpose": "Indexes blockchain data and builds knowledge graphs",
            "github_features": [
                "Indexes DeFi protocols from GitHub repositories",
                "Builds knowledge graphs from smart contracts",
                "Organizes protocol documentation"
            ],
            "commands": ["index", "build", "organize"],
            "example": "index uniswap protocol"
        },
        "📊 AnalyzerAgent": {
            "purpose": "Analyzes markets and detects arbitrage opportunities",
            "github_features": [
                "Analyzes smart contract code from GitHub",
                "Searches for arbitrage patterns in codebases",
                "Evaluates protocol implementations"
            ],
            "commands": ["analyze", "detect", "evaluate"],
            "example": "analyze ethereum arbitrage"
        },
        "⚡ ExecutorAgent": {
            "purpose": "Executes trades and manages positions",
            "github_features": [
                "Verifies smart contracts through GitHub",
                "Validates protocol implementations",
                "Ensures security before execution"
            ],
            "commands": ["execute", "trade", "manage"],
            "example": "execute flashloan strategy"
        },
        "🛡️ GuardianAgent": {
            "purpose": "Monitors security and manages risks",
            "github_features": [
                "Scans GitHub for security vulnerabilities",
                "Monitors protocol security updates",
                "Analyzes security audit reports"
            ],
            "commands": ["secure", "monitor", "protect"],
            "example": "secure scan vulnerabilities"
        }
    }
    
    for agent_name, details in agents.items():
        print(f"\n{agent_name}")
        print("-" * 40)
        print(f"Purpose: {details['purpose']}")
        print("GitHub Features:")
        for feature in details['github_features']:
            print(f"  • {feature}")
        print(f"Commands: {', '.join(details['commands'])}")
        print(f"Example: '{details['example']}'")

def show_advanced_features():
    """Show advanced features and workflows"""
    print("\n🚀 ADVANCED FEATURES")
    print("="*60)
    
    print("🔥 MULTI-AGENT WORKFLOWS")
    print("The system can run complex workflows that involve multiple agents:")
    print("1. IndexerAgent indexes protocols from GitHub")
    print("2. AnalyzerAgent analyzes the indexed data for opportunities")
    print("3. ExecutorAgent verifies contracts and prepares execution")
    print("4. GuardianAgent performs security checks")
    print("5. CoordinatorAgent orchestrates the final execution")
    print()
    
    print("🔗 GITHUB INTEGRATION")
    print("Every agent uses GitHub for enhanced capabilities:")
    print("• Real-time repository analysis")
    print("• Smart contract code verification")
    print("• Security vulnerability scanning")
    print("• Protocol documentation indexing")
    print("• Community project discovery")
    print()
    
    print("🌐 MULTI-CHAIN SUPPORT")
    print("Supported blockchains:")
    print("• Ethereum (ETH)")
    print("• Polygon (MATIC)")
    print("• Arbitrum (ARB)")
    print("• Optimism (OP)")
    print("• Binance Smart Chain (BSC)")
    print()
    
    print("💬 INTELLIGENT CHAT INTERFACE")
    print("The chat interface understands natural language:")
    print("• 'Find arbitrage opportunities on Ethereum'")
    print("• 'What's the security status of Aave protocol?'")
    print("• 'Execute the most profitable strategy'")
    print("• 'Show me the performance of all agents'")

def show_troubleshooting():
    """Show troubleshooting guide"""
    print("\n🔧 TROUBLESHOOTING")
    print("="*60)
    
    issues = [
        {
            "problem": "GitHub token not working",
            "solutions": [
                "Check if token has correct permissions (repo access)",
                "Verify token is not expired",
                "Ensure no extra spaces in token string",
                "Try setting token as environment variable"
            ]
        },
        {
            "problem": "Agents not responding",
            "solutions": [
                "Check if all dependencies are installed",
                "Verify MCP servers are running",
                "Restart the system",
                "Check system logs for errors"
            ]
        },
        {
            "problem": "No arbitrage opportunities found",
            "solutions": [
                "Market conditions may not be favorable",
                "Try different chains or protocols",
                "Check if indexing is complete",
                "Verify network connectivity"
            ]
        },
        {
            "problem": "Slow performance",
            "solutions": [
                "Check GitHub API rate limits",
                "Reduce scope of analysis",
                "Restart agents to clear cache",
                "Check system resources"
            ]
        }
    ]
    
    for issue in issues:
        print(f"\n❌ Problem: {issue['problem']}")
        print("   Solutions:")
        for solution in issue['solutions']:
            print(f"   • {solution}")

def show_safety_tips():
    """Show safety and best practices"""
    print("\n🛡️ SAFETY & BEST PRACTICES")
    print("="*60)
    
    print("🔒 SECURITY BEST PRACTICES")
    print("• Always verify contracts before execution")
    print("• Start with small amounts for testing")
    print("• Monitor gas fees and slippage")
    print("• Use the GuardianAgent security scans")
    print("• Keep your GitHub token secure")
    print()
    
    print("💰 FINANCIAL SAFETY")
    print("• Never invest more than you can afford to lose")
    print("• Understand the risks of arbitrage trading")
    print("• Monitor market conditions continuously")
    print("• Set appropriate stop-loss limits")
    print("• Test strategies on testnets first")
    print()
    
    print("🎯 OPERATIONAL TIPS")
    print("• Keep the system updated")
    print("• Monitor agent performance regularly")
    print("• Use workflow automation for efficiency")
    print("• Review system metrics periodically")
    print("• Backup important configurations")

async def interactive_tutorial():
    """Interactive tutorial mode"""
    print("\n🎓 INTERACTIVE TUTORIAL")
    print("="*60)
    print("Let's walk through using the system step by step!")
    print()
    
    steps = [
        {
            "title": "Step 1: System Overview",
            "action": lambda: show_system_overview()
        },
        {
            "title": "Step 2: Quick Start",
            "action": lambda: show_quick_start()
        },
        {
            "title": "Step 3: Command Examples", 
            "action": lambda: show_command_examples()
        },
        {
            "title": "Step 4: Agent Details",
            "action": lambda: show_agent_details()
        },
        {
            "title": "Step 5: Advanced Features",
            "action": lambda: show_advanced_features()
        },
        {
            "title": "Step 6: Safety Tips",
            "action": lambda: show_safety_tips()
        },
        {
            "title": "Step 7: Troubleshooting",
            "action": lambda: show_troubleshooting()
        }
    ]
    
    for i, step in enumerate(steps):
        print(f"\n{'='*60}")
        print(f"📚 {step['title']}")
        print('='*60)
        
        choice = input(f"\nShow {step['title']}? (y/n/skip): ").strip().lower()
        
        if choice in ['y', 'yes', '']:
            step['action']()
            input("\nPress Enter to continue...")
        elif choice == 'skip':
            break
        elif choice in ['n', 'no']:
            continue

def main():
    """Main usage guide"""
    print("🎯 HOW TO USE THE ENHANCED MULTI-CHAIN AGENTIC COORDINATION SYSTEM")
    print("="*80)
    
    while True:
        print("\n📋 USAGE GUIDE OPTIONS")
        print("-" * 40)
        print("1. 📖 Quick Start Guide")
        print("2. 💻 Command Examples")
        print("3. 🤖 Agent Details")
        print("4. 🚀 Advanced Features")
        print("5. 🔧 Troubleshooting")
        print("6. 🛡️ Safety & Best Practices")
        print("7. 🎓 Interactive Tutorial")
        print("8. 🚀 Launch System Now")
        print("9. ❌ Exit")
        
        choice = input("\nSelect option (1-9): ").strip()
        
        try:
            if choice == "1":
                show_quick_start()
            elif choice == "2":
                show_command_examples()
            elif choice == "3":
                show_agent_details()
            elif choice == "4":
                show_advanced_features()
            elif choice == "5":
                show_troubleshooting()
            elif choice == "6":
                show_safety_tips()
            elif choice == "7":
                asyncio.run(interactive_tutorial())
            elif choice == "8":
                print("\n🚀 LAUNCHING SYSTEM...")
                print("Run: python advanced_agentic_coordination.py")
                break
            elif choice == "9":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-9.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        if choice in ['1', '2', '3', '4', '5', '6']:
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
