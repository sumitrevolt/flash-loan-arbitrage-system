# 🏦 Aave Flash Loan Monitoring System

A comprehensive monitoring solution for Aave flash loan arbitrage operations on Polygon network.

## 🚀 Overview


This monitoring system provides real-time tracking and analysis of:

- Aave pool liquidity and utilization
- Flash loan executions and success rates
- Arbitrage opportunities across DEXs
- Gas prices and transaction costs
- Performance metrics and profitability
- WebSocket-based live updates
- Alert system for critical events


## 📋 Components

### 1. **Aave Flash Loan Monitor** (`aave_flash_loan_monitor.py`)

Main monitoring dashboard that tracks:

- Aave pool metrics (liquidity, utilization, fees)
- Flash loan execution history
- Performance statistics
- Real-time arbitrage opportunities
- System health status


### 2. **WebSocket Monitor** (`aave_websocket_monitor.py`)

Real-time event monitoring via WebSocket:

- Flash loan event detection
- DEX swap monitoring
- Gas price tracking
- Alert notifications
- WebSocket server for client connections


### 3. **Live Arbitrage Monitor** (`live_arbitrage_monitor.py`)

Continuous arbitrage opportunity scanner:

- Multi-DEX price monitoring
- Profit calculations with fees
- Opportunity identification
- Trade route optimization


### 4. **Monitoring Launcher** (`launch_aave_monitoring.py`)

Orchestrates all monitoring components:

- Prerequisite checks
- Process management
- Auto-restart capabilities
- Status tracking
- Web dashboard generation


## 🛠️ Installation

### Prerequisites
```bash
# Required packages
pip install web3 python-dotenv psutil websockets aiohttp

# Optional (for full monitoring stack)
# Prometheus - https://prometheus.io/download/
# Grafana - https://grafana.com/grafana/download
```

### Environment Setup
Create a `.env` file in the project root:
```bash
# Required
POLYGON_RPC_URL=https://polygon-rpc.com/your-endpoint
POLYGON_WS_URL=wss://polygon-ws.com/your-endpoint

# Optional
ALERT_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook
```

### Configuration
Ensure `production_config.json` exists with:
```json
{
  "aave": {
    "pool_address": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "flash_loan_fee": 0.0009
  },
  "tokens": {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
  },
  "dexes": {
    "uniswapv3": {
      "router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
      "fee_tier": 0.003
    },
    "sushiswap": {
      "router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
      "fee_tier": 0.003
    }
  },
  "trading": {
    "min_profit_usd": 10,
    "min_trade_size_usd": 1000
  }
}
```

## 🚀 Quick Start

### Launch All Monitoring Components
```bash
python monitoring/launch_aave_monitoring.py
```

This will:
1. Check all prerequisites
2. Launch all monitoring components
3. Create a web dashboard (`dashboard.html`)
4. Display status and access URLs

### Run Individual Components

```bash
# Main monitor only
python monitoring/aave_flash_loan_monitor.py

# WebSocket monitor only
python monitoring/aave_websocket_monitor.py

# Arbitrage monitor only
python monitoring/live_arbitrage_monitor.py
```

## 📊 Monitoring Dashboard

### Terminal Dashboard
The main monitor displays:
```
🏦 AAVE FLASH LOAN ARBITRAGE MONITOR
================================================================================
🕐 Last Update: 2024-01-20 15:30:45

📊 AAVE POOL STATUS
--------------------------------------------------------------------------------
Token      Available Liquidity    Utilization    Flash Fee    Status
USDC       $12,345,678.45            45.23%        0.090%     ✅ Ready
USDT       $8,234,567.12             62.15%        0.090%     ✅ Ready
WETH       $5,123,456.78             78.45%        0.090%     ⚠️ High Util
WMATIC     $234,567.89               23.45%        0.090%     ✅ Ready

⛽ GAS PRICES
--------------------------------------------------------------------------------
Current: 45.23 gwei | Base Fee: 42.15 gwei | Status: ✅ Safe

📈 PERFORMANCE METRICS
--------------------------------------------------------------------------------
Total Executions: 156 | Success Rate: 94.2% | Total Profit: $2,345.67
Total Gas Cost: $456.78 | Net Profit: $1,888.89 | Avg Profit/Trade: $12.67

🔄 RECENT FLASH LOAN EXECUTIONS
--------------------------------------------------------------------------------
Time       Token    Amount        Route                     Profit    Gas      Status
15:28:32   USDC     $10,000      UniswapV3 → SushiSwap     $25.50    $5.25    ✅ Success
15:25:18   WETH     $50,000      SushiSwap → QuickSwap     $125.75   $12.50   ✅ Success
```

