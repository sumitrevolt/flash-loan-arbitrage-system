require('dotenv').config();
const { ethers } = require('hardhat');

// Contract ABI for the deployed contract
const AAVE_FLASH_LOAN_ABI = [
    "function executeFlashLoanArbitrage(address asset, uint256 amount, bytes calldata params) external",
    "function getOwner() external view returns (address)",
    "function getFlashLoanCount() external view returns (uint256)",
    "function getTotalProfit() external view returns (uint256)",
    "function getStats() external view returns (uint256, uint256, uint256)",
    "function USDC() external view returns (address)",
    "function WMATIC() external view returns (address)",
    "event FlashLoanExecuted(address asset, uint256 amount, uint256 premium)",
    "event ArbitrageCompleted(address asset, uint256 amount, uint256 profit)",
    "event ArbitrageFailed(address asset, uint256 amount, string reason)"
];

// Configuration
const CONFIG = {
    // Update this with your deployed contract address
    CONTRACT_ADDRESS: "0x20397497Cc0B67277d356939980721D0b3FD2c0F", // Replace with your Aave contract
    
    // Amoy testnet token addresses
    USDC: "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582",
    WMATIC: "0x9c3c9283d3e44854697cd22D3faA240cfB0e7582",
    
    // Flash loan amounts (in wei)
    FLASH_LOAN_AMOUNTS: {
        USDC: ethers.utils.parseUnits("1000", 6), // 1000 USDC
        WMATIC: ethers.utils.parseEther("1000")   // 1000 WMATIC
    },
    
    // Arbitrage strategies
    STRATEGIES: [
        "DEX_ARBITRAGE",
        "LIQUIDATION_ARBITRAGE", 
        "YIELD_ARBITRAGE",
        "DEFAULT"
    ],
    
    // Minimum profit threshold (basis points)
    MIN_PROFIT_BPS: 30, // 0.30%
    
    // Bot settings
    LOOP_INTERVAL: 90 * 1000, // 90 seconds
    MAX_RETRIES: 3
};

class AaveFlashLoanBot {
    constructor() {
        this.provider = null;
        this.signer = null;
        this.contract = null;
        this.isRunning = false;
        this.stats = {
            totalFlashLoans: 0,
            successfulArbitrages: 0,
            failedArbitrages: 0,
            totalProfit: 0
        };
    }

    async initialize() {
        console.log("🚀 Initializing Aave Flash Loan Bot...\n");
        
        // Setup provider and signer
        this.provider = new ethers.providers.JsonRpcProvider(process.env.AMOY_RPC_URL);
        this.signer = new ethers.Wallet(process.env.PRIVATE_KEY, this.provider);
        
        console.log("📍 Bot wallet address:", this.signer.address);
        
        // Check balance
        const balance = await this.signer.getBalance();
        console.log("💰 POL balance:", ethers.utils.formatEther(balance));
        
        if (balance.lt(ethers.utils.parseEther("1"))) {
            console.log("⚠️  Warning: Low POL balance. Get more from faucet!");
        }
        
        // Connect to contract
        this.contract = new ethers.Contract(CONFIG.CONTRACT_ADDRESS, AAVE_FLASH_LOAN_ABI, this.signer);
        
        // Verify contract connection
        try {
            const owner = await this.contract.getOwner();
            console.log("👤 Contract owner:", owner);
            
            if (owner.toLowerCase() !== this.signer.address.toLowerCase()) {
                throw new Error("You are not the owner of this contract!");
            }
            
            const flashLoanCount = await this.contract.getFlashLoanCount();
            console.log("📊 Current flash loan count:", flashLoanCount.toString());
            
        } catch (error) {
            console.error("❌ Contract connection failed:", error.message);
            process.exit(1);
        }
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log("✅ Bot initialized successfully!\n");
    }

    setupEventListeners() {
        // Listen for flash loan events
        this.contract.on("FlashLoanExecuted", (asset, amount, premium, event) => {
            console.log("⚡ Flash Loan Executed:");
            console.log(`  Asset: ${asset}`);
            console.log(`  Amount: ${ethers.utils.formatUnits(amount, 6)} tokens`);
            console.log(`  Premium: ${ethers.utils.formatUnits(premium, 6)} tokens`);
            console.log(`  Tx: ${event.transactionHash}`);
        });

        this.contract.on("ArbitrageCompleted", (asset, amount, profit, event) => {
            console.log("🎉 Arbitrage Successful:");
            console.log(`  Asset: ${asset}`);
            console.log(`  Profit: ${ethers.utils.formatUnits(profit, 6)} tokens`);
            console.log(`  Tx: ${event.transactionHash}`);
            this.stats.successfulArbitrages++;
            this.stats.totalProfit += parseFloat(ethers.utils.formatUnits(profit, 6));
        });

        this.contract.on("ArbitrageFailed", (asset, amount, reason, event) => {
            console.log("❌ Arbitrage Failed:");
            console.log(`  Asset: ${asset}`);
            console.log(`  Reason: ${reason}`);
            console.log(`  Tx: ${event.transactionHash}`);
            this.stats.failedArbitrages++;
        });
    }

