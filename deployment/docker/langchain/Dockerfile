# LangChain Multi-Agent Flash Loan System
# Optimized for multi-agent coordination, RAG, tool use, and code interpretation
# Enhanced with NVIDIA Inference support for MCP server agents
FROM python:3.11-slim

LABEL maintainer="Flash Loan Team"
LABEL description="LangChain Multi-Agent System for Flash Loan Arbitrage"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements files
COPY requirements-basic.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-basic.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
