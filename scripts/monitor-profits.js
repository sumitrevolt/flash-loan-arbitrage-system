require('dotenv').config();
const { ethers } = require("ethers");

// Configuration
const AMOY_RPC = process.env.AMOY_RPC_URL;
const PROFIT_CONTRACT_ADDRESS = "0x20397497Cc0B67277d356939980721D0b3FD2c0F";

// Contract ABI
const PROFIT_CONTRACT_ABI = [
    "function getTotalProfit() external view returns (uint256)",
    "function getStats() external view returns (uint256, uint256, uint256)",
    "function getOwner() external view returns (address)"
];

async function monitorProfits() {
    console.log("📊 PROFIT MONITOR");
    console.log("=================");
    
    try {
        const provider = new ethers.providers.JsonRpcProvider(AMOY_RPC);
        const contract = new ethers.Contract(PROFIT_CONTRACT_ADDRESS, PROFIT_CONTRACT_ABI, provider);
        
        console.log("📍 Contract:", PROFIT_CONTRACT_ADDRESS);
        console.log("🌐 Network: Amoy Testnet");
        
        // Get current stats
        const stats = await contract.getStats();
        const totalProfit = stats[0];
        const successfulTrades = stats[1];
        const failedTrades = stats[2];
        const owner = await contract.getOwner();
        
        console.log("\n💰 CURRENT PROFITS:");
        console.log("   Total Profit:", ethers.utils.formatUnits(totalProfit, 6), "USDC");
        console.log("   Successful Trades:", successfulTrades.toString());
        console.log("   Failed Trades:", failedTrades.toString());
        
        const totalTrades = successfulTrades.toNumber() + failedTrades.toNumber();
        if (totalTrades > 0) {
            const successRate = (successfulTrades.toNumber() / totalTrades) * 100;
            console.log("   Success Rate:", successRate.toFixed(1) + "%");
            
            if (successfulTrades.toNumber() > 0) {
                const avgProfitPerTrade = parseFloat(ethers.utils.formatUnits(totalProfit, 6)) / successfulTrades.toNumber();
                console.log("   Avg Profit/Trade:", avgProfitPerTrade.toFixed(6), "USDC");
            }
        }
        
        console.log("\n📋 CONTRACT INFO:");
        console.log("   Owner:", owner);
        console.log("   Contract Balance:", totalProfit.gt(0) ? "Has profits to withdraw" : "No profits accumulated");
        console.log("   Timestamp:", new Date().toLocaleString());
        
        if (totalProfit.gt(0)) {
            console.log("\n💸 To withdraw profits, run:");
            console.log("   node scripts/withdraw-profits.js");
        }
        
    } catch (error) {
        console.error("❌ Error monitoring profits:", error.message);
    }
}

monitorProfits(); 