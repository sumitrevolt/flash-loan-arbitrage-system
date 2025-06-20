const { ethers } = require("hardhat");
require("dotenv").config();

async function main() {
    console.log("🩺 FLASH LOAN CONTRACT HEALTH CHECK");
    console.log("=" .repeat(50));
    
    const contractAddress = process.argv[2] || process.env.CONTRACT_ADDRESS;
    
    if (!contractAddress) {
        console.error("❌ Error: Contract address not provided!");
        console.log("Usage: npm run health-check <CONTRACT_ADDRESS>");
        console.log("Or set CONTRACT_ADDRESS in your .env file");
        process.exit(1);
    }
    
    console.log("📍 Contract Address:", contractAddress);
    
    try {
        // Get contract instance
        const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrageFixed");
        const contract = FlashLoanArbitrage.attach(contractAddress);
        
        // Basic connectivity check
        console.log("\n🔍 Checking contract connectivity...");
        const owner = await contract.owner();
        console.log("✅ Contract accessible");
        console.log("🔑 Owner:", owner);
        
        // Health check
        console.log("\n🩺 Performing health assessment...");
        const [isHealthy, status, tokenCount, dexCount, failedCount] = await contract.healthCheck();
        
        console.log("📊 Health Status:", status);
        console.log("🪙 Whitelisted Tokens:", tokenCount.toString());
        console.log("🔄 Approved DEXes:", dexCount.toString());
        console.log("❌ Failed Transactions:", failedCount.toString());
        
        if (isHealthy) {
            console.log("✅ Overall Status: HEALTHY");
        } else {
            console.log("⚠️  Overall Status: NEEDS ATTENTION");
        }
        
        // Get swap statistics
        console.log("\n📈 Performance Statistics:");
        const [
            totalSwaps,
            successfulSwaps,
            failedSwaps,
            totalProfits,
            totalFees,
            lastSwapTimestamp,
            highestProfit,
            mostProfitableToken
        ] = await contract.getSwapStatistics();
        
        console.log("🔄 Total Swaps:", totalSwaps.toString());
        console.log("✅ Successful:", successfulSwaps.toString());
        console.log("❌ Failed:", failedSwaps.toString());
        console.log("💰 Total Profits:", ethers.utils.formatEther(totalProfits), "tokens");
        console.log("💸 Total Fees:", ethers.utils.formatEther(totalFees), "tokens");
        
        if (lastSwapTimestamp.gt(0)) {
            const lastSwapDate = new Date(lastSwapTimestamp.toNumber() * 1000);
            console.log("⏰ Last Swap:", lastSwapDate.toISOString());
            console.log("🏆 Highest Profit:", ethers.utils.formatEther(highestProfit));
            console.log("🎯 Most Profitable Token:", mostProfitableToken);
        } else {
            console.log("⏰ No swaps executed yet");
        }
        
        // Configuration check
        console.log("\n⚙️  Configuration:");
        const slippageTolerance = await contract.slippageTolerance();
        const maxFailedTransactions = await contract.maxFailedTransactions();
        const feePercentage = await contract.feePercentage();
        const feesEnabled = await contract.feesEnabled();
        const paused = await contract.paused();
        
        console.log("📊 Slippage Tolerance:", (slippageTolerance.toNumber() / 100).toFixed(2) + "%");
        console.log("🔢 Max Failed Transactions:", maxFailedTransactions.toString());
        console.log("💰 Fee Percentage:", (feePercentage.toNumber() / 100).toFixed(2) + "%");
        console.log("💸 Fees Enabled:", feesEnabled ? "Yes" : "No");
        console.log("⏸️  Paused:", paused ? "Yes" : "No");
        
        // Recommendations
        console.log("\n💡 Recommendations:");
        
        if (!isHealthy) {
            if (tokenCount.lt(5)) {
                console.log("🪙 Consider whitelisting more tokens");
            }
            if (dexCount.lt(3)) {
                console.log("🔄 Consider approving more DEXes");
            }
            if (failedCount.gt(5)) {
                console.log("🔄 Consider resetting failed transaction counter");
            }
        }
        
        if (paused) {
            console.log("⚠️  Contract is paused - unpause to enable operations");
        }
        
        if (totalSwaps.eq(0)) {
            console.log("🚀 Ready for first arbitrage execution");
        }
        
        console.log("\n✅ Health check completed successfully!");
        
    } catch (error) {
        console.error("\n❌ Health check failed!");
        console.error("Error:", error.message);
        
        if (error.message.includes("call revert exception")) {
            console.log("💡 The contract might not be deployed at this address");
        } else if (error.message.includes("network")) {
            console.log("💡 Check your network connection and RPC URL");
        }
        
        process.exit(1);
    }
}

main()
    .then(() => {
        console.log("\n🎉 Health check completed!");
        process.exit(0);
    })
    .catch((error) => {
        console.error("💥 Health check failed:", error);
        process.exit(1);
    });
