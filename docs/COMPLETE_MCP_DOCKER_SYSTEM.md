# Complete MCP Docker System Documentation
> Full orchestration system with 21 MCP servers, 10 agents, and enterprise infrastructure

## 🚀 System Overview

The complete MCP Docker system consists of:

### Components (39 containers total)
- **6 Infrastructure Services**: Redis, PostgreSQL, RabbitMQ, etcd, Prometheus, Grafana
- **21 MCP Servers**: Specialized microservices (ports 4000-4020)
- **10 Agents**: Intelligent coordination agents (ports 5000-5009)
- **2 Communication Services**: Discord Bot, Nginx reverse proxy

### Architecture Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    Communication Layer                       │
│              Discord Bot | Nginx Reverse Proxy              │
├─────────────────────────────────────────────────────────────┤
│                      Agent Layer                            │
│    Master | Code Analysis | Build | Test | Execution       │
│    Monitoring | Risk | Recovery | UI | Discord             │
├─────────────────────────────────────────────────────────────┤
│                    MCP Server Layer                         │
│  AI Integration | Blockchain | Coordination | Data Providers│
│  DEX Services | Execution | Foundry | Market Analysis      │
│  Monitoring | Orchestration | Production | Quality         │
│  Recovery | Risk Management | Task Management | UI         │
│  Utilities | Legacy | Scripts | Logging                     │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                       │
│     Redis | PostgreSQL | RabbitMQ | etcd                   │
│           Prometheus | Grafana                              │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- Docker Desktop 4.x or higher
- Docker Compose v2.x
- 16GB RAM minimum (32GB recommended)
- 50GB available disk space
- Windows 10/11, macOS, or Linux

## 🛠️ Quick Start

### 1. Clone and Setup
```bash
# Clone repository
git clone <repository-url>
cd <project-directory>

# Copy environment file
cp docker/.env.example .env

# Edit .env with your values
# IMPORTANT: Set DISCORD_BOT_TOKEN if using Discord integration
```

### 2. Launch System

#### Full System (All 39 containers)
```powershell
# PowerShell
.\Start-Complete-Docker-System.ps1 -Mode full -Build

# Or using docker-compose directly
docker-compose -f docker/compose/docker-compose.complete.yml up -d
```

#### Minimal System (Core services only)
```powershell
.\Start-Complete-Docker-System.ps1 -Mode minimal
```

#### Development Mode (Infrastructure only)
```powershell
.\Start-Complete-Docker-System.ps1 -Mode dev
```

## 📊 Service Details

### MCP Servers (Ports 4000-4020)

| Service | Port | Description | Key Functions |
|---------|------|-------------|---------------|
| master-coordinator | 4000 | Central orchestration hub | Service discovery, health monitoring, command routing |
| ai-integration | 4001 | AI/Copilot integration | LLM integration, code generation |
| blockchain-integration | 4002 | Blockchain operations | Flash loans, DEX integration |
| coordination | 4003 | Service coordination | Inter-service communication |
| data-providers | 4004 | External data sources | Price oracles, market data |
| dex-services | 4005 | DEX integrations | Uniswap, Sushiswap, price feeds |
| execution | 4006 | Transaction execution | Flash loan execution, arbitrage |
| foundry-integration | 4007 | Foundry framework | Smart contract compilation/testing |
| market-analysis | 4008 | Market monitoring | Liquidity analysis, opportunities |
| monitoring | 4009 | System monitoring | Health checks, metrics collection |
| orchestration | 4010 | Workflow orchestration | Complex task coordination |
| production | 4011 | Production services | Live trading operations |
| quality | 4012 | Code quality | Static analysis, testing |
| recovery | 4013 | Error recovery | Self-healing, rollback |
| risk-management | 4014 | Risk assessment | Position limits, exposure |
| task-management | 4015 | Task queue | Job scheduling, distribution |
| ui | 4016 | Dashboard backend | Web UI services |
| utilities | 4017 | Shared utilities | Common functions |
| legacy | 4018 | Legacy support | Backward compatibility |
| scripts | 4019 | Script execution | Automation scripts |
| logging | 4020 | Centralized logging | Log aggregation, analysis |

### Agents (Ports 5000-5009)

| Agent | Port | Role | Responsibilities |
|-------|------|------|------------------|
| master-coordinator | 5000 | Overall coordination | System-wide decisions, resource allocation |
| code-analysis | 5001 | Code quality | Static analysis, vulnerability scanning |
| build | 5002 | Build automation | Compilation, packaging, deployment |
| test | 5003 | Testing | Unit tests, integration tests, e2e |
| execution | 5004 | Task execution | Running jobs, managing workflows |
| monitoring | 5005 | System monitoring | Metrics, alerts, dashboards |
| risk | 5006 | Risk management | Risk assessment, mitigation |
| recovery | 5007 | Error recovery | Failure detection, recovery actions |
| ui | 5008 | UI management | Frontend coordination |
| discord | 5009 | Discord integration | Bot commands, notifications |

## 🌐 Access Points

### Web Interfaces
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **RabbitMQ Management**: http://localhost:15672 (mcp_admin/mcp_secure_2025)
- **Prometheus**: http://localhost:9090
- **MCP Dashboard**: http://localhost:8080

