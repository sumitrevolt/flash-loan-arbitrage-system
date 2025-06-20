# Self-Healing AI Coordination System

🚀 **A comprehensive Docker-based coordination system with AI-powered self-healing capabilities**

## Overview

This system orchestrates coordination between multiple MCP (Model Context Protocol) servers and AI agents with advanced self-healing capabilities. It automatically monitors, detects failures, and recovers from issues to ensure high availability and reliability.

## 🌟 Key Features

### Self-Healing Capabilities
- **Automatic Failure Detection**: Monitors all services continuously
- **Intelligent Recovery**: AI-powered diagnosis and healing strategies
- **Resource Optimization**: Monitors CPU, memory, and disk usage
- **Predictive Maintenance**: Prevents issues before they occur
- **Error Pattern Analysis**: Learns from past failures

### Architecture Components

#### 🔧 Infrastructure Services
- **Redis**: Fast caching and pub/sub messaging
- **PostgreSQL**: Persistent data storage
- **RabbitMQ**: Message queuing and coordination
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

#### 🤖 MCP Servers (11 Specialized Servers)
1. **Price Feed Server** (Port 8100) - Real-time price data
2. **Arbitrage Server** (Port 8101) - Arbitrage opportunity detection
3. **Flash Loan Server** (Port 8102) - Flash loan management
4. **DEX Aggregator** (Port 8103) - DEX integration
5. **EVM Server** (Port 8104) - Ethereum Virtual Machine interactions
6. **Foundry Server** (Port 8105) - Smart contract development
7. **Risk Management** (Port 8106) - Risk assessment
8. **Liquidity Monitor** (Port 8107) - Liquidity pool tracking
9. **Compliance Checker** (Port 8108) - Regulatory compliance
10. **Gas Optimizer** (Port 8109) - Transaction cost optimization
11. **Market Analyzer** (Port 8110) - Market trend analysis

#### 🎯 AI Agents (11 Specialized Agents)
1. **Flash Loan Optimizer** (Port 9001) - Optimize flash loan strategies
2. **Risk Manager** (Port 9002) - Risk assessment and management
3. **Arbitrage Detector** (Port 9003) - Cross-DEX arbitrage detection
4. **Transaction Executor** (Port 9004) - Smart transaction execution
5. **Market Analyzer** (Port 9005) - Real-time market analysis
6. **Route Optimizer** (Port 9006) - Transaction path optimization
7. **Compliance Checker** (Port 9007) - Regulatory adherence
8. **Security Analyst** (Port 9008) - Vulnerability scanning
9. **Gas Optimizer** (Port 9009) - Cost minimization
10. **Liquidity Monitor** (Port 9010) - Liquidity pool monitoring
11. **Self-Healing Agent** (Port 8300) - 🔥 **System self-healing and recovery**

#### 🎛️ Main Services
- **Coordination System** (Port 8000) - Central orchestrator
- **Dashboard** (Port 8080) - Web interface

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11+
- 8GB+ RAM recommended
- 20GB+ disk space

### Option 1: Full Self-Healing System (Recommended)
```bash
# Start the complete self-healing system
python self_healing_coordination_launcher.py
```

### Option 2: PowerShell Launcher
```powershell
# Windows PowerShell
.\launch_coordination_system.ps1 -System self-healing

# Or start with tests first
.\launch_coordination_system.ps1 -Action test
```

### Option 3: Test System First
```bash
# Run comprehensive tests
python test_self_healing_system.py
```

## 🧪 Testing

### Quick Test
```bash
python test_self_healing_system.py
```

### Manual Testing Steps
1. **Prerequisites Test**: `.\launch_coordination_system.ps1 -Action test`
2. **Start Test System**: `.\launch_coordination_system.ps1 -System test`
3. **Health Check**: `.\launch_coordination_system.ps1 -Action health`
4. **Full System**: `.\launch_coordination_system.ps1 -System self-healing`

## 📊 Monitoring & Dashboards

### Primary Interfaces
- **System Dashboard**: http://localhost:8080
- **Self-Healing Agent**: http://localhost:8300
- **Coordination API**: http://localhost:8000

