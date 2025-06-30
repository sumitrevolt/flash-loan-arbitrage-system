#!/bin/bash

set -e

echo "🚀 Flash Loan Arbitrage System Launcher"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=(
        "logs"
        "data/cache"
        "data/databases"
        "blockchain_data"
        "arbitrage_logs"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
    
    print_success "Directories created"
}

# Check environment variables
check_environment() {
    print_status "Checking environment variables..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << EOF
# Flash Loan Arbitrage System Configuration

# API Keys (REQUIRED for live trading)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GITHUB_TOKEN=your_github_token_here

# Database Passwords
POSTGRES_PASSWORD=flashloan_secure_password_2024
RABBITMQ_PASSWORD=rabbitmq_secure_password_2024
GRAFANA_PASSWORD=admin

# Trading Configuration (IMPORTANT!)
PRIVATE_KEY=0x1234567890abcdef...  # Your private key for trading (KEEP SECURE!)
FLASH_LOAN_CONTRACT=0x...  # Your deployed flash loan contract address
EXECUTE_TRADES=false  # Set to 'true' for live trading, 'false' for simulation

# Risk Management
MAX_GAS_PRICE=500  # Maximum gas price in gwei
MIN_PROFIT_THRESHOLD=0.001  # Minimum profit threshold (0.1%)

# System Configuration
LOG_LEVEL=INFO
MONITORING_INTERVAL=1
EOF
        print_warning "Please edit .env file with your actual values before proceeding!"
        print_warning "⚠️  NEVER commit your private keys to version control!"
        read -p "Press Enter to continue after editing .env file..."
    fi
    
    # Check critical environment variables
    source .env
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
        print_warning "OPENAI_API_KEY not set. AI features will be limited."
    fi
    
    if [ "$EXECUTE_TRADES" = "true" ]; then
        if [ -z "$PRIVATE_KEY" ] || [ "$PRIVATE_KEY" = "0x1234567890abcdef..." ]; then
            print_error "PRIVATE_KEY must be set for live trading!"
            print_error "Set EXECUTE_TRADES=false for simulation mode."
            exit 1
        fi
        
        if [ -z "$FLASH_LOAN_CONTRACT" ] || [ "$FLASH_LOAN_CONTRACT" = "0x..." ]; then
            print_error "FLASH_LOAN_CONTRACT must be set for live trading!"
            exit 1
        fi
        
        print_warning "⚠️  LIVE TRADING MODE ENABLED ⚠️"
        print_warning "This will execute real transactions with real money!"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            print_status "Switching to simulation mode..."
            sed -i 's/EXECUTE_TRADES=true/EXECUTE_TRADES=false/' .env
        fi
    else
        print_status "Running in simulation mode (safe)"
    fi
    
    print_success "Environment check completed"
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    cd deployment/docker/docker
    
    # Build images in parallel for faster startup
    docker-compose -f docker-compose.advanced-langchain.yml build --parallel
    
    cd ../../..
    
    print_success "Docker images built successfully"
}

# Start the system
start_system() {
    print_status "Starting Flash Loan Arbitrage System..."
    
    cd deployment/docker/docker
    
    # Start infrastructure services first
    print_status "Starting infrastructure services..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d redis postgres-master rabbitmq etcd
    
    # Wait for infrastructure to be ready
    print_status "Waiting for infrastructure services to be ready..."
    sleep 30
    
    # Start monitoring services
    print_status "Starting monitoring services..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d prometheus grafana jaeger
    
    # Start core services
    print_status "Starting core arbitrage services..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d \
        web3-node \
        blockchain-monitor \
        arbitrage-executor \
        langchain-orchestrator
    
    # Wait for core services
    print_status "Waiting for core services to initialize..."
    sleep 20
    
    # Start AI and analysis services
    print_status "Starting AI services..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d \
        quantum-decision-engine \
        swarm-coordinator \
        market-predictor \
        risk-manager
    
    # Start agent swarm
    print_status "Starting agent swarm..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d \
        market-intelligence-director \
        risk-management-chief \
        dex-analyst-1 \
        mev-protection-agent
    
    # Start dashboard and load balancer
    print_status "Starting dashboard and load balancer..."
    docker-compose -f docker-compose.advanced-langchain.yml up -d \
        arbitrage-dashboard \
        nginx
    
    cd ../../..
    
    print_success "System startup complete!"
}

# Check system health
check_health() {
    print_status "Checking system health..."
    
    # Wait a bit for services to fully start
    sleep 10
    
    services=(
        "http://localhost:6379" "Redis"
        "http://localhost:8000/health" "LangChain Orchestrator"
        "http://localhost:8070/health" "Blockchain Monitor"
        "http://localhost:8071/health" "Arbitrage Executor"
        "http://localhost:3001/health" "Dashboard"
        "http://localhost:3000" "Grafana"
        "http://localhost:9090" "Prometheus"
    )
    
    healthy_count=0
    total_services=$((${#services[@]} / 2))
    
    for ((i=0; i<${#services[@]}; i+=2)); do
        url="${services[i]}"
        name="${services[i+1]}"
        
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$name is healthy"
            ((healthy_count++))
        else
            print_warning "$name is not responding"
        fi
    done
    
    print_status "Health check complete: $healthy_count/$total_services services healthy"
    
    if [ $healthy_count -eq $total_services ]; then
        print_success "🎉 All services are running perfectly!"
    else
        print_warning "Some services may still be starting up. Wait a few minutes and check again."
    fi
}

# Display system URLs
show_urls() {
    echo ""
    echo "🌐 System Access URLs:"
    echo "======================"
    echo ""
    echo "📊 Main Dashboard:           http://localhost:3001"
    echo "🎛️  Grafana Monitoring:      http://localhost:3000 (admin/admin)"
    echo "📈 Prometheus Metrics:       http://localhost:9090"
    echo "🔍 Jaeger Tracing:           http://localhost:16686"
    echo "🤖 LangChain Orchestrator:   http://localhost:8000"
    echo "⛓️  Blockchain Monitor:       http://localhost:8070"
    echo "💰 Arbitrage Executor:       http://localhost:8071"
    echo "🕸️  Web3 Node RPC:           http://localhost:8545"
    echo ""
    echo "📋 Quick Commands:"
    echo "=================="
    echo "View logs:           docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml logs -f"
    echo "Stop system:         docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml down"
    echo "Restart service:     docker-compose -f deployment/docker/docker/docker-compose.advanced-langchain.yml restart <service>"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "Welcome to the Flash Loan Arbitrage System!"
    echo "This system will start a comprehensive blockchain arbitrage bot"
    echo "with AI-driven decision making and real-time monitoring."
    echo ""
    
    # Ask for confirmation
    read -p "Do you want to start the system? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Operation cancelled."
        exit 0
    fi
    
    check_prerequisites
    create_directories
    check_environment
    build_images
    start_system
    check_health
    show_urls
    
    echo ""
    print_success "🚀 Flash Loan Arbitrage System is now running!"
    print_status "Monitor the dashboard at http://localhost:3001"
    print_status "Check system logs for real-time activity"
    echo ""
    print_warning "⚠️  Remember: This system can execute real trades if configured!"
    print_warning "Always monitor the system and understand the risks involved."
    echo ""
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 