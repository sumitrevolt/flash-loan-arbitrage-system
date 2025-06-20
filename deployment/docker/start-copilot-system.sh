#!/bin/bash

# GitHub Copilot Pro LangChain System Startup Script
# ==================================================

set -e

echo "🚀 Starting GitHub Copilot Pro LangChain Multi-Agent System..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.template .env
    echo "📝 Please edit .env file with your API keys before continuing."
    echo "   Required keys: OPENAI_API_KEY, GITHUB_TOKEN, GITHUB_COPILOT_API_KEY"
    exit 1
fi

# Check for required environment variables
echo "🔍 Checking environment variables..."

required_vars=("OPENAI_API_KEY" "GITHUB_TOKEN")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] && [ -z "$(grep "^$var=" .env | cut -d'=' -f2)" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '%s\n' "${missing_vars[@]}"
    echo "   Please set these in your .env file"
    exit 1
fi

echo "✅ Environment variables validated"

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker installation verified"

# Build and start containers
echo "🏗️  Building and starting containers..."
docker compose -f docker-compose.langchain-enhanced.yml down --remove-orphans
docker compose -f docker-compose.langchain-enhanced.yml build --no-cache
docker compose -f docker-compose.langchain-enhanced.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo "🏥 Performing health checks..."

services=(
    "redis:6379"
    "postgres:5432"
    "rabbitmq:15672"
    "langchain-coordinator:8000"
)

for service in "${services[@]}"; do
    name=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    echo "   Checking $name on port $port..."
    if timeout 10 bash -c "echo >/dev/tcp/localhost/$port"; then
        echo "   ✅ $name is ready"
    else
        echo "   ❌ $name is not responding"
    fi
done

# Test GitHub Copilot Pro agent
echo "🤖 Testing GitHub Copilot Pro agent..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")

if [ "$response" = "200" ]; then
    echo "✅ GitHub Copilot Pro agent is ready"
else
    echo "⚠️  GitHub Copilot Pro agent may not be fully ready (HTTP $response)"
fi

# Display service URLs
echo ""
echo "🌐 Service URLs:"
echo "   Main API:           http://localhost:8000"
echo "   Agent Coordination: http://localhost:8001"
echo "   RAG Service:        http://localhost:8003"
echo "   Code Interpreter:   http://localhost:8004"
echo "   Grafana Dashboard:  http://localhost:3000 (admin/admin)"
echo "   RabbitMQ Admin:     http://localhost:15672 (flash_loan_mq/flash_loan_mq_2025)"
echo "   Prometheus:         http://localhost:9090"
echo "   Health Check:       http://localhost:8080/health"
echo ""

echo "🎉 GitHub Copilot Pro LangChain System is running!"
echo ""
echo "📚 Quick Start Guide:"
echo "   1. Test the system: curl http://localhost:8000/health"
echo "   2. Generate code: curl -X POST http://localhost:8000/api/agents/github_copilot -H 'Content-Type: application/json' -d '{\"action\":\"generate_code\",\"specification\":\"Flash loan contract\"}'"
echo "   3. Review code: curl -X POST http://localhost:8000/api/agents/github_copilot -H 'Content-Type: application/json' -d '{\"action\":\"review_code\",\"code\":\"your_code_here\"}'"
echo "   4. View logs: docker logs flash-loan-langchain-coordinator"
echo "   5. Stop system: docker compose -f docker-compose.langchain-enhanced.yml down"
echo ""
echo "📖 For detailed documentation, see README_COPILOT.md"
