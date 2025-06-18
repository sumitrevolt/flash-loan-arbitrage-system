#!/usr/bin/env node

from fastmcp import FastMCP
from typing import Dict, List, Any, Optional
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.training.mcp_training_coordinator import MCPTrainingCoordinator

# Initialize FastMCP server
mcp = FastMCP("Training Coordinator MCP Server")

# Global coordinator instance
coordinator: Optional[MCPTrainingCoordinator] = None

@mcp.tool()
async def discover_training_servers() -> Dict[str, Any]:
    """Discover MCP servers available for training data collection"""
    
    global coordinator
    if not coordinator:
        coordinator = MCPTrainingCoordinator()
    
    servers = await coordinator.discover_mcp_servers()
    
    return {
        "discovered_servers": len(servers),
        "servers": [
            {
                "name": server.name,
                "host": server.host,
                "port": server.port,
                "capabilities": server.capabilities,
                "health_status": server.health_status
            } for server in servers
        ],
        "total_capabilities": len(set(cap for server in servers for cap in server.capabilities))
    }

@mcp.tool()
async def train_models(model_types: List[str] = None) -> Dict[str, Any]:
    """Train ML models using data from MCP servers"""
    
    global coordinator
    if not coordinator:
        coordinator = MCPTrainingCoordinator()
    
    if model_types is None:
        model_types = ["arbitrage_predictor", "risk_classifier"]
    
    results = await coordinator.train_models(model_types)
    
    return {
        "training_initiated": True,
        "session_id": results.get("session_id"),
        "models_training": model_types,
        "training_data_size": results.get("training_data_size", 0),
        "results": results.get("results", {}),
        "status": "completed" if "error" not in results else "failed"
    }

@mcp.tool()
async def get_training_status(session_id: str = None) -> Dict[str, Any]:
    """Get status of training sessions"""
    
    global coordinator
    if not coordinator:
        coordinator = MCPTrainingCoordinator()
    
    status = await coordinator.get_training_status(session_id)
    
    return {
        "training_status_retrieved": True,
        "session_id": session_id,
        "status": status
    }

@mcp.tool()
async def collect_training_data(data_types: List[str] = None) -> Dict[str, Any]:
    """Collect training data from MCP servers"""
    
    global coordinator
    if not coordinator:
        coordinator = MCPTrainingCoordinator()
    
    if data_types is None:
        data_types = ["arbitrage", "revenue", "risk"]
    
    training_data = await coordinator.collect_training_data(data_types)
    
    return {
        "data_collection_completed": True,
        "samples_collected": len(training_data),
        "data_types": data_types,
        "columns": list(training_data.columns) if not training_data.empty else [],
        "sample_data": training_data.head(3).to_dict('records') if not training_data.empty else []
    }

@mcp.tool()
async def deploy_models(session_id: str) -> Dict[str, Any]:
    """Deploy trained models to MCP servers"""
    
    global coordinator
    if not coordinator:
        coordinator = MCPTrainingCoordinator()
    
    deployment_results = await coordinator.deploy_models_to_servers(session_id)
    
    return {
        "deployment_initiated": True,
        "session_id": session_id,
        "deployment_results": deployment_results,
        "successful_deployments": deployment_results.get("deployed_servers", 0)
    }

@mcp.tool()
async def retrain_models(model_types: List[str] = None, force: bool = False) -> Dict[str, Any]:
    """Retrain models with fresh data"""
    
    global coordinator
    if not coordinator:
        coordinator = MCPTrainingCoordinator()
    
    # Collect fresh data
    fresh_data = await coordinator.collect_training_data(["arbitrage", "revenue", "risk"])
    
    if len(fresh_data) < 50 and not force:
        return {
            "retrain_skipped": True,
            "reason": "Insufficient fresh data",
            "data_size": len(fresh_data),
            "minimum_required": 50
        }
    
    # Trigger retraining
    results = await coordinator.train_models(model_types)
    
    return {
        "retrain_completed": True,
        "fresh_data_size": len(fresh_data),
        "training_results": results,
        "session_id": results.get("session_id")
    }

@mcp.tool()
async def get_model_performance() -> Dict[str, Any]:
    """Get performance metrics of trained models"""
    
    global coordinator
    if not coordinator:
        coordinator = MCPTrainingCoordinator()
    
    # Get latest training session
    status = await coordinator.get_training_status()
    
    performance_summary = {
        "models_available": len(coordinator.ml_trainer.models),
        "feature_importance": coordinator.ml_trainer.feature_importance,
        "latest_session": status.get("recent_sessions", [{}])[0] if status.get("recent_sessions") else {},
        "training_history_available": len(status.get("recent_sessions", []))
    }
    
    return performance_summary

if __name__ == "__main__":
    import uvicorn
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    print("Starting Training Coordinator MCP Server...")
    print("Available tools:")
    print("- discover_training_servers: Find MCP servers for training")
    print("- train_models: Train ML models using MCP data")
    print("- get_training_status: Check training progress")
    print("- collect_training_data: Gather data from servers")
    print("- deploy_models: Deploy trained models")
    print("- retrain_models: Retrain with fresh data")
    print("- get_model_performance: View model metrics")
    
    uvicorn.run(mcp.app, host="localhost", port=3010)
