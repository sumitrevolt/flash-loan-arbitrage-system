#!/bin/bash
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
