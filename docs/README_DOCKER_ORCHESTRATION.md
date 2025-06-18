# 🐳 MCP Docker Orchestration System

## Complete Docker-Based MCP Orchestration with 21 Agents

This repository contains a comprehensive Docker orchestration system for managing 21 MCP (Model Context Protocol) agents specialized for flash loan arbitrage operations. The system implements the best practices outlined in the task specifications.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP ORCHESTRATION SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│  🎯 Central Coordinator Hub (Port 3000)                        │
│  ├── Online MCP Integration (GitHub, Context7, Upstash)        │
│  ├── Docker Agent Coordination                                 │
│  └── Real-time Arbitrage Management                            │
├─────────────────────────────────────────────────────────────────┤
│  📡 Infrastructure Layer                                        │
│  ├── Redis (Shared Memory) - Port 6379                        │
│  ├── PostgreSQL (Persistence) - Port 5432                     │
│  ├── RabbitMQ (Message Bus) - Port 5672                       │
│  ├── etcd (Configuration) - Port 2379                         │
│  ├── Prometheus (Metrics) - Port 9090                         │
│  ├── Grafana (Monitoring) - Port 3001                         │
│  ├── Jaeger (Tracing) - Port 16686                           │
│  └── Nginx (Load Balancer) - Port 80                         │
├─────────────────────────────────────────────────────────────────┤
│  🤖 10 MCP Agents (Ports 3101-3110)                           │
│  ├── Code Indexers (20) - Full repo understanding             │
│  ├── Builders (15) - Project scaffolding & compilation        │
│  ├── Test Writers (10) - Unit & integration tests             │
│  ├── Executors (15) - Build-run-verification                  │
│  ├── Coordinators (10) - Middle-layer routing                 │
│  ├── Planners (5) - Long-term strategy                        │
│  ├── Fixers (10) - Self-healing & debugging                   │
│  ├── UI Coders (10) - Frontend & design                       │
│  ├── Reviewers (15) - Quality assurance                       │
│  └── Admin (1) - Top-level control                            │
└─────────────────────────────────────────────────────────────────┘
```

## ✅ Implementation Features

### Best Approach: Docker + Centralized Coordination + Message Bus ✅

- **Docker Compose with Bridge Network**: All 10 agents in dedicated containers
- **Central MCP Coordinator Hub**: Handles task assignment, monitoring, and state management
- **Message Bus Integration**: RabbitMQ for agent communication and task queuing
- **Shared Memory Layer**: Redis for real-time coordination and caching
- **Persistent Storage**: PostgreSQL for logs, project maps, and coordination data

### Agent Roles & Specialization ✅

| Role | Count | Port Range | Description |
|------|-------|------------|-------------|
| Code Indexers | 20 | 3101-3120 | Full repo understanding & analysis |
| Builders | 15 | 3121-3135 | Project scaffolding & compilation |
| Test Writers | 10 | 3141-3150 | Unit & integration test creation |
| Executors | 15 | 3161-3175 | Build-run-verification & flash loans |
| Coordinators | 10 | 3181-3190 | Middle-layer routing & workflow management |
| Planners | 5 | 3201-3205 | Long-term project strategy & planning |
| Fixers | 10 | 3211-3220 | Self-healing & error fixing |
| UI Coders | 10 | 3231-3240 | Frontend & design implementation |
| Reviewers | 15 | 3251-3265 | Code review & quality assurance |
| Admin | 1 | 3301 | Top-level control & administration |

### Project Memory & Coordination ✅

- **Redis**: Shared memory map for real-time coordination
- **PostgreSQL**: Long-term history, agent registry, task management
- **etcd**: Configuration synchronization across all agents
- **Volume Mounting**: Shared code access with file locking

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11+
   ```

### 1. Generate Orchestration Files

```bash
# Generate all 10 agents and infrastructure
python generate_full_docker_compose.py
```

### 2. Start the Complete System

```bash
# Option 1: Use management script (Recommended)
python manage_mcp_orchestration.py start

# Option 2: Manual startup
python manage_mcp_orchestration.py check      # Check prerequisites
python manage_mcp_orchestration.py build      # Build Docker images
python manage_mcp_orchestration.py start-infra    # Start infrastructure
python manage_mcp_orchestration.py start-coordinator  # Start coordinator
python manage_mcp_orchestration.py start-agents       # Start all agents
```

### 3. Monitor System Status

```bash
# Check system status
python manage_mcp_orchestration.py status

# Follow logs
python manage_mcp_orchestration.py logs --follow

# Follow specific service logs
python manage_mcp_orchestration.py logs --service mcp-coordinator --follow
```

## 📊 Monitoring & Observability

### Access Points

- **Main Dashboard**: http://localhost:8080
- **Grafana Monitoring**: http://localhost:3001 (admin/mcp_admin_2025)
- **Prometheus Metrics**: http://localhost:9090
- **RabbitMQ Management**: http://localhost:15672 (mcp_admin/mcp_secure_2025)
- **Jaeger Tracing**: http://localhost:16686

### Key Metrics

- **Agent Health**: Real-time status of all 10 agents
- **Task Distribution**: Load balancing across agent types
- **Coordination Efficiency**: Success rates and performance
- **Flash Loan Opportunities**: Detection and execution metrics
- **System Performance**: Resource usage and optimization

## 🔧 Management Commands

### Selective Agent Management

