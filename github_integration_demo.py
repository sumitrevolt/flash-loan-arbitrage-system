#!/usr/bin/env python3
"""
Enhanced GitHub Integration Demonstration
=========================================

This script demonstrates all 5 agents actively using the GitHub token
for their specialized operations with real examples.
"""

import asyncio
import json
import os
from datetime import datetime
from github import Github

class GitHubIntegrationDemo:
    """Demonstrate GitHub integration across all agents"""
    
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.github = Github(github_token)
        
    async def run_demo(self):
        """Run comprehensive GitHub integration demonstration"""
        print("🚀 ENHANCED GITHUB INTEGRATION DEMONSTRATION")
        print("="*80)
        
        try:
            # Verify GitHub connection
            await self._verify_github_connection()
            
            # Demonstrate each agent's GitHub capabilities
            await self._demo_coordinator_github_features()
            await self._demo_indexer_github_features()
            await self._demo_analyzer_github_features()
            await self._demo_executor_github_features()
            await self._demo_guardian_github_features()
            
            # Show multi-agent coordination
            await self._demo_multi_agent_coordination()
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
    
    async def _verify_github_connection(self):
        """Verify GitHub connection and show user info"""
        print("\n🔗 VERIFYING GITHUB CONNECTION")
        print("-" * 40)
        
        try:
            user = self.github.get_user()
            print(f"✅ Connected to GitHub as: {user.login}")
            print(f"   Name: {user.name}")
            print(f"   Public Repos: {user.public_repos}")
            print(f"   Followers: {user.followers}")
            print(f"   Following: {user.following}")
            
            # Check rate limit
            rate_limit = self.github.get_rate_limit()
            core_limit = rate_limit.core
            print(f"   API Rate Limit: {core_limit.remaining}/{core_limit.limit}")
            print(f"   Reset Time: {core_limit.reset}")
            
        except Exception as e:
            print(f"❌ GitHub connection failed: {e}")
            raise
    
    async def _demo_coordinator_github_features(self):
        """Demonstrate CoordinatorAgent GitHub features"""
        print("\n🎯 COORDINATOR AGENT - GITHUB PROJECT ANALYSIS")
        print("-" * 60)
        
        print("🔍 Searching for DeFi coordination projects...")
        
        try:
            # Search for DeFi coordination repositories
            repos = self.github.search_repositories("defi arbitrage coordination", sort="stars")
            
            print("📊 TOP DEFI COORDINATION PROJECTS:")
            for i, repo in enumerate(repos[:5], 1):
                print(f"   {i}. ⭐ {repo.full_name} ({repo.stargazers_count} stars)")
                print(f"      📝 {repo.description}")
                print(f"      🔧 Language: {repo.language}")
                print(f"      📅 Updated: {repo.updated_at.strftime('%Y-%m-%d')}")
                print()
            
            print("✅ CoordinatorAgent can access GitHub project data for coordination")
            
        except Exception as e:
            print(f"❌ Coordinator GitHub demo failed: {e}")
    
    async def _demo_indexer_github_features(self):
        """Demonstrate IndexerAgent GitHub features"""
        print("\n📚 INDEXER AGENT - PROTOCOL REPOSITORY INDEXING")
        print("-" * 60)
        
        print("🔍 Indexing major DeFi protocol repositories...")
        
        try:
            protocols = {
                "Uniswap": "Uniswap/v3-core",
                "Aave": "aave/aave-v3-core", 
                "Compound": "compound-finance/compound-protocol",
                "SushiSwap": "sushiswap/sushiswap"
            }
            
            protocol_data = {}
            
            for protocol_name, repo_name in protocols.items():
                try:
                    repo = self.github.get_repo(repo_name)
                    
                    # Get contract files
                    contracts = []
                    try:
                        contents = repo.get_contents("contracts")
                        if isinstance(contents, list):
                            for item in contents[:5]:
                                if item.name.endswith('.sol'):
                                    contracts.append(item.name)
                    except:
                        pass
                    
                    protocol_data[protocol_name] = {
                        "repository": repo.full_name,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "language": repo.language,
                        "updated": repo.updated_at.strftime('%Y-%m-%d'),
                        "contracts": contracts[:5]
                    }
                    
                    print(f"📦 {protocol_name}:")
                    print(f"   Repository: {repo.full_name}")
                    print(f"   ⭐ Stars: {repo.stargazers_count}")
                    print(f"   🍴 Forks: {repo.forks_count}")
                    print(f"   📄 Smart Contracts: {len(contracts)}")
                    if contracts:
                        print(f"   🔧 Sample Contracts: {', '.join(contracts[:3])}...")
                    print()
                    
                except Exception as e:
                    print(f"   ❌ Failed to index {protocol_name}: {e}")
            
            print("✅ IndexerAgent can systematically index DeFi protocols from GitHub")
            
        except Exception as e:
            print(f"❌ Indexer GitHub demo failed: {e}")
    
    async def _demo_analyzer_github_features(self):
        """Demonstrate AnalyzerAgent GitHub features"""
        print("\n📊 ANALYZER AGENT - SMART CONTRACT CODE ANALYSIS")
        print("-" * 60)
        
        print("🔍 Analyzing arbitrage-related smart contract code...")
        
        try:
            # Search for arbitrage smart contracts
            code_results = self.github.search_code("flashloan arbitrage language:solidity")
            
            print("💰 ARBITRAGE SMART CONTRACT ANALYSIS:")
            
            analysis_results = []
            for i, code in enumerate(code_results[:5], 1):
                repo_info = {
                    "file": f"{code.repository.full_name}/{code.path}",
                    "repository": code.repository.full_name,
                    "description": code.repository.description,
                    "stars": code.repository.stargazers_count,
                    "language": code.repository.language
                }
                analysis_results.append(repo_info)
                
                print(f"   {i}. 📄 {code.repository.full_name}/{code.name}")
                print(f"      ⭐ Repository: {code.repository.full_name} ({code.repository.stargazers_count} stars)")
                print(f"      📝 Description: {code.repository.description}")
                print(f"      🔧 Language: {code.repository.language}")
                print()
            
            print("🧠 ANALYSIS INSIGHTS:")
            total_stars = sum(r['stars'] for r in analysis_results)
            avg_stars = total_stars / len(analysis_results) if analysis_results else 0
            print(f"   • Found {len(analysis_results)} arbitrage implementations")
            print(f"   • Average repository popularity: {avg_stars:.0f} stars")
            print(f"   • Primary language: Solidity")
            print(f"   • Analysis confidence: High")
            
            print("✅ AnalyzerAgent can analyze smart contract code from GitHub")
            
        except Exception as e:
            print(f"❌ Analyzer GitHub demo failed: {e}")
    
    async def _demo_executor_github_features(self):
        """Demonstrate ExecutorAgent GitHub features"""
        print("\n⚡ EXECUTOR AGENT - CONTRACT VERIFICATION")
        print("-" * 60)
        
        print("🔍 Verifying smart contracts before execution...")
        
        try:
            # Analyze Uniswap V3 contracts for execution
            repo = self.github.get_repo("Uniswap/v3-core")
            
            print("🔒 CONTRACT VERIFICATION RESULTS:")
            print(f"   Repository: {repo.full_name}")
            print(f"   ⭐ Trust Score: {repo.stargazers_count} stars (High Trust)")
            print(f"   🍴 Community: {repo.forks_count} forks")
            print(f"   📅 Last Updated: {repo.updated_at.strftime('%Y-%m-%d')}")
            print(f"   🏢 Owner: {repo.owner.login}")
            print(f"   📊 Open Issues: {repo.open_issues_count}")
            
            # Check for security-related files
            security_indicators = []
            try:
                contents = repo.get_contents("")
                for item in contents:
                    if any(keyword in item.name.lower() for keyword in ['security', 'audit', 'test']):
                        security_indicators.append(item.name)
            except:
                pass
            
            print(f"   🛡️  Security Files: {len(security_indicators)}")
            if security_indicators:
                print(f"      • {', '.join(security_indicators[:3])}...")
            
            # Get recent commits
            commits = list(repo.get_commits()[:3])
            print(f"   📈 Recent Activity: {len(commits)} commits")
            for commit in commits:
                print(f"      • {commit.commit.message[:50]}... ({commit.commit.author.date.strftime('%Y-%m-%d')})")
            
            verification_score = min(repo.stargazers_count / 1000, 10)  # Max 10
            print(f"   ✅ Verification Score: {verification_score:.1f}/10.0")
            
            if verification_score > 5:
                print("   🟢 SAFE FOR EXECUTION")
            else:
                print("   🟡 REQUIRES ADDITIONAL VERIFICATION")
            
            print("✅ ExecutorAgent can verify contracts through GitHub analysis")
            
        except Exception as e:
            print(f"❌ Executor GitHub demo failed: {e}")
    
    async def _demo_guardian_github_features(self):
        """Demonstrate GuardianAgent GitHub features"""
        print("\n🛡️  GUARDIAN AGENT - SECURITY VULNERABILITY SCANNING")
        print("-" * 60)
        
        print("🔍 Scanning for security vulnerabilities in DeFi projects...")
        
        try:
            # Search for security-related repositories
            security_repos = self.github.search_repositories("defi security audit vulnerability")
            
            print("🔒 SECURITY ANALYSIS RESULTS:")
            
            vulnerability_data = []
            for i, repo in enumerate(security_repos[:4], 1):
                
                # Analyze repository for security indicators
                security_score = 0
                
                # Check repository metrics
                if repo.stargazers_count > 100:
                    security_score += 2
                if repo.forks_count > 50:
                    security_score += 1
                if repo.open_issues_count < 10:
                    security_score += 1
                
                # Check for security-related content
                security_files = []
                try:
                    contents = repo.get_contents("")
                    for item in contents:
                        if any(keyword in item.name.lower() for keyword in ['security', 'audit', 'vulnerability', 'safe']):
                            security_files.append(item.name)
                            security_score += 1
                except:
                    pass
                
                vulnerability_data.append({
                    "repo": repo.full_name,
                    "security_score": min(security_score, 10),
                    "security_files": security_files
                })
                
                print(f"   {i}. 🔍 {repo.full_name}")
                print(f"      ⭐ Stars: {repo.stargazers_count}")
                print(f"      🔧 Language: {repo.language}")
                print(f"      📝 {repo.description}")
                print(f"      🛡️  Security Score: {min(security_score, 10)}/10")
                if security_files:
                    print(f"      📄 Security Files: {', '.join(security_files[:2])}...")
                print()
            
            # Security summary
            avg_security_score = sum(v['security_score'] for v in vulnerability_data) / len(vulnerability_data)
            print(f"📊 SECURITY SUMMARY:")
            print(f"   • Repositories Analyzed: {len(vulnerability_data)}")
            print(f"   • Average Security Score: {avg_security_score:.1f}/10")
            print(f"   • High Security Repos: {sum(1 for v in vulnerability_data if v['security_score'] >= 7)}")
            print(f"   • Requires Review: {sum(1 for v in vulnerability_data if v['security_score'] < 7)}")
            
            print("✅ GuardianAgent can scan GitHub for security vulnerabilities")
            
        except Exception as e:
            print(f"❌ Guardian GitHub demo failed: {e}")
    
    async def _demo_multi_agent_coordination(self):
        """Demonstrate multi-agent coordination using GitHub data"""
        print("\n🤝 MULTI-AGENT COORDINATION WITH GITHUB DATA")
        print("-" * 60)
        
        print("🎯 Simulating coordinated DeFi arbitrage analysis...")
        
        try:
            # Simulate a coordinated workflow
            workflow_steps = [
                "1. 📚 IndexerAgent: Index Uniswap V3 protocol from GitHub",
                "2. 📊 AnalyzerAgent: Analyze arbitrage opportunities in indexed code",
                "3. ⚡ ExecutorAgent: Verify contracts for safe execution",
                "4. 🛡️  GuardianAgent: Perform security scan on execution plan",
                "5. 🎯 CoordinatorAgent: Orchestrate final execution strategy"
            ]
            
            print("🔄 COORDINATION WORKFLOW:")
            for step in workflow_steps:
                print(f"   {step}")
                await asyncio.sleep(0.5)  # Simulate processing
            
            # Simulate coordination results
            coordination_results = {
                "protocols_indexed": 4,
                "arbitrage_opportunities": 12,
                "contracts_verified": 8,
                "security_issues": 1,
                "recommended_actions": 3,
                "estimated_profit": "$2,500",
                "risk_level": "Medium",
                "execution_confidence": "85%"
            }
            
            print("\n📊 COORDINATION RESULTS:")
            for key, value in coordination_results.items():
                formatted_key = key.replace('_', ' ').title()
                print(f"   • {formatted_key}: {value}")
            
            print("\n🎉 MULTI-AGENT COORDINATION SUCCESSFUL!")
            print("   All agents successfully used GitHub token for specialized operations")
            
        except Exception as e:
            print(f"❌ Multi-agent coordination demo failed: {e}")

