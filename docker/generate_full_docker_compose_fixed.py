#!/usr/bin/env python3
"""
Generate complete Docker Compose configuration for MCP agents
Extends existing MCP architecture with full orchestration system
"""

import json
import os
from typing import Dict, List, Any

# Agent role definitions matching your MCP server structure
AGENT_ROLES: Dict[str, Dict[str, Any]] = {
    "code_indexers": {
        "count": 8,
        "port_start": 3101,
        "description": "Full repo understanding and code analysis",
        "mcp_paths": [
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/task_management",
            "/app/mcp_servers/utilities",
            "/app/mcp_servers/scripts",
            "/app/mcp_servers/ai_integration",
            "/app/mcp_servers/market_analysis",
            "/app/mcp_servers/data_providers",
            "/app/mcp_servers/monitoring"
        ]
    },
    "builders": {
        "count": 10,
        "port_start": 3121,
        "description": "Project scaffolding and build agents",
        "mcp_paths": [
            "/app/mcp_servers/production",
            "/app/mcp_servers/foundry_integration",
            "/app/mcp_servers/blockchain_integration",
            "/app/mcp_servers/execution",
            "/app/mcp_servers/utilities",
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/task_management",
            "/app/mcp_servers/scripts",
            "/app/mcp_servers/quality",
            "/app/mcp_servers/ai_integration"
        ]
    },
    "test_writers": {
        "count": 10,
        "port_start": 3141,
        "description": "Unit and integration test creation",
        "mcp_paths": [
            "/app/mcp_servers/quality",
            "/app/mcp_servers/monitoring",
            "/app/mcp_servers/execution",
            "/app/mcp_servers/foundry_integration",
            "/app/mcp_servers/blockchain_integration",
            "/app/mcp_servers/dex_services",
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/utilities",
            "/app/mcp_servers/risk_management",
            "/app/mcp_servers/recovery"
        ]
    },
    "executors": {
        "count": 15,
        "port_start": 3161,
        "description": "Build run verification agents",
        "mcp_paths": [
            "/app/mcp_servers/execution",
            "/app/mcp_servers/blockchain_integration",
            "/app/mcp_servers/foundry_integration",
            "/app/mcp_servers/dex_services",
            "/app/mcp_servers/market_analysis",
            "/app/mcp_servers/data_providers",
            "/app/mcp_servers/production",
            "/app/mcp_servers/orchestration",
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/risk_management",
            "/app/mcp_servers/monitoring",
            "/app/mcp_servers/recovery",
            "/app/mcp_servers/utilities",
            "/app/mcp_servers/task_management",
            "/app/mcp_servers/ai_integration"
        ]
    },
    "coordinators": {
        "count": 10,
        "port_start": 3181,
        "description": "Middle-layer routing and coordination",
        "mcp_paths": [
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/orchestration",
            "/app/mcp_servers/task_management",
            "/app/mcp_servers/monitoring",
            "/app/mcp_servers/production",
            "/app/mcp_servers/utilities",
            "/app/mcp_servers/ai_integration",
            "/app/mcp_servers/risk_management",
            "/app/mcp_servers/recovery",
            "/app/mcp_servers/quality"
        ]
    },
    "planners": {
        "count": 5,
        "port_start": 3201,
        "description": "Long-term project strategy and planning",
        "mcp_paths": [
            "/app/mcp_servers/orchestration",
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/ai_integration",
            "/app/mcp_servers/production",
            "/app/mcp_servers/task_management"
        ]
    },
    "fixers": {
        "count": 10,
        "port_start": 3211,
        "description": "Self-healing and error fixing",
        "mcp_paths": [
            "/app/mcp_servers/recovery",
            "/app/mcp_servers/monitoring",
            "/app/mcp_servers/quality",
            "/app/mcp_servers/risk_management",
            "/app/mcp_servers/ai_integration",
            "/app/mcp_servers/utilities",
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/execution",
            "/app/mcp_servers/foundry_integration",
            "/app/mcp_servers/blockchain_integration"
        ]
    },
    "ui_coders": {
        "count": 10,
        "port_start": 3231,
        "description": "Frontend and design implementation",
        "mcp_paths": [
            "/app/mcp_servers/ui",
            "/app/mcp_servers/monitoring",
            "/app/mcp_servers/production",
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/ai_integration",
            "/app/mcp_servers/utilities",
            "/app/mcp_servers/task_management",
            "/app/mcp_servers/quality",
            "/app/mcp_servers/orchestration",
            "/app/mcp_servers/data_providers"
        ]
    },
    "reviewers": {
        "count": 15,
        "port_start": 3251,
        "description": "Code review and quality assurance",
        "mcp_paths": [
            "/app/mcp_servers/quality",
            "/app/mcp_servers/monitoring",
            "/app/mcp_servers/ai_integration",
            "/app/mcp_servers/coordination",
            "/app/mcp_servers/production",
            "/app/mcp_servers/utilities",
            "/app/mcp_servers/risk_management",
            "/app/mcp_servers/recovery",
            "/app/mcp_servers/execution",
            "/app/mcp_servers/foundry_integration",
            "/app/mcp_servers/blockchain_integration",
            "/app/mcp_servers/dex_services",
            "/app/mcp_servers/market_analysis",
            "/app/mcp_servers/orchestration",
            "/app/mcp_servers/task_management"
        ]
    },
    "admins": {
        "count": 1,
        "port_start": 3301,
        "description": "Top-level control and administration",
        "mcp_paths": [
            "/app/mcp_servers/orchestration"
        ]
    }
}

