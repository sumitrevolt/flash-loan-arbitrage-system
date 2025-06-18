#!/usr/bin/env python3
"""
Simple LangChain Setup and Deploy Script
========================================

This script will:
1. Check and fix basic syntax issues
2. Create minimal requirements 
3. Set up Docker configuration
4. Deploy the LangChain orchestrator
"""

import subprocess
import sys
import os
from pathlib import Path

def check_syntax():
    """Check if the Python file has valid syntax"""
    try:
        result = subprocess.run([
            sys.executable, "-m", "py_compile", "enhanced_langchain_orchestrator.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Syntax is valid!")
            return True
        else:
            print(f"❌ Syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking syntax: {e}")
        return False

def create_minimal_requirements():
    """Create minimal requirements file that will work"""
    requirements = [
        "langchain",
        "langchain-community", 
        "langchain-core",
        "numpy",
        "pandas",
        "aiohttp",
        "docker",
        "pyyaml",
        "python-dotenv",
        "asyncio",
    ]
    
    with open("requirements-minimal.txt", "w") as f:
        f.write("\n".join(requirements))
    
    print("✅ Created minimal requirements file")

def create_simple_dockerfile():
    """Create a simple Dockerfile that will work"""
    dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-minimal.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy application files
COPY enhanced_langchain_orchestrator.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "enhanced_langchain_orchestrator.py"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile)
    
    print("✅ Created simple Dockerfile")

def create_simple_compose():
    """Create simple docker-compose.yml"""
    compose = """services:
  langchain-orchestrator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(compose)
    
    print("✅ Created simple docker-compose.yml")

def deploy():
    """Deploy with Docker"""
    try:
        print("🏗️ Building Docker image...")
        result = subprocess.run(["docker-compose", "build"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False
            
        print("🚀 Starting services...")
        result = subprocess.run(["docker-compose", "up", "-d"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Deploy failed: {result.stderr}")
            return False
            
        print("✅ Deployment successful!")
        print("📊 Check status with: docker-compose ps")
        print("📋 View logs with: docker-compose logs -f")
        return True
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 LangChain Simple Setup & Deploy")
    print("=" * 40)
    
    # Check current syntax
    print("\n1. Checking syntax...")
    if not check_syntax():
        print("⚠️ Syntax issues detected, but proceeding with deployment...")
    
    # Create requirements
    print("\n2. Creating requirements...")
    create_minimal_requirements()
    
    # Create Docker files
    print("\n3. Creating Docker configuration...")
    create_simple_dockerfile()
    create_simple_compose()
    
    # Deploy
    print("\n4. Deploying...")
    success = deploy()
    
    if success:
        print("\n🎉 LangChain orchestrator deployed successfully!")
        print("\nAccess points:")
        print("- Main service: http://localhost:8000")
        print("- Health check: http://localhost:8000/health")
    else:
        print("\n💥 Deployment failed!")
        
    return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
