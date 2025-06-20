#!/usr/bin/env python3
"""
MCP Training Status Checker
Quick script to check the status of MCP server training
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime

# Add project paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.training.mcp_training_coordinator import MCPTrainingCoordinator

async def check_training_status():
    """Check the current training status"""
    
    print("🔍 Checking MCP Training Status...")
    print("=" * 50)
    
    coordinator = MCPTrainingCoordinator()
    
    try:
        # Check server discovery
        servers = await coordinator.discover_mcp_servers()
        print(f"📍 MCP Servers: {len(servers)} discovered")
        
        for server in servers:
            status_emoji = "🟢" if server.health_status == "healthy" else "🔴"
            print(f"   {status_emoji} {server.name} ({server.host}:{server.port})")
            print(f"      Capabilities: {', '.join(server.capabilities)}")
        
        print()
        
        # Check training sessions
        status = await coordinator.get_training_status()
        recent_sessions = status.get("recent_sessions", [])
        
        print(f"🧠 Training Sessions: {len(recent_sessions)} recent")
        
        if recent_sessions:
            for session in recent_sessions[:3]:  # Show last 3 sessions
                print(f"   📋 Session: {session['session_id']}")
                print(f"      Models: {', '.join(session['model_types'])}")
                print(f"      Status: {session['status']}")
                print(f"      Time: {session['start_time']}")
                print()
        else:
            print("   ℹ️ No training sessions found")
        
        # Check available models
        models = coordinator.ml_trainer.models
        print(f"🤖 Trained Models: {len(models)}")
        
        if models:
            for model_name in models.keys():
                print(f"   ✅ {model_name}")
        else:
            print("   ℹ️ No trained models found")
        
        print()
        
        # Check feature importance
        feature_importance = coordinator.ml_trainer.feature_importance
        if feature_importance:
            print("📊 Feature Importance Available:")
            for model_name in feature_importance.keys():
                print(f"   📈 {model_name}")
        else:
            print("📊 No feature importance data available")
        
        print("\n" + "=" * 50)
        print("✅ Status check completed")
        
        return {
            "servers": len(servers),
            "sessions": len(recent_sessions),
            "models": len(models),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(check_training_status())
