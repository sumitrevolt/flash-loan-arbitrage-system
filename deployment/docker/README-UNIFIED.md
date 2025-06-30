# Unified Docker Deployment

This directory contains all Docker Compose files, entrypoints, and orchestration scripts for unified MCP and arbitrage system deployment.

## Canonical Files

- **start-unified-system.sh / .ps1**: Launches the unified Docker system (Linux/Windows).
- **docker-compose.unified.yml**: Main Docker Compose file for unified deployment.
- **docker-entrypoint.sh**: Entrypoint script for Docker containers.
- **unified_docker_launcher.ps1**: PowerShell launcher for unified Docker setup.
- **DEPLOYMENT-GUIDE.md**: Comprehensive deployment instructions and troubleshooting.

## Usage

Use the provided launch scripts to start or stop the system. See the deployment guide for advanced options and troubleshooting.

---

Obsolete or redundant Docker Compose files and scripts have been archived or removed as part of the project cleanup.

# Unified Docker Orchestration System

## Overview

The Unified Docker Orchestration System is a comprehensive, production-ready containerized environment that integrates LangChain, AutoGen, and MCP (Model Context Protocol) servers with full infrastructure support. This system provides a complete solution for multi-agent AI coordination, memory management, and scalable service orchestration.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED ORCHESTRATION SYSTEM                 │
├─────────────────────────────────────────────────────────────────┤
│  🎯 Coordination Layer                                          │
│  ├── LangChain Coordinator (Port 8000-8002, 8080)              │
│  └── AutoGen Coordinator (Port 8010-8013)                      │
├─────────────────────────────────────────────────────────────────┤
│  🔧 MCP Server Layer                                            │
│  ├── Supermemory MCP (Port 8100)                               │
│  ├── Context7 MCP (Port 8101)                                  │
│  ├── Filesystem MCP (Port 8102)                                │
│  └── TaskManager MCP (Port 8103)                               │
├─────────────────────────────────────────────────────────────────┤
│  💾 Infrastructure Layer                                        │
│  ├── PostgreSQL (Port 5432)                                    │
│  ├── Redis (Port 6379)                                         │
│  └── RabbitMQ (Port 5672, Management 15672)                    │
├─────────────────────────────────────────────────────────────────┤
│  📊 Monitoring Layer                                            │
│  ├── Prometheus (Port 9090)                                    │
│  ├── Grafana (Port 3000)                                       │
│  ├── Elasticsearch (Port 9200)                                 │
│  └── Kibana (Port 5601)                                        │
├─────────────────────────────────────────────────────────────────┤
│  🌐 Interface Layer                                             │
│  ├── Unified Dashboard (Port 8090)                             │
│  └── Health Checker (Background)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Network Architecture

- **Network**: `flash-loan-network` (172.20.0.0/16)
- **Service Discovery**: DNS-based with static IP allocation
- **Load Balancing**: Built-in Docker Compose load balancing
- **Health Checks**: Comprehensive health monitoring for all services

## Quick Start

### Prerequisites

- **Docker**: Version 20.10+ with Docker Compose
- **System Requirements**:
  - Memory: 8GB+ RAM recommended
  - Storage: 10GB+ available disk space
  - CPU: 4+ cores recommended
- **API Keys**: OpenAI, Anthropic, or Google AI API keys

### Installation

1. **Clone and Navigate**:
   ```bash
   cd deployment/docker
   ```

2. **Configure Environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your API keys and configuration
   ```

3. **Start the System**:
   ```bash
   chmod +x start-unified-system.sh
   ./start-unified-system.sh
   ```

4. **Access Services**:
   - **Unified Dashboard**: http://localhost:8090
   - **LangChain API**: http://localhost:8000
   - **AutoGen API**: http://localhost:8010
   - **Grafana Monitoring**: http://localhost:3000

### Quick Validation

```bash
# Check all services are running
docker compose -f docker-compose.unified.yml ps

# Test LangChain coordinator
curl http://localhost:8000/health

# Test AutoGen coordinator  
curl http://localhost:8010/health

