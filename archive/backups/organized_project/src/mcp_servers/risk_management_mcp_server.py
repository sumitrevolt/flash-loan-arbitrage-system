#!/usr/bin/env python3
"""
Risk Management MCP Server
==========================

Risk assessment and management for AAVE flash loan operations.
Evaluates and mitigates risks before execution.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
import pickle
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RiskManagementMCP")

class RiskManagementMCPServer:
    """Risk assessment and management server"""
    
    def __init__(self):
        self.server_name = "risk_management_mcp_server"
        self.port = 8002
        self.running = False
        self.risk_model = None
        
        # Risk thresholds
        self.risk_thresholds = {
            "max_slippage": 0.02,  # 2%
            "max_gas_price_gwei": 100,
            "min_liquidity_usd": 10000,
            "min_confidence_score": 0.6,
            "max_execution_time": 60
        }
        
        # Load trained risk model
        self.load_risk_model()
    
    def load_risk_model(self):
        """Load the trained risk assessment model"""
        try:
            model_path = "models/risk_regressor.pkl"
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.risk_model = pickle.load(f)
                logger.info("Risk assessment model loaded successfully")
            else:
                logger.warning("Risk model not found, using heuristic risk assessment")
        except Exception as e:
            logger.error(f"Error loading risk model: {e}")
    
    def assess_transaction_risk(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for a flash loan transaction"""
        risk_score = 0.0
        risk_factors = []
        
        try:
            # Assess slippage risk
            slippage = transaction_data.get("slippage", 0.0)
            if slippage > self.risk_thresholds["max_slippage"]:
                risk_score += 0.3
                risk_factors.append(f"High slippage: {slippage:.2%}")
            
            # Assess gas price risk
            gas_price_gwei = transaction_data.get("gas_price_gwei", 0)
            if gas_price_gwei > self.risk_thresholds["max_gas_price_gwei"]:
                risk_score += 0.2
                risk_factors.append(f"High gas price: {gas_price_gwei} gwei")
            
            # Assess liquidity risk
            liquidity_usd = transaction_data.get("liquidity_usd", 0)
            if liquidity_usd < self.risk_thresholds["min_liquidity_usd"]:
                risk_score += 0.25
                risk_factors.append(f"Low liquidity: ${liquidity_usd:,}")
            
            # Assess profit confidence
            confidence = transaction_data.get("confidence_score", 0.0)
            if confidence < self.risk_thresholds["min_confidence_score"]:
                risk_score += 0.15
                risk_factors.append(f"Low confidence: {confidence:.2f}")
            
            # Assess execution time
            execution_time = transaction_data.get("estimated_execution_time", 0)
            if execution_time > self.risk_thresholds["max_execution_time"]:
                risk_score += 0.1
                risk_factors.append(f"Long execution time: {execution_time}s")
            
            # Use ML model if available
            if self.risk_model:
                try:
                    # Prepare features for model
                    features = [
                        slippage,
                        gas_price_gwei / 100,  # Normalize
                        liquidity_usd / 100000,  # Normalize
                        confidence,
                        execution_time / 60  # Normalize
                    ]
                    
                    # Pad features to match training data
                    while len(features) < 26:  # Match training feature count
                        features.append(0.0)
                    
                    ml_risk = self.risk_model.predict([features])[0]
                    risk_score = (risk_score + ml_risk) / 2  # Combine heuristic and ML
                    
                except Exception as e:
                    logger.warning(f"ML risk assessment failed: {e}")
            
            # Determine risk level
            if risk_score < 0.3:
                risk_level = "LOW"
            elif risk_score < 0.6:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            # Determine if transaction should be approved
            approved = risk_score < 0.6 and len(risk_factors) < 3
            
            return {
                "risk_score": round(risk_score, 3),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "approved": approved,
                "timestamp": datetime.now().isoformat(),
                "recommendations": self.get_risk_recommendations(risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {
                "error": str(e),
                "risk_score": 1.0,  # Maximum risk on error
                "approved": False
            }
    
    def get_risk_recommendations(self, risk_factors: list) -> list:
        """Get recommendations based on risk factors"""
        recommendations = []
        
        for factor in risk_factors:
            if "slippage" in factor.lower():
                recommendations.append("Consider using multiple smaller transactions")
            elif "gas" in factor.lower():
                recommendations.append("Wait for lower gas prices or use flashloan gas optimization")
            elif "liquidity" in factor.lower():
                recommendations.append("Use multiple DEXs or wait for better liquidity")
            elif "confidence" in factor.lower():
                recommendations.append("Wait for better price confirmation")
            elif "execution" in factor.lower():
                recommendations.append("Optimize transaction routing")
        
        if not recommendations:
            recommendations.append("Transaction appears safe to execute")
        
        return recommendations
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        try:
            if method == "assess_risk":
                transaction_data = params.get("transaction_data", {})
                return self.assess_transaction_risk(transaction_data)
                
            elif method == "get_risk_thresholds":
                return {
                    "thresholds": self.risk_thresholds,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif method == "update_risk_thresholds":
                new_thresholds = params.get("thresholds", {})
                self.risk_thresholds.update(new_thresholds)
                return {
                    "status": "updated",
                    "thresholds": self.risk_thresholds
                }
                
            elif method == "health_check":
                return {
                    "status": "healthy",
                    "server": self.server_name,
                    "timestamp": datetime.now().isoformat(),
                    "model_loaded": self.risk_model is not None,
                    "risk_thresholds": self.risk_thresholds
                }
                
            else:
                return {"error": f"Unknown method: {method}"}
                
        except Exception as e:
            logger.error(f"Error handling request {method}: {e}")
            return {"error": str(e)}
    
    async def start_server(self):
        """Start the MCP server"""
        self.running = True
        logger.info(f"Starting {self.server_name} on port {self.port}")
        
        try:
            while self.running:
                # Periodic risk monitoring
                await asyncio.sleep(60)  # Monitor every minute
                logger.info(f"{self.server_name} monitoring - Risk model: {'✅' if self.risk_model else '❌'}")
                
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            logger.info(f"{self.server_name} shutting down")
    
    def stop_server(self):
        """Stop the MCP server"""
        self.running = False

async def main():
    """Main server function"""
    server = RiskManagementMCPServer()
    
    try:
        logger.info("=" * 50)
        logger.info("RISK MANAGEMENT MCP SERVER")
        logger.info("=" * 50)
        logger.info("Advanced risk assessment for AAVE flash loans")
        logger.info("ML-powered risk scoring and recommendations")
        logger.info("=" * 50)
        
        await server.start_server()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        server.stop_server()
    except Exception as e:
        logger.error(f"Server startup error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
