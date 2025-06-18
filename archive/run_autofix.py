#!/usr/bin/env python3
"""
Simple LangChain Auto-Fix Runner
==============================

This script runs the comprehensive auto-fix system for the LangChain orchestrator.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_autofix():
    """Run the auto-fix system"""
    current_dir = Path.cwd()
    autofix_script = current_dir / "langchain_autofix_system.py"
    
    if not autofix_script.exists():
        print("❌ Auto-fix script not found!")
        return False
        
    print("🚀 Starting LangChain Auto-Fix...")
    print("This will automatically fix:")
    print("  - Syntax errors")
    print("  - Import issues") 
    print("  - Indentation problems")
    print("  - Docker configuration")
    print("  - Package dependencies")
    print("  - File encoding issues")
    print()
    
    try:
        # Run the auto-fix system
        result = subprocess.run([
            sys.executable, str(autofix_script)
        ], cwd=current_dir)
        
        if result.returncode == 0:
            print("✅ Auto-fix completed successfully!")
            
            # Test the orchestrator
            print("\n🧪 Testing orchestrator syntax...")
            orchestrator_file = current_dir / "enhanced_langchain_orchestrator.py"
            if orchestrator_file.exists():
                test_result = subprocess.run([
                    sys.executable, "-m", "py_compile", str(orchestrator_file)
                ], capture_output=True, text=True)
                
                if test_result.returncode == 0:
                    print("✅ Orchestrator syntax is valid!")
                else:
                    print(f"❌ Syntax issues remain: {test_result.stderr}")
                    
            return True
        else:
            print("❌ Auto-fix failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running auto-fix: {e}")
        return False

def main():
    """Main function"""
    print("🔧 LangChain Auto-Fix Runner")
    print("=" * 40)
    
    success = run_autofix()
    
    if success:
        print("\n🎉 Auto-fix process completed successfully!")
        print("\nNext steps:")
        print("1. Review the fixed files")
        print("2. Run: docker-compose up -d")
        print("3. Check logs: docker-compose logs -f")
    else:
        print("\n💥 Auto-fix process failed!")
        print("Check the logs for details.")
        
    return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
