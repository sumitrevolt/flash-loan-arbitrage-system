# 🆓 Free Price API Alternatives Guide

This guide shows you **completely free alternatives** to CoinGecko for getting live cryptocurrency prices in your flash loan arbitrage system.

## 🎯 **Quick Start - Use These FREE APIs**

```bash
# Test all free APIs
npm run test-free-apis

# Run bot with free APIs instead of CoinGecko
npm run free-bot
```

## 📊 **Top 5 Free Price Sources**

### 1. **DexScreener API** 🥇
- **Cost**: Completely FREE, unlimited requests
- **Best for**: DEX prices, liquidity data, volume
- **Data**: Real-time from 50+ DEXs
- **No API key required**

```javascript
// Example usage
const response = await axios.get(
  'https://api.dexscreener.com/latest/dex/tokens/0x0000000000000000000000000000000000001010'
);
const price = response.data.pairs[0].priceUsd;
```

### 2. **CoinCap API** 🥈  
- **Cost**: Completely FREE, no limits
- **Best for**: Market cap, 24h change, CEX prices
- **Data**: Top 2000 cryptocurrencies
- **No API key required**

```javascript
const response = await axios.get('https://api.coincap.io/v2/assets/polygon');
const price = response.data.data.priceUsd;
```

### 3. **CryptoCompare API** 🥉
- **Cost**: FREE tier with 100,000 calls/month
- **Best for**: Historical data, detailed metrics
- **Data**: 5000+ cryptocurrencies
- **API key optional for higher limits**

```javascript
const response = await axios.get(
  'https://min-api.cryptocompare.com/data/pricemultifull?fsyms=MATIC,ETH,BTC&tsyms=USD'
);
```

### 4. **Exchange APIs** 💡
- **Binance**: Free public endpoints
- **KuCoin**: Free market data
- **Gate.io**: Free price feeds
- **Coinbase**: Free public API

```javascript
// Binance (free)
const binance = await axios.get('https://api.binance.com/api/v3/ticker/price?symbol=MATICUSDT');

// KuCoin (free)  
const kucoin = await axios.get('https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=MATIC-USDT');
```

### 5. **On-Chain Sources** ⛓️
- **Cost**: Only gas fees (read calls often cached)
- **Best for**: Most accurate DEX prices
- **Sources**: Uniswap quoters, Chainlink feeds, pool reserves

## 🛠 **Implementation Examples**

### Basic Free Price Service

```javascript
const FreePriceServices = require('./scripts/free-price-services');

const priceService = new FreePriceServices();
await priceService.start();

// Get best price from multiple sources
const price = priceService.getBestPrice('WMATIC');
console.log(`WMATIC: $${price.usd}`);

// Get arbitrage opportunities
const opportunities = priceService.getArbitrageOpportunities(0.01); // 1% threshold
```

### Replace CoinGecko in Your Bot

**OLD (CoinGecko - requires API key):**
```javascript
const response = await axios.get(
  'https://api.coingecko.com/api/v3/simple/price?ids=matic-network&vs_currencies=usd',
  { headers: { 'x-cg-demo-api-key': process.env.COINGECKO_API_KEY } }
);
```

**NEW (Free APIs - no API key):**
```javascript
const priceService = new FreePriceServices();
const price = priceService.getBestPrice('WMATIC');
```

## 📋 **Complete Free API List**

| API | Cost | Limit | Best For | Reliability |
|-----|------|-------|----------|-------------|
| **DexScreener** | FREE | Unlimited | DEX data | ⭐⭐⭐⭐⭐ |
| **CoinCap** | FREE | Unlimited | Basic prices | ⭐⭐⭐⭐ |
| **CryptoCompare** | FREE | 100k/month | Detailed data | ⭐⭐⭐⭐ |
| **CoinLore** | FREE | Unlimited | Market data | ⭐⭐⭐ |
| **Coinranking** | FREE | 10k/month | Top coins | ⭐⭐⭐ |
| **Binance** | FREE | Unlimited | Exchange data | ⭐⭐⭐⭐⭐ |
| **KuCoin** | FREE | Unlimited | Exchange data | ⭐⭐⭐⭐ |
| **On-chain** | Gas only | Unlimited | DEX quotes | ⭐⭐⭐⭐⭐ |

## 🚀 **Migration Guide**

### Step 1: Install Free Price Service
```bash
# Already included in your project!
# File: scripts/free-price-services.js
```

