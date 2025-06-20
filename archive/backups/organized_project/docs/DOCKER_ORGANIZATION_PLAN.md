# 🐳 Docker Organization Plan for Flash Loan MCP System

## 📋 Executive Summary

This document outlines a comprehensive plan to organize all Docker-related files and configurations for the Flash Loan MCP (Model Context Protocol) system. The plan includes proper structure for Docker setup, MCP server configurations, agent deployments, and inter-container communication architecture.

## 🎯 Objectives

1. **Centralize** all Docker-related files into a well-organized `docker/` directory
2. **Standardize** Dockerfile structures for MCP servers and agents
3. **Implement** robust communication between 10 MCP agents and 21 servers
4. **Enable** easy scaling and management of the distributed system
5. **Ensure** monitoring and observability across all components

## 📁 Proposed Docker Folder Structure

```
docker/
├── compose/                      # All docker-compose files
│   ├── docker-compose.yml        # Main orchestration (10 agents)
│   ├── docker-compose.mcp-servers.yml  # MCP servers setup
│   ├── docker-compose.dev.yml    # Development overrides
│   ├── docker-compose.prod.yml   # Production overrides
│   └── docker-compose.test.yml   # Testing configuration
│
├── dockerfiles/                  # Organized Dockerfile definitions
│   ├── base/                     # Base images
│   │   ├── Dockerfile.python     # Python base for MCP servers
│   │   ├── Dockerfile.node       # Node.js base for coordinators
│   │   └── Dockerfile.gpu        # GPU-enabled base
│   ├── servers/                  # MCP server Dockerfiles
│   │   ├── Dockerfile.mcp-server # Generic MCP server
│   │   ├── Dockerfile.orchestration
│   │   ├── Dockerfile.blockchain
│   │   ├── Dockerfile.data-provider
│   │   └── Dockerfile.ai-integration
│   ├── agents/                   # MCP agent Dockerfiles
│   │   ├── Dockerfile.mcp-agent  # Generic MCP agent
│   │   ├── Dockerfile.code-indexer
│   │   ├── Dockerfile.builder
│   │   ├── Dockerfile.executor
│   │   └── Dockerfile.coordinator
│   └── infrastructure/           # Supporting services
│       ├── Dockerfile.coordinator # Main coordinator
│       ├── Dockerfile.redis
│       └── Dockerfile.prometheus
│
├── mcp-setup/                    # MCP-specific setup files
│   ├── servers/                  # Server configurations by category
│   │   ├── orchestration/
│   │   │   ├── config.json
│   │   │   ├── requirements.txt
│   │   │   └── entrypoint.sh
│   │   ├── blockchain/
│   │   │   ├── config.json
│   │   │   ├── requirements.txt
│   │   │   └── entrypoint.sh
│   │   ├── data-providers/
│   │   │   ├── config.json
│   │   │   ├── requirements.txt
│   │   │   └── entrypoint.sh
│   │   ├── ai-integration/
│   │   │   ├── config.json
│   │   │   ├── requirements.txt
│   │   │   └── entrypoint.sh
│   │   ├── market-analysis/
│   │   ├── execution/
│   │   ├── risk-management/
│   │   ├── ui/
│   │   └── utils/
│   │
│   ├── agents/                   # Agent configurations by type
│   │   ├── code-indexers/
│   │   │   ├── config.json
│   │   │   ├── agent-manifest.json
│   │   │   └── entrypoint.sh
│   │   ├── builders/
│   │   ├── test-writers/
│   │   ├── executors/
│   │   ├── coordinators/
│   │   ├── planners/
│   │   ├── fixers/
│   │   ├── ui-coders/
│   │   ├── reviewers/
│   │   └── admin/
│   │
│   └── templates/                # Templates for new servers/agents
│       ├── mcp-server-template/
│       └── mcp-agent-template/
│
├── configs/                      # Service configurations
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── mcp-routes.conf       # MCP service routing
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts/
│   │       └── mcp-alerts.yml
│   ├── grafana/
│   │   ├── grafana.ini
│   │   └── dashboards/
│   │       ├── mcp-servers.json
│   │       └── mcp-agents.json
│   ├── redis/
│   │   └── redis.conf
│   ├── postgres/
│   │   ├── init.sql
│   │   └── mcp-schema.sql
│   ├── rabbitmq/
│   │   └── rabbitmq.conf
│   └── etcd/
│       └── etcd.conf
│
├── scripts/                      # Management and utility scripts
│   ├── entrypoints/             # Service entrypoint scripts
│   │   ├── mcp_server_entrypoint.sh
│   │   ├── mcp_agent_entrypoint.sh
│   │   └── coordinator_entrypoint.sh
│   ├── health-checks/           # Health monitoring
│   │   ├── health_check.py
│   │   ├── mcp_server_health.py
│   │   └── mcp_agent_health.py
│   ├── management/              # Docker management
│   │   ├── manage_mcp_orchestration.py (moved from root)
│   │   ├── mcp_server_manager.py
│   │   ├── start_mcp_servers.py
│   │   └── scale_agents.sh
│   ├── generators/              # Configuration generators
│   │   ├── generate_docker_compose.py
│   │   ├── create_clean_compose.py
│   │   └── generate_agent_configs.py
│   └── utilities/               # Helper scripts
│       ├── backup_volumes.sh
│       ├── clean_logs.sh
│       └── update_images.sh
│
├── monitoring/                   # Monitoring setup
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── rules/
│   │       ├── mcp_server_rules.yml
│   │       └── mcp_agent_rules.yml
│   ├── grafana/
│   │   └── dashboards/
│   │       ├── mcp-overview.json
│   │       ├── flash-loan-metrics.json
│   │       └── agent-performance.json
│   └── alertmanager/
│       └── alertmanager.yml
│
├── docs/                        # Docker documentation
│   ├── README.md                # Main Docker guide
│   ├── QUICK_START.md           # Quick start guide
│   ├── ARCHITECTURE.md          # System architecture
│   ├── MCP_SETUP.md            # MCP setup guide
│   └── TROUBLESHOOTING.md      # Common issues
│
├── volumes/                     # Persistent data (gitignored)
│   ├── redis_data/
│   ├── postgres_data/
│   ├── etcd_data/
│   ├── prometheus_data/
│   ├── grafana_data/
│   └── mcp_logs/
│
└── .env.example                 # Environment variables template
```

