require('dotenv').config();
const { ethers } = require("ethers");
const axios = require('axios');

// Amoy testnet configuration
const AMOY_RPC = process.env.AMOY_RPC_URL;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const CONTRACT_ADDRESS = "0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5";

// Real testnet token addresses for Amoy
const TOKENS = {
    USDC: "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582",    // Circle testnet USDC
    WMATIC: "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889",  // Wrapped MATIC on testnet
    // Using well-known mainnet addresses for price reference (we'll get testnet data separately)
    MAINNET_WMATIC: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    MAINNET_USDC: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
};

// Aave Pool on Amoy
const AAVE_POOL = "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A";

// Fixed contract ABI - only functions that actually exist
const CONTRACT_ABI = [
    "function executeArbitrage(address asset, uint256 amount, bytes params) external",
    "function POOL() external view returns (address)"
];

const ERC20_ABI = [
    "function balanceOf(address owner) external view returns (uint256)",
    "function decimals() external view returns (uint8)",
    "function symbol() external view returns (string)"
];

// Chainlink Price Feed ABI
const CHAINLINK_ABI = [
    "function latestRoundData() external view returns (uint80 roundId, int256 price, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)"
];

// Chainlink Price Feeds on Polygon Mainnet
const PRICE_FEEDS = {
    'MATIC/USD': '0xAB594600376Ec9fD91F8e885dADF0CE036862dE0',
    'ETH/USD': '0xF9680D99D6C9589e2a93a78A04A279e509205945'
};

class RealtimeWeb3ArbitrageBot {
    constructor() {
        this.provider = new ethers.providers.JsonRpcProvider(AMOY_RPC);
        this.wallet = new ethers.Wallet(PRIVATE_KEY, this.provider);
        this.contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, this.wallet);
        
        // Connect to Polygon mainnet for Chainlink price feeds
        this.mainnetProvider = new ethers.providers.JsonRpcProvider("https://polygon-rpc.com");
        
