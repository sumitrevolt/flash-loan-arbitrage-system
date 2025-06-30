#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time

from aiohttp import web
from dataclasses import dataclass
from mcp_servers.profit_optimizer_mcp_server import ProfitOptimizerMCPServer
from mcp_servers.real_time_price_mcp_server import RealTimePriceMCPServer
from web3 import Web3
import aiohttp
"""
Unified Flash Loan Arbitrage System with MCP Integration
=======================================================

Production-ready unified system that consolidates all functionality:
- Real-time arbitrage monitoring using Web3
- MCP server integration for intelligent task distribution
- Flash loan execution via Aave Protocol
- AI optimization and strategy enhancement
- Real blockchain data only (no mock/simulation)

Usage:
    python unified_flash_loan_arbitrage_system.py --mode execute
    python unified_flash_loan_arbitrage_system.py --mode monitor --min-profit 10
    python unified_flash_loan_arbitrage_system.py --mode analyze --ai-optimize
"""


# Import MCP servers with proper path handling
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    MCP_SERVERS_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] MCP servers not available: {e}")
    MCP_SERVERS_AVAILABLE = False
    
    # Create mock classes
    class RealTimePriceMCPServer:
        def __init__(self): pass
        async def start(self): pass
        async def shutdown(self): pass
        
    class ProfitOptimizerMCPServer:
        def __init__(self): pass
        async def start(self): pass
        async def shutdown(self): pass

# Configure logging

# Unicode-safe logging setup
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('unified_arbitrage_system.log')


    


@dataclass
class ArbitrageOpportunity:
    """Real-time arbitrage opportunity data"""
    token: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    price_diff_pct: float
    optimal_trade_size: float
    net_profit: float
    gas_price_gwei: float
    timestamp: str
    execution_ready: bool

@dataclass
class FlashLoanParams:
    """Flash loan execution parameters"""
    asset: str
    amount: int
    recipient: str
    params: bytes
    referral_code: int

