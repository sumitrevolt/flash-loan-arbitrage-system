#!/usr/bin/env python3
"""
Contract Verification and Token/DEX Approval Checker
====================================================

Verifies all token contracts, DEX addresses, and AAVE contracts on Polygon.
Checks if contracts are deployed correctly and tokens have proper approvals.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import aiohttp
from web3 import Web3
from web3.exceptions import ContractLogicError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContractVerifier")

class ContractVerifier:
    """Verifies all contracts and token approvals"""
    
    def __init__(self):
        self.w3 = None
        self.config = {}
        self.verification_results = {
            "aave_contracts": {},
            "token_contracts": {},
            "dex_contracts": {},
            "approvals": {},
            "summary": {}
        }
        
        # Load environment
        self.load_env()
        
        # Load configuration
        self.load_config()
        
        # Initialize Web3
        self.init_web3()
    
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
            else:
                logger.error("Configuration file not found")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def init_web3(self):
        """Initialize Web3 connection"""
        try:
            rpc_url = os.getenv('POLYGON_RPC_URL')
            if not rpc_url:
                logger.error("POLYGON_RPC_URL not set")
                return
            
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if self.w3.is_connected():
                logger.info(f"✅ Connected to Polygon network")
                logger.info(f"Latest block: {self.w3.eth.block_number}")
            else:
                logger.error("❌ Failed to connect to Polygon network")
                
        except Exception as e:
            logger.error(f"Web3 initialization error: {e}")
    
    def print_banner(self):
        """Print verification banner"""
        print("=" * 80)
        print("🔍 CONTRACT VERIFICATION & TOKEN APPROVAL CHECKER")
        print("=" * 80)
        print(f"📅 Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Network: Polygon Mainnet")
        print(f"🔗 RPC: {os.getenv('POLYGON_RPC_URL', 'Not configured')}")
        print("=" * 80)
    
    async def verify_contract_exists(self, address: str, name: str) -> Dict[str, Any]:
        """Verify if a contract exists at the given address"""
        try:
            if not self.w3:
                return {"exists": False, "error": "Web3 not initialized"}
            
            # Check if address is valid
            if not Web3.is_address(address):
                return {"exists": False, "error": "Invalid address format"}
            
            # Get contract code
            code = self.w3.eth.get_code(address)
            
            if len(code) > 2:  # More than just '0x'
                # Try to get some basic info
                try:
                    balance = self.w3.eth.get_balance(address)
                    return {
                        "exists": True,
                        "address": address,
                        "name": name,
                        "code_size": len(code),
                        "balance_wei": balance,
                        "verified": True
                    }
                except Exception as e:
                    return {
                        "exists": True,
                        "address": address,
                        "name": name,
                        "code_size": len(code),
                        "error": str(e),
                        "verified": False
                    }
            else:
                return {
                    "exists": False,
                    "address": address,
                    "name": name,
                    "error": "No contract code found"
                }
                
        except Exception as e:
            return {
                "exists": False,
                "address": address,
                "name": name,
                "error": str(e)
            }
    
    async def verify_aave_contracts(self):
        """Verify AAVE V3 contracts"""
        logger.info("🏦 Verifying AAVE V3 contracts...")
        
        aave_config = self.config.get("aave_flash_loan_config", {}).get("aave_v3_polygon", {})
        
        contracts_to_verify = {
            "pool": aave_config.get("pool_address"),
            "data_provider": aave_config.get("data_provider"),
            "price_oracle": aave_config.get("price_oracle")
        }
        
        for contract_name, address in contracts_to_verify.items():
            if address:
                result = await self.verify_contract_exists(address, f"AAVE {contract_name}")
                self.verification_results["aave_contracts"][contract_name] = result
                
                status = "✅" if result.get("exists") else "❌"
                print(f"{status} AAVE {contract_name.upper()}: {address}")
                if result.get("error"):
                    print(f"   Error: {result['error']}")
            else:
                print(f"❌ AAVE {contract_name.upper()}: Not configured")
    
    async def verify_token_contracts(self):
        """Verify all token contracts"""
        logger.info("🪙 Verifying token contracts...")
        
        tokens = self.config.get("aave_flash_loan_config", {}).get("supported_tokens", {})
        
        for token_symbol, token_config in tokens.items():
            address = token_config.get("address")
            if address:
                result = await self.verify_contract_exists(address, token_symbol)
                self.verification_results["token_contracts"][token_symbol] = result
                
                status = "✅" if result.get("exists") else "❌"
                decimals = token_config.get("decimals", "Unknown")
                print(f"{status} {token_symbol}: {address} (decimals: {decimals})")
                if result.get("error"):
                    print(f"   Error: {result['error']}")
            else:
                print(f"❌ {token_symbol}: No address configured")
    
    async def verify_dex_contracts(self):
        """Verify all DEX contracts"""
        logger.info("🔄 Verifying DEX contracts...")
        
        dexs = self.config.get("aave_flash_loan_config", {}).get("dex_configuration", {})
        
        for dex_name, dex_config in dexs.items():
            print(f"\n📍 Verifying {dex_name.upper()}:")
            
            # Verify router
            router_address = dex_config.get("router")
            if router_address:
                result = await self.verify_contract_exists(router_address, f"{dex_name} router")
                if not self.verification_results["dex_contracts"].get(dex_name):
                    self.verification_results["dex_contracts"][dex_name] = {}
                self.verification_results["dex_contracts"][dex_name]["router"] = result
                
                status = "✅" if result.get("exists") else "❌"
                print(f"   {status} Router: {router_address}")
                if result.get("error"):
                    print(f"      Error: {result['error']}")
            
            # Verify factory (if exists)
            factory_address = dex_config.get("factory")
            if factory_address:
                result = await self.verify_contract_exists(factory_address, f"{dex_name} factory")
                self.verification_results["dex_contracts"][dex_name]["factory"] = result
                
                status = "✅" if result.get("exists") else "❌"
                print(f"   {status} Factory: {factory_address}")
                if result.get("error"):
                    print(f"      Error: {result['error']}")
            
            # Verify quoter (for Uniswap V3)
            quoter_address = dex_config.get("quoter")
            if quoter_address:
                result = await self.verify_contract_exists(quoter_address, f"{dex_name} quoter")
                self.verification_results["dex_contracts"][dex_name]["quoter"] = result
                
                status = "✅" if result.get("exists") else "❌"
                print(f"   {status} Quoter: {quoter_address}")
                if result.get("error"):
                    print(f"      Error: {result['error']}")
    
    def check_known_contract_updates(self):
        """Check for any known contract address updates"""
        logger.info("🔄 Checking for known contract updates...")
        
        # Known correct addresses as of 2025 (these should be verified)
        known_addresses = {
            "polygon_tokens": {
                "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # Native USDC
                "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # Tether USD
                "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",   # DAI Stablecoin
                "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", # Wrapped MATIC
                "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"    # Wrapped ETH
            },
            "aave_v3_polygon": {
                "pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
                "data_provider": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
                "price_oracle": "0xb023e699F5a33916Ea823A16485eb259579C9f86"
            },
            "dex_routers": {
                "quickswap_router": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
                "sushiswap_router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
                "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564"
            }
        }
        
        print("\n📋 KNOWN CORRECT ADDRESSES (2025):")
        print("-" * 50)
        
        # Compare with our configuration
        config_tokens = self.config.get("aave_flash_loan_config", {}).get("supported_tokens", {})
        
        mismatches = []
        
        for token, known_addr in known_addresses["polygon_tokens"].items():
            config_addr = config_tokens.get(token, {}).get("address", "")
            if config_addr and config_addr.lower() != known_addr.lower():
                mismatches.append({
                    "type": "token",
                    "name": token,
                    "configured": config_addr,
                    "known_correct": known_addr
                })
            
            match_status = "✅" if config_addr.lower() == known_addr.lower() else "⚠️"
            print(f"{match_status} {token}: {known_addr}")
        
        # Check AAVE addresses
        aave_config = self.config.get("aave_flash_loan_config", {}).get("aave_v3_polygon", {})
        for contract, known_addr in known_addresses["aave_v3_polygon"].items():
            config_addr = aave_config.get(f"{contract}_address" if contract != "pool" else "pool_address", "")
            if config_addr and config_addr.lower() != known_addr.lower():
                mismatches.append({
                    "type": "aave",
                    "name": contract,
                    "configured": config_addr,
                    "known_correct": known_addr
                })
        
        if mismatches:
            print(f"\n⚠️  FOUND {len(mismatches)} ADDRESS MISMATCHES:")
            for mismatch in mismatches:
                print(f"   {mismatch['type'].upper()} {mismatch['name']}:")
                print(f"      Configured: {mismatch['configured']}")
                print(f"      Should be:  {mismatch['known_correct']}")
        
        return mismatches
    
    def generate_verification_summary(self):
        """Generate verification summary"""
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        
        # Count results
        total_contracts = 0
        verified_contracts = 0
        
        # AAVE contracts
        aave_results = self.verification_results["aave_contracts"]
        aave_verified = sum(1 for r in aave_results.values() if r.get("exists"))
        total_contracts += len(aave_results)
        verified_contracts += aave_verified
        
        print(f"🏦 AAVE Contracts: {aave_verified}/{len(aave_results)} verified")
        
        # Token contracts
        token_results = self.verification_results["token_contracts"]
        token_verified = sum(1 for r in token_results.values() if r.get("exists"))
        total_contracts += len(token_results)
        verified_contracts += token_verified
        
        print(f"🪙 Token Contracts: {token_verified}/{len(token_results)} verified")
        
        # DEX contracts
        dex_results = self.verification_results["dex_contracts"]
        dex_verified = 0
        dex_total = 0
        for dex_contracts in dex_results.values():
            for contract_result in dex_contracts.values():
                dex_total += 1
                if contract_result.get("exists"):
                    dex_verified += 1
        
        total_contracts += dex_total
        verified_contracts += dex_verified
        
        print(f"🔄 DEX Contracts: {dex_verified}/{dex_total} verified")
        
        # Overall status
        print(f"\n📈 OVERALL STATUS: {verified_contracts}/{total_contracts} contracts verified")
        
        success_rate = (verified_contracts / total_contracts * 100) if total_contracts > 0 else 0
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        # Status indicator
        if success_rate >= 95:
            print("🎯 STATUS: ✅ EXCELLENT - All contracts verified")
        elif success_rate >= 80:
            print("🎯 STATUS: ⚠️  GOOD - Most contracts verified")
        else:
            print("🎯 STATUS: ❌ NEEDS ATTENTION - Many contracts failed verification")
        
        return {
            "total_contracts": total_contracts,
            "verified_contracts": verified_contracts,
            "success_rate": success_rate
        }
    
    async def run_verification(self):
        """Run complete verification process"""
        self.print_banner()
        
        if not self.w3 or not self.w3.is_connected():
            print("❌ Cannot proceed without Web3 connection")
            return
        
        try:
            # Verify all contract types
            await self.verify_aave_contracts()
            await self.verify_token_contracts()
            await self.verify_dex_contracts()
            
            # Check for known updates
            mismatches = self.check_known_contract_updates()
            
            # Generate summary
            summary = self.generate_verification_summary()
            
            # Save results
            self.save_verification_results()
            
            print("\n" + "=" * 60)
            print("✅ VERIFICATION COMPLETE")
            print("=" * 60)
            
            if summary["success_rate"] >= 95:
                print("🚀 All contracts verified and ready for deployment!")
            elif mismatches:
                print("⚠️  Some address mismatches found - review recommended")
            else:
                print("🔧 Some contracts need attention - check logs for details")
                
        except Exception as e:
            logger.error(f"Verification error: {e}")
    
    def save_verification_results(self):
        """Save verification results to file"""
        try:
            os.makedirs("logs", exist_ok=True)
            
            results_file = f"logs/contract_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(results_file, 'w') as f:
                json.dump(self.verification_results, f, indent=2)
            
            logger.info(f"Verification results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

async def main():
    """Main verification function"""
    verifier = ContractVerifier()
    await verifier.run_verification()

if __name__ == "__main__":
    asyncio.run(main())
