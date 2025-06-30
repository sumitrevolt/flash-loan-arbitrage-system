// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import {IPool} from "@aave/core-v3/contracts/interfaces/IPool.sol";
import {IFlashLoanSimpleReceiver} from "@aave/core-v3/contracts/interfaces/IFlashLoanSimpleReceiver.sol";
import {IPoolAddressesProvider} from "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract WorkingFlashLoanArbitrage is IFlashLoanSimpleReceiver {
    IPoolAddressesProvider public immutable ADDRESSES_PROVIDER;
    IPool public immutable POOL;
    
    address public owner;
    uint256 public flashLoanCount;
    
    event FlashLoanExecuted(address asset, uint256 amount, uint256 premium);
    event ArbitrageCompleted(address asset, uint256 amount, uint256 profit);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    constructor(address _addressProvider) {
        ADDRESSES_PROVIDER = IPoolAddressesProvider(_addressProvider);
        POOL = IPool(IPoolAddressesProvider(_addressProvider).getPool());
        owner = msg.sender;
        flashLoanCount = 0;
    }
    
    // Main function that our scripts call
    function executeArbitrage(
        address asset,
        uint256 amount,
        bytes calldata params
    ) external onlyOwner {
        // Request flash loan from Aave
        POOL.flashLoanSimple(
            address(this),
            asset,
            amount,
            params,
            0 // referralCode
        );
        
        flashLoanCount++;
    }
    
    // Aave flash loan callback
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(POOL), "Only Aave pool can call this");
        require(initiator == address(this), "Only this contract can initiate");
        
        emit FlashLoanExecuted(asset, amount, premium);
        
        // Arbitrage logic would go here
        // For demo purposes, we'll just ensure we have enough to repay
        uint256 totalDebt = amount + premium;
        
        // Check we have enough to repay (in a real scenario, this would come from arbitrage profit)
        uint256 balance = IERC20(asset).balanceOf(address(this));
        
        // If we don't have enough, the transaction will fail (which is expected for testing)
        // In production, this is where arbitrage logic would generate profit
        
        // For demo: simulate a small profit scenario
        if (balance >= totalDebt) {
            emit ArbitrageCompleted(asset, amount, balance - totalDebt);
        }
        
        // Approve the pool to pull the debt + premium
        IERC20(asset).approve(address(POOL), totalDebt);
        
        return true;
    }
    
    // Getter functions that our scripts expect
    function getOwner() external view returns (address) {
        return owner;
    }
    
    function getFlashLoanCount() external view returns (uint256) {
        return flashLoanCount;
    }
    
    // Emergency functions
    function withdrawToken(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner, amount);
    }
    
    function withdrawETH() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
    
    // Allow contract to receive ETH
    receive() external payable {}
} 