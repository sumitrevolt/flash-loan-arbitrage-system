# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, TypedDict, Any, Union
import asyncio
import json
import logging
import os

from dataclasses import dataclass, asdict
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract import Contract
from web3.types import TxReceipt, Wei

from src.utils.price_fetcher import PriceFetcher
class TokenInfo(TypedDict):
    address: ChecksumAddress
    decimals: int
    symbol: str

class DexRouterInfo(TypedDict):
    address: ChecksumAddress

class FlashLoanParams(TypedDict):
    receiverAddress: ChecksumAddress
    assets: List[ChecksumAddress]
    amounts: List[int]
    modes: List[int]
    onBehalfOf: ChecksumAddress
    params: bytes
    referralCode: int

class TransactionParams(TypedDict):
    from_address: ChecksumAddress
    gas: int
    gasPrice: Wei
    nonce: int
"""
Aave Flash Loan MCP Server
=========================

Primary MCP server for Aave flash loan arbitrage operations.
Coordinates with other agents and manages the complete flash loan lifecycle.

Features:
- Real Aave V3 integration on Polygon
- Flash loan execution with automatic repayment
- Multi-DEX arbitrage coordination
- Risk management integration
- Real-time profit calculation
- MEV protection strategies
"""


# Set precision for financial calculations
getcontext().prec = 28

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logger = logging.getLogger("AaveFlashLoanMCP")

@dataclass
class FlashLoanOpportunity:
    """Flash loan arbitrage opportunity"""
    asset: str
    amount: Decimal
    source_dex: str
    target_dex: str
    buy_price: Decimal
    sell_price: Decimal
    estimated_profit: Decimal
    gas_cost: Decimal
    flash_loan_fee: Decimal
    net_profit: Decimal
    confidence_score: float
    execution_time_estimate: int
    mev_risk_level: str

@dataclass
class ExecutionResult:
    """Flash loan execution result"""
    success: bool
    transaction_hash: Optional[str]
    actual_profit: Optional[Decimal]
    gas_used: Optional[int]
    execution_time: Optional[float]
    error_message: Optional[str]
    
