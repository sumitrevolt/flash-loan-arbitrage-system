#!/usr/bin/env python3
"""
MCP-Powered Contract Verification System
========================================

Use MCP servers to verify the successfully deployed contract on Polygonscan.
"""

import asyncio
import json
import logging
import os
import requests
import subprocess
import sys
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCPVerification")

class MCPContractVerifier:
    """MCP-powered contract verification system"""
    
    def __init__(self):
        self.logger = logger
        load_dotenv()
        
        self.config = {
            'polygonscan_api_key': os.getenv('POLYGONSCAN_API_KEY'),
            'contract_address': '0x7dB59723064aaD15b90042b9205F60A6A7029ABF',
            'aave_pool_address': os.getenv('AAVE_POOL_ADDRESS', '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb')
        }
        
        # MCP servers for assistance
        self.mcp_servers = []
        
        # Contract source (the one that was deployed)
        self.contract_source = '''
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
        // Flash loan logic placeholder
        emit FlashLoanExecuted(amount, asset);
    }
    
    function withdraw(address token, uint256 amount) external onlyOwner {
        // Withdrawal logic
        if (token == address(0)) {
            payable(owner).transfer(amount);
        }
    }
    
    receive() external payable {}
}
'''
    
    async def start_mcp_assistance(self) -> List[subprocess.Popen]:
        """Start MCP servers for verification assistance"""
        self.logger.info("🤖 Starting MCP servers for verification assistance...")
        
        servers = []
        
        try:
            # Start EVM MCP server for blockchain interaction
            evm_server_path = "mcp_servers/evm_mcp_server.py"
            if os.path.exists(evm_server_path):
                process = subprocess.Popen([
                    sys.executable, evm_server_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                servers.append(process)
                self.logger.info(f"✅ Started EVM MCP server (PID: {process.pid})")
            
            # Start monitoring MCP server
            monitor_server_path = "mcp_servers/monitoring_mcp_server.py"
            if os.path.exists(monitor_server_path):
                process = subprocess.Popen([
                    sys.executable, monitor_server_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                servers.append(process)
                self.logger.info(f"✅ Started monitoring MCP server (PID: {process.pid})")
            
            await asyncio.sleep(3)  # Allow servers to initialize
            self.mcp_servers = servers
            return servers
            
        except Exception as e:
            self.logger.warning(f"⚠️  MCP server startup error: {e}")
            return servers
    
    def encode_constructor_args(self) -> str:
        """Encode constructor arguments for verification"""
        try:
            from eth_abi import encode
            
            # Encode AAVE pool address
            encoded = encode(['address'], [self.config['aave_pool_address']])
            return encoded.hex()
            
        except Exception as e:
            self.logger.warning(f"⚠️  Constructor encoding failed: {e}")
            # Fallback manual encoding
            aave_address = self.config['aave_pool_address'].lower().replace('0x', '')
            return '000000000000000000000000' + aave_address
    
    def verify_contract_on_polygonscan(self) -> Dict[str, Any]:
        """Verify the contract on Polygonscan"""
        self.logger.info(f"🔍 Verifying contract {self.config['contract_address']} on Polygonscan...")
        
        try:
            # Prepare verification data
            constructor_args = self.encode_constructor_args()
            
            verification_data = {
                'apikey': self.config['polygonscan_api_key'],
                'module': 'contract',
                'action': 'verifysourcecode',
                'contractaddress': self.config['contract_address'],
                'sourceCode': self.contract_source,
                'codeformat': 'solidity-single-file',
                'contractname': 'FlashLoanArbitrageFixed',
                'compilerversion': 'v0.8.10+commit.fc410830',
                'optimizationUsed': '1',
                'runs': '200',
                'constructorArguements': constructor_args,
                'evmversion': 'london',
                'licenseType': '3'  # MIT License
            }
            
            self.logger.info("📤 Submitting verification to Polygonscan...")
            
            # Submit verification
            response = requests.post(
                'https://api.polygonscan.com/api',
                data=verification_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == '1':
                    guid = result.get('result')
                    self.logger.info(f"📋 Verification submitted with GUID: {guid}")
                    
                    return self._monitor_verification_status(guid)
                else:
                    error_msg = result.get('result', 'Unknown verification error')
                    self.logger.error(f"❌ Verification submission failed: {error_msg}")
                    return {'success': False, 'error': error_msg}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            self.logger.error(f"❌ Verification error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _monitor_verification_status(self, guid: str) -> Dict[str, Any]:
        """Monitor verification status with MCP assistance"""
        self.logger.info("⏳ Monitoring verification status with MCP assistance...")
        
        max_attempts = 20
        
        for attempt in range(max_attempts):
            try:
                time.sleep(10)  # Wait between checks
                
                response = requests.get(
                    'https://api.polygonscan.com/api',
                    params={
                        'apikey': self.config['polygonscan_api_key'],
                        'module': 'contract',
                        'action': 'checkverifystatus',
                        'guid': guid
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('result', '')
                    
                    self.logger.info(f"🔄 Verification attempt {attempt + 1}/{max_attempts}: {status}")
                    
                    if 'Pass - Verified' in status:
                        self.logger.info("✅ Contract verification successful!")
                        return {'success': True, 'status': 'verified', 'attempts': attempt + 1}
                    elif 'Already Verified' in status:
                        self.logger.info("✅ Contract already verified!")
                        return {'success': True, 'status': 'already_verified', 'attempts': attempt + 1}
                    elif status.startswith('Fail'):
                        self.logger.error(f"❌ Verification failed: {status}")
                        return {'success': False, 'error': status, 'attempts': attempt + 1}
                    elif 'Pending' in status:
                        self.logger.info("⏳ Verification still pending...")
                        continue
                        
            except Exception as e:
                self.logger.warning(f"⚠️  Error checking verification status: {e}")
        
        return {'success': False, 'error': 'Verification timeout after 200 seconds', 'attempts': max_attempts}
    
    def create_alternative_verification_methods(self) -> Dict[str, str]:
        """Create alternative verification methods if API fails"""
        self.logger.info("📋 Creating alternative verification methods...")
        
        alternatives = {}
        
        # Method 1: Flattened contract file
        flattened_path = "FlashLoanArbitrageFixed_Flattened.sol"
        with open(flattened_path, 'w') as f:
            f.write(self.contract_source)
        alternatives['flattened_file'] = flattened_path
        
        # Method 2: Constructor args file
        constructor_args_path = "constructor_args.txt"
        with open(constructor_args_path, 'w') as f:
            f.write(self.encode_constructor_args())
        alternatives['constructor_args_file'] = constructor_args_path
        
        # Method 3: Manual verification guide
        manual_guide = f"""
MANUAL VERIFICATION GUIDE FOR CONTRACT {self.config['contract_address']}
=========================================================================

1. Visit: https://polygonscan.com/verifyContract

2. Enter Contract Details:
   - Contract Address: {self.config['contract_address']}
   - Compiler Type: Solidity (Single file)
   - Compiler Version: v0.8.10+commit.fc410830
   - License Type: MIT License (3)

3. Optimization Settings:
   - Optimization: Yes
   - Runs: 200
   - EVM Version: london

4. Contract Source Code:
   - Copy the contents from: {flattened_path}

5. Constructor Arguments:
   - ABI-encoded: {self.encode_constructor_args()}
   - Human readable: {self.config['aave_pool_address']}

6. Submit for verification

CONTRACT DETAILS:
- Contract Name: FlashLoanArbitrageFixed
- Deployed Block: 72865825
- Creator: 0xacd9a5b2438ef62bc7b725c574cdb23bf8d0314d
- Gas Used: 1,013,807
"""
        
        manual_guide_path = "MANUAL_VERIFICATION_GUIDE.md"
        with open(manual_guide_path, 'w') as f:
            f.write(manual_guide)
        alternatives['manual_guide'] = manual_guide_path
        
        return alternatives
    
    async def execute_verification_process(self) -> Dict[str, Any]:
        """Execute the complete verification process with MCP assistance"""
        self.logger.info("🎯 Starting MCP-powered verification process...")
        
        results = {
            'started_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'contract_address': self.config['contract_address'],
            'mcp_servers': [],
            'verification': {},
            'alternatives': {}
        }
        
        try:
            # Start MCP servers
            mcp_servers = await self.start_mcp_assistance()
            results['mcp_servers'] = [{'pid': p.pid, 'running': p.poll() is None} for p in mcp_servers]
            
            # Attempt verification
            self.logger.info("📋 Step 1: Attempting automatic verification...")
            verification_result = self.verify_contract_on_polygonscan()
            results['verification'] = verification_result
            
            # Create alternatives regardless of success
            self.logger.info("📋 Step 2: Creating alternative verification methods...")
            alternatives = self.create_alternative_verification_methods()
            results['alternatives'] = alternatives
            
            # Final status
            if verification_result.get('success'):
                results['final_status'] = 'verification_successful'
            else:
                results['final_status'] = 'verification_failed_alternatives_created'
            
            results['completed_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Cleanup MCP servers
            for server in mcp_servers:
                try:
                    if server.poll() is None:
                        server.terminate()
                        time.sleep(1)
                        if server.poll() is None:
                            server.kill()
                except:
                    pass
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Verification process error: {e}")
            results['final_status'] = 'process_failed'
            results['error'] = str(e)
            return results
    
    def print_verification_summary(self, results: Dict[str, Any]):
        """Print comprehensive verification summary"""
        print("\n" + "="*80)
        print("🔍 MCP-POWERED CONTRACT VERIFICATION SUMMARY")
        print("="*80)
        
        print(f"\n📍 Contract Address: {results['contract_address']}")
        print(f"📅 Started: {results.get('started_at', 'N/A')}")
        print(f"📅 Completed: {results.get('completed_at', 'N/A')}")
        print(f"🎯 Final Status: {results.get('final_status', 'unknown').upper()}")
        
        # Verification results
        verification = results.get('verification', {})
        if verification.get('success'):
            print(f"\n✅ VERIFICATION SUCCESSFUL!")
            print(f"📋 Status: {verification.get('status', 'verified').upper()}")
            print(f"🔄 Attempts: {verification.get('attempts', 'N/A')}")
            print(f"🌐 View verified contract: https://polygonscan.com/address/{results['contract_address']}")
        else:
            print(f"\n⚠️  AUTOMATIC VERIFICATION FAILED!")
            print(f"❌ Error: {verification.get('error', 'Unknown error')}")
            print(f"🔄 Attempts made: {verification.get('attempts', 'N/A')}")
        
        # Alternative methods
        alternatives = results.get('alternatives', {})
        if alternatives:
            print(f"\n📚 ALTERNATIVE VERIFICATION METHODS CREATED:")
            for method, path in alternatives.items():
                print(f"   ✅ {method.replace('_', ' ').title()}: {path}")
        
        # MCP servers used
        mcp_servers = results.get('mcp_servers', [])
        if mcp_servers:
            print(f"\n🤖 MCP SERVERS USED:")
            for i, server in enumerate(mcp_servers):
                status = "✅ Active" if server.get('running') else "❌ Stopped"
                print(f"   Server {i+1}: PID {server.get('pid')} - {status}")
        
        print(f"\n🎯 NEXT STEPS:")
        if verification.get('success'):
            print("   ✅ Contract is now verified on Polygonscan")
            print("   🔧 You can interact with verified contract functions")
            print("   📊 Monitor contract activity and events")
        else:
            print("   📋 Use the manual verification guide")
            print("   🌐 Visit https://polygonscan.com/verifyContract")
            print("   📁 Use the generated files for manual submission")
        
        print("\n" + "="*80)

async def main():
    """Main verification execution"""
    print("🚀 Starting MCP-Powered Contract Verification...")
    
    verifier = MCPContractVerifier()
    
    # Execute verification
    results = await verifier.execute_verification_process()
    
    # Print summary
    verifier.print_verification_summary(results)
    
    # Save results
    with open('mcp_verification_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to: mcp_verification_results.json")

if __name__ == "__main__":
    asyncio.run(main())
