#!/bin/sh
# Claude Desktop Bridge Startup Script

echo "🌉 Starting Claude Desktop Bridge Service..."

# Set environment variables
export NODE_ENV=${NODE_ENV:-production}
export PORT=${PORT:-8080}
export WEB_PORT=${WEB_PORT:-9090}

# Wait for dependencies
echo "⏳ Waiting for Redis..."
until nc -z redis 6379; do
    sleep 1
done

echo "⏳ Waiting for PostgreSQL..."
until nc -z postgres 5432; do
    sleep 1
done

echo "✅ Dependencies ready"

# Start the Claude bridge service
echo "🚀 Starting Claude Desktop Bridge..."
node claude-bridge-server.js &

# Start the web interface
echo "🌐 Starting Web Interface..."
node web-interface-server.js &

# Wait for all processes
wait
