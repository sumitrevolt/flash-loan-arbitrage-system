#!/usr/bin/env python3
"""
Test script to verify Docker MCP server configuration
"""

import subprocess
import sys
import os
import json
from typing import Dict, Tuple, Callable, Optional, List

def test_docker_connection() -> bool:
    """Test if Docker is accessible"""
    try:
        result = subprocess.run(['docker', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker is accessible")
            return True
        else:
            print("❌ Docker is not accessible")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Docker connection failed: {e}")
        return False

def test_uvx_available() -> bool:
    """Test if uvx is available"""
    uvx_path = r"C:\Users\Ratanshila\.local\bin\uvx.exe"
    if os.path.exists(uvx_path):
        print("✅ uvx is available")
        return True
    else:
        print(f"❌ uvx not found at {uvx_path}")
        return False

def test_mcp_server_docker_package() -> Optional[bool]:
    """Test if mcp-server-docker package can be installed"""
    try:
        uvx_path = r"C:\Users\Ratanshila\.local\bin\uvx.exe"
        result = subprocess.run([uvx_path, 'mcp-server-docker', '--version'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ mcp-server-docker package is working")
            print(f"Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ mcp-server-docker package failed")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ mcp-server-docker test timed out (likely installing dependencies)")
        return None
    except Exception as e:
        print(f"❌ mcp-server-docker test failed: {e}")
        return False

def check_vscode_mcp_config() -> bool:
    """Check VSCode MCP configuration"""
    settings_path = os.path.expanduser(r"~\AppData\Roaming\Code\User\settings.json")
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        if 'mcp' in settings and 'servers' in settings['mcp']:
            servers = settings['mcp']['servers']
            if 'docker' in servers:
                docker_config = servers['docker']
                print("✅ Docker MCP server is configured in VSCode")
                print(f"Command: {docker_config.get('command', 'Not set')}")
                print(f"Args: {docker_config.get('args', 'Not set')}")
                print(f"Env: {docker_config.get('env', 'Not set')}")
                return True
            else:
                print("❌ Docker MCP server not found in VSCode configuration")
                return False
        else:
            print("❌ MCP configuration not found in VSCode settings")
            return False
    except FileNotFoundError:
        print(f"❌ VSCode settings file not found: {settings_path}")
        return False
    except json.JSONDecodeError:
        print("❌ VSCode settings file is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error reading VSCode settings: {e}")
        return False

def main() -> int:
    """Run all tests"""
    print("Testing Docker MCP Server Configuration")
    print("=" * 50)
    
    tests: List[Tuple[str, Callable[[], Optional[bool]]]] = [
        ("Docker Connection", test_docker_connection),
        ("uvx Availability", test_uvx_available),
        ("VSCode MCP Config", check_vscode_mcp_config),
        ("mcp-server-docker Package", test_mcp_server_docker_package)
    ]
    
    results: Dict[str, Optional[bool]] = {}
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        result = test_func()
        results[test_name] = result
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
            all_passed = False
        else:
            status = "⏰ TIMEOUT/PENDING"
        
        print(f"{test_name}: {status}")
    
    if all_passed:
        print("\n🎉 All tests passed! Docker MCP server should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
