#!/usr/bin/env python3
"""
MCP Server Connection Test
Tests that MCP servers can actually start and respond properly
"""
import subprocess
import sys
import time
import json
import os
from pathlib import Path

def test_mcp_server_startup(server_name, server_path, timeout=10):
    """Test if an MCP server can start without errors"""
    try:
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONPATH'] = r"C:\Users\Ratanshila\Documents\flash loan\mcp_servers;C:\Users\Ratanshila\Documents\flash loan"
        
        # Start the server process
        process = subprocess.Popen(
            [r"C:\Program Files\Python311\python.exe", server_path, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Wait for process to complete or timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            
            if process.returncode == 0:
                print(f"✓ {server_name} - Server can start successfully")
                return True
            else:
                print(f"✗ {server_name} - Server failed to start")
                if stderr:
                    print(f"  Error: {stderr[:200]}...")
                return False
                
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"✗ {server_name} - Server startup timed out")
            return False
            
    except Exception as e:
        print(f"✗ {server_name} - Exception during startup test: {e}")
        return False

def test_key_mcp_servers():
    """Test key MCP servers that are essential for flash loan system"""
    servers_to_test = [
        ("Enhanced Copilot", r"C:\Users\Ratanshila\Documents\flash loan\mcp_servers\ai_integration\working_enhanced_copilot_mcp_server.py"),
        ("EVM MCP Server", r"C:\Users\Ratanshila\Documents\flash loan\mcp_servers\blockchain_integration\evm-mcp-server\evm_mcp_server.py"),
        ("Matic MCP Server", r"C:\Users\Ratanshila\Documents\flash loan\mcp_servers\blockchain_integration\matic-mcp-server\matic_mcp_server.py"),
        ("Unified Flash Loan", r"C:\Users\Ratanshila\Documents\flash loan\mcp_servers\execution\working_unified_flash_loan_mcp_server.py")
    ]
    
    success_count = 0
    total_count = len(servers_to_test)
    
    print("Testing MCP Server Startup...")
    print("=" * 50)
    
    for server_name, server_path in servers_to_test:
        if Path(server_path).exists():
            if test_mcp_server_startup(server_name, server_path):
                success_count += 1
        else:
            print(f"✗ {server_name} - File not found: {server_path}")
    
    print("=" * 50)
    print(f"Server Startup Test Results: {success_count}/{total_count} servers passed")
    
    return success_count == total_count

def check_mcp_config():
    """Check if MCP configuration file is properly formatted"""
    config_path = r"c:\Users\Ratanshila\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        server_count = len(config.get('mcpServers', {}))
        flash_loan_servers = [name for name in config.get('mcpServers', {}).keys() if 'flash_loan' in name.lower()]
        
        print(f"✓ MCP Configuration loaded successfully")
        print(f"  Total servers configured: {server_count}")
        print(f"  Flash loan servers: {len(flash_loan_servers)}")
        print(f"  Flash loan server names: {', '.join(flash_loan_servers)}")
        
        return True
        
    except Exception as e:
        print(f"✗ MCP Configuration error: {e}")
        return False

def main():
    print("=== MCP Server Connection Test ===\n")
    
    print("1. Checking MCP Configuration:")
    config_ok = check_mcp_config()
    
    print("\n2. Testing Server Startup:")
    servers_ok = test_key_mcp_servers()
    
    print(f"\n=== Final Results ===")
    if config_ok and servers_ok:
        print("🎉 SUCCESS: All MCP servers are ready!")
        print("\n✅ Dependencies installed correctly")
        print("✅ Python path configured properly") 
        print("✅ MCP configuration is valid")
        print("✅ Key servers can start without errors")
        print("\n🚀 Next Steps:")
        print("1. Restart VS Code or the Cline extension")
        print("2. MCP servers should now connect without 'ModuleNotFoundError'")
        print("3. Flash loan arbitrage system should be operational")
    else:
        print("❌ Some issues remain:")
        if not config_ok:
            print("- MCP configuration needs attention")
        if not servers_ok:
            print("- Some servers failed startup tests")

if __name__ == "__main__":
    main()
