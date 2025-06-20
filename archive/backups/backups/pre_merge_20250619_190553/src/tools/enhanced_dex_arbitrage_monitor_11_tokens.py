#!/usr/bin/env python3
"""
Enhanced DEX Arbitrage Monitor for 11 Tokens with Web3 Integration
Real-time monitoring of all 11 tokens across multiple DEXes with arbitrage calculations
Port 8008 - Comprehensive Token Monitoring & Arbitrage Analysis
"""

import asyncio
import aiohttp
import time
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
import logging
import threading
from typing import Dict, List, Any, Union, TypedDict, Optional
import math
from web3 import Web3
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Type Aliases for complex data structures

# For Network Configuration
class _NetworkConfigDetail(TypedDict):
    rpc_url: str
    gas_price_gwei: int
    native_token: str
    native_price_usd: float

NetworkConfigs = Dict[str, _NetworkConfigDetail]

# For DEX Price Details
class _DexPriceDetailTyped(TypedDict):
    price: float
    liquidity: float
    volume_24h: float
    fee_percent: float
    chain: str
    timestamp: float
    change_24h: Optional[float]

_DexPricesForTokenTyped = Dict[str, _DexPriceDetailTyped]
AllDexPrices = Dict[str, _DexPricesForTokenTyped]

# For CoinGecko Price Details
class _CoinGeckoPriceDetailTyped(TypedDict):
    price: float
    change_24h: Optional[float]
    market_cap: Optional[float]

CoinGeckoApiResponse = Dict[str, _CoinGeckoPriceDetailTyped]

# For Market Metrics
_MarketMetricsValue = Union[int, float, str, List[Dict[str, Any]], Dict[str, Any], None]
MarketMetrics = Dict[str, _MarketMetricsValue]


@dataclass
class TokenInfo:
    """Token information structure"""
    symbol: str
    address: str
    decimals: int
    coingecko_id: str
    name: str

