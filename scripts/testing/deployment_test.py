"""
Quick Deployment Test Script
Tests all major components of the Multi-MCP Server Container System
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def test_component(name, test_func):
    """Test a component and report results."""
    print(f"\n🧪 Testing {name}...")
    try:
        result = test_func()
        if result:
            print(f"✅ {name}: PASSED")
            return True
        else:
            print(f"❌ {name}: FAILED")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False

def test_python_dependencies():
    """Test if required Python dependencies are available."""
    required_packages = [
        'networkx', 'aiohttp', 'sqlite3', 'json', 'asyncio',
        'requests', 'pathlib', 'datetime', 'hashlib', 'uuid'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Missing package: {package}")
            return False
    return True

def test_mcp_framework():
    """Test if MCP framework is available."""
    try:
        import mcp
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import ServerCapabilities
        return True
    except ImportError as e:
        print(f"MCP framework issue: {e}")
        return False

def test_github_copilot_server():
    """Test if the enhanced GitHub Copilot MCP server can be imported."""
    try:
        sys.path.insert(0, '.')
        from mcp_servers.mcp_github_copilot_server import GitHubCopilotMCPServer
        server = GitHubCopilotMCPServer()
        return True
    except Exception as e:
        print(f"Server import issue: {e}")
        return False

def test_docker():
    """Test if Docker is available."""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

def test_docker_compose():
    """Test if Docker Compose is available."""
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

def test_configuration_files():
    """Test if required configuration files exist."""
    required_files = [
        'docker-compose.github-enhanced.yml',
        'config/working_cline_mcp_config.json',
        'mcp_servers/mcp_github_copilot_server.py',
        'requirements-github-copilot-enhanced.txt'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"Missing file: {file_path}")
            return False
    return True

def test_workflow_files():
    """Test if GitHub workflow files exist."""
    workflow_files = [
        '.github/workflows/flash-loan-mcp.yml',
        '.github/workflows/price-feed-mcp.yml',
        '.github/workflows/risk-manager-mcp.yml'
    ]
    
    for file_path in workflow_files:
        if not Path(file_path).exists():
            print(f"Missing workflow: {file_path}")
            return False
    return True

def test_mcp_config():
    """Test if MCP configuration is valid JSON."""
    try:
        with open('config/working_cline_mcp_config.json', 'r') as f:
            config = json.load(f)
        
        # Check if GitHub Copilot enhanced server is configured
        servers = config.get('mcpServers', {})
        return 'github-copilot-enhanced' in servers
    except Exception as e:
        print(f"Config issue: {e}")
        return False

def main():
    """Run all deployment tests."""
    print("🚀 Multi-MCP Server Container System - Deployment Test")
    print("=" * 60)
    
    tests = [
        ("Python Dependencies", test_python_dependencies),
        ("MCP Framework", test_mcp_framework),
        ("GitHub Copilot Server", test_github_copilot_server),
        ("Docker", test_docker),
        ("Docker Compose", test_docker_compose),
        ("Configuration Files", test_configuration_files),
        ("Workflow Files", test_workflow_files),
        ("MCP Configuration", test_mcp_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_component(test_name, test_func):
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT! 🎉")
        print("\n🚀 Next Steps:")
        print("1. Set GitHub tokens in environment variables")
        print("2. Run: docker-compose -f docker-compose.github-enhanced.yml up -d")
        print("3. Test: python mcp_servers\\mcp_github_copilot_server.py")
        return True
    else:
        print(f"❌ {total - passed} TESTS FAILED - Please fix issues before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
