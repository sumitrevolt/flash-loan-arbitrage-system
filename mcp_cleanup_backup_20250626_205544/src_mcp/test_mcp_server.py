# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import os
import sys

    from mcp_servers.mcp_github_copilot_server import main
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Test script to start the enhanced GitHub Copilot MCP server
"""


# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Starting Enhanced GitHub Copilot MCP Server...")
    main()
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)