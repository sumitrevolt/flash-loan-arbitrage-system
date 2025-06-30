# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from typing import Optional
import asyncio
import logging
import os
import sys

import aiohttp
"""
Health check script for MCP servers
"""

# Set up logging

# Unicode-safe logging setup
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_mcp_server_health(port: int, timeout: int = 10) -> bool:
    """
    Check if MCP server is healthy by attempting to connect to its port
    """
    try:
        # Try to connect to the server port
        reader, writer = await asyncio.wait_for()
            asyncio.open_connection('localhost', port),
            timeout=timeout
        
        writer.close()
        await writer.wait_closed()
        return True
    except (ConnectionRefusedError, asyncio.TimeoutError, OSError) as e:
        logger.warning(str(f"Health check failed for port {port}: {e}")
        return False

async def main():
    """Main health check function"""
    # Get port from environment variable
    port = int(os.getenv('MCP_PORT', '8000'))
    
    # Perform health check
    is_healthy = await check_mcp_server_health(port)
    
    if is_healthy:
        logger.info(str(f"MCP server on port {port} is healthy")
        sys.exit(0)
    else:
        logger.error(str(f"MCP server on port {port} is not healthy")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())