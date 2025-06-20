#!/usr/bin/env python3
"""
Unified Price Fetcher
Combines advanced DEX price fetching capabilities with direct Web3 integration
Real-time price aggregation from multiple Polygon and Ethereum DEXes
"""

import platform
import asyncio
import logging
import aiohttp
import os
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from decimal import Decimal, getcontext
from dataclasses import dataclass
from web3 import Web3
import time
from datetime import datetime

# Setup Windows-compatible event loop FIRST
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Set high precision
getcontext().prec = 50

logger = logging.getLogger('UnifiedPriceFetcher')

@dataclass
class PriceData:
    price: Decimal
    liquidity: Decimal
    source: str
    timestamp: float
    confidence: float

@dataclass
class TokenInfo:
    symbol: str
    address: str
    decimals: int
    coingecko_id: str

@dataclass
class DEXInfo:
    name: str
    router_address: str
    factory_address: str
    chain_id: int
    enabled: bool = True
    fee_tier: float = 0.003

class UnifiedPriceFetcher:
    """
    Unified price fetcher combining:
    - Direct Web3 blockchain queries
    - The Graph subgraph integration
    - Multiple DEX support across chains
    - Real-time arbitrage detection
    """
    
    def __init__(self):
        self.setup_logging()
        self.load_environment()
        self.initialize_middleware()
        self.initialize_web3_connections()
        self.setup_token_contracts()
        self.setup_dex_contracts()
        
        self.session = None
        self.prices_cache = {}
        self.liquidity_cache = {}
        self.current_prices: Dict[str, Dict[str, Decimal]] = {}
        
        # DEX-specific configurations
        self.dex_configs = {
            'quickswap': {
                'subgraph': 'https://api.thegraph.com/subgraphs/name/sameepsi/quickswap06',
                'type': 'uniswap_v2'
            },
            'uniswap_v3': {
                'subgraph': 'https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon',
                'type': 'uniswap_v3'
            },
            'sushiswap': {
                'subgraph': 'https://api.thegraph.com/subgraphs/name/sushiswap/exchange-polygon',
                'type': 'uniswap_v2'
            }
        }
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def load_environment(self):
        """Load environment variables and RPC endpoints"""
        self.rpc_endpoints = {
            'ethereum': os.getenv('ETHEREUM_RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY'),
            'polygon': os.getenv('POLYGON_RPC_URL', 'https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY'),
            'arbitrum': os.getenv('ARBITRUM_RPC_URL', 'https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY'),
            'optimism': os.getenv('OPTIMISM_RPC_URL', 'https://opt-mainnet.g.alchemy.com/v2/YOUR_KEY')
        }
        
        # Fallback to public RPCs if not configured
        if 'YOUR_KEY' in self.rpc_endpoints['ethereum']:
            self.rpc_endpoints = {
                'ethereum': 'https://eth.llamarpc.com',
                'polygon': 'https://polygon.llamarpc.com',
                'arbitrum': 'https://arbitrum.llamarpc.com',
                'optimism': 'https://optimism.llamarpc.com'
            }
        
        logger.info("RPC endpoints configured")
        
    def initialize_middleware(self):
        """Initialize placeholder for geth_poa_middleware"""
        self._geth_poa_middleware_actual: Optional[Callable[..., Any]] = None
        try:
            from web3.middleware.geth_poa import geth_poa_middleware as _imported_middleware
            self._geth_poa_middleware_actual = _imported_middleware
        except ImportError:
            logger.info("web3.middleware.geth_poa.geth_poa_middleware not found. POA middleware will not be used.")
            
    def initialize_web3_connections(self):
        """Initialize Web3 connections to multiple chains"""
        self.web3_connections: Dict[str, Web3] = {}
        
        for chain, rpc_url in self.rpc_endpoints.items():
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # Add PoA middleware for some chains
                if chain in ['polygon'] and self._geth_poa_middleware_actual is not None:
                    w3.middleware_onion.inject(self._geth_poa_middleware_actual, layer=0)
                
                if w3.is_connected():
                    self.web3_connections[chain] = w3
                    logger.info(f"Connected to {chain} - Block: {w3.eth.block_number}")
                else:
                    logger.error(f"Failed to connect to {chain}")
                    
            except Exception as e:
                logger.error(f"Error connecting to {chain}: {e}")
        
        if not self.web3_connections:
            raise Exception("No Web3 connections established")
            
    def setup_token_contracts(self):
        """Setup token contract addresses and info for all tokens"""
        # Ethereum tokens
        self.tokens = {
            'WETH': TokenInfo('WETH', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 18, 'ethereum'),
            'USDC': TokenInfo('USDC', '0xA0b86a33E6B2aaBe1F3fc06d1d2F5e8b0B26C88c', 6, 'usd-coin'),
            'USDT': TokenInfo('USDT', '0xdAC17F958D2ee523a2206206994597C13D831ec7', 6, 'tether'),
            'DAI': TokenInfo('DAI', '0x6B175474E89094C44Da98b954EedeAC495271d0F', 18, 'dai'),
            'WBTC': TokenInfo('WBTC', '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 8, 'wrapped-bitcoin'),
            'LINK': TokenInfo('LINK', '0x514910771AF9Ca656af840dff83E8264EcF986CA', 18, 'chainlink'),
            'UNI': TokenInfo('UNI', '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 18, 'uniswap'),
            'AAVE': TokenInfo('AAVE', '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', 18, 'aave'),
            'CRV': TokenInfo('CRV', '0xD533a949740bb3306d119CC777fa900bA034cd52', 18, 'curve-dao-token'),
            'SUSHI': TokenInfo('SUSHI', '0x6B3595068778DD592e39A122f4f5a5cF09C90fE2', 18, 'sushi')
        }
        
        # Polygon token addresses
        self.polygon_tokens = {
            'WMATIC': TokenInfo('WMATIC', '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 18, 'matic-network'),
            'USDC': TokenInfo('USDC', '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 6, 'usd-coin'),
            'USDT': TokenInfo('USDT', '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 6, 'tether'),
            'WETH': TokenInfo('WETH', '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', 18, 'ethereum'),
            'WBTC': TokenInfo('WBTC', '0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6', 8, 'wrapped-bitcoin'),
            'DAI': TokenInfo('DAI', '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', 18, 'dai')
        }
        
        logger.info(f"Configured {len(self.tokens)} Ethereum tokens and {len(self.polygon_tokens)} Polygon tokens")
        
    def setup_dex_contracts(self):
        """Setup DEX contract addresses and info"""
        self.dexes = {
            'uniswap_v2': DEXInfo(
                'Uniswap V2',
                '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
                1
            ),
            'uniswap_v3': DEXInfo(
                'Uniswap V3',
                '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                '0x1F98431c8aD98523631AE4a59f267346ea31F984',
                1
            ),
            'sushiswap': DEXInfo(
                'SushiSwap',
                '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
                '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
                1
            ),
            'quickswap': DEXInfo(
                'QuickSwap',
                '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
                137
            ),
            'curve': DEXInfo(
                'Curve',
                '0xd51a44d3fae010294c616388b506acda1bfaae46',
                '0x0959158b6040d32d04c301a72cbfd6b39e21c9ae',
                1,
                enabled=False  # Placeholder for now
            ),
            'balancer': DEXInfo(
                'Balancer',
                '0xBA12222222228d8Ba445958a75a0704d566BF2C8',
                '0x0000000000000000000000000000000000000000',
                1,
                enabled=False  # Placeholder for now
            ),
            'dodo': DEXInfo(
                'DODO',
                '0x0000000000000000000000000000000000000000',
                '0x0000000000000000000000000000000000000000',
                1,
                enabled=False  # Placeholder for now
            )
        }
        
        logger.info(f"Configured {len(self.dexes)} DEXes")
        
    def load_abi(self, contract_type: str) -> List[Dict[str, Any]]:
        """Load ABI for different contract types"""
        abis_data: Dict[str, List[Dict[str, Any]]] = {
            'erc20': [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                }
            ],
            'uniswap_v2_pair': [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "getReserves",
                    "outputs": [
                        {"name": "_reserve0", "type": "uint112"},
                        {"name": "_reserve1", "type": "uint112"},
                        {"name": "_blockTimestampLast", "type": "uint32"}
                    ],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "token0",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "token1",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function"
                }
            ],
            'uniswap_v2_factory': [
                {
                    "constant": True,
                    "inputs": [
                        {"name": "tokenA", "type": "address"},
                        {"name": "tokenB", "type": "address"}
                    ],
                    "name": "getPair",
                    "outputs": [{"name": "pair", "type": "address"}],
                    "type": "function"
                }
            ]
        }
        return abis_data.get(contract_type, [])
        
    async def start(self):
        """Initialize the price fetcher"""
        if platform.system() == 'Windows':
            connector = aiohttp.TCPConnector(use_dns_cache=False, ssl=False)
            self.session = aiohttp.ClientSession(connector=connector)
        else:
            self.session = aiohttp.ClientSession()
        logger.info("Unified price fetcher started")
        
    async def stop(self):
        """Stop the price fetcher"""
        if self.session:
            await self.session.close()
            
    async def get_pair_address(self, dex_name: str, token0_addr: str, token1_addr: str, chain: str) -> Optional[str]:
        """Get pair address from DEX factory"""
        try:
            dex = self.dexes[dex_name]
            if not dex.enabled:
                return None
                
            w3 = self.web3_connections[chain]
            
            factory_abi = self.load_abi('uniswap_v2_factory')
            factory_contract = w3.eth.contract(
                address=Web3.to_checksum_address(dex.factory_address),
                abi=factory_abi
            )
            
            pair_address = factory_contract.functions.getPair(
                Web3.to_checksum_address(token0_addr),
                Web3.to_checksum_address(token1_addr)
            ).call()
            
            if pair_address == '0x0000000000000000000000000000000000000000':
                return None
                
            return pair_address
            
        except Exception as e:
            logger.debug(f"Error getting pair address for {dex_name}: {e}")
            return None
            
    async def get_pair_reserves(self, pair_address: str, chain: str) -> Tuple[int, int]:
        """Get reserves from a Uniswap V2 style pair"""
        try:
            w3 = self.web3_connections[chain]
            pair_abi = self.load_abi('uniswap_v2_pair')
            
            pair_contract = w3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=pair_abi
            )
            
            reserves = pair_contract.functions.getReserves().call()
            return reserves[0], reserves[1]
            
        except Exception as e:
            logger.debug(f"Error getting reserves from {pair_address}: {e}")
            return 0, 0
            
    def calculate_amm_price(self, amount_in: Decimal, reserve_in: Decimal, reserve_out: Decimal, fee_rate: Decimal) -> Decimal:
        """Calculate AMM price using constant product formula"""
        try:
            # Apply fee
            amount_in_with_fee = amount_in * (Decimal('1') - fee_rate)
            
            # Constant product formula: (x + dx) * (y - dy) = x * y
            # dy = (y * dx) / (x + dx)
            numerator = reserve_out * amount_in_with_fee
            denominator = reserve_in + amount_in_with_fee
            
            if denominator == 0:
                return Decimal('0')
            
            amount_out = numerator / denominator
            
            # Return price as output/input ratio
            return amount_out / amount_in if amount_in > 0 else Decimal('0')
            
        except Exception as e:
            logger.error(f"AMM price calculation error: {e}")
            return Decimal('0')
            
    async def calculate_price_from_reserves(
        self,
        reserve0: int,
        reserve1: int,
        decimals0: int,
        decimals1: int,
        token0_is_base: bool = True
    ) -> Decimal:
        """Calculate price from reserves"""
        try:
            if reserve0 == 0 or reserve1 == 0:
                return Decimal('0')
            
            # Adjust for decimals
            adjusted_reserve0 = Decimal(reserve0) / Decimal(10 ** decimals0)
            adjusted_reserve1 = Decimal(reserve1) / Decimal(10 ** decimals1)
            
            if token0_is_base:
                # Price of token0 in terms of token1
                price = adjusted_reserve1 / adjusted_reserve0
            else:
                # Price of token1 in terms of token0
                price = adjusted_reserve0 / adjusted_reserve1
            
            return price
            
        except Exception as e:
            logger.error(f"Error calculating price from reserves: {e}")
            return Decimal('0')
            
    async def get_dex_price(self, dex_name: str, token_a: str, token_b: str, amount: Decimal, chain: Optional[str] = None) -> Optional[PriceData]:
        """Get price from specific DEX with unified interface"""
        try:
            if dex_name not in self.dexes or not self.dexes[dex_name].enabled:
                return None
                
            # Determine chain if not provided
            if chain is None:
                chain = 'polygon' if dex_name == 'quickswap' else 'ethereum'
                
            # Get token addresses based on chain
            if chain == 'polygon':
                tokens = self.polygon_tokens
            else:
                tokens = self.tokens
                
            if token_a not in tokens or token_b not in tokens:
                return None
                
            token_a_info = tokens[token_a]
            token_b_info = tokens[token_b]
            
            # Use specific implementation based on DEX type
            if dex_name in ['uniswap_v2', 'sushiswap', 'quickswap']:
                return await self.get_uniswap_v2_style_price(dex_name, token_a_info, token_b_info, amount, chain)
            elif dex_name == 'uniswap_v3':
                return await self.get_uniswap_v3_price(token_a_info, token_b_info, amount, chain)
            else:
                logger.warning(f"Price fetching not implemented for {dex_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting price from {dex_name}: {e}")
            return None
            
    async def get_uniswap_v2_style_price(self, dex_name: str, token_a: TokenInfo, token_b: TokenInfo, amount: Decimal, chain: str) -> Optional[PriceData]:
        """Generic Uniswap V2 style price fetcher"""
        try:
            # Get pair address
            pair_address = await self.get_pair_address(dex_name, token_a.address, token_b.address, chain)
            if not pair_address:
                return None
                
            # Get reserves
            reserve0, reserve1 = await self.get_pair_reserves(pair_address, chain)
            if reserve0 == 0 or reserve1 == 0:
                return None
                
            # Determine token order
            w3 = self.web3_connections[chain]
            pair_abi = self.load_abi('uniswap_v2_pair')
            pair_contract = w3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=pair_abi
            )
            
            token0_addr = pair_contract.functions.token0().call()
            
            # Calculate price
            if token0_addr.lower() == token_a.address.lower():
                token_a_reserve = Decimal(reserve0)
                token_b_reserve = Decimal(reserve1)
            else:
                token_a_reserve = Decimal(reserve1)
                token_b_reserve = Decimal(reserve0)
                
            # Adjust for decimals
            token_a_reserve = token_a_reserve / (10 ** token_a.decimals)
            token_b_reserve = token_b_reserve / (10 ** token_b.decimals)
            
            if token_a_reserve == 0:
                return None
                
            # Calculate price with AMM formula
            fee_rate = Decimal(str(self.dexes[dex_name].fee_tier))
            price = self.calculate_amm_price(amount, token_a_reserve, token_b_reserve, fee_rate)
            
            return PriceData(
                price=price,
                liquidity=token_a_reserve,
                source=dex_name,
                timestamp=time.time(),
                confidence=min(0.95, float(token_a_reserve) / 10000)
            )
            
        except Exception as e:
            logger.debug(f"{dex_name} price fetch error: {e}")
            return None
            
    async def get_uniswap_v3_price(self, token_a: TokenInfo, token_b: TokenInfo, amount: Decimal, chain: str) -> Optional[PriceData]:
        """Get price from Uniswap V3 using The Graph"""
        try:
            if not self.session:
                return None
                
            query = """
            {
              pools(where: {
                token0_in: ["%s", "%s"],
                token1_in: ["%s", "%s"]
              }, orderBy: totalValueLockedUSD, orderDirection: desc, first: 3) {
                id
                token0 {
                  id
                  symbol
                  decimals
                }
                token1 {
                  id
                  symbol
                  decimals
                }
                liquidity
                sqrtPrice
                feeTier
                totalValueLockedUSD
              }
            }
            """ % (
                token_a.address.lower(),
                token_b.address.lower(),
                token_a.address.lower(),
                token_b.address.lower()
            )
            
            subgraph_url = self.dex_configs['uniswap_v3']['subgraph']
            
            timeout = aiohttp.ClientTimeout(total=5)
            async with self.session.post(
                subgraph_url,
                json={'query': query},
                timeout=timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('data', {}).get('pools', [])
                    
                    if pools:
                        # Use the pool with highest TVL
                        best_pool = pools[0]
                        
                        # Calculate price from sqrtPrice
                        sqrt_price = Decimal(best_pool['sqrtPrice'])
                        price = (sqrt_price / (2 ** 96)) ** 2
                        
                        # Adjust for token order and decimals
                        token0_addr = best_pool['token0']['id'].lower()
                        
                        if token0_addr != token_a.address.lower():
                            price = 1 / price
                            
                        # Adjust for decimals
                        token_a_decimals = int(best_pool['token0']['decimals']) if token0_addr == token_a.address.lower() else int(best_pool['token1']['decimals'])
                        token_b_decimals = int(best_pool['token1']['decimals']) if token0_addr == token_a.address.lower() else int(best_pool['token0']['decimals'])
                        
                        price = price * (10 ** (token_a_decimals - token_b_decimals))
                        
                        # Calculate output amount
                        fee_rate = Decimal(best_pool['feeTier']) / 1000000
                        output_amount = self.calculate_amm_price(amount, Decimal('1000000'), Decimal('1000000') * price, fee_rate)
                        
                        return PriceData(
                            price=output_amount / amount,
                            liquidity=Decimal(best_pool['totalValueLockedUSD']),
                            source='uniswap_v3',
                            timestamp=time.time(),
                            confidence=min(0.95, float(best_pool['totalValueLockedUSD']) / 100000)
                        )
            
            return None
            
        except Exception as e:
            logger.debug(f"Uniswap V3 price fetch error: {e}")
            return None
            
    async def get_all_prices(self, token_a: str, token_b: str, amount: Decimal) -> Dict[str, PriceData]:
        """Get prices from all available DEXes"""
        prices: Dict[str, PriceData] = {}
        
        # Parallel fetch from all DEXes
        tasks: List[Tuple[str, Any]] = []
        for dex_name, dex_info in self.dexes.items():
            if dex_info.enabled:
                chain = 'polygon' if dex_name == 'quickswap' else 'ethereum'
                task = self.get_dex_price(dex_name, token_a, token_b, amount, chain)
                tasks.append((dex_name, task))
        
        # Execute all tasks
        task_coroutines = [task for _, task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Process results
        for (dex_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.debug(f"Error fetching price from {dex_name}: {result}")
                continue
            
            if result and isinstance(result, PriceData):
                prices[dex_name] = result
        
        return prices
        
    async def get_best_prices(self, token_a: str, token_b: str, amount: Decimal) -> Tuple[Optional[PriceData], Optional[PriceData]]:
        """Get best buy and sell prices"""
        all_prices = await self.get_all_prices(token_a, token_b, amount)
        
        if not all_prices:
            return None, None
        
        # Sort by price for buy (lowest) and sell (highest)
        sorted_prices = sorted(all_prices.values(), key=lambda x: Any: Any: x.price)
        
        best_buy = sorted_prices[0] if sorted_prices else None
        best_sell = sorted_prices[-1] if sorted_prices else None
        
        return best_buy, best_sell
        
    async def fetch_all_prices(self) -> Dict[str, Dict[str, Decimal]]:
        """Fetch prices for all token pairs from all DEXes"""
        logger.info("Fetching live prices from all DEXes...")
        
        # Token pairs to monitor
        token_pairs = [
            ('WETH', 'USDC'), ('WETH', 'USDT'), ('WETH', 'DAI'),
            ('WBTC', 'WETH'), ('WBTC', 'USDC'),
            ('WMATIC', 'USDC'), ('WMATIC', 'USDT'),
            ('DAI', 'USDC'), ('USDT', 'USDC'),
            ('LINK', 'WETH'), ('UNI', 'WETH'),
            ('AAVE', 'WETH'), ('CRV', 'WETH'), ('SUSHI', 'WETH')
        ]
        
        prices: Dict[str, Dict[str, Decimal]] = {}
        
        # Fetch from each DEX
        for dex_name, dex_info in self.dexes.items():
            if not dex_info.enabled:
                continue
                
            chain = 'polygon' if dex_name == 'quickswap' else 'ethereum'
            if chain not in self.web3_connections:
                continue
                
            prices[dex_name] = {}
            
            # Fetch each token pair
            for token_a, token_b in token_pairs:
                try:
                    price_data = await self.get_dex_price(dex_name, token_a, token_b, Decimal('1'), chain)
                    if price_data and price_data.price > 0:
                        pair_key = f"{token_a}/{token_b}"
                        prices[dex_name][pair_key] = price_data.price
                        
                except Exception as e:
                    logger.error(f"Error fetching {token_a}/{token_b} from {dex_name}: {e}")
                    continue
            
            logger.info(f"Fetched {len(prices[dex_name])} prices from {dex_name}")
        
        self.current_prices = prices
        return prices
        
    async def get_real_time_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """Find real arbitrage opportunities using live on-chain data"""
        await self.fetch_all_prices()
        
        opportunities = []
        
        # Check each token pair across all DEXes
        all_pairs: Set[str] = set()
        for dex_prices in self.current_prices.values():
            all_pairs.update(dex_prices.keys())
        
        for pair in all_pairs:
            dex_prices_for_pair: Dict[str, Decimal] = {}
            
            # Collect prices from all DEXes for this pair
            for dex_name, dex_prices in self.current_prices.items():
                if pair in dex_prices and dex_prices[pair] > 0:
                    dex_prices_for_pair[dex_name] = dex_prices[pair]
            
            if len(dex_prices_for_pair) < 2:
                continue
            
            # Find arbitrage opportunity
            min_dex = min(dex_prices_for_pair, key=lambda k: Any: dex_prices_for_pair[k])
            max_dex = max(dex_prices_for_pair, key=lambda k: Any: dex_prices_for_pair[k])
            
            buy_price = dex_prices_for_pair[min_dex]
            sell_price = dex_prices_for_pair[max_dex]
            
            if buy_price == Decimal('0'):
                continue
                
            price_diff = sell_price - buy_price
            profit_percentage = (price_diff / buy_price) * Decimal('100')
            
            # Filter significant opportunities (>0.1%)
            if profit_percentage > Decimal('0.1'):
                opportunity = {
                    'pair': pair,
                    'buy_dex': min_dex,
                    'sell_dex': max_dex,
                    'buy_price': float(buy_price),
                    'sell_price': float(sell_price),
                    'profit_percentage': float(profit_percentage),
                    'timestamp': datetime.now().isoformat()
                }
                opportunities.append(opportunity)
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: Any: Any: x['profit_percentage'], reverse=True)
        
        logger.info(f"Found {len(opportunities)} real arbitrage opportunities")
        return opportunities
        
    def get_latest_prices(self) -> Dict[str, Dict[str, Decimal]]:
        """Get the latest fetched prices"""
        return self.current_prices

async def main():
    """Test the unified price fetcher"""
    print("Unified Price Fetcher - Combined DEX Data")
    print("=" * 50)
    
    fetcher = UnifiedPriceFetcher()
    await fetcher.start()
    
    try:
        # Test individual price fetch
        print("\nTesting individual price fetch...")
        price_data = await fetcher.get_dex_price('quickswap', 'WMATIC', 'USDC', Decimal('1'))
        if price_data:
            print(f"QuickSwap WMATIC/USDC: ${price_data.price:.6f}")
            print(f"Liquidity: {price_data.liquidity}, Confidence: {price_data.confidence:.2f}")
        
        # Test best prices
        print("\nTesting best price comparison...")
        best_buy, best_sell = await fetcher.get_best_prices('WETH', 'USDC', Decimal('1'))
        if best_buy and best_sell:
            print(f"Best buy: {best_buy.source} @ ${best_buy.price:.6f}")
            print(f"Best sell: {best_sell.source} @ ${best_sell.price:.6f}")
            
        # Find arbitrage opportunities
        print("\nSearching for arbitrage opportunities...")
        opportunities = await fetcher.get_real_time_arbitrage_opportunities()
        
        print(f"\nFound {len(opportunities)} arbitrage opportunities:")
        for i, opp in enumerate(opportunities[:3]):  # Top 3
            print(f"{i+1}. {opp['pair']}: {opp['profit_percentage']:.3f}% profit")
            print(f"   Buy: {opp['buy_dex']} @ ${opp['buy_price']:.6f}")
            print(f"   Sell: {opp['sell_dex']} @ ${opp['sell_price']:.6f}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await fetcher.stop()

if __name__ == "__main__":
    asyncio.run(main())
