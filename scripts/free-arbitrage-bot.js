const { ethers } = require("ethers");
const FreePriceServices = require("./free-price-services");
const config = require("../config/amoy-config");

class FreeArbitrageBot {
  constructor() {
    this.provider = new ethers.JsonRpcProvider(config.NETWORK.RPC_URL);
    this.wallet = new ethers.Wallet(process.env.PRIVATE_KEY, this.provider);
    this.priceService = new FreePriceServices();
    
    this.contract = null;
    this.isRunning = false;
    this.stats = {
      totalTrades: 0,
      successfulTrades: 0,
      failedTrades: 0,
      totalProfit: 0,
      startTime: Date.now()
    };
    
    this.minProfitThreshold = 0.02; // 2% minimum profit
    this.maxGasPrice = ethers.parseUnits("50", "gwei");
    this.flashLoanAmount = ethers.parseUnits("1000", 18); // 1000 WMATIC
  }

  async init() {
    console.log("🤖 Initializing Free Arbitrage Bot...");
    
    try {
      // Load contract ABI and connect
      const contractABI = [
        "function executeArbitrage(address token, uint256 amount, bytes calldata params) external",
        "function getFlashLoanFee(uint256 amount) external view returns (uint256)",
        "function owner() external view returns (address)",
        "function paused() external view returns (bool)",
        "event ArbitrageExecuted(address indexed token, uint256 amount, uint256 profit)",
        "event ArbitrageFailed(address indexed token, uint256 amount, string reason)"
      ];
      
      const contractAddress = process.env.FLASH_LOAN_CONTRACT;
      if (!contractAddress) {
        throw new Error("FLASH_LOAN_CONTRACT address not found in environment");
      }
      
      this.contract = new ethers.Contract(contractAddress, contractABI, this.wallet);
      
      // Check if contract is accessible
      const owner = await this.contract.owner();
      const isPaused = await this.contract.paused();
      
      console.log(`✅ Contract loaded: ${contractAddress}`);
      console.log(`   Owner: ${owner}`);
      console.log(`   Paused: ${isPaused}`);
      console.log(`   Bot wallet: ${this.wallet.address}`);
      
      // Initialize price service
      await this.priceService.start();
      console.log("✅ Free price service started");
      
      // Set up event listeners
      this.setupEventListeners();
      
    } catch (error) {
      console.error("❌ Initialization failed:", error.message);
      throw error;
    }
  }

  setupEventListeners() {
    // Listen for arbitrage events
    this.contract.on("ArbitrageExecuted", (token, amount, profit, event) => {
      this.stats.successfulTrades++;
      this.stats.totalProfit += Number(ethers.formatEther(profit));
      
      console.log("🎉 Arbitrage Executed Successfully!");
      console.log(`   Token: ${token}`);
      console.log(`   Amount: ${ethers.formatEther(amount)} tokens`);
      console.log(`   Profit: ${ethers.formatEther(profit)} ETH`);
      console.log(`   TX: ${event.transactionHash}`);
    });

    this.contract.on("ArbitrageFailed", (token, amount, reason, event) => {
      this.stats.failedTrades++;
      
      console.log("❌ Arbitrage Failed");
      console.log(`   Token: ${token}`);
      console.log(`   Amount: ${ethers.formatEther(amount)} tokens`);
      console.log(`   Reason: ${reason}`);
      console.log(`   TX: ${event.transactionHash}`);
    });

    // Graceful shutdown
    process.on('SIGINT', () => {
      console.log('\n🛑 Received SIGINT, shutting down gracefully...');
      this.stop();
      process.exit(0);
    });
  }

  async start() {
    console.log("🚀 Starting Free Arbitrage Bot...");
    this.isRunning = true;
    this.stats.startTime = Date.now();

    // Main arbitrage loop
    this.arbitrageLoop();
    
    // Status reporting
    this.statusReporting();
  }

  async stop() {
    console.log("🛑 Stopping Free Arbitrage Bot...");
    this.isRunning = false;
    this.priceService.stop();
    
    // Print final stats
    this.printStats();
  }

