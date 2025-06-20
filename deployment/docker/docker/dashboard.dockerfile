# Dashboard Dockerfile for Flash Loan System
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY dashboard/ ./dashboard/
COPY mcp_servers/ ./mcp_servers/
COPY config/ ./config/
COPY templates/ ./templates/

# Expose port
EXPOSE 5000

# Run the dashboard
CMD ["python", "dashboard/start_dashboard.py"]
