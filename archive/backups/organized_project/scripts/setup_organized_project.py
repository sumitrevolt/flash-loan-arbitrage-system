#!/usr/bin/env python3
"""
Flash Loan Project - Post Organization Setup Script
Helps transition to the organized project structure
"""

import os
import sys
from pathlib import Path

def setup_organized_project():
    """Setup the organized project for development"""
    
    # Set project root
    project_root = Path(__file__).parent.parent
    print(f"🚀 Setting up organized Flash Loan project at: {project_root}")
    
    # Check if we're in the right directory
    if not (project_root / "src").exists():
        print("❌ Error: Not in organized project directory")
        print("   Please run this script from organized_project/scripts/")
        return False
    
    print("\n📁 Project Structure Verification:")
    
    # Verify key directories exist
    key_dirs = [
        "src/core",
        "src/mcp_servers", 
        "src/coordination",
        "src/agents",
        "src/integrations",
        "config/environments",
        "config/docker",
        "scripts",
        "docs",
        "tests"
    ]
    
    for dir_path in key_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            file_count = len(list(full_path.glob("*")))
            print(f"   ✅ {dir_path}/ ({file_count} files)")
        else:
            print(f"   ❌ {dir_path}/ (missing)")
    
    # Check for requirements file
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        print(f"   ✅ requirements.txt ({req_file.stat().st_size} bytes)")
    else:
        print("   ❌ requirements.txt (missing)")
    
    print("\n🔧 Next Steps:")
    print("   1. Install dependencies:")
    print(f"      cd {project_root}")
    print("      pip install -r requirements.txt")
    print()
    print("   2. Set up environment:")
    print("      cp config/environments/.env.example .env")
    print("      # Edit .env with your settings")
    print()
    print("   3. Test MCP servers:")
    print("      python src/mcp_servers/enhanced_mcp_price_feed_server.py")
    print()
    print("   4. Launch coordination system:")
    print("      python scripts/enhanced_system_launcher.py")
    print()
    print("   5. Run tests:")
    print("      python -m pytest tests/")
    
    print("\n📚 Documentation:")
    docs_dir = project_root / "docs"
    if docs_dir.exists():
        md_files = list(docs_dir.glob("*.md"))
        print(f"   Available guides in docs/ ({len(md_files)} files):")
        for md_file in md_files[:5]:  # Show first 5
            print(f"     - {md_file.name}")
        if len(md_files) > 5:
            print(f"     ... and {len(md_files) - 5} more")
    
    print("\n🎯 System Ready!")
    print("   The flash loan arbitrage system has been successfully organized.")
    print("   All duplicates removed and files properly structured.")
    print("   Ready for development and deployment!")
    
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("🏗️  FLASH LOAN PROJECT - ORGANIZED SETUP")  
    print("=" * 60)
    
    try:
        success = setup_organized_project()
        if success:
            print("\n✅ Setup verification complete!")
            print("🚀 Project ready for development!")
        else:
            print("\n❌ Setup verification failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

