#!/usr/bin/env python3
"""
Flash Loan Agents Starter
This script starts all the agents needed for the flash loan system.
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Import the auto_executor singleton instance and message bus
from src.flash_loan.core.auto_executor import auto_executor
from src.flash_loan.core.message_bus import message_bus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/agents.log')
    ]
)
logger = logging.getLogger('FlashLoanAgents')

async def main(args):
    """Main function to start all agents"""
    logger.info("Starting Flash Loan Agents")

    # Convert string arguments to appropriate types
    real_execution = args.real_execution.lower() == 'true'
    auto_execute = args.auto_execute.lower() == 'true'
    use_real_prices = args.use_real_prices.lower() == 'true'
    force_real_data = args.force_real_data.lower() == 'true'
    track_profits = args.track_profits.lower() == 'true'

    # Convert numeric arguments
    profit_threshold = float(args.profit_threshold)
    trade_size = float(args.trade_size)
    increase_percentage = float(args.increase_percentage)
    max_trade_size = float(args.max_trade_size)

    # Initialize the auto executor
    await auto_executor.initialize(
        real_execution=real_execution,
        auto_execute=auto_execute,
        use_real_prices=use_real_prices,
        force_real_data=force_real_data,
        track_profits=track_profits,
        min_profit_threshold=profit_threshold,
        trade_size=trade_size,
        increase_percentage=increase_percentage,
        max_trade_size=max_trade_size,
        contract_address=args.contract_address
    )

    logger.info("Auto executor initialized with the following parameters:")
    logger.info(f"  Real Execution: {real_execution}")
    logger.info(f"  Auto Execute: {auto_execute}")
    logger.info(f"  Use Real Prices: {use_real_prices}")
    logger.info(f"  Force Real Data: {force_real_data}")
    logger.info(f"  Track Profits: {track_profits}")
    logger.info(f"  Profit Threshold: ${profit_threshold}")
    logger.info(f"  Trade Size: ${trade_size}")
    logger.info(f"  Increase Percentage: {increase_percentage}%")
    logger.info(f"  Max Trade Size: ${max_trade_size}")
    logger.info(f"  Contract Address: {args.contract_address}")

    # Note: The core auto_executor doesn't have a start() method
    # Instead, it's designed to respond to events via the message bus

    # Subscribe to arbitrage opportunity events
    def handle_opportunity(opportunity):
        logger.info(f"Received arbitrage opportunity: {opportunity.get('token')} from {opportunity.get('buy_dex')} to {opportunity.get('sell_dex')}")
        if auto_execute:
            # The auto_executor will handle opportunities directly through its own subscription
            # We just log it here for visibility
            logger.info(f"Auto executor will process opportunity with profit: ${opportunity.get('profit_usd', 0):.2f}")

    # Register the handler with the message bus (not async)
    message_bus.subscribe("arbitrage_opportunities", handle_opportunity)

    logger.info("Auto executor initialized in real revenue mode with real data. Press Ctrl+C to stop.")
    logger.info("Subscribed to arbitrage opportunity events via message bus")

    # Keep the script running
    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        logger.info("Stopping agents...")
    except Exception as e:
        logger.error(f"Error in agent loop: {e}")
    finally:
        logger.info("Agents stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Flash Loan Agents")
    parser.add_argument("--real-execution", default="true", help="Execute real trades")
    parser.add_argument("--auto-execute", default="true", help="Automatically execute trades")
    parser.add_argument("--use-real-prices", default="true", help="Use real prices from blockchain")
    parser.add_argument("--force-real-data", default="true", help="Force using real data")
    parser.add_argument("--track-profits", default="true", help="Track profits")
    parser.add_argument("--profit-threshold", default="5.0", help="Minimum profit threshold in USD")
    parser.add_argument("--trade-size", type=float, default=1000.0, help="Initial trade size in USD")
    parser.add_argument("--increase-percentage", default="1.0", help="Percentage to increase trade size after successful trade")
    parser.add_argument("--max-trade-size", default="5000.0", help="Maximum trade size in USD")
    parser.add_argument("--contract-address", default="0xd84a56D6aAA9ff46D1a29590a499DAf45F432215", help="Flash loan contract address")

    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        logger.info("Agents stopped by user")
    except Exception as e:
        logger.error(f"Error starting agents: {e}")
        sys.exit(1)