## 🔗 MCP Server-Agent Communication Architecture

### Communication Flow Diagram

```mermaid
graph TB
    subgraph "Docker Network: mcpnet"
        subgraph "Infrastructure Layer"
            RMQ[RabbitMQ<br/>Port 5672]
            REDIS[Redis<br/>Port 6379]
            ETCD[etcd<br/>Port 2379]
            PG[PostgreSQL<br/>Port 5432]
        end
        
        subgraph "Coordination Layer"
            COORD[MCP Coordinator Hub<br/>Port 3000]
            LB[Nginx Load Balancer<br/>Port 80]
        end
        
        subgraph "MCP Servers (Ports 8000-8080)"
            S1[Orchestration Servers<br/>8000-8009]
            S2[Blockchain Servers<br/>8010-8019]
            S3[Data Provider Servers<br/>8020-8029]
            S4[AI Integration Servers<br/>8030-8039]
        end
        
        subgraph "MCP Agents (Ports 3101-3301)"
            A1[Code Indexers<br/>3101-3120]
            A2[Builders<br/>3121-3135]
            A3[Executors<br/>3136-3150]
            A4[Coordinators<br/>3151-3160]
        end
    end
    
    %% Communication Paths
    COORD -.->|Service Discovery| ETCD
    COORD -->|Task Assignment| RMQ
    COORD -->|State Management| REDIS
    COORD -->|Persistence| PG
    
    S1 <-->|Message Bus| RMQ
    S2 <-->|Message Bus| RMQ
    S3 <-->|Message Bus| RMQ
    S4 <-->|Message Bus| RMQ
    
    A1 -->|Subscribe Tasks| RMQ
    A2 -->|Subscribe Tasks| RMQ
    A3 -->|Subscribe Tasks| RMQ
    A4 -->|Subscribe Tasks| RMQ
    
    A1 -.->|Cache Results| REDIS
    A2 -.->|Cache Results| REDIS
    
    LB -->|Route Requests| S1
    LB -->|Route Requests| S2
```

### 📡 Communication Mechanisms

#### 1. Message Bus (RabbitMQ)
Primary communication channel for async task distribution and event propagation.

