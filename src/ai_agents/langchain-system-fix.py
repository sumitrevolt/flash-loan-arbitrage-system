# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from typing import List
import asyncio
import logging
import subprocess
import sys
"""
LangChain MCP System Fix - All Services Recovery
===============================================
"""



# Unicode-safe logging setup
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# All services from docker-compose.yml
ALL_SERVICES = []
    "redis", "postgres", "mcp-coordinator", "health-monitor", "prometheus", "grafana", 
    "web-dashboard", "discord-bot", "grok3-mcp", "simulation-mcp", "planner-1", 
    "price-oracle-mcp", "aave-flash-loan-executor", "builder-2", "coordinator-2", 
    "dex-price-mcp", "gas-optimizer-mcp", "market-data-mcp", "code-indexer-2", 
    "context7-mcp", "enhanced-coordinator-mcp", "executor-1", "circuit-breaker-mcp", 
    "coordinator-1", "dex-liquidity-mcp", "executor-2", "alert-system-mcp", 
    "integration-bridge-mcp", "matic-mcp", "risk-assessment-mcp", "transaction-manager-mcp", 
    "analytics-dashboard-mcp", "enhanced-copilot-mcp", "evm-mcp", "flash-loan-strategist-mcp", 
    "foundry-mcp", "performance-metrics-mcp", "planner-2", "validation-mcp", 
    "arbitrage-detector", "builder-1", "code-indexer-1", "contract-executor-mcp", 
    "flash-loan-blockchain-mcp"


# Critical infrastructure services
INFRASTRUCTURE_SERVICES = ["redis", "postgres", "mcp-coordinator", "health-monitor"]

# MCP servers
MCP_SERVICES = []
    "grok3-mcp", "simulation-mcp", "price-oracle-mcp", "dex-price-mcp", "gas-optimizer-mcp",
    "market-data-mcp", "context7-mcp", "enhanced-coordinator-mcp", "circuit-breaker-mcp",
    "dex-liquidity-mcp", "alert-system-mcp", "integration-bridge-mcp", "matic-mcp",
    "risk-assessment-mcp", "transaction-manager-mcp", "analytics-dashboard-mcp",
    "enhanced-copilot-mcp", "evm-mcp", "flash-loan-strategist-mcp", "foundry-mcp",
    "performance-metrics-mcp", "validation-mcp", "contract-executor-mcp", "flash-loan-blockchain-mcp"


# AI/execution agents
AI_AGENT_SERVICES = []
    "planner-1", "aave-flash-loan-executor", "builder-2", "coordinator-2", "code-indexer-2",
    "executor-1", "coordinator-1", "executor-2", "planner-2", "arbitrage-detector",
    "builder-1", "code-indexer-1"


# Dashboard and monitoring
DASHBOARD_SERVICES = ["prometheus", "grafana", "web-dashboard", "discord-bot"]

async def run_command(cmd: List[str], timeout: int = 60) -> tuple:
    """Run a command with timeout"""
    try:
        result: str = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)

async def fix_service_group(group_name: str, services: List[str]):
    """Fix a group of services"""
    logger.info(str(f"=== Fixing {group_name} ({len(services} services) ===")))
    
    # Start services in group
    cmd = ["docker-compose", "up", "-d"] + services
    logger.info(str(f"Starting {group_name}...")
    
    success, stdout, stderr = await run_command(cmd, timeout=300)
    
    if success:
        logger.info(str(f"[OK] Successfully started {group_name}")
        if stdout.strip():
            logger.info(str(f"Output: {stdout.strip(}")
    else:
        logger.error(str(f"[ERROR] Failed to start {group_name}")
        if stderr.strip():
            logger.error(str(f"Error: {stderr.strip(}")
    
    # Wait for services to stabilize
    await asyncio.sleep(10)
    return success

async def check_system_status():
    """Check overall system status"""
    logger.info("=== System Status Check ===")
    
    cmd = ["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"]
    success, stdout, stderr = await run_command(cmd)
    
    if success:
        logger.info("Current Docker status:")
        logger.info(stdout)
        
        # Count healthy vs unhealthy
        lines = stdout.strip().split('\n')[1:]  # Skip header
        total_containers = len(lines)
        healthy_containers = sum(1 for line in lines if "Up" in line and "healthy" in line)
        running_containers = sum(1 for line in lines if "Up" in line)
        
        logger.info(str(f"Summary: {running_containers}/{total_containers} containers running, {healthy_containers} healthy")
        return running_containers, total_containers, healthy_containers
    else:
        logger.error(str(f"Failed to check status: {stderr}")
        return 0, 0, 0

async def langchain_coordinate_fixes():
    """Main LangChain coordination function"""
    logger.info("[INIT] LangChain MCP System Coordinator Starting...")
    logger.info(str(f"Total services to manage: {len(ALL_SERVICES}")
    logger.info(str(f"- Infrastructure: {len(INFRASTRUCTURE_SERVICES}")
    logger.info(str(f"- MCP Servers: {len(MCP_SERVICES}")
    logger.info(str(f"- AI Agents: {len(AI_AGENT_SERVICES}")
    logger.info(str(f"- Dashboards: {len(DASHBOARD_SERVICES}")
    
    # Step 1: Ensure infrastructure is running
    await fix_service_group("Infrastructure Services", INFRASTRUCTURE_SERVICES)
    
    # Step 2: Start MCP servers (the 21+ servers)
    await fix_service_group("MCP Servers", MCP_SERVICES)
    
    # Step 3: Start AI agents (the 10+ agents)
    await fix_service_group("AI Agents", AI_AGENT_SERVICES)
    
    # Step 4: Start monitoring and dashboards
    await fix_service_group("Dashboard Services", DASHBOARD_SERVICES)
    
    # Step 5: Final status check
    logger.info("=== Final System Status ===")
    running, total, healthy = await check_system_status()
    
    if running == total:
        logger.info("[CELEBRATE] ALL SERVICES ARE RUNNING!")
    elif running > total * 0.8:  # 80% success rate
        logger.info(str(f"[OK] Most services running ({running}/{total}")
    else:
        logger.warning(str(f"[WARN] Some services still having issues ({running}/{total}")
    
    # Step 6: Try to restart any failed services one more time
    if running < total:
        logger.info("[SYNC] Attempting to restart failed services...")
        cmd = ["docker-compose", "up", "-d"] + ALL_SERVICES
        success, stdout, stderr = await run_command(cmd, timeout=600)
        
        if success:
            logger.info("[OK] Final restart command completed")
            await asyncio.sleep(15)
            await check_system_status()
        else:
            logger.error(str(f"[ERROR] Final restart failed: {stderr}")
    
    logger.info("🏁 LangChain MCP System Coordination Complete!")

if __name__ == "__main__":
    try:
        asyncio.run(langchain_coordinate_fixes())
        print("\n[CELEBRATE] LangChain coordination completed successfully!")
    except KeyboardInterrupt:
        print("\n[STOP] LangChain coordination interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] LangChain coordination failed: {e}")
        sys.exit(1)