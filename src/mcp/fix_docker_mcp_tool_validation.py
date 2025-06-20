#!/usr/bin/env python3
"""
Fix for Docker MCP Server Tool Validation Error

This script addresses the error:
"Failed to validate tool mcp_docker_create_container: Error: tool parameters array type must have items"

The issue is with the mcp-server-docker package's tool schema definitions.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def check_current_docker_mcp_config() -> Dict[str, Any]:
    """Check current Docker MCP configuration in VSCode settings"""
    settings_path = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        docker_config = settings.get('mcp', {}).get('servers', {}).get('docker', {})
        print(f"✅ Current Docker MCP Config: {docker_config}")
        return docker_config
    except Exception as e:
        print(f"❌ Error reading VSCode settings: {e}")
        return {}

def try_alternative_docker_mcp_server() -> bool:
    """Try using an alternative Docker MCP server implementation"""
    settings_path = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        # Alternative 1: Use NPX version which might be more stable
        alternative_config = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-docker"],
            "env": {}
        }
        
        # Update the Docker MCP server configuration
        if 'mcp' not in settings:
            settings['mcp'] = {}
        if 'servers' not in settings['mcp']:
            settings['mcp']['servers'] = {}
        
        settings['mcp']['servers']['docker'] = alternative_config
        
        # Write back to settings
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
        
        print("✅ Updated Docker MCP server to use NPX version")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Docker MCP configuration: {e}")
        return False

def disable_docker_mcp_server() -> bool:
    """Temporarily disable the Docker MCP server to avoid validation errors"""
    settings_path = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        # Remove or comment out the Docker MCP server
        if 'mcp' in settings and 'servers' in settings['mcp']:
            if 'docker' in settings['mcp']['servers']:
                # Backup the configuration
                docker_backup = settings['mcp']['servers']['docker'].copy()
                
                # Remove the docker server temporarily
                del settings['mcp']['servers']['docker']
                
                # Add a backup entry for later restoration
                settings['mcp']['servers']['docker_disabled'] = docker_backup
                
                # Write back to settings
                with open(settings_path, 'w') as f:
                    json.dump(settings, f, indent=4)
                
                print("✅ Temporarily disabled Docker MCP server")
                print("✅ Configuration backed up as 'docker_disabled'")
                return True
        
        print("⚠️  Docker MCP server not found in configuration")
        return False
        
    except Exception as e:
        print(f"❌ Error disabling Docker MCP server: {e}")
        return False

def test_docker_functionality() -> bool:
    """Test basic Docker functionality without MCP"""
    try:
        result = subprocess.run(['docker', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker is working correctly")
            return True
        else:
            print("❌ Docker is not working")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def create_github_issue_template() -> str:
    """Create a template for reporting the issue to the MCP server repository"""
    issue_template = """
# Docker MCP Server Tool Validation Error

## Description
The `mcp-server-docker` package is failing tool validation with the error:
```
Failed to validate tool mcp_docker_create_container: Error: tool parameters array type must have items
```

## Error Details
- **Tool**: `mcp_docker_create_container`
- **Issue**: Tool parameters array type must have items
- **Root Cause**: JSON Schema validation failure - array type parameters need `items` property

## Expected Behavior
The tool should validate successfully and be available for use.

## Environment
- **OS**: Windows 11
- **MCP Server**: mcp-server-docker (via uvx)
- **VSCode**: Latest
- **Docker**: Docker Desktop

## Reproduction Steps
1. Configure mcp-server-docker in VSCode MCP settings
2. Start VSCode with MCP enabled
3. Observe validation error in MCP logs

## Suggested Fix
The tool schema definition should include proper `items` specification for array type parameters:

```json
{
  "type": "array", 
  "items": {
    "type": "string"  // or appropriate item type
  }
}
```

## Workaround
Currently using alternative Docker integration or temporarily disabling the MCP server.
"""
    
    return issue_template.strip()

def main():
    """Main fix routine"""
    print("Docker MCP Server Tool Validation Fix")
    print("=" * 50)
    
    # Step 1: Check current configuration
    print("\n1. Checking current Docker MCP configuration...")
    current_config = check_current_docker_mcp_config()
    
    # Step 2: Test Docker functionality
    print("\n2. Testing Docker functionality...")
    docker_works = test_docker_functionality()
    
    if not docker_works:
        print("❌ Docker is not working. Please fix Docker installation first.")
        return 1
    
    # Step 3: Provide fix options
    print("\n3. Fix Options:")
    print("   A. Try alternative NPX-based Docker MCP server")
    print("   B. Temporarily disable Docker MCP server")
    print("   C. Create GitHub issue template")
    print("   D. Exit without changes")
    
    choice = input("\nSelect option (A/B/C/D): ").upper().strip()
    
    if choice == 'A':
        print("\n🔧 Trying alternative Docker MCP server...")
        if try_alternative_docker_mcp_server():
            print("✅ Alternative configuration applied")
            print("🔄 Please restart VSCode to test the changes")
        else:
            print("❌ Failed to apply alternative configuration")
            return 1
    
    elif choice == 'B':
        print("\n🔧 Disabling Docker MCP server...")
        if disable_docker_mcp_server():
            print("✅ Docker MCP server disabled")
            print("🔄 Please restart VSCode")
            print("💡 You can re-enable later by renaming 'docker_disabled' to 'docker' in settings")
        else:
            print("❌ Failed to disable Docker MCP server")
            return 1
    
    elif choice == 'C':
        print("\n📝 GitHub Issue Template:")
        print("-" * 50)
        print(create_github_issue_template())
        print("-" * 50)
        print("\n💡 Copy the above template and create an issue at:")
        print("   https://github.com/modelcontextprotocol/servers/issues")
    
    elif choice == 'D':
        print("\n⏸️  Exiting without changes")
        return 0
    
    else:
        print("❌ Invalid option selected")
        return 1
    
    # Step 4: Final recommendations
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS:")
    print("=" * 50)
    print("1. 🔄 Restart VSCode to apply configuration changes")
    print("2. 🧪 Test MCP functionality after restart")
    print("3. 📝 Report the issue to the MCP server repository")
    print("4. 🔄 Check for updates to mcp-server-docker package")
    print("5. 💡 Consider alternative Docker integrations if needed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
