const hre = require("hardhat");

async function main() {
    console.log("🚀 Deploying FlashLoanArbitrageFixed to Amoy testnet...");
    console.log("============================================================");

    // Get the contract factory
    const FlashLoanArbitrageFixed = await hre.ethers.getContractFactory("FlashLoanArbitrageFixed");
    
    // Aave Pool Addresses Provider on Amoy testnet
    const aavePoolAddressesProvider = "0x69850E1C0C6e20DaD83BdB9A26E5F5ee3C9951E5";
    
    console.log(`📋 Using Aave Pool Addresses Provider: ${aavePoolAddressesProvider}`);
    
    // Deploy the contract
    console.log("🔨 Deploying contract...");
    const contract = await FlashLoanArbitrageFixed.deploy(aavePoolAddressesProvider);
    
    // Wait for deployment
    await contract.waitForDeployment();
    
    const contractAddress = await contract.getAddress();
    console.log(`✅ Contract deployed to: ${contractAddress}`);
    
    // Get deployer info
    const [deployer] = await hre.ethers.getSigners();
    const balance = await hre.ethers.provider.getBalance(deployer.address);
    
    console.log(`👤 Deployer: ${deployer.address}`);
    console.log(`💰 Deployer Balance: ${hre.ethers.formatEther(balance)} MATIC`);
    
    // Wait a bit for the contract to be indexed
    console.log("⏳ Waiting for contract to be indexed...");
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    // Test basic functionality
    console.log("🧪 Testing basic contract functions...");
    try {
        const owner = await contract.owner();
        const isHealthy = await contract.healthCheck();
        const contractInfo = await contract.getContractInfo();
        
        console.log(`✅ Contract Owner: ${owner}`);
        console.log(`✅ Contract Healthy: ${isHealthy[0]} (${isHealthy[1]})`);
        console.log(`✅ Contract Version: ${contractInfo[0]}`);
        console.log(`✅ Whitelisted Tokens: ${isHealthy[2]}`);
        console.log(`✅ Approved DEXes: ${isHealthy[3]}`);
        
    } catch (error) {
        console.log(`⚠️  Error testing contract: ${error.message}`);
    }
    
    console.log("\n🎯 DEPLOYMENT COMPLETE!");
    console.log("============================================================");
    console.log(`📝 Update your .env file with:`);
    console.log(`CONTRACT_ADDRESS=${contractAddress}`);
    console.log(`\n🔧 Update real_revenue_generator.py with:`);
    console.log(`self.contract_address = "${contractAddress}"`);
    
    // Save deployment info
    const deploymentInfo = {
        network: "amoy",
        contractAddress: contractAddress,
        deployer: deployer.address,
        timestamp: new Date().toISOString(),
        aavePoolAddressesProvider: aavePoolAddressesProvider,
        version: "2.1"
    };
    
    require('fs').writeFileSync(
        'deployment_info.json', 
        JSON.stringify(deploymentInfo, null, 2)
    );
    
    console.log(`💾 Deployment info saved to deployment_info.json`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    }); 