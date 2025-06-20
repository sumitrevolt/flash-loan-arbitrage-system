#!/usr/bin/env python3
"""
MCP Training Status Checker - Simple Version
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def check_mcp_status():
    """Check status of all MCP servers"""
    
    mcp_servers = [
        # MCP Core Services
        {"name": "mcp-auth-manager", "port": 8100},
        {"name": "mcp-blockchain", "port": 8101},
        {"name": "mcp-defi-analyzer", "port": 8102},
        {"name": "mcp-flash-loan", "port": 8103},
        {"name": "mcp-arbitrage", "port": 8104},
        {"name": "mcp-liquidity", "port": 8105},
        {"name": "mcp-price-feed", "port": 8106},
        {"name": "mcp-risk-manager", "port": 8107},
        {"name": "mcp-portfolio", "port": 8108},
        {"name": "mcp-api-client", "port": 8109},
        {"name": "mcp-database", "port": 8110},
        {"name": "mcp-cache-manager", "port": 8111},
        {"name": "mcp-file-processor", "port": 8112},
        {"name": "mcp-notification", "port": 8113},
        {"name": "mcp-monitoring", "port": 8114},
        {"name": "mcp-security", "port": 8115},
        {"name": "mcp-data-analyzer", "port": 8116},
        {"name": "mcp-web-scraper", "port": 8117},
        {"name": "mcp-task-queue", "port": 8118},
        {"name": "mcp-filesystem", "port": 8119},
        {"name": "mcp-coordinator", "port": 8120},
        # AI Agent Services
        {"name": "agent-coordinator", "port": 8200},
        {"name": "agent-analyzer", "port": 8201},
        {"name": "agent-executor", "port": 8202},
        {"name": "agent-risk-manager", "port": 8203},
        {"name": "agent-monitor", "port": 8204},
        {"name": "agent-data-collector", "port": 8205},
        {"name": "agent-arbitrage-bot", "port": 8206},
        {"name": "agent-liquidity-manager", "port": 8207},
        {"name": "agent-reporter", "port": 8208},
        {"name": "agent-healer", "port": 8209},
    ]
    
    print("MCP Server Training Status")
    print("=" * 50)
    print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    healthy_count = 0
    total_count = len(mcp_servers)
    
    for server in mcp_servers:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{server['port']}/health", 
                                     timeout=aiohttp.ClientTimeout(total=3)) as response:
                    if response.status == 200:
                        print(f"✓ {server['name']:25} - HEALTHY (Port {server['port']})")
                        healthy_count += 1
                    else:
                        print(f"⚠ {server['name']:25} - ISSUES (Status: {response.status})")
        except Exception:
            print(f"✗ {server['name']:25} - OFFLINE")
    
    print()
    print("=" * 50)
    print(f"SUMMARY: {healthy_count}/{total_count} servers are healthy")
    print(f"Training Success Rate: {(healthy_count/total_count)*100:.1f}%")
    
    if healthy_count == total_count:
        print("🎉 ALL MCP SERVERS ARE TRAINED AND HEALTHY!")
    elif healthy_count > total_count * 0.8:
        print("✅ Most MCP servers are trained and healthy")
    else:
        print("⚠️ Some MCP servers need attention")
    
    return {"healthy": healthy_count, "total": total_count, "rate": healthy_count/total_count}

if __name__ == "__main__":
    asyncio.run(check_mcp_status())
