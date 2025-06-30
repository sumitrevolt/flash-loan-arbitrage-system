#!/usr/bin/env python3
"""
Example: Using NVIDIA Inference with LangChain MCP Server Agents
This demonstrates how to leverage GPU-accelerated inference for MCP servers
"""

import os
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Import the NVIDIA inference adapter
from nvidia_inference_adapter import (
    nvidia_generate_text,
    nvidia_generate_embeddings,
    get_mcp_optimization_config,
    get_nvidia_adapter
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app for MCP server
app = FastAPI(title="NVIDIA-Enhanced MCP Server")


class InferenceRequest(BaseModel):
    """Request model for inference"""
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    use_nvidia: bool = True


class EmbeddingRequest(BaseModel):
    """Request model for embeddings"""
    texts: list[str]
    use_nvidia: bool = True


class MCPServerWithNvidia:
    """Enhanced MCP Server with NVIDIA Inference support"""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.nvidia_config = get_mcp_optimization_config(server_name)
        self.nvidia_enabled = self.nvidia_config.get("enabled", False)
        
        if self.nvidia_enabled:
            logger.info(f"NVIDIA Inference enabled for {server_name}")
            logger.info(f"Primary model: {self.nvidia_config['primary_model']}")
            logger.info(f"Embedding model: {self.nvidia_config['embedding_model']}")
        else:
            logger.warning(f"NVIDIA Inference not enabled for {server_name}")
            
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using NVIDIA-accelerated inference if available"""
        if self.nvidia_enabled and kwargs.get("use_nvidia", True):
            # Use NVIDIA-accelerated inference
            model_name = self.nvidia_config["primary_model"]
            return nvidia_generate_text(
                prompt=prompt,
                model_name=model_name,
                max_tokens=kwargs.get("max_tokens", 512),
                temperature=kwargs.get("temperature", 0.7)
            )
        else:
            # Fallback to standard inference (placeholder)
            return f"Standard inference response for: {prompt}"
            
    async def generate_embeddings(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Generate embeddings using NVIDIA-accelerated inference if available"""
        if self.nvidia_enabled and kwargs.get("use_nvidia", True):
            # Use NVIDIA-accelerated inference
            model_name = self.nvidia_config["embedding_model"]
            embeddings = nvidia_generate_embeddings(texts, model_name=model_name)
            return embeddings.tolist()
        else:
            # Fallback to standard embeddings (placeholder)
            return [[0.1] * 768 for _ in texts]  # Mock embeddings


# Initialize the MCP server with NVIDIA support
server_name = os.getenv("MCP_SERVER_NAME", "context7-mcp")
mcp_server = MCPServerWithNvidia(server_name)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "server": server_name,
        "nvidia_enabled": mcp_server.nvidia_enabled,
        "nvidia_config": mcp_server.nvidia_config
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    nvidia_status = "enabled" if mcp_server.nvidia_enabled else "disabled"
    
    # Check GPU availability
    gpu_info = {}
    if mcp_server.nvidia_enabled:
        adapter = get_nvidia_adapter()
        gpu_info = adapter.get_gpu_memory_usage()
        
    return {
        "status": "healthy",
        "server": server_name,
        "nvidia_inference": nvidia_status,
        "gpu_info": gpu_info
    }


@app.post("/inference/text")
async def generate_text_endpoint(request: InferenceRequest):
    """Generate text using NVIDIA-accelerated inference"""
    try:
        response = await mcp_server.generate_text(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            use_nvidia=request.use_nvidia
        )
        
        return {
            "response": response,
            "model": mcp_server.nvidia_config.get("primary_model", "default"),
            "nvidia_used": mcp_server.nvidia_enabled and request.use_nvidia
        }
        
    except Exception as e:
        logger.error(f"Error in text generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inference/embeddings")
async def generate_embeddings_endpoint(request: EmbeddingRequest):
    """Generate embeddings using NVIDIA-accelerated inference"""
    try:
        embeddings = await mcp_server.generate_embeddings(
            texts=request.texts,
            use_nvidia=request.use_nvidia
        )
        
        return {
            "embeddings": embeddings,
            "model": mcp_server.nvidia_config.get("embedding_model", "default"),
            "nvidia_used": mcp_server.nvidia_enabled and request.use_nvidia,
            "num_embeddings": len(embeddings)
        }
        
    except Exception as e:
        logger.error(f"Error in embedding generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/capabilities")
async def mcp_capabilities():
    """Return MCP server capabilities"""
    base_capabilities = {
        "server_info": {
            "name": server_name,
            "version": "1.0.0",
            "nvidia_enabled": mcp_server.nvidia_enabled
        },
        "capabilities": {
            "tools": ["text_generation", "embeddings"],
            "resources": ["models", "gpu_memory"]
        }
    }
    
    if mcp_server.nvidia_enabled:
        base_capabilities["nvidia_optimization"] = {
            "primary_model": mcp_server.nvidia_config["primary_model"],
            "embedding_model": mcp_server.nvidia_config["embedding_model"],
            "gpu_config": mcp_server.nvidia_config.get("gpu_config", {})
        }
        
    return base_capabilities


# Example usage for LangChain integration
def create_nvidia_powered_langchain_tool():
    """Create a LangChain tool that uses NVIDIA inference"""
    from langchain.tools import Tool
    
    async def nvidia_inference_tool(query: str) -> str:
        """Use NVIDIA-accelerated inference through MCP server"""
        response = await mcp_server.generate_text(query, use_nvidia=True)
        return response
        
    return Tool(
        name="NVIDIA_Inference",
        func=lambda x: asyncio.run(nvidia_inference_tool(x)),
        description="Use NVIDIA GPU-accelerated inference for fast text generation"
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting {server_name} with NVIDIA Inference support on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 