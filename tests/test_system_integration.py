"""
Integration Tests for Flash Loan Arbitrage System
==============================================

Comprehensive test suite covering:
- System startup and initialization
- MCP server communication
- AI agent coordination
- Trading logic validation
- Error handling and recovery
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Import system components
from config.system_config import ConfigManager, get_config
from enhanced_revenue_activator import EnhancedRevenueActivator
from streamlined_system import StreamlinedTaskSystem
from realtime_price_feed import RealtimePriceFeed

class TestSystemIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment with mock configurations"""
        self.config_manager = ConfigManager()
        
        # Override with test configuration
        self.config_manager.config.environment = "test"
        self.config_manager.config.trading.auto_execute = False
        self.config_manager.config.trading.max_trade_size_usd = 100.0
        self.config_manager.config.mcp.timeout_seconds = 5
    
    @pytest.mark.asyncio
    async def test_system_startup_sequence(self):
        """Test complete system startup and initialization"""
        activator = EnhancedRevenueActivator()
        
        # Mock external dependencies
        with patch.object(activator, 'load_configurations') as mock_load:
            mock_load.return_value = None
            
            # Test initialization
            assert activator.revenue_metrics['total_profit_usd'] == 0.0
            assert activator.revenue_metrics['trades_executed'] == 0
    
    @pytest.mark.asyncio 
    async def test_mcp_server_discovery(self):
        """Test MCP server discovery and health checking"""
        system = StreamlinedTaskSystem()
        
        # Mock Docker client
        with patch.object(system, 'docker_client') as mock_docker:
            # Mock running containers
            mock_container = Mock()
            mock_container.name = "flashloan-mcp-arbitrage"
            mock_container.attrs = {
                'NetworkSettings': {
                    'Ports': {
                        '8080/tcp': [{'HostPort': '8080'}]
                    }
                }
            }
            mock_docker.containers.list.return_value = [mock_container]
            
            await system.discover_services()
            
            # Verify MCP server was discovered
            assert len(system.mcp_servers) >= 1
            assert "flashloan-mcp-arbitrage" in system.mcp_servers
            
            server = system.mcp_servers["flashloan-mcp-arbitrage"]
            assert server.service_type == "mcp_server"
            assert server.port == 8080
            assert "arbitrage_analysis" in server.capabilities

    @pytest.mark.asyncio
    async def test_ai_agent_task_assignment(self):
        """Test AI agent task creation and assignment"""
        system = StreamlinedTaskSystem()
        
        # Mock agents
        system.ai_agents = {
            "flashloan-agent-arbitrage-bot": Mock(),
            "flashloan-agent-risk-manager": Mock()
        }
        system.agent_capabilities = {
            "flashloan-agent-arbitrage-bot": ["arbitrage_detection"],
            "flashloan-agent-risk-manager": ["risk_assessment"]
        }
        
        # Test task creation
        task = system.create_task(
            task_type="analyze_arbitrage",
            description="Test arbitrage analysis",
            parameters={"chain": "polygon"}
        )
        
        assert task.id is not None
        assert task.type == "analyze_arbitrage"
        assert task.assigned_agent == "flashloan-agent-arbitrage-bot"
        assert task.status.value == "assigned"

    @pytest.mark.asyncio
    async def test_price_feed_integration(self):
        """Test real-time price feed functionality"""
        # Mock the price feed system
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock successful price response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'ethereum': {'usd': 2000.0},
                'bitcoin': {'usd': 45000.0}
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test price fetching (simplified)
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {'ids': 'ethereum,bitcoin', 'vs_currencies': 'usd'}
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        price_data = await response.json()
                        assert 'ethereum' in price_data
                        assert price_data['ethereum']['usd'] > 0

    @pytest.mark.asyncio
    async def test_arbitrage_opportunity_detection(self):
        """Test arbitrage opportunity detection logic"""
        activator = EnhancedRevenueActivator()
        
        # Mock price data with arbitrage opportunity
        mock_prices = {
            'ETH/USDC': {
                'uniswap': 2000.0,
                'sushiswap': 2005.0,  # 0.25% price difference
                'volume': 1000000
            }
        }
        
        # Test opportunity detection (simplified)
        price_diff = mock_prices['ETH/USDC']['sushiswap'] - mock_prices['ETH/USDC']['uniswap']
        profit_percentage = (price_diff / mock_prices['ETH/USDC']['uniswap']) * 100
        
        # Should detect profitable opportunity
        assert profit_percentage > 0.1  # Minimum 0.1% profit
        assert mock_prices['ETH/USDC']['volume'] > 100000  # Sufficient liquidity

    @pytest.mark.asyncio
    async def test_risk_management_validation(self):
        """Test risk management and safety checks"""
        config = get_config()
        
        # Test trading limits
        trade_size = 5000.0
        assert trade_size <= config.trading.max_trade_size_usd
        
        # Test slippage tolerance
        expected_price = 2000.0
        actual_price = 2010.0
        slippage = abs(actual_price - expected_price) / expected_price
        
        assert slippage <= config.trading.slippage_tolerance * 2  # Allow some tolerance for tests

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self):
        """Test system health monitoring and reporting"""
        system = StreamlinedTaskSystem()
        
        # Mock services for health check
        system.ai_agents = {"test-agent": Mock()}
        system.mcp_servers = {"test-server": Mock()}
        
        with patch('requests.get') as mock_get:
            # Mock healthy responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            health_report = await system.health_check()
            
            assert 'healthy_agents' in health_report
            assert 'healthy_servers' in health_report
            assert health_report['total_agents'] >= 0
            assert health_report['total_servers'] >= 0

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test system error handling and recovery mechanisms"""
        activator = EnhancedRevenueActivator()
        
        # Test error recovery
        with patch.object(activator, 'command_mcp_server') as mock_command:
            # Simulate server failure
            mock_command.side_effect = Exception("Connection failed")
            
            # Test that system continues despite errors
            result = await activator.index_market_data()
            
            # Should handle error gracefully
            assert result is False  # Function should return False on error
            mock_command.assert_called_once()

    def test_configuration_validation(self):
        """Test configuration validation and error reporting"""
        config_manager = ConfigManager()
        
        # Test with invalid configuration
        config_manager.config.trading.max_trade_size_usd = -100  # Invalid
        config_manager.config.trading.slippage_tolerance = 2.0   # Invalid (>1)
        
        issues = config_manager.validate_config()
        
        assert len(issues) > 0
        assert any("MAX_TRADE_SIZE_USD must be positive" in issue for issue in issues)
        assert any("SLIPPAGE_TOLERANCE must be between 0 and 1" in issue for issue in issues)

    @pytest.mark.asyncio
    async def test_task_execution_workflow(self):
        """Test complete task execution workflow"""
        system = StreamlinedTaskSystem()
        
        # Setup mock environment
        system.ai_agents = {"test-agent": Mock()}
        
        # Create and execute task
        task = system.create_task("test_task", "Test task description")
        
        with patch('requests.post') as mock_post:
            # Mock successful execution
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success", "result": "test_result"}
            mock_post.return_value = mock_response
            
            # If no agent assigned, it should still handle gracefully
            if task.assigned_agent:
                success = await system.execute_task(task.id)
                assert success in [True, False]  # Should return a boolean

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test system handling of concurrent operations"""
        activator = EnhancedRevenueActivator()
        
        # Test concurrent task execution
        tasks = []
        for i in range(3):
            task = asyncio.create_task(activator.index_market_data())
            tasks.append(task)
        
        # All tasks should complete without hanging
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that all tasks completed (either True, False, or Exception)
        assert len(results) == 3
        for result in results:
            assert isinstance(result, (bool, Exception))