# View system logs
docker compose -f docker-compose.unified.yml logs -f
```

## Service Details

### 🎯 Coordination Services

#### LangChain Coordinator
- **Purpose**: Multi-agent coordination using LangChain framework
- **Endpoints**:
  - `GET /health` - Health check
  - `GET /status` - Detailed system status
  - `POST /tasks` - Task execution
  - `GET /agents` - List available agents
- **Features**:
  - RAG (Retrieval-Augmented Generation)
  - Vector store integration
  - Memory management
  - Tool registry
  - Code interpretation

#### AutoGen Coordinator
- **Purpose**: Multi-agent conversations and coordination
- **Endpoints**:
  - `GET /health` - Health check
  - `GET /service/info` - Service information
  - `POST /service/coordination-test` - Test coordination
  - `GET /service/logs` - Recent logs
- **Features**:
  - Multi-agent conversations
  - Code execution
  - Task delegation
  - Conversation logging

### 🔧 MCP Server Layer

#### Supermemory MCP Server
- **Purpose**: Universal memory across LLMs
- **Port**: 8100
- **Tools**:
  - `add_memory` - Store memories
  - `search_memories` - Semantic search
  - `get_memory` - Retrieve specific memory
  - `list_memories` - List all memories
  - `delete_memory` - Remove memories

#### Context7 MCP Server
- **Purpose**: Library documentation and code examples
- **Port**: 8101
- **Tools**:
  - `resolve-library-id` - Find library ID
  - `get-library-docs` - Retrieve documentation

#### Filesystem MCP Server
- **Purpose**: Safe filesystem operations
- **Port**: 8102
- **Tools**:
  - `read_file` - File reading
  - `write_file` - File creation/modification
  - `list_directory` - Directory listing
  - `search_files` - File search

#### TaskManager MCP Server
- **Purpose**: Task planning and management
- **Port**: 8103
- **Tools**:
  - `request_planning` - Plan tasks
  - `get_next_task` - Retrieve pending tasks
  - `mark_task_done` - Complete tasks
  - `approve_task_completion` - Task approval

### 💾 Infrastructure Services

#### PostgreSQL Database
- **Version**: 15-alpine
- **Purpose**: Primary data storage
- **Features**:
  - Persistent data volumes
  - Health monitoring
  - Connection pooling ready
  - Backup-friendly configuration

#### Redis Cache
- **Version**: 7-alpine
- **Purpose**: Caching and session storage
- **Features**:
  - Password protection
  - Persistent storage
  - Performance optimization
  - Pub/sub capabilities

#### RabbitMQ Message Broker
- **Version**: 3-management-alpine
- **Purpose**: Asynchronous messaging
- **Features**:
  - Management interface (Port 15672)
  - Persistent queues
  - High availability ready
  - Message routing

### 📊 Monitoring Services

#### Prometheus + Grafana
- **Purpose**: Metrics collection and visualization
- **Access**: Grafana at http://localhost:3000
- **Features**:
  - Service metrics
  - Custom dashboards
  - Alerting capabilities
  - Historical data

#### Elasticsearch + Kibana
- **Purpose**: Log aggregation and analysis
- **Access**: Kibana at http://localhost:5601
- **Features**:
  - Centralized logging
  - Log search and analysis
  - Custom dashboards
  - Alerting

## Configuration Guide

### Environment Variables

The system uses a comprehensive `.env` file for configuration. Key sections include:

#### Core API Keys
```bash
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GITHUB_TOKEN=your_github_token_here
```

#### Database Configuration
```bash
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_redis_password_here
RABBITMQ_PASSWORD=your_rabbitmq_password_here
```

#### Service Configuration
```bash
LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
```

### Customization Options

#### Scaling Services
```bash
# Scale LangChain coordinators
docker compose -f docker-compose.unified.yml up -d --scale langchain-coordinator=3

# Scale AutoGen coordinators
docker compose -f docker-compose.unified.yml up -d --scale autogen-coordinator=2
```

#### Resource Limits
Edit `docker-compose.unified.yml` to add resource constraints:
```yaml
services:
  langchain-coordinator:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## Management Commands

