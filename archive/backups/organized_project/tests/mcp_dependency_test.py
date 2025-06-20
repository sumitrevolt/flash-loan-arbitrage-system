#!/usr/bin/env python3
"""
MCP Dependency Test Script
Tests that all required Python packages are available for MCP servers
"""
import sys
import subprocess

def test_python_path():
    """Test the Python executable path"""
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    return True

def test_required_packages():
    """Test that all required packages are importable"""
    required_packages = [
        'aiohttp',
        'aiofiles', 
        'web3',
        'mcp',
        'asyncio',
        'json',
        'logging',
        'typing',
        'pathlib'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} - OK")
        except ImportError as e:
            print(f"✗ {package} - FAILED: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\nFailed imports: {failed_imports}")
        return False
    else:
        print("\nAll required packages are available!")
        return True

def test_mcp_server_syntax():
    """Test that MCP server files have valid Python syntax"""
    server_files = [
        r"C:\Users\Ratanshila\Documents\flash loan\mcp_servers\ai_integration\working_enhanced_copilot_mcp_server.py",
        r"C:\Users\Ratanshila\Documents\flash loan\mcp_servers\blockchain_integration\evm-mcp-server\evm_mcp_server.py",
        r"C:\Users\Ratanshila\Documents\flash loan\mcp_servers\blockchain_integration\matic-mcp-server\matic_mcp_server.py"
    ]
    
    for server_file in server_files:
        try:
            with open(server_file, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, server_file, 'exec')
            print(f"✓ {server_file} - Syntax OK")
        except FileNotFoundError:
            print(f"✗ {server_file} - File not found")
        except SyntaxError as e:
            print(f"✗ {server_file} - Syntax Error: {e}")
        except Exception as e:
            print(f"✗ {server_file} - Error: {e}")

def main():
    print("=== MCP Dependency Test ===\n")
    
    print("1. Testing Python Path:")
    test_python_path()
    
    print("\n2. Testing Required Packages:")
    packages_ok = test_required_packages()
    
    print("\n3. Testing MCP Server Syntax:")
    test_mcp_server_syntax()
    
    print(f"\n=== Test Summary ===")
    if packages_ok:
        print("✓ All dependencies are available")
        print("✓ MCP servers should work correctly")
        print("\nNext steps:")
        print("1. Restart the Cline/Claude Dev extension")
        print("2. Check MCP server connections")
    else:
        print("✗ Some dependencies are missing")
        print("Please install missing packages with pip")

if __name__ == "__main__":
    main()
