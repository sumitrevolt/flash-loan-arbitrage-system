#!/usr/bin/env python3
"""
Quick LangChain MCP Fix Command - Targeted Service Recovery
==========================================================
"""

import subprocess
import asyncio
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def quick_fix_services():
    """Quick fix for all Docker services"""
    logger.info("=== LangChain MCP Quick Fix Started ===")
    
    # Services that need fixing based on Docker status
    failing_services = [
        "flash-loan-aave-mcp",
        "flashloan-agent-main-1", 
        "flashloan-mcp-connection-test-1"
    ]
    
    working_services = [
        "flash-loan-postgres",
        "flash-loan-redis",
        "flash-loan-mcp-coordinator",
        "flashloan-mcp-aave-flash-loan-1"
    ]
    
    logger.info(f"Found {len(failing_services)} services needing fixes")
    logger.info(f"Found {len(working_services)} services already working")
    
    # Fix strategy 1: Restart failing containers
    for service in failing_services:
        logger.info(f"Restarting {service}...")
        try:
            result: str = subprocess.run(
                ["docker", "restart", service], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            if result.returncode == 0:
                logger.info(f"✅ Successfully restarted {service}")
            else:
                logger.error(f"❌ Failed to restart {service}: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout restarting {service}")
        except Exception as e:
            logger.error(f"❌ Error restarting {service}: {e}")
        
        await asyncio.sleep(2)
    
    # Fix strategy 2: Start missing MCP servers
    mcp_servers_to_start = [
        "context7-mcp",
        "grok3-mcp", 
        "enhanced-copilot-mcp",
        "matic-mcp",
        "evm-mcp",
        "foundry-mcp",
        "price-feed-mcp",
        "dex-data-mcp",
        "market-data-mcp",
        "trade-execution-mcp",
        "arbitrage-mcp",
        "risk-analysis-mcp",
        "portfolio-mcp",
        "analytics-mcp",
        "performance-mcp",
        "health-monitor-mcp",
        "log-aggregator-mcp",
        "orchestration-mcp",
        "task-management-mcp",
        "coordination-mcp"
    ]
    
    logger.info(f"Starting {len(mcp_servers_to_start)} MCP servers...")
    
    # Start all MCP servers at once
    try:
        cmd = ["docker-compose", "up", "-d"] + mcp_servers_to_start
        logger.info(f"Running: {' '.join(cmd)}")
        
        result: str = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        
        if result.returncode == 0:
            logger.info("✅ Successfully started MCP servers")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"❌ Failed to start MCP servers: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout starting MCP servers")
    except Exception as e:
        logger.error(f"❌ Error starting MCP servers: {e}")
    
    # Fix strategy 3: Start AI agents
    ai_agents_to_start = [
        "arbitrage-agent",
        "risk-management-agent", 
        "market-analysis-agent",
        "execution-agent",
        "monitoring-agent",
        "data-collection-agent",
        "strategy-agent",
        "coordination-agent",
        "learning-agent",
        "reporting-agent"
    ]
    
    logger.info(f"Starting {len(ai_agents_to_start)} AI agents...")
    
    try:
        cmd = ["docker-compose", "up", "-d"] + ai_agents_to_start
        logger.info(f"Running: {' '.join(cmd)}")
        
        result: str = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        
        if result.returncode == 0:
            logger.info("✅ Successfully started AI agents")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"❌ Failed to start AI agents: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout starting AI agents")
    except Exception as e:
        logger.error(f"❌ Error starting AI agents: {e}")
    
    # Final status check
    logger.info("Checking final status...")
    await asyncio.sleep(10)
    
    try:
        result: str = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        logger.info("Current Docker status:")
        logger.info(result.stdout)
    except Exception as e:
        logger.error(f"❌ Error checking status: {e}")
    
    logger.info("=== LangChain MCP Quick Fix Completed ===")

if __name__ == "__main__":
    try:
        asyncio.run(quick_fix_services())
        print("\n🎉 Quick fix completed! Check the logs above for results.")
    except KeyboardInterrupt:
        print("\n🛑 Quick fix interrupted by user")
    except Exception as e:
        print(f"\n❌ Quick fix failed: {e}")
        sys.exit(1)
