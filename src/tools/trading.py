"""
Trading models for flash loan arbitrage system
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from decimal import Decimal

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage trading opportunity"""
    path: List[str]  # List of DEXs in trading path
    tokens: List[str]  # List of tokens in trading path
    expected_profit: Decimal
    gas_estimate: int
    timestamp: float

@dataclass
class TradeResult:
    """Represents the result of an executed trade"""
    success: bool
    profit: Decimal  
    gas_cost: Decimal
    path: List[str]
    tokens: List[str]
    timestamp: float
    tx_hash: str