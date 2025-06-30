const { ethers } = require("ethers");
const config = require("../config/amoy-config");
const RealTimePriceService = require("./real-time-price-service");

class ArbitrageBot {
  constructor(contractAddress, privateKey) {
    this.provider = new ethers.JsonRpcProvider(config.NETWORK.RPC_URL);
    this.wallet = new ethers.Wallet(privateKey, this.provider);
    this.contractAddress = contractAddress;
    
    // Initialize contract
    this.contract = new ethers.Contract(
      contractAddress,
      [
        "function executeArbitrage(address borrowToken, uint256 amount, address dex1, address dex2, address intermediateToken, uint24 dex1Fee, uint24 dex2Fee, uint256 deadline) external",
        "function getSwapStatistics() external view returns (uint256, uint256, uint256, uint256, uint256, uint256, uint256, address)",
        "function healthCheck() external view returns (bool, string, uint256, uint256, uint256)",
        "function owner() external view returns (address)",
        "function pause() external",
        "function unpause() external",
        "function withdrawToken(address token, uint256 amount) external",
        "event ArbitrageExecuted(address indexed token, uint256 amount, address dex1, address dex2, address intermediateToken, uint256 profit, uint256 fee, uint256 gasUsed, uint256 timestamp)",
        "event ArbitrageFailed(address indexed token, uint256 amount, string reason, uint256 gasUsed)"
      ],
      this.wallet
    );

    // Initialize price service
    this.priceService = new RealTimePriceService();
    
    // Bot configuration
    this.isRunning = false;
    this.executionInterval = 60000; // 1 minute
    this.minProfitThreshold = 0.02; // 2% minimum profit
    this.maxGasPrice = ethers.parseUnits("50", "gwei");
    this.maxSlippage = 500; // 5%
    
    // Statistics
    this.stats = {
      totalExecutions: 0,
      successfulTrades: 0,
      failedTrades: 0,
      totalProfits: 0,
      totalGasUsed: 0,
      startTime: Date.now()
    };

    // Setup event listeners
    this.setupEventListeners();
  }

  setupEventListeners() {
    this.contract.on("ArbitrageExecuted", (token, amount, dex1, dex2, intermediateToken, profit, fee, gasUsed, timestamp) => {
      this.stats.successfulTrades++;
      this.stats.totalProfits += Number(ethers.formatUnits(profit, 18));
      this.stats.totalGasUsed += Number(gasUsed);
      
      console.log("🎉 ARBITRAGE EXECUTED!");
      console.log(`💰 Token: ${token}`);
      console.log(`📊 Amount: ${ethers.formatUnits(amount, 18)}`);
      console.log(`🔄 DEX1: ${dex1}`);
      console.log(`🔄 DEX2: ${dex2}`);
      console.log(`💵 Profit: ${ethers.formatUnits(profit, 18)} tokens`);
      console.log(`💸 Fee: ${ethers.formatUnits(fee, 18)} tokens`);
      console.log(`⛽ Gas Used: ${gasUsed.toString()}`);
      console.log("========================================\n");
    });

    this.contract.on("ArbitrageFailed", (token, amount, reason, gasUsed) => {
      this.stats.failedTrades++;
      this.stats.totalGasUsed += Number(gasUsed);
      
      console.log("❌ ARBITRAGE FAILED!");
      console.log(`💰 Token: ${token}`);
      console.log(`📊 Amount: ${ethers.formatUnits(amount, 18)}`);
      console.log(`❌ Reason: ${reason}`);
      console.log(`⛽ Gas Used: ${gasUsed.toString()}`);
      console.log("========================================\n");
    });
  }

  async start() {
    console.log("🤖 Starting Arbitrage Bot...");
    console.log(`📍 Contract: ${this.contractAddress}`);
    console.log(`👤 Wallet: ${this.wallet.address}`);
    
    // Verify contract health
    const healthCheck = await this.contract.healthCheck();
    if (!healthCheck[0]) {
      throw new Error(`Contract is not healthy: ${healthCheck[1]}`);
    }
    
    console.log("✅ Contract health check passed");
    
    // Start price service
    await this.priceService.start();
    
    // Start bot
    this.isRunning = true;
    this.executionLoop();
    
    console.log("🚀 Arbitrage Bot is now running!");
  }

