"""
Complete System Integration Test
Tests the entire flash loan arbitrage system end-to-end
"""

import asyncio
import pytest
import logging
from decimal import Decimal
from datetime import datetime, timedelta

from src.core.database import init_database, db_ops
from src.core.arbitrage_engine import ArbitrageEngine
from src.mcp_servers.price_feed_server import PriceFeedServer
from frontend.dashboard import app

logger = logging.getLogger(__name__)

@pytest.fixture
async def system_setup():
    """Setup complete system for testing"""
    # Initialize database
    await init_database()
    
    # Initialize components
    arbitrage_engine = ArbitrageEngine()
    price_feed_server = PriceFeedServer()
    
    yield {
        "arbitrage_engine": arbitrage_engine,
        "price_feed_server": price_feed_server
    }
    
    # Cleanup
    await arbitrage_engine.shutdown()
    await price_feed_server.shutdown()

@pytest.mark.asyncio
async def test_complete_arbitrage_flow(system_setup):
    """Test complete arbitrage discovery and execution flow"""
    components = system_setup
    
    # 1. Test price feed updates
    await components["price_feed_server"].update_price("WETH", "uniswap_v3", Decimal("2000.50"))
    await components["price_feed_server"].update_price("WETH", "quickswap", Decimal("2005.75"))
    
    # 2. Test opportunity discovery
    opportunities = await components["arbitrage_engine"].discover_opportunities()
    assert len(opportunities) > 0, "Should discover arbitrage opportunities"
    
    # 3. Test opportunity execution (simulation mode)
    best_opportunity = max(opportunities, key=lambda x: x.estimated_profit_usd)
    result = await components["arbitrage_engine"].execute_opportunity(best_opportunity, dry_run=True)
    
    assert result["success"], f"Arbitrage execution failed: {result.get('error')}"
    assert result["profit_usd"] > 0, "Should generate positive profit"

@pytest.mark.asyncio
async def test_database_operations():
    """Test database operations and data persistence"""
    # Test saving price feed
    await db_ops.save_price_feed("WETH", "uniswap_v3", Decimal("2000.00"))
    
    # Test retrieving opportunities
    opportunities = await db_ops.get_active_opportunities(limit=10)
    assert isinstance(opportunities, list), "Should return list of opportunities"
    
    # Test recording metrics
    await db_ops.record_system_metric("test_metric", Decimal("100.50"), "USD")

@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker functionality"""
    components = system_setup
    
    # Simulate multiple failures
    for i in range(5):
        await components["arbitrage_engine"].record_failure("WETH", "Transaction failed")
    
    # Check circuit breaker status
    is_tripped = await components["arbitrage_engine"].is_circuit_breaker_active("WETH")
    assert is_tripped, "Circuit breaker should be active after multiple failures"

@pytest.mark.asyncio
async def test_api_endpoints():
    """Test API endpoints and dashboard functionality"""
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/api/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_trades" in data
    assert "active_opportunities" in data
    
    # Test trades endpoint
    response = client.get("/api/trades")
    assert response.status_code == 200

def test_configuration_loading():
    """Test system configuration loading"""
    from src.core.config import load_config
    
    config = load_config()
    
    # Verify required configuration keys
    required_keys = [
        "min_profit_threshold_usd",
        "max_trade_amount_usd",
        "slippage_tolerance_percent"
    ]
    
    for key in required_keys:
        assert key in config, f"Missing required config key: {key}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
