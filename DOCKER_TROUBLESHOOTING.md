# Docker Compose Troubleshooting Guide

## 🚨 Issue: Web3 Node Container Failing

### Problem
The `flash-loan-web3-node` container was marked as unhealthy, causing the entire Docker Compose application to fail to start.

### Root Causes
1. **Health check using `curl` instead of `wget`** - The ethereum/client-go image doesn't have curl installed
2. **Trying to sync with Ethereum mainnet** - This requires enormous resources and time
3. **Invalid health check endpoint** - Simple port checking doesn't verify JSON-RPC functionality

### ✅ Solutions Applied

#### 1. Switched to Development Mode
**Before:**
```yaml
command: >
  --http
  --http.addr 0.0.0.0
  --http.api eth,net,web3,debug
  --syncmode snap
```

**After:**
```yaml
command: >
  --dev
  --dev.period 1
  --http
  --http.addr 0.0.0.0
  --http.port 8545
  --http.api eth,net,web3,debug,personal,txpool
  --allow-insecure-unlock
  --mine
  --miner.threads 1
```

#### 2. Fixed Health Check
**Before:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8545"]
```

**After:**
```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "wget -q -O - --post-data='{\"jsonrpc\":\"2.0\",\"method\":\"web3_clientVersion\",\"params\":[],\"id\":1}' --header='Content-Type: application/json' http://localhost:8545 | grep -q '\"result\"'"]
```

#### 3. Added WebSocket Support
```yaml
ports:
  - "${WEB3_NODE_PORT:-8545}:8545"
  - "${WEB3_WS_PORT:-8546}:8546"
```

## 🔧 How to Fix Your Setup

### Option 1: Use the Automated Fix Script
```powershell
.\fix_docker_startup.ps1
```

### Option 2: Manual Steps

1. **Stop all containers:**
```bash
docker compose down --remove-orphans
```

2. **Clean up problematic containers:**
```bash
docker container rm -f flash-loan-web3-node flash-loan-postgres flash-loan-redis
```

3. **Start services incrementally:**
```bash
# Start infrastructure first
docker compose up -d postgres redis

# Wait for them to be healthy
docker compose ps

# Start web3 node
docker compose up -d web3-node

# Start application services
docker compose up -d
```

## 🧪 Testing the Fix

### Test Web3 Node
```bash
# Test basic connectivity
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":1}' \
  http://localhost:8545

# Expected response:
# {"jsonrpc":"2.0","id":1,"result":"Geth/v1.x.x-stable/linux-amd64/go1.x.x"}
```

### Check Container Health
```bash
docker compose ps
# All containers should show "healthy" status
```

### View Logs
```bash
# Check specific container logs
docker compose logs web3-node
docker compose logs postgres
docker compose logs redis
```

## 🎯 Benefits of the New Setup

1. **Fast Startup** - Development mode starts immediately, no blockchain sync required
2. **Reliable Health Checks** - Actually tests JSON-RPC functionality
3. **Complete API Access** - Includes personal and txpool APIs for development
4. **WebSocket Support** - Enables real-time blockchain event monitoring
5. **Auto-mining** - Automatically mines blocks for testing

## 🚀 Next Steps

After the infrastructure is running:

1. **Start Application Services:**
```bash
docker compose up -d langchain-coordinator autogen-coordinator
```

2. **Access Services:**
- Web3 RPC: http://localhost:8545
- Web3 WebSocket: ws://localhost:8546
- PostgreSQL: localhost:5432
- Redis: localhost:6379

3. **Monitor Status:**
```bash
docker compose ps
docker compose logs -f
```

## 🔍 Common Issues and Solutions

### Issue: "Port already in use"
```bash
# Find what's using the port
netstat -ano | findstr :8545
# Kill the process or change the port in docker-compose.env
```

### Issue: "Network not found"
```bash
# Recreate the network
docker network rm flashloan_flash-loan-network
docker compose up -d
```

### Issue: "Volume mount failed"
```bash
# Ensure directories exist
mkdir -p logs deployment/docker/langchain deployment/docker/autogen
```

## 📝 Environment Variables

Create a `.env` file or use `docker-compose.env`:

```env
# Database
POSTGRES_DB=flash_loan_db
POSTGRES_USER=flash_loan_user
POSTGRES_PASSWORD=flash_loan_secure_2025

# Web3
WEB3_NODE_PORT=8545
WEB3_WS_PORT=8546

# Redis
REDIS_PASSWORD=flash_loan_redis_2025

# Development
ENABLE_REAL_EXECUTION=false
ENABLE_TESTING=true
```

This setup provides a stable, fast-starting development environment for your flash loan application! 