  async stop() {
    console.log("🛑 Stopping Arbitrage Bot...");
    this.isRunning = false;
    this.priceService.stop();
    
    if (this.executionTimer) {
      clearInterval(this.executionTimer);
    }
    
    this.printStats();
    console.log("✅ Arbitrage Bot stopped");
  }

  executionLoop() {
    this.executionTimer = setInterval(async () => {
      if (this.isRunning) {
        await this.scanAndExecute();
      }
    }, this.executionInterval);
  }

  async scanAndExecute() {
    try {
      console.log("🔍 Scanning for arbitrage opportunities...");
      
      // Get current gas price
      const gasPrice = await this.provider.getFeeData();
      if (gasPrice.gasPrice > this.maxGasPrice) {
        console.log("⛽ Gas price too high, skipping execution");
        return;
      }

      // Get arbitrage opportunities
      const opportunities = this.priceService.getArbitrageOpportunities(this.minProfitThreshold);
      
      if (opportunities.length === 0) {
        console.log("😴 No profitable opportunities found");
        this.priceService.printPriceSummary();
        return;
      }

      // Execute the most profitable opportunity
      const bestOpportunity = opportunities.reduce((best, current) => 
        current.profitPercentage > best.profitPercentage ? current : best
      );

      console.log(`🎯 Found opportunity: ${bestOpportunity.profitPercentage.toFixed(2)}% profit on ${bestOpportunity.token}`);
      
      await this.executeArbitrage(bestOpportunity);
      
    } catch (error) {
      console.error("❌ Error in execution loop:", error.message);
    }
  }

  async executeArbitrage(opportunity) {
    try {
      console.log("⚡ Executing arbitrage...");
      
      // Calculate flash loan amount (start with 1000 WMATIC)
      const borrowAmount = ethers.parseUnits("1000", 18);
      
      // Get token addresses
      const borrowToken = config.TOKENS.WMATIC.address;
      const intermediateToken = config.TOKENS.USDC.address;
      
      // Determine DEX addresses
      const dex1Address = opportunity.buyDex === 'uniswap' ? 
        config.DEXS.UNISWAP_V3.ROUTER : config.DEXS.QUICKSWAP.ROUTER;
      const dex2Address = opportunity.sellDex === 'uniswap' ? 
        config.DEXS.UNISWAP_V3.ROUTER : config.DEXS.QUICKSWAP.ROUTER;
      
      // Set fees
      const dex1Fee = opportunity.buyDex === 'uniswap' ? 3000 : 0;
      const dex2Fee = opportunity.sellDex === 'uniswap' ? 3000 : 0;
      
      // Set deadline (5 minutes from now)
      const deadline = Math.floor(Date.now() / 1000) + 300;
      
      console.log(`📊 Borrowing: ${ethers.formatUnits(borrowAmount, 18)} WMATIC`);
      console.log(`🔄 Buy DEX: ${opportunity.buyDex} (${dex1Address})`);
      console.log(`🔄 Sell DEX: ${opportunity.sellDex} (${dex2Address})`);
      console.log(`💱 Intermediate: USDC (${intermediateToken})`);
      
      // Execute the arbitrage
      const tx = await this.contract.executeArbitrage(
        borrowToken,
        borrowAmount,
        dex1Address,
        dex2Address,
        intermediateToken,
        dex1Fee,
        dex2Fee,
        deadline,
        {
          gasLimit: 3000000,
          gasPrice: gasPrice.gasPrice
        }
      );

      console.log(`📝 Transaction submitted: ${tx.hash}`);
      
      // Wait for confirmation
      const receipt = await tx.wait();
      console.log(`✅ Transaction confirmed in block: ${receipt.blockNumber}`);
      
      this.stats.totalExecutions++;
      
    } catch (error) {
      console.error("❌ Arbitrage execution failed:", error.message);
      this.stats.failedTrades++;
    }
  }

