#!/usr/bin/env python3
"""
Entrypoint script for Coordination Dashboard container
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Coordination Dashboard")

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
        <head><title>Coordination Dashboard</title></head>
        <body>
            <h1>Docker Coordination System</h1>
            <h2>System Status: Active</h2>
            <ul>
                <li><a href="http://localhost:8100/health">MCP Server Health</a></li>
                <li><a href="http://localhost:9001/health">Agent Health</a></li>
                <li><a href="http://localhost:8000/health">Orchestrator Health</a></li>
                <li><a href="http://localhost:15672">RabbitMQ Management</a></li>
            </ul>
        </body>
    </html>
    """

@app.get("/health")
def health():
    return {"status": "healthy", "dashboard": "active"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
