"""
Main entry point for Foundry MCP Server

Run with: python -m foundry_mcp_server
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from server.mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())