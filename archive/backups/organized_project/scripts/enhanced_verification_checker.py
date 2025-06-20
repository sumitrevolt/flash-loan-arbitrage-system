#!/usr/bin/env python3
"""
Enhanced Contract Verification Status Checker
Check the status of the submitted verification
"""

import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_verification_status_detailed():
    """Check the detailed verification status"""
    
    contract_address = "0xb5855560f3558844dCC5856BDa33D2fb7BD4B04F"
    guid = "vwqbz9gkftbkhqnj78ihgjltmy1rxxdxkabxjt6qnjwujxxqta"  # From previous submission
    api_key = os.getenv("POLYGONSCAN_API_KEY")
    
    if not api_key:
        print("❌ No Polygonscan API key found!")
        return False
    
    api_url = "https://api.polygonscan.com/api"
    
    print(f"🔍 Checking verification status for contract: {contract_address}")
    print(f"📋 GUID: {guid}")
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # Check verification status using GUID
    status_params = {
        'apikey': api_key,
        'module': 'contract',
        'action': 'checkverifystatus',
        'guid': guid
    }
    
    try:
        print(f"\n🌐 Making request to: {api_url}")
        print(f"📊 Parameters: {status_params}")
        
        response = requests.get(api_url, params=status_params)
        print(f"📡 Response status: {response.status_code}")
        
        result = response.json()
        print(f"📄 Raw response: {result}")
        
        if result.get('status') == '1':
            if result.get('result') == 'Pass - Verified':
                print(f"\n✅ CONTRACT SUCCESSFULLY VERIFIED!")
                print(f"🔗 View verified contract: https://polygonscan.com/address/{contract_address}#code")
                return True
            elif 'Pending' in str(result.get('result', '')):
                print(f"\n⏳ Verification is still pending...")
                print(f"📝 Status: {result.get('result')}")
                return False
            else:
                print(f"\n❌ Verification failed: {result.get('result')}")
                return False
        else:
            print(f"\n⚠️  API returned status 0: {result.get('message')}")
            # Try alternative method - check if contract source is available
            return check_contract_source_directly(contract_address, api_key)
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

def check_contract_source_directly(contract_address, api_key):
    """Check if contract source code is available (alternative method)"""
    
    print(f"\n🔄 Trying alternative method - checking contract source directly...")
    
    api_url = "https://api.polygonscan.com/api"
    
    params = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': contract_address,
        'apikey': api_key
    }
    
    try:
        response = requests.get(api_url, params=params)
        result = response.json()
        
        print(f"📄 Source check response: {result}")
        
        if result.get('status') == '1' and result.get('result'):
            contract_info = result['result'][0]
            
            if contract_info.get('SourceCode') and contract_info.get('SourceCode') != '':
                print(f"\n✅ CONTRACT IS VERIFIED!")
                print(f"📋 Contract Name: {contract_info.get('ContractName', 'Unknown')}")
                print(f"🔧 Compiler Version: {contract_info.get('CompilerVersion', 'Unknown')}")
                print(f"⚡ Optimization: {contract_info.get('OptimizationUsed', 'Unknown')}")
                print(f"🔗 View source: https://polygonscan.com/address/{contract_address}#code")
                return True
            else:
                print(f"\n⏳ Contract not yet verified - source code not available")
                return False
        else:
            print(f"\n❌ Error getting contract source: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking contract source: {e}")
        return False

def wait_for_verification(max_wait_minutes=10):
    """Wait for verification to complete with periodic checks"""
    
    print(f"\n⏰ Waiting for verification to complete (max {max_wait_minutes} minutes)...")
    
    wait_interval = 30  # seconds
    max_attempts = (max_wait_minutes * 60) // wait_interval
    
    for attempt in range(max_attempts):
        print(f"\n🔄 Check #{attempt + 1}/{max_attempts} (waiting {wait_interval}s between checks)")
        
        if check_verification_status_detailed():
            return True
        
        if attempt < max_attempts - 1:  # Don't wait after the last attempt
            print(f"⏱️  Waiting {wait_interval} seconds before next check...")
            time.sleep(wait_interval)
    
    print(f"\n⏰ Verification check timed out after {max_wait_minutes} minutes")
    print(f"💡 You can manually check at: https://polygonscan.com/address/0xb5855560f3558844dCC5856BDa33D2fb7BD4B04F#code")
    return False

if __name__ == "__main__":
    print("🚀 Enhanced Contract Verification Status Checker")
    print("=" * 55)
    
    # First do an immediate check
    print("\n1️⃣ Immediate status check...")
    is_verified = check_verification_status_detailed()
    
    if not is_verified:
        print("\n2️⃣ Contract not yet verified, starting monitoring...")
        wait_for_verification(max_wait_minutes=10)
    
    print("\n🎉 Verification check completed!")
