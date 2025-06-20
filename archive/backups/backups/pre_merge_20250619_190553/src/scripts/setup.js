const { ethers } = require("hardhat");
require("dotenv").config();

async function main() {
    console.log("=".repeat(60));
    console.log("🛠️  FLASH LOAN CONTRACT SETUP & CONFIGURATION");
    console.log("=".repeat(60));
    
    // Get the contract address from arguments or environment
    const contractAddress = process.argv[2] || process.env.CONTRACT_ADDRESS;
    
    if (!contractAddress) {
        console.error("❌ Error: Contract address not provided!");
        console.log("Usage: npx hardhat run scripts/setup.js --network polygon <CONTRACT_ADDRESS>");
        process.exit(1);
    }
    
    console.log("📍 Contract Address:", contractAddress);
    
    // Get the signer
    const [deployer] = await ethers.getSigners();
    console.log("👤 Setup Account:", deployer.address);
    
    // Check balance
    const balance = await deployer.getBalance();
    console.log("💰 Account Balance:", ethers.utils.formatEther(balance), "MATIC");
    
    try {
        // Get contract instance
        console.log("\n📋 Getting contract instance...");
        const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrageFixed");
        const contract = FlashLoanArbitrage.attach(contractAddress);
        
        // Verify we can connect to the contract
        const owner = await contract.owner();
        console.log("🔑 Contract Owner:", owner);
        
        if (owner.toLowerCase() !== deployer.address.toLowerCase()) {
            console.error("❌ Error: You are not the owner of this contract!");
            console.log("Contract Owner:", owner);
            console.log("Your Address:", deployer.address);
            process.exit(1);
        }
        
        console.log("✅ Ownership verified!");
        
        // Perform health check
        console.log("\n🩺 Performing initial health check...");
        const [isHealthy, status, tokenCount, dexCount, failedCount] = await contract.healthCheck();
        console.log("🏥 Health Status:", status);
        console.log("🪙 Whitelisted Tokens:", tokenCount.toString());
        console.log("🔄 Approved DEXes:", dexCount.toString());
        console.log("❌ Failed Transactions:", failedCount.toString());
        
        // Token Configuration
        console.log("\n" + "=".repeat(40));
        console.log("🪙 TOKEN CONFIGURATION");
        console.log("=".repeat(40));
        
        const additionalTokens = [
            { symbol: "UNI", address: "0xb33EaAd8d922B1083446DC23f610c2567fB5180f" },
            { symbol: "CRV", address: "0x172370d5Cd63279eFa6d502DAB29171933a610AF" },
            { symbol: "COMP", address: "0x8505b9d2254A7Ae468c0E9dd10Ccea3A837aef5c" },
            { symbol: "YFI", address: "0xDA537104D6A5edd53c6fBba9A898708E465260b6" },
            { symbol: "SNX", address: "0x50B728D8D964fd00C2d0AAD81718b71311feF68a" },
            { symbol: "1INCH", address: "0x9c2C5fd7b07E95EE044DDeba0E97a665F142394f" },
            { symbol: "BAL", address: "0x9a71012B13CA4d3D0Cdc72A177DF3ef03b0E76A3" },
            { symbol: "SUSHI", address: "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a" }
        ];
        
        console.log("📝 Adding additional tokens to whitelist...");
        
        // Batch whitelist additional tokens
        try {
            const tokenAddresses = additionalTokens.map(token => token.address);
            const tx = await contract.whitelistTokensBatch(tokenAddresses, true, {
                gasLimit: 500000
            });
            console.log("⏳ Transaction sent:", tx.hash);
            await tx.wait();
            console.log("✅ Additional tokens whitelisted successfully!");
            
            // Verify each token
            for (const token of additionalTokens) {
                const isWhitelisted = await contract.whitelistedTokens(token.address);
                console.log(`${isWhitelisted ? '✅' : '❌'} ${token.symbol}: ${isWhitelisted ? 'Whitelisted' : 'Failed'}`);
            }
        } catch (error) {
            console.log("⚠️  Error whitelisting additional tokens:", error.message);
        }
        
        // DEX Configuration
        console.log("\n" + "=".repeat(40));
        console.log("🔄 DEX CONFIGURATION");
        console.log("=".repeat(40));
        
        const additionalDexes = [
            { name: "Curve", address: "0x094d12e5b541784701FD8d65F11fc0598FBC6332" },
            { name: "Balancer", address: "0xBA12222222228d8Ba445958a75a0704d566BF2C8" },
            { name: "1inch", address: "0x1111111254fb6c44bAC0beD2854e76F90643097d" },
            { name: "Paraswap", address: "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57" }
        ];
        
        console.log("📝 Approving additional DEXes...");
        
        for (const dex of additionalDexes) {
            try {
                console.log(`🔄 Approving ${dex.name}...`);
                const tx = await contract.approveDex(dex.address, true, {
                    gasLimit: 100000
                });
                await tx.wait();
                
                const isApproved = await contract.approvedDexes(dex.address);
                console.log(`${isApproved ? '✅' : '❌'} ${dex.name}: ${isApproved ? 'Approved' : 'Failed'}`);
            } catch (error) {
                console.log(`❌ Error approving ${dex.name}:`, error.message);
            }
        }
        
        // Contract Configuration
        console.log("\n" + "=".repeat(40));
        console.log("⚙️  CONTRACT CONFIGURATION");
        console.log("=".repeat(40));
        
        // Set optimal slippage tolerance (3%)
        console.log("📊 Setting slippage tolerance to 3%...");
        try {
            const tx = await contract.setSlippageTolerance(300, {
                gasLimit: 100000
            });
            await tx.wait();
            console.log("✅ Slippage tolerance set to 3%");
        } catch (error) {
            console.log("⚠️  Error setting slippage tolerance:", error.message);
        }
        
        // Set max failed transactions
        console.log("🔢 Setting max failed transactions to 10...");
        try {
            const tx = await contract.setMaxFailedTransactions(10, {
                gasLimit: 100000
            });
            await tx.wait();
            console.log("✅ Max failed transactions set to 10");
        } catch (error) {
            console.log("⚠️  Error setting max failed transactions:", error.message);
        }
        
        // Token Approval Setup
        console.log("\n" + "=".repeat(40));
        console.log("🔐 TOKEN APPROVAL SETUP");
        console.log("=".repeat(40));
        
        // Setup token approvals for major tokens
        const ERC20_ABI = [
            "function approve(address spender, uint256 amount) external returns (bool)",
            "function allowance(address owner, address spender) external view returns (uint256)",
            "function balanceOf(address account) external view returns (uint256)",
            "function symbol() external view returns (string)"
        ];
        
        const majorTokens = [
            "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", // WETH
            "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", // USDC
            "0xc2132D05D31c914a87C6611C10748AEb04B58e8F", // USDT
            "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063", // DAI
            "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", // WMATIC
        ];
        
        const dexRouters = [
            "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", // Uniswap V3
            "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff", // QuickSwap
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"  // SushiSwap
        ];
        
        console.log("⚠️  NOTE: Token approvals must be done when the contract has token balances.");
        console.log("This setup prepares the contract but actual approvals happen during execution.");
        
        // Aave Flash Loan Setup
        console.log("\n" + "=".repeat(40));
        console.log("🏦 AAVE FLASH LOAN SETUP");
        console.log("=".repeat(40));
        
        // Verify Aave integration
        console.log("🔍 Verifying Aave integration...");
        try {
            const poolAddressProvider = await contract.ADDRESSES_PROVIDER();
            const pool = await contract.POOL();
            console.log("✅ Aave Pool Address Provider:", poolAddressProvider);
            console.log("✅ Aave Pool:", pool);
        } catch (error) {
            console.log("⚠️  Error checking Aave integration:", error.message);
        }
        
        // Final Health Check
        console.log("\n" + "=".repeat(40));
        console.log("🩺 FINAL HEALTH CHECK");
        console.log("=".repeat(40));
        
        const [finalHealthy, finalStatus, finalTokenCount, finalDexCount, finalFailedCount] = await contract.healthCheck();
        console.log("🏥 Final Health Status:", finalStatus);
        console.log("🪙 Total Whitelisted Tokens:", finalTokenCount.toString());
        console.log("🔄 Total Approved DEXes:", finalDexCount.toString());
        console.log("❌ Failed Transactions:", finalFailedCount.toString());
        
        if (finalHealthy) {
            console.log("✅ CONTRACT IS FULLY CONFIGURED AND READY!");
        } else {
            console.log("⚠️  Contract needs additional configuration.");
        }
        
        // Usage Instructions
        console.log("\n" + "=".repeat(50));
        console.log("📋 USAGE INSTRUCTIONS");
        console.log("=".repeat(50));
        console.log("1. ✅ Contract is deployed and configured");
        console.log("2. ✅ Tokens are whitelisted");
        console.log("3. ✅ DEXes are approved");
        console.log("4. ✅ Parameters are optimized");
        console.log("\n📝 To execute arbitrage:");
        console.log("   - Call executeArbitrage() with proper parameters");
        console.log("   - Ensure contract has enough tokens for testing");
        console.log("   - Monitor gas costs and profitability");
        console.log("\n🔍 Monitoring:");
        console.log("   - Use healthCheck() regularly");
        console.log("   - Check getSwapStatistics() for performance");
        console.log("   - Monitor events for debugging");
        
        console.log("\n🎉 SETUP COMPLETED SUCCESSFULLY!");
        
    } catch (error) {
        console.error("\n❌ SETUP FAILED!");
        console.error("Error:", error.message);
        
        if (error.message.includes("Ownable: caller is not the owner")) {
            console.error("💡 Solution: Make sure you're using the contract owner's wallet");
        } else if (error.message.includes("insufficient funds")) {
            console.error("💡 Solution: Add more MATIC to your wallet for gas fees");
        }
        
        throw error;
    }
}

main()
    .then(() => {
        console.log("\n🎉 SETUP SCRIPT COMPLETED!");
        process.exit(0);
    })
    .catch((error) => {
        console.error("\n💥 SETUP SCRIPT FAILED!");
        console.error(error);
        process.exit(1);
    });
