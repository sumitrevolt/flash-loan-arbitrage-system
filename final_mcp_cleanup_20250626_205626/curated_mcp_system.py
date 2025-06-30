#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Curated MCP System - LangChain + AutoGen Focus
Best 21 MCP Servers + 10-21 AI Agents + Docker + Cursor Integration
"""

from pathlib import Path
import asyncio
import json
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CuratedMCPSystem:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.curated_dir = self.base_dir / "curated_mcp_system"
        
        # Curated directories
        self.mcp_dir = self.curated_dir / "mcp_servers"
        self.agents_dir = self.curated_dir / "ai_agents"
        self.docker_dir = self.curated_dir / "docker"
        self.config_dir = self.curated_dir / "config"
        
        # Best 21 MCP servers (curated for quality and functionality)
        self.best_mcp_servers = [
            # Core LangChain & AutoGen Integration (Priority 1)
            "complete_langchain_mcp_integration.py",
            "langchain_mcp_orchestrator.py",
            "unified_mcp_orchestration_manager.py",
            "unified_mcp_coordinator.py",
            
            # Flash Loan & DeFi Core (Priority 1) 
            "aave_flash_loan_mcp_server.py",
            "working_flash_loan_mcp.py",
            "dex_aggregator_mcp_server.py",
            
            # Blockchain & EVM (Priority 1)
            "evm_mcp_server.py",
            "real_time_price_mcp_server.py",
            "clean_matic_mcp_server.py",
            
            # AI & Code Intelligence (Priority 2)
            "mcp_github_copilot_server_enhanced.py",
            "llm_code_suggestion_mcp_server.py",
            "code_editing_mcp_server.py",
            
            # System Management (Priority 2)
            "enhanced_mcp_server_manager.py",
            "mcp_server_manager.py",
            "monitoring_mcp_server.py",
            
            # Integration & Communication (Priority 3)
            "clean_context7_mcp_server.py",
            "mcp_integration_bridge.py",
            "github_mcp_integration.py",
            
            # Specialized Tools (Priority 3)
            "risk_management_mcp_server.py",
            "profit_optimizer_mcp_server.py"

        
        # Best AI agents by category (10-21 agents total)
        self.best_ai_agents = {
            "arbitrage": [
                "arbitrage_detector.py",  # Enhanced arbitrage detection
                "flash_loan_optimizer.py",  # Flash loan optimization
                "route_optimizer.py"  # Route optimization
            ],
            "risk": [
                "risk_manager.py",  # Comprehensive risk analysis
                "security_analyst.py",  # Security analysis
                "compliance_checker.py"  # Compliance checking
            ],
            "market": [
                "market_analyzer.py",  # Market analysis
                "liquidity_monitor.py",  # Liquidity monitoring
                "gas_optimizer.py"  # Gas optimization
            ],
            "transaction": [
                "transaction_executor.py"  # Transaction execution
            ],
            "general": [
                # We'll create enhanced general agents
                "langchain_coordinator.py",  # LangChain coordination
                "autogen_orchestrator.py",  # AutoGen orchestration
                "system_monitor.py",  # System monitoring
                "data_processor.py",  # Data processing
                "api_gateway.py"  # API gateway


    
    def create_directories(self):
        """Create curated directory structure"""
        logger.info("Creating curated directory structure...")
        
        directories = [
            self.curated_dir,
            self.mcp_dir,
            self.agents_dir,
            self.docker_dir,
            self.config_dir

        
        # Create agent category directories
        for category in self.best_ai_agents.keys():
            directories.append(self.agents_dir / category)
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def copy_best_mcp_servers(self):
        """Copy the best 21 MCP servers to curated directory"""
        logger.info("Copying best 21 MCP servers...")
        
        source_dir = self.base_dir / "mcp_servers"
        copied_count = 0
        
        for server_name in self.best_mcp_servers:
            source_file = source_dir / server_name
            dest_file = self.mcp_dir / server_name
            
            if source_file.exists():
                try:
                    shutil.copy2(source_file, dest_file)
                    logger.info(f"Copied: {server_name}")
                    copied_count += 1
                except Exception as e:
                    logger.error(f"Failed to copy {server_name}: {e}")
            else:
                logger.warning(f"Server not found: {server_name}")
        
        logger.info(f"Successfully copied {copied_count}/{len(self.best_mcp_servers)} MCP servers")
    
    def copy_best_ai_agents(self):
        """Copy and organize the best AI agents"""
        logger.info("Copying and organizing best AI agents...")
        
        source_dirs = [
            self.base_dir / "ai_agents",
            self.base_dir / "ai_agents_unified",
            self.base_dir / "autogen_agents"

        
        copied_count = 0
        
        for category, agents in self.best_ai_agents.items():
            category_dir = self.agents_dir / category
            
            for agent_name in agents:
                # Try to find the agent in source directories
                found = False
                
                for source_dir in source_dirs:
                    if source_dir.exists():
                        # Check in category subdirectories
                        for subdir in source_dir.iterdir():
                            if subdir.is_dir():
                                source_file = subdir / agent_name
                                if source_file.exists():
                                    dest_file = category_dir / agent_name
                                    try:
                                        shutil.copy2(source_file, dest_file)
                                        logger.info(f"Copied: {category}/{agent_name}")
                                        copied_count += 1
                                        found = True
                                        break
                                    except Exception as e:
                                        logger.error(f"Failed to copy {agent_name}: {e}")
                        
                        # Check in root directory
                        if not found:
                            source_file = source_dir / agent_name
                            if source_file.exists():
                                dest_file = category_dir / agent_name
                                try:
                                    shutil.copy2(source_file, dest_file)
                                    logger.info(f"Copied: {category}/{agent_name}")
                                    copied_count += 1
                                    found = True
                                except Exception as e:
                                    logger.error(f"Failed to copy {agent_name}: {e}")
                
                if not found:
                    # Create a template agent if not found
                    self.create_template_agent(category_dir, agent_name, category)
                    copied_count += 1
        
        total_agents = sum(len(agents) for agents in self.best_ai_agents.values())
        logger.info(f"Successfully set up {copied_count}/{total_agents} AI agents")
    
    def create_template_agent(self, category_dir: Path, agent_name: str, category: str):
        """Create a template agent if original not found"""
        logger.info(f"Creating template agent: {category}/{agent_name}")
        
        agent_file = category_dir / agent_name
        
        template_content = f'''#!/usr/bin/env python3
"""
{agent_name.replace('.py', '').replace('_', ' ').title()}
Category: {category}
"""

import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class {agent_name.replace('.py', '').replace('_', ' ').title().replace(' ', '')}:
    """
    {category.title()} agent for {agent_name.replace('.py', '').replace('_', ' ')}
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {{}}
        self.status = "initialized"
        
    async def initialize(self):
        """Initialize the agent"""
        logger.info(f"Initializing {{self.__class__.__name__}}")
        self.status = "ready"
        return True
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data according to agent's specialty"""
        logger.info(f"Processing data with {{self.__class__.__name__}}")
        
        # Template processing based on category
        if "{category}" == "arbitrage":
            return await self._process_arbitrage(data)
        elif "{category}" == "risk":
            return await self._process_risk(data)
        elif "{category}" == "market":
            return await self._process_market(data)
        elif "{category}" == "transaction":
            return await self._process_transaction(data)
        else:
            return await self._process_general(data)
    
    async def _process_arbitrage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process arbitrage-related data"""
        return {{
            "type": "arbitrage_analysis",
            "opportunities": [],
            "profit_potential": 0.0,
            "risk_level": "low"

    
    async def _process_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process risk-related data"""
        return {{
            "type": "risk_analysis",
            "risk_score": 0.5,
            "recommendations": [],
            "warnings": []

    
    async def _process_market(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process market-related data"""
        return {{
            "type": "market_analysis",
            "trends": [],
            "predictions": {{}}

    
    async def _process_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process transaction-related data"""
        return {{
            "type": "transaction_analysis",
            "status": "ready",
            "estimated_gas": 21000

    
    async def _process_general(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process general data"""
        return {{
            "type": "general_processing",
            "result": "processed",
            "data": data

    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {{
            "agent": self.__class__.__name__,
            "category": "{category}",
            "status": self.status,
            "config": self.config


if __name__ == "__main__":
    async def main():
        agent = {agent_name.replace('.py', '').replace('_', ' ').title().replace(' ', '')}()
        await agent.initialize()
        
        # Test processing
        test_data = {{"test": True, "timestamp": "now"}}
        result = await agent.process(test_data)
        print(f"Agent result: {{result}}")
    
    asyncio.run(main())
'''
        
        with open(agent_file, 'w') as f:
            f.write(template_content)
    
    def create_docker_configuration(self):
        """Create Docker configuration for the curated system"""
        logger.info("Creating Docker configuration...")
        
        # Docker Compose file
        docker_compose = {
            "version": "3.8",
            "services": {
                # MCP Servers
                "mcp-langchain": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile.mcp"
                    },
                    "ports": ["3000-3010:3000-3010"],
                    "environment": [
                        "MCP_SERVER_TYPE=langchain",
                        "PORT=3000"
                    ],
                    "volumes": [
                        "./mcp_servers:/app/mcp_servers:ro",
                        "./config:/app/config:ro"

                },
                "mcp-autogen": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile.mcp"
                    },
                    "ports": ["3011-3015:3011-3015"],
                    "environment": [
                        "MCP_SERVER_TYPE=autogen",
                        "PORT=3011"
                    ],
                    "volumes": [
                        "./mcp_servers:/app/mcp_servers:ro",
                        "./config:/app/config:ro"

                },
                "mcp-defi": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile.mcp"
                    },
                    "ports": ["3016-3020:3016-3020"],
                    "environment": [
                        "MCP_SERVER_TYPE=defi",
                        "PORT=3016"
                    ],
                    "volumes": [
                        "./mcp_servers:/app/mcp_servers:ro",
                        "./config:/app/config:ro"

                },
                
                # AI Agents
                "ai-arbitrage": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile.agents"
                    },
                    "ports": ["4000-4002:4000-4002"],
                    "environment": [
                        "AGENT_CATEGORY=arbitrage",
                        "PORT=4000"
                    ],
                    "volumes": [
                        "./ai_agents:/app/ai_agents:ro",
                        "./config:/app/config:ro"

                },
                "ai-risk": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile.agents"
                    },
                    "ports": ["4003-4005:4003-4005"],
                    "environment": [
                        "AGENT_CATEGORY=risk",
                        "PORT=4003"
                    ],
                    "volumes": [
                        "./ai_agents:/app/ai_agents:ro",
                        "./config:/app/config:ro"

                },
                "ai-market": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile.agents"
                    },
                    "ports": ["4006-4008:4006-4008"],
                    "environment": [
                        "AGENT_CATEGORY=market",
                        "PORT=4006"
                    ],
                    "volumes": [
                        "./ai_agents:/app/ai_agents:ro",
                        "./config:/app/config:ro"

                },
                "ai-general": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile.agents"
                    },
                    "ports": ["4009-4015:4009-4015"],
                    "environment": [
                        "AGENT_CATEGORY=general",
                        "PORT=4009"
                    ],
                    "volumes": [
                        "./ai_agents:/app/ai_agents:ro",
                        "./config:/app/config:ro"

                },
                
                # System Components
                "coordinator": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile.coordinator"
                    },
                    "ports": ["8000:8000"],
                    "environment": [
                        "COORDINATOR_TYPE=unified",
                        "PORT=8000"
                    ],
                    "volumes": [
                        "./config:/app/config:ro"
                    ],
                    "depends_on": [
                        "mcp-langchain",
                        "mcp-autogen", 
                        "mcp-defi",
                        "ai-arbitrage",
                        "ai-risk",
                        "ai-market",
                        "ai-general"


            },
            "networks": {
                "curated-mcp": {
                    "driver": "bridge"



        
        # Save Docker Compose
        try:
            import yaml
            with open(self.docker_dir / "docker-compose.yml", 'w') as f:
                yaml.dump(docker_compose, f, default_flow_style=False)
        except ImportError:
            # Fallback to JSON if PyYAML not available
            with open(self.docker_dir / "docker-compose.json", 'w') as f:
                json.dump(docker_compose, f, indent=2)
        
        # Create Dockerfiles
        self.create_dockerfiles()
    
    def create_dockerfiles(self):
        """Create Dockerfiles for different components"""
        
        # MCP Servers Dockerfile
        mcp_dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP servers
COPY mcp_servers/ ./mcp_servers/
COPY config/ ./config/

# Create startup script
COPY docker/start_mcp_servers.py ./start_mcp_servers.py

EXPOSE 3000-3020

CMD ["python", "start_mcp_servers.py"]
'''
        
        # AI Agents Dockerfile  
        agents_dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy AI agents
COPY ai_agents/ ./ai_agents/
COPY config/ ./config/

# Create startup script
COPY docker/start_ai_agents.py ./start_ai_agents.py

EXPOSE 4000-4020

CMD ["python", "start_ai_agents.py"]
'''
        
        # Coordinator Dockerfile
        coordinator_dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy coordinator
COPY config/ ./config/
COPY docker/coordinator.py ./coordinator.py

EXPOSE 8000

CMD ["python", "coordinator.py"]
'''
        
        # Save Dockerfiles
        with open(self.docker_dir / "Dockerfile.mcp", 'w') as f:
            f.write(mcp_dockerfile)
        
        with open(self.docker_dir / "Dockerfile.agents", 'w') as f:
            f.write(agents_dockerfile)
        
        with open(self.docker_dir / "Dockerfile.coordinator", 'w') as f:
            f.write(coordinator_dockerfile)
    
    def create_cursor_integration(self):
        """Create optimized Cursor MCP integration"""
        logger.info("Creating Cursor MCP integration...")
        
        cursor_config = {
            "mcpServers": {
                # Core LangChain Integration
                "curated-langchain": {
                    "command": "docker",
                    "args": [
                        "exec", "curated_mcp_system-mcp-langchain-1",
                        "python", "/app/mcp_servers/complete_langchain_mcp_integration.py"
                    ],
                    "disabled": False,
                    "autoApprove": [],
                    "alwaysAllow": [
                        "langchain_query",
                        "autogen_coordination",
                        "agent_management",
                        "system_status"

                },
                
                # Flash Loan & DeFi
                "curated-defi": {
                    "command": "docker", 
                    "args": [
                        "exec", "curated_mcp_system-mcp-defi-1",
                        "python", "/app/mcp_servers/aave_flash_loan_mcp_server.py"
                    ],
                    "disabled": False,
                    "autoApprove": [],
                    "alwaysAllow": [
                        "flash_loan_analysis",
                        "arbitrage_detection",
                        "price_monitoring",
                        "risk_assessment"

                },
                
                # AI Agents Coordination
                "curated-agents": {
                    "command": "docker",
                    "args": [
                        "exec", "curated_mcp_system-coordinator-1", 
                        "python", "/app/coordinator.py"
                    ],
                    "disabled": False,
                    "autoApprove": [],
                    "alwaysAllow": [
                        "agent_status",
                        "agent_command",
                        "system_metrics",
                        "health_check"




        
        # Save Cursor config
        cursor_dir = self.curated_dir / ".kilocode"
        cursor_dir.mkdir(exist_ok=True)
        
        with open(cursor_dir / "mcp.json", 'w') as f:
            json.dump(cursor_config, f, indent=2)
    
    def create_system_configuration(self):
        """Create system configuration files"""
        logger.info("Creating system configuration...")
        
        # Master configuration
        master_config = {
            "system": {
                "name": "Curated MCP System",
                "version": "1.0.0",
                "focus": ["langchain", "autogen", "defi", "flash_loans"]
            },
            "mcp_servers": {
                "count": len(self.best_mcp_servers),
                "categories": {
                    "core_integration": 4,
                    "defi_blockchain": 6, 
                    "ai_intelligence": 5,
                    "system_management": 3,
                    "integration_tools": 3
                },
                "ports": {
                    "langchain": "3000-3010",
                    "autogen": "3011-3015", 
                    "defi": "3016-3020"

            },
            "ai_agents": {
                "total_count": sum(len(agents) for agents in self.best_ai_agents.values()),
                "categories": self.best_ai_agents,
                "ports": {
                    "arbitrage": "4000-4002",
                    "risk": "4003-4005",
                    "market": "4006-4008",
                    "transaction": "4009",
                    "general": "4010-4015"

            },
            "integration": {
                "cursor_mcp": True,
                "docker_compose": True,
                "health_monitoring": True,
                "auto_restart": True


        
        # Save master config
        with open(self.config_dir / "master_config.json", 'w') as f:
            json.dump(master_config, f, indent=2)
        
        # Create requirements.txt
        requirements = [
            "asyncio",
            "aiohttp",
            "fastapi",
            "uvicorn",
            "pydantic",
            "langchain",
            "langchain-community", 
            "langchain-openai",
            "autogen-agentchat",
            "web3",
            "requests",
            "pyyaml",
            "docker",
            "psutil"

        
        with open(self.curated_dir / "requirements.txt", 'w') as f:
            f.write('\n'.join(requirements))
    
    async def run_setup(self):
        """Run the complete curated system setup"""
        logger.info("🎯 Setting up Curated MCP System - LangChain + AutoGen Focus")
        
        try:
            # Create directory structure
            self.create_directories()
            
            # Copy best components
            self.copy_best_mcp_servers()
            self.copy_best_ai_agents()
            
            # Create configurations
            self.create_docker_configuration()
            self.create_cursor_integration()
            self.create_system_configuration()
            
            logger.info("✅ Curated MCP System setup complete!")
            logger.info(f"📁 System location: {self.curated_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False

async def main():
    system = CuratedMCPSystem()
    success = await system.run_setup()
    
    if success:
        print("\n🎉 SUCCESS: Curated MCP System ready!")
        print(f"📍 Location: {system.curated_dir}")
        print("🚀 Next steps:")
        print("  1. cd curated_mcp_system")
        print("  2. docker-compose -f docker/docker-compose.yml up -d")
        print("  3. Open Cursor IDE (MCP auto-configured)")
    else:
        print("❌ Setup failed. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main()) 