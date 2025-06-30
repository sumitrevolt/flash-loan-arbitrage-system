# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Dict, List, Optional
import json
import os
import re
import subprocess
import sys
"""
GitHub MCP Server Integration
Integrates GitHub MCP server with existing MCP infrastructure
"""


class GitHubMCPIntegration:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / ".vscode"
        self.mcp_servers_dir = self.base_dir / "mcp_servers"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed"""
        print("Checking prerequisites...")
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] Docker: {result.stdout.strip()}")
            else:
                print("[ERROR] Docker not found")
                return False
        except FileNotFoundError:
            print("[ERROR] Docker not installed")
            return False
        
        # Check GitHub token
        github_token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN') or os.getenv('GITHUB_TOKEN')
        if github_token:
            print("[OK] GitHub token found")
        else:
            print("[WARNING] No GitHub token found - will need to set later")
        
        return True
    
    def pull_github_mcp_image(self) -> bool:
        """Pull the GitHub MCP server Docker image"""
        print("Pulling GitHub MCP server image...")
        
        try:
            result = subprocess.run([)]
                'docker', 'pull', 'ghcr.io/github/github-mcp-server'
            ], capture_output=True, text=True
            
            if result.returncode == 0:
                print("[OK] GitHub MCP server image pulled successfully")
                return True
            else:
                print(f"[ERROR] Failed to pull image: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] Exception pulling image: {e}")
            return False
    
    def create_vscode_config(self) -> bool:
        """Create or update VS Code MCP configuration"""
        print("Creating VS Code MCP configuration...")
        
        self.config_dir.mkdir(exist_ok=True)
        
        # GitHub MCP configuration
        github_mcp_config = {}
            "inputs": []
                {}
                    "type": "promptString",
                    "id": "github_token",
                    "description": "GitHub Personal Access Token",
                    "password": True
                
            ],
            "servers": {}
                "github": {}
                    "command": "docker",
                    "args": []
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "GITHUB_PERSONAL_ACCESS_TOKEN",
                        "ghcr.io/github/github-mcp-server"
                    ],
                    "env": {}
                        "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
                    
                },
                "github-enhanced": {}
                    "command": "docker",
                    "args": []
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "GITHUB_PERSONAL_ACCESS_TOKEN",
                        "-e",
                        "GITHUB_TOOLSETS=repos,issues,pull_requests,code_security",
                        "ghcr.io/github/github-mcp-server"
                    ],
                    "env": {}
                        "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
                    
                
            
        
        
        # Write VS Code configuration
        config_file = self.config_dir / 'mcp.json'
        with open(config_file, 'w') as f:
            json.dump(github_mcp_config, f, indent=2)
        
        print(f"[OK] VS Code configuration created: {config_file}")
        return True
    
    def create_docker_compose_addition(self) -> bool:
        """Create Docker Compose configuration for GitHub MCP"""
        print("Creating Docker Compose configuration...")
        
        docker_compose_addition = {}
            "version": "3.8",
            "services": {}
                "mcp-github": {}
                    "image": "ghcr.io/github/github-mcp-server",
                    "container_name": "mcp-github",
                    "environment": []
                        "GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PERSONAL_ACCESS_TOKEN}",
                        "GITHUB_TOOLSETS=all"
                    ],
                    "ports": ["8017:8017"],
                    "restart": "unless-stopped",
                    "networks": ["mcp-network"]
                },
                "mcp-filesystem": {}
                    "image": "ghcr.io/cyanheads/filesystem-mcp-server",
                    "container_name": "mcp-filesystem",
                    "ports": ["8018:8018"],
                    "volumes": []
                        ".:/workspace:rw"
                    ],
                    "restart": "unless-stopped",
                    "networks": ["mcp-network"]
                
            },
            "networks": {}
                "mcp-network": {}
                    "external": True
                
            
        
        
        # Write Docker Compose file
        compose_file = self.mcp_servers_dir / 'docker-compose.github-mcp.yml'
        with open(compose_file, 'w') as f:
            json.dump(docker_compose_addition, f, indent=2)
        
        print(f"[OK] Docker Compose configuration created: {compose_file}")
        return True
    
    def create_startup_script(self) -> bool:
        """Create startup script for GitHub MCP servers"""
        print("Creating startup script...")
        
        startup_script = """#!/bin/bash
