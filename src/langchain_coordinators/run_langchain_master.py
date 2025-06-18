#!/usr/bin/env python3
"""
Execute LangChain Master Coordinator
===================================
Simple execution script to run the master coordinator
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Execute the master coordinator"""
    print("🎮 [CONTROL] Starting LangChain Master Coordinator...")
    print("=" * 80)
    print("🚀 [START] COMMANDING LANGCHAIN TO FIX ALL MCP SERVERS AND AI AGENTS")
    print("=" * 80)
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run the master coordinator
    try:
        result: str = subprocess.run([
            sys.executable, 
            "langchain_master_coordinator.py"
        ], check=True)
        
        print("✅ [SUCCESS] Master coordination completed successfully!")
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"❌ [ERROR] Master coordination failed with exit code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("🛑 [STOP] Master coordination interrupted by user")
        return 1
    except Exception as e:
        print(f"🔥 [CRITICAL] Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
