FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install coordinator specific dependencies
RUN pip install --no-cache-dir \
    flask>=3.0.0 \
    flask-cors>=4.0.0 \
    aiohttp>=3.9.0 \
    redis>=5.0.0 \
    psycopg2-binary>=2.9.0 \
    sqlalchemy>=2.0.0 \
    web3>=6.11.0 \
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
# Wait for PostgreSQL to be ready\n\
echo "Waiting for PostgreSQL..."\n\
while ! nc -z postgres 5432; do\n\
  sleep 1\n\
done\n\
echo "PostgreSQL is ready!"\n\
\n\
# Set Python path\n\
export PYTHONPATH=/app:$PYTHONPATH\n\
\n\
# Start the MCP Coordinator\n\
echo "Starting MCP Coordinator..."\n\
cd /app && python core/coordinators/aave_flash_loan_coordinator.py\n\
' > /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9000/health || exit 1

# Expose port
EXPOSE 9000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]