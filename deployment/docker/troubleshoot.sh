#!/bin/bash

# Comprehensive Troubleshooting Script for LangChain-AutoGen-MCP System
# 
# This script provides automated diagnosis and fixes for common deployment issues

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs/troubleshooting"
CONFIG_DIR="${PROJECT_ROOT}/config"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.unified.yml"
TROUBLESHOOT_REPORT="${LOG_DIR}/troubleshoot-report-$(date +%Y%m%d_%H%M%S).json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p "${LOG_DIR}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/troubleshoot.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/troubleshoot.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/troubleshoot.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/troubleshoot.log"
}

log_fix() {
    echo -e "${PURPLE}[FIX]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/troubleshoot.log"
}

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/troubleshoot.log"
}

# Initialize troubleshoot report
init_troubleshoot_report() {
    cat > "${TROUBLESHOOT_REPORT}" << EOF
{
  "troubleshoot_run": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "script_version": "1.0.0",
    "system": "LangChain-AutoGen-MCP Unified System"
  },
  "issues_detected": [],
  "fixes_applied": [],
  "system_info": {},
  "recommendations": [],
  "summary": {
    "total_issues": 0,
    "issues_fixed": 0,
    "issues_remaining": 0,
    "system_health": "unknown"
  }
}
EOF
}

# Add issue to report
add_issue() {
    local category="$1"
    local issue="$2"
    local severity="$3"
    local description="$4"
    local fix_attempted="${5:-false}"
    
    python3 -c "
import json
import sys

try:
    with open('${TROUBLESHOOT_REPORT}', 'r') as f:
        data = json.load(f)
    
    issue_data = {
        'category': '${category}',
        'issue': '${issue}',
        'severity': '${severity}',
        'description': '${description}',
        'fix_attempted': ${fix_attempted,,},
        'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
    }
    
    data['issues_detected'].append(issue_data)
    data['summary']['total_issues'] += 1
    
    with open('${TROUBLESHOOT_REPORT}', 'w') as f:
        json.dump(data, f, indent=2)
        
except Exception as e:
    print(f'Error updating report: {e}', file=sys.stderr)
"
}

# Add fix to report
add_fix() {
    local issue="$1"
    local fix_description="$2"
    local success="$3"
    
    python3 -c "
import json
import sys

try:
    with open('${TROUBLESHOOT_REPORT}', 'r') as f:
        data = json.load(f)
    
    fix_data = {
        'issue': '${issue}',
        'fix_description': '${fix_description}',
        'success': ${success,,},
        'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
    }
    
    data['fixes_applied'].append(fix_data)
    if ${success,,}; then
        data['summary']['issues_fixed'] += 1
    fi
    
    with open('${TROUBLESHOOT_REPORT}', 'w') as f:
        json.dump(data, f, indent=2)
        
except Exception as e:
    print(f'Error updating report: {e}', file=sys.stderr)
"
}

