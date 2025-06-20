#!/bin/bash
# Flash Loan Arbitrage System Startup Script

set -e

echo "🚀 Starting Flash Loan Arbitrage System..."

# Check prerequisites
echo "🔍 Checking prerequisites..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo "⚠️ No .env file found, using defaults"
fi

# Start services based on mode
MODE=${1:-development}

case $MODE in
    "development")
        echo "🔧 Starting in development mode..."
        npm run dev
        ;;
    "production")
        echo "🏭 Starting in production mode..."
        docker-compose up -d
        echo "✅ Production services started"
        echo "📊 Dashboard: http://localhost:8000"
        echo "📈 Grafana: http://localhost:3000"
        ;;
    "docker")
        echo "🐳 Starting with Docker..."
        docker-compose up
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        echo "Usage: $0 [development|production|docker]"
        exit 1
        ;;
esac
