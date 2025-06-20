#!/usr/bin/env python3
"""
LangChain MCP Project Organizer - Setup and Runner
================================================

This script helps setup and run the comprehensive project organizer.
It handles environment setup, dependency installation, and execution.

Author: GitHub Copilot Assistant
Date: June 18, 2025
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_and_install_dependencies():
    """Check and install required dependencies"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'langchain>=0.2.17',
        'langchain-openai>=0.1.25',
        'langchain-community>=0.2.19',
        'langchain-core>=0.2.43',
        'openai>=1.55.0',
        'requests',
        'aiohttp',
        'asyncio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            pkg_name = package.split('>=')[0].split('==')[0]
            __import__(pkg_name.replace('-', '_'))
            print(f"✅ {pkg_name} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {pkg_name} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    return True

def setup_environment():
    """Setup environment variables and configuration"""
    print("⚙️ Setting up environment...")
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ OPENAI_API_KEY not found in environment")
        print("To enable LangChain AI features, set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("The organizer will still work in fallback mode without it.")
    else:
        print("✅ OpenAI API key found")
    
    # Set project root
    project_root = os.getcwd()
    os.environ['PROJECT_ROOT'] = project_root
    print(f"📁 Project root set to: {project_root}")
    
    return True

def create_backup():
    """Create a backup before organization"""
    print("💾 Creating backup before organization...")
    
    project_root = Path(os.getcwd())
    backup_dir = project_root / 'backup_before_organization'
    
    if backup_dir.exists():
        print("⚠️ Backup directory already exists, skipping...")
        return True
    
    try:
        backup_dir.mkdir()
        
        # Copy critical files
        critical_files = [
            'package.json',
            'requirements*.txt',
            'docker-compose*.yml',
            '*.config.js',
            '*.env*'
        ]
        
        import glob
        import shutil
        
        for pattern in critical_files:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    shutil.copy2(file_path, backup_dir / os.path.basename(file_path))
                    print(f"📋 Backed up: {file_path}")
        
        print("✅ Backup created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def run_organizer():
    """Run the LangChain MCP organizer"""
    print("🚀 Running LangChain MCP Project Organizer...")
    
    try:
        # Import and run the organizer
        from langchain_mcp_project_organizer import LangChainMCPOrganizer
        import asyncio
        
        async def run_organization():
            organizer = LangChainMCPOrganizer(os.getcwd())
            
            if organizer.llm:
                print("🤖 Using AI-powered organization...")
                results = await organizer.run_intelligent_organization()
            else:
                print("🔧 Using standard organization...")
                results = await organizer.run_comprehensive_cleanup()
            
            return results
        
        results = asyncio.run(run_organization())
        
        print("\n🎉 Organization completed successfully!")
        print(f"📊 Results summary:")
        for key, value in results.items():
            print(f"  - {key.replace('_', ' ').title()}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Organization failed: {e}")
        return False

def post_organization_steps():
    """Provide post-organization guidance"""
    print("\n📋 Post-Organization Steps:")
    print("1. Review the organization report in docs/ORGANIZATION_SUMMARY.md")
    print("2. Check archived files in archive/ directory")
    print("3. Update your Docker configurations for new file paths")
    print("4. Test MCP servers: check config/mcp_servers.json")
    print("5. Update any hardcoded file paths in your scripts")
    print("6. Review and update documentation")
    
    project_root = Path(os.getcwd())
    
    # Check if important files were moved
    important_locations = {
        'MCP Servers': project_root / 'src' / 'mcp_servers',
        'AI Agents': project_root / 'src' / 'ai_agents', 
        'Configurations': project_root / 'config',
        'Documentation': project_root / 'docs',
        'Docker Files': project_root / 'docker'
    }
    
    print("\n📍 New file locations:")
    for name, location in important_locations.items():
        if location.exists():
            count = len(list(location.glob('*')))
            print(f"  - {name}: {location} ({count} files)")

def main():
    """Main execution function"""
    print("=" * 60)
    print("🚀 LangChain MCP Project Organizer - Setup & Runner")
    print("=" * 60)
    
    # Setup steps
    steps = [
        ("Checking dependencies", check_and_install_dependencies),
        ("Setting up environment", setup_environment),
        ("Creating backup", create_backup),
        ("Running organizer", run_organizer)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ {step_name} failed. Aborting.")
            sys.exit(1)
    
    # Post-organization guidance
    post_organization_steps()
    
    print("\n🎉 Organization process completed successfully!")
    print("Check the logs and reports for detailed information.")

if __name__ == "__main__":
    main()
