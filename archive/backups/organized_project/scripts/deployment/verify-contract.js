#!/usr/bin/env node
/**
 * Contract Verification Script for PolygonScan
 * Automatically verifies the deployed flash loan contract
 */

const { run, network } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("\n🔍 Contract Verification on PolygonScan");
  console.log("=" * 50);
  
  const networkName = network.name;
  
  // Load deployment info
  const deploymentFile = path.join(__dirname, "..", "..", "deployments", `${networkName}-deployment.json`);
  
  if (!fs.existsSync(deploymentFile)) {
    throw new Error(`Deployment file not found: ${deploymentFile}`);
  }
  
  const deploymentInfo = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  
  console.log(`📡 Network: ${deploymentInfo.networkName}`);
  console.log(`📍 Contract: ${deploymentInfo.contractAddress}`);
  console.log(`🏦 Aave Provider: ${deploymentInfo.aaveAddressProvider}`);
  
  try {
    console.log("\n⏳ Submitting verification to PolygonScan...");
    
    await run("verify:verify", {
      address: deploymentInfo.contractAddress,
      constructorArguments: [deploymentInfo.aaveAddressProvider],
      contract: "contracts/FlashLoanArbitrageFixed.sol:FlashLoanArbitrageFixed"
    });
    
    console.log("✅ Contract verification successful!");
    
    // Update deployment info with verification status
    deploymentInfo.verified = true;
    deploymentInfo.verifiedAt = new Date().toISOString();
    
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
    
    console.log(`\n🔗 View verified contract at:`);
    
    if (networkName === "polygon") {
      console.log(`   https://polygonscan.com/address/${deploymentInfo.contractAddress}`);
    } else if (networkName === "mumbai") {
      console.log(`   https://mumbai.polygonscan.com/address/${deploymentInfo.contractAddress}`);
    }
    
  } catch (error) {
    if (error.message.includes("Already Verified")) {
      console.log("✅ Contract is already verified!");
    } else {
      throw error;
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Verification failed:");
    console.error(error);
    process.exit(1);
  });
