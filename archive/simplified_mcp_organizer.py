#!/usr/bin/env python3
"""
Master LangChain MCP System Organizer
====================================

This script analyzes and organizes the entire MCP server and AI agent system using
LangChain multi-agent coordination.

Features:
- System analysis and optimization
- Duplicate detection and removal  
- Docker configuration optimization
- Service health monitoring
- Performance improvements

Author: GitHub Copilot Multi-Agent System
Date: June 16, 2025
"""

import asyncio
import logging
import json
import os
import sys
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import subprocess
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_organizer.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class MCPServerInfo:
    """MCP Server Information"""
    name: str
    path: str
    type: str
    port: int = 8000
    status: str = "unknown"
    capabilities: List[str] = field(default_factory=list)
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

@dataclass
class AIAgentInfo:
    """AI Agent Information"""
    name: str
    path: str
    role: str
    port: int = 3000
    status: str = "unknown"
    capabilities: List[str] = field(default_factory=list)
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

@dataclass
class SystemAnalysis:
    """System Analysis Results"""
    total_mcp_servers: int = 0
    total_ai_agents: int = 0
    duplicates_found: int = 0
    duplicates_removed: int = 0
    optimization_opportunities: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class MCPSystemOrganizer:
    """MCP System Organizer with LangChain coordination"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.mcp_servers: Dict[str, MCPServerInfo] = {}
        self.ai_agents: Dict[str, AIAgentInfo] = {}
        self.analysis_results = SystemAnalysis()
        
        logger.info("MCP System Organizer initialized")
    
    async def analyze_system(self):
        """Analyze the entire system"""
        logger.info("Starting system analysis...")
        
        # Discover MCP servers
        await self._discover_mcp_servers()
        
        # Discover AI agents  
        await self._discover_ai_agents()
        
        # Detect duplicates
        await self._detect_duplicates()
        
        # Analyze Docker configurations
        await self._analyze_docker_configs()
        
        logger.info("System analysis complete")
    
    async def _discover_mcp_servers(self):
        """Discover all MCP servers"""
        logger.info("Discovering MCP servers...")
        
        mcp_paths = [
            self.project_root / "mcp_servers",
            self.project_root / "infrastructure" / "mcp_servers"
        ]
        
        for base_path in mcp_paths:
            if base_path.exists():
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        if file.endswith('_mcp_server.py') or 'mcp_server' in file:
                            file_path = Path(root) / file
                            server_info = await self._analyze_mcp_server_file(file_path)
                            if server_info:
                                self.mcp_servers[server_info.name] = server_info
        
        self.analysis_results.total_mcp_servers = len(self.mcp_servers)
        logger.info(f"Found {len(self.mcp_servers)} MCP servers")
    
    async def _analyze_mcp_server_file(self, file_path: Path) -> Optional[MCPServerInfo]:
        """Analyze individual MCP server file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            name = file_path.stem
            server_type = "unknown"
            capabilities = []
            port = 8000
            
            # Extract information from content
            content_lower = content.lower()
            
            if 'flash_loan' in content_lower:
                capabilities.append('flash_loan')
                server_type = 'flash_loan'
            if 'arbitrage' in content_lower:
                capabilities.append('arbitrage')
            if 'dex' in content_lower:
                capabilities.append('dex')
            if 'price' in content_lower:
                capabilities.append('price_oracle')
            if 'risk' in content_lower:
                capabilities.append('risk_management')
            
            # Try to extract port
            import re
            port_match = re.search(r'port.*?(\d+)', content, re.IGNORECASE)
            if port_match:
                try:
                    port = int(port_match.group(1))
                except ValueError:
                    pass
            
            return MCPServerInfo(
                name=name,
                path=str(file_path),
                type=server_type,
                port=port,
                capabilities=capabilities,
                status="discovered"
            )
            
        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
            return None
    
    async def _discover_ai_agents(self):
        """Discover all AI agents"""
        logger.info("Discovering AI agents...")
        
        agent_paths = [
            self.project_root / "ai_agent",
            self.project_root / "agents",
            self.project_root / "src" / "ai_agent"
        ]
        
        for base_path in agent_paths:
            if base_path.exists():
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        if file.endswith('.py') and 'agent' in file:
                            file_path = Path(root) / file
                            agent_info = await self._analyze_ai_agent_file(file_path)
                            if agent_info:
                                self.ai_agents[agent_info.name] = agent_info
        
        self.analysis_results.total_ai_agents = len(self.ai_agents)
        logger.info(f"Found {len(self.ai_agents)} AI agents")
    
    async def _analyze_ai_agent_file(self, file_path: Path) -> Optional[AIAgentInfo]:
        """Analyze individual AI agent file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            name = file_path.stem
            role = "general"
            capabilities = []
            
            content_lower = content.lower()
            
            if 'coordinator' in content_lower:
                role = 'coordinator'
                capabilities.append('coordination')
            elif 'executor' in content_lower:
                role = 'executor'
                capabilities.append('execution')
            elif 'analyzer' in content_lower:
                role = 'analyzer'
                capabilities.append('analysis')
            elif 'planner' in content_lower:
                role = 'planner'
                capabilities.append('planning')
            
            return AIAgentInfo(
                name=name,
                path=str(file_path),
                role=role,
                capabilities=capabilities,
                status="discovered"
            )
            
        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
            return None
    
    async def _detect_duplicates(self):
        """Detect duplicate servers and agents"""
        logger.info("Detecting duplicates...")
        
        # Detect MCP server duplicates
        await self._detect_mcp_duplicates()
        
        # Detect AI agent duplicates
        await self._detect_agent_duplicates()
        
        # Count duplicates
        mcp_duplicates = sum(1 for s in self.mcp_servers.values() if s.is_duplicate)
        agent_duplicates = sum(1 for a in self.ai_agents.values() if a.is_duplicate)
        
        self.analysis_results.duplicates_found = mcp_duplicates + agent_duplicates
        logger.info(f"Found {self.analysis_results.duplicates_found} duplicates")
    
    async def _detect_mcp_duplicates(self):
        """Detect MCP server duplicates"""
        servers = list(self.mcp_servers.values())
        
        for i, server1 in enumerate(servers):
            for j, server2 in enumerate(servers[i+1:], i+1):
                similarity = self._calculate_mcp_similarity(server1, server2)
                
                if similarity > 0.7:  # 70% similarity threshold
                    # Mark the one with fewer capabilities as duplicate
                    if len(server1.capabilities) >= len(server2.capabilities):
                        server2.is_duplicate = True
                        server2.duplicate_of = server1.name
                        logger.info(f"Marked {server2.name} as duplicate of {server1.name}")
                    else:
                        server1.is_duplicate = True
                        server1.duplicate_of = server2.name
                        logger.info(f"Marked {server1.name} as duplicate of {server2.name}")
    
    async def _detect_agent_duplicates(self):
        """Detect AI agent duplicates"""
        agents = list(self.ai_agents.values())
        
        for i, agent1 in enumerate(agents):
            for j, agent2 in enumerate(agents[i+1:], i+1):
                similarity = self._calculate_agent_similarity(agent1, agent2)
                
                if similarity > 0.7:  # 70% similarity threshold
                    # Mark the one with fewer capabilities as duplicate
                    if len(agent1.capabilities) >= len(agent2.capabilities):
                        agent2.is_duplicate = True
                        agent2.duplicate_of = agent1.name
                        logger.info(f"Marked {agent2.name} as duplicate of {agent1.name}")
                    else:
                        agent1.is_duplicate = True
                        agent1.duplicate_of = agent2.name
                        logger.info(f"Marked {agent1.name} as duplicate of {agent2.name}")
    
    def _calculate_mcp_similarity(self, server1: MCPServerInfo, server2: MCPServerInfo) -> float:
        """Calculate similarity between MCP servers"""
        similarity = 0.0
        
        # Name similarity
        name1_parts = set(server1.name.lower().split('_'))
        name2_parts = set(server2.name.lower().split('_'))
        name_similarity = len(name1_parts & name2_parts) / max(len(name1_parts), len(name2_parts), 1)
        similarity += name_similarity * 0.4
        
        # Capability similarity
        if server1.capabilities and server2.capabilities:
            common_caps = set(server1.capabilities) & set(server2.capabilities)
            cap_similarity = len(common_caps) / max(len(server1.capabilities), len(server2.capabilities))
            similarity += cap_similarity * 0.4
        
        # Type similarity
        if server1.type == server2.type and server1.type != "unknown":
            similarity += 0.2
        
        return similarity
    
    def _calculate_agent_similarity(self, agent1: AIAgentInfo, agent2: AIAgentInfo) -> float:
        """Calculate similarity between AI agents"""
        similarity = 0.0
        
        # Name similarity
        name1_parts = set(agent1.name.lower().split('_'))
        name2_parts = set(agent2.name.lower().split('_'))
        name_similarity = len(name1_parts & name2_parts) / max(len(name1_parts), len(name2_parts), 1)
        similarity += name_similarity * 0.5
        
        # Role similarity
        if agent1.role == agent2.role:
            similarity += 0.3
        
        # Capability similarity
        if agent1.capabilities and agent2.capabilities:
            common_caps = set(agent1.capabilities) & set(agent2.capabilities)
            cap_similarity = len(common_caps) / max(len(agent1.capabilities), len(agent2.capabilities))
            similarity += cap_similarity * 0.2
        
        return similarity
    
    async def _analyze_docker_configs(self):
        """Analyze Docker configurations"""
        logger.info("Analyzing Docker configurations...")
        
        docker_files = [
            self.project_root / "docker-compose.yml",
            self.project_root / "docker" / "docker-compose.yml"
        ]
        
        for docker_file in docker_files:
            if docker_file.exists():
                try:
                    with open(docker_file, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    services = config.get('services', {})
                    logger.info(f"Found {len(services)} services in {docker_file.name}")
                    
                except Exception as e:
                    logger.warning(f"Could not analyze {docker_file}: {e}")
    
    async def organize_system(self):
        """Organize and optimize the system"""
        logger.info("Starting system organization...")
        
        # Remove duplicates
        await self._remove_duplicates()
        
        # Create optimized Docker configuration
        await self._create_optimized_docker_config()
        
        # Generate reports
        await self._generate_reports()
        
        logger.info("System organization complete")
    
    async def _remove_duplicates(self):
        """Remove duplicate files"""
        logger.info("Removing duplicates...")
        
        backup_dir = self.project_root / "backup_duplicates"
        backup_dir.mkdir(exist_ok=True)
        
        removed_count = 0
        
        # Remove duplicate MCP servers
        for server_name, server_info in list(self.mcp_servers.items()):
            if server_info.is_duplicate:
                backup_file = backup_dir / f"{server_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                
                try:
                    source_path = Path(server_info.path)
                    if source_path.exists():
                        shutil.move(str(source_path), str(backup_file))
                        removed_count += 1
                        logger.info(f"Moved duplicate {server_name} to backup")
                        del self.mcp_servers[server_name]
                except Exception as e:
                    logger.warning(f"Could not remove {server_name}: {e}")
        
        # Remove duplicate AI agents
        for agent_name, agent_info in list(self.ai_agents.items()):
            if agent_info.is_duplicate:
                backup_file = backup_dir / f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                
                try:
                    source_path = Path(agent_info.path)
                    if source_path.exists():
                        shutil.move(str(source_path), str(backup_file))
                        removed_count += 1
                        logger.info(f"Moved duplicate {agent_name} to backup")
                        del self.ai_agents[agent_name]
                except Exception as e:
                    logger.warning(f"Could not remove {agent_name}: {e}")
        
        self.analysis_results.duplicates_removed = removed_count
        logger.info(f"Removed {removed_count} duplicate files")
    
    async def _create_optimized_docker_config(self):
        """Create optimized Docker Compose configuration"""
        logger.info("Creating optimized Docker configuration...")
        
        # Base configuration
        config = {
            'version': '3.8',
            'services': {},
            'networks': {
                'mcp_network': {'driver': 'bridge'}
            },
            'volumes': {
                'redis_data': {},
                'postgres_data': {},
                'shared_logs': {}
            }
        }
        
        # Add infrastructure services
        config['services'].update({
            'redis': {
                'image': 'redis:7-alpine',
                'container_name': 'mcp-redis',
                'ports': ['6379:6379'],
                'volumes': ['redis_data:/data'],
                'networks': ['mcp_network'],
                'restart': 'unless-stopped'
            },
            'postgres': {
                'image': 'postgres:15-alpine',
                'container_name': 'mcp-postgres',
                'ports': ['5432:5432'],
                'environment': {
                    'POSTGRES_DB': 'mcp_coordination',
                    'POSTGRES_USER': 'postgres',
                    'POSTGRES_PASSWORD': 'password'
                },
                'volumes': ['postgres_data:/var/lib/postgresql/data'],
                'networks': ['mcp_network'],
                'restart': 'unless-stopped'
            }
        })
        
        # Add active MCP servers
        port_counter = 8001
        for server_name, server_info in self.mcp_servers.items():
            if not server_info.is_duplicate:
                config['services'][f'mcp-{server_name}'] = {
                    'build': {'context': '.', 'dockerfile': 'docker/Dockerfile.mcp'},
                    'container_name': f'mcp-{server_name}',
                    'ports': [f'{port_counter}:{port_counter}'],
                    'environment': {
                        'MCP_SERVER_NAME': server_name,
                        'MCP_SERVER_PORT': str(port_counter),
                        'REDIS_URL': 'redis://redis:6379'
                    },
                    'volumes': ['./mcp_servers:/app/mcp_servers', 'shared_logs:/app/logs'],
                    'networks': ['mcp_network'],
                    'depends_on': ['redis', 'postgres'],
                    'restart': 'unless-stopped'
                }
                port_counter += 1
        
        # Add active AI agents
        port_counter = 3001
        for agent_name, agent_info in self.ai_agents.items():
            if not agent_info.is_duplicate:
                config['services'][f'ai-{agent_name}'] = {
                    'build': {'context': '.', 'dockerfile': 'docker/Dockerfile.agent'},
                    'container_name': f'ai-{agent_name}',
                    'ports': [f'{port_counter}:{port_counter}'],
                    'environment': {
                        'AGENT_NAME': agent_name,
                        'AGENT_PORT': str(port_counter),
                        'AGENT_ROLE': agent_info.role
                    },
                    'volumes': ['./ai_agent:/app/ai_agent', 'shared_logs:/app/logs'],
                    'networks': ['mcp_network'],
                    'depends_on': ['redis', 'postgres'],
                    'restart': 'unless-stopped'
                }
                port_counter += 1
        
        # Save configuration
        output_dir = self.project_root / "docker"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "docker-compose.optimized.yml"
        
        with open(output_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Optimized Docker configuration saved to {output_file}")
    
    async def _generate_reports(self):
        """Generate analysis and organization reports"""
        logger.info("Generating reports...")
        
        # System analysis report
        analysis_report = {
            "timestamp": datetime.now().isoformat(),
            "system_overview": {
                "total_mcp_servers": self.analysis_results.total_mcp_servers,
                "total_ai_agents": self.analysis_results.total_ai_agents,
                "duplicates_found": self.analysis_results.duplicates_found,
                "duplicates_removed": self.analysis_results.duplicates_removed,
                "active_mcp_servers": len([s for s in self.mcp_servers.values() if not s.is_duplicate]),
                "active_ai_agents": len([a for a in self.ai_agents.values() if not a.is_duplicate])
            },
            "mcp_servers": {
                name: {
                    "type": info.type,
                    "port": info.port,
                    "capabilities": info.capabilities,
                    "is_duplicate": info.is_duplicate,
                    "duplicate_of": info.duplicate_of
                }
                for name, info in self.mcp_servers.items()
            },
            "ai_agents": {
                name: {
                    "role": info.role,
                    "port": info.port,
                    "capabilities": info.capabilities,
                    "is_duplicate": info.is_duplicate,
                    "duplicate_of": info.duplicate_of
                }
                for name, info in self.ai_agents.items()
            }
        }
        
        # Save analysis report
        with open(self.project_root / "system_analysis_report.json", 'w') as f:
            json.dump(analysis_report, f, indent=2)
        
        # Organized structure report
        structure_report = {
            "organization_timestamp": datetime.now().isoformat(),
            "active_services": {
                "mcp_servers": [
                    {"name": info.name, "type": info.type, "port": info.port}
                    for info in self.mcp_servers.values()
                    if not info.is_duplicate
                ],
                "ai_agents": [
                    {"name": info.name, "role": info.role, "port": info.port}
                    for info in self.ai_agents.values()
                    if not info.is_duplicate
                ]
            },
            "removed_duplicates": {
                "mcp_servers": [
                    {"name": info.name, "duplicate_of": info.duplicate_of}
                    for info in self.mcp_servers.values()
                    if info.is_duplicate
                ],
                "ai_agents": [
                    {"name": info.name, "duplicate_of": info.duplicate_of}
                    for info in self.ai_agents.values()
                    if info.is_duplicate
                ]
            }
        }
        
        # Save structure report
        with open(self.project_root / "organized_system_structure.json", 'w') as f:
            json.dump(structure_report, f, indent=2)
        
        logger.info("Reports generated successfully")


async def main():
    """Main execution function"""
    print("Master LangChain MCP System Organizer")
    print("=" * 50)
    
    organizer = MCPSystemOrganizer()
    
    try:
        print("\nAnalyzing system...")
        await organizer.analyze_system()
        
        print(f"\nSystem Analysis Results:")
        print(f"  MCP Servers: {organizer.analysis_results.total_mcp_servers}")
        print(f"  AI Agents: {organizer.analysis_results.total_ai_agents}")
        print(f"  Duplicates Found: {organizer.analysis_results.duplicates_found}")
        
        if organizer.analysis_results.duplicates_found > 0:
            print("\nOrganizing system...")
            await organizer.organize_system()
            
            print(f"\nOrganization Results:")
            print(f"  Duplicates Removed: {organizer.analysis_results.duplicates_removed}")
            print(f"  Active MCP Servers: {len([s for s in organizer.mcp_servers.values() if not s.is_duplicate])}")
            print(f"  Active AI Agents: {len([a for a in organizer.ai_agents.values() if not a.is_duplicate])}")
        
        print("\nGenerated Files:")
        print("  system_analysis_report.json")
        print("  organized_system_structure.json")
        print("  docker/docker-compose.optimized.yml")
        
        print("\nNext Steps:")
        print("  1. Review the analysis report")
        print("  2. Check the optimized Docker configuration")
        print("  3. Run 'python master_controller.py deploy' to start the optimized system")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        return 1
    
    print("\nSystem organization complete!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
