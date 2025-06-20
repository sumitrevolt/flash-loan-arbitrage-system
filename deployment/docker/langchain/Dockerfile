# LangChain Multi-Agent Flash Loan System
# Optimized for multi-agent coordination, RAG, tool use, and code interpretation
FROM python:3.11-slim

LABEL maintainer="Flash Loan Team"
LABEL description="LangChain Multi-Agent System for Flash Loan Arbitrage"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    nodejs \
    npm \
    redis-tools \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs \
    /app/data \
    /app/models \
    /app/vector_store \
    /app/agent_memory \
    /app/tools \
    /app/configs

# Set permissions
RUN chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 8000 8001 8002 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "main.py"]
