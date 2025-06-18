#!/usr/bin/env python3
"""
Configure Flash Loan Bot with Real-Time Data and Monitoring
Coordinates all MCP servers for optimal flash loan execution
Uses existing configuration files and provides comprehensive agent settings
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flash_loan_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FlashLoanSystemConfigurator:
    def __init__(self):
        # Configuration file paths
        self.config_dir = Path(__file__).parent
        self.unified_config_path = self.config_dir / "unified_mcp_config.json"
        self.arbitrage_config_path = self.config_dir / "arbitrage_config.json" 
        self.wallet_config_path = self.config_dir / "wallet_config.json"
        
        # Load configurations from existing files
        self.unified_config = self.load_config(self.unified_config_path)
        self.arbitrage_config = self.load_config(self.arbitrage_config_path)
        self.wallet_config = self.load_config(self.wallet_config_path)
        
        # MCP Server configuration based on existing setup
        self.mcp_servers: Dict[str, Dict[str, Any]] = {
            'flash_loan': {
                'host': 'localhost', 
                'port': 8000, 
                'status': 'unknown',
                'name': 'Unified Flash Loan MCP Server'
            },
            'taskmanager': {
                'host': 'localhost', 
                'port': 8001, 
                'status': 'unknown',
                'name': 'TaskManager MCP Server'
            },
            'foundry': {
                'host': 'localhost', 
                'port': 8002, 
                'status': 'unknown',
                'name': 'Enhanced Foundry MCP Server'
            }
        }
        
        # Agent settings
        self.agent_settings: Dict[str, Any] = {
            'trading_enabled': True,
            'monitoring_enabled': True,
            'auto_execute_trades': False,  # Safety first
            'risk_management': {
                'max_daily_trades': 50,
                'max_loss_threshold': 0.02,  # 2% max loss
                'cooldown_period': 300  # 5 minutes between trades
            },
            'notifications': {
                'successful_trades': True,
                'failed_trades': True,
                'profit_alerts': True,
                'system_status': True
            }
        }
        
        self.monitoring_active = False
        self.real_time_data: Dict[str, Any] = {}
        self.successful_trades: List[Dict[str, Any]] = []
        self.failed_trades: List[Dict[str, Any]] = []
        self.daily_profit = 0.0
        self.trades_today = 0
        self.last_trade_time: Optional[datetime] = None

    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from existing JSON files"""
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"✅ Loaded configuration from {config_path.name}")
                return config
            else:
                logger.warning(f"⚠️ Configuration file not found: {config_path}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error loading config from {config_path}: {e}")
            return {}

    def save_agent_settings(self) -> bool:
        """Save agent settings to a configuration file"""
        try:
            settings_path = self.config_dir / "agent_settings.json"
            with open(settings_path, 'w') as f:
                json.dump(self.agent_settings, f, indent=2)
            logger.info(f"✅ Agent settings saved to {settings_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving agent settings: {e}")
            return False

    def update_agent_setting(self, key: str, value: Any) -> bool:
        """Update a specific agent setting"""
        try:
            keys = key.split('.')
            current = self.agent_settings
            
            # Navigate to the correct nested level
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Set the value
            current[keys[-1]] = value
            self.save_agent_settings()
            logger.info(f"✅ Updated agent setting {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating agent setting {key}: {e}")
            return False

    async def check_server_health(self, server_name: str, host: str, port: int) -> bool:
        """Check if MCP server is healthy and responding"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f'http://{host}:{port}/health') as response:
                    if response.status == 200:
                        self.mcp_servers[server_name]['status'] = 'healthy'
                        logger.info(f"✅ {server_name} MCP server is healthy on port {port}")
                        return True
                    else:
                        self.mcp_servers[server_name]['status'] = 'unhealthy'
                        logger.warning(f"⚠️ {server_name} MCP server responded with status {response.status}")
                        return False
        except Exception as e:
            self.mcp_servers[server_name]['status'] = 'offline'
            logger.error(f"❌ {server_name} MCP server is offline: {e}")
            return False

    async def configure_flash_loan_server(self) -> bool:
        """Configure Flash Loan MCP server using existing configuration files"""
        try:
            # Use existing arbitrage configuration
            from typing import Any, Dict
            arbitrage_config: Dict[str, Any] = self.arbitrage_config.get('flash_loan_arbitrage', {})
            config_data: Dict[str, Any] = {
                "mode": "production",
                "real_time_monitoring": True,
                "arbitrage_settings": {
                    "min_profit_threshold": arbitrage_config.get('min_profit_usd', 2.0),
                    "max_gas_price": self.wallet_config.get('max_gas_price_gwei', 200),
                    "slippage_tolerance": arbitrage_config.get('slippage_tolerance', 0.025),
                    "execution_timeout": self.wallet_config.get('transaction_timeout', 300),
                    "max_trade_size": arbitrage_config.get('max_trade_size_usd', 1100.0)
                },
                "networks": list(self.unified_config.get('networks', {}).keys()),
                "dex_integration": self.arbitrage_config.get('dexes', {}),
                "monitoring": {
                    "trade_tracking": True,
                    "profit_reporting": True,
                    "gas_optimization": True,
                    "real_time_alerts": True,
                    "scan_interval": arbitrage_config.get('scan_interval_seconds', 2)
                },
                "tokens": self.arbitrage_config.get('tokens', {}),
                "wallet": {
                    "address": self.wallet_config.get('wallet_address'),
                    "network": self.wallet_config.get('network', 'polygon'),
                    "gas_limit": self.wallet_config.get('gas_limit', 500000)
                }
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f'http://localhost:8000/configure',
                    json=config_data
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Flash Loan MCP server configured successfully with existing settings")
                        return True
                    else:
                        logger.error(f"❌ Failed to configure Flash Loan server: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error configuring Flash Loan server: {e}")
            return False

    async def configure_foundry_server(self) -> bool:
        """Configure Foundry MCP server using existing configuration"""
        try:
            from typing import Any, Dict
            foundry_config: Dict[str, Any] = self.unified_config.get('foundry', {})
            config_data: Dict[str, Any] = {
                "compilation": {
                    "optimizer": True,
                    "optimizer_runs": 200,
                    "solidity_version": "0.8.19"
                },
                "testing": {
                    "fork_networks": list(self.unified_config.get('networks', {}).keys()),
                    "gas_reporting": True,
                    "coverage": True,
                    "timeout": foundry_config.get('test_timeout', 120)
                },
                "deployment": {
                    "verify_contracts": True,
                    "gas_estimation": True
                },
                "anvil": {
                    "port_range": foundry_config.get('anvil_port_range', [8545, 8560]),
                    "enabled": foundry_config.get('enabled', True)
                }
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f'http://localhost:8002/configure',
                    json=config_data
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Foundry MCP server configured successfully with existing settings")
                        return True
                    else:
                        logger.error(f"❌ Failed to configure Foundry server: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error configuring Foundry server: {e}")
            return False

    async def start_real_time_monitoring(self):
        """Start real-time monitoring of blockchain data and trade execution"""
        logger.info("🔄 Starting real-time monitoring system...")
        self.monitoring_active = True
        
        # Start multiple monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_blockchain_data()),
            asyncio.create_task(self.monitor_dex_prices()),
            asyncio.create_task(self.monitor_gas_prices()),
            asyncio.create_task(self.monitor_trade_execution()),
            asyncio.create_task(self.display_live_dashboard())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            self.monitoring_active = False

    async def monitor_blockchain_data(self):
        """Monitor real-time blockchain data"""
        while self.monitoring_active:
            try:
                # Get latest block data
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get('http://localhost:8000/blockchain/latest') as response:
                        if response.status == 200:
                            data = await response.json()
                            self.real_time_data['blockchain'] = data
                            
                await asyncio.sleep(2)  # Update every 2 seconds
            except Exception as e:
                logger.error(f"Error monitoring blockchain data: {e}")
                await asyncio.sleep(5)

    async def monitor_dex_prices(self):
        """Monitor DEX prices for arbitrage opportunities"""
        while self.monitoring_active:
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get('http://localhost:8000/dex/prices') as response:
                        if response.status == 200:
                            data = await response.json()
                            self.real_time_data['dex_prices'] = data
                            
                            # Check for arbitrage opportunities
                            opportunities = await self.detect_arbitrage_opportunities(data)
                            if opportunities:
                                logger.info(f"🎯 Arbitrage opportunities detected: {len(opportunities)}")
                                
                await asyncio.sleep(1)  # Update every second
            except Exception as e:
                logger.error(f"Error monitoring DEX prices: {e}")
                await asyncio.sleep(3)

    async def monitor_gas_prices(self):
        """Monitor gas prices across networks"""
        while self.monitoring_active:
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get('http://localhost:8000/gas/prices') as response:
                        if response.status == 200:
                            data = await response.json()
                            self.real_time_data['gas_prices'] = data
                            
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error monitoring gas prices: {e}")
                await asyncio.sleep(10)

    async def monitor_trade_execution(self):
        """Monitor successful trade executions"""
        while self.monitoring_active:
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get('http://localhost:8000/trades/recent') as response:
                        if response.status == 200:
                            trades = await response.json()
                            for trade in trades:
                                if trade.get('status') == 'success' and trade not in self.successful_trades:
                                    self.successful_trades.append(trade)
                                    self.daily_profit += float(trade.get('profit', 0))
                                    self.trades_today += 1
                                    self.last_trade_time = datetime.now()
                                    
                                    logger.info(f"💰 Successful trade executed: "
                                              f"Profit: ${trade.get('profit', 'N/A')} "
                                              f"Gas: {trade.get('gas_used', 'N/A')} "
                                              f"TxHash: {trade.get('tx_hash', 'N/A')}")
                                    
                                    # Send notification if enabled
                                    if self.agent_settings['notifications']['successful_trades']:
                                        await self.send_trade_notification(trade, 'success')
                                        
                                elif trade.get('status') == 'failed' and trade not in self.failed_trades:
                                    self.failed_trades.append(trade)
                                    logger.warning(f"⚠️ Failed trade: {trade.get('error', 'Unknown error')}")
                                    
                                    if self.agent_settings['notifications']['failed_trades']:
                                        await self.send_trade_notification(trade, 'failed')
                            
                await asyncio.sleep(3)  # Update every 3 seconds
            except Exception as e:
                logger.error(f"Error monitoring trades: {e}")
                await asyncio.sleep(5)

    async def send_trade_notification(self, trade: Dict[str, Any], trade_type: str):
        """Send trade notification (can be extended for external notifications)"""
        try:
            message = f"Trade {trade_type.upper()}: "
            if trade_type == 'success':
                message += f"Profit: ${trade.get('profit', 'N/A')}, Gas: {trade.get('gas_used', 'N/A')}"
            else:
                message += f"Error: {trade.get('error', 'Unknown error')}"
            
            # For now, just log - can be extended to email, Slack, etc.
            logger.info(f"📢 NOTIFICATION: {message}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    async def detect_arbitrage_opportunities(self, price_data: Dict[str, Any]) -> list[dict[str, float | str]]:
        """Detect arbitrage opportunities from price data"""
        from typing import Any, Dict, cast
        opportunities: list[dict[str, float | str]] = []

        # Simple arbitrage detection logic
        tokens_dict: Dict[str, Any] = cast(Dict[str, Any], price_data.get('tokens', {}))
        for token_key, exchanges_val in tokens_dict.items():
            token: str = str(token_key)
            exchanges: Dict[str, Any] = cast(Dict[str, Any], exchanges_val)
            # exchanges is always a dict here
            if len(exchanges) >= 2:
                try:
                    prices: list[float] = [float(cast(Dict[str, Any], ex).get('price', 0)) for ex in exchanges.values() if isinstance(ex, dict)]
                    if len(prices) >= 2:
                        min_price: float = min(prices)
                        max_price: float = max(prices)

                        if min_price > 0 and (max_price - min_price) / min_price > 0.005:  # 0.5% threshold
                            opportunities.append({
                                'token': token,
                                'min_price': min_price,
                                'max_price': max_price,
                                'profit_potential': (max_price - min_price) / min_price,
                                'timestamp': datetime.now().isoformat()
                            })
                except (ValueError, TypeError, KeyError) as e:
                    logger.debug(f"Error processing token {token}: {e}")

        return opportunities

    async def display_live_dashboard(self) -> None:
        """Display live dashboard in terminal"""
        while self.monitoring_active:
            try:
                # Clear screen and display dashboard
                print("\033[2J\033[H")  # Clear screen
                print("=" * 80)
                print("🚀 FLASH LOAN BOT - REAL-TIME MONITORING DASHBOARD")
                print("=" * 80)
                print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()

                # Agent Settings Summary
                print("⚙️  AGENT SETTINGS:")
                print(f"  Trading: {'✅ ENABLED' if self.agent_settings['trading_enabled'] else '❌ DISABLED'}")
                print(f"  Auto-Execute: {'✅ ON' if self.agent_settings['auto_execute_trades'] else '❌ OFF'}")
                print(f"  Daily Trades Limit: {self.agent_settings['risk_management']['max_daily_trades']}")
                print(f"  Today's Trades: {self.trades_today}")
                print(f"  Daily Profit: ${self.daily_profit:.4f}")
                print()

                # MCP Server Status
                print("🔧 MCP SERVER STATUS:")
                for name, server in self.mcp_servers.items():
                    status_emoji = "✅" if server['status'] == 'healthy' else "❌"
                    print(f"  {status_emoji} {name.upper()}: {server['status']} (Port {server['port']})")
                print()

                # Configuration Status
                print("📋 CONFIGURATION STATUS:")
                print(f"  Unified Config: {'✅' if self.unified_config else '❌'} Loaded")
                print(f"  Arbitrage Config: {'✅' if self.arbitrage_config else '❌'} Loaded")
                print(f"  Wallet Config: {'✅' if self.wallet_config else '❌'} Loaded")
                print()

                # Real-time Data
                if 'blockchain' in self.real_time_data:
                    blockchain = self.real_time_data['blockchain']
                    print(f"⛓️  BLOCKCHAIN STATUS:")
                    print(f"  Block Number: {blockchain.get('block_number', 'N/A')}")
                    print(f"  Gas Price: {blockchain.get('gas_price', 'N/A')} gwei")
                    print()

                if 'dex_prices' in self.real_time_data:
                    from typing import Any, Dict, cast
                    dex_data: Any = self.real_time_data['dex_prices']
                    tokens_dict: Dict[str, Any] = {}
                    if isinstance(dex_data, dict):
                        dex_data_dict: Dict[str, Any] = cast(Dict[str, Any], dex_data)
                        tokens_dict = dex_data_dict.get('tokens', {})
                    token_count: int = len(tokens_dict)
                    print(f"💱 DEX MONITORING: {token_count} tokens tracked")
                    print()

                # Successful Trades
                print(f"💰 TRADING SUMMARY:")
                print(f"  Successful Trades: {len(self.successful_trades)} total")
                print(f"  Failed Trades: {len(self.failed_trades)} total")
                if self.successful_trades:
                    recent_trades = self.successful_trades[-3:]  # Show last 3 trades
                    print("  Recent Successful Trades:")
                    for trade in recent_trades:
                        profit = trade.get('profit', 'N/A')
                        gas = trade.get('gas_used', 'N/A')
                        print(f"    • Profit: ${profit} | Gas: {gas}")
                print()

                print("Press Ctrl+C to stop monitoring...")
                print("=" * 80)

                await asyncio.sleep(2)  # Update dashboard every 2 seconds

            except Exception as e:
                logger.error(f"Error in dashboard: {e}")
                await asyncio.sleep(5)

    async def execute_trade_command(self, trade_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a flash loan trade through the MCP system"""
        try:
            # Check if trading is enabled
            if not self.agent_settings['trading_enabled']:
                return {'success': False, 'error': 'Trading is disabled in agent settings'}
            
            # Check daily trade limits
            if self.trades_today >= self.agent_settings['risk_management']['max_daily_trades']:
                return {'success': False, 'error': 'Daily trade limit reached'}
            
            # Check cooldown period
            if (self.last_trade_time and 
                (datetime.now() - self.last_trade_time).seconds < self.agent_settings['risk_management']['cooldown_period']):
                return {'success': False, 'error': 'Cooldown period active'}
            
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    'http://localhost:8000/execute/flashloan',
                    json=trade_params
                ) as response:
                    result: str = await response.json()
                    
                    if response.status == 200 and result.get('success'):
                        logger.info(f"✅ Trade executed successfully: {result.get('tx_hash')}")
                        return result
                    else:
                        logger.error(f"❌ Trade execution failed: {result.get('error')}")
                        return result
                        
        except Exception as e:
            logger.error(f"❌ Error executing trade: {e}")
            return {'success': False, 'error': str(e)}

    async def run_configuration(self):
        """Main configuration and monitoring loop"""
        logger.info("🚀 Starting Flash Loan Bot Configuration...")
        
        # Step 1: Load and validate configurations
        logger.info("📋 Loading existing configuration files...")
        if not self.unified_config:
            logger.warning("⚠️ Unified MCP config not found - using defaults")
        if not self.arbitrage_config:
            logger.warning("⚠️ Arbitrage config not found - using defaults")
        if not self.wallet_config:
            logger.warning("⚠️ Wallet config not found - using defaults")
        
        # Step 2: Save initial agent settings
        self.save_agent_settings()
        
        # Step 3: Check all MCP server health
        logger.info("📊 Checking MCP server health...")
        health_tasks = [
            self.check_server_health(name, server['host'], server['port'])
            for name, server in self.mcp_servers.items()
        ]
        health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        healthy_servers = sum(1 for result in health_results if result is True)
        logger.info(f"✅ {healthy_servers}/{len(self.mcp_servers)} MCP servers are healthy")
        
        # Step 4: Configure servers with existing configurations
        if self.mcp_servers['flash_loan']['status'] == 'healthy':
            await self.configure_flash_loan_server()
        
        if self.mcp_servers['foundry']['status'] == 'healthy':
            await self.configure_foundry_server()
        
        # Step 5: Start real-time monitoring
        logger.info("🔄 Starting real-time monitoring and trade execution system...")
        await self.start_real_time_monitoring()

async def main():
    """Main entry point"""
    configurator = FlashLoanSystemConfigurator()
    
    try:
        await configurator.run_configuration()
    except KeyboardInterrupt:
        logger.info("🛑 System stopped by user")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
    finally:
        logger.info("🔚 Flash Loan Bot Configuration completed")

if __name__ == "__main__":
    print("🚀 Flash Loan Bot System Configurator")
    print("=" * 50)
    print("📋 Using existing configuration files:")
    print("   • unified_mcp_config.json")
    print("   • arbitrage_config.json") 
    print("   • wallet_config.json")
    print("⚙️ Creating agent_settings.json for bot configuration")
    print("=" * 50)
    asyncio.run(main())
