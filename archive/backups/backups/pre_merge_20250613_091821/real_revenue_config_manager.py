#!/usr/bin/env python3
"""
Real Revenue Configuration Manager
Configures the system for real revenue generation with live API keys and wallet setup
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import getpass
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealRevenueConfig")

class RealRevenueConfigManager:
    """Manages configuration for real revenue generation"""
    
    def __init__(self, config_path: str = "config/arbitrage-config.json"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load existing configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"✅ Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            raise
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"✅ Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
            raise
    
    def setup_real_api_keys(self):
        """Interactive setup for real API keys"""
        logger.info("🔑 Setting up real API keys for revenue generation...")
        
        print("\n" + "="*60)
        print("🔑 REAL API KEY SETUP FOR REVENUE GENERATION")
        print("="*60)
        print("To generate real revenue, you need API keys from blockchain providers.")
        print("We'll help you set up free tier accounts that are sufficient to start.")
        print()
        
        # Alchemy API Key (recommended)
        print("1. ALCHEMY API KEY (Recommended - Free tier available)")
        print("   - Go to: https://dashboard.alchemy.com/")
        print("   - Sign up for free account")
        print("   - Create a new app for Polygon Mainnet")
        print("   - Copy the API key from your dashboard")
        print()
        
        alchemy_key = input("Enter your Alchemy API key (or press Enter to skip): ").strip()
        
        if alchemy_key:
            # Update Polygon network (main revenue network)
            self.config['networks']['polygon']['rpc_url'] = f"https://polygon-mainnet.g.alchemy.com/v2/{alchemy_key}"
            logger.info("✅ Alchemy API key configured for Polygon")
            
            # Ask if they want to enable other networks
            enable_ethereum = input("Enable Ethereum network? (y/n): ").lower() == 'y'
            if enable_ethereum:
                self.config['networks']['ethereum']['rpc_url'] = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}"
                self.config['networks']['ethereum']['enabled'] = True
                logger.info("✅ Ethereum network enabled")
            
            enable_arbitrum = input("Enable Arbitrum network? (y/n): ").lower() == 'y'
            if enable_arbitrum:
                self.config['networks']['arbitrum']['rpc_url'] = f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}"
                self.config['networks']['arbitrum']['enabled'] = True
                logger.info("✅ Arbitrum network enabled")
        
        else:
            # Alternative: Infura
            print("\n2. INFURA API KEY (Alternative)")
            print("   - Go to: https://infura.io/")
            print("   - Sign up for free account")
            print("   - Create a new project")
            print("   - Copy the project ID")
            print()
            
            infura_key = input("Enter your Infura project ID (or press Enter to skip): ").strip()
            
            if infura_key:
                self.config['networks']['polygon']['rpc_url'] = f"https://polygon-mainnet.infura.io/v3/{infura_key}"
                self.config['networks']['ethereum']['rpc_url'] = f"https://mainnet.infura.io/v3/{infura_key}"
                logger.info("✅ Infura API key configured")
        
        # Public RPC fallback
        if not alchemy_key and not infura_key:
            print("\n⚠️ No API keys provided. Using public RPCs (limited functionality)")
            print("Public RPCs have rate limits and may not be suitable for high-frequency trading.")
            use_public = input("Use public RPCs anyway? (y/n): ").lower() == 'y'
            
            if use_public:
                self.config['networks']['polygon']['rpc_url'] = "https://polygon-rpc.com"
                logger.info("✅ Public RPC configured for Polygon")
    
    def setup_wallet_configuration(self):
        """Setup wallet configuration for trading"""
        logger.info("👛 Setting up wallet configuration...")
        
        print("\n" + "="*60)
        print("👛 WALLET SETUP FOR REVENUE GENERATION")
        print("="*60)
        print("You need a wallet with some cryptocurrency to pay for gas fees.")
        print("IMPORTANT: Only use a wallet specifically for this bot!")
        print()
        
        print("SECURITY RECOMMENDATIONS:")
        print("- Use a dedicated wallet only for this bot")
        print("- Start with small amounts for testing")
        print("- Never share your private key")
        print("- Store private key securely as environment variable")
        print()
        
        wallet_address = input("Enter your wallet address (0x...): ").strip()
        
        if wallet_address and wallet_address.startswith('0x') and len(wallet_address) == 42:
            self.config['wallet']['address'] = wallet_address
            logger.info("✅ Wallet address configured")
            
            print("\nPrivate Key Setup:")
            print("For security, we'll store your private key as an environment variable.")
            print("The bot will read it from ARBITRAGE_WALLET_KEY environment variable.")
            print()
            
            setup_private_key = input("Set up private key now? (y/n): ").lower() == 'y'
            
            if setup_private_key:
                private_key = getpass.getpass("Enter your wallet private key (hidden input): ").strip()
                
                if private_key:
                    # Set environment variable for current session
                    os.environ['ARBITRAGE_WALLET_KEY'] = private_key
                    
                    # Instructions for permanent setup
                    print("\n✅ Private key set for current session.")
                    print("\nTo make this permanent, add this to your system environment variables:")
                    print(f"ARBITRAGE_WALLET_KEY={private_key[:10]}...")
                    print("\nWindows: Add to System Environment Variables")
                    print("Or create a .env file in your project directory")
                    
                    # Create .env file
                    env_file = Path(".env")
                    env_content = f"ARBITRAGE_WALLET_KEY={private_key}\n"
                    
                    if input("\nCreate .env file with private key? (y/n): ").lower() == 'y':
                        with open(env_file, 'w') as f:
                            f.write(env_content)
                        logger.info("✅ .env file created with private key")
        else:
            logger.warning("⚠️ Invalid wallet address format")
    
    def setup_trading_parameters(self):
        """Setup optimized trading parameters for revenue generation"""
        logger.info("⚙️ Setting up trading parameters...")
        
        print("\n" + "="*60)
        print("⚙️ TRADING PARAMETERS FOR REVENUE OPTIMIZATION")
        print("="*60)
        
        # Current settings
        current_min_profit = self.config['arbitrage_settings']['min_profit_threshold_usd']
        current_max_gas = self.config['arbitrage_settings']['max_gas_price_gwei']
        
        print(f"Current minimum profit threshold: ${current_min_profit}")
        print(f"Current maximum gas price: {current_max_gas} Gwei")
        print()
        
        # Optimize for real revenue
        print("RECOMMENDED SETTINGS FOR REAL REVENUE:")
        print("- Minimum profit: $5-10 (covers gas costs and provides profit)")
        print("- Maximum gas price: 100-200 Gwei (balance speed vs cost)")
        print("- Scan interval: 3-5 seconds (balance opportunity vs API limits)")
        print()
        
        # Update settings
        new_min_profit = input(f"Enter minimum profit threshold (current: ${current_min_profit}): ").strip()
        if new_min_profit:
            try:
                self.config['arbitrage_settings']['min_profit_threshold_usd'] = float(new_min_profit)
                logger.info(f"✅ Minimum profit threshold set to ${new_min_profit}")
            except ValueError:
                logger.warning("⚠️ Invalid profit threshold, keeping current value")
        
        new_max_gas = input(f"Enter maximum gas price in Gwei (current: {current_max_gas}): ").strip()
        if new_max_gas:
            try:
                self.config['arbitrage_settings']['max_gas_price_gwei'] = int(new_max_gas)
                logger.info(f"✅ Maximum gas price set to {new_max_gas} Gwei")
            except ValueError:
                logger.warning("⚠️ Invalid gas price, keeping current value")
        
        new_scan_interval = input("Enter scan interval in seconds (3-10 recommended): ").strip()
        if new_scan_interval:
            try:
                self.config['arbitrage_settings']['scan_interval_seconds'] = int(new_scan_interval)
                logger.info(f"✅ Scan interval set to {new_scan_interval} seconds")
            except ValueError:
                logger.warning("⚠️ Invalid scan interval, keeping current value")
        
        # Enable high-volume trading pairs
        print("\nOptimizing token pairs for maximum revenue...")
        high_volume_pairs = [
            {"name": "WETH/USDC", "enabled": True},
            {"name": "WMATIC/USDC", "enabled": True},
            {"name": "WBTC/USDC", "enabled": True},
            {"name": "WETH/USDT", "enabled": True}
        ]
        
        for i, pair in enumerate(self.config['token_pairs']):
            if pair['name'] in [hp['name'] for hp in high_volume_pairs]:
                self.config['token_pairs'][i]['enabled'] = True
                # Increase trade amounts for better profits
                if pair['name'] == 'WETH/USDC':
                    self.config['token_pairs'][i]['min_trade_amount'] = 1000
                    self.config['token_pairs'][i]['max_trade_amount'] = 50000
                elif pair['name'] == 'WMATIC/USDC':
                    self.config['token_pairs'][i]['min_trade_amount'] = 500
                    self.config['token_pairs'][i]['max_trade_amount'] = 25000
        
        logger.info("✅ Token pairs optimized for revenue generation")
    
    def verify_configuration(self) -> bool:
        """Verify configuration is ready for real revenue generation"""
        logger.info("🔍 Verifying configuration for real revenue generation...")
        
        issues: List[Dict[str, Any]] = []
        
        # Check API keys
        polygon_rpc = self.config['networks']['polygon']['rpc_url']
        if 'YOUR_API_KEY' in polygon_rpc:
            issues.append("❌ Polygon RPC still has placeholder API key")
        else:
            logger.info("✅ Polygon RPC configured with real API key")
        
        # Check wallet
        wallet_address = self.config['wallet']['address']
        if not wallet_address:
            issues.append("❌ Wallet address not configured")
        else:
            logger.info("✅ Wallet address configured")
        
        # Check private key environment variable
        private_key = os.environ.get('ARBITRAGE_WALLET_KEY')
        if not private_key:
            issues.append("❌ Private key environment variable not set")
        else:
            logger.info("✅ Private key environment variable configured")
        
        # Check enabled networks
        enabled_networks = [name for name, config in self.config['networks'].items() if config['enabled']]
        if not enabled_networks:
            issues.append("❌ No networks enabled")
        else:
            logger.info(f"✅ Enabled networks: {', '.join(enabled_networks)}")
        
        # Check enabled DEXes
        enabled_dexes = [name for name, config in self.config['dexes'].items() if config['enabled']]
        if len(enabled_dexes) < 2:
            issues.append("❌ Need at least 2 DEXes enabled for arbitrage")
        else:
            logger.info(f"✅ Enabled DEXes: {', '.join(enabled_dexes)}")
        
        # Check enabled token pairs
        enabled_pairs = [pair['name'] for pair in self.config['token_pairs'] if pair['enabled']]
        if not enabled_pairs:
            issues.append("❌ No token pairs enabled")
        else:
            logger.info(f"✅ Enabled token pairs: {', '.join(enabled_pairs)}")
        
        if issues:
            logger.error("❌ Configuration issues found:")
            for issue in issues:
                logger.error(f"  {issue}")
            return False
        else:
            logger.info("✅ Configuration ready for real revenue generation!")
            return True
    
    def test_api_connectivity(self) -> bool:
        """Test API connectivity to ensure real trading is possible"""
        logger.info("🔌 Testing API connectivity...")
        
        # Test Polygon RPC
        polygon_rpc = self.config['networks']['polygon']['rpc_url']
        
        try:
            # Simple RPC call to test connectivity
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }
            
            response = requests.post(polygon_rpc, json=payload, timeout=10)
            
            if response.status_code == 200:
                result: str = response.json()
                if 'result' in result:
                    block_number = int(result['result'], 16)
                    logger.info(f"✅ Polygon RPC connected - Latest block: {block_number}")
                    return True
                else:
                    logger.error(f"❌ RPC error: {result}")
                    return False
            else:
                logger.error(f"❌ HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def setup_complete_real_revenue_config(self):
        """Complete setup process for real revenue generation"""
        print("\n" + "="*80)
        print("🚀 COMPLETE SETUP FOR REAL REVENUE GENERATION")
        print("="*80)
        print("This wizard will configure your system for actual revenue generation.")
        print("Please have your API keys and wallet information ready.")
        print()
        
        # Step 1: API Keys
        print("STEP 1: API KEY SETUP")
        print("-" * 30)
        self.setup_real_api_keys()
        
        # Step 2: Wallet
        print("\nSTEP 2: WALLET SETUP")
        print("-" * 30)
        self.setup_wallet_configuration()
        
        # Step 3: Trading Parameters
        print("\nSTEP 3: TRADING PARAMETERS")
        print("-" * 30)
        self.setup_trading_parameters()
        
        # Step 4: Save Configuration
        print("\nSTEP 4: SAVE CONFIGURATION")
        print("-" * 30)
        self.save_config()
        
        # Step 5: Verification
        print("\nSTEP 5: VERIFICATION")
        print("-" * 30)
        config_valid = self.verify_configuration()
        api_connected = self.test_api_connectivity()
        
        if config_valid and api_connected:
            print("\n" + "="*80)
            print("🎉 SETUP COMPLETE! READY FOR REAL REVENUE GENERATION!")
            print("="*80)
            print("Your system is now configured for real revenue generation.")
            print("The bot will trade with real cryptocurrency and generate actual profits.")
            print()
            print("NEXT STEPS:")
            print("1. Ensure your wallet has enough ETH/MATIC for gas fees")
            print("2. Start with small trade amounts to test the system")
            print("3. Monitor the dashboard for real-time revenue tracking")
            print("4. Scale up trade amounts as you gain confidence")
            print()
            print("⚠️ IMPORTANT: Start with small amounts and monitor closely!")
            print("="*80)
            return True
        else:
            print("\n❌ Setup incomplete. Please fix the issues above and try again.")
            return False

def main():
    """Main function for configuration setup"""
    config_manager = RealRevenueConfigManager()
    
    print("🚀 Real Revenue Configuration Manager")
    print("====================================")
    print()
    print("Choose an option:")
    print("1. Complete setup for real revenue generation")
    print("2. Setup API keys only")
    print("3. Setup wallet only")
    print("4. Setup trading parameters only")
    print("5. Verify current configuration")
    print("6. Test API connectivity")
    print()
    
    choice = input("Enter your choice (1-6): ").strip()
    
    if choice == '1':
        config_manager.setup_complete_real_revenue_config()
    elif choice == '2':
        config_manager.setup_real_api_keys()
        config_manager.save_config()
    elif choice == '3':
        config_manager.setup_wallet_configuration()
        config_manager.save_config()
    elif choice == '4':
        config_manager.setup_trading_parameters()
        config_manager.save_config()
    elif choice == '5':
        config_manager.verify_configuration()
    elif choice == '6':
        config_manager.test_api_connectivity()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
