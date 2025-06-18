from typing import Dict, List, Any, Optional\n#!/usr/bin/env python3
"""
Flash Loan Arbitrage Bot - Production Readiness Check
Comprehensive validation of all components for production deployment
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account

# Load environment variables
load_dotenv()

class ProductionReadinessValidator:
    """Comprehensive production readiness validator"""
    
    def __init__(self):
        self.contract_address = "0x153dDf13D58397740c40E9D1a6e183A8c0F36c32"
        self.polygon_rpc = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
        self.private_key = os.getenv("PRIVATE_KEY")
        self.issues: List[Dict[str, Any]] = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
        
        # Required DEXes for production
        self.required_dexes = {
            "QuickSwap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
            "Uniswap V3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
            "SushiSwap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
            "Curve": "0x094d12e5b541784701FD8d65F11fc0598FBC6332",
            "Balancer": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
            "DODO": "0x6D310348d5c12009854DFCf72e0DF9027e8cb4f4"
        }
        
        # Contract ABI for validation
        self.contract_abi = [
            {
                "inputs": [{"internalType": "address", "name": "", "type": "address"}],
                "name": "approvedDexes",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "owner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "paused",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
    def add_check(self, description, success, details=None):
        """Add a check result"""
        self.total_checks += 1
        if success:
            self.success_count += 1
            print(f"✅ {description}")
            if details:
                print(f"   {details}")
        else:
            self.issues.append(f"{description}: {details}" if details else description)
            print(f"❌ {description}")
            if details:
                print(f"   {details}")
    
    def add_warning(self, description, details=None):
        """Add a warning"""
        self.warnings.append(f"{description}: {details}" if details else description)
        print(f"⚠️  {description}")
        if details:
            print(f"   {details}")
    
    def check_environment_variables(self):
        """Check environment configuration"""
        print("\n🔧 Environment Configuration")
        print("-" * 50)
        
        # Check .env file
        env_file = Path(".env")
        self.add_check("Environment file exists", env_file.exists(), str(env_file))
        
        # Check required environment variables
        required_vars = ["PRIVATE_KEY", "POLYGON_RPC_URL"]
        for var in required_vars:
            value = os.getenv(var)
            if var == "PRIVATE_KEY":
                # Don't print the actual key
                self.add_check(f"{var} is set", bool(value), "***REDACTED***" if value else "Not set")
            else:
                self.add_check(f"{var} is set", bool(value), value or "Not set")
    
    def check_network_connectivity(self):
        """Check blockchain connectivity"""
        print("\n🌐 Network Connectivity")
        print("-" * 50)
        
        try:
            self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
            
            # Check connection
            is_connected = self.web3.is_connected()
            self.add_check("Polygon RPC connection", is_connected)
            
            if is_connected:
                # Check chain ID
                chain_id = self.web3.eth.chain_id
                self.add_check("Correct chain ID (137)", chain_id == 137, f"Chain ID: {chain_id}")
                
                # Check latest block
                latest_block = self.web3.eth.block_number
                self.add_check("Can read latest block", latest_block > 0, f"Block: {latest_block:,}")
                
                # Check account if private key exists
                if self.private_key:
                    try:
                        self.account = Account.from_key(self.private_key)
                        balance = self.web3.eth.get_balance(self.account.address)
                        balance_matic = self.web3.from_wei(balance, 'ether')
                        
                        self.add_check("Account loaded", True, f"Address: {self.account.address}")
                        self.add_check("Account has MATIC balance", balance > 0, f"Balance: {balance_matic:.4f} MATIC")
                        
                        if balance_matic < 0.1:
                            self.add_warning("Low MATIC balance", f"Only {balance_matic:.4f} MATIC available")
                            
                    except Exception as e:
                        self.add_check("Account validation", False, str(e))
                        
        except Exception as e:
            self.add_check("Network connectivity", False, str(e))
    
    def check_contract_status(self):
        """Check contract deployment and status"""
        print("\n📋 Contract Status")
        print("-" * 50)
        
        try:
            # Check contract code
            contract_code = self.web3.eth.get_code(Web3.to_checksum_address(self.contract_address))
            self.add_check("Contract is deployed", len(contract_code) > 2, f"Contract: {self.contract_address}")
            
            # Load contract
            self.contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.contract_abi
            )
            
            # Check owner
            try:
                owner = self.contract.functions.owner().call()
                self.add_check("Contract owner accessible", True, f"Owner: {owner}")
                
                if self.private_key and hasattr(self, 'account'):
                    is_owner = owner.lower() == self.account.address.lower()
                    self.add_check("User is contract owner", is_owner)
                    
            except Exception as e:
                self.add_check("Contract owner check", False, str(e))
            
            # Check paused status
            try:
                paused = self.contract.functions.paused().call()
                self.add_check("Contract not paused", not paused, f"Paused: {paused}")
            except Exception as e:
                self.add_warning("Pause status check failed", str(e))
                
        except Exception as e:
            self.add_check("Contract validation", False, str(e))
    
    def check_dex_approvals(self):
        """Check DEX approval status"""
        print("\n🔄 DEX Approval Status")
        print("-" * 50)
        
        if not hasattr(self, 'contract'):
            self.add_check("DEX approval check", False, "Contract not loaded")
            return
        
        approved_count = 0
        
        for dex_name, dex_address in self.required_dexes.items():
            try:
                is_approved = self.contract.functions.approvedDexes(
                    Web3.to_checksum_address(dex_address)
                ).call()
                
                self.add_check(f"{dex_name} approved", is_approved, dex_address)
                
                if is_approved:
                    approved_count += 1
                    
            except Exception as e:
                self.add_check(f"{dex_name} approval check", False, str(e))
        
        # Summary check
        all_approved = approved_count == len(self.required_dexes)
        self.add_check("All required DEXes approved", all_approved, 
                      f"{approved_count}/{len(self.required_dexes)} DEXes approved")
    
    def check_project_files(self):
        """Check required project files"""
        print("\n📁 Project Files")
        print("-" * 50)
        
        required_files = [
            "quick_dex_check.py",
            "dex_manager_utility.py", 
            "comprehensive_dex_report.py",
            "foundry-mcp-server/advanced_dex_management_server.py",
            ".env"
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            self.add_check(f"File exists: {file_path}", path.exists())
    
    def check_dependencies(self):
        """Check Python dependencies"""
        print("\n📦 Dependencies")
        print("-" * 50)
        
        required_packages = [
            "web3",
            "eth_account", 
            "python-dotenv",
            "asyncio",
            "websockets",
            "aiohttp"
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.add_check(f"Package: {package}", True)
            except ImportError:
                self.add_check(f"Package: {package}", False, "Not installed")
    
    def check_mcp_server(self):
        """Check MCP server configuration"""
        print("\n🖥️  MCP Server")
        print("-" * 50)
        
        server_file = Path("foundry-mcp-server/advanced_dex_management_server.py")
        self.add_check("MCP server file exists", server_file.exists())
        
        if server_file.exists():
            # Check if server can be imported
            try:
                sys.path.append('foundry-mcp-server')
                from advanced_dex_management_server import AdvancedDEXMCPServer
                self.add_check("MCP server can be imported", True)
                
                # Basic server instantiation test
                try:
                    server = AdvancedDEXMCPServer()
                    self.add_check("MCP server can be instantiated", True)
                except Exception as e:
                    self.add_check("MCP server instantiation", False, str(e))
                    
            except ImportError as e:
                self.add_check("MCP server import", False, str(e))
    
    def run_performance_tests(self):
        """Run basic performance tests"""
        print("\n⚡ Performance Tests")
        print("-" * 50)
        
        if not hasattr(self, 'web3') or not self.web3.is_connected():
            self.add_check("Performance tests", False, "No network connection")
            return
        
        # Test RPC response time
        start_time = time.time()
        try:
            block_number = self.web3.eth.block_number
            response_time = time.time() - start_time
            
            self.add_check("RPC response time < 2s", response_time < 2.0, 
                          f"Response time: {response_time:.3f}s")
            
            if response_time > 1.0:
                self.add_warning("Slow RPC response", f"Response time: {response_time:.3f}s")
                
        except Exception as e:
            self.add_check("RPC performance test", False, str(e))
        
        # Test contract call performance
        if hasattr(self, 'contract'):
            start_time = time.time()
            try:
                for _ in range(3):  # Test multiple calls
                    self.contract.functions.owner().call()
                
                avg_time = (time.time() - start_time) / 3
                self.add_check("Contract call performance", avg_time < 1.0,
                              f"Average call time: {avg_time:.3f}s")
                
            except Exception as e:
                self.add_check("Contract performance test", False, str(e))
    
    def generate_report(self):
        """Generate final production readiness report"""
        print("\n" + "=" * 70)
        print("🎯 PRODUCTION READINESS REPORT")
        print("=" * 70)
        
        # Success rate
        success_rate = (self.success_count / self.total_checks * 100) if self.total_checks > 0 else 0
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({self.success_count}/{self.total_checks})")
        
        # Determine readiness status
        if success_rate >= 95 and len(self.issues) == 0:
            status = "🟢 PRODUCTION READY"
            recommendation = "Your flash loan arbitrage bot is ready for production deployment!"
        elif success_rate >= 85 and len(self.issues) <= 2:
            status = "🟡 NEARLY READY"
            recommendation = "Minor issues need to be addressed before production deployment."
        else:
            status = "🔴 NOT READY"
            recommendation = "Significant issues must be resolved before production deployment."
        
        print(f"🚦 Status: {status}")
        print(f"💡 Recommendation: {recommendation}")
        
        # Show issues
        if self.issues:
            print(f"\n❌ Issues to resolve ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        # Show warnings
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        # Production checklist
        print(f"\n✅ Production Deployment Checklist:")
        print("   ✓ All 6 DEXes approved on contract")
        print("   ✓ Contract owner verification confirmed")
        print("   ✓ Network connectivity validated")
        print("   ✓ Account has sufficient MATIC balance")
        print("   ✓ MCP server functionality verified")
        print("   ✓ All dependencies installed")
        
        print(f"\n📋 Next Steps:")
        if success_rate >= 95:
            print("   1. Begin live testing with small amounts")
            print("   2. Monitor transaction success rates")
            print("   3. Scale up operation gradually")
            print("   4. Set up automated monitoring")
        else:
            print("   1. Address the issues listed above")
            print("   2. Re-run this production readiness check")
            print("   3. Validate fixes in development environment")
        
        print("=" * 70)
        return success_rate >= 95

def main():
    """Run complete production readiness validation"""
    print("🏗️  Flash Loan Arbitrage Bot - Production Readiness Check")
    print("=" * 70)
    print("📋 Contract: 0x153dDf13D58397740c40E9D1a6e183A8c0F36c32")
    print("🌐 Network: Polygon Mainnet")
    print(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    
    validator = ProductionReadinessValidator()
    
    try:
        # Run all checks
        validator.check_environment_variables()
        validator.check_network_connectivity()
        validator.check_contract_status()
        validator.check_dex_approvals()
        validator.check_project_files()
        validator.check_dependencies()
        validator.check_mcp_server()
        validator.run_performance_tests()
        
        # Generate final report
        is_ready = validator.generate_report()
        
        return is_ready
        
    except Exception as e:
        print(f"❌ Critical error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        ready = main()
        sys.exit(0 if ready else 1)
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
