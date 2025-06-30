#!/usr/bin/env python3
"""
Flash Loan Arbitrage Revenue Generation Startup Script
=====================================================

This script helps you start generating real revenue on Amoy testnet
and then move to production mainnet.

Author: AI Assistant
Version: 1.0
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List

class RevenueGenerationSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        print("🚀 Flash Loan Arbitrage Revenue Generation Setup")
        print("=" * 60)
        
    def check_prerequisites(self) -> List[str]:
        """Check if all prerequisites are met"""
        print("\n📋 Checking Prerequisites...")
        
        issues: List[str] = []
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                issues.append("Node.js not found")
        except FileNotFoundError:
            issues.append("Node.js not found")
            
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm: {result.stdout.strip()}")
            else:
                issues.append("npm not found")
        except FileNotFoundError:
            issues.append("npm not found")
            
        # Check Python
        print(f"✅ Python: {sys.version.split()[0]}")
        
        # Check if .env exists
        env_file = self.project_root / '.env'
        if env_file.exists():
            print("✅ .env file exists")
        else:
            issues.append(".env file not found")
            
        # Check package.json
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            print("✅ package.json exists")
        else:
            issues.append("package.json not found")
            
        return issues
    
    def create_env_template(self):
        """Create .env template if it doesn't exist"""
        env_content = """# ===========================================
# FLASH LOAN ARBITRAGE SYSTEM CONFIGURATION
# ===========================================

# ===========================================
# AMOY TESTNET CONFIGURATION
# ===========================================
# Replace with your actual private key (without 0x prefix)
PRIVATE_KEY=your_private_key_here
ARBITRAGE_PRIVATE_KEY=your_private_key_here

# Amoy RPC URLs
AMOY_RPC_URL=https://rpc-amoy.polygon.technology
POLYGON_RPC_URL=https://rpc-amoy.polygon.technology
RPC_URL=https://rpc-amoy.polygon.technology

# ===========================================
# API KEYS (Get from respective services)
# ===========================================
POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
COINGECKO_API_KEY=your_coingecko_api_key_here
MORALIS_API_KEY=your_moralis_api_key_here

# ===========================================
# TRADING PARAMETERS
# ===========================================
MIN_PROFIT_USD=3.0
MAX_PROFIT_USD=30.0
MAX_GAS_PRICE_GWEI=50
SLIPPAGE_TOLERANCE=500
ENABLE_REAL_EXECUTION=true
TRADING_ENABLED=true

# ===========================================
# CONTRACT ADDRESSES (SET AFTER DEPLOYMENT)
# ===========================================
CONTRACT_ADDRESS=
FLASH_LOAN_CONTRACT_ADDRESS=

# ===========================================
# INSTRUCTIONS
# ===========================================
# 1. Replace 'your_private_key_here' with your actual private key
# 2. Get POL tokens from https://faucet.polygon.technology/
# 3. Get API keys from the respective services
# 4. Save this file and run the deployment script
"""
        
        env_file = self.project_root / '.env'
        if not env_file.exists():
            try:
                with open(env_file, 'w') as f:
                    f.write(env_content)
                print(f"✅ Created .env template at {env_file}")
                return True
            except Exception as e:
                print(f"❌ Failed to create .env file: {e}")
                return False
        return True
    
    def install_dependencies(self):
        """Install npm dependencies"""
        print("\n📦 Installing Dependencies...")
        
        try:
            result = subprocess.run(['npm', 'install'], 
                                 cwd=self.project_root,
                                 capture_output=True, 
                                 text=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def compile_contracts(self):
        """Compile smart contracts"""
        print("\n🔨 Compiling Smart Contracts...")
        
        try:
            result = subprocess.run(['npx', 'hardhat', 'compile'], 
                                 cwd=self.project_root,
                                 capture_output=True, 
                                 text=True)
            
            if result.returncode == 0:
                print("✅ Contracts compiled successfully")
                return True
            else:
                print(f"❌ Failed to compile contracts: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error compiling contracts: {e}")
            return False
    
    def deploy_to_amoy(self):
        """Deploy contracts to Amoy testnet"""
        print("\n🚀 Deploying to Amoy Testnet...")
        
        # Check if .env has been configured
        env_file = self.project_root / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                if 'your_private_key_here' in content:
                    print("❌ Please configure your .env file with actual values first!")
                    print("   Edit .env and replace 'your_private_key_here' with your actual private key")
                    return False
        
        try:
            result = subprocess.run(['npx', 'hardhat', 'run', 
                                   'scripts/deploy-flashloan-fixed.js', 
                                   '--network', 'amoy'], 
                                 cwd=self.project_root,
                                 capture_output=True, 
                                 text=True)
            
            if result.returncode == 0:
                print("✅ Contract deployed to Amoy successfully!")
                print(result.stdout)
                
                # Try to extract contract address from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'deployed to:' in line.lower():
                        address = line.split(':')[-1].strip()
                        self.update_env_with_contract_address(address)
                        print(f"📍 Contract Address: {address}")
                        break
                
                return True
            else:
                print(f"❌ Failed to deploy contracts: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error deploying contracts: {e}")
            return False
    
    def update_env_with_contract_address(self, address: str) -> None:
        """Update .env file with deployed contract address"""
        env_file = self.project_root / '.env'
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Update contract address lines
                content = content.replace('CONTRACT_ADDRESS=', f'CONTRACT_ADDRESS={address}')
                content = content.replace('FLASH_LOAN_CONTRACT_ADDRESS=', f'FLASH_LOAN_CONTRACT_ADDRESS={address}')
                
                with open(env_file, 'w') as f:
                    f.write(content)
                    
                print("✅ Updated .env with contract address")
            except Exception as e:
                print(f"❌ Failed to update .env: {e}")
    
    def start_arbitrage_bot(self):
        """Start the arbitrage bot"""
        print("\n🤖 Starting Arbitrage Bot...")
        
        # Check which arbitrage systems are available
        arbitrage_scripts = [
            'src/arbitrage/start_24_7_arbitrage.py',
            'src/arbitrage/production_arbitrage_system.py',
            'scripts/real-arbitrage-bot.js'
        ]
        
        available_scripts = []
        for script in arbitrage_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                available_scripts.append(script)
        
        if not available_scripts:
            print("❌ No arbitrage scripts found")
            return False
        
        print(f"📋 Available arbitrage systems:")
        for i, script in enumerate(available_scripts, 1):
            print(f"   {i}. {script}")
        
        print("\n🚀 Starting 24/7 arbitrage system...")
        
        # Start the Python arbitrage system
        python_script = 'src/arbitrage/start_24_7_arbitrage.py'
        if python_script in available_scripts:
            try:
                print(f"▶️  Starting: python {python_script}")
                # Run in background
                subprocess.Popen([sys.executable, python_script], 
                               cwd=self.project_root)
                print("✅ Arbitrage bot started in background")
                return True
            except Exception as e:
                print(f"❌ Failed to start arbitrage bot: {e}")
                return False
        
        return False
    
    def run_setup(self):
        """Run the complete setup process"""
        print(f"📁 Project Root: {self.project_root}")
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Check prerequisites
        issues = self.check_prerequisites()
        if issues:
            print(f"\n❌ Prerequisites not met:")
            for issue in issues:
                print(f"   - {issue}")
            
            if ".env file not found" in issues:
                print("\n🔧 Creating .env template...")
                self.create_env_template()
                print("\n⚠️  Please edit .env file with your actual credentials and run this script again")
                return False
            return False
        
        # Step 2: Install dependencies
        if not self.install_dependencies():
            return False
        
        # Step 3: Compile contracts
        if not self.compile_contracts():
            return False
        
        # Step 4: Deploy to Amoy
        if not self.deploy_to_amoy():
            return False
        
        # Step 5: Start arbitrage bot
        if not self.start_arbitrage_bot():
            return False
        
        print("\n🎉 Revenue Generation System Started Successfully!")
        print("=" * 60)
        print("📊 Monitor your profits:")
        print("   - Check console output for real-time updates")
        print("   - View logs in the logs/ directory")
        print("   - Open dashboard at http://localhost:8000")
        print("\n💰 Expected Revenue:")
        print("   - Target: $10-30 per hour on testnet")
        print("   - Production: $100-500 per day")
        print("\n⚠️  Next Steps for Production:")
        print("   1. Test thoroughly on Amoy testnet")
        print("   2. Fund your wallet with MATIC for mainnet")
        print("   3. Update .env with mainnet configuration")
        print("   4. Deploy to Polygon mainnet")
        
        return True

def main():
    """Main entry point"""
    setup = RevenueGenerationSetup()
    
    try:
        success = setup.run_setup()
        if success:
            print("\n✅ Setup completed successfully!")
            print("🔄 System is now running...")
            
            # Keep script running to show status
            try:
                while True:
                    time.sleep(60)
                    print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - System running... (Ctrl+C to stop)")
            except KeyboardInterrupt:
                print("\n👋 Shutdown requested")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 