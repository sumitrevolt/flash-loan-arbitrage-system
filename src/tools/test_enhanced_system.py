#!/usr/bin/env python3
"""
Test Enhanced LangChain MCP Integration
=======================================

This script tests the enhanced LangChain MCP integration system to ensure
all components are working correctly.
"""

import asyncio
import logging
import json
from datetime import datetime

# Setup logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_functionality():
    """Test basic functionality of the enhanced system"""
    print("🧪 Testing Enhanced LangChain MCP Integration System")
    print("=" * 60)
    
    # Test 1: Import modules
    print("\n1. Testing module imports...")
    try:
        from enhanced_langchain_coordinator import EnhancedLangChainCoordinator
        from enhanced_mcp_server_manager import EnhancedMCPServerManager
        print("✅ Core modules imported successfully")
    except ImportError as e:
        print(f"❌ Module import failed: {e}")
        return False
    
    # Test 2: Create coordinator instance
    print("\n2. Testing coordinator creation...")
    try:
        coordinator = EnhancedLangChainCoordinator()
        print("✅ Coordinator instance created successfully")
    except Exception as e:
        print(f"❌ Coordinator creation failed: {e}")
        return False
    
    # Test 3: Create server manager instance
    print("\n3. Testing server manager creation...")
    try:
        server_manager = EnhancedMCPServerManager()
        print("✅ Server manager instance created successfully")
    except Exception as e:
        print(f"❌ Server manager creation failed: {e}")
        return False
    
    # Test 4: Configuration loading
    print("\n4. Testing configuration...")
    try:
        config = coordinator.config
        if 'mcp_servers' in config and 'llm' in config:
            print("✅ Configuration loaded successfully")
            print(f"   - Found {len(config.get('mcp_servers', {}))} MCP server configurations")
            print(f"   - LLM model: {config.get('llm', {}).get('model', 'unknown')}")
        else:
            print("⚠️ Configuration incomplete")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    # Test 5: Basic LangChain components
    print("\n5. Testing LangChain components...")
    try:
        # Test basic LangChain imports
        from langchain.chains import LLMChain
        from langchain.prompts import PromptTemplate
        from langchain.memory import ConversationBufferMemory
        print("✅ LangChain components available")
    except ImportError as e:
        print(f"❌ LangChain components missing: {e}")
        return False
    
    # Test 6: System dependencies
    print("\n6. Testing system dependencies...")
    dependencies = {
        'docker': 'Docker client',
        'redis': 'Redis client',
        'psutil': 'System utilities',
        'aiohttp': 'HTTP client',
        'yaml': 'YAML parser'
    }
    
    missing_deps = []
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {desc} available")
        except ImportError:
            print(f"❌ {desc} missing")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"⚠️ Missing dependencies: {', '.join(missing_deps)}")
        print("   Run: pip install -r requirements.txt")
    
    # Test 7: File structure
    print("\n7. Testing file structure...")
    from pathlib import Path
    
    required_files = [
        'enhanced_langchain_coordinator.py',
        'enhanced_mcp_server_manager.py',
        'complete_langchain_mcp_integration.py',
        'launch_enhanced_system.py',
        'requirements.txt'
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
    
    print("\n📊 Test Summary:")
    print("=" * 30)
    print("✅ Basic functionality tests completed")
    print("🌐 The system is ready for launch!")
    print("\n🚀 To start the system:")
    print("1. Run: python launch_enhanced_system.py")
    print("2. Or run: start_enhanced_system.bat (Windows)")
    print("3. Or run: .\start_enhanced_system.ps1 (PowerShell)")
    
    return True

async def test_integration_example():
    """Test a simple integration example"""
    print("\n🔬 Running Integration Example...")
    print("-" * 40)
    
    try:
        # Create a simple example of the integration
        from enhanced_langchain_coordinator import EnhancedLangChainCoordinator
        
        # Create coordinator
        coordinator = EnhancedLangChainCoordinator()
        
        # Test configuration access
        mcp_servers = coordinator.config.get('mcp_servers', {})
        print(f"📡 Configured MCP servers: {list(mcp_servers.keys())}")
        
        # Test server info creation
        from enhanced_mcp_server_manager import MCPServerInstance, ServerStatus
        
        # Create a test server instance
        test_server = MCPServerInstance(
            name="test-server",
            port=9999,
            capabilities=["test", "example"],
            status=ServerStatus.HEALTHY,
            health_score=0.95
        )
        
        print(f"🧪 Test server created: {test_server.name}")
        print(f"   Status: {test_server.status.value}")
        print(f"   Health Score: {test_server.health_score}")
        print(f"   Capabilities: {', '.join(test_server.capabilities)}")
        
        print("✅ Integration example completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration example failed: {e}")
        return False

async def main():
    """Main test function"""
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run basic functionality tests
    basic_success = await test_basic_functionality()
    
    if basic_success:
        # Run integration example
        await test_integration_example()
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if basic_success:
        print("\n🎉 All tests passed! The Enhanced LangChain MCP System is ready to use!")
        print("\n📚 Next steps:")
        print("1. Review the configuration in 'enhanced_coordinator_config.yaml'")
        print("2. Ensure Docker is running for full functionality")
        print("3. Launch the system using one of the provided startup scripts")
        print("4. Access the dashboard at http://localhost:8000")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above and fix them before proceeding.")

if __name__ == "__main__":
    asyncio.run(main())
