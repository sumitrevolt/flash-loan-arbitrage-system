require('dotenv').config();
const { ethers } = require("ethers");

// Amoy testnet configuration
const AMOY_RPC = process.env.AMOY_RPC_URL;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const CONTRACT_ADDRESS = "0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5";

// Testnet token addresses for Amoy
const TOKENS = {
    MATIC: "0x0000000000000000000000000000000000001010", // Native POL wrapper
    USDC: "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582",    // Circle testnet USDC
    WETH: "0x360ad4f9a9A8EFe9A8DCB5f461c4Cc1047E1Dcf9",    // Testnet WETH
};

// Simplified mock price oracle for testnet
const MOCK_PRICES = {
    'MATIC/USDC': { price: 0.85, lastUpdate: Date.now() },
    'WETH/USDC': { price: 2800.0, lastUpdate: Date.now() },
    'WETH/MATIC': { price: 3294.12, lastUpdate: Date.now() }
};

// Simple contract ABI for basic interactions
const CONTRACT_ABI = [
    "function executeArbitrage(address asset, uint256 amount, bytes params) external",
    "function getOwner() external view returns (address)",
    "function getFlashLoanCount() external view returns (uint256)",
    "function POOL() external view returns (address)"
];

// ERC20 ABI for balance checking
const ERC20_ABI = [
    "function balanceOf(address owner) external view returns (uint256)",
    "function decimals() external view returns (uint8)",
    "function symbol() external view returns (string)"
];

class TestnetArbitrageBot {
    constructor() {
        this.provider = new ethers.providers.JsonRpcProvider(AMOY_RPC);
        this.wallet = new ethers.Wallet(PRIVATE_KEY, this.provider);
        this.contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, this.wallet);
        
