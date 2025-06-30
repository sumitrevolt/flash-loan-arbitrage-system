require('dotenv').config();
const { ethers } = require("ethers");

// Amoy testnet configuration
const AMOY_RPC = process.env.AMOY_RPC_URL;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const CONTRACT_ADDRESS = "0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5";

// Testnet token addresses for Amoy
const TOKENS = {
    USDC: "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582",    // Circle testnet USDC
    WETH: "0x360ad4f9a9A8EFe9A8DCB5f461c4Cc1047E1Dcf9",    // Testnet WETH (if available)
    WMATIC: "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889",  // Wrapped MATIC on testnet
};

// Aave Pool on Amoy
const AAVE_POOL = "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A";

const CONTRACT_ABI = [
    "function executeArbitrage(address asset, uint256 amount, bytes params) external",
    "function getOwner() external view returns (address)",
    "function getFlashLoanCount() external view returns (uint256)",
    "function POOL() external view returns (address)"
];

const ERC20_ABI = [
    "function balanceOf(address owner) external view returns (uint256)",
    "function decimals() external view returns (uint8)",
    "function symbol() external view returns (string)",
    "function approve(address spender, uint256 amount) external returns (bool)",
    "function transfer(address to, uint256 amount) external returns (bool)",
    "function allowance(address owner, address spender) external view returns (uint256)"
];

// Simple DEX router interface for testnet
const DEX_ROUTER_ABI = [
    "function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts)",
    "function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)"
];

class TestnetRealArbitrageBot {
    constructor() {
        this.provider = new ethers.providers.JsonRpcProvider(AMOY_RPC);
        this.wallet = new ethers.Wallet(PRIVATE_KEY, this.provider);
        this.contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, this.wallet);
        
