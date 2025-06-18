#!/usr/bin/env python3
"""
Auto-generate Docker Compose file with all MCP servers and AI agents
"""
import json
import yaml
import os

def load_mcp_config():
    """Load MCP server configuration"""
    with open('unified_mcp_config.json', 'r') as f:
        return json.load(f)

def load_ai_agents_config():
    """Load AI agents configuration"""
    try:
        with open('ai_agents_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default AI agents if config doesn't exist
        return {
            "agents": {
                "flash_loan_optimizer": {"port": 9001, "type": "flash_loan_optimizer"},
                "risk_manager": {"port": 9002, "type": "risk_management"},
                "arbitrage_detector": {"port": 9003, "type": "arbitrage"},
                "portfolio_manager": {"port": 9004, "type": "portfolio"},
                "market_analyzer": {"port": 9005, "type": "market_analysis"},
                "defi_coordinator": {"port": 9006, "type": "defi_coordination"},
                "price_monitor": {"port": 9007, "type": "price_monitoring"},
                "liquidity_tracker": {"port": 9008, "type": "liquidity_tracking"}
            }
        }

def generate_base_compose():
    """Generate base compose structure"""
    return {
        'networks': {
            'coordination_network': {
                'driver': 'bridge'
            }
        },
        'volumes': {
            'postgres_data': None,
            'redis_data': None,
            'rabbitmq_data': None,
            'grafana_data': None,
            'prometheus_data': None
        },
        'services': {}
    }

def add_infrastructure_services(compose):
    """Add infrastructure services"""
    compose['services'].update({
        'redis': {
            'image': 'redis:7-alpine',
            'container_name': 'coordination_redis',
            'ports': ['6379:6379'],
            'volumes': ['redis_data:/data'],
            'networks': ['coordination_network'],
            'healthcheck': {
                'test': ['CMD', 'redis-cli', 'ping'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            },
            'restart': 'unless-stopped'
        },
        'rabbitmq': {
            'image': 'rabbitmq:3-management',
            'container_name': 'coordination_rabbitmq',
            'environment': {
                'RABBITMQ_DEFAULT_USER': 'coordination',
                'RABBITMQ_DEFAULT_PASS': 'coordination_pass',
                'RABBITMQ_DEFAULT_VHOST': 'coordination'
            },
            'ports': ['5672:5672', '15672:15672'],
            'volumes': ['rabbitmq_data:/var/lib/rabbitmq'],
            'networks': ['coordination_network'],
            'healthcheck': {
                'test': ['CMD', 'rabbitmqctl', 'status'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            },
            'restart': 'unless-stopped'
        },
        'postgres': {
            'image': 'postgres:15-alpine',
            'container_name': 'coordination_postgres',
            'environment': {
                'POSTGRES_DB': 'coordination',
                'POSTGRES_USER': 'coordination',
                'POSTGRES_PASSWORD': 'coordination_pass'
            },
            'ports': ['5432:5432'],
            'volumes': ['postgres_data:/var/lib/postgresql/data'],
            'networks': ['coordination_network'],
            'healthcheck': {
                'test': ['CMD-SHELL', 'pg_isready -d coordination -U coordination'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            },
            'restart': 'unless-stopped'
        },
        'prometheus': {
            'image': 'prom/prometheus:latest',
            'container_name': 'coordination_prometheus',
            'ports': ['9090:9090'],
            'volumes': ['prometheus_data:/prometheus'],
            'networks': ['coordination_network'],
            'restart': 'unless-stopped'
        },
        'grafana': {
            'image': 'grafana/grafana:latest',
            'container_name': 'coordination_grafana',
            'ports': ['3000:3000'],
            'volumes': ['grafana_data:/var/lib/grafana'],
            'environment': {
                'GF_SECURITY_ADMIN_PASSWORD': 'admin'
            },
            'networks': ['coordination_network'],
            'restart': 'unless-stopped'
        }
    })

def add_mcp_servers(compose, mcp_config):
    """Add all MCP servers"""
    servers = mcp_config['servers']
    
    for server_name, server_config in servers.items():
        if not server_config.get('enabled', True):
            continue
            
        port = server_config.get('port', 8000)
        service_name = f"mcp_{server_name}"
        
        compose['services'][service_name] = {
            'build': {
                'context': '..',
                'dockerfile': 'docker/Dockerfile.mcp'
            },
            'container_name': service_name,
            'environment': {
                'SERVER_TYPE': server_name,
                'PORT': str(port),
                'REDIS_URL': 'redis://coordination_redis:6379',
                'POSTGRES_URL': 'postgresql://coordination:coordination_pass@coordination_postgres:5432/coordination',
                'POLYGON_RPC_URL': '${POLYGON_RPC_URL:-https://polygon-rpc.com}',
                'ARBITRAGE_PRIVATE_KEY': '${ARBITRAGE_PRIVATE_KEY:-}'
            },
            'ports': [f"{port}:{port}"],
            'depends_on': {
                'redis': {'condition': 'service_healthy'},
                'postgres': {'condition': 'service_healthy'}
            },
            'networks': ['coordination_network'],
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', f'http://localhost:{port}/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3,
                'start_period': '40s'
            },
            'restart': 'unless-stopped'
        }

def add_ai_agents(compose, ai_config):
    """Add all AI agents"""
    agents = ai_config['agents']
    
    for agent_name, agent_config in agents.items():
        port = agent_config.get('port', 9000)
        agent_type = agent_config.get('type', agent_name)
        service_name = f"ai_agent_{agent_name}"
        
        compose['services'][service_name] = {
            'build': {
                'context': '..',
                'dockerfile': 'docker/Dockerfile.agent'
            },
            'container_name': service_name,
            'environment': {
                'AGENT_TYPE': agent_type,
                'AGENT_NAME': agent_name,
                'PORT': str(port),
                'REDIS_URL': 'redis://coordination_redis:6379',
                'POSTGRES_URL': 'postgresql://coordination:coordination_pass@coordination_postgres:5432/coordination'
            },
            'ports': [f"{port}:{port}"],
            'depends_on': {
                'redis': {'condition': 'service_healthy'}
            },
            'networks': ['coordination_network'],
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', f'http://localhost:{port}/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3,
                'start_period': '40s'
            },
            'restart': 'unless-stopped'
        }

def add_self_healing_agent(compose):
    """Add self-healing agent"""
    compose['services']['ai_agent_self_healing'] = {
        'build': {
            'context': '..',
            'dockerfile': 'docker/Dockerfile.self-healing'
        },
        'container_name': 'ai_agent_self_healing',
        'environment': {
            'AGENT_TYPE': 'self_healing',
            'AGENT_NAME': 'self_healing_agent',
            'PORT': '8300',
            'REDIS_URL': 'redis://coordination_redis:6379'
        },
        'ports': ['8300:8300'],
        'volumes': ['/var/run/docker.sock:/var/run/docker.sock:ro'],
        'depends_on': {
            'redis': {'condition': 'service_healthy'}
        },
        'networks': ['coordination_network'],
        'healthcheck': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8300/health'],
            'interval': '30s',
            'timeout': '10s',
            'retries': 3
        },
        'restart': 'unless-stopped',
        'privileged': True
    }

def add_coordination_system(compose, mcp_config, ai_config):
    """Add main coordination system"""
    # Build environment variables for all MCP servers and AI agents
    env = {
        'REDIS_URL': 'redis://coordination_redis:6379',
        'POSTGRES_URL': 'postgresql://coordination:coordination_pass@coordination_postgres:5432/coordination',
        'RABBITMQ_URL': 'amqp://coordination:coordination_pass@coordination_rabbitmq:5672/coordination',
        'POLYGON_RPC_URL': '${POLYGON_RPC_URL:-https://polygon-rpc.com}',
        'ARBITRAGE_PRIVATE_KEY': '${ARBITRAGE_PRIVATE_KEY:-}'
    }
    
    # Add MCP server URLs
    for server_name, server_config in mcp_config['servers'].items():
        if server_config.get('enabled', True):
            port = server_config.get('port', 8000)
            env[f'MCP_{server_name.upper()}_URL'] = f'http://mcp_{server_name}:{port}'
    
    # Add AI agent URLs
    for agent_name, agent_config in ai_config['agents'].items():
        port = agent_config.get('port', 9000)
        env[f'AI_AGENT_{agent_name.upper()}_URL'] = f'http://ai_agent_{agent_name}:{port}'
    
    # Self-healing agent URL
    env['AI_AGENT_SELF_HEALING_URL'] = 'http://ai_agent_self_healing:8300'
    
    # Build dependencies
    depends_on = {
        'redis': {'condition': 'service_healthy'},
        'postgres': {'condition': 'service_healthy'},
        'rabbitmq': {'condition': 'service_healthy'},
        'ai_agent_self_healing': {'condition': 'service_healthy'}
    }
    
    compose['services']['coordination_system'] = {
        'build': {
            'context': '..',
            'dockerfile': 'docker/Dockerfile.coordination'
        },
        'container_name': 'coordination_system',
        'environment': env,
        'ports': ['8000:8000'],
        'depends_on': depends_on,
        'networks': ['coordination_network'],
        'healthcheck': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:8000/health'],
            'interval': '30s',
            'timeout': '10s',
            'retries': 3
        },
        'restart': 'unless-stopped'
    }

