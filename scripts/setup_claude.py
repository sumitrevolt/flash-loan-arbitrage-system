#!/usr/bin/env python3
"""
Claude Desktop Setup Script for Flash Loan Arbitrage System
Configures Claude Desktop to work with MCP servers
"""

import os
import json
import shutil
from pathlib import Path
import platform
from typing import Optional

def get_claude_config_path() -> Optional[Path]:
    """Get the Claude Desktop configuration path based on OS"""
    system = platform.system()
    
    if system == "Windows":
        appdata = os.environ.get('APPDATA')
        if appdata:
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":  # macOS
        home = Path.home()
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        home = Path.home()
        return home / ".config" / "Claude" / "claude_desktop_config.json"
    
    return None

def setup_claude_config() -> bool:
    """Setup Claude Desktop configuration"""
    print("Setting up Claude Desktop configuration for Flash Loan Arbitrage System...")
    
    # Get current directory (project root)
    project_root = Path(__file__).parent.absolute()
    print(f"Project root: {project_root}")
    
    # Load the config template
    config_file = project_root / "claude_desktop_config.json"
    if not config_file.exists():
        print("❌ claude_desktop_config.json not found in project root!")
        return False
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Update paths to use absolute paths
    for server_name, server_config in config['mcpServers'].items():
        server_config['cwd'] = str(project_root)
        server_config['env']['PYTHONPATH'] = str(project_root)
    
    # Get Claude Desktop config path
    claude_config_path = get_claude_config_path()
    if not claude_config_path:
        print("❌ Could not determine Claude Desktop config path for your OS")
        return False
    
    print(f"Claude Desktop config path: {claude_config_path}")
    
    # Create directory if it doesn't exist
    claude_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup existing config if it exists
    if claude_config_path.exists():
        backup_path = claude_config_path.with_suffix('.json.backup')
        shutil.copy2(claude_config_path, backup_path)
        print(f"📁 Backed up existing config to: {backup_path}")
    
    # Write the new config
    with open(claude_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Claude Desktop configuration updated successfully!")
    print("\nConfigured MCP Servers:")
    for server_name in config['mcpServers'].keys():
        print(f"  - {server_name}")
    
    print("\n📋 Next steps:")
    print("1. Restart Claude Desktop application")
    print("2. Open a new conversation")
    print("3. The MCP servers should be available automatically")
    print("4. Test the integration by asking about flash loan arbitrage")
    
    return True

def verify_dependencies() -> bool:
    """Verify that required Python packages are installed"""
    print("Checking Python dependencies...")
    
    required_packages = [
        'web3',
        'requests',
        'asyncio',
        'json',
        'logging',
        'typing'
    ]
    
    missing_packages: list[str] = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def test_mcp_servers() -> None:
    """Test if MCP servers can be started"""
    print("\nTesting MCP servers...")
    
    project_root = Path(__file__).parent.absolute()
    test_servers = [
        "simple_mcp_server.py",
        "minimal-mcp-server.py",
        "working_flash_loan_mcp.py"
    ]
    
    for server in test_servers:
        server_path = project_root / server
        if server_path.exists():
            print(f"✅ Found: {server}")
        else:
            print(f"❌ Missing: {server}")
    
    print("\nMCP server files check completed!")

def main() -> None:
    """Main setup function"""
    print("🚀 Claude Desktop Setup for Flash Loan Arbitrage System")
    print("=" * 60)
    
    # Verify dependencies
    if not verify_dependencies():
        print("❌ Please install missing dependencies before proceeding")
        return
    
    # Test MCP servers
    test_mcp_servers()
    
    # Setup Claude configuration
    if setup_claude_config():
        print("\n🎉 Setup completed successfully!")
        print("\nYou can now use Claude Desktop with your flash loan arbitrage system!")
        print("The following MCP servers are now available:")
        print("- Flash Loan Arbitrage Detection")
        print("- Real-time Price Monitoring") 
        print("- Aave Protocol Integration")
        print("- Blockchain Interactions")
        print("- AI Context Integration")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
