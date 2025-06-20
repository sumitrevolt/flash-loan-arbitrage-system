#!/usr/bin/env python3
"""
Live Mode Preparation Script
===========================

This script helps you prepare for live AAVE flash loan trading by:
1. Checking wallet balance and funding requirements
2. Validating environment configuration
3. Enabling live execution mode
4. Providing step-by-step instructions

PREREQUISITES:
- Wallet funded with MATIC (minimum 0.2 MATIC for gas fees)
- PRIVATE_KEY set in .env file
- All MCP servers trained and validated
"""

import os
import json
from pathlib import Path
from web3 import Web3
from datetime import datetime

def check_environment():
    """Check environment configuration"""
    print("🔍 CHECKING ENVIRONMENT CONFIGURATION")
    print("=" * 50)
    
    issues = []
    
    # Check .env file
    env_path = Path(".env")
    if not env_path.exists():
        issues.append("❌ .env file not found")
        return issues
    
    # Load environment
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    # Check required variables
    required_vars = [
        'POLYGON_RPC_URL',
        'ENABLE_REAL_EXECUTION',
        'MIN_PROFIT_USD',
        'MAX_PROFIT_USD'
    ]
    
    for var in required_vars:
        if var in env_vars:
            print(f"✅ {var}: {env_vars[var]}")
        else:
            issues.append(f"❌ Missing: {var}")
    
    # Check PRIVATE_KEY
    if 'PRIVATE_KEY' in env_vars and env_vars['PRIVATE_KEY']:
        print(f"✅ PRIVATE_KEY: Set (length: {len(env_vars['PRIVATE_KEY'])})")
    else:
        issues.append("❌ PRIVATE_KEY not set in .env file")
    
    # Check execution mode
    if env_vars.get('ENABLE_REAL_EXECUTION', 'false').lower() == 'true':
        print("✅ ENABLE_REAL_EXECUTION: true (Live mode enabled)")
    else:
        print("🟡 ENABLE_REAL_EXECUTION: false (Test mode)")
        
    return issues

def check_wallet_balance():
    """Check wallet balance and funding requirements"""
    print("\n💰 CHECKING WALLET BALANCE")
    print("=" * 50)
    
    try:
        # Load environment
        env_path = Path(".env")
        env_vars = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        
        rpc_url = env_vars.get('POLYGON_RPC_URL')
        private_key = env_vars.get('PRIVATE_KEY')
        
        if not rpc_url or not private_key:
            print("❌ RPC URL or PRIVATE_KEY not configured")
            return False
        
        # Connect to network
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("❌ Failed to connect to Polygon network")
            return False
        
        # Load account
        account = w3.eth.account.from_key(private_key)
        print(f"📍 Wallet Address: {account.address}")
        
        # Check MATIC balance
        balance_wei = w3.eth.get_balance(account.address)
        balance_matic = balance_wei / 10**18
        
        print(f"💎 MATIC Balance: {balance_matic:.6f} MATIC")
        
        # Calculate required balance
        required_gas = 2000000  # 20 approvals × 100k gas each
        current_gas_price = w3.eth.gas_price
        gas_price_gwei = current_gas_price / 10**9
        required_matic = (required_gas * current_gas_price) / 10**18
        
        print(f"⛽ Current Gas Price: {gas_price_gwei:.1f} gwei")
        print(f"📊 Required for Approvals: {required_matic:.6f} MATIC")
        print(f"🔄 Recommended Minimum: {required_matic * 2:.6f} MATIC (2x buffer)")
        
        if balance_matic >= required_matic * 2:
            print("✅ Wallet sufficiently funded for live trading")
            return True
        elif balance_matic >= required_matic:
            print("🟡 Wallet has minimum balance (consider adding more)")
            return True
        else:
            print("❌ Insufficient MATIC balance for approvals")
            print(f"   Need: {required_matic * 2 - balance_matic:.6f} more MATIC")
            return False
            
    except Exception as e:
        print(f"❌ Error checking wallet balance: {e}")
        return False

