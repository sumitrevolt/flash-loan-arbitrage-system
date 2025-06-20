#!/usr/bin/env python3
"""
MCP Training Starter Script
Coordinates training across all MCP servers
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.training.mcp_training_coordinator import MCPTrainingCoordinator

async def main():
    print("🚀 Starting MCP Training System")
    print("=" * 50)
    
    try:
        # Initialize coordinator
        coordinator = MCPTrainingCoordinator()
        
        # Step 1: Discover servers
        print("\n📡 Discovering MCP servers...")
        servers = await coordinator.discover_mcp_servers()
        print(f"✅ Found {len(servers)} servers:")
        for server in servers:
            print(f"   - {server.name} ({server.host}:{server.port}) - {', '.join(server.capabilities)}")
        
        if not servers:
            print("❌ No MCP servers found. Please start your MCP servers first.")
            return
        
        # Step 2: Collect training data
        print("\n📊 Collecting training data...")
        training_data = await coordinator.collect_training_data(["arbitrage", "revenue", "risk"])
        print(f"✅ Collected {len(training_data)} training samples")
        
        if len(training_data) < 10:
            print("⚠️ Warning: Limited training data available. Using synthetic data for demonstration.")
        
        # Step 3: Train models
        print("\n🤖 Training ML models...")
        print("   Training models: arbitrage_predictor, risk_classifier, neural_network")
        
        start_time = time.time()
        results = await coordinator.train_models([
            "arbitrage_predictor", 
            "risk_classifier", 
            "neural_network"
        ])
        training_time = time.time() - start_time
        
        # Step 4: Display results
        print(f"\n📈 Training completed in {training_time:.2f} seconds")
        print(f"Session ID: {results.get('session_id')}")
        
        for model_type, model_results in results.get("results", {}).items():
            if "error" not in model_results:
                print(f"\n✅ {model_type}:")
                if "train_mse" in model_results:
                    print(f"   Train MSE: {model_results['train_mse']:.4f}")
                    print(f"   Test MSE: {model_results['test_mse']:.4f}")
                if "train_accuracy" in model_results:
                    print(f"   Train Accuracy: {model_results['train_accuracy']:.4f}")
                    print(f"   Test Accuracy: {model_results['test_accuracy']:.4f}")
                if "feature_importance" in model_results:
                    print("   Top Features:")
                    importance = model_results["feature_importance"]
                    for feature, score in sorted(importance.items(), key=lambda x: Any: Any: x[1], reverse=True)[:3]:
                        print(f"     - {feature}: {score:.4f}")
            else:
                print(f"❌ {model_type}: {model_results['error']}")
        
        # Step 5: Deploy models (if training was successful)
        if results.get("results") and all("error" not in r for r in results["results"].values()):
            print("\n🚀 Deploying models to servers...")
            deployment = await coordinator.deploy_models_to_servers(results["session_id"])
            print(f"✅ Deployed to {deployment.get('deployed_servers', 0)} servers")
        
        # Step 6: Show final status
        print("\n📋 Training Summary:")
        print(f"   Session: {results.get('session_id')}")
        print(f"   Models trained: {len(results.get('results', {}))}")
        print(f"   Training data: {results.get('training_data_size')} samples")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n🎉 MCP Training completed successfully!")
        print("\nNext steps:")
        print("1. Start the training MCP server: python mcp_servers/training_mcp_server.py")
        print("2. Use trained models in your arbitrage strategies")
        print("3. Monitor model performance and retrain as needed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        sys.exit(1)
