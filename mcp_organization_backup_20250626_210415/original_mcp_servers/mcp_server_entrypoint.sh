#!/bin/bash
set -e

# MCP Server Entrypoint Script
# Handles startup, health monitoring, and graceful shutdown

echo "🚀 Starting MCP Server: $MCP_SERVER_NAME"
echo "📁 Server File: $MCP_SERVER_FILE"
echo "🔌 Server Port: $MCP_SERVER_PORT"

# Environment setup
export PYTHONPATH="/app:$PYTHONPATH"
export MCP_LOG_LEVEL=${MCP_LOG_LEVEL:-INFO}
export MCP_ENABLE_METRICS=${MCP_ENABLE_METRICS:-true}

# Create necessary directories
mkdir -p /app/logs /app/data /app/config

# Log file for this server
LOG_FILE="/app/logs/${MCP_SERVER_NAME}.log"
ERROR_LOG="/app/logs/${MCP_SERVER_NAME}_error.log"

# Function to handle graceful shutdown
cleanup() {
    echo "🛑 Shutting down MCP server: $MCP_SERVER_NAME"
    if [ ! -z "$SERVER_PID" ]; then
        kill -TERM "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    echo "✅ MCP server shutdown complete"
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for dependencies (Redis, PostgreSQL, etc.)
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    
    echo "⏳ Waiting for $service_name at $host:$port..."
    
    for i in {1..30}; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $service_name is ready"
            return 0
        fi
        echo "   Attempt $i/30 - $service_name not ready, waiting..."
        sleep 2
    done
    
    echo "❌ Timeout waiting for $service_name"
    return 1
}

# Wait for core services if they're configured
if [ ! -z "$REDIS_URL" ]; then
    wait_for_service redis 6379 "Redis"
fi

if [ ! -z "$POSTGRES_URL" ]; then
    wait_for_service postgres 5432 "PostgreSQL"
fi

# Check if server file exists
if [ ! -f "/app/$MCP_SERVER_FILE" ]; then
    echo "❌ Error: Server file not found: /app/$MCP_SERVER_FILE"
    exit 1
fi

# Set up logging configuration
cat > /app/logging_config.json << EOF
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "$LOG_FILE",
            "formatter": "detailed",
            "level": "$MCP_LOG_LEVEL"
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": "$ERROR_LOG",
            "formatter": "detailed",
            "level": "ERROR"
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "level": "$MCP_LOG_LEVEL"
        }
    },
    "loggers": {
        "": {
            "handlers": ["file", "error_file", "console"],
            "level": "$MCP_LOG_LEVEL",
            "propagate": false
        }
    }
}
EOF

# Start the MCP server
echo "🔥 Starting MCP Server..."
echo "   Command: python /app/$MCP_SERVER_FILE"
echo "   Logs: $LOG_FILE"

# Run with proper error handling
{
    cd /app
    python "$MCP_SERVER_FILE" 2>&1 | tee -a "$LOG_FILE" &
    SERVER_PID=$!
    
    echo "📊 MCP Server started with PID: $SERVER_PID"
    
    # Monitor the process
    while kill -0 "$SERVER_PID" 2>/dev/null; do
        sleep 5
    done
    
    # Check exit status
    wait "$SERVER_PID"
    exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        echo "❌ MCP Server exited with code: $exit_code"
        exit $exit_code
    fi
    
} || {
    echo "❌ Failed to start MCP server"
    exit 1
}