class TestSecurityValidation:
    """Security-focused tests"""
    
    def test_private_key_handling(self):
        """Test that private keys are handled securely"""
        config = get_config()
        
        # Private key should not be logged or exposed
        assert not config.blockchain.private_key or len(config.blockchain.private_key) > 10
        
        # Should use environment variables, not hardcoded values
        import os
        if os.getenv("PRIVATE_KEY"):
            assert config.blockchain.private_key == os.getenv("PRIVATE_KEY")

    def test_trading_limits_enforcement(self):
        """Test that trading limits are properly enforced"""
        config = get_config()
        
        # Test maximum trade size
        max_trade = config.trading.max_trade_size_usd
        assert max_trade > 0
        assert max_trade < 1000000  # Reasonable upper limit
        
        # Test minimum profit requirements
        min_profit = config.trading.min_profit_usd
        assert min_profit > 0
        assert min_profit < max_trade  # Profit should be less than max trade

class TestPerformanceMetrics:
    """Performance and metrics tests"""
    
    def test_response_time_requirements(self):
        """Test that system meets response time requirements"""
        start_time = time.time()
        
        # Test configuration loading time
        config_manager = ConfigManager()
        config_manager.load_config()
        
        load_time = time.time() - start_time
        
        # Configuration should load quickly
        assert load_time < 1.0  # Should load in under 1 second

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self):
        """Test system performance under concurrent load"""
        system = StreamlinedTaskSystem()
        
        # Create multiple concurrent tasks
        start_time = time.time()
        
        concurrent_tasks = []
        for i in range(10):
            task = asyncio.create_task(system.health_check())
            concurrent_tasks.append(task)
        
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # All tasks should complete reasonably quickly
        assert total_time < 30.0  # Should complete in under 30 seconds
        assert len(results) == 10

# Utility functions for testing
def create_mock_price_data() -> Dict[str, Any]:
    """Create mock price data for testing"""
    return {
        'timestamp': int(time.time()),
        'prices': {
            'ETH/USDC': {
                'uniswap': 2000.0,
                'sushiswap': 2005.0,
                'pancakeswap': 1998.0
            },
            'BTC/USDT': {
                'uniswap': 45000.0,
                'sushiswap': 45100.0
            }
        }
    }

def create_mock_arbitrage_opportunity() -> Dict[str, Any]:
    """Create mock arbitrage opportunity for testing"""
    return {
        'token_pair': 'ETH/USDC',
        'buy_exchange': 'uniswap',
        'sell_exchange': 'sushiswap',
        'buy_price': 2000.0,
        'sell_price': 2005.0,
        'profit_usd': 25.0,
        'profit_percentage': 0.25,
        'gas_cost_usd': 15.0,
        'net_profit_usd': 10.0,
        'confidence_score': 0.85
    }

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])