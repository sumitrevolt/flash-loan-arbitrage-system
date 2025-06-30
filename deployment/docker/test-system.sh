#!/bin/bash

# Comprehensive System Testing and Validation Script
# For the Unified LangChain-AutoGen-MCP Flash Loan System
# 
# This script validates all container builds, tests service endpoints,
# verifies integrations, and performs end-to-end testing

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs/test-results"
CONFIG_DIR="${PROJECT_ROOT}/config"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.unified.yml"
TEST_RESULTS_FILE="${LOG_DIR}/system-test-results-$(date +%Y%m%d_%H%M%S).json"
HEALTH_CHECK_TIMEOUT=300
SERVICE_START_TIMEOUT=180

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p "${LOG_DIR}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/test-system.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/test-system.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/test-system.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${LOG_DIR}/test-system.log"
}

# Initialize test results JSON
init_test_results() {
    cat > "${TEST_RESULTS_FILE}" << EOF
{
  "test_run": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "script_version": "1.0.0",
    "system": "LangChain-AutoGen-MCP Unified System"
  },
  "phases": {
    "pre_deployment": {
      "status": "pending",
      "checks": {}
    },
    "container_builds": {
      "status": "pending",
      "builds": {}
    },
    "service_deployment": {
      "status": "pending",
      "services": {}
    },
    "endpoint_testing": {
      "status": "pending",
      "endpoints": {}
    },
    "integration_testing": {
      "status": "pending",
      "integrations": {}
    },
    "load_testing": {
      "status": "pending",
      "results": {}
    },
    "end_to_end_testing": {
      "status": "pending",
      "scenarios": {}
    }
  },
  "summary": {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "duration_seconds": 0
  }
}
EOF
}

# Update test results JSON
update_test_result() {
    local phase="$1"
    local test_name="$2"
    local status="$3"
    local details="$4"
    local duration="${5:-0}"
    
    python3 -c "
import json
import sys

try:
    with open('${TEST_RESULTS_FILE}', 'r') as f:
        data = json.load(f)
    
    # Update phase status and test result
    if '${phase}' not in data['phases']:
        data['phases']['${phase}'] = {'status': 'pending'}
    
    # Determine the correct key based on phase
    if '${phase}' == 'container_builds':
        key = 'builds'
    elif '${phase}' == 'service_deployment':
        key = 'services'
    elif '${phase}' == 'endpoint_testing':
        key = 'endpoints'
    elif '${phase}' == 'integration_testing':
        key = 'integrations'
    elif '${phase}' == 'load_testing':
        key = 'results'
    elif '${phase}' == 'end_to_end_testing':
        key = 'scenarios'
    else:
        key = 'checks'
    
    if key not in data['phases']['${phase}']:
        data['phases']['${phase}'][key] = {}
    
    data['phases']['${phase}'][key]['${test_name}'] = {
        'status': '${status}',
        'details': '${details}',
        'duration_seconds': ${duration},
        'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
    }
    
    # Update summary counters
    data['summary']['total_tests'] += 1
    if '${status}' == 'passed':
        data['summary']['passed'] += 1
    elif '${status}' == 'failed':
        data['summary']['failed'] += 1
    elif '${status}' == 'warning':
        data['summary']['warnings'] += 1
    
    with open('${TEST_RESULTS_FILE}', 'w') as f:
        json.dump(data, f, indent=2)
        
except Exception as e:
    print(f'Error updating test results: {e}', file=sys.stderr)
    sys.exit(1)
"
}

