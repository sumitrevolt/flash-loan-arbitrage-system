require('dotenv').config();
const { ethers } = require('hardhat');

async function main() {
    console.log("🔍 Checking Aave V3 availability on Amoy testnet...\n");
    
    const provider = new ethers.providers.JsonRpcProvider(process.env.AMOY_RPC_URL);
    const [signer] = await ethers.getSigners();
    
    console.log("📍 Wallet address:", signer.address);
    
    // Aave V3 Pool Address Provider on Amoy testnet
    const AAVE_POOL_ADDRESSES_PROVIDER = "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A";
    
    console.log("🏦 Checking Aave Pool Addresses Provider:", AAVE_POOL_ADDRESSES_PROVIDER);
    
    try {
        // Check if address exists
        const code = await provider.getCode(AAVE_POOL_ADDRESSES_PROVIDER);
        console.log("📄 Contract code length:", code.length);
        
        if (code === "0x") {
            console.log("❌ No contract found at this address");
            console.log("🔄 Aave V3 might not be deployed on Amoy testnet");
            
            // Let's check Polygon mainnet addresses for reference
            console.log("\n📋 Known Aave V3 addresses:");
            console.log("- Polygon Mainnet Pool Provider: 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb");
            console.log("- Ethereum Mainnet Pool Provider: 0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e");
            
        } else {
            console.log("✅ Contract found!");
            
            // Try to read the pool address
            const poolAddressProviderABI = [
                "function getPool() external view returns (address)"
            ];
            
            const poolAddressProvider = new ethers.Contract(
                AAVE_POOL_ADDRESSES_PROVIDER,
                poolAddressProviderABI,
                provider
            );
            
            const poolAddress = await poolAddressProvider.getPool();
            console.log("🏊 Pool address:", poolAddress);
            
            // Check if pool exists
            const poolCode = await provider.getCode(poolAddress);
            if (poolCode === "0x") {
                console.log("❌ Pool contract not found");
            } else {
                console.log("✅ Pool contract exists!");
                console.log("📄 Pool code length:", poolCode.length);
            }
        }
        
    } catch (error) {
        console.error("❌ Error checking Aave contracts:", error.message);
        
        console.log("\n🔄 Alternative approach: Let's check what testnets Aave supports");
        console.log("Known Aave V3 testnets:");
        console.log("- Sepolia: 0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A");
        console.log("- Goerli: 0xC911B590248d127aD18546B186cC6B324e99F02c");
        console.log("- Mumbai: Not available anymore (deprecated)");
        
        console.log("\n💡 Solution: We might need to use a different testnet or create a mock flash loan");
    }
    
    // Check current network
    const network = await provider.getNetwork();
    console.log("\n🌐 Current network:");
    console.log("- Chain ID:", network.chainId);
    console.log("- Name:", network.name);
    
    if (network.chainId !== 80002) {
        console.log("⚠️ Warning: Expected Amoy chain ID 80002, got", network.chainId);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Script failed:", error);
        process.exit(1);
    }); 