  async getContractStats() {
    try {
      const stats = await this.contract.getSwapStatistics();
      return {
        totalSwaps: Number(stats[0]),
        successfulSwaps: Number(stats[1]),
        failedSwaps: Number(stats[2]),
        totalProfits: ethers.formatUnits(stats[3], 18),
        totalFees: ethers.formatUnits(stats[4], 18),
        lastSwapTimestamp: Number(stats[5]),
        highestProfit: ethers.formatUnits(stats[6], 18),
        mostProfitableToken: stats[7]
      };
    } catch (error) {
      console.error("❌ Error getting contract stats:", error.message);
      return null;
    }
  }

  async withdrawProfits(tokenAddress, amount) {
    try {
      console.log(`💸 Withdrawing ${amount} tokens...`);
      
      const tx = await this.contract.withdrawToken(tokenAddress, ethers.parseUnits(amount, 18));
      await tx.wait();
      
      console.log("✅ Profits withdrawn successfully");
      
    } catch (error) {
      console.error("❌ Withdrawal failed:", error.message);
    }
  }

  printStats() {
    const runtime = (Date.now() - this.stats.startTime) / 1000 / 60; // minutes
    
    console.log("\n📊 Bot Performance Statistics:");
    console.log("========================================");
    console.log(`⏱️  Runtime: ${runtime.toFixed(2)} minutes`);
    console.log(`🚀 Total Executions: ${this.stats.totalExecutions}`);
    console.log(`✅ Successful Trades: ${this.stats.successfulTrades}`);
    console.log(`❌ Failed Trades: ${this.stats.failedTrades}`);
    console.log(`💰 Total Profits: ${this.stats.totalProfits.toFixed(6)} tokens`);
    console.log(`⛽ Total Gas Used: ${this.stats.totalGasUsed.toLocaleString()}`);
    
    if (this.stats.successfulTrades > 0) {
      console.log(`📈 Success Rate: ${((this.stats.successfulTrades / this.stats.totalExecutions) * 100).toFixed(2)}%`);
      console.log(`💵 Avg Profit/Trade: ${(this.stats.totalProfits / this.stats.successfulTrades).toFixed(6)} tokens`);
    }
    console.log("========================================\n");
  }

  async printCurrentStatus() {
    console.log("\n🤖 Arbitrage Bot Status:");
    console.log("========================================");
    console.log(`🟢 Status: ${this.isRunning ? 'Running' : 'Stopped'}`);
    console.log(`📍 Contract: ${this.contractAddress}`);
    console.log(`👤 Wallet: ${this.wallet.address}`);
    
    // Get wallet balance
    const balance = await this.provider.getBalance(this.wallet.address);
    console.log(`💰 Wallet Balance: ${ethers.formatUnits(balance, 18)} POL`);
    
    // Get contract stats
    const contractStats = await this.getContractStats();
    if (contractStats) {
      console.log(`📊 Contract Swaps: ${contractStats.totalSwaps}`);
      console.log(`✅ Successful: ${contractStats.successfulSwaps}`);
      console.log(`💰 Total Profits: ${contractStats.totalProfits} tokens`);
    }
    
    console.log("========================================\n");
  }
}

// Main execution
async function main() {
  require('dotenv').config();
  
  const contractAddress = process.env.CONTRACT_ADDRESS || process.argv[2];
  const privateKey = process.env.PRIVATE_KEY;
  
  if (!contractAddress) {
    console.error("❌ Please provide contract address via CONTRACT_ADDRESS env var or command line");
    process.exit(1);
  }
  
  if (!privateKey) {
    console.error("❌ Please provide PRIVATE_KEY in .env file");
    process.exit(1);
  }
  
  const bot = new ArbitrageBot(contractAddress, privateKey);
  
  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log("\n🛑 Received shutdown signal...");
    await bot.stop();
    process.exit(0);
  });
  
  // Start the bot
  try {
    await bot.start();
    
    // Print status every 5 minutes
    setInterval(async () => {
      await bot.printCurrentStatus();
    }, 300000);
    
  } catch (error) {
    console.error("❌ Bot startup failed:", error.message);
    process.exit(1);
  }
}

// Export for use as module
module.exports = ArbitrageBot;

// Run if called directly
if (require.main === module) {
  main();
} 