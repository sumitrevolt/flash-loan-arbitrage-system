#!/usr/bin/env node
/**
 * Contract Configuration Script
 * Sets up initial configuration for the deployed flash loan contract
 */

const { ethers, network } = require("hardhat");
const fs = require("fs");
const path = require("path");

// Token addresses on Polygon
const POLYGON_TOKENS = {
  WETH: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
  WBTC: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
  USDC: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
  USDT: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
  DAI: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
  WMATIC: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
  LINK: "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
  AAVE: "0xD6DF932A45C0f255f85145f286eA0b292B21C90B"
};

// DEX router addresses on Polygon
const POLYGON_DEXES = {
  UniswapV3: "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
  QuickSwap: "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
  SushiSwap: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
};

async function main() {
  console.log("\n⚙️  Flash Loan Contract Configuration");
  console.log("=" * 50);
  
  const [owner] = await ethers.getSigners();
  const networkName = network.name;
  
  // Load deployment info
  const deploymentFile = path.join(__dirname, "..", "..", "deployments", `${networkName}-deployment.json`);
  
  if (!fs.existsSync(deploymentFile)) {
    throw new Error(`Deployment file not found: ${deploymentFile}`);
  }
  
  const deploymentInfo = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  const contractAddress = deploymentInfo.contractAddress;
  
  console.log(`📡 Network: ${deploymentInfo.networkName}`);
  console.log(`📍 Contract: ${contractAddress}`);
  console.log(`👤 Owner: ${owner.address}`);
  
  // Connect to deployed contract
  const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrageFixed");
  const contract = FlashLoanArbitrage.attach(contractAddress);
  
  console.log("\n🔍 Checking current contract status...");
  
  // Check if owner matches
  const contractOwner = await contract.owner();
  if (contractOwner.toLowerCase() !== owner.address.toLowerCase()) {
    throw new Error(`Owner mismatch! Contract owner: ${contractOwner}, Signer: ${owner.address}`);
  }
  
  // Get contract health
  const [isHealthy, status, tokenCount, dexCount] = await contract.healthCheck();
  console.log(`📊 Health Status: ${status}`);
  console.log(`🪙 Whitelisted Tokens: ${tokenCount}`);
  console.log(`🔄 Approved DEXes: ${dexCount}`);
  
  if (!isHealthy) {
    console.log("\n⚠️  Contract needs configuration. Setting up...");
    
    // Configure slippage tolerance
    console.log("🎯 Setting slippage tolerance to 3%...");
    const slippageTx = await contract.setSlippageTolerance(300); // 3%
    await slippageTx.wait();
    console.log("✅ Slippage tolerance configured");
    
    // Configure circuit breaker
    console.log("🛡️ Setting circuit breaker to 10 failed transactions...");
    const circuitTx = await contract.setMaxFailedTransactions(10);
    await circuitTx.wait();
    console.log("✅ Circuit breaker configured");
    
    // Batch whitelist additional tokens if needed
    const tokensToWhitelist = Object.values(POLYGON_TOKENS);
    console.log("🪙 Whitelisting additional tokens...");
    
    try {
      const whitelistTx = await contract.whitelistTokensBatch(tokensToWhitelist, true);
      await whitelistTx.wait();
      console.log("✅ Tokens whitelisted");
    } catch (error) {
      console.log("⚠️  Tokens already whitelisted or error occurred:", error.message);
    }
    
    // Approve additional DEXes
    console.log("🔄 Approving DEXes...");
    
    for (const [dexName, dexAddress] of Object.entries(POLYGON_DEXES)) {
      try {
        const approveTx = await contract.approveDex(dexAddress, true);
        await approveTx.wait();
        console.log(`✅ ${dexName} approved`);
      } catch (error) {
        console.log(`⚠️  ${dexName} already approved or error:`, error.message);
      }
    }
    
    // Configure fees (2% to owner)
    console.log("💰 Configuring fee structure (2% to owner)...");
    const feeTx = await contract.setFeeParameters(
      200, // 2%
      owner.address, // Fee recipient
      true // Fees enabled
    );
    await feeTx.wait();
    console.log("✅ Fee structure configured");
  }
  
  // Final health check
  console.log("\n🔍 Final health check...");
  const [finalHealthy, finalStatus, finalTokens, finalDexes] = await contract.healthCheck();
  
  console.log(`📊 Final Status: ${finalStatus}`);
  console.log(`🪙 Whitelisted Tokens: ${finalTokens}`);
  console.log(`🔄 Approved DEXes: ${finalDexes}`);
  
  if (finalHealthy) {
    console.log("✅ Contract is healthy and ready for operation!");
  } else {
    console.log("⚠️  Contract still needs attention");
  }
  
  // Save configuration info
  const configInfo = {
    ...deploymentInfo,
    configured: true,
    configuredAt: new Date().toISOString(),
    finalHealthStatus: finalStatus,
    tokensConfigured: finalTokens,
    dexesConfigured: finalDexes,
    slippageTolerance: "3%",
    circuitBreakerLimit: 10,
    feePercentage: "2%",
    feeRecipient: owner.address
  };
  
  fs.writeFileSync(deploymentFile, JSON.stringify(configInfo, null, 2));
  
  console.log("\n🎉 Configuration complete!");
  console.log("\n📋 Next Steps:");
  console.log("1. Test the contract with small amounts");
  console.log("2. Monitor gas costs and performance");
  console.log("3. Set up automated monitoring");
  console.log("4. Begin arbitrage operations");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Configuration failed:");
    console.error(error);
    process.exit(1);
  });
