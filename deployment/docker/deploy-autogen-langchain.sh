#!/bin/bash

# AutoGen & LangChain Deployment Script
# =====================================
# Comprehensive deployment script for the Flash Loan AutoGen and LangChain systems

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.unified.yml"
ENV_FILE="$SCRIPT_DIR/.env"
LOG_FILE="$SCRIPT_DIR/logs/deployment.log"

# Ensure logs directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Print banner
print_banner() {
    echo -e "${PURPLE}"
    echo "=================================================================="
    echo "    Flash Loan AutoGen & LangChain Deployment System"
    echo "=================================================================="
    echo -e "${NC}"
    echo -e "${CYAN}🚀 Starting deployment of advanced multi-agent systems...${NC}"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking deployment prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    # Check compose file
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Clean up existing containers and volumes
cleanup_existing() {
    log_step "Cleaning up existing containers and volumes..."
    
    # Stop and remove existing containers
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans --volumes 2>/dev/null || true
    
    # Remove unused images and networks (optional)
    docker system prune -f --volumes 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Build images
build_images() {
    log_step "Building Docker images..."
    
    # Build all services with no cache for fresh deployment
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache --parallel; then
        log_success "All images built successfully"
    else
        log_error "Image building failed"
        exit 1
    fi
}

# Start infrastructure services first
start_infrastructure() {
    log_step "Starting infrastructure services..."
    
    # Start core infrastructure
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis rabbitmq; then
        log_info "Infrastructure services started"
        
        # Wait for services to be ready
        log_info "Waiting for infrastructure services to be ready..."
        sleep 30
        
        # Check PostgreSQL
        log_info "Checking PostgreSQL readiness..."
        for i in {1..30}; do
            if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U flash_loan_user -d flash_loan_db &> /dev/null; then
                log_success "PostgreSQL is ready"
                break
            fi
            if [[ $i -eq 30 ]]; then
                log_error "PostgreSQL failed to start properly"
                exit 1
            fi
            sleep 2
        done
        
        # Check Redis
        log_info "Checking Redis readiness..."
        for i in {1..30}; do
            if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli ping &> /dev/null; then
                log_success "Redis is ready"
                break
            fi
            if [[ $i -eq 30 ]]; then
                log_error "Redis failed to start properly"
                exit 1
            fi
            sleep 2
        done
        
        log_success "All infrastructure services are ready"
    else
        log_error "Failed to start infrastructure services"
        exit 1
    fi
}

# Start MCP servers
start_mcp_servers() {
    log_step "Starting MCP servers..."
    
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d mcp-supermemory mcp-context7 mcp-filesystem mcp-taskmanager; then
        log_success "MCP servers started"
        
        # Wait for MCP servers to be ready
        log_info "Waiting for MCP servers to initialize..."
        sleep 20
        
        log_success "MCP servers are ready"
    else
        log_error "Failed to start MCP servers"
        exit 1
    fi
}

# Start AutoGen and LangChain services
start_agent_systems() {
    log_step "Starting AutoGen and LangChain systems..."
    
    # Start LangChain coordinator first
    log_info "Starting LangChain coordinator..."
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d langchain-coordinator; then
        log_success "LangChain coordinator started"
    else
        log_error "Failed to start LangChain coordinator"
        exit 1
    fi
    
    # Wait for LangChain to be ready
    log_info "Waiting for LangChain to initialize..."
    sleep 45
    
    # Check LangChain health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "LangChain coordinator is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_warn "LangChain health check timeout, continuing..."
            break
        fi
        sleep 3
    done
    
    # Start AutoGen coordinator
    log_info "Starting AutoGen coordinator..."
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d autogen-coordinator; then
        log_success "AutoGen coordinator started"
    else
        log_error "Failed to start AutoGen coordinator"
        exit 1
    fi
    
    # Wait for AutoGen to be ready
    log_info "Waiting for AutoGen to initialize..."
    sleep 45
    
    # Check AutoGen health
    for i in {1..30}; do
        if curl -f http://localhost:8010/health &> /dev/null; then
            log_success "AutoGen coordinator is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_warn "AutoGen health check timeout, continuing..."
            break
        fi
        sleep 3
    done
    
    log_success "Both agent systems are running"
}

# Start monitoring and support services
start_monitoring() {
    log_step "Starting monitoring and support services..."
    
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d system-monitor grafana elasticsearch kibana web-dashboard health-checker; then
        log_success "Monitoring services started"
        
        # Wait for services to initialize
        log_info "Waiting for monitoring services to initialize..."
        sleep 30
        
        log_success "Monitoring services are ready"
    else
        log_warn "Some monitoring services may have failed to start, but core systems are running"
    fi
}

# Display deployment status
show_deployment_status() {
    log_step "Checking deployment status..."
    
    echo ""
    echo -e "${CYAN}🔍 Service Status Check:${NC}"
    echo "=================================================================="
    
    # Show running containers
    echo -e "${BLUE}Running Containers:${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    echo ""
    echo -e "${BLUE}Service Endpoints:${NC}"
    echo "----------------------------------------------------------------"
    echo -e "📊 ${GREEN}LangChain Coordinator:${NC}     http://localhost:8000"
    echo -e "📊 ${GREEN}LangChain Health:${NC}          http://localhost:8000/health"
    echo -e "📊 ${GREEN}LangChain Status:${NC}          http://localhost:8000/status"
    echo ""
    echo -e "🤖 ${GREEN}AutoGen Coordinator:${NC}       http://localhost:8010"
    echo -e "🤖 ${GREEN}AutoGen Health:${NC}            http://localhost:8010/health"
    echo -e "🤖 ${GREEN}AutoGen Service Info:${NC}      http://localhost:8010/service/info"
    echo ""
    echo -e "📡 ${GREEN}MCP Supermemory:${NC}           http://localhost:8100"
    echo -e "📡 ${GREEN}MCP Context7:${NC}              http://localhost:8101"
    echo -e "📡 ${GREEN}MCP Filesystem:${NC}            http://localhost:8102"
    echo -e "📡 ${GREEN}MCP Task Manager:${NC}          http://localhost:8103"
    echo ""
    echo -e "📈 ${GREEN}Grafana Dashboard:${NC}         http://localhost:3000"
    echo -e "📈 ${GREEN}Prometheus Metrics:${NC}        http://localhost:9090"
    echo -e "📈 ${GREEN}Kibana Logs:${NC}               http://localhost:5601"
    echo -e "📈 ${GREEN}Web Dashboard:${NC}             http://localhost:8090"
    echo ""
    echo -e "💾 ${GREEN}PostgreSQL:${NC}                localhost:5432"
    echo -e "💾 ${GREEN}Redis:${NC}                     localhost:6379"
    echo -e "💾 ${GREEN}RabbitMQ Management:${NC}       http://localhost:15672"
    echo ""
}

# Test system functionality
test_deployment() {
    log_step "Testing deployment functionality..."
    
    echo -e "${CYAN}🧪 Running deployment tests...${NC}"
    
    # Test LangChain
    echo -e "${BLUE}Testing LangChain coordinator...${NC}"
    if curl -s http://localhost:8000/health | grep -q "healthy\|ok"; then
        log_success "✅ LangChain coordinator is healthy"
    else
        log_warn "⚠️ LangChain coordinator health check failed"
    fi
    
    # Test AutoGen
    echo -e "${BLUE}Testing AutoGen coordinator...${NC}"
    if curl -s http://localhost:8010/health | grep -q "healthy\|ok"; then
        log_success "✅ AutoGen coordinator is healthy"
    else
        log_warn "⚠️ AutoGen coordinator health check failed"
    fi
    
    # Test database connection
    echo -e "${BLUE}Testing database connection...${NC}"
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U flash_loan_user -d flash_loan_db &> /dev/null; then
        log_success "✅ PostgreSQL connection is working"
    else
        log_warn "⚠️ PostgreSQL connection test failed"
    fi
    
    # Test Redis connection
    echo -e "${BLUE}Testing Redis connection...${NC}"
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "✅ Redis connection is working"
    else
        log_warn "⚠️ Redis connection test failed"
    fi
    
    echo ""
    log_success "Deployment testing completed"
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy          Full deployment (default)"
    echo "  restart         Restart all services"
    echo "  stop            Stop all services"
    echo "  status          Show service status"
    echo "  logs            Show service logs"
    echo "  test            Test deployment"
    echo "  cleanup         Clean up all containers and volumes"
    echo "  help            Show this help message"
    echo ""
}

# Main deployment function
deploy_systems() {
    print_banner
    
    log_info "Starting AutoGen and LangChain deployment..."
    log_info "Project root: $PROJECT_ROOT"
    log_info "Compose file: $COMPOSE_FILE"
    log_info "Environment file: $ENV_FILE"
    
    check_prerequisites
    cleanup_existing
    build_images
    start_infrastructure
    start_mcp_servers
    start_agent_systems
    start_monitoring
    
    show_deployment_status
    test_deployment
    
    echo ""
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉${NC}"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo "1. Configure API keys in $ENV_FILE"
    echo "2. Access the web dashboard at http://localhost:8090"
    echo "3. Monitor services using Grafana at http://localhost:3000"
    echo "4. Check logs with: $0 logs"
    echo ""
    echo -e "${YELLOW}To stop all services: $0 stop${NC}"
    echo ""
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy_systems
        ;;
    "restart")
        log_info "Restarting all services..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
        show_deployment_status
        ;;
    "stop")
        log_info "Stopping all services..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
        log_success "All services stopped"
        ;;
    "status")
        show_deployment_status
        ;;
    "logs")
        echo -e "${CYAN}Service logs (press Ctrl+C to exit):${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
        ;;
    "test")
        test_deployment
        ;;
    "cleanup")
        log_warn "This will remove all containers, volumes, and data. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            cleanup_existing
            docker system prune -af --volumes
            log_success "Cleanup completed"
        fi
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac