#!/usr/bin/env python3
"""
Consolidated Trading MCP Server
==============================
Unified trading execution server combining flash loan and arbitrage functionality
Executes trades, manages risk, and coordinates with pricing servers
"""

import asyncio
import json
import logging
import time
from decimal import Decimal, getcontext
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from flask import Flask, jsonify, request
from web3 import Web3
import requests

# Set precision for financial calculations
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradeStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TradeOrder:
    """Trade order structure"""
    id: str
    token_pair: str
    amount: Decimal
    buy_dex: str
    sell_dex: str
    buy_price: Decimal
    sell_price: Decimal
    expected_profit: Decimal
    status: TradeStatus
    created_at: datetime
    executed_at: Optional[datetime] = None
    tx_hash: Optional[str] = None
    actual_profit: Optional[Decimal] = None
    gas_used: Optional[int] = None
    gas_price: Optional[Decimal] = None

@dataclass
class RiskLimits:
    """Risk management limits"""
    max_trade_amount: Decimal
    max_daily_trades: int
    max_daily_loss: Decimal
    min_profit_threshold: Decimal
    max_slippage: Decimal

class ConsolidatedTradingServer:
    """
    Consolidated trading server for flash loan arbitrage
    Replaces multiple duplicate trading servers
    """
    
    def __init__(self):
        self.app = Flask(__name__)
        self.active_trades: Dict[str, TradeOrder] = {}
        self.completed_trades: List[TradeOrder] = []
        self.pricing_server_url = "http://localhost:8001"
        
        # Risk management
        self.risk_limits = RiskLimits(
            max_trade_amount=Decimal("10000"),
            max_daily_trades=100,
            max_daily_loss=Decimal("1000"),
            min_profit_threshold=Decimal("0.1"),  # 0.1%
            max_slippage=Decimal("0.5")  # 0.5%
        )
        
        # Trading statistics
        self.stats = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit": Decimal("0"),
            "total_gas_used": 0,
            "average_profit": Decimal("0"),
            "success_rate": 0.0
        }
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health')
        def health():
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_trades": len(self.active_trades),
                "completed_trades": len(self.completed_trades),
                "total_profit": float(self.stats["total_profit"])
            })
            
        @self.app.route('/execute', methods=['POST'])
        def execute_trade():
            """Execute a flash loan arbitrage trade"""
            try:
                data = request.json
                token_pair = data.get('token_pair')
                amount = Decimal(str(data.get('amount', 0)))
                
                if not token_pair or amount <= 0:
                    return jsonify({"error": "Invalid parameters"}), 400
                
                # Get best arbitrage opportunity
                opportunity = self.get_best_opportunity(token_pair)
                if not opportunity:
                    return jsonify({"error": "No arbitrage opportunity found"}), 404
                
                # Create trade order
                trade_order = self.create_trade_order(opportunity, amount)
                
                # Execute trade asynchronously
                asyncio.create_task(self.execute_trade_async(trade_order))
                
                return jsonify({
                    "trade_id": trade_order.id,
                    "status": trade_order.status.value,
                    "expected_profit": float(trade_order.expected_profit)
                })
                
            except Exception as e:
                logger.error(f"Error executing trade: {e}")
                return jsonify({"error": str(e)}), 500
                
        @self.app.route('/trades')
        def get_trades():
            """Get all trades"""
            all_trades = []
            
            # Active trades
            for trade in self.active_trades.values():
                all_trades.append(self.trade_to_dict(trade))
                
            # Completed trades (last 100)
            for trade in self.completed_trades[-100:]:
                all_trades.append(self.trade_to_dict(trade))
                
            return jsonify(all_trades)
            
        @self.app.route('/trades/<trade_id>')
        def get_trade(trade_id: str):
            """Get specific trade details"""
            # Check active trades
            if trade_id in self.active_trades:
                return jsonify(self.trade_to_dict(self.active_trades[trade_id]))
                
            # Check completed trades
            for trade in self.completed_trades:
                if trade.id == trade_id:
                    return jsonify(self.trade_to_dict(trade))
                    
            return jsonify({"error": "Trade not found"}), 404
            
        @self.app.route('/stats')
        def get_stats():
            """Get trading statistics"""
            return jsonify({
                "total_trades": self.stats["total_trades"],
                "successful_trades": self.stats["successful_trades"],
                "failed_trades": self.stats["failed_trades"],
                "total_profit": float(self.stats["total_profit"]),
                "average_profit": float(self.stats["average_profit"]),
                "success_rate": self.stats["success_rate"],
                "total_gas_used": self.stats["total_gas_used"]
            })
            
        @self.app.route('/cancel/<trade_id>', methods=['POST'])
        def cancel_trade(trade_id: str):
            """Cancel an active trade"""
            if trade_id not in self.active_trades:
                return jsonify({"error": "Trade not found"}), 404
                
            trade = self.active_trades[trade_id]
            if trade.status == TradeStatus.EXECUTING:
                return jsonify({"error": "Cannot cancel executing trade"}), 400
                
            trade.status = TradeStatus.CANCELLED
            self.move_to_completed(trade)
            
            return jsonify({"message": "Trade cancelled"})
            
    def get_best_opportunity(self, token_pair: str) -> Optional[Dict]:
        """Get best arbitrage opportunity from pricing server"""
        try:
            response = requests.get(f"{self.pricing_server_url}/arbitrage", timeout=5)
            if response.status_code == 200:
                opportunities = response.json()
                for opp in opportunities:
                    if opp["token_pair"] == token_pair:
                        return opp
            return None
        except Exception as e:
            logger.error(f"Error getting opportunities: {e}")
            return None
            
    def create_trade_order(self, opportunity: Dict, amount: Decimal) -> TradeOrder:
        """Create a trade order from an arbitrage opportunity"""
        trade_id = f"trade_{int(time.time())}_{len(self.active_trades)}"
        
        expected_profit = Decimal(str(opportunity["estimated_profit"]))
        
        trade_order = TradeOrder(
            id=trade_id,
            token_pair=opportunity["token_pair"],
            amount=amount,
            buy_dex=opportunity["buy_dex"],
            sell_dex=opportunity["sell_dex"],
            buy_price=Decimal(str(opportunity["buy_price"])),
            sell_price=Decimal(str(opportunity["sell_price"])),
            expected_profit=expected_profit,
            status=TradeStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.active_trades[trade_id] = trade_order
        return trade_order
        
    async def execute_trade_async(self, trade_order: TradeOrder):
        """Execute trade asynchronously"""
        try:
            logger.info(f"Executing trade {trade_order.id}")
            
            # Risk checks
            if not self.risk_check(trade_order):
                trade_order.status = TradeStatus.FAILED
                self.move_to_completed(trade_order)
                return
                
            trade_order.status = TradeStatus.EXECUTING
            
            # Simulate trade execution
            await self.simulate_flash_loan_execution(trade_order)
            
            # Update statistics
            self.update_stats(trade_order)
            
        except Exception as e:
            logger.error(f"Error executing trade {trade_order.id}: {e}")
            trade_order.status = TradeStatus.FAILED
            self.move_to_completed(trade_order)
            
    def risk_check(self, trade_order: TradeOrder) -> bool:
        """Perform risk management checks"""
        
        # Check trade amount limit
        if trade_order.amount > self.risk_limits.max_trade_amount:
            logger.warning(f"Trade amount {trade_order.amount} exceeds limit")
            return False
            
        # Check minimum profit threshold
        profit_percentage = (trade_order.expected_profit / trade_order.amount) * 100
        if profit_percentage < self.risk_limits.min_profit_threshold:
            logger.warning(f"Profit {profit_percentage}% below threshold")
            return False
            
        # Check daily trade limit
        today_trades = sum(1 for t in self.completed_trades 
                          if t.created_at.date() == datetime.now().date())
        if today_trades >= self.risk_limits.max_daily_trades:
            logger.warning("Daily trade limit reached")
            return False
            
        return True
        
    async def simulate_flash_loan_execution(self, trade_order: TradeOrder):
        """Simulate flash loan execution (replace with actual Web3 calls in production)"""
        
        # Simulate execution time
        await asyncio.sleep(2)
        
        # Simulate success/failure (90% success rate for demo)
        import random
        success = random.random() < 0.9
        
        if success:
            # Simulate actual execution results
            slippage = Decimal(str(random.uniform(0.0, 0.3)))  # 0-0.3% slippage
            actual_profit = trade_order.expected_profit * (1 - slippage / 100)
            gas_used = random.randint(150000, 300000)
            gas_price = Decimal(str(random.uniform(20, 50)))  # Gwei
            
            trade_order.status = TradeStatus.COMPLETED
            trade_order.executed_at = datetime.now()
            trade_order.actual_profit = actual_profit
            trade_order.gas_used = gas_used
            trade_order.gas_price = gas_price
            trade_order.tx_hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
            
            logger.info(f"Trade {trade_order.id} completed successfully. "
                       f"Profit: ${float(actual_profit):.2f}")
                       
        else:
            trade_order.status = TradeStatus.FAILED
            trade_order.executed_at = datetime.now()
            logger.warning(f"Trade {trade_order.id} failed")
            
        self.move_to_completed(trade_order)
        
    def move_to_completed(self, trade_order: TradeOrder):
        """Move trade from active to completed"""
        if trade_order.id in self.active_trades:
            del self.active_trades[trade_order.id]
        self.completed_trades.append(trade_order)
        
        # Keep only last 1000 completed trades
        if len(self.completed_trades) > 1000:
            self.completed_trades = self.completed_trades[-1000:]
            
    def update_stats(self, trade_order: TradeOrder):
        """Update trading statistics"""
        self.stats["total_trades"] += 1
        
        if trade_order.status == TradeStatus.COMPLETED:
            self.stats["successful_trades"] += 1
            if trade_order.actual_profit:
                self.stats["total_profit"] += trade_order.actual_profit
        else:
            self.stats["failed_trades"] += 1
            
        # Update success rate
        self.stats["success_rate"] = (
            self.stats["successful_trades"] / self.stats["total_trades"] * 100
            if self.stats["total_trades"] > 0 else 0
        )
        
        # Update average profit
        self.stats["average_profit"] = (
            self.stats["total_profit"] / self.stats["successful_trades"]
            if self.stats["successful_trades"] > 0 else Decimal("0")
        )
        
        if trade_order.gas_used:
            self.stats["total_gas_used"] += trade_order.gas_used
            
    def trade_to_dict(self, trade: TradeOrder) -> Dict:
        """Convert trade order to dictionary"""
        return {
            "id": trade.id,
            "token_pair": trade.token_pair,
            "amount": float(trade.amount),
            "buy_dex": trade.buy_dex,
            "sell_dex": trade.sell_dex,
            "buy_price": float(trade.buy_price),
            "sell_price": float(trade.sell_price),
            "expected_profit": float(trade.expected_profit),
            "actual_profit": float(trade.actual_profit) if trade.actual_profit else None,
            "status": trade.status.value,
            "created_at": trade.created_at.isoformat(),
            "executed_at": trade.executed_at.isoformat() if trade.executed_at else None,
            "tx_hash": trade.tx_hash,
            "gas_used": trade.gas_used,
            "gas_price": float(trade.gas_price) if trade.gas_price else None
        }
        
    def run(self, host='0.0.0.0', port=8002):
        """Run the trading server"""
        logger.info(f"🚀 Starting Consolidated Trading MCP Server on {host}:{port}")
        logger.info(f"Risk limits: Max trade ${float(self.risk_limits.max_trade_amount)}, "
                   f"Min profit {float(self.risk_limits.min_profit_threshold)}%")
        
        self.app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True
        )

def main():
    """Main entry point"""
    server = ConsolidatedTradingServer()
    server.run()

if __name__ == "__main__":
    main()
