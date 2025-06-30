# Multi-stage build for MCP servers
FROM python:3.11-slim as base

# Build arguments
ARG SERVER_TYPE
ARG SERVER_PATH

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MCP_SERVER_TYPE=${SERVER_TYPE}
ENV MCP_SERVER_PATH=${SERVER_PATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY mcp_servers/requirements.txt ./mcp_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r mcp_requirements.txt

# Install additional MCP-specific dependencies
RUN pip install --no-cache-dir \
    fastmcp>=0.9.0 \
    mcp>=1.0.0 \
    aiohttp>=3.9.0 \
    redis>=5.0.0 \
    web3>=6.11.0 \
    flask>=3.0.0 \
    flask-cors>=4.0.0 \
    python-dotenv>=1.0.0 \
    structlog>=23.0.0 \
    prometheus-client>=0.19.0

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Wait for Redis to be ready\n\
echo "Waiting for Redis..."\n\
while ! nc -z redis 6379; do\n\
  sleep 1\n\
done\n\
echo "Redis is ready!"\n\
\n\
# Set Python path\n\
export PYTHONPATH=/app:$PYTHONPATH\n\
\n\
# Start the MCP server based on type\n\
case "$MCP_SERVER_TYPE" in\n\
  "context7")\n\
    echo "Starting Context7 MCP Server..."\n\
    cd /app && python mcp_servers/ai_integration/clean_context7_mcp_server.py\n\
    ;;\n\
  "grok3")\n\
    echo "Starting Grok3 MCP Server..."\n\
    cd /app && python mcp_servers/ai_integration/start_grok3.py\n\
    ;;\n\
  "enhanced_copilot")\n\
    echo "Starting Enhanced Copilot MCP Server..."\n\
    cd /app && python mcp_servers/ai_integration/working_enhanced_copilot_mcp_server.py\n\
    ;;\n\
  "matic")\n\
    echo "Starting Matic MCP Server..."\n\
    cd /app && python mcp_servers/blockchain_integration/clean_matic_mcp_server.py\n\
    ;;\n\
  "evm")\n\
    echo "Starting EVM MCP Server..."\n\
    cd /app && python mcp_servers/blockchain_integration/evm-mcp-server/evm_mcp_server.py\n\
    ;;\n\
  "foundry")\n\
    echo "Starting Foundry MCP Server..."\n\
    cd /app && python mcp_servers/blockchain_integration/working_enhanced_foundry_mcp_server.py\n\
    ;;\n\
  "flash_loan_blockchain")\n\
    echo "Starting Flash Loan Blockchain MCP Server..."\n\
    cd /app && python mcp_servers/blockchain_integration/working_flash_loan_mcp.py\n\
    ;;\n\
  "price_oracle")\n\
    echo "Starting Price Oracle MCP Server..."\n\
    cd /app && python mcp_servers/data_providers/price-oracle-mcp-server/price_oracle_mcp_server.py\n\
    ;;\n\
  "dex_price")\n\
    echo "Starting DEX Price MCP Server..."\n\
    cd /app && python mcp_servers/data_providers/dex_price_mcp_server.py\n\
    ;;\n\
  "contract_executor")\n\
    echo "Starting Contract Executor MCP Server..."\n\
    cd /app && python mcp_servers/execution/mcp_contract_executor_server.py\n\
    ;;\n\
  "flash_loan_strategist")\n\
    echo "Starting Flash Loan Strategist MCP Server..."\n\
    cd /app && python mcp_servers/execution/mcp_flash_loan_strategist_server.py\n\
    ;;\n\
  "enhanced_coordinator")\n\
    echo "Starting Enhanced Coordinator MCP Server..."\n\
    cd /app && python mcp_servers/coordination/mcp_enhanced_coordinator.py\n\
    ;;\n\
  "integration_bridge")\n\
    echo "Starting Integration Bridge MCP Server..."\n\
    cd /app && python mcp_servers/coordination/mcp_integration_bridge.py\n\
    ;;\n\
  "aave_flash_loan_executor")\n\
    echo "Starting Aave Flash Loan Executor MCP Server..."\n\
    cd /app && python mcp_servers/flash_loan/aave_flash_loan_mcp_server.py\n\
    ;;\n\
  "arbitrage_detector")\n\
    echo "Starting Arbitrage Detector MCP Server..."\n\
    cd /app && python mcp_servers/analytics/arbitrage_detector_mcp_server.py\n\
    ;;\n\
  *)\n\
    echo "Unknown server type: $MCP_SERVER_TYPE"\n\
    echo "Available types: context7, grok3, enhanced_copilot, matic, evm, foundry, flash_loan_blockchain, price_oracle, dex_price, contract_executor, flash_loan_strategist, enhanced_coordinator, integration_bridge, aave_flash_loan_executor, arbitrage_detector"\n\
    exit 1\n\
    ;;\n\
esac\n\
' > /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Install netcat for health checks
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${MCP_PORT:-8000}/health || exit 1

# Expose port (will be overridden by environment)
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]