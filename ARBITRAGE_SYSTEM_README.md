# 🚀 Flash Loan Arbitrage System

A comprehensive, AI-driven flash loan arbitrage system with real-time blockchain monitoring, LangChain orchestration, and automated execution capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [System Components](#system-components)
- [Monitoring & Dashboards](#monitoring--dashboards)
- [Safety & Risk Management](#safety--risk-management)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## 🔍 Overview

This system combines advanced blockchain monitoring, AI decision-making, and automated execution to identify and execute profitable flash loan arbitrage opportunities across multiple DEXs (Decentralized Exchanges).

### Key Capabilities

- **Real-time Blockchain Monitoring**: Monitors mempool and new blocks for arbitrage opportunities
- **AI-Driven Decision Making**: Uses LangChain orchestration with confidence scoring and risk assessment
- **Multi-DEX Support**: Supports Uniswap V2/V3, SushiSwap, Balancer, and others
- **Risk Management**: Built-in gas price monitoring, profit thresholds, and position sizing
- **Simulation Mode**: Safe testing environment before live trading
- **Comprehensive Monitoring**: Grafana dashboards, Prometheus metrics, and Jaeger tracing

## ✨ Features

### 🤖 AI & Automation
- LangChain-powered decision orchestration
- Quantum decision engine for optimization
- Swarm intelligence for market analysis
- Real-time risk assessment and management

### ⚡ High-Performance Execution
- Sub-second transaction execution
- MEV protection via Flashbots integration
- Gas optimization strategies
- Parallel processing architecture

### 📊 Monitoring & Analytics
- Real-time dashboard with live metrics
- Historical performance analysis
- Alert system for opportunities and risks
- Detailed logging and tracing

### 🔒 Security & Safety
- Simulation mode for testing
- Multi-layer risk management
- Secure private key handling
- Transaction validation and verification

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web3 Node     │    │ Blockchain      │    │ LangChain       │
│   (Geth)        │◄──►│ Monitor         │◄──►│ Orchestrator    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Redis Cache     │◄──►│ Arbitrage       │◄──►│ Risk Manager    │
│ & Pub/Sub       │    │ Executor        │    │ & AI Agents     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Dashboard &     │
                       │ Monitoring      │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker + Docker Compose** (Linux)
- **8GB+ RAM** (16GB recommended for full system)
- **20GB+ disk space**
- **Stable internet connection**

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd flash-loan-arbitrage-system
   ```

2. **Run the launcher**:

   **Windows (PowerShell)**:
   ```powershell
   .\launch_arbitrage_system.ps1
   ```

   **Linux/Mac (Bash)**:
   ```bash
   ./launch_arbitrage_system.sh
   ```

3. **Configure environment** (first run will create `.env` template):
   ```bash
   # Edit .env file with your settings
   notepad .env  # Windows
   nano .env     # Linux/Mac
   ```

4. **Access the system**:
   - 📊 **Main Dashboard**: http://localhost:3001
   - 🎛️ **Grafana Monitoring**: http://localhost:3000 (admin/admin)
   - 🤖 **LangChain API**: http://localhost:8000

## ⚙️ Configuration

### Environment Variables (`.env` file)

```bash
# API Keys (Required for AI features)
OPENAI_API_KEY=sk-...                    # OpenAI API key for LangChain
ANTHROPIC_API_KEY=sk-ant-...             # Anthropic Claude API key
GITHUB_TOKEN=ghp_...                     # GitHub token for integrations

# Trading Configuration
PRIVATE_KEY=0x...                        # Your Ethereum private key (SECURE!)
FLASH_LOAN_CONTRACT=0x...                # Deployed flash loan contract address
EXECUTE_TRADES=false                     # true=live trading, false=simulation

# Risk Management
MAX_GAS_PRICE=500                        # Maximum gas price in gwei
MIN_PROFIT_THRESHOLD=0.001               # Minimum profit (0.1% = 0.001)

# Database Passwords
POSTGRES_PASSWORD=secure_password_2024
RABBITMQ_PASSWORD=secure_password_2024
GRAFANA_PASSWORD=admin
```

### Trading Modes

#### 🔒 Simulation Mode (Default & Recommended)
```bash
EXECUTE_TRADES=false
```
- **Safe testing environment**
- **No real money at risk**
- **Full system functionality**
- **Performance metrics and analysis**

#### 💰 Live Trading Mode
```bash
EXECUTE_TRADES=true
PRIVATE_KEY=0x...                # Your actual private key
FLASH_LOAN_CONTRACT=0x...        # Your deployed contract
```
⚠️ **WARNING**: Live trading involves real money and risk!

## 🧩 System Components

### Core Services

| Service | Port | Description |
|---------|------|-------------|
| **LangChain Orchestrator** | 8000 | AI decision-making and coordination |
| **Blockchain Monitor** | 8070 | Real-time blockchain transaction monitoring |
| **Arbitrage Executor** | 8071 | Trade execution and transaction management |
| **Web3 Node** | 8545 | Ethereum blockchain node (HTTP RPC) |
| **Web3 Node WS** | 8546 | Ethereum blockchain node (WebSocket) |

### AI & Analysis Services

| Service | Port | Description |
|---------|------|-------------|
| **Quantum Decision Engine** | 8010 | Advanced optimization algorithms |
| **Market Predictor** | 8040 | Transformer-based market analysis |
| **Risk Manager** | 8050 | Real-time risk assessment |
| **Swarm Coordinator** | 8020 | Distributed intelligence coordination |

### Infrastructure Services

| Service | Port | Description |
|---------|------|-------------|
| **Redis** | 6379 | Caching and pub/sub messaging |
| **PostgreSQL** | 5432 | Primary database |
| **RabbitMQ** | 5672/15672 | Message queue system |
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Monitoring dashboards |
| **Jaeger** | 16686 | Distributed tracing |

## 📊 Monitoring & Dashboards

### Main Dashboard (Port 3001)
- **Live System Status**: Real-time health of all services
- **Arbitrage Opportunities**: Current opportunities and analysis
- **Performance Metrics**: Profit/loss, success rates, execution times
- **Risk Overview**: Current exposure and risk levels

### Grafana Dashboards (Port 3000)
- **System Performance**: CPU, memory, network usage
- **Trading Metrics**: Trades executed, profits, gas usage
- **Blockchain Metrics**: Block times, gas prices, mempool status
- **AI Decision Metrics**: Confidence scores, prediction accuracy

### Prometheus Metrics (Port 9090)
- Custom metrics for all system components
- Trading performance indicators
- System health and resource usage
- Alert rules for critical conditions

## 🔒 Safety & Risk Management

### Built-in Safety Features

1. **Simulation Mode**: Test strategies without real money
2. **Gas Price Limits**: Automatic gas price monitoring and limits
3. **Profit Thresholds**: Minimum profit requirements before execution
4. **Position Sizing**: Dynamic calculation of trade sizes
5. **Circuit Breakers**: Automatic shutdowns on excessive losses

### Risk Parameters

```bash
# Configure in .env file
MAX_GAS_PRICE=500              # Maximum gas price (gwei)
MIN_PROFIT_THRESHOLD=0.001     # Minimum profit (0.1%)
MAX_POSITION_SIZE=5.0          # Maximum ETH per trade
STOP_LOSS_THRESHOLD=-0.01      # Stop trading at 1% total loss
```

### Best Practices

1. **Start with Simulation Mode**: Always test strategies first
2. **Monitor Gas Prices**: High gas can eliminate profits
3. **Diversify Strategies**: Don't rely on single arbitrage type
4. **Set Conservative Limits**: Start with small position sizes
5. **Regular Monitoring**: Check system health and performance

## 🔧 Troubleshooting

### Common Issues

#### Docker Not Starting
```bash
# Check Docker daemon
docker info

# Restart Docker service (Linux)
sudo systemctl restart docker

# Windows: Restart Docker Desktop
```

#### Services Not Responding
```bash
# Check service logs
docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml logs <service-name>

# Restart specific service
docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml restart <service-name>
```

#### Web3 Connection Issues
- Check if Web3 node is running: `curl http://localhost:8545`
- Verify blockchain data directory permissions
- Restart web3-node service

#### Memory/Performance Issues
- Increase Docker memory allocation (8GB minimum)
- Reduce number of replicated services
- Monitor resource usage in Grafana

### Useful Commands

```bash
# View all service logs
docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml logs -f

# Stop all services
docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml down

# Restart entire system
docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml restart

# Check service status
docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml ps

# Scale specific service
docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml up -d --scale dex-analyst-1=5
```

## 💻 Development

### Architecture Overview

The system uses a microservices architecture with the following layers:

1. **Data Layer**: Blockchain monitoring and data ingestion
2. **Processing Layer**: AI analysis and decision making
3. **Execution Layer**: Trade execution and risk management
4. **Presentation Layer**: Dashboards and monitoring

### Adding New Features

1. **New DEX Integration**: Extend `BlockchainMonitor` class
2. **Custom AI Strategies**: Modify `LangChainOrchestrator` analysis
3. **Additional Risk Metrics**: Enhance `RiskManager` calculations
4. **New Monitoring**: Add Prometheus metrics and Grafana panels

### Testing

```bash
# Run system tests
python -m pytest tests/

# Test specific component
python -m pytest tests/test_blockchain_monitor.py

# Load testing
python scripts/load_test.py
```

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## 🔗 Additional Resources

- **LangChain Documentation**: https://langchain.readthedocs.io/
- **Flash Loan Strategies**: [docs/flash-loan-strategies.md](docs/flash-loan-strategies.md)
- **DEX Integration Guide**: [docs/dex-integration.md](docs/dex-integration.md)
- **Risk Management**: [docs/risk-management.md](docs/risk-management.md)

## ⚠️ Disclaimer

This software is for educational and research purposes. Flash loan arbitrage involves significant financial risk. Always:

- Test thoroughly in simulation mode
- Understand the risks involved
- Start with small amounts
- Monitor the system continuously
- Have proper risk management in place

**The developers are not responsible for any financial losses incurred through the use of this software.**

## 📞 Support

For support and questions:

- **Issues**: Create GitHub issue
- **Discussions**: GitHub Discussions
- **Documentation**: Check `docs/` directory
- **Monitoring**: System dashboard at http://localhost:3001 