### System Management

#### Start System
```bash
./start-unified-system.sh
```

#### Stop System (Preserve Data)
```bash
./stop-unified-system.sh
```

#### Stop System (Clean All Data)
```bash
./stop-unified-system.sh --cleanup
```

#### Force Stop
```bash
./stop-unified-system.sh --force
```

### Service Management

#### View Logs
```bash
# All services
docker compose -f docker-compose.unified.yml logs -f

# Specific service
docker compose -f docker-compose.unified.yml logs -f langchain-coordinator

# Follow specific service
docker compose -f docker-compose.unified.yml logs -f --tail=100 autogen-coordinator
```

#### Restart Services
```bash
# Restart specific service
docker compose -f docker-compose.unified.yml restart langchain-coordinator

# Restart all coordinators
docker compose -f docker-compose.unified.yml restart langchain-coordinator autogen-coordinator
```

#### Scale Services
```bash
# Scale up coordinators
docker compose -f docker-compose.unified.yml up -d --scale langchain-coordinator=2
```

### Health Monitoring

#### Check Service Health
```bash
# Overall system health
curl http://localhost:8000/health
curl http://localhost:8010/health

# Individual service status
docker compose -f docker-compose.unified.yml ps
```

#### Monitor Logs
```bash
# Real-time system logs
tail -f logs/startup.log

# Service-specific logs
docker logs flash-loan-langchain
docker logs flash-loan-autogen
```

## API Documentation

### LangChain Coordinator API

#### Health Check
```bash
GET /health
```
Response:
```json
{
  "status": "healthy",
  "timestamp": 1640995200,
  "services": {
    "memory_manager": "healthy",
    "vector_store": "healthy",
    "tool_registry": "healthy"
  },
  "version": "1.0.0"
}
```

#### Task Execution
```bash
POST /tasks
Content-Type: application/json

{
  "task_type": "code_analysis",
  "description": "Analyze the provided Python code for potential issues",
  "context": {
    "code": "def hello_world(): print('Hello, World!')"
  },
  "agent_type": "code_interpreter"
}
```

### AutoGen Coordinator API

#### Service Information
```bash
GET /service/info
```

#### Coordination Test
```bash
POST /service/coordination-test
```

### MCP Server APIs

#### Supermemory - Add Memory
```bash
POST /tools/add_memory
{
  "content": "Important information to remember",
  "title": "Meeting Notes",
  "tags": ["meeting", "planning"]
}
```

#### Context7 - Get Documentation
```bash
POST /tools/get-library-docs
{
  "context7CompatibleLibraryID": "/vercel/next.js",
  "topic": "routing"
}
```

## Troubleshooting

### Common Issues

#### Services Not Starting
1. **Check Docker Resources**:
   ```bash
   docker system df
   docker system prune -f  # If needed
   ```

2. **Verify Port Availability**:
   ```bash
   netstat -tulpn | grep :8000
   lsof -i :8000  # macOS
   ```

3. **Check Logs**:
   ```bash
   docker compose -f docker-compose.unified.yml logs [service-name]
   ```

#### Database Connection Issues
1. **Verify PostgreSQL Health**:
   ```bash
   docker exec flash-loan-postgres pg_isready -U flash_loan_user
   ```

2. **Check Environment Variables**:
   ```bash
   docker exec flash-loan-langchain env | grep POSTGRES
   ```

#### Memory Issues
1. **Check Available Memory**:
   ```bash
   free -h
   docker stats
   ```

2. **Reduce Resource Usage**:
   - Disable monitoring services temporarily
   - Scale down coordinator replicas
   - Adjust Docker memory limits

#### API Key Issues
1. **Verify API Keys**:
   ```bash
   # Test OpenAI API
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

2. **Check Service Configuration**:
   ```bash
   docker exec flash-loan-langchain env | grep API_KEY
   ```

### Performance Optimization

#### Database Optimization
```sql
-- Connect to PostgreSQL and run
\c flash_loan_db
VACUUM ANALYZE;
REINDEX DATABASE flash_loan_db;
```

#### Redis Optimization
```bash
# Check Redis memory usage
docker exec flash-loan-redis redis-cli INFO memory

