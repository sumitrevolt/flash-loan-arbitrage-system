#!/usr/bin/env python3
"""
Real-time DEX Price Monitor with Arbitrage Calculations
Integrates with MCP dashboard for live price feeds and opportunity detection
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    """Data class for price information"""
    token_pair: str
    dex: str
    price: float
    volume_24h: float
    liquidity: float
    timestamp: datetime
    block_number: Optional[int] = None

@dataclass
class ArbitrageOpportunity:
    """Data class for arbitrage opportunity"""
    token_pair: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    spread_percent: float
    potential_profit: float
    min_trade_amount: float
    max_trade_amount: float
    gas_cost_estimate: float
    net_profit: float
    timestamp: datetime

class DEXPriceMonitor:
    """Real-time DEX price monitoring with arbitrage calculations"""
    
    def __init__(self):
        self.prices: Dict[str, Dict[str, PriceData]] = {}
        self.opportunities: List[ArbitrageOpportunity] = []
        self.running = False
        self.update_interval = 10  # seconds
        
        # Load configuration
        self.load_config()
        
        # DEX configurations for Polygon
        self.dex_configs = {
            'uniswap_v3': {
                'name': 'Uniswap V3',
                'subgraph': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-polygon',
                'factory_address': '0x1F98431c8aD98523631AE4a59f267346ea31F984'
            },
            'sushiswap': {
                'name': 'SushiSwap',
                'subgraph': 'https://api.thegraph.com/subgraphs/name/sushiswap/exchange-polygon',
                'factory_address': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4'
            },
            'quickswap': {
                'name': 'QuickSwap',
                'subgraph': 'https://api.thegraph.com/subgraphs/name/sameepsi/quickswap06',
                'factory_address': '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32'
            }
        }
        
        # Token pairs to monitor (Polygon addresses)
        self.token_pairs = {
            'WETH/USDC': {
                'token0': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',  # WETH
                'token1': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',  # USDC
                'decimals0': 18,
                'decimals1': 6
            },
            'WMATIC/USDC': {
                'token0': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',  # WMATIC
                'token1': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',  # USDC
                'decimals0': 18,
                'decimals1': 6
            },
            'WBTC/WETH': {
                'token0': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',  # WBTC
                'token1': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',  # WETH
                'decimals0': 8,
                'decimals1': 18
            }
        }
        
    def load_config(self):
        """Load configuration from environment and files"""
        try:
            # Load from production config if available
            config_path = Path("production_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.min_profit_threshold = config.get('min_profit_threshold', 0.01)  # 1%
                    self.max_slippage = config.get('max_slippage', 0.005)  # 0.5%
                    self.gas_price_gwei = config.get('gas_price_gwei', 30)
            else:
                # Default values
                self.min_profit_threshold = 0.01
                self.max_slippage = 0.005
                self.gas_price_gwei = 30
                
            # Load RPC URL
            self.rpc_url = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
            
        except Exception as e:
            logger.warning(f"Config loading error: {e}, using defaults")
            self.min_profit_threshold = 0.01
            self.max_slippage = 0.005
            self.gas_price_gwei = 30
            self.rpc_url = 'https://polygon-rpc.com'
    
    async def fetch_uniswap_v3_prices(self, session: aiohttp.ClientSession) -> List[PriceData]:
        """Fetch prices from Uniswap V3 on Polygon"""
        try:
            query = """
            {
              pools(first: 10, orderBy: volumeUSD, orderDirection: desc, 
                    where: {
                      token0_in: [
                        "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                        "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
                        "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
                      ]
                    }) {
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
                token0Price
                token1Price
                volumeUSD
                totalValueLockedUSD
                txCount
              }
            }
            """
            
            async with session.post(
                self.dex_configs['uniswap_v3']['subgraph'],
                json={'query': query},
                timeout=10
            ) as response:
                data = await response.json()
                
                prices = []
                for pool in data.get('data', {}).get('pools', []):
                    token0_symbol = pool['token0']['symbol']
                    token1_symbol = pool['token1']['symbol']
                    pair_name = f"{token0_symbol}/{token1_symbol}"
                    
                    # Calculate price (token1 per token0)
                    price = float(pool['token0Price']) if pool['token0Price'] else 0
                    
                    if price > 0:
                        price_data = PriceData(
                            token_pair=pair_name,
                            dex='uniswap_v3',
                            price=price,
                            volume_24h=float(pool.get('volumeUSD', 0)),
                            liquidity=float(pool.get('totalValueLockedUSD', 0)),
                            timestamp=datetime.now()
                        )
                        prices.append(price_data)
                        
                return prices
                
        except Exception as e:
            logger.error(f"Error fetching Uniswap V3 prices: {e}")
            return []
    
    async def fetch_sushiswap_prices(self, session: aiohttp.ClientSession) -> List[PriceData]:
        """Fetch prices from SushiSwap on Polygon"""
        try:
            query = """
            {
              pairs(first: 10, orderBy: volumeUSD, orderDirection: desc,
                    where: {
                      token0_in: [
                        "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                        "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
                        "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
                      ]
                    }) {
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
                token0Price
                token1Price
                volumeUSD
                reserveUSD
                txCount
              }
            }
            """
            
            async with session.post(
                self.dex_configs['sushiswap']['subgraph'],
                json={'query': query},
                timeout=10
            ) as response:
                data = await response.json()
                
                prices = []
                for pair in data.get('data', {}).get('pairs', []):
                    token0_symbol = pair['token0']['symbol']
                    token1_symbol = pair['token1']['symbol']
                    pair_name = f"{token0_symbol}/{token1_symbol}"
                    
                    price = float(pair['token0Price']) if pair['token0Price'] else 0
                    
                    if price > 0:
                        price_data = PriceData(
                            token_pair=pair_name,
                            dex='sushiswap',
                            price=price,
                            volume_24h=float(pair.get('volumeUSD', 0)),
                            liquidity=float(pair.get('reserveUSD', 0)),
                            timestamp=datetime.now()
                        )
                        prices.append(price_data)
                        
                return prices
                
        except Exception as e:
            logger.error(f"Error fetching SushiSwap prices: {e}")
            return []
    
    async def fetch_quickswap_prices(self, session: aiohttp.ClientSession) -> List[PriceData]:
        """Fetch prices from QuickSwap on Polygon"""
        try:
            query = """
            {
              pairs(first: 10, orderBy: volumeUSD, orderDirection: desc,
                    where: {
                      token0_in: [
                        "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                        "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
                        "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
                      ]
                    }) {
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
                token0Price
                token1Price
                volumeUSD
                reserveUSD
                txCount
              }
            }
            """
            
            async with session.post(
                self.dex_configs['quickswap']['subgraph'],
                json={'query': query},
                timeout=10
            ) as response:
                data = await response.json()
                
                prices = []
                for pair in data.get('data', {}).get('pairs', []):
                    token0_symbol = pair['token0']['symbol']
                    token1_symbol = pair['token1']['symbol']
                    pair_name = f"{token0_symbol}/{token1_symbol}"
                    
                    price = float(pair['token0Price']) if pair['token0Price'] else 0
                    
                    if price > 0:
                        price_data = PriceData(
                            token_pair=pair_name,
                            dex='quickswap',
                            price=price,
                            volume_24h=float(pair.get('volumeUSD', 0)),
                            liquidity=float(pair.get('reserveUSD', 0)),
                            timestamp=datetime.now()
                        )
                        prices.append(price_data)
                        
                return prices
                
        except Exception as e:
            logger.error(f"Error fetching QuickSwap prices: {e}")
            return []
    
    async def fetch_all_prices(self) -> Dict[str, List[PriceData]]:
        """Fetch prices from all DEXs"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.fetch_uniswap_v3_prices(session),
                self.fetch_sushiswap_prices(session),
                self.fetch_quickswap_prices(session)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_prices = {
                'uniswap_v3': results[0] if not isinstance(results[0], Exception) else [],
                'sushiswap': results[1] if not isinstance(results[1], Exception) else [],
                'quickswap': results[2] if not isinstance(results[2], Exception) else []
            }
            
            return all_prices
    
    def calculate_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """Calculate arbitrage opportunities between DEXs"""
        opportunities = []
        
        # Group prices by token pair
        pair_prices = {}
        for dex, price_list in self.prices.items():
            for price_data in price_list:
                pair = price_data.token_pair
                if pair not in pair_prices:
                    pair_prices[pair] = {}
                pair_prices[pair][dex] = price_data
        
        # Find arbitrage opportunities
        for pair, dex_prices in pair_prices.items():
            if len(dex_prices) < 2:
                continue
                
            dex_names = list(dex_prices.keys())
            
            for i in range(len(dex_names)):
                for j in range(i + 1, len(dex_names)):
                    dex1, dex2 = dex_names[i], dex_names[j]
                    price1, price2 = dex_prices[dex1].price, dex_prices[dex2].price
                    
                    if price1 <= 0 or price2 <= 0:
                        continue
                    
                    # Calculate spread
                    if price1 < price2:
                        buy_dex, sell_dex = dex1, dex2
                        buy_price, sell_price = price1, price2
                    else:
                        buy_dex, sell_dex = dex2, dex1
                        buy_price, sell_price = price2, price1
                    
                    spread_percent = (sell_price - buy_price) / buy_price
                    
                    if spread_percent >= self.min_profit_threshold:
                        # Estimate trade amounts based on liquidity
                        buy_liquidity = dex_prices[buy_dex].liquidity
                        sell_liquidity = dex_prices[sell_dex].liquidity
                        
                        min_trade = 1000  # $1000 minimum
                        max_trade = min(buy_liquidity * 0.05, sell_liquidity * 0.05)  # 5% of liquidity
                        
                        # Estimate gas costs (Polygon is cheap)
                        gas_cost = 0.01 * 30  # Rough estimate in USD
                        
                        # Calculate potential profit
                        potential_profit = max_trade * spread_percent
                        net_profit = potential_profit - gas_cost
                        
                        if net_profit > 0:
                            opportunity = ArbitrageOpportunity(
                                token_pair=pair,
                                buy_dex=buy_dex,
                                sell_dex=sell_dex,
                                buy_price=buy_price,
                                sell_price=sell_price,
                                spread_percent=spread_percent * 100,  # Convert to percentage
                                potential_profit=potential_profit,
                                min_trade_amount=min_trade,
                                max_trade_amount=max_trade,
                                gas_cost_estimate=gas_cost,
                                net_profit=net_profit,
                                timestamp=datetime.now()
                            )
                            opportunities.append(opportunity)
        
        # Sort by net profit
        opportunities.sort(key=lambda x: Any: Any: x.net_profit, reverse=True)
        return opportunities[:10]  # Top 10 opportunities
    
    async def update_prices(self):
        """Update all price data"""
        try:
            logger.info("Updating price data from all DEXs...")
            new_prices = await self.fetch_all_prices()
            
            # Update stored prices
            self.prices = new_prices
            
            # Calculate arbitrage opportunities
            self.opportunities = self.calculate_arbitrage_opportunities()
            
            logger.info(f"Updated prices from {len(self.prices)} DEXs, found {len(self.opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
    
    async def start_monitoring(self):
        """Start the price monitoring loop"""
        self.running = True
        logger.info("Starting DEX price monitoring...")
        
        while self.running:
            try:
                await self.update_prices()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def stop_monitoring(self):
        """Stop the price monitoring"""
        self.running = False
        logger.info("Stopping DEX price monitoring...")
    
    def get_current_prices(self) -> Dict[str, Any]:
        """Get current price data for API"""
        result: str = {
            'timestamp': datetime.now().isoformat(),
            'prices': {},
            'opportunities': [],
            'summary': {
                'total_pairs_monitored': 0,
                'total_opportunities': len(self.opportunities),
                'best_opportunity_profit': 0
            }
        }
        
        # Format prices
        for dex, price_list in self.prices.items():
            result['prices'][dex] = []
            for price_data in price_list:
                result['prices'][dex].append({
                    'token_pair': price_data.token_pair,
                    'price': price_data.price,
                    'volume_24h': price_data.volume_24h,
                    'liquidity': price_data.liquidity,
                    'timestamp': price_data.timestamp.isoformat()
                })
            result['summary']['total_pairs_monitored'] += len(price_list)
        
        # Format opportunities
        for opp in self.opportunities:
            result['opportunities'].append({
                'token_pair': opp.token_pair,
                'buy_dex': opp.buy_dex,
                'sell_dex': opp.sell_dex,
                'buy_price': opp.buy_price,
                'sell_price': opp.sell_price,
                'spread_percent': round(opp.spread_percent, 2),
                'potential_profit': round(opp.potential_profit, 2),
                'net_profit': round(opp.net_profit, 2),
                'max_trade_amount': round(opp.max_trade_amount, 2),
                'timestamp': opp.timestamp.isoformat()
            })
        
        if self.opportunities:
            result['summary']['best_opportunity_profit'] = round(self.opportunities[0].net_profit, 2)
        
        return result

# Global instance
price_monitor = DEXPriceMonitor()

async def main():
    """Main function for standalone testing"""
    try:
        await price_monitor.start_monitoring()
    except KeyboardInterrupt:
        price_monitor.stop_monitoring()
        logger.info("Price monitoring stopped by user")

if __name__ == "__main__":
    asyncio.run(main())
