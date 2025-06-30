require('dotenv').config();
const { ethers } = require('hardhat');

async function main() {
    console.log("Deploying Aave Flash Loan Arbitrage Contract...\n");
    
    // Get the deployer account
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);
    
    // Get account balance
    const balance = await deployer.getBalance();
    console.log("Account balance:", ethers.utils.formatEther(balance), "POL\n");
    
    // Aave V3 Pool Address Provider on Amoy testnet
    const AAVE_POOL_ADDRESSES_PROVIDER = "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A";
    
    console.log("Using Aave Pool Addresses Provider:", AAVE_POOL_ADDRESSES_PROVIDER);
    
    // Deploy the contract
    const AaveFlashLoanArbitrage = await ethers.getContractFactory("AaveFlashLoanArbitrage");
    const contract = await AaveFlashLoanArbitrage.deploy(AAVE_POOL_ADDRESSES_PROVIDER);
    
    await contract.deployed();
    
    console.log("✅ AaveFlashLoanArbitrage deployed to:", contract.address);
    console.log("📄 Transaction hash:", contract.deployTransaction.hash);
    console.log("⛽ Gas used:", contract.deployTransaction.gasLimit.toString());
    
    // Wait for a few block confirmations
    console.log("\nWaiting for block confirmations...");
    await contract.deployTransaction.wait(2);
    
    // Get contract info
    const owner = await contract.getOwner();
    const flashLoanCount = await contract.getFlashLoanCount();
    
    console.log("\n📊 Contract Information:");
    console.log("- Owner:", owner);
    console.log("- Flash Loan Count:", flashLoanCount.toString());
    console.log("- USDC Address:", await contract.USDC());
    console.log("- WMATIC Address:", await contract.WMATIC());
    
    // Get Aave pool address from the contract
    const poolAddressProvider = await contract.ADDRESSES_PROVIDER();
    const poolAddress = await contract.POOL();
    
    console.log("\n🏦 Aave Integration:");
    console.log("- Pool Addresses Provider:", poolAddressProvider);
    console.log("- Pool Address:", poolAddress);
    
    console.log("\n✨ Contract deployed successfully!");
    console.log("\n🚀 Next steps:");
    console.log("1. Run: node scripts/aave-flashloan-bot.js");
    console.log("2. The bot will execute real Aave flash loans for arbitrage");
    
    // Save deployment info
    const deploymentInfo = {
        network: "amoy",
        contractAddress: contract.address,
        transactionHash: contract.deployTransaction.hash,
        deployer: deployer.address,
        timestamp: new Date().toISOString(),
        aavePoolAddressProvider: AAVE_POOL_ADDRESSES_PROVIDER,
        gasUsed: contract.deployTransaction.gasLimit.toString()
    };
    
    console.log("\n💾 Deployment Info:", JSON.stringify(deploymentInfo, null, 2));
    
    return contract.address;
}

main()
    .then((address) => {
        console.log(`\n🎉 Deployment completed! Contract address: ${address}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    }); 