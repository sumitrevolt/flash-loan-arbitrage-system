#!/usr/bin/env python3
"""
MCP Dashboard - Consolidated Version
===================================

This file was created by merging the following sources:
- enhanced_mcp_dashboard_with_chat.py
- dashboard/enhanced_mcp_dashboard_with_chat.py
- mcp_servers/ui/enhanced_mcp_dashboard_with_chat.py

Merged on: 2025-06-12

Real-time monitoring dashboard with integrated chat, DEX price monitoring,
and comprehensive system management for the flash loan arbitrage system.
"""

import asyncio
import os
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
import json

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import aiohttp
import requests

# Set high precision for financial calculations
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fix for Windows event loop issue
import platform
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@dataclass
class ArbitrageOpportunity:
    """Data class for arbitrage opportunities"""
    id: str
    token_pair: str
    dex_buy: str
    dex_sell: str
    buy_price: float
    sell_price: float
    profit_usd: float
    profit_percentage: float
    trade_amount: float
    confidence_score: float
    risk_level: str
    execution_priority: int
    timestamp: datetime
    gas_cost: float = 0.0
    slippage_impact: float = 0.0
    liquidity_available: float = 0.0

@dataclass 
class SystemMetrics:
    """System performance metrics"""
    total_revenue: float = 0.0
    daily_revenue: float = 0.0
    hourly_revenue: float = 0.0
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_gas_spent: float = 0.0
    net_profit: float = 0.0
    success_rate: float = 0.0
    average_profit_per_trade: float = 0.0
    best_opportunity_profit: float = 0.0
    opportunities_detected: int = 0
    execution_time_avg: float = 0.0
    uptime_seconds: float = 0.0
    system_health: str = "unknown"