```bash
# Start specific agent types
python manage_mcp_orchestration.py start-agents --agent-type executor --count 5

# Start specific roles
python manage_mcp_orchestration.py start-agents --agent-type code_indexer --count 10

# Monitor specific agents
docker-compose logs -f mcp-executor-1 mcp-executor-2
```

### System Scaling

```bash
# Scale specific services
docker-compose up -d --scale mcp-executor-1=3

# Add more agents (modify docker-compose.yml)
# Then restart
docker-compose up -d
```

### Troubleshooting

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs mcp-coordinator
docker-compose logs mcp-executor-1

# Restart failing services
docker-compose restart mcp-coordinator

# Full system restart
python manage_mcp_orchestration.py stop
python manage_mcp_orchestration.py start
```

## 🎯 Flash Loan Arbitrage Integration

The system is specifically designed for flash loan arbitrage with these features:

### Real-time Price Monitoring
- **Data Providers**: Multiple agents monitoring DEX prices
- **Opportunity Detection**: AI-powered arbitrage identification
- **Risk Assessment**: Automated risk evaluation and filtering

### Execution Pipeline
1. **Code Indexers**: Analyze contract code and integration patterns
2. **Planners**: Strategy development and risk assessment
3. **Builders**: Compile and prepare execution contracts
4. **Test Writers**: Validate execution logic and edge cases
5. **Executors**: Deploy and execute flash loan transactions
6. **Reviewers**: Post-execution analysis and optimization
7. **Fixers**: Handle any issues or recovery scenarios

### Integration with Online MCPs
- **GitHub MCP**: Automatic documentation and code management
- **Context7 MCP**: DEX integration documentation and verification
- **Upstash MCP**: Real-time data caching and coordination

## 📁 File Structure

```
.
├── docker-compose.yml              # Main orchestration file
├── manage_mcp_orchestration.py     # Management CLI
├── generate_full_docker_compose.py # Generation script
├── online_mcp_coordinator.py       # Enhanced coordinator
├── docker/
│   ├── Dockerfile.coordinator      # Coordinator image
│   └── Dockerfile.mcp-agent       # Agent base image
├── config/
│   ├── agent_manifest.json        # Agent configuration
│   ├── redis.conf                 # Redis configuration
│   └── prometheus.yml             # Monitoring configuration
├── sql/
│   └── init.sql                   # Database schema
├── mcp_servers/                   # Existing MCP server infrastructure
├── logs/                          # System logs
└── shared_project/                # Shared code volume
```

## 🔐 Security Features

- **Network Isolation**: Docker bridge network with controlled access
- **Authentication**: Secured services with dedicated credentials
- **Resource Limits**: Container resource constraints and monitoring
- **Health Checks**: Automated health monitoring and recovery
- **Audit Logging**: Comprehensive activity logging and tracing

## 📈 Performance Optimization

### Load Balancing
- **Nginx**: Frontend load balancing across agents
- **Task Distribution**: Intelligent workload distribution
- **Resource Monitoring**: Real-time performance tracking

### Caching Strategy
- **Redis**: Shared memory for coordination
- **Local Caching**: Agent-level caching for performance
- **Database Optimization**: Indexed queries and connection pooling

### Scalability
- **Horizontal Scaling**: Easy addition of new agents
- **Service Mesh**: Microservices architecture
- **Auto-scaling**: Resource-based scaling triggers

## 🛠️ Development & Extension

### Adding New Agent Types

1. **Define Role**: Add to `AGENT_ROLES` in `generate_full_docker_compose.py`
2. **Create Implementation**: Add MCP server in `mcp_servers/`
3. **Update Dockerfile**: Modify `docker/Dockerfile.mcp-agent`
4. **Regenerate**: Run `python generate_full_docker_compose.py`

### Custom MCP Integrations

1. **Add Server**: Implement in `mcp_servers/`
2. **Update Configuration**: Modify `unified_online_mcp_config.json`
3. **Extend Coordinator**: Update `online_mcp_coordinator.py`
4. **Test Integration**: Use `manage_mcp_orchestration.py status`

## 🎉 Success Metrics

The system successfully implements:

✅ **10 MCP Agents** in specialized roles
✅ **Docker Compose Orchestration** with bridge networking
✅ **Centralized Coordination** with message bus integration
✅ **Shared Memory & Persistence** (Redis + PostgreSQL)
✅ **Volume Mounting** with file locking
✅ **Comprehensive Monitoring** (Prometheus + Grafana)
✅ **Load Balancing** with Nginx
✅ **Health Checks** and auto-recovery
✅ **Management CLI** for operations
✅ **Flash Loan Integration** ready

## 📞 Support & Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 3000-3301, 5432, 6379, etc. are available
2. **Memory Requirements**: System requires ~8GB RAM for all agents
3. **Docker Daemon**: Ensure Docker is running and accessible
4. **File Permissions**: Check shared volume permissions

### Getting Help

- Check logs: `python manage_mcp_orchestration.py logs`
- System status: `python manage_mcp_orchestration.py status`
- Container health: `docker-compose ps`
- Resource usage: `docker stats`

---

**🚀 Your 10-agent MCP orchestration system is ready for flash loan arbitrage operations!**
## Quick Start

```bash
cp docker/.env.example docker/.env
docker compose -f docker/compose/docker-compose.infra.yml         up -d --build
docker compose -f docker/compose/docker-compose.mcp-servers.yml   up -d --build
docker compose -f docker/compose/docker-compose.mcp-agents.yml    up -d --build
docker compose -f docker/compose/docker-compose.bot.yml           up -d --build
```

Note: All services share the network `mcpnet`.
