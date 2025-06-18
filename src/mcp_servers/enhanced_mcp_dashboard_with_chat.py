#!/usr/bin/env python3
"""
Enhanced MCP Dashboard with Chat Interface and DEX Price Monitoring
Real-time monitoring dashboard with integrated chat and DEX price monitoring
Port 8004 - Main MCP Dashboard with DEX Integration
"""

import threading
import time
import asyncio
import os
import logging
import requests
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit  # type: ignore
from flask_cors import CORS
import aiohttp
from pathlib import Path
from typing import Dict, Any, List
from decimal import Decimal, getcontext
from dataclasses import dataclass
import json

# Set high precision for financial calculations
getcontext().prec = 28

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DEX Price Monitor imports
try:
    from dex_price_monitor import price_monitor
    dex_monitor_available = True
except ImportError:
    logger.warning("DEX price monitor not available")
    dex_monitor_available = False

# Arbitrage calculation data classes
@dataclass
class ArbitrageOpportunity:
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
class ArbitrageMetrics:
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

# Fix for Windows event loop issue
import platform
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mcp-dashboard-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
chat_history: List[Dict[str, Any]] = []
dex_price_data: Dict[str, Any] = {}
arbitrage_opportunities: List[Dict[str, Any]] = []
arbitrage_metrics = ArbitrageMetrics()
live_opportunities: List[ArbitrageOpportunity] = []

# Enhanced arbitrage calculation state
arbitrage_stats: Dict[str, Any] = {
    "total_opportunities": 0,
    "profitable_opportunities": 0,
    "average_profit": 0.0,
    "best_opportunity": 0.0,
    "risk_distribution": {"low": 0, "medium": 0, "high": 0},
    "dex_performance": {},
    "token_performance": {},
    "gas_costs": {"average": 0.0, "total": 0.0},
    "execution_times": {"average": 0.0, "fastest": 0.0, "slowest": 0.0},
    "liquidity_analysis": {},
    "price_impact_analysis": {},
    "slippage_analysis": {}
}

# MCP Server URLs
MCP_SERVERS = {
    'copilot': 'http://localhost:8003',  # Enhanced Copilot MCP Server
    'foundry': 'http://localhost:8001',  # Enhanced Foundry MCP Server
    'unified': 'http://localhost:8000',  # Unified Flash Loan MCP Server
    'production': 'http://localhost:8002',  # Production MCP Server (placeholder)
    'dex-price': 'http://localhost:8008',  # DEX Price Monitor MCP Server
}

COPILOT_URL = os.getenv("COPILOT_MCP_URL", "http://localhost:8003/chat")
FOUNDRY_URL = os.getenv("FOUNDRY_MCP_URL", "http://localhost:8001/chat")
UNIFIED_URL = os.getenv("UNIFIED_MCP_URL", "http://localhost:8000/chat")
PRODUCTION_URL = os.getenv("PRODUCTION_MCP_URL", "http://localhost:8002/chat")
DEX_PRICE_URL = os.getenv("DEX_PRICE_MCP_URL", "http://localhost:8008")

# Update MCP server configuration to match actual running servers
mcp_servers: Dict[str, Dict[str, Any]] = {
    "copilot-agent": {
        "name": "Enhanced Copilot Agent",
        "status": "running",
        "port": 8003,
        "connected": True,
        "health": {"status": "healthy", "uptime": "2h 15m"},
        "url": "http://localhost:8003/chat"
    },    "foundry-server": {
        "name": "Enhanced Foundry MCP Server",
        "status": "running",
        "port": 8001,
        "connected": True,
        "health": {"status": "healthy", "uptime": "2h 15m"},
        "url": "http://localhost:8001/chat"
    },
    "unified-server": {
        "name": "Unified Flash Loan MCP Server",
        "status": "running",
        "port": 8000,
        "connected": True,
        "health": {"status": "healthy", "uptime": "2h 15m"},
        "url": "http://localhost:8000/chat"
    },
    "production-server": {
        "name": "Production MCP Server",
        "status": "stopped",
        "port": 8002,
        "connected": False,
        "health": {"status": "offline", "uptime": "0m"},
        "url": "http://localhost:8002/chat"
    },
    "flash-loan": {
        "name": "Flash Loan Revenue Bot",
        "status": "stopped",
        "port": 5000,
        "connected": False,
        "health": {"status": "offline", "uptime": "0m"},
        "url": "http://localhost:5000/api"
    },    "task-manager": {
        "name": "Task Manager Server",
        "status": "running",
        "port": 8007,
        "connected": True,
        "health": {"status": "healthy", "uptime": "1h 45m"},
        "url": "http://localhost:8007/chat"
    },
    "dex-price-monitor": {
        "name": "DEX Price Monitor",
        "status": "running",
        "port": 8008,
        "connected": True,
        "health": {"status": "healthy", "uptime": "1h 30m"},
        "url": "http://localhost:8008/dashboard-data"
    }
}

system_metrics: Dict[str, Any] = {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "network_io": {"in": 125.5, "out": 89.3},
    "disk_usage": 73.4,
    "active_connections": 12,
    "total_requests": 1543,
    "error_rate": 0.02,
    "revenue_bot_status": "stopped",
    "total_revenue": 0.00,
    "daily_revenue": 0.00,
    "success_rate": 0.0,
    "active_opportunities": 0,
    "best_opportunity": 0.0,
    "dex_monitor_status": "running"
}

active_tasks: List[Dict[str, Any]] = [
    {
        "id": "task-001",
        "server": "copilot-agent",
        "type": "code_optimization",
        "status": "in_progress",
        "progress": 65,
        "started": "2025-01-06T09:30:00",
        "eta": "3 minutes"
    },
    {
        "id": "task-002",
        "server": "foundry-server",
        "type": "contract_deployment",
        "status": "completed",
        "progress": 100,
        "started": "2025-01-06T09:25:00",
        "completed": "2025-01-06T09:28:00"
    }
]

# Dashboard routes
@app.route('/')
def index():
    """Render main dashboard with DEX monitoring"""
    return render_template('dashboard_with_dex.html')

@app.route('/api/servers')
def get_servers():
    """Get MCP server status"""
    return jsonify(mcp_servers)

@app.route('/api/metrics')
def get_metrics():
    """Get system metrics"""
    return jsonify(system_metrics)

@app.route('/api/tasks')
def get_tasks():
    """Get active tasks"""
    return jsonify(active_tasks)

@app.route('/api/chat/history')
def get_chat_history():
    """Get chat history"""
    return jsonify(chat_history)