# Pre-deployment checks
run_pre_deployment_checks() {
    log_info "Starting pre-deployment checks..."
    local start_time=$(date +%s)
    
    # Check Docker installation
    if command -v docker >/dev/null 2>&1; then
        log_success "Docker is installed: $(docker --version)"
        update_test_result "pre_deployment" "docker_installation" "passed" "Docker is available"
    else
        log_error "Docker is not installed"
        update_test_result "pre_deployment" "docker_installation" "failed" "Docker not found"
        return 1
    fi
    
    # Check Docker Compose installation
    if command -v docker-compose >/dev/null 2>&1; then
        log_success "Docker Compose is installed: $(docker-compose --version)"
        update_test_result "pre_deployment" "docker_compose_installation" "passed" "Docker Compose is available"
    else
        log_error "Docker Compose is not installed"
        update_test_result "pre_deployment" "docker_compose_installation" "failed" "Docker Compose not found"
        return 1
    fi
    
    # Check required files
    local required_files=(
        "${COMPOSE_FILE}"
        "${CONFIG_DIR}/unified_mcp_config.json"
        "${PROJECT_ROOT}/.env"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "Required file exists: $file"
            update_test_result "pre_deployment" "file_$(basename "$file")" "passed" "File exists"
        else
            log_error "Required file missing: $file"
            update_test_result "pre_deployment" "file_$(basename "$file")" "failed" "File not found"
        fi
    done
    
    # Check system resources
    local available_memory=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
    local available_disk=$(df -h "${PROJECT_ROOT}" | awk 'NR==2{print $4}')
    
    log_info "Available memory: ${available_memory}GB"
    log_info "Available disk space: ${available_disk}"
    
    if (( $(echo "$available_memory > 4.0" | bc -l) )); then
        update_test_result "pre_deployment" "memory_check" "passed" "Sufficient memory: ${available_memory}GB"
    else
        update_test_result "pre_deployment" "memory_check" "warning" "Low memory: ${available_memory}GB"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "Pre-deployment checks completed in ${duration} seconds"
}

# Validate container builds
validate_container_builds() {
    log_info "Starting container build validation..."
    local start_time=$(date +%s)
    
    # List of services to build
    local services=(
        "langchain-coordinator::deployment/docker/langchain/Dockerfile"
        "autogen-coordinator::deployment/docker/autogen/Dockerfile"
        "mcp-supermemory::deployment/docker/containers/mcp_servers/Dockerfile.supermemory"
        "web-dashboard::deployment/docker/containers/dashboard/Dockerfile"
        "health-checker::deployment/docker/containers/health-checker/Dockerfile"
    )
    
    for service_def in "${services[@]}"; do
        IFS="::" read -r service_name dockerfile_path <<< "$service_def"
        log_info "Building container for service: $service_name"
        
        local build_start=$(date +%s)
        if docker build -t "test-${service_name}" -f "${PROJECT_ROOT}/${dockerfile_path}" "${PROJECT_ROOT}" > "${LOG_DIR}/build-${service_name}.log" 2>&1; then
            local build_end=$(date +%s)
            local build_duration=$((build_end - build_start))
            log_success "Successfully built $service_name in ${build_duration} seconds"
            update_test_result "container_builds" "$service_name" "passed" "Build successful" "$build_duration"
        else
            log_error "Failed to build $service_name"
            update_test_result "container_builds" "$service_name" "failed" "Build failed" "0"
        fi
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "Container build validation completed in ${duration} seconds"
}

# Deploy services
deploy_services() {
    log_info "Starting service deployment..."
    local start_time=$(date +%s)
    
    # Stop any existing services
    log_info "Stopping existing services..."
    docker-compose -f "${COMPOSE_FILE}" down --remove-orphans > "${LOG_DIR}/docker-down.log" 2>&1 || true
    
    # Start infrastructure services first
    log_info "Starting infrastructure services..."
    if docker-compose -f "${COMPOSE_FILE}" up -d postgres redis rabbitmq > "${LOG_DIR}/docker-infra-up.log" 2>&1; then
        log_success "Infrastructure services started"
        update_test_result "service_deployment" "infrastructure" "passed" "Services started successfully"
    else
        log_error "Failed to start infrastructure services"
        update_test_result "service_deployment" "infrastructure" "failed" "Failed to start services"
        return 1
    fi
    
    # Wait for infrastructure to be ready
    log_info "Waiting for infrastructure services to be ready..."
    sleep 30
    
    # Start MCP servers
    log_info "Starting MCP servers..."
    if docker-compose -f "${COMPOSE_FILE}" up -d mcp-supermemory mcp-context7 mcp-filesystem mcp-taskmanager > "${LOG_DIR}/docker-mcp-up.log" 2>&1; then
        log_success "MCP servers started"
        update_test_result "service_deployment" "mcp_servers" "passed" "MCP servers started successfully"
    else
        log_error "Failed to start MCP servers"
        update_test_result "service_deployment" "mcp_servers" "failed" "Failed to start MCP servers"
        return 1
    fi
    
    # Wait for MCP servers to be ready
    log_info "Waiting for MCP servers to be ready..."
    sleep 45
    
    # Start coordinator services
    log_info "Starting coordinator services..."
    if docker-compose -f "${COMPOSE_FILE}" up -d langchain-coordinator autogen-coordinator > "${LOG_DIR}/docker-coordinators-up.log" 2>&1; then
        log_success "Coordinator services started"
        update_test_result "service_deployment" "coordinators" "passed" "Coordinators started successfully"
    else
        log_error "Failed to start coordinator services"
        update_test_result "service_deployment" "coordinators" "failed" "Failed to start coordinators"
        return 1
    fi
    
    # Start remaining services
    log_info "Starting remaining services..."
    if docker-compose -f "${COMPOSE_FILE}" up -d > "${LOG_DIR}/docker-all-up.log" 2>&1; then
        log_success "All services started"
        update_test_result "service_deployment" "all_services" "passed" "All services started successfully"
    else
        log_error "Failed to start all services"
        update_test_result "service_deployment" "all_services" "failed" "Failed to start all services"
        return 1
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "Service deployment completed in ${duration} seconds"
}

# Test service endpoints
test_service_endpoints() {
    log_info "Starting endpoint testing..."
    local start_time=$(date +%s)
    
    # Define endpoints to test
    local endpoints=(
        "postgres::localhost:5432::tcp"
        "redis::localhost:6379::tcp"
        "rabbitmq::localhost:15672::http"
        "mcp-supermemory::localhost:8100/health::http"
        "mcp-context7::localhost:8101/health::http"
        "mcp-filesystem::localhost:8102/health::http"
        "mcp-taskmanager::localhost:8103/health::http"
        "langchain-coordinator::localhost:8000/health::http"
        "autogen-coordinator::localhost:8010/health::http"
        "prometheus::localhost:9090/-/healthy::http"
        "grafana::localhost:3000/api/health::http"
        "elasticsearch::localhost:9200/_cluster/health::http"
        "kibana::localhost:5601/api/status::http"
        "web-dashboard::localhost:8090/health::http"
    )
    
    for endpoint_def in "${endpoints[@]}"; do
        IFS="::" read -r service_name endpoint protocol <<< "$endpoint_def"
        log_info "Testing endpoint: $service_name ($endpoint)"
        
        local test_start=$(date +%s)
        local test_result="failed"
        local test_details=""
        
        case "$protocol" in
            "http")
                if curl -f -s --max-time 10 "http://$endpoint" > /dev/null 2>&1; then
                    test_result="passed"
                    test_details="HTTP endpoint responded successfully"
                else
                    test_details="HTTP endpoint did not respond or returned error"
                fi
                ;;
            "tcp")
                if timeout 10 bash -c "echo >/dev/tcp/${endpoint/:/ }" 2>/dev/null; then
                    test_result="passed"
                    test_details="TCP connection successful"
                else
                    test_details="TCP connection failed"
                fi
                ;;
        esac
        
        local test_end=$(date +%s)
        local test_duration=$((test_end - test_start))
        
        if [[ "$test_result" == "passed" ]]; then
            log_success "Endpoint test passed: $service_name"
        else
            log_error "Endpoint test failed: $service_name"
        fi
        
        update_test_result "endpoint_testing" "$service_name" "$test_result" "$test_details" "$test_duration"
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "Endpoint testing completed in ${duration} seconds"
}