# System information collection
collect_system_info() {
    log_info "Collecting system information..."
    
    local system_info="{}"
    
    # Docker version
    if command -v docker >/dev/null 2>&1; then
        local docker_version=$(docker --version 2>/dev/null || echo "unknown")
        system_info=$(echo "$system_info" | python3 -c "
import sys, json
data = json.load(sys.stdin)
data['docker_version'] = '${docker_version}'
print(json.dumps(data))
")
    fi
    
    # Docker Compose version
    if command -v docker-compose >/dev/null 2>&1; then
        local compose_version=$(docker-compose --version 2>/dev/null || echo "unknown")
        system_info=$(echo "$system_info" | python3 -c "
import sys, json
data = json.load(sys.stdin)
data['docker_compose_version'] = '${compose_version}'
print(json.dumps(data))
")
    fi
    
    # System resources
    local memory_total=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}' 2>/dev/null || echo "unknown")
    local memory_free=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}' 2>/dev/null || echo "unknown")
    local disk_usage=$(df -h "${PROJECT_ROOT}" | awk 'NR==2{print $5}' 2>/dev/null || echo "unknown")
    
    system_info=$(echo "$system_info" | python3 -c "
import sys, json
data = json.load(sys.stdin)
data['memory_total_gb'] = '${memory_total}'
data['memory_free_gb'] = '${memory_free}'
data['disk_usage'] = '${disk_usage}'
data['project_root'] = '${PROJECT_ROOT}'
print(json.dumps(data))
")
    
    # Update report with system info
    python3 -c "
import json
import sys

try:
    with open('${TROUBLESHOOT_REPORT}', 'r') as f:
        data = json.load(f)
    
    data['system_info'] = ${system_info}
    
    with open('${TROUBLESHOOT_REPORT}', 'w') as f:
        json.dump(data, f, indent=2)
        
except Exception as e:
    print(f'Error updating system info: {e}', file=sys.stderr)
"
    
    log_success "System information collected"
}

# Check Docker installation and status
check_docker_status() {
    log_info "Checking Docker status..."
    
    # Check if Docker is installed
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed"
        add_issue "docker" "docker_not_installed" "critical" "Docker is not installed on the system"
        
        log_info "Would you like to install Docker? (y/n)"
        if [[ "${AUTO_FIX:-false}" == "true" ]]; then
            log_fix "Auto-installing Docker..."
            install_docker
        else
            log_warning "Docker installation skipped. Please install Docker manually."
        fi
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        add_issue "docker" "docker_daemon_not_running" "critical" "Docker daemon is not accessible"
        
        log_fix "Attempting to start Docker daemon..."
        if systemctl is-active --quiet docker 2>/dev/null; then
            log_success "Docker daemon is already running"
        else
            if sudo systemctl start docker 2>/dev/null; then
                log_success "Docker daemon started successfully"
                add_fix "docker_daemon_not_running" "Started Docker daemon using systemctl" "true"
            else
                log_error "Failed to start Docker daemon"
                add_fix "docker_daemon_not_running" "Failed to start Docker daemon" "false"
                return 1
            fi
        fi
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose is not installed"
        add_issue "docker" "docker_compose_not_installed" "critical" "Docker Compose is not installed"
        
        log_fix "Installing Docker Compose..."
        install_docker_compose
    fi
    
    log_success "Docker status check completed"
}

# Install Docker (Ubuntu/Debian)
install_docker() {
    log_info "Installing Docker..."
    
    if [[ -f /etc/debian_version ]]; then
        # Ubuntu/Debian installation
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        
        log_success "Docker installed successfully"
        add_fix "docker_not_installed" "Installed Docker using official script" "true"
    else
        log_error "Automatic Docker installation not supported for this OS"
        add_fix "docker_not_installed" "Docker installation not supported for this OS" "false"
    fi
}

# Install Docker Compose
install_docker_compose() {
    log_info "Installing Docker Compose..."
    
    local compose_version="2.24.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/v${compose_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    if command -v docker-compose >/dev/null 2>&1; then
        log_success "Docker Compose installed successfully"
        add_fix "docker_compose_not_installed" "Installed Docker Compose v${compose_version}" "true"
    else
        log_error "Docker Compose installation failed"
        add_fix "docker_compose_not_installed" "Docker Compose installation failed" "false"
    fi
}

# Check required files and directories
check_required_files() {
    log_info "Checking required files and directories..."
    
    local required_files=(
        "${COMPOSE_FILE}"
        "${PROJECT_ROOT}/.env"
        "${CONFIG_DIR}/unified_mcp_config.json"
    )
    
    local required_dirs=(
        "${LOG_DIR}"
        "${CONFIG_DIR}"
        "${PROJECT_ROOT}/data"
        "${PROJECT_ROOT}/logs"
    )
    
    # Check files
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file missing: $file"
            add_issue "files" "missing_file_$(basename "$file")" "high" "Required file $file is missing"
            
            # Attempt to create/fix missing files
            fix_missing_file "$file"
        else
            log_success "Required file exists: $file"
        fi
    done
    
    # Check directories
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_warning "Required directory missing: $dir"
            log_fix "Creating directory: $dir"
            mkdir -p "$dir"
            
            if [[ -d "$dir" ]]; then
                log_success "Directory created successfully: $dir"
                add_fix "missing_directory_$(basename "$dir")" "Created missing directory" "true"
            else
                log_error "Failed to create directory: $dir"
                add_fix "missing_directory_$(basename "$dir")" "Failed to create directory" "false"
                add_issue "files" "missing_directory_$(basename "$dir")" "medium" "Required directory $dir could not be created"
            fi
        else
            log_success "Required directory exists: $dir"
        fi
    done
}

# Fix missing files
fix_missing_file() {
    local file="$1"
    local filename=$(basename "$file")
    
    case "$filename" in
        ".env")
            log_fix "Creating default .env file..."
            create_default_env_file
            ;;
        "docker-compose.unified.yml")
            log_error "Docker Compose file is missing and cannot be auto-generated"
            add_fix "missing_file_$filename" "Cannot auto-generate Docker Compose file" "false"
            ;;
        "unified_mcp_config.json")
            log_fix "Creating default MCP configuration..."
            create_default_mcp_config
            ;;
        *)
            log_warning "Unknown missing file: $file"
            ;;
    esac
}

