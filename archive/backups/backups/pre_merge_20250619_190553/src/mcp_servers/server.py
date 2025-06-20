#!/usr/bin/env python3
"""
MCP Server: coordinator
Inter-service coordination
"""

import os
import time
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP-coordinator")

app = FastAPI()

SERVER_NAME = "coordinator"
SERVER_PORT = 8021
DESCRIPTION = "Inter-service coordination"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'http://orchestrator:8000')

# Server state
server_state = {
    "start_time": datetime.now(),
    "task_count": 0,
    "status": "running",
    "last_heartbeat": datetime.now()
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = datetime.now() - server_state["start_time"]
    return {
        "status": "healthy",
        "server": SERVER_NAME,
        "port": SERVER_PORT,
        "description": DESCRIPTION,
        "uptime_seconds": uptime.total_seconds(),
        "task_count": server_state["task_count"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def status():
    """Detailed status endpoint"""
    uptime = datetime.now() - server_state["start_time"]
    return {
        "server": SERVER_NAME,
        "port": SERVER_PORT,
        "description": DESCRIPTION,
        "uptime": str(uptime),
        "task_count": server_state["task_count"],
        "status": server_state["status"],
        "github_token_configured": bool(GITHUB_TOKEN),
        "last_heartbeat": server_state["last_heartbeat"].isoformat()
    }

@app.post("/task")
async def process_task(task: dict):
    """Process a task from the orchestrator"""
    try:
        logger.info(f"Processing task: {task.get('name', 'unnamed')}")
        
        # Simulate task processing based on server type
        await asyncio.sleep(2)  # Simulate work
        
        server_state["task_count"] += 1
        server_state["last_heartbeat"] = datetime.now()
        
        result = {
            "server": SERVER_NAME,
            "task": task,
            "result": f"{SERVER_NAME} processed task successfully",
            "timestamp": datetime.now().isoformat(),
            "task_number": server_state["task_count"]
        }
        
        logger.info(f"Task completed: {result['result']}")
        return result
        
    except Exception as e:
        logger.error(f"Task processing failed: {e}")
        return {"error": str(e), "server": SERVER_NAME}

@app.get("/metrics")
async def metrics():
    """Server metrics endpoint"""
    uptime = datetime.now() - server_state["start_time"]
    return {
        "server": SERVER_NAME,
        "uptime_seconds": uptime.total_seconds(),
        "task_count": server_state["task_count"],
        "tasks_per_hour": server_state["task_count"] / max(uptime.total_seconds() / 3600, 0.1),
        "memory_usage": "simulated_low",
        "cpu_usage": "simulated_normal",
        "status": server_state["status"]
    }

async def heartbeat_loop():
    """Send heartbeat to orchestrator"""
    while True:
        try:
            if ORCHESTRATOR_URL:
                # Simulate heartbeat to orchestrator
                server_state["last_heartbeat"] = datetime.now()
                logger.info(f"Heartbeat sent to orchestrator - Tasks: {server_state['task_count']}")
            
            await asyncio.sleep(60)  # Heartbeat every minute
            
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {SERVER_NAME} MCP Server on port {SERVER_PORT}")
    logger.info(f"Description: {DESCRIPTION}")
    
    # Start heartbeat loop
    asyncio.create_task(heartbeat_loop())

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {SERVER_NAME} MCP Server on port {SERVER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
