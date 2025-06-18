#!/usr/bin/env python3
"""
Unified MCP Coordinator for Flash Loan Arbitrage
Complete coordination of all MCP servers with real-time automation
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
import subprocess
import signal
import platform
import socket
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable, Tuple, cast
from dataclasses import dataclass, asdict, field
from decimal import Decimal
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from types import FrameType

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging first
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mcp_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Windows-specific asyncio event loop fix for aiodns compatibility
if platform.system() == 'Windows':
    try:
        # Set the event loop policy to WindowsProactorEventLoopPolicy to avoid aiodns issues
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info("Set Windows ProactorEventLoopPolicy for aiodns compatibility")
    except AttributeError:
        # Fallback for older Python versions
        try:
            import asyncio.windows_events
            asyncio.set_event_loop_policy(asyncio.windows_events.WindowsProactorEventLoopPolicy())
            logger.info("Set Windows ProactorEventLoopPolicy (fallback)")
        except ImportError:
            logger.warning("Unable to set Windows event loop policy, may encounter aiodns issues")

@dataclass
class MCPServerInfo:
    """Information about an MCP server"""
    name: str
    type: str  # 'python' or 'typescript'
    path: str
    port: int
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    process: Optional[subprocess.Popen[bytes]] = None
    health_status: str = "unknown"
    last_health_check: Optional[datetime] = None
    start_time: Optional[datetime] = None
    restart_count: int = 0

@dataclass
class FlashLoanOpportunity:
    """Flash loan arbitrage opportunity"""
    token_symbol: str
    token_address: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    profit_usd: float
    profit_percentage: float
    gas_cost_usd: float
    net_profit_usd: float
    liquidity_available: float
    max_trade_size: float
    timestamp: datetime
    confidence_score: float
    risk_level: str

@dataclass
class ArbitrageTask:
    """Enhanced task for arbitrage execution coordination"""
    task_id: str
    token_pair: str
    buy_dex: str
    sell_dex: str
    expected_profit: Decimal
    priority: str  # 'low', 'normal', 'high', 'critical'
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    mcp_responses: Dict[str, Any] = field(default_factory=lambda: {})
    execution_time_ms: float = 0.0
    gas_used: int = 0
    actual_profit: Decimal = Decimal('0')

@dataclass
class MCPServerStatus:
    """Enhanced status information for MCP servers"""
    name: str
    endpoint: str
    port: int
    status: str  # 'online', 'offline', 'error', 'starting', 'stopping'
    last_check: datetime
    response_time_ms: float
    error_count: int = 0
    total_requests: int = 0
    success_rate: float = 0.0
    uptime_start: Optional[datetime] = None
    restart_count: int = 0

class UnifiedMCPCoordinator:
    """
    Unified coordinator for all MCP servers and real-time flash loan automation
    """
    def __init__(self, config_path: str = "unified_mcp_config.json"):
        self.config_path = Path(config_path)
        self.workspace_path = Path(os.getcwd())
        self.servers: Dict[str, MCPServerInfo] = {}
        self.is_running = False
        self.health_check_interval = 30
        self.data_sources = {}
        self.flash_loan_opportunities: List[FlashLoanOpportunity] = []
        self.risk_limits = self._load_risk_limits()
        
        # MCP server configurations
        self.mcp_servers: Dict[str, Any] = {}
        self.start_time: Optional[datetime] = None
        self.monitoring_task: Optional[asyncio.Task[None]] = None
        
        # Initialize Flask app for API endpoints
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_flask_routes()
        
        # Data aggregation with proper typing
        self.price_data: Dict[str, Dict[str, Any]] = {}
        self.liquidity_data: Dict[str, Any] = {}
        self.gas_prices: Dict[str, float] = {}
        
        # Load configuration
        self._load_configuration()
        
        # Performance metrics
        self.metrics: Dict[str, Union[int, float]] = {
            'total_opportunities_found': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit_usd': 0.0,
            'average_profit_per_trade': 0.0,
            'system_uptime': 0,
            'data_refresh_rate': 0
        }
    
    def _load_configuration(self) -> None:
        """Load MCP server configuration with proper environment variable handling"""
        try:
            with open(self.config_path) as f:
                config = json.load(f)
            
            # Load server configurations
            for server_id, server_config in config.get('servers', {}).items():
                env_config: Dict[str, Any] = server_config.get('environment_variables', {})
                processed_env_vars: Dict[str, str] = {}
                if 'required' in env_config or 'optional' in env_config:
                    required_vars = cast(List[str], env_config.get('required', []))
                    optional_vars = cast(List[str], env_config.get('optional', []))
                    for var_name in required_vars + optional_vars:
                        env_value = os.getenv(var_name)
                        if env_value:
                            processed_env_vars[var_name] = env_value
                        elif var_name in required_vars:
                            logger.warning(f"Required environment variable {var_name} not found for server {server_id}")
                else:
                    for key, value in env_config.items():
                        if isinstance(value, str):
                            processed_env_vars[key] = value
                        else:
                            processed_env_vars[key] = str(value)
                
                server_info = MCPServerInfo(
                    name=cast(str, server_config['name']),
                    type=cast(str, server_config['type']),
                    path=cast(str, server_config['path']),
                    port=cast(int, server_config['port']),
                    enabled=server_config.get('enabled', True),
                    dependencies=[str(dep) for dep in server_config.get('dependencies', [])],
                    environment_vars=processed_env_vars
                )
                self.servers[server_id] = server_info
            
            # Load global configuration
            global_config = config.get('global_configuration', {})
            self.health_check_interval = global_config.get('health_check_interval', 30)
            
            logger.info(f"Loaded configuration for {len(self.servers)} MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Attempting to load alternative configuration or use default settings.")
            alternative_path = Path("alternative_mcp_config.json")
            if alternative_path.exists():
                try:
                    with open(alternative_path) as f:
                        config = json.load(f)
                    for server_id, server_config in config.get('servers', {}).items():
                        env_config: Dict[str, Any] = server_config.get('environment_variables', {})
                        processed_env_vars: Dict[str, str] = {}
                        if 'required' in env_config or 'optional' in env_config:
                            required_vars = cast(List[str], env_config.get('required', []))
                            optional_vars = cast(List[str], env_config.get('optional', []))
                            for var_name in required_vars + optional_vars:
                                env_value = os.getenv(var_name)
                                if env_value:
                                    processed_env_vars[var_name] = env_value
                                elif var_name in required_vars:
                                    logger.warning(f"Required environment variable {var_name} not found for server {server_id}")
                        else:
                            for key, value in env_config.items():
                                if isinstance(value, str):
                                    processed_env_vars[key] = value
                                else:
                                    processed_env_vars[key] = str(value)
                        
                        server_info = MCPServerInfo(
                            name=cast(str, server_config['name']),
                            type=cast(str, server_config['type']),
                            path=cast(str, server_config['path']),
                            port=cast(int, server_config['port']),
                            enabled=server_config.get('enabled', True),
                            dependencies=[str(dep) for dep in server_config.get('dependencies', [])],
                            environment_vars=processed_env_vars
                        )
                        self.servers[server_id] = server_info
                    
                    global_config = config.get('global_configuration', {})
                    self.health_check_interval = global_config.get('health_check_interval', 30)
                    
                    logger.info(f"Loaded alternative configuration for {len(self.servers)} MCP servers from {alternative_path}")
                    return
                except Exception as alt_e:
                    logger.error(f"Failed to load alternative configuration: {alt_e}")
            
            # If no alternative config is found, use default empty configuration
            logger.info("Using default empty configuration.")
            self.servers = {}
            self.health_check_interval = 30

    def _load_risk_limits(self) -> Dict[str, float]:
        """Load risk management parameters"""
        return {
            'min_profit_threshold': float(os.getenv('MIN_PROFIT_THRESHOLD', 50)),
            'max_slippage': float(os.getenv('MAX_SLIPPAGE', 0.005)),
            'max_position_size': float(os.getenv('MAX_POSITION_SIZE', 10000)),
            'stop_loss_percentage': float(os.getenv('STOP_LOSS_PERCENTAGE', 0.02)),
            'take_profit_percentage': float(os.getenv('TAKE_PROFIT_PERCENTAGE', 0.05)),
            'liquidity_threshold': float(os.getenv('LIQUIDITY_THRESHOLD', 50000))
        }

    def _setup_flask_routes(self) -> None:
        """Setup Flask API routes"""
        
        # @self.app.route('/api/status')
        # def get_status():
        #     """Get system status"""
        #     return jsonify({
        #         'status': 'running' if self.is_running else 'stopped',
        #         'servers': {
        #             server_id: {
        #                 'name': server.name,
        #                 'type': server.type,
        #                 'port': server.port,
        #                 'health_status': server.health_status,
        #                 'restart_count': server.restart_count,
        #                 'uptime': (datetime.now() - server.start_time).total_seconds() if server.start_time else 0
        #             }
        #             for server_id, server in self.servers.items()
        #         },
        #         'metrics': self.metrics,
        #         'opportunities_count': len(self.flash_loan_opportunities)
        #     })
        
        # @self.app.route('/api/opportunities')
        # def get_opportunities():
        #     """Get current flash loan opportunities"""
        #     # Convert opportunities to serializable format
        #     opportunities: List[Dict[str, Any]] = []
        #     for opp in self.flash_loan_opportunities[-50:]:  # Last 50 opportunities
        #         opportunities.append({
        #             'token_symbol': opp.token_symbol,
        #             'buy_dex': opp.buy_dex,
        #             'sell_dex': opp.sell_dex,
        #             'profit_usd': opp.profit_usd,
        #             'profit_percentage': opp.profit_percentage,
        #             'net_profit_usd': opp.net_profit_usd,
        #             'confidence_score': opp.confidence_score,
        #             'risk_level': opp.risk_level,
        #             'timestamp': opp.timestamp.isoformat()
        #         })
        #     return jsonify(opportunities)
        
        @self.app.route('/api/execute_opportunity', methods=['POST'])
        async def execute_opportunity() -> Any:  # type: ignore
            """Execute a flash loan opportunity"""
            try:
                data: Dict[str, Any] = request.get_json()  # type-annotate JSON payload
                opportunity_id = data.get('opportunity_id')
                
                if not opportunity_id or opportunity_id >= len(self.flash_loan_opportunities):
                    return jsonify({'error': 'Invalid opportunity ID'}), 400
                
                opportunity = cast(FlashLoanOpportunity, self.flash_loan_opportunities[opportunity_id])
                result: Dict[str, Any] = await self._execute_flash_loan(opportunity)
                
                return jsonify({
                    'success': result['success'],
                    'message': result['message'],
                    'transaction_hash': result.get('tx_hash'),
                    'profit_realized': result.get('profit')
                })
                
            except Exception as e:
                logger.error(f"Error executing opportunity: {e}")
                return jsonify({'error': str(e)}), 500

    def _get_server_env(self, server: MCPServerInfo) -> Dict[str, str]:
        # Merge base environment with server-specific variables
        env = os.environ.copy()
        env.update(server.environment_vars)
        return env

    async def start_mcp_server(self, server_id: str, server: MCPServerInfo) -> bool:
        """Start an individual MCP server"""
        try:
            if server.process and server.process.poll() is None:
                logger.info(f"Server {server_id} is already running")
                return True
            
            server_path = self.workspace_path / server.path
            
            if server.type == 'python':
                # Start Python MCP server
                cmd = [sys.executable, str(server_path)]
                env = self._get_server_env(server)
                server.process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=server_path.parent
                )
            elif server.type == 'typescript':
                # Start TypeScript MCP server
                built_path = server_path.parent / 'dist' / 'index.js'
                if not built_path.exists():
                    logger.error(f"Built TypeScript file not found: {built_path}")
                    return False
                cmd = ['node', str(built_path)]
                env = self._get_server_env(server)
                server.process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=built_path.parent
                )
            
            server.start_time = datetime.now()
            server.health_status = "starting"
            
            # Wait a moment for the server to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if server.process and hasattr(server.process, 'poll') and server.process.poll() is None:
                server.health_status = "running"
                logger.info(f"Successfully started MCP server: {server_id}")
                return True
            else:            logger.error(f"Failed to start MCP server: {server_id}")
            return False
                
        except Exception as e:
            logger.error(f"Error starting server {server_id}: {e}")
            server.health_status = "error"
            return False

    async def stop_mcp_server(self, server_id: str, server: MCPServerInfo) -> None:
        """Stop an individual MCP server"""
        try:
            if server.process:
                server.process.terminate()
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(self._wait_for_process(server.process)),
                        timeout=10
                    )
                except asyncio.TimeoutError:
                    server.process.kill()
                    logger.warning(f"Force killed server {server_id}")
                
                server.process = None
                server.health_status = "stopped"
                logger.info(f"Stopped MCP server: {server_id}")
        except Exception as e:
            logger.error(f"Error stopping server {server_id}: {e}")

    async def _wait_for_process(self, process: subprocess.Popen[bytes]) -> None:
        """Wait for process to terminate"""
        while process.poll() is None:
            await asyncio.sleep(0.1)

    async def health_check_servers(self) -> None:
        """Perform health checks on all servers"""
        for server_id, server in self.servers.items():
            if not server.enabled:
                continue
                
            try:                # Check if process is still running
                if server.process and server.process.poll() is None:
                    # Use TCP connection check instead of aiohttp to avoid aiodns
                    try:
                        # Simple TCP connection test
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result: str = sock.connect_ex(('localhost', server.port))
                        sock.close()
                        
                        if result == 0:
                            server.health_status = "healthy"
                        else:
                            server.health_status = "unreachable"
                    except Exception:
                        server.health_status = "unreachable"
                else:
                    server.health_status = "stopped"
                    if server.enabled:
                        # Attempt restart
                        logger.info(f"Attempting to restart stopped server: {server_id}")
                        await self.start_mcp_server(server_id, server)
                        server.restart_count += 1
                        
                server.last_health_check = datetime.now()
                
            except Exception as e:
                logger.error(f"Health check failed for {server_id}: {e}")
                server.health_status = "error"

    async def aggregate_price_data(self) -> None:
        """Aggregate price data from all MCP servers"""
        try:
            # Query each MCP server for price data
            tasks: List[Any] = []
            for server_id, server in self.servers.items():
                if server.health_status == "healthy":
                    tasks.append(self._query_server_data(server_id, server))
            
            # Wait for all queries to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, dict):
                    self._process_price_data(cast(Dict[str, Any], result))
                    
        except Exception as e:
            logger.error(f"Error aggregating price data: {e}")

    async def _query_server_data(self, server_id: str, server: MCPServerInfo) -> Dict[str, Any]:
        """Query data from a specific MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{server.port}/api/prices",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        data['source'] = server_id
                        return data
        except Exception as e:
            logger.debug(f"Could not query data from {server_id}: {e}")
        return {}

    def _process_price_data(self, data: Dict[str, Any]) -> None:
        """Process price data and identify arbitrage opportunities"""
        if not data or 'prices' not in data:
            return
            
        source = data.get('source', 'unknown')
        prices = cast(Dict[str, Dict[str, Union[float, int, str]]], data.get('prices', {}))
        
        # Update price data
        for token, price_info in prices.items():
            if token not in self.price_data:
                self.price_data[token] = {}
            
            self.price_data[token][source] = {
                'price': price_info.get('price', 0),
                'liquidity': price_info.get('liquidity', 0),
                'timestamp': datetime.now(),
                'volume_24h': price_info.get('volume_24h', 0)
            }
        
        # Check for arbitrage opportunities
        self._identify_arbitrage_opportunities()

    def _identify_arbitrage_opportunities(self) -> None:
        """Identify flash loan arbitrage opportunities with enhanced real-time analysis"""
        try:
            current_opportunities: List[FlashLoanOpportunity] = []
            current_time = datetime.now()
            
            for token, dex_prices in self.price_data.items():
                if len(dex_prices) < 2:
                    continue
                
                # Filter only fresh price data (less than 10 seconds old)
                fresh_prices: List[Tuple[str, float, float, Dict[str, Any]]] = []
                for dex, data in dex_prices.items():
                    price_age = (current_time - data['timestamp']).total_seconds()
                    if (price_age < 10 and 
                        data['price'] > 0 and 
                        data['liquidity'] > self.risk_limits['liquidity_threshold']):
                        fresh_prices.append((dex, data['price'], data['liquidity'], data))
                
                if len(fresh_prices) < 2:
                    continue
                
                # Sort by price
                fresh_prices.sort(key=lambda x: Any: Any: x[1])
                
                buy_dex, buy_price, buy_liquidity, buy_data = fresh_prices[0]
                sell_dex, sell_price, sell_liquidity, sell_data = fresh_prices[-1]
                
                if buy_price > 0 and sell_price > buy_price:
                    profit_percentage = (sell_price - buy_price) / buy_price
                    
                    # Higher minimum profit threshold for real trading
                    if profit_percentage > 0.005:  # Minimum 0.5% profit for real execution
                        
                        # Enhanced liquidity analysis for safer trade sizing
                        max_trade_size = min(
                            buy_liquidity * 0.03,  # Max 3% of liquidity for reduced slippage
                            sell_liquidity * 0.03,
                            50000  # Max $50k per trade for risk management
                        )
                        
                        # Enhanced gas cost estimation based on DEX types
                        gas_cost_usd = self._calculate_enhanced_gas_cost(buy_dex, sell_dex)
                        
                        # Account for slippage impact
                        slippage_impact = self._estimate_slippage_impact(
                            max_trade_size, buy_liquidity, sell_liquidity
                        )
                        
                        adjusted_profit_percentage = profit_percentage - slippage_impact
                        profit_usd = max_trade_size * adjusted_profit_percentage
                        net_profit_usd = profit_usd - gas_cost_usd
                        
                        if net_profit_usd > self.risk_limits['min_profit_threshold']:
                            # Get token address from our token registry
                            token_address = self._get_token_address(token)
                            
                            opportunity = FlashLoanOpportunity(
                                token_symbol=token,
                                token_address=token_address,
                                buy_dex=buy_dex,
                                sell_dex=sell_dex,
                                buy_price=buy_price,
                                sell_price=sell_price,
                                profit_usd=profit_usd,
                                profit_percentage=adjusted_profit_percentage,
                                gas_cost_usd=gas_cost_usd,
                                net_profit_usd=net_profit_usd,
                                liquidity_available=min(buy_liquidity, sell_liquidity),
                                max_trade_size=max_trade_size,
                                timestamp=current_time,
                                confidence_score=self._calculate_enhanced_confidence_score(
                                    adjusted_profit_percentage, 
                                    min(buy_liquidity, sell_liquidity),
                                    buy_data,
                                    sell_data
                                ),
                                risk_level=self._assess_enhanced_risk_level(
                                    adjusted_profit_percentage, 
                                    min(buy_liquidity, sell_liquidity),
                                    slippage_impact
                                )
                            )
                            
                            current_opportunities.append(opportunity)
            
            # Sort opportunities by net profit and confidence
            current_opportunities.sort(
                key=lambda x: Any: Any: (x.net_profit_usd * x.confidence_score), 
                reverse=True
            )
            
            # Keep only top 20 opportunities to avoid spam
            self.flash_loan_opportunities = current_opportunities[:20]
            self.metrics['total_opportunities_found'] = len(self.flash_loan_opportunities)
            
            if current_opportunities:
                logger.info(f"Found {len(current_opportunities)} real-time arbitrage opportunities")
                # Log top 3 opportunities with details
                for i, opp in enumerate(current_opportunities[:3]):
                    logger.info(f"  #{i+1}: {opp.token_symbol} {opp.buy_dex}→{opp.sell_dex} "
                              f"Profit: ${opp.net_profit_usd:.2f} "
                              f"Confidence: {opp.confidence_score:.2f} "
                              f"Risk: {opp.risk_level}")
                
        except Exception as e:
            logger.error(f"Error identifying arbitrage opportunities: {e}")

    def _calculate_enhanced_gas_cost(self, buy_dex: str, sell_dex: str) -> float:
        """Calculate enhanced gas cost based on DEX types and current gas prices"""
        # Base gas costs for different DEX types
        gas_costs = {
            'uniswap_v3': 150000,
            'uniswap_v2': 120000,
            'sushiswap': 120000,
            'balancer': 180000,
            '1inch': 200000,  # Aggregator uses more gas
            'curve': 160000
        }
        
        buy_gas = gas_costs.get(buy_dex.lower(), 150000)
        sell_gas = gas_costs.get(sell_dex.lower(), 150000)
        flash_loan_gas = 50000  # Flash loan overhead
        
        total_gas = buy_gas + sell_gas + flash_loan_gas
        
        # Get current gas price (simplified - in real implementation would query gas tracker)
        gas_price_gwei = self.gas_prices.get('standard', 30)  # Default 30 gwei
        gas_price_eth = gas_price_gwei * 1e-9
        
        # Get ETH price (simplified - in real implementation would use price oracle)
        eth_price_usd = 2000  # Default ETH price
        
        gas_cost_usd = total_gas * gas_price_eth * eth_price_usd
        return gas_cost_usd

    def _estimate_slippage_impact(self, trade_size: float, buy_liquidity: float, sell_liquidity: float) -> float:
        """Estimate slippage impact based on trade size vs liquidity"""
        buy_impact = min(trade_size / buy_liquidity, 0.05)  # Max 5% impact
        sell_impact = min(trade_size / sell_liquidity, 0.05)
        
        # Convert to percentage
        total_slippage = (buy_impact + sell_impact) * 0.5  # Average impact
        return total_slippage

    def _get_token_address(self, token_symbol: str) -> str:
        """Get token contract address from symbol"""
        # Token address registry (mainnet addresses)
        token_addresses = {
            'ETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'USDC': '0xA0b86a33E6441e36D04b4395aD3fB4e44C6A74f4',
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
            'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
            'LINK': '0x514910771AF9Ca656af840dff83E8264EcF986CA',
            'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
            'AAVE': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',
            'COMP': '0xc00e94Cb662C3520282E6f5717214004A7f26888'
        }
        return token_addresses.get(token_symbol.upper(), '')

    def _calculate_enhanced_confidence_score(self, profit_percentage: float, liquidity: float, 
                                           buy_data: Dict[str, Any], sell_data: Dict[str, Any]) -> float:
        """Calculate enhanced confidence score with multiple factors"""
        # Base confidence from profit and liquidity
        profit_score = min(profit_percentage * 100, 5) / 5  # Max 5% profit = 1.0
        liquidity_score = min(liquidity / 1000000, 1.0)  # Max 1M liquidity = 1.0
        
        # Data freshness score
        current_time = datetime.now()
        buy_age = (current_time - buy_data['timestamp']).total_seconds()
        sell_age = (current_time - sell_data['timestamp']).total_seconds()
        max_age = max(buy_age, sell_age)
        freshness_score = max(1 - max_age / 30, 0)  # 30 seconds max age
        
        # Volume score (higher recent volume = more confidence)
        buy_volume = buy_data.get('volume_24h', 0)
        sell_volume = sell_data.get('volume_24h', 0)
        avg_volume = (buy_volume + sell_volume) / 2
        volume_score = min(avg_volume / 10000000, 1.0)  # Max 10M volume = 1.0
        
        # Weighted average
        confidence = (
            profit_score * 0.4 +
            liquidity_score * 0.3 +
            freshness_score * 0.2 +
            volume_score * 0.1
        )
        
        return min(confidence, 1.0)

    def _assess_enhanced_risk_level(self, profit_percentage: float, liquidity: float, 
                                  slippage_impact: float) -> str:
        """Assess enhanced risk level with multiple factors"""
        risk_score = 0
        
        # Profit risk (very high profit might indicate stale data or MEV risk)
        if profit_percentage > 0.1:  # >10% profit is suspicious
            risk_score += 3
        elif profit_percentage > 0.05:  # >5% profit is high risk
            risk_score += 2
        elif profit_percentage < 0.01:  # <1% profit is low margin
            risk_score += 1
        
        # Liquidity risk
        if liquidity < 100000:  # <100k liquidity
            risk_score += 2
        elif liquidity < 500000:  # <500k liquidity
            risk_score += 1
        
        # Slippage risk
        if slippage_impact > 0.02:  # >2% slippage
            risk_score += 2
        elif slippage_impact > 0.01:  # >1% slippage
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 5:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"

    async def _execute_flash_loan(self, opportunity: FlashLoanOpportunity) -> Dict[str, Any]:
        """Execute a flash loan opportunity"""
        try:
            # This would integrate with the actual flash loan execution logic
            # For now, return a simulated result
            
            logger.info(f"Executing flash loan for {opportunity.token_symbol}: "
                       f"{opportunity.buy_dex} -> {opportunity.sell_dex}, "
                       f"Expected profit: ${opportunity.net_profit_usd:.2f}")
            
            # Check if we have real execution capability
            execution_result: str = await self._call_arbitrage_trading_mcp(
                "execute_flash_loan_arbitrage",
                {
                    "token_pair": opportunity.token_symbol + "/USDC",
                    "buy_dex": opportunity.buy_dex,
                    "sell_dex": opportunity.sell_dex,
                    "amount": float(opportunity.max_trade_size),
                    "expected_profit": float(opportunity.net_profit_usd),
                    "risk_level": opportunity.risk_level,
                    "confidence_score": opportunity.confidence_score
                }
            )
            
            if execution_result and execution_result.get('success'):
                # Real execution succeeded
                self.metrics['successful_trades'] += 1
                self.metrics['total_profit_usd'] += opportunity.net_profit_usd
                
                return {
                    'status': 'success',
                    'transaction_hash': execution_result.get('transaction_hash'),
                    'actual_profit': execution_result.get('actual_profit', opportunity.net_profit_usd),
                    'gas_used': execution_result.get('gas_used'),
                    'execution_time': execution_result.get('execution_time')
                }
            else:
                # Simulate execution (for testing/development)
                success = opportunity.confidence_score > 0.7
                
                if success:
                    self.metrics['successful_trades'] += 1
                    self.metrics['total_profit_usd'] += opportunity.net_profit_usd
                    
                    return {
                        'status': 'simulated_success',
                        'simulated_profit': opportunity.net_profit_usd,
                        'note': 'Simulated execution - real trading not available'
                    }
                else:
                    self.metrics['failed_trades'] += 1
                    return {
                        'status': 'simulated_failure',
                        'reason': 'Low confidence score'
                    }
            
        except Exception as e:
            logger.error(f"Flash loan execution failed: {e}")
            self.metrics['failed_trades'] += 1
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            # Update average profit
            total_trades = self.metrics['successful_trades'] + self.metrics['failed_trades']
            if total_trades > 0:
                self.metrics['average_profit_usd'] = self.metrics['total_profit_usd'] / total_trades

    async def _call_arbitrage_trading_mcp(self, tool: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call the arbitrage trading MCP server"""
        try:
            server_config = self.mcp_servers.get('arbitrage_trading')
            if not server_config:
                logger.warning("Arbitrage trading MCP server not configured")
                return None
            
            url = f"http://{server_config['host']}:{server_config['port']}/tools/{tool}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Arbitrage trading MCP call failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling arbitrage trading MCP: {e}")
            return None

    async def _save_opportunity_log(self, opportunity: FlashLoanOpportunity, result: Dict[str, Any]) -> None:
        """Save opportunity execution log"""
        try:
            log_entry: Dict[str, Any] = {
                'timestamp': datetime.now().isoformat(),
                'opportunity': asdict(opportunity),
                'execution_result': result,
                'system_metrics': self.metrics.copy()
            }
            
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            # Save to file
            log_file = f"logs/arbitrage_log_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Append to daily log file
            logs: List[Any] = []  # explicitly typed list
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save opportunity log: {e}")

    async def generate_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        try:
            # Get MCP server statuses
            server_statuses = {}
            for name, config in self.mcp_servers.items():
                status = await self._check_mcp_server_status(name, config)
                server_statuses[name] = status
            
            # Calculate performance metrics
            total_trades = self.metrics['successful_trades'] + self.metrics['failed_trades']
            success_rate = (self.metrics['successful_trades'] / total_trades * 100) if total_trades > 0 else 0
            
            # Get recent opportunities
            recent_opportunities = []
            log_file = f"logs/arbitrage_log_{datetime.now().strftime('%Y%m%d')}.json"
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        logs = json.load(f)
                        recent_opportunities = logs[-10:]  # Last 10 opportunities
                except:
                    pass
            
            report: Dict[str, Any] = {}
            report = {
                'generated_at': datetime.now().isoformat(),
                'system_status': 'operational' if self.is_running else 'stopped',
                'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600 if self.start_time else 0,
                'mcp_servers': server_statuses,
                'performance_metrics': {
                    'total_opportunities_found': self.metrics['total_opportunities_found'],
                    'total_trades_executed': total_trades,
                    'successful_trades': self.metrics['successful_trades'],
                    'failed_trades': self.metrics['failed_trades'],
                    'success_rate_percent': round(success_rate, 2),
                    'total_profit_usd': round(self.metrics['total_profit_usd'], 2),
                    'average_profit_usd': round(self.metrics['average_profit_usd'], 2)
                },
                'recent_opportunities': recent_opportunities
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating system report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    async def start(self) -> None:
        """Start the unified MCP coordinator"""
        logger.info("Starting Unified MCP Coordinator...")
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # Start all enabled MCP servers
        for server_id, server in self.servers.items():
            if server.enabled:
                await self.start_mcp_server(server_id, server)
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Unified MCP Coordinator started successfully")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for health checks and data aggregation"""
        while self.is_running:
            try:
                # Perform health checks
                await self.health_check_servers()
                
                # Aggregate price data
                await self.aggregate_price_data()
                
                # Wait for next cycle
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _check_mcp_server_status(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check the status of an MCP server"""
        try:
            url = f"http://{config.get('host', 'localhost')}:{config.get('port', 8000)}/health"
            
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                        
                        if response.status == 200:
                            return {
                                'name': name,
                                'status': 'online',
                                'response_time_ms': response_time,
                                'last_check': datetime.now().isoformat()
                            }
                        else:
                            return {
                                'name': name,
                                'status': 'error',
                                'response_time_ms': response_time,
                                'last_check': datetime.now().isoformat(),
                                'error': f"HTTP {response.status}"
                            }
                except asyncio.TimeoutError:
                    return {
                        'name': name,
                        'status': 'timeout',
                        'response_time_ms': 5000,
                        'last_check': datetime.now().isoformat(),
                        'error': 'Request timeout'
                    }
                except Exception as e:
                    return {
                        'name': name,
                        'status': 'offline',
                        'response_time_ms': 0,
                        'last_check': datetime.now().isoformat(),
                        'error': str(e)
                    }
        except Exception as e:
            return {
                'name': name,
                'status': 'error',
                'response_time_ms': 0,
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }

    async def shutdown(self):
        """Graceful shutdown of the coordinator"""
        logger.info("Shutting down Unified MCP Coordinator...")
        
        self.is_running = False
        
        # Cancel monitoring task
        if hasattr(self, 'monitoring_task') and self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Generate final report
        try:
            final_report = await self.generate_system_report()
            report_file = f"logs/final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs('logs', exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(final_report, f, indent=2, default=str)
            logger.info(f"Final report saved to {report_file}")
        except Exception as e:
            logger.error(f"Failed to generate final report: {e}")
        
        logger.info("Unified MCP Coordinator shutdown complete")

def signal_handler(coordinator: UnifiedMCPCoordinator) -> Callable[[int, Optional[FrameType]], None]:
    """Signal handler for graceful shutdown"""
    def handler(signum: int, frame: Optional[FrameType]) -> None:
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(coordinator.shutdown())
    return handler

async def main():
    """Main entry point"""
    coordinator = UnifiedMCPCoordinator()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler(coordinator))
    signal.signal(signal.SIGTERM, signal_handler(coordinator))
    
    try:
        await coordinator.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await coordinator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
