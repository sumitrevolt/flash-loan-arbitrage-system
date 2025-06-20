#!/usr/bin/env python3
"""
Production Deployment Validation Script
Validates all systems are ready for production flash loan arbitrage trading
"""

import asyncio
import json
import os
import platform
import requests
from typing import List, Dict
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

def test_environment_variables() -> bool:
    """Test all required environment variables are set"""
    print("\n🔍 Testing Environment Variables...")
    
    required_vars = [
        "POLYGON_RPC_URL",
        "PRIVATE_KEY", 
        "ACCOUNT_ADDRESS",
        "ETHERSCAN_API_KEY",
        "POLYGONSCAN_API_KEY"
    ]
    
    missing_vars: List[str] = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            
    if missing_vars:
        print(f"❌ Missing required variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_api_connectivity() -> bool:
    """Test API connectivity for external services"""
    print("\n🌐 Testing API Connectivity...")
    
    all_passed = True
    
    # Test Polygon RPC
    try:
        polygon_rpc = os.getenv("POLYGON_RPC_URL")
        if polygon_rpc:
            response = requests.post(
                polygon_rpc,
                json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                timeout=10
            )
            if response.status_code == 200 and "result" in response.json():
                block_num = int(response.json()['result'], 16)
                print(f"✅ Polygon RPC - Connected successfully - Block: {block_num}")
            else:
                print("❌ Polygon RPC - Failed to get block number")
                all_passed = False
        else:
            print("❌ Polygon RPC URL not configured")
            all_passed = False
    except Exception as e:
        print(f"❌ Polygon RPC - Connection failed: {str(e)}")
        all_passed = False
        
    # Test Etherscan API
    try:
        etherscan_key = os.getenv("ETHERSCAN_API_KEY")
        if etherscan_key:
            response = requests.get(
                f"https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={etherscan_key}",
                timeout=10
            )
            if response.status_code == 200 and "result" in response.json():
                print("✅ Etherscan API - Connected successfully")
            else:
                print("❌ Etherscan API - API key invalid or service unavailable")
                all_passed = False
        else:
            print("❌ Etherscan API key not configured")
            all_passed = False
    except Exception as e:
        print(f"❌ Etherscan API - Connection failed: {str(e)}")
        all_passed = False
        
    # Test Polygonscan API
    try:
        polygonscan_key = os.getenv("POLYGONSCAN_API_KEY")
        if polygonscan_key:
            response = requests.get(
                f"https://api.polygonscan.com/api?module=proxy&action=eth_blockNumber&apikey={polygonscan_key}",
                timeout=10
            )
            if response.status_code == 200 and "result" in response.json():
                print("✅ Polygonscan API - Connected successfully")
            else:
                print("❌ Polygonscan API - API key invalid or service unavailable") 
                all_passed = False
        else:
            print("❌ Polygonscan API key not configured")
            all_passed = False
    except Exception as e:
        print(f"❌ Polygonscan API - Connection failed: {str(e)}")
        all_passed = False
        
    return all_passed

def test_mcp_servers() -> bool:
    """Test MCP server connectivity"""
    print("\n🖥️  Testing MCP Servers...")
    
    all_passed = True
    
    mcp_servers: List[Dict[str, str]] = [
        {"name": "Copilot MCP", "url": "http://127.0.0.1:3002/health"},
        {"name": "TaskManager MCP", "url": "http://127.0.0.1:8007/health"},
        {"name": "Flash Loan Arbitrage TS", "url": "http://127.0.0.1:8000/health"}
    ]
    
    for server in mcp_servers:
        try:
            response = requests.get(server["url"], timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'ok')
                print(f"✅ MCP {server['name']} - Server healthy - Status: {status}")
            else:
                print(f"❌ MCP {server['name']} - Server returned status code: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ MCP {server['name']} - Connection failed: {str(e)}")
            all_passed = False
            
    return all_passed

def test_web3_connectivity() -> bool:
    """Test Web3 connectivity and wallet access"""
    print("\n⛓️  Testing Web3 Connectivity...")
    
    all_passed = True
    
    try:
        # Initialize Web3
        rpc_url = os.getenv("POLYGON_RPC_URL")
        if not rpc_url:
            print("❌ Web3 Setup - No RPC URL configured")
            return False
            
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Test connection
        if w3.is_connected():
            print("✅ Web3 Connection - Connected to Polygon network")
            
            # Get latest block
            latest_block = w3.eth.block_number
            print(f"✅ Blockchain Sync - Latest block: {latest_block}")
            
            # Test wallet
            private_key = os.getenv("PRIVATE_KEY")
            if private_key and len(private_key) == 64:
                try:
                    account = w3.eth.account.from_key(private_key)
                    balance = w3.eth.get_balance(account.address)
                    balance_matic = w3.from_wei(balance, 'ether')
                    
                    print(f"✅ Wallet Access - Address: {account.address}")
                    print(f"✅ Wallet Balance - {balance_matic:.4f} MATIC")
                    
                    # Check if balance is sufficient for gas
                    if balance_matic < 0.1:
                        print(f"⚠️  WARNING - Low MATIC balance ({balance_matic:.4f}) - recommend at least 0.1 MATIC for gas")
                        
                except Exception as e:
                    print(f"❌ Wallet Access - Invalid private key: {str(e)}")
                    all_passed = False
            else:
                print("❌ Wallet Access - Private key not configured or invalid length")
                all_passed = False
                
        else:
            print("❌ Web3 Connection - Failed to connect to Polygon network")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Web3 Setup - Initialization failed: {str(e)}")
        all_passed = False
        
    return all_passed

def test_system_requirements() -> bool:
    """Test system requirements"""
    print("\n💻 Testing System Requirements...")
    
    all_passed = True
    
    # Test Python version
    python_version = platform.python_version()
    major, minor = map(int, python_version.split('.')[:2])
    
    if major == 3 and minor >= 8:
        print(f"✅ Python Version - Python {python_version} (compatible)")
    else:
        print(f"❌ Python Version - Python {python_version} (requires 3.8+)")
        all_passed = False
        
    # Test Windows asyncio fix
    if platform.system() == "Windows":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            print("✅ Windows Asyncio Fix - ProactorEventLoopPolicy applied")
        except Exception as e:
            print(f"❌ Windows Asyncio Fix - Failed to set event loop policy: {str(e)}")
            all_passed = False
            
    return all_passed

def test_configuration_files() -> bool:
    """Test configuration file validity"""
    print("\n📋 Testing Configuration Files...")
    
    all_passed = True
    
    # Test unified_mcp_config.json
    try:
        with open("unified_mcp_config.json", "r") as f:
            config = json.load(f)
        
        servers = config.get("servers", {})
        print(f"✅ MCP Configuration - Valid JSON with {len(servers)} server configurations")
        
        # Check for required fields
        required_fields: List[str] = ["name", "version", "servers", "global_configuration"]
        missing_fields: List[str] = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"⚠️  WARNING - MCP Config missing fields: {', '.join(missing_fields)}")
            
    except FileNotFoundError:
        print("❌ MCP Configuration - unified_mcp_config.json not found")
        all_passed = False
    except json.JSONDecodeError as e:
        print(f"❌ MCP Configuration - Invalid JSON: {str(e)}")
        all_passed = False
    except Exception as e:
        print(f"❌ MCP Configuration - Error reading config: {str(e)}")
        all_passed = False
        
    return all_passed

async def main() -> bool:
    """Main validation function"""
    print("🚀 Production Deployment Validation Starting...")
    
    # Run all validation tests
    test_results: List[bool] = []
    
    test_results.append(test_environment_variables())
    test_results.append(test_system_requirements())
    test_results.append(test_configuration_files())
    test_results.append(test_api_connectivity())
    test_results.append(test_mcp_servers())
    test_results.append(test_web3_connectivity())
    
    # Generate final report
    print("\n" + "="*60)
    print("🎯 PRODUCTION VALIDATION REPORT")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results)
    failed_tests = total_tests - passed_tests
    
    print(f"\nTest Summary:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {failed_tests}")
    
    if failed_tests == 0:
        print(f"\n🎉 ALL TESTS PASSED - READY FOR PRODUCTION!")
    else:
        print(f"\n❌ {failed_tests} TESTS FAILED - PRODUCTION NOT READY")
        
    print(f"\nProduction readiness: {'🟢 READY' if failed_tests == 0 else '🔴 NOT READY'}")
    print("="*60)
    
    return failed_tests == 0

if __name__ == "__main__":
    # Fix for Windows aiodns issue
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    success = asyncio.run(main())
    exit(0 if success else 1)
