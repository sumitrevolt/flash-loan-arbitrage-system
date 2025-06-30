"""
Arbitrage Executor Service
Executes flash loan arbitrage opportunities identified by the blockchain monitor
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
from eth_account import Account
import numpy as np

# Configure logging
logger.add("logs/arbitrage_executor.log", rotation="1 day", retention="7 days")

class ArbitrageExecutor:
    def __init__(self):
        self.web3_rpc_url = os.getenv("WEB3_RPC_URL", "http://web3-node:8545")
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://langchain-orchestrator:8000")
        self.private_key = os.getenv("PRIVATE_KEY")
        self.contract_address = os.getenv("CONTRACT_ADDRESS")
        self.max_slippage = float(os.getenv("MAX_SLIPPAGE", "0.005"))
        self.execute_trades = os.getenv("EXECUTE_TRADES", "false").lower() == "true"
        
        # Initialize connections
        self.web3 = Web3(Web3.HTTPProvider(self.web3_rpc_url))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.redis_client = redis.from_url(self.redis_url)
        
        # Initialize account if private key is provided
        self.account = None
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            logger.info(f"Initialized account: {self.account.address}")
        else:
            logger.warning("No private key provided - running in simulation mode")
        
        # Flash loan contract ABI (simplified)
        self.flash_loan_abi = [
            {
                "inputs": [
                    {"name": "asset", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "params", "type": "bytes"}
                ],
                "name": "flashLoan",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        # Initialize contract if address is provided
        self.flash_loan_contract = None
        if self.contract_address:
            self.flash_loan_contract = self.web3.eth.contract(
                address=self.contract_address,
                abi=self.flash_loan_abi
            )
        
        self.app = FastAPI(title="Arbitrage Executor", version="1.0.0")
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
                    "account": self.account.address if self.account else "simulation",
                    "execute_trades": self.execute_trades,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")
        
        @self.app.get("/stats")
        async def get_stats():
            try:
                stats = {
                    "trades_executed": int(self.redis_client.get("trades_executed") or 0),
                    "successful_trades": int(self.redis_client.get("successful_trades") or 0),
                    "total_profit": float(self.redis_client.get("total_profit") or 0.0),
                    "gas_used": int(self.redis_client.get("gas_used") or 0),
                    "execution_mode": "live" if self.execute_trades else "simulation"
                }
                if stats["trades_executed"] > 0:
                    stats["success_rate"] = stats["successful_trades"] / stats["trades_executed"]
                    stats["average_profit"] = stats["total_profit"] / stats["trades_executed"]
                return stats
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/execute")
        async def execute_arbitrage(opportunity: Dict[str, Any]):
            """Execute an arbitrage opportunity"""
            try:
                result = await self.execute_arbitrage_opportunity(opportunity)
                return result
            except Exception as e:
                logger.error(f"Failed to execute arbitrage: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_listening(self):
        """Start listening for arbitrage opportunities"""
        try:
            logger.info("Starting to listen for arbitrage opportunities...")
            
            # Subscribe to Redis channel for opportunities
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe("arbitrage_opportunities")
            
            while True:
                try:
                    message = pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'message':
                        opportunity = json.loads(message['data'].decode('utf-8'))
                        await self.process_opportunity(opportunity)
                    
                    await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                    
                except Exception as e:
                    logger.error(f"Error processing opportunity: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Fatal error in opportunity listener: {e}")
    
    async def process_opportunity(self, opportunity: Dict[str, Any]):
        """Process an arbitrage opportunity"""
        try:
            logger.info(f"Processing arbitrage opportunity: {opportunity.get('type', 'unknown')}")
            
            # Validate opportunity
            if not self.validate_opportunity(opportunity):
                logger.warning("Opportunity validation failed")
                return
            
            # Check if we should execute this opportunity
            if not await self.should_execute(opportunity):
                logger.info("Opportunity execution criteria not met")
                return
            
            # Execute the arbitrage
            result = await self.execute_arbitrage_opportunity(opportunity)
            
            # Update statistics
            await self.update_execution_stats(result)
            
            # Notify orchestrator of execution result
            await self.notify_execution_result(opportunity, result)
            
        except Exception as e:
            logger.error(f"Error processing opportunity: {e}")
    
    def validate_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Validate an arbitrage opportunity"""
        try:
            required_fields = ["type", "estimated_profit", "confidence"]
            for field in required_fields:
                if field not in opportunity:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Check minimum profit threshold
            if opportunity["estimated_profit"] < 0.001:  # 0.1% minimum
                logger.info(f"Profit too low: {opportunity['estimated_profit']}")
                return False
            
            # Check confidence threshold
            if opportunity["confidence"] < 0.7:  # 70% minimum confidence
                logger.info(f"Confidence too low: {opportunity['confidence']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating opportunity: {e}")
            return False
    
    async def should_execute(self, opportunity: Dict[str, Any]) -> bool:
        """Determine if we should execute this opportunity"""
        try:
            # Check gas price
            current_gas_price = self.web3.eth.gas_price
            max_gas_price = self.web3.to_wei(200, 'gwei')  # 200 gwei max
            
            if current_gas_price > max_gas_price:
                logger.info(f"Gas price too high: {current_gas_price} > {max_gas_price}")
                return False
            
            # Check account balance if in live mode
            if self.execute_trades and self.account:
                balance = self.web3.eth.get_balance(self.account.address)
                min_balance = self.web3.to_wei(0.1, 'ether')  # 0.1 ETH minimum
                
                if balance < min_balance:
                    logger.warning(f"Insufficient balance: {balance} < {min_balance}")
                    return False
            
            # Risk management checks
            estimated_gas = 300000  # Estimated gas for flash loan
            gas_cost = current_gas_price * estimated_gas
            gas_cost_eth = self.web3.from_wei(gas_cost, 'ether')
            
            # Ensure profit exceeds gas cost by at least 50%
            if opportunity["estimated_profit"] < gas_cost_eth * 1.5:
                logger.info(f"Profit doesn't justify gas cost: {opportunity['estimated_profit']} < {gas_cost_eth * 1.5}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking execution criteria: {e}")
            return False
    
    async def execute_arbitrage_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an arbitrage opportunity"""
        execution_start = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Executing arbitrage opportunity: {opportunity}")
            
            if not self.execute_trades:
                # Simulation mode
                result = await self.simulate_execution(opportunity)
            else:
                # Live execution
                result = await self.execute_live_trade(opportunity)
            
            execution_time = (datetime.now(timezone.utc) - execution_start).total_seconds()
            result["execution_time"] = execution_time
            
            logger.info(f"Arbitrage execution completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing arbitrage opportunity: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now(timezone.utc) - execution_start).total_seconds()
            }
    
    async def simulate_execution(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate execution of an arbitrage opportunity"""
        try:
            # Simulate execution delay
            await asyncio.sleep(0.1)
            
            # Calculate simulated results
            estimated_profit = opportunity["estimated_profit"]
            estimated_gas = 300000
            gas_price = self.web3.eth.gas_price
            gas_cost = self.web3.from_wei(gas_price * estimated_gas, 'ether')
            net_profit = estimated_profit - gas_cost
            
            # Add some randomness to simulate real-world conditions
            success_probability = opportunity["confidence"]
            success = np.random.random() < success_probability
            
            if success:
                # Simulate some slippage
                actual_profit = net_profit * (1 - np.random.random() * self.max_slippage)
            else:
                actual_profit = -gas_cost  # Only lose gas cost
            
            return {
                "success": success,
                "simulated": True,
                "estimated_profit": estimated_profit,
                "actual_profit": actual_profit,
                "gas_cost": gas_cost,
                "gas_used": estimated_gas,
                "transaction_hash": f"0x{''.join([f'{np.random.randint(0, 16):x}' for _ in range(64)])}"  # Mock hash
            }
            
        except Exception as e:
            logger.error(f"Error in simulation: {e}")
            raise
    
    async def execute_live_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a live arbitrage trade"""
        try:
            if not self.account or not self.flash_loan_contract:
                raise ValueError("Account or contract not configured for live trading")
            
            # Prepare transaction parameters
            asset_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # WETH
            amount = self.web3.to_wei(1, 'ether')  # 1 ETH flash loan
            params = b''  # Encoded parameters for the arbitrage strategy
            
            # Build transaction
            transaction = self.flash_loan_contract.functions.flashLoan(
                asset_address,
                amount,
                params
            ).build_transaction({
                'from': self.account.address,
                'gas': 500000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.account.address)
            })
            
            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            # Calculate actual results
            gas_used = receipt.gasUsed
            gas_cost = self.web3.from_wei(receipt.gasUsed * receipt.effectiveGasPrice, 'ether')
            
            # For this example, we'll simulate the profit calculation
            # In production, you'd parse the logs to get actual token amounts
            success = receipt.status == 1
            if success:
                actual_profit = opportunity["estimated_profit"] - gas_cost
            else:
                actual_profit = -gas_cost
            
            return {
                "success": success,
                "simulated": False,
                "transaction_hash": tx_hash.hex(),
                "gas_used": gas_used,
                "gas_cost": gas_cost,
                "actual_profit": actual_profit,
                "block_number": receipt.blockNumber
            }
            
        except Exception as e:
            logger.error(f"Error executing live trade: {e}")
            raise
    
    async def update_execution_stats(self, result: Dict[str, Any]):
        """Update execution statistics"""
        try:
            self.redis_client.incr("trades_executed")
            
            if result["success"]:
                self.redis_client.incr("successful_trades")
            
            if "actual_profit" in result:
                current_profit = float(self.redis_client.get("total_profit") or 0)
                new_profit = current_profit + result["actual_profit"]
                self.redis_client.set("total_profit", new_profit)
            
            if "gas_used" in result:
                current_gas = int(self.redis_client.get("gas_used") or 0)
                new_gas = current_gas + result["gas_used"]
                self.redis_client.set("gas_used", new_gas)
                
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
    
    async def notify_execution_result(self, opportunity: Dict[str, Any], result: Dict[str, Any]):
        """Notify the orchestrator of execution result"""
        try:
            notification = {
                "opportunity": opportunity,
                "execution_result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Store in Redis
            redis_key = f"execution_result:{result.get('transaction_hash', 'simulation')}"
            self.redis_client.setex(redis_key, 3600, json.dumps(notification))  # 1-hour TTL
            
            # Notify orchestrator
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.orchestrator_url}/arbitrage/execution_result",
                        json=notification,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            logger.info("Successfully notified orchestrator of execution result")
                        else:
                            logger.warning(f"Failed to notify orchestrator: {response.status}")
                except Exception as e:
                    logger.error(f"Error notifying orchestrator: {e}")
                    
        except Exception as e:
            logger.error(f"Error notifying execution result: {e}")

# Global executor instance
executor = ArbitrageExecutor()

async def startup_event():
    """Start listening when the service starts"""
    asyncio.create_task(executor.start_listening())

executor.app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    logger.info("Starting Arbitrage Executor Service...")
    uvicorn.run(
        executor.app,
        host="0.0.0.0",
        port=8071,
        log_level="info"
    ) 