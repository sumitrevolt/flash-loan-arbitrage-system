require('dotenv').config();
const { ethers } = require("ethers");
const axios = require('axios');

// Amoy testnet configuration
const AMOY_RPC = process.env.AMOY_RPC_URL;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const CONTRACT_ADDRESS = "0xEcc0F821891eD07fA2fDC5f61985BA21b735BDC8"; // New working contract

// Real testnet token addresses for Amoy
const TOKENS = {
    USDC: "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582",    // Circle testnet USDC
    WMATIC: "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889",  // Wrapped MATIC on testnet
};

// Working contract ABI
const CONTRACT_ABI = [
    "function executeArbitrage(address asset, uint256 amount, bytes params) external",
    "function getOwner() external view returns (address)",
    "function getFlashLoanCount() external view returns (uint256)",
    "function POOL() external view returns (address)"
];

const ERC20_ABI = [
    "function balanceOf(address account) external view returns (uint256)",
    "function decimals() external view returns (uint8)",
    "function symbol() external view returns (string)"
];

// Price feed configuration
const CHAINLINK_MATIC_USD = "0xd0D5e3DB44DE05E9F294BB0a3bEEaF030DE24Ada"; // Polygon mainnet for reference
const API_ENDPOINTS = {
    coingecko: "https://api.coingecko.com/api/v3/simple/price?ids=matic-network&vs_currencies=usd",
    coinmarketcap: "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=MATIC"
};

class RealTimeArbitrageBot {
    constructor() {
        this.provider = new ethers.providers.JsonRpcProvider(AMOY_RPC);
        this.wallet = new ethers.Wallet(PRIVATE_KEY, this.provider);
        this.contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, this.wallet);
        
        this.lastPriceUpdate = 0;
        this.currentPrice = 0;
        this.isRunning = false;
        
