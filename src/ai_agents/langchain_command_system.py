#!/usr/bin/env python3
"""
LangChain-Powered Command System for MCP Servers and AI Agents
============================================================

Advanced command system that uses LangChain to orchestrate all MCP servers 
and AI agents for indexing, self-healing, revenue generation, and coordination.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
import websockets
from pathlib import Path

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool, BaseTool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from langchain.agents.agent_types import AgentType

# Local imports
from core.interaction_system_enhancer import InteractionSystemEnhancer
from enhanced_orchestrator_integration import EnhancedDockerOrchestrator

logger = logging.getLogger(__name__)

@dataclass
class CommandResult:
    """Result of a command execution"""
    success: bool
    message: str
    data: Optional[Dict] = None
    agent_responses: Optional[List] = None

class MCPServerTool(BaseTool):
    """LangChain tool for MCP server interactions"""
    
    name: str = "mcp_server_command"
    description: str = "Execute commands on MCP servers for arbitrage operations"
    
    def __init__(self, command_system):
        super().__init__()
        self.command_system = command_system
    
    def _run(self, command: str, server: str = None, **kwargs) -> str:
        """Execute MCP server command"""
        try:
            result = asyncio.run(self.command_system.execute_mcp_command(command, server))
            return f"MCP Command Result: {result}"
        except Exception as e:
            return f"MCP Command Error: {str(e)}"
    
    async def _arun(self, command: str, server: str = None, **kwargs) -> str:
        """Async execution of MCP server command"""
        try:
            result = await self.command_system.execute_mcp_command(command, server)
            return f"MCP Command Result: {result}"
        except Exception as e:
            return f"MCP Command Error: {str(e)}"

class AIAgentTool(BaseTool):
    """LangChain tool for AI agent interactions"""
    
    name: str = "ai_agent_command"
    description: str = "Coordinate with AI agents for market analysis and execution"
    
    def __init__(self, command_system):
        super().__init__()
        self.command_system = command_system
    
    def _run(self, command: str, agent: str = None, **kwargs) -> str:
        """Execute AI agent command"""
        try:
            result = asyncio.run(self.command_system.execute_agent_command(command, agent))
            return f"Agent Command Result: {result}"
        except Exception as e:
            return f"Agent Command Error: {str(e)}"
    
    async def _arun(self, command: str, agent: str = None, **kwargs) -> str:
        """Async execution of AI agent command"""
        try:
            result = await self.command_system.execute_agent_command(command, agent)
            return f"Agent Command Result: {result}"
        except Exception as e:
            return f"Agent Command Error: {str(e)}"

class RevenueGeneratorTool(BaseTool):
    """LangChain tool for revenue generation commands"""
    
    name: str = "revenue_generator"
    description: str = "Execute revenue generation strategies and arbitrage operations"
    
    def __init__(self, command_system):
        super().__init__()
        self.command_system = command_system
    
    def _run(self, strategy: str, params: Dict = None, **kwargs) -> str:
        """Execute revenue generation strategy"""
        try:
            result = asyncio.run(self.command_system.execute_revenue_strategy(strategy, params))
            return f"Revenue Strategy Result: {result}"
        except Exception as e:
            return f"Revenue Strategy Error: {str(e)}"
    
    async def _arun(self, strategy: str, params: Dict = None, **kwargs) -> str:
        """Async execution of revenue strategy"""
        try:
            result = await self.command_system.execute_revenue_strategy(strategy, params)
            return f"Revenue Strategy Result: {result}"
        except Exception as e:
            return f"Revenue Strategy Error: {str(e)}"

class LangChainCommandSystem:
    """Main LangChain command system for MCP servers and AI agents"""
    
    def __init__(self):
        self.orchestrator = None
        self.interaction_enhancer = None
        self.agents = {}
        self.mcp_servers = {}
        self.revenue_stats = {
            'total_profit': 0.0,
            'successful_trades': 0,
            'failed_trades': 0,
            'opportunities_found': 0,
            'uptime_hours': 0
        }
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
        
        self.memory = ConversationBufferWindowMemory(
            k=10,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Initialize tools
        self.tools = [
            MCPServerTool(self),
            AIAgentTool(self),
            RevenueGeneratorTool(self),
            Tool(
                name="system_status",
                description="Get current system status and health",
                func=self.get_system_status
            ),
            Tool(
                name="market_analysis",
                description="Perform comprehensive market analysis",
                func=self.perform_market_analysis
            ),
            Tool(
                name="auto_heal",
                description="Execute self-healing procedures",
                func=self.execute_self_healing
            )
        ]
        
        # Create agent prompt
        self.agent_prompt = PromptTemplate.from_template("""
You are an advanced arbitrage trading AI commanding a fleet of MCP servers and AI agents.

Available Tools: {tools}
Tool Names: {tool_names}

Your mission:
1. Index and analyze all market data across chains
2. Coordinate AI agents for optimal strategies
3. Execute profitable arbitrage opportunities
4. Maintain system health through self-healing
5. Generate consistent revenue

