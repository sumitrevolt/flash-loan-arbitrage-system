const FreePriceServices = require('./free-price-services');
const axios = require('axios');

async function testAllFreeAPIs() {
  console.log("🧪 Testing All Free Price API Sources");
  console.log("=====================================\n");

  // Test 1: DexScreener (Best for DEX data)
  console.log("1️⃣ DexScreener API (FREE - Unlimited)");
  try {
    const response = await axios.get(
      'https://api.dexscreener.com/latest/dex/tokens/0x0000000000000000000000000000000000001010',
      { timeout: 5000 }
    );
    
    if (response.data?.pairs?.length > 0) {
      const pair = response.data.pairs[0];
      console.log(`✅ MATIC: $${parseFloat(pair.priceUsd).toFixed(6)} (${pair.dexId})`);
      console.log(`   Volume 24h: $${(parseFloat(pair.volume.h24) / 1000000).toFixed(2)}M`);
      console.log(`   Liquidity: $${(parseFloat(pair.liquidity.usd) / 1000000).toFixed(2)}M`);
    }
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
  console.log();

  // Test 2: CoinCap API (Completely free)
  console.log("2️⃣ CoinCap API (FREE - No limits)");
  try {
    const response = await axios.get('https://api.coincap.io/v2/assets/polygon', { timeout: 5000 });
    
    if (response.data?.data) {
      const data = response.data.data;
      console.log(`✅ MATIC: $${parseFloat(data.priceUsd).toFixed(6)}`);
      console.log(`   24h Change: ${parseFloat(data.changePercent24Hr).toFixed(2)}%`);
      console.log(`   Market Cap: $${(parseFloat(data.marketCapUsd) / 1000000000).toFixed(2)}B`);
    }
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
  console.log();

  // Test 3: CryptoCompare (100k calls/month free)
  console.log("3️⃣ CryptoCompare API (FREE - 100k calls/month)");
  try {
    const symbols = ['MATIC', 'ETH', 'BTC', 'USDC'];
    const response = await axios.get(
      `https://min-api.cryptocompare.com/data/pricemultifull?fsyms=${symbols.join(',')}&tsyms=USD`,
      { timeout: 5000 }
    );
    
    if (response.data?.RAW) {
      for (const [symbol, data] of Object.entries(response.data.RAW)) {
        if (data.USD) {
          console.log(`✅ ${symbol}: $${data.USD.PRICE.toFixed(6)} (${data.USD.CHANGEPCT24HOUR.toFixed(2)}%)`);
        }
      }
    }
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
  console.log();

  // Test 4: CoinLore (Completely free)
  console.log("4️⃣ CoinLore API (FREE - No limits)");
  try {
    const response = await axios.get('https://api.coinlore.net/api/ticker/?id=3890', { timeout: 5000 });
    
    if (response.data?.length > 0) {
      const data = response.data[0];
      console.log(`✅ MATIC: $${parseFloat(data.price_usd).toFixed(6)}`);
      console.log(`   24h Change: ${parseFloat(data.percent_change_24h).toFixed(2)}%`);
      console.log(`   Market Cap: $${(parseFloat(data.market_cap_usd) / 1000000000).toFixed(2)}B`);
    }
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
  console.log();

  // Test 5: Coinranking (10k requests/month free)
  console.log("5️⃣ Coinranking API (FREE - 10k requests/month)");
  try {
    const response = await axios.get(
      'https://api.coinranking.com/v2/coins?symbols[]=MATIC&limit=1',
      { timeout: 5000 }
    );
    
    if (response.data?.data?.coins?.length > 0) {
      const coin = response.data.data.coins[0];
      console.log(`✅ MATIC: $${parseFloat(coin.price).toFixed(6)}`);
      console.log(`   24h Change: ${parseFloat(coin.change).toFixed(2)}%`);
      console.log(`   Market Cap: $${(parseFloat(coin.marketCap) / 1000000000).toFixed(2)}B`);
    }
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
  console.log();

  // Test 6: Alternative APIs
  console.log("6️⃣ Additional Free APIs");
  
  // Binance public API (free)
  try {
    const response = await axios.get('https://api.binance.com/api/v3/ticker/price?symbol=MATICUSDT', { timeout: 5000 });
    if (response.data?.price) {
      console.log(`✅ Binance MATIC: $${parseFloat(response.data.price).toFixed(6)}`);
    }
  } catch (error) {
    console.log(`⚠️ Binance API: ${error.message}`);
  }

  // KuCoin public API (free)
  try {
    const response = await axios.get('https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=MATIC-USDT', { timeout: 5000 });
    if (response.data?.data?.price) {
      console.log(`✅ KuCoin MATIC: $${parseFloat(response.data.data.price).toFixed(6)}`);
    }
  } catch (error) {
    console.log(`⚠️ KuCoin API: ${error.message}`);
  }

  console.log("\n🔗 On-Chain Price Sources (Always Free):");
  console.log("- Uniswap V3 Quoter contracts");
  console.log("- Chainlink Price Feeds");
  console.log("- DEX pool reserves");
  console.log("- AMM price calculations");

  console.log("\n📝 Summary of Free Options:");
  console.log("=============================");
  console.log("🥇 BEST: DexScreener - Unlimited, real-time DEX data");
  console.log("🥈 GOOD: CoinCap - No limits, reliable CEX data");
  console.log("🥉 SOLID: CryptoCompare - 100k calls/month, detailed data");
  console.log("💡 BACKUP: CoinLore, Coinranking, Binance, KuCoin");
  console.log("⛓️ ON-CHAIN: Always free, most accurate for your DEX");
}

async function testFreePriceService() {
  console.log("\n🚀 Testing Integrated Free Price Service");
  console.log("=========================================\n");

  const priceService = new FreePriceServices();
  
  try {
    await priceService.start();
    
    // Wait for prices to update
    setTimeout(() => {
      priceService.printPriceSummary();
      
      // Test best price function
      const bestPrice = priceService.getBestPrice('WMATIC');
      if (bestPrice) {
        console.log(`🎯 Best WMATIC Price: $${bestPrice.usd.toFixed(6)} (${bestPrice.source})`);
        console.log(`   Based on ${bestPrice.sources || 1} source(s)\n`);
      }
      
      priceService.stop();
    }, 10000); // Wait 10 seconds
    
  } catch (error) {
    console.error("❌ Service error:", error.message);
    priceService.stop();
  }
}

// Run tests
if (require.main === module) {
  (async () => {
    await testAllFreeAPIs();
    await testFreePriceService();
  })();
} 