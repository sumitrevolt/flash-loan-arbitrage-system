#!/usr/bin/env python3
"""
Complete Docker Compose file generator for MCP servers
Creates a clean file without duplicates
"""

def create_clean_docker_compose():
    """Create a completely clean Docker Compose file"""
    
    compose_content = '''version: '3.8'

networks:
  mcp-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  redis_data:
  postgres_data:
  rabbitmq_data:
  prometheus_data:
  grafana_data:
  mcp_logs:
  mcp_data:

services:
  # ============================================================================
  # INFRASTRUCTURE SERVICES
  # ============================================================================
  
  redis:
    image: redis:7-alpine
    container_name: mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: mcp-postgres
    environment:
      POSTGRES_DB: mcp_coordination
      POSTGRES_USER: mcp_admin
      POSTGRES_PASSWORD: mcp_secure_2025
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp_admin -d mcp_coordination"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: mcp-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: mcp_admin
      RABBITMQ_DEFAULT_PASS: mcp_secure_2025
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: mcp-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - mcp-network
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: mcp-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: mcp_admin_2025
    ports:
      - "3002:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - mcp-network
    restart: unless-stopped

  # ============================================================================
  # COORDINATION SERVERS (Priority: Highest)
  # ============================================================================

  coordinator-enhanced:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-coordinator-enhanced
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=coordinator-enhanced
      - MCP_SERVER_PORT=3000
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://mcp_admin:mcp_secure_2025@postgres:5432/mcp_coordination
      - RABBITMQ_URL=amqp://mcp_admin:mcp_secure_2025@rabbitmq:5672/
    ports:
      - "3000:3000"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
      - postgres
      - rabbitmq
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/coordination/mcp_enhanced_coordinator.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  server-coordinator:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-server-coordinator
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=server-coordinator
      - MCP_SERVER_PORT=3001
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://mcp_admin:mcp_secure_2025@postgres:5432/mcp_coordination
      - RABBITMQ_URL=amqp://mcp_admin:mcp_secure_2025@rabbitmq:5672/
    ports:
      - "3001:3001"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
      - postgres
      - rabbitmq
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/coordination/server_coordinator.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  integration-bridge:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-integration-bridge
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=integration-bridge
      - MCP_SERVER_PORT=3003
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://mcp_admin:mcp_secure_2025@postgres:5432/mcp_coordination
      - RABBITMQ_URL=amqp://mcp_admin:mcp_secure_2025@rabbitmq:5672/
    ports:
      - "3003:3003"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
      - postgres
      - rabbitmq
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/coordination/integration_bridge.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  unified-coordinator:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-unified-coordinator
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=unified-coordinator
      - MCP_SERVER_PORT=3004
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://mcp_admin:mcp_secure_2025@postgres:5432/mcp_coordination
      - RABBITMQ_URL=amqp://mcp_admin:mcp_secure_2025@rabbitmq:5672/
    ports:
      - "3004:3004"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
      - postgres
      - rabbitmq
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/coordination/unified_coordinator.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # ============================================================================
  # AI INTEGRATION SERVERS (Priority: High)
  # ============================================================================

  context7-clean:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-context7-clean
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=context7-clean
      - MCP_SERVER_PORT=3010
      - REDIS_URL=redis://redis:6379
    ports:
      - "3010:3010"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/ai_integration/context7_clean.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3010/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  grok3:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-grok3
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=grok3
      - MCP_SERVER_PORT=3011
      - REDIS_URL=redis://redis:6379
    ports:
      - "3011:3011"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/ai_integration/grok3.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3011/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  start-grok3:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-start-grok3
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=start-grok3
      - MCP_SERVER_PORT=3012
      - REDIS_URL=redis://redis:6379
    ports:
      - "3012:3012"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/ai_integration/start_grok3.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3012/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  copilot:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-copilot
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=copilot
      - MCP_SERVER_PORT=3013
      - REDIS_URL=redis://redis:6379
    ports:
      - "3013:3013"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/ai_integration/copilot.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3013/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  context7:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-context7
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=context7
      - MCP_SERVER_PORT=3014
      - REDIS_URL=redis://redis:6379
    ports:
      - "3014:3014"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/ai_integration/context7.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3014/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # ============================================================================
  # BLOCKCHAIN INTEGRATION SERVERS (Priority: High)
  # ============================================================================

  matic-clean:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-matic-clean
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=matic-clean
      - MCP_SERVER_PORT=3020
      - REDIS_URL=redis://redis:6379
    ports:
      - "3020:3020"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/blockchain_integration/matic_clean.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3020/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  matic:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-matic
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=matic
      - MCP_SERVER_PORT=3021
      - REDIS_URL=redis://redis:6379
    ports:
      - "3021:3021"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/blockchain_integration/matic.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3021/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  foundry:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-foundry
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=foundry
      - MCP_SERVER_PORT=3022
      - REDIS_URL=redis://redis:6379
    ports:
      - "3022:3022"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/blockchain_integration/foundry.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3022/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  flash-loan:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-flash-loan
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=flash-loan
      - MCP_SERVER_PORT=3023
      - REDIS_URL=redis://redis:6379
    ports:
      - "3023:3023"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/blockchain_integration/flash_loan.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3023/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  evm:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-evm
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=evm
      - MCP_SERVER_PORT=3024
      - REDIS_URL=redis://redis:6379
    ports:
      - "3024:3024"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/blockchain_integration/evm.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3024/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  matic-server:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-matic-server
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=matic-server
      - MCP_SERVER_PORT=3025
      - REDIS_URL=redis://redis:6379
    ports:
      - "3025:3025"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/blockchain_integration/matic_server.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3025/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # ============================================================================
  # DATA & EXECUTION SERVERS (Priority: Medium)
  # ============================================================================

  dex-price:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-dex-price
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=dex-price
      - MCP_SERVER_PORT=3030
      - REDIS_URL=redis://redis:6379
    ports:
      - "3030:3030"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/data_providers/dex_price.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3030/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  price-oracle:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-price-oracle
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=price-oracle
      - MCP_SERVER_PORT=3031
      - REDIS_URL=redis://redis:6379
    ports:
      - "3031:3031"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/data_providers/price_oracle.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3031/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  dex-services:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-dex-services
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=dex-services
      - MCP_SERVER_PORT=3032
      - REDIS_URL=redis://redis:6379
    ports:
      - "3032:3032"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/execution/dex_services.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3032/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  evm-integration:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-evm-integration
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=evm-integration
      - MCP_SERVER_PORT=3033
      - REDIS_URL=redis://redis:6379
    ports:
      - "3033:3033"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/execution/evm_integration.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3033/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  contract-executor:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-contract-executor
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=contract-executor
      - MCP_SERVER_PORT=3034
      - REDIS_URL=redis://redis:6379
    ports:
      - "3034:3034"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/execution/contract_executor.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3034/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # ============================================================================
  # SPECIALIZED SERVERS (Priority: Medium)
  # ============================================================================

  flash-loan-strategist:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp-server
    container_name: mcp-flash-loan-strategist
    environment:
      - PYTHONPATH=/app
      - MCP_SERVER_NAME=flash-loan-strategist
      - MCP_SERVER_PORT=3040
      - REDIS_URL=redis://redis:6379
    ports:
      - "3040:3040"
    volumes:
      - ../mcp_servers:/app/mcp_servers
      - mcp_logs:/app/logs
      - mcp_data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
    entrypoint: ["/app/docker/entrypoint.sh"]
    command: ["python", "/app/mcp_servers/flash_loan_strategy/flash_loan_strategist.py"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3040/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
'''
    
    with open('docker-compose.mcp-servers.yml', 'w') as f:
        f.write(compose_content)
    
    print("Clean Docker Compose file created successfully!")
    print("Services included:")
    print("- Infrastructure: redis, postgres, rabbitmq, prometheus, grafana")
    print("- Coordination: coordinator-enhanced, server-coordinator, integration-bridge, unified-coordinator")
    print("- AI Integration: context7-clean, grok3, start-grok3, copilot, context7")
    print("- Blockchain: matic-clean, matic, foundry, flash-loan, evm, matic-server")
    print("- Data & Execution: dex-price, price-oracle, dex-services, evm-integration, contract-executor")
    print("- Specialized: flash-loan-strategist")
    print("Total: 26 services (5 infrastructure + 21 MCP servers)")

if __name__ == "__main__":
    create_clean_docker_compose()
