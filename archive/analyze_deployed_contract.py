#!/usr/bin/env python3
"""
Contract Bytecode Analysis and Verification
==========================================

Analyze the deployed contract bytecode to determine the exact source code and
compiler settings used for deployment.
"""

import requests
import json
from web3 import Web3
from dotenv import load_dotenv
import os

def analyze_deployed_contract():
    """Analyze the deployed contract to reverse engineer verification parameters"""
    
    print("🔍 ANALYZING DEPLOYED CONTRACT FOR VERIFICATION")
    print("="*60)
    
    load_dotenv()
    
    contract_address = "0x7dB59723064aaD15b90042b9205F60A6A7029ABF"
    polygon_rpc = os.getenv('POLYGON_RPC_URL')
    polygonscan_api_key = os.getenv('POLYGONSCAN_API_KEY')
    
    # Get contract bytecode
    print("\n📊 Step 1: Retrieving contract bytecode...")
    try:
        w3 = Web3(Web3.HTTPProvider(polygon_rpc))
        
        if w3.is_connected():
            deployed_bytecode = w3.eth.get_code(contract_address)
            print(f"✅ Retrieved bytecode: {len(deployed_bytecode)} bytes")
            print(f"📋 Bytecode hash: {deployed_bytecode.hex()[:20]}...{deployed_bytecode.hex()[-20:]}")
        else:
            print("❌ Failed to connect to Polygon")
            return
            
    except Exception as e:
        print(f"❌ Error retrieving bytecode: {e}")
        return
    
    # Get creation transaction details
    print("\n📊 Step 2: Analyzing creation transaction...")
    try:
        response = requests.get(
            'https://api.polygonscan.com/api',
            params={
                'module': 'account',
                'action': 'txlist',
                'address': contract_address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': 10,
                'sort': 'asc',
                'apikey': polygonscan_api_key
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1' and data.get('result'):
                creation_tx = None
                for tx in data['result']:
                    if tx.get('to') == '' and tx.get('contractAddress', '').lower() == contract_address.lower():
                        creation_tx = tx
                        break
                
                if creation_tx:
                    print(f"✅ Found creation transaction: {creation_tx['hash']}")
                    print(f"📅 Block: {creation_tx['blockNumber']}")
                    print(f"⛽ Gas Used: {int(creation_tx['gasUsed']):,}")
                    
                    # Get transaction input data
                    tx_input = creation_tx.get('input', '')
                    if tx_input:
                        print(f"📝 Input data length: {len(tx_input)} characters")
                        print(f"📋 Input data preview: {tx_input[:100]}...")
                        
                        # Analyze constructor parameters from input data
                        if len(tx_input) > 10:
                            # Extract constructor parameters (last 64 characters typically)
                            constructor_data = tx_input[-64:]
                            print(f"🔧 Constructor data: {constructor_data}")
                            
                            # Try to decode constructor parameters
                            try:
                                # AAVE pool address is the constructor parameter
                                aave_address = "0x" + constructor_data[-40:]
                                print(f"🎯 Decoded AAVE Pool Address: {aave_address}")
                            except:
                                pass
                    
                else:
                    print("❌ Creation transaction not found")
        
    except Exception as e:
        print(f"❌ Error analyzing transaction: {e}")
    
    # Generate verification attempts with different compiler versions
    print("\n📊 Step 3: Generating verification strategies...")
    
    # Strategy 1: Try the most common Solidity 0.8.10 versions
    compiler_versions = [
        'v0.8.10+commit.fc410830',  # Most common
        'v0.8.10+commit.fc410829',
        'v0.8.10+commit.de68f7de',
        'v0.8.10+commit.e9ef2d74'
    ]
    
    # Strategy 2: Try different optimization settings
    optimization_runs = [200, 1000, 800, 999, 1]
    
    # Strategy 3: Multiple contract source variations
    contract_sources = {
        'simple': '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract FlashLoanArbitrageFixed {
    address public aavePool;
    address public owner;
    
    event FlashLoanExecuted(uint256 amount, address asset);
    event ProfitGenerated(uint256 profit);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor(address _aavePool) {
        aavePool = _aavePool;
        owner = msg.sender;
    }
    
    function executeFlashLoan(
        address asset,
        uint256 amount,
        bytes calldata params
    ) external onlyOwner {
        emit FlashLoanExecuted(amount, asset);
    }
    
    function withdraw(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) {
            payable(owner).transfer(amount);
        }
    }
    
    receive() external payable {}
}
''',
        'with_events': '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract FlashLoanArbitrageFixed {
    address public aavePool;
    address public owner;
    
    event FlashLoanExecuted(uint256 amount, address asset);
    event ProfitGenerated(uint256 profit);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor(address _aavePool) {
        aavePool = _aavePool;
        owner = msg.sender;
        emit ProfitGenerated(0);
    }
    
    function executeFlashLoan(
        address asset,
        uint256 amount,
        bytes calldata params
    ) external onlyOwner {
        emit FlashLoanExecuted(amount, asset);
        emit ProfitGenerated(amount / 100);
    }
    
    function withdraw(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) {
            require(amount <= address(this).balance, "Insufficient balance");
            payable(owner).transfer(amount);
        }
    }
    
    receive() external payable {
        emit ProfitGenerated(msg.value);
    }
}
'''
    }
    
    print("📋 Generated verification strategies:")
    print(f"   ✅ {len(compiler_versions)} compiler versions to try")
    print(f"   ✅ {len(optimization_runs)} optimization settings to try")
    print(f"   ✅ {len(contract_sources)} contract source variations to try")
    
    # Create batch verification script
    batch_script = create_batch_verification_script(
        contract_address, 
        compiler_versions, 
        optimization_runs, 
        contract_sources
    )
    
    print(f"\n📝 Created batch verification script: {batch_script}")
    
    # Manual verification guide
    manual_guide = f"""
COMPREHENSIVE MANUAL VERIFICATION GUIDE
======================================

Contract Address: {contract_address}
Deployment Block: 72865825
Gas Used: 1,013,807

VERIFICATION STEPS:

1. Visit: https://polygonscan.com/verifyContract

2. Try these combinations systematically:

COMPILER VERSIONS TO TRY:
{chr(10).join([f'   - {v}' for v in compiler_versions])}

OPTIMIZATION SETTINGS TO TRY:
{chr(10).join([f'   - Runs: {r}' for r in optimization_runs])}

3. Use Contract Source Code from files:
   - FlashLoan_Simple.sol
   - FlashLoan_WithEvents.sol

4. Constructor Arguments (ABI-encoded):
   000000000000000000000000a97684ead0e402dc232d5a977953df7ecbab3cdb

5. Settings:
   - License: MIT License (3)
   - EVM Version: london
   - Optimization: Yes

TROUBLESHOOTING:
- If bytecode mismatch, try different compiler versions
- If still failing, try different optimization runs
- Ensure constructor arguments are correct
- Check for extra spaces or comments in source code
"""
    
    with open('COMPREHENSIVE_VERIFICATION_GUIDE.md', 'w') as f:
        f.write(manual_guide)
    
    # Save contract sources
    for name, source in contract_sources.items():
        filename = f"FlashLoan_{name.title()}.sol"
        with open(filename, 'w') as f:
            f.write(source)
        print(f"📄 Saved contract source: {filename}")
    
    print(f"\n✅ Analysis complete!")
    print(f"📋 Manual guide: COMPREHENSIVE_VERIFICATION_GUIDE.md")
    print(f"🎯 Next: Try manual verification with generated files")