### Web Dashboard
Open `monitoring/dashboard.html` in your browser for:
- Real-time WebSocket updates
- Visual metrics display
- Alert notifications
- Links to Prometheus/Grafana

## 🚨 Alert System

The system monitors and alerts on:
- **High Gas Prices**: When gas > 150 gwei
- **Low Liquidity**: When pool liquidity < $100k
- **High Utilization**: When utilization > 85%
- **Large Flash Loans**: When loan amount > $100k
- **Failed Transactions**: When flash loan reverts

Alerts are displayed in:
- Terminal output (highlighted)
- Web dashboard notifications
- Optional webhook notifications

## 📈 Metrics Tracked

### Pool Metrics
- Available liquidity per token
- Utilization rates
- Flash loan fees
- Reserve data updates

### Performance Metrics
- Total/successful executions
- Success rate percentage
- Gross/net profit
- Gas costs
- Average profit per trade

### Opportunity Metrics
- DEX price disparities
- Arbitrage routes
- Expected profits
- Risk scores
- Executability status

## 🔧 Advanced Configuration

### Custom Alert Thresholds
Edit in `aave_websocket_monitor.py`:
```python
self.alert_thresholds = {
    'min_profit': Decimal('100'),      # Alert on profits > $100
    'high_gas': 150,                   # Alert on gas > 150 gwei
    'large_loan': Decimal('100000'),   # Alert on loans > $100k
}
```

### Safety Parameters
Edit in `aave_flash_loan_monitor.py`:
```python
self.max_utilization = Decimal('0.85')  # 85% max utilization
self.min_liquidity = Decimal('100000')  # Min $100k liquidity
self.max_gas_price = 200                # Max 200 gwei
```

## 🔍 Troubleshooting

### Common Issues

1. **"Missing environment variable: POLYGON_RPC_URL"**
   - Ensure `.env` file exists with required variables

2. **"Port 8765 is already in use"**
   - Kill existing process: `lsof -ti:8765 | xargs kill -9`

3. **"WebSocket connection failed"**
   - Check POLYGON_WS_URL is valid
   - Ensure WebSocket endpoint supports subscriptions

4. **"Failed to fetch Aave metrics"**
   - Verify pool address is correct
   - Check RPC endpoint is responsive

### Logs
Monitor logs for debugging:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python monitoring/launch_aave_monitoring.py
```

## 📊 Integration with Grafana

### Prometheus Metrics
Available at `http://localhost:9090`:
- `flash_loan_executions_total`
- `flash_loan_success_rate`
- `arbitrage_profit_total`
- `gas_price_gwei`
- `pool_liquidity_usd`
- `pool_utilization_percent`

### Grafana Dashboard
Import the dashboard JSON from `monitoring/grafana-dashboard.json` (if available) or create custom dashboards using Prometheus metrics.

## 🛡️ Security Considerations

1. **RPC Endpoints**: Use private/authenticated endpoints
2. **WebSocket Security**: Implement authentication for production
3. **Alert Webhooks**: Use secure webhook URLs
4. **Configuration**: Never commit sensitive data to version control

## 📝 License

This monitoring system is part of the Aave Flash Loan Arbitrage Bot project.

---

## 🤝 Contributing

To add new monitoring features:
1. Add new metrics to relevant monitor class
2. Update dashboard displays
3. Add corresponding alerts if needed
4. Update documentation

For support, please refer to the main project documentation.