require('dotenv').config();
const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 Deploying Working Flash Loan Arbitrage Contract...");
    
    // Amoy testnet Aave V3 Pool Address Provider
    const AAVE_POOL_ADDRESS_PROVIDER = "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A";
    
    // Get the deployer account
    const [deployer] = await ethers.getSigners();
    console.log("📍 Deploying with account:", deployer.address);
    
    // Check balance
    const balance = await deployer.getBalance();
    console.log("💰 Account balance:", ethers.utils.formatEther(balance), "POL");
    
    if (balance.lt(ethers.utils.parseEther("0.1"))) {
        console.log("❌ Insufficient balance for deployment. Need at least 0.1 POL");
        console.log("💡 Get POL from: https://faucet.polygon.technology/");
        return;
    }
    
    // Get the contract factory
    const WorkingFlashLoanArbitrage = await ethers.getContractFactory("WorkingFlashLoanArbitrage");
    
    console.log("⏳ Deploying contract...");
    
    // Deploy the contract
    const flashLoanContract = await WorkingFlashLoanArbitrage.deploy(
        AAVE_POOL_ADDRESS_PROVIDER
    );
    
    console.log("⏳ Waiting for deployment confirmation...");
    await flashLoanContract.deployed();
    
    console.log("✅ Contract deployed successfully!");
    console.log("📍 Contract address:", flashLoanContract.address);
    console.log("📍 Transaction hash:", flashLoanContract.deployTransaction.hash);
    console.log("⛽ Gas used:", flashLoanContract.deployTransaction.gasLimit.toString());
    
    // Verify contract setup
    console.log("\n🔍 Verifying contract setup...");
    
    try {
        const owner = await flashLoanContract.getOwner();
        const flashLoanCount = await flashLoanContract.getFlashLoanCount();
        const pool = await flashLoanContract.POOL();
        
        console.log("✅ Contract verification:");
        console.log("   Owner:", owner);
        console.log("   Flash loan count:", flashLoanCount.toString());
        console.log("   Aave Pool:", pool);
        console.log("   Owner match:", owner.toLowerCase() === deployer.address.toLowerCase());
        
    } catch (error) {
        console.log("⚠️  Contract verification failed:", error.message);
    }
    
    // Save deployment info
    const deploymentInfo = {
        network: "amoy",
        contractAddress: flashLoanContract.address,
        transactionHash: flashLoanContract.deployTransaction.hash,
        deployerAddress: deployer.address,
        aavePoolProvider: AAVE_POOL_ADDRESS_PROVIDER,
        timestamp: new Date().toISOString(),
        blockNumber: flashLoanContract.deployTransaction.blockNumber
    };
    
    console.log("\n📋 Deployment Summary:");
    console.log(JSON.stringify(deploymentInfo, null, 2));
    
    console.log("\n🎯 Next steps:");
    console.log("1. Update your scripts to use the new contract address:");
    console.log(`   CONTRACT_ADDRESS = "${flashLoanContract.address}"`);
    console.log("2. Run the fixed arbitrage script:");
    console.log("   node scripts/fixed-realtime-arbitrage.js");
    console.log("3. View on explorer:");
    console.log(`   https://www.oklink.com/amoy/address/${flashLoanContract.address}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    }); 