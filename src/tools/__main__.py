# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
import asyncio
import sys

from server.mcp_server import main
"""
Main entry point for Foundry MCP Server

Run with: python -m foundry_mcp_server
"""


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))


if __name__ == "__main__":
    asyncio.run(main())