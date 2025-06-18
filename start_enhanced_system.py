#!/usr/bin/env python3
"""
🚀 Enhanced Agentic Flash Loan Arbitrage System - Quick Starter
============================================================

This is a simple startup script for your enhanced system.
It provides a clean interface to launch the full system.
"""

import asyncio
import os
import sys
from pathlib import Path

def print_banner():
    """Print system banner"""
    print("\n" + "="*80)
    print("🚀 ENHANCED AGENTIC FLASH LOAN ARBITRAGE SYSTEM")
    print("="*80)
    print("🎯 Features: Auto-Healing | GitHub Integration | 80+ MCP Servers | 10 AI Agents")
    print("💡 Advanced Capabilities: Self-Healing | Pattern Recognition | Real-time Monitoring")
    print("="*80)

def check_environment():
    """Check if we're in the right environment"""
    current_dir = Path.cwd()
    required_files = [
        "enhanced_agentic_launcher.py",
        "unified_mcp_config.json",
        "ai_agents_config.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   • {file}")
        print("\n💡 Please ensure you're in the correct project directory.")
        return False
    
    return True

def show_system_info():
    """Show system information"""
    print("\n📊 SYSTEM INFORMATION")
    print("-" * 50)
    print(f"📂 Project Directory: {Path.cwd()}")
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    print(f"💻 Platform: {sys.platform}")
    
    # Check if main files exist
    files_status = {
        "Enhanced Launcher": "enhanced_agentic_launcher.py",
        "MCP Config": "unified_mcp_config.json", 
        "AI Agents Config": "ai_agents_config.json",
        "Master Coordination": "master_coordination_system.py",
        "LangChain System": "langchain_command_system.py"
    }
    
    print("\n📋 SYSTEM FILES STATUS")
    print("-" * 50)
    for name, filename in files_status.items():
        exists = Path(filename).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {filename}")

def show_quick_commands():
    """Show quick command reference"""
    print("\n🎮 QUICK COMMAND REFERENCE")
    print("-" * 50)
    print("Once the system starts, use these commands:")
    print("  🚀 'start'           - Start all systems")
    print("  📊 'status'          - Show system status")
    print("  💰 'arbitrage'       - Scan for opportunities")
    print("  🔍 'github <query>'  - Search GitHub patterns")
    print("  🔧 'heal'            - Manual healing")
    print("  ❓ 'help'            - Show all commands")
    print("  🚪 'quit'            - Exit system")

def main():
    """Main startup function"""
    print_banner()
    
    print("\n🔍 SYSTEM CHECKS")
    print("-" * 50)
    
    # Check environment
    print("Checking environment...", end=" ")
    if not check_environment():
        print("\n❌ Environment check failed!")
        print("\n💡 To fix this:")
        print("1. Navigate to your flash loan project directory")
        print("2. Ensure all required files are present")
        print("3. Run this script again")
        try:
            input("\nPress Enter to exit...")
        except (KeyboardInterrupt, EOFError):
            pass
        return
    
    print("✅ Environment OK")
    
    # Show system info
    show_system_info()
    
    # Show quick commands
    show_quick_commands()
    
    print("\n🚀 LAUNCH OPTIONS")
    print("-" * 50)
    print("1. 🎯 Launch Enhanced System (Recommended)")
    print("2. 📊 System Information Only")
    print("3. 🚪 Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == "1":
                print("\n🚀 Launching Enhanced Agentic System...")
                print("=" * 80)
                print("🔄 Starting enhanced_agentic_launcher.py...")
                print("💡 This will start all MCP servers, AI agents, and coordination systems")
                print("⏰ Initial startup may take 1-2 minutes...")
                print("=" * 80)
                
                # Import and run the enhanced launcher
                try:
                    from enhanced_agentic_launcher import main as launcher_main
                    asyncio.run(launcher_main())
                except ImportError:
                    print("❌ Could not import enhanced launcher!")
                    print("💡 Trying direct execution...")
                    try:
                        os.system("python enhanced_agentic_launcher.py")
                    except Exception as e:
                        print(f"❌ Direct execution failed: {e}")
                except Exception as e:
                    print(f"❌ Launch error: {e}")
                    print("💡 Trying direct execution...")
                    try:
                        os.system("python enhanced_agentic_launcher.py")
                    except Exception as e2:
                        print(f"❌ Direct execution also failed: {e2}")
                break
                
            elif choice == "2":
                print("\n📊 System information displayed above.")
                print("💡 Use option 1 to launch the system.")
                continue
                
            elif choice == "3":
                print("\n👋 Goodbye! Your enhanced system is ready when you are.")
                break
                
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Your enhanced system is ready when you are.")
            break
        except EOFError:
            print("\n\n👋 Goodbye! Your enhanced system is ready when you are.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Startup cancelled. Your enhanced system is ready when you are.")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print("Please check your environment and try again.")
