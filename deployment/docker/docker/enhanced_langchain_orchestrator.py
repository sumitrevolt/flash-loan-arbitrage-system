"""
Enhanced LangChain Orchestrator
Coordinates flash loan arbitrage operations with AI-driven decision making
"""
import asyncio
import json
import os
from typing import Dict, List, Optional, Any
import aiohttp
import redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger
from datetime import datetime, timezone
from pydantic import BaseModel
import numpy as np

# Configure logging
logger.add("logs/langchain_orchestrator.log", rotation="1 day", retention="7 days")

class ArbitrageOpportunity(BaseModel):
    transaction_hash: Optional[str] = None
    type: str
    dex_from: Optional[str] = None
    dex_to: Optional[str] = None
    token_pair: str
    estimated_profit: float
    gas_price: Optional[int] = None
    timestamp: str
    block_number: Optional[int] = None
    confidence: float

class ExecutionResult(BaseModel):
    success: bool
    simulated: bool
    estimated_profit: float
    actual_profit: float
    gas_cost: float
    gas_used: int
    transaction_hash: str
    execution_time: float

class LangChainOrchestrator:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.blockchain_monitor_url = "http://blockchain-monitor:8070"
        self.arbitrage_executor_url = "http://arbitrage-executor:8071"
        
        # Initialize connections
        self.redis_client = redis.from_url(self.redis_url)
        
        # AI decision parameters
        self.min_confidence_threshold = 0.75
        self.max_risk_exposure = 10.0  # ETH
        self.profit_target_multiplier = 2.0
        
        # Performance tracking
        self.performance_metrics = {
            "opportunities_analyzed": 0,
            "opportunities_executed": 0,
            "total_profit": 0.0,
            "success_rate": 0.0,
            "avg_execution_time": 0.0
        }
        
        self.app = FastAPI(title="LangChain Orchestrator", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()
        
    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def setup_routes(self):
        @self.app.get("/health")
        async def health():
            try:
                # Check Redis connection
                self.redis_client.ping()
                
                # Check dependent services
                services_status = await self.check_dependent_services()
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "services": services_status,
                    "performance": self.performance_metrics
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")
        
        @self.app.get("/")
        async def root():
            return {
                "service": "LangChain Orchestrator",
                "version": "1.0.0",
                "description": "AI-driven flash loan arbitrage coordination",
                "endpoints": {
                    "health": "/health",
                    "arbitrage_opportunity": "/arbitrage/opportunity",
                    "execution_result": "/arbitrage/execution_result",
                    "metrics": "/metrics",
                    "gpu_status": "/gpu/status"
                }
            }
        
        @self.app.post("/arbitrage/opportunity")
        async def receive_arbitrage_opportunity(
            opportunity: ArbitrageOpportunity,
            background_tasks: BackgroundTasks
        ):
            """Receive and analyze arbitrage opportunity from blockchain monitor"""
            try:
                logger.info(f"Received arbitrage opportunity: {opportunity.type}")
                
                # Update metrics
                self.performance_metrics["opportunities_analyzed"] += 1
                
                # Analyze opportunity with AI
                analysis = await self.analyze_opportunity_with_ai(opportunity.dict())
                
                # Make execution decision
                if analysis["should_execute"]:
                    background_tasks.add_task(self.coordinate_execution, opportunity.dict(), analysis)
                    
                return {
                    "status": "received",
                    "analysis": analysis,
                    "will_execute": analysis["should_execute"]
                }
                
            except Exception as e:
                logger.error(f"Error processing arbitrage opportunity: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/arbitrage/execution_result")
        async def receive_execution_result(result: Dict[str, Any]):
            """Receive execution result from arbitrage executor"""
            try:
                logger.info(f"Received execution result: {result.get('execution_result', {}).get('success', False)}")
                
                # Update performance metrics
                await self.update_performance_metrics(result)
                
                # Store result for analysis
                await self.store_execution_result(result)
                
                # Learn from the result
                await self.learn_from_execution(result)
                
                return {"status": "processed"}
                
            except Exception as e:
                logger.error(f"Error processing execution result: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/generate")
        async def generate_response(request: Dict[str, Any]):
            """Generate AI response (for compatibility)"""
            try:
                # Mock AI response for demonstration
                response = {
                    "response": "AI analysis complete",
                    "confidence": 0.85,
                    "recommendations": [
                        "Monitor gas prices",
                        "Increase profit threshold",
                        "Diversify DEX coverage"
                    ]
                }
                return response
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/embeddings")
        async def generate_embeddings(request: Dict[str, Any]):
            """Generate embeddings (for compatibility)"""
            try:
                # Mock embeddings response
                text = request.get("text", "")
                # Simulate embedding vector
                embedding = np.random.randn(384).tolist()  # 384-dimensional embedding
                
                return {
                    "embedding": embedding,
                    "model": "mock-embedding-model",
                    "tokens": len(text.split())
                }
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/gpu/status")
        async def gpu_status():
            """Get GPU status (mock for compatibility)"""
            return {
                "gpu_available": True,
                "gpu_count": 2,
                "gpu_memory": "32GB",
                "utilization": "45%"
            }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get orchestrator metrics"""
            try:
                # Get additional metrics from Redis
                redis_metrics = {
                    "opportunities_in_queue": self.redis_client.llen("arbitrage_queue"),
                    "active_executions": self.redis_client.scard("active_executions"),
                    "total_volume": float(self.redis_client.get("total_volume") or 0)
                }
                
                return {
                    **self.performance_metrics,
                    **redis_metrics,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def check_dependent_services(self) -> Dict[str, str]:
        """Check status of dependent services"""
        services = {}
        
        # Check blockchain monitor
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.blockchain_monitor_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    services["blockchain_monitor"] = "healthy" if response.status == 200 else "unhealthy"
        except:
            services["blockchain_monitor"] = "unhealthy"
        
        # Check arbitrage executor
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.arbitrage_executor_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    services["arbitrage_executor"] = "healthy" if response.status == 200 else "unhealthy"
        except:
            services["arbitrage_executor"] = "unhealthy"
        
        return services
    
    async def analyze_opportunity_with_ai(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze arbitrage opportunity using AI decision making"""
        try:
            # Extract key metrics
            estimated_profit = opportunity["estimated_profit"]
            confidence = opportunity["confidence"]
            token_pair = opportunity.get("token_pair", "unknown")
            
            # AI-driven analysis factors
            analysis = {
                "profit_score": self.calculate_profit_score(estimated_profit),
                "confidence_score": confidence,
                "market_conditions": await self.assess_market_conditions(),
                "risk_assessment": await self.assess_risk(opportunity),
                "timing_score": self.calculate_timing_score(opportunity)
            }
            
            # Combined decision score
            decision_score = (
                analysis["profit_score"] * 0.3 +
                analysis["confidence_score"] * 0.25 +
                analysis["market_conditions"] * 0.2 +
                (1 - analysis["risk_assessment"]) * 0.15 +
                analysis["timing_score"] * 0.1
            )
            
            # Decision threshold
            should_execute = (
                decision_score > 0.7 and
                confidence > self.min_confidence_threshold and
                estimated_profit > 0.002  # 0.2% minimum
            )
            
            analysis.update({
                "decision_score": decision_score,
                "should_execute": should_execute,
                "reasoning": self.generate_reasoning(analysis, should_execute),
                "recommended_amount": self.calculate_recommended_amount(opportunity, analysis)
            })
            
            logger.info(f"AI Analysis complete: Score={decision_score:.3f}, Execute={should_execute}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {
                "decision_score": 0.0,
                "should_execute": False,
                "error": str(e)
            }
    
    def calculate_profit_score(self, estimated_profit: float) -> float:
        """Calculate profit score (0-1)"""
        # Normalize profit score (sigmoid-like function)
        return min(1.0, estimated_profit / 0.01)  # 1% profit = max score
    
    async def assess_market_conditions(self) -> float:
        """Assess current market conditions (0-1 score)"""
        try:
            # Mock market condition assessment
            # In production, this would analyze various market indicators
            
            # Check recent execution success rate
            recent_successes = int(self.redis_client.get("recent_successes") or 0)
            recent_attempts = int(self.redis_client.get("recent_attempts") or 1)
            success_rate = recent_successes / recent_attempts
            
            # Check current gas price trends
            current_gas = int(self.redis_client.get("current_gas_price") or 50)
            gas_score = max(0, 1 - (current_gas - 20) / 180)  # Lower gas = better
            
            # Combine factors
            market_score = (success_rate * 0.7 + gas_score * 0.3)
            return min(1.0, max(0.0, market_score))
            
        except Exception as e:
            logger.error(f"Error assessing market conditions: {e}")
            return 0.5  # Neutral score on error
    
    async def assess_risk(self, opportunity: Dict[str, Any]) -> float:
        """Assess risk level (0-1, where 1 is highest risk)"""
        try:
            risk_factors = []
            
            # Gas price risk
            gas_price = opportunity.get("gas_price", 50)
            gas_risk = min(1.0, (gas_price - 20) / 180)  # Higher gas = higher risk
            risk_factors.append(gas_risk)
            
            # Profit margin risk
            profit_margin = opportunity["estimated_profit"]
            margin_risk = max(0, 1 - profit_margin / 0.005)  # Lower margin = higher risk
            risk_factors.append(margin_risk)
            
            # Token pair risk (some pairs are more volatile)
            token_pair = opportunity.get("token_pair", "")
            pair_risk = 0.3 if "USDT" in token_pair else 0.2  # USDT pairs slightly riskier
            risk_factors.append(pair_risk)
            
            # Time-based risk (older opportunities are riskier)
            timestamp = datetime.fromisoformat(opportunity["timestamp"].replace("Z", "+00:00"))
            age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
            age_risk = min(1.0, age_seconds / 300)  # 5 minutes = max age risk
            risk_factors.append(age_risk)
            
            # Average risk
            overall_risk = np.mean(risk_factors)
            return min(1.0, max(0.0, overall_risk))
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return 0.8  # High risk on error (conservative)
    
    def calculate_timing_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate timing score based on opportunity freshness"""
        try:
            timestamp = datetime.fromisoformat(opportunity["timestamp"].replace("Z", "+00:00"))
            age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
            
            # Fresh opportunities get higher scores
            if age_seconds < 10:
                return 1.0
            elif age_seconds < 30:
                return 0.8
            elif age_seconds < 60:
                return 0.5
            elif age_seconds < 120:
                return 0.2
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating timing score: {e}")
            return 0.0
    
    def generate_reasoning(self, analysis: Dict[str, Any], should_execute: bool) -> str:
        """Generate human-readable reasoning for the decision"""
        if should_execute:
            return f"Execute: High decision score ({analysis['decision_score']:.3f}) with good profit potential and acceptable risk"
        else:
            factors = []
            if analysis["profit_score"] < 0.5:
                factors.append("low profit potential")
            if analysis["confidence_score"] < 0.7:
                factors.append("low confidence")
            if analysis["risk_assessment"] > 0.7:
                factors.append("high risk")
            
            return f"Skip: {', '.join(factors) if factors else 'insufficient decision score'}"
    
    def calculate_recommended_amount(self, opportunity: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Calculate recommended flash loan amount"""
        base_amount = 1.0  # 1 ETH base
        
        # Adjust based on profit potential
        profit_multiplier = min(2.0, 1 + analysis["profit_score"])
        
        # Adjust based on confidence
        confidence_multiplier = analysis["confidence_score"]
        
        # Adjust based on risk
        risk_multiplier = 1 - (analysis["risk_assessment"] * 0.5)
        
        recommended = base_amount * profit_multiplier * confidence_multiplier * risk_multiplier
        return max(0.1, min(5.0, recommended))  # Between 0.1 and 5 ETH
    
    async def coordinate_execution(self, opportunity: Dict[str, Any], analysis: Dict[str, Any]):
        """Coordinate execution of arbitrage opportunity"""
        try:
            logger.info(f"Coordinating execution for opportunity: {opportunity.get('type', 'unknown')}")
            
            # Mark as active execution
            execution_id = f"exec_{datetime.now(timezone.utc).isoformat()}"
            self.redis_client.sadd("active_executions", execution_id)
            
            # Send to arbitrage executor
            execution_request = {
                **opportunity,
                "analysis": analysis,
                "execution_id": execution_id,
                "recommended_amount": analysis.get("recommended_amount", 1.0)
            }
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.arbitrage_executor_url}/execute",
                        json=execution_request,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Execution request sent successfully: {execution_id}")
                            self.performance_metrics["opportunities_executed"] += 1
                        else:
                            logger.error(f"Execution request failed: {response.status}")
                except Exception as e:
                    logger.error(f"Error sending execution request: {e}")
            
            # Clean up active execution
            self.redis_client.srem("active_executions", execution_id)
            
        except Exception as e:
            logger.error(f"Error coordinating execution: {e}")
    
    async def update_performance_metrics(self, result: Dict[str, Any]):
        """Update performance metrics based on execution result"""
        try:
            execution_result = result.get("execution_result", {})
            
            if execution_result.get("success"):
                profit = execution_result.get("actual_profit", 0)
                self.performance_metrics["total_profit"] += profit
                
                # Update success rate
                current_executed = self.performance_metrics["opportunities_executed"]
                if current_executed > 0:
                    successful = int(self.performance_metrics["success_rate"] * current_executed)
                    successful += 1
                    self.performance_metrics["success_rate"] = successful / current_executed
            
            # Update average execution time
            exec_time = execution_result.get("execution_time", 0)
            current_avg = self.performance_metrics["avg_execution_time"]
            current_count = self.performance_metrics["opportunities_executed"]
            
            if current_count > 0:
                new_avg = ((current_avg * (current_count - 1)) + exec_time) / current_count
                self.performance_metrics["avg_execution_time"] = new_avg
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def store_execution_result(self, result: Dict[str, Any]):
        """Store execution result for historical analysis"""
        try:
            # Store in Redis with TTL
            result_key = f"execution_history:{datetime.now(timezone.utc).isoformat()}"
            self.redis_client.setex(result_key, 86400, json.dumps(result))  # 24-hour TTL
            
            # Update aggregate statistics
            execution_result = result.get("execution_result", {})
            if execution_result.get("success"):
                self.redis_client.incr("recent_successes")
            self.redis_client.incr("recent_attempts")
            
            # Expire counters after 1 hour to keep them recent
            self.redis_client.expire("recent_successes", 3600)
            self.redis_client.expire("recent_attempts", 3600)
            
        except Exception as e:
            logger.error(f"Error storing execution result: {e}")
    
    async def learn_from_execution(self, result: Dict[str, Any]):
        """Learn from execution results to improve future decisions"""
        try:
            opportunity = result.get("opportunity", {})
            execution_result = result.get("execution_result", {})
            
            # Extract learning data
            predicted_profit = opportunity.get("estimated_profit", 0)
            actual_profit = execution_result.get("actual_profit", 0)
            confidence = opportunity.get("confidence", 0)
            success = execution_result.get("success", False)
            
            # Calculate prediction accuracy
            if predicted_profit > 0:
                profit_accuracy = min(1.0, actual_profit / predicted_profit) if success else 0.0
                
                # Store learning data
                learning_data = {
                    "predicted_profit": predicted_profit,
                    "actual_profit": actual_profit,
                    "confidence": confidence,
                    "success": success,
                    "profit_accuracy": profit_accuracy,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Store for future model training
                learning_key = f"learning_data:{datetime.now(timezone.utc).isoformat()}"
                self.redis_client.setex(learning_key, 604800, json.dumps(learning_data))  # 7-day TTL
                
                logger.info(f"Learning data stored: accuracy={profit_accuracy:.3f}")
                
        except Exception as e:
            logger.error(f"Error in learning process: {e}")

# Global orchestrator instance
orchestrator = LangChainOrchestrator()

async def startup_event():
    """Initialize orchestrator on startup"""
    logger.info("LangChain Orchestrator starting up...")
    
    # Initialize Redis connections
    try:
        orchestrator.redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

orchestrator.app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    logger.info("Starting Enhanced LangChain Orchestrator...")
    uvicorn.run(
        orchestrator.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 