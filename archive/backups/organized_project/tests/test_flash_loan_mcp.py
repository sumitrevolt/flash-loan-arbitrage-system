#!/usr/bin/env python3
"""
Flash Loan MCP Server Tests
Unit tests for flash loan functionality
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from mcp_servers.mcp_flash_loan_server import FlashLoanMCPServer

class TestFlashLoanMCPServer:
    
    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        return FlashLoanMCPServer()
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server.server.name == "flash-loan-mcp"
        assert hasattr(server, 'web3')
        assert hasattr(server, 'flash_loan_contract')
    
    @pytest.mark.asyncio
    async def test_list_resources(self, server):
        """Test resource listing."""
        resources = await server.server.list_resources()
        assert len(resources) > 0
        
        resource_names = [r.name for r in resources]
        assert "Flash Loan Pools" in resource_names
        assert "Arbitrage Opportunities" in resource_names
    
    @pytest.mark.asyncio
    async def test_flash_loan_execution_tool(self, server):
        """Test flash loan execution tool."""
        arguments = {
            "token_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "amount": "1000000000000000000",  # 1 ETH
            "dex_route": ["uniswap", "sushiswap"]
        }
        
        with patch.object(server, 'execute_flash_loan', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0x123...",
                "profit": "0.01",
                "gas_used": 150000
            }
            
            result = await server.execute_flash_loan_tool(arguments)
            
            assert result["success"] is True
            assert "transaction_hash" in result
            assert "profit" in result
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_arbitrage_opportunity(self, server):
        """Test arbitrage opportunity calculation."""
        arguments = {
            "token_pair": "ETH/USDC",
            "amount": "1000000000000000000"
        }
        
        with patch.object(server, 'get_dex_prices', new_callable=AsyncMock) as mock_prices:
            mock_prices.return_value = {
                "uniswap": 2500.50,
                "sushiswap": 2503.75,
                "quickswap": 2499.25
            }
            
            result = await server.calculate_arbitrage_opportunity_tool(arguments)
            
            assert "opportunity" in result
            assert "profit_potential" in result
            assert "optimal_route" in result
    
    @pytest.mark.asyncio
    async def test_risk_assessment(self, server):
        """Test risk assessment functionality."""
        arguments = {
            "token_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "amount": "1000000000000000000",
            "strategy": "triangular_arbitrage"
        }
        
        result = await server.assess_risks_tool(arguments)
        
        assert "risk_score" in result
        assert "risk_factors" in result
        assert result["risk_score"] >= 0 and result["risk_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_gas_estimation(self, server):
        """Test gas price estimation."""
        arguments = {
            "transaction_type": "flash_loan",
            "complexity": "high"
        }
        
        with patch.object(server, 'get_current_gas_prices', new_callable=AsyncMock) as mock_gas:
            mock_gas.return_value = {
                "slow": 20,
                "standard": 25,
                "fast": 35,
                "instant": 50
            }
            
            result = await server.estimate_gas_costs_tool(arguments)
            
            assert "estimated_gas" in result
            assert "gas_price_options" in result
            assert "total_cost_eth" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, server):
        """Test error handling in tools."""
        arguments = {
            "token_address": "invalid_address",
            "amount": "0"
        }
        
        result = await server.execute_flash_loan_tool(arguments)
        
        assert "error" in result or result["success"] is False
    
    def test_validation_functions(self, server):
        """Test input validation functions."""
        # Test valid Ethereum address
        assert server.is_valid_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619") is True
        
        # Test invalid address
        assert server.is_valid_address("invalid_address") is False
        
        # Test amount validation
        assert server.is_valid_amount("1000000000000000000") is True
        assert server.is_valid_amount("0") is False
        assert server.is_valid_amount("-1") is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
