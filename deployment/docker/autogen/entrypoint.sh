#!/bin/bash

# AutoGen Multi-Agent System Entrypoint Script
# ============================================
# Handles proper service initialization, dependencies, and health checks

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    fi
}

# Environment variables with defaults
export REDIS_URL="${REDIS_URL:-redis://redis:6379}"
export POSTGRES_URL="${POSTGRES_URL:-postgresql://postgres:password@postgres:5432/flash_loan}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434/v1}"
export SERVICE_PORT="${SERVICE_PORT:-8000}"
export HOST="${HOST:-0.0.0.0}"
export MAX_ROUND="${MAX_ROUND:-10}"
export AUTOGEN_LOG_LEVEL="${AUTOGEN_LOG_LEVEL:-INFO}"
export PYTHONPATH="/app:${PYTHONPATH:-}"

# Cleanup function for graceful shutdown
cleanup() {
    log_info "Received shutdown signal, cleaning up..."
    if [[ -n "${MAIN_PID:-}" ]]; then
        log_info "Stopping main process (PID: $MAIN_PID)..."
        kill -TERM "$MAIN_PID" 2>/dev/null || true
        wait "$MAIN_PID" 2>/dev/null || true
    fi
    log_info "Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT SIGQUIT

# Function to wait for service availability
wait_for_service() {
    local service_name="$1"
    local host="$2"
    local port="$3"
    local max_attempts="${4:-30}"
    local attempt=1

    log_info "Waiting for $service_name at $host:$port..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
            log_info "$service_name is available!"
            return 0
        fi
        
        log_debug "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    log_error "$service_name is not available after $max_attempts attempts"
    return 1
}

# Function to check Redis connectivity
check_redis() {
    log_info "Checking Redis connection..."
    
    # Extract host and port from REDIS_URL
    local redis_host=$(echo "$REDIS_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    local redis_port=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
    
    redis_host="${redis_host:-redis}"
    redis_port="${redis_port:-6379}"
    
    if wait_for_service "Redis" "$redis_host" "$redis_port" 30; then
        # Test Redis with actual connection
        if timeout 10 redis-cli -h "$redis_host" -p "$redis_port" ping >/dev/null 2>&1; then
            log_info "Redis connection test successful"
            return 0
        else
            log_warn "Redis ping failed, but port is open. Service may still be starting..."
            return 0
        fi
    else
        log_warn "Redis is not available, continuing with degraded functionality..."
        return 1
    fi
}

# Function to check PostgreSQL connectivity
check_postgres() {
    log_info "Checking PostgreSQL connection..."
    
    # Extract components from POSTGRES_URL
    if [[ "$POSTGRES_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        local pg_user="${BASH_REMATCH[1]}"
        local pg_pass="${BASH_REMATCH[2]}"
        local pg_host="${BASH_REMATCH[3]}"
        local pg_port="${BASH_REMATCH[4]}"
        local pg_db="${BASH_REMATCH[5]}"
        
        if wait_for_service "PostgreSQL" "$pg_host" "$pg_port" 30; then
            # Test PostgreSQL with actual connection
            export PGPASSWORD="$pg_pass"
            if timeout 10 psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -d "$pg_db" -c "SELECT 1;" >/dev/null 2>&1; then
                log_info "PostgreSQL connection test successful"
                return 0
            else
                log_warn "PostgreSQL connection failed, but port is open. Service may still be starting..."
                return 0
            fi
        else
            log_warn "PostgreSQL is not available, continuing without database..."
            return 1
        fi
    else
        log_warn "Invalid PostgreSQL URL format, skipping database check..."
        return 1
    fi
}

# Function to check Ollama connectivity
check_ollama() {
    log_info "Checking Ollama connection..."
    
    local ollama_host=$(echo "$OLLAMA_HOST" | sed 's|http://||' | sed 's|/.*||' | cut -d':' -f1)
    local ollama_port=$(echo "$OLLAMA_HOST" | sed 's|http://||' | sed 's|/.*||' | cut -d':' -f2)
    
    ollama_host="${ollama_host:-ollama}"
    ollama_port="${ollama_port:-11434}"
    
    if wait_for_service "Ollama" "$ollama_host" "$ollama_port" 15; then
        log_info "Ollama is available"
        return 0
    else
        log_warn "Ollama is not available, will use other LLM providers..."
        return 1
    fi
}

# Function to initialize directories and permissions
init_directories() {
    log_info "Initializing directories and permissions..."
    
    # Create necessary directories
    mkdir -p /app/logs
    mkdir -p /app/data
    mkdir -p /app/models
    mkdir -p /app/autogen_work
    mkdir -p /app/conversation_logs
    mkdir -p /app/agent_memory
    mkdir -p /app/configs
    mkdir -p /app/tmp
    
    # Set proper permissions (only if running as root)
    if [[ $EUID -eq 0 ]]; then
        chown -R autogen:autogen /app/logs /app/data /app/models /app/autogen_work /app/conversation_logs /app/agent_memory /app/configs /app/tmp 2>/dev/null || true
    fi
    
    log_info "Directory initialization completed"
}

# Function to validate environment
validate_environment() {
    log_info "Validating environment configuration..."
    
    # Check required Python modules
    python -c "import autogen" 2>/dev/null || {
        log_error "AutoGen not properly installed"
        exit 1
    }
    
    python -c "import fastapi" 2>/dev/null || {
        log_error "FastAPI not properly installed"
        exit 1
    }
    
    python -c "import redis" 2>/dev/null || {
        log_error "Redis client not properly installed"
        exit 1
    }
    
    # Check if main.py exists
    if [[ ! -f "/app/main.py" ]]; then
        log_error "main.py not found in /app"
        exit 1
    fi
    
    # Validate configuration
    if [[ -z "$OPENAI_API_KEY" ]]; then
        log_warn "OPENAI_API_KEY not set, will use Ollama or other providers"
    fi
    
    log_info "Environment validation completed"
}

# Function to run health checks
run_health_checks() {
    log_info "Running pre-startup health checks..."
    
    local redis_ok=false
    local postgres_ok=false
    local ollama_ok=false
    
    check_redis && redis_ok=true
    check_postgres && postgres_ok=true
    check_ollama && ollama_ok=true
    
    log_info "Health check summary:"
    log_info "  Redis: $(if $redis_ok; then echo "✓ OK"; else echo "✗ Failed"; fi)"
    log_info "  PostgreSQL: $(if $postgres_ok; then echo "✓ OK"; else echo "✗ Failed"; fi)"
    log_info "  Ollama: $(if $ollama_ok; then echo "✓ OK"; else echo "✗ Failed"; fi)"
    
    # At least Redis should be available for full functionality
    if ! $redis_ok; then
        log_warn "Redis is not available - some features may be limited"
    fi
}

# Function to start the main application
start_application() {
    log_info "Starting AutoGen Multi-Agent System..."
    log_info "Configuration:"
    log_info "  Service Port: $SERVICE_PORT"
    log_info "  Max Rounds: $MAX_ROUND"
    log_info "  Log Level: $AUTOGEN_LOG_LEVEL"
    log_info "  Work Directory: $AUTOGEN_WORK_DIR"
    
    # Execute the main command in the background
    exec "$@" &
    MAIN_PID=$!
    
    log_info "Main process started with PID: $MAIN_PID"
    
    # Wait for the main process
    wait "$MAIN_PID"
    local exit_code=$?
    
    log_info "Main process exited with code: $exit_code"
    exit $exit_code
}

# Main execution flow
main() {
    log_info "🚀 Starting AutoGen Multi-Agent System initialization..."
    log_info "Environment: $(uname -a)"
    log_info "Python version: $(python --version)"
    log_info "Working directory: $(pwd)"
    
    # Initialize directories
    init_directories
    
    # Validate environment
    validate_environment
    
    # Run health checks
    run_health_checks
    
    # Start the application
    start_application "$@"
}

# Execute main function with all arguments
main "$@"