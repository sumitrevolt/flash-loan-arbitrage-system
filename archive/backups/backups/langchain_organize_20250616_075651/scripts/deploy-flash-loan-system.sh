#!/bin/bash

# Flash Loan Arbitrage System Deployment Script
# This script sets up and deploys the entire system with all AI enhancements

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=(
        "logs"
        "monitoring/alerts"
        "mcp_servers/quality"
        "mcp_servers/recovery"
        "data/redis"
        "data/prometheus"
        "data/grafana"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_success "Created directory: $dir"
    done
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Copy .env.example to .env if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
            print_warning "Please update .env with your actual configuration values"
        else
            print_error ".env.example not found. Please create .env file manually."
            exit 1
        fi
    else
        print_success ".env file already exists"
    fi
}

# Build base image
build_base_image() {
    print_status "Building base Docker image..."
    
    docker build -t flash-loan-base:latest -f docker/Dockerfile.base .
    if [ $? -eq 0 ]; then
        print_success "Base image built successfully"
    else
        print_error "Failed to build base image"
        exit 1
    fi
}

# Update docker-compose to use coordinator-fastapi
update_docker_compose() {
    print_status "Updating docker-compose configuration..."
    
    # Check if fixed compose file exists
    if [ -f docker-compose-fixed.yml ]; then
        # Update coordinator dockerfile references
        sed -i 's|dockerfile: docker/Dockerfile.coordinator|dockerfile: docker/Dockerfile.coordinator-fastapi|g' docker-compose-fixed.yml
        print_success "Updated docker-compose to use FastAPI-enabled coordinator"
    else
        print_warning "docker-compose-fixed.yml not found. Using default configuration."
    fi
}

# Deploy monitoring stack
deploy_monitoring() {
    print_status "Deploying monitoring stack..."
    
    # Start Prometheus and Grafana first
    docker-compose -f docker-compose-fixed.yml up -d prometheus grafana
    
    print_success "Monitoring stack deployed"
    print_status "Grafana will be available at http://localhost:3000 (admin/admin)"
    print_status "Prometheus will be available at http://localhost:9090"
}

# Deploy core services
deploy_core_services() {
    print_status "Deploying core services..."
    
    # Start Redis first as it's a dependency
    docker-compose -f docker-compose-fixed.yml up -d redis
    sleep 5  # Wait for Redis to start
    
    # Start all other services
    docker-compose -f docker-compose-fixed.yml up -d
    
    print_success "All services deployed"
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Wait for services to start
    sleep 30
    
    # Check service health
    services=(
        "redis:6379"
        "flash-loan-mcp:3001"
        "arbitrage-detector:8004"
        "risk-manager:8005"
        "mcp-coordinator:8000"
        "code-quality-checker:8010"
        "recovery-agent:8011"
    )
    
    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d':' -f1)
        service_port=$(echo $service | cut -d':' -f2)
        
        if docker-compose -f docker-compose-fixed.yml ps | grep -q "$service_name.*Up"; then
            print_success "$service_name is running"
        else
            print_error "$service_name is not running"
        fi
    done
}

# Display summary
display_summary() {
    echo ""
    echo "======================================"
    echo "Flash Loan Arbitrage System Deployed!"
    echo "======================================"
    echo ""
    echo "Services:"
    echo "  - Redis: redis://localhost:6379"
    echo "  - Flash Loan MCP: http://localhost:3001"
    echo "  - Arbitrage Detector: http://localhost:8004"
    echo "  - Risk Manager: http://localhost:8005"
    echo "  - MCP Coordinator: http://localhost:8000"
    echo "  - MCP Dashboard: http://localhost:8080"
    echo "  - Code Quality Checker: http://localhost:8010"
    echo "  - Recovery Agent: http://localhost:8011"
    echo ""
    echo "Monitoring:"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000"
    echo ""
    echo "AI Enhancements:"
    echo "  ✓ Code Quality Checker Agent - Automated code validation"
    echo "  ✓ Recovery Agent - Auto-healing for failed containers"
    echo "  ✓ FastAPI Integration - REST API endpoints for all services"
    echo ""
    echo "Commands:"
    echo "  View logs: docker-compose -f docker-compose-fixed.yml logs -f [service-name]"
    echo "  Stop all: docker-compose -f docker-compose-fixed.yml down"
    echo "  Restart service: docker-compose -f docker-compose-fixed.yml restart [service-name]"
    echo ""
    print_warning "Remember to update .env file with your actual configuration!"
}

# Main execution
main() {
    echo "Flash Loan Arbitrage System Deployment"
    echo "======================================"
    echo ""
    
    check_prerequisites
    create_directories
    setup_environment
    build_base_image
    update_docker_compose
    deploy_monitoring
    deploy_core_services
    verify_deployment
    display_summary
}

# Run main function
main