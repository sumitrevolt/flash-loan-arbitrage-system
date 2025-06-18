# 🚀 Optimized Docker Setup for MCP Flash Loan System

## Overview

This optimized Docker configuration provides a production-ready setup for your Flash Loan Arbitrage system with:
- **5 Core MCP Servers** (each in separate containers)
- **3 Infrastructure Services** (Redis, PostgreSQL, RabbitMQ)
- **2 Monitoring Services** (Prometheus, Grafana)
- **2 Optional Services** (Dashboard UI, Discord Bot)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network (mcpnet)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Infrastructure Layer:                                      │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐                   │
│  │  Redis  │ │ PostgreSQL│ │ RabbitMQ │                   │
│  └────┬────┘ └─────┬────┘ └─────┬────┘                   │
│       └────────────┼────────────┘                         │
│                    │                                       │
│  MCP Servers Layer:│                                       │
│  ┌─────────────────▼──────────────┐                      │
│  │      MCP Coordinator (3000)     │                      │
│  └────────────┬───────────────────┘                      │
│               │                                           │
│  ┌────────────┼────────────┬──────────┬─────────────┐   │
│  ▼            ▼            ▼          ▼             ▼   │
│┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐│
││Arbitrage ││Flash Loan││   Risk   ││   DEX    ││Dashboard ││
││ Detector ││ Executor ││ Manager  ││ Monitor  ││   UI     ││
││  (3001)  ││  (3002)  ││  (3003)  ││  (3004)  ││  (8080)  ││
│└──────────┘└──────────┘└──────────┘└──────────┘└──────────┘│
│                                                             │
│  Monitoring Layer:                                          │
│  ┌────────────┐ ┌─────────┐                               │
│  │ Prometheus │ │ Grafana │                               │
│  │   (9090)   │ │  (3005) │                               │
│  └────────────┘ └─────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- PowerShell (Windows) or Bash (Linux/Mac)
- At least 8GB RAM available
- Ports 3000-3005, 5432, 6379, 8080, 9090, 15672 available

### 1. Start the System

```powershell
# Windows PowerShell
.\Start-Optimized-Docker.ps1

# With clean start (removes old containers)
.\Start-Optimized-Docker.ps1 -Clean

# Skip building images
.\Start-Optimized-Docker.ps1 -NoBuild
```

### 2. Verify Services

Check all services are running:
```bash
docker-compose -f docker/compose/docker-compose.optimized.yml ps
```

### 3. Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| MCP Coordinator | http://localhost:3000 | Central orchestration |
| Arbitrage Detector | http://localhost:3001 | Finds arbitrage opportunities |
| Flash Loan Executor | http://localhost:3002 | Executes flash loan trades |
| Risk Manager | http://localhost:3003 | Risk assessment and limits |
| DEX Monitor | http://localhost:3004 | Monitors DEX prices |
| Dashboard | http://localhost:8080 | Web UI for monitoring |
| Prometheus | http://localhost:9090 | Metrics collection |
| Grafana | http://localhost:3005 | Metrics visualization (admin/admin) |
| RabbitMQ | http://localhost:15672 | Message queue UI (admin/admin) |

## Configuration

### Environment Variables

Create a `docker/.env` file with:

```env
# PostgreSQL
POSTGRES_PASSWORD=your_secure_password

# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASS=your_secure_password

# Grafana
GRAFANA_PASSWORD=your_secure_password

# Blockchain
PRIVATE_KEY=your_wallet_private_key
RPC_URL=https://polygon-rpc.com

# Risk Limits
MAX_POSITION_SIZE=10000
MAX_GAS_PRICE=500

# Discord Bot (optional)
DISCORD_TOKEN=your_bot_token
```

### Customizing Services

Edit `docker/compose/docker-compose.optimized.yml` to:
- Add/remove services
- Change resource limits
- Modify port mappings
- Add environment variables

## Monitoring

### View Logs
```bash
# All services
docker-compose -f docker/compose/docker-compose.optimized.yml logs -f

# Specific service
docker-compose -f docker/compose/docker-compose.optimized.yml logs -f mcp-coordinator
```

### Health Checks
```bash
# Check coordinator health
curl http://localhost:3000/health

# View Prometheus targets
curl http://localhost:9090/api/v1/targets
```

### Grafana Dashboards

1. Access Grafana at http://localhost:3005
2. Login with admin/admin (or your configured password)
3. Import dashboards from `docker/compose/config/grafana/dashboards/`

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   netstat -ano | findstr :3000
   
   # Kill process
   taskkill /PID <PID> /F
   ```

2. **Container won't start**
   ```bash
   # Check logs
   docker-compose -f docker/compose/docker-compose.optimized.yml logs <service-name>
   
   # Rebuild image
   docker-compose -f docker/compose/docker-compose.optimized.yml build --no-cache <service-name>
   ```

3. **Network issues**
   ```bash
   # Recreate network
   docker network rm mcpnet
   docker network create mcpnet
   ```

### Reset Everything
```powershell
# Complete cleanup
docker-compose -f docker/compose/docker-compose.optimized.yml down -v
docker network prune -f
docker volume prune -f
.\Start-Optimized-Docker.ps1 -Clean
```

## Production Deployment

### Security Considerations

1. **Use secrets management** for sensitive data
2. **Enable TLS** for all services
3. **Restrict network access** with firewall rules
4. **Regular backups** of PostgreSQL and Redis data
5. **Monitor resource usage** and set limits

### Scaling

To scale specific services:
```bash
# Scale arbitrage detector to 3 instances
docker-compose -f docker/compose/docker-compose.optimized.yml up -d --scale mcp-arbitrage-detector=3
```

### Resource Limits

Add resource constraints in docker-compose.yml:
```yaml
services:
  mcp-coordinator:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## Development

### Adding New MCP Servers

1. Create server script in `mcp_servers/`
2. Add service definition to `docker-compose.optimized.yml`
3. Update Prometheus configuration
4. Rebuild and restart

### Local Development

Mount local code for hot-reloading:
```yaml
volumes:
  - ./mcp_servers:/app/mcp_servers:ro
  - ./core:/app/core:ro
```

## Support

- Check logs first: `docker-compose logs -f`
- Review this guide
- Check Docker daemon status
- Ensure all ports are available
- Verify environment variables are set

## Next Steps

1. Configure your `.env` file with real values
2. Start the system with `.\Start-Optimized-Docker.ps1`
3. Access the dashboard at http://localhost:8080
4. Monitor metrics in Grafana at http://localhost:3005
5. Begin monitoring for arbitrage opportunities!

---

**Note**: This optimized setup reduces resource usage from 140+ containers to just 10-12 containers while maintaining all essential functionality for flash loan arbitrage operations.