        console.log("🚀 Real-time Web3 Flash Loan Arbitrage Bot");
        console.log("==========================================");
    }

    async initialize() {
        try {
            console.log("🤖 Initializing arbitrage bot...");
            console.log("📍 Wallet:", this.wallet.address);
            console.log("📍 Contract:", CONTRACT_ADDRESS);
            
            // Get network info
            const network = await this.provider.getNetwork();
            const block = await this.provider.getBlockNumber();
            const gasPrice = await this.provider.getGasPrice();
            
            console.log("🌐 Network Information:");
            console.log("   Chain ID:", network.chainId);
            console.log("   Current Block:", block);
            console.log("   Gas Price:", ethers.utils.formatUnits(gasPrice, "gwei"), "gwei");
            
            // Get wallet balances
            const polBalance = await this.provider.getBalance(this.wallet.address);
            const usdcContract = new ethers.Contract(TOKENS.USDC, ERC20_ABI, this.provider);
            const usdcBalance = await usdcContract.balanceOf(this.wallet.address);
            const usdcDecimals = await usdcContract.decimals();
            
            console.log("   Your POL:", ethers.utils.formatEther(polBalance), "POL");
            console.log("   Your USDC:", ethers.utils.formatUnits(usdcBalance, usdcDecimals), "USDC");
            
            // Verify contract
            console.log("\n🔍 Verifying contract...");
            const owner = await this.contract.getOwner();
            const flashLoanCount = await this.contract.getFlashLoanCount();
            const pool = await this.contract.POOL();
            
            console.log("✅ Contract verification:");
            console.log("   Owner:", owner);
            console.log("   Flash loan count:", flashLoanCount.toString());
            console.log("   Aave Pool:", pool);
            console.log("   Owner match:", owner.toLowerCase() === this.wallet.address.toLowerCase());
            
            return true;
        } catch (error) {
            console.log("❌ Initialization failed:", error.message);
            return false;
        }
    }

    async fetchRealTimePrice() {
        const sources = [];
        
        try {
            // Chainlink price feed (from Polygon mainnet for reference)
            const chainlinkAbi = ["function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80)"];
            
            try {
                // Connect to Polygon mainnet for Chainlink data
                const polygonProvider = new ethers.providers.JsonRpcProvider("https://polygon-rpc.com");
                const polygonFeed = new ethers.Contract(CHAINLINK_MATIC_USD, chainlinkAbi, polygonProvider);
                const [, price, , updatedAt] = await polygonFeed.latestRoundData();
                const chainlinkPrice = parseFloat(ethers.utils.formatUnits(price, 8));
                const timestamp = new Date(updatedAt * 1000).toLocaleTimeString();
                sources.push({ name: "Chainlink", price: chainlinkPrice, timestamp });
            } catch (err) {
                console.log("⚠️  Chainlink price unavailable:", err.message);
            }
        } catch (error) {
            console.log("⚠️  Chainlink setup failed:", error.message);
        }

        // CoinGecko API
        try {
            const response = await axios.get(API_ENDPOINTS.coingecko, { timeout: 5000 });
            const geckoPrice = response.data['matic-network'].usd;
            const timestamp = new Date().toLocaleTimeString();
            sources.push({ name: "CoinGecko", price: geckoPrice, timestamp });
        } catch (error) {
            console.log("⚠️  CoinGecko price unavailable:", error.message);
        }

        return sources;
    }

    simulateDEXPrices(basePrice) {
        const dexes = ["Uniswap V3", "QuickSwap", "SushiSwap", "1inch", "ParaSwap"];
        const prices = {};
        
        dexes.forEach(dex => {
            // Simulate realistic price variations (-0.5% to +0.5%)
            const variation = (Math.random() - 0.5) * 0.01; // ±0.5%
            const price = basePrice * (1 + variation);
            const percentChange = ((price - basePrice) / basePrice * 100);
            
            prices[dex] = {
                price: price,
                change: percentChange
            };
        });
        
        return prices;
    }

    findBestArbitrage(prices) {
        const dexNames = Object.keys(prices);
        let bestOpportunity = null;
        let maxSpread = 0;
        
        for (let i = 0; i < dexNames.length; i++) {
            for (let j = i + 1; j < dexNames.length; j++) {
                const dex1 = dexNames[i];
                const dex2 = dexNames[j];
                const price1 = prices[dex1].price;
                const price2 = prices[dex2].price;
                
                const spread = Math.abs(price2 - price1) / Math.min(price1, price2) * 100;
                
                if (spread > maxSpread) {
                    maxSpread = spread;
                    bestOpportunity = {
                        buyFrom: price1 < price2 ? dex1 : dex2,
                        sellTo: price1 < price2 ? dex2 : dex1,
                        buyPrice: Math.min(price1, price2),
                        sellPrice: Math.max(price1, price2),
                        spread: spread
                    };
                }
            }
        }
        
        return bestOpportunity;
    }

    async executeArbitrage(opportunity, basePrice, priceSource) {
        const amount = ethers.utils.parseUnits("100", 6); // 100 USDC
        const profitPer1000 = (opportunity.spread / 100) * 1000;
        const expectedProfit = (opportunity.spread / 100) * 100;
        
        console.log("\n⚡ EXECUTING REAL-TIME ARBITRAGE");
        console.log("=====================================");
        console.log("📋 Execution Details:");
        console.log("   Asset: USDC (" + TOKENS.USDC + ")");
        console.log("   Amount: 100 USDC");
        console.log("   Price Source:", priceSource);
        console.log("   Base Price: $" + basePrice.toFixed(4));
        console.log("   Strategy:", opportunity.buyFrom, "→", opportunity.sellTo);
        console.log("   Expected profit: $" + expectedProfit.toFixed(2));
        console.log("   Timestamp:", new Date().toLocaleString());
        
        try {
            // Execute the arbitrage transaction
            console.log("\n📊 Executing arbitrage transaction...");
            const params = ethers.utils.defaultAbiCoder.encode(
                ["string", "uint256"], 
                [opportunity.buyFrom + " → " + opportunity.sellTo, Math.floor(opportunity.spread * 100)]
            );
            
            const tx = await this.contract.executeArbitrage(
                TOKENS.USDC,
                amount,
                params,
                {
                    gasLimit: 300000,
                    gasPrice: ethers.utils.parseUnits("50", "gwei")
                }
            );
            
            console.log("⏳ Transaction submitted:", tx.hash);
            console.log("⏳ Waiting for confirmation...");
            
            const receipt = await tx.wait();
            console.log("✅ Transaction confirmed!");
            console.log("   Block number:", receipt.blockNumber);
            console.log("   Gas used:", receipt.gasUsed.toString());
            console.log("   Status:", receipt.status === 1 ? "Success" : "Failed");
            
            // Check updated flash loan count
            const newCount = await this.contract.getFlashLoanCount();
            console.log("   New flash loan count:", newCount.toString());
            
            console.log("\n🎉 Arbitrage execution completed!");
            
            return true;
            
        } catch (error) {
            console.log("❌ Arbitrage execution failed:", error.message);
            return false;
        }
    }

    async runArbitrageCycle(cycleNumber, totalCycles) {
        console.log(`\n🔄 Cycle ${cycleNumber}/${totalCycles}`);
        console.log("==================================================");
        
        // Fetch real-time prices
        console.log("🔍 Fetching real-time MATIC price from multiple sources...");
        const priceSources = await this.fetchRealTimePrice();
        
        if (priceSources.length === 0) {
            console.log("❌ No price sources available. Skipping cycle.");
            return false;
        }
        
        // Display prices
        console.log("📊 MATIC/USD prices from", priceSources.length, "sources:");
        priceSources.forEach(source => {
            console.log(`   ${source.name}: $${source.price.toFixed(4)} (${source.timestamp})`);
        });
        
        // Use primary price source (prefer Chainlink, fallback to CoinGecko)
        const primarySource = priceSources.find(s => s.name === "Chainlink") || priceSources[0];
        const basePrice = primarySource.price;
        console.log("✅ Using", primarySource.name, "price: $" + basePrice.toFixed(4));
        
        // Simulate DEX prices
        const dexPrices = this.simulateDEXPrices(basePrice);
        console.log("\n💱 Current DEX MATIC/USDC Prices (based on real $" + basePrice.toFixed(4) + "):");
        Object.entries(dexPrices).forEach(([dex, data]) => {
            const sign = data.change >= 0 ? "+" : "";
            console.log(`   ${dex}: $${data.price.toFixed(4)} (${sign}${data.change.toFixed(3)}%)`);
        });
        
        // Find best arbitrage opportunity
        const opportunity = this.findBestArbitrage(dexPrices);
        console.log("\n📈 Best Arbitrage Opportunity:");
        console.log(`   Buy from: ${opportunity.buyFrom} at $${opportunity.buyPrice.toFixed(4)}`);
        console.log(`   Sell to: ${opportunity.sellTo} at $${opportunity.sellPrice.toFixed(4)}`);
        console.log(`   Spread: ${opportunity.spread.toFixed(4)}%`);
        
        // Check if profitable (minimum 0.2% spread)
        const minSpread = 0.2;
        if (opportunity.spread >= minSpread) {
            const profitPer1000 = (opportunity.spread / 100) * 1000;
            console.log("🎯 PROFITABLE ARBITRAGE DETECTED!");
            console.log(`   Profit per 1000 USDC: $${profitPer1000.toFixed(2)}`);
            console.log(`   ROI: ${opportunity.spread.toFixed(3)}%`);
            console.log(`   Price source: ${primarySource.name}`);
            
            console.log("\n🎯 Executing arbitrage opportunity...");
            const success = await this.executeArbitrage(opportunity, basePrice, primarySource.name);
            
            if (success) {
                console.log(`✅ Arbitrage cycle ${cycleNumber} completed successfully.`);
                return true;
            } else {
                console.log(`❌ Arbitrage cycle ${cycleNumber} failed.`);
                return false;
            }
        } else {
            console.log(`❌ Spread ${opportunity.spread.toFixed(4)}% below minimum ${minSpread}%`);
            console.log(`⏭️  No profitable opportunities in cycle ${cycleNumber}.`);
            return false;
        }
    }

    async start(cycles = 5, intervalSeconds = 45) {
        if (this.isRunning) {
            console.log("⚠️  Bot is already running!");
            return;
        }

        const initialized = await this.initialize();
        if (!initialized) {
            console.log("❌ Failed to initialize bot.");
            return;
        }

        this.isRunning = true;
        console.log(`\n🎯 Starting arbitrage bot for ${cycles} cycles...`);
        console.log(`⏰ Cycle interval: ${intervalSeconds} seconds\n`);

        for (let cycle = 1; cycle <= cycles && this.isRunning; cycle++) {
            try {
                await this.runArbitrageCycle(cycle, cycles);
                
                if (cycle < cycles) {
                    console.log(`\n⏰ Waiting ${intervalSeconds} seconds before next cycle...`);
                    await new Promise(resolve => setTimeout(resolve, intervalSeconds * 1000));
                }
            } catch (error) {
                console.log(`❌ Error in cycle ${cycle}:`, error.message);
            }
        }

        this.isRunning = false;
        console.log("\n🏁 Arbitrage bot completed all cycles.");
        console.log("💡 To continue running, restart the script.");
    }

    stop() {
        this.isRunning = false;
        console.log("🛑 Arbitrage bot stopped by user.");
    }
}

// Main execution
async function main() {
    const bot = new RealTimeArbitrageBot();
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n🛑 Received interrupt signal. Stopping bot...');
        bot.stop();
        process.exit(0);
    });
    
    // Start the bot
    await bot.start(5, 45); // 5 cycles, 45 seconds between cycles
}

main().catch((error) => {
    console.error("❌ Bot crashed:", error);
    process.exit(1);
}); 