#!/usr/bin/env python3
"""
Enhanced MCP Price Feed Server - Compatible Version
Provides price data and arbitrage opportunities without additional dependencies
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced MCP Price Feed Server", version="1.0.0")

class PriceRequest(BaseModel):
    token_pairs: List[str]
    dexs: Optional[List[str]] = None

class ArbitrageRequest(BaseModel):
    token_pair: str
    min_profit_threshold: Optional[float] = 0.01

# Simulated price data with realistic price movements
PRICE_DATA = {
    "ETH/USDC": {
        "uniswap_v2": 2050.00,
        "sushiswap": 2052.00,
        "pancakeswap": 2048.50,
        "1inch": 2051.25
    },
    "WBTC/USDC": {
        "uniswap_v2": 43500.00,
        "sushiswap": 43450.00,
        "pancakeswap": 43520.00,
        "1inch": 43480.00
    },
    "USDC/DAI": {
        "uniswap_v2": 1.0001,
        "sushiswap": 0.9999,
        "pancakeswap": 1.0002,
        "1inch": 1.0000
    },
    "UNI/USDC": {
        "uniswap_v2": 7.25,
        "sushiswap": 7.28,
        "pancakeswap": 7.22,
        "1inch": 7.26
    }
}

# Supported tokens and DEXs
SUPPORTED_TOKENS = [
    "ETH", "WBTC", "USDC", "DAI", "UNI", "LINK", "AAVE", "COMP", "SUSHI", "WETH"
]

SUPPORTED_DEXS = [
    "uniswap_v2", "uniswap_v3", "sushiswap", "pancakeswap", "1inch", "curve"
]

def simulate_price_movement(base_price: float, volatility: float = 0.001) -> float:
    """Simulate realistic price movements"""
    change = random.uniform(-volatility, volatility)
    return base_price * (1 + change)

def update_prices():
    """Update prices with simulated market movements"""
    for token_pair in PRICE_DATA:
        for dex in PRICE_DATA[token_pair]:
            current_price = PRICE_DATA[token_pair][dex]
            # Higher volatility for smaller market cap tokens
            volatility = 0.002 if token_pair in ["UNI/USDC", "USDC/DAI"] else 0.001
            PRICE_DATA[token_pair][dex] = simulate_price_movement(current_price, volatility)

def find_arbitrage_opportunities(token_pair: str, min_profit_threshold: float = 0.01) -> List[Dict]:
    """Find arbitrage opportunities for a token pair"""
    if token_pair not in PRICE_DATA:
        return []
    
    prices = PRICE_DATA[token_pair]
    opportunities = []
    
    # Find price differences between DEXs
    dex_prices = list(prices.items())
    for i in range(len(dex_prices)):
        for j in range(i + 1, len(dex_prices)):
            dex1, price1 = dex_prices[i]
            dex2, price2 = dex_prices[j]
            
            if price1 > price2:
                profit_pct = (price1 - price2) / price2
                if profit_pct >= min_profit_threshold:
                    opportunities.append({
                        "token_pair": token_pair,
                        "buy_dex": dex2,
                        "sell_dex": dex1,
                        "buy_price": price2,
                        "sell_price": price1,
                        "profit_percentage": profit_pct * 100,
                        "estimated_profit_usd": (price1 - price2) * 10,  # Assuming 10 token trade
                        "timestamp": datetime.now().isoformat()
                    })
            elif price2 > price1:
                profit_pct = (price2 - price1) / price1
                if profit_pct >= min_profit_threshold:
                    opportunities.append({
                        "token_pair": token_pair,
                        "buy_dex": dex1,
                        "sell_dex": dex2,
                        "buy_price": price1,
                        "sell_price": price2,
                        "profit_percentage": profit_pct * 100,
                        "estimated_profit_usd": (price2 - price1) * 10,
                        "timestamp": datetime.now().isoformat()
                    })
    
    return opportunities

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/get_prices")
async def get_prices_get(token_pairs: str = None, dexs: str = None):
    """Get current prices for token pairs from specified DEXs (GET method)"""
    return await _get_prices_impl(token_pairs, dexs)

@app.post("/get_prices")
async def get_prices_post(request: Dict[str, Any]):
    """Get current prices for token pairs from specified DEXs (POST method)"""
    try:
        tokens = request.get('tokens', [])
        dexs = request.get('dexs', [])
        
        # Map tokens to available token pairs
        available_pairs = []
        token_mapping = {
            'ETH': 'ETH/USDC',
            'WETH': 'ETH/USDC',
            'WMATIC': 'ETH/USDC',  # Use ETH as proxy for WMATIC
            'WBTC': 'WBTC/USDC',
            'USDC': 'USDC/DAI',
            'DAI': 'USDC/DAI',
            'UNI': 'UNI/USDC'
        }
        
        for token in tokens:
            if token in token_mapping:
                pair = token_mapping[token]
                if pair not in available_pairs:
                    available_pairs.append(pair)
        
        # If no specific tokens requested, return all pairs
        if not available_pairs:
            available_pairs = list(PRICE_DATA.keys())
        
        token_pairs_str = ",".join(available_pairs)
        dexs_str = ",".join(dexs) if dexs else None
        
        result = await _get_prices_impl(token_pairs_str, dexs_str)
        logger.info(f"📊 Price data requested via POST: {len(result.get('prices', {}))} pairs for tokens {tokens}")
        return result
        
    except Exception as e:
        logger.error(f"Error in POST get_prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _get_prices_impl(token_pairs: str = None, dexs: str = None):
    """Implementation for getting prices (shared between GET and POST)"""
    try:
        # Update prices with market simulation
        update_prices()
        
        # Parse comma-separated parameters
        requested_pairs = token_pairs.split(",") if token_pairs else list(PRICE_DATA.keys())
        requested_dexs = dexs.split(",") if dexs else None
        
        result = {}
        for pair in requested_pairs:
            if pair in PRICE_DATA:
                if requested_dexs:
                    result[pair] = {dex: price for dex, price in PRICE_DATA[pair].items() 
                                  if dex in requested_dexs}
                else:
                    result[pair] = PRICE_DATA[pair].copy()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "prices": result,
            "market_status": "active"
        }
    
    except Exception as e:
        logger.error(f"Error getting prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/request")
async def mcp_request(request: Dict[str, Any]):
    """MCP protocol endpoint for handling requests"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "get_prices":
            token_pairs = params.get("token_pairs", list(PRICE_DATA.keys()))
            dexs = params.get("dexs")
            
            update_prices()
            
            result = {}
            for pair in token_pairs:
                if pair in PRICE_DATA:
                    if dexs:
                        result[pair] = {dex: price for dex, price in PRICE_DATA[pair].items() 
                                      if dex in dexs}
                    else:
                        result[pair] = PRICE_DATA[pair].copy()
            
            return {
                "id": request.get("id"),
                "result": {
                    "status": "success",
                    "prices": result,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        elif method == "get_arbitrage_opportunities":
            token_pair = params.get("token_pair")
            min_profit = params.get("min_profit_threshold", 0.01)
            
            if token_pair:
                opportunities = find_arbitrage_opportunities(token_pair, min_profit)
            else:
                opportunities = []
                for pair in PRICE_DATA:
                    opportunities.extend(find_arbitrage_opportunities(pair, min_profit))
            
            return {
                "id": request.get("id"),
                "result": {
                    "status": "success",
                    "opportunities": opportunities,
                    "count": len(opportunities),
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        else:
            return {
                "id": request.get("id"),
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            }
    
    except Exception as e:
        logger.error(f"MCP request error: {e}")
        return {
            "id": request.get("id", None),
            "error": {"code": -32603, "message": str(e)}
        }

@app.get("/get_arbitrage_opportunities")
async def get_arbitrage_opportunities(token_pair: str = None, min_profit_threshold: float = 0.01):
    """Get current arbitrage opportunities"""
    try:
        update_prices()
        
        if token_pair:
            opportunities = find_arbitrage_opportunities(token_pair, min_profit_threshold)
        else:
            opportunities = []
            for pair in PRICE_DATA:
                opportunities.extend(find_arbitrage_opportunities(pair, min_profit_threshold))
        
        return {
            "status": "success",
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting arbitrage opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/supported_tokens")
async def get_supported_tokens():
    """Get list of supported tokens"""
    return {
        "status": "success",
        "tokens": SUPPORTED_TOKENS,
        "count": len(SUPPORTED_TOKENS),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/supported_dexs")
async def get_supported_dexs():
    """Get list of supported DEXs"""
    return {
        "status": "success",
        "dexs": SUPPORTED_DEXS,
        "count": len(SUPPORTED_DEXS),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/market_status")
async def get_market_status():
    """Get overall market status and statistics"""
    update_prices()
    
    total_opportunities = 0
    for pair in PRICE_DATA:
        total_opportunities += len(find_arbitrage_opportunities(pair))
    
    return {
        "status": "success",
        "market_active": True,
        "total_token_pairs": len(PRICE_DATA),
        "total_dexs": len(SUPPORTED_DEXS),
        "active_arbitrage_opportunities": total_opportunities,
        "last_update": datetime.now().isoformat()
    }

# Background task to continuously update prices
async def price_updater():
    """Background task to update prices every 5 seconds"""
    while True:
        try:
            update_prices()
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Price updater error: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(price_updater())
    logger.info("Enhanced MCP Price Feed Server started successfully")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8106)
