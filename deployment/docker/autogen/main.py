#!/usr/bin/env python3
"""
AutoGen Flash Loan Coordinator with Cursor API Integration
Main service for coordinating AutoGen agents using Cursor's AI capabilities.
"""

import os
import sys
import asyncio
import logging
import uvicorn
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import json

# Add shared modules to path
sys.path.append('/app/shared')

try:
    from cursor_api_client import (
        CursorAPIClient, 
        CursorConfig, 
        CursorMessage, 
        CursorResponse,
        create_cursor_client
    )
except ImportError:
    print("Warning: Cursor API client not found. Using fallback configuration.")
    CursorAPIClient = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/autogen-coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CursorAutoGenLLM:
    """Custom AutoGen LLM wrapper for Cursor API"""
    
    def __init__(self, config: Optional[CursorConfig] = None):
        self.config = config or CursorConfig.from_env()
        self.cursor_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Cursor API client"""
        try:
            if os.getenv('ENABLE_CURSOR_INTEGRATION', 'true').lower() == 'true':
                self.cursor_client = CursorAPIClient(self.config)
                logger.info("Cursor API client initialized for AutoGen")
            else:
                logger.warning("Cursor integration disabled for AutoGen")
        except Exception as e:
            logger.error(f"Failed to initialize Cursor API client: {e}")
    
    async def get_cursor_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Get response from Cursor API"""
        if not self.cursor_client:
            return "Cursor API client not available"
        
        try:
            if not self.cursor_client.session:
                await self.cursor_client.start_session()
            
            cursor_messages = [
                CursorMessage(role=msg["role"], content=msg["content"])
                for msg in messages
            ]
            
            response = await self.cursor_client.chat_completion(
                messages=cursor_messages,
                model=kwargs.get('model', self.config.model),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature)
            )
            
            return response.content
        
        except Exception as e:
            logger.error(f"Cursor API call failed: {e}")
            return f"Error: {str(e)}"

# Pydantic models for API
class AutoGenRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to send to AutoGen agents")
    agents: List[str] = Field(default=["arbitrage", "smart_contract", "risk"], description="Agents to include in the conversation")
    max_turns: int = Field(default=10, description="Maximum conversation turns")
    temperature: float = Field(default=0.1, description="LLM temperature")

class AutoGenResponse(BaseModel):
    conversation: List[Dict[str, Any]] = Field(..., description="Full conversation history")
    summary: str = Field(..., description="Conversation summary")
    agents_used: List[str] = Field(..., description="Agents that participated")
    total_turns: int = Field(..., description="Total conversation turns")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class HealthResponse(BaseModel):
    status: str
    cursor_api: bool
    autogen: bool
    agents_count: int
    timestamp: str