# Create default .env file
create_default_env_file() {
    cat > "${PROJECT_ROOT}/.env" << 'EOF'
# LangChain-AutoGen-MCP System Environment Configuration

# API Keys (REQUIRED - Set these before deployment)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GITHUB_TOKEN=your_github_token_here
GITHUB_COPILOT_API_KEY=your_github_copilot_api_key_here

# Database Configuration
POSTGRES_DB=flash_loan_db
POSTGRES_USER=flash_loan_user
POSTGRES_PASSWORD=flash_loan_secure_2025
POSTGRES_PORT=5432

# Redis Configuration
REDIS_PASSWORD=flash_loan_redis_2025
REDIS_PORT=6379

# RabbitMQ Configuration
RABBITMQ_USER=flash_loan_mq
RABBITMQ_PASSWORD=flash_loan_mq_2025
RABBITMQ_VHOST=flash_loan_vhost
RABBITMQ_PORT=5672
RABBITMQ_MANAGEMENT_PORT=15672

# MCP Server Configuration
SUPERMEMORY_API_KEY=your_supermemory_api_key_here

# System Configuration
LOG_LEVEL=INFO
ENABLE_METRICS=true
ENABLE_DEBUG=false

# Monitoring Configuration
GRAFANA_PASSWORD=admin
ALERT_WEBHOOK_URL=

# GitHub Copilot Configuration
GITHUB_COPILOT_ENABLED=true
GITHUB_COPILOT_MODEL=gpt-4-turbo-preview

# LangChain Configuration
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
VECTOR_STORE_PROVIDER=chroma
EMBEDDING_MODEL=text-embedding-ada-002

# AutoGen Configuration
AUTOGEN_MAX_AGENTS=10
AUTOGEN_CONVERSATION_TIMEOUT=600

# Performance Configuration
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
ENABLE_CODE_EXECUTION=true
CODE_EXECUTION_TIMEOUT=30
EOF
    
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        log_success "Default .env file created"
        add_fix "missing_file_.env" "Created default .env file" "true"
        log_warning "Please update the API keys in .env file before deployment"
    else
        log_error "Failed to create .env file"
        add_fix "missing_file_.env" "Failed to create .env file" "false"
    fi
}

