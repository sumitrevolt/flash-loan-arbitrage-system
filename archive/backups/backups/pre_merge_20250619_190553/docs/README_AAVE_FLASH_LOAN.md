# 🚀 Aave Flash Loan Arbitrage System

A comprehensive, production-ready Aave flash loan arbitrage system with MCP (Model Context Protocol) integration, multi-agent coordination, and AI-powered optimization.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Safety & Risk Management](#safety--risk-management)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## ✨ Features

### Core Functionality
- **Real Aave V3 Flash Loans** on Polygon network
- **Multi-DEX Arbitrage** across QuickSwap, SushiSwap, Uniswap V3
- **Live Price Feeds** from The Graph subgraphs and direct Web3 calls
- **AI-Powered Optimization** for profit maximization
- **MEV Protection** with private mempool support
- **Real-time Risk Management** with circuit breakers

### Advanced Features
- **MCP Server Architecture** for modular agent coordination
- **Multi-Agent System** (Execution, Risk, Analytics, Monitoring, etc.)
- **Real-time Dashboard** with live metrics
- **Comprehensive Logging** and performance tracking
- **Gas Optimization** with dynamic pricing
- **Emergency Stop** mechanisms

### Supported Assets
- USDC, USDT, DAI (Stablecoins)
- WMATIC (Native token)
- WETH (Ethereum)

### Supported DEXes
- ✅ QuickSwap (Polygon)
- ✅ SushiSwap (Polygon)
- ✅ Uniswap V3 (Polygon)
- 🔄 Curve (Coming soon)
- 🔄 Balancer V2 (Coming soon)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Aave Flash Loan System                   │
├─────────────────────────────────────────────────────────────┤
│  🎯 Main Launcher (launch_aave_flash_loan_system.py)        │
│     ├── Environment Validation                             │
│     ├── MCP Server Orchestration                           │
│     └── Health Monitoring                                  │
├─────────────────────────────────────────────────────────────┤
│  🤖 MCP Agents (Specialized Microservices)                 │
│     ├── 💰 Aave Flash Loan Executor                        │
│     ├── 📊 Real-time Price Fetcher                         │
│     ├── 🔍 Arbitrage Opportunity Scanner                   │
│     ├── 🛡️  Risk Management Agent                          │
│     ├── ⚡ Gas Optimization Agent                           │
│     ├── 🔒 MEV Protection Agent                            │
│     ├── 🧠 AI Profit Optimizer                             │
│     ├── 📈 Blockchain Monitor                              │
│     └── ⚙️  Transaction Executor                           │
├─────────────────────────────────────────────────────────────┤
│  🌐 Data Sources (Live Data Only)                          │
│     ├── The Graph Subgraphs                               │
│     ├── Direct Web3 Calls                                 │
│     ├── Aave V3 Protocol                                  │
│     └── DEX Smart Contracts                               │
├─────────────────────────────────────────────────────────────┤
│  📊 Monitoring & Dashboard                                 │
│     ├── Web Dashboard (Port 9001)                         │
│     ├── Real-time Logs                                    │
│     ├── Performance Metrics                               │
│     └── Health Checks                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **RPC Access** to Polygon network (Alchemy/Infura recommended)
3. **Private Key** with some MATIC for gas fees
4. **Basic understanding** of DeFi and flash loans

### Installation

1. **Clone and setup environment:**
```bash
# Copy environment template
cp .env.aave_flash_loan .env

# Edit .env with your actual values
nano .env
```

2. **Essential environment variables to configure:**
```bash
# RPC Access (Required)
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY

# Wallet (Required)
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

# Aave Protocol (Pre-configured)
AAVE_POOL_ADDRESS=0x794a61358D6845594F94dc1DB02A252b5b4814aD
```

3. **Install dependencies:**
```bash
pip install web3 aiohttp python-dotenv psutil
```

4. **Create directory structure:**
```bash
mkdir -p logs data backups
mkdir -p mcp_servers/{aave,pricing,risk,gas,mev,ai,monitoring,execution}
```

### Launch System

```bash
# Start the complete system
python launch_aave_flash_loan_system.py

# Or with specific mode
python core/trading/unified_arbitrage_system.py --mode monitor
```

### Access Dashboard

Once running, access the web dashboard at:
- **Main Dashboard:** http://localhost:9001
- **Health Check:** http://localhost:9001/health
- **Live Logs:** http://localhost:9001/logs

## ⚙️ Configuration

### Main Configuration Files

1. **`config/aave_flash_loan_mcp_config.json`** - MCP server and agent configuration
2. **`.env`** - Environment variables and secrets
3. **`config/mcp_servers.json`** - General MCP server settings

### Key Configuration Options

#### Risk Parameters
```json
{
  "min_profit_usd": 10,
  "max_slippage": 0.01,
  "max_flash_loan_usd": 1000000,
  "circuit_breaker_threshold": 5
}
```

#### Supported Trading Pairs
- WMATIC/USDC
- WMATIC/USDT
- USDC/USDT
- WETH/USDC
- DAI/USDC

#### Agent Roles
- **EXECUTION** - Execute flash loans and transactions
- **RISK** - Risk management and safety checks
- **ANALYTICS** - Opportunity analysis and detection
- **MONITORING** - System health and blockchain monitoring
- **OPTIMIZATION** - Gas and profit optimization

## 📖 Usage

### Monitor Mode (Safe Start)
```bash
python core/trading/unified_arbitrage_system.py --mode monitor
```
- Finds arbitrage opportunities
- No actual trading
- Safe for testing and analysis

### Execution Mode (Live Trading)
```bash
python core/trading/unified_arbitrage_system.py --mode execute
```
- Executes profitable opportunities
- Requires funded wallet
- Real money at risk

### Analysis Mode (AI Insights)
```bash
python core/trading/unified_arbitrage_system.py --mode analyze
```
- AI-powered market analysis
- Pattern recognition
- Performance optimization suggestions

### Manual Flash Loan Testing
```python
from mcp_servers.aave.aave_flash_loan_mcp_server import AaveFlashLoanMCPServer

# Initialize server
server = AaveFlashLoanMCPServer()
await server.initialize_web3()

# Check Aave liquidity
liquidity = await server.get_aave_pool_liquidity('USDC')
print(f"Available USDC liquidity: {liquidity}")

# Simulate flash loan
result = await server.simulate_flash_loan({
    'asset': 'USDC',
    'amount': 10000,
    'arbitrage_path': ['quickswap', 'sushiswap']
})
print(f"Simulation result: {result}")
```

## 🛡️ Safety & Risk Management

### Built-in Safety Features

1. **Circuit Breakers**
   - Automatic shutdown after consecutive failures
   - Configurable failure thresholds
   - Cooldown periods

2. **Risk Limits**
   - Maximum flash loan amounts
   - Minimum profit requirements
   - Slippage protection

3. **Real-time Monitoring**
   - Health checks every 15 seconds
   - Automatic restart of failed components
   - Alert systems

4. **MEV Protection**
   - Private mempool integration
   - Transaction bundling
   - Front-running detection

### Recommended Safety Practices

1. **Start Small**
   ```bash
   # Set conservative limits initially
   MIN_PROFIT_USD=10
   MAX_FLASH_LOAN_USD=10000
   SAFE_MODE=true
   ```

2. **Monitor Closely**
   - Watch dashboard during first runs
   - Check logs regularly: `tail -f logs/system_launcher.log`
   - Set up alerts for your contact methods

3. **Test Environment First**
   ```bash
   # Use testnet for initial testing
   POLYGON_RPC_URL=https://rpc-mumbai.maticvigil.com
   ```

4. **Emergency Stop**
   ```bash
   # Kill all processes immediately
   pkill -f "aave_flash_loan"
   
   # Or use Ctrl+C for graceful shutdown
   ```

## 📊 Monitoring

### Web Dashboard Features

- **System Status** - All agents and their health
- **Live Opportunities** - Current arbitrage opportunities
- **Execution History** - Past transactions and results
- **Performance Metrics** - Profit, success rate, gas usage
- **Risk Indicators** - Current risk levels and alerts

### Log Files

```bash
# Main system logs
tail -f logs/system_launcher.log

# Individual agent logs
tail -f logs/unified_mcp_coordinator.log
tail -f logs/unified_arbitrage_system.log

# Real-time monitoring
watch -n 1 "curl -s http://localhost:9001/health | jq"
```

### Key Metrics to Monitor

1. **Profitability**
   - Total profit earned
   - Average profit per transaction
   - Success rate percentage

2. **Performance**
   - Opportunities found per hour
   - Execution speed (< 30 seconds target)
   - Gas efficiency

3. **Risk Indicators**
   - Failed transaction count
   - Circuit breaker status
   - Slippage occurrences

## 🔧 Troubleshooting

### Common Issues

#### 1. "Environment validation failed"
```bash
# Check RPC connection
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  $POLYGON_RPC_URL

# Verify environment variables
grep -E "(POLYGON_RPC_URL|PRIVATE_KEY)" .env
```

#### 2. "No MCP servers configured"
```bash
# Check configuration file exists
ls -la config/aave_flash_loan_mcp_config.json

# Validate JSON format
cat config/aave_flash_loan_mcp_config.json | jq
```

#### 3. "Failed to start server"
```bash
# Check Python path and permissions
which python
python --version

# Install missing dependencies
pip install -r requirements.txt
```

#### 4. "No profitable opportunities found"
```bash
# Check DEX connections
python -c "
from mcp_servers.pricing.real_time_price_mcp_server import RealTimePriceFetcher
import asyncio
fetcher = RealTimePriceFetcher()
print(asyncio.run(fetcher.get_live_prices()))
"
```

#### 5. "Transaction failed"
```bash
# Check wallet balance
python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('$POLYGON_RPC_URL'))
print(f'Balance: {w3.eth.get_balance(\"YOUR_ADDRESS\") / 1e18} MATIC')
"
```

### Performance Optimization

1. **RPC Performance**
   ```bash
   # Use premium RPC providers
   POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
   
   # Enable connection pooling
   MAX_CONCURRENT_REQUESTS=50
   ```

2. **Resource Usage**
   ```bash
   # Monitor system resources
   htop
   
   # Adjust worker processes
   MCP_MAX_CONCURRENT_SERVERS=10
   ```

3. **Network Latency**
   ```bash
   # Use geographically close RPC
   # Enable local caching
   PRICE_CACHE_TTL_SECONDS=30
   ```

## 📋 System Requirements

### Minimum Requirements
- **OS:** Linux/macOS/Windows 10+
- **RAM:** 4GB available
- **CPU:** 2+ cores
- **Storage:** 10GB free space
- **Network:** Stable internet (< 100ms latency to RPC)

### Recommended Requirements
- **OS:** Ubuntu 20.04+ or macOS 12+
- **RAM:** 8GB available
- **CPU:** 4+ cores (for parallel processing)
- **Storage:** 50GB SSD
- **Network:** Dedicated server with low latency

### Cloud Deployment
For production deployment, consider:
- **AWS EC2** (c5.large or larger)
- **Google Cloud Compute** (n2-standard-2 or larger)
- **DigitalOcean Droplets** (4GB+ RAM)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. **Fork the repository**
2. **Create feature branch:** `git checkout -b feature/amazing-feature`
3. **Make changes and test thoroughly**
4. **Commit changes:** `git commit -m 'Add amazing feature'`
5. **Push to branch:** `git push origin feature/amazing-feature`
6. **Open Pull Request**

### Areas for Contribution

- Additional DEX integrations (Curve, Balancer, etc.)
- Enhanced AI optimization algorithms
- Mobile dashboard/monitoring app
- Additional blockchain networks
- Performance optimizations
- Documentation improvements

## ⚠️ Disclaimer

**IMPORTANT LEGAL DISCLAIMERS:**

1. **Financial Risk:** This software involves real financial transactions and risk of loss
2. **No Warranty:** Provided "as-is" without any warranties
3. **Educational Purpose:** Primarily for educational and research purposes
4. **Regulatory Compliance:** Ensure compliance with local financial regulations
5. **Due Diligence:** Thoroughly test before risking significant amounts

**The developers are not responsible for any financial losses incurred through use of this software.**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation:** [Full Documentation](docs/)
- **API Reference:** [API Docs](docs/api.md)
- **Examples:** [Usage Examples](examples/)
- **Community:** [Discord Server](https://discord.gg/aave-arbitrage)
- **Support:** [GitHub Issues](https://github.com/your-repo/issues)

---

## 🎯 Quick Commands Reference

```bash
# Start system
python launch_aave_flash_loan_system.py

# Monitor mode (safe)
python core/trading/unified_arbitrage_system.py --mode monitor

# Check system health
curl http://localhost:9001/health

# View live logs
tail -f logs/system_launcher.log

# Emergency stop
pkill -f "aave_flash_loan"

# Check opportunities
curl http://localhost:9001 | grep "opportunities"
```

---

**Happy Trading! 🚀💰**

Remember: Start small, monitor closely, and never risk more than you can afford to lose.
