#!/usr/bin/env python3
"""
Health Check Fix for Unified MCP Coordinator
Replaces aiohttp-based health checks with socket-based checks
"""

import socket
import asyncio
import logging
from typing import Dict, Any

async def socket_health_check(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Simple socket-based health check that avoids aiodns issues
    """
    try:
        # Create socket connection with timeout
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result: str = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

async def test_all_mcp_servers():
    """Test all MCP server ports"""
    servers = {
        "Flash Loan MCP": 3001,
        "Enhanced Copilot MCP": 3002, 
        "Enhanced Foundry MCP": 3003,
        "Flash Loan Arbitrage MCP (TS)": 3004,
        "TaskManager MCP": 3005
    }
    
    print("🔍 SOCKET-BASED HEALTH CHECK TEST")
    print("=" * 50)
    
    for server_name, port in servers.items():
        is_healthy = await socket_health_check("localhost", port)
        status = "✅ HEALTHY" if is_healthy else "❌ UNREACHABLE"
        print(f"{server_name:<35} Port {port}: {status}")
    
    print("\n✨ Socket-based health checks work without aiodns!")

if __name__ == "__main__":
    asyncio.run(test_all_mcp_servers())
