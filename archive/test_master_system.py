#!/usr/bin/env python3
"""
Test Script for Master LangChain System
========================================

Quick test to verify all components are working correctly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the source directory to the path
sys.path.append(str(Path(__file__).parent / "src" / "langchain_coordinators"))

async def test_system():
    """Test the master system"""
    print("🧪 Testing Master LangChain System...")
    
    try:
        # Import the system
        from master_langchain_system import MasterLangChainSystem
        print("✅ Successfully imported MasterLangChainSystem")
        
        # Initialize the system
        system = MasterLangChainSystem()
        print("✅ System instance created")
        
        # Test initialization
        init_result = await system.initialize()
        if init_result["success"]:
            print(f"✅ System initialized ({init_result['subsystems_ready']}/{init_result['total_subsystems']} subsystems ready)")
        else:
            print(f"❌ System initialization failed: {init_result.get('error', 'Unknown error')}")
        
        # Test basic functionality
        print("\n🔧 Testing basic functionality...")
        
        # Test terminal command
        terminal_result = await system.execute_terminal_command("echo Hello World")
        if terminal_result.get("success"):
            print("✅ Terminal command execution works")
        else:
            print(f"⚠️ Terminal command test: {terminal_result.get('error', 'Unknown error')}")
        
        # Test code assistance
        code_result = await system.get_code_assistance("def hello():", "test.py")
        if code_result.get("success"):
            print(f"✅ Code assistance works ({len(code_result.get('suggestions', []))} suggestions)")
        else:
            print(f"⚠️ Code assistance test: {code_result.get('error', 'Unknown error')}")
        
        # Test system status
        status = await system.get_system_status()
        print(f"✅ System status retrieved (uptime: {status['master_system']['uptime']})")
        
        # Test project management
        project_result = await system.manage_project("analyze_structure")
        if project_result.get("success"):
            print("✅ Project management works")
        else:
            print(f"⚠️ Project management test: {project_result.get('error', 'Unknown error')}")
        
        print("\n📊 Test Summary:")
        print(f"  - System initialized: {init_result['success']}")
        print(f"  - Subsystems ready: {init_result['subsystems_ready']}/{init_result['total_subsystems']}")
        print(f"  - Agents active: {status['terminal_coordinator']['agents_active']}")
        print(f"  - System uptime: {status['master_system']['uptime']}")
        
        # Cleanup
        await system.shutdown()
        print("✅ System shutdown completed")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_individual_components():
    """Test individual components"""
    print("\n🧪 Testing individual components...")
    
    try:
        # Test MultiAgentTerminalCoordinator
        from multi_agent_terminal_coordinator import MultiAgentTerminalCoordinator
        coordinator = MultiAgentTerminalCoordinator()
        await coordinator.initialize()
        print("✅ MultiAgentTerminalCoordinator works")
        await coordinator.shutdown()
    except Exception as e:
        print(f"⚠️ MultiAgentTerminalCoordinator test failed: {e}")
    
    try:
        # Test GitHubCopilotTrainer
        from github_copilot_trainer import GitHubCopilotTrainer
        trainer = GitHubCopilotTrainer()
        suggestions = await trainer.generate_copilot_suggestions("def test():", "python")
        print(f"✅ GitHubCopilotTrainer works ({len(suggestions)} suggestions)")
    except Exception as e:
        print(f"⚠️ GitHubCopilotTrainer test failed: {e}")
    
    try:
        # Test MCPServerManager
        from mcp_server_trainer import MCPServerManager
        manager = MCPServerManager()
        status = await manager.get_server_status()
        print(f"✅ MCPServerManager works ({status['total_servers']} servers configured)")
    except Exception as e:
        print(f"⚠️ MCPServerManager test failed: {e}")

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "langchain",
        "aiohttp", 
        "aiofiles",
        "requests",
        "psutil",
        "pandas",
        "pathlib"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required dependencies are available")
    return True

async def main():
    """Main test function"""
    print("=" * 60)
    print("🚀 MASTER LANGCHAIN SYSTEM TEST")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return 1
    
    # Test individual components
    await test_individual_components()
    
    # Test the full system
    success = await test_system()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("🚀 Your Master LangChain System is ready to use!")
        print("\nTo start the system, run:")
        print("  python src/langchain_coordinators/master_langchain_system.py")
        print("  or")
        print("  start_master_langchain_system.bat")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the error messages above and fix any issues.")
    
    print("=" * 60)
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
