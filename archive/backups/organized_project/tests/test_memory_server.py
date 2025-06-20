#!/usr/bin/env python3
"""
Test script for MCP Memory Server integration
"""

import json
import subprocess
import time
import os
from pathlib import Path

def test_memory_server_config():
    """Test if the memory server configuration is valid"""
    config_file = Path("config/claude_mcp_config.json")
    
    if not config_file.exists():
        print("❌ Claude MCP config file not found")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if 'memory' in config.get('mcpServers', {}):
            print("✅ Memory server found in configuration")
            memory_config = config['mcpServers']['memory']
            
            # Validate configuration structure
            if memory_config.get('command') == 'npx':
                print("✅ Memory server command is correct")
            else:
                print("❌ Memory server command is incorrect")
                return False
                
            if '-y' in memory_config.get('args', []):
                print("✅ Memory server args include -y flag")
            else:
                print("❌ Memory server args missing -y flag")
                return False
                
            if '@modelcontextprotocol/server-memory' in memory_config.get('args', []):
                print("✅ Memory server package is correct")
            else:
                print("❌ Memory server package is incorrect")
                return False
                
            return True
        else:
            print("❌ Memory server not found in configuration")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False

def test_node_availability():
    """Test if Node.js and npx are available"""
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Node.js available: {result.stdout.strip()}")
        else:
            print("❌ Node.js not available")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Node.js not found in PATH")
        return False
    
    try:
        result = subprocess.run(['npx', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ npx available: {result.stdout.strip()}")
            return True
        else:
            print("❌ npx not available")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ npx not found in PATH")
        return False

def test_memory_package_availability():
    """Test if the MCP memory server package can be accessed"""
    print("🔍 Testing MCP memory server package availability...")
    try:
        # Try to get package info without installing
        result = subprocess.run([
            'npx', '--yes', '@modelcontextprotocol/server-memory', '--help'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ MCP memory server package is accessible")
            return True
        else:
            print(f"❌ MCP memory server package test failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ MCP memory server package test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing MCP memory server package: {e}")
        return False

def create_test_config():
    """Create a test configuration file"""
    test_config = {
        "mcpServers": {
            "memory": {
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-memory"
                ]
            }
        }
    }
    
    test_config_file = Path("config/test_memory_mcp_config.json")
    try:
        with open(test_config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        print(f"✅ Test configuration created: {test_config_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating test configuration: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing MCP Memory Server Integration")
    print("=" * 50)
    
    # Test 1: Configuration validation
    print("\n1. Testing configuration...")
    config_valid = test_memory_server_config()
    
    # Test 2: Node.js/npx availability
    print("\n2. Testing Node.js/npx availability...")
    node_available = test_node_availability()
    
    # Test 3: Package availability
    print("\n3. Testing package availability...")
    package_available = test_memory_package_availability()
    
    # Test 4: Create test config
    print("\n4. Creating test configuration...")
    test_config_created = create_test_config()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"Configuration Valid: {'✅' if config_valid else '❌'}")
    print(f"Node.js/npx Available: {'✅' if node_available else '❌'}")
    print(f"Package Accessible: {'✅' if package_available else '❌'}")
    print(f"Test Config Created: {'✅' if test_config_created else '❌'}")
    
    all_tests_passed = all([config_valid, node_available, package_available, test_config_created])
    
    if all_tests_passed:
        print("\n🎉 All tests passed! Memory server is ready to use.")
        print("\nNext steps:")
        print("1. Restart Claude Desktop")
        print("2. Test memory functionality in Claude")
        print("3. Ask Claude to remember something and then recall it")
    else:
        print("\n⚠️  Some tests failed. Please address the issues above.")
        
        if not node_available:
            print("\n💡 To install Node.js:")
            print("   - Download from: https://nodejs.org/")
            print("   - Or use a package manager like Chocolatey: choco install nodejs")
    
    return all_tests_passed

if __name__ == "__main__":
    main()