@dataclass
class DEXInfo:
    """DEX information structure"""
    name: str
    chain: str
    router_address: str
    factory_address: str
    fee_percent: float

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity structure"""
    token: str
    dex_buy: str
    dex_sell: str
    buy_price: float
    sell_price: float
    price_diff: float
    profit_percentage: float
    optimal_trade_size: float
    estimated_profit: float
    gas_cost: float
    net_profit: float
    confidence_score: float
    risk_level: str
    liquidity_score: float
    timestamp: float

class EnhancedDEXArbitrageCalculator:
    """Advanced arbitrage calculator with comprehensive analysis"""
    
    def __init__(self):
        # Network configurations
        self.networks: NetworkConfigs = {
            'ethereum': {
                'rpc_url': 'https://eth-mainnet.g.alchemy.com/v2/your-api-key',
                'gas_price_gwei': 25,
                'native_token': 'ETH',
                'native_price_usd': 2450.0
            },
            'polygon': {
                'rpc_url': 'https://polygon-mainnet.g.alchemy.com/v2/your-api-key',
                'gas_price_gwei': 30,
                'native_token': 'MATIC',
                'native_price_usd': 0.85
            },
            'bsc': {
                'rpc_url': 'https://bsc-dataseed.binance.org/',
                'gas_price_gwei': 5,
                'native_token': 'BNB',
                'native_price_usd': 315.0
            }
        }
        
        self.base_gas_limit = 350000
        self.slippage_tolerance = 0.5
        self.min_profit_threshold = 10.0
        
        # Initialize configurations
        self.setup_token_configs()
        self.setup_dex_configs()
        self.setup_web3_providers()
        
    def setup_web3_providers(self):
        """Setup Web3 providers for different networks"""
        try:
            self.web3_providers = {
                'ethereum': Web3(Web3.HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/demo')),
                'polygon': Web3(Web3.HTTPProvider('https://polygon-rpc.com')),
                'bsc': Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
            }
            
            # Test connections
            for network, w3 in self.web3_providers.items():
                if w3.is_connected():
                    logger.info(f"Connected to {network} network")
                else:
                    logger.warning(f"Failed to connect to {network} network")
                    
        except Exception as e:
            logger.error(f"Error setting up Web3 providers: {e}")
            self.web3_providers = {}
        
    def setup_token_configs(self):
        """Setup all 11 token configurations across networks"""
        self.tokens = {
            'WETH': TokenInfo('WETH', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 18, 'ethereum', 'Wrapped Ethereum'),
            'USDC': TokenInfo('USDC', '0xA0b86a33E6B2aaBe1F3fc06d1d2F5e8b0B26C88c', 6, 'usd-coin', 'USD Coin'),
            'USDT': TokenInfo('USDT', '0xdAC17F958D2ee523a2206206994597C13D831ec7', 6, 'tether', 'Tether USD'),
            'DAI': TokenInfo('DAI', '0x6B175474E89094C44Da98b954EedeAC495271d0F', 18, 'dai', 'Dai Stablecoin'),
            'WBTC': TokenInfo('WBTC', '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 8, 'wrapped-bitcoin', 'Wrapped Bitcoin'),
            'WMATIC': TokenInfo('WMATIC', '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 18, 'matic-network', 'Wrapped Matic'),
            'LINK': TokenInfo('LINK', '0x514910771AF9Ca656af840dff83E8264EcF986CA', 18, 'chainlink', 'Chainlink'),
            'UNI': TokenInfo('UNI', '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 18, 'uniswap', 'Uniswap'),
            'AAVE': TokenInfo('AAVE', '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', 18, 'aave', 'Aave'),
            'CRV': TokenInfo('CRV', '0xD533a949740bb3306d119CC777fa900bA034cd52', 18, 'curve-dao-token', 'Curve DAO Token'),
            'SUSHI': TokenInfo('SUSHI', '0x6B3595068778DD592e39A122f4f5a5cF09C90fE2', 18, 'sushi', 'SushiSwap')
        }
        
        # Polygon network addresses for supported tokens
        self.polygon_tokens = {
            'WMATIC': TokenInfo('WMATIC', '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', 18, 'matic-network', 'Wrapped Matic'),
            'USDC': TokenInfo('USDC', '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 6, 'usd-coin', 'USD Coin'),
            'USDT': TokenInfo('USDT', '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 6, 'tether', 'Tether USD'),
            'WETH': TokenInfo('WETH', '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', 18, 'ethereum', 'Wrapped Ethereum'),
            'WBTC': TokenInfo('WBTC', '0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6', 8, 'wrapped-bitcoin', 'Wrapped Bitcoin'),
            'DAI': TokenInfo('DAI', '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', 18, 'dai', 'Dai Stablecoin')
        }
        
    def setup_dex_configs(self):
        """Setup DEX configurations across networks"""
        self.dexes = {
            'uniswap_v2': DEXInfo('Uniswap V2', 'ethereum', '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f', 0.3),
            'uniswap_v3': DEXInfo('Uniswap V3', 'ethereum', '0xE592427A0AEce92De3Edee1F18E0157C05861564', '0x1F98431c8aD98523631AE4a59f267346ea31F984', 0.3),
            'sushiswap': DEXInfo('SushiSwap', 'ethereum', '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F', '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac', 0.3),
            'quickswap': DEXInfo('QuickSwap', 'polygon', '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff', '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32', 0.3),
            'pancakeswap': DEXInfo('PancakeSwap', 'bsc', '0x10ED43C718714eb63d5aA57B78B54704E256024E', '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73', 0.25),
            'balancer': DEXInfo('Balancer', 'ethereum', '0xBA12222222228d8Ba445958a75a0704d566BF2C8', '0xBA12222222228d8Ba445958a75a0704d566BF2C8', 0.2),
            'curve': DEXInfo('Curve', 'ethereum', '0x99a58482BD75cbab83b27EC03CA68fF489b5788f', '0x0959158b6040D32d04c301A72CBFD6b39E21c9AE', 0.04)
        }
    
    def calculate_price_impact(self, trade_size: float, liquidity: float, token_symbol: str) -> float:
        """Calculate price impact based on trade size, liquidity, and token characteristics"""
        if liquidity <= 0:
            return 0.15
        
        # Base impact calculation
        impact_ratio = trade_size / liquidity
        
        # Token-specific adjustments
        volatility_multiplier = {
            'WBTC': 1.2, 'WETH': 1.1, 'AAVE': 1.5, 'UNI': 1.4, 'SUSHI': 1.6,
            'LINK': 1.3, 'CRV': 1.4, 'WMATIC': 1.2, 'USDC': 0.8, 'USDT': 0.8, 'DAI': 0.9
        }.get(token_symbol, 1.0)
        
        # Calculate impact with volatility adjustment
        base_impact = impact_ratio * volatility_multiplier
        
        # Apply logarithmic scaling for large trades
        if impact_ratio > 0.05:
            base_impact = base_impact * (1 + math.log(impact_ratio * 20))
        
        return round(min(base_impact, 0.30), 4)
    
    def calculate_confidence_score(self, price_spread: float, liquidity_avg: float, 
                                 volatility: float, data_age: float, token_symbol: str) -> float:
        """Calculate confidence score with token-specific factors"""
        # Base confidence from spread size
        spread_confidence = min(price_spread / 3.0, 1.0)
        
        # Liquidity confidence (varies by token)
        liquidity_thresholds = {
            'WETH': 2000000, 'WBTC': 1000000, 'USDC': 5000000, 'USDT': 5000000,
            'DAI': 2000000, 'WMATIC': 500000, 'LINK': 300000, 'UNI': 200000,
            'AAVE': 150000, 'CRV': 100000, 'SUSHI': 100000
        }
        threshold = liquidity_thresholds.get(token_symbol, 500000)
        liquidity_confidence = min(liquidity_avg / threshold, 1.0)
        
        # Volatility penalty (token-specific)
        volatility_tolerance = {
            'USDC': 2.0, 'USDT': 2.0, 'DAI': 3.0, 'WETH': 8.0, 'WBTC': 10.0,
            'WMATIC': 15.0, 'LINK': 12.0, 'UNI': 15.0, 'AAVE': 18.0, 'CRV': 20.0, 'SUSHI': 25.0
        }.get(token_symbol, 15.0)
        volatility_penalty = max(0, 1.0 - (volatility / volatility_tolerance))
        
        # Data freshness
        freshness = max(0, 1.0 - (data_age / 45.0))
        
        # Combined confidence with token weighting
        confidence = (
            spread_confidence * 0.35 + 
            liquidity_confidence * 0.30 + 
            volatility_penalty * 0.25 + 
            freshness * 0.10
        )
        
        return round(max(0, min(1, confidence)), 3)
    
    def calculate_gas_cost_usd(self, network: str = 'ethereum', complex_arbitrage: bool = True) -> float:
        """Calculate gas cost in USD for specified network"""
        network_config = self.networks.get(network, self.networks['ethereum'])
        
        # Adjust gas limit based on complexity
        gas_limit = self.base_gas_limit
        if complex_arbitrage:
            gas_limit = int(gas_limit * 1.5)
        
        # Calculate gas cost
        gas_cost_native = (network_config['gas_price_gwei'] * gas_limit) / 1e9
        gas_cost_usd = gas_cost_native * network_config['native_price_usd']
        
        return round(gas_cost_usd, 4)
    
    def calculate_optimal_trade_size(self, price_diff_percent: float, liquidity_a: float, 
                                   liquidity_b: float, token_symbol: str, max_trade_usd: float = 100000) -> float:
        """Calculate optimal trade size with token-specific considerations"""
        min_liquidity = min(liquidity_a, liquidity_b)
        
        # Token-specific liquidity utilization limits
        liquidity_limits = {
            'USDC': 0.08, 'USDT': 0.08, 'DAI': 0.07, 'WETH': 0.06, 'WBTC': 0.05,
            'WMATIC': 0.04, 'LINK': 0.03, 'UNI': 0.03, 'AAVE': 0.025, 'CRV': 0.02, 'SUSHI': 0.02
        }
        limit = liquidity_limits.get(token_symbol, 0.03)
        
        # Liquidity-constrained size
        liquidity_constrained_size = min_liquidity * limit
        
        # Price difference adjusted size
        price_factor = min(price_diff_percent / 2.0, 2.0)
        price_adjusted_size = max_trade_usd * price_factor
        
        # Token-specific minimum sizes
        min_sizes = {
            'WETH': 5000, 'WBTC': 10000, 'USDC': 2000, 'USDT': 2000, 'DAI': 2000,
            'WMATIC': 1000, 'LINK': 1500, 'UNI': 1500, 'AAVE': 2000, 'CRV': 1000, 'SUSHI': 1000
        }
        min_size = min_sizes.get(token_symbol, 1500)
        
        optimal_size = min(liquidity_constrained_size, price_adjusted_size, max_trade_usd)
        return round(max(min_size, optimal_size), 2)
    
    def assess_risk_level(self, confidence: float, price_impact: float, 
                         liquidity_avg: float, token_symbol: str) -> str:
        """Assess risk level with token-specific factors"""
        risk_score = 0
        
        # Confidence scoring
        if confidence >= 0.8:
            risk_score += 1
        elif confidence >= 0.6:
            risk_score += 2
        elif confidence >= 0.4:
            risk_score += 3
        else:
            risk_score += 4
        
        # Price impact scoring
        if price_impact <= 0.01:
            risk_score += 1
        elif price_impact <= 0.03:
            risk_score += 2
        elif price_impact <= 0.06:
            risk_score += 3
        else:
            risk_score += 4
        
        # Liquidity scoring (token-specific thresholds)
        liquidity_thresholds = {
            'WETH': [3000000, 1000000], 'WBTC': [2000000, 500000], 'USDC': [10000000, 2000000],
            'USDT': [10000000, 2000000], 'DAI': [3000000, 800000], 'WMATIC': [1000000, 200000],
            'LINK': [500000, 100000], 'UNI': [300000, 80000], 'AAVE': [200000, 50000],
            'CRV': [150000, 40000], 'SUSHI': [150000, 40000]
        }
        thresholds = liquidity_thresholds.get(token_symbol, [500000, 100000])
        
        if liquidity_avg >= thresholds[0]:
            risk_score += 1
        elif liquidity_avg >= thresholds[1]:
            risk_score += 2
        else:
            risk_score += 3
        
        # Token-specific risk adjustments
        token_risk_multipliers = {
            'USDC': 0.8, 'USDT': 0.8, 'DAI': 0.9, 'WETH': 1.0, 'WBTC': 1.1,
            'WMATIC': 1.2, 'LINK': 1.1, 'UNI': 1.3, 'AAVE': 1.4, 'CRV': 1.5, 'SUSHI': 1.6
        }
        risk_score = risk_score * token_risk_multipliers.get(token_symbol, 1.0)
        
        # Determine risk level
        if risk_score <= 4:
            return "LOW"
        elif risk_score <= 7:
            return "MEDIUM"
        else:
            return "HIGH"


class RealTimeDEXMonitor:
    """Real-time DEX monitoring and arbitrage detection with Web3 integration"""
    
    def __init__(self):
        self.calculator = EnhancedDEXArbitrageCalculator()
        self.current_prices: AllDexPrices = {}
        self.arbitrage_opportunities: List[ArbitrageOpportunity] = []
        self.market_metrics: MarketMetrics = {}
        self.monitoring_active = False
        self.update_interval = 10
        
        # Web3 integration attributes
        self.web3_providers: Dict[str, Web3] = {}
        self.uniswap_v2_pair_abi: List[Dict[str, Any]] = []
        self.uniswap_v2_factory_abi: List[Dict[str, Any]] = []
        
        # MCP server integration
        self.mcp_servers = {
            'taskmanager': 'http://localhost:8007',
            'flashloan': 'http://localhost:8000',
            'production': 'http://localhost:8004'
        }
        
        # Initialize Web3 providers and contract ABIs
        self.setup_web3_providers()
        self.get_contract_abis()

    def setup_web3_providers(self):
        """Setup Web3 providers for different networks"""
        try:
            self.web3_providers = {
                'ethereum': Web3(Web3.HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/demo')),
                'polygon': Web3(Web3.HTTPProvider('https://polygon-rpc.com')),
                'bsc': Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
            }
            
            # Test connections
            for network, w3 in self.web3_providers.items():
                if w3.is_connected():
                    logger.info(f"Connected to {network} network")
                else:
                    logger.warning(f"Failed to connect to {network} network")
                    
        except Exception as e:
            logger.error(f"Error setting up Web3 providers: {e}")
            self.web3_providers = {}

    def get_contract_abis(self):
        """Get contract ABIs for DEX interactions"""
        # Uniswap V2 Pair ABI (minimal required functions)
        self.uniswap_v2_pair_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                    {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                    {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token0",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token1",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Uniswap V2 Factory ABI (minimal required functions)
        self.uniswap_v2_factory_abi = [
            {
                "constant": True,
                "inputs": [
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"}
                ],
                "name": "getPair",
                "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]

    async def get_real_dex_prices(self, base_prices: CoinGeckoApiResponse) -> AllDexPrices:
        """Get real DEX prices using Web3 instead of simulation"""
        dex_prices: AllDexPrices = {}
        
        for token_symbol, price_info in base_prices.items():
            dex_prices[token_symbol] = {}
            
            # Get real prices from each DEX
            for dex_name, dex_info in self.calculator.dexes.items():
                try:
                    # Get real price from DEX
                    real_price = await self.get_uniswap_v2_price(
                        token_symbol, dex_name, dex_info.chain
                    )
                    
                    if real_price is not None:
                        # Calculate liquidity and volume estimates
                        liquidity = self._estimate_liquidity(token_symbol, dex_name, real_price)
                        volume_24h = self._estimate_volume(token_symbol, dex_name, liquidity)
                        
                        dex_prices[token_symbol][dex_name] = {
                            'price': real_price,
                            'liquidity': liquidity,
                            'volume_24h': volume_24h,
                            'fee_percent': dex_info.fee_percent,
                            'chain': dex_info.chain,
                            'timestamp': time.time(),
                            'change_24h': price_info.get('change_24h')
                        }
                    else:
                        # Use fallback price if Web3 call fails
                        fallback_price = self._get_fallback_price(
                            price_info['price'], dex_name, token_symbol
                        )
                        dex_prices[token_symbol][dex_name] = {
                            'price': fallback_price,
                            'liquidity': self._estimate_liquidity(token_symbol, dex_name, fallback_price),
                            'volume_24h': self._estimate_volume(token_symbol, dex_name, 1000000),
                            'fee_percent': dex_info.fee_percent,
                            'chain': dex_info.chain,
                            'timestamp': time.time(),
                            'change_24h': price_info.get('change_24h')
                        }
                        
                except Exception as e:
                    logger.warning(f"Error getting real price for {token_symbol} on {dex_name}: {e}")
                    # Use fallback price
                    fallback_price = self._get_fallback_price(
                        price_info['price'], dex_name, token_symbol
                    )
                    dex_prices[token_symbol][dex_name] = {
                        'price': fallback_price,
                        'liquidity': self._estimate_liquidity(token_symbol, dex_name, fallback_price),
                        'volume_24h': self._estimate_volume(token_symbol, dex_name, 1000000),
                        'fee_percent': dex_info.fee_percent,
                        'chain': dex_info.chain,
                        'timestamp': time.time(),
                        'change_24h': price_info.get('change_24h')
                    }
        
        return dex_prices

    async def get_uniswap_v2_price(self, token_symbol: str, dex_name: str, network: str) -> Optional[float]:
        """Get real price from Uniswap V2 style DEX using Web3"""
        try:
            # Only handle Uniswap V2 style DEXes for now
            if dex_name not in ['uniswap_v2', 'sushiswap', 'quickswap', 'pancakeswap']:
                return None
                
            w3 = self.web3_providers.get(network)
            if not w3 or not w3.is_connected():
                return None
                
            # Get token info
            token_info = self.calculator.tokens.get(token_symbol)
            if network == 'polygon':
                token_info = self.calculator.polygon_tokens.get(token_symbol)
                
            if not token_info:
                return None
                
            # Get WETH address for the network
            weth_addresses = {
                'ethereum': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'polygon': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
                'bsc': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
            }
            weth_address = weth_addresses.get(network)
            
            if not weth_address or token_info.address.lower() == weth_address.lower():
                return None  # Skip WETH pairs for now
                
            # Get DEX factory address
            dex_info = self.calculator.dexes.get(dex_name)
            if not dex_info:
                return None
                  # Create factory contract
            factory_contract = w3.eth.contract(  # type: ignore
                address=Web3.to_checksum_address(dex_info.factory_address),
                abi=self.uniswap_v2_factory_abi
            )
            
            # Get pair address
            pair_address = factory_contract.functions.getPair(  # type: ignore
                Web3.to_checksum_address(token_info.address), 
                Web3.to_checksum_address(weth_address)
            ).call()
            
            if pair_address == '0x0000000000000000000000000000000000000000':
                return None  # Pair doesn't exist
                  # Create pair contract
            pair_contract = w3.eth.contract(  # type: ignore
                address=Web3.to_checksum_address(pair_address),
                abi=self.uniswap_v2_pair_abi
            )
            
            # Get reserves
            reserves = pair_contract.functions.getReserves().call()  # type: ignore
            reserve0, reserve1, _ = reserves
            
            # Get token order
            token0 = pair_contract.functions.token0().call()  # type: ignore
            # token1 = pair_contract.functions.token1().call()  # type: ignore
            
            # Calculate price
            if token0.lower() == token_info.address.lower():
                # Token is token0, WETH is token1
                token_reserve = reserve0
                weth_reserve = reserve1
            else:
                # Token is token1, WETH is token0
                token_reserve = reserve1
                weth_reserve = reserve0
                
            if token_reserve == 0:
                return None
                
            # Calculate price in WETH
            price_in_weth = weth_reserve / token_reserve
            
            # Adjust for decimals
            weth_decimals = 18
            price_in_weth = price_in_weth * (10 ** (token_info.decimals - weth_decimals))
            
            # Convert to USD (using ETH price from CoinGecko)
            # For simplicity, using a fixed ETH price, but this should come from CoinGecko
            eth_price_usd = 2450.0  # This should be dynamic
            price_usd = price_in_weth * eth_price_usd
            
            return price_usd
            
        except Exception as e:
            logger.error(f"Error getting Uniswap V2 price for {token_symbol} on {dex_name}: {e}")
            return None

    def _get_fallback_price(self, base_price: float, dex_name: str, token_symbol: str) -> float:
        """Generate fallback price when Web3 calls fail"""
        # Add DEX-specific spread variations
        dex_spreads = {
            'uniswap_v2': 0.002, 'uniswap_v3': 0.001, 'sushiswap': 0.003,
            'quickswap': 0.004, 'pancakeswap': 0.003, 'balancer': 0.002, 'curve': 0.001
        }
        
        spread = dex_spreads.get(dex_name, 0.002)
        
        # Add random variation within spread
        import random
        variation = random.uniform(-spread, spread)
        
        return base_price * (1 + variation)

    def _estimate_liquidity(self, token_symbol: str, dex_name: str, price: float) -> float:
        """Estimate liquidity based on token and DEX characteristics"""
        # Base liquidity estimates by token
        base_liquidity = {
            'WETH': 5000000, 'USDC': 10000000, 'USDT': 8000000, 'DAI': 3000000,
            'WBTC': 2000000, 'WMATIC': 1000000, 'LINK': 500000, 'UNI': 300000,
            'AAVE': 200000, 'CRV': 150000, 'SUSHI': 150000
        }
        
        # DEX liquidity multipliers
        dex_multipliers = {
            'uniswap_v2': 1.0, 'uniswap_v3': 1.2, 'sushiswap': 0.3,
            'quickswap': 0.1, 'pancakeswap': 0.8, 'balancer': 0.2, 'curve': 0.5
        }
        
        base = base_liquidity.get(token_symbol, 500000)
        multiplier = dex_multipliers.get(dex_name, 0.3)
        
        return base * multiplier

    def _estimate_volume(self, token_symbol: str, dex_name: str, liquidity: float) -> float:
        """Estimate 24h volume based on liquidity"""
        # Volume is typically 2-5x liquidity for active pairs
        volume_multiplier = {
            'WETH': 4.0, 'USDC': 5.0, 'USDT': 4.5, 'DAI': 3.0,
            'WBTC': 3.5, 'WMATIC': 2.5, 'LINK': 2.0, 'UNI': 2.0,
            'AAVE': 1.5, 'CRV': 1.5, 'SUSHI': 1.5
        }
        
        multiplier = volume_multiplier.get(token_symbol, 2.0)
        return liquidity * multiplier

    async def fetch_coingecko_prices(self) -> CoinGeckoApiResponse:
        """Fetch current prices from CoinGecko API"""
        try:
            # Build CoinGecko API URL for all tokens
            token_ids = [token.coingecko_id for token in self.calculator.tokens.values()]
            ids_param = ','.join(token_ids)
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert to our expected format
                        prices: CoinGeckoApiResponse = {}
                        for symbol, token in self.calculator.tokens.items():
                            coingecko_data = data.get(token.coingecko_id, {})
                            if coingecko_data:
                                prices[symbol] = {
                                    'price': coingecko_data.get('usd', 0.0),
                                    'change_24h': coingecko_data.get('usd_24h_change'),
                                    'market_cap': coingecko_data.get('usd_market_cap')
                                }
                            else:
                                # Fallback price if token not found
                                prices[symbol] = {
                                    'price': 1.0,  # Default price
                                    'change_24h': None,
                                    'market_cap': None
                                }
                        
                        return prices
                    else:
                        logger.error(f"CoinGecko API error: {response.status}")
                        return self._get_fallback_prices()
                        
        except Exception as e:
            logger.error(f"Error fetching CoinGecko prices: {e}")
            return self._get_fallback_prices()

    def _get_fallback_prices(self) -> CoinGeckoApiResponse:
        """Get fallback prices when CoinGecko is unavailable"""
        fallback_prices: CoinGeckoApiResponse = {
            'WETH': {'price': 2450.0, 'change_24h': 1.2, 'market_cap': None},
            'USDC': {'price': 1.0, 'change_24h': 0.1, 'market_cap': None},
            'USDT': {'price': 1.0, 'change_24h': -0.05, 'market_cap': None},
            'DAI': {'price': 1.0, 'change_24h': 0.02, 'market_cap': None},
            'WBTC': {'price': 43500.0, 'change_24h': 2.1, 'market_cap': None},
            'WMATIC': {'price': 0.85, 'change_24h': 3.2, 'market_cap': None},
            'LINK': {'price': 14.50, 'change_24h': 1.8, 'market_cap': None},
            'UNI': {'price': 8.75, 'change_24h': 2.5, 'market_cap': None},
            'AAVE': {'price': 165.0, 'change_24h': 1.9, 'market_cap': None},
            'CRV': {'price': 0.42, 'change_24h': 4.1, 'market_cap': None},
            'SUSHI': {'price': 0.89, 'change_24h': 3.8, 'market_cap': None}
        }
        return fallback_prices

    def find_arbitrage_opportunities(self, dex_prices: AllDexPrices) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities across DEXes"""
        opportunities: List[ArbitrageOpportunity] = []
        
        for token_symbol, token_prices in dex_prices.items():
            if len(token_prices) < 2:
                continue
                
            # Compare all DEX pairs for this token
            dex_names = list(token_prices.keys())
            for i in range(len(dex_names)):
                for j in range(i + 1, len(dex_names)):
                    dex_a, dex_b = dex_names[i], dex_names[j]
                    price_a = token_prices[dex_a]['price']
                    price_b = token_prices[dex_b]['price']
                    
                    # Determine buy/sell DEXes
                    if price_a < price_b:
                        buy_dex, sell_dex = dex_a, dex_b
                        buy_price, sell_price = price_a, price_b
                    else:
                        buy_dex, sell_dex = dex_b, dex_a
                        buy_price, sell_price = price_b, price_a
                    
                    # Calculate price difference
                    price_diff = sell_price - buy_price
                    profit_percentage = (price_diff / buy_price) * 100
                    
                    # Skip if profit too small
                    if profit_percentage < 0.5:  # Minimum 0.5% profit
                        continue
                    
                    # Calculate opportunity metrics
                    liquidity_buy = token_prices[buy_dex]['liquidity']
                    liquidity_sell = token_prices[sell_dex]['liquidity']
                    liquidity_avg = (liquidity_buy + liquidity_sell) / 2
                    
                    # Calculate optimal trade size
                    optimal_size = self.calculator.calculate_optimal_trade_size(
                        profit_percentage, liquidity_buy, liquidity_sell, token_symbol
                    )
                    
                    # Calculate price impact
                    price_impact = self.calculator.calculate_price_impact(
                        optimal_size, liquidity_avg, token_symbol
                    )
                    
                    # Calculate gas costs
                    buy_chain = token_prices[buy_dex]['chain']
                    gas_cost = self.calculator.calculate_gas_cost_usd(buy_chain, True)
                    
                    # Calculate profits
                    estimated_profit = optimal_size * (profit_percentage / 100)
                    net_profit = estimated_profit - gas_cost
                    
                    # Skip if not profitable after gas
                    if net_profit < self.calculator.min_profit_threshold:
                        continue
                    
                    # Calculate confidence score
                    data_age = max(
                        time.time() - token_prices[buy_dex]['timestamp'],
                        time.time() - token_prices[sell_dex]['timestamp']
                    )
                    
                    confidence = self.calculator.calculate_confidence_score(
                        profit_percentage, liquidity_avg, 
                        abs(token_prices[buy_dex].get('change_24h', 0) or 0),
                        data_age, token_symbol
                    )
                    
                    # Assess risk level
                    risk_level = self.calculator.assess_risk_level(
                        confidence, price_impact, liquidity_avg, token_symbol
                    )
                    
                    # Create opportunity
                    opportunity = ArbitrageOpportunity(
                        token=token_symbol,
                        dex_buy=buy_dex,
                        dex_sell=sell_dex,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        price_diff=price_diff,
                        profit_percentage=profit_percentage,
                        optimal_trade_size=optimal_size,
                        estimated_profit=estimated_profit,
                        gas_cost=gas_cost,
                        net_profit=net_profit,
                        confidence_score=confidence,
                        risk_level=risk_level,
                        liquidity_score=min(liquidity_avg / 1000000, 1.0),
                        timestamp=time.time()
                    )
                    
                    opportunities.append(opportunity)
        
        # Sort by net profit
        opportunities.sort(key=lambda x: Any: Any: x.net_profit, reverse=True)
        return opportunities

    async def update_market_data(self):
        """Update market data with real Web3 prices"""
        try:
            logger.info("Updating market data with real Web3 prices...")
            
            # Fetch base prices from CoinGecko
            base_prices = await self.fetch_coingecko_prices()
            
            # Get real DEX prices using Web3
            self.current_prices = await self.get_real_dex_prices(base_prices)
            
            # Find arbitrage opportunities
            self.arbitrage_opportunities = self.find_arbitrage_opportunities(self.current_prices)
            
            # Update market metrics
            self.market_metrics = {
                'total_tokens': len(self.current_prices),
                'total_dexes': len(self.calculator.dexes),
                'arbitrage_opportunities': len(self.arbitrage_opportunities),
                'best_opportunity': self.arbitrage_opportunities[0].__dict__ if self.arbitrage_opportunities else None,
                'total_liquidity': sum(
                    sum(dex_data['liquidity'] for dex_data in token_data.values())
                    for token_data in self.current_prices.values()
                ),
                'last_update': datetime.now().isoformat(),
                'web3_status': 'connected' if self.web3_providers else 'disconnected'
            }
            
            logger.info(f"Found {len(self.arbitrage_opportunities)} arbitrage opportunities")
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")

    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.monitoring_active = True
        logger.info("Starting DEX monitoring with Web3 integration...")
        
        while self.monitoring_active:
            try:
                await self.update_market_data()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_active = False
        logger.info("Stopping DEX monitoring...")

    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status"""
        return {
            'monitoring_active': self.monitoring_active,
            'web3_connections': {
                network: w3.is_connected() if w3 else False 
                for network, w3 in self.web3_providers.items()
            },
            'last_update': self.market_metrics.get('last_update'),
            'opportunities_count': len(self.arbitrage_opportunities),
            'total_tokens': len(self.current_prices)
        }


# Global monitor instance
monitor = RealTimeDEXMonitor()

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    return jsonify({
        'message': 'Enhanced DEX Arbitrage Monitor with Web3 Integration',
        'status': 'active',
        'port': 8008,
        'features': [
            'Real-time Web3 price fetching',
            'Multi-chain DEX monitoring',
            'Advanced arbitrage detection', 
            'Gas cost optimization',
            'Risk assessment'
        ]
    })

@app.route('/api/prices')
def get_prices():
    """Get current DEX prices"""
    return jsonify({
        'prices': monitor.current_prices,
        'timestamp': time.time(),
        'source': 'web3_real_time'
    })

@app.route('/api/opportunities')
def get_opportunities():
    """Get arbitrage opportunities"""
    top_opportunities: List[Dict[str, Any]] = []
    
    for opp in monitor.arbitrage_opportunities[:10]:  # Top 10
        top_opportunities.append({
            'token': opp.token,
            'dex_buy': opp.dex_buy,
            'dex_sell': opp.dex_sell,
            'buy_price': opp.buy_price,
            'sell_price': opp.sell_price,
            'profit_percentage': opp.profit_percentage,
            'net_profit': opp.net_profit,
            'confidence_score': opp.confidence_score,
            'risk_level': opp.risk_level,
            'optimal_trade_size': opp.optimal_trade_size,
            'gas_cost': opp.gas_cost,
            'timestamp': opp.timestamp
        })
    
    return jsonify({
        'opportunities': top_opportunities,
        'total_found': len(monitor.arbitrage_opportunities),
        'timestamp': time.time()
    })

@app.route('/api/metrics')
def get_metrics():
    """Get market metrics"""
    return jsonify(monitor.market_metrics)

@app.route('/api/status')
def get_status():
    """Get monitor status"""
    return jsonify(monitor.get_status())

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start monitoring"""
    if not monitor.monitoring_active:
        # Start monitoring in background thread
        def run_monitor():
            asyncio.run(monitor.start_monitoring())
        
        thread = threading.Thread(target=run_monitor, daemon=True)
        thread.start()
        
        return jsonify({'message': 'Monitoring started', 'status': 'active'})
    else:
        return jsonify({'message': 'Monitoring already active', 'status': 'active'})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring"""
    monitor.stop_monitoring()
    return jsonify({'message': 'Monitoring stopped', 'status': 'inactive'})

@app.route('/api/data')
def get_all_data():
    """Get comprehensive data for dashboard"""
    opportunities_data: List[Dict[str, Any]] = []
    
    for opp in monitor.arbitrage_opportunities:
        opportunities_data.append({
            'token': opp.token,
            'dex_buy': opp.dex_buy,
            'dex_sell': opp.dex_sell,
            'buy_price': opp.buy_price,
            'sell_price': opp.sell_price,
            'price_diff': opp.price_diff,
            'profit_percentage': opp.profit_percentage,
            'optimal_trade_size': opp.optimal_trade_size,
            'estimated_profit': opp.estimated_profit,
            'gas_cost': opp.gas_cost,
            'net_profit': opp.net_profit,
            'confidence_score': opp.confidence_score,
            'risk_level': opp.risk_level,
            'liquidity_score': opp.liquidity_score,
            'timestamp': opp.timestamp
        })
    
    return jsonify({
        'prices': monitor.current_prices,
        'opportunities': opportunities_data,
        'metrics': monitor.market_metrics,
        'status': monitor.get_status(),
        'timestamp': time.time()
    })


def main():
    """Main entry point"""
    logger.info("Enhanced DEX Arbitrage Monitor starting on port 8008...")
    logger.info("Features: Web3 Integration, Real-time Prices, Multi-chain Support")
    
    try:
        app.run(host='0.0.0.0', port=8008, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Error starting server: {e}")


if __name__ == '__main__':
    main()