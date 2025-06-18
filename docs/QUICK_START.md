# ⚡ QUICK START GUIDE

## 🚀 Deploy Your Flash Loan Contract in 5 Minutes

### Prerequisites
- Node.js installed
- At least 0.5 MATIC in your wallet
- PolygonScan API key

### Step 1: Configure Environment (2 minutes)
1. Update `.env` file:
   ```bash
   PRIVATE_KEY=your_actual_private_key_here
   WALLET_ADDRESS=your_wallet_address_here
   POLYGONSCAN_API_KEY=your_polygonscan_api_key_here
   ```

### Step 2: Deploy & Setup (3 minutes)
```bash
# Complete automated deployment
npm run full-deploy

# This runs:
# - npm run compile (compile contracts)
# - npm run deploy:ai (AI-powered deployment)
# - Reminder to verify and setup
```

### Step 3: Verify & Configure
```bash
# Verify contract on PolygonScan
npm run verify

# Setup tokens and DEXes with AI optimization
npm run setup:mcp

# Check contract health
npm run health-check
```

### 🎉 You're Ready!
Your flash loan arbitrage contract is now deployed and configured on Polygon mainnet.

### Next Steps
- Monitor with `npm run health-check`
- Start with small arbitrage amounts
- Scale up based on performance

### Need Help?
- Check `README.md` for detailed instructions
- Review `PRODUCTION_DEPLOYMENT_GUIDE.md` for advanced setup
- See `PROJECT_STATUS_FINAL.md` for complete feature overview

---
**⚠️ Important**: Always test with small amounts first and monitor performance closely.
