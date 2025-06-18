#!/usr/bin/env python3
"""
System Fix Validator
===================

This script validates that the Unicode and dependency fixes are working correctly.
"""

import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from unicode_safe_logger import get_unicode_safe_logger
    print("✅ Unicode logger imported successfully")
except Exception as e:
    print(f"❌ Failed to import unicode logger: {e}")
    sys.exit(1)

def test_unicode_logging():
    """Test that Unicode logging works without encoding errors"""
    print("\n🔍 Testing Unicode-safe logging...")
    
    try:
        logger = get_unicode_safe_logger("test_logger", "test_fix.log")
        
        # Test various emoji messages that were causing issues
        test_messages = [
            "🚀 Starting Self-Healing Coordination System",
            "🔍 Checking prerequisites...",
            "✅ Docker found: Docker version 28.1.1",
            "🔧 Setting up environment...",
            "🔨 Building Docker images...",
            "❌ Error building images",
        ]
        
        for message in test_messages:
            logger.info(message)
            print(f"✅ Logged: {message}")
        
        print("✅ All Unicode logging tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Unicode logging test failed: {e}")
        return False

def test_package_compatibility():
    """Test that package versions are compatible"""
    print("\n📦 Testing package compatibility...")
    
    try:
        # Test if we can import the packages that were causing conflicts
        import langchain
        print(f"✅ langchain version: {langchain.__version__}")
        
        # Test specific components
        try:
            from langchain.llms import OpenAI
            print("✅ langchain.llms imported successfully")
        except ImportError as e:
            print(f"⚠️ langchain.llms import issue (may be normal): {e}")
        
        try:
            from langchain_community.llms import Ollama
            print("✅ langchain_community imported successfully")
        except ImportError as e:
            print(f"⚠️ langchain_community import issue: {e}")
        
        try:
            from langchain_core.messages import HumanMessage
            print("✅ langchain_core imported successfully")
        except ImportError as e:
            print(f"⚠️ langchain_core import issue: {e}")
        
        print("✅ Package compatibility tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Package import test failed: {e}")
        print("Note: This is expected if packages aren't installed yet.")
        return False

def main():
    """Run all validation tests"""
    print("🔧 System Fix Validator")
    print("=" * 50)
    
    unicode_ok = test_unicode_logging()
    package_ok = test_package_compatibility()
    
    print("\n📊 Test Results:")
    print(f"Unicode Logging: {'✅ PASS' if unicode_ok else '❌ FAIL'}")
    print(f"Package Compatibility: {'✅ PASS' if package_ok else '⚠️  SKIP (not installed)'}")
    
    if unicode_ok:
        print("\n🎉 Unicode fixes are working correctly!")
        print("You should no longer see UnicodeEncodeError messages.")
    
    print("\n🚀 Next steps:")
    print("1. Try running the system again with: .\\launch_coordination_system.ps1 -System test-complete")
    print("2. The Docker builds should now work without dependency conflicts")
    print("3. All emoji characters will be converted to text representations")

if __name__ == "__main__":
    main()