### API Endpoints
- **Master Coordinator**: http://localhost:4000
- **System Status**: http://localhost:4000/status
- **Service List**: http://localhost:4000/servers
- **Agent List**: http://localhost:4000/agents
- **Health Check**: http://localhost:4000/health
- **Metrics**: http://localhost:4000/metrics

## 💬 Discord Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| !status | Get overall system status | `!status` |
| !servers | List all MCP servers | `!servers` |
| !agents | List all agents | `!agents` |
| !execute | Execute command on services | `!execute all status` |
| !restart | Restart a specific service | `!restart server execution` |
| !logs | Get service logs | `!logs mcp-execution 50` |
| !metrics | View system metrics | `!metrics` |
| !alert | Test alert system | `!alert warning` |

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Core Configuration
POSTGRES_USER=mcp_user
POSTGRES_PASSWORD=secure_password_2025
POSTGRES_DB=mcp_system

# Redis Configuration
REDIS_PASSWORD=redis_secure_2025

# RabbitMQ Configuration
RABBITMQ_DEFAULT_USER=mcp_admin
RABBITMQ_DEFAULT_PASS=mcp_secure_2025

# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_METRICS_CHANNEL_ID=channel_id
DISCORD_ALERTS_CHANNEL_ID=channel_id
DISCORD_LOGS_CHANNEL_ID=channel_id

# API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
ETHEREUM_RPC_URL=your_rpc_url
```

### Docker Resources
Recommended Docker Desktop settings:
- CPUs: 8+ cores
- Memory: 16GB+
- Swap: 4GB
- Disk image size: 100GB+

## 📊 Monitoring & Observability

### Grafana Dashboards
1. System Overview - Overall health and performance
2. MCP Servers - Individual server metrics
3. Agent Performance - Agent task processing
4. Infrastructure - Redis, PostgreSQL, RabbitMQ metrics

### Prometheus Metrics
- `mcp_server_health` - Server health status
- `mcp_agent_health` - Agent health status
- `mcp_commands_total` - Total commands processed
- `mcp_response_time_seconds` - Response time histogram
- `agent_tasks_total` - Tasks processed by agents
- `agent_task_duration_seconds` - Task execution duration

### Logging
- Centralized logging via mcp-logging service
- Log aggregation from all containers
- Searchable via Grafana Loki (optional)

## 🛡️ Security Considerations

1. **Network Isolation**: All services communicate via Docker network
2. **Authentication**: Services use API keys and tokens
3. **TLS/SSL**: Nginx provides SSL termination
4. **Secrets Management**: Use Docker secrets for sensitive data
5. **Access Control**: Role-based permissions for agents

## 🔍 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check logs
docker-compose -f docker/compose/docker-compose.complete.yml logs <service-name>

# Restart specific service
docker-compose -f docker/compose/docker-compose.complete.yml restart <service-name>
```

#### Port Conflicts
```bash
# Check port usage
netstat -an | findstr :<port>

# Stop conflicting service or change port in docker-compose
```

#### Memory Issues
```bash
# Check Docker resource usage
docker stats

# Increase Docker Desktop memory allocation
```

### Health Checks
```bash
# Check all service health
curl http://localhost:4000/status

# Individual service health
curl http://localhost:<service-port>/health
```

## 🚀 Advanced Usage

### Scaling Services
```bash
# Scale specific service
docker-compose -f docker/compose/docker-compose.complete.yml up -d --scale mcp-execution=3
```

### Custom Agent Development
```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def on_initialize(self):
        # Initialize your agent
        pass
        
    async def on_task(self, task_type, task_data):
        # Handle tasks
        return {"result": "completed"}
```

### Adding New MCP Server
1. Create server script in `mcp_servers/`
2. Add to `docker-compose.complete.yml`
3. Register in master coordinator
4. Update documentation

## 📦 Backup & Recovery

### Backup Data
```bash
# Backup PostgreSQL
docker exec postgres pg_dump -U mcp_user mcp_system > backup.sql

# Backup Redis
docker exec redis redis-cli --rdb /data/dump.rdb

# Backup volumes
docker run --rm -v mcp_postgres_data:/data -v $(pwd):/backup ubuntu tar cvf /backup/postgres_backup.tar /data
```

### Restore Data
```bash
# Restore PostgreSQL
docker exec -i postgres psql -U mcp_user mcp_system < backup.sql

# Restore Redis
docker cp dump.rdb redis:/data/dump.rdb
docker restart redis
```

## 🔄 Updates & Maintenance

### Update Services
```bash
# Pull latest images
docker-compose -f docker/compose/docker-compose.complete.yml pull

# Recreate containers
docker-compose -f docker/compose/docker-compose.complete.yml up -d --force-recreate
```

### Clean Up
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes (careful!)
docker volume prune
```

## 📞 Support & Contributing

- **Issues**: Report bugs via GitHub Issues
- **Discord**: Join our Discord server for support
- **Contributing**: See CONTRIBUTING.md for guidelines

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

*Last updated: December 2024*
*Version: 1.0.0*