class MCPDashboard:
    """Enhanced MCP Dashboard with real-time monitoring"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        self.app.config['SECRET_KEY'] = 'mcp-dashboard-secret-key'
        
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # System state
        self.chat_history: List[Dict[str, Any]] = []
        self.arbitrage_opportunities: List[ArbitrageOpportunity] = []
        self.system_metrics = SystemMetrics()
        self.dex_prices: Dict[str, Dict[str, float]] = {}
        self.mcp_servers_status: Dict[str, Dict[str, Any]] = {}
        self.ai_agents_status: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.config = {
            "coordinator_url": os.getenv("COORDINATOR_URL", "http://localhost:4000"),
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "update_interval": int(os.getenv("UPDATE_INTERVAL", "5")),
            "max_opportunities": int(os.getenv("MAX_OPPORTUNITIES", "50")),
            "max_chat_history": int(os.getenv("MAX_CHAT_HISTORY", "100"))
        }
        
        # Initialize routes and websocket handlers
        self._setup_routes()
        self._setup_websocket_handlers()
        
        # Start background tasks
        self.start_time = time.time()
        self._start_background_tasks()
        
        logger.info(f"MCP Dashboard initialized on port {port}")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html', config=self.config)
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "service": "MCP Dashboard",
                "uptime": time.time() - self.start_time,
                "version": "1.0.0"
            })
        
        @self.app.route('/api/system-status')
        def get_system_status():
            """Get comprehensive system status"""
            return jsonify({
                "system_metrics": asdict(self.system_metrics),
                "mcp_servers": self.mcp_servers_status,
                "ai_agents": self.ai_agents_status,
                "opportunities_count": len(self.arbitrage_opportunities),
                "uptime": time.time() - self.start_time,
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/api/opportunities')
        def get_opportunities():
            """Get current arbitrage opportunities"""
            opportunities_data = []
            for opp in self.arbitrage_opportunities[-self.config["max_opportunities"]:]:
                opp_dict = asdict(opp)
                opp_dict['timestamp'] = opp.timestamp.isoformat()
                opportunities_data.append(opp_dict)
            
            return jsonify({
                "opportunities": opportunities_data,
                "count": len(opportunities_data),
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/api/dex-prices')
        def get_dex_prices():
            """Get current DEX prices"""
            return jsonify({
                "prices": self.dex_prices,
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/api/chat-history')
        def get_chat_history():
            """Get chat history"""
            return jsonify({
                "messages": self.chat_history[-self.config["max_chat_history"]:],
                "count": len(self.chat_history)
            })
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get detailed metrics"""
            return jsonify({
                "metrics": asdict(self.system_metrics),
                "performance": {
                    "opportunities_per_hour": len(self.arbitrage_opportunities) / max((time.time() - self.start_time) / 3600, 1),
                    "success_rate": self.system_metrics.success_rate,
                    "average_profit": self.system_metrics.average_profit_per_trade,
                    "total_revenue": self.system_metrics.total_revenue
                },
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files"""
            return send_from_directory('static', filename)
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected: {request.sid}")
            # Send initial data
            emit('system_status', {
                "metrics": asdict(self.system_metrics),
                "opportunities": len(self.arbitrage_opportunities),
                "servers": len(self.mcp_servers_status),
                "agents": len(self.ai_agents_status)
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('chat_message')
        def handle_chat_message(data):
            """Handle chat messages"""
            try:
                message = {
                    "id": f"msg_{int(time.time() * 1000)}",
                    "user": data.get("user", "Anonymous"),
                    "message": data.get("message", ""),
                    "timestamp": datetime.now().isoformat(),
                    "type": "user"
                }
                
                self.chat_history.append(message)
                
                # Keep chat history manageable
                if len(self.chat_history) > self.config["max_chat_history"]:
                    self.chat_history = self.chat_history[-self.config["max_chat_history"]:]
                
                # Broadcast to all clients
                self.socketio.emit('new_chat_message', message)
                
                # Process with AI if available
                asyncio.create_task(self._process_chat_message(data.get("message", "")))
                
            except Exception as e:
                logger.error(f"Error handling chat message: {e}")
                emit('error', {"message": "Failed to process chat message"})
        
        @self.socketio.on('request_update')
        def handle_update_request():
            """Handle manual update requests"""
            asyncio.create_task(self._send_live_updates())
        
        @self.socketio.on('execute_opportunity')
        def handle_execute_opportunity(data):
            """Handle manual opportunity execution"""
            opportunity_id = data.get("opportunity_id")
            if opportunity_id:
                asyncio.create_task(self._execute_opportunity(opportunity_id))
    
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        def run_background():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Start monitoring tasks
            loop.create_task(self._monitor_system())
            loop.create_task(self._monitor_opportunities())
            loop.create_task(self._update_dex_prices())
            loop.create_task(self._send_periodic_updates())
            
            loop.run_forever()
        
        thread = threading.Thread(target=run_background, daemon=True)
        thread.start()
        logger.info("Background monitoring tasks started")
    
    async def _monitor_system(self):
        """Monitor system components"""
        while True:
            try:
                # Update system metrics
                self.system_metrics.uptime_seconds = time.time() - self.start_time
                
                # Fetch data from coordinator
                await self._fetch_coordinator_data()
                
                # Update health status
                if self.system_metrics.success_rate > 0.8:
                    self.system_metrics.system_health = "excellent"
                elif self.system_metrics.success_rate > 0.6:
                    self.system_metrics.system_health = "good"
                elif self.system_metrics.success_rate > 0.4:
                    self.system_metrics.system_health = "fair"
                else:
                    self.system_metrics.system_health = "poor"
                
                await asyncio.sleep(self.config["update_interval"])
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _monitor_opportunities(self):
        """Monitor arbitrage opportunities"""
        while True:
            try:
                # Simulate opportunity detection (replace with real data)
                if len(self.arbitrage_opportunities) < 10:  # Keep demo active
                    opportunity = self._generate_mock_opportunity()
                    self.arbitrage_opportunities.append(opportunity)
                    
                    # Update metrics
                    self.system_metrics.opportunities_detected += 1
                    
                    # Keep list manageable
                    if len(self.arbitrage_opportunities) > self.config["max_opportunities"]:
                        self.arbitrage_opportunities = self.arbitrage_opportunities[-self.config["max_opportunities"]:]
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Opportunity monitoring error: {e}")
                await asyncio.sleep(15)
    
    async def _update_dex_prices(self):
        """Update DEX prices"""
        while True:
            try:
                # Mock DEX price data (replace with real price fetching)
                import random
                
                dexes = ["uniswap", "sushiswap", "pancakeswap", "curve", "balancer"]
                tokens = ["ETH", "USDC", "USDT", "WBTC", "DAI"]
                
                for dex in dexes:
                    if dex not in self.dex_prices:
                        self.dex_prices[dex] = {}
                    
                    for token in tokens:
                        # Generate realistic price variations
                        base_price = {"ETH": 3000, "USDC": 1, "USDT": 1, "WBTC": 65000, "DAI": 1}[token]
                        variation = random.uniform(-0.002, 0.002)  # 0.2% variation
                        self.dex_prices[dex][token] = base_price * (1 + variation)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"DEX price update error: {e}")
                await asyncio.sleep(10)
    
    async def _send_periodic_updates(self):
        """Send periodic updates to connected clients"""
        while True:
            try:
                await self._send_live_updates()
                await asyncio.sleep(self.config["update_interval"])
            except Exception as e:
                logger.error(f"Periodic update error: {e}")
                await asyncio.sleep(10)
    
    async def _send_live_updates(self):
        """Send live updates to all connected clients"""
        try:
            # System status update
            self.socketio.emit('system_update', {
                "metrics": asdict(self.system_metrics),
                "opportunities_count": len(self.arbitrage_opportunities),
                "servers_count": len(self.mcp_servers_status),
                "agents_count": len(self.ai_agents_status),
                "timestamp": datetime.now().isoformat()
            })
            
            # Recent opportunities update
            recent_opportunities = []
            for opp in self.arbitrage_opportunities[-10:]:
                opp_dict = asdict(opp)
                opp_dict['timestamp'] = opp.timestamp.isoformat()
                recent_opportunities.append(opp_dict)
            
            self.socketio.emit('opportunities_update', {
                "opportunities": recent_opportunities,
                "total_count": len(self.arbitrage_opportunities)
            })
            
            # DEX prices update
            self.socketio.emit('prices_update', {
                "prices": self.dex_prices,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Live update error: {e}")
    
    async def _fetch_coordinator_data(self):
        """Fetch data from the system coordinator"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get system status
                async with session.get(f"{self.config['coordinator_url']}/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Update metrics from coordinator
                        if "metrics" in data:
                            metrics_data = data["metrics"]
                            self.system_metrics.total_trades = metrics_data.get("opportunities_executed", 0)
                            self.system_metrics.successful_trades = metrics_data.get("successful_trades", 0)
                            self.system_metrics.failed_trades = metrics_data.get("failed_trades", 0)
                            self.system_metrics.total_revenue = metrics_data.get("total_profit_usd", 0.0)
                            
                            if self.system_metrics.total_trades > 0:
                                self.system_metrics.success_rate = (
                                    self.system_metrics.successful_trades / self.system_metrics.total_trades
                                )
                                self.system_metrics.average_profit_per_trade = (
                                    self.system_metrics.total_revenue / self.system_metrics.total_trades
                                )
                        
                        # Update component status
                        if "agent_status" in data:
                            self.ai_agents_status = data["agent_status"]
                        
                        if "service_status" in data:
                            self.mcp_servers_status = data["service_status"]
                
        except Exception as e:
            logger.warning(f"Could not fetch coordinator data: {e}")
            # Continue with mock data for demo purposes
    
    def _generate_mock_opportunity(self) -> ArbitrageOpportunity:
        """Generate mock arbitrage opportunity for demo"""
        import random
        
        token_pairs = ["ETH/USDC", "WBTC/ETH", "USDT/USDC", "DAI/USDT"]
        dexes = ["uniswap", "sushiswap", "pancakeswap", "curve", "balancer"]
        risk_levels = ["low", "medium", "high"]
        
        token_pair = random.choice(token_pairs)
        dex_buy = random.choice(dexes)
        dex_sell = random.choice([d for d in dexes if d != dex_buy])
        
        buy_price = random.uniform(2800, 3200) if "ETH" in token_pair else random.uniform(0.98, 1.02)
        price_spread = random.uniform(0.001, 0.02)  # 0.1% to 2% spread
        sell_price = buy_price * (1 + price_spread)
        
        trade_amount = random.uniform(1000, 10000)
        profit_usd = trade_amount * price_spread
        profit_percentage = price_spread * 100
        
        return ArbitrageOpportunity(
            id=f"opp_{int(time.time() * 1000)}_{random.randint(100, 999)}",
            token_pair=token_pair,
            dex_buy=dex_buy,
            dex_sell=dex_sell,
            buy_price=buy_price,
            sell_price=sell_price,
            profit_usd=profit_usd,
            profit_percentage=profit_percentage,
            trade_amount=trade_amount,
            confidence_score=random.uniform(0.6, 0.95),
            risk_level=random.choice(risk_levels),
            execution_priority=random.randint(1, 5),
            timestamp=datetime.now(),
            gas_cost=random.uniform(20, 100),
            slippage_impact=random.uniform(0.1, 1.0),
            liquidity_available=random.uniform(50000, 500000)
        )
    
    async def _process_chat_message(self, message: str):
        """Process chat message with AI (if available)"""
        try:
            # Simple AI responses for demo
            responses = {
                "status": "System is running normally. All components are operational.",
                "help": "Available commands: status, opportunities, metrics, health",
                "opportunities": f"Currently tracking {len(self.arbitrage_opportunities)} opportunities.",
                "metrics": f"Success rate: {self.system_metrics.success_rate:.1%}, Total revenue: ${self.system_metrics.total_revenue:.2f}",
                "health": f"System health: {self.system_metrics.system_health}"
            }
            
            # Find matching response
            response_text = "I'm here to help! Try asking about status, opportunities, metrics, or health."
            for keyword, response in responses.items():
                if keyword.lower() in message.lower():
                    response_text = response
                    break
            
            # Add AI response to chat
            ai_message = {
                "id": f"ai_{int(time.time() * 1000)}",
                "user": "AI Assistant",
                "message": response_text,
                "timestamp": datetime.now().isoformat(),
                "type": "ai"
            }
            
            self.chat_history.append(ai_message)
            self.socketio.emit('new_chat_message', ai_message)
            
        except Exception as e:
            logger.error(f"Chat processing error: {e}")
    
    async def _execute_opportunity(self, opportunity_id: str):
        """Execute an arbitrage opportunity"""
        try:
            # Find the opportunity
            opportunity = None
            for opp in self.arbitrage_opportunities:
                if opp.id == opportunity_id:
                    opportunity = opp
                    break
            
            if not opportunity:
                self.socketio.emit('execution_error', {"message": "Opportunity not found"})
                return
            
            # Simulate execution
            success = opportunity.confidence_score > 0.7  # Simple success criteria
            
            if success:
                self.system_metrics.successful_trades += 1
                self.system_metrics.total_revenue += opportunity.profit_usd
            else:
                self.system_metrics.failed_trades += 1
            
            self.system_metrics.total_trades += 1
            
            # Update success rate
            if self.system_metrics.total_trades > 0:
                self.system_metrics.success_rate = (
                    self.system_metrics.successful_trades / self.system_metrics.total_trades
                )
            
            # Notify clients
            self.socketio.emit('execution_result', {
                "opportunity_id": opportunity_id,
                "success": success,
                "profit": opportunity.profit_usd if success else 0,
                "message": f"Execution {'successful' if success else 'failed'}"
            })
            
            logger.info(f"Executed opportunity {opportunity_id}: {'success' if success else 'failed'}")
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            self.socketio.emit('execution_error', {"message": str(e)})
    
    def create_dashboard_template(self):
        """Create the dashboard HTML template"""
        template_dir = Path("templates")
        template_dir.mkdir(exist_ok=True)
        
        dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Flash Loan Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a0a; color: #fff; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #333; }
        .metric-value { font-size: 2em; font-weight: bold; color: #4CAF50; }
        .metric-label { color: #aaa; margin-top: 5px; }
        .opportunities-section, .chat-section { background: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 20px; }
        .opportunity-item { background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #4CAF50; }
        .opportunity-profit { color: #4CAF50; font-weight: bold; }
        .opportunity-risk { padding: 3px 8px; border-radius: 12px; font-size: 0.8em; }
        .risk-low { background: #4CAF50; }
        .risk-medium { background: #FF9800; }
        .risk-high { background: #f44336; }
        .chat-messages { height: 300px; overflow-y: auto; background: #2a2a2a; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
        .chat-input { width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid #555; border-radius: 5px; color: #fff; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-healthy { background: #4CAF50; }
        .status-warning { background: #FF9800; }
        .status-error { background: #f44336; }
        .btn { background: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #45a049; }
        .btn-danger { background: #f44336; }
        .btn-danger:hover { background: #da190b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MCP Flash Loan Dashboard</h1>
            <p>Real-time monitoring and control for autonomous arbitrage trading</p>
            <div id="system-status">
                <span class="status-indicator status-healthy"></span>
                <span>System Status: <span id="health-status">Initializing...</span></span>
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="total-revenue">$0.00</div>
                <div class="metric-label">Total Revenue</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="success-rate">0%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="total-trades">0</div>
                <div class="metric-label">Total Trades</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="opportunities-count">0</div>
                <div class="metric-label">Active Opportunities</div>
            </div>
        </div>

        <div class="opportunities-section">
            <h2>🎯 Live Arbitrage Opportunities</h2>
            <div id="opportunities-list">
                <p>Loading opportunities...</p>
            </div>
        </div>

        <div class="chat-section">
            <h2>💬 AI Assistant Chat</h2>
            <div id="chat-messages" class="chat-messages"></div>
            <input type="text" id="chat-input" class="chat-input" placeholder="Ask about system status, opportunities, or metrics...">
        </div>
    </div>

    <script>
        const socket = io();
        
        // Update system metrics
        function updateMetrics(metrics) {
            document.getElementById('total-revenue').textContent = `$${metrics.total_revenue.toFixed(2)}`;
            document.getElementById('success-rate').textContent = `${(metrics.success_rate * 100).toFixed(1)}%`;
            document.getElementById('total-trades').textContent = metrics.total_trades;
            document.getElementById('health-status').textContent = metrics.system_health;
        }
        
        // Update opportunities list
        function updateOpportunities(opportunities) {
            const container = document.getElementById('opportunities-list');
            document.getElementById('opportunities-count').textContent = opportunities.length;
            
            if (opportunities.length === 0) {
                container.innerHTML = '<p>No opportunities available</p>';
                return;
            }
            
            container.innerHTML = opportunities.map(opp => `
                <div class="opportunity-item">
                    <strong>${opp.token_pair}</strong> - ${opp.dex_buy} → ${opp.dex_sell}
                    <div class="opportunity-profit">Profit: $${opp.profit_usd.toFixed(2)} (${opp.profit_percentage.toFixed(2)}%)</div>
                    <div>Confidence: ${(opp.confidence_score * 100).toFixed(1)}% | Risk: <span class="opportunity-risk risk-${opp.risk_level}">${opp.risk_level}</span></div>
                    <button class="btn" onclick="executeOpportunity('${opp.id}')">Execute</button>
                </div>
            `).join('');
        }
        
        // Add chat message
        function addChatMessage(msg) {
            const container = document.getElementById('chat-messages');
            const msgDiv = document.createElement('div');
            msgDiv.innerHTML = `
                <strong>${msg.user}:</strong> ${msg.message}
                <div style="font-size: 0.8em; color: #aaa;">${new Date(msg.timestamp).toLocaleTimeString()}</div>
            `;
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        // Execute opportunity
        function executeOpportunity(opportunityId) {
            socket.emit('execute_opportunity', { opportunity_id: opportunityId });
        }
        
        // Socket event handlers
        socket.on('system_update', data => updateMetrics(data.metrics));
        socket.on('opportunities_update', data => updateOpportunities(data.opportunities));
        socket.on('new_chat_message', addChatMessage);
        
        socket.on('execution_result', data => {
            addChatMessage({
                user: 'System',
                message: `Opportunity ${data.opportunity_id}: ${data.message}`,
                timestamp: new Date().toISOString()
            });
        });
        
        // Chat input handler
        document.getElementById('chat-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const message = this.value.trim();
                if (message) {
                    socket.emit('chat_message', { user: 'User', message: message });
                    this.value = '';
                }
            }
        });
        
        // Initial data request
        socket.emit('request_update');
    </script>
</body>
</html>"""
        
        with open(template_dir / "dashboard.html", 'w') as f:
            f.write(dashboard_html)
        
        logger.info("Dashboard template created")
    
    def run(self, debug: bool = False):
        """Run the dashboard"""
        # Create template if it doesn't exist
        if not Path("templates/dashboard.html").exists():
            self.create_dashboard_template()
        
        logger.info(f"Starting MCP Dashboard on port {self.port}")
        logger.info(f"Dashboard will be available at: http://localhost:{self.port}")
        
        self.socketio.run(
            self.app,
            host='0.0.0.0',
            port=self.port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )

def main():
    """Main function to start the dashboard"""
    port = int(os.getenv("DASHBOARD_PORT", 8080))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    dashboard = MCPDashboard(port=port)
    dashboard.run(debug=debug)

if __name__ == "__main__":
    main()
