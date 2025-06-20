#!/usr/bin/env python3
"""
Environment Test Script
======================

Quick test to validate the Python environment and critical dependencies
before running the full Master LangChain System.
"""

import sys
import os
import traceback
from pathlib import Path

def test_import(module_name, optional=False):
    """Test importing a module and report status"""
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        status = "⚠️" if optional else "❌"
        print(f"{status} {module_name} - {e}")
        return False
    except Exception as e:
        print(f"❌ {module_name} - Unexpected error: {e}")
        return False

def main():
    print("🧪 Environment Test Script")
    print("=" * 50)
    
    # Test Python version
    print(f"🐍 Python Version: {sys.version}")
    print(f"📁 Current Directory: {os.getcwd()}")
    print(f"📁 Script Directory: {Path(__file__).parent}")
    
    print("\n🔍 Testing Critical Imports:")
    print("-" * 30)
    
    # Critical imports (must work)
    critical_modules = [
        "asyncio",
        "pathlib", 
        "json",
        "logging",
        "sys",
        "os",
        "traceback",
        "psutil"
    ]
    
    critical_success = 0
    for module in critical_modules:
        if test_import(module):
            critical_success += 1
    
    print(f"\nCritical: {critical_success}/{len(critical_modules)} ✅")
    
    print("\n🔍 Testing Essential Imports:")
    print("-" * 30)
    
    # Essential imports (should work)
    essential_modules = [
        "aiohttp",
        "requests", 
        "pandas",
        "numpy"
    ]
    
    essential_success = 0
    for module in essential_modules:
        if test_import(module):
            essential_success += 1
    
    print(f"\nEssential: {essential_success}/{len(essential_modules)} ✅")
    
    print("\n🔍 Testing Optional Imports:")
    print("-" * 30)
    
    # Optional imports (nice to have)
    optional_modules = [
        "langchain",
        "langchain_community",
        "langchain_openai",
        "openai",
        "web3",
        "rich",
        "click",
        "docker",
        "redis",
        "matplotlib"
    ]
    
    optional_success = 0
    for module in optional_modules:
        if test_import(module, optional=True):
            optional_success += 1
    
    print(f"\nOptional: {optional_success}/{len(optional_modules)} ✅")
    
    print("\n" + "=" * 50)
    
    # Overall assessment
    total_critical = len(critical_modules)
    total_essential = len(essential_modules)
    
    if critical_success == total_critical and essential_success >= total_essential * 0.8:
        print("🎉 Environment is READY!")
        print("The Master LangChain System should work correctly.")
        return 0
    elif critical_success == total_critical:
        print("⚠️ Environment is PARTIALLY READY")
        print("Critical modules work, but some essential modules are missing.")
        print("The system may work with reduced functionality.")
        return 0
    else:
        print("❌ Environment is NOT READY")
        print("Critical modules are missing. Please install dependencies.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Test script failed: {e}")
        traceback.print_exc()
        sys.exit(1)
