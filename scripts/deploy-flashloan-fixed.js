require('dotenv').config();
const { ethers } = require('hardhat');

async function main() {
    console.log("🚀 Deploying FlashLoanArbitrageFixed Contract...\n");
    
    // Get the deployer account
    const [deployer] = await ethers.getSigners();
    console.log("📍 Deploying contracts with account:", deployer.address);
    
    // Get account balance
    const balance = await deployer.getBalance();
    console.log("💰 Account balance:", ethers.utils.formatEther(balance), "POL\n");
    
    // Aave V3 Pool Address Provider on Amoy testnet
    const AAVE_POOL_ADDRESSES_PROVIDER = "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A";
    
    console.log("🏦 Using Aave Pool Addresses Provider:", AAVE_POOL_ADDRESSES_PROVIDER);
    
    // Deploy the contract
    console.log("⚙️  Compiling and deploying FlashLoanArbitrageFixed...");
    const FlashLoanArbitrageFixed = await ethers.getContractFactory("contracts/FlashLoanArbitrageFixed.sol:FlashLoanArbitrageFixed");
    
    const contract = await FlashLoanArbitrageFixed.deploy(AAVE_POOL_ADDRESSES_PROVIDER, {
        gasLimit: 3000000, // Set a higher gas limit for complex contract
        gasPrice: ethers.utils.parseUnits("30", "gwei") // Increased gas price for Amoy
    });
    
    await contract.deployed();
    
    console.log("✅ FlashLoanArbitrageFixed deployed to:", contract.address);
    console.log("📄 Transaction hash:", contract.deployTransaction.hash);
    console.log("⛽ Gas used:", contract.deployTransaction.gasLimit.toString());
    
    // Wait for a few block confirmations
    console.log("\n⏳ Waiting for block confirmations...");
    await contract.deployTransaction.wait(3);
    
    // Get contract info
    console.log("🔍 Verifying contract deployment...");
    const owner = await contract.owner();
    const uniswapV3Router = await contract.uniswapV3Router();
    const uniswapV3Quoter = await contract.uniswapV3Quoter();
    const slippageTolerance = await contract.slippageTolerance();
    
    console.log("\n📊 Contract Information:");
    console.log("- Owner:", owner);
    console.log("- Uniswap V3 Router:", uniswapV3Router);
    console.log("- Uniswap V3 Quoter:", uniswapV3Quoter);
    console.log("- Slippage Tolerance:", slippageTolerance.toString(), "basis points");
    
    // Get contract version and health status
    try {
        const [version, deploymentDate, description] = await contract.getContractInfo();
        console.log("\n📝 Contract Details:");
        console.log("- Version:", version);
        console.log("- Deployment Date:", deploymentDate);
        console.log("- Description:", description);
        
        const [isHealthy, status, tokenCount, dexCount, failedCount] = await contract.healthCheck();
        console.log("\n🏥 Health Check:");
        console.log("- Is Healthy:", isHealthy);
        console.log("- Status:", status);
        console.log("- Whitelisted Tokens:", tokenCount.toString());
        console.log("- Approved DEXes:", dexCount.toString());
        console.log("- Failed Transactions:", failedCount.toString());
        
    } catch (error) {
        console.log("ℹ️  Could not fetch detailed contract info:", error.message);
    }
    
    console.log("\n🎯 Contract Features:");
    console.log("- ✅ Real Aave V3 Flash Loans");
    console.log("- ✅ Uniswap V2/V3 Integration");
    console.log("- ✅ Multi-DEX Arbitrage");
    console.log("- ✅ Circuit Breaker Protection");
    console.log("- ✅ Slippage Protection");
    console.log("- ✅ Fee Management System");
    console.log("- ✅ Comprehensive Event Logging");
    console.log("- ✅ Emergency Functions");
    
    console.log("\n🚀 Next Steps:");
    console.log("1. Run: node scripts/flashloan-arbitrage-bot.js");
    console.log("2. Execute real arbitrage opportunities");
    console.log("3. Monitor profits and statistics");
    
    // Save deployment info
    const deploymentInfo = {
        network: "amoy",
        contractName: "FlashLoanArbitrageFixed",
        contractAddress: contract.address,
        transactionHash: contract.deployTransaction.hash,
        deployer: deployer.address,
        timestamp: new Date().toISOString(),
        aavePoolAddressProvider: AAVE_POOL_ADDRESSES_PROVIDER,
        gasUsed: contract.deployTransaction.gasLimit.toString(),
        owner: owner,
        uniswapV3Router: uniswapV3Router,
        uniswapV3Quoter: uniswapV3Quoter
    };
    
    console.log("\n💾 Deployment Summary:");
    console.log(JSON.stringify(deploymentInfo, null, 2));
    
    return contract.address;
}

main()
    .then((address) => {
        console.log(`\n🎉 Deployment completed successfully!`);
        console.log(`📍 Contract Address: ${address}`);
        console.log(`🔗 View on PolygonScan: https://amoy.polygonscan.com/address/${address}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    }); 