# Create default MCP configuration
create_default_mcp_config() {
    cat > "${CONFIG_DIR}/unified_mcp_config.json" << 'EOF'
{
  "servers": {
    "supermemory": {
      "name": "supermemory",
      "type": "python",
      "path": "mcp_servers/supermemory/supermemory_mcp_server.py",
      "port": 8100,
      "enabled": true,
      "auto_restart": true,
      "environment_variables": {
        "MCP_SERVER_NAME": "supermemory",
        "PORT": "8100",
        "SUPERMEMORY_API_KEY": "${SUPERMEMORY_API_KEY}"
      },
      "description": "Universal Memory MCP Server"
    },
    "context7": {
      "name": "context7",
      "type": "node",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "port": 8101,
      "enabled": true,
      "auto_restart": true,
      "environment_variables": {
        "MCP_SERVER_NAME": "context7",
        "PORT": "8101"
      },
      "description": "Context7 MCP Server"
    },
    "filesystem": {
      "name": "filesystem",
      "type": "node",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "port": 8102,
      "enabled": true,
      "auto_restart": true,
      "environment_variables": {
        "MCP_SERVER_NAME": "filesystem",
        "PORT": "8102"
      },
      "description": "Filesystem MCP Server"
    }
  },
  "global_configuration": {
    "health_check_interval": 30,
    "auto_restart": true,
    "log_level": "INFO"
  }
}
EOF
    
    if [[ -f "${CONFIG_DIR}/unified_mcp_config.json" ]]; then
        log_success "Default MCP configuration created"
        add_fix "missing_file_unified_mcp_config.json" "Created default MCP configuration" "true"
    else
        log_error "Failed to create MCP configuration"
        add_fix "missing_file_unified_mcp_config.json" "Failed to create MCP configuration" "false"
    fi
}

# Check container status
check_container_status() {
    log_info "Checking container status..."
    
    # Check if any containers are running
    local running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "flash-loan|langchain|autogen|mcp" || echo "")
    
    if [[ -z "$running_containers" ]]; then
        log_warning "No system containers are currently running"
        add_issue "containers" "no_containers_running" "medium" "No system containers are currently running"
        
        log_info "Would you like to start the containers? (y/n)"
        if [[ "${AUTO_START:-false}" == "true" ]]; then
            log_fix "Auto-starting containers..."
            start_containers
        fi
    else
        log_info "Running containers:"
        echo "$running_containers"
        
        # Check for failed containers
        local failed_containers=$(docker ps -a --filter "status=exited" --format "table {{.Names}}\t{{.Status}}" | grep -E "flash-loan|langchain|autogen|mcp" || echo "")
        
        if [[ -n "$failed_containers" ]]; then
            log_warning "Found failed containers:"
            echo "$failed_containers"
            add_issue "containers" "failed_containers_detected" "high" "Some containers have failed and exited"
            
            # Attempt to restart failed containers
            restart_failed_containers
        fi
    fi
}

# Start containers
start_containers() {
    log_info "Starting system containers..."
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        if docker-compose -f "$COMPOSE_FILE" up -d > "${LOG_DIR}/container-start.log" 2>&1; then
            log_success "Containers started successfully"
            add_fix "no_containers_running" "Started containers using docker-compose" "true"
        else
            log_error "Failed to start containers"
            add_fix "no_containers_running" "Failed to start containers" "false"
            log_info "Check logs: ${LOG_DIR}/container-start.log"
        fi
    else
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        add_fix "no_containers_running" "Docker Compose file not found" "false"
    fi
}

# Restart failed containers
restart_failed_containers() {
    log_info "Restarting failed containers..."
    
    local failed_containers=$(docker ps -a --filter "status=exited" --format "{{.Names}}" | grep -E "flash-loan|langchain|autogen|mcp" || echo "")
    
    if [[ -n "$failed_containers" ]]; then
        for container in $failed_containers; do
            log_fix "Restarting container: $container"
            
            if docker restart "$container" > "${LOG_DIR}/restart-${container}.log" 2>&1; then
                log_success "Successfully restarted: $container"
                add_fix "failed_containers_detected" "Restarted container $container" "true"
            else
                log_error "Failed to restart: $container"
                add_fix "failed_containers_detected" "Failed to restart container $container" "false"
                
                # Check container logs for errors
                log_info "Checking logs for $container..."
                docker logs --tail 50 "$container" > "${LOG_DIR}/logs-${container}.log" 2>&1
                log_info "Container logs saved to: ${LOG_DIR}/logs-${container}.log"
            fi
        done
    fi
}