# Test integrations
test_integrations() {
    log_info "Starting integration testing..."
    local start_time=$(date +%s)
    
    # Test LangChain to AutoGen communication
    log_info "Testing LangChain to AutoGen integration..."
    if curl -f -s --max-time 30 -X POST "http://localhost:8000/api/v1/coordinate" \
        -H "Content-Type: application/json" \
        -d '{"task": "test_integration", "target": "autogen"}' > "${LOG_DIR}/langchain-autogen-test.json" 2>&1; then
        log_success "LangChain to AutoGen integration test passed"
        update_test_result "integration_testing" "langchain_autogen" "passed" "Integration successful"
    else
        log_error "LangChain to AutoGen integration test failed"
        update_test_result "integration_testing" "langchain_autogen" "failed" "Integration failed"
    fi
    
    # Test MCP server connectivity
    local mcp_servers=("supermemory" "context7" "filesystem" "taskmanager")
    for server in "${mcp_servers[@]}"; do
        log_info "Testing MCP server connectivity: $server"
        local port_map="8100 8101 8102 8103"
        local ports=($port_map)
        local index=0
        
        case "$server" in
            "supermemory") index=0 ;;
            "context7") index=1 ;;
            "filesystem") index=2 ;;
            "taskmanager") index=3 ;;
        esac
        
        local port=${ports[$index]}
        if curl -f -s --max-time 10 "http://localhost:$port/health" > /dev/null 2>&1; then
            log_success "MCP server $server is accessible"
            update_test_result "integration_testing" "mcp_$server" "passed" "Server accessible"
        else
            log_error "MCP server $server is not accessible"
            update_test_result "integration_testing" "mcp_$server" "failed" "Server not accessible"
        fi
    done
    
    # Test database connectivity
    log_info "Testing database connectivity..."
    if docker exec flash-loan-postgres pg_isready -U flash_loan_user -d flash_loan_db > /dev/null 2>&1; then
        log_success "PostgreSQL connectivity test passed"
        update_test_result "integration_testing" "postgresql" "passed" "Database accessible"
    else
        log_error "PostgreSQL connectivity test failed"
        update_test_result "integration_testing" "postgresql" "failed" "Database not accessible"
    fi
    
    # Test Redis connectivity
    log_info "Testing Redis connectivity..."
    if docker exec flash-loan-redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis connectivity test passed"
        update_test_result "integration_testing" "redis" "passed" "Cache accessible"
    else
        log_error "Redis connectivity test failed"
        update_test_result "integration_testing" "redis" "failed" "Cache not accessible"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "Integration testing completed in ${duration} seconds"
}