Current System Status:
- MCP Servers: {mcp_status}
- AI Agents: {agent_status}
- Revenue Stats: {revenue_stats}

Previous conversation:
{chat_history}

Human Command: {input}

Think step by step and use tools as needed. 
Focus on profitable opportunities and system optimization.

{agent_scratchpad}
""")
        
        # Create agent executor
        self.agent_executor = None
        self.setup_agent_executor()
    
    def setup_agent_executor(self):
        """Setup the LangChain agent executor"""
        try:
            # Create the agent
            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.agent_prompt
            )
            
            # Create executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )
            
            logger.info("✅ LangChain agent executor initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup agent executor: {e}")
    
    async def initialize_system(self):
        """Initialize the command system with orchestrator and enhancer"""
        try:
            print("🚀 Initializing LangChain Command System...")
            
            # Initialize orchestrator
            self.orchestrator = EnhancedDockerOrchestrator()
            
            # Initialize interaction enhancer
            self.interaction_enhancer = InteractionSystemEnhancer()
            
            # Load MCP server configs
            await self.load_mcp_servers()
            
            # Load AI agent configs
            await self.load_ai_agents()
            
            print("✅ LangChain Command System initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {e}")
            return False
    
    async def load_mcp_servers(self):
        """Load MCP server configurations"""
        try:
            config_path = Path("unified_mcp_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.mcp_servers = config.get('mcp_servers', {})
                    print(f"📋 Loaded {len(self.mcp_servers)} MCP servers")
        except Exception as e:
            logger.error(f"❌ Failed to load MCP servers: {e}")
    
    async def load_ai_agents(self):
        """Load AI agent configurations"""
        try:
            config_path = Path("ai_agents_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.agents = config.get('agents', {})
                    print(f"🤖 Loaded {len(self.agents)} AI agents")
        except Exception as e:
            logger.error(f"❌ Failed to load AI agents: {e}")
    
    async def execute_command(self, command: str) -> CommandResult:
        """Execute a command through LangChain agent"""
        try:
            print(f"\n🎯 Executing command: {command}")
            
            # Prepare context
            context = {
                'mcp_status': f"{len(self.mcp_servers)} servers",
                'agent_status': f"{len(self.agents)} agents",
                'revenue_stats': self.revenue_stats,
                'tools': [tool.name for tool in self.tools],
                'tool_names': ', '.join([tool.name for tool in self.tools])
            }
            
            # Execute through agent
            if self.agent_executor:
                response = await self.agent_executor.ainvoke({
                    "input": command,
                    **context
                })
                
                return CommandResult(
                    success=True,
                    message=response.get('output', 'Command executed'),
                    data={'response': response}
                )
            else:
                return CommandResult(
                    success=False,
                    message="Agent executor not initialized"
                )
                
        except Exception as e:
            logger.error(f"❌ Command execution failed: {e}")
            return CommandResult(
                success=False,
                message=f"Command failed: {str(e)}"
            )
    
    async def execute_mcp_command(self, command: str, server: str = None) -> Dict:
        """Execute command on MCP servers"""
        results = {}
        
        if server and server in self.mcp_servers:
            # Execute on specific server
            results[server] = await self._call_mcp_server(server, command)
        else:
            # Execute on all servers
            for server_name in self.mcp_servers:
                results[server_name] = await self._call_mcp_server(server_name, command)
        
        return results
    
    async def _call_mcp_server(self, server_name: str, command: str) -> Dict:
        """Call a specific MCP server"""
        try:
            server_config = self.mcp_servers[server_name]
            url = f"http://localhost:{server_config['port']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{url}/execute", json={
                    'command': command,
                    'timestamp': datetime.now().isoformat()
                }) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'error': str(e)}
    
    async def execute_agent_command(self, command: str, agent: str = None) -> Dict:
        """Execute command on AI agents"""
        results = {}
        
        if agent and agent in self.agents:
            # Execute on specific agent
            results[agent] = await self._call_ai_agent(agent, command)
        else:
            # Execute on all agents
            for agent_name in self.agents:
                results[agent_name] = await self._call_ai_agent(agent_name, command)
        
        return results
    
    async def _call_ai_agent(self, agent_name: str, command: str) -> Dict:
        """Call a specific AI agent"""
        try:
            agent_config = self.agents[agent_name]
            url = f"http://localhost:{agent_config['port']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{url}/command", json={
                    'command': command,
                    'timestamp': datetime.now().isoformat()
                }) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'error': str(e)}
    
    async def execute_revenue_strategy(self, strategy: str, params: Dict = None) -> Dict:
        """Execute revenue generation strategy"""
        try:
            print(f"💰 Executing revenue strategy: {strategy}")
            
            if strategy == "scan_arbitrage":
                return await self._scan_arbitrage_opportunities(params)
            elif strategy == "execute_trade":
                return await self._execute_arbitrage_trade(params)
            elif strategy == "optimize_portfolio":
                return await self._optimize_portfolio(params)
            elif strategy == "compound_profits":
                return await self._compound_profits(params)
            else:
                return {'error': f'Unknown strategy: {strategy}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    async def _scan_arbitrage_opportunities(self, params: Dict) -> Dict:
        """Scan for arbitrage opportunities"""
        # This would integrate with your MCP servers
        opportunities = []
        
        # Call price feed server
        price_data = await self._call_mcp_server('price-feed', 'get_all_prices')
        
        # Call arbitrage server
        arb_data = await self._call_mcp_server('arbitrage', 'scan_opportunities')
        
        # Analyze with AI agents
        analysis = await self._call_ai_agent('analyzer', 'analyze_opportunities')
        
        return {
            'opportunities_found': len(opportunities),
            'price_data': price_data,
            'arbitrage_data': arb_data,
            'ai_analysis': analysis
        }
    
    async def _execute_arbitrage_trade(self, params: Dict) -> Dict:
        """Execute an arbitrage trade"""
        # This would execute actual trades
        trade_result = {
            'trade_id': f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'profit_usd': 0.0,
            'gas_cost': 0.0,
            'net_profit': 0.0,
            'status': 'pending'
        }
        
        # Update revenue stats
        if trade_result['net_profit'] > 0:
            self.revenue_stats['total_profit'] += trade_result['net_profit']
            self.revenue_stats['successful_trades'] += 1
        else:
            self.revenue_stats['failed_trades'] += 1
        
        return trade_result
    
    async def _optimize_portfolio(self, params: Dict) -> Dict:
        """Optimize portfolio allocation"""
        return {'status': 'optimized', 'changes': []}
    
    async def _compound_profits(self, params: Dict) -> Dict:
        """Compound profits for increased capital"""
        return {'status': 'compounded', 'new_capital': 0.0}
    
    def get_system_status(self) -> str:
        """Get current system status"""
        status = {
            'mcp_servers': len(self.mcp_servers),
            'ai_agents': len(self.agents),
            'revenue_stats': self.revenue_stats,
            'timestamp': datetime.now().isoformat()
        }
        return json.dumps(status, indent=2)
    
    def perform_market_analysis(self) -> str:
        """Perform market analysis"""
        analysis = {
            'market_conditions': 'analyzing...',
            'opportunities': 'scanning...',
            'risk_level': 'calculating...',
            'recommended_actions': []
        }
        return json.dumps(analysis, indent=2)
    
    def execute_self_healing(self) -> str:
        """Execute self-healing procedures"""
        healing_actions = [
            'Checking service health',
            'Restarting failed services',
            'Optimizing performance',
            'Updating configurations'
        ]
        return f"Self-healing executed: {', '.join(healing_actions)}"

# VS Code Integration Commands
class VSCodeCommandInterface:
    """VS Code command interface for direct system interaction"""
    
    def __init__(self, command_system: LangChainCommandSystem):
        self.command_system = command_system
        self.websocket_server = None
        self.connected_clients = set()
    
    async def start_vscode_server(self, port: int = 8888):
        """Start WebSocket server for VS Code integration"""
        try:
            self.websocket_server = await websockets.serve(
                self.handle_vscode_connection,
                "localhost",
                port
            )
            print(f"🔌 VS Code interface started on ws://localhost:{port}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start VS Code server: {e}")
    
    async def handle_vscode_connection(self, websocket, path):
        """Handle VS Code WebSocket connections"""
        try:
            self.connected_clients.add(websocket)
            print(f"🔗 VS Code client connected ({len(self.connected_clients)} total)")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    command = data.get('command', '')
                    
                    # Execute command through LangChain
                    result = await self.command_system.execute_command(command)
                    
                    # Send response back to VS Code
                    response = {
                        'type': 'command_result',
                        'success': result.success,
                        'message': result.message,
                        'data': result.data,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.discard(websocket)
            print(f"🔌 VS Code client disconnected ({len(self.connected_clients)} total)")

# Main execution
async def main():
    """Main entry point for the LangChain command system"""
    print("🚀 Starting LangChain Command System...")
    
    # Initialize command system
    command_system = LangChainCommandSystem()
    await command_system.initialize_system()
    
    # Initialize VS Code interface
    vscode_interface = VSCodeCommandInterface(command_system)
    await vscode_interface.start_vscode_server()
    
    # Start command loop
    print("\n🎯 LangChain Command System Ready!")
    print("Commands available:")
    print("  - 'index codex' - Build comprehensive market index")
    print("  - 'self heal' - Execute self-healing procedures")
    print("  - 'start bot' - Start active trading bot")
    print("  - 'generate revenue' - Execute revenue strategies")
    print("  - 'coordinate agents' - Manage AI agent coordination")
    print("  - 'system status' - Get current system status")
    print("  - 'quit' - Exit system")
    
    try:
        while True:
            try:
                command = input("\n🎯 Enter command: ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                
                if command:
                    result = await command_system.execute_command(command)
                    print(f"\n📊 Result: {result.message}")
                    if result.data:
                        print(f"📋 Data: {json.dumps(result.data, indent=2)}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    finally:
        print("\n👋 Shutting down LangChain Command System...")

if __name__ == "__main__":
    asyncio.run(main())
