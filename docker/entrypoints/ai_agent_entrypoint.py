#!/usr/bin/env python3
"""
Entrypoint script for AI Agent containers
"""

import os
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="AI Agent")

@app.get("/health")
def health():
    agent_type = os.getenv("AGENT_TYPE", "unknown")
    return {"status": "healthy", "agent_type": agent_type}

@app.post("/coordinate")
def coordinate(data: dict = None):
    agent_type = os.getenv("AGENT_TYPE", "unknown")
    return {"status": "completed", "agent": agent_type, "result": f"{agent_type} task completed"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 9001))
    uvicorn.run(app, host="0.0.0.0", port=port)
