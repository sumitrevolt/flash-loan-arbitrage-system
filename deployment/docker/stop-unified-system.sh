#!/bin/bash

# Unified Docker Orchestration System Shutdown Script
# ===================================================
# This script gracefully stops all services with proper cleanup options.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.unified.yml"
LOG_FILE="$SCRIPT_DIR/logs/shutdown.log"

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

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -f, --force         Force stop all containers without graceful shutdown"
    echo "  -c, --cleanup       Clean up volumes and networks (DESTRUCTIVE)"
    echo "  -k, --keep-data     Keep data volumes (default behavior)"
    echo "  -r, --remove-images Remove built images after stopping"
    echo "  -q, --quiet         Quiet mode - minimal output"
    echo ""
    echo "Examples:"
    echo "  $0                  # Graceful shutdown, keep all data"
    echo "  $0 --cleanup        # Stop and remove all volumes/networks"
    echo "  $0 --force          # Force stop all containers immediately"
    echo "  $0 --remove-images  # Stop and remove custom images"
    exit 0
}

# Default options
FORCE_STOP=false
CLEANUP_VOLUMES=false
KEEP_DATA=true
REMOVE_IMAGES=false
QUIET_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -f|--force)
            FORCE_STOP=true
            shift
            ;;
        -c|--cleanup)
            CLEANUP_VOLUMES=true
            KEEP_DATA=false
            shift
            ;;
        -k|--keep-data)
            KEEP_DATA=true
            CLEANUP_VOLUMES=false
            shift
            ;;
        -r|--remove-images)
            REMOVE_IMAGES=true
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Initialize logging
mkdir -p "$SCRIPT_DIR/logs"
echo "Shutdown log - $(date)" > "$LOG_FILE"

if [[ "$QUIET_MODE" != true ]]; then
    log_header "🛑 UNIFIED DOCKER ORCHESTRATION SYSTEM SHUTDOWN"
fi

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

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    log_error "Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Confirmation for destructive operations
if [[ "$CLEANUP_VOLUMES" == true ]]; then
    if [[ "$QUIET_MODE" != true ]]; then
        echo -e "${RED}⚠️  WARNING: This will permanently delete all data volumes!${NC}"
        echo -e "${RED}   This includes databases, logs, and all persistent data.${NC}"
        echo ""
        read -p "Are you sure you want to continue? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Operation cancelled by user"
            exit 0
        fi
    fi
fi

# Step 1: Service Shutdown Strategy
if [[ "$QUIET_MODE" != true ]]; then
    log_header "📋 SHUTDOWN STRATEGY"
    log_info "Force stop: $FORCE_STOP"
    log_info "Cleanup volumes: $CLEANUP_VOLUMES"
    log_info "Keep data: $KEEP_DATA"
    log_info "Remove images: $REMOVE_IMAGES"
fi

# Step 2: Graceful Service Shutdown
if [[ "$QUIET_MODE" != true ]]; then
    log_header "🔄 STOPPING SERVICES"
fi

if [[ "$FORCE_STOP" == true ]]; then
    log_info "Force stopping all services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" kill
    $COMPOSE_CMD -f "$COMPOSE_FILE" down --remove-orphans
else
    log_info "Gracefully stopping services in reverse dependency order..."
    
    # Stop non-critical services first
    log_info "Stopping monitoring and dashboard services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" stop health-checker web-dashboard grafana kibana elasticsearch system-monitor || true
    
    # Stop coordination services
    log_info "Stopping coordination services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" stop langchain-coordinator autogen-coordinator || true
    
    # Stop MCP servers
    log_info "Stopping MCP servers..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" stop mcp-taskmanager mcp-filesystem mcp-context7 mcp-supermemory || true
    
    # Stop infrastructure services last
    log_info "Stopping infrastructure services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" stop rabbitmq redis postgres || true
    
    # Remove containers
    log_info "Removing containers..."
    if [[ "$CLEANUP_VOLUMES" == true ]]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" down --volumes --remove-orphans
    else
        $COMPOSE_CMD -f "$COMPOSE_FILE" down --remove-orphans
    fi
fi

log_success "All services stopped successfully"

# Step 3: Volume Management
if [[ "$CLEANUP_VOLUMES" == true ]]; then
    if [[ "$QUIET_MODE" != true ]]; then
        log_header "🗑️  CLEANING UP VOLUMES"
    fi
    
    log_info "Removing data volumes..."
    
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
        if docker volume ls | grep -q "$volume"; then
            docker volume rm "$volume" || log_warning "Failed to remove volume: $volume"
            log_success "Removed volume: $volume"
        else
            log_info "Volume not found: $volume"
        fi
    done
    
    # Remove any orphaned volumes
    log_info "Removing orphaned volumes..."
    docker volume prune -f || log_warning "Failed to prune volumes"
    
elif [[ "$QUIET_MODE" != true ]]; then
    log_info "Data volumes preserved (use --cleanup to remove)"
fi

# Step 4: Network Cleanup
if [[ "$CLEANUP_VOLUMES" == true ]]; then
    if [[ "$QUIET_MODE" != true ]]; then
        log_header "🌐 CLEANING UP NETWORKS"
    fi
    
    log_info "Removing custom networks..."
    
    if docker network ls | grep -q flash-loan-network; then
        docker network rm flash-loan-network || log_warning "Failed to remove network: flash-loan-network"
        log_success "Removed network: flash-loan-network"
    else
        log_info "Network not found: flash-loan-network"
    fi
    
    # Remove any orphaned networks
    log_info "Removing orphaned networks..."
    docker network prune -f || log_warning "Failed to prune networks"
    
