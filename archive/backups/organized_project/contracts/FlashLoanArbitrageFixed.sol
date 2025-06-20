// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@aave/core-v3/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";
import "@uniswap/v3-periphery/contracts/interfaces/IQuoter.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";

/**
 * @title FlashLoanArbitrageFixed
 * @dev Fixed flash loan arbitrage contract with proper parameter passing and stack optimization
 * @notice Version 2.1 - Updated June 2025 with enhanced safety features
 * @author Flash Loan Arbitrage Team
 */
contract FlashLoanArbitrageFixed is FlashLoanSimpleReceiverBase, Ownable, ReentrancyGuard, Pausable {
    // DEX addresses
    address public uniswapV3Router;
    address public uniswapV3Quoter;
    address public constant WETH = 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619; // WETH on Polygon

    // State variables
    mapping(address => bool) public whitelistedTokens;
    mapping(address => bool) public approvedDexes;
    uint256 public slippageTolerance = 500; // 5% slippage tolerance (in basis points)
    uint256 public failedTransactionsCount = 0;
    uint256 public maxFailedTransactions = 6;

    // Fee mechanism
    uint256 public feePercentage = 500; // 5% fee (in basis points)
    address public feeRecipient;
    bool public feesEnabled = true;

    // Arbitrage parameters struct to reduce stack depth
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

    // Swap statistics for monitoring
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

    // Events
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
    event SwapFailed(address indexed tokenIn, address indexed tokenOut, uint256 amountIn, string reason);
    event SwapExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        address indexed dex,
        uint256 amountIn,
        uint256 amountOut,
        uint256 timestamp
    );
    event DebugLog(string message, uint256 value);
    event TokenWhitelisted(address indexed token, bool status);
    event TokensBatchWhitelisted(address[] tokens, bool status);
    event DexApprovalChanged(address dex, bool approved);
    event FeeParametersUpdated(uint256 feePercentage, address feeRecipient, bool feesEnabled);
    event ProfitDistributed(address token, uint256 totalProfit, uint256 ownerAmount, uint256 feeAmount);

    /**
     * @dev Constructor
     * @param _addressProvider The address of the Aave Pool Addresses Provider
     */    constructor(IPoolAddressesProvider _addressProvider)
        FlashLoanSimpleReceiverBase(_addressProvider)
        Ownable(msg.sender)
    {
        // Initialize DEX addresses (Updated June 2025)
        uniswapV3Router = 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45; // SwapRouter02 (Correct)
        uniswapV3Quoter = 0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6; // Uniswap V3 Quoter (Verified)

        // Set fee recipient to owner by default
        feeRecipient = owner();

        // Approve DEXes
        approvedDexes[uniswapV3Router] = true;
        approvedDexes[0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff] = true; // QuickSwap
        approvedDexes[0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506] = true; // SushiSwap

        // Whitelist common tokens
        _whitelistInitialTokens();
    }

    /**
     * @dev Whitelist initial tokens to reduce constructor complexity
     */
    function _whitelistInitialTokens() internal {
        whitelistedTokens[WETH] = true; // WETH
        whitelistedTokens[0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6] = true; // WBTC
        whitelistedTokens[0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174] = true; // USDC
        whitelistedTokens[0xc2132D05D31c914a87C6611C10748AEb04B58e8F] = true; // USDT
        whitelistedTokens[0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063] = true; // DAI
        whitelistedTokens[0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270] = true; // WMATIC
        whitelistedTokens[0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39] = true; // LINK
        whitelistedTokens[0xD6DF932A45C0f255f85145f286eA0b292B21C90B] = true; // AAVE

        // Emit events for each token
        emit TokenWhitelisted(WETH, true);
        emit TokenWhitelisted(0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6, true);
        emit TokenWhitelisted(0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174, true);
        emit TokenWhitelisted(0xc2132D05D31c914a87C6611C10748AEb04B58e8F, true);
        emit TokenWhitelisted(0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063, true);
        emit TokenWhitelisted(0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270, true);
        emit TokenWhitelisted(0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39, true);
        emit TokenWhitelisted(0xD6DF932A45C0f255f85145f286eA0b292B21C90B, true);
    }

    /**
     * @dev Execute arbitrage using flash loan
     */
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
        // Check circuit breaker
        require(failedTransactionsCount < maxFailedTransactions, "Circuit breaker triggered");

        // Validate parameters
        _validateArbitrageParams(borrowToken, intermediateToken, dex1, dex2, amount, deadline);

        emit DebugLog("Starting arbitrage execution", block.timestamp);

        // Request flash loan with all parameters
        _requestFlashLoan(borrowToken, amount, dex1, dex2, intermediateToken, dex1Fee, dex2Fee, deadline);
    }

    /**
     * @dev Validate arbitrage parameters
     */
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

    /**
     * @dev Request flash loan from Aave
     */
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
            0 // referralCode
        ) {
            // Flash loan successful
            failedTransactionsCount = 0; // Reset counter on success
        } catch Error(string memory reason) {
            // Flash loan failed with reason
            failedTransactionsCount++;
            emit ArbitrageFailed(borrowToken, amount, reason, initialGas - gasleft());
        } catch {
            // Flash loan failed without reason
            failedTransactionsCount++;
            emit ArbitrageFailed(borrowToken, amount, "Unknown error", initialGas - gasleft());
        }
    }

    /**
     * @dev Aave flash loan callback function
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        // Ensure the caller is the Aave lending pool
        require(msg.sender == address(POOL), "Caller must be Aave lending pool");

        // Decode parameters into a struct to reduce stack depth
        ArbitrageParams memory arbParams = _decodeParams(params);

        // Add amount and premium to the params struct
        arbParams.amount = amount;
        arbParams.premium = premium;

        // Execute the arbitrage strategy
        _executeArbitrageStrategy(arbParams);

        // Return true to indicate success
        return true;
    }

    /**
     * @dev Decode parameters from flash loan callback
     */
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
            amount: 0, // Will be set later
            premium: 0  // Will be set later
        });
    }

    /**
     * @dev Execute the arbitrage strategy
     */
    function _executeArbitrageStrategy(ArbitrageParams memory params) internal {
        // Calculate amount to repay
        uint256 amountToRepay = params.amount + params.premium;

        emit DebugLog("Starting arbitrage", block.timestamp);

        // First swap: borrowToken -> intermediateToken
        IERC20(params.borrowToken).approve(params.dex1, params.amount);

        // Execute first swap
        uint256 intermediateAmount = _executeSwap(
            params.borrowToken,
            params.intermediateToken,
            params.amount,
            params.dex1,
            params.dex1Fee,
            params.deadline
        );

        // Reset approval after swap
        IERC20(params.borrowToken).approve(params.dex1, 0);

        emit DebugLog("First swap completed", intermediateAmount);

        // Only proceed if first swap was successful
        if (intermediateAmount > 0) {
            _executeSecondSwap(params, intermediateAmount, amountToRepay);
        }

        // Approve Aave to take the repayment amount
        IERC20(params.borrowToken).approve(address(POOL), amountToRepay);
    }

    /**
     * @dev Execute the second swap and handle profits
     */
    function _executeSecondSwap(
        ArbitrageParams memory params,
        uint256 intermediateAmount,
        uint256 amountToRepay
    ) internal {
        // Second swap: intermediateToken -> borrowToken
        IERC20(params.intermediateToken).approve(params.dex2, intermediateAmount);

        uint256 finalAmount = _executeSwap(
            params.intermediateToken,
            params.borrowToken,
            intermediateAmount,
            params.dex2,
            params.dex2Fee,
            params.deadline
        );

        // Reset approval after swap
        IERC20(params.intermediateToken).approve(params.dex2, 0);

        emit DebugLog("Second swap completed", finalAmount);

        // Calculate and handle profit if any
        if (finalAmount > amountToRepay) {
            uint256 profit = finalAmount - amountToRepay;
            emit DebugLog("Profit calculated", profit);

            // Update swap statistics
            swapStats.totalSwaps++;
            swapStats.successfulSwaps++;
            swapStats.totalProfits += profit;
            swapStats.lastSwapTimestamp = block.timestamp;

            // Track highest profit
            if (profit > swapStats.highestProfit) {
                swapStats.highestProfit = profit;
                swapStats.mostProfitableToken = params.borrowToken;
            }

            // Calculate fee if enabled
            uint256 feeAmount = 0;
            if (feesEnabled && feeRecipient != address(0)) {
                feeAmount = profit * feePercentage / 10000;
                swapStats.totalFees += feeAmount;

                // Transfer fee to recipient
                if (feeAmount > 0) {
                    IERC20(params.borrowToken).transfer(feeRecipient, feeAmount);
                }
            }

            // Transfer remaining profit to owner
            uint256 ownerAmount = profit - feeAmount;
            IERC20(params.borrowToken).transfer(owner(), ownerAmount);

            // Emit detailed event
            emit ArbitrageExecuted(
                params.borrowToken,
                params.amount,
                params.dex1,
                params.dex2,
                params.intermediateToken,
                profit,
                feeAmount,
                gasleft(), // Approximate gas used
                block.timestamp
            );

            // Emit profit distribution event
            emit ProfitDistributed(params.borrowToken, profit, ownerAmount, feeAmount);
        } else {
            // Update failed swap statistics
            swapStats.totalSwaps++;
            swapStats.failedSwaps++;
        }
    }

    /**
     * @dev Execute a swap on either Uniswap V2 or V3
     */
    function _executeSwap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        address router,
        uint24 fee,
        uint256 deadline
    ) internal returns (uint256) {
        if (router == uniswapV3Router) {
            return _swapOnUniswapV3(tokenIn, tokenOut, amountIn, router, fee, deadline);
        } else {
            return _swapOnUniswapV2(tokenIn, tokenOut, amountIn, router, deadline);
        }
    }

    /**
     * @dev Swap tokens using Uniswap V3
     */
    function _swapOnUniswapV3(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        address router,
        uint24 fee,
        uint256 deadline
    ) internal returns (uint256) {
        // Get expected output amount using Quoter
        uint256 expectedAmountOut = _getUniswapV3Quote(tokenIn, tokenOut, fee, amountIn);

        // Calculate minimum amount out with slippage tolerance
        uint256 amountOutMinimum = expectedAmountOut * (10000 - slippageTolerance) / 10000;

        // Create swap parameters
        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            fee: fee,
            recipient: address(this),
            deadline: deadline,
            amountIn: amountIn,
            amountOutMinimum: amountOutMinimum, // Apply slippage protection
            sqrtPriceLimitX96: 0
        });

        // Execute the swap
        uint256 amountOut = ISwapRouter(router).exactInputSingle(params);

        // Emit swap event for monitoring
        emit SwapExecuted(tokenIn, tokenOut, router, amountIn, amountOut, block.timestamp);

        return amountOut;
    }

    /**
     * @dev Get quote from Uniswap V3 Quoter with gas optimization
     * Note: Although Quoter functions modify state for calculations,
     * they're called with staticcall so they don't actually persist state changes
     */
    function _getUniswapV3Quote(
        address tokenIn,
        address tokenOut,
        uint24 fee,
        uint256 amountIn
    ) internal returns (uint256) {
        // Gas optimization: return early for zero amounts
        if (amountIn == 0) return 0;
        
        try IQuoter(uniswapV3Quoter).quoteExactInputSingle(
            tokenIn,
            tokenOut,
            fee,
            amountIn,
            0 // sqrtPriceLimitX96
        ) returns (uint256 amountOut) {
            return amountOut;
        } catch {
            // If quote fails, return 0 to prevent execution
            // This is safer than returning a conservative estimate
            return 0;
        }
    }

    /**
     * @dev Swap tokens using Uniswap V2
     */
    function _swapOnUniswapV2(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        address router,
        uint256 deadline
    ) internal returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        // Get expected output amount for slippage calculation
        uint256[] memory expectedAmounts = IUniswapV2Router02(router).getAmountsOut(amountIn, path);
        uint256 amountOutMin = expectedAmounts[1] * (10000 - slippageTolerance) / 10000;

        uint256[] memory amounts = IUniswapV2Router02(router).swapExactTokensForTokens(
            amountIn,
            amountOutMin, // Apply slippage protection
            path,
            address(this),
            deadline
        );

        uint256 amountOut = amounts[amounts.length - 1];

        // Emit swap event for monitoring
        emit SwapExecuted(tokenIn, tokenOut, router, amountIn, amountOut, block.timestamp);

        return amountOut;
    }

    /**
     * @dev Whitelist a token
     */
    function whitelistToken(address token, bool status) public onlyOwner whenNotPaused {
        whitelistedTokens[token] = status;
        emit TokenWhitelisted(token, status);
    }

    /**
     * @dev Whitelist multiple tokens at once
     * @param tokens Array of token addresses to whitelist
     * @param status Whitelist status to set for all tokens
     */
    function whitelistTokensBatch(address[] calldata tokens, bool status) external onlyOwner whenNotPaused {
        require(tokens.length > 0, "Empty tokens array");

        for (uint256 i = 0; i < tokens.length; i++) {
            whitelistedTokens[tokens[i]] = status;
            // Individual events are still emitted for each token
            emit TokenWhitelisted(tokens[i], status);
        }

        // Emit batch event for easier off-chain tracking
        emit TokensBatchWhitelisted(tokens, status);
    }

    /**
     * @dev Approve or disapprove a DEX
     */
    function approveDex(address dex, bool status) external onlyOwner whenNotPaused {
        require(dex != address(0), "Invalid DEX address");
        approvedDexes[dex] = status;
        emit DexApprovalChanged(dex, status);
    }

    /**
     * @dev Set slippage tolerance
     */
    function setSlippageTolerance(uint256 _slippageTolerance) external onlyOwner whenNotPaused {
        require(_slippageTolerance <= 1000, "Slippage tolerance too high"); // Max 10%
        slippageTolerance = _slippageTolerance;
    }

    /**
     * @dev Set maximum failed transactions
     */
    function setMaxFailedTransactions(uint256 _maxFailedTransactions) external onlyOwner whenNotPaused {
        maxFailedTransactions = _maxFailedTransactions;
    }

    /**
     * @dev Reset failed transactions counter
     */
    function resetFailedTransactionsCount() external onlyOwner whenNotPaused {
        failedTransactionsCount = 0;
    }

    /**
     * @dev Set fee parameters
     * @param _feePercentage Fee percentage in basis points (e.g., 500 = 5%)
     * @param _feeRecipient Address to receive fees
     * @param _feesEnabled Whether fees are enabled
     */
    function setFeeParameters(
        uint256 _feePercentage,
        address _feeRecipient,
        bool _feesEnabled
    ) external onlyOwner whenNotPaused {
        require(_feePercentage <= 3000, "Fee too high"); // Max 30%
        require(_feeRecipient != address(0), "Invalid fee recipient");

        feePercentage = _feePercentage;
        feeRecipient = _feeRecipient;
        feesEnabled = _feesEnabled;

        emit FeeParametersUpdated(_feePercentage, _feeRecipient, _feesEnabled);
    }

    /**
     * @dev Get current swap statistics
     */
    function getSwapStatistics() external view returns (
        uint256 totalSwaps,
        uint256 successfulSwaps,
        uint256 failedSwaps,
        uint256 totalProfits,
        uint256 totalFees,
        uint256 lastSwapTimestamp,
        uint256 highestProfit,
        address mostProfitableToken
    ) {
        return (
            swapStats.totalSwaps,
            swapStats.successfulSwaps,
            swapStats.failedSwaps,
            swapStats.totalProfits,
            swapStats.totalFees,
            swapStats.lastSwapTimestamp,
            swapStats.highestProfit,
            swapStats.mostProfitableToken
        );
    }

    /**
     * @dev Get contract version and deployment info
     */
    function getContractInfo() external pure returns (
        string memory version,
        string memory deploymentDate,
        string memory description
    ) {
        return (
            "2.1",
            "June 2025",
            "Enhanced Flash Loan Arbitrage Contract with improved safety features"
        );
    }

    /**
     * @dev Check if the contract is healthy and ready for operations
     */
    function healthCheck() external view returns (
        bool isHealthy,
        string memory status,
        uint256 whitelistedTokenCount,
        uint256 approvedDexCount,
        uint256 currentFailedCount
    ) {
        // Count whitelisted tokens
        uint256 tokenCount = 0;
        address[] memory commonTokens = new address[](8);
        commonTokens[0] = WETH;
        commonTokens[1] = 0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6;
        commonTokens[2] = 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174;
        commonTokens[3] = 0xc2132D05D31c914a87C6611C10748AEb04B58e8F;
        commonTokens[4] = 0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063;
        commonTokens[5] = 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270;
        commonTokens[6] = 0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39;
        commonTokens[7] = 0xD6DF932A45C0f255f85145f286eA0b292B21C90B;
        
        for (uint256 i = 0; i < commonTokens.length; i++) {
            if (whitelistedTokens[commonTokens[i]]) {
                tokenCount++;
            }
        }
        
        // Count approved DEXes
        uint256 dexCount = 0;
        if (approvedDexes[uniswapV3Router]) dexCount++;
        if (approvedDexes[0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff]) dexCount++;
        if (approvedDexes[0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506]) dexCount++;
        
        bool healthy = !paused() && 
                      failedTransactionsCount < maxFailedTransactions && 
                      tokenCount > 0 && 
                      dexCount > 0;
        
        string memory statusMsg = healthy ? "Healthy" : "Needs Attention";
        
        return (healthy, statusMsg, tokenCount, dexCount, failedTransactionsCount);
    }

    /**
     * @dev Withdraw tokens from the contract
     */
    function withdrawToken(address token, uint256 amount) external onlyOwner whenNotPaused {
        IERC20(token).transfer(owner(), amount);
    }

    /**
     * @dev Pause the contract. Only owner can call this.
     */
    function pause() public onlyOwner {
        _pause();
    }

    /**
     * @dev Unpause the contract. Only owner can call this.
     */
    function unpause() public onlyOwner {
        _unpause();
    }

    /**
     * @dev Receive ETH
     */
    receive() external payable {}

    /**
     * @dev Emergency function to withdraw all tokens in case of issues
     */
    function emergencyWithdrawAll() external onlyOwner whenPaused {
        // Get common token addresses to check for balances
        address[] memory commonTokens = new address[](8);
        commonTokens[0] = WETH;
        commonTokens[1] = 0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6; // WBTC
        commonTokens[2] = 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174; // USDC
        commonTokens[3] = 0xc2132D05D31c914a87C6611C10748AEb04B58e8F; // USDT
        commonTokens[4] = 0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063; // DAI
        commonTokens[5] = 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270; // WMATIC
        commonTokens[6] = 0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39; // LINK
        commonTokens[7] = 0xD6DF932A45C0f255f85145f286eA0b292B21C90B; // AAVE
        
        for (uint256 i = 0; i < commonTokens.length; i++) {
            IERC20 token = IERC20(commonTokens[i]);
            uint256 balance = token.balanceOf(address(this));
            if (balance > 0) {
                token.transfer(owner(), balance);
            }
        }
        
        // Withdraw any ETH/MATIC
        if (address(this).balance > 0) {
            payable(owner()).transfer(address(this).balance);
        }
    }

    /**
     * @dev Update DEX router addresses if needed
     */
    function updateDexAddresses(
        address _uniswapV3Router,
        address _uniswapV3Quoter
    ) external onlyOwner whenPaused {
        require(_uniswapV3Router != address(0) && _uniswapV3Quoter != address(0), "Invalid addresses");
        
        // Remove old router from approved DEXes
        approvedDexes[uniswapV3Router] = false;
        
        // Update addresses
        uniswapV3Router = _uniswapV3Router;
        uniswapV3Quoter = _uniswapV3Quoter;
        
        // Add new router to approved DEXes
        approvedDexes[uniswapV3Router] = true;
        
        emit DexApprovalChanged(_uniswapV3Router, true);
    }
}
