import asyncio
from src.langchain_coordinators.langchain_final_coordinator_fixed import LangChainFinalCoordinator

async def command_multiple_agents():
    """Example of commanding multiple LangChain agents"""
    
    # Initialize the coordinator
    coordinator = LangChainFinalCoordinator()
    await coordinator.initialize()
    
    # Command multiple agents for different tasks
    tasks = [
        {
            "agent_type": "mcp_server",
            "task": "Analyze flash loan opportunities",
            "server": "flash-loan-mcp"
        },
        {
            "agent_type": "blockchain_agent", 
            "task": "Monitor DEX prices",
            "server": "dex-services-mcp"
        },
        {
            "agent_type": "risk_agent",
            "task": "Assess arbitrage risks",
            "server": "price-oracle-mcp"
        }
    ]
    
    # Execute final coordination which starts all MCP servers and agents
    print("🚀 Starting LangChain coordination system...")
    success = await coordinator.execute_final_coordination()
    
    if success:
        print("✅ All agents and MCP servers are now coordinated and running")
        
        # Test connectivity to see which services are available
        connectivity_results = await coordinator.test_service_connectivity()
        
        print("\n📊 Agent Status Report:")
        for task in tasks:
            service_name = task["server"].replace("-mcp", "").replace("-", " ").title()
            status = "🟢 Available" if any(service_name.lower() in key.lower() for key in connectivity_results.keys()) else "🔴 Not Available"
            print(f"  {task['agent_type']}: {task['task']} -> {status}")
    else:
        print("❌ Coordination failed - some agents may not be available")

if __name__ == "__main__":
    asyncio.run(command_multiple_agents())
