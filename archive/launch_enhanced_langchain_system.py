#!/usr/bin/env python3
"""
Enhanced LangChain System Launcher
Launches the complete orchestration system with 21 MCP servers and 10 agents
"""

import os
import sys
import asyncio
import subprocess
import time
import argparse
from pathlib import Path

def setup_environment():
    """Setup environment variables and configurations"""
    
    # Default environment variables
    env_vars = {
        'GITHUB_TOKEN': '',  # Set this to your GitHub token
        'GITHUB_REPO': 'your-username/your-repo',  # Set this to your GitHub repo
        'ORCHESTRATOR_MODE': 'enhanced',
        'AUTO_HEAL_ENABLED': 'true',
        'MCP_SERVERS_COUNT': '21',
        'AGENTS_COUNT': '10',
        'REDIS_URL': 'redis://redis:6379',
        'POSTGRES_URL': 'postgresql://postgres:postgres_password@postgres:5432/flashloan',
        'RABBITMQ_URL': 'amqp://rabbitmq:rabbitmq_password@rabbitmq:5672',
        'DOCKER_HOST': 'unix:///var/run/docker.sock'
    }
    
    # Load environment variables from .env file if exists
    env_file = Path('.env')
    if env_file.exists():
        print("Loading environment from .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Set environment variables
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
    
    print("Environment configured successfully")

def create_required_directories():
    """Create required directories for the system"""
    directories = [
        'logs',
        'data',
        'containers/orchestrator',
        'containers/mcp_servers',
        'containers/mcp_servers/server_implementations',
        'containers/agents'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_dockerfiles():
    """Create Dockerfiles for containers if they don't exist"""
    
    # Orchestrator Dockerfile
    orchestrator_dockerfile = Path('containers/orchestrator/Dockerfile')
    if not orchestrator_dockerfile.exists():
        orchestrator_dockerfile.write_text("""FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the orchestrator
CMD ["python", "/app/enhanced_langchain_orchestrator.py"]
""")
    
    # MCP Servers Dockerfile
    mcp_dockerfile = Path('containers/mcp_servers/Dockerfile')
    if not mcp_dockerfile.exists():
        mcp_dockerfile.write_text("""FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY . .

# Expose port
EXPOSE 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:9000/health || exit 1

# Run the MCP server
CMD ["python", "/app/mcp_server_template.py"]
""")
    
    # Agents Dockerfile
    agents_dockerfile = Path('containers/agents/Dockerfile')
    if not agents_dockerfile.exists():
        agents_dockerfile.write_text("""FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)"

# Run the agent
CMD ["python", "/app/agent_template.py"]
""")

def create_requirements_files():
    """Create requirements.txt files for containers"""
    
    requirements = """# Core dependencies
python>=3.11
asyncio
aiohttp
aioredis
psycopg2-binary
pika
docker
redis
tenacity

# LangChain and AI dependencies
langchain
langchain-community
langchain-core
openai
anthropic

# AutoGen dependencies
pyautogen

# Web and API dependencies
fastapi
uvicorn
requests

# Data processing
pandas
numpy
json5

# Logging and monitoring
structlog
prometheus_client

# Development and testing
pytest
black
flake8
mypy
"""
    
    # Write requirements to all container directories
    container_dirs = [
        'containers/orchestrator',
        'containers/mcp_servers', 
        'containers/agents'
    ]
    
    for container_dir in container_dirs:
        req_file = Path(container_dir) / 'requirements.txt'
        req_file.write_text(requirements)
        print(f"Created requirements.txt in {container_dir}")

def create_env_template():
    """Create .env template file"""
    env_template = """.env
# GitHub Integration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=your-username/your-repo

# System Configuration  
ORCHESTRATOR_MODE=enhanced
AUTO_HEAL_ENABLED=true
MCP_SERVERS_COUNT=21
AGENTS_COUNT=10

# Infrastructure URLs (for Docker Compose)
REDIS_URL=redis://redis:6379
POSTGRES_URL=postgresql://postgres:postgres_password@postgres:5432/flashloan
RABBITMQ_URL=amqp://rabbitmq:rabbitmq_password@rabbitmq:5672

# Docker Configuration
DOCKER_HOST=unix:///var/run/docker.sock
"""
    
    env_file = Path('.env.template')
    if not env_file.exists():
        env_file.write_text(env_template)
        print("Created .env.template - copy this to .env and configure your settings")

def check_docker():
    """Check if Docker is available and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Docker is available: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Docker daemon is running")
                return True
            else:
                print("Docker daemon is not running")
                return False
        else:
            print("Docker is not installed")
            return False
    except FileNotFoundError:
        print("Docker command not found")
        return False

def build_containers():
    """Build Docker containers"""
    print("Building Docker containers...")
    
    try:
        # Build orchestrator
        print("Building orchestrator container...")
        subprocess.run([
            'docker', 'build', 
            '-t', 'langchain-orchestrator',
            './containers/orchestrator'
        ], check=True)
        
        # Build MCP servers
        print("Building MCP servers container...")
        subprocess.run([
            'docker', 'build',
            '-t', 'mcp-server',
            './containers/mcp_servers'
        ], check=True)
        
        # Build agents
        print("Building agents container...")
        subprocess.run([
            'docker', 'build',
            '-t', 'langchain-agent', 
            './containers/agents'
        ], check=True)
        
        print("All containers built successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error building containers: {e}")
        return False

def launch_system(detached=True):
    """Launch the complete system using Docker Compose"""
    print("Launching Enhanced LangChain System...")
    
    compose_file = 'docker-compose-enhanced-langchain.yml'
    if not Path(compose_file).exists():
        print(f"Error: {compose_file} not found")
        return False
    
    try:
        cmd = ['docker-compose', '-f', compose_file, 'up']
        if detached:
            cmd.append('-d')
        
        subprocess.run(cmd, check=True)
        
        if detached:
            print("System launched successfully in detached mode")
            print("Use 'docker-compose -f docker-compose-enhanced-langchain.yml logs -f' to view logs")
            print("Use 'docker-compose -f docker-compose-enhanced-langchain.yml down' to stop the system")
        else:
            print("System launched successfully")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error launching system: {e}")
        return False

def stop_system():
    """Stop the system"""
    print("Stopping Enhanced LangChain System...")
    
    try:
        subprocess.run([
            'docker-compose', '-f', 'docker-compose-enhanced-langchain.yml', 'down'
        ], check=True)
        print("System stopped successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error stopping system: {e}")
        return False

def show_system_status():
    """Show system status"""
    print("Enhanced LangChain System Status:")
    
    try:
        # Show running containers
        result = subprocess.run([
            'docker-compose', '-f', 'docker-compose-enhanced-langchain.yml', 'ps'
        ], capture_output=True, text=True)
        
        print("\\nRunning Services:")
        print(result.stdout)
        
        # Show logs from orchestrator
        print("\\nOrchestrator Logs (last 10 lines):")
        subprocess.run([
            'docker-compose', '-f', 'docker-compose-enhanced-langchain.yml', 
            'logs', '--tail=10', 'orchestrator'
        ])
        
    except subprocess.CalledProcessError as e:
        print(f"Error getting system status: {e}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced LangChain System Launcher')
    parser.add_argument('action', choices=['setup', 'build', 'start', 'stop', 'status', 'restart'], 
                       help='Action to perform')
    parser.add_argument('--foreground', action='store_true', 
                       help='Run in foreground (default: detached)')
    
    args = parser.parse_args()
    
    if args.action == 'setup':
        print("Setting up Enhanced LangChain System...")
        setup_environment()
        create_required_directories()
        create_dockerfiles()
        create_requirements_files()
        create_env_template()
        print("Setup completed successfully!")
        print("Next steps:")
        print("1. Copy .env.template to .env and configure your settings")
        print("2. Run: python launch_system.py build")
        print("3. Run: python launch_system.py start")
    
    elif args.action == 'build':
        if not check_docker():
            sys.exit(1)
        
        if not build_containers():
            sys.exit(1)
        
        print("Build completed successfully!")
    
    elif args.action == 'start':
        if not check_docker():
            sys.exit(1)
        
        if not launch_system(detached=not args.foreground):
            sys.exit(1)
    
    elif args.action == 'stop':
        if not stop_system():
            sys.exit(1)
    
    elif args.action == 'status': 
        show_system_status()
    
    elif args.action == 'restart':
        print("Restarting system...")
        stop_system()
        time.sleep(5)
        if not launch_system(detached=not args.foreground):
            sys.exit(1)

if __name__ == "__main__":
    main()
