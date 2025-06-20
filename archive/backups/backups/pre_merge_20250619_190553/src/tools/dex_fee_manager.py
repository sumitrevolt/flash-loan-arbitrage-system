"""
DEX Fee Manager for Flash Loan Arbitrage System.
Handles dynamic fee calculations for different DEXes and token pairs.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, Tuple

class DexFeeManager:
    """
    Manages DEX fees for different exchanges and token pairs.
    Provides dynamic fee calculation based on DEX version and token pair.
    """

    def __init__(self, config_path: str = "config/dex_fee_config.json"):
        """
        Initialize the DEX fee manager.

        Args:
            config_path: Path to the DEX fee configuration file
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_path = config_path
        self.config = self._load_config()
        self.default_fees = self.config.get("default_fees", {})
        self.token_pair_fees = self.config.get("token_pair_fees", {})
        self.dex_versions = self.config.get("dex_versions", {})
        self.aave_fee = self.config.get("aave_fee", 0.0009)  # Default to 0.09%
        self.pool_addresses = self.config.get("pool_addresses", {})

    def _load_config(self) -> Dict[str, Any]:
        """
        Load the DEX fee configuration from file.

        Returns:
            Dict[str, Any]: DEX fee configuration
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"DEX fee configuration file not found at {self.config_path}. Using default values.")
                return {
                    "default_fees": {
                        "uniswap": {"v2": 0.003, "v3": {"default": 0.003}},
                        "sushiswap": {"default": 0.003},
                        "quickswap": {"v2": 0.003, "v3": {"default": 0.003}}
                    },
                    "aave_fee": 0.0009,
                    "dex_versions": {
                        "uniswap": "v3",
                        "sushiswap": "v2",
                        "quickswap": "v2"
                    }
                }
        except Exception as e:
            self.logger.error(f"Error loading DEX fee configuration: {e}")
            return {
                "default_fees": {
                    "uniswap": {"v2": 0.003, "v3": {"default": 0.003}},
                    "sushiswap": {"default": 0.003},
                    "quickswap": {"v2": 0.003, "v3": {"default": 0.003}}
                },
                "aave_fee": 0.0009,
                "dex_versions": {
                    "uniswap": "v3",
                    "sushiswap": "v2",
                    "quickswap": "v2"
                }
            }

    def get_dex_version(self, dex_name: str) -> str:
        """
        Get the version of a DEX.

        Args:
            dex_name: Name of the DEX (lowercase)

        Returns:
            str: DEX version (e.g., 'v2', 'v3')
        """
        dex_name = dex_name.lower()
        return self.dex_versions.get(dex_name, "v2")

    def get_fee_for_token_pair(self, token1: str, token2: str, dex_name: str) -> float:
        """
        Get the fee for a specific token pair on a DEX.

        Args:
            token1: First token symbol
            token2: Second token symbol
            dex_name: Name of the DEX (lowercase)

        Returns:
            float: Fee as a decimal (e.g., 0.003 for 0.3%)
        """
        dex_name = dex_name.lower()
        token1, token2 = token1.upper(), token2.upper()
        
        # Try both token orderings
        pair_key = f"{token1}-{token2}"
        reverse_pair_key = f"{token2}-{token1}"
        
        # Get DEX version
        dex_version = self.get_dex_version(dex_name)
        
        # Check if we have a specific fee for this token pair
        if pair_key in self.token_pair_fees:
            dex_fees = self.token_pair_fees[pair_key].get(dex_name, {})
            if dex_version in dex_fees:
                return dex_fees[dex_version]
        
        # Try reverse order
        if reverse_pair_key in self.token_pair_fees:
            dex_fees = self.token_pair_fees[reverse_pair_key].get(dex_name, {})
            if dex_version in dex_fees:
                return dex_fees[dex_version]
        
        # Fall back to default fees for the DEX and version
        if dex_name in self.default_fees:
            dex_defaults = self.default_fees[dex_name]
            if isinstance(dex_defaults, dict):
                if dex_version in dex_defaults:
                    version_defaults = dex_defaults[dex_version]
                    if isinstance(version_defaults, dict):
                        return version_defaults.get("default", 0.003)
                    return version_defaults
            return dex_defaults.get("default", 0.003)
        
        # Ultimate fallback
        self.logger.warning(f"No fee configuration found for {dex_name} {dex_version}, using default 0.3%")
        return 0.003

    def get_fee_for_single_token(self, token: str, dex_name: str) -> float:
        """
        Get the fee for a single token on a DEX.
        Uses WETH as the paired token for fee lookup.

        Args:
            token: Token symbol
            dex_name: Name of the DEX (lowercase)

        Returns:
            float: Fee as a decimal (e.g., 0.003 for 0.3%)
        """
        # For single tokens, we typically pair with WETH for fee lookup
        return self.get_fee_for_token_pair(token, "WETH", dex_name)

    def get_aave_fee(self) -> float:
        """
        Get the Aave flash loan fee.

        Returns:
            float: Aave fee as a decimal (e.g., 0.0009 for 0.09%)
        """
        return self.aave_fee

    def calculate_fees(self, token: str, buy_dex: str, sell_dex: str, amount_usd: float) -> Dict[str, float]:
        """
        Calculate all fees for an arbitrage transaction.

        Args:
            token: Token symbol
            buy_dex: Buy DEX name
            sell_dex: Sell DEX name
            amount_usd: Transaction amount in USD

        Returns:
            Dict[str, float]: Fee breakdown
        """
        buy_dex = buy_dex.lower()
        sell_dex = sell_dex.lower()
        
        buy_fee_rate = self.get_fee_for_single_token(token, buy_dex)
        sell_fee_rate = self.get_fee_for_single_token(token, sell_dex)
        aave_fee_rate = self.get_aave_fee()
        
        buy_fee_usd = amount_usd * buy_fee_rate
        sell_fee_usd = amount_usd * sell_fee_rate  # Approximation, actual sell amount may differ
        aave_fee_usd = amount_usd * aave_fee_rate
        
        total_fees_usd = buy_fee_usd + sell_fee_usd + aave_fee_usd
        
        return {
            "buy_dex_fee_usd": buy_fee_usd,
            "sell_dex_fee_usd": sell_fee_usd,
            "aave_fee_usd": aave_fee_usd,
            "total_fees_usd": total_fees_usd,
            "buy_fee_rate": buy_fee_rate,
            "sell_fee_rate": sell_fee_rate,
            "aave_fee_rate": aave_fee_rate
        }

    def get_best_pool_fee_tier(self, token1: str, token2: str, dex_name: str) -> int:
        """
        Get the best fee tier for a token pair on a DEX.
        For Uniswap V3 and similar DEXes with multiple fee tiers.

        Args:
            token1: First token symbol
            token2: Second token symbol
            dex_name: Name of the DEX (lowercase)

        Returns:
            int: Fee tier in basis points (e.g., 3000 for 0.3%)
        """
        dex_name = dex_name.lower()
        token1, token2 = token1.upper(), token2.upper()
        
        # Try both token orderings
        pair_key = f"{token1}-{token2}"
        reverse_pair_key = f"{token2}-{token1}"
        
        # Default fee tier (0.3%)
        default_fee_tier = 3000
        
        # Check if we have pool addresses for this DEX
        if dex_name not in self.pool_addresses:
            return default_fee_tier
        
        # Get DEX version
        dex_version = self.get_dex_version(dex_name)
        
        # Check if we have pool addresses for this version
        if dex_version not in self.pool_addresses[dex_name]:
            return default_fee_tier
        
        # Check if we have pool addresses for this token pair
        pools = self.pool_addresses[dex_name][dex_version]
        if pair_key in pools:
            # Return the first fee tier (assuming it's the best)
            try:
                return int(next(iter(pools[pair_key].keys())))
            except StopIteration:
                # Handle case where keys() is empty
                self.logger.warning(f"Empty fee tier list for {pair_key} in {dex_name} {dex_version}")
        
        # Try reverse order
        if reverse_pair_key in pools:
            # Return the first fee tier (assuming it's the best)
            try:
                return int(next(iter(pools[reverse_pair_key].keys())))
            except StopIteration:
                # Handle case where keys() is empty
                self.logger.warning(f"Empty fee tier list for {reverse_pair_key} in {dex_name} {dex_version}")
        
        # Default to 0.3% fee tier
        return default_fee_tier

# Create a singleton instance
dex_fee_manager = DexFeeManager()