def generate_docker_compose_yaml():
    """Generate complete docker-compose.yml with all MCP agents"""
    
    compose_content = """version: '3.9'

services:
  # ===== CORE INFRASTRUCTURE =====
  # Central MCP Coordinator Hub
  mcp-coordinator:
    build:
      context: .
      dockerfile: docker/Dockerfile.coordinator
    container_name: mcp-coordinator-hub
    ports:
      - "3000:3000"  # Main coordination API
      - "8080:8080"  # Dashboard/UI
    environment:
      - NODE_ENV=production
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://postgres:password@postgres:5432/mcp_coordination
      - RABBITMQ_URL=amqp://rabbitmq:5672
      - TOTAL_AGENTS=10
    volumes:
      - ./shared_project:/app/project
      - ./logs/coordinator:/app/logs
      - ./config:/app/config
      - ./mcp_servers:/app/mcp_servers
    networks:
      - mcpnet
    depends_on:
      - redis
      - postgres
      - rabbitmq
    restart: unless-stopped

  # Message Bus - RabbitMQ
  rabbitmq:
    image: rabbitmq:3-management
    container_name: mcp-rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"  # Management UI
    environment:
      - RABBITMQ_DEFAULT_USER=mcp_admin
      - RABBITMQ_DEFAULT_PASS=mcp_secure_2025
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - mcpnet
    restart: unless-stopped

  # Shared Memory - Redis
  redis:
    image: redis:7-alpine
    container_name: mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - mcpnet
    restart: unless-stopped

  # Database - PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: mcp-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=mcp_coordination
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - mcpnet
    restart: unless-stopped

  # Configuration Service
  etcd:
    image: quay.io/coreos/etcd:v3.5.0
    container_name: mcp-etcd
    ports:
      - "2379:2379"
      - "2380:2380"
    environment:
      - ETCD_NAME=etcd0
      - ETCD_INITIAL_ADVERTISE_PEER_URLS=http://etcd:2380
      - ETCD_LISTEN_PEER_URLS=http://0.0.0.0:2380
      - ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:2379
      - ETCD_ADVERTISE_CLIENT_URLS=http://etcd:2379
      - ETCD_INITIAL_CLUSTER=etcd0=http://etcd:2380
    volumes:
      - etcd_data:/etcd-data
    networks:
      - mcpnet
    restart: unless-stopped

"""

    # Generate all MCP agents
    for role, config in AGENT_ROLES.items():
        compose_content += f"  # ===== {role.upper().replace('_', ' ')} ({config['count']} agents) =====\n"
        
        for i in range(1, config['count'] + 1):
            port = config['port_start'] + i - 1
            mcp_path = config['mcp_paths'][(i - 1) % len(config['mcp_paths'])]
            
            compose_content += f"""  {role.rstrip('s')}-{i}:
    build:
      context: .
      dockerfile: docker/Dockerfile.mcp-agent
      args:
        AGENT_TYPE: {role.rstrip('s')}
        AGENT_ID: {i}
    container_name: mcp-{role.rstrip('s')}-{i}
    ports: ["{port}:3000"]
    environment:
      - AGENT_ROLE={role.rstrip('s')}
      - AGENT_ID={i}
      - COORDINATOR_URL=http://mcp-coordinator:3000
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://rabbitmq:5672
      - ETCD_URL=http://etcd:2379
      - MCP_SERVER_PATH={mcp_path}
      - ENABLE_FLASH_LOAN={'true' if 'executor' in role else 'false'}
      - ADMIN_PRIVILEGES={'true' if 'admin' in role else 'false'}
    volumes:
      - ./shared_project:/app/project
      - ./mcp_servers:/app/mcp_servers
      - ./logs/agents:/app/logs
      - ./config:/app/config
    networks: [mcpnet]
    depends_on: [mcp-coordinator]
    restart: unless-stopped

"""

    # Add monitoring and observability
    compose_content += """  # ===== MONITORING & OBSERVABILITY =====
  grafana:
    image: grafana/grafana:latest
    container_name: mcp-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=mcp_admin_2025
      - GF_INSTALL_PLUGINS=redis-datasource,postgres-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning
    networks: [mcpnet]
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: mcp-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks: [mcpnet]
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: mcp-jaeger
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks: [mcpnet]
    restart: unless-stopped

  # Load Balancer
  nginx:
    image: nginx:alpine
    container_name: mcp-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./logs/nginx:/var/log/nginx
    networks: [mcpnet]
    depends_on: [mcp-coordinator]
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
  rabbitmq_data:
  grafana_data:
  prometheus_data:
  etcd_data:

networks:
  mcpnet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

"""
    
    return compose_content

