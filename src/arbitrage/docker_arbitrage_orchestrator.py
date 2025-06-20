#!/usr/bin/env python3
"""
24/7 Flash Loan Arbitrage System - Docker Edition
=================================================

Orchestrates real-time arbitrage operations using Docker-based MCP servers and AI agents.
Implements profit range filtering, real-time price monitoring, and agentic coordination.
"""

import asyncio
import aiohttp
import json
import logging
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from web3 import Web3
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('docker_arbitrage_24_7.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DockerArbitrageOrchestrator:
    """24/7 Arbitrage orchestrator using Docker-based MCP services"""
    
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.system_start_time = datetime.now()
        
        # Configuration
        self.contract_address = os.getenv('CONTRACT_ADDRESS', '0x35791D283Ec6eeF6C7687026CaF026C5F84C7c15')
        self.private_key = os.getenv('ARBITRAGE_PRIVATE_KEY')
        self.rpc_url = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
        self.min_profit_usd = float(os.getenv('MIN_PROFIT_USD', '3.0'))
        self.max_profit_usd = float(os.getenv('MAX_PROFIT_USD', '30.0'))
        self.max_gas_price_gwei = float(os.getenv('MAX_GAS_PRICE_GWEI', '50.0'))
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Docker MCP Services - Using actual running containers (aligned with user's setup of 21 servers)
        self.mcp_services = {
            'flash_loan': 'http://localhost:8085',      # mcp_flash_loan_server
            'price_feed': 'http://localhost:8091',      # mcp_price_feed_server
            'arbitrage': 'http://localhost:8073',       # mcp_arbitrage_server
            'blockchain': 'http://localhost:8075',      # mcp_blockchain_server
            'defi_analyzer': 'http://localhost:8081',   # mcp_defi_analyzer_server
            'liquidity': 'http://localhost:8087',       # mcp_liquidity_server
            'risk_manager': 'http://localhost:8094',    # mcp_risk_manager_server
            'monitoring': 'http://localhost:8088',      # mcp_monitoring_server
            'coordinator': 'http://localhost:8077',     # mcp_coordinator_server
            'data_analyzer': 'http://localhost:8080',   # mcp_data_analyzer_server
            'evm': 'http://localhost:8065',             # evm_mcp_server
            'foundry': 'http://localhost:8068',         # foundry_mcp_mcp_server
            'copilot': 'http://localhost:8059',         # copilot_mcp_mcp_server
            'dex_aggregator': 'http://localhost:8062',  # dex_aggregator_mcp_server
            'portfolio': 'http://localhost:8090',       # mcp_portfolio_server
            'security': 'http://localhost:8095',        # mcp_security_server
            'notification': 'http://localhost:8089',    # mcp_notification_server
            'task_queue': 'http://localhost:8102',      # mcp_task_queue_server
            'database': 'http://localhost:8079',        # mcp_database_server
            'integration_bridge': 'http://localhost:8086', # mcp_integration_bridge
            'profit_optimizer': 'http://localhost:8108' # profit_optimizer_mcp_server
        }
        
        # AI Agents - Using actual running containers (aligned with user's setup of 10 agents)
        self.ai_agents = {
            'flash_loan_optimizer': 'http://localhost:9001', # flash_loan_optimizer
            'risk_manager': 'http://localhost:9002',         # risk_manager
            'arbitrage_detector': 'http://localhost:9003',   # arbitrage_detector
            'transaction_executor': 'http://localhost:9004', # transaction_executor
            'market_analyzer': 'http://localhost:8201',      # flashloan-agent-analyzer (mapped)
            'data_collector': 'http://localhost:8205',       # flashloan-agent-data-collector
            'arbitrage_bot': 'http://localhost:8206',        # flashloan-agent-arbitrage-bot
            'liquidity_manager': 'http://localhost:8207',    # flashloan-agent-liquidity-manager
            'reporter': 'http://localhost:8208',             # flashloan-agent-reporter
            'healer': 'http://localhost:8209',               # flashloan-agent-healer
        }
        
        # Supported tokens on Polygon
        self.tokens = {
            'WMATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
            'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
            'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
            'WBTC': '0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6',
            'LINK': '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39',
            'UNI': '0xb33EaAd8d922B1083446DC23f610c2567fB5180f',
            'AAVE': '0xD6DF932A45C0f255f85145f286eA0b292B21C90B',
            'CRV': '0x172370d5Cd63279eFa6d502DAB29171933a610AF',
            'BAL': '0x9a71012B13CA4d3D0Cdc72A177DF3ef03b0E76A3',
            'SUSHI': '0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a',
            'COMP': '0x8505b9d2254A7Ae468c0E9dd10Ccea3A837aef5c',
            'MKR': '0x6f7C932e7684666C9fd1d44527765433e01fF61d',
            'SNX': '0x50B728D8D964fd00C2d0AAD81718b71311feF68a'
        }
        
        # DEX configurations
        self.dexs = {
            'QuickSwap': {
                'factory': '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
                'router': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff'
            },
            'SushiSwap': {
                'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
            },
            'UniswapV3': {
                'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
                'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564'
            },
            'Balancer': {
                'vault': '0xBA12222222228d8Ba445958a75a0704d566BF2C8'
            },
            'Curve': {
                'registry': '0x47bB542B9dE58b970bA50c9dae444DDB4c16751a'
            }
        }
        
        # Statistics
        self.stats = {
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit_usd': 0.0,
            'total_gas_spent': 0.0,
            'uptime_hours': 0.0,
            'last_opportunity': None,
            'last_execution': None,
            'health_checks': 0,
            'errors': 0
        }
        
        # Load Aave pool ABI
        self.aave_pool_abi = self._load_aave_abi()
        
    def _load_aave_abi(self) -> List[Dict]:
        """Load Aave pool ABI"""
        try:
            with open('abi/aave_pool.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Aave ABI: {e}")
            return []
    
    async def start_system(self):
        """Start the complete 24/7 arbitrage system"""
        logger.info("🚀 Starting Docker-based 24/7 Flash Loan Arbitrage System")
        logger.info("=" * 80)
        
        try:
            # Initialize system components
            await self._initialize_system()
            
            # Start main orchestration loop
            await self._run_orchestration_loop()
            
        except KeyboardInterrupt:
            logger.info("👋 Shutdown signal received")
            await self._shutdown_system()
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            await self._handle_system_error(e)
    
    async def _initialize_system(self):
        """Initialize all system components"""
        logger.info("🔄 Initializing system components...")
        
        # Check Web3 connection
        if not self.w3.is_connected():
            raise Exception("❌ Failed to connect to Polygon network")
        
        current_block = self.w3.eth.block_number
        logger.info(f"✅ Connected to Polygon (Block: {current_block})")
        
        # Verify contract deployment
        contract_code = self.w3.eth.get_code(self.contract_address)
        if contract_code == '0x':
            raise Exception(f"❌ No contract found at {self.contract_address}")
        
        logger.info(f"✅ Flash loan contract verified at {self.contract_address}")
        
        # Check Docker services
        await self._check_docker_services()
        
        # Initialize AI agents
        await self._initialize_ai_agents()
        
        # Start health monitoring
        asyncio.create_task(self._health_monitoring_loop())
        
        logger.info("✅ System initialization complete")
    
    async def _check_docker_services(self):
        """Check status of Docker-based MCP services"""
        logger.info("🔄 Checking Docker MCP services...")
        
        active_services = []
        inactive_services = []
        
        # Check MCP services
        for name, url in self.mcp_services.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health", timeout=3) as response:
                        if response.status == 200:
                            active_services.append(f"MCP-{name}")
                        else:
                            inactive_services.append(f"MCP-{name}")
            except Exception:
                inactive_services.append(f"MCP-{name}")
        
        # Check AI agents
        for name, url in self.ai_agents.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health", timeout=3) as response:
                        if response.status == 200:
                            active_services.append(f"Agent-{name}")
                        else:
                            inactive_services.append(f"Agent-{name}")
            except Exception:
                inactive_services.append(f"Agent-{name}")
        
        logger.info(f"✅ {len(active_services)} services active: {', '.join(active_services[:5])}{'...' if len(active_services) > 5 else ''}")
        
        if inactive_services:
            logger.warning(f"⚠️ {len(inactive_services)} services inactive: {', '.join(inactive_services[:3])}{'...' if len(inactive_services) > 3 else ''}")
    
    async def _initialize_ai_agents(self):
        """Initialize AI agents with system parameters"""
        logger.info("🤖 Initializing AI agents...")
        
        init_config = {
            'contract_address': self.contract_address,
            'tokens': self.tokens,
            'dexs': self.dexs,
            'min_profit_usd': self.min_profit_usd,
            'max_profit_usd': self.max_profit_usd,
            'max_gas_price_gwei': self.max_gas_price_gwei
        }
        
        for name, url in self.ai_agents.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{url}/initialize", 
                                          json=init_config, 
                                          timeout=10) as response:
                        if response.status == 200:
                            logger.debug(f"✅ {name} agent initialized")
                        else:
                            logger.warning(f"⚠️ {name} agent initialization failed")
            except Exception as e:
                logger.warning(f"⚠️ {name} agent unreachable: {e}")
    
    async def _run_orchestration_loop(self):
        """Main orchestration loop for 24/7 operation"""
        logger.info("🎯 Starting main orchestration loop...")
        self.is_running = True
        
        # Start concurrent tasks
        tasks = [
            asyncio.create_task(self._price_monitoring_loop()),
            asyncio.create_task(self._opportunity_detection_loop()),
            asyncio.create_task(self._execution_coordination_loop()),
            asyncio.create_task(self._statistics_reporting_loop()),
            asyncio.create_task(self._admin_control_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"❌ Orchestration error: {e}")
            self.is_running = False
    
    async def _price_monitoring_loop(self):
        """Continuous price monitoring from multiple sources"""
        logger.info("📊 Starting price monitoring...")
        
        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(10)
                    continue
                
                # Get current gas price
                gas_price_gwei = self.w3.eth.gas_price / 1e9
                
                if gas_price_gwei > self.max_gas_price_gwei:
                    logger.warning(f"⛽ High gas price: {gas_price_gwei:.1f} Gwei (max: {self.max_gas_price_gwei})")
                    await asyncio.sleep(30)
                    continue
                
                # Request price updates from price feed MCP
                await self._request_price_updates()
                
                # Update DEX liquidity data
                await self._update_liquidity_data()
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Price monitoring error: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(10)
    
    async def _request_price_updates(self):
        """Request price updates from MCP price feed service"""
        try:
            price_feed_url = self.mcp_services['price_feed']
            
            request_data = {
                'tokens': list(self.tokens.keys()),
                'dexs': list(self.dexs.keys()),
                'include_liquidity': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{price_feed_url}/get_prices", 
                                      json=request_data, 
                                      timeout=10) as response:
                    if response.status == 200:
                        price_data = await response.json()
                        logger.debug(f"📊 Price data updated: {len(price_data.get('prices', {}))} tokens")
                        return price_data
                    else:
                        logger.warning(f"⚠️ Price feed service error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Price request error: {e}")
        
        return None
    
    async def _update_liquidity_data(self):
        """Update liquidity data from DEXs and Aave"""
        try:
            liquidity_url = self.mcp_services['liquidity']
            
            request_data = {
                'tokens': list(self.tokens.keys()),
                'dexs': list(self.dexs.keys()),
                'check_aave': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{liquidity_url}/check_liquidity", 
                                      json=request_data, 
                                      timeout=15) as response:
                    if response.status == 200:
                        liquidity_data = await response.json()
                        logger.debug(f"💧 Liquidity data updated: {len(liquidity_data.get('pools', {}))} pools")
                        return liquidity_data
                        
        except Exception as e:
            logger.error(f"Liquidity update error: {e}")
        
        return None
    
    async def _opportunity_detection_loop(self):
        """Detect arbitrage opportunities using AI agents"""
        logger.info("🔍 Starting opportunity detection...")
        
        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(10)
                    continue
                
                # Request opportunity analysis from arbitrage MCP
                opportunities = await self._detect_opportunities()
                
                if opportunities:
                    self.stats['opportunities_found'] += len(opportunities)
                    logger.info(f"💰 Found {len(opportunities)} arbitrage opportunities")
                    
                    # Filter opportunities by profit range
                    filtered_ops = await self._filter_opportunities(opportunities)
                    
                    if filtered_ops:
                        logger.info(f"✅ {len(filtered_ops)} opportunities within profit range ${self.min_profit_usd}-${self.max_profit_usd}")
                        
                        # Send to execution queue
                        await self._queue_opportunities(filtered_ops)
                
                await asyncio.sleep(3)  # Check every 3 seconds
                
            except Exception as e:
                logger.error(f"Opportunity detection error: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(10)
    
    async def _detect_opportunities(self) -> List[Dict]:
        """Detect arbitrage opportunities using MCP arbitrage service"""
        try:
            arbitrage_url = self.mcp_services['arbitrage']
            
            request_data = {
                'tokens': list(self.tokens.keys()),
                'dexs': list(self.dexs.keys()),
                'min_profit_usd': self.min_profit_usd,
                'max_profit_usd': self.max_profit_usd,
                'include_fees': True,
                'check_liquidity': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{arbitrage_url}/scan_opportunities", 
                                      json=request_data, 
                                      timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('opportunities', [])
                        
        except Exception as e:
            logger.error(f"Opportunity detection error: {e}")
        
        return []
    
    async def _filter_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Filter opportunities by profit range and validation"""
        filtered = []
        
        for opp in opportunities:
            try:
                profit_usd = float(opp.get('estimated_profit_usd', 0))
                
                # Check profit range
                if not (self.min_profit_usd <= profit_usd <= self.max_profit_usd):
                    continue
                
                # Additional validation through risk manager
                if await self._validate_opportunity(opp):
                    filtered.append(opp)
                    
            except Exception as e:
                logger.error(f"Opportunity filtering error: {e}")
        
        return filtered
    
    async def _validate_opportunity(self, opportunity: Dict) -> bool:
        """Validate opportunity through risk manager agent"""
        try:
            risk_manager_url = self.ai_agents['risk_manager']
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{risk_manager_url}/validate_opportunity", 
                                      json=opportunity, 
                                      timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('is_valid', False)
                        
        except Exception as e:
            logger.error(f"Opportunity validation error: {e}")
        
        return False
    
    async def _queue_opportunities(self, opportunities: List[Dict]):
        """Queue opportunities for execution"""
        try:
            executor_url = self.ai_agents['executor']
            
            request_data = {
                'opportunities': opportunities,
                'contract_address': self.contract_address,
                'execution_mode': 'production'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{executor_url}/queue_opportunities", 
                                      json=request_data, 
                                      timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"📤 Queued {result.get('queued_count', 0)} opportunities for execution")
                        
        except Exception as e:
            logger.error(f"Opportunity queueing error: {e}")
    
    async def _execution_coordination_loop(self):
        """Coordinate execution of arbitrage opportunities"""
        logger.info("⚡ Starting execution coordination...")
        
        while self.is_running:
            try:
                if self.is_paused:
                    await asyncio.sleep(10)
                    continue
                
                # Check execution queue
                await self._process_execution_queue()
                
                await asyncio.sleep(2)  # Process every 2 seconds
                
            except Exception as e:
                logger.error(f"Execution coordination error: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(10)
    
    async def _process_execution_queue(self):
        """Process pending executions"""
        try:
            executor_url = self.ai_agents['executor']
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{executor_url}/process_queue", timeout=20) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('executions_processed', 0) > 0:
                            processed = result['executions_processed']
                            successful = result.get('successful_executions', 0)
                            failed = result.get('failed_executions', 0)
                            
                            self.stats['opportunities_executed'] += processed
                            self.stats['successful_trades'] += successful
                            self.stats['failed_trades'] += failed
                            
                            if successful > 0:
                                profit_usd = result.get('total_profit_usd', 0)
                                self.stats['total_profit_usd'] += profit_usd
                                self.stats['last_execution'] = datetime.now()
                                
                                logger.info(f"✅ Executed {successful} trades, Profit: ${profit_usd:.2f}")
                            
                            if failed > 0:
                                logger.warning(f"❌ {failed} executions failed")
                        
        except Exception as e:
            logger.error(f"Execution processing error: {e}")
    
    async def _statistics_reporting_loop(self):
        """Report system statistics periodically"""
        logger.info("📈 Starting statistics reporting...")
        
        while self.is_running:
            try:
                # Calculate uptime
                uptime = datetime.now() - self.system_start_time
                self.stats['uptime_hours'] = uptime.total_seconds() / 3600
                
                # Report every 5 minutes
                if int(time.time()) % 300 == 0:
                    await self._report_statistics()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Statistics reporting error: {e}")
                await asyncio.sleep(60)
    
    async def _report_statistics(self):
        """Report current system statistics"""
        try:
            logger.info("📊 SYSTEM STATISTICS")
            logger.info("=" * 50)
            logger.info(f"⏱️  Uptime: {self.stats['uptime_hours']:.1f} hours")
            logger.info(f"🔍 Opportunities Found: {self.stats['opportunities_found']}")
            logger.info(f"⚡ Opportunities Executed: {self.stats['opportunities_executed']}")
            logger.info(f"✅ Successful Trades: {self.stats['successful_trades']}")
            logger.info(f"❌ Failed Trades: {self.stats['failed_trades']}")
            logger.info(f"💰 Total Profit: ${self.stats['total_profit_usd']:.2f}")
            logger.info(f"⚠️  Errors: {self.stats['errors']}")
            
            success_rate = 0
            if self.stats['opportunities_executed'] > 0:
                success_rate = (self.stats['successful_trades'] / self.stats['opportunities_executed']) * 100
            logger.info(f"📈 Success Rate: {success_rate:.1f}%")
            
            # Send to reporter agent
            await self._send_statistics_to_reporter()
            
        except Exception as e:
            logger.error(f"Statistics reporting error: {e}")
    
    async def _send_statistics_to_reporter(self):
        """Send statistics to reporter agent"""
        try:
            reporter_url = self.ai_agents['reporter']
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{reporter_url}/update_statistics", 
                                      json=self.stats, 
                                      timeout=10) as response:
                    if response.status == 200:
                        logger.debug("📊 Statistics sent to reporter")
                        
        except Exception as e:
            logger.error(f"Reporter communication error: {e}")
    
    async def _admin_control_loop(self):
        """Handle admin controls (pause/resume/shutdown)"""
        logger.info("👤 Admin control interface active")
        
        while self.is_running:
            try:
                # Check for control commands via file system
                await self._check_admin_commands()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Admin control error: {e}")
                await asyncio.sleep(10)
    
    async def _check_admin_commands(self):
        """Check for admin command files"""
        try:
            # Check for pause command
            if os.path.exists('PAUSE_ARBITRAGE'):
                if not self.is_paused:
                    self.is_paused = True
                    logger.warning("⏸️  SYSTEM PAUSED by admin command")
                os.remove('PAUSE_ARBITRAGE')
            
            # Check for resume command
            if os.path.exists('RESUME_ARBITRAGE'):
                if self.is_paused:
                    self.is_paused = False
                    logger.info("▶️  SYSTEM RESUMED by admin command")
                os.remove('RESUME_ARBITRAGE')
            
            # Check for shutdown command
            if os.path.exists('SHUTDOWN_ARBITRAGE'):
                logger.warning("🛑 SHUTDOWN commanded by admin")
                os.remove('SHUTDOWN_ARBITRAGE')
                self.is_running = False
                
        except Exception as e:
            logger.error(f"Admin command check error: {e}")
    
    async def _health_monitoring_loop(self):
        """Monitor system health and auto-heal"""
        logger.info("🏥 Health monitoring active")
        
        while self.is_running:
            try:
                self.stats['health_checks'] += 1
                
                # Check critical services
                critical_services = ['flash_loan', 'arbitrage', 'price_feed']
                unhealthy_services = []
                
                for service in critical_services:
                    if not await self._check_service_health(service):
                        unhealthy_services.append(service)
                
                if unhealthy_services:
                    logger.warning(f"🚨 Unhealthy services: {', '.join(unhealthy_services)}")
                    await self._trigger_healing(unhealthy_services)
                
                await asyncio.sleep(30)  # Health check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            if service_name in self.mcp_services:
                url = self.mcp_services[service_name]
            elif service_name in self.ai_agents:
                url = self.ai_agents[service_name]
            else:
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=5) as response:
                    return response.status == 200
                    
        except Exception:
            return False
    
    async def _trigger_healing(self, unhealthy_services: List[str]):
        """Trigger healing for unhealthy services"""
        try:
            healer_url = self.ai_agents['healer']
            
            request_data = {
                'unhealthy_services': unhealthy_services,
                'action': 'restart_services'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{healer_url}/heal_services", 
                                      json=request_data, 
                                      timeout=30) as response:
                    if response.status == 200:
                        logger.info(f"🏥 Healing triggered for {len(unhealthy_services)} services")
                        
        except Exception as e:
            logger.error(f"Healing trigger error: {e}")
    
    async def _handle_system_error(self, error: Exception):
        """Handle system-wide errors"""
        logger.error(f"🚨 SYSTEM ERROR: {error}")
        self.stats['errors'] += 1
        
        # Try to gracefully shutdown
        await self._shutdown_system()
    
    async def _shutdown_system(self):
        """Gracefully shutdown the system"""
        logger.info("🛑 Shutting down arbitrage system...")
        self.is_running = False
        
        # Send shutdown signal to all agents
        for name, url in self.ai_agents.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{url}/shutdown", timeout=5) as response:
                        if response.status == 200:
                            logger.debug(f"✅ {name} agent shutdown")
            except Exception:
                pass
        
        # Final statistics report
        await self._report_statistics()
        logger.info("✅ System shutdown complete")


# Admin control commands
async def pause_system():
    """Create pause command file"""
    with open('PAUSE_ARBITRAGE', 'w') as f:
        f.write(f"PAUSED at {datetime.now()}")
    print("⏸️  Pause command sent")

async def resume_system():
    """Create resume command file"""
    with open('RESUME_ARBITRAGE', 'w') as f:
        f.write(f"RESUMED at {datetime.now()}")
    print("▶️  Resume command sent")

async def shutdown_system():
    """Create shutdown command file"""
    with open('SHUTDOWN_ARBITRAGE', 'w') as f:
        f.write(f"SHUTDOWN at {datetime.now()}")
    print("🛑 Shutdown command sent")


async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'pause':
            await pause_system()
            return
        elif command == 'resume':
            await resume_system()
            return
        elif command == 'shutdown':
            await shutdown_system()
            return
        elif command == 'status':
            print("📊 Checking system status...")
            # Could add status check here
            return
    
    # Start the orchestrator
    orchestrator = DockerArbitrageOrchestrator()
    await orchestrator.start_system()


if __name__ == "__main__":
    asyncio.run(main())
