require('dotenv').config();
const { ethers } = require("ethers");

// Configuration
const AMOY_RPC = process.env.AMOY_RPC_URL;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const PROFIT_CONTRACT_ADDRESS = "0x20397497Cc0B67277d356939980721D0b3FD2c0F";
const USDC_ADDRESS = "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582";

// Contract ABI
const PROFIT_CONTRACT_ABI = [
    "function getTotalProfit() external view returns (uint256)",
    "function getStats() external view returns (uint256, uint256, uint256)",
    "function withdrawProfit(address token) external",
    "function getOwner() external view returns (address)"
];

const ERC20_ABI = [
    "function balanceOf(address account) external view returns (uint256)",
    "function symbol() external view returns (string)"
];

async function withdrawProfits() {
    console.log("💸 PROFIT WITHDRAWAL");
    console.log("====================");
    
    try {
        const provider = new ethers.providers.JsonRpcProvider(AMOY_RPC);
        const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
        const contract = new ethers.Contract(PROFIT_CONTRACT_ADDRESS, PROFIT_CONTRACT_ABI, wallet);
        const usdcContract = new ethers.Contract(USDC_ADDRESS, ERC20_ABI, provider);
        
        console.log("📍 Contract:", PROFIT_CONTRACT_ADDRESS);
        console.log("📍 Wallet:", wallet.address);
        
        // Check current profits
        const stats = await contract.getStats();
        const totalProfit = stats[0];
        const successfulTrades = stats[1];
        
        console.log("\n💰 PROFIT STATUS:");
        console.log("   Total Profit:", ethers.utils.formatUnits(totalProfit, 6), "USDC");
        console.log("   Successful Trades:", successfulTrades.toString());
        
        if (totalProfit.eq(0)) {
            console.log("ℹ️  No profits to withdraw yet.");
            return;
        }
        
        // Check wallet balance before withdrawal
        const balanceBefore = await usdcContract.balanceOf(wallet.address);
        console.log("   Wallet USDC Before:", ethers.utils.formatUnits(balanceBefore, 6), "USDC");
        
        console.log("\n🔄 Initiating withdrawal...");
        
        // Execute withdrawal
        const tx = await contract.withdrawProfit(USDC_ADDRESS, {
            gasLimit: 200000,
            gasPrice: ethers.utils.parseUnits("50", "gwei")
        });
        
        console.log("⏳ Transaction submitted:", tx.hash);
        console.log("⏳ Waiting for confirmation...");
        
        const receipt = await tx.wait();
        console.log("✅ Withdrawal confirmed!");
        console.log("   Block number:", receipt.blockNumber);
        console.log("   Gas used:", receipt.gasUsed.toString());
        console.log("   Gas cost:", ethers.utils.formatEther(receipt.gasUsed.mul(receipt.effectiveGasPrice)), "POL");
        
        // Check wallet balance after withdrawal
        const balanceAfter = await usdcContract.balanceOf(wallet.address);
        const withdrawnAmount = balanceAfter.sub(balanceBefore);
        
        console.log("\n🎉 WITHDRAWAL SUCCESSFUL!");
        console.log("   Amount Withdrawn:", ethers.utils.formatUnits(withdrawnAmount, 6), "USDC");
        console.log("   New Wallet Balance:", ethers.utils.formatUnits(balanceAfter, 6), "USDC");
        
        // Check updated contract stats
        const newStats = await contract.getStats();
        const newTotalProfit = newStats[0];
        
        console.log("\n📊 UPDATED CONTRACT STATUS:");
        console.log("   Remaining Profit:", ethers.utils.formatUnits(newTotalProfit, 6), "USDC");
        console.log("   Total Trades:", newStats[1].toString());
        
        console.log("\n💰 SUMMARY:");
        console.log("   Your profits have been successfully withdrawn!");
        console.log("   You can continue running the bot to generate more profits.");
        console.log("   Next steps:");
        console.log("   - Run: node scripts/profit-arbitrage-bot.js (to generate more profits)");
        console.log("   - Run: node scripts/monitor-profits.js (to check status)");
        
    } catch (error) {
        console.error("❌ Withdrawal failed:", error.message);
        
        if (error.message.includes("Only owner")) {
            console.log("💡 Make sure you're using the correct wallet that deployed the contract.");
        } else if (error.message.includes("No profit")) {
            console.log("💡 No profits available to withdraw yet. Run the bot to generate profits first.");
        }
    }
}

withdrawProfits(); 