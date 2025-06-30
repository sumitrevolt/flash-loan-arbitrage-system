#!/bin/bash

# Unified Docker Orchestration System Startup Script
# ==================================================
# This script starts the complete unified system with proper dependency management,
# health checks, and service coordination.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.unified.yml"
ENV_FILE="$SCRIPT_DIR/.env"
LOG_FILE="$SCRIPT_DIR/logs/startup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_header() {
    echo -e "\n${PURPLE}========================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${PURPLE}$1${NC}" | tee -a "$LOG_FILE"
    echo -e "${PURPLE}========================================${NC}\n" | tee -a "$LOG_FILE"
}

# Cleanup function
cleanup() {
    log_warning "Script interrupted. Cleaning up..."
    exit 1
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Initialize logging
mkdir -p "$SCRIPT_DIR/logs"
echo "Startup log - $(date)" > "$LOG_FILE"

log_header "🚀 UNIFIED DOCKER ORCHESTRATION SYSTEM STARTUP"

# Step 1: Environment Validation
log_header "🔍 ENVIRONMENT VALIDATION"

log_info "Validating environment setup..."

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running"
    exit 1
fi

log_success "Docker is installed and running"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not available"
    exit 1
fi

# Determine compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

log_success "Docker Compose is available: $COMPOSE_CMD"

# Check for required files
if [[ ! -f "$COMPOSE_FILE" ]]; then
    log_error "Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

log_success "Docker Compose configuration found"

# Check for environment file
if [[ ! -f "$ENV_FILE" ]]; then
    log_warning "Environment file not found: $ENV_FILE"
    log_info "Copying from template..."
    
    if [[ -f "$SCRIPT_DIR/.env.template" ]]; then
        cp "$SCRIPT_DIR/.env.template" "$ENV_FILE"
        log_warning "Please edit $ENV_FILE with your actual API keys and configuration"
        log_warning "The system will start with default/demo values where possible"
    else
        log_error "Environment template not found: $SCRIPT_DIR/.env.template"
        exit 1
    fi
fi

log_success "Environment configuration ready"

# Step 2: System Requirements Check
log_header "⚙️ SYSTEM REQUIREMENTS CHECK"

# Check available disk space (minimum 10GB)
AVAILABLE_SPACE=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
MIN_SPACE=$((10 * 1024 * 1024)) # 10GB in KB

if [[ $AVAILABLE_SPACE -lt $MIN_SPACE ]]; then
    log_warning "Low disk space. Available: $((AVAILABLE_SPACE / 1024 / 1024))GB, Recommended: 10GB+"
else
    log_success "Sufficient disk space available: $((AVAILABLE_SPACE / 1024 / 1024))GB"
fi

# Check available memory (minimum 8GB)
AVAILABLE_MEM=$(free -m | awk 'NR==2{print $7}')
MIN_MEM=8192

if [[ $AVAILABLE_MEM -lt $MIN_MEM ]]; then
    log_warning "Low memory available. Available: ${AVAILABLE_MEM}MB, Recommended: 8192MB+"
else
    log_success "Sufficient memory available: ${AVAILABLE_MEM}MB"
fi

# Step 3: Network and Volume Preparation
log_header "🌐 NETWORK AND VOLUME PREPARATION"

log_info "Creating Docker network and volumes..."

# Create network if it doesn't exist
if ! docker network ls | grep -q flash-loan-network; then
    docker network create --driver bridge --subnet=172.20.0.0/16 flash-loan-network
    log_success "Created Docker network: flash-loan-network"
else
    log_info "Docker network already exists: flash-loan-network"
fi

# Create volumes
VOLUMES=(
    "flash-loan_postgres_data"
    "flash-loan_redis_data"
    "flash-loan_rabbitmq_data"
    "flash-loan_vector_store_data"
    "flash-loan_langchain_data"
    "flash-loan_autogen_data"
    "flash-loan_mcp_data"
)

for volume in "${VOLUMES[@]}"; do
    if ! docker volume ls | grep -q "$volume"; then
        docker volume create "$volume"
        log_success "Created volume: $volume"
    else
        log_info "Volume already exists: $volume"
    fi
done

# Step 4: Build Custom Images
log_header "🔧 BUILDING CUSTOM IMAGES"

log_info "Building custom Docker images..."

# Build LangChain image
log_info "Building LangChain coordinator image..."
if docker build -t flash-loan-langchain:latest "$SCRIPT_DIR/langchain" >> "$LOG_FILE" 2>&1; then
    log_success "LangChain coordinator image built successfully"
else
    log_error "Failed to build LangChain coordinator image"
    exit 1
fi

# Build AutoGen image
log_info "Building AutoGen coordinator image..."
if docker build -t flash-loan-autogen:latest "$SCRIPT_DIR/autogen" >> "$LOG_FILE" 2>&1; then
    log_success "AutoGen coordinator image built successfully"
else
    log_error "Failed to build AutoGen coordinator image"
    exit 1
fi

# Create additional required files
log_info "Creating required configuration files..."

# Create basic Prometheus configuration
mkdir -p "$SCRIPT_DIR/config"
cat > "$SCRIPT_DIR/config/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'langchain-coordinator'
    static_configs:
      - targets: ['langchain-coordinator:8080']
  
  - job_name: 'autogen-coordinator'
    static_configs:
      - targets: ['autogen-coordinator:8013']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
  
  - job_name: 'rabbitmq'
    static_configs:
      - targets: ['rabbitmq:15672']
EOF

# Create health check services configuration
cat > "$SCRIPT_DIR/config/health-check-services.json" << 'EOF'
{
  "services": [
    {
      "name": "langchain-coordinator",
      "url": "http://langchain-coordinator:8000/health",
      "timeout": 10,
      "critical": true
    },
    {
      "name": "autogen-coordinator",
      "url": "http://autogen-coordinator:8000/health",
      "timeout": 10,
      "critical": true
    },
    {
      "name": "postgres",
      "url": "postgresql://flash_loan_user:password@postgres:5432/flash_loan_db",
      "timeout": 5,
      "critical": true
    },
    {
      "name": "redis",
      "url": "redis://redis:6379",
      "timeout": 5,
      "critical": true
    },
    {
      "name": "rabbitmq",
      "url": "http://rabbitmq:15672/api/overview",
      "timeout": 10,
      "critical": true
    }
  ]
}
EOF

log_success "Configuration files created"

# Step 5: Service Startup with Dependency Management
log_header "🚀 STARTING SERVICES"

log_info "Starting services in dependency order..."

# Start infrastructure services first
log_info "Starting infrastructure services..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d postgres redis rabbitmq

# Wait for infrastructure to be healthy
log_info "Waiting for infrastructure services to become healthy..."
MAX_WAIT=300  # 5 minutes
WAIT_TIME=0

while [[ $WAIT_TIME -lt $MAX_WAIT ]]; do
    if docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q postgres && \
       docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q redis && \
       docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q rabbitmq; then
        log_success "Infrastructure services are running"
        break
    fi
    
    sleep 10
    WAIT_TIME=$((WAIT_TIME + 10))
    log_info "Waiting for infrastructure... (${WAIT_TIME}s/${MAX_WAIT}s)"
done

if [[ $WAIT_TIME -ge $MAX_WAIT ]]; then
    log_error "Infrastructure services failed to start within timeout"
    exit 1
fi

# Start MCP servers
log_info "Starting MCP servers..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d mcp-supermemory mcp-context7 mcp-filesystem mcp-taskmanager

# Wait for MCP servers
log_info "Waiting for MCP servers to become healthy..."
sleep 30

# Start coordinators
log_info "Starting LangChain and AutoGen coordinators..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d langchain-coordinator autogen-coordinator

# Wait for coordinators
log_info "Waiting for coordinators to become healthy..."
sleep 60

# Start monitoring services
log_info "Starting monitoring services..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d system-monitor grafana elasticsearch kibana

# Start remaining services
log_info "Starting remaining services..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d web-dashboard health-checker

# Step 6: Health Verification
log_header "🏥 HEALTH VERIFICATION"

log_info "Performing comprehensive health checks..."

# Define services to check
SERVICES=(
    "postgres:5432"
    "redis:6379"
    "rabbitmq:15672"
    "langchain-coordinator:8000"
    "autogen-coordinator:8010"
    "mcp-supermemory:8100"
    "mcp-context7:8101"
    "mcp-filesystem:8102"
    "mcp-taskmanager:8103"
)

FAILED_SERVICES=()

for service in "${SERVICES[@]}"; do
    service_name="${service%:*}"
    port="${service#*:}"
    
    log_info "Checking $service_name..."
    
    # Try to connect to the service
    if timeout 10 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
        log_success "$service_name is responding on port $port"
    else
        log_warning "$service_name is not responding on port $port"
        FAILED_SERVICES+=("$service_name")
    fi
done

# Step 7: Service Discovery and Status
log_header "📊 SERVICE STATUS REPORT"

log_info "Generating service status report..."

# Show running containers
log_info "Running containers:"
docker compose -f "$COMPOSE_FILE" ps

# Show service endpoints
log_info "Service endpoints available:"
echo -e "${GREEN}Core Services:${NC}"
echo "  • LangChain Coordinator: http://localhost:8000"
echo "  • AutoGen Coordinator: http://localhost:8010"
echo ""
echo -e "${GREEN}MCP Servers:${NC}"
echo "  • Supermemory MCP: http://localhost:8100"
echo "  • Context7 MCP: http://localhost:8101"  
echo "  • Filesystem MCP: http://localhost:8102"
echo "  • TaskManager MCP: http://localhost:8103"
echo ""
echo -e "${GREEN}Infrastructure:${NC}"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo "  • RabbitMQ Management: http://localhost:15672"
echo ""
echo -e "${GREEN}Monitoring:${NC}"
echo "  • Prometheus: http://localhost:9090"
echo "  • Grafana: http://localhost:3000"
echo "  • Kibana: http://localhost:5601"
echo "  • Elasticsearch: http://localhost:9200"
echo ""
echo -e "${GREEN}Dashboard:${NC}"
echo "  • Unified Dashboard: http://localhost:8090"

# Step 8: Final Status and Recommendations
log_header "✅ STARTUP COMPLETE"

if [[ ${#FAILED_SERVICES[@]} -eq 0 ]]; then
    log_success "🎉 All services started successfully!"
    log_success "The unified Docker orchestration system is ready for use."
else
    log_warning "⚠️ Some services may need attention:"
    for service in "${FAILED_SERVICES[@]}"; do
        log_warning "  - $service"
    done
    log_info "Check individual service logs with: docker logs <container-name>"
fi

log_info "📋 Next steps:"
echo "  1. Access the unified dashboard at http://localhost:8090"
echo "  2. Check service health at individual endpoints"
echo "  3. Review logs: tail -f $LOG_FILE"
echo "  4. Monitor services: docker compose -f $COMPOSE_FILE logs -f"
echo ""
echo "📖 Management commands:"
echo "  • Stop system: ./stop-unified-system.sh"
echo "  • View logs: docker compose -f $COMPOSE_FILE logs -f [service]"
echo "  • Restart service: docker compose -f $COMPOSE_FILE restart [service]"
echo "  • Scale services: docker compose -f $COMPOSE_FILE up -d --scale [service]=N"

log_success "🚀 Unified Docker Orchestration System startup completed!"
log_info "Startup log saved to: $LOG_FILE"

exit 0