require('dotenv').config();
const { ethers } = require('hardhat');

async function main() {
    console.log("🚀 Deploying AaveFlashLoanFixed Contract...\n");
    
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
    console.log("⚙️  Compiling and deploying AaveFlashLoanFixed...");
    const AaveFlashLoanFixed = await ethers.getContractFactory("AaveFlashLoanFixed");
    
    const contract = await AaveFlashLoanFixed.deploy(AAVE_POOL_ADDRESSES_PROVIDER, {
        gasLimit: 2000000,
        gasPrice: ethers.utils.parseUnits("30", "gwei")
    });
    
    await contract.deployed();
    
    console.log("✅ AaveFlashLoanFixed deployed to:", contract.address);
    console.log("📄 Transaction hash:", contract.deployTransaction.hash);
    console.log("⛽ Gas used:", contract.deployTransaction.gasLimit.toString());
    
    // Wait for confirmations
    console.log("\n⏳ Waiting for block confirmations...");
    await contract.deployTransaction.wait(3);
    
    // Get contract info
    console.log("🔍 Verifying contract deployment...");
    const owner = await contract.getOwner();
    const flashLoanCount = await contract.getFlashLoanCount();
    const totalProfit = await contract.getTotalProfit();
    
    console.log("\n📊 Contract Information:");
    console.log("- Owner:", owner);
    console.log("- Flash Loan Count:", flashLoanCount.toString());
    console.log("- Total Profit Generated:", ethers.utils.formatUnits(totalProfit, 6), "tokens");
    console.log("- USDC Address:", await contract.USDC());
    console.log("- WMATIC Address:", await contract.WMATIC());
    
    // Get Aave pool info
    const poolAddressProvider = await contract.ADDRESSES_PROVIDER();
    const poolAddress = await contract.POOL();
    
    console.log("\n🏦 Aave Integration:");
    console.log("- Pool Addresses Provider:", poolAddressProvider);
    console.log("- Pool Address:", poolAddress);
    
    console.log("\n✅ Contract Features:");
    console.log("- ✅ Real Aave V3 Flash Loans");
    console.log("- ✅ Multiple Arbitrage Strategies");
    console.log("- ✅ Event Logging & Debugging");
    console.log("- ✅ Owner Access Control");
    console.log("- ✅ Emergency Withdrawal Functions");
    
    console.log("\n🚀 Next Steps:");
    console.log("1. Run: node scripts/aave-flashloan-simple-bot.js");
    console.log("2. Execute real Aave flash loans");
    console.log("3. Monitor arbitrage results");
    
    // Save deployment info
    const deploymentInfo = {
        network: "amoy",
        contractName: "AaveFlashLoanFixed",
        contractAddress: contract.address,
        transactionHash: contract.deployTransaction.hash,
        deployer: deployer.address,
        timestamp: new Date().toISOString(),
        aavePoolAddressProvider: AAVE_POOL_ADDRESSES_PROVIDER,
        gasUsed: contract.deployTransaction.gasLimit.toString(),
        owner: owner
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