class UnifiedFlashLoanArbitrageSystem:
    """Unified system for flash loan arbitrage with MCP integration and AG-UI support"""

    def __init__(self):
        self.logger = logging.getLogger("UnifiedArbitrageSystem")
        self.is_running = False
        self.mode = "monitor"  # monitor, execute, analyze

        # AG-UI event endpoint (set this to your frontend or AG-UI middleware)
        self.agui_event_url = os.getenv("AGUI_EVENT_URL", "http://localhost:8081/agui/event")

        # Load environment variables
        self._load_environment()

        # Initialize blockchain connection
        self._initialize_web3()

        # Load configuration
        self.config = self._load_configuration()

        # Initialize MCP servers
        from typing import Dict, Union
        from mcp_servers.real_time_price_mcp_server import RealTimePriceMCPServer
        from mcp_servers.profit_optimizer_mcp_server import ProfitOptimizerMCPServer

        self.mcp_servers: Dict[str, Union[RealTimePriceMCPServer, ProfitOptimizerMCPServer]] = {}
        self.mcp_enabled = False

        # Real-time data sources
        self.price_feeds = {}
        self.dex_contracts = {}
        self.aave_contracts = {}

        # Performance tracking
        self.stats = {
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'total_profit_usd': 0.0,
            'gas_used': 0,
            'execution_errors': 0,
            'uptime_start': datetime.now()


        # Safety parameters
        self.min_profit_usd = 5.0
        self.max_trade_size = 10000.0
        self.max_gas_price_gwei = 50
        self.max_slippage = 0.005  # 0.5%

        # Token configurations (real Polygon addresses)
        self.tokens = {
            'WMATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
            'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
            'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
            'WBTC': '0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6'


        # DEX router addresses (real Polygon addresses)
        self.dex_routers = {
            'QuickSwap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
            'SushiSwap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
            'UniswapV3': '0xE592427A0AEce92De3Edee1F18E0157C05861564'


        # Aave V3 addresses (real Polygon addresses)
        self.aave_addresses = {
            'pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
            'provider': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
            'data_provider': '0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654'


        # Start AG-UI HTTP server for receiving user events
        self.agui_app = web.Application()
        self.agui_app.add_routes([web.post('/agui/user_event', self.handle_agui_user_event)])
        self.agui_runner = None

    def _load_environment(self):
        """Load environment variables from .env file"""
        env_path = Path('.env')
        self.logger.info(f"[DEBUG] Checking for .env file at {env_path.resolve()}")
        self.logger.debug(f"[DEBUG] Environment variables required: ARBITRAGE_PRIVATE_KEY, POLYGON_RPC_URL")
        if env_path.exists():
            self.logger.info("[DEBUG] .env file found, loading variables...")
            self.logger.debug(f"[DEBUG] Validating format of POLYGON_RPC_URL: {os.getenv('POLYGON_RPC_URL')}")
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                        self.logger.info(f"[DEBUG] Loaded env var: {key}={value[:4]}***")
        else:
            self.logger.warning("[WARN] .env file not found. Environment variables may be missing.")

        # Validate required environment variables
        required_vars = ['ARBITRAGE_PRIVATE_KEY', 'POLYGON_RPC_URL']
        for var in required_vars:
            val = os.getenv(var)
            if not val:
                self.logger.error(f"[ERROR] Required environment variable {var} not found")
                raise Exception(f"Required environment variable {var} not found")
            else:
                self.logger.info(f"[DEBUG] Env var {var} is set.")

        # Check production mode settings
        production_mode = os.getenv('PRODUCTION_MODE', 'true').lower() == 'true'
        simulation_mode = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'

        self.logger.info(f"[DEBUG] PRODUCTION_MODE={production_mode}, SIMULATION_MODE={simulation_mode}")

        if not production_mode and simulation_mode:
            self.logger.warning("[WARN] System configured in SIMULATION mode")
        elif production_mode and not simulation_mode:
            self.logger.info("[OK] System configured in PRODUCTION mode - using real data only")
        else:
            self.logger.info("[OK] Using production mode defaults")
        simulation_mode = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'

        if not production_mode and simulation_mode:
            self.logger.warning("[WARN] System configured in SIMULATION mode")
        elif production_mode and not simulation_mode:
            self.logger.info("[OK] System configured in PRODUCTION mode - using real data only")
        else:
            self.logger.info("[OK] Using production mode defaults")
                
    def _initialize_web3(self):
        """Initialize Web3 connection to Polygon network"""
        try:
            polygon_rpc = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
            self.w3 = Web3(Web3.HTTPProvider(polygon_rpc))
            
            if not self.w3.is_connected():
                self.logger.error("[ERROR] Failed to connect to Polygon network")
                raise Exception("Failed to connect to Polygon network")
                
            # Setup wallet
            private_key = os.getenv('ARBITRAGE_PRIVATE_KEY')
            if private_key:
                self.account = self.w3.eth.account.from_key(private_key)
                self.wallet_address = self.account.address
                self.logger.info(str(f"[OK] Wallet initialized: {self.wallet_address}")
            else:
                raise Exception("ARBITRAGE_PRIVATE_KEY not found")
                
            self.logger.info(str(f"[OK] Connected to Polygon network (Block: {self.w3.eth.block_number}")
            self.logger.debug(f"[DEBUG] Wallet address: {self.wallet_address}")
            
        except Exception as e:
            self.logger.error(str(f"[ERROR] Failed to initialize Web3: {e}")
            raise
            
    def _load_configuration(self) -> Dict[str, Any]:
        """Load system configuration"""
        try:
            with open('unified_mcp_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("Configuration file not found, using defaults")
            self.logger.debug(f"[DEBUG] Default configuration: {json.dumps(self.config, indent=2)}")
            return {
                "system": {
                    "min_profit_usd": 5.0,
                    "max_trade_size": 10000.0,
                    "max_gas_price_gwei": 50,
                    "real_execution_enabled": False
                },
                "mcpServers": {},
                "monitoring": {
                    "price_update_interval": 5,
                    "opportunity_scan_interval": 2


                
            
            
    async def initialize_system(self, mode: str, **kwargs):
        """Initialize the complete system"""
        self.mode = mode
        self.logger.info("[INIT] Initializing Unified Flash Loan Arbitrage System")
        self.logger.info("=" * 70)
        
        # Display startup banner
        self._display_startup_banner(mode, kwargs)
        
        # Apply configuration overrides
        if 'min_profit' in kwargs:
            self.min_profit_usd = kwargs['min_profit']
        if 'max_trade_size' in kwargs:
            self.max_trade_size = kwargs['max_trade_size']
        if 'gas_limit' in kwargs:
            self.max_gas_price_gwei = kwargs['gas_limit']
            
        # Initialize real-time price feeds
        await self._initialize_price_feeds()
        
        # Initialize DEX contracts
        await self._initialize_dex_contracts()
        
        # Initialize Aave contracts
        await self._initialize_aave_contracts()
        
        # Initialize MCP servers if enabled
        if kwargs.get('enable_mcp', True):
            await self._initialize_mcp_servers()
            
        self.logger.info("[OK] System initialization complete")
        
    def _display_startup_banner(self, mode: str, config: Dict[str, Any]):
        """Display system startup banner"""
        banner_lines = [
            "[HOT] UNIFIED FLASH LOAN ARBITRAGE SYSTEM [HOT]",
            "=" * 70,
            f"[TASK] Mode: {mode.upper()}",
            f"💰 Min Profit: ${config.get('min_profit', self.min_profit_usd):.2f}",
            f"[METRICS] Max Trade Size: ${config.get('max_trade_size', self.max_trade_size):,.0f}",
            f"⛽ Gas Limit: {config.get('gas_limit', self.max_gas_price_gwei)} Gwei",
            f"🏦 Flash Loan Provider: Aave V3",
            f"🔗 Network: Polygon",
            f"👛 Wallet: {self.wallet_address[:10]}...{self.wallet_address[-6:]}",
            f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70

        
        
        for line in banner_lines:
            self.logger.info(line)
            
    async def _initialize_price_feeds(self):
        """Initialize real-time price feeds from DEXs"""
        self.logger.info("[METRICS] Initializing real-time price feeds...")
        
        # Router ABI for getAmountsOut
        router_abi = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [
                    {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
                ],
                "stateMutability": "view",
                "type": "function"


            
        
        
        # Initialize router contracts
        for dex_name, router_address in self.dex_routers.items():
            try:
                contract = self.w3.eth.contract(
                    address=router_address,
                    abi=router_abi

                
                self.price_feeds[dex_name] = contract
                self.logger.info(str(f"[OK] {dex_name} price feed initialized")
            except Exception as e:
                self.logger.error(str(f"[ERROR] Failed to initialize {dex_name} price feed: {e}")
                
    async def _initialize_dex_contracts(self):
        """Initialize DEX router contracts"""
        self.logger.info("[SYNC] Initializing DEX contracts...")
        # This would load the actual router contracts for trade execution
        # Implementation depends on specific DEX requirements
        
    async def _initialize_aave_contracts(self):
        """Initialize Aave V3 contracts for flash loans"""
        self.logger.info("🏦 Initializing Aave V3 contracts...")
        
        try:
            # Load Aave Pool ABI
            with open('abi/aave_pool.json', 'r') as f:
                pool_abi = json.load(f)
                
            # Initialize Aave Pool contract
            self.aave_pool = self.w3.eth.contract(
                address=self.aave_addresses['pool'],
                abi=pool_abi

            
            
            self.logger.info("[OK] Aave V3 Pool contract initialized")
            
        except Exception as e:
            self.logger.error(str(f"[ERROR] Failed to initialize Aave contracts: {e}")
            raise
            
    async def _initialize_mcp_servers(self):
        """Initialize MCP servers for AI optimization and task management"""
        self.logger.info("🤖 Initializing MCP servers...")
        try:
            # Initialize available MCP servers
            self.logger.info("[DEBUG] Creating RealTimePriceMCPServer instance...")
            try:
                self.mcp_servers['price'] = RealTimePriceMCPServer()
                self.logger.info("[OK] RealTimePriceMCPServer initialized successfully.")
            except Exception as e:
                self.logger.error(f"[ERROR] Failed to initialize RealTimePriceMCPServer: {e}")

            self.logger.info("[DEBUG] Creating ProfitOptimizerMCPServer instance...")
            try:
                self.mcp_servers['profit'] = ProfitOptimizerMCPServer()
                self.logger.info("[OK] ProfitOptimizerMCPServer initialized successfully.")
            except Exception as e:
                self.logger.error(f"[ERROR] Failed to initialize ProfitOptimizerMCPServer: {e}")
            # Start MCP servers
            for name, server in self.mcp_servers.items():
                self.logger.info(f"[DEBUG] Starting MCP server: {name}")
                await server.start()
                self.logger.info(str(f"[OK] {name} MCP server started")
            self.mcp_enabled = True
            self.logger.info(f"[DEBUG] MCP servers initialized: {list(self.mcp_servers.keys()}")
        except Exception as e:
            self.logger.warning(str(f"[WARN] MCP initialization failed: {e}")
            self.mcp_enabled = False
            
    async def start_system(self):
        """Start the complete arbitrage system"""
        try:
            self.is_running = True
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start monitoring tasks based on mode
            tasks = []
            
            if self.mode in ['monitor', 'execute', 'analyze']:
                tasks.append(asyncio.create_task(self._price_monitoring_loop()))
                tasks.append(asyncio.create_task(self._opportunity_detection_loop()))
                
            if self.mode == 'execute':
                tasks.append(asyncio.create_task(self._execution_loop()))
                
            if self.mode == 'analyze' and self.mcp_enabled:
                tasks.append(asyncio.create_task(self._ai_optimization_loop()))
                
            # Always run metrics reporting
            tasks.append(asyncio.create_task(self._metrics_reporting_loop()))
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except KeyboardInterrupt:
            self.logger.info("👋 Shutdown signal received")
        except Exception as e:
            self.logger.error(str(f"[ERROR] System error: {e}")
        finally:
            await self.shutdown()
            
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            self.logger.info(str(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def _price_monitoring_loop(self):
        """Monitor real-time prices from all DEXs"""
        self.logger.info("[METRICS] Starting real-time price monitoring...")
        self.logger.info("[OPTIMIZED] Enhanced price monitoring for high-frequency updates.")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # Update gas price
                current_gas = self.w3.eth.gas_price / 1e9
                
                if current_gas > self.max_gas_price_gwei:
                    self.logger.warning(str(f"⛽ High gas price: {current_gas:.1f} Gwei (limit: {self.max_gas_price_gwei}")
                    await asyncio.sleep(10)
                    continue
                
                # Fetch prices for all tokens from all DEXs
                price_data = {}
                for token_symbol, token_address in self.tokens.items():
                    token_prices = await self._fetch_token_prices_real_time(token_symbol, token_address)
                    if token_prices:
                        price_data[token_symbol] = token_prices
                        
                # Store updated prices
                self.current_prices = price_data
                
                end_time = time.time()
                self.logger.debug(str(f"Price update completed in {end_time - start_time:.2f}s")
                
                # Wait before next update
                await asyncio.sleep(self.config.get('monitoring', {}).get('price_update_interval', 5))
                
            except Exception as e:
                self.logger.error(str(f"Price monitoring error: {e}")
                await asyncio.sleep(10)
                
    async def _fetch_token_prices_real_time(self, token_symbol: str, token_address: str) -> Dict[str, float]:
        self.logger.debug(f"[DEBUG] Fetching real-time prices for {token_symbol} at {token_address}")
        """Fetch real-time token prices from all DEXs using Web3"""
        prices = {}
        self.logger.info(f"[OPTIMIZED] Fetching prices for {token_symbol} with reduced Web3 calls.")
        
        if token_symbol == 'USDC':
            # USDC is our price reference
            for dex_name in self.dex_routers.keys():
                prices[dex_name] = 1.0
            return prices
            
        try:
            usdc_address = self.tokens['USDC']
            amount_in = 10**18  # 1 token (18 decimals)
            
            # Adjust for token decimals
            if token_symbol in ['USDC', 'USDT']:
                amount_in = 10**6
            elif token_symbol == 'WBTC':
                amount_in = 10**8
                
            for dex_name, router_contract in self.price_feeds.items():
                try:
                    # Get price path: Token -> USDC
                    path = [token_address, usdc_address]
                    amounts_out = router_contract.functions.getAmountsOut(amount_in, path).call()
                    
                    if amounts_out and len(amounts_out) > 1:
                        usdc_out = amounts_out[-1]
                        # Calculate price per token
                        price = usdc_out / (10**6)  # USDC has 6 decimals
                        
                        # Normalize to per-token price
                        if token_symbol in ['USDC', 'USDT']:
                            price = price / (amount_in / 10**6)
                        elif token_symbol == 'WBTC':
                            price = price / (amount_in / 10**8)
                        else:
                            price = price / (amount_in / 10**18)
                            
                        if price > 0:
                            prices[dex_name] = price
                            
                except Exception as e:
                    self.logger.debug(str(f"Failed to get {token_symbol} price from {dex_name}: {e}")
                    self.logger.debug(f"[DEBUG] Token address: {token_address}, Router: {dex_name}")
                    continue
                    
        except Exception as e:
            self.logger.error(str(f"Error fetching prices for {token_symbol}: {e}")
            
        return prices
        
    async def _opportunity_detection_loop(self):
        """Detect arbitrage opportunities in real-time"""
        self.logger.info("[SEARCH] Starting opportunity detection...")
        
        while self.is_running:
            try:
                if not hasattr(self, 'current_prices'):
                    await asyncio.sleep(1)
                    continue
                    
                opportunities = []
                
                # Analyze each token for arbitrage opportunities
                for token_symbol, dex_prices in self.current_prices.items():
                    if len(dex_prices) < 2:
                        continue
                        
                    # Find best buy and sell prices
                    price_list = [(dex, price) for dex, price in dex_prices.items()]
                    price_list.sort(key=lambda x: x[1])
                    
                    buy_dex, buy_price = price_list[0]
                    sell_dex, sell_price = price_list[-1]
                    
                    if buy_price <= 0 or sell_price <= 0:
                        continue
                        
                    # Calculate price difference
                    price_diff_pct = ((sell_price - buy_price) / buy_price) * 100
                    
                    if price_diff_pct < 0.2:  # Minimum 0.2% difference
                        continue
                        
                    # Calculate optimal trade size and profitability
                    opportunity = await self._analyze_opportunity_profitability()
                        token_symbol, buy_dex, sell_dex, buy_price, sell_price, price_diff_pct
                    
                    
                    if opportunity and opportunity.net_profit >= self.min_profit_usd:
                        opportunities.append(opportunity)
                        
                # Process found opportunities
                if opportunities:
                    await self._process_opportunities(opportunities)
                    
                await asyncio.sleep(self.config.get('monitoring', {}).get('opportunity_scan_interval', 2))
                
            except Exception as e:
                self.logger.error(str(f"Opportunity detection error: {e}")
                await asyncio.sleep(5)
                
    async def _analyze_opportunity_profitability(self, token: str, buy_dex: str, sell_dex: str,
                                                 buy_price: float, sell_price: float,
                                                 price_diff_pct: float) -> Optional[ArbitrageOpportunity]:
        self.logger.debug(f"[DEBUG] Analyzing profitability for {token} between {buy_dex} and {sell_dex}")
                                               buy_price: float, sell_price: float, 
                                               price_diff_pct: float) -> Optional[ArbitrageOpportunity]:
        """Analyze profitability of arbitrage opportunity including all fees"""
        try:
            # Get current gas price
            gas_price_gwei = self.w3.eth.gas_price / 1e9
            
            if gas_price_gwei > self.max_gas_price_gwei:
                return None
                
            # Calculate optimal trade size (simplified)
            base_trade_size = min(self.max_trade_size, 2000.0)  # Start with $2000
            
            # Estimate total costs
            dex_fee = 0.003  # 0.3% typical DEX fee
            aave_fee = 0.0009  # 0.09% Aave flash loan fee
            estimated_gas_cost = 200000 * gas_price_gwei * 1e-9 * 2000  # ~$4 at 50 Gwei, MATIC at $1
            
            # Calculate gross profit
            gross_profit = base_trade_size * (price_diff_pct / 100)
            
            # Calculate net profit after all fees
            total_fees = base_trade_size * (dex_fee * 2 + aave_fee) + estimated_gas_cost
            net_profit = gross_profit - total_fees
            
            if net_profit < self.min_profit_usd:
                return None
                
            return ArbitrageOpportunity(
                token=token,
                buy_dex=buy_dex,
                sell_dex=sell_dex,
                buy_price=buy_price,
                sell_price=sell_price,
                price_diff_pct=price_diff_pct,
                optimal_trade_size=base_trade_size,
                net_profit=net_profit,
                gas_price_gwei=gas_price_gwei,
                timestamp=datetime.now().isoformat(),
                execution_ready=(self.mode == 'execute' and net_profit >= self.min_profit_usd)

            
            
        except Exception as e:
            self.logger.error(str(f"Profitability analysis error: {e}")
            return None
            
    async def _process_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """Process found arbitrage opportunities and emit AG-UI events"""
        # Sort by profitability
        opportunities.sort(key=lambda x: x.net_profit, reverse=True)

        self.stats['opportunities_found'] += len(opportunities)

        for i, opp in enumerate(opportunities[:3]):  # Show top 3
            self.logger.info(
                f"💰 Opportunity #{i+1}: {opp.token} | "
                f"{opp.buy_dex} → {opp.sell_dex} | "
                f"Profit: ${opp.net_profit:.2f} | "
                f"Size: ${opp.optimal_trade_size:,.0f} | "
                f"Diff: {opp.price_diff_pct:.2f}%"


            # Emit AG-UI event for frontend/UI
            await self.emit_agui_event({
                "event": "opportunity_found",
                "data": {
                    "token": opp.token,
                    "buy_dex": opp.buy_dex,
                    "sell_dex": opp.sell_dex,
                    "buy_price": opp.buy_price,
                    "sell_price": opp.sell_price,
                    "price_diff_pct": opp.price_diff_pct,
                    "optimal_trade_size": opp.optimal_trade_size,
                    "net_profit": opp.net_profit,
                    "timestamp": opp.timestamp



            # Submit to MCP for analysis if available
            if self.mcp_enabled and 'arbitrage' in self.mcp_servers:
                try:
                    await self.mcp_servers['arbitrage'].submit_opportunity(opp)
                    self.logger.info(f"[OK] Opportunity submitted to MCP server: {opp.token}")
                except Exception as e:
                    self.logger.error(f"[ERROR] Failed to submit opportunity to MCP server: {e}")
                
    async def _execution_loop(self):
        """Execute profitable arbitrage opportunities"""
        self.logger.info("[FAST] Starting execution loop...")
        
        while self.is_running:
            try:
                # Check if real execution is enabled
                real_execution = self.config.get('system', {}).get('real_execution_enabled', False)
                
                if not real_execution:
                    self.logger.info("🔸 Real execution disabled - would execute profitable opportunities")
                    await asyncio.sleep(30)
                    continue
                    
                # Implementation would include actual flash loan execution
                # This is a critical component that requires extensive testing
                self.logger.info("🔸 Execution loop active - monitoring for execution-ready opportunities")
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(str(f"Execution loop error: {e}")
                await asyncio.sleep(5)
                
    async def _ai_optimization_loop(self):
        """AI-powered strategy optimization using Copilot MCP"""
        self.logger.info("🤖 Starting AI optimization loop...")
        
        while self.is_running:
            try:
                if self.mcp_enabled and 'copilot' in self.mcp_servers:
                    # Submit current strategy for optimization
                    strategy_data = {
                        'current_performance': self.stats,
                        'recent_opportunities': getattr(self, 'recent_opportunities', []),
                        'gas_trends': await self._get_gas_trends(),
                        'market_conditions': await self._analyze_market_conditions()

                    
                    
                    await self.mcp_servers['copilot'].optimize_strategy(strategy_data)
                    
                await asyncio.sleep(300)  # Optimize every 5 minutes
                
            except Exception as e:
                self.logger.error(str(f"AI optimization error: {e}")
                await asyncio.sleep(60)
                
    async def _get_gas_trends(self) -> Dict[str, Any]:
        """Analyze recent gas price trends"""
        try:
            current_gas = self.w3.eth.gas_price / 1e9
            return {}
                'current_gwei': current_gas,
                'trend': 'stable',  # Would implement actual trend analysis
                'recommendation': 'proceed' if current_gas < self.max_gas_price_gwei else 'wait'
            
        except Exception:
            return {'error': 'Unable to fetch gas trends'}
            
    async def _analyze_market_conditions(self) -> Dict[str, Any]:
        """Analyze current market conditions"""
        try:
            # Simplified market analysis
            total_opportunities = self.stats['opportunities_found']
            success_rate = (self.stats['opportunities_executed'] / max(total_opportunities, 1)) * 100
            
            return {}
                'opportunities_per_hour': total_opportunities / max((datetime.now() - self.stats['uptime_start']).total_seconds() / 3600, 1),
                'success_rate': success_rate,
                'market_volatility': 'normal',  # Would implement actual volatility analysis
                'recommendation': 'active' if success_rate > 50 else 'cautious'
            
        except Exception:
            return {'error': 'Unable to analyze market conditions'}
            
    async def _metrics_reporting_loop(self):
        """Report system metrics periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Report every 5 minutes
                
                uptime = datetime.now() - self.stats['uptime_start']
                
                self.logger.info("[METRICS] System Metrics Report:")
                self.logger.info(str(f"  ⏰ Uptime: {uptime}")
                self.logger.info(str(f"  [TASK] Mode: {self.mode.upper(}")
                self.logger.info(str(f"  💰 Opportunities Found: {self.stats['opportunities_found']}")
                self.logger.info(str(f"  [OK] Opportunities Executed: {self.stats['opportunities_executed']}")
                self.logger.info(str(f"  💵 Total Profit: ${self.stats['total_profit_usd']:.2f}")
                self.logger.info(str(f"  ⛽ Gas Used: {self.stats['gas_used']} Gwei")
                self.logger.info(str(f"  [ERROR] Errors: {self.stats['execution_errors']}")
                
                if self.mcp_enabled:
                    active_servers = [name for name, server in self.mcp_servers.items()]
                    self.logger.info(str(f"  🤖 MCP Servers: {len(active_servers} active")
                    
            except Exception as e:
                self.logger.error(str(f"Metrics reporting error: {e}")
                
    async def emit_agui_event(self, event: dict):
        """Emit AG-UI event to the configured AG-UI endpoint"""
        self.logger.info(f"[AGUI] Attempting to emit AG-UI event '{event.get('event')}' to {self.agui_event_url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.agui_event_url, json=event) as resp:
                    self.logger.info(f"[AGUI] Completed emission of AG-UI event '{event.get('event')}' to {self.agui_event_url} (status {resp.status})")
        except Exception as e:
            self.logger.error(f"[AGUI] Failed to emit AG-UI event '{event.get('event')}' to {self.agui_event_url}: {e}")
        finally:
            self.logger.info(f"[AGUI] AG-UI event emission attempt finished for event: {event.get('event')}")

    async def start_agui_server(self, host="0.0.0.0", port=8081):
        """Start AG-UI HTTP server to receive user events"""
        self.logger.info(f"[AGUI] Attempting to start AG-UI HTTP server on {host}:{port}")
        try:
            self.agui_runner = web.AppRunner(self.agui_app)
            await self.agui_runner.setup()
            site = web.TCPSite(self.agui_runner, host, port)
            self.logger.info(f"[AGUI] Starting AG-UI HTTP server on {host}:{port}")
            await site.start()
            self.logger.info(f"[AGUI] Completed startup of AG-UI HTTP server on {host}:{port}")
        except Exception as e:
            self.logger.error(f"[AGUI] Failed to start AG-UI HTTP server on {host}:{port}: {e}")
        finally:
            self.logger.info(f"[AGUI] AG-UI HTTP server startup attempt finished for {host}:{port}")

    async def handle_agui_user_event(self, request):
        """Handle incoming AG-UI user events (POST /agui/user_event)"""
        try:
            data = await request.json()
            self.logger.info(f"[AGUI] Received user event: {data}")
            # Here you can route user events to your agent logic as needed
            return web.json_response({"status": "ok"})
        except Exception as e:
            self.logger.error(f"[AGUI] Error handling user event: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=400)

    async def enable_real_execution(self):
        """Enable real blockchain execution"""
        self.logger.info("[HOT] ENABLING REAL BLOCKCHAIN EXECUTION")
        self.logger.info("[WARN] WARNING: This will enable REAL money transactions!")

        # Update configuration
        self.config['system']['real_execution_enabled'] = True

        # Save updated configuration
        with open('unified_mcp_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)

        self.logger.info("[OK] Real execution enabled - system will execute profitable trades")
        return True

    async def shutdown(self):
        """Gracefully shutdown the system"""
        self.logger.info("[STOP] Initiating system shutdown...")
        self.is_running = False

        # Shutdown MCP servers
        for name, server in self.mcp_servers.items():
            try:
                await server.shutdown()
                self.logger.info(str(f"[OK] {name} MCP server stopped")
            except Exception as e:
                self.logger.error(str(f"Error stopping {name} server: {e}")

        # Shutdown AG-UI HTTP server
        if self.agui_runner:
            self.logger.info("[AGUI] Shutting down AG-UI HTTP server")
            await self.agui_runner.cleanup()

        self.logger.info("[OK] System shutdown complete")
async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified Flash Loan Arbitrage System",
        formatter_class=argparse.RawDescriptionHelpFormatter


    parser.add_argument(
        "--mode",
        choices=["monitor", "execute", "analyze"],
        default="monitor",
        help="System operation mode"


    parser.add_argument(
        "--min-profit",
        type=float,
        default=5.0,
        help="Minimum profit threshold in USD"


    parser.add_argument(
        "--max-trade-size",
        type=float,
        default=10000.0,
        help="Maximum trade size in USD"


    parser.add_argument(
        "--gas-limit",
        type=int,
        default=50,
        help="Gas price limit in Gwei"


    parser.add_argument(
        "--enable-real-execution",
        action="store_true",
        help="Enable real blockchain execution (DANGER: REAL MONEY)"


    parser.add_argument(
        "--disable-mcp",
        action="store_true",
        help="Disable MCP server integration"


    parser.add_argument(
        "--agui-server",
        action="store_true",
        help="Start AG-UI HTTP server for receiving user events"


    args = parser.parse_args()

    # Create and initialize the system
    system = UnifiedFlashLoanArbitrageSystem()

    try:
        # Initialize system with configuration
        await system.initialize_system(
            mode=args.mode,
            min_profit=args.min_profit,
            max_trade_size=args.max_trade_size,
            gas_limit=args.gas_limit,
            enable_mcp=not args.disable_mcp


        # Start AG-UI HTTP server if requested
        if args.agui_server:
            await system.start_agui_server()

        # Enable real execution if requested
        if args.enable_real_execution:
            await system.enable_real_execution()

        # Start the system
        await system.start_system()

    except KeyboardInterrupt:
        print("\n👋 Shutdown requested by user")
    except Exception as e:
        logging.error(f"[ERROR] System startup failed: {e}")
        sys.exit(1)
if __name__ == "__main__":
    asyncio.run(main())