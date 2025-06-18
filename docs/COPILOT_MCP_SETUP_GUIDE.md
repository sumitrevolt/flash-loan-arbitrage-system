# GitHub Copilot MCP Integration Instructions

## Problem
GitHub Copilot is not using the MCP (Model Context Protocol) servers running in Docker containers.

## Solution
I've created a bridge system that allows GitHub Copilot to connect to your MCP servers. Here's what was set up:

### 1. MCP Bridge (`mcp_bridge.py`)
- Creates a WebSocket bridge on port 8888
- Proxies requests between GitHub Copilot and Docker MCP servers
- Health checks all MCP servers
- Handles connection management

### 2. Copilot MCP Client (`copilot_mcp_client.py`)
- Python client for GitHub Copilot integration
- Convenience functions for common operations
- Context generation for AI assistance

### 3. Setup Script (`setup_copilot_mcp.ps1`)
- Automated setup for the integration
- Tests MCP server health
- Creates VS Code tasks and environment configuration

## Setup Instructions

### Step 1: Install Dependencies
```powershell
pip install websockets aiohttp
```

### Step 2: Run Setup Script
```powershell
.\setup_copilot_mcp.ps1
```

### Step 3: Start MCP Bridge
```powershell
python mcp_bridge.py --verbose
```

### Step 4: Test Connection
```powershell
python copilot_mcp_client.py
```

## Manual Setup (Alternative)

### 1. Start MCP Bridge
Open a terminal and run:
```powershell
python mcp_bridge.py --verbose
```

The bridge will:
- Connect to all MCP servers running in Docker
- Start WebSocket server on ws://localhost:8888
- Show health status of all servers

### 2. Configure VS Code
Add to your `.vscode/settings.json`:
```json
{
  "github.copilot.enable": {
    "*": true
  },
  "github.copilot.chat.agent.thinkingTool": true
}
```

### 3. Use MCP Functions in Code
You can now use MCP functions in your Python code:

```python
import asyncio
from copilot_mcp_client import (
    mcp_get_flash_loan_opportunities,
    mcp_analyze_protocol,
    mcp_get_prices,
    mcp_check_liquidity
)

# Example usage
async def main():
    # Get flash loan opportunities
    opportunities = await mcp_get_flash_loan_opportunities()
    print(f"Found {len(opportunities)} opportunities")
    
    # Analyze a DeFi protocol
    analysis = await mcp_analyze_protocol("aave")
    print(f"Aave analysis: {analysis}")
    
    # Get token prices
    prices = await mcp_get_prices(["ETH", "USDC", "DAI"])
    print(f"Current prices: {prices}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Available MCP Servers

Your system has the following MCP servers running:

| Server Name | Port | Description |
|-------------|------|-------------|
| flash_loan_blockchain | 8101 | Blockchain operations and flash loan functionality |
| defi_analyzer | 8102 | DeFi protocol analysis and insights |
| flash_loan | 8103 | Core flash loan operations |
| arbitrage | 8104 | Arbitrage opportunity detection and execution |
| liquidity | 8105 | Liquidity pool management and analysis |
| price_feed | 8106 | Real-time price data and feeds |
| risk_manager | 8107 | Risk assessment and management |
| portfolio | 8108 | Portfolio tracking and management |
| api_client | 8109 | External API integrations |
| database | 8110 | Database operations and queries |
| cache_manager | 8111 | Caching and performance optimization |
| file_processor | 8112 | File processing and management |
| notification | 8113 | Notification and alerting system |
| monitoring | 8114 | System monitoring and health checks |
| security | 8115 | Security and authentication |
| data_analyzer | 8116 | Data analysis and processing |
| web_scraper | 8117 | Web scraping and data collection |
| task_queue | 8118 | Task queuing and job management |
| filesystem | 8119 | File system operations |
| coordinator | 8120 | MCP server coordination and orchestration |

## Testing the Integration

### 1. Check MCP Bridge Status
```powershell
# Test WebSocket connection
python -c "import asyncio; import websockets; asyncio.run(websockets.connect('ws://localhost:8888').send('{\"action\":\"ping\"}'))"
```

### 2. Test MCP Server Health
```powershell
# Check individual server health
curl http://localhost:8101/health  # flash_loan_blockchain
curl http://localhost:8103/health  # flash_loan
curl http://localhost:8104/health  # arbitrage
```

### 3. Test GitHub Copilot Integration
1. Open VS Code
2. Open a Python file
3. Start typing flash loan related code
4. GitHub Copilot should now have access to your MCP server context

## Troubleshooting

### Issue: MCP Bridge Connection Failed
**Solution:** 
1. Check if Docker containers are running: `docker ps`
2. Restart containers: `docker-compose up -d`
3. Wait 30 seconds for health checks to pass

### Issue: GitHub Copilot Not Using MCP Context
**Solution:**
1. Restart VS Code
2. Ensure MCP bridge is running
3. Check `.vscode/settings.json` configuration
4. Try using the convenience functions in your code

### Issue: MCP Server Not Responding
**Solution:**
1. Check container logs: `docker logs [container-name]`
2. Restart specific container: `docker restart [container-name]`
3. Check port conflicts: `netstat -an | findstr 81xx`

## Advanced Configuration

### Custom MCP Bridge Port
```powershell
python mcp_bridge.py --port 9999
```

### Enable Debug Logging
```powershell
python mcp_bridge.py --verbose
```

### Custom Server Configuration
Edit `mcp_bridge.py` to add/remove MCP servers in the `mcp_servers` dictionary.

## Integration Benefits

With this setup, GitHub Copilot now has access to:
- Real-time flash loan opportunities
- DeFi protocol analysis
- Live token prices and liquidity data  
- Risk assessment capabilities
- Portfolio management tools
- Blockchain interaction methods

This enables GitHub Copilot to provide more intelligent suggestions for your flash loan arbitrage system development.
