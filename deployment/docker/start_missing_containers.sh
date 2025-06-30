#!/bin/bash
# Script to start the missing langchain and autogen containers

echo "🔍 Checking for LangChain and AutoGen containers..."

# Function to check if container exists and is running
check_container() {
    local container_name=$1
    if docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name"; then
        status=$(docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep "$container_name" | awk '{print $2}')
        echo "✅ Container $container_name found: $status"
        return 0
    else
        echo "❌ Container $container_name not found"
        return 1
    fi
}

# Check current container status
echo "📊 Current container status:"
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "(langchain|autogen|coordinator)"

echo ""
echo "🚀 Starting missing containers..."

# Start LangChain coordinator if not running
if ! check_container "flash-loan-langchain-coordinator"; then
    echo "🔧 Starting LangChain coordinator..."
    cd /c/Users/Ratanshila/Documents/flash\ loan/deployment/docker
    docker-compose -f docker-compose.langchain-enhanced.yml up -d langchain-coordinator
fi

# Build and start AutoGen container
echo "🔧 Building AutoGen container..."
docker build -f docker/Dockerfile.autogen -t autogen-coordinator .

echo "🔧 Starting AutoGen container..."
docker run -d \
    --name autogen-coordinator \
    --network master-coordination-network \
    -p 8700:8000 \
    -e REDIS_URL="redis://:master_coordination_2025@master-redis:6379" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-dummy_key}" \
    autogen-coordinator

# Verify containers are running
echo ""
echo "✅ Final verification:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "(langchain|autogen)"

# Test container health
echo ""
echo "🏥 Health checks:"
if check_container "flash-loan-langchain-coordinator"; then
    echo "Testing LangChain health..."
    curl -f http://localhost:8600/health || echo "LangChain health check failed"
fi

if check_container "autogen-coordinator"; then
    echo "Testing AutoGen health..."
    curl -f http://localhost:8700/health || echo "AutoGen health check failed"
fi

echo "🎉 Container startup script completed!"