#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import signal
import sys
import threading
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs
import os
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dataclasses import dataclass

from agents.code_interpreter_agent import CodeInterpreterAgent
from services.memory_manager import MemoryManager
from services.tool_registry import ToolRegistry
from services.vector_store import VectorStoreService
from utils.config import get_config
from utils.logger import setup_logger

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

from langchain.llms.base import LLM
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/langchain-coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CursorLLM(LLM):
    """Custom LangChain LLM wrapper for Cursor API"""
    
    cursor_client: Optional[CursorAPIClient] = None
    model_name: str = "cursor-gpt-4"
    temperature: float = 0.1
    max_tokens: int = 4096
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_cursor_client()
    
    def _setup_cursor_client(self):
        """Initialize Cursor API client"""
        try:
            if os.getenv('ENABLE_CURSOR_INTEGRATION', 'true').lower() == 'true':
                config = CursorConfig.from_env()
                self.cursor_client = CursorAPIClient(config)
                logger.info("Cursor API client initialized successfully")
            else:
                logger.warning("Cursor integration disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Cursor API client: {e}")
    
    @property
    def _llm_type(self) -> str:
        return "cursor"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Make a call to Cursor API"""
        return asyncio.run(self._acall(prompt, stop))
    
    async def _acall(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Async call to Cursor API"""
        if not self.cursor_client:
            return "Cursor API client not available"
        
        try:
            if not self.cursor_client.session:
                await self.cursor_client.start_session()
            
            messages = [CursorMessage(role="user", content=prompt)]
            response = await self.cursor_client.chat_completion(
                messages=messages,
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.content
        
        except Exception as e:
            logger.error(f"Cursor API call failed: {e}")
            return f"Error: {str(e)}"

class FlashLoanAnalysisTool(BaseTool):
    """Tool for analyzing flash loan opportunities using Cursor API"""
    
    name: str = "flash_loan_analyzer"
    description: str = "Analyze flash loan arbitrage opportunities and smart contracts"
    cursor_client: Optional[CursorAPIClient] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            config = CursorConfig.from_env()
            self.cursor_client = CursorAPIClient(config)
        except Exception as e:
            logger.error(f"Failed to initialize Cursor client for tool: {e}")
    
    def _run(self, query: str) -> str:
        """Run the flash loan analysis"""
        return asyncio.run(self._arun(query))
    
    async def _arun(self, query: str) -> str:
        """Async run the flash loan analysis"""
        if not self.cursor_client:
            return "Cursor API client not available for analysis"
        
        try:
            if not self.cursor_client.session:
                await self.cursor_client.start_session()
            
            response = await self.cursor_client.code_analysis(
                code=query,
                analysis_type="flash_loan_analysis",
                language="solidity"
            )
            
            return response.content
        
        except Exception as e:
            logger.error(f"Flash loan analysis failed: {e}")
            return f"Analysis error: {str(e)}"

class CodeGenerationTool(BaseTool):
    """Tool for generating code using Cursor API"""
    
    name: str = "code_generator"
    description: str = "Generate smart contracts and Python code for flash loan arbitrage"
    cursor_client: Optional[CursorAPIClient] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            config = CursorConfig.from_env()
            self.cursor_client = CursorAPIClient(config)
        except Exception as e:
            logger.error(f"Failed to initialize Cursor client for tool: {e}")
    
    def _run(self, prompt: str) -> str:
        """Run code generation"""
        return asyncio.run(self._arun(prompt))
    
    async def _arun(self, prompt: str) -> str:
        """Async run code generation"""
        if not self.cursor_client:
            return "Cursor API client not available for code generation"
        
        try:
            if not self.cursor_client.session:
                await self.cursor_client.start_session()
            
            # Parse the prompt to determine language and requirements
            language = "python"
            if "solidity" in prompt.lower() or "smart contract" in prompt.lower():
                language = "solidity"
            
            response = await self.cursor_client.code_generation(
                prompt=prompt,
                language=language,
                context="Flash loan arbitrage system",
                requirements=["Security focused", "Gas optimized", "Well documented"]
            )
            
            return response.content
        
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return f"Generation error: {str(e)}"

# Pydantic models for API
class LangChainRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to send to LangChain")
    agent_type: str = Field(default="react", description="Type of agent to use")
    tools: List[str] = Field(default=["flash_loan_analyzer", "code_generator"], description="Tools to make available")
    max_iterations: int = Field(default=5, description="Maximum agent iterations")

class LangChainResponse(BaseModel):
    response: str = Field(..., description="Agent response")
    agent_type: str = Field(..., description="Agent type used")
    iterations: int = Field(..., description="Number of iterations")
    tools_used: List[str] = Field(..., description="Tools that were used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class HealthResponse(BaseModel):
    status: str
    cursor_api: bool
    langchain: bool
    timestamp: str

# FastAPI app
app = FastAPI(
    title="LangChain Flash Loan Coordinator",
    description="LangChain-based AI coordination service with Cursor API integration",
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
cursor_llm: Optional[CursorLLM] = None
agent_executor: Optional[AgentExecutor] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    global cursor_llm, agent_executor
    
    logger.info("Starting LangChain Coordinator with Cursor API integration")
    
    try:
        # Initialize Cursor LLM
        cursor_llm = CursorLLM(
            model_name=os.getenv('CURSOR_MODEL', 'cursor-gpt-4'),
            temperature=float(os.getenv('CURSOR_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('CURSOR_MAX_TOKENS', '4096'))
        )
        
        # Initialize tools
        tools = [
            FlashLoanAnalysisTool(),
            CodeGenerationTool()
        ]
        
        # Create agent
        prompt_template = PromptTemplate(
            input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
            template="""You are an expert flash loan arbitrage specialist with access to AI-powered tools.
            Use the available tools to help analyze opportunities and generate code.
            
            Tools available: {tool_names}
            Tool descriptions:
            {tools}
            
            Question: {input}
            
            Think step by step about what tools you need to use.
            
            {agent_scratchpad}
            """
        )
        
        agent = create_react_agent(
            llm=cursor_llm,
            tools=tools,
            prompt=prompt_template
        )
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            memory=ConversationBufferMemory()
        )
        
        logger.info("LangChain Coordinator initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize LangChain Coordinator: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    cursor_api_ok = False
    langchain_ok = False
    
    try:
        if cursor_llm and cursor_llm.cursor_client:
            cursor_api_ok = await cursor_llm.cursor_client.health_check()
        
        if agent_executor:
            langchain_ok = True
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
    
    status = "healthy" if cursor_api_ok and langchain_ok else "unhealthy"
    
    return HealthResponse(
        status=status,
        cursor_api=cursor_api_ok,
        langchain=langchain_ok,
        timestamp=str(asyncio.get_event_loop().time())
    )

@app.post("/langchain/chat", response_model=LangChainResponse)
async def chat_with_langchain(request: LangChainRequest, background_tasks: BackgroundTasks):
    """Chat with LangChain agents using Cursor API"""
    
    if not agent_executor:
        raise HTTPException(status_code=503, detail="LangChain agent not initialized")
    
    try:
        logger.info(f"Processing LangChain request: {request.prompt[:100]}...")
        
        # Run the agent
        result = await agent_executor.arun(
            input=request.prompt,
            max_iterations=request.max_iterations
        )
        
        return LangChainResponse(
            response=result,
            agent_type=request.agent_type,
            iterations=1,  # TODO: Track actual iterations
            tools_used=request.tools,
            metadata={
                "model": os.getenv('CURSOR_MODEL', 'cursor-gpt-4'),
                "timestamp": str(asyncio.get_event_loop().time())
            }
        )
        
    except Exception as e:
        logger.error(f"LangChain chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/langchain/code-generation")
async def generate_code(prompt: str, language: str = "python"):
    """Generate code using Cursor API directly"""
    
    if not cursor_llm or not cursor_llm.cursor_client:
        raise HTTPException(status_code=503, detail="Cursor API client not available")
    
    try:
        response = await cursor_llm.cursor_client.code_generation(
            prompt=prompt,
            language=language,
            context="Flash loan arbitrage system"
        )
        
        return {
            "code": response.content,
            "language": language,
            "model": response.model,
            "usage": response.usage,
            "response_time": response.response_time
        }
        
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/langchain/contract-audit")
async def audit_contract(contract_code: str, contract_type: str = "arbitrage"):
    """Audit smart contract using Cursor API"""
    
    if not cursor_llm or not cursor_llm.cursor_client:
        raise HTTPException(status_code=503, detail="Cursor API client not available")
    
    try:
        response = await cursor_llm.cursor_client.smart_contract_audit(
            contract_code=contract_code,
            contract_type=contract_type
        )
        
        return {
            "audit_result": response.content,
            "contract_type": contract_type,
            "model": response.model,
            "usage": response.usage,
            "response_time": response.response_time
        }
        
    except Exception as e:
        logger.error(f"Contract audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv('SERVICE_PORT', '8000'))
    host = os.getenv('SERVICE_HOST', '0.0.0.0')
    
    logger.info(f"Starting LangChain Coordinator on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        # Cleanup agents
        for agent_name, agent in agents.items():
            logger.info(str(f"🧹 Cleaning up agent: {agent_name}"))
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()
        
        # Cleanup services
        if vector_store:
            logger.info("🧹 Cleaning up vector store...")
            await vector_store.cleanup()
            
        if memory_manager:
            logger.info("🧹 Cleaning up memory manager...")
            await memory_manager.cleanup()
        
        logger.info("[OK] All services cleaned up")
        
    except Exception as e:
        logger.error(str(f"[ERROR] Cleanup failed: {e}"))

async def health_check():
    """Perform health check"""
    try:
        services_status = {}
        
        # Check memory manager
        if memory_manager:
            try:
                await memory_manager.get_memory_stats()
                services_status["memory_manager"] = "healthy"
            except:
                services_status["memory_manager"] = "unhealthy"
        else:
            services_status["memory_manager"] = "not_initialized"
        
        # Check vector store
        if vector_store:
            try:
                await vector_store.list_collections()
                services_status["vector_store"] = "healthy"
            except:
                services_status["vector_store"] = "unhealthy"
        else:
            services_status["vector_store"] = "not_initialized"
        
        # Check tool registry
        if tool_registry:
            try:
                await tool_registry.list_tools()
                services_status["tool_registry"] = "healthy"
            except:
                services_status["tool_registry"] = "unhealthy"
        else:
            services_status["tool_registry"] = "not_initialized"
        
        # Check agents
        services_status["agents"] = f"{len(agents)}_active"
        
        overall_status = "healthy" if all(
            status != "unhealthy" for status in services_status.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "services": services_status,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(str(f"[ERROR] Health check failed: {e}"))
        return {
            "status": "error",
            "timestamp": time.time(),
            "error": str(e),
            "version": "1.0.0"
        }

async def get_system_status():
    """Get detailed system status"""
    try:
        status = {
            "config": config.get_config_summary() if config else {},
            "memory": await memory_manager.get_memory_stats() if memory_manager else {},
            "vector_store": {
                "collections": await vector_store.list_collections() if vector_store else []
            },
            "tools": {
                "total": len(await tool_registry.list_tools()) if tool_registry else 0,
                "categories": await tool_registry.get_categories() if tool_registry else []
            },
            "agents": {
                "total": len(agents),
                "active": list(agents.keys())
            }
        }
        return status
        
    except Exception as e:
        logger.error(str(f"[ERROR] Failed to get system status: {e}"))
        return {"error": str(e)}

async def process_task(task_type: str, description: str, context: Dict[str, Any], agent_type: str = "code_interpreter"):
    """Process a task using the specified agent"""
    try:
        task_id = str(uuid.uuid4())
        timestamp = time.time()
        
        logger.info(str(f"[LOG] Processing task {task_id}: {description}"))
        
        # Get the appropriate agent
        if agent_type not in agents:
            raise ValueError(f"Agent type '{agent_type}' not available")
        
        agent = agents[agent_type]
        
        # Execute task
        result = await agent.process_direct(description, context)
        
        # Store in memory if available
        if memory_manager:
            await memory_manager.store_conversation(
                session_id=task_id,
                agent_name=agent_type,
                message_type="task_request",
                message_content=description,
                metadata={"task_id": task_id, "context": context}
            )
            
            await memory_manager.store_conversation(
                session_id=task_id,
                agent_name=agent_type,
                message_type="task_response",
                message_content=str(result),
                metadata={"task_id": task_id, "result": result}
            )
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(str(f"[ERROR] Task processing failed: {e}"))
        return {
            "task_id": str(uuid.uuid4()),
            "status": "failed",
            "error": str(e),
            "timestamp": time.time()
        }

async def simple_web_server():
    """Simple HTTP server for basic endpoints"""
    try:
        
        class RequestHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                # Suppress default logging
                pass
            
            def do_GET(self):
                parsed_path = urlparse(self.path)
                
                if parsed_path.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    health_data = asyncio.run(health_check())
                    self.wfile.write(json.dumps(health_data, ensure_ascii=True, default=str).encode())
                
                elif parsed_path.path == '/status':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    status_data = asyncio.run(get_system_status())
                    self.wfile.write(json.dumps(status_data, ensure_ascii=True, default=str).encode())
                
                elif parsed_path.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    html = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>LangChain Multi-Agent System</title>
                    </head>
                    <body>
                        <h1>LangChain Multi-Agent System</h1>
                        <p>System is running</p>
                        <ul>
                            <li><a href="/health">Health Check</a></li>
                            <li><a href="/status">System Status</a></li>
                        </ul>
                    </body>
                    </html>
                    """
                    self.wfile.write(html.encode())
                
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'Not Found')
            
            def do_POST(self):
                if self.path == '/tasks':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    try:
                        data = json.loads(post_data.decode('utf-8'))
                        result = asyncio.run(process_task(
                            task_type=data.get('task_type', 'general'),
                            description=data.get('description', ''),
                            context=data.get('context', {}),
                            agent_type=data.get('agent_type', 'code_interpreter')
                        ))
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result, ensure_ascii=True, default=str).encode())
                        
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        error_response = {"error": str(e)}
                        self.wfile.write(json.dumps(error_response, ensure_ascii=True, default=str).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'Not Found')
        
        def run_server():
            server = HTTPServer(('0.0.0.0', 8000), RequestHandler)
            logger.info("[NETWORK] HTTP server started on port 8000")
            server.serve_forever()
        
        # Run server in background thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        return server_thread
        
    except Exception as e:
        logger.error(str(f"[ERROR] Failed to start web server: {e}"))
        return None

# Signal handlers
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(str(f"📡 Received signal {signum}, initiating graceful shutdown..."))
    shutdown_event.set()

async def main():
    """Main application entry point"""
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("[START] LangChain Multi-Agent System starting...")
    
    try:
        # Initialize all services
        await initialize_services()
        logger.info("[OK] All services initialized successfully")
        
        # Start web server
        server_thread = await simple_web_server()
        
        logger.info("[INIT] LangChain Multi-Agent System is ready!")
        logger.info("📡 Endpoints available:")
        logger.info("   - http://localhost:8000/ (Home")
        logger.info("   - http://localhost:8000/health (Health Check")
        logger.info("   - http://localhost:8000/status (System Status")
        logger.info("   - POST http://localhost:8000/tasks (Task Execution")
        
        # Keep the application running
        while not shutdown_event.is_set():
            await asyncio.sleep(1)
        
        logger.info("[STOP] Shutdown signal received, cleaning up...")
        await cleanup_services()
        
        return 0
        
    except Exception as e:
        logger.error(str(f"[ERROR] Application failed: {e}"))
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("👋 Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(str(f"[ERROR] Application failed: {e}"))
        logger.error(traceback.format_exc())
        sys.exit(1)