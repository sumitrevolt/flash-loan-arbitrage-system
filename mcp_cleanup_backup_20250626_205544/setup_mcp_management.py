#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Setup Script for MCP Management System
Initializes all components: MCP servers, Cursor integration, SAMR, and AI agents
"""

from pathlib import Path
import asyncio
import subprocess
import sys

def print_banner():
    print("""
🚀 MCP Management System Setup
===============================================
Unified Management for:
• Local MCP Servers (100+ servers)
• Cursor MCP Integration  
• SAMR Agent Routing System
• AI Agents Organization
===============================================
    """

def check_requirements():
    """Check if required packages are available"""
    print("🔍 Checking requirements...")
    
    required_packages = ['yaml', 'psutil']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages
            print("   ✅ Packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install packages: {e}")
            return False
    
    return True

async def run_setup_component(script_path, description):
    """Run a setup component"""
    print(f"🔧 {description}...")
    
    try:
        if script_path.exists():
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True
            
            if result.returncode == 0:
                print(f"   ✅ {description} completed")
                return True
            else:
                print(f"   ❌ {description} failed: {result.stderr}")
                return False
        else:
            print(f"   ⚠️  {script_path} not found, skipping")
            return True
            
    except Exception as e:
        print(f"   ❌ {description} error: {e}")
        return False

async def main():
    """Main setup function"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements check failed. Please install missing packages manually.")
        return
    
    base_dir = Path.cwd()
    mcp_management_dir = base_dir / "mcp_management"
    
    # Ensure mcp_management directory exists
    mcp_management_dir.mkdir(exist_ok=True)
    
    print("🏗️  Initializing MCP Management System...")
    
    # Setup components in order
    setup_tasks = [
        (mcp_management_dir / "simple_controller.py", "Setting up MCP Controller"),
        (mcp_management_dir / "organize_ai_agents.py", "Organizing AI Agents"),

    
    success_count = 0
    
    for script_path, description in setup_tasks:
        success = await run_setup_component(script_path, description)
        if success:
            success_count += 1
    
    # Check current system state
    print("\n📊 System Status Check:")
    
    # Check directories
    directories_to_check = [
        ("mcp_management/config", "Configuration directory"),
        ("mcp_management/scripts", "Scripts directory"),
        ("mcp_management/logs", "Logs directory"),
        ("ai_agents_unified", "Unified agents directory"),
        (".kilocode", "Cursor configuration")

    
    for dir_path, description in directories_to_check:
        if (base_dir / dir_path).exists():
            print(f"   ✅ {description}")
        else:
            print(f"   ⚠️  {description} (will be created)")
    
    # Check key files
    key_files = [
        ("mcp_management/config/master_config.yaml", "Master configuration"),
        (".kilocode/mcp.json", "Cursor MCP configuration"),
        ("mcp_servers", "MCP servers directory")

    
    for file_path, description in key_files:
        if (base_dir / file_path).exists():
            print(f"   ✅ {description}")
        else:
            print(f"   ⚠️  {description} (not found)")
    
    print("\n📈 Setup Summary:")
    print(f"   Completed: {success_count}/{len(setup_tasks)} components")
    
    if success_count == len(setup_tasks):
        print("\n🎉 MCP Management System setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Review configuration:")
        print("   cat mcp_management/config/master_config.yaml")
        print("\n2. Start the system:")
        print("   python mcp_management/scripts/start_all.py")
        print("\n3. Check system status:")
        print("   python mcp_management/status_check.py")
        print("\n4. Test SAMR routing:")
        print("   python mcp_management/samr_router.py")
        print("\n📚 Documentation:")
        print("   cat mcp_management/README.md")
        
    else:
        print("\n⚠️  Setup completed with some issues.")
        print("Please check the error messages above and run individual components manually.")
    
    print("\n" + "="*50)
    print("🔗 Key System Components:")
    print("• MCP Servers: Port range 3000-3099")
    print("• SAMR System: Port 4000 (routing), 4001 (management)")  
    print("• AI Agents: Port range 5000-5099")
    print("• Cursor Integration: Automatic sync with .kilocode/mcp.json")
    print("="*50)

def create_quick_start_script():
    """Create a quick start script for future use"""
    quick_start_content = """#!/usr/bin/env python3
'''
Quick Start Script for MCP Management System
'''

import subprocess
import sys
from pathlib import Path

def quick_start():
    base_dir = Path.cwd()
    
    print("🚀 Quick Starting MCP Management System...")
    
    # Start core components
    scripts = [
        "mcp_management/scripts/start_all.py",
        "mcp_management/samr_router.py"

    
    for script in scripts:
        script_path = base_dir / script
        if script_path.exists():
            print(f"Starting {script}...")
            subprocess.Popen([sys.executable, str(script_path)])
        else:
            print(f"Script not found: {script}")
    
    print("✅ Quick start completed!")
    print("Check status: python mcp_management/status_check.py")

if __name__ == "__main__":
    quick_start()
"""
    
    with open("quick_start_mcp.py", "w") as f:
        f.write(quick_start_content)
    
    print("📝 Created quick_start_mcp.py for future use")

if __name__ == "__main__":
    try:
        # Run the main setup
        asyncio.run(main())
        
        # Create quick start script
        create_quick_start_script()
        
    except KeyboardInterrupt:
        print("\n🛑 Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        print("Please check the error and try again")
    
    print("\n🏁 Setup script completed") 