# Check port conflicts
check_port_conflicts() {
    log_info "Checking for port conflicts..."
    
    local required_ports=(5432 6379 5672 15672 8000 8010 8100 8101 8102 8103 9090 3000 9200 5601 8090)
    local conflicts_found=false
    
    for port in "${required_ports[@]}"; do
        if lsof -i ":$port" >/dev/null 2>&1; then
            local process=$(lsof -i ":$port" -t 2>/dev/null | head -1)
            local process_name=$(ps -p "$process" -o comm= 2>/dev/null || echo "unknown")
            
            # Check if it's one of our Docker containers
            if docker ps --format "{{.Ports}}" | grep -q ":$port->"; then
                log_success "Port $port is used by our system containers"
            else
                log_warning "Port $port is in use by process: $process_name (PID: $process)"
                add_issue "ports" "port_conflict_$port" "medium" "Port $port is in use by external process $process_name"
                conflicts_found=true
            fi
        else
            log_debug "Port $port is available"
        fi
    done
    
    if [[ "$conflicts_found" == "false" ]]; then
        log_success "No port conflicts detected"
    fi
}

# Check system resources
check_system_resources() {
    log_info "Checking system resources..."
    
    # Check memory
    local memory_total=$(free -m | awk 'NR==2{print $2}')
    local memory_available=$(free -m | awk 'NR==2{print $7}')
    local memory_usage_percent=$(( (memory_total - memory_available) * 100 / memory_total ))
    
    log_info "Memory usage: ${memory_usage_percent}% (Available: $((memory_available/1024))GB)"
    
    if [[ $memory_available -lt 2048 ]]; then
        log_warning "Low available memory: $((memory_available/1024))GB"
        add_issue "resources" "low_memory" "medium" "Available memory is below 2GB"
    fi
    
    # Check disk space
    local disk_usage=$(df "${PROJECT_ROOT}" | awk 'NR==2{print $5}' | sed 's/%//')
    log_info "Disk usage: ${disk_usage}%"
    
    if [[ $disk_usage -gt 90 ]]; then
        log_warning "High disk usage: ${disk_usage}%"
        add_issue "resources" "high_disk_usage" "high" "Disk usage is above 90%"
        
        # Offer to clean up Docker
        log_fix "Cleaning up Docker system..."
        cleanup_docker_system
    fi
    
    # Check CPU load
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local cpu_load_percent=$(echo "$cpu_load * 100 / $cpu_cores" | bc -l 2>/dev/null || echo "0")
    
    log_info "CPU load: ${cpu_load} (${cpu_load_percent%.*}%)"
    
    if (( $(echo "$cpu_load_percent > 80" | bc -l) )); then
        log_warning "High CPU load: ${cpu_load_percent%.*}%"
        add_issue "resources" "high_cpu_load" "medium" "CPU load is above 80%"
    fi
}

# Cleanup Docker system
cleanup_docker_system() {
    log_info "Cleaning up Docker system..."
    
    # Remove unused containers, networks, images
    if docker system prune -f > "${LOG_DIR}/docker-cleanup.log" 2>&1; then
        log_success "Docker system cleanup completed"
        add_fix "high_disk_usage" "Cleaned up Docker system" "true"
    else
        log_error "Docker system cleanup failed"
        add_fix "high_disk_usage" "Docker cleanup failed" "false"
    fi
    
    # Remove unused volumes (be careful with this)
    if [[ "${AGGRESSIVE_CLEANUP:-false}" == "true" ]]; then
        docker volume prune -f >> "${LOG_DIR}/docker-cleanup.log" 2>&1
        log_info "Aggressive cleanup: removed unused volumes"
    fi
}

