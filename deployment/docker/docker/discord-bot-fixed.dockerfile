FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Discord bot specific dependencies
RUN pip install --no-cache-dir \
    discord.py>=2.3.0 \
    aiohttp>=3.9.0 \
    redis>=5.0.0 \
    python-dotenv>=1.0.0

# Copy application code
COPY discord_bot/ ./discord_bot/
COPY config/ ./config/

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
# Wait for MCP Coordinator to be ready\n\
echo "Waiting for MCP Coordinator..."\n\
while ! nc -z mcp-coordinator 9000; do\n\
  sleep 1\n\
done\n\
echo "MCP Coordinator is ready!"\n\
\n\
# Start the Discord bot\n\
echo "Starting Discord Bot..."\n\
cd /app && python discord_bot/enhanced_flash_loan_bot.py\n\
' > /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import redis; r=redis.from_url('redis://redis:6379'); r.ping()" || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]