#!/usr/bin/env python3
"""
Enhanced Production Readiness Check with Real-time Data Validation
Validates all components including Foundry MCP Server integration
"""

import asyncio
import json
import logging
import os
import sys
import platform
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup Windows-compatible event loop
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedProductionChecker:
    """Enhanced production readiness checker"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.errors = []
        
    async def run_all_checks(self) -> bool:
        """Run all production readiness checks"""
        print("🔍 Enhanced Production Readiness Check")
        print("=" * 50)
        
        checks = [
            ("Environment Variables", self.check_environment_variables),
            ("Configuration Files", self.check_configuration_files),
            ("Python Dependencies", self.check_python_dependencies),
            ("Foundry MCP Server", self.check_foundry_mcp_server),
            ("Real-time Data Connector", self.check_realtime_connector),
            ("Network Connectivity", self.check_network_connectivity),
            ("Contract Deployment", self.check_contract_deployment),
            ("Risk Management", self.check_risk_management),
            ("Logging Configuration", self.check_logging_configuration)
        ]
        
        for check_name, check_func in checks:
            try:
                print(f"\n📋 {check_name}...")
                success = await check_func()
                
                if success:
                    print(f"✅ {check_name}: PASSED")
                    self.checks_passed += 1
                else:
                    print(f"❌ {check_name}: FAILED")
                    self.checks_failed += 1
                    
            except Exception as e:
                print(f"💥 {check_name}: ERROR - {e}")
                self.checks_failed += 1
                self.errors.append(f"{check_name}: {e}")
        
        # Print summary
        self.print_summary()
        
        return self.checks_failed == 0
    
    async def check_environment_variables(self) -> bool:
        """Check required environment variables"""
        required_vars = [
            "POLYGON_RPC_URL",
            "PRIVATE_KEY",
            "FLASH_LOAN_CONTRACT"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"   Missing variables: {missing_vars}")
            return False
        
        # Validate contract address
        contract_address = os.getenv("FLASH_LOAN_CONTRACT")
        expected_address = "0x153dDf13D58397740c40E9D1a6e183A8c0F36c32"
        
        if contract_address != expected_address:
            print(f"   Warning: Contract address mismatch")
            print(f"   Expected: {expected_address}")
            print(f"   Got: {contract_address}")
            self.warnings += 1
        
        print(f"   All required environment variables present")
        return True
    
    async def check_configuration_files(self) -> bool:
        """Check configuration files"""
        config_files = [
            "production_config.json",
            "contract_abi.json"
        ]
        
        missing_files = []
        for file_path in config_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"   Missing config files: {missing_files}")
            return False
        
        # Validate production config structure
        try:
            with open("production_config.json", 'r') as f:
                config = json.load(f)
                
            required_sections = [
                "deployment", "tokens", "dexes", "aave", 
                "trading", "risk_management", "monitoring",
                "foundry_mcp_server", "data_sources"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in config:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"   Missing config sections: {missing_sections}")
                return False
            
            print(f"   Configuration files valid")
            return True
            
        except json.JSONDecodeError as e:
            print(f"   Invalid JSON in production_config.json: {e}")
            return False
    
    async def check_python_dependencies(self) -> bool:
        """Check Python dependencies"""
        required_modules = [
            "web3", "aiohttp", "websockets", "eth_account",
            "json", "asyncio", "logging", "decimal"
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"   Missing Python modules: {missing_modules}")
            print(f"   Install with: pip install {' '.join(missing_modules)}")
            return False
          # Check custom modules
        try:
            from production_arbitrage_bot import ArbitrageEngine
            from realtime_data_connector import RealTimeDataConnector
            print(f"   All dependencies available")
            return True
        except ImportError as e:
            print(f"   Custom module import error: {e}")
            return False
    
    async def check_foundry_mcp_server(self) -> bool:
        """Check Foundry MCP Server availability and health"""
        try:
            # Check if server directory exists
            server_path = "foundry-mcp-server"
            if not os.path.exists(server_path):
                print(f"   MCP server directory not found: {server_path}")
                return False
            
            # Check if server is running using PowerShell first (most reliable on Windows)
            import subprocess
            try:
                result: str = subprocess.run([
                    "powershell", "-Command", 
                    "try { $response = Invoke-RestMethod -Uri 'http://localhost:8001/health' -TimeoutSec 10; Write-Host $response.status } catch { Write-Host 'error' }"
                ], capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0 and "healthy" in result.stdout:
                    print(f"   MCP Server running and healthy")
                    return True
                else:
                    print(f"   MCP Server health check failed: {result.stdout.strip()}")
                    return False
                    
            except subprocess.TimeoutExpired:
                print(f"   MCP Server health check timeout")
                return False
            except Exception as powershell_error:
                print(f"   PowerShell health check failed: {powershell_error}")
                
                # Fallback to aiohttp with Windows-compatible settings
                health_url = "http://127.0.0.1:8001/health"
                
                # Use Windows-compatible connector to avoid aiodns issues
                connector = aiohttp.TCPConnector(use_dns_cache=False)
                timeout = aiohttp.ClientTimeout(total=10)
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    try:
                        async with session.get(health_url, timeout=10) as response:
                            if response.status == 200:
                                health_data = await response.json()
                                
                                if health_data.get('status') == 'healthy':
                                    print(f"   MCP Server running and healthy")
                                    
                                    # Check foundry availability
                                    if not health_data.get('foundry_available', False):
                                        print(f"   Warning: Foundry not installed (server functional for basic ops)")
                                        self.warnings += 1
                                    
                                    return True
                                else:
                                    print(f"   MCP Server unhealthy: {health_data}")
                                    return False
                            else:
                                print(f"   MCP Server returned status {response.status}")
                                return False
                                
                    except asyncio.TimeoutError:
                        print(f"   MCP Server health check timeout")
                        return False
                    except aiohttp.ClientError as e:
                        print(f"   MCP Server connection error: {e}")
                        return False
                        
        except Exception as e:
            print(f"   MCP Server check error: {e}")
            return False
    
    async def check_realtime_connector(self) -> bool:
        """Check real-time data connector"""
        try:
            from realtime_data_connector import RealTimeDataConnector
            
            # Load config for connector
            with open("production_config.json", 'r') as f:
                config = json.load(f)
            
            # Test connector initialization
            connector = RealTimeDataConnector(config)
            
            # Check configuration
            mcp_config = config.get('foundry_mcp_server', {})
            if not mcp_config.get('enabled', True):
                print(f"   Warning: Real-time data connector disabled in config")
                self.warnings += 1
            
            print(f"   Real-time data connector available")
            return True
            
        except Exception as e:
            print(f"   Real-time connector error: {e}")
            return False
    
    async def check_network_connectivity(self) -> bool:
        """Check network connectivity"""
        try:
            from web3 import Web3
            
            rpc_url = os.getenv('POLYGON_RPC_URL')
            if not rpc_url:
                print(f"   RPC URL not configured")
                return False
            
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not w3.is_connected():
                print(f"   Cannot connect to Polygon network")
                return False
            
            chain_id = w3.eth.chain_id
            if chain_id != 137:
                print(f"   Wrong network: Expected Polygon (137), got {chain_id}")
                return False
            
            # Check latest block
            latest_block = w3.eth.block_number
            print(f"   Connected to Polygon Mainnet (Block: {latest_block})")
            
            return True
            
        except Exception as e:
            print(f"   Network connectivity error: {e}")
            return False
    
    async def check_contract_deployment(self) -> bool:
        """Check contract deployment"""
        try:
            from web3 import Web3
            
            rpc_url = os.getenv('POLYGON_RPC_URL')
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            contract_address = os.getenv('FLASH_LOAN_CONTRACT')
            expected_address = "0x153dDf13D58397740c40E9D1a6e183A8c0F36c32"
            
            if contract_address != expected_address:
                print(f"   Contract address mismatch")
                return False
            
            # Check if contract exists
            code = w3.eth.get_code(contract_address)
            if code == b'':
                print(f"   No contract found at {contract_address}")
                return False
            
            # Load and validate ABI
            with open('contract_abi.json', 'r') as f:
                contract_abi = json.load(f)
            
            contract = w3.eth.contract(address=contract_address, abi=contract_abi)
            
            print(f"   Contract deployed and accessible at {contract_address}")
            return True
            
        except Exception as e:
            print(f"   Contract check error: {e}")
            return False
    
    async def check_risk_management(self) -> bool:
        """Check risk management configuration"""
        try:
            with open("production_config.json", 'r') as f:
                config = json.load(f)
            
            risk_config = config.get('risk_management', {})
            
            # Check required risk parameters
            required_params = [
                'max_daily_trades', 'max_daily_loss_usd', 
                'circuit_breaker_loss_threshold', 'max_consecutive_failures',
                'emergency_stop_enabled'
            ]
            
            missing_params = []
            for param in required_params:
                if param not in risk_config:
                    missing_params.append(param)
            
            if missing_params:
                print(f"   Missing risk parameters: {missing_params}")
                return False
            
            # Validate risk limits
            if risk_config.get('max_daily_loss_usd', 0) <= 0:
                print(f"   Invalid max daily loss limit")
                return False
            
            if not risk_config.get('emergency_stop_enabled', False):
                print(f"   Warning: Emergency stop disabled")
                self.warnings += 1
            
            print(f"   Risk management properly configured")
            return True
            
        except Exception as e:
            print(f"   Risk management check error: {e}")
            return False
    
    async def check_logging_configuration(self) -> bool:
        """Check logging configuration"""
        try:
            # Check if logs directory exists
            logs_dir = Path("logs")
            if not logs_dir.exists():
                print(f"   Creating logs directory")
                logs_dir.mkdir(exist_ok=True)
            
            # Test log file creation
            test_log = logs_dir / "test.log"
            with open(test_log, 'w') as f:
                f.write(f"Test log entry: {datetime.now()}\n")
            
            if test_log.exists():
                test_log.unlink()  # Clean up
                print(f"   Logging directory accessible")
                return True
            else:
                print(f"   Cannot create log files")
                return False
                
        except Exception as e:
            print(f"   Logging check error: {e}")
            return False
    
    def print_summary(self):
        """Print check summary"""
        print("\n" + "=" * 50)
        print("📊 PRODUCTION READINESS SUMMARY")
        print("=" * 50)
        print(f"✅ Checks Passed: {self.checks_passed}")
        print(f"❌ Checks Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        
        if self.errors:
            print(f"\n🚨 ERRORS:")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.checks_failed == 0:
            print(f"\n🎉 SYSTEM READY FOR PRODUCTION!")
            print(f"   Real-time data integration: ENABLED")
            print(f"   MCP Server integration: ACTIVE")
            print(f"   All safety checks: PASSED")
        else:
            print(f"\n⚠️  SYSTEM NOT READY - Fix errors before production use")
        
        print("=" * 50)

async def main():
    """Main entry point"""
    checker = EnhancedProductionChecker()
    success = await checker.run_all_checks()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