def add_dashboard(compose):
    """Add dashboard service"""
    compose['services']['dashboard'] = {
        'image': 'nginx:alpine',
        'container_name': 'coordination_dashboard',
        'ports': ['8080:80'],
        'depends_on': ['coordination_system'],
        'networks': ['coordination_network'],
        'restart': 'unless-stopped'
    }

def generate_complete_compose():
    """Generate complete Docker Compose configuration"""
    print("Loading MCP configuration...")
    mcp_config = load_mcp_config()
    
    print("Loading AI agents configuration...")
    ai_config = load_ai_agents_config()
    
    print("Generating base compose structure...")
    compose = generate_base_compose()
    
    print("Adding infrastructure services...")
    add_infrastructure_services(compose)
    
    print(f"Adding {len(mcp_config['servers'])} MCP servers...")
    add_mcp_servers(compose, mcp_config)
    
    print(f"Adding {len(ai_config['agents'])} AI agents...")
    add_ai_agents(compose, ai_config)
    
    print("Adding self-healing agent...")
    add_self_healing_agent(compose)
    
    print("Adding coordination system...")
    add_coordination_system(compose, mcp_config, ai_config)
    
    print("Adding dashboard...")
    add_dashboard(compose)
    
    return compose

def save_compose_file(compose, filename):
    """Save compose configuration to file"""
    os.makedirs('docker', exist_ok=True)
    filepath = os.path.join('docker', filename)
    
    with open(filepath, 'w') as f:
        # Add header comment
        f.write("# Auto-generated Docker Compose file for Complete MCP System\n")
        f.write("# Generated with all 81 MCP servers and 8 AI agents\n")
        f.write("# Use: docker-compose -f docker/docker-compose-complete.yml up -d\n\n")
        
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False, indent=2)
    
    print(f"Docker Compose file saved to: {filepath}")
    return filepath

