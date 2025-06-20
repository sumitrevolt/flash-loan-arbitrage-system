#!/usr/bin/env python3
"""
Advanced Contract Verification System
Fixes all errors and automatically verifies the contract
"""

import os
import requests
import time
import json
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

class ContractVerifier:
    def __init__(self):
        self.contract_address = "0xb5855560f3558844dCC5856BDa33D2fb7BD4B04F"
        self.api_key = os.getenv("POLYGONSCAN_API_KEY")
        self.polygon_rpc = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
        self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
        
        if not self.api_key:
            raise ValueError("POLYGONSCAN_API_KEY not found in .env file")
        
        print(f"🔧 Initializing Contract Verifier")
        print(f"📍 Contract: {self.contract_address}")
        print(f"🔑 API Key: {self.api_key[:10]}...")
        print(f"🌐 RPC: {self.polygon_rpc}")

    def get_contract_bytecode(self):
        """Get the actual deployed bytecode"""
        try:
            bytecode = self.web3.eth.get_code(self.contract_address)
            print(f"📊 Contract bytecode length: {len(bytecode)} bytes")
            return bytecode.hex()
        except Exception as e:
            print(f"❌ Error getting bytecode: {e}")
            return None

    def get_transaction_details(self):
        """Get contract creation transaction details"""
        api_url = "https://api.polygonscan.com/api"
        
        # Get contract creation info
        params = {
            'module': 'contract',
            'action': 'getcontractcreation',
            'contractaddresses': self.contract_address,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(api_url, params=params)
            result = response.json()
            
            if result.get('status') == '1' and result.get('result'):
                creation_info = result['result'][0]
                print(f"🏗️  Contract Creator: {creation_info.get('contractCreator')}")
                print(f"📊 Creation Tx: {creation_info.get('txHash')}")
                return creation_info
            else:
                print(f"⚠️  Couldn't get creation info: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting creation info: {e}")
            return None

    def create_optimized_source_code(self):
        """Create optimized source code that should match deployment"""
        
        # This is a corrected version based on the deployment
        source_code = '''// SPDX-License-Identifier: MIT
pragma solidity 0.8.10;

// Minimal implementations of required interfaces and contracts

abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
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

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

abstract contract Pausable is Context {
    event Paused(address account);
    event Unpaused(address account);
    
    bool private _paused;
    
    constructor() {
        _paused = false;
    }
    
    function paused() public view virtual returns (bool) {
        return _paused;
    }
    
    modifier whenNotPaused() {
        require(!paused(), "Pausable: paused");
        _;
    }
    
    modifier whenPaused() {
        require(paused(), "Pausable: not paused");
        _;
    }
    
    function _pause() internal virtual whenNotPaused {
        _paused = true;
        emit Paused(_msgSender());
    }
    
    function _unpause() internal virtual whenPaused {
        _paused = false;
        emit Unpaused(_msgSender());
    }
}

interface IPoolAddressesProvider {
    function getPool() external view returns (address);
}

interface IPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

interface IFlashLoanSimpleReceiver {
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool);
    
    function ADDRESSES_PROVIDER() external view returns (IPoolAddressesProvider);
    function POOL() external view returns (IPool);
}

abstract contract FlashLoanSimpleReceiverBase is IFlashLoanSimpleReceiver {
    IPoolAddressesProvider public immutable override ADDRESSES_PROVIDER;
    IPool public immutable override POOL;
    
    constructor(IPoolAddressesProvider provider) {
        ADDRESSES_PROVIDER = provider;
        POOL = IPool(provider.getPool());
    }
}

interface ISwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
    
    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}

interface IQuoter {
    function quoteExactInputSingle(
        address tokenIn,
        address tokenOut,
        uint24 fee,
        uint256 amountIn,
        uint160 sqrtPriceLimitX96
    ) external returns (uint256 amountOut);
}

interface IUniswapV2Router02 {
    function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts);
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);
}

contract FlashLoanArbitrageFixed is FlashLoanSimpleReceiverBase, Ownable, ReentrancyGuard, Pausable {
    
    address public uniswapV3Router;
    address public uniswapV3Quoter;
    address public constant WETH = 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619;
    
    mapping(address => bool) public whitelistedTokens;
    mapping(address => bool) public approvedDexes;
    uint256 public slippageTolerance = 500;
    uint256 public failedTransactionsCount = 0;
    uint256 public maxFailedTransactions = 6;
    
    uint256 public feePercentage = 500;
    address public feeRecipient;
    bool public feesEnabled = true;
    
    struct ArbitrageParams {
        address borrowToken;
        address dex1;
        address dex2;
        address intermediateToken;
        uint24 dex1Fee;
        uint24 dex2Fee;
        uint256 deadline;
        uint256 amount;
        uint256 premium;
    }
    
    struct SwapStats {
        uint256 totalSwaps;
        uint256 successfulSwaps;
        uint256 failedSwaps;
        uint256 totalProfits;
        uint256 totalFees;
        uint256 lastSwapTimestamp;
        uint256 highestProfit;
        address mostProfitableToken;
    }
    
    SwapStats public swapStats;
    
    event ArbitrageExecuted(
        address indexed token,
        uint256 amount,
        address dex1,
        address dex2,
        address intermediateToken,
        uint256 profit,
        uint256 fee,
        uint256 gasUsed,
        uint256 timestamp
    );
    
    event ArbitrageFailed(address indexed token, uint256 amount, string reason, uint256 gasUsed);
    event SwapExecuted(address indexed tokenIn, address indexed tokenOut, address indexed dex, uint256 amountIn, uint256 amountOut, uint256 timestamp);
    event DebugLog(string message, uint256 value);
    event TokenWhitelisted(address indexed token, bool status);
    event DexApprovalChanged(address dex, bool approved);
    event FeeParametersUpdated(uint256 feePercentage, address feeRecipient, bool feesEnabled);
    event ProfitDistributed(address token, uint256 totalProfit, uint256 ownerAmount, uint256 feeAmount);
    
    constructor(IPoolAddressesProvider _addressProvider)
        FlashLoanSimpleReceiverBase(_addressProvider)
        Ownable()
    {
        uniswapV3Router = 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45;
        uniswapV3Quoter = 0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6;
        feeRecipient = owner();
        
        approvedDexes[uniswapV3Router] = true;
        approvedDexes[0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff] = true;
        approvedDexes[0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506] = true;
        
        _whitelistInitialTokens();
    }
    
    function _whitelistInitialTokens() internal {
        whitelistedTokens[WETH] = true;
        whitelistedTokens[0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6] = true;
        whitelistedTokens[0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174] = true;
        whitelistedTokens[0xc2132D05D31c914a87C6611C10748AEb04B58e8F] = true;
        whitelistedTokens[0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063] = true;
        whitelistedTokens[0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270] = true;
        whitelistedTokens[0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39] = true;
        whitelistedTokens[0xD6DF932A45C0f255f85145f286eA0b292B21C90B] = true;
    }
    
    function executeArbitrage(
        address borrowToken,
        uint256 amount,
        address dex1,
        address dex2,
        address intermediateToken,
        uint24 dex1Fee,
        uint24 dex2Fee,
        uint256 deadline
    ) external nonReentrant whenNotPaused {
        require(failedTransactionsCount < maxFailedTransactions, "Circuit breaker triggered");
        _validateArbitrageParams(borrowToken, intermediateToken, dex1, dex2, amount, deadline);
        emit DebugLog("Starting arbitrage execution", block.timestamp);
        _requestFlashLoan(borrowToken, amount, dex1, dex2, intermediateToken, dex1Fee, dex2Fee, deadline);
    }
    
    function _validateArbitrageParams(
        address borrowToken,
        address intermediateToken,
        address dex1,
        address dex2,
        uint256 amount,
        uint256 deadline
    ) internal view {
        require(whitelistedTokens[borrowToken] && whitelistedTokens[intermediateToken], "Invalid token");
        require(approvedDexes[dex1] && approvedDexes[dex2], "Invalid DEX");
        require(amount > 0, "Invalid amount");
        require(deadline > block.timestamp, "Invalid deadline");
    }
    
    function _requestFlashLoan(
        address borrowToken,
        uint256 amount,
        address dex1,
        address dex2,
        address intermediateToken,
        uint24 dex1Fee,
        uint24 dex2Fee,
        uint256 deadline
    ) internal {
        uint256 initialGas = gasleft();
        
        try POOL.flashLoanSimple(
            address(this),
            borrowToken,
            amount,
            abi.encode(borrowToken, dex1, dex2, intermediateToken, dex1Fee, dex2Fee, deadline),
            0
        ) {
            failedTransactionsCount = 0;
        } catch Error(string memory reason) {
            failedTransactionsCount++;
            emit ArbitrageFailed(borrowToken, amount, reason, initialGas - gasleft());
        } catch {
            failedTransactionsCount++;
            emit ArbitrageFailed(borrowToken, amount, "Unknown error", initialGas - gasleft());
        }
    }
    
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(POOL), "Caller must be Aave lending pool");
        
        ArbitrageParams memory arbParams = _decodeParams(params);
        arbParams.amount = amount;
        arbParams.premium = premium;
        
        _executeArbitrageStrategy(arbParams);
        return true;
    }
    
    function _decodeParams(bytes calldata params) internal pure returns (ArbitrageParams memory) {
        (
            address borrowToken,
            address dex1,
            address dex2,
            address intermediateToken,
            uint24 dex1Fee,
            uint24 dex2Fee,
            uint256 deadline
        ) = abi.decode(params, (address, address, address, address, uint24, uint24, uint256));
        
        return ArbitrageParams({
            borrowToken: borrowToken,
            dex1: dex1,
            dex2: dex2,
            intermediateToken: intermediateToken,
            dex1Fee: dex1Fee,
            dex2Fee: dex2Fee,
            deadline: deadline,
            amount: 0,
            premium: 0
        });
    }
    
    function _executeArbitrageStrategy(ArbitrageParams memory params) internal {
        uint256 amountToRepay = params.amount + params.premium;
        
        IERC20(params.borrowToken).approve(params.dex1, params.amount);
        uint256 intermediateAmount = _executeSwap(params.borrowToken, params.intermediateToken, params.amount, params.dex1, params.dex1Fee, params.deadline);
        IERC20(params.borrowToken).approve(params.dex1, 0);
        
        if (intermediateAmount > 0) {
            IERC20(params.intermediateToken).approve(params.dex2, intermediateAmount);
            uint256 finalAmount = _executeSwap(params.intermediateToken, params.borrowToken, intermediateAmount, params.dex2, params.dex2Fee, params.deadline);
            IERC20(params.intermediateToken).approve(params.dex2, 0);
            
            if (finalAmount > amountToRepay) {
                uint256 profit = finalAmount - amountToRepay;
                _handleProfit(params, profit);
            }
        }
        
        IERC20(params.borrowToken).approve(address(POOL), amountToRepay);
    }
    
    function _handleProfit(ArbitrageParams memory params, uint256 profit) internal {
        swapStats.totalSwaps++;
        swapStats.successfulSwaps++;
        swapStats.totalProfits += profit;
        swapStats.lastSwapTimestamp = block.timestamp;
        
        if (profit > swapStats.highestProfit) {
            swapStats.highestProfit = profit;
            swapStats.mostProfitableToken = params.borrowToken;
        }
        
        uint256 feeAmount = 0;
        if (feesEnabled && feeRecipient != address(0)) {
            feeAmount = profit * feePercentage / 10000;
            swapStats.totalFees += feeAmount;
            if (feeAmount > 0) {
                IERC20(params.borrowToken).transfer(feeRecipient, feeAmount);
            }
        }
        
        uint256 ownerAmount = profit - feeAmount;
        IERC20(params.borrowToken).transfer(owner(), ownerAmount);
        
        emit ArbitrageExecuted(params.borrowToken, params.amount, params.dex1, params.dex2, params.intermediateToken, profit, feeAmount, gasleft(), block.timestamp);
        emit ProfitDistributed(params.borrowToken, profit, ownerAmount, feeAmount);
    }
    
    function _executeSwap(address tokenIn, address tokenOut, uint256 amountIn, address router, uint24 fee, uint256 deadline) internal returns (uint256) {
        if (router == uniswapV3Router) {
            return _swapOnUniswapV3(tokenIn, tokenOut, amountIn, router, fee, deadline);
        } else {
            return _swapOnUniswapV2(tokenIn, tokenOut, amountIn, router, deadline);
        }
    }
    
    function _swapOnUniswapV3(address tokenIn, address tokenOut, uint256 amountIn, address router, uint24 fee, uint256 deadline) internal returns (uint256) {
        uint256 expectedAmountOut = _getUniswapV3Quote(tokenIn, tokenOut, fee, amountIn);
        uint256 amountOutMinimum = expectedAmountOut * (10000 - slippageTolerance) / 10000;
        
        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            fee: fee,
            recipient: address(this),
            deadline: deadline,
            amountIn: amountIn,
            amountOutMinimum: amountOutMinimum,
            sqrtPriceLimitX96: 0
        });
        
        uint256 amountOut = ISwapRouter(router).exactInputSingle(params);
        emit SwapExecuted(tokenIn, tokenOut, router, amountIn, amountOut, block.timestamp);
        return amountOut;
    }
    
    function _getUniswapV3Quote(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn) internal returns (uint256) {
        if (amountIn == 0) return 0;
        
        try IQuoter(uniswapV3Quoter).quoteExactInputSingle(tokenIn, tokenOut, fee, amountIn, 0) returns (uint256 amountOut) {
            return amountOut;
        } catch {
            return 0;
        }
    }
    
    function _swapOnUniswapV2(address tokenIn, address tokenOut, uint256 amountIn, address router, uint256 deadline) internal returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;
        
        uint256[] memory expectedAmounts = IUniswapV2Router02(router).getAmountsOut(amountIn, path);
        uint256 amountOutMin = expectedAmounts[1] * (10000 - slippageTolerance) / 10000;
        
        uint256[] memory amounts = IUniswapV2Router02(router).swapExactTokensForTokens(amountIn, amountOutMin, path, address(this), deadline);
        
        uint256 amountOut = amounts[amounts.length - 1];
        emit SwapExecuted(tokenIn, tokenOut, router, amountIn, amountOut, block.timestamp);
        return amountOut;
    }
    
    function whitelistToken(address token, bool status) public onlyOwner whenNotPaused {
        whitelistedTokens[token] = status;
        emit TokenWhitelisted(token, status);
    }
    
    function withdrawToken(address token, uint256 amount) external onlyOwner whenNotPaused {
        IERC20(token).transfer(owner(), amount);
    }
    
    function pause() public onlyOwner {
        _pause();
    }
    
    function unpause() public onlyOwner {
        _unpause();
    }
    
    receive() external payable {}
}'''
        
        return source_code

    def try_verification_with_multiple_settings(self):
        """Try verification with multiple compiler settings"""
        
        source_code = self.create_optimized_source_code()
        
        # Different settings to try
        verification_configs = [
            {
                'compiler': 'v0.8.10+commit.fc410830',
                'optimization': '1',
                'runs': '200',
                'evm': 'london'
            },
            {
                'compiler': 'v0.8.10+commit.fc410830',
                'optimization': '0',
                'runs': '200',
                'evm': 'london'
            },
            {
                'compiler': 'v0.8.19+commit.7dd6d404',
                'optimization': '1',
                'runs': '200',
                'evm': 'london'
            },
            {
                'compiler': 'v0.8.20+commit.a1b79de6',
                'optimization': '1',
                'runs': '200',
                'evm': 'london'
            },
            {
                'compiler': 'v0.8.10+commit.fc410830',
                'optimization': '1',
                'runs': '1000',
                'evm': 'london'
            }
        ]
        
        for i, config in enumerate(verification_configs, 1):
            print(f"\n🔄 Trying verification config {i}/{len(verification_configs)}")
            print(f"   Compiler: {config['compiler']}")
            print(f"   Optimization: {config['optimization']}")
            print(f"   Runs: {config['runs']}")
            print(f"   EVM: {config['evm']}")
            
            success = self.submit_verification(source_code, config)
            if success:
                return True
            
            # Wait between attempts
            time.sleep(5)
        
        return False

    def submit_verification(self, source_code, config):
        """Submit verification with specific config"""
        
        api_url = "https://api.polygonscan.com/api"
        
        verification_data = {
            'apikey': self.api_key,
            'module': 'contract',
            'action': 'verifysourcecode',
            'contractaddress': self.contract_address,
            'sourceCode': source_code,
            'codeformat': 'solidity-single-file',
            'contractname': 'FlashLoanArbitrageFixed',
            'compilerversion': config['compiler'],
            'optimizationUsed': config['optimization'],
            'runs': config['runs'],
            'constructorArguments': '000000000000000000000000a97684ead0e402dc232d5a977953df7ecbab3cdb',
            'evmversion': config['evm'],
            'licenseType': '3',
        }
        
        try:
            response = requests.post(api_url, data=verification_data)
            result = response.json()
            
            print(f"📡 Response: {result}")
            
            if result.get('status') == '1':
                guid = result.get('result')
                print(f"✅ Verification submitted! GUID: {guid}")
                
                # Check status
                return self.check_verification_status(guid)
            else:
                print(f"❌ Submission failed: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error submitting verification: {e}")
            return False

    def check_verification_status(self, guid, max_attempts=10):
        """Check verification status"""
        
        api_url = "https://api.polygonscan.com/api"
        
        for attempt in range(max_attempts):
            try:
                status_params = {
                    'apikey': self.api_key,
                    'module': 'contract',
                    'action': 'checkverifystatus',
                    'guid': guid
                }
                
                response = requests.get(api_url, params=status_params)
                result = response.json()
                
                print(f"🔄 Check {attempt + 1}: {result}")
                
                if result.get('status') == '1':
                    if result.get('result') == 'Pass - Verified':
                        print(f"🎉 SUCCESS! CONTRACT VERIFIED!")
                        print(f"🔗 View: https://polygonscan.com/address/{self.contract_address}#code")
                        return True
                    elif 'Pending' in str(result.get('result', '')):
                        print(f"⏳ Still pending...")
                        time.sleep(10)
                        continue
                    else:
                        print(f"❌ Failed: {result.get('result')}")
                        return False
                else:
                    if 'Pending in queue' in str(result.get('result', '')):
                        print(f"⏳ In queue...")
                        time.sleep(10)
                        continue
                    else:
                        print(f"❌ Status error: {result}")
                        return False
                        
            except Exception as e:
                print(f"❌ Error checking status: {e}")
                time.sleep(5)
                continue
        
        print("⏰ Status check timed out")
        return False

    def verify_contract(self):
        """Main verification function"""
        
        print("🚀 Starting Advanced Contract Verification")
        print("=" * 50)
        
        # Get contract info
        print("\n1️⃣ Getting contract information...")
        bytecode = self.get_contract_bytecode()
        creation_info = self.get_transaction_details()
        
        # Try verification
        print("\n2️⃣ Attempting verification with multiple configurations...")
        success = self.try_verification_with_multiple_settings()
        
        if success:
            print("\n🎉 CONTRACT SUCCESSFULLY VERIFIED!")
            return True
        else:
            print("\n⚠️  Automatic verification failed")
            print("💡 Try manual verification on Polygonscan")
            return False

def main():
    try:
        verifier = ContractVerifier()
        verifier.verify_contract()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return False

if __name__ == "__main__":
    main()
