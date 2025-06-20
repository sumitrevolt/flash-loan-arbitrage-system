const { ethers } = require("hardhat");
require("dotenv").config();

async function main() {
    console.log("=".repeat(50));
    console.log("🚀 FLASH LOAN ARBITRAGE CONTRACT DEPLOYMENT");
    console.log("=".repeat(50));
    
    // Get the deployer account
    const [deployer] = await ethers.getSigners();
    console.log("📝 Deploying contracts with account:", deployer.address);
    
    // Check balance
    const balance = await deployer.getBalance();
    console.log("💰 Account balance:", ethers.utils.formatEther(balance), "MATIC");
    
    if (balance.lt(ethers.utils.parseEther("0.1"))) {
        console.log("⚠️  WARNING: Low balance detected! Make sure you have enough MATIC for deployment.");
    }
    
    // Aave V3 Pool Address Provider on Polygon
    const AAVE_POOL_ADDRESS_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb";
    console.log("🏦 Using Aave Pool Address Provider:", AAVE_POOL_ADDRESS_PROVIDER);
    
    try {
        // Get the contract factory
        console.log("\n📋 Getting contract factory...");
        const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrageFixed");
        
        // Estimate gas for deployment
        console.log("⛽ Estimating deployment gas...");
        const deployTx = FlashLoanArbitrage.getDeployTransaction(AAVE_POOL_ADDRESS_PROVIDER);
        const estimatedGas = await deployer.estimateGas(deployTx);
        console.log("📊 Estimated gas for deployment:", estimatedGas.toString());
        
        // Deploy the contract
        console.log("\n🔨 Deploying FlashLoanArbitrageFixed contract...");
        const flashLoanContract = await FlashLoanArbitrage.deploy(
            AAVE_POOL_ADDRESS_PROVIDER,
            {
                gasLimit: estimatedGas.mul(120).div(100), // Add 20% buffer
            }
        );
        
        console.log("⏳ Waiting for deployment transaction...");
        await flashLoanContract.deployed();
        
        console.log("\n✅ CONTRACT DEPLOYED SUCCESSFULLY!");
        console.log("📍 Contract Address:", flashLoanContract.address);
        console.log("🔗 Transaction Hash:", flashLoanContract.deployTransaction.hash);
        console.log("⛽ Gas Used:", flashLoanContract.deployTransaction.gasLimit?.toString());
        
        // Wait for a few confirmations before verification
        console.log("\n⏳ Waiting for confirmations...");
        await flashLoanContract.deployTransaction.wait(2);
        
        // Verify contract health
        console.log("\n🩺 Performing health check...");
        try {
            const [isHealthy, status, tokenCount, dexCount, failedCount] = await flashLoanContract.healthCheck();
            console.log("🏥 Health Status:", status);
            console.log("🪙 Whitelisted Tokens:", tokenCount.toString());
            console.log("🔄 Approved DEXes:", dexCount.toString());
            console.log("❌ Failed Transactions:", failedCount.toString());
            
            if (isHealthy) {
                console.log("✅ Contract is healthy and ready for use!");
            } else {
                console.log("⚠️  Contract needs attention before use.");
            }
        } catch (error) {
            console.log("⚠️  Could not perform health check:", error.message);
        }
        
        // Get contract info
        console.log("\n📋 Getting contract information...");
        try {
            const [version, deploymentDate, description] = await flashLoanContract.getContractInfo();
            console.log("📊 Contract Version:", version);
            console.log("📅 Contract Date:", deploymentDate);
            console.log("📝 Description:", description);
        } catch (error) {
            console.log("⚠️  Could not get contract info:", error.message);
        }
        
        // Check whitelisted tokens
        console.log("\n🪙 Checking whitelisted tokens...");
        const commonTokens = {
            "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
            "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "LINK": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
            "AAVE": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B"
        };
        
        for (const [symbol, address] of Object.entries(commonTokens)) {
            try {
                const isWhitelisted = await flashLoanContract.whitelistedTokens(address);
                console.log(`${isWhitelisted ? '✅' : '❌'} ${symbol} (${address}): ${isWhitelisted ? 'Whitelisted' : 'Not Whitelisted'}`);
            } catch (error) {
                console.log(`❌ ${symbol}: Error checking status`);
            }
        }
        
        // Check approved DEXes
        console.log("\n🔄 Checking approved DEXes...");
        const dexes = {
            "Uniswap V3": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
            "QuickSwap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
            "SushiSwap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
        };
        
        for (const [name, address] of Object.entries(dexes)) {
            try {
                const isApproved = await flashLoanContract.approvedDexes(address);
                console.log(`${isApproved ? '✅' : '❌'} ${name} (${address}): ${isApproved ? 'Approved' : 'Not Approved'}`);
            } catch (error) {
                console.log(`❌ ${name}: Error checking status`);
            }
        }
        
        // Save deployment information
        const deploymentInfo = {
            contractAddress: flashLoanContract.address,
            deploymentTransaction: flashLoanContract.deployTransaction.hash,
            deployer: deployer.address,
            network: "Polygon",
            timestamp: new Date().toISOString(),
            aavePoolAddressProvider: AAVE_POOL_ADDRESS_PROVIDER,
            gasUsed: flashLoanContract.deployTransaction.gasLimit?.toString(),
            whitelistedTokens: commonTokens,
            approvedDexes: dexes
        };
        
        console.log("\n💾 Deployment Summary:");
        console.log(JSON.stringify(deploymentInfo, null, 2));
        
        // Instructions for next steps
        console.log("\n" + "=".repeat(50));
        console.log("📋 NEXT STEPS:");
        console.log("=".repeat(50));
        console.log("1. Verify the contract on PolygonScan using:");
        console.log(`   npx hardhat verify --network polygon ${flashLoanContract.address} "${AAVE_POOL_ADDRESS_PROVIDER}"`);
        console.log("\n2. Fund the contract with some MATIC for gas fees");
        console.log("\n3. Test the contract with small amounts first");
        console.log("\n4. Monitor the contract health regularly");
        console.log("\n5. Consider setting up automated monitoring");
        
        return {
            contractAddress: flashLoanContract.address,
            deploymentHash: flashLoanContract.deployTransaction.hash
        };
        
    } catch (error) {
        console.error("\n❌ DEPLOYMENT FAILED!");
        console.error("Error:", error.message);
        
        if (error.message.includes("insufficient funds")) {
            console.error("💡 Solution: Add more MATIC to your wallet");
        } else if (error.message.includes("gas")) {
            console.error("💡 Solution: Try increasing gas limit or gas price");
        } else if (error.message.includes("nonce")) {
            console.error("💡 Solution: Wait a moment and try again, or reset your wallet nonce");
        }
        
        throw error;
    }
}

// Error handling and execution
main()
    .then((result) => {
        if (result) {
            console.log("\n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!");
            console.log("📍 Contract Address:", result.contractAddress);
        }
        process.exit(0);
    })
    .catch((error) => {
        console.error("\n💥 DEPLOYMENT SCRIPT FAILED!");
        console.error(error);
        process.exit(1);
    });
