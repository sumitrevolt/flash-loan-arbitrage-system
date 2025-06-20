#!/usr/bin/env python3
"""
Contract Verification Script for Polygonscan
This script verifies the FlashLoanArbitrageFixed contract on Polygonscan
"""

import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_contract_on_polygonscan():
    """Verify the deployed contract on Polygonscan"""
    
    # Contract details
    contract_address = "0xb5855560f3558844dCC5856BDa33D2fb7BD4B04F"
    
    # Read the contract source code
    try:
        with open("core/contracts/FlashLoanArbitrageFixed.sol", "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading contract source: {e}")
        return False
    
    # Polygonscan API endpoint for contract verification
    api_url = "https://api.polygonscan.com/api"
    
    # Get API key from environment (you'll need to get one from Polygonscan)
    api_key = os.getenv("POLYGONSCAN_API_KEY", "YourApiKeyToken")
    
    # Contract verification parameters
    verification_data = {
        'apikey': api_key,
        'module': 'contract',
        'action': 'verifysourcecode',
        'contractaddress': contract_address,
        'sourceCode': source_code,
        'codeformat': 'solidity-single-file',
        'contractname': 'FlashLoanArbitrageFixed',
        'compilerversion': 'v0.8.10+commit.fc410830',  # Solidity 0.8.10
        'optimizationUsed': '1',
        'runs': '200',
        'constructorArguments': '',  # Add constructor arguments if any
        'evmversion': 'london',
        'licenseType': '3',  # MIT License
        'libraryname1': '',
        'libraryaddress1': '',
        'libraryname2': '',
        'libraryaddress2': '',
        'libraryname3': '',
        'libraryaddress3': '',
        'libraryname4': '',
        'libraryaddress4': '',
        'libraryname5': '',
        'libraryaddress5': '',
        'libraryname6': '',
        'libraryaddress6': '',
        'libraryname7': '',
        'libraryaddress7': '',
        'libraryname8': '',
        'libraryaddress8': '',
        'libraryname9': '',
        'libraryaddress9': '',
        'libraryname10': '',
        'libraryaddress10': ''
    }
    
    print(f"Attempting to verify contract: {contract_address}")
    print(f"Contract name: FlashLoanArbitrageFixed")
    print(f"Compiler version: {verification_data['compilerversion']}")
    
    if api_key == "YourApiKeyToken":
        print("\n⚠️  WARNING: No Polygonscan API key found!")
        print("To verify the contract automatically, you need to:")
        print("1. Get a free API key from https://polygonscan.com/apis")
        print("2. Add POLYGONSCAN_API_KEY=your_key_here to your .env file")
        print("\nFor now, showing manual verification instructions...")
        show_manual_verification_steps(contract_address, source_code)
        return False
    
    try:
        # Submit verification request
        response = requests.post(api_url, data=verification_data)
        result = response.json()
        
        if result['status'] == '1':
            guid = result['result']
            print(f"✅ Verification submitted successfully!")
            print(f"GUID: {guid}")
            
            # Check verification status
            return check_verification_status(api_key, guid, contract_address)
        else:
            print(f"❌ Verification failed: {result.get('message', 'Unknown error')}")
            print(f"Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def check_verification_status(api_key, guid, contract_address):
    """Check the status of contract verification"""
    
    api_url = "https://api.polygonscan.com/api"
    max_attempts = 20
    
    for attempt in range(max_attempts):
        try:
            status_params = {
                'apikey': api_key,
                'module': 'contract',
                'action': 'checkverifystatus',
                'guid': guid
            }
            
            response = requests.get(api_url, params=status_params)
            result = response.json()
            
            if result['status'] == '1':
                if result['result'] == 'Pass - Verified':
                    print(f"✅ Contract verified successfully!")
                    print(f"🔗 View on Polygonscan: https://polygonscan.com/address/{contract_address}#code")
                    return True
                elif result['result'] == 'Pending in queue':
                    print(f"⏳ Verification pending... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(10)
                    continue
                else:
                    print(f"❌ Verification failed: {result['result']}")
                    return False
            else:
                print(f"❌ Status check failed: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            time.sleep(5)
            continue
    
    print("⏰ Verification timed out. Check manually on Polygonscan.")
    return False

def show_manual_verification_steps(contract_address, source_code):
    """Show manual verification steps"""
    
    print("\n" + "="*60)
    print("📋 MANUAL CONTRACT VERIFICATION STEPS")
    print("="*60)
    
    print(f"\n1. Go to: https://polygonscan.com/address/{contract_address}#code")
    print("2. Click 'Verify and Publish' button")
    print("3. Fill in the following details:")
    print("   - Contract Address: " + contract_address)
    print("   - Compiler Type: Solidity (Single file)")
    print("   - Compiler Version: v0.8.10+commit.fc410830")
    print("   - Open Source License Type: MIT License (3)")
    print("   - Optimization: Yes")
    print("   - Optimization Runs: 200")
    print("   - EVM Version: london")
    
    print("\n4. Copy and paste the following source code:")
    print("-" * 40)
    print("CONTRACT SOURCE CODE:")
    print("-" * 40)
    print(source_code[:500] + "...")
    print("-" * 40)
    print("(Full source code has been saved and can be copied from the file)")
    
    print(f"\n5. If there are constructor arguments, add them in the appropriate field")
    print(f"6. Click 'Verify and Publish'")
    
    print("\n" + "="*60)

def check_contract_status():
    """Check the current contract status on Polygonscan"""
    
    contract_address = "0xb5855560f3558844dCC5856BDa33D2fb7BD4B04F"
    api_url = "https://api.polygonscan.com/api"
    
    # Check if contract is already verified
    params = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': contract_address,
        'apikey': 'YourApiKeyToken'  # Public endpoint doesn't require API key
    }
    
    try:
        response = requests.get(api_url, params=params)
        result = response.json()
        
        if result['status'] == '1' and result['result']:
            contract_info = result['result'][0]
            
            print(f"📊 CONTRACT STATUS REPORT")
            print(f"Contract Address: {contract_address}")
            print(f"Contract Name: {contract_info.get('ContractName', 'Unknown')}")
            print(f"Compiler Version: {contract_info.get('CompilerVersion', 'Unknown')}")
            print(f"Optimization Used: {contract_info.get('OptimizationUsed', 'Unknown')}")
            print(f"Runs: {contract_info.get('Runs', 'Unknown')}")
            
            if contract_info.get('SourceCode'):
                print(f"✅ Contract is VERIFIED")
                print(f"🔗 View source: https://polygonscan.com/address/{contract_address}#code")
                return True
            else:
                print(f"❌ Contract is NOT VERIFIED")
                return False
        else:
            print(f"❌ Error checking contract status: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 FlashLoanArbitrageFixed Contract Verification Tool")
    print("=" * 55)
    
    # First check current status
    print("\n1. Checking current contract status...")
    is_verified = check_contract_status()
    
    if not is_verified:
        print("\n2. Starting verification process...")
        verify_contract_on_polygonscan()
    else:
        print("\n✅ Contract is already verified!")
        
    print("\n🎉 Verification process completed!")
