#!/bin/bash

# Initialize GitHub CLI auth if token exists
if [ -f "/app/.github_token" ]; then
    gh auth login --with-token < /app/.github_token
fi

# Start GitHub Copilot daemon
nohup github-copilot-cli daemon > /var/log/copilot.log 2>&1 &

# Start MCP servers based on SERVER_TYPE environment variable
case "$SERVER_TYPE" in
    "flash_loan")
        exec python -m mcp_servers.flash_loan_mcp_server
        ;;
    "price_feed") 
        exec python -m mcp_servers.price_feed_mcp_server
        ;;
    "arbitrage")
        exec python -m mcp_servers.arbitrage_mcp_server
        ;;
    "risk_manager")
        exec python -m mcp_servers.risk_manager_mcp_server
        ;;
    *)
        echo "Starting generic MCP server"
        exec python -m mcp_servers.mcp_server_base
        ;;
esac