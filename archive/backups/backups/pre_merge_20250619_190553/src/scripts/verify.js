const { ethers, run } = require("hardhat");
require("dotenv").config();

async function main() {
    console.log("=".repeat(50));
    console.log("🔍 CONTRACT VERIFICATION SCRIPT");
    console.log("=".repeat(50));
    
    // Contract address (will be provided as argument or from environment)
    const contractAddress = process.argv[2] || process.env.CONTRACT_ADDRESS;
    
    if (!contractAddress) {
        console.error("❌ Error: Contract address not provided!");
        console.log("Usage: npx hardhat run scripts/verify.js --network polygon <CONTRACT_ADDRESS>");
        console.log("Or set CONTRACT_ADDRESS environment variable");
        process.exit(1);
    }
    
    console.log("📍 Contract Address:", contractAddress);
    
    // Aave V3 Pool Address Provider on Polygon
    const AAVE_POOL_ADDRESS_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb";
    console.log("🏦 Constructor Argument - Aave Pool Address Provider:", AAVE_POOL_ADDRESS_PROVIDER);
    
    try {
        console.log("\n🔍 Starting contract verification...");
        
        await run("verify:verify", {
            address: contractAddress,
            constructorArguments: [AAVE_POOL_ADDRESS_PROVIDER],
        });
        
        console.log("\n✅ CONTRACT VERIFICATION SUCCESSFUL!");
        console.log("🔗 Your contract is now verified on PolygonScan");
        console.log(`📋 View at: https://polygonscan.com/address/${contractAddress}`);
        
    } catch (error) {
        if (error.message.toLowerCase().includes("already verified")) {
            console.log("\n✅ Contract is already verified!");
            console.log(`📋 View at: https://polygonscan.com/address/${contractAddress}`);
        } else {
            console.error("\n❌ VERIFICATION FAILED!");
            console.error("Error:", error.message);
            
            // Common troubleshooting tips
            console.log("\n💡 TROUBLESHOOTING TIPS:");
            console.log("1. Make sure POLYGONSCAN_API_KEY is set in your .env file");
            console.log("2. Wait a few minutes after deployment before verifying");
            console.log("3. Ensure the contract address is correct");
            console.log("4. Check that the constructor arguments match exactly");
            console.log("5. Try again in a few minutes - PolygonScan can be busy");
            
            throw error;
        }
    }
}

main()
    .then(() => {
        console.log("\n🎉 VERIFICATION SCRIPT COMPLETED!");
        process.exit(0);
    })
    .catch((error) => {
        console.error("\n💥 VERIFICATION SCRIPT FAILED!");
        console.error(error);
        process.exit(1);
    });
