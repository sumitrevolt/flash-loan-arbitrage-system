#!/usr/bin/env python3
"""
MCP Server Status Verification
Checks status of all MCP servers for Cline integration
"""

import requests
import json
from pathlib import Path

def test_mcp_server(name, port):
    """Test MCP server health and capabilities"""
    try:
        # Test health endpoint
        health_response = requests.get(f"http://localhost:{port}/health", timeout=3)
        health_ok = health_response.status_code == 200
        health_data = health_response.json() if health_ok else {}
        
        # Test capabilities endpoint
        cap_response = requests.get(f"http://localhost:{port}/mcp/capabilities", timeout=3)
        cap_ok = cap_response.status_code == 200
        cap_data = cap_response.json() if cap_ok else {}
        
        return {
            'name': name,
            'port': port,
            'health_ok': health_ok,
            'capabilities_ok': cap_ok,
            'health_data': health_data,
            'capabilities': cap_data.get('capabilities', {}),
            'status': 'online' if health_ok and cap_ok else 'offline'
        }
    except Exception as e:
        return {
            'name': name,
            'port': port,
            'health_ok': False,
            'capabilities_ok': False,
            'error': str(e),
            'status': 'offline'
        }

def main():
    print("🔍 MCP Server Status Verification for Cline")
    print("=" * 50)
    
    # Define MCP servers that should be running
    servers = [
        ("context7_clean", 4100),
        ("flash_loan_blockchain", 4101),
        ("matic_mcp_server", 4102)
    ]
    
    results = []
    online_count = 0
    
    for name, port in servers:
        result: str = test_mcp_server(name, port)
        results.append(result)
        if result['status'] == 'online':
            online_count += 1
    
    # Print results
    print(f"\n📊 MCP Server Status:")
    print("-" * 50)
    
    for result in results:
        status_icon = "🟢" if result['status'] == 'online' else "🔴"
        print(f"{status_icon} {result['name']:<25} Port: {result['port']:<6} Status: {result['status'].upper()}")
        
        if result['status'] == 'online':
            caps = result['capabilities']
            if 'tools' in caps:
                tools = ', '.join(caps['tools'][:3])  # First 3 tools
                if len(caps['tools']) > 3:
                    tools += f" (+{len(caps['tools'])-3} more)"
                print(f"   └─ Tools: {tools}")
    
    print(f"\n📈 Summary:")
    print(f"   Online: {online_count}/{len(servers)} servers")
    print(f"   Status: {'✅ READY' if online_count == len(servers) else '⚠️ PARTIAL' if online_count > 0 else '❌ OFFLINE'}")
    
    # Check VS Code configuration
    settings_file = Path(".vscode/settings.json")
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            if 'mcpServers' in settings:
                configured_servers = list(settings['mcpServers'].keys())
                print(f"\n⚙️  VS Code Configuration:")
                print(f"   Configured MCP servers: {', '.join(configured_servers)}")
                print(f"   Configuration file: {settings_file.absolute()}")
            else:
                print(f"\n⚠️  VS Code configuration missing mcpServers section")
        except Exception as e:
            print(f"\n❌ Error reading VS Code configuration: {e}")
    else:
        print(f"\n❌ VS Code settings file not found: {settings_file.absolute()}")
    
    print(f"\n🎯 Next Steps for Cline:")
    if online_count == len(servers):
        print(f"   1. ✅ All MCP servers are running")
        print(f"   2. 🔄 Restart VS Code/Cline to reload MCP configuration")
        print(f"   3. 🔍 Check Cline UI - servers should show as 'online'")
        print(f"   4. ✨ Test MCP functionality in Cline")
    else:
        print(f"   1. ❌ Some MCP servers are offline")
        print(f"   2. 🔧 Run: python simple_mcp_orchestrator.py")
        print(f"   3. 🔄 Then restart VS Code/Cline")
    
    return 0 if online_count == len(servers) else 1

if __name__ == "__main__":
    exit(main())
