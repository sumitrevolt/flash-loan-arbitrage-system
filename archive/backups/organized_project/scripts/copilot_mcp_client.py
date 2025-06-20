"""
GitHub Copilot MCP Client
This module provides an interface for GitHub Copilot to interact with MCP servers.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CopilotMCPClient:
    """Client for GitHub Copilot to interact with MCP servers."""
    
    def __init__(self, bridge_url: str = "ws://localhost:8888"):
        self.bridge_url = bridge_url
        self.websocket = None
        self.mcp_servers: Dict[str, str] = {}
        self.is_connected = False
        
    async def connect(self) -> bool:
        """Connect to the MCP bridge."""
        try:
            self.websocket = await websockets.connect(self.bridge_url)
            self.is_connected = True
            logger.info(f"Connected to MCP bridge at {self.bridge_url}")
            
            # Get available servers
            await self.refresh_servers()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP bridge: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP bridge."""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from MCP bridge")
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MCP bridge and wait for response."""
        if not self.is_connected or not self.websocket:
            raise Exception("Not connected to MCP bridge")
        
        try:
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def refresh_servers(self) -> Dict[str, str]:
        """Refresh the list of available MCP servers."""
        try:
            response = await self.send_message({"action": "list_servers"})
            if response.get("status") == "success":
                self.mcp_servers = response.get("servers", {})
                logger.info(f"Found {len(self.mcp_servers)} available MCP servers")
                return self.mcp_servers
            else:
                logger.error(f"Failed to refresh servers: {response.get('message')}")
                return {}
        except Exception as e:
            logger.error(f"Error refreshing servers: {e}")
            return {}
    
    async def call_mcp_server(self, server_name: str, method: str = "GET", path: str = "/", data: Any = None) -> Dict[str, Any]:
        """Call a specific MCP server."""
        if server_name not in self.mcp_servers:
            await self.refresh_servers()
            if server_name not in self.mcp_servers:
                return {"status": "error", "message": f"Server '{server_name}' not available"}
        message: Dict[str, Any] = {
            "action": "proxy_request",
            "server": server_name,
            "method": method,
            "path": path,
            "data": data
        }
        
        return await self.send_message(message)
    
    # Flash Loan specific methods
    async def get_flash_loan_opportunities(self) -> Dict[str, Any]:
        """Get flash loan arbitrage opportunities."""
        return await self.call_mcp_server("arbitrage", "GET", "/opportunities")
    
    async def analyze_defi_protocol(self, protocol: str) -> Dict[str, Any]:
        """Analyze a DeFi protocol."""
        data = {"protocol": protocol}
        return await self.call_mcp_server("defi_analyzer", "POST", "/analyze", data)
    
    async def get_token_prices(self, tokens: List[str]) -> Dict[str, Any]:
        """Get current token prices."""
        data = {"tokens": tokens}
        return await self.call_mcp_server("price_feed", "POST", "/prices", data)
    
    async def check_liquidity(self, token_pair: str) -> Dict[str, Any]:
        """Check liquidity for a token pair."""
        data = {"pair": token_pair}
        return await self.call_mcp_server("liquidity", "POST", "/check", data)
    
    async def assess_risk(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for a trading strategy."""
        return await self.call_mcp_server("risk_manager", "POST", "/assess", strategy)
    
    async def get_portfolio_status(self) -> Dict[str, Any]:
        """Get current portfolio status."""
        return await self.call_mcp_server("portfolio", "GET", "/status")
    
    async def execute_flash_loan(self, loan_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a flash loan (simulation mode by default)."""
        return await self.call_mcp_server("flash_loan", "POST", "/execute", loan_params)
    
    # Utility methods for GitHub Copilot integration    def get_context_for_copilot(self) -> str:
        """Get context string for GitHub Copilot."""
        context = [
            "Available MCP Services for Flash Loan System:",
            f"Connected to {len(self.mcp_servers)} MCP servers:",  # type: ignore
        ]
        
        for server_name in self.mcp_servers.keys():  # type: ignore
            context.append(f"  - {server_name}: {self._get_server_description(server_name)}")  # type: ignore
        
        context.extend([
            "",
            "Available operations:",
            "  - get_flash_loan_opportunities(): Find arbitrage opportunities",
            "  - analyze_defi_protocol(protocol): Analyze DeFi protocols",
            "  - get_token_prices(tokens): Get real-time token prices",
            "  - check_liquidity(pair): Check liquidity for token pairs",
            "  - assess_risk(strategy): Risk assessment for strategies",
            "  - get_portfolio_status(): Current portfolio information",
            "  - execute_flash_loan(params): Execute flash loan operations",
        ])
        
        return "\n".join(context)
    
    def _get_server_description(self, server_name: str) -> str:
        """Get description for a server."""
        descriptions = {
            "flash_loan_blockchain": "Blockchain operations and flash loan functionality",
            "defi_analyzer": "DeFi protocol analysis and insights",
            "flash_loan": "Core flash loan operations",
            "arbitrage": "Arbitrage opportunity detection and execution",
            "liquidity": "Liquidity pool management and analysis",
            "price_feed": "Real-time price data and feeds",
            "risk_manager": "Risk assessment and management",
            "portfolio": "Portfolio tracking and management",
            "api_client": "External API integrations",
            "database": "Database operations and queries",
            "cache_manager": "Caching and performance optimization",
            "file_processor": "File processing and management",
            "notification": "Notification and alerting system",
            "monitoring": "System monitoring and health checks",
            "security": "Security and authentication",
            "data_analyzer": "Data analysis and processing",
            "web_scraper": "Web scraping and data collection",
            "task_queue": "Task queuing and job management",
            "filesystem": "File system operations",
            "coordinator": "MCP server coordination and orchestration"
        }
        return descriptions.get(server_name, "Unknown server")

# Global client instance for GitHub Copilot
_copilot_mcp_client = None

async def get_copilot_mcp_client() -> CopilotMCPClient:
    """Get or create the global MCP client for GitHub Copilot."""
    global _copilot_mcp_client
    
    if _copilot_mcp_client is None:
        _copilot_mcp_client = CopilotMCPClient()
        await _copilot_mcp_client.connect()
    
    return _copilot_mcp_client

# Convenience functions for GitHub Copilot
async def mcp_get_flash_loan_opportunities():
    """Get flash loan opportunities (GitHub Copilot convenience function)."""
    client = await get_copilot_mcp_client()
    return await client.get_flash_loan_opportunities()

async def mcp_analyze_protocol(protocol: str):
    """Analyze DeFi protocol (GitHub Copilot convenience function)."""
    client = await get_copilot_mcp_client()
    return await client.analyze_defi_protocol(protocol)

async def mcp_get_prices(tokens: List[str]):
    """Get token prices (GitHub Copilot convenience function)."""
    client = await get_copilot_mcp_client()
    return await client.get_token_prices(tokens)

async def mcp_check_liquidity(pair: str):
    """Check liquidity (GitHub Copilot convenience function)."""
    client = await get_copilot_mcp_client()
    return await client.check_liquidity(pair)

async def mcp_assess_risk(strategy: Dict[str, Any]):
    """Assess risk (GitHub Copilot convenience function)."""
    client = await get_copilot_mcp_client()
    return await client.assess_risk(strategy)

async def mcp_get_portfolio():
    """Get portfolio status (GitHub Copilot convenience function)."""
    client = await get_copilot_mcp_client()
    return await client.get_portfolio_status()

def main():
    """Test the MCP client."""
    async def test():
        client = CopilotMCPClient()
        if await client.connect():
            print("✓ Connected to MCP bridge")
            print("\nAvailable servers:")
            for name, endpoint in client.mcp_servers.items():  # type: ignore
                print(f"  - {name}: {endpoint}")  # type: ignore
            
            print("\nTesting flash loan opportunities...")
            opportunities = await client.get_flash_loan_opportunities()
            print(f"Opportunities: {opportunities}")
            
            await client.disconnect()
        else:
            print("✗ Failed to connect to MCP bridge")
            print("Make sure the MCP bridge is running: python mcp_bridge.py")
    
    asyncio.run(test())

if __name__ == "__main__":
    main()
