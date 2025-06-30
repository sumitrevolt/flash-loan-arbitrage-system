require('dotenv').config();
const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 Deploying Profit-Generating Arbitrage Contract...");
    
    // Get the deployer account
    const [deployer] = await ethers.getSigners();
    console.log("📍 Deploying with account:", deployer.address);
    
    // Check balance
    const balance = await deployer.getBalance();
    console.log("💰 Account balance:", ethers.utils.formatEther(balance), "POL");
    
    if (balance.lt(ethers.utils.parseEther("0.05"))) {
        console.log("❌ Insufficient balance for deployment. Need at least 0.05 POL");
        console.log("💡 Get POL from: https://faucet.polygon.technology/");
        return;
    }
    
    // Get the contract factory
    const RealArbitrageFlashLoan = await ethers.getContractFactory("RealArbitrageFlashLoan");
    
    console.log("⏳ Deploying profit-generating contract...");
    
    // Deploy the contract
    const arbitrageContract = await RealArbitrageFlashLoan.deploy();
    
    console.log("⏳ Waiting for deployment confirmation...");
    await arbitrageContract.deployed();
    
    console.log("✅ Profit Contract deployed successfully!");
    console.log("📍 Contract address:", arbitrageContract.address);
    console.log("📍 Transaction hash:", arbitrageContract.deployTransaction.hash);
    console.log("⛽ Gas used:", arbitrageContract.deployTransaction.gasLimit.toString());
    
    // Verify contract setup
    console.log("\n🔍 Verifying contract setup...");
    
    try {
        const owner = await arbitrageContract.getOwner();
        const totalProfit = await arbitrageContract.getTotalProfit();
        const stats = await arbitrageContract.getStats();
        
        console.log("✅ Contract verification:");
        console.log("   Owner:", owner);
        console.log("   Total Profit:", ethers.utils.formatUnits(totalProfit, 6), "USDC");
        console.log("   Successful Trades:", stats[1].toString());
        console.log("   Failed Trades:", stats[2].toString());
        console.log("   Owner match:", owner.toLowerCase() === deployer.address.toLowerCase());
        
    } catch (error) {
        console.log("⚠️  Contract verification failed:", error.message);
    }
    
    // Save deployment info
    const deploymentInfo = {
        network: "amoy",
        contractAddress: arbitrageContract.address,
        transactionHash: arbitrageContract.deployTransaction.hash,
        deployerAddress: deployer.address,
        contractType: "RealArbitrageFlashLoan",
        timestamp: new Date().toISOString(),
        blockNumber: arbitrageContract.deployTransaction.blockNumber
    };
    
    console.log("\n📋 Deployment Summary:");
    console.log(JSON.stringify(deploymentInfo, null, 2));
    
    console.log("\n🎯 Next steps:");
    console.log("1. Update your scripts to use the new profit contract:");
    console.log(`   CONTRACT_ADDRESS = "${arbitrageContract.address}"`);
    console.log("2. Run the profit-generating arbitrage bot:");
    console.log("   node scripts/profit-arbitrage-bot.js");
    console.log("3. Monitor profits:");
    console.log("   node scripts/monitor-profits.js");
    console.log("4. View on explorer:");
    console.log(`   https://www.oklink.com/amoy/address/${arbitrageContract.address}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    }); 