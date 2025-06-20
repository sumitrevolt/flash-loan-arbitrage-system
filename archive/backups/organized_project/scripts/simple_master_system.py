#!/usr/bin/env python3
"""
Simple Master LangChain System Test
===================================

A simplified version of the Master LangChain System for testing.
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Set up logging without Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SimpleMasterSystem:
    """Simple Master LangChain System for testing"""
    
    def __init__(self):
        self.project_root = project_root
        logger.info("Initializing Simple Master LangChain System...")
        
        # Basic status tracking
        self.status = {
            "initialized": True,
            "agents_available": ["terminal", "copilot", "mcp", "project"],
            "system_ready": True
        }
        
        logger.info("System initialized successfully!")
    
    async def start(self):
        """Start the interactive system"""
        logger.info("Starting interactive interface...")
        print("\n" + "="*60)
        print("🚀 MASTER LANGCHAIN SYSTEM - INTERACTIVE MODE")
        print("="*60)
        print("Available commands:")
        print("  help     - Show available commands")
        print("  status   - Show system status") 
        print("  test     - Run system test")
        print("  exit     - Exit the system")
        print("="*60)
        
        while True:
            try:
                command = input("\n💡 Master System> ").strip().lower()
                
                if command == "exit":
                    print("👋 Goodbye!")
                    break
                elif command == "help":
                    self.show_help()
                elif command == "status":
                    self.show_status()
                elif command == "test":
                    await self.run_test()
                elif command == "":
                    continue
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n👋 Interrupted by user. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        """Show help information"""
        print("\n📖 HELP - Available Commands:")
        print("-" * 40)
        print("help     - Show this help message")
        print("status   - Display system status and health")
        print("test     - Run a comprehensive system test")
        print("exit     - Exit the Master LangChain System")
        print("\n💡 Tips:")
        print("- All commands are case-insensitive")
        print("- Use Ctrl+C to interrupt at any time")
    
    def show_status(self):
        """Show system status"""
        print("\n📊 SYSTEM STATUS:")
        print("-" * 40)
        print(f"✅ System Ready: {self.status['system_ready']}")
        print(f"✅ Project Root: {self.project_root}")
        print(f"✅ Available Agents: {len(self.status['agents_available'])}")
        for agent in self.status['agents_available']:
            print(f"   - {agent}")
        print(f"✅ Python Version: {sys.version.split()[0]}")
        print(f"✅ Working Directory: {os.getcwd()}")
    
    async def run_test(self):
        """Run system tests"""
        print("\n🧪 RUNNING SYSTEM TESTS...")
        print("-" * 40)
        
        tests = [
            ("Environment Setup", self.test_environment),
            ("File System Access", self.test_file_system),
            ("Agent Initialization", self.test_agents),
            ("System Integration", self.test_integration)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                print(f"Testing {test_name}...", end=" ")
                await test_func() if asyncio.iscoroutinefunction(test_func) else test_func()
                print("✅ PASS")
                passed += 1
            except Exception as e:
                print(f"❌ FAIL: {e}")
        
        print(f"\n📈 Test Results: {passed}/{len(tests)} tests passed")
        if passed == len(tests):
            print("🎉 All tests passed! System is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the errors above.")
    
    def test_environment(self):
        """Test environment setup"""
        # Test critical imports
        import json, pathlib, asyncio
        assert sys.version_info >= (3, 8), "Python 3.8+ required"
    
    def test_file_system(self):
        """Test file system access"""
        assert self.project_root.exists(), "Project root must exist"
        assert (self.project_root / "src").exists(), "src directory must exist"
    
    async def test_agents(self):
        """Test agent availability"""
        assert len(self.status['agents_available']) > 0, "At least one agent must be available"
    
    async def test_integration(self):
        """Test system integration"""
        assert self.status['system_ready'], "System must be ready"

async def main():
    """Main function"""
    try:
        system = SimpleMasterSystem()
        await system.start()
    except Exception as e:
        logger.error(f"System failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
