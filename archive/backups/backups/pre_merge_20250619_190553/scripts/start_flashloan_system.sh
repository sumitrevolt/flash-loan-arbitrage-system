#!/bin/bash

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found."
    echo "Please copy .env.example to .env and configure it with your credentials:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
required_vars=(
    "POSTGRES_PASSWORD"
    "GITHUB_TOKEN"
    "OPENAI_API_KEY" 
    "REDIS_PASSWORD"
    "ETHEREUM_RPC_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required variable $var is not set in .env"
        exit 1
    fi
done

# Start containers
echo "Starting containers..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to initialize
echo "Waiting for services to start..."
sleep 15

# Initialize services
echo "Initializing database..."
docker exec -it postgres-db psql -U $POSTGRES_USER -c "CREATE DATABASE flashloan;" || true

echo "Initializing Redis cluster..."
docker exec -it redis-cluster redis-cli --cluster create \
    $(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-cluster):6379 \
    --cluster-replicas 0 -a $REDIS_PASSWORD --cluster-yes || true

echo "Initializing GitHub Copilot..."
docker exec -it orchestrator gh auth login --with-token <<< "$GITHUB_TOKEN"
docker exec -it orchestrator github-copilot-cli auth

echo "Flash loan system started successfully!"
echo ""
echo "Access services:"
echo "- Grafana:    http://localhost:3000 (admin:$GRAFANA_PASSWORD)"
echo "- Prometheus: http://localhost:9090"
echo "- Orchestrator API: http://localhost:8080"