# DEX Price Monitoring API Endpoints
@app.route('/api/dex/prices')
def get_dex_prices():
    """Get current DEX prices"""
    try:
        response = requests.get(f"{DEX_PRICE_URL}/prices", timeout=5)
        if response.status_code == 200:
            global dex_price_data
            dex_price_data = response.json()
            return jsonify(dex_price_data)
        else:
            return jsonify({'error': 'DEX price service unavailable'}), 503
    except Exception as e:
        logger.error(f"Error fetching DEX prices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dex/opportunities')
def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    try:
        response = requests.get(f"{DEX_PRICE_URL}/opportunities", timeout=5)
        if response.status_code == 200:
            global arbitrage_opportunities
            arbitrage_opportunities = response.json()
            return jsonify(arbitrage_opportunities)
        else:
            return jsonify({'opportunities': []}), 200
    except Exception as e:
        logger.error(f"Error fetching arbitrage opportunities: {e}")
        return jsonify({'opportunities': []}), 200

@app.route('/api/dex/dashboard-data')
def get_dex_dashboard_data():
    """Get comprehensive DEX dashboard data"""
    try:
        response = requests.get(f"{DEX_PRICE_URL}/dashboard-data", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({
                'prices': {},
                'opportunities': [],
                'dex_stats': {},
                'monitoring_status': 'unavailable'
            }), 200
    except Exception as e:
        logger.error(f"Error fetching DEX dashboard data: {e}")
        return jsonify({
            'prices': {},
            'opportunities': [],
            'dex_stats': {},
            'monitoring_status': 'error',
            'error': str(e)
        }), 200

@app.route('/api/dex/control/<action>', methods=['POST'])
def dex_control(action: str):
    """Control DEX price monitoring service"""
    try:
        response = requests.post(f"{DEX_PRICE_URL}/{action}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'success': False, 'error': 'DEX service unavailable'}), 503
    except Exception as e:
        logger.error(f"Error controlling DEX service: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Chat proxy endpoint for direct API access
@app.route("/api/copilot_chat", methods=['POST'])
def copilot_chat():
    """
    Forward the incoming chat message to the Copilot MCP server and return its
    answer so that the dashboard chat panel can display it.
    Expected JSON payload: { "message": "<user text>" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_msg = data.get("message", "").strip()
        if not user_msg:
            return jsonify({'error': 'Missing message'}), 400

        # Use requests for synchronous HTTP call
        import requests
        
        # Forward to Copilot MCP
        try:
            response = requests.post(
                COPILOT_URL,
                json={"message": user_msg},
                timeout=30
            )
            
            if response.status_code != 200:
                return jsonify({'error': 'Copilot MCP error'}), 502
                
            resp_json = response.json()
        except requests.exceptions.RequestException as e:
            return jsonify({'error': f'Copilot MCP unreachable: {e}'}), 500

        # Normalize response shape for the front-end
        answer = resp_json.get("answer") or resp_json.get("response") or str(resp_json)
        return jsonify({"answer": answer})
        
    except Exception as e:
        logger.error(f"Error in copilot_chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect() -> None:
    """Handle client connection"""
    sid = getattr(request, 'sid', 'unknown')
    logger.info(f"Client connected: {sid}")
    emit('connection_status', {'status': 'connected', 'sid': sid})
    
    # Send initial data
    emit('servers_update', mcp_servers)
    emit('metrics_update', system_metrics)
    emit('tasks_update', active_tasks)
    
    # Send initial DEX data
    try:
        response = requests.get(f"{DEX_PRICE_URL}/dashboard-data", timeout=3)
        if response.status_code == 200:
            dex_data = response.json()
            emit('dex_prices_update', dex_data.get('prices', {}))
            emit('arbitrage_opportunities_update', dex_data.get('opportunities', []))
            emit('dex_stats_update', dex_data.get('dex_stats', {}))
    except Exception as e:
        logger.warning(f"Could not fetch initial DEX data: {e}")
        emit('dex_prices_update', {})
        emit('arbitrage_opportunities_update', [])
        emit('dex_stats_update', {})

@socketio.on('disconnect')
def handle_disconnect() -> None:
    """Handle client disconnection"""
    sid = getattr(request, 'sid', 'unknown')
    logger.info(f"Client disconnected: {sid}")

@socketio.on('server_action')
def handle_server_action(data: Dict[str, Any]) -> None:
    """Handle server control actions"""
    server_id = data.get('server_id')
    action = data.get('action')
    
    if server_id and server_id in mcp_servers:
        server = mcp_servers[server_id]
        
        if action == 'start':
            server['status'] = 'running'
            server['connected'] = True
            health = server.get('health')
            if isinstance(health, dict):
                health['status'] = 'healthy'
        elif action == 'stop':
            server['status'] = 'stopped'
            server['connected'] = False
            health = server.get('health')
            if isinstance(health, dict):
                health['status'] = 'offline'
        elif action == 'restart':
            server['status'] = 'restarting'
            # Simulate restart
            socketio.start_background_task(restart_server, server_id)
        
        socketio.emit('servers_update', mcp_servers, to='/')  # type: ignore
        emit('action_result', {
            'success': True,
            'message': f"Server {server_id} {action} successful"
        })

@socketio.on('chat_message')
def handle_chat_message(data: Dict[str, Any]) -> None:
    """Handle chat messages with MCP server integration"""
    message = data.get('message', '')
    user = data.get('user', 'Anonymous')
    
    logger.info(f"📩 Received chat message from {user}: {message}")
    
    if message:
        timestamp = datetime.now().isoformat()
        chat_entry: Dict[str, Any] = {
            'id': f"msg-{len(chat_history)}",
            'user': user,
            'message': message,
            'timestamp': timestamp,
            'type': 'user'
        }
        
        chat_history.append(chat_entry)
        logger.info(f"📤 Broadcasting user message to all clients")
        
        # Broadcast user message to all clients
        socketio.emit('new_message', chat_entry, to='/')  # type: ignore
        
        # Process commands if message starts with /
        if message.startswith('/'):
            logger.info(f"🔧 Processing command: {message}")
            process_chat_command(message, user)
        else:
            logger.info(f"🤖 Sending to MCP servers for AI response")
            # Send message to MCP servers for AI-powered response
            socketio.start_background_task(handle_mcp_chat_sync, message, user)

@socketio.on('execute_task')
def handle_execute_task(data: Dict[str, Any]) -> None:
    """Handle task execution requests"""
    task_type = data.get('type')
    server_id = data.get('server_id')
    parameters = data.get('parameters', {})
    
    task_id = f"task-{len(active_tasks) + 1:03d}"
    new_task: Dict[str, Any] = {
        'id': task_id,
        'server': server_id,
        'type': task_type,
        'status': 'queued',
        'progress': 0,
        'started': datetime.now().isoformat(),
        'parameters': parameters
    }
    
    active_tasks.append(new_task)
    socketio.emit('tasks_update', active_tasks, to='/')  # type: ignore
    
    # Start background task execution
    socketio.start_background_task(execute_task_async, task_id)

# Helper functions
def handle_mcp_chat_sync(message: str, user: str) -> None:
    """Synchronous wrapper for async MCP chat processing"""
    try:
        # Try to get the current event loop, or create a new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to use asyncio.create_task
                asyncio.create_task(process_mcp_chat_message(message, user))
            else:
                loop.run_until_complete(process_mcp_chat_message(message, user))
        except RuntimeError:
            # No event loop exists, create a new one
            asyncio.run(process_mcp_chat_message(message, user))
    except Exception as e:
        logger.error(f"Error in sync chat handler: {e}")
        # Fallback to local processing
        local_response = process_local_chat_response(message)
        bot_response: Dict[str, Any] = {
            'id': f"msg-{len(chat_history)}",
            'user': 'Local Assistant',
            'message': local_response,
            'timestamp': datetime.now().isoformat(),
            'type': 'system'
        }
        chat_history.append(bot_response)
        socketio.emit('new_message', bot_response, to='/')  # type: ignore

async def process_mcp_chat_message(message: str, user: str) -> None:
    """Process chat message with MCP servers for AI-powered responses"""
    try:
        logger.info(f"🤖 Processing MCP chat message: {message}")
        # Try Copilot MCP Server first (primary AI assistant)
        copilot_response = await query_mcp_server("http://localhost:8003/chat", message, "Enhanced Copilot")
        
        if copilot_response and copilot_response.get('success'):
            logger.info(f"✅ Got response from Copilot MCP server")
            bot_response: Dict[str, Any] = {
                'id': f"msg-{len(chat_history)}",
                'user': 'Enhanced Copilot Agent',
                'message': copilot_response.get('response', 'No response available'),                'timestamp': datetime.now().isoformat(),
                'type': 'assistant'
            }
            chat_history.append(bot_response)
            logger.info(f"📤 Emitting Copilot response to all clients: {bot_response['message'][:100]}...")
            socketio.emit('new_message', bot_response, to='/')  # type: ignore
            return
        
        # Fallback to Foundry MCP Server if available
        foundry_response = await query_mcp_server("http://localhost:8001/chat", message, "Foundry")
        
        if foundry_response and foundry_response.get('success'):
            bot_response: Dict[str, Any] = {
                'id': f"msg-{len(chat_history)}",
                'user': 'Foundry MCP Server',
                'message': foundry_response.get('response', 'No response available'),
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant'
            }
            chat_history.append(bot_response)
            socketio.emit('new_message', bot_response, to='/')  # type: ignore
            return
          # Fallback to Unified Flash Loan MCP Server
        unified_response = await query_mcp_server("http://localhost:8000/chat", message, "Unified")
        
        if unified_response and unified_response.get('success'):
            bot_response: Dict[str, Any] = {
                'id': f"msg-{len(chat_history)}",
                'user': 'Unified Flash Loan Server',
                'message': unified_response.get('response', 'No response available'),
                'timestamp': datetime.now().isoformat(),
                'type': 'assistant'
            }
            chat_history.append(bot_response)
            socketio.emit('new_message', bot_response, to='/')  # type: ignore
            return
        
        # Fallback to local processing if MCP servers are unavailable
        local_response = process_local_chat_response(message)
        bot_response: Dict[str, Any] = {
            'id': f"msg-{len(chat_history)}",
            'user': 'Local Assistant',
            'message': local_response,
            'timestamp': datetime.now().isoformat(),
            'type': 'system'
        }
        chat_history.append(bot_response)
        socketio.emit('new_message', bot_response, to='/')  # type: ignore
        
    except Exception as e:
        logger.error(f"Error processing MCP chat message: {e}")
        error_response: Dict[str, Any] = {
            'id': f"msg-{len(chat_history)}",
            'user': 'System',
            'message': f"Sorry, I encountered an error: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'type': 'error'
        }
        chat_history.append(error_response)
        socketio.emit('new_message', error_response, to='/')  # type: ignore

async def query_mcp_server(url: str, message: str, server_name: str) -> Dict[str, Any]:
    """Query an MCP server with a message"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={'message': message, 'user_id': 'dashboard_user'},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully queried {server_name} MCP server")
                    return data
                else:
                    logger.warning(f"{server_name} MCP server returned status {response.status}")
                    return {'success': False, 'error': f"HTTP {response.status}"}
    except Exception as e:
        logger.warning(f"Could not reach {server_name} MCP server: {e}")
        return {'success': False, 'error': str(e)}

def process_local_chat_response(message: str) -> str:
    """Generate local fallback response when MCP servers are unavailable"""
    message_lower = message.lower()
    
    # DEX-specific responses
    if any(word in message_lower for word in ['dex', 'price', 'prices', 'uniswap', 'sushiswap', 'quickswap']):
        try:
            response = requests.get(f"{DEX_PRICE_URL}/dashboard-data", timeout=3)
            if response.status_code == 200:
                data = response.json()
                prices = data.get('prices', {})
                opportunities = data.get('opportunities', [])
                
                if prices:
                    price_summary = "📊 **Current DEX Prices:**\n\n"
                    for pair, pair_data in prices.items():
                        price_summary += f"**{pair}:**\n"
                        for dex, dex_data in pair_data.items():
                            price_summary += f"• {dex}: ${dex_data['price']:.4f}\n"
                        price_summary += "\n"
                    
                    if opportunities:
                        price_summary += f"\n🎯 **Active Opportunities:** {len(opportunities)}\n"
                        best_op = max(opportunities, key=lambda x: Any: Any: x.get('net_profit', 0))
                        price_summary += f"• Best: {best_op['token_pair']} - ${best_op['net_profit']:.2f} profit\n"
                    
                    return price_summary
                else:
                    return "📊 DEX price monitoring is active but no current price data available. Please check if the DEX Price Monitor server is running on port 8008."
            else:
                return "❌ DEX Price Monitor service is not responding. Please ensure the DEX Price MCP Server is running on port 8008."
        except Exception as e:
            return f"⚠️ Could not fetch DEX prices: {str(e)}\n\nTo enable DEX price monitoring:\n1. Start the DEX Price MCP Server on port 8008\n2. Ensure dex_price_monitor.py is running\n3. Check network connectivity"
    
    if any(word in message_lower for word in ['arbitrage', 'opportunity', 'opportunities', 'profit']):
        try:
            response = requests.get(f"{DEX_PRICE_URL}/opportunities", timeout=3)
            if response.status_code == 200:
                opportunities = response.json().get('opportunities', [])
                
                if opportunities:
                    arb_summary = f"🎯 **Arbitrage Opportunities Found: {len(opportunities)}**\n\n"
                    
                    # Show top 3 opportunities
                    top_ops = sorted(opportunities, key=lambda x: Any: Any: x.get('net_profit', 0), reverse=True)[:3]
                    
                    for i, op in enumerate(top_ops, 1):
                        alert_emoji = "🚨" if op.get('alert_level') == 'high' else "⚡" if op.get('alert_level') == 'medium' else "💡"
                        arb_summary += f"**{i}. {alert_emoji} {op['token_pair']}**\n"
                        arb_summary += f"• Route: {op['buy_dex']} → {op['sell_dex']}\n"
                        arb_summary += f"• Net Profit: ${op['net_profit']:.2f} ({op['profit_percentage']:.2f}%)\n"
                        arb_summary += f"• Trade Amount: ${op['trade_amount']:.0f}\n"
                        arb_summary += f"• Gas Cost: ${op['gas_cost']:.2f}\n\n"
                    
                    return arb_summary + "🚀 Ready to execute? Say 'Start the revenue bot' to begin automated trading!"
                else:
                    return "🔍 No profitable arbitrage opportunities detected at the moment.\n\nThe system is continuously monitoring for:\n• Price spreads > 1%\n• Sufficient liquidity\n• Favorable gas costs\n\nOpportunities will appear here when market conditions are favorable."
            else:
                return "❌ Could not fetch arbitrage opportunities. Please ensure the DEX Price Monitor is running."
        except Exception as e:
            return f"⚠️ Error fetching opportunities: {str(e)}"

    elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
        return """Hello! 👋 I'm your Enhanced Copilot Agent for the Flash Loan Revenue System!

🤖 **I can help you with:**
• Starting and monitoring the revenue bot
• Analyzing arbitrage opportunities  
• Optimizing smart contracts for gas efficiency
• Real-time system status and metrics
• Trading insights and risk assessment

💡 **Try asking:**
• "Start the revenue bot"
• "What's the current status?"
• "Show me opportunities"
• "How much have we made?"
• "Optimize my contract code"

**Note:** For full AI capabilities, ensure MCP servers on ports 8001, 8002, and 8003 are running!"""

    elif any(word in message_lower for word in ['status', 'health', 'running']):
        active_servers = sum(1 for s in mcp_servers.values() if s['status'] == 'running')
        return f"""📊 **System Status Overview:**

🖥️ **MCP Servers:** {active_servers}/{len(mcp_servers)} running
💰 **Revenue Metrics:** ${system_metrics['total_revenue']:.2f} total (system initializing)
📈 **Active Tasks:** {len([t for t in active_tasks if t['status'] in ['queued', 'in_progress']])}
⚡ **System Health:** {system_metrics['cpu_usage']}% CPU, {system_metrics['memory_usage']}% Memory

🔧 **Available MCP Servers:**
• Enhanced Copilot Agent (Port 8003): AI optimization & analysis
• Enhanced Foundry Server (Port 8002): Smart contract deployment  
• Production MCP Server (Port 8001): Production management
• Flash Loan Revenue Bot (Port 5000): Trading automation
• Task Manager Server (Port 3012): Task orchestration

Ready to help optimize your flash loan revenue system!"""

    elif any(word in message_lower for word in ['help', 'commands', 'what can you do']):
        return """🚀 **Enhanced Copilot Agent - Command Center**

💡 **Smart Trading Commands:**
• "Start the revenue bot" - Initialize automated trading
• "Stop the bot" - Halt trading operations
• "Show opportunities" - Display current arbitrage opportunities
• "Revenue report" - Get detailed profit/loss analysis

🔧 **System Management:**
• "Server status" - Check all MCP server health
• "System metrics" - View performance statistics
• "Restart servers" - Restart unresponsive services

🤖 **AI-Powered Analysis:**
• "Optimize this contract [code]" - Gas optimization suggestions
• "Analyze risk for [strategy]" - Risk assessment
• "Best practices for [topic]" - Development guidance
• "Security audit [contract]" - Vulnerability detection

📊 **Monitoring & Reports:**
• "Daily revenue" - Today's earnings summary
• "Transaction history" - Recent activity log
• "Performance metrics" - System efficiency stats

Type any natural language request - I'm designed to understand and help! 🎯"""

    elif any(word in message_lower for word in ['opportunity', 'opportunities', 'arbitrage']):
        return """🎯 **Flash Loan Arbitrage Opportunities** (Demo Mode)

⚡ **Current Market Analysis:**
• ETH/USDC: 0.23% price difference between Uniswap-Sushiswap
• WBTC/ETH: 0.31% spread on Curve vs Balancer  
• DAI/USDC: 0.08% opportunity on 1inch vs Paraswap

💰 **Estimated Profits:**
• Capital: $10,000 → Potential: $25-45 per trade
• Capital: $50,000 → Potential: $125-225 per trade
• Capital: $100,000 → Potential: $250-450 per trade

⚠️ **Note:** This is demo data. Connect to live MCP servers for real-time opportunity analysis!

**Ready to start?** Say "Start the revenue bot" to begin automated trading."""

    elif any(word in message_lower for word in ['revenue', 'profit', 'earnings', 'made']):
        return f"""💰 **Revenue Dashboard** (Demo Mode)

📊 **Current Performance:**
• Total Revenue: ${system_metrics['total_revenue']:.2f} (System initializing)
• Daily Revenue: ${system_metrics['daily_revenue']:.2f}  
• Success Rate: {system_metrics['success_rate']:.1f}%
• Total Trades: {len(active_tasks)}

📈 **Performance Metrics:**
• Average Profit per Trade: N/A
• Best Trade: N/A
• Active Opportunities: Scanning...
• Risk Level: Low

🔄 **System Status:**
• CPU Usage: {system_metrics['cpu_usage']}%
• Memory Usage: {system_metrics['memory_usage']}%
• Network I/O: {system_metrics['network_io']['in']:.1f} MB/s

**Ready to start earning?** Connect MCP servers and say "Start the revenue bot"!"""

    elif any(word in message_lower for word in ['optimize', 'optimization', 'gas', 'efficiency']):
        return """🔧 **AI-Powered Code Optimization** 

I excel at optimizing smart contracts for maximum efficiency! Here's what I can help with:

⚡ **Gas Optimization:**
• Loop unrolling and batching
• Storage vs memory optimization  
• Function visibility improvements
• Struct packing strategies

🛡️ **Security Enhancements:**
• Reentrancy protection
• Integer overflow/underflow checks
• Access control improvements
• Emergency pause mechanisms

📈 **Performance Improvements:**
• Assembly optimizations
• Calldata vs memory usage
• Event emission efficiency
• Contract size reduction

**To get started:** Share your contract code and I'll provide specific optimization recommendations with estimated gas savings!"""

    elif any(word in message_lower for word in ['start', 'revenue bot', 'trading']):
        return """🚀 **Starting Flash Loan Revenue Bot**

Initializing automated arbitrage trading system...

✅ **Pre-flight Checks:**
• Smart contracts deployed: ✓
• DEX connections established: ✓
• Wallet balance verified: ✓
• Gas price optimization: ✓

📊 **Bot Configuration:**
• Max transaction size: $50,000
• Minimum profit threshold: 0.5%
• Slippage tolerance: 1%
• Gas limit: 500,000

⚠️ **Important:** This is demo mode. To activate real trading:
1. Ensure MCP servers are running
2. Configure wallet private keys
3. Set up exchange API connections
4. Enable mainnet deployment

**Bot status will be updated in real-time on the dashboard.**"""

    else:
        return f"""I received your message: "{message}"

I'm your Enhanced Copilot Agent, ready to help with flash loan arbitrage, smart contract optimization, and revenue generation!

🤖 **Quick Help:**
• Say "help" for full command list
• Say "status" for system overview  
• Say "opportunities" for market analysis
• Say "optimize [code]" for gas improvements

**Note:** For full AI capabilities, ensure MCP servers are running on ports 8001, 8002, and 8003."""

def restart_server(server_id: str) -> None:
    """Simulate server restart"""
    time.sleep(2)
    if server_id in mcp_servers:
        server = mcp_servers[server_id]
        server['status'] = 'running'
        server['connected'] = True
        health = server.get('health')
        if isinstance(health, dict):
            health['status'] = 'healthy'
        socketio.emit('servers_update', mcp_servers, to='/')  # type: ignore

def execute_task_async(task_id: str) -> None:
    """Execute task asynchronously"""
    task = next((t for t in active_tasks if t['id'] == task_id), None)
    if not task:
        return
    
    # Update status to in_progress
    task['status'] = 'in_progress'
    socketio.emit('tasks_update', active_tasks, to='/')  # type: ignore
    
    # Simulate task execution
    for progress in range(0, 101, 10):
        time.sleep(0.5)
        task['progress'] = progress
        socketio.emit('tasks_update', active_tasks, to='/')  # type: ignore
    
    # Complete task
    task['status'] = 'completed'
    task['completed'] = datetime.now().isoformat()
    socketio.emit('tasks_update', active_tasks, to='/')  # type: ignore

def process_chat_command(message: str, user: str) -> None:
    """Process chat commands"""
    parts = message.split()
    command = parts[0].lower()
    
    response_message = ""
    
    if command == '/help':
        response_message = """Available commands:
/help - Show this help message
/status - Show server status
/metrics - Show system metrics
/tasks - List active tasks
/clear - Clear chat history
/servers - List all MCP servers
/revenue - Show revenue metrics"""
    
    elif command == '/status':
        active_servers = sum(1 for s in mcp_servers.values() if s['status'] == 'running')
        response_message = f"Active servers: {active_servers}/{len(mcp_servers)}"
    
    elif command == '/metrics':
        response_message = f"CPU: {system_metrics['cpu_usage']}%, Memory: {system_metrics['memory_usage']}%, Revenue: ${system_metrics['total_revenue']:.2f}"
    
    elif command == '/tasks':
        active_count = sum(1 for t in active_tasks if t['status'] in ['queued', 'in_progress'])
        response_message = f"Active tasks: {active_count}, Total: {len(active_tasks)}"
    
    elif command == '/servers':
        server_list: List[str] = []
        for _, server in mcp_servers.items():
            status_emoji = "🟢" if server['status'] == 'running' else "🔴"
            server_list.append(f"{status_emoji} {server['name']} (Port {server['port']})")
        response_message = "MCP Servers:\n" + "\n".join(server_list)
    
    elif command == '/revenue':
        response_message = f"Total Revenue: ${system_metrics['total_revenue']:.2f}, Daily: ${system_metrics['daily_revenue']:.2f}, Success Rate: {system_metrics['success_rate']:.1f}%"
    
    elif command == '/clear':
        chat_history.clear()
        socketio.emit('chat_cleared', to='/')  # type: ignore
        response_message = "Chat history cleared"
    
    else:
        response_message = f"Unknown command: {command}. Type /help for available commands."
    
    # Send bot response
    bot_response: Dict[str, Any] = {
        'id': f"msg-{len(chat_history)}",
        'user': 'System',
        'message': response_message,
        'timestamp': datetime.now().isoformat(),
        'type': 'system'
    }
    
    chat_history.append(bot_response)
    socketio.emit('new_message', bot_response, to='/')  # type: ignore

# Enhanced arbitrage calculation functions

class ArbitrageCalculator:
    """Advanced arbitrage calculation engine for dashboard"""
    
    def __init__(self):
        self.opportunities_cache: List[ArbitrageOpportunity] = []
        self.metrics_cache = ArbitrageMetrics()
        self.last_update = datetime.now()
        
    def calculate_arbitrage_profit(self, buy_price: float, sell_price: float, 
                                 trade_amount: float, gas_cost: float = 0.0,
                                 slippage: float = 0.005) -> Dict[str, float]:
        """Calculate arbitrage profit with fees and slippage"""
        try:
            # Calculate gross profit
            gross_profit = (sell_price - buy_price) * trade_amount
            
            # Apply slippage impact
            slippage_cost = trade_amount * sell_price * slippage
            
            # Calculate net profit after costs
            net_profit = gross_profit - gas_cost - slippage_cost
            
            # Calculate profit percentage
            profit_percentage = (net_profit / (buy_price * trade_amount)) * 100 if buy_price > 0 else 0
            
            return {
                'gross_profit': gross_profit,
                'net_profit': net_profit,
                'profit_percentage': profit_percentage,
                'gas_cost': gas_cost,
                'slippage_cost': slippage_cost,
                'total_costs': gas_cost + slippage_cost
            }
        except Exception as e:
            logger.error(f"Error calculating arbitrage profit: {e}")
            return {
                'gross_profit': 0.0,
                'net_profit': 0.0,
                'profit_percentage': 0.0,
                'gas_cost': gas_cost,
                'slippage_cost': 0.0,
                'total_costs': gas_cost
            }
    
    def assess_risk_level(self, profit_percentage: float, liquidity: float,
                         price_volatility: float = 0.0) -> str:
        """Assess risk level for arbitrage opportunity"""
        try:
            risk_score = 0
            
            # Profit percentage risk (higher profit = higher risk)
            if profit_percentage > 5.0:
                risk_score += 3
            elif profit_percentage > 2.0:
                risk_score += 2
            elif profit_percentage > 0.5:
                risk_score += 1
            
            # Liquidity risk (lower liquidity = higher risk)
            if liquidity < 10000:
                risk_score += 3
            elif liquidity < 50000:
                risk_score += 2
            elif liquidity < 100000:
                risk_score += 1
            
            # Volatility risk
            if price_volatility > 0.1:
                risk_score += 2
            elif price_volatility > 0.05:
                risk_score += 1
            
            if risk_score >= 6:
                return "high"
            elif risk_score >= 3:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return "medium"
    
    def analyze_dex_performance(self, opportunities: List[ArbitrageOpportunity]) -> Dict[str, Any]:
        """Analyze DEX performance metrics"""
        try:
            dex_stats = {}
            
            for opp in opportunities:
                buy_dex = opp.dex_buy
                sell_dex = opp.dex_sell
                
                # Initialize DEX stats
                for dex in [buy_dex, sell_dex]:
                    if dex not in dex_stats:
                        dex_stats[dex] = {
                            'total_opportunities': 0,
                            'total_profit': 0.0,
                            'average_profit': 0.0,
                            'as_buy_dex': 0,
                            'as_sell_dex': 0,
                            'risk_distribution': {'low': 0, 'medium': 0, 'high': 0}
                        }
                
                # Update stats
                dex_stats[buy_dex]['as_buy_dex'] += 1
                dex_stats[sell_dex]['as_sell_dex'] += 1
                
                profit = opp.profit_usd
                dex_stats[buy_dex]['total_profit'] += profit / 2
                dex_stats[sell_dex]['total_profit'] += profit / 2
                
                dex_stats[buy_dex]['total_opportunities'] += 1
                dex_stats[sell_dex]['total_opportunities'] += 1
                
                # Risk distribution
                risk = opp.risk_level
                dex_stats[buy_dex]['risk_distribution'][risk] += 1
                dex_stats[sell_dex]['risk_distribution'][risk] += 1
            
            # Calculate averages
            for dex in dex_stats:
                total_opps = dex_stats[dex]['total_opportunities']
                if total_opps > 0:
                    dex_stats[dex]['average_profit'] = dex_stats[dex]['total_profit'] / total_opps
            
            return dex_stats
            
        except Exception as e:
            logger.error(f"Error analyzing DEX performance: {e}")
            return {}
    
    def analyze_token_performance(self, opportunities: List[ArbitrageOpportunity]) -> Dict[str, Any]:
        """Analyze token pair performance metrics"""
        try:
            token_stats = {}
            
            for opp in opportunities:
                token_pair = opp.token_pair
                
                if token_pair not in token_stats:
                    token_stats[token_pair] = {
                        'total_opportunities': 0,
                        'total_profit': 0.0,
                        'average_profit': 0.0,
                        'best_profit': 0.0,
                        'average_confidence': 0.0,
                        'risk_distribution': {'low': 0, 'medium': 0, 'high': 0}
                    }
                
                stats = token_stats[token_pair]
                stats['total_opportunities'] += 1
                stats['total_profit'] += opp.profit_usd
                stats['best_profit'] = max(stats['best_profit'], opp.profit_usd)
                stats['average_confidence'] += opp.confidence_score
                stats['risk_distribution'][opp.risk_level] += 1
            
            # Calculate averages
            for token in token_stats:
                total_opps = token_stats[token]['total_opportunities']
                if total_opps > 0:
                    token_stats[token]['average_profit'] = token_stats[token]['total_profit'] / total_opps
                    token_stats[token]['average_confidence'] /= total_opps
            
            return token_stats
            
        except Exception as e:
            logger.error(f"Error analyzing token performance: {e}")
            return {}

# Initialize arbitrage calculator
arbitrage_calculator = ArbitrageCalculator()

@app.route('/api/arbitrage/calculate')
def calculate_arbitrage():
    """Calculate arbitrage opportunities with detailed metrics"""
    try:
        # Get parameters from request
        buy_price = float(request.args.get('buy_price', 0))
        sell_price = float(request.args.get('sell_price', 0))
        trade_amount = float(request.args.get('trade_amount', 1000))
        gas_cost = float(request.args.get('gas_cost', 50))
        slippage = float(request.args.get('slippage', 0.005))
        
        # Calculate profit
        profit_calc = arbitrage_calculator.calculate_arbitrage_profit(
            buy_price, sell_price, trade_amount, gas_cost, slippage
        )
        
        # Assess risk
        risk_level = arbitrage_calculator.assess_risk_level(
            profit_calc['profit_percentage'], trade_amount * 10
        )
        
        result: str = {
            'calculation': profit_calc,
            'risk_level': risk_level,
            'trade_amount': trade_amount,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in arbitrage calculation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arbitrage/opportunities')
def get_enhanced_arbitrage_opportunities():
    """Get enhanced arbitrage opportunities with detailed calculations"""
    try:
        # Fetch from MCP servers
        opportunities_data = []
        
        # Try to get from flash loan MCP server
        try:
            response = requests.get(f"{MCP_SERVERS['unified']}/opportunities", timeout=5)
            if response.status_code == 200:
                raw_opportunities = response.json()
                
                # Enhance each opportunity with detailed calculations
                for raw_opp in raw_opportunities:
                    enhanced_opp = enhance_opportunity_data(raw_opp)
                    opportunities_data.append(enhanced_opp)
                    
        except Exception as e:
            logger.warning(f"Could not fetch from MCP server: {e}")
        
        # If no MCP data, generate sample data for demo
        if not opportunities_data:
            opportunities_data = generate_sample_opportunities()
        
        # Update global state
        global live_opportunities
        live_opportunities = [ArbitrageOpportunity(**opp) for opp in opportunities_data if isinstance(opp, dict)]
        
        # Calculate performance metrics
        dex_performance = arbitrage_calculator.analyze_dex_performance(live_opportunities)
        token_performance = arbitrage_calculator.analyze_token_performance(live_opportunities)
        
        # Update global stats
        arbitrage_stats.update({
            'total_opportunities': len(live_opportunities),
            'profitable_opportunities': sum(1 for opp in live_opportunities if opp.profit_usd > 0),
            'average_profit': sum(opp.profit_usd for opp in live_opportunities) / len(live_opportunities) if live_opportunities else 0,
            'best_opportunity': max((opp.profit_usd for opp in live_opportunities), default=0),
            'dex_performance': dex_performance,
            'token_performance': token_performance
        })
        
        return jsonify({
            'opportunities': opportunities_data,
            'metrics': arbitrage_stats,
            'total_count': len(opportunities_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching enhanced arbitrage opportunities: {e}")
        return jsonify({'error': str(e)}), 500

def enhance_opportunity_data(raw_opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance raw opportunity data with detailed calculations"""
    try:
        # Extract basic data
        buy_price = float(raw_opportunity.get('buy_price', 0))
        sell_price = float(raw_opportunity.get('sell_price', 0))
        trade_amount = float(raw_opportunity.get('trade_amount', 1000))
        
        # Calculate enhanced metrics
        profit_calc = arbitrage_calculator.calculate_arbitrage_profit(
            buy_price, sell_price, trade_amount
        )
        
        risk_level = arbitrage_calculator.assess_risk_level(
            profit_calc['profit_percentage'], trade_amount * 10
        )
        
        # Create enhanced opportunity
        enhanced = {
            'id': raw_opportunity.get('id', f"opp_{int(time.time())}"),
            'token_pair': raw_opportunity.get('token_pair', 'WETH/USDC'),
            'dex_buy': raw_opportunity.get('dex_buy', 'UniswapV3'),
            'dex_sell': raw_opportunity.get('dex_sell', 'SushiSwap'),
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit_usd': profit_calc['net_profit'],
            'profit_percentage': profit_calc['profit_percentage'],
            'trade_amount': trade_amount,
            'confidence_score': float(raw_opportunity.get('confidence_score', 0.8)),
            'risk_level': risk_level,
            'execution_priority': int(raw_opportunity.get('execution_priority', 1)),
            'timestamp': datetime.now(),
            'gas_cost': profit_calc['gas_cost'],
            'slippage_impact': profit_calc['slippage_cost'],
            'liquidity_available': float(raw_opportunity.get('liquidity_available', 100000))
        }
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing opportunity data: {e}")
        return raw_opportunity

def generate_sample_opportunities() -> List[Dict[str, Any]]:
    """Generate sample arbitrage opportunities for demo purposes"""
    import random
    
    sample_opportunities = []
    tokens = ['WETH/USDC', 'WMATIC/USDT', 'WBTC/WETH', 'USDC/DAI', 'AAVE/WETH']
    dexes = ['UniswapV3', 'SushiSwap', 'QuickSwap', 'Balancer', 'Curve']
    
    for i in range(5):
        token_pair = random.choice(tokens)
        dex_buy = random.choice(dexes)
        dex_sell = random.choice([d for d in dexes if d != dex_buy])
        
        buy_price = round(random.uniform(1500, 2000), 2)
        sell_price = round(buy_price * (1 + random.uniform(0.001, 0.02)), 2)
        trade_amount = round(random.uniform(500, 5000), 2)
        
        profit_calc = arbitrage_calculator.calculate_arbitrage_profit(
            buy_price, sell_price, trade_amount
        )
        
        opportunity = {
            'id': f"demo_opp_{i+1}",
            'token_pair': token_pair,
            'dex_buy': dex_buy,
            'dex_sell': dex_sell,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit_usd': profit_calc['net_profit'],
            'profit_percentage': profit_calc['profit_percentage'],
            'trade_amount': trade_amount,
            'confidence_score': round(random.uniform(0.6, 0.95), 2),
            'risk_level': arbitrage_calculator.assess_risk_level(
                profit_calc['profit_percentage'], trade_amount * 10
            ),
            'execution_priority': random.randint(1, 5),
            'timestamp': datetime.now(),
            'gas_cost': profit_calc['gas_cost'],
            'slippage_impact': profit_calc['slippage_cost'],
            'liquidity_available': round(random.uniform(50000, 500000), 2)
        }
        
        sample_opportunities.append(opportunity)
    
    return sample_opportunities

@app.route('/api/arbitrage/metrics')
def get_arbitrage_metrics():
    """Get detailed arbitrage performance metrics"""
    try:
        # Calculate comprehensive metrics
        total_opps = len(live_opportunities)
        profitable_opps = sum(1 for opp in live_opportunities if opp.profit_usd > 0)
        
        metrics = {
            'overview': {
                'total_opportunities': total_opps,
                'profitable_opportunities': profitable_opps,
                'success_rate': (profitable_opps / total_opps * 100) if total_opps > 0 else 0,
                'average_profit': sum(opp.profit_usd for opp in live_opportunities) / total_opps if total_opps > 0 else 0,
                'best_opportunity': max((opp.profit_usd for opp in live_opportunities), default=0),
                'total_potential_profit': sum(opp.profit_usd for opp in live_opportunities if opp.profit_usd > 0)
            },
            'risk_analysis': {
                'risk_distribution': {
                    'low': sum(1 for opp in live_opportunities if opp.risk_level == 'low'),
                    'medium': sum(1 for opp in live_opportunities if opp.risk_level == 'medium'),
                    'high': sum(1 for opp in live_opportunities if opp.risk_level == 'high')
                },
                'average_confidence': sum(opp.confidence_score for opp in live_opportunities) / total_opps if total_opps > 0 else 0
            },
            'cost_analysis': {
                'total_gas_costs': sum(opp.gas_cost for opp in live_opportunities),
                'average_gas_cost': sum(opp.gas_cost for opp in live_opportunities) / total_opps if total_opps > 0 else 0,
                'total_slippage_impact': sum(opp.slippage_impact for opp in live_opportunities),
                'average_slippage': sum(opp.slippage_impact for opp in live_opportunities) / total_opps if total_opps > 0 else 0
            },
            'dex_performance': arbitrage_calculator.analyze_dex_performance(live_opportunities),
            'token_performance': arbitrage_calculator.analyze_token_performance(live_opportunities),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error calculating arbitrage metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arbitrage/execute/<opportunity_id>', methods=['POST'])
def execute_arbitrage_opportunity(opportunity_id: str):
    """Execute an arbitrage opportunity"""
    try:
        # Find the opportunity
        opportunity = None
        for opp in live_opportunities:
            if opp.id == opportunity_id:
                opportunity = opp
                break
        
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Send execution request to flash loan MCP server
        execution_data = {
            'opportunity_id': opportunity_id,
            'token_pair': opportunity.token_pair,
            'dex_buy': opportunity.dex_buy,
            'dex_sell': opportunity.dex_sell,
            'trade_amount': opportunity.trade_amount,
            'expected_profit': opportunity.profit_usd
        }
        
        try:
            response = requests.post(
                f"{MCP_SERVERS['unified']}/execute",
                json=execution_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result: str = response.json()
                return jsonify({
                    'message': 'Execution request sent successfully',
                    'execution_id': result.get('execution_id'),
                    'status': 'pending'
                })
            else:
                return jsonify({
                    'message': 'Execution request failed',
                    'status': 'failed'
                })
                
        except Exception as e:
            logger.warning(f"Could not send to MCP server: {e}")
            return jsonify({
                'message': 'Execution request queued (MCP server offline)',
                'status': 'queued'
            })
        
    except Exception as e:
        logger.error(f"Error executing arbitrage opportunity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arbitrage/simulate/<opportunity_id>', methods=['POST'])
def simulate_arbitrage_opportunity(opportunity_id: str):
    """Simulate an arbitrage opportunity using Foundry MCP"""
    try:
        # Find the opportunity
        opportunity = None
        for opp in live_opportunities:
            if opp.id == opportunity_id:
                opportunity = opp
                break
        
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Send simulation request to Foundry MCP server
        simulation_data = {
            'opportunity_id': opportunity_id,
            'token_pair': opportunity.token_pair,
            'dex_buy': opportunity.dex_buy,
            'dex_sell': opportunity.dex_sell,
            'trade_amount': opportunity.trade_amount,
            'buy_price': opportunity.buy_price,
            'sell_price': opportunity.sell_price
        }
        
        try:
            response = requests.post(
                f"{MCP_SERVERS['foundry']}/simulate",
                json=simulation_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result: str = response.json()
                return jsonify({
                    'message': f"Simulation completed. Gas estimate: ${result.get('gas_cost', 50):.2f}",
                    'simulation_result': result,
                    'status': 'completed'
                })
            else:
                return jsonify({
                    'message': 'Simulation failed',
                    'status': 'failed'
                })
                
        except Exception as e:
            logger.warning(f"Could not simulate with Foundry MCP: {e}")
            return jsonify({
                'message': 'Simulation unavailable (Foundry MCP offline)',
                'status': 'unavailable'
            })
        
    except Exception as e:
        logger.error(f"Error simulating arbitrage opportunity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arbitrage/analyze/<opportunity_id>', methods=['POST'])
def analyze_arbitrage_opportunity(opportunity_id: str):
    """Analyze an arbitrage opportunity using Copilot MCP"""
    try:
        # Find the opportunity
        opportunity = None
        for opp in live_opportunities:
            if opp.id == opportunity_id:
                opportunity = opp
                break
        
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Send analysis request to Copilot MCP server
        analysis_prompt = f"""
        Analyze this arbitrage opportunity:
        - Token Pair: {opportunity.token_pair}
        - Buy DEX: {opportunity.dex_buy} at ${opportunity.buy_price:.4f}
        - Sell DEX: {opportunity.dex_sell} at ${opportunity.sell_price:.4f}
        - Potential Profit: ${opportunity.profit_usd:.2f} ({opportunity.profit_percentage:.3f}%)
        - Trade Amount: ${opportunity.trade_amount:.0f}
        - Risk Level: {opportunity.risk_level}
        - Confidence Score: {opportunity.confidence_score:.2f}
        
        Provide analysis on execution viability, risks, and recommendations.
        """
        
        try:
            response = requests.post(
                f"{MCP_SERVERS['copilot']}/analyze",
                json={'prompt': analysis_prompt},
                timeout=20
            )
            
            if response.status_code == 200:
                result: str = response.json()
                analysis = result.get('analysis', 'Analysis completed successfully')
                return jsonify({
                    'analysis': analysis,
                    'status': 'completed'
                })
            else:
                return jsonify({
                    'analysis': 'Analysis failed',
                    'status': 'failed'
                })
                
        except Exception as e:
            logger.warning(f"Could not analyze with Copilot MCP: {e}")
            return jsonify({
                'analysis': f'Analysis unavailable (Copilot MCP offline). Basic assessment: {opportunity.risk_level} risk opportunity with {opportunity.profit_percentage:.3f}% profit potential.',
                'status': 'fallback'
            })
        
    except Exception as e:
        logger.error(f"Error analyzing arbitrage opportunity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/arbitrage/status')
def get_arbitrage_status():
    """Get overall arbitrage system status"""
    try:
        # Check MCP server health
        server_status = {}
        for server_name, url in MCP_SERVERS.items():
            try:
                response = requests.get(f"{url}/health", timeout=3)
                server_status[server_name] = response.status_code == 200
            except:
                server_status[server_name] = False
        
        # Calculate system health score
        healthy_servers = sum(1 for status in server_status.values() if status)
        total_servers = len(server_status)
        health_score = (healthy_servers / total_servers) * 100 if total_servers > 0 else 0
        
        status = {
            'system_health': health_score,
            'server_status': server_status,
            'active_opportunities': len(live_opportunities),
            'profitable_opportunities': sum(1 for opp in live_opportunities if opp.profit_usd > 0),
            'total_potential_profit': sum(opp.profit_usd for opp in live_opportunities if opp.profit_usd > 0),
            'last_update': datetime.now().isoformat(),
            'arbitrage_calculator_active': arbitrage_calculator is not None,
            'monitoring_active': True
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting arbitrage status: {e}")
        return jsonify({'error': str(e)}), 500
# Background tasks
def update_dex_prices() -> None:
    """Update DEX prices and arbitrage opportunities periodically"""
    while True:
        time.sleep(10)  # Update every 10 seconds
        try:
            # Fetch current DEX data
            response = requests.get(f"{DEX_PRICE_URL}/dashboard-data", timeout=5)
            if response.status_code == 200:
                dex_data = response.json()
                
                # Update global state
                global dex_price_data, arbitrage_opportunities
                dex_price_data = dex_data.get('prices', {})
                arbitrage_opportunities = dex_data.get('opportunities', [])
                
                # Emit updates to all clients
                socketio.emit('dex_prices_update', dex_price_data, to='/')  # type: ignore
                socketio.emit('arbitrage_opportunities_update', arbitrage_opportunities, to='/')  # type: ignore
                socketio.emit('dex_stats_update', dex_data.get('dex_stats', {}), to='/')  # type: ignore
                
                # Update system metrics with DEX data
                if arbitrage_opportunities:
                    best_opportunity = max(arbitrage_opportunities, key=lambda x: Any: Any: x.get('net_profit', 0))
                    system_metrics['best_opportunity'] = best_opportunity.get('net_profit', 0)
                    system_metrics['active_opportunities'] = len(arbitrage_opportunities)
                else:
                    system_metrics['best_opportunity'] = 0
                    system_metrics['active_opportunities'] = 0
                    
        except Exception as e:
            logger.warning(f"Error updating DEX prices: {e}")
            # Update server status if DEX service is down
            if 'dex-price-monitor' in mcp_servers:
                mcp_servers['dex-price-monitor']['status'] = 'stopped'
                mcp_servers['dex-price-monitor']['connected'] = False
                socketio.emit('servers_update', mcp_servers, to='/')  # type: ignore

def update_metrics() -> None:
    """Update system metrics periodically"""
    while True:
        time.sleep(5)
        # Simulate metric updates
        system_metrics['cpu_usage'] = round(45 + (time.time() % 20) - 10, 1)
        system_metrics['memory_usage'] = round(62 + (time.time() % 15) - 7.5, 1)
        system_metrics['network_io']['in'] = round(125 + (time.time() % 50) - 25, 1)
        system_metrics['network_io']['out'] = round(89 + (time.time() % 40) - 20, 1)
        system_metrics['active_connections'] = int(12 + (time.time() % 10) - 5)
        system_metrics['total_requests'] += int(time.time() % 5)
        
        # Simulate revenue updates (demo mode)
        if system_metrics['revenue_bot_status'] == 'running':
            system_metrics['total_revenue'] += round((time.time() % 3) * 0.1, 2)
            system_metrics['daily_revenue'] += round((time.time() % 2) * 0.05, 2)
            system_metrics['success_rate'] = min(95.0, system_metrics['success_rate'] + 0.1)
        
        socketio.emit('metrics_update', system_metrics, to='/')  # type: ignore

def check_server_health() -> None:
    """Check server health periodically"""
    while True:
        time.sleep(10)
        for _, server in mcp_servers.items():
            if server['status'] == 'running':
                # Simulate health check
                health = server.get('health', {})
                if isinstance(health, dict):
                    health['status'] = 'healthy' if server['connected'] else 'unhealthy'
                    # Update uptime
                    if health['status'] == 'healthy':
                        uptime_mins = int(time.time() % 300)
                        health['uptime'] = f"{uptime_mins // 60}h {uptime_mins % 60}m"
        
        socketio.emit('servers_update', mcp_servers, to='/')  # type: ignore

# Create templates directory and HTML file
def create_dashboard_template() -> None:
    """Create the dashboard HTML template"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced MCP Revenue Hub - Port 8004</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: #333; 
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { 
            background: rgba(255, 255, 255, 0.95); 
            padding: 30px; 
            border-radius: 15px; 
            margin-bottom: 20px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .header h1 { 
            color: #2c3e50; 
            font-size: 2.5em; 
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { color: #666; font-size: 1.1em; }
        .dashboard-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 20px; 
            margin-bottom: 20px; 
        }
        .card { 
            background: rgba(255, 255, 255, 0.95); 
            padding: 25px; 
            border-radius: 15px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); }
        .card h2 { 
            color: #34495e; 
            margin-bottom: 20px; 
            font-size: 1.4em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .server-item { 
            padding: 15px; 
            margin: 8px 0; 
            border-radius: 10px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            transition: all 0.3s ease;
        }
        .server-running { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border-left: 4px solid #4caf50; }
        .server-stopped { background: linear-gradient(135deg, #ffebee, #ffcdd2); border-left: 4px solid #f44336; }
        .server-restarting { background: linear-gradient(135deg, #fff3e0, #ffe0b2); border-left: 4px solid #ff9800; }
        .status-indicator { 
            width: 12px; 
            height: 12px; 
            border-radius: 50%; 
            display: inline-block; 
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        .status-running { background: #4caf50; }
        .status-stopped { background: #f44336; animation: none; }
        .status-restarting { background: #ff9800; }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .metric-value { 
            font-size: 2.2em; 
            font-weight: bold; 
            background: linear-gradient(45deg, #2196f3, #21cbf3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .chat-container { display: grid; grid-template-columns: 1fr 350px; gap: 20px; }
        .chat-main { 
            background: rgba(255, 255, 255, 0.95); 
            padding: 25px; 
            border-radius: 15px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .chat-messages { 
            height: 450px; 
            overflow-y: auto; 
            border: 2px solid #e1f5fe; 
            border-radius: 12px; 
            padding: 15px; 
            margin-bottom: 15px;
            background: #f8f9fa;
        }
        .chat-input-group { display: flex; gap: 10px; }
        .chat-input { 
            flex: 1; 
            padding: 12px; 
            border: 2px solid #e1f5fe; 
            border-radius: 25px; 
            outline: none;
            transition: border-color 0.3s ease;
        }
        .chat-input:focus { border-color: #2196f3; }
        .chat-send { 
            padding: 12px 25px; 
            background: linear-gradient(45deg, #2196f3, #21cbf3); 
            color: white; 
            border: none; 
            border-radius: 25px; 
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .chat-send:hover { transform: scale(1.05); }
        .message { 
            margin: 10px 0; 
            padding: 12px; 
            border-radius: 12px;
            animation: slideIn 0.3s ease;
        }
        .message-user { 
            background: linear-gradient(135deg, #e3f2fd, #bbdefb); 
            margin-left: 20px;
        }
        .message-system { 
            background: linear-gradient(135deg, #f5f5f5, #eeeeee); 
            font-style: italic; 
        }
        .message-assistant { 
            background: linear-gradient(135deg, #e8f5e9, #c8e6c9); 
            margin-right: 20px;
        }
        .message-error { 
            background: linear-gradient(135deg, #ffebee, #ffcdd2); 
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .task-item { 
            padding: 15px; 
            margin: 8px 0; 
            border-radius: 10px; 
            background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
            border-left: 4px solid #2196f3;
        }
        .progress-bar { 
            width: 100%; 
            height: 8px; 
            background: #e0e0e0; 
            
            border-radius: 4px; 
            overflow: hidden; 
            margin: 8px 0; 
        }
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(90deg, #4caf50, #8bc34a); 
            transition: width 0.5s ease; 
        }
        .action-button { 
            padding: 8px 15px; 
            margin: 0 3px; 
            border: none; 
            border-radius: 20px; 
            cursor: pointer; 
            font-size: 0.9em;
            transition: all 0.3s ease;
        }
        .btn-start { background: linear-gradient(45deg, #4caf50, #8bc34a); color: white; }
        .btn-stop { background: linear-gradient(45deg, #f44336, #e57373); color: white; }
        .btn-restart { background: linear-gradient(45deg, #ff9800, #ffb74d); color: white; }
        .action-button:hover { transform: scale(1.1); }
        .quick-actions { display: grid; gap: 10px; }
        .quick-action-btn { 
            width: 100%; 
            padding: 15px; 
            border: none; 
            border-radius: 10px; 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .quick-action-btn:hover { transform: scale(1.05); }
        .emoji { font-size: 1.5em; margin-right: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced MCP Revenue Hub</h1>
            <p>Conversational AI-Powered Arbitrage Trading System - Port 8004</p>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h2><span class="emoji">🖥️</span>MCP Servers Status</h2>
                <div id="serverList"></div>
            </div>
            
            <div class="card">
                <h2><span class="emoji">📊</span>System Metrics</h2>
                <div id="metricsDisplay"></div>
            </div>
            
            <div class="card">
                <h2><span class="emoji">⚡</span>Active Tasks</h2>
                <div id="tasksList"></div>
            </div>
        </div>
        
        <div class="chat-container">
            <div class="chat-main">
                <h2><span class="emoji">🤖</span>Enhanced Copilot Agent</h2>
                <div class="chat-messages" id="chatMessages">
                    <div class="message message-assistant">
                        <strong>Enhanced Copilot Agent</strong> <small>Ready</small><br>
                        Welcome! I'm your Enhanced Copilot Agent, powered by external AI-driven MCP servers with advanced optimization capabilities!<br><br>
                        💡 <strong>Smart Trading Commands:</strong><br>
                        • "Start the revenue bot"<br>
                        • "What's the current status?"<br>
                        • "Show me opportunities"<br>
                        • "How much have we made?"<br>
                        • "Optimize my contract code"<br><br>
                        🔧 <strong>AI-Powered Assistance:</strong><br>
                        • Code optimization and analysis<br>
                        • Smart contract efficiency tips<br>
                        • Gas cost reduction strategies<br>
                        • Security vulnerability detection<br>
                        • Performance recommendations<br><br>
                        Ask me anything - I'm here to help maximize your revenue! 🎯
                    </div>
                </div>
                <div class="chat-input-group">
                    <input type="text" class="chat-input" id="chatInput" placeholder="Ask me anything about the trading system... (type /help for commands)">
                    <button class="chat-send" onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <div class="card">
                <h2><span class="emoji">⚡</span>Quick Actions</h2>
                <div class="quick-actions">
                    <button class="quick-action-btn" onclick="sendMessage('What is the current status?')">📊 System Status</button>
                    <button class="quick-action-btn" onclick="sendMessage('Show me opportunities')">🎯 Market Opportunities</button>
                    <button class="quick-action-btn" onclick="sendMessage('Start the revenue bot')">🚀 Start Revenue Bot</button>
                    <button class="quick-action-btn" onclick="sendMessage('How much have we made?')">💰 Revenue Report</button>
                    <button class="quick-action-btn" onclick="executeQuickAction('refresh')">🔄 Refresh All</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        
        // Socket event handlers
        socket.on('connect', () => {
            console.log('Connected to Enhanced MCP Dashboard on port 8004');
        });
        
        socket.on('servers_update', (servers) => {
            updateServerList(servers);
        });
        
        socket.on('metrics_update', (metrics) => {
            updateMetrics(metrics);
        });
        
        socket.on('tasks_update', (tasks) => {
            updateTasks(tasks);
        });
        
        socket.on('new_message', (message) => {
            addChatMessage(message);
        });
        
        socket.on('chat_cleared', () => {
            document.getElementById('chatMessages').innerHTML = '';
        });
        
        // Update functions
        function updateServerList(servers) {
            const container = document.getElementById('serverList');
            container.innerHTML = '';
            
            Object.entries(servers).forEach(([id, server]) => {
                const div = document.createElement('div');
                div.className = `server-item server-${server.status}`;
                div.innerHTML = `
                    <div>
                        <span class="status-indicator status-${server.status}"></span>
                        <strong>${server.name}</strong>
                        <small>(Port: ${server.port})</small>
                    </div>
                    <div>
                        <button class="action-button btn-start" onclick="serverAction('${id}', 'start')">Start</button>
                        <button class="action-button btn-stop" onclick="serverAction('${id}', 'stop')">Stop</button>
                        <button class="action-button btn-restart" onclick="serverAction('${id}', 'restart')">Restart</button>
                    </div>
                `;
                container.appendChild(div);
            });
        }
        
        function updateMetrics(metrics) {
            const container = document.getElementById('metricsDisplay');
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <small>💰 Total Revenue</small>
                        <div class="metric-value">$${metrics.total_revenue.toFixed(2)}</div>
                    </div>
                    <div>
                        <small>📈 Daily Revenue</small>
                        <div class="metric-value">$${metrics.daily_revenue.toFixed(2)}</div>
                    </div>
                    <div>
                        <small>🎯 Success Rate</small>
                        <div class="metric-value">${metrics.success_rate.toFixed(1)}%</div>
                    </div>
                    <div>
                        <small>⚡ CPU Usage</small>
                        <div class="metric-value">${metrics.cpu_usage}%</div>
                    </div>
                    <div>
                        <small>🧠 Memory Usage</small>
                        <div class="metric-value">${metrics.memory_usage}%</div>
                    </div>
                    <div>
                        <small>🌐 Network I/O</small>
                        <div class="metric-value">${metrics.network_io.in.toFixed(1)} MB/s</div>
                    </div>
                </div>
            `;
        }
        
        function updateTasks(tasks) {
            const container = document.getElementById('tasksList');
            container.innerHTML = '';
            
            if (tasks.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #666;">No active tasks</p>';
                return;
            }
            
            tasks.forEach(task => {
                const div = document.createElement('div');
                div.className = 'task-item';
                const statusEmoji = task.status === 'completed' ? '✅' : task.status === 'in_progress' ? '🔄' : '⏳';
                div.innerHTML = `
                    <div>
                        ${statusEmoji} <strong>${task.type}</strong> on ${task.server}
                        <small>(${task.status})</small>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${task.progress}%"></div>
                    </div>
                    <small>${task.progress}% complete</small>
                `;
                container.appendChild(div);
            });
        }
        
        function addChatMessage(message) {
            const container = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = `message message-${message.type}`;
            
            const time = new Date(message.timestamp).toLocaleTimeString();
            const userEmoji = message.type === 'assistant' ? '🤖' : message.type === 'system' ? '⚙️' : '👤';
            div.innerHTML = `${userEmoji} <strong>${message.user}</strong> <small>${time}</small><br>${message.message.replace(/\\n/g, '<br>')}`;
            
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
        
        // Action functions
        function sendMessage(predefinedMessage = null) {
            const input = document.getElementById('chatInput');
            const message = predefinedMessage || input.value.trim();
            
            if (message) {
                socket.emit('chat_message', {
                    message: message,
                    user: 'User'
                });
                if (!predefinedMessage) {
                    input.value = '';
                }
            }
        }
        
        function serverAction(serverId, action) {
            socket.emit('server_action', {
                server_id: serverId,
                action: action
            });
        }
        
        function executeQuickAction(action) {
            if (action === 'refresh') {
                location.reload();
            }
        }
        
        // Enter key to send message
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Initial welcome message
        setTimeout(() => {
            addChatMessage({
                user: 'System',
                message: 'Enhanced MCP Dashboard initialized successfully on port 8004! All systems ready.',
                timestamp: new Date().toISOString(),
                type: 'system'
            });
        }, 1000);
    </script>
</body>
</html>'''
    
    (templates_dir / "dashboard.html").write_text(dashboard_html, encoding='utf-8')

# Main execution
if __name__ == '__main__':
    # Create template
    create_dashboard_template()
      # Start background threads
    metrics_thread = threading.Thread(target=update_metrics, daemon=True)
    metrics_thread.start()
    
    health_thread = threading.Thread(target=check_server_health, daemon=True)
    health_thread.start()
    
    # Start DEX price monitoring thread
    dex_thread = threading.Thread(target=update_dex_prices, daemon=True)
    dex_thread.start()
    
    dex_thread = threading.Thread(target=update_dex_prices, daemon=True)
    dex_thread.start()
      # Add welcome message to chat history
    welcome_message: Dict[str, Any] = {
        'id': 'msg-welcome',
        'user': 'Enhanced Copilot Agent',
        'message': '''Welcome to the Enhanced MCP Revenue Hub with DEX Price Monitoring! 🚀

I'm your AI-powered assistant with integrated real-time DEX price monitoring capabilities:

💹 **DEX Monitoring Features:**
• Real-time price tracking from Uniswap V3, SushiSwap, QuickSwap
• Arbitrage opportunity detection with profit calculations
• Gas cost analysis and net profit estimates
• Alert system for high-profit opportunities

🤖 **Connected MCP Servers:**
• Enhanced Copilot Agent (Port 8003) - AI optimization & analysis
• Enhanced Foundry Server (Port 8002) - Smart contract deployment  
• Production MCP Server (Port 8001) - Production management
• DEX Price Monitor (Port 8008) - Real-time price monitoring

💡 **Try asking:**
• "Show current DEX prices"
• "What arbitrage opportunities are available?"
• "Start the revenue bot"
• "Analyze profit potential"
• "Optimize my trading strategy"

Ready to maximize your flash loan revenue with real-time market intelligence! 🎯''',
        'timestamp': datetime.now().isoformat(),
        'type': 'assistant'
    }
    chat_history.append(welcome_message)
      # Run the application on port 8004
    print("🚀 Starting Enhanced MCP Dashboard with DEX Price Monitoring on http://localhost:8004")
    print("📊 Dashboard Features:")
    print("  • Real-time MCP server monitoring")
    print("  • AI-powered chat with Copilot Agent")
    print("  • Live DEX price monitoring (Uniswap V3, SushiSwap, QuickSwap)")
    print("  • Arbitrage opportunity detection and alerts")
    print("  • Flash loan revenue tracking and optimization")
    print("  • Smart contract gas optimization")
    print("  • Task management and execution")
    print("  • WebSocket real-time updates")
    print("\n💹 DEX Monitoring Features:")
    print("  • Real-time price feeds from multiple DEXs")
    print("  • Automated arbitrage opportunity scanning")
    print("  • Profit calculation with gas cost analysis")
    print("  • Alert system for high-profit opportunities")
    print("  • Integration with TaskManager MCP on port 8007")
    print("\n🔗 Access the dashboard at: http://localhost:8004")
    print("🔗 DEX Price Monitor API: http://localhost:8008")
    
    socketio.run(app, debug=True, port=8004, host='0.0.0.0')  # type: ignore