# Check environment variables
check_environment_variables() {
    log_info "Checking environment variables..."
    
    local env_file="${PROJECT_ROOT}/.env"
    local critical_vars=("OPENAI_API_KEY" "POSTGRES_PASSWORD" "REDIS_PASSWORD")
    local missing_vars=()
    
    if [[ -f "$env_file" ]]; then
        source "$env_file" 2>/dev/null || true
        
        for var in "${critical_vars[@]}"; do
            if [[ -z "${!var:-}" ]] || [[ "${!var:-}" == *"your_"*"_here" ]]; then
                missing_vars+=("$var")
            fi
        done
        
        if [[ ${#missing_vars[@]} -gt 0 ]]; then
            log_warning "Missing or placeholder environment variables: ${missing_vars[*]}"
            add_issue "configuration" "missing_env_vars" "high" "Critical environment variables are not set: ${missing_vars[*]}"
        else
            log_success "All critical environment variables are set"
        fi
    else
        log_error "Environment file not found: $env_file"
        add_issue "configuration" "missing_env_file" "critical" "Environment file .env is missing"
    fi
}

# Test network connectivity
test_network_connectivity() {
    log_info "Testing network connectivity..."
    
    # Test external connectivity
    if curl -s --max-time 5 https://api.github.com >/dev/null 2>&1; then
        log_success "External network connectivity: OK"
    else
        log_warning "External network connectivity: Failed"
        add_issue "network" "external_connectivity_failed" "medium" "Cannot reach external APIs"
    fi
    
    # Test Docker network
    local docker_networks=$(docker network ls --format "{{.Name}}" | grep -E "flash-loan|bridge" || echo "")
    if [[ -n "$docker_networks" ]]; then
        log_success "Docker networks available: $docker_networks"
    else
        log_warning "No relevant Docker networks found"
        add_issue "network" "docker_networks_missing" "medium" "Expected Docker networks not found"
    fi
}

# Generate recommendations
generate_recommendations() {
    log_info "Generating recommendations..."
    
    local recommendations=()
    
    # Check if system is production-ready
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        source "${PROJECT_ROOT}/.env" 2>/dev/null || true
        
        if [[ "${LOG_LEVEL:-}" == "DEBUG" ]]; then
            recommendations+=("Set LOG_LEVEL to INFO or WARNING for production")
        fi
        
        if [[ "${ENABLE_DEBUG:-}" == "true" ]]; then
            recommendations+=("Disable debug mode for production (ENABLE_DEBUG=false)")
        fi
    fi
    
    # Resource recommendations
    local memory_available=$(free -m | awk 'NR==2{print $7}')
    if [[ $memory_available -lt 4096 ]]; then
        recommendations+=("Consider upgrading to at least 4GB RAM for optimal performance")
    fi
    
    # Security recommendations
    recommendations+=("Ensure all API keys are properly secured and not exposed in logs")
    recommendations+=("Use strong passwords for database and cache services")
    recommendations+=("Consider enabling SSL/TLS for production deployments")
    
    # Monitoring recommendations
    recommendations+=("Set up external monitoring for production environments")
    recommendations+=("Configure log rotation to prevent disk space issues")
    recommendations+=("Set up automated backups for database and configuration")
    
    # Save recommendations to report
    for rec in "${recommendations[@]}"; do
        python3 -c "
import json
import sys

try:
    with open('${TROUBLESHOOT_REPORT}', 'r') as f:
        data = json.load(f)
    
    data['recommendations'].append('${rec}')
    
    with open('${TROUBLESHOOT_REPORT}', 'w') as f:
        json.dump(data, f, indent=2)
        
except Exception as e:
    print(f'Error updating recommendations: {e}', file=sys.stderr)
"
    done
    
    log_info "Generated ${#recommendations[@]} recommendations"
}

# Generate final report
generate_final_report() {
    log_info "Generating final troubleshooting report..."
    
    # Update summary
    python3 -c "
import json
import sys

try:
    with open('${TROUBLESHOOT_REPORT}', 'r') as f:
        data = json.load(f)
    
    # Calculate remaining issues
    total_issues = data['summary']['total_issues']
    issues_fixed = data['summary']['issues_fixed']
    issues_remaining = total_issues - issues_fixed
    
    data['summary']['issues_remaining'] = issues_remaining
    
    # Determine overall system health
    if issues_remaining == 0:
        health = 'healthy'
    elif issues_remaining <= 2:
        health = 'warning'
    else:
        health = 'critical'
    
    data['summary']['system_health'] = health
    data['troubleshoot_run']['end_timestamp'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
    
    with open('${TROUBLESHOOT_REPORT}', 'w') as f:
        json.dump(data, f, indent=2)
        
    # Print summary
    print(f'\\n=== TROUBLESHOOTING SUMMARY ===')
    print(f'Total Issues Detected: {total_issues}')
    print(f'Issues Fixed: {issues_fixed}')
    print(f'Issues Remaining: {issues_remaining}')
    print(f'System Health: {health.upper()}')
    print(f'Report saved to: ${TROUBLESHOOT_REPORT}')
        
except Exception as e:
    print(f'Error generating final report: {e}', file=sys.stderr)
"
    
    # Generate human-readable report
    local readable_report="${LOG_DIR}/troubleshoot-summary-$(date +%Y%m%d_%H%M%S).txt"
    cat > "$readable_report" << EOF
LangChain-AutoGen-MCP System Troubleshooting Report
Generated: $(date)

SYSTEM INFORMATION:
$(python3 -c "
import json
with open('${TROUBLESHOOT_REPORT}', 'r') as f:
    data = json.load(f)
    for key, value in data['system_info'].items():
        print(f'  {key}: {value}')
")

ISSUES DETECTED:
$(python3 -c "
import json
with open('${TROUBLESHOOT_REPORT}', 'r') as f:
    data = json.load(f)
    for i, issue in enumerate(data['issues_detected'], 1):
        print(f'  {i}. [{issue[\"severity\"].upper()}] {issue[\"category\"]}: {issue[\"issue\"]}')
        print(f'     {issue[\"description\"]}')
        print()
")

FIXES APPLIED:
$(python3 -c "
import json
with open('${TROUBLESHOOT_REPORT}', 'r') as f:
    data = json.load(f)
    for i, fix in enumerate(data['fixes_applied'], 1):
        status = 'SUCCESS' if fix['success'] else 'FAILED'
        print(f'  {i}. [{status}] {fix[\"issue\"]}')
        print(f'     {fix[\"fix_description\"]}')
        print()
")

RECOMMENDATIONS:
$(python3 -c "
import json
with open('${TROUBLESHOOT_REPORT}', 'r') as f:
    data = json.load(f)
    for i, rec in enumerate(data['recommendations'], 1):
        print(f'  {i}. {rec}')
")

For detailed JSON report, see: ${TROUBLESHOOT_REPORT}
EOF
    
    log_success "Human-readable report generated: $readable_report"
}

# Main troubleshooting function
main() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           LangChain-AutoGen-MCP System Troubleshooter           ║"
    echo "║                                                              ║"
    echo "║  This script will diagnose and attempt to fix common issues ║"
    echo "║  with the unified system deployment.                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log_info "Starting comprehensive system troubleshooting..."
    
    # Initialize report
    init_troubleshoot_report
    
    # Collect system information
    collect_system_info
    
    # Run diagnostic checks
    check_docker_status
    check_required_files
    check_environment_variables
    check_system_resources
    check_port_conflicts
    check_container_status
    test_network_connectivity
    
    # Generate recommendations and final report
    generate_recommendations
    generate_final_report
    
    log_success "Troubleshooting completed!"
    echo
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Review the troubleshooting report"
    echo "2. Address any remaining issues"
    echo "3. Run the test-system.sh script to validate fixes"
    echo "4. Check the deployment guide for additional help"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  --auto-fix            Automatically attempt to fix issues"
        echo "  --auto-start          Automatically start containers if stopped"
        echo "  --aggressive-cleanup  Perform aggressive Docker cleanup (removes volumes)"
        echo "  --help, -h           Show this help message"
        exit 0
        ;;
    --auto-fix)
        AUTO_FIX=true
        ;;
    --auto-start)
        AUTO_START=true
        ;;
    --aggressive-cleanup)
        AGGRESSIVE_CLEANUP=true
        ;;
esac

# Set additional flags from environment
AUTO_FIX="${AUTO_FIX:-false}"
AUTO_START="${AUTO_START:-false}"
AGGRESSIVE_CLEANUP="${AGGRESSIVE_CLEANUP:-false}"

# Run main function
main "$@"