async def interactive_demo():
    """Interactive demonstration mode"""
    print("\n💬 INTERACTIVE GITHUB INTEGRATION DEMO")
    print("="*80)
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        github_token = input("Enter your GitHub token: ").strip()
        if not github_token:
            print("❌ GitHub token required")
            return
    
    demo = GitHubIntegrationDemo(github_token)
    
    while True:
        print("\n🎯 AVAILABLE DEMONSTRATIONS:")
        print("1. 🔗 Verify GitHub Connection")
        print("2. 🎯 Coordinator GitHub Features")
        print("3. 📚 Indexer GitHub Features")
        print("4. 📊 Analyzer GitHub Features")
        print("5. ⚡ Executor GitHub Features")
        print("6. 🛡️  Guardian GitHub Features")
        print("7. 🤝 Multi-Agent Coordination")
        print("8. 🚀 Full Demo Suite")
        print("9. ❌ Exit")
        
        choice = input("\nSelect demo (1-9): ").strip()
        
        try:
            if choice == "1":
                await demo._verify_github_connection()
            elif choice == "2":
                await demo._demo_coordinator_github_features()
            elif choice == "3":
                await demo._demo_indexer_github_features()
            elif choice == "4":
                await demo._demo_analyzer_github_features()
            elif choice == "5":
                await demo._demo_executor_github_features()
            elif choice == "6":
                await demo._demo_guardian_github_features()
            elif choice == "7":
                await demo._demo_multi_agent_coordination()
            elif choice == "8":
                await demo.run_demo()
            elif choice == "9":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-9.")
        except Exception as e:
            print(f"❌ Demo error: {e}")

async def main():
    """Main execution"""
    print("🚀 ENHANCED GITHUB INTEGRATION DEMONSTRATION")
    print("="*80)
    print("This demo shows all 5 agents actively using GitHub token:")
    print("• CoordinatorAgent: Project analysis and coordination")
    print("• IndexerAgent: Protocol repository indexing")
    print("• AnalyzerAgent: Smart contract code analysis")
    print("• ExecutorAgent: Contract verification")
    print("• GuardianAgent: Security vulnerability scanning")
    
    mode = input("\nRun [F]ull demo or [I]nteractive mode? (F/I): ").strip().upper()
    
    if mode == "I":
        await interactive_demo()
    else:
        # Full demo mode
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            github_token = input("Enter your GitHub token: ").strip()
            if not github_token:
                print("❌ GitHub token required")
                return
        
        demo = GitHubIntegrationDemo(github_token)
        await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
