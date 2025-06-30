"""
Blockchain Monitor Service
Monitors blockchain transactions and identifies flash loan arbitrage opportunities
"""
import asyncio
import json
import os
from typing import Dict, List, Optional, Any
import aiohttp
import redis
from web3 import Web3
from web3.middleware.geth_poa import geth_poa_middleware
from fastapi import FastAPI, HTTPException
import uvicorn
from loguru import logger
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# Configure logging
logger.add("logs/blockchain_monitor.log", rotation="1 day", retention="7 days")

class BlockchainMonitor:
    def __init__(self):
        self.web3_rpc_url = os.getenv("WEB3_RPC_URL", "http://web3-node:8545")
        self.web3_ws_url = os.getenv("WEB3_WS_URL", "ws://web3-node:8546")
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://langchain-orchestrator:8000")
        self.min_profit_threshold = float(os.getenv("MIN_PROFIT_THRESHOLD", "0.001"))
        self.max_gas_price = int(os.getenv("MAX_GAS_PRICE", "200"))
        
        # Initialize connections
        self.web3 = Web3(Web3.HTTPProvider(self.web3_rpc_url))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.redis_client = redis.from_url(self.redis_url)
        
        # DEX addresses (placeholder - update with real addresses)
        self.dex_addresses = {
            "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
            "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
            "balancer": "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
        }
        
        # Token addresses
        self.token_addresses = {
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "USDC": "0xA0b86a33E6411b547a1D71bbA13D9b60BB30a8D9",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7"
        }
        
        self.app = FastAPI(title="Blockchain Monitor", version="1.0.0")
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.get("/health")
        async def health():
            try:
                # Check Web3 connection
                latest_block = self.web3.eth.block_number
                # Check Redis connection
                self.redis_client.ping()
                return {
                    "status": "healthy",
                    "latest_block": latest_block,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")
        
        @self.app.get("/stats")
        async def get_stats():
            try:
                stats = {
                    "opportunities_found": self.redis_client.get("opportunities_found") or 0,
                    "transactions_monitored": self.redis_client.get("transactions_monitored") or 0,
                    "average_profit": self.redis_client.get("average_profit") or 0.0,
                    "gas_price": self.web3.eth.gas_price
                }
                return stats
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def monitor_mempool(self):
        """Monitor mempool for pending transactions"""
        try:
            logger.info("Starting mempool monitoring...")
            
            while True:
                try:
                    # Get pending transactions
                    pending_txs = self.web3.eth.get_block('pending', full_transactions=True)
                    
                    if pending_txs and pending_txs.transactions:
                        logger.info(f"Found {len(pending_txs.transactions)} pending transactions")
                        
                        for tx in pending_txs.transactions:
                            await self.analyze_transaction(tx)
                            
                        # Update monitoring stats
                        self.redis_client.incr("transactions_monitored", len(pending_txs.transactions))
                    
                    await asyncio.sleep(1)  # Check every second
                    
                except Exception as e:
                    logger.error(f"Error monitoring mempool: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Fatal error in mempool monitoring: {e}")
            
    async def monitor_new_blocks(self):
        """Monitor new blocks for arbitrage opportunities"""
        try:
            logger.info("Starting block monitoring...")
            last_block = self.web3.eth.block_number
            
            while True:
                try:
                    current_block = self.web3.eth.block_number
                    
                    if current_block > last_block:
                        logger.info(f"New block: {current_block}")
                        
                        # Analyze the new block
                        block = self.web3.eth.get_block(current_block, full_transactions=True)
                        await self.analyze_block(block)
                        
                        last_block = current_block
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error monitoring blocks: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Fatal error in block monitoring: {e}")
    
    async def analyze_transaction(self, tx):
        """Analyze a transaction for arbitrage opportunities"""
        try:
            # Check if transaction involves DEX interactions
            if tx.to and tx.to.lower() in [addr.lower() for addr in self.dex_addresses.values()]:
                logger.info(f"DEX transaction detected: {tx.hash.hex()}")
                
                # Decode transaction data (simplified)
                opportunity = await self.identify_arbitrage_opportunity(tx)
                
                if opportunity:
                    await self.notify_arbitrage_opportunity(opportunity)
                    
        except Exception as e:
            logger.error(f"Error analyzing transaction {tx.hash.hex()}: {e}")
    
    async def analyze_block(self, block):
        """Analyze a block for arbitrage opportunities"""
        try:
            if not block.transactions:
                return
                
            logger.info(f"Analyzing block {block.number} with {len(block.transactions)} transactions")
            
            dex_transactions = []
            for tx in block.transactions:
                if tx.to and tx.to.lower() in [addr.lower() for addr in self.dex_addresses.values()]:
                    dex_transactions.append(tx)
            
            if dex_transactions:
                logger.info(f"Found {len(dex_transactions)} DEX transactions in block {block.number}")
                
                # Analyze for cross-DEX arbitrage opportunities
                opportunities = await self.find_cross_dex_opportunities(dex_transactions)
                
                for opportunity in opportunities:
                    await self.notify_arbitrage_opportunity(opportunity)
                    
        except Exception as e:
            logger.error(f"Error analyzing block {block.number}: {e}")
    
    async def identify_arbitrage_opportunity(self, tx) -> Optional[Dict]:
        """Identify potential arbitrage opportunity from a transaction"""
        try:
            # Simplified arbitrage detection logic
            # In production, this would involve detailed price analysis
            
            if tx.value > 0:  # Only analyze transactions with value
                # Mock arbitrage opportunity for demonstration
                opportunity = {
                    "transaction_hash": tx.hash.hex(),
                    "type": "simple_arbitrage",
                    "dex_from": "uniswap_v2",
                    "dex_to": "sushiswap",
                    "token_pair": "WETH/USDC",
                    "estimated_profit": self.min_profit_threshold * 2,  # Mock calculation
                    "gas_price": tx.gasPrice,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "block_number": None,
                    "confidence": 0.85
                }
                
                if opportunity["estimated_profit"] > self.min_profit_threshold:
                    return opportunity
                    
        except Exception as e:
            logger.error(f"Error identifying arbitrage opportunity: {e}")
            
        return None
    
    async def find_cross_dex_opportunities(self, transactions: List) -> List[Dict]:
        """Find cross-DEX arbitrage opportunities"""
        opportunities = []
        
        try:
            # Group transactions by token pairs
            token_movements = {}
            
            for tx in transactions:
                # Simplified token movement detection
                # In production, decode transaction logs for actual transfers
                if tx.value > 0:
                    key = f"WETH_trade_{tx.to}"
                    if key not in token_movements:
                        token_movements[key] = []
                    token_movements[key].append(tx)
            
            # Look for price discrepancies
            for token_pair, txs in token_movements.items():
                if len(txs) >= 2:  # Need at least 2 transactions for comparison
                    opportunity = {
                        "type": "cross_dex_arbitrage",
                        "token_pair": token_pair,
                        "transactions": [tx.hash.hex() for tx in txs[:2]],
                        "estimated_profit": self.min_profit_threshold * 1.5,
                        "timestamp": datetime.utcnow().isoformat(),
                        "confidence": 0.75
                    }
                    opportunities.append(opportunity)
                    
        except Exception as e:
            logger.error(f"Error finding cross-DEX opportunities: {e}")
            
        return opportunities
    
    async def notify_arbitrage_opportunity(self, opportunity: Dict):
        """Notify the LangChain orchestrator of an arbitrage opportunity"""
        try:
            # Store in Redis for immediate access
            redis_key = f"arbitrage_opportunity:{opportunity['transaction_hash'] if 'transaction_hash' in opportunity else opportunity['timestamp']}"
            self.redis_client.setex(redis_key, 300, json.dumps(opportunity))  # 5-minute TTL
            
            # Publish to Redis channel for real-time processing
            self.redis_client.publish("arbitrage_opportunities", json.dumps(opportunity))
            
            # Notify LangChain orchestrator
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.orchestrator_url}/arbitrage/opportunity",
                        json=opportunity,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"Successfully notified orchestrator of opportunity: {opportunity.get('type', 'unknown')}")
                        else:
                            logger.warning(f"Failed to notify orchestrator: {response.status}")
                except asyncio.TimeoutError:
                    logger.warning("Timeout notifying orchestrator")
                except Exception as e:
                    logger.error(f"Error notifying orchestrator: {e}")
            
            # Update statistics
            self.redis_client.incr("opportunities_found")
            
            # Calculate running average profit
            current_avg = float(self.redis_client.get("average_profit") or 0)
            current_count = int(self.redis_client.get("opportunities_found") or 1)
            new_avg = ((current_avg * (current_count - 1)) + opportunity.get("estimated_profit", 0)) / current_count
            self.redis_client.set("average_profit", new_avg)
            
            logger.info(f"Arbitrage opportunity detected: {opportunity}")
            
        except Exception as e:
            logger.error(f"Error notifying arbitrage opportunity: {e}")
    
    async def start_monitoring(self):
        """Start all monitoring tasks"""
        tasks = [
            asyncio.create_task(self.monitor_mempool()),
            asyncio.create_task(self.monitor_new_blocks())
        ]
        
        logger.info("Starting blockchain monitoring tasks...")
        await asyncio.gather(*tasks)

# Global monitor instance
monitor = BlockchainMonitor()

async def startup_event():
    """Start monitoring when the service starts"""
    asyncio.create_task(monitor.start_monitoring())

monitor.app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    logger.info("Starting Blockchain Monitor Service...")
    uvicorn.run(
        monitor.app,
        host="0.0.0.0",
        port=8070,
        log_level="info"
    ) 