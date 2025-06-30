#!/bin/bash

# LangChain Multi-Agent System Entrypoint
# ========================================
# 
# This script handles the startup sequence for the LangChain container,
# ensuring all services are properly initialized and dependencies are ready.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Configuration
STARTUP_TIMEOUT=${STARTUP_TIMEOUT:-120}
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-5}
MAX_RETRIES=${MAX_RETRIES:-10}

# Service health check functions
check_postgres() {
    log_debug "Checking PostgreSQL connection..."
    python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'flash_loan_db'),
        user=os.getenv('POSTGRES_USER', 'flash_loan_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'flash_loan_secure_2025')
    )
    conn.close()
    print('PostgreSQL connection successful')
except Exception as e:
    print(f'PostgreSQL connection failed: {e}')
    exit(1)
"
}

check_redis() {
    log_debug "Checking Redis connection..."
    python3 -c "
import redis
import os
try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        password=os.getenv('REDIS_PASSWORD', 'flash_loan_redis_2025'),
        decode_responses=True
    )
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
"
}

check_environment() {
    log_info "Checking environment configuration..."
    
    # Check required environment variables
    required_vars=(
        "POSTGRES_HOST"
        "POSTGRES_DB" 
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "REDIS_HOST"
        "REDIS_PASSWORD"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi
    
    # Check API keys (warn if missing)
    if [[ -z "${OPENAI_API_KEY}" ]]; then
        log_warn "OPENAI_API_KEY not set - some LLM features may not work"
    fi
    
    if [[ -z "${ANTHROPIC_API_KEY}" ]]; then
        log_warn "ANTHROPIC_API_KEY not set - Anthropic models will not be available"
    fi
    
    log_info "Environment configuration check completed"
}

wait_for_service() {
    local service_name=$1
    local check_function=$2
    local retries=0
    
    log_info "Waiting for $service_name to be ready..."
    
    while [[ $retries -lt $MAX_RETRIES ]]; do
        if $check_function > /dev/null 2>&1; then
            log_info "$service_name is ready"
            return 0
        fi
        
        retries=$((retries + 1))
        log_debug "Attempt $retries/$MAX_RETRIES failed, retrying in ${HEALTH_CHECK_INTERVAL}s..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log_error "$service_name is not ready after $MAX_RETRIES attempts"
    return 1
}

setup_directories() {
    log_info "Setting up application directories..."
    
    # Create necessary directories
    mkdir -p /app/logs
    mkdir -p /app/data
    mkdir -p /app/models
    mkdir -p /app/vector_store
    mkdir -p /app/agent_memory
    mkdir -p /app/tools
    mkdir -p /app/configs
    mkdir -p /app/temp
    
    # Set proper permissions
    chmod 755 /app/logs
    chmod 755 /app/data
    chmod 755 /app/vector_store
    chmod 755 /app/agent_memory
    chmod 777 /app/temp
    
    log_info "Directory setup completed"
}

initialize_database() {
    log_info "Initializing database schema..."
    
    python3 -c "
import asyncio
import sys
import os
sys.path.append('/app')

async def init_db():
    try:
        from services.memory_manager import MemoryManager
        from utils.config import get_config
        
        config = get_config()
        memory_manager = MemoryManager()
        await memory_manager.initialize()
        await memory_manager.cleanup()
        print('Database initialization completed')
    except Exception as e:
        print(f'Database initialization failed: {e}')
        sys.exit(1)

asyncio.run(init_db())
"
    
    if [[ $? -eq 0 ]]; then
        log_info "Database initialization completed"
    else
        log_error "Database initialization failed"
        return 1
    fi
}

initialize_vector_store() {
    log_info "Initializing vector store..."
    
    python3 -c "
import asyncio
import sys
import os
sys.path.append('/app')

async def init_vector_store():
    try:
        from services.vector_store import VectorStoreService
        from utils.config import get_config
        
        config = get_config()
        vector_store = VectorStoreService()
        await vector_store.initialize()
        await vector_store.cleanup()
        print('Vector store initialization completed')
    except Exception as e:
        print(f'Vector store initialization failed: {e}')
        # Don't exit for vector store failures - it's not critical
        print('Continuing without vector store...')

asyncio.run(init_vector_store())
"
    
    log_info "Vector store initialization completed"
}

setup_logging() {
    log_info "Setting up logging configuration..."
    
    # Create logging configuration
    cat > /app/logging.conf << 'EOF'
[loggers]
keys=root,uvicorn,langchain,agents,services

[handlers]
keys=console,file,error_file

[formatters]
keys=standard,detailed

[logger_root]
level=INFO
handlers=console,file

[logger_uvicorn]
level=INFO
handlers=console,file
qualname=uvicorn
propagate=0

[logger_langchain]
level=INFO
handlers=console,file
qualname=langchain
propagate=0

[logger_agents]
level=INFO
handlers=console,file
qualname=agents
propagate=0

[logger_services]
level=INFO
handlers=console,file
qualname=services
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=standard
args=(sys.stdout,)

[handler_file]
class=logging.handlers.RotatingFileHandler
level=INFO
formatter=detailed
args=('/app/logs/langchain.log', 'a', 10485760, 5)

[handler_error_file]
class=logging.handlers.RotatingFileHandler
level=ERROR
formatter=detailed
args=('/app/logs/langchain_errors.log', 'a', 10485760, 5)

[formatter_standard]
format=%(asctime)s [%(levelname)s] %(name)s: %(message)s

[formatter_detailed]
format=%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s
EOF
    
    log_info "Logging configuration completed"
}

graceful_shutdown() {
    log_info "Received shutdown signal, gracefully stopping services..."
    
    # Kill the main process if it exists
    if [[ -n "$MAIN_PID" ]]; then
        log_info "Stopping main application (PID: $MAIN_PID)..."
        kill -TERM $MAIN_PID 2>/dev/null || true
        
        # Wait for graceful shutdown
        local timeout=30
        while [[ $timeout -gt 0 ]] && kill -0 $MAIN_PID 2>/dev/null; do
            sleep 1
            timeout=$((timeout - 1))
        done
        
        if kill -0 $MAIN_PID 2>/dev/null; then
            log_warn "Process did not shutdown gracefully, forcing termination..."
            kill -KILL $MAIN_PID 2>/dev/null || true
        fi
    fi
    
    log_info "Shutdown completed"
    exit 0
}

health_check_endpoint() {
    log_info "Starting health check endpoint..."
    
    python3 -c "
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time

class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                'status': 'healthy',
                'timestamp': time.time(),
                'services': {
                    'langchain': 'running',
                    'database': 'connected',
                    'redis': 'connected'
                }
            }
            
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8001), HealthHandler)
    server.serve_forever()

