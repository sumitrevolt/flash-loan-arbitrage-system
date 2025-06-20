#!/bin/bash
set -e

echo "🚀 Starting Enhanced LangChain Orchestrator..."

# Set up environment variables
export PYTHONPATH="/app:$PYTHONPATH"
export PYTHONUNBUFFERED=1
export REDIS_URL="redis://localhost:6379"
export REDIS_PASSWORD="langchain_redis_password_2025"

# Create necessary directories
mkdir -p /app/logs /app/data /app/config /tmp/langchain

# Set proper permissions
chown -R appuser:appuser /app/logs /app/data /app/config /tmp/langchain

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    
    echo "⏳ Waiting for $service_name to be ready..."
    while ! nc -z $host $port; do
        sleep 1
    done
    echo "✅ $service_name is ready!"
}

# Function to check and fix common issues
auto_fix_issues() {
    echo "🔧 Running auto-fix checks..."
    
    # Check Python syntax
    if ! python -m py_compile enhanced_langchain_orchestrator.py; then
        echo "❌ Python syntax error detected. Attempting to fix..."
        # Create a backup
        cp enhanced_langchain_orchestrator.py enhanced_langchain_orchestrator.py.backup
        
        # Basic syntax fixes
        sed -i 's/ADVANCED_ML_AVAILABLE/advanced_ml_available/g' enhanced_langchain_orchestrator.py
        sed -i 's/^      /    /g' enhanced_langchain_orchestrator.py  # Fix 6-space indentation
        sed -i '/^from langchain_openai import ChatOpenAI$/d' enhanced_langchain_orchestrator.py  # Remove duplicate imports
        sed -i '/^from langchain_community.llms import HuggingFacePipeline$/d' enhanced_langchain_orchestrator.py
        
        # Test again
        if python -m py_compile enhanced_langchain_orchestrator.py; then
            echo "✅ Syntax issues fixed automatically!"
        else
            echo "❌ Could not fix syntax issues automatically. Using backup."
            mv enhanced_langchain_orchestrator.py.backup enhanced_langchain_orchestrator.py
        fi
    fi
    
    # Check required environment variables
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "⚠️  Warning: OPENAI_API_KEY not set. Some features may not work."
    fi
    
    # Check disk space
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 90 ]; then
        echo "⚠️  Warning: Disk usage is ${DISK_USAGE}%. Cleaning up..."
        # Clean up temporary files
        find /tmp -type f -name "*.tmp" -delete 2>/dev/null || true
        find /app -name "*.pyc" -delete 2>/dev/null || true
        find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # Check memory usage
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ $MEMORY_USAGE -gt 90 ]; then
        echo "⚠️  Warning: Memory usage is ${MEMORY_USAGE}%. Consider increasing container memory."
    fi
    
    echo "✅ Auto-fix checks completed!"
}

# Function to setup health check endpoint
setup_health_check() {
    cat > /tmp/health_check.py << 'EOF'
import asyncio
import json
from aiohttp import web
import sys
import os
sys.path.append('/app')

async def health_check(request):
    """Health check endpoint"""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": "$(date -Iseconds)",
            "services": {
                "redis": "checking",
                "orchestrator": "checking"
            }
        }
        
        # Check Redis connection
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, password='langchain_redis_password_2025', decode_responses=True)
            r.ping()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check main orchestrator
        if os.path.exists('/app/enhanced_langchain_orchestrator.py'):
            health_status["services"]["orchestrator"] = "healthy"
        else:
            health_status["services"]["orchestrator"] = "unhealthy: file not found"
            health_status["status"] = "unhealthy"
        
        return web.json_response(health_status)
    except Exception as e:
        return web.json_response({
            "status": "unhealthy",
            "error": str(e)
        }, status=500)

app = web.Application()
app.router.add_get('/health', health_check)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8000)
EOF

    # Start health check service in background
    python /tmp/health_check.py &
    HEALTH_PID=$!
    echo $HEALTH_PID > /tmp/health_check.pid
}

# Function to monitor and restart services
monitor_services() {
    while true; do
        # Check if main orchestrator is running
        if ! pgrep -f "enhanced_langchain_orchestrator.py" > /dev/null; then
            echo "⚠️  Main orchestrator not running. Attempting restart..."
            cd /app
            python enhanced_langchain_orchestrator.py &
        fi
        
        # Check if health service is running
        if ! pgrep -f "health_check.py" > /dev/null; then
            echo "⚠️  Health check service not running. Restarting..."
            setup_health_check
        fi
        
        sleep 30
    done
}

# Main execution flow
echo "🔍 Running pre-flight checks..."
auto_fix_issues

echo "🏥 Setting up health check service..."
setup_health_check

# Switch to app user for main processes
echo "👤 Switching to application user..."
exec su -c "
    cd /app
    
    # Set environment for appuser
    export PYTHONPATH='/app:\$PYTHONPATH'
    export PYTHONUNBUFFERED=1
    export REDIS_URL='redis://localhost:6379'
    export REDIS_PASSWORD='langchain_redis_password_2025'
    
    echo '🎯 Starting main orchestrator...'
    python enhanced_langchain_orchestrator.py &
    MAIN_PID=\$!
    
    echo '📊 Starting service monitor...'
    $(declare -f monitor_services)
    monitor_services &
    MONITOR_PID=\$!
    
    # Wait for any process to exit
    wait \$MAIN_PID \$MONITOR_PID
" appuser