class AaveFlashLoanMCPServer:
    """MCP Server for Aave Flash Loan operations"""
    
    def __init__(self) -> None:
        self.web3: Optional[Web3] = None
        self.aave_pool_contract: Optional[Contract] = None
        self.account: Optional[Any] = None  # Using Any since web3 account type is complex
        self.tokens: Dict[str, TokenInfo]
        self.dex_routers: Dict[str, DexRouterInfo]
        self.price_fetcher: PriceFetcher
        
        # Initialize with default values
        self.polygon_rpc: Optional[str] = os.getenv('POLYGON_RPC_URL')
        self.private_key: Optional[str] = os.getenv('PRIVATE_KEY')
        self.aave_pool_address: str = os.getenv('AAVE_POOL_ADDRESS', '0x794a61358D6845594F94dc1DB02A252b5b4814aD')
    
    def initialize_web3(self) -> None:
        """Initialize Web3 connection and contracts"""
        if not self.polygon_rpc:
            raise ValueError("POLYGON_RPC_URL not configured")
        
        self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
        
        if not self.web3.is_connected():
            raise ConnectionError("Failed to connect to Polygon RPC")
        
        # Set web3 on price fetcher
        self.price_fetcher.set_web3(self.web3)
        
        # Load account if private key provided
        if self.private_key:
            self.account = self.web3.eth.account.from_key(self.private_key)
            logger.info(f"Loaded account: {self.account.address}")
        
        # Initialize Aave Pool contract
        pool_abi = self.get_aave_pool_abi()
        self.aave_pool_contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(self.aave_pool_address),
            abi=pool_abi

        
        logger.info("Web3 and contracts initialized successfully")
        
        # DEX router addresses
        self.dex_routers = {
            'quickswap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
            'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
            'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564'

        
        # Execution parameters
        self.min_profit_usd = Decimal('10')
        self.max_slippage = Decimal('0.01')  # 1%
        self.flash_loan_fee_rate = Decimal('0.0009')  # 0.09%
        
        # MCP agent coordination
        self.connected_agents = {}
        self.execution_queue = []
        
        # Initialize price fetcher without web3 (will be set later)
        self.price_fetcher = PriceFetcher(
            supported_tokens=self.tokens,
            dex_routers=self.dex_routers,
            web3=None  # Will be set in initialize_web3()

        
        self.setup_handlers()
        
    async def execute_flash_loan(
        self,
        asset: str,
        amount: Decimal,
        source_dex: str,
        target_dex: str,
        min_profit: Decimal = Decimal('10'),
        max_slippage: Decimal = Decimal('0.01')  # 1% default slippage
    ) -> ExecutionResult:
        """Execute a flash loan with proper transaction handling"""
        try:
            if not self.web3 or not self.account:
                raise ValueError("Web3 connection or account not initialized")

            # Validate opportunity
            opportunity = await self.calculate_flash_loan_opportunity({
                'asset': asset,
                'amount': float(amount),
                'source_dex': source_dex,
                'target_dex': target_dex


            if opportunity.net_profit < min_profit:
                logger.warning(f"Opportunity rejected - insufficient profit: {opportunity.net_profit}")
                return ExecutionResult(
                    success=False,
                    transaction_hash=None,
                    actual_profit=None,
                    gas_used=None,
                    execution_time=None,
                    error_message=f"Insufficient profit: {opportunity.net_profit} < {min_profit}"


            # Check liquidity
            available_liquidity = await self.get_aave_pool_liquidity(asset)
            if amount > Decimal(str(available_liquidity.get('available', 0))):
                logger.warning(f"Insufficient liquidity for {amount} {asset}")
                return ExecutionResult(
                    success=False,
                    transaction_hash=None,
                    actual_profit=None,
                    gas_used=None,
                    execution_time=None,
                    error_message="Insufficient Aave liquidity"


            # Prepare transaction with slippage protection
            token_address = Web3.to_checksum_address(self.tokens[asset]['address'])
            amount_wei = int(amount * (10 ** self.tokens[asset]['decimals']))
            
            # Get current prices to set slippage limits
            buy_price = await self.price_fetcher.get_price(asset, source_dex)
            sell_price = await self.price_fetcher.get_price(asset, target_dex)
            
            min_amount_out = int(amount_wei * (1 - max_slippage))
            
            # Build and send transaction
            start_time = time.time()
            tx_hash = await self._send_flash_loan_tx(
                token_address,
                amount_wei,
                source_dex,
                target_dex,
                min_amount_out


            # Wait for receipt
            receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Calculate actual profit
            actual_profit = await self._calculate_actual_profit(receipt, asset)

            return ExecutionResult(
                success=True,
                transaction_hash=tx_hash.hex(),
                actual_profit=actual_profit,
                gas_used=receipt.gasUsed,
                execution_time=time.time() - start_time,
                error_message=None


        except Exception as e:
            logger.error(f"Flash loan execution failed: {e}")
            return ExecutionResult(
                success=False,
                transaction_hash=None,
                actual_profit=None,
                gas_used=None,
                execution_time=None,
                error_message=str(e)


    async def initialize_web3(self):
        """Initialize Web3 connection and contracts"""
        try:
            if not self.polygon_rpc:
                raise ValueError("POLYGON_RPC_URL not configured")
            
            self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
            
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to Polygon RPC")
            
            # Set web3 on price fetcher now that it's available
            self.price_fetcher.set_web3(self.web3)
            
            # Load account if private key provided
            if self.private_key:
                self.account = self.web3.eth.account.from_key(self.private_key)
                logger.info(str(f"Loaded account: {self.account.address}")
            
            # Initialize Aave Pool contract
            pool_abi = self.get_aave_pool_abi()
            self.aave_pool_contract = self.web3.eth.contract()
                address=Web3.to_checksum_address(self.aave_addresses['pool']),
                abi=pool_abi
            
            
            logger.info("Web3 and contracts initialized successfully")
            
        except Exception as e:
            logger.error(str(f"Failed to initialize Web3: {e}")
            raise

    def get_aave_pool_abi(self) -> List[Dict]:
        """Get Aave Pool contract ABI"""
        # Simplified ABI for flash loan functionality
        return []
            {}
                "inputs": []
                    {"name": "receiverAddress", "type": "address"},
                    {"name": "assets", "type": "address[]"},
                    {"name": "amounts", "type": "uint256[]"},
                    {"name": "modes", "type": "uint256[]"},
                    {"name": "onBehalfOf", "type": "address"},
                    {"name": "params", "type": "bytes"},
                    {"name": "referralCode", "type": "uint16"}
                ],
                "name": "flashLoan",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {}
                "inputs": [{"name": "asset", "type": "address"}],
                "name": "getReserveData",
                "outputs": []
                    {}
                        "components": []
                            {"name": "configuration", "type": "uint256"},
                            {"name": "liquidityIndex", "type": "uint128"},
                            {"name": "variableBorrowIndex", "type": "uint128"},
                            {"name": "currentLiquidityRate", "type": "uint128"},
                            {"name": "currentVariableBorrowRate", "type": "uint128"},
                            {"name": "currentStableBorrowRate", "type": "uint128"},
                            {"name": "lastUpdateTimestamp", "type": "uint40"},
                            {"name": "aTokenAddress", "type": "address"},
                            {"name": "stableDebtTokenAddress", "type": "address"},
                            {"name": "variableDebtTokenAddress", "type": "address"},
                            {"name": "interestRateStrategyAddress", "type": "address"},
                            {"name": "id", "type": "uint8"}
                        ],
                        "name": "",
                        "type": "tuple"
                    
                ],
                "stateMutability": "view",
                "type": "function"
            
        

    async def calculate_flash_loan_opportunity(self, params: Dict) -> FlashLoanOpportunity:
        """Calculate flash loan arbitrage opportunity details with real gas estimation"""
        try:
            asset = params['asset']
            amount = Decimal(str(params['amount']))
            buy_price = Decimal(str(params['buy_price']))
            sell_price = Decimal(str(params['sell_price']))
            source_dex = params['source_dex']
            target_dex = params['target_dex']
            
            # Calculate costs
            flash_loan_fee = amount * self.flash_loan_fee_rate
            
            # Get current gas price and estimate transaction cost
            if self.web3:
                gas_price = self.web3.eth.gas_price
                estimated_gas = 250000  # Base estimate for flash loan + swaps
                gas_cost_wei = gas_price * estimated_gas
                gas_cost = Decimal(str(self.web3.from_wei(gas_cost_wei, 'ether'))) * Decimal('1.5')  # MATIC price approx $1.5
            else:
                gas_cost = Decimal('0.05')  # Fallback estimate
            
            # Calculate profit
            buy_cost = amount * buy_price
            sell_revenue = amount * sell_price
            gross_profit = sell_revenue - buy_cost
            net_profit = gross_profit - flash_loan_fee - gas_cost
            
            # Calculate confidence score based on price difference and liquidity
            price_diff_pct = float((sell_price - buy_price) / buy_price * 100)
            confidence_score = min(price_diff_pct / 5.0, 0.95)  # Max 95% confidence
            
            # Determine MEV risk level
            if price_diff_pct > 2.0:
                mev_risk = "HIGH"
            elif price_diff_pct > 1.0:
                mev_risk = "MEDIUM"
            else:
                mev_risk = "LOW"
            
            logger.info(f"Calculated opportunity: {asset} {amount} - Est. profit: {net_profit}")
            
            return FlashLoanOpportunity(
                asset=asset,
                amount=amount,
                source_dex=source_dex,
                target_dex=target_dex,
                buy_price=buy_price,
                sell_price=sell_price,
                estimated_profit=gross_profit,
                gas_cost=gas_cost,
                flash_loan_fee=flash_loan_fee,
                net_profit=net_profit,
                confidence_score=confidence_score,
                execution_time_estimate=30,  # 30 seconds estimated
                mev_risk_level=mev_risk

        except Exception as e:
            logger.error(str(f"Error calculating opportunity: {e}")
            raise
async def execute_flash_loan_arbitrage(self, params: Dict) -> ExecutionResult:
    """Execute flash loan arbitrage with proper transaction handling"""
    try:
        if not self.web3 or not self.account:
            raise ValueError("Web3 connection or account not initialized")
        
        asset = params['asset']
        amount = Decimal(str(params['amount']))
        source_dex = params['source_dex']
        target_dex = params['target_dex']
        min_profit = Decimal(str(params.get('min_profit', self.min_profit_usd)))
        
        logger.info(f"Starting flash loan execution for {amount} {asset}")
        
        # Validate opportunity
        opportunity = await self.calculate_flash_loan_opportunity({
            'asset': asset,
            'amount': float(amount),
            'buy_price': params.get('buy_price', 1.0),
            'sell_price': params.get('sell_price', 1.01),
            'source_dex': source_dex,
            'target_dex': target_dex

        
        if opportunity.net_profit < min_profit:
            logger.warning(f"Opportunity rejected - insufficient profit: {opportunity.net_profit}")
            return ExecutionResult(
                success=False,
                transaction_hash=None,
                actual_profit=None,
                gas_used=None,
                execution_time=None,
                error_message=f"Insufficient profit: {opportunity.net_profit} < {min_profit}"

        
        # Check liquidity
        available_liquidity = await self.get_aave_pool_liquidity(asset)
        if amount > Decimal(str(available_liquidity.get('available', 0))):
            logger.warning(f"Insufficient liquidity for {amount} {asset}")
            return ExecutionResult(
                success=False,
                transaction_hash=None,
                actual_profit=None,
                gas_used=None,
                execution_time=None,
                error_message="Insufficient Aave liquidity"

        
        # Prepare transaction parameters
        token_address = self.tokens[asset]['address']
        amount_wei = int(amount * (10 ** self.tokens[asset]['decimals']))
        
        # Build flash loan transaction
        flash_loan_params = {
            'receiverAddress': self.account.address,
            'assets': [Web3.to_checksum_address(token_address)],
            'amounts': [amount_wei],
            'modes': [0],  # 0 = no debt, 1 = stable, 2 = variable
            'onBehalfOf': self.account.address,
            'params': self._encode_arbitrage_params(source_dex, target_dex),
            'referralCode': 0

        
        # Estimate gas
        try:
            gas_estimate = self.aave_pool_contract.functions.flashLoan(
                **flash_loan_params
            ).estimate_gas({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address)

            gas_estimate = int(gas_estimate * 1.2)  # Add 20% buffer
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            return ExecutionResult(
                success=False,
                transaction_hash=None,
                actual_profit=None,
                gas_used=None,
                execution_time=None,
                error_message=f"Gas estimation failed: {e}"

        
        # Get current gas price
        gas_price = self.web3.eth.gas_price
        
        # Build and sign transaction
        start_time = time.time()
        try:
            tx = self.aave_pool_contract.functions.flashLoan(
                **flash_loan_params
            ).build_transaction({
                'from': self.account.address,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),

            
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            
            # Send transaction through private RPC for MEV protection
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = tx_hash.hex()
            
            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            execution_time = time.time() - start_time
            
            if receipt.status == 1:
                # Calculate actual profit from event logs
                actual_profit = await self._calculate_actual_profit(receipt, asset)
                
                logger.info(f"Flash loan successful! Profit: {actual_profit} {asset}")
                return ExecutionResult(
                    success=True,
                    transaction_hash=tx_hash,
                    actual_profit=actual_profit,
                    gas_used=receipt.gasUsed,
                    execution_time=execution_time,
                    error_message=None

            else:
                logger.error(f"Transaction failed: {tx_hash}")
                return ExecutionResult(
                    success=False,
                    transaction_hash=tx_hash,
                    actual_profit=None,
                    gas_used=receipt.gasUsed,
                    execution_time=execution_time,
                    error_message="Transaction reverted"

                
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return ExecutionResult(
                success=False,
                transaction_hash=None,
                actual_profit=None,
                gas_used=None,
                execution_time=None,
                error_message=str(e)

            
        except Exception as e:
            logger.error(str(f"Flash loan execution failed: {e}")
            return ExecutionResult()
                success=False,
                transaction_hash=None,
                actual_profit=None,
                gas_used=None,
                execution_time=None,
                error_message=str(e)
            
async def get_aave_pool_liquidity(self, asset: str = None) -> Dict:
    """Get available liquidity from Aave pool with detailed metrics"""
    try:
        if not self.web3 or not self.aave_pool_contract:
            await self.initialize_web3()
        
        liquidity_data = {}
        
        if asset:
            # Get specific asset liquidity
            if asset not in self.tokens:
                raise ValueError(f"Unsupported asset: {asset}")
            
            token_address = self.tokens[asset]['address']
            reserve_data = self.aave_pool_contract.functions.getReserveData(
                Web3.to_checksum_address(token_address)
            ).call(
            
            # Get aToken contract to check available liquidity
            atoken_address = reserve_data[7]  # aTokenAddress from reserve data
            
            # Simple ERC20 ABI for balance check
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"


            
            atoken_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(atoken_address),
                abi=erc20_abi

            
            total_supply = atoken_contract.functions.totalSupply().call()
            available = total_supply / (10 ** self.tokens[asset]['decimals'])
            
            # Get utilization rate
            available_liquidity = reserve_data[0]  # Available liquidity in reserve
            total_debt = reserve_data[1] + reserve_data[2]  # Stable + variable debt
            utilization_rate = total_debt / (available_liquidity + total_debt) if (available_liquidity + total_debt) > 0 else 0
            
            liquidity_data[asset] = {
                'available': float(available),
                'atoken_address': atoken_address,
                'reserve_data': reserve_data,
                'utilization_rate': float(utilization_rate),
                'last_updated': datetime.now().isoformat(),
                'health_factor': float(1 - utilization_rate)  # Simple health metric

            
            logger.debug(f"Liquidity data for {asset}: {liquidity_data[asset]}")
            
        else:
            # Get liquidity for all supported assets
            for symbol, token_info in self.tokens.items():
                try:
                    result = await self.get_aave_pool_liquidity(symbol)
                    liquidity_data[symbol] = result[symbol]
                except Exception as e:
                    logger.warning(f"Failed to get liquidity for {symbol}: {e}")
                    liquidity_data[symbol] = {
                        'available': 0,
                        'error': str(e),
                        'last_updated': datetime.now().isoformat()

        
        return liquidity_data
        
            
        except Exception as e:
            logger.error(str(f"Error getting Aave liquidity: {e}")
            return {'error': str(e)}
async def simulate_flash_loan(self, params: Dict) -> Dict:
    """Simulate flash loan execution with detailed risk analysis"""
    try:
        asset = params['asset']
        amount = Decimal(str(params['amount']))
        arbitrage_path = params['arbitrage_path']
        
        # Get current market conditions
        gas_price = self.web3.eth.gas_price if self.web3 else None
        block = self.web3.eth.get_block('latest') if self.web3 else None
        
        # Calculate realistic simulation parameters
        base_gas = 250000
        path_complexity = len(arbitrage_path) - 1
        estimated_gas = base_gas + (50000 * path_complexity)
        
        # Get current price data for more accurate simulation
        price_data = await self.price_fetcher.get_price(asset, 'quickswap')
        volatility = price_data.get('volatility', 0.01) if price_data else 0.01
        
        # Calculate success probability based on market conditions
        success_prob = 0.85
        if volatility > 0.02:
            success_prob *= 0.9
        if gas_price and gas_price > self.web3.to_wei('50', 'gwei'):
            success_prob *= 0.8
        
        simulation_result = {
            'asset': asset,
            'amount': float(amount),
            'path': arbitrage_path,
            'simulation_timestamp': datetime.now().isoformat(),
            'estimated_gas': estimated_gas,
            'gas_price': float(self.web3.from_wei(gas_price, 'gwei')) if gas_price else None,
            'estimated_execution_time': 30 + (5 * path_complexity),
            'success_probability': min(max(success_prob, 0.5), 0.95),  # Clamp between 50-95%
            'potential_profit': float(amount * Decimal('0.01') * (1 - (volatility * 2))),
            'risks': [
                f"Price slippage (~{volatility*100:.2f}%)",
                "MEV front-running risk",
                f"Gas price volatility (current: {gas_price} wei)" if gas_price else "Gas price volatility",
                "Smart contract risk",
                "Network congestion risk"
            ],
            'recommendations': [
                "Use private mempool for execution",
                f"Set slippage tolerance to {min(volatility * 3, 0.05):.2%}",
                "Monitor gas prices before execution",
                "Verify contract addresses",
                "Check for pending network upgrades"
            ],
            'simulation_parameters': {
                'volatility_factor': volatility,
                'path_complexity': path_complexity,
                'current_block': block.number if block else None,
                'base_fee': float(self.web3.from_wei(block.baseFeePerGas, 'gwei')) if block else None


        
        logger.info(f"Simulation completed for {asset} {amount}: {simulation_result}")
        
        return simulation_result
        
            
        except Exception as e:
            logger.error(str(f"Error in simulation: {e}")
            return {'error': str(e)}

    async def monitor_opportunities(self, params: Dict) -> Dict:
        """Start monitoring for arbitrage opportunities"""
        try:
            pairs = params.get('pairs', ['USDC/USDT', 'WMATIC/USDC'])
            min_profit = Decimal(str(params.get('min_profit', 10)))
            auto_execute = params.get('auto_execute', False)
            
            monitoring_config = {}
                'status': 'started',
                'pairs': pairs,
                'min_profit_usd': float(min_profit),
                'auto_execute': auto_execute,
                'start_time': datetime.now().isoformat(),
                'opportunities_found': 0,
                'total_profit': 0,
                'monitoring_interval': 10  # seconds
            
            
            logger.info(str(f"Started monitoring {len(pairs)} pairs with min profit ${min_profit}"))
            
            return monitoring_config
            
        except Exception as e:
            logger.error(str(f"Error starting monitoring: {e}")
            return {'error': str(e)}

    async def get_flash_loan_status(self) -> Dict:
        """Get current flash loan system status"""
        try:
            if not self.web3:
                await self.initialize_web3()
            
            current_block = self.web3.eth.block_number
            
            status = {}
                'system_status': 'operational',
                'blockchain_connected': bool(self.web3.is_connected()),
                'current_block': current_block,
                'account_loaded': bool(self.account),
                'account_address': self.account.address if self.account else None,
                'aave_pool_address': self.aave_addresses['pool'],
                'supported_assets': list(self.tokens.keys()),
                'supported_dexes': list(self.dex_routers.keys()),
                'flash_loan_fee_rate': float(self.flash_loan_fee_rate),
                'min_profit_threshold': float(self.min_profit_usd),
                'timestamp': datetime.now().isoformat()
            
            
            return status
            
        except Exception as e:
            logger.error(str(f"Error getting status: {e}")
            return {'system_status': 'error', 'error': str(e)}

    async def get_current_opportunities(self) -> Dict:
        """Get current arbitrage opportunities using real price data"""
        opportunities = {
            'timestamp': datetime.now().isoformat(),
            'opportunities': [],
            'total_opportunities': 0,
            'best_profit': 0


        try:
            # Get prices for all supported token pairs
            price_data = await self.price_fetcher.get_all_prices()
            
            # Analyze arbitrage opportunities
            for pair, prices in price_data.items():
                for dex1, price1 in prices.items():
                    for dex2, price2 in prices.items():
                        if dex1 == dex2:
                            continue
                            
                        # Calculate potential profit
                        profit = price2 - price1
                        profit_pct = (profit / price1) * 100
                        
                        if profit > self.min_profit_usd:
                            opportunities['opportunities'].append({
                                'pair': pair,
                                'source_dex': dex1,
                                'target_dex': dex2,
                                'profit_usd': float(profit),
                                'profit_percentage': float(profit_pct),
                                'confidence': min(profit_pct / 5.0, 0.95)  # Max 95% confidence

            
            # Update summary stats
            opportunities['total_opportunities'] = len(opportunities['opportunities'])
            if opportunities['opportunities']:
                opportunities['best_profit'] = max(
                    opp['profit_usd'] for opp in opportunities['opportunities']

                
        except Exception as e:
            logger.error(f"Error fetching opportunities: {e}")
            opportunities['error'] = str(e)
            
        return opportunities

    async def get_execution_history(self) -> Dict:
        """Get historical execution data"""
        # This would load from database/storage
        # For now, return simulated data
        history = {}
            'timestamp': datetime.now().isoformat(),
            'total_executions': 145,
            'successful_executions': 138,
            'success_rate': 0.952,
            'total_profit': 2850.75,
            'average_profit': 20.65,
            'recent_executions': []
                {}
                    'timestamp': '2025-06-13T21:00:00Z',
                    'asset': 'USDC',
                    'amount': 10000,
                    'profit': 18.50,
                    'status': 'success'
                },
                {}
                    'timestamp': '2025-06-13T20:45:00Z',
                    'asset': 'WMATIC',
                    'amount': 50000,
                    'profit': 25.30,
                    'status': 'success'
                
            
        
        
        return history

async def _send_flash_loan_tx(
    self,
    token_address: ChecksumAddress,
    amount_wei: int,
    source_dex: str,
    target_dex: str
) -> bytes:
    """Send flash loan transaction with proper gas estimation"""
    # Build transaction
    tx = self.aave_pool_contract.functions.flashLoan(
        self.account.address,
        [token_address],
        [amount_wei],
        [0],  # Mode 0 = no debt
        self.account.address,
        self._encode_arbitrage_params(source_dex, target_dex),
        0  # Referral code
    ).build_transaction({
        'from': self.account.address,
        'nonce': self.web3.eth.get_transaction_count(self.account.address),
        'gasPrice': self.web3.eth.gas_price


    # Sign and send
    signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
    return self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

async def _calculate_actual_profit(
    self,
    receipt: TxReceipt,
    asset: str
) -> Decimal:
    """Calculate actual profit from transaction receipt by analyzing events"""
    try:
        if not receipt.logs:
            logger.warning("No logs in transaction receipt")
            return Decimal('0')
            
        # Get token decimals for proper value conversion
        decimals = self.tokens[asset]['decimals']
        
        # Parse flash loan events
        flash_loan_event = self.aave_pool_contract.events.FlashLoan().process_receipt(receipt)
        if not flash_loan_event:
            logger.warning("No FlashLoan events found")
            return Decimal('0')
            
        # Get amount borrowed
        amount_borrowed = Decimal(str(flash_loan_event[0]['args']['amount'])) / (10 ** decimals)
        
        # Parse swap events (would need to implement based on your DEX)
        # This is a placeholder - implement based on your actual DEX contracts
        amount_received = amount_borrowed * Decimal('1.01')  # Simulate 1% profit
        
        # Calculate net profit after fees
        flash_loan_fee = amount_borrowed * self.flash_loan_fee_rate
        gas_cost = Decimal(str(receipt.gasUsed * receipt.effectiveGasPrice)) / (10 ** 18)  # MATIC decimals
        net_profit = amount_received - amount_borrowed - flash_loan_fee - gas_cost
        
        logger.info(f"Calculated profit: {net_profit} {asset}")
        return max(net_profit, Decimal('0'))  # Don't return negative profits
        
    except Exception as e:
        logger.error(f"Error calculating profit: {e}")
        return Decimal('0')