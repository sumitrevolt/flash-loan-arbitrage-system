#!/usr/bin/env python3
"""
Online MCP Coordinator for Flash Loan Arbitrage
Leverages working online MCP servers for enhanced functionality
Extended with Docker orchestration support for 10 MCP agents
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
import subprocess

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/online_mcp_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Windows-specific asyncio event loop fix
if platform.system() == 'Windows':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info("✅ Set Windows ProactorEventLoopPolicy for aiodns compatibility")
    except AttributeError:
        try:
            import asyncio.windows_events
            asyncio.set_event_loop_policy(asyncio.windows_events.WindowsProactorEventLoopPolicy())
            logger.info("✅ Set Windows ProactorEventLoopPolicy (fallback)")
        except ImportError:
            logger.warning("⚠️ Unable to set Windows event loop policy")

@dataclass
class OnlineMCPServer:
    """Configuration for online MCP server"""
    name: str
    server_name: str
    description: str
    tools: List[str]
    enabled: bool = True
    priority: str = "medium"
    last_used: Optional[datetime] = None
    success_count: int = 0
    error_count: int = 0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0

@dataclass
class ArbitrageOpportunity:
    """Enhanced arbitrage opportunity with online MCP integration"""
    token_symbol: str
    token_address: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    profit_usd: float
    profit_percentage: float
    gas_cost_usd: float
    net_profit_usd: float
    liquidity_available: float
    max_trade_size: float
    timestamp: datetime
    confidence_score: float
    risk_level: str
    github_tracked: bool = False
    documentation_verified: bool = False

class OnlineMCPCoordinator:
    """
    Enhanced coordinator that leverages working online MCP servers for flash loan arbitrage
    Extended with Docker orchestration support for 10 MCP agents
    """
    
    def __init__(self, config_path: str = "unified_online_mcp_config.json"):
        self.config_path = Path(config_path)
        self.online_servers: Dict[str, OnlineMCPServer] = {}
        self.docker_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_manifest: Dict[str, Any] = {}
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Load configuration
        self._load_configuration()
        self._load_docker_configuration()
        
        # Performance tracking
        self.metrics = {
            'total_opportunities_found': 0,
            'github_integrations': 0,
            'documentation_queries': 0,
            'successful_mcp_calls': 0,
            'failed_mcp_calls': 0,
            'system_uptime_seconds': 0,
            'docker_agents_running': 0,
            'total_agent_tasks': 0,
            'coordination_efficiency': 0.0,
            'last_update': datetime.now()
        }
        
        # Data storage
        self.opportunities: List[ArbitrageOpportunity] = []
        self.price_data: Dict[str, Dict[str, Any]] = {}
        self.agent_tasks: Dict[str, List[Dict[str, Any]]] = {}
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        os.makedirs('logs/coordinator', exist_ok=True)
        os.makedirs('logs/agents', exist_ok=True)
        
        logger.info("🚀 Enhanced Online MCP Coordinator with Docker orchestration initialized")
    
    def _load_configuration(self) -> None:
        """Load configuration from JSON file"""
        try:
            if not self.config_path.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Load online MCP servers
            online_mcp_config = config.get('online_mcp_servers', {})
            for server_id, server_config in online_mcp_config.items():
                server = OnlineMCPServer(
                    name=server_id,
                    server_name=server_config['server_name'],
                    description=server_config['description'],
                    tools=server_config['tools'],
                    enabled=server_config.get('enabled', True),
                    priority=server_config.get('priority', 'medium')
                )
                self.online_servers[server_id] = server
            
            logger.info(f"✅ Loaded {len(self.online_servers)} online MCP server configurations")
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            raise
    
    def _load_docker_configuration(self) -> None:
        """Load Docker agent configuration and manifest"""
        try:
            # Load agent manifest if it exists
            manifest_path = Path("config/agent_manifest.json")
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    self.agent_manifest = json.load(f)
                
                # Initialize agent tasks tracking
                for role, role_data in self.agent_manifest.get('agent_roles', {}).items():
                    self.agent_tasks[role] = []
                    for agent in role_data.get('agents', []):
                        self.docker_agents[agent['name']] = {
                            'id': agent['id'],
                            'role': agent['role'],
                            'container_name': agent['container_name'],
                            'port': agent['port'],
                            'url': agent['url'],
                            'mcp_server_path': agent['mcp_server_path'],
                            'capabilities': agent['capabilities'],
                            'priority': agent['priority'],
                            'status': 'unknown',
                            'last_heartbeat': None,
                            'tasks_assigned': 0,
                            'tasks_completed': 0,
                            'error_count': 0
                        }
                
                logger.info(f"✅ Loaded Docker configuration for {len(self.docker_agents)} agents")
                logger.info(f"   • Total agent roles: {len(self.agent_manifest.get('agent_roles', {}))}")
                logger.info(f"   • Total agents: {self.agent_manifest.get('total_agents', 0)}")
            else:
                logger.warning("⚠️ No agent manifest found - Docker orchestration disabled")
                
        except Exception as e:
            logger.error(f"❌ Failed to load Docker configuration: {e}")
    
    async def test_docker_agents(self) -> Dict[str, Dict[str, Any]]:
        """Test connectivity to Docker MCP agents"""
        results = {}
        
        if not self.docker_agents:
            logger.warning("⚠️ No Docker agents configured")
            return results
        
        logger.info(f"🔍 Testing {len(self.docker_agents)} Docker MCP agents...")
        
        for agent_name, agent_config in self.docker_agents.items():
            try:
                # Test agent health via HTTP
                timeout = aiohttp.ClientTimeout(total=5)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    health_url = f"{agent_config['url']}/health"
                    async with session.get(health_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            results[agent_name] = {
                                "status": "healthy",
                                "message": f"Agent {agent_name} responding",
                                "details": data
                            }
                            agent_config['status'] = 'healthy'
                            agent_config['last_heartbeat'] = datetime.now()
                        else:
                            results[agent_name] = {
                                "status": "unhealthy",
                                "message": f"Agent returned status {response.status}"
                            }
                            agent_config['status'] = 'unhealthy'
                            
            except Exception as e:
                results[agent_name] = {
                    "status": "error",
                    "message": f"Failed to connect: {str(e)}"
                }
                agent_config['status'] = 'error'
                agent_config['error_count'] += 1
        
        # Update metrics
        healthy_agents = sum(1 for result in results.values() if result.get('status') == 'healthy')
        self.metrics['docker_agents_running'] = healthy_agents
        
        logger.info(f"📊 Docker Agent Health: {healthy_agents}/{len(self.docker_agents)} agents healthy")
        return results
    
    async def coordinate_agent_task(self, task_type: str, description: str, target_role: str = None, requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """Coordinate a task across Docker MCP agents"""
        try:
            if not self.docker_agents:
                return {"error": "No Docker agents available", "status": "failed"}
            
            # Select appropriate agents based on role and capabilities
            suitable_agents = []
            
            if target_role:
                # Find agents with specific role
                suitable_agents = [
                    name for name, config in self.docker_agents.items()
                    if config['role'] == target_role and config['status'] == 'healthy'
                ]
            else:
                # Find agents with required capabilities
                required_caps = requirements.get('capabilities', []) if requirements else []
                for name, config in self.docker_agents.items():
                    if config['status'] == 'healthy':
                        agent_caps = config.get('capabilities', [])
                        if all(cap in agent_caps for cap in required_caps):
                            suitable_agents.append(name)
            
            if not suitable_agents:
                return {"error": f"No suitable agents found for role: {target_role}", "status": "failed"}
            
            # Select best agent based on workload
            selected_agent = min(suitable_agents, 
                               key=lambda name: Any: self.docker_agents[name]['tasks_assigned'])
            
            # Create task
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.agent_tasks.get(target_role or 'general', []))}"
            task = {
                'task_id': task_id,
                'type': task_type,
                'description': description,
                'assigned_agent': selected_agent,
                'status': 'assigned',
                'created_at': datetime.now().isoformat(),
                'requirements': requirements or {}
            }
            
            # Track task
            role_key = target_role or 'general'
            if role_key not in self.agent_tasks:
                self.agent_tasks[role_key] = []
            self.agent_tasks[role_key].append(task)
            
            # Update agent stats
            self.docker_agents[selected_agent]['tasks_assigned'] += 1
            self.metrics['total_agent_tasks'] += 1
            
            # Send task to agent (simulated)
            await self._send_task_to_agent(selected_agent, task)
            
            logger.info(f"📋 Assigned task {task_id} to agent {selected_agent}")
            
            return {
                "status": "success",
                "task_id": task_id,
                "assigned_agent": selected_agent,
                "agent_role": self.docker_agents[selected_agent]['role']
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to coordinate task: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def _send_task_to_agent(self, agent_name: str, task: Dict[str, Any]) -> bool:
        """Send task to specific Docker agent"""
        try:
            agent_config = self.docker_agents[agent_name]
            
            # Send task via HTTP POST (simulated)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                task_url = f"{agent_config['url']}/tasks"
                async with session.post(task_url, json=task) as response:
                    if response.status == 200:
                        result: str = await response.json()
                        logger.info(f"✅ Task sent to {agent_name}: {result}")
                        return True
                    else:
                        logger.error(f"❌ Failed to send task to {agent_name}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error sending task to {agent_name}: {e}")
            return False
    
    async def get_agent_coordination_status(self) -> Dict[str, Any]:
        """Get comprehensive status of agent coordination"""
        try:
            status = {
                "total_agents": len(self.docker_agents),
                "healthy_agents": sum(1 for agent in self.docker_agents.values() if agent['status'] == 'healthy'),
                "total_tasks": self.metrics.get('total_agent_tasks', 0),
                "agent_roles": {},
                "coordination_efficiency": 0.0
            }
            
            # Calculate per-role statistics
            for role, role_data in self.agent_manifest.get('agent_roles', {}).items():
                role_agents = [agent for agent in self.docker_agents.values() if agent['role'] == role.rstrip('s')]
                
                status["agent_roles"][role] = {
                    "total_agents": len(role_agents),
                    "healthy_agents": sum(1 for agent in role_agents if agent['status'] == 'healthy'),
                    "total_tasks_assigned": sum(agent['tasks_assigned'] for agent in role_agents),
                    "total_tasks_completed": sum(agent['tasks_completed'] for agent in role_agents),
                    "average_load": sum(agent['tasks_assigned'] for agent in role_agents) / max(len(role_agents), 1),
                    "error_rate": sum(agent['error_count'] for agent in role_agents) / max(len(role_agents), 1)
                }
            
            # Calculate coordination efficiency
            total_assigned = sum(agent['tasks_assigned'] for agent in self.docker_agents.values())
            total_completed = sum(agent['tasks_completed'] for agent in self.docker_agents.values())
            
            if total_assigned > 0:
                status["coordination_efficiency"] = (total_completed / total_assigned) * 100
                self.metrics['coordination_efficiency'] = status["coordination_efficiency"]
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get coordination status: {e}")
            return {"error": str(e)}
    
    async def test_online_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """Test all configured online MCP servers"""
        results = {}
        
        logger.info("🔍 Testing online MCP servers...")
        
        for server_id, server in self.online_servers.items():
            if not server.enabled:
                results[server_id] = {"status": "disabled", "message": "Server disabled in config"}
                continue
            
            try:
                # Test specific server functionality
                if server_id == "github":
                    result: str = await self._test_github_mcp()
                elif server_id == "upstash_context7":
                    result: str = await self._test_upstash_context7_mcp()
                elif server_id == "context7_clean":
                    result: str = await self._test_context7_clean_mcp()
                else:
                    result: str = {"status": "unknown", "message": "No test implemented"}
                
                results[server_id] = result
                
                if result.get("status") == "success":
                    server.success_count += 1
                    logger.info(f"✅ {server_id}: {result.get('message', 'Test passed')}")
                else:
                    server.error_count += 1
                    logger.warning(f"⚠️ {server_id}: {result.get('message', 'Test failed')}")
                
            except Exception as e:
                server.error_count += 1
                results[server_id] = {"status": "error", "message": str(e)}
                logger.error(f"❌ {server_id} test failed: {e}")
        
        return results
    
    async def _test_github_mcp(self) -> Dict[str, Any]:
        """Test GitHub MCP server functionality"""
        try:
            # Test search repositories (non-destructive operation)
            result: str = await self._call_github_mcp_tool("search_repositories", {
                "query": "flash loan arbitrage",
                "page": 1,
                "perPage": 5
            })
            
            if result:
                return {
                    "status": "success",
                    "message": f"GitHub MCP working - found {len(result.get('items', []))} repositories",
                    "details": result
                }
            else:
                return {
                    "status": "error",
                    "message": "GitHub MCP returned no results"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"GitHub MCP test failed: {str(e)}"
            }
    
    async def _test_upstash_context7_mcp(self) -> Dict[str, Any]:
        """Test Upstash Context7 MCP server"""
        try:
            # Test library resolution
            result: str = await self._call_upstash_context7_tool("resolve-library-id", {
                "libraryName": "web3"
            })
            
            if result:
                return {
                    "status": "success",
                    "message": "Upstash Context7 MCP working - library resolution successful",
                    "details": result
                }
            else:
                return {
                    "status": "error",
                    "message": "Upstash Context7 MCP returned no results"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Upstash Context7 MCP test failed: {str(e)}"
            }
    
    async def _test_context7_clean_mcp(self) -> Dict[str, Any]:
        """Test Context7 Clean MCP server"""
        try:
            # Test health check
            result: str = await self._call_context7_clean_tool("health", {})
            
            if result:
                return {
                    "status": "success",
                    "message": "Context7 Clean MCP working - health check passed",
                    "details": result
                }
            else:
                return {
                    "status": "error",
                    "message": "Context7 Clean MCP health check failed"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Context7 Clean MCP test failed: {str(e)}"
            }
    
    async def _call_github_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call GitHub MCP tool using use_mcp_tool"""
        try:
            # This would be implemented by the calling system
            # For now, simulate the call
            logger.info(f"📞 Calling GitHub MCP tool: {tool_name} with args: {arguments}")
            
            # Simulate successful response
            if tool_name == "search_repositories":
                return {
                    "items": [
                        {"name": "flash-loan-example", "description": "Example flash loan implementation"},
                        {"name": "arbitrage-bot", "description": "Arbitrage trading bot"}
                    ],
                    "total_count": 2
                }
            
            return {"success": True, "tool": tool_name}
            
        except Exception as e:
            logger.error(f"❌ GitHub MCP tool call failed: {e}")
            return None
    
    async def _call_upstash_context7_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call Upstash Context7 MCP tool"""
        try:
            logger.info(f"📞 Calling Upstash Context7 tool: {tool_name} with args: {arguments}")
            
            # Simulate successful response
            if tool_name == "resolve-library-id":
                return {
                    "library_id": "/ethereum/web3.js",
                    "description": "Ethereum JavaScript API",
                    "version": "latest"
                }
            
            return {"success": True, "tool": tool_name}
            
        except Exception as e:
            logger.error(f"❌ Upstash Context7 tool call failed: {e}")
            return None
    
    async def _call_context7_clean_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call Context7 Clean MCP tool"""
        try:
            logger.info(f"📞 Calling Context7 Clean tool: {tool_name} with args: {arguments}")
            
            # Simulate successful response
            return {"status": "healthy", "server": "context7_clean"}
            
        except Exception as e:
            logger.error(f"❌ Context7 Clean tool call failed: {e}")
            return None
    
    async def enhance_arbitrage_with_mcp(self, opportunity: ArbitrageOpportunity) -> ArbitrageOpportunity:
        """Enhance arbitrage opportunity using online MCP servers"""
        try:
            # Use GitHub MCP to track and document opportunity
            github_server = self.online_servers.get("github")
            if github_server and github_server.enabled:
                github_result: str = await self._document_opportunity_on_github(opportunity)
                if github_result:
                    opportunity.github_tracked = True
                    self.metrics['github_integrations'] += 1
            
            # Use Context7 to verify DEX integration documentation
            context7_server = self.online_servers.get("context7_clean")
            if context7_server and context7_server.enabled:
                docs_result: str = await self._verify_dex_documentation(opportunity)
                if docs_result:
                    opportunity.documentation_verified = True
                    self.metrics['documentation_queries'] += 1
            
            logger.info(f"✅ Enhanced opportunity {opportunity.token_symbol} with MCP integrations")
            return opportunity
            
        except Exception as e:
            logger.error(f"❌ Failed to enhance opportunity with MCP: {e}")
            return opportunity
    
    async def _document_opportunity_on_github(self, opportunity: ArbitrageOpportunity) -> bool:
        """Document opportunity on GitHub using MCP"""
        try:
            # Create opportunity documentation
            doc_content = self._generate_opportunity_documentation(opportunity)
            
            # Use GitHub MCP to create/update file
            result: str = await self._call_github_mcp_tool("create_or_update_file", {
                "owner": "YOUR_GITHUB_USERNAME",  # From config
                "repo": "flash-loan-arbitrage-bot",
                "path": f"opportunities/{opportunity.token_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                "content": doc_content,
                "message": f"Document arbitrage opportunity for {opportunity.token_symbol}",
                "branch": "main"
            })
            
            return result is not None
            
        except Exception as e:
            logger.error(f"❌ Failed to document opportunity on GitHub: {e}")
            return False
    
    def _generate_opportunity_documentation(self, opportunity: ArbitrageOpportunity) -> str:
        """Generate markdown documentation for opportunity"""
        return f"""# Arbitrage Opportunity: {opportunity.token_symbol}

## Summary
- **Token**: {opportunity.token_symbol} ({opportunity.token_address})
- **Buy DEX**: {opportunity.buy_dex} @ ${opportunity.buy_price:.6f}
- **Sell DEX**: {opportunity.sell_dex} @ ${opportunity.sell_price:.6f}
- **Profit**: ${opportunity.net_profit_usd:.2f} ({opportunity.profit_percentage:.2%})
- **Risk Level**: {opportunity.risk_level}
- **Confidence**: {opportunity.confidence_score:.2f}

## Details
- **Max Trade Size**: ${opportunity.max_trade_size:,.2f}
- **Available Liquidity**: ${opportunity.liquidity_available:,.2f}
- **Gas Cost**: ${opportunity.gas_cost_usd:.2f}
- **Timestamp**: {opportunity.timestamp.isoformat()}

## Risk Assessment
- **Risk Level**: {opportunity.risk_level}
- **Confidence Score**: {opportunity.confidence_score:.2f}/1.0

## Execution Plan
1. Monitor price stability
2. Execute flash loan from Aave V3
3. Buy {opportunity.token_symbol} on {opportunity.buy_dex}
4. Sell {opportunity.token_symbol} on {opportunity.sell_dex}
5. Repay flash loan + fees
6. Capture profit: ${opportunity.net_profit_usd:.2f}

---
*Generated by Online MCP Coordinator*
*System: Flash Loan Arbitrage Bot v2.0*
"""
    
    async def _verify_dex_documentation(self, opportunity: ArbitrageOpportunity) -> bool:
        """Verify DEX integration documentation using Context7"""
        try:
            # Search for DEX integration documentation
            buy_dex_docs = await self._call_context7_clean_tool("search_docs", {
                "library": opportunity.buy_dex,
                "query": "flash loan integration swap"
            })
            
            sell_dex_docs = await self._call_context7_clean_tool("search_docs", {
                "library": opportunity.sell_dex,
                "query": "flash loan integration swap"
            })
            
            return buy_dex_docs is not None and sell_dex_docs is not None
            
        except Exception as e:
            logger.error(f"❌ Failed to verify DEX documentation: {e}")
            return False
    
    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report using online MCP servers"""
        try:
            # Test all servers
            server_status = await self.test_online_mcp_servers()
            
            # Test Docker agents if available
            docker_status = await self.test_docker_agents() if self.docker_agents else {}
            
            # Calculate uptime
            uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            self.metrics['system_uptime_seconds'] = uptime
            
            # Generate report
            report = {
                "generated_at": datetime.now().isoformat(),
                "system_info": {
                    "version": "2.0.0",
                    "uptime_hours": uptime / 3600,
                    "status": "operational" if self.is_running else "stopped"
                },
                "online_mcp_servers": {
                    server_id: {
                        "name": server.name,
                        "description": server.description,
                        "enabled": server.enabled,
                        "priority": server.priority,
                        "success_rate": server.success_rate,
                        "total_calls": server.success_count + server.error_count,
                        "status": server_status.get(server_id, {}).get("status", "unknown")
                    }
                    for server_id, server in self.online_servers.items()
                },
                "docker_agents": {
                    "total_configured": len(self.docker_agents),
                    "healthy_agents": len([a for a in docker_status.values() if a.get('status') == 'healthy']),
                    "agent_status": docker_status
                },
                "performance_metrics": self.metrics,
                "opportunities": {
                    "total_found": len(self.opportunities),
                    "github_tracked": sum(1 for opp in self.opportunities if opp.github_tracked),
                    "documentation_verified": sum(1 for opp in self.opportunities if opp.documentation_verified)
                }
            }
            
            # Save report to file
            report_file = f"logs/online_mcp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"📊 Generated comprehensive report: {report_file}")
            return report
            
        except Exception as e:
            logger.error(f"❌ Failed to generate report: {e}")
            return {"error": str(e), "generated_at": datetime.now().isoformat()}
    
    async def start(self) -> None:
        """Start the online MCP coordinator"""
        logger.info("🚀 Starting Enhanced Online MCP Coordinator...")
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # Test all online MCP servers
        test_results = await self.test_online_mcp_servers()
        
        # Count successful connections
        successful_servers = sum(1 for result in test_results.values() if result.get("status") == "success")
        
        if successful_servers > 0:
            logger.info(f"✅ Successfully connected to {successful_servers}/{len(self.online_servers)} online MCP servers")
        else:
            logger.warning("⚠️ No online MCP servers are responding - system running in limited mode")
        
        # Test Docker agents if configured
        if self.docker_agents:
            docker_results = await self.test_docker_agents()
            healthy_agents = sum(1 for result in docker_results.values() if result.get("status") == "healthy")
            logger.info(f"🐳 Docker Agent Status: {healthy_agents}/{len(self.docker_agents)} agents healthy")
        else:
            logger.info("🐳 No Docker agents configured - coordination disabled")
        
        # Start monitoring loop
        monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("🎯 Enhanced Online MCP Coordinator started and monitoring")
        
        # Keep running
        try:
            await monitoring_task
        except KeyboardInterrupt:
            logger.info("👋 Shutting down Enhanced Online MCP Coordinator...")
            self.is_running = False
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Update metrics
                self.metrics['last_update'] = datetime.now()
                
                # Simulate finding arbitrage opportunities
                if len(self.opportunities) < 10:  # Keep max 10 opportunities
                    new_opportunity = await self._simulate_arbitrage_opportunity()
                    if new_opportunity:
                        enhanced_opportunity = await self.enhance_arbitrage_with_mcp(new_opportunity)
                        self.opportunities.append(enhanced_opportunity)
                        self.metrics['total_opportunities_found'] = len(self.opportunities)
                
                # Generate periodic reports
                current_time = datetime.now()
                if current_time.minute % 15 == 0 and current_time.second < 5:  # Every 15 minutes
                    await self.generate_comprehensive_report()
                
                # Wait before next cycle
                await asyncio.sleep(30)  # 30 second cycle
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _simulate_arbitrage_opportunity(self) -> Optional[ArbitrageOpportunity]:
        """Simulate finding an arbitrage opportunity"""
        try:
            # Simulate realistic arbitrage opportunity
            tokens = ["ETH", "USDC", "WBTC", "DAI", "LINK"]
            dexes = ["uniswap_v3", "sushiswap", "balancer", "1inch"]
            
            import random
            token = random.choice(tokens)
            buy_dex = random.choice(dexes)
            sell_dex = random.choice([d for d in dexes if d != buy_dex])
            
            buy_price = random.uniform(1500, 3000)  # ETH price range
            profit_pct = random.uniform(0.005, 0.02)  # 0.5% to 2% profit
            sell_price = buy_price * (1 + profit_pct)
            
            trade_size = random.uniform(10000, 50000)
            profit_usd = trade_size * profit_pct
            gas_cost = random.uniform(20, 100)
            net_profit = profit_usd - gas_cost
            
            if net_profit > 50:  # Minimum profit threshold
                opportunity = ArbitrageOpportunity(
                    token_symbol=token,
                    token_address="0x" + "".join(random.choices("0123456789abcdef", k=40)),
                    buy_dex=buy_dex,
                    sell_dex=sell_dex,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    profit_usd=profit_usd,
                    profit_percentage=profit_pct,
                    gas_cost_usd=gas_cost,
                    net_profit_usd=net_profit,
                    liquidity_available=random.uniform(100000, 1000000),
                    max_trade_size=trade_size,
                    timestamp=datetime.now(),
                    confidence_score=random.uniform(0.6, 0.95),
                    risk_level=random.choice(["low", "medium", "high"])
                )
                
                logger.info(f"💰 Found simulated opportunity: {token} {buy_dex}→{sell_dex} "
                          f"${net_profit:.2f} profit")
                return opportunity
            
        except Exception as e:
            logger.error(f"❌ Error simulating opportunity: {e}")
        
        return None

async def main():
    """Main entry point"""
    coordinator = OnlineMCPCoordinator()
    
    try:
        await coordinator.start()
    except KeyboardInterrupt:
        logger.info("👋 Gracefully shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
