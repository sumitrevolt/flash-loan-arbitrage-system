from fastapi import FastAPI, Request
import httpx
import asyncio
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)

# Example: Assign roles to agents
AGENT_ROLES = {
    1: 'indexer', 2: 'indexer', 3: 'indexer',
    4: 'analyzer', 5: 'analyzer', 6: 'analyzer',
    7: 'fetcher', 8: 'fetcher',
    9: 'coordinator', 10: 'coordinator'
}

AI_AGENT_URLS = [f"http://ai_agent-{i}:5000/action" for i in range(1, 11)]
MCP_SERVER_URLS = [f"http://mcp_server-{i}:5000/action" for i in range(1, 22)]

@app.get('/')
def read_root():
    return {"message": "Commanding and Analysis Service Running"}

@app.get('/status')
async def get_status():
    # Aggregate status from all agents and servers
    async with httpx.AsyncClient() as client:
        agent_tasks = [client.get(url) for url in AI_AGENT_URLS]
        server_tasks = [client.get(url) for url in MCP_SERVER_URLS]
        agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        server_results = await asyncio.gather(*server_tasks, return_exceptions=True)
    agent_status = [r.json() if hasattr(r, 'json') else str(r) for r in agent_results]
    server_status = [r.json() if hasattr(r, 'json') else str(r) for r in server_results]
    return {"ai_agents": agent_status, "mcp_servers": server_status}

@app.post('/command')
async def send_command(request: Request):
    data = await request.json()
    target = data.get("target")
    action = data.get("action")
    results = {}
    async with httpx.AsyncClient() as client:
        if target == "all_agents":
            tasks = [client.post(url, json={"action": action}) for url in AI_AGENT_URLS]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            results = {f"agent_{i+1}": (r.json() if hasattr(r, 'json') else str(r)) for i, r in enumerate(responses)}
        elif target == "all_mcp_servers":
            tasks = [client.post(url, json={"action": action}) for url in MCP_SERVER_URLS]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            results = {f"mcp_server_{i+1}": (r.json() if hasattr(r, 'json') else str(r)) for i, r in enumerate(responses)}
        elif target.startswith('role:'):
            role = target.split(':', 1)[1]
            agent_ids = [i for i, r in AGENT_ROLES.items() if r == role]
            tasks = [client.post(f"http://ai_agent-{i}:5000/action", json={"action": action}) for i in agent_ids]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            results = {f"agent_{i}": (r.json() if hasattr(r, 'json') else str(r)) for i, r in zip(agent_ids, responses)}
        else:
            # Target a specific agent or server
            if target.startswith('ai_agent-'):
                idx = int(target.split('-')[1])
                url = f"http://ai_agent-{idx}:5000/action"
            elif target.startswith('mcp_server-'):
                idx = int(target.split('-')[1])
                url = f"http://mcp_server-{idx}:5000/action"
            else:
                return {"error": "Unknown target"}
            try:
                resp = await client.post(url, json={"action": action})
                results = resp.json()
            except Exception as e:
                results = {"error": str(e)}
    return results

@app.post('/flashloan')
async def trigger_flashloan(request: Request):
    data = await request.json()
    amount = data.get("amount")
    token_address = data.get("token_address")
    # Relay flashloan execution to all MCP servers
    async with httpx.AsyncClient() as client:
        tasks = [client.post(url, json={"action": "flashloan", "amount": amount, "token_address": token_address}) for url in MCP_SERVER_URLS]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    results = {f"mcp_server_{i+1}": (r.json() if hasattr(r, 'json') else str(r)) for i, r in enumerate(responses)}
    return results 