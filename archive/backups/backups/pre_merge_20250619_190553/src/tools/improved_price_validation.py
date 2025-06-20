"""
Improved price validation module for Flash Loan Arbitrage System.
Provides enhanced validation for token prices across different DEXes.
"""

import logging
from typing import Dict, Tuple, List, Any, Optional
import statistics

# Configure logging
logger = logging.getLogger(__name__)

# Define problematic token symbols that need special handling
PROBLEMATIC_TOKENS = {
    "COMP": {
        "max_deviation": 100.0,  # Allow 100% deviation for COMP
        "min_valid_price": 30.0,  # Minimum valid price for COMP
        "max_valid_price": 500.0,  # Maximum valid price for COMP
        "known_bad_dexes": ["quickswap"]  # DEXes known to have bad prices for COMP
    },
    "QUICK": {
        "max_deviation": 100.0,  # Allow 100% deviation for QUICK
        "min_valid_price": 10.0,  # Minimum valid price for QUICK
        "max_valid_price": 100.0,  # Maximum valid price for QUICK
        "known_bad_dexes": []  # No specific bad DEXes for QUICK yet
    },
    "WMATIC": {
        "max_deviation": 50.0,  # Allow 50% deviation for WMATIC
        "min_valid_price": 0.1,  # Minimum valid price for WMATIC
        "max_valid_price": 10.0,  # Maximum valid price for WMATIC
        "known_bad_dexes": []  # No specific bad DEXes for WMATIC yet
    }
}

# Default validation settings
DEFAULT_VALIDATION = {
    "max_deviation": 20.0,  # 20% deviation by default
    "min_valid_price": 0.001,  # Minimum valid price
    "max_valid_price": 1000000.0,  # Maximum valid price
    "known_bad_dexes": []  # No known bad DEXes by default
}

def get_validation_settings(token_symbol: str) -> Dict[str, Any]:
    """
    Get validation settings for a specific token.
    
    Args:
        token_symbol: Token symbol
        
    Returns:
        Dict[str, Any]: Validation settings
    """
    # Normalize token symbol
    token_symbol = token_symbol.upper()
    
    # Return token-specific settings if available, otherwise default
    return PROBLEMATIC_TOKENS.get(token_symbol, DEFAULT_VALIDATION)

def validate_price(
    token_symbol: str,
    dex_name: str,
    price: float,
    all_prices: Dict[str, float],
    max_deviation: Optional[float] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate a token price against prices from other DEXes.
    
    Args:
        token_symbol: Token symbol
        dex_name: DEX name
        price: Price to validate
        all_prices: All prices from different DEXes
        max_deviation: Maximum allowed deviation percentage
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, reason)
    """
    # Get validation settings for this token
    settings = get_validation_settings(token_symbol)
    
    # Use provided max_deviation if specified, otherwise use from settings
    if max_deviation is None:
        max_deviation = settings["max_deviation"]
    
    # Check if price is within valid range
    if price < settings["min_valid_price"]:
        return False, f"Price (${price}) is below minimum valid price (${settings['min_valid_price']})"
    
    if price > settings["max_valid_price"]:
        return False, f"Price (${price}) is above maximum valid price (${settings['max_valid_price']})"
    
    # Check if this DEX is known to have bad prices for this token
    if dex_name.lower() in [d.lower() for d in settings["known_bad_dexes"]]:
        logger.warning(f"{dex_name} is known to have unreliable prices for {token_symbol}")
        # We don't immediately invalidate, but we'll be more strict in validation
        max_deviation = max_deviation * 0.5  # Cut the allowed deviation in half
    
    # If we only have one price (this one), it's valid as long as it's in range
    if len(all_prices) <= 1:
        return True, None
    
    # Get prices from other DEXes
    other_prices = [p for d, p in all_prices.items() if d.lower() != dex_name.lower()]
    
    if not other_prices:
        return True, None
    
    # Calculate median price (more robust than mean)
    median_price = statistics.median(other_prices)
    
    # Calculate deviation
    if median_price == 0:
        return False, "Median price is zero"
    
    deviation_pct = abs(price - median_price) / median_price * 100
    
    # Check if deviation is within allowed range
    if deviation_pct > max_deviation:
        return False, f"Price deviates {deviation_pct:.2f}% from median (${median_price:.6f}), max allowed: {max_deviation:.2f}%"
    
    return True, None

def validate_token_prices(
    token_symbol: str,
    all_prices: Dict[str, float],
    max_deviation: Optional[float] = None
) -> Dict[str, Tuple[bool, Optional[str]]]:
    """
    Validate all prices for a token across different DEXes.
    
    Args:
        token_symbol: Token symbol
        all_prices: All prices from different DEXes
        max_deviation: Maximum allowed deviation percentage
        
    Returns:
        Dict[str, Tuple[bool, Optional[str]]]: Validation results for each DEX
    """
    # Get validation settings for this token
    settings = get_validation_settings(token_symbol)
    
    # Use provided max_deviation if specified, otherwise use from settings
    if max_deviation is None:
        max_deviation = settings["max_deviation"]
    
    # Initialize results
    results = {}
    
    # If we have fewer than 2 prices, we can't validate against other prices
    if len(all_prices) < 2:
        for dex, price in all_prices.items():
            # Just check if price is within valid range
            if price < settings["min_valid_price"]:
                results[dex] = (False, f"Price (${price}) is below minimum valid price (${settings['min_valid_price']})")
            elif price > settings["max_valid_price"]:
                results[dex] = (False, f"Price (${price}) is above maximum valid price (${settings['max_valid_price']})")
            else:
                results[dex] = (True, None)
        return results
    
    # Calculate median price (more robust than mean)
    all_prices_values = list(all_prices.values())
    median_price = statistics.median(all_prices_values)
    
    # Validate each price
    for dex, price in all_prices.items():
        # Check if price is within valid range
        if price < settings["min_valid_price"]:
            results[dex] = (False, f"Price (${price}) is below minimum valid price (${settings['min_valid_price']})")
            continue
        
        if price > settings["max_valid_price"]:
            results[dex] = (False, f"Price (${price}) is above maximum valid price (${settings['max_valid_price']})")
            continue
        
        # Check if this DEX is known to have bad prices for this token
        dex_max_deviation = max_deviation
        if dex.lower() in [d.lower() for d in settings["known_bad_dexes"]]:
            logger.warning(f"{dex} is known to have unreliable prices for {token_symbol}")
            dex_max_deviation = max_deviation * 0.5  # Cut the allowed deviation in half
        
        # Calculate deviation
        if median_price == 0:
            results[dex] = (False, "Median price is zero")
            continue
        
        deviation_pct = abs(price - median_price) / median_price * 100
        
        # Check if deviation is within allowed range
        if deviation_pct > dex_max_deviation:
            results[dex] = (False, f"Price deviates {deviation_pct:.2f}% from median (${median_price:.6f}), max allowed: {dex_max_deviation:.2f}%")
        else:
            results[dex] = (True, None)
    
    return results

def filter_valid_prices(token_symbol: str, all_prices: Dict[str, float]) -> Dict[str, float]:
    """
    Filter out invalid prices for a token.
    
    Args:
        token_symbol: Token symbol
        all_prices: All prices from different DEXes
        
    Returns:
        Dict[str, float]: Filtered prices
    """
    # Validate all prices
    validation_results = validate_token_prices(token_symbol, all_prices)
    
    # Filter out invalid prices
    filtered_prices = {}
    for dex, price in all_prices.items():
        is_valid, _ = validation_results.get(dex, (False, None))
        if is_valid:
            filtered_prices[dex] = price
    
    return filtered_prices
