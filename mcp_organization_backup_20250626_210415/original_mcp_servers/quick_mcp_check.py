# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List
import os


# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Quick MCP Server Requirements Checker
"""

# import json # Unused import

def check_mcp_servers():
    workspace = Path(".")
    print("[SEARCH] MCP Server Requirements Check")
    print("=" * 50)
    
    # Find Python MCP servers
    python_servers: List[Path] = []
    for py_file in workspace.rglob("*mcp*server*.py"):
        if "archive" not in str(py_file) and "backup" not in str(py_file):
            python_servers.append(py_file)
      # Find TypeScript MCP servers  
    ts_servers: List[Path] = []
    for ts_file in workspace.rglob("**/index.ts"):
        if "mcp" in str(ts_file.parent):
            ts_servers.append(ts_file)
    
    print(f"📄 Found {len(python_servers)} Python MCP servers:")
    for server in python_servers:
        print(f"   • {server.relative_to(workspace)}")
    
    print(f"\n📄 Found {len(ts_servers)} TypeScript MCP servers:")
    for server in ts_servers:
        print(f"   • {server.relative_to(workspace)}")
    
    # Check config files
    print("\n[SETUP] Configuration Files:")
    config_files = ["unified_mcp_config.json", "production_config.json", "unified_config.json", "deployment_config.json"]
    found_configs: List[str] = []
    for config in config_files:
        if (workspace / config).exists():
            found_configs.append(config)
            print(f"   ✓ {config}")
        else:
            print(f"   [ERROR] {config} (missing)")
    
    # Check environment variables
    print("\n🌍 Environment Variables:")
    env_vars = ["POLYGON_RPC_URL", "PRIVATE_KEY", "ETHERSCAN_API_KEY"]
    for var in env_vars:
        if os.getenv(var):
            print(f"   ✓ {var}")
        else:
            print(f"   [ERROR] {var} (not set)")
    
    # Check directories
    print("\n📁 Directory Structure:")
    dirs = ["mcp", "core", "config", "logs", "scripts"]
    for dir_name in dirs:
        if (workspace / dir_name).exists():
            print(f"   ✓ {dir_name}/")
        else:
            print(f"   [ERROR] {dir_name}/ (missing)")
    
    print("\n" + "=" * 50)
    print(f"[METRICS] Summary: {len(python_servers) + len(ts_servers)} MCP servers, {len(found_configs)} config files")

if __name__ == "__main__":
    check_mcp_servers()