elif [[ "$QUIET_MODE" != true ]]; then
    log_info "Networks preserved (use --cleanup to remove)"
fi

# Step 5: Image Cleanup
if [[ "$REMOVE_IMAGES" == true ]]; then
    if [[ "$QUIET_MODE" != true ]]; then
        log_header "🖼️  CLEANING UP IMAGES"
    fi
    
    log_info "Removing custom built images..."
    
    IMAGES=(
        "flash-loan-langchain:latest"
        "flash-loan-autogen:latest"
    )
    
    for image in "${IMAGES[@]}"; do
        if docker images | grep -q "${image%:*}"; then
            docker rmi "$image" || log_warning "Failed to remove image: $image"
            log_success "Removed image: $image"
        else
            log_info "Image not found: $image"
        fi
    done
    
    # Remove dangling images
    log_info "Removing dangling images..."
    docker image prune -f || log_warning "Failed to prune images"
    
elif [[ "$QUIET_MODE" != true ]]; then
    log_info "Images preserved (use --remove-images to clean up)"
fi

# Step 6: System Cleanup
if [[ "$CLEANUP_VOLUMES" == true ]]; then
    if [[ "$QUIET_MODE" != true ]]; then
        log_header "🧹 SYSTEM CLEANUP"
    fi
    
    log_info "Performing comprehensive Docker cleanup..."
    
    # Remove all stopped containers
    docker container prune -f || log_warning "Failed to prune containers"
    
    # Remove unused images
    docker image prune -a -f || log_warning "Failed to prune all images"
    
    # Remove build cache
    docker builder prune -f || log_warning "Failed to prune build cache"
    
    log_success "System cleanup completed"
fi

# Step 7: Log Management
if [[ "$QUIET_MODE" != true ]]; then
    log_header "📝 LOG MANAGEMENT"
fi

# Archive current logs if cleanup is requested
if [[ "$CLEANUP_VOLUMES" == true ]]; then
    log_info "Archiving current logs..."
    ARCHIVE_NAME="logs_archive_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    if [[ -d "$SCRIPT_DIR/logs" ]]; then
        tar -czf "$SCRIPT_DIR/$ARCHIVE_NAME" -C "$SCRIPT_DIR" logs/ || log_warning "Failed to archive logs"
        rm -rf "$SCRIPT_DIR/logs"/* || log_warning "Failed to clean log directory"
        log_success "Logs archived to: $ARCHIVE_NAME"
    fi
else
    log_info "Logs preserved in: $SCRIPT_DIR/logs/"
fi

# Step 8: Final Status Report
if [[ "$QUIET_MODE" != true ]]; then
    log_header "📊 SHUTDOWN SUMMARY"
    
    # Show remaining containers (should be empty)
    REMAINING_CONTAINERS=$(docker ps -a --filter "name=flash-loan" --format "table {{.Names}}\t{{.Status}}" | tail -n +2)
    
    if [[ -z "$REMAINING_CONTAINERS" ]]; then
        log_success "✅ All flash-loan containers stopped and removed"
    else
        log_warning "⚠️ Some containers may still be running:"
        echo "$REMAINING_CONTAINERS"
    fi
    
    # Show remaining volumes
    if [[ "$CLEANUP_VOLUMES" == false ]]; then
        REMAINING_VOLUMES=$(docker volume ls --filter "name=flash-loan" --format "table {{.Name}}" | tail -n +2)
        if [[ -n "$REMAINING_VOLUMES" ]]; then
            log_info "📦 Preserved data volumes:"
            echo "$REMAINING_VOLUMES"
        fi
    fi
    
    # Show disk space freed (approximate)
    if [[ "$CLEANUP_VOLUMES" == true ]]; then
        log_info "💾 Disk space cleanup completed"
        log_info "Run 'docker system df' to check Docker disk usage"
    fi
fi

# Step 9: Restart Instructions
if [[ "$QUIET_MODE" != true ]]; then
    log_header "🔄 RESTART INSTRUCTIONS"
    
    if [[ "$CLEANUP_VOLUMES" == true ]]; then
        log_info "Complete system cleanup performed."
        log_info "To restart the system:"
        echo "  1. Review and update environment configuration: $SCRIPT_DIR/.env"
        echo "  2. Run: ./start-unified-system.sh"
        echo "  3. All data will be initialized fresh"
    else
        log_info "Data preserved shutdown completed."
        log_info "To restart the system:"
        echo "  1. Run: ./start-unified-system.sh"
        echo "  2. All data and configurations will be restored"
    fi
    
    echo ""
    log_info "🛠️ Troubleshooting commands:"
    echo "  • Check Docker status: docker system df"
    echo "  • List remaining containers: docker ps -a"
    echo "  • List remaining volumes: docker volume ls"
    echo "  • List remaining networks: docker network ls"
    echo "  • Force cleanup: docker system prune -a --volumes"
fi

# Final success message
if [[ "$QUIET_MODE" != true ]]; then
    log_success "🏁 Unified Docker Orchestration System shutdown completed!"
    log_info "Shutdown log saved to: $LOG_FILE"
else
    echo "Shutdown completed successfully"
fi

exit 0