def generate_agent_manifest():
    """Generate agent manifest for coordination"""
    manifest = {
        "version": "2.0.0",
        "generated_at": "2025-01-11T21:50:00Z",
        "total_agents": sum(config['count'] for config in AGENT_ROLES.values()),
        "agent_roles": {}
    }
    
    for role, config in AGENT_ROLES.items():
        agents = []
        for i in range(1, config['count'] + 1):
            port = config['port_start'] + i - 1
            mcp_path = config['mcp_paths'][(i - 1) % len(config['mcp_paths'])]
            
            agents.append({
                "id": i,
                "name": f"{role.rstrip('s')}-{i}",
                "container_name": f"mcp-{role.rstrip('s')}-{i}",
                "port": port,
                "url": f"http://localhost:{port}",
                "mcp_server_path": mcp_path,
                "role": role.rstrip('s'),
                "description": config['description'],
                "capabilities": get_agent_capabilities(role),
                "priority": get_agent_priority(role)
            })
        
        manifest["agent_roles"][role] = {
            "count": config['count'],
            "description": config['description'],
            "port_range": f"{config['port_start']}-{config['port_start'] + config['count'] - 1}",
            "agents": agents
        }
    
    return manifest

def get_agent_capabilities(role: str) -> List[str]:
    """Get capabilities for each agent role"""
    capabilities_map = {
        "code_indexers": [
            "code_analysis", "repo_understanding", "pattern_recognition",
            "dependency_mapping", "architecture_analysis"
        ],
        "builders": [
            "project_scaffolding", "compilation", "build_automation",
            "dependency_management", "deployment_preparation"
        ],
        "test_writers": [
            "unit_testing", "integration_testing", "test_automation",
            "coverage_analysis", "test_reporting"
        ],
        "executors": [
            "build_execution", "verification", "deployment",
            "flash_loan_execution", "contract_interaction"
        ],
        "coordinators": [
            "task_routing", "agent_coordination", "workflow_management",
            "resource_allocation", "status_monitoring"
        ],
        "planners": [
            "strategy_planning", "roadmap_creation", "resource_planning",
            "risk_assessment", "timeline_management"
        ],
        "fixers": [
            "error_detection", "auto_fixing", "system_healing",
            "recovery_procedures", "debugging"
        ],
        "ui_coders": [
            "frontend_development", "ui_design", "user_experience",
            "responsive_design", "dashboard_creation"
        ],
        "reviewers": [
            "code_review", "quality_assurance", "security_audit",
            "performance_analysis", "compliance_check"
        ],
        "admins": [
            "system_administration", "global_control", "security_management",
            "policy_enforcement", "system_monitoring"
        ]
    }
    
    return capabilities_map.get(role, [])

def get_agent_priority(role: str) -> str:
    """Get priority level for each agent role"""
    priority_map = {
        "code_indexers": "high",
        "builders": "high", 
        "test_writers": "medium",
        "executors": "critical",
        "coordinators": "high",
        "planners": "medium",
        "fixers": "high",
        "ui_coders": "low",
        "reviewers": "medium",
        "admins": "critical"
    }
    
    return priority_map.get(role, "medium")

def main():
    """Generate all Docker orchestration files"""
    print("🚀 Generating Docker orchestration system for MCP agents...")
    
    # Ensure directories exist
    os.makedirs("docker", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    os.makedirs("sql", exist_ok=True)
    os.makedirs("shared_project", exist_ok=True)
    os.makedirs("logs/coordinator", exist_ok=True)
    os.makedirs("logs/agents", exist_ok=True)
    
    # Generate docker-compose.yml
    print("📝 Generating docker-compose.yml...")
    compose_content = generate_docker_compose_yaml()
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    
    # Generate agent manifest
    print("📋 Generating agent manifest...")
    manifest = generate_agent_manifest()
    with open("config/agent_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Generate summary report
    total_agents = sum(config['count'] for config in AGENT_ROLES.values())
    print(f"\n✅ Generated Docker orchestration system:")
    print(f"   • Total MCP Agents: {total_agents}")
    print(f"   • Agent Roles: {len(AGENT_ROLES)}")
    print(f"   • Port Range: 3101-{3301}")
    print(f"   • Infrastructure Services: 7")
    
    print("\n📊 Agent Distribution:")
    for role, config in AGENT_ROLES.items():
        print(f"   • {role.replace('_', ' ').title()}: {config['count']} agents")
    
    print(f"\n🌐 Generated files:")
    print(f"   • docker-compose.yml")
    print(f"   • config/agent_manifest.json")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. Create Docker images: docker build -f docker/Dockerfile.coordinator -t mcp-coordinator .")
    print(f"   2. Start infrastructure: docker-compose up -d redis postgres rabbitmq etcd")
    print(f"   3. Start coordinator: docker-compose up -d mcp-coordinator")
    print(f"   4. Start all agents: docker-compose up -d")
    print(f"   5. Monitor system: docker-compose logs -f mcp-coordinator")

if __name__ == "__main__":
    main()
