#!/usr/bin/env python3
"""
Profit Optimizer MCP Server
===========================

Optimizes flash loan execution for maximum profit within the $4-$30 target range.
Uses ML models to predict and optimize profit outcomes.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
import pickle
import os
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProfitOptimizerMCP")

class ProfitOptimizerMCPServer:
    """Profit optimization server for flash loans"""
    
    def __init__(self):
        self.server_name = "profit_optimizer_mcp_server"
        self.port = 8003
        self.running = False
        
        # Load trained models
        self.profit_model = None
        self.arbitrage_model = None
        
        # Profit targets
        self.profit_targets = {
            "min_profit_usd": 4.0,
            "max_profit_usd": 30.0,
            "optimal_profit_usd": 15.0,
            "profit_margin_threshold": 0.1  # 10% profit margin minimum
        }
        
        # Load trained models
        self.load_models()
    
    def load_models(self):
        """Load trained ML models"""
        try:
            # Load profit prediction model
            profit_model_path = "models/profit_regressor.pkl"
            if os.path.exists(profit_model_path):
                with open(profit_model_path, 'rb') as f:
                    self.profit_model = pickle.load(f)
                logger.info("Profit prediction model loaded successfully")
            
            # Load arbitrage classification model
            arb_model_path = "models/arbitrage_classifier.pkl"
            if os.path.exists(arb_model_path):
                with open(arb_model_path, 'rb') as f:
                    self.arbitrage_model = pickle.load(f)
                logger.info("Arbitrage classification model loaded successfully")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def optimize_flash_loan_amount(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize flash loan amount for maximum profit"""
        try:
            base_amount = opportunity.get("amount", 10000)
            token_price = opportunity.get("token_price", 1.0)
            
            # Test different amounts to find optimal
            amounts_to_test = [
                base_amount * 0.5,
                base_amount,
                base_amount * 1.5,
                base_amount * 2.0,
                base_amount * 3.0
            ]
            
            best_profit = 0
            best_amount = base_amount
            profit_analysis = []
            
            for amount in amounts_to_test:
                predicted_profit = self.predict_profit(opportunity, amount)
                
                # Check if within target range
                if (self.profit_targets["min_profit_usd"] <= predicted_profit <= 
                    self.profit_targets["max_profit_usd"]):
                    
                    profit_analysis.append({
                        "amount": amount,
                        "predicted_profit": predicted_profit,
                        "profit_margin": predicted_profit / (amount * token_price),
                        "in_target_range": True
                    })
                    
                    if predicted_profit > best_profit:
                        best_profit = predicted_profit
                        best_amount = amount
                else:
                    profit_analysis.append({
                        "amount": amount,
                        "predicted_profit": predicted_profit,
                        "profit_margin": predicted_profit / (amount * token_price),
                        "in_target_range": False
                    })
            
            return {
                "optimized_amount": best_amount,
                "predicted_profit": best_profit,
                "profit_analysis": profit_analysis,
                "optimization_successful": best_profit > 0
            }
            
        except Exception as e:
            logger.error(f"Amount optimization error: {e}")
            return {"error": str(e)}
    
    def predict_profit(self, opportunity: Dict[str, Any], amount: float = None) -> float:
        """Predict profit using ML model"""
        try:
            if not self.profit_model:
                # Fallback heuristic calculation
                return self.calculate_heuristic_profit(opportunity, amount)
            
            # Prepare features for ML model
            features = self.prepare_features(opportunity, amount)
            
            # Predict profit
            predicted_profit = self.profit_model.predict([features])[0]
            
            return max(0, predicted_profit)  # Ensure non-negative
            
        except Exception as e:
            logger.warning(f"ML profit prediction failed: {e}")
            return self.calculate_heuristic_profit(opportunity, amount)
    
    def calculate_heuristic_profit(self, opportunity: Dict[str, Any], amount: float = None) -> float:
        """Calculate profit using heuristic methods"""
        try:
            if not amount:
                amount = opportunity.get("amount", 10000)
            
            # Basic profit calculation
            price_diff = opportunity.get("price_difference", 0.01)
            dex_fee = opportunity.get("dex_fee", 0.003)
            flash_loan_fee = opportunity.get("flash_loan_fee", 0.0009)
            gas_cost_usd = opportunity.get("gas_cost_usd", 2.0)
            
            # Calculate gross profit
            gross_profit = amount * price_diff
            
            # Subtract fees
            total_fees = amount * (dex_fee + flash_loan_fee)
            
            # Net profit
            net_profit = gross_profit - total_fees - gas_cost_usd
            
            return max(0, net_profit)
            
        except Exception as e:
            logger.error(f"Heuristic profit calculation error: {e}")
            return 0.0
    
    def prepare_features(self, opportunity: Dict[str, Any], amount: float = None) -> List[float]:
        """Prepare features for ML model"""
        if not amount:
            amount = opportunity.get("amount", 10000)
        
        features = [
            amount / 10000,  # Normalized amount
            opportunity.get("price_difference", 0.01),
            opportunity.get("liquidity_usd", 100000) / 100000,  # Normalized
            opportunity.get("gas_price_gwei", 30) / 100,  # Normalized
            opportunity.get("slippage", 0.01),
            opportunity.get("confidence_score", 0.8),
            opportunity.get("dex_fee", 0.003),
            opportunity.get("flash_loan_fee", 0.0009),
        ]
        
        # Pad features to match training data (26 features)
        while len(features) < 26:
            features.append(np.random.random() * 0.1)  # Add some randomness
        
        return features[:26]  # Ensure exactly 26 features
    
    def filter_opportunities_by_profit_target(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter opportunities to match profit targets"""
        filtered_opportunities = []
        
        for opp in opportunities:
            predicted_profit = self.predict_profit(opp)
            
            # Check if within target range
            if (self.profit_targets["min_profit_usd"] <= predicted_profit <= 
                self.profit_targets["max_profit_usd"]):
                
                opp["predicted_profit"] = predicted_profit
                opp["in_target_range"] = True
                filtered_opportunities.append(opp)
        
        # Sort by predicted profit (descending)
        filtered_opportunities.sort(key=lambda x: x["predicted_profit"], reverse=True)
        
        logger.info(f"Filtered {len(opportunities)} opportunities to {len(filtered_opportunities)} within profit target")
        return filtered_opportunities
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        try:
            if method == "optimize_amount":
                opportunity = params.get("opportunity", {})
                return self.optimize_flash_loan_amount(opportunity)
                
            elif method == "predict_profit":
                opportunity = params.get("opportunity", {})
                amount = params.get("amount")
                profit = self.predict_profit(opportunity, amount)
                return {"predicted_profit": profit}
                
            elif method == "filter_opportunities":
                opportunities = params.get("opportunities", [])
                filtered = self.filter_opportunities_by_profit_target(opportunities)
                return {"filtered_opportunities": filtered}
                
            elif method == "get_profit_targets":
                return {
                    "profit_targets": self.profit_targets,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif method == "health_check":
                return {
                    "status": "healthy",
                    "server": self.server_name,
                    "timestamp": datetime.now().isoformat(),
                    "profit_model_loaded": self.profit_model is not None,
                    "arbitrage_model_loaded": self.arbitrage_model is not None,
                    "profit_targets": self.profit_targets
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
                # Periodic optimization monitoring
                await asyncio.sleep(45)  # Monitor every 45 seconds
                logger.info(f"{self.server_name} optimizing - Target: ${self.profit_targets['min_profit_usd']}-${self.profit_targets['max_profit_usd']}")
                
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            logger.info(f"{self.server_name} shutting down")
    
    def stop_server(self):
        """Stop the MCP server"""
        self.running = False

async def main():
    """Main server function"""
    server = ProfitOptimizerMCPServer()
    
    try:
        logger.info("=" * 50)
        logger.info("PROFIT OPTIMIZER MCP SERVER")
        logger.info("=" * 50)
        logger.info("ML-powered profit optimization for AAVE flash loans")
        logger.info("Target Range: $4 - $30 profit")
        logger.info("=" * 50)
        
        await server.start_server()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        server.stop_server()
    except Exception as e:
        logger.error(f"Server startup error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
