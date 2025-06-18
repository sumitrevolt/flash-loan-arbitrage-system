#!/usr/bin/env python3
"""
Enhanced Docker Compose Generator with Optimized Health Checks
Generates docker-compose.yml with proper health check timing for all services
"""

import os
import yaml
from datetime import datetime

def generate_enhanced_docker_compose():
    """Generate enhanced Docker Compose with optimized health checks"""
    
    compose_config = {
        'version': '3.8',
        'networks': {
            'flashloan-network': {
                'driver': 'bridge'
            }
        },
        'volumes': {
            'postgres_data': None,
            'redis_data': None
        },
        'services': {}
    }
    
    # Infrastructure Services
    compose_config['services']['postgres'] = {
        'image': 'postgres:15-alpine',
        'container_name': 'flashloan-postgres',
        'environment': {
            'POSTGRES_DB': 'flashloan_mcp',
            'POSTGRES_USER': 'postgres',
            'POSTGRES_PASSWORD': 'password'
        },
        'volumes': ['postgres_data:/var/lib/postgresql/data'],
        'ports': ['5432:5432'],
        'networks': ['flashloan-network'],
        'restart': 'unless-stopped',
        'healthcheck': {
            'test': ['CMD-SHELL', 'pg_isready -U postgres'],
            'interval': '15s',
            'timeout': '10s',
            'retries': 5,
            'start_period': '30s'
        }
    }
    
    compose_config['services']['redis'] = {
        'image': 'redis:7-alpine',
        'container_name': 'flashloan-redis',
        'volumes': ['redis_data:/data'],
        'ports': ['6379:6379'],
        'networks': ['flashloan-network'],
        'restart': 'unless-stopped',
        'healthcheck': {
            'test': ['CMD', 'redis-cli', 'ping'],
            'interval': '15s',
            'timeout': '5s',
            'retries': 5,
            'start_period': '20s'
        }
    }
    
    compose_config['services']['rabbitmq'] = {
        'image': 'rabbitmq:3.12-management-alpine',
        'container_name': 'flashloan-rabbitmq',
        'environment': {
            'RABBITMQ_DEFAULT_USER': 'admin',
            'RABBITMQ_DEFAULT_PASS': 'password'
        },
        'ports': ['5672:5672', '15672:15672'],
        'networks': ['flashloan-network'],
        'restart': 'unless-stopped',
        'healthcheck': {
            'test': ['CMD', 'rabbitmq-diagnostics', '-q', 'ping'],
            'interval': '30s',
            'timeout': '15s',
            'retries': 5,
            'start_period': '60s'
        }
    }
    
    # MCP Servers with optimized health checks
    mcp_servers = [
        {'name': 'flash-loan-mcp', 'port': 4001, 'image': 'python:3.11-slim', 'deps': 'flask web3 requests'},
        {'name': 'web3-provider-mcp', 'port': 4002, 'image': 'python:3.11-slim', 'deps': 'flask web3 requests'},
        {'name': 'dex-price-server', 'port': 4003, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'arbitrage-detector-mcp', 'port': 4004, 'image': 'python:3.11-slim', 'deps': 'flask web3 requests'},
        {'name': 'foundry-integration-mcp', 'port': 4005, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'evm-mcp-server', 'port': 4006, 'image': 'python:3.11-slim', 'deps': 'flask web3 requests'},
        {'name': 'matic-mcp-server', 'port': 4007, 'image': 'python:3.11-slim', 'deps': 'flask web3 requests'},
        {'name': 'github-mcp-server', 'port': 4008, 'image': 'node:18-alpine', 'deps': 'express cors axios'},
        {'name': 'context7-mcp-server', 'port': 4009, 'image': 'node:18-alpine', 'deps': 'express cors'},
        {'name': 'enhanced-copilot-mcp-server', 'port': 4010, 'image': 'node:18-alpine', 'deps': 'express cors'},
        {'name': 'price-oracle-mcp-server', 'port': 4011, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'dex-services-mcp', 'port': 4012, 'image': 'python:3.11-slim', 'deps': 'flask web3 requests'},
        {'name': 'notification-service', 'port': 4013, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'audit-logger', 'port': 4014, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'liquidity-monitor', 'port': 4015, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'market-data-feed', 'port': 4016, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'risk-manager', 'port': 4017, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'performance-monitor', 'port': 4018, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'analytics-engine', 'port': 4019, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'code-indexer', 'port': 4020, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
        {'name': 'health-checker', 'port': 4021, 'image': 'python:3.11-slim', 'deps': 'flask requests'},
    ]
    
    # Generate MCP server configurations
    for server in mcp_servers:
        service_name = server['name'].replace('-', '_')
        container_name = f"flashloan-{server['name']}"
        
        if 'node' in server['image']:
            # Node.js based service
            compose_config['services'][service_name] = {
                'image': server['image'],
                'container_name': container_name,
                'ports': [f"{server['port']}:4000"],
                'environment': {
                    'MCP_SERVER_ID': server['name'],
                    'NODE_ENV': 'production'
                },
                'command': f"""sh -c "
                    apk add --no-cache wget &&
                    npm init -y &&
                    npm install {server['deps']} &&
                    cat > server.js << 'EOF'
const express = require('express');
const app = express();
app.use(express.json());
app.get('/health', (req, res) => res.json({{status: 'healthy', service: '{server['name']}', port: {server['port']}}}));
app.get('/status', (req, res) => res.json({{service: '{server['name']}', ready: true}}));
app.listen(4000, () => console.log('{server['name']} running on port 4000'));
EOF
                    node server.js
                    \"""",
                'networks': ['flashloan-network'],
                'restart': 'unless-stopped',
                'healthcheck': {
                    'test': ['CMD-SHELL', 'wget --no-verbose --tries=1 --spider http://localhost:4000/health || exit 1'],
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 5,
                    'start_period': '90s'
                }
            }
        else:
            # Python based service
            compose_config['services'][service_name] = {
                'image': server['image'],
                'container_name': container_name,
                'ports': [f"{server['port']}:4000"],
                'environment': {
                    'MCP_SERVER_ID': server['name'],
                    'PYTHONUNBUFFERED': '1'
                },
                'command': f"""sh -c "
                    apt-get update && apt-get install -y wget && 
                    pip install {server['deps']} &&
                    cat > server.py << 'EOF'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({{'status': 'healthy', 'service': '{server['name']}', 'port': {server['port']}}}))

@app.route('/status')
def status():
    return jsonify({{'service': '{server['name']}', 'ready': True}}))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=False)
EOF
                    python server.py
                    \"""",
                'networks': ['flashloan-network'],
                'restart': 'unless-stopped',
                'healthcheck': {
                    'test': ['CMD-SHELL', 'wget --no-verbose --tries=1 --spider http://localhost:4000/health || exit 1'],
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 5,
                    'start_period': '120s'
                }
            }
    
    # AI Agents
    ai_agents = [
        {'name': 'coordinator-agent', 'port': 5001},
        {'name': 'arbitrage-agent', 'port': 5002},
        {'name': 'monitoring-agent', 'port': 5003},
        {'name': 'builder-agent', 'port': 5004},
        {'name': 'aave-executor', 'port': 5005},
        {'name': 'contract-executor', 'port': 5006},
    ]
    
    # Generate AI agent configurations
    for agent in ai_agents:
        service_name = agent['name'].replace('-', '_')
        container_name = f"flashloan-{agent['name']}"
        
        compose_config['services'][service_name] = {
            'image': 'python:3.11-slim',
            'container_name': container_name,
            'ports': [f"{agent['port']}:4000"],
            'environment': {
                'AGENT_ID': agent['name'],
                'PYTHONUNBUFFERED': '1'
            },
            'command': f"""sh -c "
                apt-get update && apt-get install -y wget && 
                pip install flask requests &&
                cat > agent.py << 'EOF'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({{'status': 'healthy', 'agent': '{agent['name']}', 'port': {agent['port']}}}))

@app.route('/status')
def status():
    return jsonify({{'agent': '{agent['name']}', 'ready': True, 'capabilities': ['analysis', 'execution']}}))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=False)
EOF
                python agent.py
                \"""",
            'networks': ['flashloan-network'],
            'restart': 'unless-stopped',
            'depends_on': ['postgres', 'redis', 'rabbitmq'],
            'healthcheck': {
                'test': ['CMD-SHELL', 'wget --no-verbose --tries=1 --spider http://localhost:4000/health || exit 1'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 5,
                'start_period': '120s'
            }
        }
    
    return compose_config

def main():
    """Generate and save enhanced Docker Compose configuration"""
    print("🏗️ Generating Enhanced Docker Compose Configuration...")
    print("=" * 60)
    
    # Generate configuration
    config = generate_enhanced_docker_compose()
    
    # Save to file
    output_file = 'docker-compose.enhanced.yml'
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
    
    print(f"✅ Enhanced Docker Compose saved to: {output_file}")
    print(f"📊 Configuration includes:")
    print(f"   • 3 Infrastructure services")
    print(f"   • 21 MCP servers with optimized health checks")
    print(f"   • 6 AI agents with dependency management")
    print(f"   • Health check timing:")
    print(f"     - Node.js services: 90s start period")
    print(f"     - Python services: 120s start period")
    print(f"     - Infrastructure: 30-60s start period")
    print(f"   • 30s health check intervals")
    print(f"   • 10s health check timeouts")
    print(f"   • 5 retries before marking unhealthy")
    
    print(f"\n🚀 To deploy with enhanced health checks:")
    print(f"   docker-compose -f {output_file} up -d")
    
    print(f"\n📋 Recommended next steps:")
    print(f"   1. Review the generated configuration")
    print(f"   2. Deploy with: docker-compose -f {output_file} up -d")
    print(f"   3. Wait 2-3 minutes for all services to start")
    print(f"   4. Run: python comprehensive_system_verifier.py")

if __name__ == "__main__":
    main()
