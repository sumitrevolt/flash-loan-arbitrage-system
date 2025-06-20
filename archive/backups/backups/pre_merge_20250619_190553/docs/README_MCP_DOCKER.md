# 🐳 MCP Servers Docker Setup

Complete Docker containerization of your 21 Model Context Protocol (MCP) servers with infrastructure support, monitoring, and easy management.

## 📋 Overview

This setup provides:
- **21 Containerized MCP Servers** across multiple categories
- **Infrastructure Services**: Redis, PostgreSQL, RabbitMQ
- **Monitoring**: Grafana, Prometheus
- **Health Monitoring**: Automated health checks
- **Management Tools**: Easy start/stop/monitor scripts

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Docker Environment                   │
├─────────────────────────────────────────────────────────────┤
│  🔧 Infrastructure Services                                │
│  ├── Redis (Cache & Message Broker)                        │
│  ├── PostgreSQL (Coordination Database)                    │
│  └── RabbitMQ (Task Queue)                                 │
├─────────────────────────────────────────────────────────────┤
│  🤖 21 MCP Servers                                         │
│  ├── AI Integration (5 servers)                            │
│  ├── Blockchain Integration (6 servers)                    │
│  ├── Coordination (4 servers)                              │
│  ├── Data Providers (2 servers)                            │
│  ├── DEX Services (1 server)                               │
│  ├── EVM Integration (1 server)                            │
│  └── Execution (2 servers)                                 │
├─────────────────────────────────────────────────────────────┤
│  📊 Monitoring & Management                                │
│  ├── Grafana Dashboard                                     │
│  ├── Prometheus Metrics                                    │
│  └── Health Monitoring                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker compose --version

# Make sure you have Python 3.11+
python --version
```

### 2. Launch Everything

```bash
# Simple interactive launcher
python docker/start_mcp_servers.py

# Or use the management script directly
python docker/mcp_server_manager.py start
```

### 3. Access Your Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **MCP Dashboard** | http://localhost:8080 | - |
| **Grafana** | http://localhost:3002 | admin / mcp_admin_2025 |
| **Prometheus** | http://localhost:9090 | - |
| **RabbitMQ** | http://localhost:15672 | mcp_admin / mcp_secure_2025 |

## 📝 MCP Servers List

### 🤖 AI Integration (5 servers)
1. **Context7 Clean** - Port 8001 - Context analysis and management
2. **Grok3** - Port 3003 - Advanced AI coordination
3. **Start Grok3** - Port 8002 - Grok3 launcher service
4. **Copilot** - Port 8003 - AI assistant capabilities
5. **Context7** - Port 8004 - Enhanced context server

### ⛓️ Blockchain Integration (6 servers)
6. **Matic Clean** - Port 8005 - Polygon network integration
7. **Matic** - Port 8006 - Polygon utilities
8. **Foundry** - Port 8007 - Smart contract development
9. **Flash Loan** - Port 8008 - Flash loan coordination
10. **EVM** - Port 8009 - EVM blockchain interactions
11. **Matic Server** - Port 8010 - Polygon server management

### 🎛️ Coordination (4 servers)
12. **Coordinator Enhanced** - Port 3000 - Master coordination
13. **Integration Bridge** - Port 8011 - Cross-service communication
14. **Server Coordinator** - Port 3001 - Server management
15. **Unified Coordinator** - Port 8012 - Unified coordination layer

### 📊 Data Providers (2 servers)
16. **DEX Price** - Port 8013 - DEX price monitoring
17. **Price Oracle** - Port 8014 - Price oracle services

### 🔄 DEX Services (1 server)
18. **DEX Services** - Port 8015 - DEX interaction services

### ⚡ EVM Integration (1 server)
19. **EVM Integration** - Port 8016 - Extended EVM support

### 🎯 Execution (2 servers)
20. **Contract Executor** - Port 3005 - Smart contract execution
21. **Flash Loan Strategist** - Port 3004 - Flash loan strategy

## 🛠️ Management Commands

### Using the Interactive Launcher
```bash
python docker/start_mcp_servers.py
```

### Using the Management Script
```bash
# Build all images
python docker/mcp_server_manager.py build

# Start infrastructure only
python docker/mcp_server_manager.py start --infra-only

# Start all servers
python docker/mcp_server_manager.py start

# Check status
python docker/mcp_server_manager.py status

# Health check
python docker/mcp_server_manager.py health

# View logs
python docker/mcp_server_manager.py logs mcp-grok3

