#!/usr/bin/env python3
"""
Comprehensive MCP Server Training Script
Trains all MCP servers with their ML models and capabilities
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

# Add project paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.training.mcp_training_coordinator import MCPTrainingCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ComprehensiveMCPTrainer:
    """Comprehensive trainer for all MCP servers"""
    
    def __init__(self):
        self.coordinator = MCPTrainingCoordinator()
        self.training_results = {}
        self.deployment_results = {}
        
    async def initialize(self):
        """Initialize the training environment"""
        logger.info("🚀 Initializing MCP Training Environment...")
        
        # Create necessary directories
        os.makedirs("models", exist_ok=True)
        os.makedirs("training_logs", exist_ok=True)
        os.makedirs("training_data", exist_ok=True)
        
        logger.info("✅ Training environment initialized")
    
    async def discover_all_servers(self) -> List[Dict[str, Any]]:
        """Discover all available MCP servers"""
        logger.info("🔍 Discovering MCP servers...")
        
        try:
            servers = await self.coordinator.discover_mcp_servers()
            
            server_info = []
            for server in servers:
                info = {
                    "name": server.name,
                    "host": server.host,
                    "port": server.port,
                    "capabilities": server.capabilities,
                    "health_status": server.health_status,
                    "training_ready": any(cap in ["training_data", "arbitrage", "ml_models", "ai_agents"] 
                                        for cap in server.capabilities)
                }
                server_info.append(info)
                
                logger.info(f"📍 Found server: {server.name} at {server.host}:{server.port}")
                logger.info(f"   Capabilities: {', '.join(server.capabilities)}")
                logger.info(f"   Training Ready: {'✅' if info['training_ready'] else '❌'}")
            
            logger.info(f"🎯 Discovered {len(servers)} MCP servers ({len([s for s in server_info if s['training_ready']])} training-ready)")
            return server_info
            
        except Exception as e:
            logger.error(f"❌ Error discovering servers: {e}")
            return []
    
    async def collect_comprehensive_data(self) -> pd.DataFrame:
        """Collect training data from all available sources"""
        logger.info("📊 Collecting comprehensive training data...")
        
        try:
            # Define all data types we want to collect
            data_types = [
                "arbitrage",
                "revenue", 
                "risk",
                "liquidity",
                "price_feeds",
                "market_data",
                "transaction_history",
                "performance_metrics"
            ]
            
            training_data = await self.coordinator.collect_training_data(data_types)
            
            logger.info(f"📈 Collected {len(training_data)} training samples")
            logger.info(f"📋 Data columns: {list(training_data.columns)}")
            
            # Save training data for inspection
            training_data.to_csv("training_data/collected_data.csv", index=False)
            logger.info("💾 Training data saved to training_data/collected_data.csv")
            
            return training_data
            
        except Exception as e:
            logger.error(f"❌ Error collecting training data: {e}")
            return pd.DataFrame()
    
    async def train_all_models(self) -> Dict[str, Any]:
        """Train all available ML models"""
        logger.info("🧠 Training all ML models...")
        
        try:
            # Define all model types to train
            model_types = [
                "arbitrage_predictor",
                "risk_classifier", 
                "neural_network",
                "liquidity_optimizer",
                "price_predictor",
                "revenue_forecaster",
                "market_analyzer"
            ]
            
            training_session_results = {}
            
            for model_type in model_types:
                logger.info(f"🔄 Training {model_type}...")
                
                try:
                    # Train individual model
                    results = await self.coordinator.train_models([model_type])
                    training_session_results[model_type] = results
                    
                    if "error" not in results:
                        logger.info(f"✅ {model_type} training completed successfully")
                        if "results" in results:
                            for metric, value in results["results"].items():
                                logger.info(f"   📊 {metric}: {value}")
                    else:
                        logger.warning(f"⚠️ {model_type} training had issues: {results.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"❌ Error training {model_type}: {e}")
                    training_session_results[model_type] = {"error": str(e)}
            
            self.training_results = training_session_results
            
            # Save training results
            with open("training_logs/training_results.json", "w") as f:
                json.dump(training_session_results, f, indent=2, default=str)
            
            successful_models = len([r for r in training_session_results.values() if "error" not in r])
            logger.info(f"🎯 Training completed: {successful_models}/{len(model_types)} models successful")
            
            return training_session_results
            
        except Exception as e:
            logger.error(f"❌ Error in training process: {e}")
            return {"error": str(e)}
    
    async def deploy_to_all_servers(self) -> Dict[str, Any]:
        """Deploy trained models to all capable servers"""
        logger.info("🚀 Deploying models to MCP servers...")
        
        try:
            # Get the latest training session ID
            session_id = None
            if self.training_results:
                for model_results in self.training_results.values():
                    if isinstance(model_results, dict) and "session_id" in model_results:
                        session_id = model_results["session_id"]
                        break
            
            if not session_id:
                logger.warning("⚠️ No valid session ID found for deployment")
                return {"error": "No trained models to deploy"}
            
            deployment_results = await self.coordinator.deploy_models_to_servers(session_id)
            self.deployment_results = deployment_results
            
            logger.info(f"📦 Deployment results:")
            for server_name, result in deployment_results.get("deployments", {}).items():
                if "error" not in result:
                    logger.info(f"   ✅ {server_name}: Deployment successful")
                else:
                    logger.warning(f"   ❌ {server_name}: {result.get('error', 'Unknown error')}")
            
            successful_deployments = deployment_results.get("deployed_servers", 0)
            total_servers = len(deployment_results.get("deployments", {}))
            logger.info(f"🎯 Deployment completed: {successful_deployments}/{total_servers} servers successful")
            
            # Save deployment results
            with open("training_logs/deployment_results.json", "w") as f:
                json.dump(deployment_results, f, indent=2, default=str)
            
            return deployment_results
            
        except Exception as e:
            logger.error(f"❌ Error in deployment process: {e}")
            return {"error": str(e)}
    
    async def validate_training(self) -> Dict[str, Any]:
        """Validate training results and model performance"""
        logger.info("🔍 Validating training results...")
        
        try:
            validation_results = {
                "trained_models": len(self.coordinator.ml_trainer.models),
                "model_list": list(self.coordinator.ml_trainer.models.keys()),
                "feature_importance": self.coordinator.ml_trainer.feature_importance,
                "training_sessions": len(self.training_results),
                "successful_trainings": len([r for r in self.training_results.values() if "error" not in r]),
                "deployment_success": self.deployment_results.get("deployed_servers", 0),
                "validation_timestamp": datetime.now().isoformat()
            }
            
            logger.info("📊 Training Validation Summary:")
            logger.info(f"   🧠 Models trained: {validation_results['trained_models']}")
            logger.info(f"   📋 Model types: {', '.join(validation_results['model_list'])}")
            logger.info(f"   ✅ Successful sessions: {validation_results['successful_trainings']}/{validation_results['training_sessions']}")
            logger.info(f"   🚀 Deployed to servers: {validation_results['deployment_success']}")
            
            # Save validation results
            with open("training_logs/validation_results.json", "w") as f:
                json.dump(validation_results, f, indent=2, default=str)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Error in validation: {e}")
            return {"error": str(e)}
    
    async def generate_training_report(self) -> str:
        """Generate comprehensive training report"""
        logger.info("📄 Generating training report...")
        
        try:
            report_lines = [
                "=" * 80,
                "MCP SERVERS TRAINING REPORT",
                "=" * 80,
                f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "SUMMARY:",
                f"- Servers Discovered: {len(self.coordinator.servers)}",
                f"- Models Trained: {len(self.coordinator.ml_trainer.models)}",
                f"- Training Sessions: {len(self.training_results)}",
                f"- Successful Deployments: {self.deployment_results.get('deployed_servers', 0)}",
                "",
                "TRAINED MODELS:",
            ]
            
            for model_name in self.coordinator.ml_trainer.models.keys():
                report_lines.append(f"  ✅ {model_name}")
            
            report_lines.extend([
                "",
                "SERVER STATUS:",
            ])
            
            for server_name, server in self.coordinator.servers.items():
                status = "🟢 Healthy" if server.health_status == "healthy" else "🔴 Unhealthy"
                report_lines.append(f"  {status} {server_name} ({server.host}:{server.port})")
                report_lines.append(f"     Capabilities: {', '.join(server.capabilities)}")
            
            if self.coordinator.ml_trainer.feature_importance:
                report_lines.extend([
                    "",
                    "FEATURE IMPORTANCE:",
                ])
                
                for model_name, features in self.coordinator.ml_trainer.feature_importance.items():
                    report_lines.append(f"  {model_name}:")
                    for feature, importance in sorted(features.items(), key=lambda x: x[1], reverse=True)[:5]:
                        report_lines.append(f"    - {feature}: {importance:.4f}")
            
            report_lines.extend([
                "",
                "=" * 80,
            ])
            
            report_content = "\n".join(report_lines)
            
            # Save report
            with open("training_logs/training_report.txt", "w") as f:
                f.write(report_content)
            
            logger.info("📄 Training report saved to training_logs/training_report.txt")
            return report_content
            
        except Exception as e:
            logger.error(f"❌ Error generating report: {e}")
            return f"Error generating report: {e}"

async def main():
    """Main training execution function"""
    
    print("🎯 Starting Comprehensive MCP Server Training")
    print("=" * 60)
    
    trainer = ComprehensiveMCPTrainer()
    
    try:
        # Step 1: Initialize
        await trainer.initialize()
        
        # Step 2: Discover servers
        servers = await trainer.discover_all_servers()
        if not servers:
            logger.error("❌ No MCP servers found. Make sure servers are running.")
            return
        
        # Step 3: Collect training data
        training_data = await trainer.collect_comprehensive_data()
        if training_data.empty:
            logger.warning("⚠️ No training data collected, using synthetic data")
        
        # Step 4: Train all models
        training_results = await trainer.train_all_models()
        
        # Step 5: Deploy to servers
        deployment_results = await trainer.deploy_to_all_servers()
        
        # Step 6: Validate results
        validation_results = await trainer.validate_training()
        
        # Step 7: Generate report
        report = await trainer.generate_training_report()
        
        print("\n" + "=" * 60)
        print("🎉 MCP SERVER TRAINING COMPLETED")
        print("=" * 60)
        print(f"📊 Models Trained: {validation_results.get('trained_models', 0)}")
        print(f"🚀 Servers Deployed: {validation_results.get('deployment_success', 0)}")
        print(f"📄 Report: training_logs/training_report.txt")
        print(f"📋 Logs: mcp_training.log")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        print(f"\n❌ Training failed: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())
