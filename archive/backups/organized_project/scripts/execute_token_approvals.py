#!/usr/bin/env python3
"""
Token Approval Execution System for Live Trading
================================================

Executes the 20 required token approvals for AAVE flash loan live trading mode.
This script prepares your wallet for profit-targeted arbitrage operations.

SAFETY FEATURES:
- Simulation mode by default
- Transaction preview before execution
- Gas estimation and optimization
- Comprehensive error handling
- Progress tracking and logging

REQUIRED APPROVALS:
- 5 tokens × 4 contracts = 20 total approvals
- USDC, USDT, DAI, WMATIC, WETH
- AAVE Pool + QuickSwap + SushiSwap + Uniswap V3
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from web3 import Web3
from web3.exceptions import TransactionNotFound
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/approval_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TokenApprovalExecutor")

class TokenApprovalExecutor:
    """Executes token approvals for live trading"""
    
    def __init__(self):
        self.w3 = None
        self.account = None
        self.config = {}
        self.approvals = []
        
        # ERC20 approve function signature
        self.approve_signature = "0x095ea7b3"  # approve(address,uint256)
        self.max_uint256 = "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        
        # Execution settings
        self.simulation_mode = True  # Start in simulation mode for safety
        self.gas_multiplier = 1.2    # Add 20% buffer to gas estimates
        self.max_gas_price_gwei = 100  # Maximum gas price
        
        # Load configuration and initialize
        self.load_env()
        self.load_config()
        self.init_web3()
        self.prepare_approvals()
    
    def load_env(self):
        """Load environment variables"""
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    def load_config(self):
        """Load AAVE configuration"""
        try:
            config_path = Path("config/aave_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def init_web3(self):
        """Initialize Web3 connection"""
        try:
            rpc_url = os.getenv('POLYGON_RPC_URL')
            if not rpc_url:
                logger.error("POLYGON_RPC_URL not configured")
                return
            
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if self.w3.is_connected():
                logger.info(f"Connected to Polygon network (Block: {self.w3.eth.block_number})")
                
                # Try to load account if private key is available
                private_key = os.getenv('PRIVATE_KEY')
                if private_key:
                    self.account = self.w3.eth.account.from_key(private_key)
                    logger.info(f"Wallet loaded: {self.account.address}")
                else:
                    logger.warning("PRIVATE_KEY not set - simulation mode only")
            else:
                logger.error("Failed to connect to Polygon network")
                
        except Exception as e:
            logger.error(f"Web3 initialization error: {e}")
    
    def prepare_approvals(self):
        """Prepare all required approval transactions"""
        if not self.config:
            logger.error("Configuration not loaded")
            return
        
        config = self.config.get("aave_flash_loan_config", {})
        tokens = config.get("supported_tokens", {})
        dexs = config.get("dex_configuration", {})
        aave_pool = config.get("aave_v3_polygon", {}).get("pool_address")
        
        self.approvals = []
        
        # Prepare spenders list
        spenders = []
        
        # Add AAVE pool
        if aave_pool:
            spenders.append({
                "address": aave_pool,
                "name": "AAVE V3 Pool",
                "purpose": "Flash loan repayment"
            })
        
        # Add DEX routers
        for dex_name, dex_config in dexs.items():
            if dex_config.get("enabled", True):
                router = dex_config.get("router")
                if router:
                    spenders.append({
                        "address": router,
                        "name": f"{dex_name.upper()} Router",
                        "purpose": "DEX trading"
                    })
        
        # Create approval transactions for each token-spender combination
        approval_id = 1
        for token_symbol, token_config in tokens.items():
            token_address = token_config.get("address")
            if token_address:
                for spender in spenders:
                    approval = {
                        "id": approval_id,
                        "token_symbol": token_symbol,
                        "token_address": token_address,
                        "spender_address": spender["address"],
                        "spender_name": spender["name"],
                        "purpose": spender["purpose"],
                        "amount": self.max_uint256,
                        "status": "pending",
                        "gas_estimate": None,
                        "transaction_hash": None
                    }
                    self.approvals.append(approval)
                    approval_id += 1
        
        logger.info(f"Prepared {len(self.approvals)} approval transactions")
    
    def print_approval_summary(self):
        """Print summary of all approvals"""
        print("=" * 80)
        print("🔐 TOKEN APPROVAL EXECUTION FOR LIVE TRADING")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Network: Polygon Mainnet")
        print(f"👛 Wallet: {self.account.address if self.account else 'Not loaded'}")
        print(f"⚙️  Mode: {'🔴 LIVE' if not self.simulation_mode else '🟡 SIMULATION'}")
        print(f"📊 Total Approvals: {len(self.approvals)}")
        print()
        
        # Group by token
        tokens = {}
        for approval in self.approvals:
            token = approval["token_symbol"]
            if token not in tokens:
                tokens[token] = []
            tokens[token].append(approval)
        
        print("📋 APPROVAL BREAKDOWN:")
        print("-" * 50)
        
        for token_symbol, token_approvals in tokens.items():
            print(f"\n🪙 {token_symbol} ({len(token_approvals)} approvals):")
            for approval in token_approvals:
                print(f"   {approval['id']:2d}. {approval['spender_name']}")
                print(f"       Purpose: {approval['purpose']}")
                print(f"       Contract: {approval['spender_address']}")
        
        print(f"\n💰 COST ESTIMATION:")
        print(f"   Gas per approval: ~100,000")
        print(f"   Total gas needed: ~{len(self.approvals) * 100000:,}")
        
        current_gas_price = self.get_current_gas_price()
        if current_gas_price:
            total_cost_matic = (len(self.approvals) * 100000 * current_gas_price) / 10**18
            print(f"   Current gas price: {current_gas_price / 10**9:.1f} gwei")
            print(f"   Estimated cost: ~{total_cost_matic:.4f} MATIC")
    
    def get_current_gas_price(self) -> Optional[int]:
        """Get current gas price from network"""
        try:
            if self.w3:
                return self.w3.eth.gas_price
        except Exception as e:
            logger.warning(f"Failed to get gas price: {e}")
        return None
    
    def estimate_approval_gas(self, approval: Dict[str, Any]) -> Optional[int]:
        """Estimate gas for an approval transaction"""
        try:
            if not self.w3 or not self.account:
                return 100000  # Default estimate
            
            # Build transaction for estimation
            transaction = {
                'to': approval['token_address'],
                'data': self.build_approval_data(approval['spender_address']),
                'from': self.account.address,
                'value': 0
            }
            
            # Estimate gas
            gas_estimate = self.w3.eth.estimate_gas(transaction)
            
            # Add buffer
            buffered_gas = int(gas_estimate * self.gas_multiplier)
            
            return buffered_gas
            
        except Exception as e:
            logger.warning(f"Gas estimation failed for {approval['token_symbol']}: {e}")
            return 100000  # Fallback estimate
    
    def build_approval_data(self, spender_address: str) -> str:
        """Build approval transaction data"""
        # Remove 0x prefix from spender address and pad to 32 bytes
        spender_hex = spender_address[2:].lower().zfill(64)
        
        # Combine: function signature + spender + amount
        return f"{self.approve_signature}{spender_hex}{self.max_uint256[2:]}"
    
    async def simulate_approval(self, approval: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate an approval transaction"""
        try:
            # Estimate gas
            gas_estimate = self.estimate_approval_gas(approval)
            approval["gas_estimate"] = gas_estimate
            
            # Get current gas price
            gas_price = self.get_current_gas_price()
            
            # Calculate cost
            cost_wei = (gas_estimate * gas_price) if gas_price else 0
            cost_matic = cost_wei / 10**18 if cost_wei else 0
            
            return {
                "success": True,
                "gas_estimate": gas_estimate,
                "gas_price_gwei": gas_price / 10**9 if gas_price else 0,
                "cost_matic": cost_matic,
                "transaction_data": self.build_approval_data(approval["spender_address"])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_approval(self, approval: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a real approval transaction"""
        try:
            if not self.account:
                raise ValueError("No wallet loaded for execution")
            
            # Get current gas price
            gas_price = self.get_current_gas_price()
            if not gas_price:
                raise ValueError("Could not get gas price")
            
            # Check if gas price is reasonable
            gas_price_gwei = gas_price / 10**9
            if gas_price_gwei > self.max_gas_price_gwei:
                raise ValueError(f"Gas price too high: {gas_price_gwei:.1f} gwei")
            
            # Estimate gas
            gas_estimate = self.estimate_approval_gas(approval)
            
            # Build transaction
            transaction = {
                'to': approval['token_address'],
                'data': self.build_approval_data(approval['spender_address']),
                'value': 0,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            }
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, os.getenv('PRIVATE_KEY'))
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Approval sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                "success": receipt.status == 1,
                "transaction_hash": tx_hash.hex(),
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "effective_gas_price": receipt.get('effectiveGasPrice', gas_price)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_simulation(self):
        """Run approval simulation"""
        print("\n🧪 RUNNING APPROVAL SIMULATION")
        print("=" * 50)
        
        total_gas = 0
        total_cost = 0.0
        successful_simulations = 0
        
        for i, approval in enumerate(self.approvals):
            print(f"\n{i+1:2d}/{len(self.approvals)} Simulating {approval['token_symbol']} → {approval['spender_name']}")
            
            result = await self.simulate_approval(approval)
            
            if result["success"]:
                gas = result["gas_estimate"]
                cost = result["cost_matic"]
                
                print(f"     ✅ Gas: {gas:,}, Cost: {cost:.6f} MATIC")
                
                total_gas += gas
                total_cost += cost
                successful_simulations += 1
            else:
                print(f"     ❌ Simulation failed: {result['error']}")
        
        print(f"\n📊 SIMULATION SUMMARY:")
        print(f"   Successful: {successful_simulations}/{len(self.approvals)}")
        print(f"   Total Gas: {total_gas:,}")
        print(f"   Total Cost: {total_cost:.6f} MATIC")
        
        if successful_simulations == len(self.approvals):
            print("   🎯 All simulations passed - ready for execution!")
        else:
            print("   ⚠️  Some simulations failed - check errors above")
    
    async def execute_all_approvals(self):
        """Execute all approval transactions"""
        if self.simulation_mode:
            print("❌ Cannot execute in simulation mode")
            print("   Set simulation_mode = False to enable live execution")
            return
        
        print("\n🔴 EXECUTING LIVE APPROVAL TRANSACTIONS")
        print("=" * 50)
        print("⚠️  WARNING: This will execute real transactions with real fees!")
        
        response = input("\nProceed with live execution? (type 'YES' to confirm): ")
        if response != 'YES':
            print("Execution cancelled.")
            return
        
        successful_approvals = 0
        failed_approvals = 0
        total_gas_used = 0
        total_cost = 0.0
        
        for i, approval in enumerate(self.approvals):
            print(f"\n{i+1:2d}/{len(self.approvals)} Executing {approval['token_symbol']} → {approval['spender_name']}")
            
            result = await self.execute_approval(approval)
            
            if result["success"]:
                gas_used = result["gas_used"]
                gas_price = result["effective_gas_price"]
                cost = (gas_used * gas_price) / 10**18
                
                print(f"     ✅ Transaction: {result['transaction_hash']}")
                print(f"     📊 Gas used: {gas_used:,}, Cost: {cost:.6f} MATIC")
                
                approval["status"] = "confirmed"
                approval["transaction_hash"] = result["transaction_hash"]
                
                successful_approvals += 1
                total_gas_used += gas_used
                total_cost += cost
            else:
                print(f"     ❌ Failed: {result['error']}")
                approval["status"] = "failed"
                failed_approvals += 1
            
            # Small delay between transactions
            if i < len(self.approvals) - 1:
                print("     ⏳ Waiting 2 seconds...")
                await asyncio.sleep(2)
        
        print(f"\n🎯 EXECUTION COMPLETE")
        print("=" * 30)
        print(f"✅ Successful: {successful_approvals}")
        print(f"❌ Failed: {failed_approvals}")
        print(f"⛽ Total gas used: {total_gas_used:,}")
        print(f"💰 Total cost: {total_cost:.6f} MATIC")
        
        if successful_approvals == len(self.approvals):
            print("\n🚀 ALL APPROVALS COMPLETE - LIVE TRADING ENABLED!")
            self.save_approval_results()
        else:
            print(f"\n⚠️  {failed_approvals} approvals failed - review and retry")
    
    def save_approval_results(self):
        """Save approval results to file"""
        try:
            os.makedirs("logs", exist_ok=True)
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "wallet_address": self.account.address if self.account else None,
                "total_approvals": len(self.approvals),
                "successful_approvals": sum(1 for a in self.approvals if a["status"] == "confirmed"),
                "approvals": self.approvals
            }
            
            results_file = f"logs/approval_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Approval results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    async def run(self):
        """Main execution function"""
        if not self.w3 or not self.w3.is_connected():
            print("❌ Web3 connection required")
            return
        
        if not self.approvals:
            print("❌ No approvals prepared")
            return
        
        # Print summary
        self.print_approval_summary()
        
        # Run simulation
        await self.run_simulation()
        
        # Ask user what to do next
        print("\n🎯 NEXT STEPS:")
        print("1. Review simulation results above")
        print("2. Fund wallet with MATIC for gas fees")
        print("3. Set PRIVATE_KEY environment variable")
        print("4. Set simulation_mode = False for live execution")
        print("5. Re-run this script to execute approvals")
        
        if not self.simulation_mode and self.account:
            await self.execute_all_approvals()

async def main():
    """Main function"""
    print("=" * 80)
    print("🔐 TOKEN APPROVAL SYSTEM FOR AAVE FLASH LOAN LIVE TRADING")
    print("=" * 80)
    
    executor = TokenApprovalExecutor()
    await executor.run()

if __name__ == "__main__":
    asyncio.run(main())
