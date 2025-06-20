# Health Monitor Dockerfile for Flash Loan System
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY monitoring/ ./monitoring/
COPY mcp_servers/ ./mcp_servers/
COPY config/ ./config/

# Expose port (if needed)
EXPOSE 8888

# Run the health monitor
CMD ["python", "monitoring/health_monitor.py"]
