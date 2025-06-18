#!/usr/bin/env python3
"""
Continuous Learning System for MCP Servers
Implements automated model improvement using real trading data
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pickle
import os
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuous_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ModelPerformance:
    """Track model performance metrics"""
    model_name: str
    server_port: int
    accuracy: float
    mse: float
    r2_score: float
    training_samples: int
    last_updated: datetime
    improvement_percentage: float = 0.0

@dataclass
class LearningData:
    """Structure for learning data"""
    features: np.ndarray
    labels: np.ndarray
    metadata: Dict[str, Any]

class ContinuousLearningSystem:
    """Manages continuous learning for all MCP servers"""
    
    def __init__(self):
        self.db_path = "continuous_learning.db"
        self.models_path = "models"
        self.real_data_db = "real_trading_data.db"
        
        # MCP server configuration
        self.mcp_servers = {
            # Core MCP servers (8100-8120)
            'market_data_server': 8100,
            'arbitrage_detector': 8101,
            'risk_manager': 8102,
            'portfolio_optimizer': 8103,
            'trade_executor': 8104,
            'price_predictor': 8105,
            'liquidity_analyzer': 8106,
            'gas_optimizer': 8107,
            'flash_loan_coordinator': 8108,
            'profit_calculator': 8109,
            'security_monitor': 8110,
            'compliance_checker': 8111,
            'performance_tracker': 8112,
            'alert_manager': 8113,
            'data_aggregator': 8114,
            'strategy_selector': 8115,
            'execution_planner': 8116,
            'bridge_coordinator': 8117,
            'slippage_calculator': 8118,
            'timing_optimizer': 8119,
            'cross_chain_monitor': 8120,
            
            # AI Agent servers (8200-8209)
            'trading_agent': 8200,
            'analysis_agent': 8201,
            'risk_agent': 8202,
            'execution_agent': 8203,
            'monitor_agent': 8204,
            'research_agent': 8205,
            'optimization_agent': 8206,
            'alert_agent': 8207,
            'reporting_agent': 8208,
            'learning_agent': 8209
        }
        
        self.learning_interval = 3600  # 1 hour
        self.min_samples_for_training = 100
        self.performance_threshold = 0.05  # 5% improvement required for update
        self.running = False
        
        # Create models directory
        os.makedirs(self.models_path, exist_ok=True)
    
    async def initialize_database(self):
        """Initialize continuous learning database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Model performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    server_port INTEGER NOT NULL,
                    accuracy REAL,
                    mse REAL,
                    r2_score REAL,
                    training_samples INTEGER,
                    last_updated DATETIME,
                    improvement_percentage REAL DEFAULT 0.0,
                    model_version INTEGER DEFAULT 1
                )
            ''')
            
            # Learning sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start DATETIME NOT NULL,
                    session_end DATETIME,
                    models_updated INTEGER DEFAULT 0,
                    total_samples_processed INTEGER DEFAULT 0,
                    average_improvement REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Feature importance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feature_importance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    importance_score REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Learning feedback
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    prediction_id TEXT,
                    actual_outcome REAL,
                    predicted_outcome REAL,
                    feedback_score REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Continuous learning database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def extract_features_from_market_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Extract features and labels from market data"""
        try:
            if df.empty:
                return np.array([]), np.array([])
            
            # Ensure we have required columns
            required_columns = ['price', 'volume', 'volatility', 'spread']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 0.0
            
            # Calculate technical indicators
            df['price_ma_5'] = df['price'].rolling(window=5, min_periods=1).mean()
            df['price_ma_20'] = df['price'].rolling(window=20, min_periods=1).mean()
            df['volume_ma'] = df['volume'].rolling(window=10, min_periods=1).mean()
            df['price_std'] = df['price'].rolling(window=10, min_periods=1).std().fillna(0)
            
            # Price change features
            df['price_change'] = df['price'].pct_change().fillna(0)
            df['price_change_abs'] = df['price_change'].abs()
            
            # Volume features
            df['volume_ratio'] = df['volume'] / (df['volume_ma'] + 1e-8)
            
            # Volatility features
            df['volatility_normalized'] = df['volatility'] / (df['volatility'].std() + 1e-8)
            
            # Features for prediction
            feature_columns = [
                'price', 'volume', 'volatility', 'spread',
                'price_ma_5', 'price_ma_20', 'volume_ma', 'price_std',
                'price_change', 'price_change_abs', 'volume_ratio', 'volatility_normalized'
            ]
            
            # Create features matrix
            features = df[feature_columns].fillna(0).values
            
            # Create labels (predict next period price change)
            labels = df['price_change'].shift(-1).fillna(0).values
            
            # Remove last row (no future price change)
            features = features[:-1]
            labels = labels[:-1]
            
            return features, labels
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return np.array([]), np.array([])
    
    def extract_arbitrage_features(self) -> Tuple[np.ndarray, np.ndarray]:
        """Extract features for arbitrage opportunity prediction"""
        try:
            # Connect to real trading data database
            conn = sqlite3.connect(self.real_data_db)
            
            # Get recent arbitrage data
            query = '''
                SELECT profit_percentage, volume_available, 
                       (julianday('now') - julianday(timestamp)) * 24 as hours_ago
                FROM arbitrage_opportunities 
                WHERE timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp DESC
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                return np.array([]), np.array([])
            
            # Create features
            features = df[['volume_available', 'hours_ago']].fillna(0).values
            
            # Create labels (profitable if > 0.5%)
            labels = (df['profit_percentage'] > 0.5).astype(int).values
            
            return features, labels
            
        except Exception as e:
            logger.error(f"Arbitrage feature extraction failed: {e}")
            return np.array([]), np.array([])
    
    async def get_real_market_data(self, hours: int = 24) -> pd.DataFrame:
        """Get real market data for training"""
        try:
            if not os.path.exists(self.real_data_db):
                logger.warning("Real trading data database not found")
                return pd.DataFrame()
                
            conn = sqlite3.connect(self.real_data_db)
            
            query = '''
                SELECT timestamp, symbol, price, volume, volatility, spread, exchange
                FROM market_data 
                WHERE timestamp >= datetime('now', '-{} hours')
                ORDER BY timestamp ASC
            '''.format(hours)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Convert timestamp to datetime
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get real market data: {e}")
            return pd.DataFrame()
    
    def train_price_prediction_model(self, features: np.ndarray, labels: np.ndarray) -> Tuple[Any, Dict]:
        """Train price prediction model"""
        try:
            if len(features) < self.min_samples_for_training:
                logger.warning(f"Not enough samples for training: {len(features)}")
                return None, {}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Calculate accuracy (within 10% of actual)
            accuracy = np.mean(np.abs(y_pred - y_test) / (np.abs(y_test) + 1e-8) < 0.1)
            
            performance = {
                'accuracy': accuracy,
                'mse': mse,
                'r2_score': r2,
                'training_samples': len(X_train),
                'feature_importance': model.feature_importances_.tolist()
            }
            
            return {'model': model, 'scaler': scaler}, performance
            
        except Exception as e:
            logger.error(f"Price prediction model training failed: {e}")
            return None, {}
    
    def train_arbitrage_model(self, features: np.ndarray, labels: np.ndarray) -> Tuple[Any, Dict]:
        """Train arbitrage opportunity detection model"""
        try:
            if len(features) < self.min_samples_for_training:
                logger.warning(f"Not enough samples for arbitrage training: {len(features)}")
                return None, {}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            performance = {
                'accuracy': accuracy,
                'mse': 0.0,  # Not applicable for classification
                'r2_score': 0.0,  # Not applicable for classification
                'training_samples': len(X_train),
                'feature_importance': model.feature_importances_.tolist()
            }
            
            return {'model': model, 'scaler': scaler}, performance
            
        except Exception as e:
            logger.error(f"Arbitrage model training failed: {e}")
            return None, {}
    
    async def update_mcp_server_model(self, server_name: str, port: int, model_data: Dict) -> bool:
        """Update MCP server with new model"""
        try:
            # Save model to file
            model_file = os.path.join(self.models_path, f"{server_name}_model.pkl")
            with open(model_file, 'wb') as f:
                pickle.dump(model_data, f)
            
            # Send update to MCP server
            async with aiohttp.ClientSession() as session:
                update_url = f"http://localhost:{port}/update_model"
                
                # Prepare model data for transmission
                model_json = {
                    'model_file': model_file,
                    'performance': model_data.get('performance', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                async with session.post(update_url, json=model_json, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully updated model for {server_name} on port {port}")
                        return True
                    else:
                        logger.warning(f"Failed to update {server_name}: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to update MCP server {server_name}: {e}")
            return False
    
    async def train_and_update_models(self):
        """Train and update all models based on real data"""
        logger.info("Starting model training and update cycle...")
        
        session_start = datetime.now()
        models_updated = 0
        total_samples = 0
        improvements = []
        
        try:
            # Get real market data
            market_data = await self.get_real_market_data(hours=168)  # 1 week of data
            
            if market_data.empty:
                logger.warning("No real market data available for training")
                return
            
            logger.info(f"Retrieved {len(market_data)} market data points for training")
            
            # Extract features for different model types
            price_features, price_labels = self.extract_features_from_market_data(market_data)
            arbitrage_features, arbitrage_labels = self.extract_arbitrage_features()
            
            total_samples = len(price_features) + len(arbitrage_features)
            
            # Define model assignments
            price_prediction_servers = [
                'price_predictor', 'market_data_server', 'trading_agent', 
                'analysis_agent', 'research_agent'
            ]
            
            arbitrage_servers = [
                'arbitrage_detector', 'profit_calculator', 'execution_agent',
                'optimization_agent', 'flash_loan_coordinator'
            ]
            
            # Train price prediction models
            if len(price_features) >= self.min_samples_for_training:
                model_data, performance = self.train_price_prediction_model(price_features, price_labels)
                
                if model_data:
                    for server_name in price_prediction_servers:
                        if server_name in self.mcp_servers:
                            port = self.mcp_servers[server_name]
                            
                            # Check if improvement is significant
                            old_performance = await self.get_model_performance(server_name)
                            improvement = 0.0
                            
                            if old_performance:
                                if performance['accuracy'] > old_performance['accuracy']:
                                    improvement = ((performance['accuracy'] - old_performance['accuracy']) / 
                                                 old_performance['accuracy']) * 100
                            else:
                                improvement = 100.0  # First time training
                            
                            if improvement >= self.performance_threshold or old_performance is None:
                                model_data['performance'] = performance
                                if await self.update_mcp_server_model(server_name, port, model_data):
                                    await self.save_model_performance(server_name, port, performance, improvement)
                                    models_updated += 1
                                    improvements.append(improvement)
                                    logger.info(f"Updated {server_name} with {improvement:.2f}% improvement")
                            else:
                                logger.info(f"Skipping {server_name} - improvement too small: {improvement:.2f}%")
            
            # Train arbitrage models
            if len(arbitrage_features) >= self.min_samples_for_training:
                model_data, performance = self.train_arbitrage_model(arbitrage_features, arbitrage_labels)
                
                if model_data:
                    for server_name in arbitrage_servers:
                        if server_name in self.mcp_servers:
                            port = self.mcp_servers[server_name]
                            
                            # Check improvement
                            old_performance = await self.get_model_performance(server_name)
                            improvement = 0.0
                            
                            if old_performance:
                                if performance['accuracy'] > old_performance['accuracy']:
                                    improvement = ((performance['accuracy'] - old_performance['accuracy']) / 
                                                 old_performance['accuracy']) * 100
                            else:
                                improvement = 100.0
                            
                            if improvement >= self.performance_threshold or old_performance is None:
                                model_data['performance'] = performance
                                if await self.update_mcp_server_model(server_name, port, model_data):
                                    await self.save_model_performance(server_name, port, performance, improvement)
                                    models_updated += 1
                                    improvements.append(improvement)
                                    logger.info(f"Updated {server_name} with {improvement:.2f}% improvement")
            
            # Save learning session
            await self.save_learning_session(
                session_start, datetime.now(), models_updated, 
                total_samples, np.mean(improvements) if improvements else 0.0
            )
            
            logger.info(f"Training cycle completed: {models_updated} models updated, "
                       f"{total_samples} samples processed, "
                       f"average improvement: {np.mean(improvements):.2f}%" if improvements else "0%")
            
        except Exception as e:
            logger.error(f"Model training and update failed: {e}")
    
    async def get_model_performance(self, model_name: str) -> Optional[Dict]:
        """Get latest model performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT accuracy, mse, r2_score, training_samples 
                FROM model_performance 
                WHERE model_name = ? 
                ORDER BY last_updated DESC 
                LIMIT 1
            ''', (model_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'accuracy': result[0],
                    'mse': result[1], 
                    'r2_score': result[2],
                    'training_samples': result[3]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            return None
    
    async def save_model_performance(self, model_name: str, port: int, performance: Dict, improvement: float):
        """Save model performance to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO model_performance 
                (model_name, server_port, accuracy, mse, r2_score, training_samples, 
                 last_updated, improvement_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_name, port, performance['accuracy'], performance['mse'],
                performance['r2_score'], performance['training_samples'],
                datetime.now(), improvement
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save model performance: {e}")
    
    async def save_learning_session(self, start_time: datetime, end_time: datetime, 
                                  models_updated: int, samples_processed: int, avg_improvement: float):
        """Save learning session to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO learning_sessions 
                (session_start, session_end, models_updated, total_samples_processed, 
                 average_improvement, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (start_time, end_time, models_updated, samples_processed, avg_improvement, 'completed'))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save learning session: {e}")
    
    async def start_continuous_learning(self):
        """Start continuous learning loop"""
        logger.info("Starting continuous learning system...")
        
        await self.initialize_database()
        self.running = True
        
        try:
            while self.running:
                await self.train_and_update_models()
                
                # Wait for next cycle
                logger.info(f"Waiting {self.learning_interval} seconds for next learning cycle...")
                await asyncio.sleep(self.learning_interval)
                
        except KeyboardInterrupt:
            logger.info("Continuous learning stopped by user")
        except Exception as e:
            logger.error(f"Continuous learning error: {e}")
        finally:
            self.running = False
    
    def stop_learning(self):
        """Stop continuous learning"""
        self.running = False
        logger.info("Stopping continuous learning...")
    
    async def generate_learning_report(self) -> Dict:
        """Generate comprehensive learning report"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get recent performance data
            performance_df = pd.read_sql_query('''
                SELECT model_name, accuracy, improvement_percentage, training_samples, last_updated
                FROM model_performance 
                WHERE last_updated >= datetime('now', '-24 hours')
                ORDER BY last_updated DESC
            ''', conn)
            
            # Get learning sessions
            sessions_df = pd.read_sql_query('''
                SELECT * FROM learning_sessions 
                WHERE session_start >= datetime('now', '-24 hours')
                ORDER BY session_start DESC
            ''', conn)
            
            conn.close()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'models_trained': len(performance_df),
                'average_accuracy': performance_df['accuracy'].mean() if not performance_df.empty else 0,
                'average_improvement': performance_df['improvement_percentage'].mean() if not performance_df.empty else 0,
                'total_training_samples': performance_df['training_samples'].sum() if not performance_df.empty else 0,
                'learning_sessions': len(sessions_df),
                'top_performing_models': performance_df.nlargest(5, 'accuracy').to_dict('records') if not performance_df.empty else [],
                'most_improved_models': performance_df.nlargest(5, 'improvement_percentage').to_dict('records') if not performance_df.empty else []
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate learning report: {e}")
            return {}

async def main():
    """Main function"""
    learning_system = ContinuousLearningSystem()
    
    try:
        await learning_system.start_continuous_learning()
    except KeyboardInterrupt:
        logger.info("Continuous learning stopped")
    finally:
        learning_system.stop_learning()

if __name__ == "__main__":
    asyncio.run(main())
