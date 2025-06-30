#!/bin/bash
set -e

echo "Starting Arbitrage Executor Service..."

# Wait for dependencies
echo "Waiting for Web3 node..."
while ! curl -f http://flash-loan-web3-node:8545 >/dev/null 2>&1; do
    echo "Web3 node not ready, waiting..."
    sleep 5
done

echo "Waiting for Redis..."
while ! python -c "import redis; r=redis.Redis(host='flash-loan-redis', port=6379, password='flash_loan_redis_2025'); r.ping()" >/dev/null 2>&1; do
    echo "Redis not ready, waiting..."
    sleep 5
done

echo "Waiting for Blockchain Monitor..."
while ! curl -f http://blockchain-monitor:8070/health >/dev/null 2>&1; do
    echo "Blockchain monitor not ready, waiting..."
    sleep 5
done

echo "Starting arbitrage executor..."
cd /app
python -m execution.arbitrage_executor 