    async executeFlashLoan(asset, amount, strategy) {
        try {
            console.log(`\n🔄 Executing Flash Loan Arbitrage...`);
            console.log(`📊 Strategy: ${strategy}`);
            console.log(`💰 Asset: ${asset}`);
            console.log(`📈 Amount: ${ethers.utils.formatUnits(amount, 6)} tokens`);
            
            // Encode parameters for the flash loan
            const params = ethers.utils.defaultAbiCoder.encode(
                ["string", "uint256"],
                [strategy, CONFIG.MIN_PROFIT_BPS]
            );
            
            // Execute flash loan
            const tx = await this.contract.executeFlashLoanArbitrage(
                asset,
                amount,
                params,
                {
                    gasLimit: 500000, // Adjust gas limit as needed
                    gasPrice: ethers.utils.parseUnits("2", "gwei")
                }
            );
            
            console.log("📤 Transaction sent:", tx.hash);
            console.log("⏳ Waiting for confirmation...");
            
            const receipt = await tx.wait();
            
            if (receipt.status === 1) {
                console.log("✅ Flash loan executed successfully!");
                this.stats.totalFlashLoans++;
                return true;
            } else {
                console.log("❌ Transaction failed");
                return false;
            }
            
        } catch (error) {
            console.error("❌ Flash loan execution failed:", error.message);
            
            // Parse error for more details
            if (error.message.includes("insufficient funds")) {
                console.log("💸 Insufficient funds for gas fees");
            } else if (error.message.includes("execution reverted")) {
                console.log("🔄 Contract execution reverted - strategy not profitable");
            }
            
            return false;
        }
    }

    async getCurrentMarketConditions() {
        console.log("\n📈 Analyzing market conditions...");
        
        // Simulate market analysis (in real implementation, query DEX prices)
        const volatilityFactor = Math.random() * 100 + 50; // 50-150%
        const marketSentiment = Math.random() > 0.5 ? "bullish" : "bearish";
        
        console.log(`📊 Market volatility: ${volatilityFactor.toFixed(2)}%`);
        console.log(`🎯 Market sentiment: ${marketSentiment}`);
        
        // Determine best strategy based on conditions
        let recommendedStrategy;
        if (volatilityFactor > 120) {
            recommendedStrategy = "DEX_ARBITRAGE";
        } else if (volatilityFactor > 90) {
            recommendedStrategy = "LIQUIDATION_ARBITRAGE";
        } else if (volatilityFactor > 70) {
            recommendedStrategy = "YIELD_ARBITRAGE";
        } else {
            recommendedStrategy = "DEFAULT";
        }
        
        console.log(`🎯 Recommended strategy: ${recommendedStrategy}`);
        
        return {
            volatility: volatilityFactor,
            sentiment: marketSentiment,
            strategy: recommendedStrategy,
            profitability: volatilityFactor > 80 // Only execute if volatility > 80%
        };
    }

    async runArbitrageLoop() {
        console.log("🔄 Starting Aave Flash Loan Arbitrage Loop...\n");
        this.isRunning = true;
        
        while (this.isRunning) {
            try {
                console.log(`\n⏰ ${new Date().toLocaleTimeString()} - Checking arbitrage opportunities...`);
                
                // Analyze market conditions
                const market = await this.getCurrentMarketConditions();
                
                if (market.profitability) {
                    console.log("🎯 Profitable opportunity detected!");
                    
                    // Alternate between USDC and WMATIC flash loans
                    const useUSDC = Math.random() > 0.5;
                    const asset = useUSDC ? CONFIG.USDC : CONFIG.WMATIC;
                    const amount = useUSDC ? CONFIG.FLASH_LOAN_AMOUNTS.USDC : CONFIG.FLASH_LOAN_AMOUNTS.WMATIC;
                    
                    // Execute flash loan
                    await this.executeFlashLoan(asset, amount, market.strategy);
                    
                } else {
                    console.log("📊 No profitable opportunities at this time");
                }
                
                // Display current stats
                await this.displayStats();
                
                // Wait for next iteration
                console.log(`\n⏱️  Waiting ${CONFIG.LOOP_INTERVAL / 1000} seconds for next check...`);
                await this.sleep(CONFIG.LOOP_INTERVAL);
                
            } catch (error) {
                console.error("❌ Loop error:", error.message);
                console.log("🔄 Continuing in 30 seconds...");
                await this.sleep(30000);
            }
        }
    }

    async displayStats() {
        try {
            // Get on-chain stats
            const [totalProfit, successful, totalFlashLoans] = await this.contract.getStats();
            
            console.log("\n📊 === BOT STATISTICS ===");
            console.log(`🔥 Total Flash Loans: ${totalFlashLoans.toString()}`);
            console.log(`✅ Successful Arbitrages: ${successful.toString()}`);
            console.log(`❌ Failed Arbitrages: ${this.stats.failedArbitrages}`);
            console.log(`💰 Total Profit Generated: ${ethers.utils.formatUnits(totalProfit, 6)} tokens`);
            
            if (totalFlashLoans.gt(0)) {
                const successRate = (successful.toNumber() / totalFlashLoans.toNumber()) * 100;
                console.log(`📈 Success Rate: ${successRate.toFixed(1)}%`);
            }
            
        } catch (error) {
            console.error("Error fetching stats:", error.message);
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    stop() {
        console.log("\n🛑 Stopping Aave Flash Loan Bot...");
        this.isRunning = false;
    }
}

// Main execution
async function main() {
    const bot = new AaveFlashLoanBot();
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n⚠️  Received SIGINT, shutting down gracefully...');
        bot.stop();
        process.exit(0);
    });
    
    try {
        await bot.initialize();
        await bot.runArbitrageLoop();
    } catch (error) {
        console.error("❌ Bot crashed:", error);
        process.exit(1);
    }
}

// Run the bot
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { AaveFlashLoanBot, CONFIG }; 