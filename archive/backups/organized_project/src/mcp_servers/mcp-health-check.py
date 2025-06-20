#!/usr/bin/env python3
"""
Health check script for MCP servers
"""
import sys
import asyncio
import aiohttp
import os
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_mcp_server_health(port: int, timeout: int = 10) -> bool:
    """
    Check if MCP server is healthy by attempting to connect to its port
    """
    try:
        # Try to connect to the server port
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection('localhost', port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (ConnectionRefusedError, asyncio.TimeoutError, OSError) as e:
        logger.warning(f"Health check failed for port {port}: {e}")
        return False

async def main():
    """Main health check function"""
    # Get port from environment variable
    port = int(os.getenv('MCP_PORT', '8000'))
    
    # Perform health check
    is_healthy = await check_mcp_server_health(port)
    
    if is_healthy:
        logger.info(f"MCP server on port {port} is healthy")
        sys.exit(0)
    else:
        logger.error(f"MCP server on port {port} is not healthy")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
