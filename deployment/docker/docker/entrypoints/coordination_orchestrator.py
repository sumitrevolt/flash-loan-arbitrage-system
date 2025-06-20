#!/usr/bin/env python3
"""
Entrypoint script for Coordination Orchestrator container
"""

import os
import uvicorn
import asyncio
import aiohttp
from datetime import datetime
from fastapi import FastAPI

app = FastAPI(title="Coordination Orchestrator")

@app.get("/health")
def health():
    return {"status": "healthy", "orchestrator": "active", "timestamp": datetime.now().isoformat()}

@app.post("/coordinate")
async def coordinate(task: dict):
    # Simulate coordination with MCP servers and agents
    results = {"task": task, "timestamp": datetime.now().isoformat()}
    
    # Test MCP server
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://mcp_price_feed:8100/health") as resp:
                if resp.status == 200:
                    results["mcp_server_status"] = "healthy"
                else:
                    results["mcp_server_status"] = "unhealthy"
    except:
        results["mcp_server_status"] = "unreachable"
    
    # Test AI agent
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://agent_arbitrage_detector:9001/health") as resp:
                if resp.status == 200:
                    results["agent_status"] = "healthy"
                else:
                    results["agent_status"] = "unhealthy"
    except:
        results["agent_status"] = "unreachable"
    
    results["status"] = "coordination_completed"
    results["message"] = "Task coordinated between MCP servers and AI agents"
    
    return results

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
