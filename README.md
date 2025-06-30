# 🚀 Flash Loan Arbitrage System

A comprehensive, AI-powered flash loan arbitrage system with real-time monitoring, multi-agent coordination, and production-ready deployment infrastructure.

## ✨ Features

- **🔄 Automated Arbitrage** - 24/7 flash loan arbitrage across multiple DEXs
- **🤖 AI Coordination** - LangChain + AutoGen multi-agent systems
- **📊 Real-time Monitoring** - Comprehensive dashboard and alerts
- **🛡️ Risk Management** - Advanced circuit breakers and safety mechanisms
- **🔧 MCP Integration** - 80+ Model Context Protocol servers
- **📱 Recovery Tools** - Advanced token recovery and analysis
- **🐳 Docker Ready** - Production deployment with Docker Compose
- **💰 Revenue Tracking** - Detailed profit/loss monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agents     │    │  MCP Servers    │    │  DEX Monitor    │
│  (LangChain/    │◄──►│  (80+ servers)  │◄──►│  (Real-time)    │
│   AutoGen)      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Flash Loan Arbitrage Core                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │
│  │ Opportunity │ │ Risk        │ │ Execution   │ │ Recovery │  │
│  │ Detection   │ │ Management  │ │ Engine      │ │ Tools    │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Monitoring    │
│   (Analytics)   │    │   (Caching)     │    │   Dashboard     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone and navigate to project
cd flash-loan

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (if needed)
npm install
```

### 3. Deploy with Docker

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Services

- **Dashboard**: http://localhost:8080
- **API**: http://localhost:8000
- **Monitoring**: http://localhost:8004
- **Recovery Tools**: `python src/tools/active_recovery_assistant.py`

## 📁 Project Structure

```
flash-loan-arbitrage/
├── 📂 core/                    # Core systems
│   ├── arbitrage/              # Main arbitrage logic
│   ├── contracts/              # Smart contracts
│   ├── coordination/           # System coordination
│   └── scripts/               # Core utility scripts
├── 📂 services/               # Microservices
│   ├── mcp_servers/           # MCP server implementations
│   ├── ai_agents/             # AI agent systems
│   └── monitoring/            # System monitoring
├── 📂 src/                    # Source code
│   ├── tools/                 # 100+ specialized tools
│   ├── mcp/                   # MCP implementations
│   └── tests/                 # Test suites
├── 📂 utils/                  # Utilities
│   └── recovery/              # Recovery tools
├── 📂 deployment/             # Deployment configs
├── 📂 documentation/          # Project documentation
├── 📄 docker-compose.yml      # Docker deployment
├── 📄 requirements.txt        # Python dependencies
└── 📄 .env.example           # Environment template
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Blockchain
POLYGON_RPC_URL=https://polygon-rpc.com
PRIVATE_KEY=your_private_key_here

# AI APIs
OPENAI_API_KEY=sk-your_key_here
GITHUB_TOKEN=ghp_your_token_here

# Trading
MIN_PROFIT_USD=5.0
MAX_GAS_PRICE_GWEI=50

# Security
MAX_DAILY_LOSS_USD=100
ENABLE_CIRCUIT_BREAKER=true
```

### MCP Servers

The system includes 80+ MCP servers for enhanced functionality:

- **Filesystem Server** - File operations
- **Task Manager** - Task coordination
- **Context7** - Documentation retrieval
- **Supermemory** - Memory management
- **Custom Servers** - Arbitrage-specific tools

## 💰 Revenue Generation

### Arbitrage Strategies

1. **Flash Loan Arbitrage** - Cross-DEX price differences
2. **Triangular Arbitrage** - Multi-token cycles
3. **Liquidation Arbitrage** - DeFi protocol liquidations

### Supported DEXs

- Uniswap V2/V3
- SushiSwap
- QuickSwap
- Balancer
- 1inch
- Custom DEX integrations

### Risk Management

- Circuit breakers for loss protection
- Real-time risk scoring
- Position size limits
- Slippage protection

## 🛠️ Tools & Scripts

### Recovery Tools
```bash
# Active recovery assistant
python src/tools/active_recovery_assistant.py

# Advanced token tracer
python src/tools/advanced_token_tracer.py

# Deep address investigation
python src/tools/deep_address_investigator.py
```

### System Management
```bash
# Setup environment
python core/scripts/setup_environment.py

