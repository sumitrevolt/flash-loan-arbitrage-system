#!/usr/bin/env python3
"""
Enhanced Multichain Agentic System Launcher
==========================================

Simple launcher for your enhanced arbitrage system that integrates all your existing
MCP servers and AI agents with advanced interaction capabilities.
"""

import asyncio
import sys
import os
from pathlib import Path

# Ensure we can import from the project directory
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("""
🚀 Enhanced Multichain Agentic System Launcher
============================================

This launcher will start your enhanced arbitrage system with:
- ✅ All your existing 21 MCP servers  
- ✅ All your existing 10 AI agents
- ✅ Advanced interaction system
- ✅ Multi-agent coordination
- ✅ Event-driven architecture
- ✅ Task queue management
- ✅ Auto-healing capabilities

""")

def check_requirements():
    """Check if basic requirements are met"""
    required_files = [
        'docker_arbitrage_orchestrator.py',
        'enhanced_orchestrator_integration.py',
        'core/interaction_system_enhancer.py',
        'ai_agents_config.json',
        'unified_mcp_config.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True

async def start_system():
    """Start the enhanced system"""
    try:
        print("🔄 Importing enhanced orchestrator...")
        from enhanced_orchestrator_integration import EnhancedDockerOrchestrator
        
        print("🔄 Initializing enhanced orchestrator...")
        orchestrator = EnhancedDockerOrchestrator()
        
        print("🚀 Starting enhanced multichain agentic system...")
        print("   This will coordinate all your MCP servers and AI agents")
        print("   Press Ctrl+C to stop the system gracefully")
        print()
        
        await orchestrator.start_enhanced_system()
        
    except KeyboardInterrupt:
        print("\n👋 System shutdown requested by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        print("   Run: pip install aiohttp web3 python-dotenv")
    except Exception as e:
        print(f"❌ System error: {e}")
        print("   Check logs for more details")

def main():
    """Main launcher function"""
    print("🔍 Checking system requirements...")
    
    if not check_requirements():
        print("\n❌ System requirements not met. Please ensure all files are present.")
        return
    
    print("\n🎯 Starting enhanced multichain agentic system...")
    
    try:
        asyncio.run(start_system())
    except Exception as e:
        print(f"\n❌ Failed to start system: {e}")

if __name__ == "__main__":
    main()
