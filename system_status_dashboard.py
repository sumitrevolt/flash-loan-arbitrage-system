#!/usr/bin/env python3
"""
Enhanced System Status Dashboard
==============================

Real-time dashboard showing the status of all MCP servers, AI agents, 
and interaction system components.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from unicode_safe_logger import get_unicode_safe_logger

# Configure Unicode-safe logging
logger = get_unicode_safe_logger(__name__, 'system_status_dashboard.log')

class SystemStatusDashboard:
    """Real-time system status dashboard"""
    
    def __init__(self):
        # Your existing MCP servers (21 servers)
        self.mcp_servers = {
            'mcp_flash_loan_server': 'http://localhost:8085',
            'mcp_price_feed_server': 'http://localhost:8091',
            'mcp_arbitrage_server': 'http://localhost:8073',
            'mcp_blockchain_server': 'http://localhost:8075',
            'mcp_defi_analyzer_server': 'http://localhost:8081',
            'mcp_liquidity_server': 'http://localhost:8087',
            'mcp_risk_manager_server': 'http://localhost:8094',
            'mcp_monitoring_server': 'http://localhost:8088',
            'mcp_coordinator_server': 'http://localhost:8077',
            'mcp_data_analyzer_server': 'http://localhost:8080',
            'evm_mcp_server': 'http://localhost:8065',
            'foundry_mcp_mcp_server': 'http://localhost:8068',
            'copilot_mcp_mcp_server': 'http://localhost:8059',
            'dex_aggregator_mcp_server': 'http://localhost:8062',
            'mcp_portfolio_server': 'http://localhost:8090',
            'mcp_security_server': 'http://localhost:8095',
            'mcp_notification_server': 'http://localhost:8089',
            'mcp_task_queue_server': 'http://localhost:8102',
            'mcp_database_server': 'http://localhost:8079',
            'mcp_integration_bridge': 'http://localhost:8086',
            'profit_optimizer_mcp_server': 'http://localhost:8108'
        }
        
        # Your existing AI agents (10 agents)
        self.ai_agents = {
            'flash_loan_optimizer': 'http://localhost:9001',
            'risk_manager': 'http://localhost:9002',
            'arbitrage_detector': 'http://localhost:9003',
            'transaction_executor': 'http://localhost:9004',
            'market_analyzer': 'http://localhost:8201',
            'data_collector': 'http://localhost:8205',
            'arbitrage_bot': 'http://localhost:8206',
            'liquidity_manager': 'http://localhost:8207',
            'reporter': 'http://localhost:8208',
            'healer': 'http://localhost:8209'
        }
        
        # System status tracking
        self.status_data = {
            'mcp_servers': {},
            'ai_agents': {},
            'system_health': 0,
            'total_interactions': 0,
            'last_update': None
        }
    
    async def check_service_health(self, url: str) -> Dict:
        """Check health of a single service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'status': 'healthy',
                            'response_time': response.headers.get('X-Response-Time', 'N/A'),
                            'data': data
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'response_time': 'N/A',
                            'error': f'HTTP {response.status}'
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'timeout',
                'response_time': '>5000ms',
                'error': 'Request timeout'
            }
        except Exception as e:
            return {
                'status': 'unreachable',
                'response_time': 'N/A',
                'error': str(e)
            }
    
    async def update_system_status(self):
        """Update status of all system components"""
        logger.info("🔄 Updating system status...")
        
        # Check MCP servers
        mcp_tasks = []
        for name, url in self.mcp_servers.items():
            task = asyncio.create_task(self.check_service_health(url))
            mcp_tasks.append((name, task))
        
        # Check AI agents
        agent_tasks = []
        for name, url in self.ai_agents.items():
            task = asyncio.create_task(self.check_service_health(url))
            agent_tasks.append((name, task))
        
        # Wait for all health checks to complete
        for name, task in mcp_tasks:
            try:
                self.status_data['mcp_servers'][name] = await task
            except Exception as e:
                self.status_data['mcp_servers'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        for name, task in agent_tasks:
            try:
                self.status_data['ai_agents'][name] = await task
            except Exception as e:
                self.status_data['ai_agents'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Calculate system health
        self.status_data['system_health'] = self.calculate_system_health()
        self.status_data['last_update'] = datetime.now().isoformat()
    
    def calculate_system_health(self) -> float:
        """Calculate overall system health percentage"""
        total_services = len(self.mcp_servers) + len(self.ai_agents)
        healthy_services = 0
        
        # Count healthy MCP servers
        for status in self.status_data['mcp_servers'].values():
            if status.get('status') == 'healthy':
                healthy_services += 1
        
        # Count healthy AI agents
        for status in self.status_data['ai_agents'].values():
            if status.get('status') == 'healthy':
                healthy_services += 1
        
        return (healthy_services / total_services) * 100 if total_services > 0 else 0
    
    def display_dashboard(self):
        """Display the system status dashboard"""
        # Clear screen
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
          logger.info("="*100)
        logger.info("🚀 ENHANCED MULTICHAIN AGENTIC SYSTEM - REAL-TIME DASHBOARD")
        logger.info("="*100)
        logger.info(f"⏰ Last Update: {self.status_data.get('last_update', 'Never')}")
        logger.info(f"🏥 System Health: {self.status_data['system_health']:.1f}%")
        logger.info("")
        
        # MCP Servers Status        logger.info("🔧 MCP SERVERS STATUS (21 Servers)")
        print("-" * 60)
        
        mcp_healthy = 0
        mcp_total = len(self.mcp_servers)
        
        for name, status in self.status_data['mcp_servers'].items():
            status_icon = self.get_status_icon(status.get('status', 'unknown'))
            port = self.extract_port(self.mcp_servers[name])
            response_time = status.get('response_time', 'N/A')
            
            print(f"{status_icon} {name:<35} Port: {port:<5} Response: {response_time}")
            
            if status.get('status') == 'healthy':
                mcp_healthy += 1
        
        print(f"\n📊 MCP Servers: {mcp_healthy}/{mcp_total} healthy ({(mcp_healthy/mcp_total)*100:.1f}%)")
        print()
        
        # AI Agents Status
        print("🤖 AI AGENTS STATUS (10 Agents)")
        print("-" * 60)
        
        agents_healthy = 0
        agents_total = len(self.ai_agents)
        
        for name, status in self.status_data['ai_agents'].items():
            status_icon = self.get_status_icon(status.get('status', 'unknown'))
            port = self.extract_port(self.ai_agents[name])
            response_time = status.get('response_time', 'N/A')
            
            print(f"{status_icon} {name:<35} Port: {port:<5} Response: {response_time}")
            
            if status.get('status') == 'healthy':
                agents_healthy += 1
        
        print(f"\n📊 AI Agents: {agents_healthy}/{agents_total} healthy ({(agents_healthy/agents_total)*100:.1f}%)")
        print()
        
        # System Summary
        print("📈 SYSTEM SUMMARY")
        print("-" * 30)
        print(f"Total Services: {mcp_total + agents_total}")
        print(f"Healthy Services: {mcp_healthy + agents_healthy}")
        print(f"Unhealthy Services: {(mcp_total + agents_total) - (mcp_healthy + agents_healthy)}")
        print(f"Overall Health: {self.status_data['system_health']:.1f}%")
        print()
        
        # Service Categories
        print("🎯 SERVICE CATEGORIES")
        print("-" * 40)
        print("Core Trading Services:")
        core_services = ['mcp_flash_loan_server', 'mcp_arbitrage_server', 'mcp_price_feed_server']
        for service in core_services:
            if service in self.status_data['mcp_servers']:
                status = self.status_data['mcp_servers'][service].get('status', 'unknown')
                icon = self.get_status_icon(status)
                print(f"  {icon} {service}")
        
        print("\nAI Decision Agents:")
        ai_core = ['arbitrage_detector', 'risk_manager', 'flash_loan_optimizer']
        for agent in ai_core:
            if agent in self.status_data['ai_agents']:
                status = self.status_data['ai_agents'][agent].get('status', 'unknown')
                icon = self.get_status_icon(status)
                print(f"  {icon} {agent}")
        
        print("\nData & Analysis Services:")
        data_services = ['mcp_data_analyzer_server', 'mcp_defi_analyzer_server', 'market_analyzer']
        for service in data_services:
            status = 'unknown'
            if service in self.status_data['mcp_servers']:
                status = self.status_data['mcp_servers'][service].get('status', 'unknown')
            elif service in self.status_data['ai_agents']:
                status = self.status_data['ai_agents'][service].get('status', 'unknown')
            icon = self.get_status_icon(status)
            print(f"  {icon} {service}")
        
        print()
        print("="*100)
        print("Press Ctrl+C to exit dashboard")
        print("="*100)
    
    def get_status_icon(self, status: str) -> str:
        """Get status icon for display"""
        status_icons = {
            'healthy': '✅',
            'unhealthy': '⚠️',
            'timeout': '⏰',
            'unreachable': '❌',
            'error': '💥',
            'unknown': '❓'
        }
        return status_icons.get(status, '❓')
    
    def extract_port(self, url: str) -> str:
        """Extract port number from URL"""
        try:
            return url.split(':')[-1]
        except:
            return 'N/A'
    
    async def run_dashboard(self, update_interval: int = 30):
        """Run the dashboard with periodic updates"""
        print("🚀 Starting Enhanced System Dashboard...")
        print("   This will monitor all your MCP servers and AI agents")
        print("   Dashboard updates every 30 seconds")
        print()
        
        try:
            while True:
                await self.update_system_status()
                self.display_dashboard()
                
                # Wait for next update
                for i in range(update_interval):
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped by user")
        except Exception as e:
            print(f"\n❌ Dashboard error: {e}")

def main():
    """Main function to run the dashboard"""
    dashboard = SystemStatusDashboard()
    
    try:
        asyncio.run(dashboard.run_dashboard())
    except Exception as e:
        print(f"Failed to start dashboard: {e}")

if __name__ == "__main__":
    main()