# FastAPI app
app = FastAPI(
    title="AutoGen Flash Loan Coordinator",
    description="AutoGen-based multi-agent system with Cursor API integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
cursor_llm: Optional[CursorAutoGenLLM] = None
agents: Dict[str, Any] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the AutoGen system"""
    global cursor_llm, agents
    
    logger.info("Starting AutoGen Coordinator with Cursor API integration")
    
    try:
        # Initialize Cursor LLM
        cursor_llm = CursorAutoGenLLM()
        logger.info(f"AutoGen Coordinator initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize AutoGen Coordinator: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    cursor_api_ok = False
    autogen_ok = False
    
    try:
        if cursor_llm and cursor_llm.cursor_client:
            cursor_api_ok = await cursor_llm.cursor_client.health_check()
        
        autogen_ok = True  # Basic check
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
    
    status = "healthy" if cursor_api_ok and autogen_ok else "unhealthy"
    
    return HealthResponse(
        status=status,
        cursor_api=cursor_api_ok,
        autogen=autogen_ok,
        agents_count=len(agents),
        timestamp=str(asyncio.get_event_loop().time())
    )

@app.post("/autogen/chat", response_model=AutoGenResponse)
async def chat_with_autogen(request: AutoGenRequest, background_tasks: BackgroundTasks):
    """Start a multi-agent conversation using AutoGen and Cursor API"""
    
    if not cursor_llm:
        raise HTTPException(status_code=503, detail="AutoGen system not initialized")
    
    try:
        logger.info(f"Starting AutoGen conversation: {request.prompt[:100]}...")
        
        # Multi-agent simulation using Cursor API
        conversation = []
        
        # Agent 1: Flash Loan Expert
        if "arbitrage" in request.agents:
            arbitrage_prompt = f"As a flash loan arbitrage expert, analyze this opportunity: {request.prompt}"
            arbitrage_response = await cursor_llm.get_cursor_response(
                [{"role": "user", "content": arbitrage_prompt}], 
                temperature=request.temperature
            )
            conversation.append({
                "agent": "FlashLoanExpert",
                "content": arbitrage_response,
                "role": "assistant"
            })
        
        # Agent 2: Smart Contract Developer
        if "smart_contract" in request.agents:
            contract_prompt = f"As a Solidity developer, review the smart contract aspects: {request.prompt}"
            contract_response = await cursor_llm.get_cursor_response(
                [{"role": "user", "content": contract_prompt}], 
                temperature=0.1  # Lower temp for code
            )
            conversation.append({
                "agent": "SolidityDeveloper",
                "content": contract_response,
                "role": "assistant"
            })
        
        # Agent 3: Risk Analyst
        if "risk" in request.agents:
            risk_prompt = f"As a DeFi risk analyst, assess the risks: {request.prompt}"
            risk_response = await cursor_llm.get_cursor_response(
                [{"role": "user", "content": risk_prompt}], 
                temperature=request.temperature
            )
            conversation.append({
                "agent": "RiskAnalyst", 
                "content": risk_response,
                "role": "assistant"
            })
        
        # Generate summary
        summary_content = " ".join([msg["content"][:200] for msg in conversation])
        summary = await cursor_llm.get_cursor_response([
            {"role": "user", "content": f"Summarize this multi-agent analysis: {summary_content}"}
        ], max_tokens=300)
        
        return AutoGenResponse(
            conversation=conversation,
            summary=summary,
            agents_used=request.agents,
            total_turns=len(conversation),
            metadata={
                "model": cursor_llm.config.model,
                "timestamp": str(asyncio.get_event_loop().time()),
                "selected_agents": request.agents
            }
        )
        
    except Exception as e:
        logger.error(f"AutoGen chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autogen/generate-contract")
async def generate_contract(prompt: str, contract_type: str = "arbitrage"):
    """Generate a smart contract using Cursor API"""
    
    if not cursor_llm:
        raise HTTPException(status_code=503, detail="AutoGen system not initialized")
    
    try:
        contract_prompt = f"""
        Generate a secure {contract_type} smart contract for flash loans.
        Requirements: {prompt}
        
        Include:
        - Proper error handling
        - Gas optimization
        - Security best practices
        - Comprehensive comments
        """
        
        result = await cursor_llm.get_cursor_response([
            {"role": "user", "content": contract_prompt}
        ], temperature=0.1, max_tokens=2048)
        
        return {
            "contract_code": result,
            "contract_type": contract_type,
            "agent": "SolidityDeveloper",
            "timestamp": str(asyncio.get_event_loop().time())
        }
        
    except Exception as e:
        logger.error(f"Contract generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autogen/risk-analysis")
async def analyze_risk(query: str, analysis_type: str = "comprehensive"):
    """Perform risk analysis using Cursor API"""
    
    if not cursor_llm:
        raise HTTPException(status_code=503, detail="AutoGen system not initialized")
    
    try:
        risk_prompt = f"""
        Perform a {analysis_type} risk analysis for this flash loan scenario:
        {query}
        
        Analyze:
        - Smart contract risks
        - Market volatility risks
        - Liquidity risks
        - Regulatory compliance
        - Mitigation strategies
        """
        
        result = await cursor_llm.get_cursor_response([
            {"role": "user", "content": risk_prompt}
        ], temperature=0.2, max_tokens=1500)
        
        return {
            "risk_analysis": result,
            "analysis_type": analysis_type,
            "agent": "RiskAnalyst",
            "timestamp": str(asyncio.get_event_loop().time())
        }
        
    except Exception as e:
        logger.error(f"Risk analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv('SERVICE_PORT', '8000'))
    host = os.getenv('SERVICE_HOST', '0.0.0.0')
    
    logger.info(f"Starting AutoGen Coordinator on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    ) 