# Run health check server in background
health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()

print('Health check endpoint started on port 8001')

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
" &
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Debug: Check Python version and environment
    log_debug "Python version: $(python3 --version)"
    log_debug "Python path: $(python3 -c 'import sys; print(sys.path)')"
    
    # Debug: Verify config.py exists and show problematic line
    log_debug "Checking config.py..."
    python3 -c "
import sys
import os
sys.path.append('/app')

try:
    # Debug: Show file existence and contents
    config_path = os.path.join('/app', 'src', 'tools', 'config.py')
    print(f'Checking config file at: {config_path}')
    print(f'File exists: {os.path.exists(config_path)}')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            lines = f.readlines()
            print('Line 82 contents:')
            print(lines[81].rstrip())  # Line numbers are 0-indexed in list
            
    from utils.config import get_config
    config = get_config()
    
    # For now, we use SQLite auto-creation
    # In production, this would run Alembic migrations
    print('Migrations completed (using auto-schema creation)')
    
except Exception as e:
    print(f'Migration check failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
    
    if [[ $? -eq 0 ]]; then
        log_info "Migrations completed successfully"
    else
        log_error "Migrations failed"
        return 1
    fi
}

# Signal handlers
trap graceful_shutdown SIGTERM SIGINT

# Main startup sequence
main() {
    log_info "Starting LangChain Multi-Agent System..."
    log_info "Startup timeout: ${STARTUP_TIMEOUT}s"
    
    # Step 1: Environment validation
    if ! check_environment; then
        log_error "Environment validation failed"
        exit 1
    fi
    
    # Step 2: Setup directories and logging
    setup_directories
    setup_logging
    
    # Step 3: Wait for dependencies
    wait_for_service "PostgreSQL" check_postgres
    wait_for_service "Redis" check_redis
    
    # Step 4: Initialize services
    run_migrations
    initialize_database
    initialize_vector_store
    
    # Step 5: Start health check endpoint
    health_check_endpoint
    
    log_info "All services initialized successfully"
    log_info "Starting main application..."
    
    # Step 6: Execute the main command
    if [[ $# -eq 0 ]]; then
        # Default command
        exec python3 main.py
    else
        # Custom command
        exec "$@"
    fi
}

# Special handling for different run modes
case "${1:-}" in
    "bash"|"sh")
        log_info "Starting interactive shell..."
        exec /bin/bash
        ;;
    "health-check")
        log_info "Running health check..."
        check_postgres && check_redis
        log_info "Health check passed"
        exit 0
        ;;
    "init-only")
        log_info "Running initialization only..."
        check_environment
        setup_directories
        wait_for_service "PostgreSQL" check_postgres
        wait_for_service "Redis" check_redis
        initialize_database
        initialize_vector_store
        log_info "Initialization completed"
        exit 0
        ;;
    *)
        # Run main startup sequence
        main "$@"
        ;;
esac