def generate_scaled_compose():
    """Generate a scaled-down version for testing"""
    print("Generating scaled-down compose for testing...")
    
    mcp_config = load_mcp_config()
    ai_config = load_ai_agents_config()
    
    # Select core servers for testing
    core_servers = [
        'mcp_price_feed_server',
        'mcp_arbitrage_server', 
        'mcp_flash_loan_server',
        'mcp_monitoring_server',
        'mcp_coordinator_server'
    ]
    
    # Filter MCP config to core servers only
    filtered_mcp = {
        'servers': {k: v for k, v in mcp_config['servers'].items() 
                   if k in core_servers and v.get('enabled', True)},
        'global_configuration': mcp_config['global_configuration']
    }
    
    # Generate compose
    compose = generate_base_compose()
    add_infrastructure_services(compose)
    add_mcp_servers(compose, filtered_mcp)
    add_ai_agents(compose, ai_config)  # Keep all AI agents
    add_self_healing_agent(compose)
    add_coordination_system(compose, filtered_mcp, ai_config)
    add_dashboard(compose)
    
    return compose

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Generating test/scaled compose file...")
        compose = generate_scaled_compose()
        filepath = save_compose_file(compose, 'docker-compose-test-complete.yml')
    else:
        print("Generating complete compose file with all services...")
        compose = generate_complete_compose()
        filepath = save_compose_file(compose, 'docker-compose-complete.yml')
    
    print(f"\nGenerated services summary:")
    services = compose['services']
    mcp_count = len([s for s in services.keys() if s.startswith('mcp_')])
    ai_count = len([s for s in services.keys() if s.startswith('ai_agent_')])
    infra_count = len([s for s in services.keys() if s in ['redis', 'postgres', 'rabbitmq', 'prometheus', 'grafana']])
    
    print(f"  Infrastructure services: {infra_count}")
    print(f"  MCP servers: {mcp_count}")
    print(f"  AI agents: {ai_count}")
    print(f"  Other services: {len(services) - mcp_count - ai_count - infra_count}")
    print(f"  Total services: {len(services)}")
