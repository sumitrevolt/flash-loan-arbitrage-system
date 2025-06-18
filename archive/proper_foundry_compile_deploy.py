#!/usr/bin/env python3
"""
Proper Contract Compilation and Deployment
Using py-solc-x to compile FlashLoanArbitrageFixed with all dependencies
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ProperContractDeployer:
    def __init__(self):
        self.private_key = os.getenv('PRIVATE_KEY')
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.polygonscan_api_key = os.getenv('POLYGONSCAN_API_KEY')
        
        # Polygon RPC
        self.rpc_url = "https://polygon-rpc.com"
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Verify connection
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Polygon network")
        
        logger.info(f"Connected to Polygon. Chain ID: {self.w3.eth.chain_id}")
        logger.info(f"Wallet address: {self.wallet_address}")
        
        # Set up Solidity compiler
        self.solc_version = "0.8.20"
        self.setup_solidity_compiler()
        
    def setup_solidity_compiler(self):
        """Setup Solidity compiler with correct version"""
        try:
            # Install and set the correct version
            install_solc(self.solc_version)
            set_solc_version(self.solc_version)
            logger.info(f"Solidity compiler version {self.solc_version} installed and set")
        except Exception as e:
            logger.error(f"Failed to setup Solidity compiler: {e}")
            raise
    def get_contract_source_with_imports(self) -> Dict[str, str]:
        """Get the complete contract source with all imports resolved"""
        
        # Read the main contract
        main_contract_path = Path("core/contracts/FlashLoanArbitrageFixed.sol")
        if not main_contract_path.exists():
            raise FileNotFoundError(f"Contract file not found: {main_contract_path}")
        
        with open(main_contract_path, 'r') as f:
            main_contract = f.read()
        
        # OpenZeppelin and Aave contracts (we'll include the essential ones directly)
        contracts = {
            "FlashLoanArbitrageFixed.sol": main_contract,
            
            # Essential OpenZeppelin contracts
            "@openzeppelin/contracts/security/ReentrancyGuard.sol": '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

abstract contract ReentrancyGuard {
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;
    uint256 private _status;

    constructor() {
        _status = _NOT_ENTERED;
    }

    modifier nonReentrant() {
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }
}
''',
            
            "@openzeppelin/contracts/access/Ownable.sol": '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Context.sol";

abstract contract Ownable is Context {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    constructor() {
        _transferOwnership(_msgSender());
    }

    function owner() public view virtual returns (address) {
        return _owner;
    }

    modifier onlyOwner() {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    function renounceOwnership() public virtual onlyOwner {
        _transferOwnership(address(0));
    }

    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        _transferOwnership(newOwner);
    }

    function _transferOwnership(address newOwner) internal virtual {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}
''',
            
            "@openzeppelin/contracts/utils/Context.sol": '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }
}
''',
            
            # Essential AAVE interfaces
            "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol": '''
// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.0;

interface IPoolAddressesProvider {
    function getPool() external view returns (address);
    function getPriceOracle() external view returns (address);
}
''',
            
            "@aave/core-v3/contracts/interfaces/IPool.sol": '''
// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.0;

struct DataTypes {
    struct ReserveData {
        uint256 configuration;
        uint128 liquidityIndex;
        uint128 currentLiquidityRate;
        uint128 variableBorrowIndex;
        uint128 currentVariableBorrowRate;
        uint128 currentStableBorrowRate;
        uint40 lastUpdateTimestamp;
        uint16 id;
        address aTokenAddress;
        address stableDebtTokenAddress;
        address variableDebtTokenAddress;
        address interestRateStrategyAddress;
        uint128 accruedToTreasury;
        uint128 unbacked;
        uint128 isolationModeTotalDebt;
    }
}

interface IPool {
    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata modes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external;
    
    function getReserveData(address asset) external view returns (DataTypes.ReserveData memory);
}
''',
            
            "@aave/core-v3/contracts/flashloan/interfaces/IFlashLoanReceiver.sol": '''
// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.0;

interface IFlashLoanReceiver {
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}
''',
            
            # Essential ERC20 interface
            "@openzeppelin/contracts/token/ERC20/IERC20.sol": '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}
'''
        }
        
        return contracts
    
    def compile_contract(self) -> Dict[str, Any]:
        """Compile the contract using py-solc-x"""
        try:
            logger.info("Compiling FlashLoanArbitrageFixed contract...")
            
            contracts_source = self.get_contract_source_with_imports()
              # Compile with optimization - using file-based compilation
            from solcx import compile_files
            
            # Create a temporary contract file with all imports flattened
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False)
            
            # Flatten all imports into one file
            flattened_source = ""
            for filename, source in contracts_source.items():
                if filename == "FlashLoanArbitrageFixed.sol":
                    # Replace import statements with actual contract content
                    flattened_source = source
                    for import_path in ["@openzeppelin/contracts/security/ReentrancyGuard.sol",
                                      "@openzeppelin/contracts/access/Ownable.sol",
                                      "@openzeppelin/contracts/utils/Context.sol",
                                      "@openzeppelin/contracts/token/ERC20/IERC20.sol",
                                      "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol",
                                      "@aave/core-v3/contracts/interfaces/IPool.sol",
                                      "@aave/core-v3/contracts/flashloan/interfaces/IFlashLoanReceiver.sol"]:
                        import_line = f'import "{import_path}";'
                        if import_line in flattened_source:
                            flattened_source = flattened_source.replace(import_line, f"// {import_line}")
            
            # Add all the dependency contracts to the flattened source
            dependencies = ""
            for filename, source in contracts_source.items():
                if filename != "FlashLoanArbitrageFixed.sol":
                    dependencies += f"{source}\n\n"
            
            flattened_source = dependencies + flattened_source
            
            temp_file.write(flattened_source)
            temp_file.close()
            
            compiled_sol = compile_files(
                [temp_file.name],
                output_values=['abi', 'bin', 'bin-runtime'],
                solc_version=self.solc_version,
                optimize=True,
                optimize_runs=200
            )
            
            # Clean up temp file
            import os
            os.unlink(temp_file.name)
            
            # Find the main contract
            contract_interface = None
            for contract_name, contract_data in compiled_sol.items():
                if 'FlashLoanArbitrageFixed' in contract_name:
                    contract_interface = contract_data
                    break
            
            if not contract_interface:
                raise ValueError("FlashLoanArbitrageFixed contract not found in compilation output")
            
            logger.info("Contract compiled successfully!")
            logger.info(f"Bytecode length: {len(contract_interface['bin'])} characters")
            logger.info(f"ABI functions: {len(contract_interface['abi'])}")
            
            return contract_interface
            
        except Exception as e:
            logger.error(f"Compilation failed: {e}")
            raise
    
    def deploy_contract(self, contract_interface: Dict[str, Any]) -> str:
        """Deploy the compiled contract"""
        try:
            logger.info("Deploying FlashLoanArbitrageFixed contract...")
            
            # Get account
            account = self.w3.eth.account.from_key(self.private_key)
            
            # Create contract instance
            contract = self.w3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            
            # Constructor arguments for FlashLoanArbitrageFixed
            # These need to be the correct Polygon addresses
            pool_addresses_provider = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"  # Polygon AAVE V3
            
            # Build transaction
            constructor_args = [pool_addresses_provider]
            
            transaction = contract.constructor(*constructor_args).build_transaction({
                'from': self.wallet_address,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'gas': 3000000,  # Increased gas limit
                'gasPrice': self.w3.to_wei('50', 'gwei'),
                'chainId': 137
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt.status == 1:
                contract_address = tx_receipt.contractAddress
                logger.info(f"Contract deployed successfully at: {contract_address}")
                
                # Save deployment info
                deployment_info = {
                    'contract_address': contract_address,
                    'transaction_hash': tx_hash.hex(),
                    'block_number': tx_receipt.blockNumber,
                    'gas_used': tx_receipt.gasUsed,
                    'constructor_args': constructor_args,
                    'compiler_version': self.solc_version,
                    'optimization': True,
                    'optimization_runs': 200
                }
                
                with open('deployment_info.json', 'w') as f:
                    json.dump(deployment_info, f, indent=2, default=str)
                
                return contract_address
            else:
                raise Exception("Transaction failed")
                
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise
    
    def verify_contract_on_polygonscan(self, contract_address: str, contract_interface: Dict[str, Any]):
        """Verify the contract on Polygonscan"""
        try:
            logger.info(f"Verifying contract {contract_address} on Polygonscan...")
            
            # Read the flattened source code
            contracts_source = self.get_contract_source_with_imports()
            
            # Combine all sources into one flattened file
            flattened_source = ""
            for filename, source in contracts_source.items():
                flattened_source += f"// File: {filename}\n{source}\n\n"
            
            # Prepare verification data
            verification_data = {
                'apikey': self.polygonscan_api_key,
                'module': 'contract',
                'action': 'verifysourcecode',
                'contractaddress': contract_address,
                'sourceCode': flattened_source,
                'codeformat': 'solidity-single-file',
                'contractname': 'FlashLoanArbitrageFixed',
                'compilerversion': f'v{self.solc_version}+commit.a4f2e591',
                'optimizationUsed': '1',
                'runs': '200',
                'constructorArguements': '',  # Will be filled if needed
                'evmversion': 'default',
                'licenseType': '3'  # MIT License
            }
            
            # Submit verification
            response = requests.post(
                'https://api.polygonscan.com/api',
                data=verification_data,
                timeout=30
            )
            
            result = response.json()
            if result.get('status') == '1':
                guid = result.get('result')
                logger.info(f"Verification submitted. GUID: {guid}")
                
                # Check verification status
                import time
                for i in range(10):  # Try 10 times
                    time.sleep(15)  # Wait 15 seconds between checks
                    
                    status_response = requests.get(
                        'https://api.polygonscan.com/api',
                        params={
                            'apikey': self.polygonscan_api_key,
                            'module': 'contract',
                            'action': 'checkverifystatus',
                            'guid': guid
                        },
                        timeout=30
                    )
                    
                    status_result = status_response.json()
                    if status_result.get('status') == '1':
                        logger.info("Contract verified successfully!")
                        return True
                    elif status_result.get('status') == '0' and 'Pending' not in status_result.get('result', ''):
                        logger.error(f"Verification failed: {status_result.get('result')}")
                        return False
                    
                    logger.info(f"Verification pending... (attempt {i+1}/10)")
                
                logger.warning("Verification status check timed out")
                return False
            else:
                logger.error(f"Verification submission failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

def main():
    """Main deployment function"""
    try:
        deployer = ProperContractDeployer()
        
        # Compile contract
        contract_interface = deployer.compile_contract()
        
        # Deploy contract
        contract_address = deployer.deploy_contract(contract_interface)
        
        # Verify contract
        verified = deployer.verify_contract_on_polygonscan(contract_address, contract_interface)
        
        print(f"\n{'='*60}")
        print("DEPLOYMENT COMPLETE!")
        print(f"{'='*60}")
        print(f"Contract Address: {contract_address}")
        print(f"Verified on Polygonscan: {'Yes' if verified else 'No'}")
        print(f"Polygonscan URL: https://polygonscan.com/address/{contract_address}")
        print(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Deployment process failed: {e}")
        raise

if __name__ == "__main__":
    main()