# Monitor system health
python services/monitoring/system_health_checker.py

# Generate reports
python core/scripts/generate_reports.py
```

## 📊 Monitoring & Analytics

### Dashboard Features
- Real-time profit/loss tracking
- Opportunity detection metrics
- System health monitoring
- Risk assessment displays

### Logging
- Structured logging with Unicode support
- Separate logs for transactions, opportunities, and errors
- Real-time log streaming

### Alerts
- Telegram notifications
- Discord webhooks
- Email alerts
- System health alerts

## 🧪 Testing

```bash
# Run all tests
pytest src/tests/

# Test specific components
pytest src/tests/test_arbitrage.py
pytest src/tests/test_mcp_servers.py

# Load testing
python src/tests/load_test_arbitrage.py
```

## 🚀 Deployment

### Production Deployment

#### Kubernetes Deployment
```bash
# Apply Kubernetes configuration
kubectl apply -f deployment.yaml

# Monitor deployment status
kubectl rollout status deployment/arbitrage-bot

# View logs
kubectl logs -l app=arbitrage-bot --tail=100 -f

# Scale the deployment
kubectl scale deployment arbitrage-bot --replicas=5

# Get resource usage
kubectl top pods -l app=arbitrage-bot
```

#### Configuration Reference

Key production environment variables:
```bash
# Web3 Configuration
WEB3_NODE_URL=http://web3-node:8545
WEB3_NODE_TIMEOUT=30
WEB3_MAX_RETRIES=3

# Resource Limits
CPU_LIMIT=2
MEMORY_LIMIT=4Gi

# Monitoring
METRICS_PORT=8080
HEALTH_CHECK_INTERVAL=30s
```

#### Operational Procedures

**Daily Maintenance:**
- Check system health: `kubectl get pods`
- Review logs: `kubectl logs -l app=arbitrage-bot --since=24h`
- Monitor resource usage: `kubectl top pods`

**Emergency Procedures:**
- Rollback: `kubectl rollout undo deployment/arbitrage-bot`
- Scale down: `kubectl scale deployment arbitrage-bot --replicas=0`
- Purge stuck transactions: `kubectl exec -it [POD] -- python purge_transactions.py`

### Manual Deployment

```bash
# Start core services
python core/arbitrage/start_24_7_arbitrage.py

# Start monitoring
python services/monitoring/consolidated_monitoring_server.py

# Start MCP servers
python mcp_servers/start_all_servers.py
```

## 📈 Performance

### System Metrics
- **Opportunity Detection**: < 100ms
- **Risk Assessment**: < 50ms
- **Trade Execution**: < 2 seconds
- **Profit Margin**: 0.5-5% typical
- **Success Rate**: 85%+ in optimal conditions

### Hardware Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended
- **Storage**: 50GB+ for logs and data
- **Network**: Stable internet connection

## 🔒 Security

### Best Practices
- Private keys stored securely
- Rate limiting on all external calls
- Circuit breakers for risk management
- Regular security audits

### Risk Mitigation
- Maximum daily loss limits
- Position size restrictions
- Slippage protection
- Emergency shutdown procedures

## 📚 Documentation

- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) - Detailed project organization
- [`API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) - API reference
- [`DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) - Deployment instructions
- [`TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes. Flash loan arbitrage involves financial risk. Use at your own discretion and ensure compliance with local regulations.

---

**🚀 Ready to start generating revenue? Follow the Quick Start guide above!**

---

# Project Setup Guide

For a complete setup and maintenance flow, see `PROJECT_SETUP_GUIDE.md` (to be created). Each major directory now contains a `README.md` describing canonical scripts, files, and usage:

- `scripts/README.md`: Python/PowerShell/Bash scripts for MCP, Docker, ABI organization and maintenance.
- `src/scripts/README.md`: JavaScript scripts for MCP-powered contract setup, deployment, and verification.
- `deployment/docker/README-UNIFIED.md`: Docker Compose, entrypoints, and orchestration scripts for unified deployment.
- `abi/README.md`: Essential ABI files and loader scripts.
- `mcp_servers/README.md`: Optimized MCP servers, AI agents, and orchestration scripts.

Obsolete, duplicate, or backup scripts and files have been archived or removed as part of the project cleanup.