        console.log(`🤖 Testnet Arbitrage Bot initialized`);
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
            const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, this.provider);
            const balance = await tokenContract.balanceOf(this.wallet.address);
            const decimals = await tokenContract.decimals();
            return ethers.utils.formatUnits(balance, decimals);
        } catch (error) {
            console.log(`ℹ️  Could not fetch ${tokenSymbol} balance: ${error.message}`);
            return '0.0';
        }
    }

    // Mock price feeds with random variations to simulate market conditions
    getMockPrice(pair) {
        const basePrices = MOCK_PRICES[pair];
        if (!basePrices) return null;

        // Add small random variations (±2%) to simulate market movement
        const variation = (Math.random() - 0.5) * 0.04; // ±2%
        const currentPrice = basePrices.price * (1 + variation);
        
        return {
            price: currentPrice,
            lastUpdate: Date.now()
        };
    }

    async checkArbitrageOpportunity() {
        console.log("\n🔍 Checking arbitrage opportunities...");

        try {
            // Get mock prices from different "sources" (simulating different DEXs)
            const uniswapPrice = this.getMockPrice('WETH/USDC');
            const sushiswapPrice = this.getMockPrice('WETH/USDC');
            
            if (!uniswapPrice || !sushiswapPrice) {
                console.log("❌ Could not fetch prices");
                return null;
            }

            // Add slight difference between "exchanges" to simulate spread
            sushiswapPrice.price *= (1 + (Math.random() - 0.5) * 0.006); // ±0.3% difference

            console.log(`📊 Mock Uniswap WETH/USDC: $${uniswapPrice.price.toFixed(2)}`);
            console.log(`📊 Mock Sushiswap WETH/USDC: $${sushiswapPrice.price.toFixed(2)}`);

            const priceDiff = Math.abs(uniswapPrice.price - sushiswapPrice.price);
            const spreadPercentage = (priceDiff / Math.min(uniswapPrice.price, sushiswapPrice.price)) * 100;

            console.log(`📈 Price spread: ${spreadPercentage.toFixed(4)}%`);

            const MIN_SPREAD = 0.25; // 0.25% minimum spread for testnet demo
            
            if (spreadPercentage >= MIN_SPREAD) {
                const buyFrom = uniswapPrice.price < sushiswapPrice.price ? 'Uniswap' : 'Sushiswap';
                const sellTo = uniswapPrice.price < sushiswapPrice.price ? 'Sushiswap' : 'Uniswap';
                const profitPer1000 = (spreadPercentage / 100) * 1000;

                console.log(`🎯 ARBITRAGE OPPORTUNITY DETECTED!`);
                console.log(`   Buy from: ${buyFrom} ($${Math.min(uniswapPrice.price, sushiswapPrice.price).toFixed(2)})`);
                console.log(`   Sell to: ${sellTo} ($${Math.max(uniswapPrice.price, sushiswapPrice.price).toFixed(2)})`);
                console.log(`   Profit per 1000 USDC: $${profitPer1000.toFixed(2)}`);

                return {
                    spread: spreadPercentage,
                    buyPrice: Math.min(uniswapPrice.price, sushiswapPrice.price),
                    sellPrice: Math.max(uniswapPrice.price, sushiswapPrice.price),
                    buyFrom,
                    sellTo,
                    profitPer1000
                };
            } else {
                console.log(`❌ Spread ${spreadPercentage.toFixed(4)}% below minimum ${MIN_SPREAD}%`);
                return null;
            }

        } catch (error) {
            console.error("❌ Error checking arbitrage:", error.message);
            return null;
        }
    }

    async simulateArbitrage(opportunity) {
        const flashLoanAmount = "1000"; // 1000 USDC for demo
        
        console.log(`\n⚡ SIMULATING Flash Loan Arbitrage:`);
        console.log(`   Flash loan amount: ${flashLoanAmount} USDC`);
        console.log(`   Expected profit: $${opportunity.profitPer1000.toFixed(2)}`);
        console.log(`   Buy from: ${opportunity.buyFrom} at $${opportunity.buyPrice.toFixed(2)}`);
        console.log(`   Sell to: ${opportunity.sellTo} at $${opportunity.sellPrice.toFixed(2)}`);

        try {
            // Check contract owner and flash loan count for monitoring
            const owner = await this.contract.getOwner();
            const flashLoanCount = await this.contract.getFlashLoanCount();
            
            console.log(`\n📊 Contract Status:`);
            console.log(`   Owner: ${owner}`);
            console.log(`   Flash loans executed: ${flashLoanCount.toString()}`);
            console.log(`   Your wallet: ${this.wallet.address}`);
            console.log(`   Owner match: ${owner.toLowerCase() === this.wallet.address.toLowerCase()}`);

            // For testnet demo, we'll just simulate the execution
            console.log(`\n🔄 SIMULATION: Executing arbitrage...`);
            
            // Simulate the arbitrage execution steps
            await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate processing time
            
            console.log(`✅ SIMULATION COMPLETE: Arbitrage would be profitable!`);
            console.log(`💰 Estimated profit: $${opportunity.profitPer1000.toFixed(2)} on 1000 USDC`);
            console.log(`📈 ROI: ${((opportunity.profitPer1000 / 1000) * 100).toFixed(3)}%`);

            return true;

        } catch (error) {
            console.error("❌ Simulation error:", error.message);
            return false;
        }
    }

    async displayPortfolio() {
        console.log(`\n💼 Portfolio Status:`);
        
        const polBalance = await this.getWalletBalance();
        const usdcBalance = await this.getTokenBalance(TOKENS.USDC, 'USDC');
        const wethBalance = await this.getTokenBalance(TOKENS.WETH, 'WETH');

        console.log(`   POL: ${parseFloat(polBalance).toFixed(4)} POL`);
        console.log(`   USDC: ${parseFloat(usdcBalance).toFixed(2)} USDC`);
        console.log(`   WETH: ${parseFloat(wethBalance).toFixed(6)} WETH`);
    }

    async run() {
        console.log(`\n🚀 Starting Testnet Arbitrage Bot...`);
        
        await this.displayPortfolio();

        while (true) {
            try {
                const opportunity = await this.checkArbitrageOpportunity();
                
                if (opportunity) {
                    await this.simulateArbitrage(opportunity);
                    console.log(`\n⏰ Waiting 30 seconds before next check...`);
                    await new Promise(resolve => setTimeout(resolve, 30000));
                } else {
                    console.log(`⏰ No opportunities found. Checking again in 10 seconds...`);
                    await new Promise(resolve => setTimeout(resolve, 10000));
                }

            } catch (error) {
                console.error("❌ Bot error:", error.message);
                console.log("⏰ Retrying in 15 seconds...");
                await new Promise(resolve => setTimeout(resolve, 15000));
            }
        }
    }
}

// Run the bot
async function main() {
    const bot = new TestnetArbitrageBot();
    await bot.run();
}

main().catch(console.error); 