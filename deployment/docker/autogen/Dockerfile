# AutoGen Multi-Agent Flash Loan System
# Advanced AutoGen coordination with full infrastructure integration
FROM python:3.11-slim

# Metadata
LABEL name="AutoGen Flash Loan Coordinator"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-minimal.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/shared

# Create a simple shared module for fallback
RUN echo "# Cursor API Client Fallback" > /app/shared/__init__.py && \
    echo "class CursorAPIClient: pass" >> /app/shared/cursor_api_client.py && \
    echo "class CursorConfig: pass" >> /app/shared/cursor_api_client.py && \
    echo "class CursorMessage: pass" >> /app/shared/cursor_api_client.py && \
    echo "class CursorResponse: pass" >> /app/shared/cursor_api_client.py

# Set environment variables
ENV PYTHONPATH="/app:/app/shared"
ENV PYTHONUNBUFFERED=1

# Expose ports
# 8000: Main AutoGen coordination API
# 8001: Health monitoring
# 8002: Agent communication
# 8080: Web dashboard
EXPOSE 8000 8001 8002 8080

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Health check with comprehensive validation
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health && \
        curl -f http://localhost:8000/system/health-check || exit 1

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]