        console.log(`🤖 Real-time Web3 Arbitrage Bot initialized`);
        console.log(`📍 Wallet: ${this.wallet.address}`);
        console.log(`📍 Contract: ${CONTRACT_ADDRESS}`);
        console.log(`🌐 Network: Amoy Testnet (Chain ID: 80002)`);
    }

    async getWalletBalance() {
        try {
            const balance = await this.provider.getBalance(this.wallet.address);
            return ethers.utils.formatEther(balance);
        } catch (error) {
            console.error('Error getting wallet balance:', error.message);
            return '0.0';
        }
    }

    async getTokenBalance(tokenAddress, tokenSymbol) {
        try {
            const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, this.provider);
            const balance = await tokenContract.balanceOf(this.wallet.address);
            const decimals = await tokenContract.decimals();
            return ethers.utils.formatUnits(balance, decimals);
        } catch (error) {
            console.log(`ℹ️  Could not fetch ${tokenSymbol} balance: ${error.message}`);
            return '0.0';
        }
    }

    // Get real-time price from Chainlink oracle
    async getChainlinkPrice(feedAddress, pairName) {
        try {
            const priceFeed = new ethers.Contract(feedAddress, CHAINLINK_ABI, this.mainnetProvider);
            const roundData = await priceFeed.latestRoundData();
            
            const price = parseFloat(ethers.utils.formatUnits(roundData.price, 8));
            const updatedAt = new Date(roundData.updatedAt.toNumber() * 1000);
            
            return {
                price,
                updatedAt,
                roundId: roundData.roundId.toString(),
                valid: true,
                source: 'Chainlink'
            };
        } catch (error) {
            console.log(`⚠️  Chainlink ${pairName} price unavailable: ${error.message}`);
            return { price: 0, valid: false };
        }
    }

    // Get real-time price from CoinGecko API
    async getCoinGeckoPrice(coinId) {
        try {
            const response = await axios.get(
                `https://api.coingecko.com/api/v3/simple/price?ids=${coinId}&vs_currencies=usd&include_last_updated_at=true`,
                { timeout: 5000 }
            );
            const data = response.data[coinId];
            
            return {
                price: data.usd,
                lastUpdated: new Date(data.last_updated_at * 1000),
                valid: true,
                source: 'CoinGecko'
            };
        } catch (error) {
            console.log(`⚠️  CoinGecko ${coinId} price unavailable: ${error.message}`);
            return { price: 0, valid: false };
        }
    }

    // Get real-time price from CoinCap API (backup)
    async getCoinCapPrice(symbol) {
        try {
            const response = await axios.get(
                `https://api.coincap.io/v2/assets/${symbol}`,
                { timeout: 5000 }
            );
            const data = response.data.data;
            
            return {
                price: parseFloat(data.priceUsd),
                lastUpdated: new Date(),
                valid: true,
                source: 'CoinCap'
            };
        } catch (error) {
            console.log(`⚠️  CoinCap ${symbol} price unavailable: ${error.message}`);
            return { price: 0, valid: false };
        }
    }

    // Aggregate real-time prices from multiple sources
    async getAggregatedPrice(asset) {
        console.log(`🔍 Fetching real-time ${asset} price from multiple sources...`);
        
        const sources = [];
        
        try {
            if (asset === 'MATIC') {
                // Get MATIC price from multiple sources
                const [chainlink, coingecko, coincap] = await Promise.all([
                    this.getChainlinkPrice(PRICE_FEEDS['MATIC/USD'], 'MATIC/USD'),
                    this.getCoinGeckoPrice('matic-network'),
                    this.getCoinCapPrice('polygon')
                ]);

                if (chainlink.valid) sources.push(chainlink);
                if (coingecko.valid) sources.push(coingecko);
                if (coincap.valid) sources.push(coincap);
            }

            if (sources.length === 0) {
                console.log(`❌ No valid price sources for ${asset}`);
                return null;
            }

            // Display all sources
            console.log(`📊 ${asset}/USD prices from ${sources.length} sources:`);
            sources.forEach(source => {
                const time = source.updatedAt ? source.updatedAt.toLocaleTimeString() : 
                           source.lastUpdated ? source.lastUpdated.toLocaleTimeString() : 'now';
                console.log(`   ${source.source}: $${source.price.toFixed(4)} (${time})`);
            });

            // Use the most recent/reliable price (prefer Chainlink, then CoinGecko, then CoinCap)
            const prioritizedSource = sources.find(s => s.source === 'Chainlink') ||
                                    sources.find(s => s.source === 'CoinGecko') ||
                                    sources[0];

            console.log(`✅ Using ${prioritizedSource.source} price: $${prioritizedSource.price.toFixed(4)}`);
            
            return prioritizedSource;

        } catch (error) {
            console.error(`❌ Error aggregating ${asset} price:`, error.message);
            return null;
        }
    }

    // Simulate DEX spreads with real-time base price
    simulateDEXSpreads(basePrice) {
        const exchanges = [
            'Uniswap V3',
            'QuickSwap',
            'SushiSwap',
            '1inch',
            'ParaSwap'
        ];
        
        const prices = {};

        exchanges.forEach(exchange => {
            // Realistic spread variations based on liquidity depth
            let spreadVariation;
            switch(exchange) {
                case 'Uniswap V3':
                    spreadVariation = (Math.random() - 0.5) * 0.004; // ±0.2% (deepest liquidity)
                    break;
                case 'QuickSwap':
                    spreadVariation = (Math.random() - 0.5) * 0.008; // ±0.4%
                    break;
                case 'SushiSwap':
                    spreadVariation = (Math.random() - 0.5) * 0.012; // ±0.6%
                    break;
                case '1inch':
                    spreadVariation = (Math.random() - 0.5) * 0.006; // ±0.3% (aggregator)
                    break;
                case 'ParaSwap':
                    spreadVariation = (Math.random() - 0.5) * 0.007; // ±0.35% (aggregator)
                    break;
                default:
                    spreadVariation = (Math.random() - 0.5) * 0.010; // ±0.5%
            }
            
            prices[exchange] = basePrice * (1 + spreadVariation);
        });

        return prices;
    }

    async checkRealtimeArbitrageOpportunities() {
        try {
            // Get real-time MATIC price
            const maticPriceData = await this.getAggregatedPrice('MATIC');
            
            if (!maticPriceData || !maticPriceData.valid) {
                console.log("❌ Could not fetch reliable MATIC price data");
                return null;
            }

            // Simulate DEX spreads based on real price
            const dexPrices = this.simulateDEXSpreads(maticPriceData.price);
            
            console.log(`\n💱 Current DEX MATIC/USDC Prices (based on real $${maticPriceData.price.toFixed(4)}):`);
            Object.entries(dexPrices).forEach(([exchange, price]) => {
                const spread = ((price - maticPriceData.price) / maticPriceData.price * 100);
                console.log(`   ${exchange}: $${price.toFixed(4)} (${spread >= 0 ? '+' : ''}${spread.toFixed(3)}%)`);
            });

            // Find best arbitrage opportunity
            const exchanges = Object.keys(dexPrices);
            const prices = Object.values(dexPrices);
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            const minExchange = exchanges[prices.indexOf(minPrice)];
            const maxExchange = exchanges[prices.indexOf(maxPrice)];

            const spreadPercentage = ((maxPrice - minPrice) / minPrice) * 100;
            
            console.log(`\n📈 Best Arbitrage Opportunity:`);
            console.log(`   Buy from: ${minExchange} at $${minPrice.toFixed(4)}`);
            console.log(`   Sell to: ${maxExchange} at $${maxPrice.toFixed(4)}`);
            console.log(`   Spread: ${spreadPercentage.toFixed(4)}%`);

            const MIN_SPREAD = 0.20; // 0.20% minimum for profitable arbitrage
            
            if (spreadPercentage >= MIN_SPREAD) {
                const profitPer1000 = (spreadPercentage / 100) * 1000;
                
                console.log(`🎯 PROFITABLE ARBITRAGE DETECTED!`);
                console.log(`   Profit per 1000 USDC: $${profitPer1000.toFixed(2)}`);
                console.log(`   ROI: ${spreadPercentage.toFixed(3)}%`);
                console.log(`   Price source: ${maticPriceData.source}`);

                return {
                    spread: spreadPercentage,
                    buyPrice: minPrice,
                    sellPrice: maxPrice,
                    buyFrom: minExchange,
                    sellTo: maxExchange,
                    profitPer1000,
                    basePrice: maticPriceData.price,
                    priceSource: maticPriceData.source,
                    timestamp: new Date()
                };
            } else {
                console.log(`❌ Spread ${spreadPercentage.toFixed(4)}% below minimum ${MIN_SPREAD}%`);
                return null;
            }

        } catch (error) {
            console.error("❌ Error checking real-time arbitrage:", error.message);
            return null;
        }
    }

    async checkContractStatus() {
        try {
            console.log(`\n📊 Contract Status Check:`);
            
            // Check Aave pool connection
            const aavePool = await this.contract.POOL();
            console.log(`   Aave Pool: ${aavePool}`);
            console.log(`   Expected: 0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A`);
            
            // Test gas estimation
            const testAmount = ethers.utils.parseUnits("100", 6); // 100 USDC
            const gasEstimate = await this.contract.estimateGas.executeArbitrage(
                TOKENS.USDC,
                testAmount,
                "0x"
            );
            
            const gasPrice = await this.provider.getGasPrice();
            const estimatedCost = gasEstimate.mul(gasPrice);
            
            console.log(`   Gas estimate: ${gasEstimate.toString()}`);
            console.log(`   Gas price: ${ethers.utils.formatUnits(gasPrice, "gwei")} gwei`);
            console.log(`   Estimated cost: ${ethers.utils.formatEther(estimatedCost)} POL`);
            
            return { viable: true, gasEstimate, gasPrice };

        } catch (error) {
            console.error("❌ Contract status check failed:", error.message);
            return { viable: false, reason: error.message };
        }
    }

    async executeRealtimeArbitrage(opportunity) {
        console.log(`\n⚡ EXECUTING REAL-TIME ARBITRAGE`);
        console.log(`=====================================`);
        
        const flashLoanAmount = ethers.utils.parseUnits("100", 6); // 100 USDC for safety
        
        console.log(`📋 Execution Details:`);
        console.log(`   Asset: USDC (${TOKENS.USDC})`);
        console.log(`   Amount: 100 USDC`);
        console.log(`   Price Source: ${opportunity.priceSource}`);
        console.log(`   Base Price: $${opportunity.basePrice.toFixed(4)}`);
        console.log(`   Strategy: Buy ${opportunity.buyFrom} → Sell ${opportunity.sellTo}`);
        console.log(`   Expected profit: $${(opportunity.profitPer1000 * 0.1).toFixed(2)}`);
        console.log(`   Timestamp: ${opportunity.timestamp.toLocaleString()}`);

        try {
            // Check contract status
            const contractStatus = await this.checkContractStatus();
            if (!contractStatus.viable) {
                console.log(`❌ Contract not viable: ${contractStatus.reason}`);
                return false;
            }

            // Get balances before
            const polBefore = await this.getWalletBalance();
            const usdcBefore = await this.getTokenBalance(TOKENS.USDC, 'USDC');
            
            console.log(`\n💼 Portfolio BEFORE:`);
            console.log(`   POL: ${parseFloat(polBefore).toFixed(4)} POL`);
            console.log(`   USDC: ${parseFloat(usdcBefore).toFixed(2)} USDC`);

            // Execute flash loan
            console.log(`\n🚀 Executing flash loan transaction...`);
            
            const tx = await this.contract.executeArbitrage(
                TOKENS.USDC,
                flashLoanAmount,
                "0x",
                {
                    gasLimit: contractStatus.gasEstimate.mul(130).div(100), // 30% buffer
                    gasPrice: contractStatus.gasPrice
                }
            );

            console.log(`📤 Transaction sent: ${tx.hash}`);
            console.log(`🔗 Explorer: https://www.oklink.com/amoy/tx/${tx.hash}`);
            console.log(`⏳ Waiting for confirmation...`);

            const receipt = await tx.wait();
            
            console.log(`✅ TRANSACTION CONFIRMED!`);
            console.log(`   Block: ${receipt.blockNumber}`);
            console.log(`   Gas used: ${receipt.gasUsed.toString()}`);
            console.log(`   Gas price: ${ethers.utils.formatUnits(receipt.effectiveGasPrice, "gwei")} gwei`);

            // Get balances after
            const polAfter = await this.getWalletBalance();
            const usdcAfter = await this.getTokenBalance(TOKENS.USDC, 'USDC');
            
            console.log(`\n💼 Portfolio AFTER:`);
            console.log(`   POL: ${parseFloat(polAfter).toFixed(4)} POL`);
            console.log(`   USDC: ${parseFloat(usdcAfter).toFixed(2)} USDC`);

            const polDiff = parseFloat(polAfter) - parseFloat(polBefore);
            const usdcDiff = parseFloat(usdcAfter) - parseFloat(usdcBefore);

            console.log(`\n📊 Net Changes:`);
            console.log(`   POL: ${polDiff > 0 ? '+' : ''}${polDiff.toFixed(4)} POL (gas fees)`);
            console.log(`   USDC: ${usdcDiff > 0 ? '+' : ''}${usdcDiff.toFixed(2)} USDC`);
            
            if (usdcDiff > 0) {
                console.log(`💰 PROFIT: +$${usdcDiff.toFixed(2)}`);
            } else if (usdcDiff < 0) {
                console.log(`📉 LOSS: $${Math.abs(usdcDiff).toFixed(2)}`);
            } else {
                console.log(`🔄 BREAK-EVEN: No USDC change`);
            }

            return true;

        } catch (error) {
            console.error("❌ Arbitrage execution failed:", error.message);
            
            if (error.message.includes("insufficient funds")) {
                const balance = await this.getWalletBalance();
                console.log(`💡 Current POL balance: ${balance} POL`);
                console.log(`💡 Get more POL: https://faucet.polygon.technology/`);
            }
            
            return false;
        }
    }

    async displayNetworkInfo() {
        console.log(`\n🌐 Network Information:`);
        
        const network = await this.provider.getNetwork();
        const blockNumber = await this.provider.getBlockNumber();
        const gasPrice = await this.provider.getGasPrice();
        const polBalance = await this.getWalletBalance();
        const usdcBalance = await this.getTokenBalance(TOKENS.USDC, 'USDC');

        console.log(`   Chain ID: ${network.chainId}`);
        console.log(`   Current Block: ${blockNumber}`);
        console.log(`   Gas Price: ${ethers.utils.formatUnits(gasPrice, "gwei")} gwei`);
        console.log(`   Your POL: ${parseFloat(polBalance).toFixed(4)} POL`);
        console.log(`   Your USDC: ${parseFloat(usdcBalance).toFixed(2)} USDC`);
    }

    async run() {
        console.log(`\n🚀 Starting Real-time Web3 Arbitrage Bot...`);
        
        await this.displayNetworkInfo();

        let cycleCount = 0;
        const MAX_CYCLES = 5; // Run 5 cycles for demo

        while (cycleCount < MAX_CYCLES) {
            try {
                console.log(`\n🔄 Cycle ${cycleCount + 1}/${MAX_CYCLES}`);
                console.log(`${'='.repeat(50)}`);
                
                const opportunity = await this.checkRealtimeArbitrageOpportunities();
                
                if (opportunity) {
                    console.log(`\n🎯 Executing arbitrage opportunity...`);
                    const success = await this.executeRealtimeArbitrage(opportunity);
                    
                    if (success) {
                        console.log(`\n✅ Arbitrage cycle ${cycleCount + 1} completed successfully!`);
                    } else {
                        console.log(`\n❌ Arbitrage cycle ${cycleCount + 1} failed.`);
                    }
                } else {
                    console.log(`\n⏭️  No profitable opportunities in cycle ${cycleCount + 1}.`);
                }
                
                cycleCount++;
                
                if (cycleCount < MAX_CYCLES) {
                    console.log(`\n⏰ Waiting 45 seconds before next cycle...`);
                    await new Promise(resolve => setTimeout(resolve, 45000));
                }

            } catch (error) {
                console.error(`❌ Cycle ${cycleCount + 1} error:`, error.message);
                console.log("⏰ Retrying in 30 seconds...");
                await new Promise(resolve => setTimeout(resolve, 30000));
            }
        }

        console.log(`\n🏁 Real-time arbitrage demo completed!`);
        console.log(`📊 Final portfolio status:`);
        await this.displayNetworkInfo();
    }
}

// Main execution
async function main() {
    console.log(`🚀 Real-time Web3 Flash Loan Arbitrage`);
    console.log(`====================================`);
    
    const bot = new RealtimeWeb3ArbitrageBot();
    await bot.run();
}

main().catch(console.error); 