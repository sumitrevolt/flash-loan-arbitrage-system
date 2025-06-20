# Quick Start Guide - Unified Flash Loan Arbitrage System

## Prerequisites

1. **Python 3.8+** installed
2. **Node.js** (for some MCP servers)
3. **Git** for version control
4. **Polygon RPC URL** (Alchemy, Infura, or QuickNode)
5. **Trading wallet** with some MATIC for gas fees

## Installation

1. **Clone or navigate to the project:**
   ```bash
   cd "c:\Users\Ratanshila\Documents\flash loan"
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.template .env
   # Edit .env with your actual values
   ```

4. **Create logs directory:**
   ```bash
   mkdir logs
   ```

## Configuration

### 1. Environment Setup
Edit `.env` file with your settings:
- `POLYGON_RPC_URL`: Your Polygon RPC endpoint
- `PRIVATE_KEY`: Your trading wallet private key (keep secure!)
- API keys for various services

### 2. MCP Servers Configuration
Edit `config/mcp_servers.json` to configure which MCP servers to run.

### 3. Arbitrage Configuration  
Edit `config/arbitrage_config.json` to set trading parameters:
- Minimum profit thresholds
- Risk management settings
- Token pairs to monitor

## Running the System

### Option 1: Full System (Recommended)
```bash
# Terminal 1: Start MCP Coordinator
python core/coordinators/unified_mcp_coordinator.py

# Terminal 2: Start Arbitrage System
python core/trading/unified_arbitrage_system.py --mode monitor

# Terminal 3: Start Monitoring Dashboard
python monitoring/unified_monitoring_dashboard.py --mode console
```

### Option 2: Individual Components

#### MCP Coordinator Only
```bash
python core/coordinators/unified_mcp_coordinator.py
```
- Web interface: http://localhost:9000/status
- Manages all MCP servers
- Provides multi-agent coordination

#### Arbitrage System Only
```bash
# Monitor mode (safe, no trading)
python core/trading/unified_arbitrage_system.py --mode monitor

# Analysis mode (with AI insights)
python core/trading/unified_arbitrage_system.py --mode analyze --ai-optimize

# Execute mode (ACTUAL TRADING - use with caution!)
python core/trading/unified_arbitrage_system.py --mode execute --min-profit 10
```

#### Monitoring Dashboard Only
```bash
# Console dashboard
python monitoring/unified_monitoring_dashboard.py --mode console

# Web dashboard
python monitoring/unified_monitoring_dashboard.py --mode web

# Both console and web
python monitoring/unified_monitoring_dashboard.py --mode both
```
- Web interface: http://localhost:5000

## Web Interfaces

1. **MCP Coordinator Dashboard:** http://localhost:9000/status
   - Server status and health
   - Agent coordination
   - Task management

2. **Monitoring Dashboard:** http://localhost:5000
   - Real-time arbitrage opportunities
   - Price monitoring
   - System statistics

## Safety Features

### 1. Paper Trading Mode
- Set `ENABLE_PAPERTRADING=true` in `.env`
- System will simulate trades without real execution

### 2. Circuit Breaker
- Automatically stops trading after consecutive failures
- Configurable cooldown period

### 3. Risk Limits
- Maximum daily loss limits
- Position size limits
- MEV risk scoring

## Monitoring

### Console Dashboard Features:
- Real-time server status
- Live arbitrage opportunities
- Token prices
- System statistics
- Colored output for easy reading

### Web Dashboard Features:
- Interactive charts
- Historical data
- Alert management
- Performance metrics

## Troubleshooting

### Common Issues:

1. **"Connection refused" errors:**
   - Check if MCP servers are running
   - Verify port availability
   - Check firewall settings

2. **"RPC connection failed":**
   - Verify `POLYGON_RPC_URL` in `.env`
   - Check RPC provider status
   - Try alternative RPC endpoints

3. **"No opportunities found":**
   - Normal during low volatility
   - Check if DEX APIs are responsive
   - Verify token configurations

4. **Import errors:**
   - Install missing dependencies: `pip install -r requirements.txt`
   - Check Python version compatibility

### Logs Location:
- System logs: `logs/`
- Individual component logs in their respective directories

## Development Mode

For development and testing:

1. **Set development environment:**
   ```bash
   ENVIRONMENT=development
   DEBUG=true
   ENABLE_PAPERTRADING=true
   ```

2. **Use test networks:**
   - Polygon Mumbai testnet
   - Lower minimum profit thresholds
   - Reduced position sizes

## Production Deployment

### Security Checklist:
- [ ] Private keys stored securely
- [ ] Web interfaces protected (authentication)
- [ ] Monitoring alerts configured
- [ ] Backup systems in place
- [ ] Risk limits properly set

### Performance Optimization:
- [ ] SSD storage for logs
- [ ] Sufficient RAM (8GB+ recommended)
- [ ] Fast internet connection
- [ ] Multiple RPC endpoints configured

## Getting Help

1. Check logs for error messages
2. Review configuration files
3. Verify environment variables
4. Test individual components
5. Check project documentation

## System Architecture

```
MCP Coordinator (Port 9000)
├── Risk Agent (Port 8002)
├── Execution Agent (Port 8001)  
├── Analytics Agent (Port 8003)
├── QA Agent (Port 8004)
└── Logs Agent (Port 8005)

Arbitrage System
├── DEX Price Monitoring
├── Opportunity Detection
├── Flash Loan Execution
└── MCP Integration

Monitoring Dashboard (Port 5000)
├── Real-time Display
├── Web Interface
├── Alert System
└── Performance Tracking
```

## Next Steps

1. **Start with monitor mode** to understand the system
2. **Analyze opportunities** to learn market patterns  
3. **Test with small amounts** before scaling up
4. **Monitor performance** and adjust parameters
5. **Set up alerts** for important events

Remember: This system handles real money. Always test thoroughly and understand the risks before trading with significant amounts.
