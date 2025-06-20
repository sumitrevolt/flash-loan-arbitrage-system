#!/usr/bin/env python3
"""
Flash Loan Integration Tests
End-to-end integration tests for the complete flash loan system
"""

import pytest
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class TestFlashLoanIntegration:
    
    @pytest.fixture
    def base_url(self):
        """Base URL for MCP servers."""
        return "http://localhost:8000"
    
    @pytest.fixture
    async def session(self):
        """Create HTTP session for testing."""
        session = aiohttp.ClientSession()
        yield session
        await session.close()
    
    @pytest.mark.asyncio
    async def test_mcp_server_health(self, session, base_url):
        """Test all MCP servers are healthy."""
        servers_to_test = [
            "flash-loan",
            "price-feed", 
            "risk-manager",
            "arbitrage",
            "blockchain"
        ]
        
        for server in servers_to_test:
            url = f"{base_url}/{server}/health"
            try:
                async with session.get(url, timeout=10) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data.get("status") == "healthy"
            except Exception as e:
                pytest.fail(f"Server {server} health check failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_price_feed_integration(self, session, base_url):
        """Test price feed integration with multiple DEXes."""
        url = f"{base_url}/price-feed/prices"
        
        async with session.get(url) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify price data structure
            assert "prices" in data
            assert len(data["prices"]) > 0
            
            # Check for major token pairs
            token_pairs = [price["pair"] for price in data["prices"]]
            assert any("ETH" in pair for pair in token_pairs)
            assert any("USDC" in pair for pair in token_pairs)
    
    @pytest.mark.asyncio
    async def test_arbitrage_opportunity_detection(self, session, base_url):
        """Test arbitrage opportunity detection across DEXes."""
        url = f"{base_url}/arbitrage/opportunities"
        
        async with session.get(url) as response:
            assert response.status == 200
            data = await response.json()
            
            assert "opportunities" in data
            
            # If opportunities exist, verify structure
            if data["opportunities"]:
                opp = data["opportunities"][0]
                required_fields = ["token_pair", "profit_potential", "dex_route", "confidence"]
                for field in required_fields:
                    assert field in opp
    
    @pytest.mark.asyncio
    async def test_flash_loan_simulation(self, session, base_url):
        """Test flash loan simulation without actual execution."""
        url = f"{base_url}/flash-loan/simulate"
        
        payload = {
            "token_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",  # WETH
            "amount": "1000000000000000000",  # 1 ETH
            "strategy": "simple_arbitrage",
            "dex_route": ["uniswap", "sushiswap"]
        }
        
        async with session.post(url, json=payload) as response:
            assert response.status == 200
            data = await response.json()
            
            assert "simulation_result" in data
            assert "estimated_profit" in data
            assert "gas_estimate" in data
            assert "risk_score" in data
    
    @pytest.mark.asyncio
    async def test_risk_manager_integration(self, session, base_url):
        """Test risk manager integration and thresholds."""
        url = f"{base_url}/risk-manager/assess"
        
        payload = {
            "transaction_type": "flash_loan",
            "amount": "10000000000000000000",  # 10 ETH
            "token_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "strategy": "triangular_arbitrage"
        }
        
        async with session.post(url, json=payload) as response:
            assert response.status == 200
            data = await response.json()
            
            assert "risk_score" in data
            assert "risk_factors" in data
            assert "recommendation" in data
            
            # Risk score should be between 0 and 10
            assert 0 <= data["risk_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_blockchain_monitoring_integration(self, session, base_url):
        """Test blockchain monitoring and mempool analysis."""
        url = f"{base_url}/blockchain/mempool"
        
        async with session.get(url) as response:
            assert response.status == 200
            data = await response.json()
            
            assert "pending_transactions" in data
            assert "gas_prices" in data
            assert "network_congestion" in data
    
    @pytest.mark.asyncio
    async def test_coordination_between_services(self, session, base_url):
        """Test coordination between different MCP services."""
        # Step 1: Get arbitrage opportunities
        opportunities_url = f"{base_url}/arbitrage/opportunities"
        async with session.get(opportunities_url) as response:
            opportunities = await response.json()
        
        if not opportunities.get("opportunities"):
            pytest.skip("No arbitrage opportunities available for testing")
        
        opportunity = opportunities["opportunities"][0]
        
        # Step 2: Assess risk for the opportunity
        risk_url = f"{base_url}/risk-manager/assess"
        risk_payload = {
            "transaction_type": "flash_loan",
            "amount": opportunity.get("amount", "1000000000000000000"),
            "token_address": opportunity.get("token_address", "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"),
            "strategy": "arbitrage"
        }
        
        async with session.post(risk_url, json=risk_payload) as response:
            risk_assessment = await response.json()
        
        # Step 3: If risk is acceptable, simulate the flash loan
        if risk_assessment.get("risk_score", 10) <= 7:  # Risk threshold
            simulation_url = f"{base_url}/flash-loan/simulate"
            simulation_payload = {
                "token_address": opportunity.get("token_address"),
                "amount": opportunity.get("amount"),
                "dex_route": opportunity.get("dex_route", ["uniswap", "sushiswap"])
            }
            
            async with session.post(simulation_url, json=simulation_payload) as response:
                simulation = await response.json()
                
                assert "simulation_result" in simulation
                assert simulation["simulation_result"]["success"] is not None
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, session, base_url):
        """Test system performance under concurrent requests."""
        urls = [
            f"{base_url}/price-feed/prices",
            f"{base_url}/arbitrage/opportunities", 
            f"{base_url}/blockchain/mempool",
            f"{base_url}/risk-manager/health"
        ]
        
        start_time = time.time()
        
        # Make 10 concurrent requests to each endpoint
        tasks = []
        for _ in range(10):
            for url in urls:
                task = asyncio.create_task(session.get(url))
                tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check that most requests succeeded
        successful_responses = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
        total_requests = len(tasks)
        
        success_rate = successful_responses / total_requests
        assert success_rate >= 0.9, f"Success rate {success_rate} below threshold"
        
        # Check performance (should complete within reasonable time)
        assert duration < 30, f"Performance test took too long: {duration}s"
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, session, base_url):
        """Test system error recovery and graceful degradation."""
        # Test with invalid token address
        invalid_simulation_url = f"{base_url}/flash-loan/simulate"
        invalid_payload = {
            "token_address": "0xinvalid",
            "amount": "1000000000000000000"
        }
        
        async with session.post(invalid_simulation_url, json=invalid_payload) as response:
            # Should handle error gracefully
            assert response.status in [400, 422]  # Bad request or validation error
            data = await response.json()
            assert "error" in data or "message" in data
    
    @pytest.mark.asyncio
    async def test_data_consistency(self, session, base_url):
        """Test data consistency across different services."""
        # Get prices from price feed
        price_url = f"{base_url}/price-feed/prices"
        async with session.get(price_url) as response:
            price_data = await response.json()
        
        # Get arbitrage opportunities
        arb_url = f"{base_url}/arbitrage/opportunities"
        async with session.get(arb_url) as response:
            arb_data = await response.json()
        
        # Verify that arbitrage calculations are based on current prices
        if price_data.get("prices") and arb_data.get("opportunities"):
            price_timestamp = price_data.get("timestamp")
            arb_timestamp = arb_data.get("timestamp")
            
            # Timestamps should be close (within 1 minute)
            if price_timestamp and arb_timestamp:
                time_diff = abs(float(price_timestamp) - float(arb_timestamp))
                assert time_diff < 60, "Price and arbitrage data timestamps too far apart"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
