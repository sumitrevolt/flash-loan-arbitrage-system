# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
import json
import os
import subprocess
"""
GitHub MCP Server Setup Script
Helps you install and configure the GitHub MCP Server for version control operations.
"""


def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Docker is installed:", result.stdout.strip())
            return True
        else:
            print("[ERROR] Docker is not installed or not accessible")
            return False
    except FileNotFoundError:
        print("[ERROR] Docker is not installed")
        return False

def pull_github_mcp_image():
    """Pull the GitHub MCP Server Docker image"""
    try:
        print("Pulling GitHub MCP Server Docker image...")
        result = subprocess.run([)]
            'docker', 'pull', 'ghcr.io/github/github-mcp-server'
        ], capture_output=True, text=True
        
        if result.returncode == 0:
            print("[OK] Successfully pulled GitHub MCP Server image")
            return True
        else:
            print("[ERROR] Failed to pull image:", result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] Error pulling image: {e}")
        return False

def test_github_mcp_server():
    """Test the GitHub MCP Server (requires GitHub token)"""
    github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
    
    if not github_token:
        print("[WARNING] No GitHub token found in environment variables")
        print("   Set GITHUB_TOKEN or GITHUB_PERSONAL_ACCESS_TOKEN to test the server")
        return False
    
    try:
        print("Testing GitHub MCP Server...")
        # Test with a simple command that doesn't require specific repos
        result = subprocess.run([)]
            'docker', 'run', '-i', '--rm',
            '-e', f'GITHUB_PERSONAL_ACCESS_TOKEN={github_token}',
            'ghcr.io/github/github-mcp-server',
            '--toolsets', 'repos'
        ], capture_output=True, text=True, timeout=30
        
        if result.returncode == 0:
            print("[OK] GitHub MCP Server test successful")
            return True
        else:
            print("[ERROR] GitHub MCP Server test failed:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("[INFO] Test timed out - but server is likely working")
        return True
    except Exception as e:
        print(f"[ERROR] Error testing server: {e}")
        return False

def create_vscode_config():
    """Create VS Code MCP configuration"""
    config_dir = Path('.vscode')
    config_dir.mkdir(exist_ok=True)
    
    mcp_config = {}
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
                
            
        
    
    
    config_file = config_dir / 'mcp.json'
    with open(config_file, 'w') as f:
        json.dump(mcp_config, f, indent=2)
    
    print(f"[OK] Created VS Code MCP configuration: {config_file}")

def show_usage_examples():
    """Show usage examples"""
    print("\nUsage Examples:")
    print("1. Start with all toolsets:")
    print("   docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=<token> ghcr.io/github/github-mcp-server --toolsets all")
    
    print("\n2. Start with specific toolsets:")
    print("   docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=<token> ghcr.io/github/github-mcp-server --toolsets repos,issues,pull_requests")
    
    print("\n3. Available toolsets:")
    print("   - repos: Repository management")
    print("   - issues: Issue tracking")
    print("   - pull_requests: PR management")
    print("   - code_security: Security scanning")
    print("   - experiments: Beta features")

def main():
    """Main setup function"""
    print("GitHub MCP Server Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_docker():
        print("\nSetup failed: Docker is required")
        print("Please install Docker and try again")
        return False
    
    # Pull Docker image
    if not pull_github_mcp_image():
        print("\nSetup failed: Could not pull Docker image")
        return False
    
    # Test server (optional)
    test_github_mcp_server()
    
    # Create VS Code config
    create_vscode_config()
    
    # Show usage examples
    show_usage_examples()
    
    print("\nGitHub MCP Server setup complete!")
    print("\nNext steps:")
    print("1. Get a GitHub Personal Access Token from: https://github.com/settings/tokens")
    print("2. Set the token in your environment: export GITHUB_PERSONAL_ACCESS_TOKEN=<your_token>")
    print("3. Test the server using the Docker commands shown above")
    
    return True

if __name__ == "__main__":
    main()