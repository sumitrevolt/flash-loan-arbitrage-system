# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from decimal import Decimal
from typing import List

from dataclasses import dataclass
"""
Trading models for flash loan arbitrage system
"""


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