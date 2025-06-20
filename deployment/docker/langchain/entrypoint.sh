#!/bin/bash
# LangChain Multi-Agent System Entrypoint

set -e

echo "🚀 Starting LangChain Multi-Agent Flash Loan System..."

# Wait for dependencies
echo "⏳ Waiting for dependencies..."

# Wait for Redis
until redis-cli -h ${REDIS_HOST:-redis} -p ${REDIS_PORT:-6379} -a ${REDIS_PASSWORD:-""} ping > /dev/null 2>&1; do
    echo "Waiting for Redis to be ready..."
    sleep 2
done
echo "✅ Redis is ready"

# Wait for PostgreSQL
until pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-flashloan_user} > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Initialize database if needed
if [ "${DB_INIT:-false}" = "true" ]; then
    echo "🔧 Initializing database..."
    python scripts/init_db.py
fi

# Initialize vector store if needed
if [ "${VECTOR_STORE_INIT:-false}" = "true" ]; then
    echo "🔧 Initializing vector store..."
    python scripts/init_vector_store.py
fi

# Load AI models if needed
if [ "${LOAD_MODELS:-false}" = "true" ]; then
    echo "🤖 Loading AI models..."
    python scripts/load_models.py
fi

# Set up agent configurations
echo "🧠 Setting up agent configurations..."
python scripts/setup_agents.py

# Start the application
echo "🎯 Starting LangChain Multi-Agent System..."

# Start background services
python scripts/start_services.py &

# Start main application
exec "$@"