### Monitoring Tools
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **RabbitMQ**: http://localhost:15672 (coordination/coordination_pass)

### Health Endpoints
All services expose `/health` endpoints:
- MCP Servers: `http://localhost:810X/health`
- AI Agents: `http://localhost:900X/health`
- Self-Healing: `http://localhost:8300/health`

## 🔧 Configuration

### Environment Variables
Create `.env` file:
```env
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRAGE_PRIVATE_KEY=your_private_key_here
COMPOSE_PROJECT_NAME=coordination_system
```

### Service Configuration
- **MCP Servers**: `unified_mcp_config.json`
- **AI Agents**: `ai_agents_config.json`
- **Docker Compose**: `docker/docker-compose-self-healing.yml`

## 🔥 Self-Healing Features

### Automatic Recovery
The self-healing agent provides:

1. **Health Monitoring**
   - Continuous service health checks
   - Resource usage monitoring
   - Performance metrics collection

2. **Failure Detection**
   - Container status monitoring
   - HTTP endpoint health checks
   - Resource threshold alerts

3. **Automatic Recovery**
   - Service restart with exponential backoff
   - Container recreation for persistent failures
   - Resource optimization when thresholds exceeded

4. **Emergency Procedures**
   - System-wide emergency recovery
   - Critical service prioritization
   - Graceful degradation

### Self-Healing API
```bash
# Check system status
curl http://localhost:8300/system-status

# Trigger healing for specific service
curl -X POST http://localhost:8300/heal-service \
  -H "Content-Type: application/json" \
  -d '{"service_name": "mcp_price_feed"}'

# Emergency system recovery
curl -X POST http://localhost:8300/emergency-healing
```

## 🛠️ Development

### Adding New Services

1. **Add MCP Server**:
   ```yaml
   # In docker-compose-self-healing.yml
   mcp_new_server:
     build:
       context: ..
       dockerfile: docker/Dockerfile.mcp
     environment:
       - SERVER_TYPE=new_server
       - PORT=8111
   ```

2. **Add AI Agent**:
   ```yaml
   ai_agent_new:
     build:
       context: ..
       dockerfile: docker/Dockerfile.agent
     environment:
       - AGENT_TYPE=new_agent
       - PORT=9011
   ```

### Custom Entrypoints
- MCP Servers: `docker/entrypoints/mcp_server_entrypoint.py`
- AI Agents: `docker/entrypoints/ai_agent_entrypoint.py`
- Self-Healing: `docker/entrypoints/self_healing_agent.py`

## 📈 Performance Optimization

### Resource Limits
Services are configured with appropriate resource limits:
- Infrastructure: 512MB-1GB RAM
- MCP Servers: 256-512MB RAM
- AI Agents: 512MB-1GB RAM
- Self-Healing: 1GB RAM

### Scaling
```bash
# Scale specific services
docker compose -f docker/docker-compose-self-healing.yml up -d --scale mcp_price_feed=3
```

## 🔒 Security

### Network Security
- All services run in isolated Docker network
- Internal communication only
- Exposed ports are minimal and necessary

### Data Security
- Environment variables for sensitive data
- No hardcoded secrets
- Volume-based persistent storage

## 🆘 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -an | findstr :8000
   ```

2. **Docker Issues**
   ```bash
   # Reset Docker
   docker system prune -a --volumes
   ```

3. **Memory Issues**
   ```bash
   # Check Docker memory
   docker system df
   ```

### Logs
```bash
# System logs
.\launch_coordination_system.ps1 -Action logs

# Specific service
docker logs coordination_system

# Self-healing logs
docker logs ai_agent_self_healing
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-agent`
3. Test thoroughly: `python test_self_healing_system.py`
4. Submit pull request

## 📜 License

MIT License - See LICENSE file for details

## 🙋‍♂️ Support

- **Issues**: Create GitHub issue
- **Documentation**: Check `/docs` folder
- **Logs**: Check service logs for debugging

---

🌟 **This system provides enterprise-grade reliability with AI-powered self-healing capabilities!**