# Perform load testing
perform_load_testing() {
    log_info "Starting load testing..."
    local start_time=$(date +%s)
    
    # Test LangChain coordinator load
    log_info "Testing LangChain coordinator load handling..."
    if command -v ab >/dev/null 2>&1; then
        if ab -n 100 -c 10 -T application/json -p <(echo '{"task": "test_load"}') \
            "http://localhost:8000/api/v1/status" > "${LOG_DIR}/langchain-load-test.log" 2>&1; then
            local avg_response_time=$(grep "Time per request" "${LOG_DIR}/langchain-load-test.log" | head -1 | awk '{print $4}')
            log_success "LangChain load test passed. Average response time: ${avg_response_time}ms"
            update_test_result "load_testing" "langchain_load" "passed" "Average response: ${avg_response_time}ms"
        else
            log_error "LangChain load test failed"
            update_test_result "load_testing" "langchain_load" "failed" "Load test failed"
        fi
    else
        log_warning "Apache Bench (ab) not available for load testing"
        update_test_result "load_testing" "langchain_load" "warning" "Load testing tool not available"
    fi
    
    # Test AutoGen coordinator load
    log_info "Testing AutoGen coordinator load handling..."
    if command -v ab >/dev/null 2>&1; then
        if ab -n 50 -c 5 "http://localhost:8010/health" > "${LOG_DIR}/autogen-load-test.log" 2>&1; then
            local avg_response_time=$(grep "Time per request" "${LOG_DIR}/autogen-load-test.log" | head -1 | awk '{print $4}')
            log_success "AutoGen load test passed. Average response time: ${avg_response_time}ms"
            update_test_result "load_testing" "autogen_load" "passed" "Average response: ${avg_response_time}ms"
        else
            log_error "AutoGen load test failed"
            update_test_result "load_testing" "autogen_load" "failed" "Load test failed"
        fi
    else
        log_warning "Apache Bench (ab) not available for load testing"
        update_test_result "load_testing" "autogen_load" "warning" "Load testing tool not available"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "Load testing completed in ${duration} seconds"
}

