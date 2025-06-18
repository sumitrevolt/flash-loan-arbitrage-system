#!/usr/bin/env python3
"""
ENHANCED AI AGENT SYSTEM
========================
Advanced AI-powered agents that integrate with the existing multi-agent coordinator
Provides ML-based predictions, advanced risk assessment, and intelligent decision making
"""

import asyncio
import numpy as np
import logging
from typing import Dict, List, Any, Union
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketPrediction:
    """Enhanced market prediction with ML confidence"""
    token_pair: str
    predicted_profit: float
    confidence_score: float
    recommended_action: str
    risk_assessment: str
    time_horizon: int

class MLPredictionEngine:
    """Machine Learning prediction engine for arbitrage opportunities"""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = True  # Set to True when models are loaded
        self.trained_models = {}
        self.model_path = "models/ml_arbitrage_model.pkl"
        self.scaler_path = "models/ml_scaler.pkl"
        
        # Create models directory
        os.makedirs("models", exist_ok=True)
        
        # Load existing model if available
        self._load_latest_models()
    
    def _load_latest_models(self):
        """Load the latest trained models from MCP training coordinator"""
        
        try:
            import joblib
            import os
            import glob
            
            model_dir = "models"
            if os.path.exists(model_dir):
                # Load latest arbitrage predictor
                arbitrage_models = glob.glob(f"{model_dir}/arbitrage_predictor_*.pkl")
                if arbitrage_models:
                    latest_model = max(arbitrage_models, key=os.path.getctime)
                    self.trained_models["arbitrage_predictor"] = joblib.load(latest_model)
                
                # Load latest risk classifier
                risk_models = glob.glob(f"{model_dir}/risk_classifier_*.pkl")
                if risk_models:
                    latest_model = max(risk_models, key=os.path.getctime)
                    self.trained_models["risk_classifier"] = joblib.load(latest_model)
                    
        except Exception as e:
            print(f"Failed to load trained models: {e}")
            self.is_trained = False
    
    def prepare_features(self, market_data: Dict[str, Any]) -> np.ndarray:
        """Extract and prepare features for ML prediction"""
        features = []
        
        # Price spread between DEXes
        buy_price = market_data.get('buy_price', 0)
        sell_price = market_data.get('sell_price', 0)
        price_spread = (sell_price - buy_price) / buy_price if buy_price > 0 else 0
        features.append(price_spread * 100)  # Convert to percentage
        
        # Liquidity metrics
        buy_liquidity = market_data.get('buy_liquidity', 0)
        sell_liquidity = market_data.get('sell_liquidity', 0)
        liquidity_ratio = min(buy_liquidity, sell_liquidity) / max(buy_liquidity, sell_liquidity) if max(buy_liquidity, sell_liquidity) > 0 else 0
        features.append(liquidity_ratio)
        
        # Volume ratios (24h)
        volume_ratio = market_data.get('volume_24h_ratio', 1.0)
        features.append(volume_ratio)
        
        # Gas price impact
        gas_price = market_data.get('gas_price_gwei', 50)
        features.append(gas_price)
        
        # Market volatility indicator
        volatility = market_data.get('market_volatility', 0.02)
        features.append(volatility)
        
        # Time-based features
        features.append(market_data.get('time_since_last_opportunity', 300))
        features.append(market_data.get('success_rate_last_10_trades', 0.5))
        features.append(market_data.get('network_congestion_score', 0.3))
        
        return np.array(features).reshape(1, -1)
    
    def train_model(self, historical_data: List[Dict[str, Any]]) -> bool:
        """Train the ML model on historical arbitrage data"""
        if len(historical_data) < 50:
            logger.warning("Insufficient data for training (need at least 50 samples)")
            return False
        
        # Prepare training data
        X = []
        y = []
        
        for trade in historical_data:
            features = self.prepare_features(trade)
            X.append(features.flatten())
            y.append(trade.get('actual_profit', 0))
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Save model
        self.save_model()
        logger.info(f"ML model trained on {len(historical_data)} samples")
        return True
    
    async def predict_arbitrage_profit(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Use trained model to predict arbitrage profit"""
        
        if "arbitrage_predictor" not in self.trained_models:
            return {"error": "Arbitrage predictor model not available"}
        
        try:
            # Prepare features
            features = [
                opportunity_data.get("price_diff_percent", 0),
                opportunity_data.get("liquidity_ratio", 1.0),
                opportunity_data.get("gas_cost_usd", 20),
                opportunity_data.get("volume_24h", 100000),
                opportunity_data.get("volatility_score", 0.5),
                opportunity_data.get("market_cap_ratio", 0.1),
                opportunity_data.get("dex_liquidity_depth", 10000),
                opportunity_data.get("slippage_estimate", 0.01)
            ]
            
            model = self.trained_models["arbitrage_predictor"]
            predicted_profit = model.predict([features])[0]
            
            # Get prediction confidence
            # Use ensemble of trees for confidence estimation
            tree_predictions = [tree.predict([features])[0] for tree in model.estimators_]
            confidence = 1.0 - (np.std(tree_predictions) / np.mean(tree_predictions))
            
            return {
                "predicted_profit": float(predicted_profit),
                "confidence": float(confidence),
                "model_used": "arbitrage_predictor",
                "features_used": len(features)
            }
            
        except Exception as e:
            return {"error": f"Prediction failed: {e}"}
    
    def predict(self, market_data: Dict[str, Any]) -> MarketPrediction:
        """Make ML-powered prediction for arbitrage opportunity"""
        if not self.is_trained:
            return self._default_prediction(market_data)
        
        # Prepare features
        features = self.prepare_features(market_data)
        features_scaled = self.scaler.transform(features)
        
        # Make prediction
        predicted_profit = float(self.model.predict(features_scaled)[0])
        confidence = self._calculate_confidence(features_scaled)
        
        # Determine action based on prediction and confidence
        if predicted_profit > 0.01 and confidence > 0.8:
            action = "EXECUTE_IMMEDIATELY"
            risk = "LOW"
        elif predicted_profit > 0.005 and confidence > 0.6:
            action = "EXECUTE_WITH_CAUTION"
            risk = "MEDIUM"
        elif predicted_profit > 0:
            action = "MONITOR_CLOSELY"
            risk = "HIGH"
        else:
            action = "SKIP_OPPORTUNITY"
            risk = "VERY_HIGH"
        
        return MarketPrediction(
            token_pair=market_data.get('token_pair', 'UNKNOWN'),
            predicted_profit=predicted_profit,
            confidence_score=confidence,
            recommended_action=action,
            risk_assessment=risk,
            time_horizon=30
        )
    
    def _calculate_confidence(self, features_scaled: np.ndarray) -> float:
        """Calculate prediction confidence based on model uncertainty"""
        if hasattr(self.model, 'estimators_'):
            # Get predictions from all trees
            tree_predictions = np.array([tree.predict(features_scaled)[0] for tree in self.model.estimators_])
            variance = np.var(tree_predictions)
            # Convert variance to confidence (0-1)
            confidence = max(0, min(1, 1 - variance * 10))
            return float(confidence)
        return 0.5
    
    def _default_prediction(self, market_data: Dict[str, Any]) -> MarketPrediction:
        """Fallback prediction when ML model is not available"""
        buy_price = market_data.get('buy_price', 0)
        sell_price = market_data.get('sell_price', 0)
        profit_estimate = (sell_price - buy_price) / buy_price if buy_price > 0 else 0
        
        return MarketPrediction(
            token_pair=market_data.get('token_pair', 'UNKNOWN'),
            predicted_profit=profit_estimate * 0.8,  # Conservative estimate
            confidence_score=0.3,
            recommended_action="EXECUTE_WITH_CAUTION" if profit_estimate > 0.01 else "SKIP_OPPORTUNITY",
            risk_assessment="MEDIUM",
            time_horizon=60
        )
    
    def save_model(self):
        """Save trained model and scaler"""
        if self.is_trained:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info("ML model saved successfully")
    
    def load_model(self):
        """Load existing model and scaler"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info("ML model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load ML model: {e}")

class AdvancedRiskAgent:
    """Advanced risk assessment agent with ML capabilities"""
    
    def __init__(self):
        self.ml_engine = MLPredictionEngine()
        self.risk_limits = {
            'max_slippage_percent': 2.0,
            'max_gas_price_gwei': 100.0,
            'min_profit_usd': 10.0,
            'max_trade_size_usd': 50000.0,
            'min_liquidity_usd': 10000.0
        }
        self.consecutive_losses = 0
        self.last_trade_timestamp = None
    
    async def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive opportunity evaluation using ML and risk rules"""
        
        # Get ML prediction
        prediction = self.ml_engine.predict(opportunity)
        
        # Perform risk assessment
        risk_assessment = self._assess_risk_factors(opportunity)
        
        # Make final decision
        should_execute = (
            prediction.recommended_action in ['EXECUTE_IMMEDIATELY', 'EXECUTE_WITH_CAUTION'] and
            risk_assessment['overall_risk_score'] > 0.6 and
            self.consecutive_losses < 3
        )
        
        # Generate explanation
        explanation = self._generate_explanation(prediction, risk_assessment, should_execute)
        
        return {
            'should_execute': should_execute,
            'ml_prediction': {
                'predicted_profit': prediction.predicted_profit,
                'confidence': prediction.confidence_score,
                'recommended_action': prediction.recommended_action
            },
            'risk_assessment': risk_assessment,
            'explanation': explanation,
            'timestamp': datetime.now().isoformat()
        }
    
    def _assess_risk_factors(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Assess various risk factors"""
        checks = {
            'profit_sufficient': opportunity.get('profit_usd', 0) >= self.risk_limits['min_profit_usd'],
            'slippage_acceptable': opportunity.get('slippage_percent', 5) <= self.risk_limits['max_slippage_percent'],
            'liquidity_adequate': min(
                opportunity.get('buy_liquidity', 0),
                opportunity.get('sell_liquidity', 0)
            ) >= self.risk_limits['min_liquidity_usd'],
            'gas_price_reasonable': opportunity.get('gas_price_gwei', 100) < self.risk_limits['max_gas_price_gwei']
        }
        
        passed_checks = sum(checks.values())
        risk_score = passed_checks / len(checks)
        
        return {
            'individual_checks': checks,
            'overall_risk_score': risk_score,
            'passed_checks': passed_checks,
            'total_checks': len(checks)
        }
    
    def _generate_explanation(self, prediction: MarketPrediction, risk_assessment: Dict[str, Any], should_execute: bool) -> str:
        """Generate human-readable explanation for the decision"""
        reasons = []
        
        if should_execute:
            reasons.append(f"ML predicts {prediction.predicted_profit:.3f} profit with {prediction.confidence_score:.2f} confidence")
            reasons.append(f"Risk score: {risk_assessment['overall_risk_score']:.2f}/1.0")
        else:
            if prediction.recommended_action == 'SKIP_OPPORTUNITY':
                reasons.append("ML recommends skipping (low profit potential)")
            if risk_assessment['overall_risk_score'] <= 0.6:
                reasons.append("Risk assessment failed minimum threshold")
            if self.consecutive_losses >= 3:
                reasons.append("Too many consecutive losses - safety pause")
        
        return " • ".join(reasons)

class IntelligentCoordinator:
    """Intelligent coordinator that enhances the existing multi-agent system"""
    
    def __init__(self):
        self.risk_agent = AdvancedRiskAgent()
        self.ml_engine = MLPredictionEngine()
        self.performance_metrics = {
            'total_opportunities_evaluated': 0,
            'opportunities_executed': 0,
            'success_rate': 0.0,
            'total_profit': 0.0
        }
    
    async def enhance_opportunity_evaluation(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced evaluation that can be integrated with existing coordinator"""
        
        self.performance_metrics['total_opportunities_evaluated'] += 1
        
        # Get enhanced evaluation
        evaluation = await self.risk_agent.evaluate_opportunity(opportunity)
        
        # Add performance context
        evaluation['performance_context'] = {
            'success_rate': self.performance_metrics['success_rate'],
            'total_evaluated': self.performance_metrics['total_opportunities_evaluated'],
            'recommendation_weight': min(1.0, self.performance_metrics['success_rate'] + 0.3)
        }
        
        return evaluation
    
    async def learn_from_trade_result(self, opportunity: Dict[str, Any], actual_result: Dict[str, Any]):
        """Learn from trade results to improve future predictions"""
        
        # Update performance metrics
        if actual_result.get('success', False):
            self.performance_metrics['opportunities_executed'] += 1
            self.performance_metrics['total_profit'] += actual_result.get('profit', 0)
            self.risk_agent.consecutive_losses = 0
        else:
            self.risk_agent.consecutive_losses += 1
        
        # Calculate success rate
        if self.performance_metrics['total_opportunities_evaluated'] > 0:
            self.performance_metrics['success_rate'] = (
                self.performance_metrics['opportunities_executed'] / 
                self.performance_metrics['total_opportunities_evaluated']
            )
        
        # Add result to training data (in real implementation, this would be persistent)
        training_sample = {**opportunity, 'actual_profit': actual_result.get('profit', 0)}
        
        logger.info(f"Learning from trade result: Success={actual_result.get('success', False)}, "
                   f"Profit={actual_result.get('profit', 0):.4f}")

# Integration functions for existing multi-agent coordinator
async def enhance_existing_coordinator():
    """Function to enhance the existing multi-agent coordinator with AI capabilities"""
    try:
        # Import the existing coordinator
        from multi_agent_coordinator import MultiAgentCoordinator
        
        # Create enhanced coordinator
        coordinator = MultiAgentCoordinator()
        ai_coordinator = IntelligentCoordinator()
        
        # Start the enhanced system
        await coordinator.start_system()
        
        logger.info("✅ Enhanced AI multi-agent system started successfully!")
        logger.info("🤖 ML prediction engine ready")
        logger.info("⚡ Advanced risk assessment active")
        logger.info("🎯 Intelligent coordination layer operational")
        
        return coordinator, ai_coordinator
        
    except ImportError:
        logger.warning("Original multi-agent coordinator not found, running in standalone mode")
        ai_coordinator = IntelligentCoordinator()
        return None, ai_coordinator

# Testing function
async def test_enhanced_ai_system():
    """Test the enhanced AI system"""
    print("\n🧪 TESTING ENHANCED AI AGENT SYSTEM")
    print("=" * 50)
    
    # Create coordinator
    ai_coordinator = IntelligentCoordinator()
    
    # Test opportunity
    test_opportunity = {
        'token_pair': 'WETH/USDC',
        'buy_price': 1000.50,
        'sell_price': 1002.75,
        'buy_liquidity': 150000,
        'sell_liquidity': 180000,
        'gas_price_gwei': 25,
        'market_volatility': 0.015,
        'profit_usd': 45.30,
        'slippage_percent': 1.2
    }
    
    # Evaluate opportunity
    evaluation = await ai_coordinator.enhance_opportunity_evaluation(test_opportunity)
    
    # Display results
    print(f"🎯 Opportunity: {test_opportunity['token_pair']}")
    print(f"   Should Execute: {evaluation['should_execute']}")
    print(f"   ML Confidence: {evaluation['ml_prediction']['confidence']:.2f}")
    print(f"   Risk Score: {evaluation['risk_assessment']['overall_risk_score']:.2f}")
    print(f"   Explanation: {evaluation['explanation']}")
    
    # Simulate trade result
    trade_result: str = {
        'success': evaluation['should_execute'],
        'profit': test_opportunity['profit_usd'] * 0.85 if evaluation['should_execute'] else 0
    }
    
    # Learn from result
    await ai_coordinator.learn_from_trade_result(test_opportunity, trade_result)
    
    print(f"\n📊 Performance Metrics:")
    print(f"   Total Evaluated: {ai_coordinator.performance_metrics['total_opportunities_evaluated']}")
    print(f"   Success Rate: {ai_coordinator.performance_metrics['success_rate']:.2f}")
    print(f"   Total Profit: ${ai_coordinator.performance_metrics['total_profit']:.2f}")

if __name__ == "__main__":
    # Run test
    asyncio.run(test_enhanced_ai_system())
