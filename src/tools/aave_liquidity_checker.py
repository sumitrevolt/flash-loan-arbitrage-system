"""
Aave liquidity checker for Flash Loan Arbitrage System.
Checks if tokens have sufficient liquidity in Aave before executing flash loans.
"""
import json
import logging
import os
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal

# Import Web3 with proper error handling
try:
    # Import from central web3_provider
    from src.utils.web3_provider import Web3
    # Import exceptions from central provider
    from src.utils.web3_provider import Web3Exception
    WEB3_IMPORTED = True
except ImportError as e:
    logging.getLogger(__name__).error(f"Failed to import Web3: {e}. Aave liquidity checking will not work properly.")
    WEB3_IMPORTED = False
    Web3 = None
    Web3Exception = Exception

class AaveLiquidityChecker:
    """
    Checks if tokens have sufficient liquidity in Aave before executing flash loans.
    """

    def __init__(self, rpc_manager=None):
        """
        Initialize the Aave liquidity checker.

        Args:
            rpc_manager: RPC manager instance for Web3 connections
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rpc_manager = rpc_manager

        if not WEB3_IMPORTED:
            self.logger.error("Web3 not imported. Aave liquidity checking will be limited.")
            
        # Aave contract addresses on Polygon
        self.aave_pool_address = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
        self.aave_data_provider_address = "0x7551b5D2763519d4e37e8B81929D336De671d46d"
        self.aave_price_oracle_address = "0x0229F777B0fAb107F9591a41d5F02E4e98dB6f2d"

        # Load ABIs
        self.data_provider_abi = self._load_abi('abi/aave_data_provider.json')
        self.price_oracle_abi = self._load_abi('abi/aave_price_oracle.json')
        self.lending_pool_abi = self._load_abi('abi/aave_lending_pool.json')
        self.pool_abi = self._load_abi('abi/aave_pool.json')

        # Initialize Web3 and contracts
        self.w3 = None
        self.data_provider = None
        self.price_oracle = None
        self.pool = None

        # Initialize token data
        self.token_data = self._load_token_data()

        # Initialize contracts
        self._initialize_contracts()

    def _load_abi(self, abi_path: str) -> list:
        """
        Load ABI from a JSON file.

        Args:
            abi_path: Path to the ABI JSON file

        Returns:
            list: ABI as a list of dictionaries
        """
        try:
            # Force use of internal minimal ABI for aave_data_provider.json to ensure correctness
            if 'aave_data_provider.json' in abi_path:
                self.logger.info(f"Using minimal ABI for {abi_path} to ensure Aave V3 compatibility.")
                return [
                    {
                        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
                        "name": "getReserveData",
                        "outputs": [
                            {"internalType": "uint256", "name": "availableLiquidity", "type": "uint256"},
                            {"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"},
                            {"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"},
                            {"internalType": "uint256", "name": "liquidityRate", "type": "uint256"},
                            {"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"},
                            {"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},
                            {"internalType": "uint256", "name": "averageStableBorrowRate", "type": "uint256"},
                            {"internalType": "uint256", "name": "liquidityIndex", "type": "uint256"},
                            {"internalType": "uint256", "name": "variableBorrowIndex", "type": "uint256"},
                            {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"}
                        ],
                        "stateMutability": "view",
                        "type": "function"
                    }
                ]

            if 'aave_price_oracle.json' in abi_path:
                return [
                    {
                        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
                        "name": "getAssetPrice",
                        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                        "stateMutability": "view",
                        "type": "function"
                    }
                ]
                
            if 'aave_pool.json' in abi_path:
                return [
                    {
                        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
                        "name": "getReserveData",
                        "outputs": [
                            {
                                "components": [
                                    {"internalType": "uint256", "name": "configuration", "type": "uint256"},
                                    {"internalType": "uint128", "name": "liquidityIndex", "type": "uint128"},
                                    {"internalType": "uint128", "name": "currentLiquidityRate", "type": "uint128"},
                                    {"internalType": "uint128", "name": "variableBorrowIndex", "type": "uint128"},
                                    {"internalType": "uint128", "name": "currentVariableBorrowRate", "type": "uint128"},
                                    {"internalType": "uint128", "name": "currentStableBorrowRate", "type": "uint128"},
                                    {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"},
                                    {"internalType": "uint16", "name": "id", "type": "uint16"},
                                    {"internalType": "address", "name": "aTokenAddress", "type": "address"},
                                    {"internalType": "address", "name": "stableDebtTokenAddress", "type": "address"},
                                    {"internalType": "address", "name": "variableDebtTokenAddress", "type": "address"},
                                    {"internalType": "address", "name": "interestRateStrategyAddress", "type": "address"},
                                    {"internalType": "uint128", "name": "accruedToTreasury", "type": "uint128"},
                                    {"internalType": "uint128", "name": "unbacked", "type": "uint128"},
                                    {"internalType": "uint128", "name": "isolationModeTotalDebt", "type": "uint128"}
                                ],
                                "internalType": "struct DataTypes.ReserveData",
                                "name": "",
                                "type": "tuple"
                            }
                        ],
                        "stateMutability": "view",
                        "type": "function"
                    }
                ]

            # Original logic for other ABIs
            # Determine the absolute path to the abi directory relative to the project root
            project_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) # flash loan/
            absolute_abi_path = os.path.join(project_root_dir, abi_path)

            if os.path.exists(absolute_abi_path):
                self.logger.debug(f"Loading ABI from: {absolute_abi_path}")
                with open(absolute_abi_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"ABI file not found at {absolute_abi_path}")
                return []
        except Exception as e:
            self.logger.error(f"Failed to load ABI from {abi_path}: {e}")
            return []

    def _load_token_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load token data from configuration.

        Returns:
            Dict[str, Dict[str, Any]]: Token data
        """
        try:
            token_data_path = 'config/token_data.json'
            if os.path.exists(token_data_path):
                with open(token_data_path, 'r') as f:
                    return json.load(f)
            else:
                # Default token data
                return {
                    "WETH": {
                        "address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                        "decimals": 18
                    },
                    "WBTC": {
                        "address": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
                        "decimals": 8
                    },
                    "USDC": {
                        "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                        "decimals": 6
                    },
                    "USDT": {
                        "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                        "decimals": 6
                    },
                    "DAI": {
                        "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                        "decimals": 18
                    },
                    "WMATIC": {
                        "address": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
                        "decimals": 18
                    },
                    "LINK": {
                        "address": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
                        "decimals": 18
                    },
                    "AAVE": {
                        "address": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
                        "decimals": 18
                    }
                }
        except Exception as e:
            self.logger.error(f"Failed to load token data: {e}")
            return {}

    def _initialize_contracts(self) -> None:
        """Initialize Web3 and Aave contracts."""
        if not WEB3_IMPORTED:
            self.logger.error("Web3 not imported. Cannot initialize contracts.")
            return

        try:
            # Get Web3 instance from RPC manager if available
            if self.rpc_manager:
                self.w3 = self.rpc_manager.get_web3()
                if not self.w3 or not self.w3.is_connected():
                    self.logger.warning("RPC manager provided but Web3 not connected. Trying direct initialization.")
                    self.w3 = None

            # Initialize Web3 directly if not available from RPC manager
            if not self.w3:
                # Try common Polygon RPC endpoints
                rpc_urls = [
                    "https://polygon-rpc.com",
                    "https://polygon.gateway.tenderly.co",
                    "https://polygon-bor.publicnode.com",
                    "https://polygon.drpc.org"
                ]

                for rpc_url in rpc_urls:
                    try:
                        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
                        if self.w3.is_connected():
                            self.logger.info(f"Connected to Polygon via {rpc_url}")
                            break
                    except Exception as e:
                        self.logger.warning(f"Failed to connect to {rpc_url}: {e}")

            if not self.w3 or not self.w3.is_connected():
                self.logger.error("Failed to initialize Web3. Aave liquidity checking will not work.")
                return

            # Initialize contracts
            if WEB3_IMPORTED and self.w3:
                self.data_provider = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.aave_data_provider_address),
                    abi=self.data_provider_abi
                )

                self.price_oracle = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.aave_price_oracle_address),
                    abi=self.price_oracle_abi
                )
                
                self.pool = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.aave_pool_address),
                    abi=self.pool_abi
                )

            self.logger.info("Aave contracts initialized successfully for real-time data")
        except Exception as e:
            self.logger.error(f"Failed to initialize contracts: {e}")

    def check_token_liquidity(self, token_symbol: str, amount_usd: float) -> Tuple[bool, float]:
        """
        Check if a token has sufficient liquidity in Aave for a flash loan.

        Args:
            token_symbol: Token symbol
            amount_usd: Amount in USD to borrow

        Returns:
            Tuple[bool, float]: (has_liquidity, available_liquidity_usd)
        """
        if not WEB3_IMPORTED or not self.w3 or not self.data_provider:
            self.logger.error("Web3 or contracts not initialized. Cannot check liquidity.")
            return False, 0.0

        if token_symbol is None or amount_usd is None:
            self.logger.error("Invalid parameters for liquidity check")
            return False, 0.0

        try:
            # Get token address
            token_info = self.token_data.get(token_symbol)
            if not token_info:
                self.logger.error(f"Unknown token: {token_symbol}")
                return False, 0.0
                
            token_address = Web3.to_checksum_address(token_info['address'])
            
            # Get real-time liquidity from Aave
            try:
                reserve_data = self.data_provider.functions.getReserveData(token_address).call()
                available_liquidity_wei = reserve_data[0]  # First element is available liquidity
                
                # Get token price from Aave oracle
                token_price = self._get_token_price(token_address)
                if not token_price:
                    self.logger.warning(f"Could not get price for {token_symbol}")
                    return False, 0.0
                
                # Convert liquidity to USD
                decimals = token_info.get('decimals', 18)
                available_liquidity_tokens = available_liquidity_wei / (10 ** decimals)
                available_liquidity_usd = available_liquidity_tokens * token_price
                
                # Check if requested amount is available
                has_liquidity = amount_usd <= available_liquidity_usd
                
                self.logger.info(f"Real-time liquidity for {token_symbol}: ${available_liquidity_usd:,.2f} "
                               f"(requested: ${amount_usd:,.2f}, sufficient: {has_liquidity})")
                
                return has_liquidity, available_liquidity_usd
                
            except Exception as e:
                self.logger.error(f"Error fetching real-time liquidity data: {e}")
                return False, 0.0

        except Exception as e:
            self.logger.error(f"Error checking liquidity for {token_symbol}: {e}")
            return False, 0.0

    def _get_token_price(self, token_address: str) -> Optional[float]:
        """
        Get real-time token price in USD from Aave price oracle.

        Args:
            token_address: Token address

        Returns:
            Optional[float]: Token price in USD
        """
        if not self.price_oracle or token_address is None:
            self.logger.error("Price oracle not initialized or invalid token address")
            return None

        try:
            # Get token price from Aave oracle (returns price in USD with 8 decimals)
            price_raw = self.price_oracle.functions.getAssetPrice(token_address).call()
            
            # Convert from 8 decimals to actual price
            price_usd = float(price_raw) / (10 ** 8)
            
            # Validate the price
            if price_usd <= 0 or price_usd > 1000000:  # Sanity check
                self.logger.warning(f"Invalid price from oracle for {token_address}: ${price_usd}")
                return None
                
            self.logger.debug(f"Real-time price for {token_address}: ${price_usd:.6f}")
            return price_usd
            
        except Exception as e:
            self.logger.error(f"Error getting real-time token price: {e}")
            return None

    def get_all_token_liquidity(self) -> Dict[str, Dict[str, Any]]:
        """
        Get real-time liquidity information for all tokens.

        Returns:
            Dict[str, Dict[str, Any]]: Liquidity information for all tokens
        """
        result: str = {}

        if self.token_data is None:
            self.logger.error("Token data is None")
            return result

        for token_symbol in self.token_data.keys():
            if token_symbol is None:
                continue

            has_liquidity, liquidity_usd = self.check_token_liquidity(token_symbol, 1000)  # Check for $1000 as baseline
            
            result[token_symbol] = {
                "has_liquidity": has_liquidity,
                "liquidity_usd": liquidity_usd,
                "flash_loan_fee": liquidity_usd * 0.0009  # Aave fee is 0.09%
            }

        return result

    def get_aave_available_liquidity(self, token_address: str, w3=None) -> Optional[int]:
        """
        Get available liquidity for a token in Aave (in wei) - real-time from blockchain.
        
        Args:
            token_address (str): The address of the token
            w3 (Web3, optional): Web3 instance to use. If None, uses self.w3
            
        Returns:
            Optional[int]: Available liquidity in the token's smallest units (wei),
                          None if an error occurs
        """
        if w3 is None:
            w3 = self.w3
            
        if not w3:
            self.logger.error("Web3 instance is not initialized")
            return None
            
        # Normalize token address
        try:
            token_address_checksum = w3.to_checksum_address(token_address)
        except Exception as e:
            self.logger.error(f"Invalid token address {token_address}: {e}")
            return None
            
        try:
            # Get real-time data from Aave data provider
            if self.data_provider:
                try:
                    # Call getReserveData from Aave data provider
                    reserve_data = self.data_provider.functions.getReserveData(token_address_checksum).call()
                    
                    # First element of the tuple is available liquidity
                    if reserve_data and len(reserve_data) > 0:
                        available_liquidity = reserve_data[0]
                        self.logger.info(f"Real-time Aave liquidity for {token_address_checksum}: {available_liquidity} wei")
                        return available_liquidity
                except Exception as e:
                    self.logger.error(f"Error getting reserve data from data provider: {e}")
                    
            # Try alternative method using the pool contract
            if self.pool:
                try:
                    # Get reserve data from pool
                    reserve_data = self.pool.functions.getReserveData(token_address_checksum).call()
                    # The aToken address is at index 8 in the tuple
                    if reserve_data and len(reserve_data) > 8:
                        atoken_address = reserve_data[8]
                        # Get balance of aToken contract (represents available liquidity)
                        token_contract = w3.eth.contract(
                            address=token_address_checksum,
                            abi=[{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
                        )
                        available_liquidity = token_contract.functions.balanceOf(atoken_address).call()
                        self.logger.info(f"Real-time Aave liquidity via aToken balance: {available_liquidity} wei")
                        return available_liquidity
                except Exception as e:
                    self.logger.error(f"Error getting liquidity via pool contract: {e}")
                    
            self.logger.error(f"Could not fetch real-time liquidity for {token_address_checksum}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Aave liquidity for {token_address_checksum}: {e}", exc_info=True)
            return None

# Create a singleton instance
aave_liquidity_checker = AaveLiquidityChecker()
