# Health Checker Service Docker Image
FROM python:3.11-slim

LABEL maintainer="Flash Loan Team"
LABEL description="System Health Checker for Unified Orchestration"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install requests psycopg2-binary redis pika

# Copy health checker script
COPY health_checker.py .
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/logs

# Create non-root user
RUN useradd -r -s /bin/false healthchecker && \
    chown -R healthchecker:healthchecker /app

USER healthchecker

# Health check for the health checker itself
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the health checker
CMD ["python", "health_checker.py"]