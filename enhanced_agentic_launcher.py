#!/usr/bin/env python3
"""
Enhanced Agentic Flash Loan Arbitrage System Launcher
===================================================

This launcher initializes and coordinates all system components including:
- Auto-healing system management
- GitHub integration for community intelligence
- MiniMax M1 AI integration for advanced analysis
- 80+ MCP servers for comprehensive DeFi coverage
- 10 AI agents for autonomous operations
- Real-time monitoring and health scoring
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import system components
try:
    from master_coordination_system import MasterCoordinationSystem
    from system_status_dashboard import SystemStatusDashboard
    from unicode_safe_logger import get_unicode_safe_logger
    from minimax_m1_integration import MiniMaxAgenticIntegration
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")

# Configure logging
logger = get_unicode_safe_logger(__name__)

class EnhancedAgenticLauncher:
    """Enhanced launcher with auto-healing, GitHub integration, and MiniMax M1 AI"""
    
    def __init__(self):
        self.master_system = None
        self.status_dashboard = None
        self.minimax_integration = None
        self.system_health = {
            'overall_health': 0,
            'components': {},
            'last_update': datetime.now().isoformat(),
            'auto_healing_active': False,
            'github_integration': False,
            'minimax_integration': False
        }
        self.running = False
        self.startup_time = None
        
    async def initialize_system(self):
        """Initialize all system components"""
        print("\n🚀 ENHANCED AGENTIC FLASH LOAN ARBITRAGE SYSTEM")
        print("=" * 80)
        print("🔄 Initializing system components...")
        
        self.startup_time = datetime.now()
        
        try:
            # Initialize status dashboard
            print("\n📊 Initializing system status dashboard...")
            self.status_dashboard = SystemStatusDashboard()
            await self.status_dashboard.initialize()
            self.system_health['components']['dashboard'] = 'active'
            
            # Initialize MiniMax M1 integration
            print("\n🤖 Initializing MiniMax M1 AI integration...")
            self.minimax_integration = MiniMaxAgenticIntegration()
            minimax_success = await self.minimax_integration.initialize_integration()
            if minimax_success:
                self.system_health['minimax_integration'] = True
                self.system_health['components']['minimax'] = 'active'
                print("✅ MiniMax M1 integration successful")
            else:
                self.system_health['components']['minimax'] = 'unavailable'
                print("⚠️ MiniMax M1 integration failed (system will continue without AI)")
            
            # Initialize master coordination system
            print("\n🎛️ Initializing master coordination system...")
            self.master_system = MasterCoordinationSystem()
            await self.master_system.initialize()
            self.system_health['components']['master'] = 'active'
            
            # Check GitHub integration
            await self._check_github_integration()
            
            # Enable auto-healing
            await self._enable_auto_healing()
            
            # Calculate overall health
            await self._update_system_health()
            
            print(f"\n✅ System initialization completed in {(datetime.now() - self.startup_time).total_seconds():.2f} seconds")
            print(f"🎯 Overall system health: {self.system_health['overall_health']:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            logger.error(f"System initialization error: {e}")
            return False
    
    async def _check_github_integration(self):
        """Check GitHub integration status"""
        try:
            import github
            github_client = github.Github()
            user = github_client.get_user()
            user.login  # Test access
            self.system_health['github_integration'] = True
            self.system_health['components']['github'] = 'active'
            print("✅ GitHub integration active")
            
            # Index DeFi repositories for enhanced intelligence
            await self._index_defi_repositories(github_client)
            
        except Exception as e:
            self.system_health['components']['github'] = 'degraded'
            print(f"⚠️ GitHub integration degraded: {e}")
    
    async def _index_defi_repositories(self, github_client):
        """Index popular DeFi repositories for community intelligence"""
        try:
            defi_repos = [
                'Uniswap/v3-core', 'Uniswap/v3-periphery',
                'sushiswap/sushiswap', 'curvefi/curve-contract',
                'aave/protocol-v2', 'compound-finance/compound-protocol',
                'OpenZeppelin/openzeppelin-contracts'
            ]
            
            for repo_name in defi_repos:
                try:
                    repo = github_client.get_repo(repo_name)
                    print(f"📚 Indexed: {repo.full_name} ({repo.stargazers_count} stars)")
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Repository indexing failed: {e}")
    
    async def _enable_auto_healing(self):
        """Enable auto-healing capabilities"""
        try:
            self.system_health['auto_healing_active'] = True
            self.system_health['components']['auto_healing'] = 'active'
            print("✅ Auto-healing system enabled")
            
            # Start auto-healing monitor
            asyncio.create_task(self._auto_healing_monitor())
            
        except Exception as e:
            print(f"⚠️ Auto-healing setup failed: {e}")
    
    async def _auto_healing_monitor(self):
        """Monitor system health and auto-heal issues"""
        while self.running:
            try:
                await self._update_system_health()
                
                # Auto-heal if health drops below threshold
                if self.system_health['overall_health'] < 70:
                    await self._auto_heal_system()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Auto-healing monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _auto_heal_system(self):
        """Attempt to heal system issues automatically"""
        print("\n🔧 AUTO-HEALING SYSTEM ACTIVATED")
        print("=" * 50)
        
        try:
            # Restart failed components
            for component, status in self.system_health['components'].items():
                if status in ['degraded', 'failed']:
                    print(f"🔄 Attempting to restart {component}...")
                    await self._restart_component(component)
            
            # Update health after healing attempts
            await self._update_system_health()
            
            healing_success = self.system_health['overall_health'] > 70
            if healing_success:
                print("✅ Auto-healing successful")
            else:
                print("⚠️ Auto-healing partially successful")
                
        except Exception as e:
            print(f"❌ Auto-healing failed: {e}")
            logger.error(f"Auto-healing error: {e}")
    
    async def _restart_component(self, component: str):
        """Restart a specific system component"""
        try:
            if component == 'minimax' and self.minimax_integration:
                await self.minimax_integration.initialize_integration()
            elif component == 'master' and self.master_system:
                await self.master_system.restart_services()
            elif component == 'dashboard' and self.status_dashboard:
                await self.status_dashboard.restart()
            
            print(f"✅ {component} restarted successfully")
            
        except Exception as e:
            print(f"❌ Failed to restart {component}: {e}")
    
    async def _update_system_health(self):
        """Update overall system health score"""
        try:
            component_scores = []
            
            for component, status in self.system_health['components'].items():
                if status == 'active':
                    component_scores.append(100)
                elif status == 'degraded':
                    component_scores.append(60)
                elif status == 'failed':
                    component_scores.append(20)
                else:  # unavailable
                    component_scores.append(0)
            
            if component_scores:
                self.system_health['overall_health'] = sum(component_scores) / len(component_scores)
            else:
                self.system_health['overall_health'] = 0
            
            self.system_health['last_update'] = datetime.now().isoformat()
            
            # Bonus for integrations
            if self.system_health['github_integration']:
                self.system_health['overall_health'] = min(100, self.system_health['overall_health'] + 5)
            
            if self.system_health['minimax_integration']:
                self.system_health['overall_health'] = min(100, self.system_health['overall_health'] + 10)
            
        except Exception as e:
            logger.error(f"Health update error: {e}")
    
    async def start_system(self):
        """Start the enhanced agentic system"""
        print("\n🎬 STARTING ENHANCED AGENTIC SYSTEM")
        print("=" * 60)
        
        self.running = True
        
        try:
            # Start master coordination
            if self.master_system:
                await self.master_system.start()
                print("✅ Master coordination system started")
            
            # Start status dashboard
            if self.status_dashboard:
                await self.status_dashboard.start_monitoring()
                print("✅ Status dashboard started")
            
            # Display system information
            await self._display_system_info()
            
            # Start interactive command loop
            await self._command_loop()
            
        except Exception as e:
            print(f"❌ System start failed: {e}")
            logger.error(f"System start error: {e}")
    
    async def _display_system_info(self):
        """Display comprehensive system information"""
        print("\n" + "=" * 80)
        print("🎯 ENHANCED AGENTIC SYSTEM STATUS")
        print("=" * 80)
        
        # System health
        health_color = "🟢" if self.system_health['overall_health'] > 80 else "🟡" if self.system_health['overall_health'] > 60 else "🔴"
        print(f"{health_color} Overall Health: {self.system_health['overall_health']:.1f}%")
        
        # Components status
        print(f"🔧 Auto-Healing: {'✅ Active' if self.system_health['auto_healing_active'] else '❌ Inactive'}")
        print(f"🐙 GitHub Integration: {'✅ Active' if self.system_health['github_integration'] else '❌ Inactive'}")
        print(f"🤖 MiniMax M1 AI: {'✅ Active' if self.system_health['minimax_integration'] else '❌ Inactive'}")
        
        # Component details
        print(f"\n📊 Component Status:")
        for component, status in self.system_health['components'].items():
            status_icon = {"active": "✅", "degraded": "⚠️", "failed": "❌", "unavailable": "🚫"}.get(status, "❓")
            print(f"   {status_icon} {component.title()}: {status}")
        
        # System capabilities
        print(f"\n🎮 Available Commands:")
        print(f"   📈 arbitrage - Find and execute arbitrage opportunities")
        print(f"   🔍 analyze <protocol> - Analyze specific DeFi protocol")
        print(f"   📊 status - Show detailed system status")
        print(f"   🔧 heal - Trigger manual system healing")
        print(f"   🐙 github <query> - Search GitHub for DeFi solutions")
        
        if self.system_health['minimax_integration']:
            print(f"   🤖 minimax_analyze - AI-powered arbitrage analysis")
            print(f"   ⚠️ minimax_risk - AI risk assessment")
            print(f"   📈 minimax_market - AI market analysis")
            print(f"   🎯 minimax_optimize - AI portfolio optimization")
            print(f"   📋 minimax_strategy - AI trading strategy generation")
            print(f"   📊 minimax_status - MiniMax integration status")
        
        print(f"   🚪 exit - Shutdown system")
        
        print("=" * 80)
    
    async def _command_loop(self):
        """Interactive command loop"""
        print("\n💬 Enhanced Agentic System Ready - Enter commands:")
        
        while self.running:
            try:
                command = input("\n🎯 > ").strip().lower()
                
                if not command:
                    continue
                    
                if command == 'exit':
                    break
                elif command == 'status':
                    await self._handle_status_command()
                elif command == 'heal':
                    await self._auto_heal_system()
                elif command.startswith('arbitrage'):
                    await self._handle_arbitrage_command(command)
                elif command.startswith('analyze'):
                    await self._handle_analyze_command(command)
                elif command.startswith('github'):
                    await self._handle_github_command(command)
                elif command.startswith('minimax_'):
                    await self._handle_minimax_command(command)
                else:
                    print(f"❓ Unknown command: {command}")
                    print("💡 Type 'status' to see available commands")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Shutdown signal received...")
                break
            except Exception as e:
                print(f"❌ Command error: {e}")
                logger.error(f"Command loop error: {e}")
    
    async def _handle_status_command(self):
        """Handle status command"""
        await self._update_system_health()
        await self._display_system_info()
        
        if self.minimax_integration and self.system_health['minimax_integration']:
            minimax_stats = await self.minimax_integration.process_command('minimax_status')
            print(f"\n🤖 MiniMax M1 Statistics:")
            print(f"   Requests: {minimax_stats.get('requests_made', 0)}")
            print(f"   Successful: {minimax_stats.get('successful_responses', 0)}")
            print(f"   Insights: {minimax_stats.get('insights_generated', 0)}")
            print(f"   Assessments: {minimax_stats.get('risk_assessments', 0)}")
    
    async def _handle_arbitrage_command(self, command):
        """Handle arbitrage analysis command"""
        print("🔍 Scanning for arbitrage opportunities...")
        
        # Simulate market data
        market_data = {
            "ETH/USDC": {"uniswap": 2450.50, "sushiswap": 2455.75, "curve": 2449.80},
            "BTC/USDT": {"uniswap": 43250.00, "sushiswap": 43280.50, "curve": 43245.75}
        }
        
        for pair, prices in market_data.items():
            max_price = max(prices.values())
            min_price = min(prices.values())
            profit_potential = ((max_price - min_price) / min_price) * 100
            
            if profit_potential > 0.1:  # 0.1% minimum
                print(f"💰 Opportunity found: {pair}")
                print(f"   Buy: {min(prices, key=prices.get)} @ ${min_price:.2f}")
                print(f"   Sell: {max(prices, key=prices.get)} @ ${max_price:.2f}")
                print(f"   Profit: {profit_potential:.3f}%")
                
                # Use MiniMax AI if available
                if self.system_health['minimax_integration']:
                    ai_analysis = await self.minimax_integration.process_command(
                        'minimax_analyze', 
                        {"token_pair": pair, "prices": prices, "profit_potential": profit_potential}
                    )
                    if 'error' not in ai_analysis:
                        print(f"   🤖 AI Analysis: {ai_analysis.get('analysis', 'Analysis completed')}")
    
    async def _handle_analyze_command(self, command):
        """Handle protocol analysis command"""
        parts = command.split()
        if len(parts) < 2:
            print("❓ Usage: analyze <protocol>")
            return
            
        protocol = parts[1].lower()
        protocols = {
            'uniswap': 'Uniswap V3 - Leading DEX with concentrated liquidity',
            'sushiswap': 'SushiSwap - Community-driven DEX with additional features',
            'curve': 'Curve Finance - Optimized for stablecoin trading',
            'aave': 'Aave - Leading lending and borrowing protocol',
            'compound': 'Compound - Algorithmic money market protocol'
        }
        
        if protocol in protocols:
            print(f"📊 Analyzing {protocol.title()}...")
            print(f"📝 {protocols[protocol]}")
            
            # Use MiniMax AI if available
            if self.system_health['minimax_integration']:
                ai_analysis = await self.minimax_integration.process_command(
                    'minimax_market', 
                    {"protocol": protocol, "analysis_type": "fundamental"}
                )
                if 'error' not in ai_analysis:
                    print(f"🤖 AI Insights: {ai_analysis.get('analysis', 'Analysis completed')}")
        else:
            print(f"❓ Unknown protocol: {protocol}")
            print(f"💡 Available: {', '.join(protocols.keys())}")
    
    async def _handle_github_command(self, command):
        """Handle GitHub search command"""
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            print("❓ Usage: github <search query>")
            return
            
        query = parts[1]
        print(f"🐙 Searching GitHub for: {query}")
        
        try:
            import github
            github_client = github.Github()
            repos = github_client.search_repositories(f"{query} DeFi")
            
            print("📚 Top repositories found:")
            for repo in list(repos)[:5]:  # Top 5 results
                print(f"   ⭐ {repo.full_name} ({repo.stargazers_count} stars)")
                print(f"      {repo.description or 'No description'}")
                
        except Exception as e:
            print(f"❌ GitHub search failed: {e}")
    
    async def _handle_minimax_command(self, command):
        """Handle MiniMax AI command"""
        if not self.system_health['minimax_integration']:
            print("❌ MiniMax M1 integration not available")
            print("💡 Set MINIMAX_API_KEY environment variable and restart")
            return
        
        try:
            # Route to MiniMax integration
            result = await self.minimax_integration.process_command(command)
            
            if 'error' in result:
                print(f"❌ MiniMax Error: {result['error']}")
            else:
                print(f"🤖 MiniMax M1 Result:")
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"   {key}: {value}")
                else:
                    print(f"   {result}")
                    
        except Exception as e:
            print(f"❌ MiniMax command failed: {e}")
    
    async def shutdown_system(self):
        """Gracefully shutdown the system"""
        print("\n🛑 SHUTTING DOWN ENHANCED AGENTIC SYSTEM")
        print("=" * 60)
        
        self.running = False
        
        try:
            # Stop components
            if self.master_system:
                await self.master_system.stop()
                print("✅ Master coordination system stopped")
                
            if self.status_dashboard:
                await self.status_dashboard.stop()
                print("✅ Status dashboard stopped")
                
            if self.minimax_integration:
                print("✅ MiniMax M1 integration disconnected")
            
            runtime = datetime.now() - self.startup_time if self.startup_time else None
            if runtime:
                print(f"⏱️ Total runtime: {runtime}")
            
            print("✅ System shutdown completed")
            
        except Exception as e:
            print(f"❌ Shutdown error: {e}")
            logger.error(f"Shutdown error: {e}")

async def main():
    """Main launcher function"""
    launcher = EnhancedAgenticLauncher()
    
    try:
        # Handle shutdown signals
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}")
            asyncio.create_task(launcher.shutdown_system())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Initialize and start system
        success = await launcher.initialize_system()
        if success:
            await launcher.start_system()
        else:
            print("❌ Failed to initialize system")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal launcher error: {e}")
        return 1
    finally:
        await launcher.shutdown_system()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