# End-to-end testing
run_end_to_end_tests() {
    log_info "Starting end-to-end testing..."
    local start_time=$(date +%s)
    
    # Flash loan workflow test
    log_info "Testing flash loan workflow..."
    local workflow_payload='{
        "workflow": "flash_loan_arbitrage",
        "parameters": {
            "token_in": "WETH",
            "token_out": "USDC",
            "amount": "1000000000000000000",
            "platforms": ["uniswap", "sushiswap"],
            "max_slippage": "0.01",
            "test_mode": true
        }
    }'
    
    if curl -f -s --max-time 60 -X POST "http://localhost:8000/api/v1/execute" \
        -H "Content-Type: application/json" \
        -d "$workflow_payload" > "${LOG_DIR}/flash-loan-workflow-test.json" 2>&1; then
        log_success "Flash loan workflow test passed"
        update_test_result "end_to_end_testing" "flash_loan_workflow" "passed" "Workflow executed successfully"
    else
        log_error "Flash loan workflow test failed"
        update_test_result "end_to_end_testing" "flash_loan_workflow" "failed" "Workflow execution failed"
    fi
    
    # Multi-agent coordination test
    log_info "Testing multi-agent coordination..."
    local coordination_payload='{
        "scenario": "multi_agent_analysis",
        "agents": ["price_analyzer", "risk_assessor", "execution_planner"],
        "task": "analyze_arbitrage_opportunity",
        "data": {
            "token_pair": "ETH/USDC",
            "exchanges": ["uniswap_v3", "sushiswap"],
            "test_mode": true
        }
    }'
    
    if curl -f -s --max-time 90 -X POST "http://localhost:8000/api/v1/coordinate" \
        -H "Content-Type: application/json" \
        -d "$coordination_payload" > "${LOG_DIR}/multi-agent-test.json" 2>&1; then
        log_success "Multi-agent coordination test passed"
        update_test_result "end_to_end_testing" "multi_agent_coordination" "passed" "Coordination successful"
    else
        log_error "Multi-agent coordination test failed"
        update_test_result "end_to_end_testing" "multi_agent_coordination" "failed" "Coordination failed"
    fi
    
    # MCP integration workflow test
    log_info "Testing MCP integration workflow..."
    local mcp_payload='{
        "workflow": "mcp_enhanced_analysis",
        "mcp_servers": ["supermemory", "context7"],
        "task": "research_defi_protocols",
        "parameters": {
            "protocols": ["aave", "compound"],
            "analysis_depth": "basic",
            "test_mode": true
        }
    }'
    
    if curl -f -s --max-time 120 -X POST "http://localhost:8000/api/v1/mcp/execute" \
        -H "Content-Type: application/json" \
        -d "$mcp_payload" > "${LOG_DIR}/mcp-workflow-test.json" 2>&1; then
        log_success "MCP integration workflow test passed"
        update_test_result "end_to_end_testing" "mcp_integration_workflow" "passed" "MCP workflow successful"
    else
        log_error "MCP integration workflow test failed"
        update_test_result "end_to_end_testing" "mcp_integration_workflow" "failed" "MCP workflow failed"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "End-to-end testing completed in ${duration} seconds"
}

# Generate comprehensive test report
generate_test_report() {
    log_info "Generating comprehensive test report..."
    
    # Update total duration in test results
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - SCRIPT_START_TIME))
    
    python3 -c "
import json
import sys

