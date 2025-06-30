const { ethers } = require("ethers");
const axios = require("axios");
const config = require("../config/amoy-config");

class RealTimePriceService {
  constructor() {
    this.provider = new ethers.JsonRpcProvider(config.NETWORK.RPC_URL);
    this.priceCache = new Map();
    this.lastUpdate = new Map();
    this.updateInterval = 30000; // 30 seconds
    this.isRunning = false;
  }

  async start() {
    console.log("🚀 Starting Real-time Price Service...");
    this.isRunning = true;
    await this.updateAllPrices();
    this.startPeriodicUpdates();
  }

  stop() {
    console.log("🛑 Stopping Real-time Price Service...");
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
      console.log("📊 Updating all token prices...");
      
      // Get prices from CoinGecko
      const coinGeckoPrices = await this.getCoinGeckoPrices();
      
      // Get prices from DEX pools
      const dexPrices = await this.getDexPrices();
      
      // Merge and cache prices
      this.mergePrices(coinGeckoPrices, dexPrices);
      
      console.log(`✅ Updated prices for ${this.priceCache.size} tokens`);
      
    } catch (error) {
      console.error("❌ Error updating prices:", error.message);
    }
  }

  async getCoinGeckoPrices() {
    try {
      const tokenIds = Object.values(config.TOKENS)
        .map(token => token.coingeckoId)
        .join(',');
      
      const response = await axios.get(
        `${config.APIS.COINGECKO.BASE_URL}/simple/price`,
        {
          params: {
            ids: tokenIds,
            vs_currencies: 'usd',
            include_24hr_change: true,
            include_last_updated_at: true
          },
          timeout: 10000
        }
      );

      const prices = {};
      for (const [symbol, tokenData] of Object.entries(config.TOKENS)) {
        const coinGeckoData = response.data[tokenData.coingeckoId];
        if (coinGeckoData) {
          prices[symbol] = {
            usd: coinGeckoData.usd,
            change24h: coinGeckoData.usd_24h_change || 0,
            lastUpdated: coinGeckoData.last_updated_at || Date.now() / 1000,
            source: 'coingecko'
          };
        }
      }

      return prices;
    } catch (error) {
      console.error("❌ CoinGecko API error:", error.message);
      return {};
    }
  }

  async getDexPrices() {
    const dexPrices = {};
    
    try {
      // Get Uniswap V3 prices
      const uniswapPrices = await this.getUniswapV3Prices();
      Object.assign(dexPrices, uniswapPrices);
      
      // Get QuickSwap prices
      const quickswapPrices = await this.getQuickSwapPrices();
      Object.assign(dexPrices, quickswapPrices);
      
    } catch (error) {
      console.error("❌ DEX price error:", error.message);
    }
    
    return dexPrices;
  }

  async getUniswapV3Prices() {
    try {
      const quoterContract = new ethers.Contract(
        config.DEXS.UNISWAP_V3.QUOTER,
        [
          "function quoteExactInputSingle(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn, uint160 sqrtPriceLimitX96) external returns (uint256 amountOut)"
        ],
        this.provider
      );

      const prices = {};
      const baseAmount = ethers.parseUnits("1", 18); // 1 token

      // Get WMATIC/USDC price as base
      try {
        const usdcOut = await quoterContract.quoteExactInputSingle(
          config.TOKENS.WMATIC.address,
          config.TOKENS.USDC.address,
          3000, // 0.3% fee
          baseAmount,
          0
        );

        const maticPrice = Number(ethers.formatUnits(usdcOut, 6));
        prices.WMATIC_UNISWAP = {
          usd: maticPrice,
          source: 'uniswap_v3',
          fee: 3000,
          lastUpdated: Date.now() / 1000
        };

      } catch (error) {
        console.log("⚠️ WMATIC/USDC Uniswap quote failed:", error.message);
      }

      return prices;
    } catch (error) {
      console.error("❌ Uniswap V3 price error:", error.message);
      return {};
    }
  }

  async getQuickSwapPrices() {
    try {
      const routerContract = new ethers.Contract(
        config.DEXS.QUICKSWAP.ROUTER,
        [
          "function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts)"
        ],
        this.provider
      );

      const prices = {};
      const baseAmount = ethers.parseUnits("1", 18);

      // Get WMATIC/USDC price on QuickSwap
      try {
        const path = [config.TOKENS.WMATIC.address, config.TOKENS.USDC.address];
        const amounts = await routerContract.getAmountsOut(baseAmount, path);
        
        const maticPrice = Number(ethers.formatUnits(amounts[1], 6));
        prices.WMATIC_QUICKSWAP = {
          usd: maticPrice,
          source: 'quickswap',
          lastUpdated: Date.now() / 1000
        };

      } catch (error) {
        console.log("⚠️ WMATIC/USDC QuickSwap quote failed:", error.message);
      }

      return prices;
    } catch (error) {
      console.error("❌ QuickSwap price error:", error.message);
      return {};
    }
  }

  mergePrices(coinGeckoPrices, dexPrices) {
    // Merge CoinGecko prices
    for (const [symbol, priceData] of Object.entries(coinGeckoPrices)) {
      this.priceCache.set(symbol, priceData);
      this.lastUpdate.set(symbol, Date.now());
    }

    // Merge DEX prices
    for (const [key, priceData] of Object.entries(dexPrices)) {
      this.priceCache.set(key, priceData);
      this.lastUpdate.set(key, Date.now());
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
    
    // Compare WMATIC prices across DEXes
    const uniswapPrice = this.getPrice('WMATIC_UNISWAP');
    const quickswapPrice = this.getPrice('WMATIC_QUICKSWAP');
    const coinGeckoPrice = this.getPrice('WMATIC');

    if (uniswapPrice && quickswapPrice) {
      const priceDiff = Math.abs(uniswapPrice.usd - quickswapPrice.usd);
      const profitPercentage = priceDiff / Math.min(uniswapPrice.usd, quickswapPrice.usd);

      if (profitPercentage >= minProfitThreshold) {
        opportunities.push({
          token: 'WMATIC',
          buyDex: uniswapPrice.usd < quickswapPrice.usd ? 'uniswap' : 'quickswap',
          sellDex: uniswapPrice.usd > quickswapPrice.usd ? 'uniswap' : 'quickswap',
          buyPrice: Math.min(uniswapPrice.usd, quickswapPrice.usd),
          sellPrice: Math.max(uniswapPrice.usd, quickswapPrice.usd),
          profitPercentage: profitPercentage * 100,
          timestamp: Date.now()
        });
      }
    }

    return opportunities;
  }

  async getRealtimeQuote(tokenIn, tokenOut, amountIn, dex = 'uniswap_v3') {
    try {
      if (dex === 'uniswap_v3') {
        const quoterContract = new ethers.Contract(
          config.DEXS.UNISWAP_V3.QUOTER,
          [
            "function quoteExactInputSingle(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn, uint160 sqrtPriceLimitX96) external returns (uint256 amountOut)"
          ],
          this.provider
        );

        const quote = await quoterContract.quoteExactInputSingle(
          tokenIn,
          tokenOut,
          3000, // 0.3% fee
          amountIn,
          0
        );

        return quote;
      } else if (dex === 'quickswap') {
        const routerContract = new ethers.Contract(
          config.DEXS.QUICKSWAP.ROUTER,
          [
            "function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts)"
          ],
          this.provider
        );

        const path = [tokenIn, tokenOut];
        const amounts = await routerContract.getAmountsOut(amountIn, path);
        return amounts[1];
      }

      return 0n;
    } catch (error) {
      console.error(`❌ Quote error for ${dex}:`, error.message);
      return 0n;
    }
  }

  printPriceSummary() {
    console.log("\n📊 Real-time Price Summary:");
    console.log("========================================");
    
    const allPrices = this.getAllPrices();
    for (const [symbol, priceData] of Object.entries(allPrices)) {
      if (priceData.usd) {
        const change = priceData.change24h ? `(${priceData.change24h.toFixed(2)}%)` : '';
        console.log(`💰 ${symbol}: $${priceData.usd.toFixed(6)} ${change} [${priceData.source}]`);
      }
    }
    
    const opportunities = this.getArbitrageOpportunities();
    if (opportunities.length > 0) {
      console.log("\n🎯 Arbitrage Opportunities:");
      opportunities.forEach(opp => {
        console.log(`⚡ ${opp.token}: Buy on ${opp.buyDex} ($${opp.buyPrice.toFixed(6)}) → Sell on ${opp.sellDex} ($${opp.sellPrice.toFixed(6)}) = ${opp.profitPercentage.toFixed(2)}% profit`);
      });
    } else {
      console.log("\n😴 No arbitrage opportunities found (threshold: 1%)");
    }
    
    console.log("========================================\n");
  }
}

module.exports = RealTimePriceService; 