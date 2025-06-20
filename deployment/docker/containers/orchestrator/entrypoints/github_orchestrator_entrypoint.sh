#!/bin/bash
set -e

# Initialize GitHub CLI if token is provided
if [ -n "$GITHUB_TOKEN" ]; then
    echo "$GITHUB_TOKEN" | gh auth login --with-token
    echo "GitHub CLI authenticated successfully"
fi

# Wait for dependencies
echo "Waiting for Redis cluster..."
while ! nc -z redis-cluster 6379 2>/dev/null; do
  sleep 1
done
echo "Redis cluster is ready!"

echo "Waiting for PostgreSQL..."
while ! nc -z postgres-db 5432 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Set Python path
export PYTHONPATH=/app:$PYTHONPATH

# Start the orchestrator
echo "Starting GitHub Pro Enhanced Orchestrator..."
exec python -m uvicorn core.orchestrator.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 2 \
    --log-level info