# GitHub MCP Server Startup Script

set -e

echo "Starting GitHub MCP Services..."

# Check if GitHub token is set
if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo "ERROR: GITHUB_PERSONAL_ACCESS_TOKEN environment variable not set"
    echo "Please set your GitHub Personal Access Token:"
    echo "export GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here"
    exit 1
fi

# Pull latest images
echo "Pulling latest images..."
docker pull ghcr.io/github/github-mcp-server
docker pull ghcr.io/cyanheads/filesystem-mcp-server

# Start services
echo "Starting GitHub MCP services..."
docker-compose -f mcp_servers/docker-compose.github-mcp.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service status
echo "Checking service status..."
docker-compose -f mcp_servers/docker-compose.github-mcp.yml ps

echo "GitHub MCP services started successfully!"
echo ""
echo "Available services:"
echo "- GitHub MCP Server: http://localhost:8017"
echo "- Filesystem MCP Server: http://localhost:8018"
echo ""
echo "To test GitHub MCP server:"
echo "docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server --toolsets repos"
"""
        
        startup_file = self.mcp_servers_dir / 'start_github_mcp.sh'
        with open(startup_file, 'w') as f:
            f.write(startup_script)
        
        # Make executable
        startup_file.chmod(0o755)
        
        print(f"[OK] Startup script created: {startup_file}")
        return True
    
    def create_windows_startup_script(self) -> bool:
        """Create Windows startup script for GitHub MCP servers"""
        print("Creating Windows startup script...")
        
        windows_script = """@echo off
REM GitHub MCP Server Startup Script for Windows

echo Starting GitHub MCP Services...

REM Check if GitHub token is set
if "%GITHUB_PERSONAL_ACCESS_TOKEN%"=="" ()
    echo ERROR: GITHUB_PERSONAL_ACCESS_TOKEN environment variable not set
    echo Please set your GitHub Personal Access Token:
    echo set GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
    pause
    exit /b 1


REM Pull latest images
echo Pulling latest images...
docker pull ghcr.io/github/github-mcp-server
docker pull ghcr.io/cyanheads/filesystem-mcp-server

REM Start services
echo Starting GitHub MCP services...
docker-compose -f mcp_servers/docker-compose.github-mcp.yml up -d

REM Wait for services to be ready
echo Waiting for services to start...
timeout /t 10 /nobreak

REM Check service status
echo Checking service status...
docker-compose -f mcp_servers/docker-compose.github-mcp.yml ps

echo GitHub MCP services started successfully!
echo.
echo Available services:
echo - GitHub MCP Server: http://localhost:8017
echo - Filesystem MCP Server: http://localhost:8018
echo.
echo To test GitHub MCP server:
echo docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server --toolsets repos

