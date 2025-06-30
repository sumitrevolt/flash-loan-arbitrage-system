const { ethers } = require("ethers");
const axios = require("axios");
const config = require("../config/amoy-config");

class FreePriceServices {
  constructor() {
    this.provider = new ethers.JsonRpcProvider(config.NETWORK.RPC_URL);
    this.priceCache = new Map();
    this.lastUpdate = new Map();
    this.updateInterval = 30000; // 30 seconds
    this.isRunning = false;
  }

  async start() {
    console.log("🚀 Starting Free Price Services...");
    this.isRunning = true;
    await this.updateAllPrices();
    this.startPeriodicUpdates();
  }

  stop() {
    console.log("🛑 Stopping Free Price Services...");
    this.isRunning = false;
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
    }
  }

  startPeriodicUpdates() {
    this.updateTimer = setInterval(async () => {
      if (this.isRunning) {
        await this.updateAllPrices();
      }
    }, this.updateInterval);
  }

  async updateAllPrices() {
    try {
      console.log("📊 Updating prices from free sources...");
      
      // Get prices from multiple free sources
      const [
        dexScreenerPrices,
        coinApiPrices,
        cryptoComparePrices,
        defipulsePrices,
        onChainPrices
      ] = await Promise.allSettled([
        this.getDexScreenerPrices(),
        this.getCoinApiPrices(),
        this.getCryptoComparePrices(),
        this.getDefiPulsePrices(),
        this.getOnChainPrices()
      ]);

      // Merge all price sources
      this.mergePriceSources([
        dexScreenerPrices.value || {},
        coinApiPrices.value || {},
        cryptoComparePrices.value || {},
        defipulsePrices.value || {},
        onChainPrices.value || {}
      ]);
      
      console.log(`✅ Updated prices for ${this.priceCache.size} tokens from multiple sources`);
      
    } catch (error) {
      console.error("❌ Error updating prices:", error.message);
    }
  }

  // 1. DexScreener API (Best for DEX prices) - FREE
  async getDexScreenerPrices() {
    try {
      const prices = {};
      
      // Get WMATIC price from DexScreener
      const response = await axios.get(
        `https://api.dexscreener.com/latest/dex/tokens/${config.TOKENS.WMATIC.address}`,
        { timeout: 5000 }
      );

      if (response.data && response.data.pairs && response.data.pairs.length > 0) {
        const pair = response.data.pairs[0]; // Get most liquid pair
        prices.WMATIC = {
          usd: parseFloat(pair.priceUsd),
          change24h: parseFloat(pair.priceChange.h24) || 0,
          volume24h: parseFloat(pair.volume.h24) || 0,
          liquidity: parseFloat(pair.liquidity?.usd) || 0,
          dex: pair.dexId,
          source: 'dexscreener',
          lastUpdated: Date.now() / 1000
        };
      }

      return prices;
    } catch (error) {
      console.log("⚠️ DexScreener API error:", error.message);
      return {};
    }
  }

  // 2. CoinAPI.io (Free tier: 100 requests/day) - FREE
  async getCoinApiPrices() {
    try {
      const prices = {};
      
      // Free endpoint for current rates
      const response = await axios.get(
        'https://rest.coinapi.io/v1/exchangerate/MATIC/USD',
        {
          headers: {
            'X-CoinAPI-Key': 'FREE' // Use 'FREE' for demo, get actual key for production
          },
          timeout: 5000
        }
      );

      if (response.data && response.data.rate) {
        prices.WMATIC_COINAPI = {
          usd: response.data.rate,
          source: 'coinapi',
          lastUpdated: Date.now() / 1000
        };
      }

      return prices;
    } catch (error) {
      console.log("⚠️ CoinAPI error:", error.message);
      return {};
    }
  }

  // 3. CryptoCompare API (Free tier: 100k calls/month) - FREE
  async getCryptoComparePrices() {
    try {
      const tokenSymbols = ['MATIC', 'ETH', 'BTC', 'USDC', 'USDT', 'UNI', 'LINK', 'AAVE'];
      const symbolString = tokenSymbols.join(',');
      
      const response = await axios.get(
        `https://min-api.cryptocompare.com/data/pricemultifull?fsyms=${symbolString}&tsyms=USD`,
        { timeout: 5000 }
      );

      const prices = {};
      if (response.data && response.data.RAW) {
        for (const [symbol, data] of Object.entries(response.data.RAW)) {
          if (data.USD) {
            const mappedSymbol = symbol === 'MATIC' ? 'WMATIC' : 
                               symbol === 'ETH' ? 'WETH' : 
                               symbol === 'BTC' ? 'WBTC' : symbol;
            
            prices[`${mappedSymbol}_CRYPTOCOMPARE`] = {
              usd: data.USD.PRICE,
              change24h: data.USD.CHANGEPCT24HOUR || 0,
              volume24h: data.USD.VOLUME24HOURTO || 0,
              source: 'cryptocompare',
              lastUpdated: data.USD.LASTUPDATE || Date.now() / 1000
            };
          }
        }
      }

      return prices;
    } catch (error) {
      console.log("⚠️ CryptoCompare API error:", error.message);
      return {};
    }
  }

  // 4. DefiPulse API (Free tier available) - FREE
  async getDefiPulsePrices() {
    try {
      const prices = {};
      
      // DefiPulse free endpoint
      const response = await axios.get(
        'https://data-api.defipulse.com/api/v1/egs/api/ethgasAPI.json',
        { timeout: 5000 }
      );

      // This is primarily for gas prices, but shows the pattern
      // They also have token price endpoints
      
      return prices;
    } catch (error) {
      console.log("⚠️ DefiPulse API error:", error.message);
      return {};
    }
  }

  // 5. On-chain Price Oracles (Always free) - FREE
  async getOnChainPrices() {
    try {
      const prices = {};
      
      // Chainlink Price Feeds (if available on Amoy)
      const chainlinkPrices = await this.getChainlinkPrices();
      Object.assign(prices, chainlinkPrices);
      
      // DEX Pool Prices (direct from contracts)
      const dexPrices = await this.getDirectDexPrices();
      Object.assign(prices, dexPrices);
      
      return prices;
    } catch (error) {
      console.log("⚠️ On-chain price error:", error.message);
      return {};
    }
  }

  async getChainlinkPrices() {
    // Chainlink MATIC/USD price feed on Polygon (example)
    try {
      const prices = {};
      
      // This would need actual Chainlink aggregator addresses on Amoy
      // For now, we'll simulate the structure
      
      return prices;
    } catch (error) {
      return {};
    }
  }

  async getDirectDexPrices() {
    try {
      const prices = {};
      
      // Get prices directly from Uniswap V3 pools
      const uniswapPrices = await this.getUniswapV3DirectPrices();
      Object.assign(prices, uniswapPrices);
      
      return prices;
    } catch (error) {
      return {};
    }
  }

  async getUniswapV3DirectPrices() {
    try {
      const prices = {};
      
      // Simple quoter call (read-only, always free)
      const quoterContract = new ethers.Contract(
        config.DEXS.UNISWAP_V3.QUOTER,
        [
          "function quoteExactInputSingle(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn, uint160 sqrtPriceLimitX96) external returns (uint256 amountOut)"
        ],
        this.provider
      );

      try {
        // Get WMATIC/USDC price
        const amountIn = ethers.parseUnits("1", 18); // 1 WMATIC
        const amountOut = await quoterContract.quoteExactInputSingle.staticCall(
          config.TOKENS.WMATIC.address,
          config.TOKENS.USDC.address,
          3000, // 0.3% fee
          amountIn,
          0
        );

        const price = Number(ethers.formatUnits(amountOut, 6)); // USDC has 6 decimals
        prices.WMATIC_UNISWAP_DIRECT = {
          usd: price,
          source: 'uniswap_v3_direct',
          fee: 3000,
          lastUpdated: Date.now() / 1000
        };

      } catch (error) {
        console.log("⚠️ Direct Uniswap quote failed:", error.message);
      }

      return prices;
    } catch (error) {
      return {};
    }
  }

  // 6. Alternative Free APIs
  async getAlternativeFreeAPIs() {
    const alternatives = [
      {
        name: "CoinLore",
        url: "https://api.coinlore.net/api/ticker/?id=3890", // MATIC ID
        free: true,
        limit: "No limit"
      },
      {
        name: "Coinranking",
        url: "https://api.coinranking.com/v2/coins", 
        free: true,
        limit: "10k requests/month"
      },
      {
        name: "Nomics",
        url: "https://api.nomics.com/v1/currencies/ticker",
        free: true,
        limit: "1 request/second"
      },
      {
        name: "CoinCap",
        url: "https://api.coincap.io/v2/assets/polygon",
        free: true,
        limit: "No limit"
      }
    ];

    // Implement one example - CoinCap (completely free)
    try {
      const response = await axios.get(
        'https://api.coincap.io/v2/assets/polygon',
        { timeout: 5000 }
      );

      if (response.data && response.data.data) {
        return {
          WMATIC_COINCAP: {
            usd: parseFloat(response.data.data.priceUsd),
            change24h: parseFloat(response.data.data.changePercent24Hr) || 0,
            source: 'coincap',
            lastUpdated: Date.now() / 1000
          }
        };
      }
    } catch (error) {
      console.log("⚠️ CoinCap API error:", error.message);
    }

    return {};
  }

  mergePriceSources(priceSources) {
    // Clear old cache
    this.priceCache.clear();
    
    // Merge all price sources with preference order
    for (const source of priceSources) {
      for (const [symbol, priceData] of Object.entries(source)) {
        if (priceData && priceData.usd) {
          this.priceCache.set(symbol, priceData);
          this.lastUpdate.set(symbol, Date.now());
        }
      }
    }
  }

  getPrice(symbol) {
    return this.priceCache.get(symbol);
  }

  getAllPrices() {
    const prices = {};
    for (const [symbol, priceData] of this.priceCache.entries()) {
      prices[symbol] = priceData;
    }
    return prices;
  }

  getArbitrageOpportunities(minProfitThreshold = 0.01) {
    const opportunities = [];
    
    // Compare WMATIC prices across different sources
    const prices = [];
    
    // Collect all WMATIC price variants
    for (const [key, priceData] of this.priceCache.entries()) {
      if (key.includes('WMATIC') && priceData.usd) {
        prices.push({
          key,
          price: priceData.usd,
          source: priceData.source
        });
      }
    }

    // Find arbitrage opportunities between sources
    for (let i = 0; i < prices.length; i++) {
      for (let j = i + 1; j < prices.length; j++) {
        const price1 = prices[i];
        const price2 = prices[j];
        
        const priceDiff = Math.abs(price1.price - price2.price);
        const profitPercentage = priceDiff / Math.min(price1.price, price2.price);

        if (profitPercentage >= minProfitThreshold) {
          opportunities.push({
            token: 'WMATIC',
            buySource: price1.price < price2.price ? price1.source : price2.source,
            sellSource: price1.price > price2.price ? price1.source : price2.source,
            buyPrice: Math.min(price1.price, price2.price),
            sellPrice: Math.max(price1.price, price2.price),
            profitPercentage: profitPercentage * 100,
            timestamp: Date.now()
          });
        }
      }
    }

    return opportunities;
  }

  printPriceSummary() {
    console.log("\n📊 Free Price Sources Summary:");
    console.log("========================================");
    
    const allPrices = this.getAllPrices();
    for (const [symbol, priceData] of Object.entries(allPrices)) {
      if (priceData.usd) {
        const change = priceData.change24h ? `(${priceData.change24h.toFixed(2)}%)` : '';
        const volume = priceData.volume24h ? `Vol: $${(priceData.volume24h / 1000000).toFixed(2)}M` : '';
        console.log(`💰 ${symbol}: $${priceData.usd.toFixed(6)} ${change} [${priceData.source}] ${volume}`);
      }
    }
    
    const opportunities = this.getArbitrageOpportunities();
    if (opportunities.length > 0) {
      console.log("\n🎯 Cross-Source Arbitrage Opportunities:");
      opportunities.forEach(opp => {
        console.log(`⚡ ${opp.token}: ${opp.buySource} ($${opp.buyPrice.toFixed(6)}) → ${opp.sellSource} ($${opp.sellPrice.toFixed(6)}) = ${opp.profitPercentage.toFixed(2)}% profit`);
      });
    } else {
      console.log("\n😴 No cross-source arbitrage opportunities found");
    }
    
    console.log("========================================\n");
  }

  // Get best price from all sources
  getBestPrice(token) {
    const prices = [];
    
    for (const [key, priceData] of this.priceCache.entries()) {
      if (key.includes(token) && priceData.usd) {
        prices.push(priceData);
      }
    }

    if (prices.length === 0) return null;

    // Return average price weighted by source reliability
    const weights = {
      'dexscreener': 0.3,
      'cryptocompare': 0.25,
      'uniswap_v3_direct': 0.2,
      'coincap': 0.15,
      'coinapi': 0.1
    };

    let totalWeight = 0;
    let weightedSum = 0;

    for (const price of prices) {
      const weight = weights[price.source] || 0.05;
      weightedSum += price.usd * weight;
      totalWeight += weight;
    }

    return totalWeight > 0 ? {
      usd: weightedSum / totalWeight,
      source: 'weighted_average',
      sources: prices.length,
      lastUpdated: Date.now() / 1000
    } : prices[0];
  }
}

module.exports = FreePriceServices; 