# Flash Loan Arbitrage Bot Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for any JavaScript dependencies
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy requirements first for better Docker layer caching
COPY requirements.txt /app/
COPY package.json package-lock.json /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies
RUN npm install

# Copy application code
COPY core/ /app/core/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY interfaces/ /app/interfaces/
COPY monitoring/ /app/monitoring/
COPY utilities/ /app/utilities/
COPY *.py /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/data/cache /app/data/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV NODE_ENV=production
ENV ARBITRAGE_MODE=production

# Expose ports
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the arbitrage bot
CMD ["python", "core/trading/unified_arbitrage_system.py"]