# Stop all
python docker/mcp_server_manager.py stop

# Cleanup everything
python docker/mcp_server_manager.py cleanup --volumes
```

### Using Docker Compose Directly
```bash
# Build images
docker compose -f docker/docker-compose.mcp-servers.yml build

# Start all services
docker compose -f docker/docker-compose.mcp-servers.yml up -d

# View logs
docker compose -f docker/docker-compose.mcp-servers.yml logs -f mcp-grok3

# Stop all services
docker compose -f docker/docker-compose.mcp-servers.yml down
```

## 🔧 Configuration

### Environment Variables
Each MCP server supports these environment variables:

```env
MCP_SERVER_NAME=server-name
MCP_SERVER_FILE=path/to/server.py
MCP_SERVER_PORT=8000
MCP_LOG_LEVEL=INFO
REDIS_URL=redis://redis:6379
POSTGRES_URL=postgresql://postgres:password@postgres:5432/mcp_coordination
```

### Custom Configuration
Modify `docker/docker-compose.mcp-servers.yml` to:
- Change ports
- Add environment variables
- Adjust resource limits
- Add volume mounts

## 📊 Monitoring

### Health Checks
All MCP servers include automated health checks that monitor:
- Process status
- Port availability
- HTTP endpoint responses
- Log file errors
- System resources

### Metrics Collection
- **Prometheus**: Collects metrics from all services
- **Grafana**: Visualizes metrics and provides dashboards
- **Built-in Health**: Custom health check system

### Logs
All logs are centralized in Docker volumes:
```bash
# View all logs
docker compose -f docker/docker-compose.mcp-servers.yml logs

# Follow specific service logs
docker compose -f docker/docker-compose.mcp-servers.yml logs -f mcp-grok3
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check which ports are in use
   netstat -tulpn | grep LISTEN
   
   # Modify ports in docker-compose.mcp-servers.yml
   ```

2. **Memory Issues**
   ```bash
   # Check Docker resource usage
   docker stats
   
   # Adjust memory limits in compose file
   ```

3. **Service Won't Start**
   ```bash
   # Check service logs
   python docker/mcp_server_manager.py logs service-name
   
   # Check health status
   python docker/mcp_server_manager.py health
   ```

4. **Database Connection Issues**
   ```bash
   # Ensure PostgreSQL is running
   docker exec mcp-postgres pg_isready -U postgres
   
   # Check Redis connection
   docker exec mcp-redis redis-cli ping
   ```

### Debug Mode
Enable debug logging by setting:
```env
MCP_LOG_LEVEL=DEBUG
```

## 🔒 Security

### Default Credentials
- **PostgreSQL**: postgres / password
- **RabbitMQ**: mcp_admin / mcp_secure_2025
- **Grafana**: admin / mcp_admin_2025

### Security Best Practices
1. Change default passwords in production
2. Use environment files for secrets
3. Enable TLS for external access
4. Implement proper network segmentation

## 📚 File Structure

```
docker/
├── Dockerfile.mcp-server          # MCP server image
├── docker-compose.mcp-servers.yml # Complete setup
├── mcp_server_manager.py           # Management script
├── start_mcp_servers.py            # Interactive launcher
├── health_check.py                 # Health monitoring
├── identify_mcp_servers.py         # Server discovery
├── entrypoints/
│   └── mcp_server_entrypoint.sh   # Container startup script
└── README_MCP_DOCKER.md           # This file
```

## 🤝 Contributing

1. **Adding New MCP Servers**:
   - Add server definition to docker-compose.yml
   - Update port mappings
   - Test with health checks

2. **Modifying Infrastructure**:
   - Update infrastructure services in compose file
   - Ensure proper dependency management
   - Update monitoring configuration

3. **Improving Management Tools**:
   - Enhance management scripts
   - Add new health check features
   - Improve error handling

## 📋 TODO / Future Enhancements

- [ ] SSL/TLS support for external access
- [ ] Advanced load balancing
- [ ] Auto-scaling based on metrics
- [ ] Backup and restore functionality
- [ ] CI/CD pipeline integration
- [ ] Kubernetes deployment manifests
- [ ] Advanced monitoring dashboards
- [ ] Log aggregation and analysis
- [ ] Performance benchmarking
- [ ] Security scanning integration

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Docker and service logs
3. Use health check tools to diagnose issues
4. Consult individual MCP server documentation

---

**Happy containerizing!** 🐳✨

Your 21 MCP servers are now ready for production deployment with full monitoring, health checks, and easy management tools.
