#!/usr/bin/env python3
"""
Check the status of the Flash Loan Arbitrage System
"""
# Import requires_web3 decorator from central provider
from src.utils.web3_provider import requires_web3


import os
import sys
import time
import asyncio
import logging
from pathlib import Path
# Import from central web3_provider
from src.utils.web3_provider import Web3, WEB3_IMPORTED
from web3.types import TxParams, Wei, ChecksumAddress
# Import exceptions from central provider
from src.utils.web3_provider import Web3Exception, ContractLogicError, TransactionNotFound
# Import middleware from centralized modules
from src.utils.middleware_compat import apply_poa_middleware

import logging
logger = logging.getLogger(__name__)
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("system_status")

# Ensure we're in the project root directory
project_root = Path(__file__).resolve().parent
os.chdir(project_root)

# Add the project root to the Python path
sys.path.append(str(project_root))

async def check_status():
    """Check the status of the Flash Loan Arbitrage System"""
    try:
        # Import system components
        from core.dex_integration import dex_integration
        from core.transaction_executor import transaction_executor
        from core.database import db
        
        # Check DEX integration status
        logger.info("Checking DEX integration status...")
        if not dex_integration.initialized:
            logger.warning("DEX integration is not initialized")
        else:
            logger.info("DEX integration is initialized")
            
            # Check Web3 connection
            if dex_integration.w3 and dex_integration.w3.is_connected():
                chain_id = await dex_integration.make_request(lambda: dex_integration.w3.eth.chain_id)
                block_number = await dex_integration.make_request(lambda: dex_integration.w3.eth.block_number)
                logger.info(f"Connected to blockchain. Chain ID: {chain_id}, Block: {block_number}")
            else:
                logger.warning("Not connected to blockchain")
        
        # Check transaction executor status
        logger.info("Checking transaction executor status...")
        stats = transaction_executor.get_stats()
        logger.info(f"Transaction stats: {stats}")
        
        # Check database status
        logger.info("Checking database status...")
        recent_opportunities = await db.get_recent_opportunities(5)
        logger.info(f"Recent opportunities: {len(recent_opportunities)}")
        
        recent_executions = await db.get_recent_executions(5)
        logger.info(f"Recent executions: {len(recent_executions)}")
        
        logger.info("System status check complete")
        
    except Exception as e:
        logger.error(f"Error checking system status: {e}")

def main():
    """Main entry point"""
    logger.info("Checking Flash Loan Arbitrage System status...")
    asyncio.run(check_status())

if __name__ == "__main__":
    main()
