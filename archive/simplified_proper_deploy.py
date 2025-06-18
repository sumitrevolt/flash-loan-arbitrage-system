#!/usr/bin/env python3
"""
Simplified Contract Deployment with Correct Dependencies
Using a simpler approach with proper Solidity compilation
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

class SimplifiedContractDeployer:
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
        
        # Set up Solidity compiler (use 0.8.10 to match the contract)
        self.solc_version = "0.8.10"
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
    
    def create_simple_flash_loan_contract(self) -> str:
        """Create a simplified flash loan contract that will actually compile"""
        return '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

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

interface IPoolAddressesProvider {
    function getPool() external view returns (address);
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
}

interface IFlashLoanReceiver {
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}

abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }
}

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

contract FlashLoanArbitrageFixed is IFlashLoanReceiver, Ownable, ReentrancyGuard {
    IPoolAddressesProvider public immutable addressesProvider;
    IPool public immutable pool;
    
    // Events
    event FlashLoanExecuted(address indexed asset, uint256 amount, uint256 premium);
    event ProfitWithdrawn(address indexed token, uint256 amount);
    
    // Errors
    error UnauthorizedFlashLoan();
    error InsufficientBalance();
    error TransferFailed();
    
    constructor(address _addressesProvider) {
        addressesProvider = IPoolAddressesProvider(_addressesProvider);
        pool = IPool(addressesProvider.getPool());
    }
    
    /**
     * @dev Execute flash loan operation
     */
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        // Verify the caller is the AAVE pool
        require(msg.sender == address(pool), "Caller must be AAVE pool");
        require(initiator == address(this), "Initiator must be this contract");
        
        // Perform arbitrage logic here
        // For now, just ensure we have enough balance to repay
        for (uint256 i = 0; i < assets.length; i++) {
            uint256 totalRepayment = amounts[i] + premiums[i];
            
            // Check if we have enough balance to repay
            IERC20 asset = IERC20(assets[i]);
            require(asset.balanceOf(address(this)) >= totalRepayment, "Insufficient balance for repayment");
            
            // Approve the pool to pull the funds
            asset.approve(address(pool), totalRepayment);
        }
        
        emit FlashLoanExecuted(assets[0], amounts[0], premiums[0]);
        return true;
    }
    
    /**
     * @dev Execute flash loan
     */
    function executeFlashLoan(
        address asset,
        uint256 amount
    ) external onlyOwner nonReentrant {
        address[] memory assets = new address[](1);
        uint256[] memory amounts = new uint256[](1);
        uint256[] memory modes = new uint256[](1);
        
        assets[0] = asset;
        amounts[0] = amount;
        modes[0] = 0; // no debt
        
        pool.flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            "",
            0
        );
    }
    
    /**
     * @dev Withdraw profits
     */
    function withdrawProfit(address token, uint256 amount) external onlyOwner {
        IERC20 tokenContract = IERC20(token);
        require(tokenContract.balanceOf(address(this)) >= amount, "Insufficient balance");
        
        bool success = tokenContract.transfer(owner(), amount);
        require(success, "Transfer failed");
        
        emit ProfitWithdrawn(token, amount);
    }
    
    /**
     * @dev Emergency withdraw all tokens
     */
    function emergencyWithdraw(address token) external onlyOwner {
        IERC20 tokenContract = IERC20(token);
        uint256 balance = tokenContract.balanceOf(address(this));
        if (balance > 0) {
            bool success = tokenContract.transfer(owner(), balance);
            require(success, "Emergency withdraw failed");
        }
    }
    
    /**
     * @dev Get contract balance for a token
     */
    function getBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }
    
    // Receive function to accept ETH
    receive() external payable {}
}
'''
    
    def compile_contract(self) -> Dict[str, Any]:
        """Compile the simplified contract"""
        try:
            logger.info("Compiling simplified FlashLoanArbitrageFixed contract...")
            
            contract_source = self.create_simple_flash_loan_contract()
            
            # Compile with optimization
            compiled_sol = compile_source(
                contract_source,
                output_values=['abi', 'bin', 'bin-runtime'],
                solc_version=self.solc_version,
                optimize=True,
                optimize_runs=200
            )
            
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
            # Polygon AAVE V3 PoolAddressesProvider
            pool_addresses_provider = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"
            
            # Build transaction
            constructor_args = [pool_addresses_provider]
            
            transaction = contract.constructor(*constructor_args).build_transaction({
                'from': self.wallet_address,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'gas': 2000000,  # Reasonable gas limit
                'gasPrice': self.w3.to_wei('50', 'gwei'),
                'chainId': 137
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt['status'] == 1:
                contract_address = tx_receipt['contractAddress']
                logger.info(f"Contract deployed successfully at: {contract_address}")
                
                # Save deployment info
                deployment_info = {
                    'contract_address': contract_address,
                    'transaction_hash': tx_hash.hex(),
                    'block_number': tx_receipt['blockNumber'],
                    'gas_used': tx_receipt['gasUsed'],
                    'constructor_args': constructor_args,
                    'compiler_version': self.solc_version,
                    'optimization': True,
                    'optimization_runs': 200,
                    'contract_source': self.create_simple_flash_loan_contract()
                }
                
                with open('simplified_deployment_info.json', 'w') as f:
                    json.dump(deployment_info, f, indent=2, default=str)
                
                return contract_address
            else:
                raise Exception("Transaction failed")
                
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise
    
    def verify_contract_on_polygonscan(self, contract_address: str):
        """Verify the contract on Polygonscan"""
        try:
            logger.info(f"Verifying contract {contract_address} on Polygonscan...")
            
            # Get the source code
            source_code = self.create_simple_flash_loan_contract()
            
            # Prepare verification data
            verification_data = {
                'apikey': self.polygonscan_api_key,
                'module': 'contract',
                'action': 'verifysourcecode',
                'contractaddress': contract_address,
                'sourceCode': source_code,
                'codeformat': 'solidity-single-file',
                'contractname': 'FlashLoanArbitrageFixed',
                'compilerversion': f'v{self.solc_version}+commit.7a7e1d8a',  # Correct commit for 0.8.10
                'optimizationUsed': '1',
                'runs': '200',
                'constructorArguements': '000000000000000000000000a97684ead0e402dc232d5a977953df7ecbab3cdb',  # Encoded constructor args
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
        deployer = SimplifiedContractDeployer()
        
        # Compile contract
        contract_interface = deployer.compile_contract()
        
        # Deploy contract
        contract_address = deployer.deploy_contract(contract_interface)
        
        # Verify contract
        verified = deployer.verify_contract_on_polygonscan(contract_address)
        
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
