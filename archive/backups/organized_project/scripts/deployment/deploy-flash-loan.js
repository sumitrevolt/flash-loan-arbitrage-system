#!/usr/bin/env node
/**
 * Flash Loan Arbitrage Contract Deployment Script
 * Deploys FlashLoanArbitrageFixed contract to Polygon network
 */

const { ethers, network } = require("hardhat");
const fs = require("fs");
const path = require("path");

// Network configurations
const NETWORK_CONFIGS = {
  polygon: {
    aaveAddressProvider: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    name: "Polygon Mainnet"
  },
  mumbai: {
    aaveAddressProvider: "0x5343b5bA672Ae99d627A1C87866b8E53F47Db2E6",
    name: "Mumbai Testnet"
  },
  hardhat: {
    aaveAddressProvider: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb", // Fork Polygon
    name: "Hardhat Fork"
  }
};

async function main() {
  console.log("\n🚀 Flash Loan Arbitrage Contract Deployment");
  console.log("=" * 60);
  
  const [deployer] = await ethers.getSigners();
  const networkName = network.name;
  const config = NETWORK_CONFIGS[networkName];
  
  if (!config) {
    throw new Error(`Unsupported network: ${networkName}`);
  }
  
  console.log(`📡 Network: ${config.name}`);
  console.log(`👤 Deployer: ${deployer.address}`);
  console.log(`💰 Balance: ${ethers.formatEther(await deployer.provider.getBalance(deployer.address))} MATIC`);
  console.log(`🏦 Aave Provider: ${config.aaveAddressProvider}`);
  
  // Check minimum balance
  const balance = await deployer.provider.getBalance(deployer.address);
  const minBalance = ethers.parseEther("0.1"); // 0.1 MATIC minimum
  
  if (balance < minBalance) {
    throw new Error(`Insufficient balance. Need at least 0.1 MATIC for deployment`);
  }
  
  console.log("\n🔨 Deploying FlashLoanArbitrageFixed contract...");
  
  // Get contract factory
  const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrageFixed");
  
  // Estimate deployment gas
  const deploymentData = FlashLoanArbitrage.interface.encodeDeploy([config.aaveAddressProvider]);
  const gasEstimate = await deployer.provider.estimateGas({
    data: deploymentData
  });
  
  console.log(`⛽ Estimated gas: ${gasEstimate.toString()}`);
  
  // Deploy contract
  const contract = await FlashLoanArbitrage.deploy(
    config.aaveAddressProvider,
    {
      gasLimit: Math.ceil(Number(gasEstimate) * 1.2) // 20% buffer
    }
  );
  
  console.log("\n⏳ Waiting for deployment confirmation...");
  await contract.waitForDeployment();
  
  const contractAddress = await contract.getAddress();
  const deploymentTx = contract.deploymentTransaction();
  
  console.log("\n✅ Deployment successful!");
  console.log(`📍 Contract Address: ${contractAddress}`);
  console.log(`🔗 Transaction Hash: ${deploymentTx.hash}`);
  console.log(`⛽ Gas Used: ${deploymentTx.gasLimit.toString()}`);
  
  // Verify contract deployment
  console.log("\n🔍 Verifying contract deployment...");
  
  try {
    const owner = await contract.owner();
    const addressProvider = await contract.ADDRESSES_PROVIDER();
    
    console.log(`👤 Contract Owner: ${owner}`);
    console.log(`🏦 Address Provider: ${addressProvider}`);
    
    if (owner.toLowerCase() === deployer.address.toLowerCase() && 
        addressProvider.toLowerCase() === config.aaveAddressProvider.toLowerCase()) {
      console.log("✅ Contract verification successful!");
    } else {
      throw new Error("Contract verification failed!");
    }
  } catch (error) {
    console.error("❌ Contract verification failed:", error.message);
  }
  
  // Save deployment info
  const deploymentInfo = {
    network: networkName,
    networkName: config.name,
    contractAddress: contractAddress,
    deployerAddress: deployer.address,
    transactionHash: deploymentTx.hash,
    blockNumber: deploymentTx.blockNumber,
    gasUsed: deploymentTx.gasLimit.toString(),
    aaveAddressProvider: config.aaveAddressProvider,
    timestamp: new Date().toISOString(),
    contractVersion: "2.1"
  };
  
  const deploymentDir = path.join(__dirname, "..", "..", "deployments");
  if (!fs.existsSync(deploymentDir)) {
    fs.mkdirSync(deploymentDir, { recursive: true });
  }
  
  const deploymentFile = path.join(deploymentDir, `${networkName}-deployment.json`);
  fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
  
  console.log(`\n💾 Deployment info saved to: ${deploymentFile}`);
  
  // Update environment file
  if (networkName === "polygon") {
    updateEnvFile(contractAddress);
  }
  
  console.log("\n🎉 Deployment complete!");
  console.log("\n📋 Next Steps:");
  console.log("1. Verify contract on PolygonScan:");
  console.log(`   npx hardhat verify --network ${networkName} ${contractAddress} "${config.aaveAddressProvider}"`);
  console.log("2. Setup initial configuration:");
  console.log(`   node scripts/setup/configure-contract.js --network ${networkName} --address ${contractAddress}`);
  console.log("3. Test the deployment:");
  console.log(`   npm run test:deployed -- --network ${networkName}`);
}

function updateEnvFile(contractAddress) {
  const envPath = path.join(__dirname, "..", "..", ".env");
  let envContent = "";
  
  if (fs.existsSync(envPath)) {
    envContent = fs.readFileSync(envPath, "utf8");
  }
  
  // Update or add contract address
  const contractAddressLine = `FLASH_LOAN_CONTRACT_ADDRESS=${contractAddress}`;
  
  if (envContent.includes("FLASH_LOAN_CONTRACT_ADDRESS=")) {
    envContent = envContent.replace(
      /FLASH_LOAN_CONTRACT_ADDRESS=.*/,
      contractAddressLine
    );
  } else {
    envContent += `\n${contractAddressLine}\n`;
  }
  
  fs.writeFileSync(envPath, envContent);
  console.log("✅ Updated .env file with contract address");
}

// Handle errors
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:");
    console.error(error);
    process.exit(1);
  });