# Optimize Redis configuration
docker exec flash-loan-redis redis-cli CONFIG SET maxmemory 512mb
```

#### Service Optimization
1. **Adjust Resource Limits** in `docker-compose.unified.yml`
2. **Scale Services** based on load
3. **Monitor Performance** via Grafana dashboards

### Log Analysis

#### Centralized Logging
Access Kibana at http://localhost:5601 for:
- Service logs aggregation
- Error pattern analysis
- Performance metrics
- Custom dashboards

#### Direct Log Access
```bash
# Service logs
docker logs flash-loan-langchain --tail=100 -f
docker logs flash-loan-autogen --tail=100 -f

# System logs
tail -f deployment/docker/logs/startup.log
tail -f deployment/docker/logs/shutdown.log
```

## Security Considerations

### Network Security
- Services communicate via internal Docker network
- External exposure limited to necessary ports
- Service-to-service authentication via environment variables

### Data Security
- Database credentials via environment variables
- API keys stored securely in `.env` file
- Volume permissions configured for security

### Access Control
- RabbitMQ management interface password protected
- Grafana admin password configurable
- Database access restricted to application services

## Backup and Recovery

### Data Backup
```bash
# Backup PostgreSQL
docker exec flash-loan-postgres pg_dump -U flash_loan_user flash_loan_db > backup.sql

# Backup Redis
docker exec flash-loan-redis redis-cli SAVE
docker cp flash-loan-redis:/data/dump.rdb ./redis-backup.rdb

# Backup volumes
docker run --rm -v flash-loan_postgres_data:/data -v $(pwd):/backup alpine \
    tar czf /backup/postgres-backup.tar.gz -C /data .
```

### System Recovery
```bash
# Restore from backup
./stop-unified-system.sh --cleanup
./start-unified-system.sh

# Restore PostgreSQL
docker exec -i flash-loan-postgres psql -U flash_loan_user flash_loan_db < backup.sql

# Restore Redis
docker cp ./redis-backup.rdb flash-loan-redis:/data/dump.rdb
docker compose -f docker-compose.unified.yml restart redis
```

## Development and Extension

### Adding New MCP Servers
1. **Create Server Configuration** in `docker-compose.unified.yml`
2. **Add Environment Variables** to `.env.template`
3. **Update Health Checks** in management scripts
4. **Document API Endpoints** in this README

### Custom Agent Development
1. **LangChain Agents**: Add to `deployment/docker/langchain/agents/`
2. **AutoGen Agents**: Add to `src/autogen_agents/`
3. **Register Tools**: Update tool registries in respective coordinators

### Monitoring Extensions
1. **Custom Metrics**: Add Prometheus exporters
2. **Dashboards**: Create Grafana dashboard configurations
3. **Alerts**: Configure alerting rules in Prometheus

## Support and Maintenance

### Health Monitoring
- **Automated Health Checks**: Built-in health checker service
- **Monitoring Dashboards**: Grafana at http://localhost:3000
- **Log Analysis**: Kibana at http://localhost:5601
- **Metrics**: Prometheus at http://localhost:9090

### Maintenance Tasks
```bash
# Regular maintenance
docker system prune -f
docker volume prune -f
./stop-unified-system.sh && ./start-unified-system.sh

# Update images
docker compose -f docker-compose.unified.yml pull
docker compose -f docker-compose.unified.yml up -d
```

### Version Management
- **Service Versions**: Defined in `docker-compose.unified.yml`
- **Configuration Versions**: Tracked in environment templates
- **Backup Strategy**: Regular automated backups recommended

---

## License and Support

This unified orchestration system is designed for production use with comprehensive monitoring, security, and management capabilities. For additional support or customization requirements, refer to the individual service documentation or create system-specific modifications following the established patterns.

**System Status**: Production Ready  
**Last Updated**: 2025-06-20  
**Version**: 1.0.0