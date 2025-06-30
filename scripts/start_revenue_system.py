#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 START AAVE FLASH LOAN REVENUE SYSTEM 🚀
=========================================

Quick launcher for the production revenue system.
"""

from pathlib import Path
import subprocess
import sys

def setup_environment():
    """Setup the environment for revenue generation"""
    print("🔧 Setting up environment...")
    
    # Create necessary directories
    directories = [
        'production',
        'production/logs',
        'production/monitoring',
        'production/config'

    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Environment setup complete")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # List of required packages
    packages = [
        'asyncio',
        'aiohttp',
        'web3',
        'requests'

    
    try:
        for package in packages:
            try:
                __import__(package)
                print(f"✅ {package} already installed")
            except ImportError:
                print(f"⏳ Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} installed")
    except Exception as e:
        print(f"⚠️  Some packages may not be available: {e}")
        print("📝 Note: The system will run with simulated data")

def start_revenue_system():
    """Start the revenue generation system"""
    print("\n" + "="*80)
    print("🚀 STARTING AAVE FLASH LOAN REVENUE SYSTEM")
    print("="*80)
    
    try:
        # Run the production revenue system
        subprocess.run([sys.executable, "production_revenue_system.py"])
    except KeyboardInterrupt:
        print("\n⏹️  System stopped by user")
    except Exception as e:
        print(f"❌ Error starting system: {e}")

def main():
    """Main function"""
    print("\n" + "="*80)
    print("🚀 AAVE FLASH LOAN REVENUE SYSTEM LAUNCHER")
    print("="*80)
    print("💰 Automated arbitrage revenue generation")
    print("⚡ Flash loan integration with Aave V3")
    print("🔄 Multi-DEX price monitoring")
    print("📊 Real-time profit tracking")
    print("="*80)
    
    # Setup environment
    setup_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Start the revenue system
    start_revenue_system()

if __name__ == "__main__":
    main() 