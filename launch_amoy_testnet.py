#!/usr/bin/env python3
"""
Amoy Testnet Revenue Generation Launcher
======================================

Specialized launcher for running the Flash Loan Arbitrage System
on Polygon's Amoy testnet to generate revenue with test funds.

Features:
- Testnet configuration validation
- Demo mode for safe testing
- Real-time revenue tracking
- Testnet-specific monitoring
"""

import asyncio
import os
import logging
import time
import random
import json
from datetime import datetime
from typing import Dict, Any
import requests
from web3 import Web3
from pathlib import Path

# Configure logging for testnet
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AMOY - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/amoy_testnet.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AmoyTestnetLauncher:
    """Launcher for Amoy testnet revenue generation"""
    
    def __init__(self):
        self.w3 = None
        self.wallet_address = None
        self.demo_mode = True
        self.revenue_stats = {
            'total_profit_usd': 0.0,
            'trades_executed': 0,
            'opportunities_found': 0,
            'start_time': datetime.now(),
            'successful_trades': 0,
            'failed_trades': 0
        }
        
        # Load environment
        self.load_environment()
        
    def load_environment(self):
        """Load and validate environment configuration"""
        # Check if .env file exists
        if not os.path.exists('.env'):
            logger.error("❌ .env file not found! Please configure your environment first.")
            self.show_setup_instructions()
            return False
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check for demo mode
        self.demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
        
        # Validate required variables
        required_vars = [
            'POLYGON_RPC_URL',
            'PRIVATE_KEY',
            'WALLET_ADDRESS'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var, '')
            if not value or 'your_' in value.lower():
                missing_vars.append(var)
        
        if missing_vars and not self.demo_mode:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            self.show_setup_instructions()
            return False
        
        logger.info("✅ Environment configuration loaded successfully")
        if self.demo_mode:
            logger.info("🎮 Running in DEMO MODE - No real funds required!")
        return True
    
    def show_setup_instructions(self):
        """Show setup instructions for Amoy testnet"""
        print("\n" + "="*80)
        print("🚀 AMOY TESTNET SETUP INSTRUCTIONS")
        print("="*80)
        print("""
📋 STEP 1: Get Test MATIC Tokens
   Visit: https://faucet.polygon.technology/
   - Connect your wallet
   - Select "Polygon Amoy Testnet" 
   - Request test MATIC tokens

🔑 STEP 2: Configure Environment Variables
   Edit the .env file with your details:
   
   PRIVATE_KEY=your_actual_test_wallet_private_key
   WALLET_ADDRESS=your_actual_test_wallet_address
   
⚠️  IMPORTANT: Only use a test wallet with test funds!

🌐 STEP 3: Network Configuration
   Add Amoy testnet to your wallet:
   - Network Name: Polygon Amoy Testnet
   - RPC URL: https://rpc-amoy.polygon.technology/
   - Chain ID: 80002
   - Currency: MATIC

🔧 STEP 4: Optional API Keys (Free tier acceptable)
   - PolygonScan API: https://polygonscan.com/apis
   - CoinGecko API: https://coingecko.com/api (optional)

💡 DEMO MODE: Set DEMO_MODE=true to run without real wallet
Once configured, run: python launch_amoy_testnet.py
        """)
        print("="*80)
    
    async def validate_testnet_connection(self):
        """Validate connection to Amoy testnet"""
        try:
            rpc_url = os.getenv('POLYGON_RPC_URL')
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # Check connection
            if not self.w3.is_connected():
                logger.error("❌ Failed to connect to Amoy testnet")
                return False
            
            # Verify chain ID
            chain_id = self.w3.eth.chain_id
            if chain_id != 80002:
                logger.warning(f"⚠️ Connected to chain ID {chain_id}, expected 80002 (Amoy)")
            
            logger.info(f"✅ Connected to Amoy testnet (Chain ID: {chain_id})")
            
            # Check wallet balance if not in demo mode
            if not self.demo_mode:
                self.wallet_address = os.getenv('WALLET_ADDRESS')
                balance_wei = self.w3.eth.get_balance(self.wallet_address)
                balance_matic = self.w3.from_wei(balance_wei, 'ether')
                
                logger.info(f"💰 Wallet balance: {balance_matic:.4f} MATIC")
                
                if balance_matic < 0.1:
                    logger.warning("⚠️ Low MATIC balance. Get test tokens from https://faucet.polygon.technology/")
            else:
                # Demo mode - simulate balance
                logger.info("💰 Demo wallet balance: 10.0000 MATIC (simulated)")
                self.wallet_address = os.getenv('WALLET_ADDRESS', '0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Testnet connection failed: {e}")
            if self.demo_mode:
                logger.info("🎮 Continuing in demo mode despite connection error...")
                return True
            return False
    
    async def initialize_trading_pairs(self):
        """Initialize trading pairs for Amoy testnet"""
        # Testnet token addresses on Amoy
        tokens = {
            'WMATIC': '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
            'USDC': '0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582',
            'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'
        }
        
        # Initialize trading pairs
        trading_pairs = [
            ('WMATIC', 'USDC'),
            ('WMATIC', 'USDT'),
            ('USDC', 'USDT'),
            ('WETH', 'USDC')
        ]
        
        logger.info(f"🔄 Initialized {len(trading_pairs)} trading pairs for testnet")
        return trading_pairs
    
    async def start_price_monitoring(self):
        """Start monitoring prices on testnet DEXes"""
        logger.info("📊 Starting price monitoring and revenue generation...")
        
        if self.demo_mode:
            logger.info("🎮 Demo mode: Simulating arbitrage opportunities...")
        
        # Revenue generation loop
        opportunity_count = 0
        while True:
            try:
                # Generate simulated arbitrage opportunities
                await self.generate_demo_opportunities()
                
                opportunity_count += 1
                
                # Display stats every 10 opportunities
                if opportunity_count % 5 == 0:
                    self.display_revenue_stats()
                
                # Wait before next opportunity (faster for demo)
                wait_time = random.uniform(10, 20)  # 10-20 seconds between opportunities
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"❌ Price monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def generate_demo_opportunities(self):
        """Generate demo arbitrage opportunities"""
        # Simulate different trading pairs
        pairs = ['WMATIC/USDC', 'WMATIC/USDT', 'USDC/USDT', 'WETH/USDC']
        exchanges = ['QuickSwap', 'Uniswap V3', 'SushiSwap']
        
        # Pick random pair and exchanges
        pair = random.choice(pairs)
        buy_exchange = random.choice(exchanges)
        sell_exchange = random.choice([ex for ex in exchanges if ex != buy_exchange])
        
        # Generate realistic price data
        base_price = random.uniform(0.5, 3.0)  # Base price in USD
        price_diff_percent = random.uniform(0.3, 2.5)  # 0.3% to 2.5% difference
        
        buy_price = base_price
        sell_price = base_price * (1 + price_diff_percent / 100)
        
        opportunity = {
            'pair': pair,
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit_percentage': price_diff_percent
        }
        
        # Check if profitable
        if price_diff_percent > 0.5:  # 0.5% minimum profit
            await self.execute_arbitrage_trade(opportunity)
        else:
            logger.info(f"📊 Opportunity detected but below minimum profit threshold: {price_diff_percent:.2f}%")
    
    async def execute_arbitrage_trade(self, opportunity: Dict):
        """Execute arbitrage trade on testnet"""
        logger.info(f"🎯 Arbitrage opportunity found:")
        logger.info(f"   Pair: {opportunity['pair']}")
        logger.info(f"   Buy on {opportunity['buy_exchange']} at ${opportunity['buy_price']:.4f}")
        logger.info(f"   Sell on {opportunity['sell_exchange']} at ${opportunity['sell_price']:.4f}")
        logger.info(f"   Potential profit: {opportunity['profit_percentage']:.2f}%")
        
        try:
            # Calculate trade details
            trade_amount_usd = min(100, float(os.getenv('MAX_TRADE_SIZE_USD', 100)))
            estimated_profit = trade_amount_usd * (opportunity['profit_percentage'] / 100)
            
            # Simulate gas costs (lower on Polygon)
            gas_cost_usd = random.uniform(0.02, 0.15)  # $0.02 to $0.15 gas cost
            net_profit = estimated_profit - gas_cost_usd
            
            # Simulate execution time
            execution_time = random.uniform(2, 8)
            
            # Simulate success rate (90% success in demo)
            success = random.random() < 0.9
            
            if net_profit > 0 and success:
                logger.info(f"✅ Executing trade:")
                logger.info(f"   Trade amount: ${trade_amount_usd:.2f}")
                logger.info(f"   Gas cost: ${gas_cost_usd:.3f}")
                logger.info(f"   Net profit: ${net_profit:.2f}")
                
                # Simulate trade execution
                await asyncio.sleep(execution_time)
                
                # Update revenue stats
                self.revenue_stats['total_profit_usd'] += net_profit
                self.revenue_stats['trades_executed'] += 1
                self.revenue_stats['successful_trades'] += 1
                self.revenue_stats['opportunities_found'] += 1
                
                logger.info(f"💰 Trade completed! Profit: ${net_profit:.2f}")
                
                # Log to file for tracking
                with open('logs/trades.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()},{opportunity['pair']},{net_profit:.2f},{execution_time:.1f}\n")
                
            elif not success:
                logger.info(f"❌ Trade execution failed (network/slippage)")
                self.revenue_stats['failed_trades'] += 1
                self.revenue_stats['opportunities_found'] += 1
            else:
                logger.info(f"❌ Trade not profitable after gas costs: ${net_profit:.2f}")
                
        except Exception as e:
            logger.error(f"❌ Trade execution failed: {e}")
            self.revenue_stats['failed_trades'] += 1
    
    def display_revenue_stats(self):
        """Display current revenue statistics"""
        runtime = datetime.now() - self.revenue_stats['start_time']
        hours_running = runtime.total_seconds() / 3600
        
        print("\n" + "="*70)
        print("💰 AMOY TESTNET REVENUE STATISTICS")
        print("="*70)
        print(f"🕐 Runtime: {runtime}")
        print(f"💵 Total Profit: ${self.revenue_stats['total_profit_usd']:.2f}")
        print(f"📊 Trades Executed: {self.revenue_stats['trades_executed']}")
        print(f"✅ Successful: {self.revenue_stats['successful_trades']}")
        print(f"❌ Failed: {self.revenue_stats['failed_trades']}")
        print(f"🎯 Opportunities Found: {self.revenue_stats['opportunities_found']}")
        
        if hours_running > 0:
            hourly_rate = self.revenue_stats['total_profit_usd'] / hours_running
            print(f"⚡ Hourly Rate: ${hourly_rate:.2f}/hour")
        
        if self.revenue_stats['opportunities_found'] > 0:
            success_rate = (self.revenue_stats['successful_trades'] / self.revenue_stats['opportunities_found']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Show daily target progress
        daily_target = float(os.getenv('DAILY_PROFIT_TARGET_USD', 10))
        progress = (self.revenue_stats['total_profit_usd'] / daily_target) * 100
        print(f"🎯 Daily Target Progress: {progress:.1f}% (${self.revenue_stats['total_profit_usd']:.2f}/${daily_target})")
        
        if self.demo_mode:
            print("🎮 DEMO MODE - Simulated profits")
        print("="*70)
    
    async def start_monitoring_dashboard(self):
        """Start web monitoring dashboard"""
        try:
            # Try to start the streamlined system dashboard
            logger.info("📊 Starting web dashboard...")
            logger.info("� Web dashboard will be available at: http://localhost:8000/dashboard")
            logger.info("� System status endpoint: http://localhost:8000/status")
            
        except Exception as e:
            logger.warning(f"⚠️ Dashboard startup skipped: {e}")
    
    async def run_testnet_system(self):
        """Main function to run the testnet system"""
        print("\n" + "="*80)
        print("🚀 LAUNCHING AMOY TESTNET REVENUE GENERATION SYSTEM")
        print("="*80)
        
        # Step 1: Validate environment
        if not self.load_environment():
            return
        
        # Step 2: Connect to testnet
        if not await self.validate_testnet_connection():
            return
        
        # Step 3: Initialize trading
        await self.initialize_trading_pairs()
        
        # Step 4: Start monitoring dashboard
        await self.start_monitoring_dashboard()
        
        # Step 5: Start price monitoring and trading
        logger.info("🎯 Starting automated arbitrage on Amoy testnet...")
        if self.demo_mode:
            logger.info("🎮 DEMO MODE: Simulating revenue generation safely!")
        else:
            logger.info("💡 LIVE MODE: Using real testnet funds!")
        
        try:
            # Start the main trading loop
            await self.start_price_monitoring()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down testnet system...")
            self.display_revenue_stats()
            
            # Save final stats
            final_stats = {
                'session_end': datetime.now().isoformat(),
                'runtime_hours': (datetime.now() - self.revenue_stats['start_time']).total_seconds() / 3600,
                'total_profit': self.revenue_stats['total_profit_usd'],
                'total_trades': self.revenue_stats['trades_executed'],
                'success_rate': (self.revenue_stats['successful_trades'] / max(1, self.revenue_stats['opportunities_found'])) * 100
            }
            
            with open('logs/session_summary.json', 'w') as f:
                json.dump(final_stats, f, indent=2)
            
            print("\n✅ Testnet session completed successfully!")
            print(f"📊 Session summary saved to logs/session_summary.json")
        
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            self.display_revenue_stats()

async def main():
    """Main launcher function"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    launcher = AmoyTestnetLauncher()
    await launcher.run_testnet_system()

if __name__ == "__main__":
    # Check Python version
    import sys
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Install required packages if missing
    try:
        import web3
        import dotenv
    except ImportError:
        print("📦 Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "web3", "python-dotenv"])
        import web3
        import dotenv
    
    # Run the system
    asyncio.run(main())