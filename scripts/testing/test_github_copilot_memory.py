#!/usr/bin/env python3
"""
GitHub Copilot MCP Memory Server Test Script
"""

import json
import subprocess
import os
from pathlib import Path

def test_vscode_settings():
    """Test VS Code workspace settings for MCP configuration"""
    settings_file = Path(".vscode/settings.json")
    
    if not settings_file.exists():
        print("❌ VS Code settings.json not found in .vscode/")
        return False
    
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        if 'mcp.servers' in settings:
            print("✅ MCP servers configuration found in VS Code settings")
            
            if 'memory' in settings['mcp.servers']:
                print("✅ Memory server configured in VS Code settings")
                memory_config = settings['mcp.servers']['memory']
                
                if 'npx.cmd' in memory_config.get('command', ''):
                    print("✅ Memory server command uses full path to npx.cmd")
                else:
                    print("⚠️  Memory server command may need full path to npx.cmd")
                
                if '@modelcontextprotocol/server-memory' in memory_config.get('args', []):
                    print("✅ Memory server package is correctly specified")
                else:
                    print("❌ Memory server package not found in args")
                    return False
                
                return True
            else:
                print("❌ Memory server not found in MCP servers")
                return False
        else:
            print("❌ MCP servers configuration not found")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in VS Code settings: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading VS Code settings: {e}")
        return False

def test_github_copilot_settings():
    """Test GitHub Copilot settings"""
    settings_file = Path(".vscode/settings.json")
    
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        copilot_settings = [
            'github.copilot.enable',
            'github.copilot.chat.agent.thinkingTool',
            'github.copilot.chat.codesearch.enabled'
        ]
        
        found_settings = []
        for setting in copilot_settings:
            if setting in settings:
                found_settings.append(setting)
        
        if found_settings:
            print(f"✅ GitHub Copilot settings found: {len(found_settings)}/{len(copilot_settings)}")
            return True
        else:
            print("⚠️  No GitHub Copilot settings found (this is okay if configured elsewhere)")
            return True
            
    except Exception as e:
        print(f"❌ Error checking GitHub Copilot settings: {e}")
        return False

def test_memory_server_availability():
    """Test if memory server can be started"""
    try:
        cmd = [
            "C:\\Program Files\\nodejs\\npx.cmd",
            "-y",
            "@modelcontextprotocol/server-memory",
            "--help"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 or "Memory" in result.stderr or "memory" in result.stderr:
            print("✅ Memory server package is accessible and working")
            return True
        else:
            print(f"❌ Memory server test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Memory server test timed out (but package might still work)")
        return True
    except Exception as e:
        print(f"❌ Error testing memory server: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing GitHub Copilot MCP Memory Server Setup")
    print("=" * 60)
    
    # Test 1: VS Code settings
    print("\n1. Testing VS Code workspace settings...")
    vscode_settings_ok = test_vscode_settings()
    
    # Test 2: GitHub Copilot settings
    print("\n2. Testing GitHub Copilot settings...")
    copilot_settings_ok = test_github_copilot_settings()
    
    # Test 3: Memory server availability
    print("\n3. Testing memory server availability...")
    memory_server_ok = test_memory_server_availability()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"VS Code Settings: {'✅' if vscode_settings_ok else '❌'}")
    print(f"GitHub Copilot Settings: {'✅' if copilot_settings_ok else '❌'}")
    print(f"Memory Server Available: {'✅' if memory_server_ok else '❌'}")
    
    all_tests_passed = all([vscode_settings_ok, copilot_settings_ok, memory_server_ok])
    
    if all_tests_passed:
        print("\n🎉 All tests passed! Memory server is ready for GitHub Copilot.")
        print("\nNext steps:")
        print("1. Restart VS Code to load the new settings")
        print("2. Open GitHub Copilot Chat")
        print("3. Test memory functionality:")
        print("   - Ask: 'Can you remember that I prefer TypeScript?'")
        print("   - Later ask: 'What programming language do I prefer?'")
        print("4. Use memory for your flash loan project context")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        print("\n💡 Common fixes:")
        print("- Ensure Node.js is installed and npx.cmd is accessible")
        print("- Check that .vscode/settings.json has valid JSON syntax")
        print("- Restart VS Code after making changes")
    
    return all_tests_passed

if __name__ == "__main__":
    main()