        console.log(`🤖 Real Testnet Arbitrage Bot initialized`);
        console.log(`📍 Wallet: ${this.wallet.address}`);
        console.log(`📍 Contract: ${CONTRACT_ADDRESS}`);
        console.log(`🌐 Network: Amoy Testnet (Chain ID: 80002)`);
    }

    async getWalletBalance() {
        try {
            const balance = await this.provider.getBalance(this.wallet.address);
            return ethers.utils.formatEther(balance);
        } catch (error) {
            console.error('Error getting wallet balance:', error.message);
            return '0.0';
        }
    }

    async getTokenBalance(tokenAddress, tokenSymbol) {
        try {
            if (!ethers.utils.isAddress(tokenAddress)) {
                console.log(`❌ Invalid token address for ${tokenSymbol}`);
                return '0.0';
            }

            const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, this.provider);
            const balance = await tokenContract.balanceOf(this.wallet.address);
            const decimals = await tokenContract.decimals();
            return ethers.utils.formatUnits(balance, decimals);
        } catch (error) {
            console.log(`ℹ️  Could not fetch ${tokenSymbol} balance: ${error.message}`);
            return '0.0';
        }
    }

    async checkContractStatus() {
        try {
            console.log(`\n📊 Flash Loan Contract Status:`);
            
            const owner = await this.contract.getOwner();
            const flashLoanCount = await this.contract.getFlashLoanCount();
            const aavePool = await this.contract.POOL();
            
            console.log(`   Owner: ${owner}`);
            console.log(`   Flash loans executed: ${flashLoanCount.toString()}`);
            console.log(`   Aave Pool: ${aavePool}`);
            console.log(`   Your wallet: ${this.wallet.address}`);
            console.log(`   You are owner: ${owner.toLowerCase() === this.wallet.address.toLowerCase()}`);

            return {
                owner,
                flashLoanCount: flashLoanCount.toString(),
                aavePool,
                isOwner: owner.toLowerCase() === this.wallet.address.toLowerCase()
            };

        } catch (error) {
            console.error("❌ Error checking contract status:", error.message);
            return null;
        }
    }

    async executeTestFlashLoan() {
        console.log(`\n⚡ Executing Test Flash Loan...`);
        
        try {
            const flashLoanAmount = ethers.utils.parseUnits("100", 6); // 100 USDC
            const params = "0x"; // Empty params for simple test

            console.log(`📋 Flash loan details:`);
            console.log(`   Asset: USDC (${TOKENS.USDC})`);
            console.log(`   Amount: 100 USDC`);
            console.log(`   Params: ${params}`);

            // Estimate gas first
            const gasEstimate = await this.contract.estimateGas.executeArbitrage(
                TOKENS.USDC,
                flashLoanAmount,
                params
            );

            console.log(`⛽ Estimated gas: ${gasEstimate.toString()}`);

            // Execute the flash loan
            const tx = await this.contract.executeArbitrage(
                TOKENS.USDC,
                flashLoanAmount,
                params,
                {
                    gasLimit: gasEstimate.mul(120).div(100), // Add 20% buffer
                }
            );

            console.log(`📤 Transaction sent: ${tx.hash}`);
            console.log(`⏳ Waiting for confirmation...`);

            const receipt = await tx.wait();
            
            console.log(`✅ Flash loan executed successfully!`);
            console.log(`   Block: ${receipt.blockNumber}`);
            console.log(`   Gas used: ${receipt.gasUsed.toString()}`);
            console.log(`   Transaction hash: ${receipt.transactionHash}`);

            return receipt;

        } catch (error) {
            console.error("❌ Flash loan execution failed:", error.message);
            
            if (error.message.includes("insufficient funds")) {
                console.log("💡 Tip: Make sure you have enough POL for gas fees");
                const balance = await this.getWalletBalance();
                console.log(`   Current POL balance: ${balance} POL`);
            }
            
            return null;
        }
    }

    async demonstrateArbitrage() {
        console.log(`\n🎯 DEMONSTRATING FLASH LOAN ARBITRAGE`);
        console.log(`=====================================`);

        // Check portfolio before
        console.log(`\n💼 Portfolio BEFORE:`);
        const polBefore = await this.getWalletBalance();
        const usdcBefore = await this.getTokenBalance(TOKENS.USDC, 'USDC');
        
        console.log(`   POL: ${parseFloat(polBefore).toFixed(4)} POL`);
        console.log(`   USDC: ${parseFloat(usdcBefore).toFixed(2)} USDC`);

        // Check contract status
        const contractStatus = await this.checkContractStatus();
        if (!contractStatus) {
            console.log("❌ Cannot proceed - contract status check failed");
            return;
        }

        if (!contractStatus.isOwner) {
            console.log("⚠️  Warning: You are not the contract owner");
            console.log("   Flash loans may still work if the contract allows it");
        }

        // Execute test flash loan
        const result = await this.executeTestFlashLoan();

        if (result) {
            console.log(`\n✅ ARBITRAGE DEMONSTRATION COMPLETE!`);
            
            // Check portfolio after
            console.log(`\n💼 Portfolio AFTER:`);
            const polAfter = await this.getWalletBalance();
            const usdcAfter = await this.getTokenBalance(TOKENS.USDC, 'USDC');
            
            console.log(`   POL: ${parseFloat(polAfter).toFixed(4)} POL`);
            console.log(`   USDC: ${parseFloat(usdcAfter).toFixed(2)} USDC`);

            const polDiff = parseFloat(polAfter) - parseFloat(polBefore);
            const usdcDiff = parseFloat(usdcAfter) - parseFloat(usdcBefore);

            console.log(`\n📊 Changes:`);
            console.log(`   POL: ${polDiff > 0 ? '+' : ''}${polDiff.toFixed(4)} POL (gas fees)`);
            console.log(`   USDC: ${usdcDiff > 0 ? '+' : ''}${usdcDiff.toFixed(2)} USDC`);

            // Update flash loan count
            const newCount = await this.contract.getFlashLoanCount();
            console.log(`\n🔢 Flash loans executed: ${contractStatus.flashLoanCount} → ${newCount.toString()}`);

        } else {
            console.log(`\n❌ ARBITRAGE DEMONSTRATION FAILED`);
            console.log(`   This could be due to:`);
            console.log(`   - Insufficient gas fees (need POL)`);
            console.log(`   - Contract not properly deployed`);
            console.log(`   - Network connectivity issues`);
            console.log(`   - Aave flash loan requirements not met`);
        }
    }

    async getTestnetTokens() {
        console.log(`\n🚰 TESTNET TOKENS GUIDE`);
        console.log(`=====================`);
        console.log(`\nTo get testnet tokens for arbitrage testing:`);
        console.log(`\n1. POL (for gas fees):`);
        console.log(`   🔗 https://faucet.polygon.technology/`);
        console.log(`   🔗 https://chainstack.com/amoy-faucet/`);
        console.log(`\n2. USDC (for arbitrage):`);
        console.log(`   🔗 https://faucet.circle.com/`);
        console.log(`\n3. Your wallet address: ${this.wallet.address}`);
        console.log(`\nOnce you have tokens, run this script again!`);
    }

    async checkPrerequisites() {
        const polBalance = parseFloat(await this.getWalletBalance());
        const usdcBalance = parseFloat(await this.getTokenBalance(TOKENS.USDC, 'USDC'));

        console.log(`\n🔍 Prerequisites Check:`);
        console.log(`   POL balance: ${polBalance.toFixed(4)} POL ${polBalance > 0.1 ? '✅' : '❌'}`);
        console.log(`   USDC balance: ${usdcBalance.toFixed(2)} USDC ${usdcBalance >= 0 ? '✅' : '❌'}`);

        const hasMinimumPol = polBalance > 0.1;
        
        if (!hasMinimumPol) {
            console.log(`\n❌ Insufficient POL for gas fees (need > 0.1 POL)`);
            await this.getTestnetTokens();
            return false;
        }

        console.log(`\n✅ Prerequisites met! Ready for arbitrage testing.`);
        return true;
    }
}

// Main execution
async function main() {
    const bot = new TestnetRealArbitrageBot();
    
    console.log(`🚀 Testnet Flash Loan Arbitrage Demo`);
    console.log(`==================================`);

    // Check if we have the prerequisites
    const ready = await bot.checkPrerequisites();
    
    if (ready) {
        await bot.demonstrateArbitrage();
    }

    console.log(`\n🎯 Demo completed. Press Ctrl+C to exit.`);
}

main().catch(console.error); 