**Queue Structure:**
```
Exchange: mcp.topic
├── Queue: tasks.code_indexer    → Code Indexer Agents
├── Queue: tasks.builder         → Builder Agents
├── Queue: tasks.executor        → Executor Agents
├── Queue: tasks.coordinator     → Coordinator Agents
├── Queue: events.flash_loan     → Flash Loan Events
├── Queue: events.arbitrage      → Arbitrage Opportunities
└── Queue: events.system         → System Events
```

#### 2. Service Discovery (etcd)
Dynamic service registration and discovery for all MCP components.

```json
{
  "/services/mcp/servers/orchestration/coordinator-1": {
    "host": "mcp-orchestration-1",
    "port": 8000,
    "status": "healthy",
    "capabilities": ["coordination", "task-routing"]
  },
  "/services/mcp/agents/code-indexer/agent-1": {
    "host": "mcp-code-indexer-1", 
    "port": 3101,
    "status": "active",
    "current_task": "index-repo-123"
  }
}
```

#### 3. Shared Memory (Redis)
Fast data sharing and caching between components.

**Redis Key Structure:**
```
mcp:agents:status:<agent_id>          # Agent status
mcp:tasks:pending                     # Pending task queue
mcp:tasks:active:<task_id>           # Active task details
mcp:results:cache:<task_id>          # Cached results
mcp:arbitrage:opportunities          # Live arbitrage data
mcp:flash_loan:pool_states          # Flash loan pool states
```

#### 4. Direct HTTP/gRPC Communication
For synchronous operations and real-time data exchange.

### 🔧 Implementation Details

#### Docker Network Configuration
```yaml
networks:
  mcpnet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.bridge.name: mcp_bridge
```

#### Environment Variables for Communication
```env
# MCP Server Environment
MCP_RABBITMQ_URL=amqp://mcp_admin:mcp_secure_2025@rabbitmq:5672
MCP_REDIS_URL=redis://redis:6379/0
MCP_ETCD_URL=http://etcd:2379
MCP_COORDINATOR_URL=http://mcp-coordinator:3000

# MCP Agent Environment
AGENT_TYPE=code_indexer
AGENT_ID=1
AGENT_RABBITMQ_QUEUE=tasks.code_indexer
AGENT_REDIS_NAMESPACE=mcp:agents:code_indexer:1
```

## 🔄 Migration Steps

### Phase 1: Structure Creation
1. Create the complete folder structure under `docker/`
2. Create `.gitkeep` files in empty directories
3. Set up `.gitignore` for volumes and temporary files

### Phase 2: File Migration
1. Move `docker-compose.yml` → `docker/compose/`
2. Move existing Dockerfiles → `docker/dockerfiles/`
3. Move `monitoring/prometheus.yml` → `docker/configs/prometheus/`
4. Move Docker-related scripts → `docker/scripts/`

### Phase 3: MCP Server Setup
1. Create Dockerfiles for each server category
2. Copy server configurations from `mcp_servers/`
3. Set up volume mounts for server code
4. Configure port mappings based on `server_config.json`

### Phase 4: MCP Agent Setup
1. Generate 10 agent configurations
2. Create agent-specific Dockerfiles
3. Set up agent communication channels
4. Configure resource limits

### Phase 5: Integration & Testing
1. Update all file references to new paths
2. Configure service dependencies
3. Set up health checks
4. Test individual components
5. Test complete system integration

### Phase 6: Documentation
1. Create comprehensive README files
2. Document port mappings
3. Add troubleshooting guides
4. Create architecture diagrams

## 📊 Benefits

1. **Centralization**: All Docker-related files in one location
2. **Scalability**: Easy to scale individual agent types
3. **Modularity**: Each component is independently configurable
4. **Maintainability**: Clear separation of concerns
5. **Monitoring**: Comprehensive monitoring setup
6. **Development**: Easy local development with volume mounts
7. **Communication**: Robust inter-container communication
8. **Service Discovery**: Dynamic service registration/discovery

## 🚀 Next Steps

1. Review and approve this plan
2. Switch to implementation mode
3. Create the folder structure
4. Migrate existing files
5. Create new configuration files
6. Test the setup
7. Deploy and monitor

## 📝 Notes

- All sensitive configuration should use environment variables
- Volumes directory will be gitignored to prevent data commits
- Each service will have its own health check endpoint
- Logging will be centralized through Docker's logging driver
- Backup scripts will be provided for persistent data