import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List

app = FastAPI()

# Allow CORS for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPP_FILE = os.getenv("OPP_FILE", "arbitrage_opportunities.json")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/opportunities")
def get_opportunities(limit: int = 20):
    """Return the latest N opportunities from the JSON file."""
    if not os.path.exists(OPP_FILE):
        return JSONResponse(content={"opportunities": []})
    with open(OPP_FILE, "r") as f:
        try:
            data = json.load(f)
        except Exception:
            data = []
    return {"opportunities": data[-limit:]}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_len = 0
    try:
        while True:
            await asyncio.sleep(2)
            if not os.path.exists(OPP_FILE):
                continue
            with open(OPP_FILE, "r") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
            if len(data) > last_len:
                # Send only new opportunities
                for opp in data[last_len:]:
                    await websocket.send_json(opp)
                last_len = len(data)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# Usage:
#   uvicorn scripts.live_web3_api:app --reload --port 8081
# Point your dashboard to http://localhost:8081/opportunities or ws://localhost:8081/ws 