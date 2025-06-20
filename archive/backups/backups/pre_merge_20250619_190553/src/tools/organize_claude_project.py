#!/usr/bin/env python3
"""
Flash Loan Project Organization Script
Organizes Docker, MCP, and AI Agent setup for Claude integration
"""

import os
import json
import shutil
# import subprocess (unused) removed
from pathlib import Path
from typing import Dict, Any

class ProjectOrganizer:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.docker_dir = self.project_root / "docker"
        self.config_dir = self.project_root / "config"
        
    def create_directory_structure(self):
        """Create organized directory structure"""
        print("📁 Creating organized directory structure...")
        
        # Main directories
        directories = [
            "docker/claude",
            "docker/mcp", 
            "docker/ai",
            "docker/monitoring",
            "config/claude",
            "config/mcp",
            "config/ai",
            "logs/claude",
            "logs/mcp", 
            "logs/ai",
            "data/claude",
            "data/mcp",
            "data/ai",
            "monitoring/prometheus",
            "monitoring/grafana",
            "web-ui/claude",
            "scripts/claude",
            "scripts/docker",
            "documentation/claude",
            "documentation/setup"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}")
    
    def organize_docker_files(self):
        """Organize Docker-related files"""
        print("\n🐳 Organizing Docker files...")
        
        # Docker files organization
        docker_files = {
            "docker-compose-claude.yml": "docker/claude/",
            "docker-compose-simple.yml": "docker/",
            "Dockerfile.arbitrage": "docker/",
            "Dockerfile.price": "docker/", 
            "Dockerfile.aave": "docker/",
            "claude-bridge-server.js": "docker/claude/",
        }
        
        for file_name, target_dir in docker_files.items():
            source_path = self.project_root / file_name
            target_path = self.project_root / target_dir / file_name
            
            if source_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if not target_path.exists():
                    shutil.copy2(source_path, target_path)
                    print(f"✅ Moved: {file_name} → {target_dir}")
    
    def organize_mcp_servers(self):
        """Organize MCP server files"""
        print("\n🔌 Organizing MCP servers...")
        
        mcp_servers = [
            "working_flash_loan_mcp.py",
            "simple_mcp_server.py", 
            "minimal-mcp-server.py",
        ]
        
        # Create MCP server directory structure
        mcp_dir = self.project_root / "mcp_servers_organized"
        mcp_dir.mkdir(exist_ok=True)
        
        for server in mcp_servers:
            source_path = self.project_root / server
            target_path = mcp_dir / server
            
            if source_path.exists() and not target_path.exists():
                shutil.copy2(source_path, target_path)
                print(f"✅ Organized: {server}")
    
    def organize_ai_agents(self):
        """Organize AI agent files"""
        print("\n🤖 Organizing AI agents...")
        
        # AI agent organization
        ai_files = {
            "ai_agent/unified_agent.py": "agents/unified/",
            "agents/": "agents/specialized/",
        }
        
        for source, target in ai_files.items():
            source_path = self.project_root / source
            target_path = self.project_root / target
            
            if source_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ AI agents organized in: {target}")
    
    def create_configuration_files(self):
        """Create organized configuration files"""
        print("\n⚙️ Creating configuration files...")
        
        # Claude Desktop configuration for Docker
        claude_config: Dict[str, Any] = {
            "mcpServers": {
                "docker-flash-loan": {
                    "command": "docker",
                    "args": ["exec", "claude-mcp-flash-loan", "python", "working_flash_loan_mcp.py"],
                    "env": {
                        "DOCKER_MODE": "true"
                    }
                },
                "docker-price-monitor": {
                    "command": "docker", 
                    "args": ["exec", "claude-mcp-price-monitor", "python", "real_time_price_mcp_server.py"],
                    "env": {
                        "DOCKER_MODE": "true"
                    }
                },
                "docker-aave": {
                    "command": "docker",
                    "args": ["exec", "claude-mcp-aave", "python", "aave_flash_loan_mcp_server.py"],
                    "env": {
                        "DOCKER_MODE": "true"
                    }
                }
            }
        }
        
        claude_config_path = self.config_dir / "claude" / "claude_desktop_docker_config.json"
        claude_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(claude_config_path, 'w') as f:
            json.dump(claude_config, f, indent=2)
        
        print(f"✅ Created Claude Docker config: {claude_config_path}")
    
    def create_startup_scripts(self):
        """Create organized startup scripts"""
        print("\n🚀 Creating startup scripts...")
        
        # Main startup script
        startup_script = """#!/bin/bash
# Flash Loan Claude Docker Startup Script

echo "🤖 Starting Flash Loan Claude System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Start Claude services
echo "🚀 Starting Claude services..."
docker compose -f docker/claude/docker-compose-claude.yml up -d

echo "⏳ Waiting for services to start..."
sleep 30

# Health checks
echo "🏥 Performing health checks..."
curl -f http://localhost:8080/health || echo "⚠️ Claude Bridge not ready"
curl -f http://localhost:8900/health || echo "⚠️ MCP Coordinator not ready"
curl -f http://localhost:7000/health || echo "⚠️ AI Coordinator not ready"

echo "🎉 Claude system startup complete!"
echo "📍 Access URLs:"
echo "  - Claude Bridge: http://localhost:8080"
echo "  - Web UI: http://localhost:3000"
echo "  - MCP Coordinator: http://localhost:8900"
echo "  - AI Coordinator: http://localhost:7000"
"""
        
        startup_path = self.project_root / "scripts" / "start_claude_system.sh"
        startup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(startup_path, 'w') as f:
            f.write(startup_script)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(startup_path, 0o755)
        
        print(f"✅ Created startup script: {startup_path}")
    
    def create_documentation(self):
        """Create comprehensive documentation"""
        print("\n📚 Creating documentation...")
        
        readme_content = r"""# Claude Docker Setup for Flash Loan Project

## Overview
This directory contains the organized Docker setup for integrating Claude with your flash loan arbitrage system.

## Architecture

### 🐳 Docker Services
- **Claude Desktop Bridge**: Integrates Claude Desktop with MCP servers
- **MCP Coordinator**: Manages Model Context Protocol servers
- **Flash Loan MCP**: Handles flash loan arbitrage logic
- **Price Monitor MCP**: Real-time cryptocurrency price monitoring
- **Aave MCP**: Aave protocol integration
- **AI Agents**: Intelligent automation and analysis

### 🔌 MCP Servers
- Port 8901: Flash Loan Arbitrage
- Port 8902: Real-time Price Monitor
- Port 8903: Aave Protocol
- Port 8904: Simple Flash Loan
- Port 8905: Blockchain Integration

### 🤖 AI Agents
- Port 7000: AI Coordinator
- Port 7001: Code Analysis Agent
- Port 7002: Trading Strategy Agent

## Quick Start

1. **Start the system**:
   ```bash
   ./scripts/start_claude_system.sh
   ```

2. **Or use the PowerShell manager**:
   ```powershell
   .\claude_docker_manager.ps1
   ```

3. **Configure Claude Desktop**:
   - Copy `config/claude/claude_desktop_docker_config.json` to Claude Desktop config
   - Restart Claude Desktop
   - Start a new conversation

## Access URLs
- Claude Bridge: http://localhost:8080
- Web UI: http://localhost:3000
- MCP Coordinator: http://localhost:8900
- AI Coordinator: http://localhost:7000
- Monitoring: http://localhost:3001

## Configuration
- Environment variables: `.env.claude`
- MCP config: `config/claude/claude_mcp_config.json`
- Docker compose: `docker/claude/docker-compose-claude.yml`

## Troubleshooting
- Check service health: `docker compose -f docker-compose-claude.yml ps`
- View logs: `docker compose -f docker-compose-claude.yml logs -f`
- Restart services: `docker compose -f docker-compose-claude.yml restart`

## Development
- Logs directory: `logs/`
- Data directory: `data/`
- Configuration: `config/`
"""
        
        readme_path = self.project_root / "documentation" / "claude" / "README.md"
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print(f"✅ Created documentation: {readme_path}")
    
    def create_monitoring_config(self):
        """Create monitoring configuration"""
        print("\n📊 Creating monitoring configuration...")
        
        # Prometheus configuration
        prometheus_config = """
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'claude-bridge'
    static_configs:
      - targets: ['claude-desktop-bridge:8080']
  
  - job_name: 'mcp-coordinator'
    static_configs:
      - targets: ['mcp-coordinator:8900']
  
  - job_name: 'ai-coordinator'
    static_configs:
      - targets: ['ai-agent-coordinator:7000']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
"""
        
        prometheus_path = self.project_root / "monitoring" / "prometheus" / "prometheus.yml"
        prometheus_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(prometheus_path, 'w') as f:
            f.write(prometheus_config)
        
        print(f"✅ Created Prometheus config: {prometheus_path}")
    
    def run_organization(self):
        """Run complete project organization"""
        print("🎯 Starting Flash Loan Project Organization for Claude...")
        print("=" * 60)
        
        try:
            self.create_directory_structure()
            self.organize_docker_files()
            self.organize_mcp_servers()
            self.organize_ai_agents()
            self.create_configuration_files()
            self.create_startup_scripts()
            self.create_documentation()
            self.create_monitoring_config()
            
            print("\n🎉 Project organization completed successfully!")
            print("\n📋 Next Steps:")
            print("1. Review the generated configuration files")
            print("2. Update environment variables in .env.claude")
            print("3. Start the system: ./scripts/start_claude_system.sh")
            print("4. Or use PowerShell: .\\claude_docker_manager.ps1")
            print("5. Configure Claude Desktop with the generated config")
            
            print("\n📁 Organized Structure:")
            print("- docker/: Docker configurations and files")
            print("- config/: Configuration files")
            print("- scripts/: Startup and management scripts")
            print("- documentation/: Setup and usage guides")
            print("- monitoring/: Prometheus and Grafana configs")
            
        except Exception as e:
            print(f"\n❌ Organization failed: {str(e)}")
            return False
        
        return True

def main():
    """Main function"""
    organizer = ProjectOrganizer()
    organizer.run_organization()

if __name__ == "__main__":
    main()
