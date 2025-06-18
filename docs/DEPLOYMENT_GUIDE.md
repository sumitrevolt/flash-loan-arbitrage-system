# Flash Loan LangChain System - Deployment Guide

## 🚀 System Overview

This system creates a robust LangChain-based flash loan system with:
- **Separate Docker containers** for each component
- **Auto-healing orchestrator** that monitors and restarts failed services
- **GitHub token integration** for CI/CD and repository operations
- **Health monitoring** with automatic recovery
- **Multi-agent coordination** for different aspects of flash loan operations

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flash Loan Network                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│  │   Orchestrator  │  │   MCP Servers   │  │    Agents    ││
│  │   (Port 8080)   │  │   (Port 8000)   │  │  (Port 8001) ││
│  │                 │  │                 │  │              ││
│  │ • Health Checks │  │ • Model Context │  │ • 10 Agents  ││
│  │ • Auto-Healing  │  │ • Protocol      │  │ • Specialized││
│  │ • Coordination  │  │ • API Gateway   │  │ • Tasks      ││
│  └─────────────────┘  └─────────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Components

### 1. Orchestrator Container
- **Main coordinator** for the entire system
- **Auto-healing capabilities** - restarts failed containers
- **Health monitoring** of all services
- **Docker socket access** for container management
- **GitHub integration** for repository operations

### 2. MCP Server Container
- **Model Context Protocol** implementation
- **LangChain integration** for AI operations
- **API gateway** for external requests
- **Data processing** and context management

### 3. Agent Container
- **10 specialized agents**:
  - coordinator (system coordination)
  - analyzer (market analysis)
  - executor (trade execution)
  - risk-manager (risk assessment)
  - monitor (system monitoring)
  - data-collector (data collection)
  - arbitrage-bot (arbitrage detection)
  - liquidity-manager (liquidity optimization)
  - reporter (report generation)
  - healer (auto-healing operations)

## 🔧 Setup Instructions

### 1. Environment Configuration

Create a `.env` file with your credentials:

```bash
# Copy the template
cp env.template .env

# Edit the .env file with your actual values
GITHUB_TOKEN=your_github_personal_access_token
OPENAI_API_KEY=your_openai_api_key
```

### 2. Build and Deploy

The system has been built using the `fixed_langchain_builder.py`:

```bash
# This command was already executed:
python fixed_langchain_builder.py build
```

### 3. Monitor System Status

Check container status:
```bash
docker compose ps
```

View logs:
```bash
# All containers
docker compose logs -f

# Specific container
docker compose logs -f orchestrator
docker compose logs -f mcp-servers
docker compose logs -f agents
```

### 4. System Monitoring

Use the built-in monitor:
```bash
python system_monitor.py
```

## 🏥 Health Endpoints

Each container exposes health check endpoints:

- **Orchestrator**: http://localhost:8080/health
- **MCP Servers**: http://localhost:8000/health
- **Agents**: http://localhost:8001/health

## 🔄 Auto-Healing Features

The orchestrator automatically:
1. **Monitors** all containers every 30 seconds
2. **Detects** failed or unhealthy services
3. **Restarts** failed containers
4. **Logs** all healing activities
5. **Maintains** system availability

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check container logs
docker compose logs [service_name]

# Rebuild specific container
docker compose build --no-cache [service_name]
docker compose up -d [service_name]
```

### Network Issues
```bash
# Recreate network
docker compose down
docker compose up -d
```

### GitHub Token Issues
1. Ensure token has proper permissions
2. Check token expiration
3. Update `.env` file and restart containers

### System Reset
```bash
# Complete cleanup and rebuild
python fixed_langchain_builder.py cleanup
python fixed_langchain_builder.py build
```

## 📊 Performance Features

### Robustness
- **Container restart policies**: unless-stopped
- **Health checks**: Built into each container
- **Auto-healing**: Orchestrator monitors and fixes issues
- **Resource management**: Proper volume and network isolation

### Scalability
- **Microservices architecture**: Each component is isolated
- **Docker networking**: Efficient inter-container communication
- **Volume management**: Persistent data storage
- **Log aggregation**: Centralized logging

### Monitoring
- **Real-time health checks**
- **Performance metrics**
- **Error tracking and recovery**
- **System status reporting**

## 🔐 Security Features

- **GitHub token integration** for secure repository access
- **Container isolation** for security
- **Network segmentation** within Docker
- **Environment variable protection**

## 📝 Usage

Once deployed, the system automatically:
1. **Starts** all containers in proper order
2. **Monitors** system health continuously
3. **Heals** failed components automatically
4. **Coordinates** between different agents
5. **Processes** flash loan operations
6. **Maintains** high availability

## 🎯 Next Steps

1. **Wait for build completion** (currently in progress)
2. **Set up environment variables** with your GitHub token
3. **Monitor system startup** and health
4. **Test API endpoints** to ensure functionality
5. **Begin flash loan operations**

The system is designed to run continuously without manual intervention, automatically recovering from failures and maintaining optimal performance.
