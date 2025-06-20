# 🚀 Flash Loan Arbitrage Contract v2.1

An advanced flash loan arbitrage system built with **Aave V3** integration, supporting multiple DEXes on **Polygon** network with comprehensive safety features and monitoring capabilities.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Usage](#-usage)
- [Testing](#-testing)
- [Security](#-security)
- [Monitoring](#-monitoring)
- [Troubleshooting](#-troubleshooting)

## ✨ Features

### 🏦 Core Functionality
- **Aave V3 Flash Loans**: Zero-collateral borrowing for arbitrage opportunities
- **Multi-DEX Support**: Uniswap V3, QuickSwap, SushiSwap, and more
- **Token Whitelisting**: Configurable token support with batch operations
- **Gas Optimization**: Efficient contract design with struct packing

### 🛡️ Security Features
- **ReentrancyGuard**: Protection against reentrancy attacks
- **Pausable Contract**: Emergency stop functionality
- **Circuit Breaker**: Automatic protection after failed transactions
- **Access Control**: Owner-only administrative functions
- **Slippage Protection**: Configurable tolerance levels

### 📊 Advanced Features
- **Fee Management**: Configurable fee structure with recipient settings
- **Swap Statistics**: Comprehensive performance tracking
- **Health Monitoring**: Real-time contract status checks
- **Emergency Withdrawal**: Safe asset recovery functionality
- **Detailed Events**: Complete transaction logging

## 🏗️ Architecture

```
FlashLoanArbitrageFixed
├── Flash Loan Integration (Aave V3)
├── DEX Routers (Uniswap V3, V2 compatible)
├── Token Management (Whitelisting)
├── Security Layer (ReentrancyGuard, Pausable)
├── Fee Management System
├── Statistics & Monitoring
└── Emergency Functions
```

### 📦 Contract Structure

- **Main Contract**: `FlashLoanArbitrageFixed.sol`
- **Dependencies**: OpenZeppelin v5.3.0, Aave V3, Uniswap periphery
- **Solidity Version**: 0.8.20
- **Network**: Polygon (Chain ID: 137)

## 🛠️ Installation

### Prerequisites

- **Node.js**: v16 or higher
- **npm**: v7 or higher
- **Git**: Latest version

### Quick Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd flash-loan-arbitrage

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit environment variables
# Add your PRIVATE_KEY and POLYGONSCAN_API_KEY
```

### Dependencies

```json
{
  "hardhat": "^2.24.3",
  "ethers": "^5.8.0",
  "@openzeppelin/contracts": "^5.3.0",
  "@aave/core-v3": "^1.19.3",
  "@uniswap/v3-periphery": "^1.4.4",
  "@uniswap/v2-periphery": "^1.1.0-beta.0"
}
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Network Configuration
POLYGON_RPC_URL=https://polygon-rpc.com
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com

# Wallet Configuration
PRIVATE_KEY=your_private_key_here

# Contract Verification
POLYGONSCAN_API_KEY=your_polygonscan_api_key

# Gas Configuration (optional)
GAS_LIMIT=6000000
GAS_PRICE=35000000000
```

### Network Configuration

The contract is configured for **Polygon Mainnet** with the following addresses:

- **Aave V3 Pool Provider**: `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb`
- **Uniswap V3 Router**: `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`
- **QuickSwap Router**: `0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff`
- **SushiSwap Router**: `0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506`

## 🚀 Deployment

### Step 1: Compile Contract

```bash
npm run compile
```

### Step 2: Deploy to Polygon

```bash
npm run deploy
```

The deployment script will:
- ✅ Deploy the contract with proper constructor arguments
- ✅ Verify deployment success
- ✅ Perform initial health checks
- ✅ Display contract information

### Step 3: Verify on PolygonScan

```bash
npm run verify <CONTRACT_ADDRESS>
```

### Step 4: Setup and Configure

```bash
npm run setup <CONTRACT_ADDRESS>
```

This will:
- ✅ Whitelist additional tokens
- ✅ Approve additional DEXes
- ✅ Set optimal parameters
- ✅ Perform final health check

## 📖 Usage

### Basic Arbitrage Execution

```javascript
// Execute arbitrage between two DEXes
await contract.executeArbitrage(
    borrowToken,      // Token to borrow
    amount,           // Amount to borrow
    dex1,             // First DEX router
    dex2,             // Second DEX router
    intermediateToken, // Token to swap through
    dex1Fee,          // DEX 1 fee tier (for V3)
    dex2Fee,          // DEX 2 fee tier (for V3)
    deadline          // Transaction deadline
);
```

### Token Management

```javascript
// Whitelist a single token
await contract.whitelistToken(tokenAddress, true);

// Batch whitelist multiple tokens
await contract.whitelistTokensBatch([token1, token2, token3], true);

// Approve a DEX
await contract.approveDex(dexAddress, true);
```

### Configuration

```javascript
// Set slippage tolerance (in basis points)
await contract.setSlippageTolerance(300); // 3%

// Set fee parameters
await contract.setFeeParameters(
    500,              // 5% fee
    feeRecipient,     // Fee recipient address
    true              // Enable fees
);
```

### Monitoring

```javascript
// Check contract health
const [isHealthy, status, tokenCount, dexCount] = await contract.healthCheck();

// Get swap statistics
const stats = await contract.getSwapStatistics();

// Get contract information
const [version, date, description] = await contract.getContractInfo();
```

## 🧪 Testing

### Run Full Test Suite

```bash
npm test
```

### Run Specific Tests

```bash
npx hardhat test --grep "Deployment"
npx hardhat test --grep "Token Management"
npx hardhat test --grep "Security"
```

### Generate Coverage Report

```bash
npm run coverage
```

### Gas Usage Report

```bash
npm run gas-report
```

## 🔒 Security

### Security Features

1. **ReentrancyGuard**: Prevents reentrancy attacks
2. **Pausable**: Emergency stop functionality
3. **Ownable**: Access control for administrative functions
4. **Circuit Breaker**: Automatic protection after failed transactions
5. **Input Validation**: Comprehensive parameter checking
6. **Slippage Protection**: MEV and sandwich attack mitigation

### Best Practices

- ✅ Always test with small amounts first
- ✅ Monitor gas prices before execution
- ✅ Use dedicated wallet for contract operations
- ✅ Keep private keys secure
- ✅ Regular health checks
- ✅ Monitor failed transaction counts

### Emergency Procedures

```javascript
// Pause contract in emergency
await contract.pause();

// Emergency withdrawal (only when paused)
await contract.emergencyWithdrawAll();

// Reset failed transaction counter
await contract.resetFailedTransactionsCount();
```

## 📊 Monitoring

### Health Monitoring

```javascript
// Regular health check
const [isHealthy, status, tokenCount, dexCount, failedCount] = await contract.healthCheck();

if (!isHealthy) {
    console.log("⚠️ Contract needs attention:", status);
}
```

### Performance Tracking

```javascript
// Get detailed statistics
const [
    totalSwaps,
    successfulSwaps,
    failedSwaps,
    totalProfits,
    totalFees,
    lastSwapTimestamp,
    highestProfit,
    mostProfitableToken
] = await contract.getSwapStatistics();
```

### Event Monitoring

Monitor these key events:

- `ArbitrageExecuted`: Successful arbitrage with profit details
- `ArbitrageFailed`: Failed arbitrage with reason
- `SwapExecuted`: Individual swap completion
- `TokenWhitelisted`: Token whitelist changes
- `DexApprovalChanged`: DEX approval changes

## 🐛 Troubleshooting

### Common Issues

#### 1. Compilation Errors

```bash
# Clean and recompile
npm run clean
npm run compile
```

#### 2. Gas Estimation Failures

```bash
# Check gas price and limit in hardhat.config.js
# Increase gas limit for complex operations
```

#### 3. Flash Loan Failures

- ✅ Ensure sufficient liquidity on target DEXes
- ✅ Check token approvals
- ✅ Verify slippage tolerance
- ✅ Monitor gas prices

#### 4. Verification Issues

```bash
# Wait a few minutes after deployment
# Ensure constructor arguments match exactly
# Check POLYGONSCAN_API_KEY in .env
```

### Debug Commands

```bash
# Check contract deployment
npx hardhat console --network polygon

# Verify network connection
npx hardhat run scripts/test-connection.js --network polygon

# Check account balance
npx hardhat run scripts/check-balance.js --network polygon
```

### Support

For issues and support:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review contract events and logs
3. Test on Mumbai testnet first
4. Monitor gas usage and costs

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided "as is" without warranty of any kind. Flash loan arbitrage involves significant risks including but not limited to:

- **Financial Risk**: Potential loss of funds
- **Technical Risk**: Smart contract vulnerabilities
- **Market Risk**: Price volatility and slippage
- **Gas Risk**: High transaction costs

Always test thoroughly and never invest more than you can afford to lose.

---

**Made with ❤️ by the Flash Loan Arbitrage Team**

*Building the future of DeFi arbitrage, one flash loan at a time.* ⚡