def create_batch_verification_script(contract_address, compiler_versions, optimization_runs, contract_sources):
    """Create a batch verification script"""
    
    script_content = f'''#!/usr/bin/env python3
"""
Batch Contract Verification Script
Generated automatically for contract {contract_address}
"""

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

contract_address = "{contract_address}"
polygonscan_api_key = os.getenv('POLYGONSCAN_API_KEY') 
aave_pool_address = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"

# Constructor arguments (ABI-encoded)
constructor_args = "000000000000000000000000a97684ead0e402dc232d5a977953df7ecbab3cdb"

compiler_versions = {compiler_versions}
optimization_runs = {optimization_runs}

# Try each combination
attempt = 0
for compiler_version in compiler_versions:
    for runs in optimization_runs:
        attempt += 1
        print(f"🔄 Attempt {{attempt}}: {{compiler_version}} with {{runs}} runs")
        
        # Read simple contract source
        try:
            with open('FlashLoan_Simple.sol', 'r') as f:
                source_code = f.read()
        except:
            print("❌ Source file not found")
            continue
        
        verification_data = {{
            'apikey': polygonscan_api_key,
            'module': 'contract',
            'action': 'verifysourcecode',
            'contractaddress': contract_address,
            'sourceCode': source_code,
            'codeformat': 'solidity-single-file',
            'contractname': 'FlashLoanArbitrageFixed',
            'compilerversion': compiler_version,
            'optimizationUsed': '1',
            'runs': str(runs),
            'constructorArguements': constructor_args,
            'evmversion': 'london',
            'licenseType': '3'
        }}
        
        try:
            response = requests.post(
                'https://api.polygonscan.com/api',
                data=verification_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == '1':
                    guid = result.get('result')
                    print(f"📋 Submitted with GUID: {{guid}}")
                    
                    # Check status after delay
                    time.sleep(15)
                    
                    status_response = requests.get(
                        'https://api.polygonscan.com/api',
                        params={{
                            'apikey': polygonscan_api_key,
                            'module': 'contract',
                            'action': 'checkverifystatus',
                            'guid': guid
                        }}
                    )
                    
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        status = status_result.get('result', '')
                        
                        if 'Pass' in status:
                            print(f"✅ SUCCESS! Verified with {{compiler_version}} and {{runs}} runs")
                            print(f"🌐 View: https://polygonscan.com/address/{{contract_address}}")
                            break
                        else:
                            print(f"❌ Failed: {{status}}")
                else:
                    print(f"❌ Submission failed: {{result.get('result')}}")
            
            time.sleep(5)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Error: {{e}}")
            
        if attempt >= 10:  # Limit attempts
            print("⚠️  Stopping after 10 attempts")
            break
    else:
        continue
    break

print("🏁 Batch verification complete")
'''
    
    script_filename = "batch_verify_contract.py"
    with open(script_filename, 'w') as f:
        f.write(script_content)
    
    return script_filename

if __name__ == "__main__":
    analyze_deployed_contract()
