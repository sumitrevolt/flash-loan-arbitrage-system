# 🚀 Quick Start: Docker MCP Servers

This guide helps you quickly deploy and manage the Docker-based MCP architecture, including 10 MCP agents for flash loan arbitrage.

Launch your entire fleet of 21 MCP servers in containers with one command!

## ⚡ Instant Launch

```bash
# 1. Start everything with the interactive launcher
python docker/start_mcp_servers.py

# 2. Or use the management script directly
python docker/mcp_server_manager.py start
```

## 🔥 What You Get

✅ **21 MCP Servers** containerized and ready  
✅ **Infrastructure**: Redis, PostgreSQL, RabbitMQ  
✅ **Monitoring**: Grafana + Prometheus  
✅ **Health Checks**: Automated monitoring  
✅ **Easy Management**: Interactive tools  

## 📊 Access Your Services

| Service | URL | Purpose |
|---------|-----|---------|
| **MCP Dashboard** | http://localhost:8080 | Central control panel |
| **Grafana** | http://localhost:3002 | Monitoring dashboards |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **RabbitMQ** | http://localhost:15672 | Message queue management |

**Default Credentials:**
- Grafana: `admin` / `mcp_admin_2025`
- RabbitMQ: `mcp_admin` / `mcp_secure_2025`

## 🏆 Your 21 MCP Servers

### 🤖 AI Integration (5 servers)
- Context7 Clean (8001) - Context analysis
- Grok3 (3003) - AI coordination  
- Start Grok3 (8002) - Launcher service
- Copilot (8003) - AI assistant
- Context7 (8004) - Enhanced context

### ⛓️ Blockchain Integration (6 servers)
- Matic Clean (8005) - Polygon integration
- Matic (8006) - Polygon utilities
- Foundry (8007) - Smart contracts
- Flash Loan (8008) - Flash loan coordination
- EVM (8009) - EVM interactions
- Matic Server (8010) - Polygon management

### 🎛️ Coordination (4 servers)
- Coordinator Enhanced (3000) - Master coordination
- Unified Coordinator (8012) - Unified layer

### 📊 Data & Execution (5 servers)
- DEX Price (8013) - Price monitoring
- Price Oracle (8014) - Oracle services
- DEX Services (8015) - DEX interactions
- EVM Integration (8016) - Extended EVM
- Contract Executor (3005) - Smart contract execution

### 🎯 Flash Loan Strategy (1 server)
- Flash Loan Strategist (3004) - Strategy execution

## 🛠️ Management Commands

```bash
# Interactive launcher (recommended for beginners)
python docker/start_mcp_servers.py

# Management script commands
python docker/mcp_server_manager.py build      # Build images
python docker/mcp_server_manager.py start      # Start all
python docker/mcp_server_manager.py status     # Check status
python docker/mcp_server_manager.py health     # Health check
python docker/mcp_server_manager.py logs SERVICE_NAME  # View logs
python docker/mcp_server_manager.py stop       # Stop all
python docker/mcp_server_manager.py cleanup    # Clean up
```

## 🔧 Prerequisites

```bash
# Make sure you have these installed:
docker --version          # Docker Engine
docker compose --version  # Docker Compose
python --version          # Python 3.11+
```

## 📋 File Structure

```
docker/
├── 📄 docker-compose.mcp-servers.yml  # Main config
├── 🐳 Dockerfile.mcp-server           # Server image
├── 🎛️ mcp_server_manager.py            # Management tool
├── 🚀 start_mcp_servers.py             # Interactive launcher
├── 🏥 health_check.py                  # Health monitoring
├── 🔍 identify_mcp_servers.py          # Server discovery
├── 📦 requirements.txt                 # Python dependencies
├── 📚 README_MCP_DOCKER.md             # Full documentation
└── entrypoints/
    └── 🔧 mcp_server_entrypoint.sh     # Container startup
```

## 🔍 Quick Troubleshooting

**Port conflicts?**
```bash
netstat -tulpn | grep LISTEN  # Check ports in use
# Modify ports in docker-compose.mcp-servers.yml
```

**Service won't start?**
```bash
python docker/mcp_server_manager.py logs SERVICE_NAME
python docker/mcp_server_manager.py health
```

**Need to reset everything?**
```bash
python docker/mcp_server_manager.py cleanup --volumes
```

## 🎯 Next Steps

1. **Launch**: `python docker/start_mcp_servers.py`
2. **Monitor**: Check http://localhost:8080 for dashboard
3. **Explore**: Visit Grafana at http://localhost:3002
4. **Test**: Run health checks with the management tool
5. **Scale**: Add more servers by modifying docker-compose.yml

## 🤝 Need Help?

- 📖 Read `docker/README_MCP_DOCKER.md` for detailed docs
- 🔍 Check logs with the management tools
- 🏥 Use health checks to diagnose issues
- 🎛️ Try the interactive launcher for guided setup

---

**🎉 You're ready to run 21 MCP servers in production!** 

Your containerized MCP fleet awaits! 🐳✨
