#!/usr/bin/env python3
"""
ADVANCED AI AGENT IMPROVEMENTS
==============================
Enhance the multi-agent system with machine learning and advanced decision-making
Integrates with the existing multi-agent coordinator for seamless operation
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, cast
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import logging
from numpy.typing import NDArray   # typed ndarray support

@dataclass
class MarketPrediction:
    """Market prediction result"""
    token_pair: str
    predicted_profit: float
    confidence_score: float
    recommended_action: str
    risk_assessment: str
    time_horizon: int  # seconds

class MLArbitragePredictor:
    """Machine learning model for arbitrage prediction"""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'price_spread_percentage',
            'liquidity_ratio',
            'volume_24h_ratio',
            'gas_price_gwei',
            'market_volatility',
            'time_since_last_opportunity',
            'success_rate_last_10_trades',
            'network_congestion_score'
        ]
    
    def prepare_features(self, market_data: Dict[str, Any]) -> NDArray[np.float64]:
        """Prepare features for ML model"""
        # Explicitly type the list to avoid “Unknown” diagnostics.
        features: list[float] = []

        # Price spread between DEXes
        buy_price = market_data.get('buy_price', 0)
        sell_price = market_data.get('sell_price', 0)
        price_spread = (sell_price - buy_price) / buy_price if buy_price > 0 else 0
        features.append(price_spread * 100)  # Convert to percentage
        
        # Liquidity ratio (sell_liquidity / buy_liquidity)
        buy_liquidity = market_data.get('buy_liquidity', 1)
        sell_liquidity = market_data.get('sell_liquidity', 1)
        liquidity_ratio = sell_liquidity / buy_liquidity if buy_liquidity > 0 else 1
        features.append(liquidity_ratio)
        
        # Volume ratio
        buy_volume = market_data.get('buy_volume_24h', 1)
        sell_volume = market_data.get('sell_volume_24h', 1)
        volume_ratio = sell_volume / buy_volume if buy_volume > 0 else 1
        features.append(volume_ratio)
        
        # Market conditions
        features.append(market_data.get('gas_price_gwei', 20))
        features.append(market_data.get('market_volatility', 0.02))
        features.append(market_data.get('time_since_last_opportunity', 60))
        features.append(market_data.get('success_rate_last_10', 0.8))
        features.append(market_data.get('network_congestion', 0.5))
        
        return np.array(features).reshape(1, -1)

    def train_model(self, historical_data: List[Dict[str, Any]]):
        """Train the ML model on historical arbitrage data"""
        if len(historical_data) < 50:
            logging.warning("Insufficient data for training (need at least 50 samples)")
            return False

        # Prepare training data
        x_data: list[list[float]] = []
        y_data: list[float] = []
        
        for trade in historical_data:
            features = self.prepare_features(trade['market_data'])
            x_data.append(features.flatten().tolist())
            y_data.append(float(trade['actual_profit_percentage']))
        
        X = np.array(x_data, dtype=float)
        y = np.array(y_data, dtype=float)
        
        # Scale features
        # Cast because sklearn stubs return ndarray[Any, Any]
        X_scaled: NDArray[np.float64] = cast(
            NDArray[np.float64],
            self.scaler.fit_transform(X)  # type: ignore[reportUnknownMemberType]
        )
        
        # Train model
        self.model.fit(X_scaled, y)  # type: ignore[reportUnknownMemberType]
        self.is_trained = True
        
        # Save model
        self.save_model()
        
        logging.info(f"ML model trained on {len(historical_data)} samples")
        return True
    
    def predict_profitability(self, market_data: Dict[str, Any]) -> MarketPrediction:
        """Predict profitability of an arbitrage opportunity"""
        if not self.is_trained:
            # Load pre-trained model or return default prediction
            if not self.load_model():
                return self._default_prediction(market_data)
        
        # Prepare features
        features = self.prepare_features(market_data)
        features_scaled: NDArray[np.float64] = cast(
            NDArray[np.float64],
            self.scaler.transform(features)  # type: ignore[reportUnknownMemberType]
        )
        
        # Make prediction
        predicted_profit = self.model.predict(features_scaled)[0]  # type: ignore[reportUnknownMemberType]
        
        # Calculate confidence score based on feature importance
        confidence = self._calculate_confidence(features_scaled)
        
        # Determine recommended action
        action = self._determine_action(predicted_profit, confidence)
        
        # Assess risk
        risk = self._assess_risk(predicted_profit, confidence, market_data)
        
        return MarketPrediction(
            token_pair=market_data.get('token_pair', 'UNKNOWN'),
            predicted_profit=predicted_profit,
            confidence_score=confidence,
            recommended_action=action,
            risk_assessment=risk,
            time_horizon=30  # 30 seconds prediction horizon
        )
    
    def _calculate_confidence(self, features: NDArray[np.float64]) -> float:
        """Calculate confidence score based on model uncertainty"""
        # Use ensemble variance as uncertainty measure
        if hasattr(self.model, 'estimators_'):
            predictions = [tree.predict(features)[0] for tree in self.model.estimators_]  # type: ignore[reportUnknownMemberType]
            variance = float(np.var(predictions))
            # Convert variance to confidence (0-1 scale)
            confidence: float = max(0.0, min(1.0, 1.0 - variance * 10.0))
        else:
            confidence = 0.5  # Default confidence
        return confidence
    
    def _determine_action(self, predicted_profit: float, confidence: float) -> str:
        """Determine recommended action based on prediction"""
        if predicted_profit > 0.01 and confidence > 0.8:
            return "EXECUTE_IMMEDIATELY"
        elif predicted_profit > 0.005 and confidence > 0.6:
            return "EXECUTE_WITH_CAUTION"
        elif predicted_profit > 0:
            return "MONITOR_CLOSELY"
        else:
            return "SKIP_OPPORTUNITY"
    
    def _assess_risk(self, predicted_profit: float, confidence: float, market_data: Dict[str, Any]) -> str:
        """Assess risk level of the opportunity"""
        risk_score = 0
        
        # Low confidence increases risk
        if confidence < 0.5:
            risk_score += 2
        elif confidence < 0.7:
            risk_score += 1
        
        # High gas prices increase risk
        gas_price = market_data.get('gas_price_gwei', 20)
        if gas_price > 50:
            risk_score += 2
        elif gas_price > 30:
            risk_score += 1
        
        # Low liquidity increases risk
        min_liquidity = min(
            market_data.get('buy_liquidity', 0),
            market_data.get('sell_liquidity', 0)
        )
        if min_liquidity < 10000:
            risk_score += 2
        elif min_liquidity < 50000:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _default_prediction(self, market_data: Dict[str, Any]) -> MarketPrediction:
        """Return default prediction when model is not available"""
        # Simple heuristic-based prediction
        buy_price = market_data.get('buy_price', 0)
        sell_price = market_data.get('sell_price', 0)
        
        if buy_price > 0:
            profit_percentage = (sell_price - buy_price) / buy_price
        else:
            profit_percentage = 0
        
        return MarketPrediction(
            token_pair=market_data.get('token_pair', 'UNKNOWN'),
            predicted_profit=profit_percentage,
            confidence_score=0.5,
            recommended_action="MONITOR_CLOSELY",
            risk_assessment="MEDIUM",
            time_horizon=30
        )
    
    def save_model(self):
        """Save trained model to disk"""
        try:
            with open('ml_arbitrage_model.pkl', 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_columns': self.feature_columns
                }, f)
            logging.info("ML model saved successfully")
        except Exception as e:
            logging.error(f"Failed to save model: {e}")
    
    def load_model(self) -> bool:
        """Load trained model from disk"""
        try:
            with open('ml_arbitrage_model.pkl', 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
                self.feature_columns = data['feature_columns']
                self.is_trained = True
            logging.info("ML model loaded successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            return False

class AdvancedRiskAgent:
    """Enhanced risk management agent with ML predictions"""

    def __init__(self):
        self.predictor = MLArbitragePredictor()
        # Explicitly type the list to avoid “Unknown” diagnostics.
        self.risk_limits: Dict[str, float | int] = {
            'max_position_size': 1000,
            'max_daily_loss': 100,
            'max_consecutive_losses': 3,
            'min_confidence_threshold': 0.6
        }
        self.daily_pnl: float = 0.0
        self.consecutive_losses: int = 0
    
    async def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate arbitrage opportunity with advanced risk assessment"""
        
        # Get ML prediction
        prediction = self.predictor.predict_profitability(opportunity)
        
        # Apply risk filters
        risk_assessment = await self._comprehensive_risk_check(opportunity, prediction)
        
        # Make final recommendation
        recommendation = self._make_recommendation(prediction, risk_assessment)
        
        return {
            'ml_prediction': prediction,
            'risk_assessment': risk_assessment,
            'recommendation': recommendation,
            'confidence_score': prediction.confidence_score,
            'should_execute': recommendation['execute']
        }
    
    async def _comprehensive_risk_check(self, opportunity: Dict[str, Any],
                                      prediction: MarketPrediction) -> Dict[str, Any]:
        """Perform comprehensive risk assessment"""
        
        checks: Dict[str, bool] = {
            'position_size_ok': opportunity.get('position_size', 0) <= self.risk_limits['max_position_size'],
            'daily_loss_limit_ok': self.daily_pnl > -self.risk_limits['max_daily_loss'],
            'consecutive_loss_limit_ok': self.consecutive_losses < self.risk_limits['max_consecutive_losses'],
            'confidence_threshold_ok': prediction.confidence_score >= self.risk_limits['min_confidence_threshold'],
            'liquidity_sufficient': min(
                opportunity.get('buy_liquidity', 0),
                opportunity.get('sell_liquidity', 0)
            ) > 10000,
            'gas_price_reasonable': opportunity.get('gas_price_gwei', 100) < 100
        }
        
        # Calculate overall risk score
        passed_checks: int = sum(checks.values())
        risk_score = passed_checks / len(checks)
        
        return {
            'individual_checks': checks,
            'overall_risk_score': risk_score,
            'risk_level': 'LOW' if risk_score > 0.8 else 'MEDIUM' if risk_score > 0.6 else 'HIGH'
        }
    
    def _make_recommendation(self, prediction: MarketPrediction, 
                           risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Make final execution recommendation"""
        
        execute = (
            prediction.recommended_action in ['EXECUTE_IMMEDIATELY', 'EXECUTE_WITH_CAUTION'] and
            risk_assessment['overall_risk_score'] > 0.6 and
            prediction.predicted_profit > 0.005  # Minimum 0.5% profit
        )
        
        if execute and prediction.recommended_action == 'EXECUTE_WITH_CAUTION':
            # Reduce position size for cautious execution
            position_multiplier = 0.5
        else:
            position_multiplier = 1.0
        
        return {
            'execute': execute,
            'position_multiplier': position_multiplier,
            'priority': 'HIGH' if prediction.confidence_score > 0.8 else 'MEDIUM',
            'reasoning': self._generate_reasoning(prediction, risk_assessment)
        }
    
    def _generate_reasoning(self, prediction: MarketPrediction, 
                          risk_assessment: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the decision"""
        
        reasons: list[str] = []
        
        if prediction.predicted_profit > 0.01:
            reasons.append(f"High predicted profit ({prediction.predicted_profit:.2%})")
        elif prediction.predicted_profit > 0.005:
            reasons.append(f"Moderate predicted profit ({prediction.predicted_profit:.2%})")
        
        if prediction.confidence_score > 0.8:
            reasons.append("High model confidence")
        elif prediction.confidence_score > 0.6:
            reasons.append("Moderate model confidence")
        else:
            reasons.append("Low model confidence")
        
        if risk_assessment['risk_level'] == 'LOW':
            reasons.append("Low risk profile")
        elif risk_assessment['risk_level'] == 'HIGH':
            reasons.append("High risk - exercise caution")
        
        return " • ".join(reasons)

# Example usage
async def test_advanced_ai_agent():
    """Test the advanced AI agent system"""
    
    # Initialize components
    risk_agent = AdvancedRiskAgent()
    
    # Example opportunity
    test_opportunity: Dict[str, Any] = {
        'token_pair': 'USDC/ETH',
        'buy_price': 1000.50,
        'sell_price': 1005.25,
        'buy_liquidity': 150000,
        'sell_liquidity': 120000,
        'position_size': 500,
        'gas_price_gwei': 25,
        'market_volatility': 0.015,
        'buy_volume_24h': 1000000,
        'sell_volume_24h': 950000
    }
    
    # Evaluate opportunity
    evaluation = await risk_agent.evaluate_opportunity(test_opportunity)  # type: ignore[arg-type]
    
    print("🤖 Advanced AI Agent Evaluation:")
    print(f"   Predicted Profit: {evaluation['ml_prediction'].predicted_profit:.2%}")
    print(f"   Confidence: {evaluation['confidence_score']:.2f}")
    print(f"   Recommendation: {evaluation['ml_prediction'].recommended_action}")
    print(f"   Risk Level: {evaluation['risk_assessment']['risk_level']}")
    print(f"   Should Execute: {evaluation['should_execute']}")
    print(f"   Reasoning: {evaluation['recommendation']['reasoning']}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    asyncio.run(test_advanced_ai_agent())
