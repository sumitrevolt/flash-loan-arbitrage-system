const { ethers } = require("hardhat");
const config = require("../config/amoy-config");

async function main() {
  console.log("🚀 Deploying FlashLoanArbitrageFixed to Amoy Testnet...");
  
  const [deployer] = await ethers.getSigners();
  
  console.log("📍 Deploying contracts with the account:", deployer.address);
  console.log("💰 Account balance:", (await deployer.provider.getBalance(deployer.address)).toString());

  // Get the contract factory
  const FlashLoanArbitrageFixed = await ethers.getContractFactory("FlashLoanArbitrageFixed");
  
  console.log("🔧 Contract compilation successful");
  
  // Deploy the contract with Aave Pool Addresses Provider
  console.log("📦 Deploying FlashLoanArbitrageFixed...");
  console.log("🏦 Using Aave Pool Addresses Provider:", config.AAVE.POOL_ADDRESSES_PROVIDER);
  
  const flashLoanContract = await FlashLoanArbitrageFixed.deploy(
    config.AAVE.POOL_ADDRESSES_PROVIDER,
    {
      gasLimit: 8000000,
      gasPrice: ethers.parseUnits("30", "gwei")
    }
  );

  await flashLoanContract.waitForDeployment();
  const contractAddress = await flashLoanContract.getAddress();

  console.log("✅ FlashLoanArbitrageFixed deployed to:", contractAddress);
  
  // Verify deployment
  console.log("🔍 Verifying deployment...");
  const owner = await flashLoanContract.owner();
  console.log("👤 Contract owner:", owner);
  
  // Get contract info
  const contractInfo = await flashLoanContract.getContractInfo();
  console.log("📋 Contract version:", contractInfo.version);
  console.log("📅 Deployment date:", contractInfo.deploymentDate);
  
  // Perform health check
  const healthCheck = await flashLoanContract.healthCheck();
  console.log("🏥 Health check:", healthCheck.isHealthy ? "✅ Healthy" : "❌ Needs Attention");
  console.log("📊 Status:", healthCheck.status);
  console.log("🪙 Whitelisted tokens:", healthCheck.whitelistedTokenCount.toString());
  console.log("🔄 Approved DEXes:", healthCheck.approvedDexCount.toString());

  // Setup initial tokens and DEXes
  console.log("\n🔧 Setting up tokens and DEXes...");
  
  // Whitelist all 15 tokens
  const tokenAddresses = Object.values(config.TOKENS).map(token => token.address);
  const tokenSymbols = Object.values(config.TOKENS).map(token => token.symbol);
  
  console.log("🪙 Whitelisting tokens:", tokenSymbols.join(", "));
  const whitelistTx = await flashLoanContract.whitelistTokensBatch(tokenAddresses, true);
  await whitelistTx.wait();
  console.log("✅ Tokens whitelisted successfully");

  // Approve additional DEXes
  console.log("🔄 Approving DEXes...");
  const dexesToApprove = [
    { name: "QuickSwap", address: config.DEXS.QUICKSWAP.ROUTER },
    { name: "SushiSwap", address: config.DEXS.SUSHISWAP.ROUTER },
    { name: "1inch", address: config.DEXS.ONEINCH.ROUTER }
  ];

  for (const dex of dexesToApprove) {
    const approveTx = await flashLoanContract.approveDex(dex.address, true);
    await approveTx.wait();
    console.log(`✅ ${dex.name} approved:`, dex.address);
  }

  // Final health check
  const finalHealthCheck = await flashLoanContract.healthCheck();
  console.log("\n🏥 Final Health Check:");
  console.log("📊 Status:", finalHealthCheck.isHealthy ? "✅ Healthy" : "❌ Needs Attention");
  console.log("🪙 Whitelisted tokens:", finalHealthCheck.whitelistedTokenCount.toString());
  console.log("🔄 Approved DEXes:", finalHealthCheck.approvedDexCount.toString());

  // Update config with deployed contract address
  config.CONTRACTS.FLASH_LOAN_ARBITRAGE = contractAddress;
  
  console.log("\n📋 Deployment Summary:");
  console.log("=====================================");
  console.log("📍 Contract Address:", contractAddress);
  console.log("🌐 Network:", config.NETWORK.NAME);
  console.log("⛽ Gas Used: ~8M gas");
  console.log("👤 Owner:", owner);
  console.log("🪙 Tokens Whitelisted:", tokenSymbols.length);
  console.log("🔄 DEXes Approved:", finalHealthCheck.approvedDexCount.toString());
  console.log("=====================================");

  console.log("\n🎯 Next Steps:");
  console.log("1. Update your .env file with the contract address");
  console.log("2. Fund your wallet with testnet tokens");
  console.log("3. Run the arbitrage bot: npm run bot");
  console.log("4. Monitor profits: npm run monitor");

  // Save deployment info
  const deploymentInfo = {
    contractAddress,
    deployer: deployer.address,
    network: config.NETWORK.NAME,
    chainId: config.NETWORK.CHAIN_ID,
    deploymentTime: new Date().toISOString(),
    gasUsed: "~8,000,000",
    tokensWhitelisted: tokenSymbols.length,
    dexesApproved: finalHealthCheck.approvedDexCount.toString()
  };

  console.log("\n💾 Saving deployment info...");
  const fs = require('fs');
  fs.writeFileSync(
    'deployment-info.json', 
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log("✅ Deployment info saved to deployment-info.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  }); 