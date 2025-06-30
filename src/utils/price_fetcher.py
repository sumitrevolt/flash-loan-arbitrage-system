# -*- coding: utf-8 -*-
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Tuple
import logging

from web3 import Web3
import aiohttp

logger = logging.getLogger("PriceFetcher")

class PriceFetcher:
    """Fetches token prices from multiple DEXs and calculates arbitrage opportunities"""
    
    def __init__(self, web3: Web3 = None, cache_ttl: int = 30):
        self.web3 = web3  # Can be None initially
        self.cache_ttl = cache_ttl  # seconds
        self.price_cache = {}
        self.last_fetch_time = {}
        
        # DEX router addresses on Polygon
        self.dex_routers = {
            'quickswap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
            'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506', 
            'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564'

        
        # Common token addresses on Polygon
        self.tokens = {
            'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
            'WMATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
            'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'


    async def fetch_price(self, dex: str, token_in: str, token_out: str) -> Decimal:
        """Fetch current price from specified DEX"""
        cache_key = f"{dex}:{token_in}:{token_out}"
        
        # Return cached price if still valid
        if cache_key in self.price_cache:
            if (datetime.now() - self.last_fetch_time[cache_key]).seconds < self.cache_ttl:
                return self.price_cache[cache_key]
        
        try:
            if dex == 'quickswap':
                price = await self._fetch_quickswap_price(token_in, token_out)
            elif dex == 'sushiswap':
                price = await self._fetch_sushiswap_price(token_in, token_out)
            elif dex == 'uniswap_v3':
                price = await self._fetch_uniswap_v3_price(token_in, token_out)
            else:
                raise ValueError(f"Unsupported DEX: {dex}")
            
            # Update cache
            self.price_cache[cache_key] = price
            self.last_fetch_time[cache_key] = datetime.now()
            
            return price
            
        except Exception as e:
            logger.error(f"Failed to fetch price from {dex}: {str(e)}")
            raise

    async def _fetch_quickswap_price(self, token_in: str, token_out: str) -> Decimal:
        """Fetch price from Quickswap API"""
        url = "https://api.quickswap.exchange/api/v1/quote"
        params = {
            'tokenIn': self.tokens[token_in],
            'tokenOut': self.tokens[token_out],
            'amountIn': str(10 ** 18)  # 1 unit of token_in

        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"Quickswap API error: {response.status}")
                
                data = await response.json()
                return Decimal(str(data['quote']))

    async def _fetch_sushiswap_price(self, token_in: str, token_out: str) -> Decimal:
        """Fetch price from Sushiswap API"""
        url = "https://api.sushi.com/swap/v1/quote"
        params = {
            'tokenIn': self.tokens[token_in],
            'tokenOut': self.tokens[token_out],
            'amount': str(10 ** 18)  # 1 unit of token_in

        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"Sushiswap API error: {response.status}")
                
                data = await response.json()
                return Decimal(str(data['price']))

    async def _fetch_uniswap_v3_price(self, token_in: str, token_out: str) -> Decimal:
        """Fetch price from Uniswap V3 using on-chain data"""
        # Simplified price calculation using Uniswap V3 pool
        # In production, would use proper tick math and pool selection
        pool_address = self._get_uniswap_v3_pool(token_in, token_out)
        
        # Simplified - would use proper Uniswap V3 ABI and calculations
        pool_contract = self.web3.eth.contract(
            address=pool_address,
            abi=self._get_uniswap_v3_pool_abi()

        
        slot0 = pool_contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]
        
        # Simplified price calculation
        price = (sqrt_price_x96 ** 2) / (2 ** 192)
        return Decimal(str(price))

    def _get_uniswap_v3_pool(self, token_in: str, token_out: str) -> str:
        """Get Uniswap V3 pool address for token pair"""
        # Simplified - would use proper factory and fee tier selection
        token0 = min(self.tokens[token_in], self.tokens[token_out])
        token1 = max(self.tokens[token_in], self.tokens[token_out])
        
        # Use deterministic pool address calculation
        # In production, would query factory contract
        return Web3.to_checksum_address(
            Web3.keccak(
                hexstr=f"0xff{self.dex_routers['uniswap_v3'][2:]}{Web3.keccak(hexstr=f'{token0[2:]}{token1[2:]}').hex()[2:]}"
            ).hex()[-40:]


    def _get_uniswap_v3_pool_abi(self) -> List[Dict]:
        """Get simplified Uniswap V3 pool ABI for price calculation"""
        return [
            {
                "inputs": [],
                "name": "slot0",
                "outputs": [
                    {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
                    {"internalType": "int24", "name": "tick", "type": "int24"},
                    {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
                    {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
                    {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
                    {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
                    {"internalType": "bool", "name": "unlocked", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"



    def set_web3(self, web3: Web3):
        """Set Web3 instance after initialization"""
        self.web3 = web3

    async def find_arbitrage_opportunities(self, token_pairs: List[Tuple[str, str]]) -> List[Dict]:
        """Find arbitrage opportunities across DEXs for given token pairs"""
        opportunities = []
        
        for token_in, token_out in token_pairs:
            try:
                # Get prices from all DEXs
                prices = {}
                for dex in self.dex_routers:
                    try:
                        prices[dex] = await self.fetch_price(dex, token_in, token_out)
                    except Exception as e:
                        logger.warning(f"Failed to get price from {dex}: {str(e)}")
                        continue
                
                if len(prices) < 2:
                    continue
                
                # Find best buy/sell prices
                best_buy_dex = min(prices, key=prices.get)
                best_sell_dex = max(prices, key=prices.get)
                
                if best_buy_dex == best_sell_dex:
                    continue
                
                price_diff = prices[best_sell_dex] - prices[best_buy_dex]
                price_diff_pct = (price_diff / prices[best_buy_dex]) * 100
                
                if price_diff_pct > 0.1:  # Minimum 0.1% difference
                    opportunities.append({
                        'pair': f"{token_in}/{token_out}",
                        'buy_dex': best_buy_dex,
                        'sell_dex': best_sell_dex,
                        'buy_price': float(prices[best_buy_dex]),
                        'sell_price': float(prices[best_sell_dex]),
                        'price_diff': float(price_diff),
                        'price_diff_pct': float(price_diff_pct),
                        'timestamp': datetime.now().isoformat()

                    
            except Exception as e:
                logger.error(f"Error processing pair {token_in}/{token_out}: {str(e)}")
                continue
                
        return opportunities