"""
Flash Loan Arbitrage System - Web Dashboard
FastAPI backend with real-time monitoring and control interface
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our database models
from ..core.database import db_manager, db_ops, init_database, shutdown_database
from ..core.database import Trade, ArbitrageOpportunity, SystemMetric, MCPServerStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class TradeResponse(BaseModel):
    id: int
    token_pair: str
    buy_dex_name: str
    sell_dex_name: str
    trade_amount: Decimal
    actual_profit_usd: Optional[Decimal]
    net_profit_usd: Optional[Decimal]
    success: bool
    executed_at: datetime

class OpportunityResponse(BaseModel):
    id: int
    token_pair: str
    buy_dex_name: str
    sell_dex_name: str
    price_difference: Decimal
    estimated_profit_usd: Decimal
    trade_amount: Decimal
    status: str
    discovered_at: datetime

class SystemStats(BaseModel):
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_profit_usd: Decimal
    active_opportunities: int
    mcp_servers_running: int

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

# Global WebSocket manager
ws_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    await init_database()
    logger.info("Dashboard started successfully")
    yield
    # Shutdown
    await shutdown_database()
    logger.info("Dashboard shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Flash Loan Arbitrage Dashboard",
    description="Real-time monitoring and control interface for flash loan arbitrage system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics"""
    try:
        async with db_manager.get_session() as session:
            # Get trade statistics
            trade_result = await session.execute(
                """
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_trades,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_trades,
                    COALESCE(SUM(CASE WHEN success THEN net_profit_usd ELSE 0 END), 0) as total_profit_usd
                FROM trades 
                WHERE executed_at >= NOW() - INTERVAL '24 hours'
                """
            )
            trade_stats = trade_result.fetchone()
            
            # Get active opportunities count
            opp_result = await session.execute(
                """
                SELECT COUNT(*) as active_opportunities
                FROM arbitrage_opportunities 
                WHERE status = 'discovered' AND expires_at > NOW()
                """
            )
            opp_count = opp_result.fetchone()[0]
            
            # Get running MCP servers count
            mcp_result = await session.execute(
                """
                SELECT COUNT(*) as running_servers
                FROM mcp_server_status 
                WHERE status = 'running' AND last_heartbeat > NOW() - INTERVAL '5 minutes'
                """
            )
            mcp_count = mcp_result.fetchone()[0]
            
            return SystemStats(
                total_trades=trade_stats[0] or 0,
                successful_trades=trade_stats[1] or 0,
                failed_trades=trade_stats[2] or 0,
                total_profit_usd=trade_stats[3] or Decimal('0'),
                active_opportunities=opp_count or 0,
                mcp_servers_running=mcp_count or 0
            )
            
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system statistics")

@app.get("/api/trades", response_model=List[TradeResponse])
async def get_recent_trades(limit: int = 50):
    """Get recent trades"""
    try:
        trades = await db_ops.get_recent_trades(limit)
        return [
            TradeResponse(
                id=trade.id,
                token_pair=trade.token_pair,
                buy_dex_name="Unknown",  # TODO: Add DEX name lookup
                sell_dex_name="Unknown",
                trade_amount=trade.trade_amount,
                actual_profit_usd=trade.actual_profit_usd,
                net_profit_usd=trade.net_profit_usd,
                success=trade.success,
                executed_at=trade.executed_at
            )
            for trade in trades
        ]
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving trades")

@app.get("/api/opportunities", response_model=List[OpportunityResponse])
async def get_active_opportunities(limit: int = 50):
    """Get active arbitrage opportunities"""
    try:
        opportunities = await db_ops.get_active_opportunities(limit)
        return [
            OpportunityResponse(
                id=opp.id,
                token_pair=opp.token_pair,
                buy_dex_name="Unknown",  # TODO: Add DEX name lookup
                sell_dex_name="Unknown",
                price_difference=opp.price_difference,
                estimated_profit_usd=opp.estimated_profit_usd,
                trade_amount=opp.trade_amount,
                status=opp.status,
                discovered_at=opp.discovered_at
            )
            for opp in opportunities
        ]
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving opportunities")

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics for charts"""
    try:
        async with db_manager.get_session() as session:
            # Get profit over time (last 24 hours)
            profit_result = await session.execute(
                """
                SELECT 
                    DATE_TRUNC('hour', executed_at) as hour,
                    SUM(CASE WHEN success THEN net_profit_usd ELSE 0 END) as profit
                FROM trades 
                WHERE executed_at >= NOW() - INTERVAL '24 hours'
                GROUP BY DATE_TRUNC('hour', executed_at)
                ORDER BY hour
                """
            )
            profit_data = [{"time": row[0].isoformat(), "profit": float(row[1] or 0)} for row in profit_result]
            
            # Get trade success rate over time
            success_result = await session.execute(
                """
                SELECT 
                    DATE_TRUNC('hour', executed_at) as hour,
                    COUNT(*) as total,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                FROM trades 
                WHERE executed_at >= NOW() - INTERVAL '24 hours'
                GROUP BY DATE_TRUNC('hour', executed_at)
                ORDER BY hour
                """
            )
            success_data = [
                {
                    "time": row[0].isoformat(), 
                    "total": row[1], 
                    "successful": row[2],
                    "success_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0
                } 
                for row in success_result
            ]
            
            return {
                "profit_over_time": profit_data,
                "success_rate_over_time": success_data
            }
            
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Wait for message from client
            data = await websocket.receive_text()
            
            # Handle different message types
            message = json.loads(data)
            if message.get("type") == "ping":
                await ws_manager.send_personal_message({"type": "pong"}, websocket)
            elif message.get("type") == "subscribe":
                # Subscribe to specific data feeds
                await ws_manager.send_personal_message({"type": "subscribed", "feed": message.get("feed")}, websocket)
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

async def broadcast_trade_update(trade_data: dict):
    """Broadcast trade update to all connected clients"""
    await ws_manager.broadcast({
        "type": "trade_update",
        "data": trade_data
    })

async def broadcast_opportunity_update(opportunity_data: dict):
    """Broadcast opportunity update to all connected clients"""
    await ws_manager.broadcast({
        "type": "opportunity_update",
        "data": opportunity_data
    })

async def broadcast_system_stats():
    """Broadcast system statistics update"""
    try:
        # Get current stats
        stats = await get_system_stats()
        await ws_manager.broadcast({
            "type": "stats_update",
            "data": stats.dict()
        })
    except Exception as e:
        logger.error(f"Error broadcasting stats: {e}")

# Background task for periodic updates
async def periodic_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            await broadcast_system_stats()
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Start background task
@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(periodic_updates())

if __name__ == "__main__":
    uvicorn.run(
        "frontend.dashboard:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
