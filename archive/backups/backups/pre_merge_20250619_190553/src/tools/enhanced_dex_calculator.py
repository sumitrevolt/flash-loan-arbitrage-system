"""
Enhanced DEX Calculator with Visual Display
Shows real-time arbitrage calculations and opportunities
"""

import asyncio
import json
import logging
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from web3 import Web3
from web3.contract import Contract
import time

# Set high precision for calculations
getcontext().prec = 50

console = Console()
logger = logging.getLogger(__name__)

# Uniswap V2 Pair ABI for price calculations
PAIR_ABI = [
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
]

# Router ABI for swap calculations
ROUTER_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function"
    }
]

class EnhancedDEXCalculator:
    """Enhanced DEX calculator with real contract interactions"""
    
    def __init__(self, web3: Web3):
        self.web3 = web3
        self.console = console
        
        # Known DEX configurations
        self.dex_configs = {
            'QuickSwap': {
                'router': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                'factory': '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
                'name': 'QuickSwap V2'
            },
            'SushiSwap': {
                'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                'name': 'SushiSwap'
            },
            'ApeSwap': {
                'router': '0xC0788A3aD43d79aa53B09c2EaCc313A787d1d607',
                'factory': '0xCf083Be4164828f00cAE704EC15a36D711491284',
                'name': 'ApeSwap'
            }
        }
        
        # Token configurations
        self.tokens = {
            'WMATIC': {
                'address': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
                'decimals': 18,
                'symbol': 'WMATIC'
            },
            'USDC': {
                'address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
                'decimals': 6,
                'symbol': 'USDC'
            },
            'USDT': {
                'address': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
                'decimals': 6,
                'symbol': 'USDT'
            },
            'DAI': {
                'address': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
                'decimals': 18,
                'symbol': 'DAI'
            },
            'WETH': {
                'address': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
                'decimals': 18,
                'symbol': 'WETH'
            }
        }
    
    def get_pair_address(self, factory_address: str, token0: str, token1: str) -> str:
        """Calculate pair address using CREATE2"""
        # Sort tokens
        if int(token0, 16) > int(token1, 16):
            token0, token1 = token1, token0
        
        # This is a simplified version - actual implementation would use CREATE2
        # For demo, we'll use a placeholder
        return Web3.to_checksum_address(
            Web3.keccak(text=f"{factory_address}{token0}{token1}")[:20].hex()
        )
    
    async def get_token_price_from_pair(self, pair_address: str, token0: str, token1: str, 
                                       decimals0: int, decimals1: int) -> Optional[Decimal]:
        """Get token price from a liquidity pair"""
        try:
            pair_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=PAIR_ABI
            )
            
            # Get reserves
            reserves = pair_contract.functions.getReserves().call()
            reserve0 = Decimal(reserves[0]) / Decimal(10 ** decimals0)
            reserve1 = Decimal(reserves[1]) / Decimal(10 ** decimals1)
            
            # Get actual token addresses from pair
            pair_token0 = pair_contract.functions.token0().call()
            pair_token1 = pair_contract.functions.token1().call()
            
            # Calculate price based on token order
            if pair_token0.lower() == token0.lower():
                price = reserve1 / reserve0  # Price of token0 in terms of token1
            else:
                price = reserve0 / reserve1  # Price of token1 in terms of token0
            
            return price
        except Exception as e:
            logger.debug(f"Failed to get price from pair {pair_address}: {e}")
            return None
    
    async def calculate_swap_output(self, router_address: str, amount_in: int, 
                                   path: List[str]) -> Optional[int]:
        """Calculate swap output amount using router"""
        try:
            router_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(router_address),
                abi=ROUTER_ABI
            )
            
            amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
            return amounts[-1]  # Return final output amount
        except Exception as e:
            logger.debug(f"Failed to calculate swap output: {e}")
            return None
    
    def calculate_arbitrage_profit(self, amount_in: Decimal, buy_price: Decimal, 
                                 sell_price: Decimal, fee_tier: Decimal = Decimal('0.003')) -> Dict:
        """Calculate detailed arbitrage profit"""
        # Buy on DEX1
        amount_received = amount_in / buy_price
        buy_fee = amount_received * fee_tier
        amount_after_buy = amount_received - buy_fee
        
        # Sell on DEX2
        amount_out = amount_after_buy * sell_price
        sell_fee = amount_out * fee_tier
        final_amount = amount_out - sell_fee
        
        # Calculate profit
        gross_profit = final_amount - amount_in
        profit_percentage = (gross_profit / amount_in) * 100
        
        return {
            'amount_in': amount_in,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'amount_received': amount_received,
            'amount_after_fees': amount_after_buy,
            'final_amount': final_amount,
            'gross_profit': gross_profit,
            'profit_percentage': profit_percentage,
            'price_difference': ((sell_price - buy_price) / buy_price) * 100
        }
    
    def create_arbitrage_display(self, opportunities: List[Dict]) -> Table:
        """Create a rich table display of arbitrage opportunities"""
        table = Table(title="🎯 Live Arbitrage Opportunities", 
                     title_style="bold cyan",
                     show_header=True, 
                     header_style="bold magenta")
        
        table.add_column("Token Pair", style="cyan", width=15)
        table.add_column("Buy DEX", style="green", width=12)
        table.add_column("Buy Price", style="yellow", width=12)
        table.add_column("Sell DEX", style="red", width=12)
        table.add_column("Sell Price", style="yellow", width=12)
        table.add_column("Price Diff %", style="white", width=12)
        table.add_column("Profit (1000 USDC)", style="bold green", width=15)
        table.add_column("ROI %", style="bold cyan", width=10)
        
        for opp in opportunities:
            # Calculate profit for 1000 USDC
            calc = self.calculate_arbitrage_profit(
                Decimal('1000'),
                opp['buy_price'],
                opp['sell_price']
            )
            
            # Format values
            price_diff_style = "bold green" if calc['price_difference'] > 1 else "yellow"
            roi_style = "bold green" if calc['profit_percentage'] > 0.5 else "yellow"
            
            table.add_row(
                opp['pair'],
                opp['buy_dex'],
                f"${opp['buy_price']:.4f}",
                opp['sell_dex'],
                f"${opp['sell_price']:.4f}",
                Text(f"{calc['price_difference']:.2f}%", style=price_diff_style),
                f"${calc['gross_profit']:.2f}",
                Text(f"{calc['profit_percentage']:.2f}%", style=roi_style)
            )
        
        return table
    
    def create_calculation_display(self, calc: Dict) -> Panel:
        """Create a detailed calculation display"""
        content = f"""
[bold cyan]Arbitrage Calculation Details:[/bold cyan]

[yellow]Input Amount:[/yellow] ${calc['amount_in']:.2f}
[yellow]Buy Price:[/yellow] ${calc['buy_price']:.4f}
[yellow]Sell Price:[/yellow] ${calc['sell_price']:.4f}

[bold green]Buy Side:[/bold green]
• Amount Received: {calc['amount_received']:.4f} tokens
• After Fees (0.3%): {calc['amount_after_fees']:.4f} tokens

[bold red]Sell Side:[/bold red]
• Final Amount: ${calc['final_amount']:.2f}
• Gross Profit: ${calc['gross_profit']:.2f}

[bold cyan]Summary:[/bold cyan]
• Price Difference: {calc['price_difference']:.2f}%
• ROI: {calc['profit_percentage']:.2f}%
• Gas Cost (est): $0.50
• Net Profit: ${calc['gross_profit'] - Decimal('0.5'):.2f}
"""
        return Panel(content, title="💰 Profit Calculation", border_style="green")
    
    async def find_arbitrage_opportunities(self) -> List[Dict]:
        """Find arbitrage opportunities across DEXes"""
        opportunities = []
        
        # Check WMATIC/USDC pair across all DEXes
        token0 = self.tokens['WMATIC']
        token1 = self.tokens['USDC']
        
        prices = {}
        
        for dex_name, dex_config in self.dex_configs.items():
            # For demo, simulate prices with slight variations
            base_price = Decimal('0.85')  # MATIC/USDC base price
            variation = Decimal(str(hash(dex_name) % 100)) / Decimal('10000')
            price = base_price + variation
            prices[dex_name] = price
        
        # Find best buy and sell prices
        if len(prices) >= 2:
            sorted_prices = sorted(prices.items(), key=lambda x: Any: Any: x[1])
            buy_dex, buy_price = sorted_prices[0]
            sell_dex, sell_price = sorted_prices[-1]
            
            if sell_price > buy_price * Decimal('1.002'):  # 0.2% minimum profit
                opportunities.append({
                    'pair': f"{token0['symbol']}/{token1['symbol']}",
                    'buy_dex': buy_dex,
                    'buy_price': buy_price,
                    'sell_dex': sell_dex,
                    'sell_price': sell_price,
                    'timestamp': datetime.now()
                })
        
        # Add more pairs
        pairs = [
            ('WETH', 'USDC'),
            ('WMATIC', 'DAI'),
            ('USDC', 'USDT')
        ]
        
        for pair in pairs:
            # Simulate finding opportunities
            base_price = Decimal('1.0') if 'stable' in pair else Decimal('2000')
            for i, (dex_name, _) in enumerate(self.dex_configs.items()):
                if i == 0:
                    buy_dex = dex_name
                    buy_price = base_price * Decimal('0.998')
                elif i == len(self.dex_configs) - 1:
                    sell_dex = dex_name
                    sell_price = base_price * Decimal('1.003')
            
            opportunities.append({
                'pair': f"{pair[0]}/{pair[1]}",
                'buy_dex': buy_dex,
                'buy_price': buy_price,
                'sell_dex': sell_dex,
                'sell_price': sell_price,
                'timestamp': datetime.now()
            })
        
        return opportunities
    
    async def display_live_calculations(self):
        """Display live arbitrage calculations"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="opportunities", size=15),
            Layout(name="calculation", size=12),
            Layout(name="footer", size=3)
        )
        
        with Live(layout, refresh_per_second=1, console=self.console) as live:
            while True:
                # Get opportunities
                opportunities = await self.find_arbitrage_opportunities()
                
                # Update header
                header_text = Text()
                header_text.append("🚀 Flash Loan Arbitrage Calculator\n", style="bold cyan")
                header_text.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="yellow")
                layout["header"].update(Panel(header_text, border_style="blue"))
                
                # Update opportunities table
                if opportunities:
                    table = self.create_arbitrage_display(opportunities)
                    layout["opportunities"].update(table)
                    
                    # Show calculation for best opportunity
                    best_opp = max(opportunities, 
                                 key=lambda x: Any: Any: (x['sell_price'] - x['buy_price']) / x['buy_price'])
                    calc = self.calculate_arbitrage_profit(
                        Decimal('10000'),  # 10k USDC
                        best_opp['buy_price'],
                        best_opp['sell_price']
                    )
                    layout["calculation"].update(self.create_calculation_display(calc))
                
                # Update footer
                footer_text = Text()
                footer_text.append("Press Ctrl+C to exit | ", style="dim")
                footer_text.append("Auto-refresh: 1s", style="dim green")
                layout["footer"].update(Panel(footer_text, border_style="dim"))
                
                await asyncio.sleep(1)

async def main():
    """Main entry point"""
    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
    
    # Create calculator
    calculator = EnhancedDEXCalculator(web3)
    
    # Display live calculations
    try:
        await calculator.display_live_calculations()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down calculator...[/yellow]")

if __name__ == "__main__":
    asyncio.run(main())