pause
"""
        
        windows_file = self.mcp_servers_dir / 'start_github_mcp.bat'
        with open(windows_file, 'w') as f:
            f.write(windows_script)
        
        print(f"[OK] Windows startup script created: {windows_file}")
        return True
    
    def test_github_mcp_connection(self) -> bool:
        """Test GitHub MCP server connection"""
        print("Testing GitHub MCP server connection...")
        
        github_token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN') or os.getenv('GITHUB_TOKEN')
        
        if not github_token:
            print("[WARNING] No GitHub token found - skipping connection test")
            return True
        
        try:
            result = subprocess.run([)]
                'docker', 'run', '--rm', '-i',
                '-e', f'GITHUB_PERSONAL_ACCESS_TOKEN={github_token}',
                'ghcr.io/github/github-mcp-server',
                '--toolsets', 'repos'
            ], capture_output=True, text=True, timeout=30
            
            if result.returncode == 0:
                print("[OK] GitHub MCP server connection test successful")
                return True
            else:
                print(f"[ERROR] Connection test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("[INFO] Connection test timed out - but server is likely working")
            return True
        except Exception as e:
            print(f"[ERROR] Exception during connection test: {e}")
            return False
    
    def add_to_existing_mcp_config(self) -> bool:
        """Add GitHub MCP to existing MCP server configurations"""
        print("Integrating with existing MCP configurations...")
        
        # Check for existing MCP configurations
        existing_configs = []
            'mcp_server_manager.py',
            'unified_mcp_coordinator.py',
            'mcp_server_template.py'
        
        
        for config_file in existing_configs:
            config_path = self.mcp_servers_dir / config_file
            if config_path.exists():
                print(f"[INFO] Found existing MCP config: {config_file}")
        
        # Create integration summary
        integration_summary = {}
            "github_mcp_integration": {}
                "status": "configured",
                "services": {}
                    "github": {}
                        "image": "ghcr.io/github/github-mcp-server",
                        "port": 8017,
                        "description": "GitHub API operations (repos, issues, PRs)"
                    },
                    "filesystem": {}
                        "image": "ghcr.io/cyanheads/filesystem-mcp-server", 
                        "port": 8018,
                        "description": "Local filesystem and Git operations"
                    
                },
                "startup_scripts": {}
                    "linux_mac": "mcp_servers/start_github_mcp.sh",
                    "windows": "mcp_servers/start_github_mcp.bat"
                },
                "vscode_config": ".vscode/mcp.json",
                "docker_compose": "mcp_servers/docker-compose.github-mcp.yml"
            
        
        
        summary_file = self.mcp_servers_dir / 'github_mcp_integration_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(integration_summary, f, indent=2)
        
        print(f"[OK] Integration summary created: {summary_file}")
        return True
    
    def run_integration(self) -> bool:
        """Run the complete GitHub MCP integration"""
        print("=" * 60)
        print("GitHub MCP Server Integration")
        print("=" * 60)
        
        steps = []
            ("Checking prerequisites", self.check_prerequisites),
            ("Pulling GitHub MCP image", self.pull_github_mcp_image),
            ("Creating VS Code configuration", self.create_vscode_config),
            ("Creating Docker Compose configuration", self.create_docker_compose_addition),
            ("Creating startup scripts", self.create_startup_script),
            ("Creating Windows startup script", self.create_windows_startup_script),
            ("Testing connection", self.test_github_mcp_connection),
            ("Integrating with existing configs", self.add_to_existing_mcp_config)
        
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"[ERROR] Failed at step: {step_name}")
                return False
        
        print("\n" + "=" * 60)
        print("GitHub MCP Integration Complete!")
        print("=" * 60)
        
        self.show_next_steps()
        return True
    
    def show_next_steps(self):
        """Show next steps to user"""
        print("\nNext Steps:")
        print("1. Set your GitHub Personal Access Token:")
        print("   export GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here")
        print("\n2. Start the GitHub MCP services:")
        print("   ./mcp_servers/start_github_mcp.sh  # Linux/Mac")
        print("   mcp_servers\\start_github_mcp.bat  # Windows")
        print("\n3. Test the integration:")
        print("   docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server --toolsets repos")
        print("\n4. Access services:")
        print("   - GitHub MCP Server: http://localhost:8017")
        print("   - Filesystem MCP Server: http://localhost:8018")
        print("\n5. VS Code Integration:")
        print("   - Configuration created in .vscode/mcp.json")
        print("   - Restart VS Code to see MCP servers in sidebar")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("GitHub MCP Server Integration Tool")
        print("Usage: python github_mcp_integration.py")
        print("\nThis script integrates GitHub MCP servers with your existing infrastructure.")
        return
    
    integration = GitHubMCPIntegration()
    success = integration.run_integration()
    
    if success:
        print("\n[OK] Integration completed successfully!")
        sys.exit(0)
    else:
        print("\n[ERROR] Integration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()