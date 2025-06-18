#!/usr/bin/env python3
"""
Docker Compose Generator - Consolidated Version
===============================================

This file was created by merging the following sources:
- generate_full_docker_compose.py
- generate_full_docker_compose_fixed.py

Merged on: 2025-06-12

Generates complete Docker Compose configuration for MCP agents with 
full orchestration system and organized architecture.
"""

import json
import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path

class DockerComposeGenerator:
    """Generate comprehensive Docker Compose configurations for the MCP system"""
    
    def __init__(self):
        # Agent role definitions matching organized MCP server structure
        self.agent_roles: Dict[str, Dict[str, Any]] = {
            "code_indexers": {
                "count": 8,
                "port_start": 3101,
                "description": "Full repo understanding and code analysis",
                "mcp_paths": [
                    "/app/infrastructure/mcp_servers/coordination",
                    "/app/infrastructure/mcp_servers/task_management",
                    "/app/utilities/scripts",
                    "/app/core/ai_agents",
                    "/app/integrations/dex",
                    "/app/infrastructure/monitoring"
                ]
            },
            "builders": {
                "count": 10,
                "port_start": 3121,
                "description": "Project scaffolding and build agents",
                "mcp_paths": [
                    "/app/infrastructure/mcp_servers/production",
                    "/app/infrastructure/mcp_servers/foundry_integration",
                    "/app/infrastructure/mcp_servers/blockchain_integration",
                    "/app/infrastructure/mcp_servers/execution",
                    "/app/utilities/tools",
                    "/app/core/coordinators"
                ]
            },
            "test_writers": {
                "count": 10,
                "port_start": 3141,
                "description": "Unit and integration test creation",
                "mcp_paths": [
                    "/app/infrastructure/mcp_servers/quality",
                    "/app/infrastructure/monitoring",
                    "/app/infrastructure/mcp_servers/execution",
                    "/app/tests",
                    "/app/core"
                ]
            },
            "executors": {
                "count": 15,
                "port_start": 3161,
                "description": "Trading execution and verification agents",
                "mcp_paths": [
                    "/app/infrastructure/mcp_servers/execution",
                    "/app/integrations/blockchain",
                    "/app/infrastructure/mcp_servers/foundry_integration",
                    "/app/integrations/dex",
                    "/app/integrations/price_feeds",
                    "/app/infrastructure/mcp_servers/production",
                    "/app/core/coordinators",
                    "/app/infrastructure/mcp_servers/risk_management",
                    "/app/infrastructure/monitoring"
                ]
            },
            "coordinators": {
                "count": 10,
                "port_start": 3181,
                "description": "Middle-layer routing and coordination",
                "mcp_paths": [
                    "/app/core/coordinators",
                    "/app/infrastructure/mcp_servers/orchestration",
                    "/app/infrastructure/mcp_servers/task_management",
                    "/app/infrastructure/monitoring",
                    "/app/utilities/tools",
                    "/app/core/ai_agents"
                ]
            },
            "planners": {
                "count": 5,
                "port_start": 3201,
                "description": "Long-term project strategy and planning",
                "mcp_paths": [
                    "/app/infrastructure/mcp_servers/orchestration",
                    "/app/core/coordinators",
                    "/app/core/ai_agents",
                    "/app/infrastructure/mcp_servers/production"
                ]
            },
            "fixers": {
                "count": 10,
                "port_start": 3211,
                "description": "Self-healing and error fixing",
                "mcp_paths": [
                    "/app/infrastructure/mcp_servers/recovery",
                    "/app/infrastructure/monitoring",
                    "/app/utilities/tools",
                    "/app/infrastructure/mcp_servers/risk_management"
                ]
            },
            "ui_coders": {
                "count": 10,
                "port_start": 3231,
                "description": "Frontend and design implementation",
                "mcp_paths": [
                    "/app/interfaces/web",
                    "/app/interfaces/api",
                    "/app/infrastructure/monitoring",
                    "/app/core/coordinators"
                ]
            },
            "reviewers": {
                "count": 15,
                "port_start": 3251,
                "description": "Code review and quality assurance",
                "mcp_paths": [
                    "/app/infrastructure/mcp_servers/quality",
                    "/app/infrastructure/monitoring",
                    "/app/tests",
                    "/app/utilities/tools"
                ]
            },
            "admins": {
                "count": 1,
                "port_start": 3301,
                "description": "Top level control and administration",
                "mcp_paths": [
                    "/app/infrastructure/mcp_servers/orchestration",
                    "/app/core/coordinators",
                    "/app/infrastructure/monitoring"
                ]
            }
        }
        
        # Infrastructure services configuration
        self.infrastructure_services = {
            "redis": {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"],
                "volumes": ["redis_data:/data"],
                "healthcheck": {
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 3
                }
            },
            "prometheus": {
                "image": "prom/prometheus:latest",
                "ports": ["9090:9090"],
                "volumes": [
                    "./infrastructure/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml",
                    "prometheus_data:/prometheus"
                ],
                "command": [
                    "--config.file=/etc/prometheus/prometheus.yml",
                    "--storage.tsdb.path=/prometheus",
                    "--web.console.libraries=/etc/prometheus/console_libraries",
                    "--web.console.templates=/etc/prometheus/consoles"
                ]
            },
            "grafana": {
                "image": "grafana/grafana:latest",
                "ports": ["3000:3000"],
                "environment": [
                    "GF_SECURITY_ADMIN_PASSWORD=admin"
                ],
                "volumes": [
                    "grafana_data:/var/lib/grafana",
                    "./infrastructure/monitoring/grafana:/etc/grafana/provisioning"
                ]
            },
            "etcd": {
                "image": "quay.io/coreos/etcd:v3.5.0",
                "ports": ["2379:2379", "2380:2380"],
                "environment": [
                    "ETCD_NAME=etcd0",
                    "ETCD_ADVERTISE_CLIENT_URLS=http://etcd:2379",
                    "ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:2379",
                    "ETCD_INITIAL_ADVERTISE_PEER_URLS=http://etcd:2380",
                    "ETCD_LISTEN_PEER_URLS=http://0.0.0.0:2380",
                    "ETCD_INITIAL_CLUSTER=etcd0=http://etcd:2380"
                ],
                "volumes": ["etcd_data:/etcd-data"]
            }
        }
    
    def generate_agent_service(self, role: str, instance_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Docker Compose service configuration for an agent"""
        port = config["port_start"] + instance_id
        service_name = f"agent-{role}-{instance_id:02d}"
        
        # Create volume mounts for MCP paths
        volumes = []
        for mcp_path in config["mcp_paths"]:
            local_path = mcp_path.replace("/app/", "./")
            volumes.append(f"{local_path}:{mcp_path}:ro")
        
        # Add common volumes
        volumes.extend([
            "./logs:/app/logs",
            "./data:/app/data",
            "./models:/app/models"
        ])
        
        return {
            "image": "flash-loan-mcp-agent:latest",
            "container_name": service_name,
            "ports": [f"{port}:{port}"],
            "environment": [
                f"AGENT_ROLE={role}",
                f"AGENT_ID={instance_id:02d}",
                f"AGENT_PORT={port}",
                f"AGENT_NAME={service_name}",
                "REDIS_URL=redis://redis:6379",
                "ETCD_URL=http://etcd:2379",
                "PROMETHEUS_GATEWAY=http://prometheus:9090"
            ],
            "volumes": volumes,
            "depends_on": ["redis", "etcd", "prometheus"],
            "networks": ["mcp-network"],
            "restart": "unless-stopped",
            "healthcheck": {
                "test": [f"curl -f http://localhost:{port}/health || exit 1"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3,
                "start_period": "40s"
            },
            "labels": [
                f"mcp.agent.role={role}",
                f"mcp.agent.instance={instance_id}",
                f"mcp.agent.port={port}",
                "mcp.component=agent"
            ]
        }
    
    def generate_mcp_server_service(self, server_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Docker Compose service for MCP server"""
        port = config["port"]
        script_path = config["script"]
        
        # Determine if it's a Python or Node.js script
        if script_path.endswith('.py'):
            command = f"python /app/infrastructure/mcp_servers/{script_path}"
        elif script_path.endswith('.js') or script_path.endswith('.ts'):
            command = f"node /app/infrastructure/mcp_servers/{script_path}"
        else:
            command = f"/app/infrastructure/mcp_servers/{script_path}"
        
        return {
            "image": "flash-loan-mcp-server:latest",
            "container_name": f"mcp-{server_name}",
            "ports": [f"{port}:{port}"],
            "environment": [
                f"MCP_SERVER_NAME={server_name}",
                f"MCP_SERVER_PORT={port}",
                "REDIS_URL=redis://redis:6379",
                "ETCD_URL=http://etcd:2379"
            ],
            "volumes": [
                "./infrastructure/mcp_servers:/app/infrastructure/mcp_servers:ro",
                "./logs:/app/logs",
                "./data:/app/data"
            ],
            "depends_on": ["redis", "etcd"],
            "networks": ["mcp-network"],
            "restart": "unless-stopped",
            "command": command,
            "healthcheck": {
                "test": [f"curl -f http://localhost:{port}/health || exit 1"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            },
            "labels": [
                f"mcp.server.name={server_name}",
                f"mcp.server.port={port}",
                "mcp.component=server"
            ]
        }
    
    def generate_coordinator_service(self) -> Dict[str, Any]:
        """Generate the master coordinator service"""
        return {
            "image": "flash-loan-coordinator:latest",
            "container_name": "mcp-master-coordinator",
            "ports": ["4000:4000"],
            "environment": [
                "SERVER_PORT=4000",
                "REDIS_URL=redis://redis:6379",
                "ETCD_URL=http://etcd:2379",
                "LOG_LEVEL=INFO"
            ],
            "volumes": [
                "./core:/app/core:ro",
                "./infrastructure:/app/infrastructure:ro",
                "./logs:/app/logs",
                "./data:/app/data"
            ],
            "depends_on": ["redis", "etcd", "prometheus"],
            "networks": ["mcp-network"],
            "restart": "unless-stopped",
            "command": "python /app/core/coordinators/complete_ai_system.py",
            "healthcheck": {
                "test": ["curl -f http://localhost:4000/health || exit 1"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            },
            "labels": [
                "mcp.component=coordinator",
                "mcp.role=master"
            ]
        }
    
    def generate_dashboard_service(self) -> Dict[str, Any]:
        """Generate the web dashboard service"""
        return {
            "image": "flash-loan-dashboard:latest",
            "container_name": "mcp-dashboard",
            "ports": ["8080:8080"],
            "environment": [
                "DASHBOARD_PORT=8080",
                "COORDINATOR_URL=http://mcp-master-coordinator:4000",
                "REDIS_URL=redis://redis:6379"
            ],
            "volumes": [
                "./interfaces/web:/app/interfaces/web:ro",
                "./logs:/app/logs"
            ],
            "depends_on": ["mcp-master-coordinator", "redis"],
            "networks": ["mcp-network"],
            "restart": "unless-stopped",
            "command": "python /app/interfaces/web/mcp_dashboard.py",
            "healthcheck": {
                "test": ["curl -f http://localhost:8080/health || exit 1"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            },
            "labels": [
                "mcp.component=dashboard",
                "mcp.interface=web"
            ]
        }
    
    def generate_complete_docker_compose(self, 
                                       include_agents: bool = True,
                                       include_servers: bool = True,
                                       include_monitoring: bool = True) -> Dict[str, Any]:
        """Generate complete Docker Compose configuration"""
        
        compose_config = {
            "version": "3.8",
            "services": {},
            "networks": {
                "mcp-network": {
                    "driver": "bridge",
                    "ipam": {
                        "config": [{"subnet": "172.20.0.0/16"}]
                    }
                }
            },
            "volumes": {
                "redis_data": {},
                "prometheus_data": {},
                "grafana_data": {},
                "etcd_data": {}
            }
        }
        
        # Add infrastructure services
        compose_config["services"].update(self.infrastructure_services)
        
        # Add master coordinator
        compose_config["services"]["mcp-master-coordinator"] = self.generate_coordinator_service()
        
        # Add dashboard
        compose_config["services"]["mcp-dashboard"] = self.generate_dashboard_service()
        
        # Add MCP servers if requested
        if include_servers:
            mcp_servers = {
                'ai-integration': {'port': 4001, 'script': 'ai_integration/enhanced_ai_server.py'},
                'blockchain-integration': {'port': 4002, 'script': 'blockchain_integration/blockchain_mcp_server.py'},
                'coordination': {'port': 4003, 'script': 'coordination/mcp_server_coordinator.py'},
                'dex-services': {'port': 4005, 'script': 'dex_services/dex_price_mcp_server.py'},
                'execution': {'port': 4006, 'script': 'execution/flash_loan_executor.py'},
                'monitoring': {'port': 4009, 'script': 'monitoring/system_monitor.py'},
                'risk-management': {'port': 4014, 'script': 'risk_management/risk_manager.py'},
                'task-management': {'port': 4015, 'script': 'task_management/mcp-taskmanager/index.js'},
            }
            
            for server_name, config in mcp_servers.items():
                compose_config["services"][f"mcp-{server_name}"] = self.generate_mcp_server_service(server_name, config)
        
        # Add agent instances if requested
        if include_agents:
            for role, config in self.agent_roles.items():
                for instance_id in range(config["count"]):
                    service_name = f"agent-{role}-{instance_id:02d}"
                    compose_config["services"][service_name] = self.generate_agent_service(role, instance_id, config)
        
        return compose_config
    
    def save_docker_compose(self, config: Dict[str, Any], filename: str = "docker-compose.yml"):
        """Save Docker Compose configuration to file"""
        output_path = Path(filename)
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"Docker Compose configuration saved to {output_path}")
        return output_path
    
    def generate_dockerfiles(self):
        """Generate Dockerfiles for different components"""
        
        # Agent Dockerfile
        agent_dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for mixed environments
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \\
    && apt-get install -y nodejs

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:$AGENT_PORT/health || exit 1

EXPOSE 3000-3400

CMD ["python", "core/ai_agents/enhanced_ai_system.py"]
"""
        
        # MCP Server Dockerfile
        server_dockerfile = """FROM node:18-slim

WORKDIR /app

# Install Python for mixed environments
RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY package*.json ./
RUN npm install

COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

EXPOSE 4000-4100

CMD ["node", "infrastructure/mcp_servers/task_management/mcp-taskmanager/index.ts"]
"""
        
        # Coordinator Dockerfile
        coordinator_dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

EXPOSE 4000

CMD ["python", "core/coordinators/complete_ai_system.py"]
"""
        
        # Dashboard Dockerfile
        dashboard_dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

EXPOSE 8080

CMD ["python", "interfaces/web/mcp_dashboard.py"]
"""
        
        # Save Dockerfiles
        dockerfiles = {
            "Dockerfile.agent": agent_dockerfile,
            "Dockerfile.server": server_dockerfile,
            "Dockerfile.coordinator": coordinator_dockerfile,
            "Dockerfile.dashboard": dashboard_dockerfile
        }
        
        for filename, content in dockerfiles.items():
            with open(filename, 'w') as f:
                f.write(content)
            print(f"Generated {filename}")
    
    def generate_build_script(self):
        """Generate Docker build script"""
        build_script = """#!/bin/bash
# Docker Build Script for Flash Loan MCP System

set -e

echo "Building Flash Loan MCP Docker Images..."

# Build agent image
echo "Building agent image..."
docker build -f Dockerfile.agent -t flash-loan-mcp-agent:latest .

# Build server image  
echo "Building server image..."
docker build -f Dockerfile.server -t flash-loan-mcp-server:latest .

# Build coordinator image
echo "Building coordinator image..."
docker build -f Dockerfile.coordinator -t flash-loan-coordinator:latest .

# Build dashboard image
echo "Building dashboard image..."
docker build -f Dockerfile.dashboard -t flash-loan-dashboard:latest .

echo "All images built successfully!"
echo ""
echo "To start the system:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the system:"
echo "  docker-compose down"
"""
        
        with open("build_docker_images.sh", 'w') as f:
            f.write(build_script)
        
        # Make executable on Unix systems
        os.chmod("build_docker_images.sh", 0o755)
        print("Generated build_docker_images.sh")

def main():
    """Main function to generate Docker Compose configuration"""
    generator = DockerComposeGenerator()
    
    # Generate different configurations
    configurations = {
        "docker-compose.yml": {
            "include_agents": True,
            "include_servers": True,
            "include_monitoring": True
        },
        "docker-compose.minimal.yml": {
            "include_agents": False,
            "include_servers": True,
            "include_monitoring": False
        },
        "docker-compose.agents-only.yml": {
            "include_agents": True,
            "include_servers": False,
            "include_monitoring": False
        }
    }
    
    for filename, options in configurations.items():
        config = generator.generate_complete_docker_compose(**options)
        generator.save_docker_compose(config, filename)
        print(f"Generated {filename} with {len(config['services'])} services")
    
    # Generate Dockerfiles and build script
    generator.generate_dockerfiles()
    generator.generate_build_script()
    
    print(f"""
Docker Compose Generation Complete!

Generated files:
- docker-compose.yml (Full system with {sum(role['count'] for role in generator.agent_roles.values())} agents)
- docker-compose.minimal.yml (Core services only)
- docker-compose.agents-only.yml (Agents without servers)
- Dockerfile.* (Component Dockerfiles)
- build_docker_images.sh (Build script)

To get started:
1. Run: ./build_docker_images.sh
2. Run: docker-compose up -d
3. Access dashboard at: http://localhost:8080
""")

if __name__ == "__main__":
    main()