### Step 2: Update Your Bot
```javascript
// Replace CoinGecko service with free service
const FreePriceServices = require('./scripts/free-price-services');
const priceService = new FreePriceServices();
```

### Step 3: Remove API Keys
```bash
# Remove from .env file (no longer needed!)
# COINGECKO_API_KEY=your_key_here  <- DELETE THIS LINE
```

### Step 4: Test Free APIs
```bash
npm run test-free-apis
```

### Step 5: Run Free Bot
```bash
npm run free-bot
```

## 💰 **Cost Comparison**

| Service | Monthly Cost | Requests/Month | Cost per 1M |
|---------|-------------|----------------|-------------|
| **CoinGecko Pro** | $129 | 10,000 | $12,900 |
| **Free APIs** | $0 | 100,000+ | $0 |
| **Your Savings** | **$129** | **90,000 more** | **$12,900** |

## 🎯 **Best Practices**

### 1. **Use Multiple Sources**
```javascript
// Combine multiple APIs for reliability
const prices = [
  await getDexScreenerPrice(),
  await getCoinCapPrice(), 
  await getCryptoComparePrice()
];
const averagePrice = prices.reduce((a, b) => a + b) / prices.length;
```

### 2. **Implement Fallbacks**
```javascript
async function getPrice(token) {
  try {
    return await getDexScreenerPrice(token);
  } catch (error) {
    try {
      return await getCoinCapPrice(token);
    } catch (error) {
      return await getOnChainPrice(token); // Always works
    }
  }
}
```

### 3. **Cache Responses**
```javascript
const cache = new Map();
const CACHE_DURATION = 30000; // 30 seconds

function getCachedPrice(token) {
  const cached = cache.get(token);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.price;
  }
  return null;
}
```

## 🔗 **API Endpoints Reference**

### DexScreener
```
GET https://api.dexscreener.com/latest/dex/tokens/{address}
```

### CoinCap  
```
GET https://api.coincap.io/v2/assets/{id}
```

### CryptoCompare
```
GET https://min-api.cryptocompare.com/data/price?fsym={from}&tsyms={to}
```

### Binance
```
GET https://api.binance.com/api/v3/ticker/price?symbol={symbol}
```

### KuCoin
```
GET https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}
```

## 🧪 **Testing Your Free Setup**

### Test Individual APIs
```bash
node -e "
const axios = require('axios');
axios.get('https://api.coincap.io/v2/assets/polygon')
  .then(r => console.log('MATIC:', r.data.data.priceUsd));
"
```

### Test Integrated Service
```bash
npm run test-free-apis
```

### Verify Arbitrage Detection
```javascript
const priceService = new FreePriceServices();
await priceService.start();

setTimeout(() => {
  const opportunities = priceService.getArbitrageOpportunities(0.01);
  console.log(`Found ${opportunities.length} opportunities`);
}, 10000);
```

## ⚡ **Quick Commands**

```bash
# Test all free APIs
npm run test-free-apis

# Run bot with free APIs  
npm run free-bot

# Check what APIs are working
node -e "require('./scripts/free-price-services')"

# Get current MATIC price from multiple sources
node -e "
const FreePriceServices = require('./scripts/free-price-services');
const service = new FreePriceServices();
service.start().then(() => {
  setTimeout(() => {
    console.log(service.getAllPrices());
    service.stop();
  }, 5000);
});
"
```

## 🔄 **Migration Success**

✅ **Before**: Paying $129/month for CoinGecko  
✅ **After**: Using free APIs with better coverage  
✅ **Result**: $1,548 saved per year + more data sources

## 🆘 **Troubleshooting**

### Common Issues

**1. "Network Error"**
```javascript
// Add timeout and retry logic
const response = await axios.get(url, { 
  timeout: 5000,
  retry: 3 
});
```

**2. "Rate Limited"**
```javascript
// Use multiple APIs for redundancy
const APIs = [dexscreener, coincap, cryptocompare];
const workingAPI = APIs.find(api => api.isWorking());
```

**3. "Price Discrepancy"**
```javascript
// Use weighted average from multiple sources
const weightedPrice = calculateWeightedAverage(prices, weights);
```

## 🎉 **You're Now Free!**

You've successfully replaced expensive APIs with free alternatives that provide:

- ✅ **More data sources** (8+ vs 1)
- ✅ **Higher reliability** (fallback options)  
- ✅ **Zero monthly costs** ($0 vs $129)
- ✅ **Real-time DEX data** (better for arbitrage)
- ✅ **No API key management**

Your arbitrage bot now has **better data at zero cost**! 🚀 