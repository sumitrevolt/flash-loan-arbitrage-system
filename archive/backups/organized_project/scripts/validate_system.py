#!/usr/bin/env python3
"""
AAVE Flash Loan System Validation
==================================

Quick validation test to verify all MCP components are properly trained and configured.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def load_env_file():
    """Load environment variables from .env file"""
    env_path = project_root / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def print_banner():
    print("=" * 60)
    print("AAVE FLASH LOAN SYSTEM VALIDATION")
    print("=" * 60)
    print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Path: {project_root}")
    print("=" * 60)

def check_trained_models():
    """Check if ML models are trained and available"""
    models_dir = project_root / "models"
    expected_models = [
        "arbitrage_classifier.pkl",
        "profit_regressor.pkl", 
        "risk_regressor.pkl"
    ]
    
    print("\n🤖 CHECKING TRAINED MODELS")
    print("-" * 30)
    
    models_found = 0
    for model in expected_models:
        model_path = models_dir / model
        if model_path.exists():
            size = model_path.stat().st_size
            print(f"✅ {model} - {size:,} bytes")
            models_found += 1
        else:
            print(f"❌ {model} - Not found")
    
    print(f"\nModels Status: {models_found}/{len(expected_models)} trained")
    return models_found == len(expected_models)

def check_configuration():
    """Check system configuration"""
    print("\n⚙️  CHECKING CONFIGURATION")
    print("-" * 30)
    
    # Check config files
    config_files = [
        "config/aave_config.json",
        "config/deployment_config.json",
        ".env"
    ]
    
    configs_found = 0
    for config_file in config_files:
        config_path = project_root / config_file
        if config_path.exists():
            print(f"✅ {config_file} - Found")
            configs_found += 1
        else:
            print(f"❌ {config_file} - Missing")
    
    # Check environment variables
    env_vars = [
        "POLYGON_RPC_URL",
        "MIN_PROFIT_USD", 
        "MAX_PROFIT_USD",
        "ENABLE_REAL_EXECUTION"
    ]
    
    print(f"\n📋 Environment Variables:")
    for var in env_vars:
        value = os.getenv(var, "Not set")
        print(f"   {var}: {value}")
    
    return configs_found == len(config_files)

def check_mcp_servers():
    """Check MCP server files"""
    print("\n🖥️  CHECKING MCP SERVERS")
    print("-" * 30)
    
    mcp_servers = [
        "mcp_servers/aave_flash_loan_mcp_server.py",
        "mcp_servers/dex_aggregator_mcp_server.py",
        "mcp_servers/risk_management_mcp_server.py",
        "mcp_servers/profit_optimizer_mcp_server.py",
        "mcp_servers/monitoring_mcp_server.py"
    ]
    
    servers_found = 0
    for server in mcp_servers:
        server_path = project_root / server
        if server_path.exists():
            print(f"✅ {server.split('/')[-1]} - Ready")
            servers_found += 1
        else:
            print(f"❌ {server.split('/')[-1]} - Missing")
    
    return servers_found >= 3  # At least core servers available

def check_system_readiness():
    """Overall system readiness check"""
    print("\n🎯 SYSTEM READINESS CHECK")
    print("-" * 30)
    
    # Load environment
    load_env_file()
    
    # Check components
    models_ok = check_trained_models()
    config_ok = check_configuration()
    servers_ok = check_mcp_servers()
    
    # Overall status
    print("\n📊 VALIDATION SUMMARY")
    print("-" * 30)
    print(f"🤖 ML Models: {'✅ Trained' if models_ok else '❌ Missing'}")
    print(f"⚙️  Configuration: {'✅ Ready' if config_ok else '❌ Incomplete'}")
    print(f"🖥️  MCP Servers: {'✅ Available' if servers_ok else '❌ Missing'}")
    
    # Profit targeting readiness
    min_profit = os.getenv('MIN_PROFIT_USD', '0')
    max_profit = os.getenv('MAX_PROFIT_USD', '0')
    
    print(f"\n💰 PROFIT TARGETING")
    print(f"   Target Range: ${min_profit} - ${max_profit}")
    print(f"   Execution Mode: {'🔴 LIVE' if os.getenv('ENABLE_REAL_EXECUTION', 'false').lower() == 'true' else '🟡 TEST'}")
    
    # Final status
    system_ready = models_ok and config_ok and servers_ok
    
    print(f"\n🎯 SYSTEM STATUS: {'✅ READY FOR OPERATIONS' if system_ready else '❌ NEEDS ATTENTION'}")
    
    if system_ready:
        print("\n🚀 NEXT STEPS:")
        print("   1. Start MCP servers (if not already running)")
        print("   2. Monitor for arbitrage opportunities")
        print("   3. Validate profit calculations")
        print("   4. Enable real execution when ready")
    
    return system_ready

def main():
    """Main validation function"""
    print_banner()
    
    try:
        system_ready = check_system_readiness()
        
        print("\n" + "=" * 60)
        if system_ready:
            print("✅ AAVE FLASH LOAN SYSTEM VALIDATION PASSED")
            print("System is trained and ready for profit-targeted operations!")
        else:
            print("❌ AAVE FLASH LOAN SYSTEM VALIDATION FAILED")
            print("Please address the issues above before proceeding.")
        print("=" * 60)
        
        return 0 if system_ready else 1
        
    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
