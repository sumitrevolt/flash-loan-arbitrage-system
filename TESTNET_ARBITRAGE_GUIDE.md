# Amoy Testnet Flash Loan Arbitrage Guide

## 🎯 Overview

This guide shows you how to test flash loan arbitrage on Polygon's Amoy testnet using the deployed contract at:
**Contract Address**: `0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5`

## 📋 Prerequisites

### 1. Get Testnet Tokens

You'll need testnet tokens to interact with the system:

#### POL (for gas fees)
- **Polygon Faucet**: https://faucet.polygon.technology/
- **Chainstack Faucet**: https://chainstack.com/amoy-faucet/
- **Amount needed**: At least 1 POL for gas fees

#### USDC (for arbitrage testing)
- **Circle Faucet**: https://faucet.circle.com/
- **Address**: `0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582`
- **Amount needed**: Any amount (for testing)

### 2. Network Configuration

Make sure your `.env` file has the Amoy testnet RPC:

```bash
AMOY_RPC_URL=https://rpc-amoy.polygon.technology/
PRIVATE_KEY=your_private_key_here
```

## 🚀 Available Scripts

### 1. Testnet Arbitrage Simulator

**File**: `scripts/testnet-arbitrage.js`

This script simulates arbitrage opportunities without spending real money:

```bash
node scripts/testnet-arbitrage.js
```

**Features**:
- Mock price feeds with realistic variations
- Simulates DEX price spreads
- Shows potential profits
- Monitors contract status
- No actual transactions (safe for testing)

### 2. Real Testnet Flash Loan Executor

**File**: `scripts/testnet-real-arbitrage.js`

This script executes actual flash loan transactions:

```bash
node scripts/testnet-real-arbitrage.js
```

**Features**:
- Executes real flash loans on Aave
- Shows before/after balances
- Tracks transaction receipts
- Requires POL for gas fees

### 3. Legacy Scripts (May have issues)

- `scripts/execute-arb.js` - Uses mainnet addresses, may fail
- `scripts/arb-loop.js` - Continuous monitoring, mainnet addresses

## 🔧 Correct Token Addresses for Amoy

| Token | Address | Source |
|-------|---------|--------|
| USDC (Testnet) | `0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582` | Circle Official |
| Native POL | Native token (for gas) | Polygon |
| WMATIC | `0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889` | Wrapped MATIC |

## 📊 Contract Information

- **Contract**: `0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5`
- **Network**: Amoy Testnet (Chain ID: 80002)
- **Aave Pool**: `0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A`

## 🎮 How to Use

### Step 1: Get Testnet Tokens

Visit the faucets and get:
1. POL for gas fees
2. USDC for arbitrage testing

### Step 2: Run the Simulator

```bash
node scripts/testnet-arbitrage.js
```

This will:
- Show your balances
- Simulate arbitrage opportunities
- Display potential profits
- Run continuously until stopped

### Step 3: Execute Real Flash Loans

```bash
node scripts/testnet-real-arbitrage.js
```

This will:
- Check prerequisites
- Execute a test flash loan
- Show transaction details
- Display before/after balances

## 📈 Expected Output

### Simulator Output
```
🤖 Testnet Arbitrage Bot initialized
📍 Wallet: 0x...
🌐 Network: Amoy Testnet (Chain ID: 80002)

💼 Portfolio Status:
   POL: 2.5000 POL
   USDC: 0.00 USDC
   WETH: 0.000000 WETH

🔍 Checking arbitrage opportunities...
📊 Mock Uniswap WETH/USDC: $2801.45
📊 Mock Sushiswap WETH/USDC: $2798.32
📈 Price spread: 0.1118%

🎯 ARBITRAGE OPPORTUNITY DETECTED!
   Buy from: Sushiswap ($2798.32)
   Sell to: Uniswap ($2801.45)
   Profit per 1000 USDC: $1.12
```

### Real Flash Loan Output
```
🚀 Testnet Flash Loan Arbitrage Demo
==================================

🔍 Prerequisites Check:
   POL balance: 2.5000 POL ✅
   USDC balance: 0.00 USDC ✅

📊 Flash Loan Contract Status:
   Owner: 0x...
   Flash loans executed: 0
   You are owner: true

⚡ Executing Test Flash Loan...
📤 Transaction sent: 0x...
✅ Flash loan executed successfully!
   Block: 14567890
   Gas used: 328,542
```

## ❌ Troubleshooting

### Common Issues

1. **CALL_EXCEPTION errors**
   - **Problem**: Using mainnet token addresses on testnet
   - **Solution**: Use the new scripts with correct testnet addresses

2. **Insufficient funds**
   - **Problem**: Not enough POL for gas
   - **Solution**: Get more POL from faucets

3. **Contract call failed**
   - **Problem**: Contract might not be owner or have insufficient permissions
   - **Solution**: Check contract status with the new scripts

### Solutions

- Use `scripts/testnet-arbitrage.js` for safe simulation
- Use `scripts/testnet-real-arbitrage.js` for actual testing
- Ensure you have testnet tokens from the correct faucets

## 🌐 Useful Links

- **Amoy Explorer**: https://www.oklink.com/amoy
- **Polygon Faucet**: https://faucet.polygon.technology/
- **Circle USDC Faucet**: https://faucet.circle.com/
- **Contract on Explorer**: https://www.oklink.com/amoy/address/0x841DCCA9B43d1AF14D52ED808ca9c30fB2d1b7e5

## 🎯 Next Steps

1. **Test the Simulator**: Start with `testnet-arbitrage.js` to understand the flow
2. **Execute Flash Loans**: Use `testnet-real-arbitrage.js` to see real transactions
3. **Monitor Results**: Check transaction hashes on the Amoy explorer
4. **Optimize Strategy**: Adjust parameters based on testnet results

## 🔒 Security Notes

- This is testnet only - tokens have no real value
- Never use mainnet private keys for testing
- Always verify contract addresses before interacting
- Test thoroughly before considering mainnet deployment

## 💡 Tips

- Start with small amounts for testing
- Monitor gas usage to estimate mainnet costs
- Use the simulator first to understand the arbitrage logic
- Check contract status before executing flash loans 