try:
    with open('${TEST_RESULTS_FILE}', 'r') as f:
        data = json.load(f)
    
    data['summary']['duration_seconds'] = ${total_duration}
    data['test_run']['end_timestamp'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
    
    with open('${TEST_RESULTS_FILE}', 'w') as f:
        json.dump(data, f, indent=2)
        
except Exception as e:
    print(f'Error updating final test results: {e}', file=sys.stderr)
    sys.exit(1)
"
    
    # Generate HTML report
    local html_report="${LOG_DIR}/system-test-report-$(date +%Y%m%d_%H%M%S).html"
    cat > "$html_report" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Test Report - LangChain-AutoGen-MCP</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .phase { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .passed { background: #d4edda; border-color: #c3e6cb; }
        .failed { background: #f8d7da; border-color: #f5c6cb; }
        .warning { background: #fff3cd; border-color: #ffeaa7; }
        .summary { background: #e2e3e5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>System Test Report</h1>
        <p><strong>System:</strong> LangChain-AutoGen-MCP Unified Flash Loan System</p>
        <p><strong>Test Run:</strong> $(date)</p>
        <p><strong>Duration:</strong> ${total_duration} seconds</p>
    </div>
EOF
    
    # Add test results summary
    echo "    <div class=\"summary\">" >> "$html_report"
    echo "        <h2>Test Summary</h2>" >> "$html_report"
    
    # Extract summary from JSON
    python3 -c "
import json
with open('${TEST_RESULTS_FILE}', 'r') as f:
    data = json.load(f)
    summary = data['summary']
    print(f'        <p><strong>Total Tests:</strong> {summary[\"total_tests\"]}</p>')
    print(f'        <p><strong>Passed:</strong> {summary[\"passed\"]}</p>')
    print(f'        <p><strong>Failed:</strong> {summary[\"failed\"]}</p>')
    print(f'        <p><strong>Warnings:</strong> {summary[\"warnings\"]}</p>')
" >> "$html_report"
    
    echo "    </div>" >> "$html_report"
    echo "</body></html>" >> "$html_report"
    
    log_success "Test report generated: $html_report"
    log_success "Detailed results: $TEST_RESULTS_FILE"
    
    # Print summary to console
    echo
    echo "========================== TEST SUMMARY =========================="
    python3 -c "
import json
with open('${TEST_RESULTS_FILE}', 'r') as f:
    data = json.load(f)
    summary = data['summary']
    print(f'Total Tests: {summary[\"total_tests\"]}')
    print(f'Passed: {summary[\"passed\"]}')
    print(f'Failed: {summary[\"failed\"]}')
    print(f'Warnings: {summary[\"warnings\"]}')
    print(f'Duration: {summary[\"duration_seconds\"]} seconds')
    
    if summary['failed'] > 0:
        print('\nFAILED TESTS:')
        for phase_name, phase_data in data['phases'].items():
            if isinstance(phase_data, dict):
                for test_type in ['checks', 'builds', 'services', 'endpoints', 'integrations', 'results', 'scenarios']:
                    if test_type in phase_data and isinstance(phase_data[test_type], dict):
                        for test_name, test_result in phase_data[test_type].items():
                            if test_result.get('status') == 'failed':
                                print(f'  - {phase_name}.{test_name}: {test_result.get(\"details\", \"No details\")}')
"
    echo "==============================================================="
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."
    
    # Stop services if requested
    if [[ "${CLEANUP_SERVICES:-false}" == "true" ]]; then
        log_info "Stopping all services..."
        docker-compose -f "${COMPOSE_FILE}" down --remove-orphans > "${LOG_DIR}/cleanup-down.log" 2>&1 || true
    fi
    
    # Remove test images
    log_info "Removing test images..."
    docker images | grep "^test-" | awk '{print $3}' | xargs -r docker rmi -f > "${LOG_DIR}/cleanup-images.log" 2>&1 || true
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    SCRIPT_START_TIME=$(date +%s)
    
    log_info "Starting comprehensive system testing..."
    log_info "Test results will be saved to: $TEST_RESULTS_FILE"
    
    # Initialize test results
    init_test_results
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Run test phases
    if ! run_pre_deployment_checks; then
        log_error "Pre-deployment checks failed. Aborting."
        exit 1
    fi
    
    if ! validate_container_builds; then
        log_error "Container build validation failed. Aborting."
        exit 1
    fi
    
    if ! deploy_services; then
        log_error "Service deployment failed. Aborting."
        exit 1
    fi
    
    # Wait for services to stabilize
    log_info "Waiting for services to stabilize..."
    sleep 60
    
    test_service_endpoints
    test_integrations
    perform_load_testing
    run_end_to_end_tests
    
    # Generate final report
    generate_test_report
    
    log_success "Comprehensive system testing completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  --cleanup-services    Stop all services after testing"
        echo "  --help, -h           Show this help message"
        exit 0
        ;;
    --cleanup-services)
        CLEANUP_SERVICES=true
        ;;
esac

# Run main function
main "$@"