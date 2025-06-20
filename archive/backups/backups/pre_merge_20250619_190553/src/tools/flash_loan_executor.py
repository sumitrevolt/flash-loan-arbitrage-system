"""
Flash Loan Executor for the Flash Loan Arbitrage System.
This module handles the execution of flash loan arbitrage trades.
"""

import logging
import os
from typing import Optional, Dict, Any

# Use core TransactionExecutor directly
from src.flash_loan.core.transaction_executor import transaction_executor as flash_loan_executor