def check_system_status():
    """Check MCP system status"""
    print("\n🔧 CHECKING SYSTEM STATUS")
    print("=" * 50)
    
    # Check if servers are trained
    models_dir = Path("models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.joblib"))
        print(f"✅ Found {len(model_files)} trained models")
        for model_file in model_files:
            print(f"   📊 {model_file.name}")
    else:
        print("❌ Models directory not found - run training first")
        return False
    
    # Check config files
    config_files = [
        "config/aave_config.json",
        "config/deployment_config.json"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ Missing: {config_file}")
            return False
    
    return True

def enable_live_mode():
    """Enable live trading mode"""
    print("\n🚀 ENABLING LIVE MODE")
    print("=" * 50)
    
    # Read current .env
    env_path = Path(".env")
    lines = []
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update ENABLE_REAL_EXECUTION
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('ENABLE_REAL_EXECUTION='):
            lines[i] = 'ENABLE_REAL_EXECUTION=true\n'
            updated = True
            break
    
    if not updated:
        lines.append('ENABLE_REAL_EXECUTION=true\n')
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("✅ Live mode enabled in .env file")
    
    # Update execute_token_approvals.py simulation mode
    approval_script = Path("execute_token_approvals.py")
    if approval_script.exists():
        with open(approval_script, 'r') as f:
            content = f.read()
        
        # Change simulation_mode = True to simulation_mode = False
        updated_content = content.replace(
            'self.simulation_mode = True  # Start in simulation mode for safety',
            'self.simulation_mode = False  # Live mode enabled'
        )
        
        with open(approval_script, 'w') as f:
            f.write(updated_content)
        
        print("✅ Token approval script updated for live execution")

def print_execution_instructions():
    """Print step-by-step execution instructions"""
    print("\n📋 LIVE EXECUTION INSTRUCTIONS")
    print("=" * 50)
    
    print("1. 🔐 EXECUTE TOKEN APPROVALS:")
    print("   python execute_token_approvals.py")
    print("   - This will execute all 20 token approvals")
    print("   - Confirm with 'YES' when prompted")
    print("   - Wait for all transactions to complete")
    print()
    
    print("2. 🚀 START TRADING SYSTEM:")
    print("   python demo_master_system.py")
    print("   - This starts the live trading system")
    print("   - Monitor logs for opportunities")
    print("   - System will execute profitable trades automatically")
    print()
    
    print("3. 📊 MONITOR PERFORMANCE:")
    print("   python monitor_system.py")
    print("   - Track system performance")
    print("   - View profit/loss statistics")
    print("   - Monitor for any issues")
    print()
    
    print("4. 🛡️ SAFETY REMINDERS:")
    print("   - Start with small amounts for testing")
    print("   - Monitor gas prices and adjust limits")
    print("   - Keep MATIC balance above 0.1 for operations")
    print("   - Review all transactions in block explorer")

def main():
    """Main execution function"""
    print("=" * 80)
    print("🚀 AAVE FLASH LOAN LIVE MODE PREPARATION")
    print("=" * 80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check environment
    env_issues = check_environment()
    
    if env_issues:
        print(f"\n❌ ENVIRONMENT ISSUES FOUND:")
        for issue in env_issues:
            print(f"   {issue}")
        print("\n🔧 Fix these issues before proceeding to live mode")
        return
    
    # Check wallet balance
    wallet_ok = check_wallet_balance()
    
    # Check system status
    system_ok = check_system_status()
    
    # Overall status
    print("\n🏁 READINESS ASSESSMENT")
    print("=" * 50)
    
    if not wallet_ok:
        print("❌ Wallet not ready - fund with MATIC")
        return
    
    if not system_ok:
        print("❌ System not ready - run training first")
        return
    
    print("✅ Environment: Ready")
    print("✅ Wallet: Funded")
    print("✅ System: Trained")
    print("✅ All checks passed - ready for live mode!")
    
    # Ask user to enable live mode
    print("\n🎯 ENABLE LIVE MODE?")
    response = input("Enable live trading mode? (y/N): ").lower()
    
    if response in ['y', 'yes']:
        enable_live_mode()
        print_execution_instructions()
        
        print("\n🎉 LIVE MODE ACTIVATED!")
        print("Follow the instructions above to start trading.")
    else:
        print("Live mode not enabled. Run this script again when ready.")

if __name__ == "__main__":
    main()