  async arbitrageLoop() {
    if (!this.isRunning) return;

    try {
      console.log("🔍 Scanning for arbitrage opportunities...");
      
      // Get current gas price
      const gasPrice = await this.provider.getFeeData();
      if (gasPrice.gasPrice > this.maxGasPrice) {
        console.log(`⛽ Gas price too high: ${ethers.formatUnits(gasPrice.gasPrice, "gwei")} gwei (max: 50)`);
        setTimeout(() => this.arbitrageLoop(), 60000); // Wait 1 minute
        return;
      }

      // Get arbitrage opportunities from free price service
      const opportunities = this.priceService.getArbitrageOpportunities(this.minProfitThreshold);
      
      if (opportunities.length > 0) {
        console.log(`🎯 Found ${opportunities.length} arbitrage opportunities!`);
        
        for (const opportunity of opportunities) {
          if (!this.isRunning) break;
          
          await this.executeArbitrage(opportunity);
          
          // Small delay between executions
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      } else {
        console.log("😴 No profitable arbitrage opportunities found");
      }

    } catch (error) {
      console.error("❌ Error in arbitrage loop:", error.message);
    }

    // Schedule next iteration (1 minute intervals)
    setTimeout(() => this.arbitrageLoop(), 60000);
  }

  async executeArbitrage(opportunity) {
    try {
      console.log(`\n⚡ Executing arbitrage for ${opportunity.token}`);
      console.log(`   Buy: ${opportunity.buySource} at $${opportunity.buyPrice.toFixed(6)}`);
      console.log(`   Sell: ${opportunity.sellSource} at $${opportunity.sellPrice.toFixed(6)}`);
      console.log(`   Expected profit: ${opportunity.profitPercentage.toFixed(2)}%`);

      // Prepare arbitrage parameters
      const tokenAddress = config.TOKENS[opportunity.token]?.address;
      if (!tokenAddress) {
        console.log(`❌ Token address not found for ${opportunity.token}`);
        return;
      }

      // Calculate flash loan fee
      const fee = await this.contract.getFlashLoanFee(this.flashLoanAmount);
      console.log(`   Flash loan fee: ${ethers.formatEther(fee)} WMATIC`);

      // Encode arbitrage parameters
      const params = ethers.AbiCoder.defaultAbiCoder().encode(
        ["address", "address", "uint256", "uint256", "bytes"],
        [
          config.DEXS.UNISWAP_V3.ROUTER, // Buy DEX
          config.DEXS.QUICKSWAP.ROUTER,  // Sell DEX
          Math.floor(opportunity.buyPrice * 1000000), // Buy price (scaled)
          Math.floor(opportunity.sellPrice * 1000000), // Sell price (scaled)
          "0x" // Additional data
        ]
      );

      // Check balance before execution
      const balance = await this.provider.getBalance(this.wallet.address);
      console.log(`   Wallet balance: ${ethers.formatEther(balance)} MATIC`);

      if (balance < ethers.parseEther("1")) {
        console.log("❌ Insufficient balance for gas fees");
        return;
      }

      // Execute arbitrage
      this.stats.totalTrades++;
      
      const tx = await this.contract.executeArbitrage(
        tokenAddress,
        this.flashLoanAmount,
        params,
        {
          gasLimit: 500000,
          gasPrice: await this.provider.getFeeData().then(data => data.gasPrice)
        }
      );

      console.log(`🔄 Transaction submitted: ${tx.hash}`);
      console.log(`   Waiting for confirmation...`);

      const receipt = await tx.wait();
      console.log(`✅ Transaction confirmed in block ${receipt.blockNumber}`);
      console.log(`   Gas used: ${receipt.gasUsed.toString()}`);

    } catch (error) {
      this.stats.failedTrades++;
      console.error(`❌ Arbitrage execution failed: ${error.message}`);
      
      if (error.code === 'INSUFFICIENT_FUNDS') {
        console.log("💸 Insufficient funds for transaction");
      } else if (error.code === 'UNPREDICTABLE_GAS_LIMIT') {
        console.log("⛽ Gas estimation failed - trade may not be profitable");
      }
    }
  }

  statusReporting() {
    if (!this.isRunning) return;

    console.log("\n📊 === FREE ARBITRAGE BOT STATUS ===");
    
    const uptime = Date.now() - this.stats.startTime;
    const hours = Math.floor(uptime / (1000 * 60 * 60));
    const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
    
    console.log(`⏱️  Uptime: ${hours}h ${minutes}m`);
    console.log(`📈 Total trades: ${this.stats.totalTrades}`);
    console.log(`✅ Successful: ${this.stats.successfulTrades}`);
    console.log(`❌ Failed: ${this.stats.failedTrades}`);
    console.log(`💰 Total profit: ${this.stats.totalProfit.toFixed(4)} ETH`);
    
    if (this.stats.totalTrades > 0) {
      const successRate = (this.stats.successfulTrades / this.stats.totalTrades * 100).toFixed(1);
      console.log(`📊 Success rate: ${successRate}%`);
    }

    // Show current prices from free sources
    this.priceService.printPriceSummary();

    console.log("================================\n");

    // Schedule next status report (5 minutes)
    setTimeout(() => this.statusReporting(), 5 * 60 * 1000);
  }

  printStats() {
    console.log("\n📋 FINAL STATISTICS");
    console.log("==================");
    console.log(`Total runtime: ${Math.floor((Date.now() - this.stats.startTime) / 60000)} minutes`);
    console.log(`Total trades executed: ${this.stats.totalTrades}`);
    console.log(`Successful trades: ${this.stats.successfulTrades}`);
    console.log(`Failed trades: ${this.stats.failedTrades}`);
    console.log(`Total profit earned: ${this.stats.totalProfit.toFixed(6)} ETH`);
    
    if (this.stats.totalTrades > 0) {
      console.log(`Average profit per trade: ${(this.stats.totalProfit / this.stats.successfulTrades || 0).toFixed(6)} ETH`);
      console.log(`Success rate: ${(this.stats.successfulTrades / this.stats.totalTrades * 100).toFixed(2)}%`);
    }
    console.log("==================\n");
  }

  // Get current token price from free services
  getCurrentPrice(token) {
    return this.priceService.getBestPrice(token);
  }

  // Get all available prices
  getAllPrices() {
    return this.priceService.getAllPrices();
  }
}

// CLI interface
async function main() {
  console.log("🤖 FREE ARBITRAGE BOT");
  console.log("=====================");
  console.log("Using completely free price APIs:");
  console.log("• DexScreener (unlimited)");
  console.log("• CoinCap (unlimited)");
  console.log("• CryptoCompare (100k/month)");
  console.log("• On-chain DEX quotes");
  console.log("• Exchange APIs (Binance, KuCoin)");
  console.log("=====================\n");

  // Check environment variables
  if (!process.env.PRIVATE_KEY) {
    console.error("❌ PRIVATE_KEY environment variable not set");
    process.exit(1);
  }

  if (!process.env.FLASH_LOAN_CONTRACT) {
    console.error("❌ FLASH_LOAN_CONTRACT environment variable not set");
    console.log("💡 Deploy the contract first using: npm run deploy");
    process.exit(1);
  }

  const bot = new FreeArbitrageBot();
  
  try {
    await bot.init();
    await bot.start();
  } catch (error) {
    console.error("❌ Bot failed to start:", error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = FreeArbitrageBot; 