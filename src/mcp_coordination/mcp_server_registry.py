# -*- coding: utf-8 -*-
"""
MCP Server Registry - Central discovery and management system for all MCP servers

This module provides centralized discovery, registration, and management
of all MCP servers in the flash loan arbitrage system.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import json
import logging
import os
import subprocess
import time

from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ServerTier(Enum):
    """Server tier classification for load balancing and priority"""
    CRITICAL = "critical"      # Tier 1 - Always active, high priority
    INTEGRATION = "integration"  # Tier 2 - Load balanced
    SPECIALIZED = "specialized"  # Tier 3 - Demand-based routing


class ServerProtocol(Enum):
    """Supported MCP communication protocols"""
    HTTP = "http"
    WEBSOCKET = "websocket" 
    STDIO = "stdio"
    SSE = "sse"


class ServerStatus(Enum):
    """Current status of MCP server"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServerCapability:
    """Represents a server capability"""
    name: str
    description: str
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    response_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPServerInfo:
    """Complete information about an MCP server"""
    # Basic identification
    server_id: str
    name: str
    description: str
    tier: ServerTier
    
    # Network configuration
    protocol: ServerProtocol
    host: str = "localhost"
    port: int = 3000
    path: str = ""
    
    # Server metadata
    version: str = "1.0.0"
    capabilities: List[ServerCapability] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Runtime information
    status: ServerStatus = ServerStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    startup_time: Optional[datetime] = None
    
    # Performance metrics
    response_times: List[float] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    active_connections: int = 0
    max_connections: int = 100
    
    # Configuration
    config_file: Optional[str] = None
    executable_path: Optional[str] = None
    startup_command: Optional[str] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)
    
    # Health and monitoring
    health_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    circuit_breaker_open: bool = False
    last_error: Optional[str] = None
    
    def get_base_url(self) -> str:
        """Get the base URL for this server"""
        protocol_str = "https" if self.protocol == ServerProtocol.HTTP and self.port == 443 else self.protocol.value
        if self.protocol in [ServerProtocol.HTTP, ServerProtocol.WEBSOCKET]:
            return f"{protocol_str}://{self.host}:{self.port}{self.path}"
        return f"{self.host}:{self.port}"
    
    def get_health_url(self) -> str:
        """Get the health check URL"""
        if self.protocol in [ServerProtocol.HTTP, ServerProtocol.WEBSOCKET]:
            return f"{self.get_base_url()}{self.health_endpoint}"
        return self.get_base_url()


class MCPServerRegistry:
    """
    Central registry for discovering, managing, and coordinating all MCP servers
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.servers: Dict[str, MCPServerInfo] = {}
        self.server_processes: Dict[str, subprocess.Popen] = {}
        
        # Discovery configuration
        self.discovery_paths = [
            "mcp_servers/",
            "src/mcp_coordination/",
            "src/langchain_integration/",
            "src/autogen_integration/"

        
        # Auto-discovery patterns
        self.server_patterns = {
            "*.py": "python",
            "*.js": "node", 
            "*.ts": "npx ts-node",
            "Dockerfile*": "docker"

        
        # Tier classifications based on server names/types
        self.tier_classification = {
            "critical": [
                "filesystem", "context7", "supermemory", "taskmanager",
                "enhanced_mcp_server_manager", "unified_mcp_coordinator"
            ],
            "integration": [
                "langchain_mcp_orchestrator", "complete_langchain_mcp_integration",
                "autogen_coordinator", "mcp_integration_bridge", "enhanced_mcp_dashboard"
            ],
            "specialized": [
                "aave_flash_loan", "flash_loan_mcp", "mcp_arbitrage_server",
                "mcp_risk_manager", "mcp_defi_analyzer", "profit_optimizer",
                "real_time_price", "risk_management", "monitoring_mcp"


        
        # Performance tracking
        self.discovery_stats = {
            "total_discovered": 0,
            "auto_registered": 0,
            "manual_registered": 0,
            "failed_discoveries": 0,
            "last_discovery_time": None

        
        # Background tasks
        self.discovery_task: Optional[asyncio.Task] = None
        self.health_monitor_task: Optional[asyncio.Task] = None
        
        logger.info("[INIT] MCP Server Registry initialized")
    
    async def initialize(self):
        """Initialize the registry and discover existing servers"""
        try:
            logger.info("[INIT] Starting MCP Server Registry initialization...")
            
            # Load any pre-configured servers
            await self._load_configured_servers()
            
            # Perform initial discovery
            await self.discover_servers()
            
            # Start background monitoring
            self.health_monitor_task = asyncio.create_task(self._health_monitoring_loop())
            self.discovery_task = asyncio.create_task(self._periodic_discovery_loop())
            
            logger.info(f"[OK] Registry initialized with {len(self.servers)} servers discovered")
            
        except Exception as e:
            logger.error(f"[ERROR] Registry initialization failed: {e}")
            raise
    
    async def discover_servers(self) -> List[MCPServerInfo]:
        """
        Discover all MCP servers in the project
        
        Returns:
            List of discovered server information
        """
        discovered_servers = []
        
        try:
            logger.info("[DISCOVERY] Starting comprehensive server discovery...")
            
            for discovery_path in self.discovery_paths:
                if os.path.exists(discovery_path):
                    servers = await self._discover_in_path(discovery_path)
                    discovered_servers.extend(servers)
            
            # Register discovered servers
            for server_info in discovered_servers:
                await self.register_server(server_info)
            
            # Update statistics
            self.discovery_stats["total_discovered"] = len(discovered_servers)
            self.discovery_stats["last_discovery_time"] = datetime.now()
            
            logger.info(f"[OK] Discovery completed: {len(discovered_servers)} servers found")
            return discovered_servers
            
        except Exception as e:
            self.discovery_stats["failed_discoveries"] += 1
            logger.error(f"[ERROR] Server discovery failed: {e}")
            return discovered_servers
    
    async def _discover_in_path(self, path: str) -> List[MCPServerInfo]:
        """Discover MCP servers in a specific path"""
        discovered = []
        
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                return discovered
            
            # Look for Python MCP servers
            for py_file in path_obj.rglob("*mcp*.py"):
                if py_file.is_file() and not py_file.name.startswith("test_"):
                    server_info = await self._analyze_python_server(py_file)
                    if server_info:
                        discovered.append(server_info)
            
            # Look for Node.js MCP servers
            for js_file in path_obj.rglob("*.js"):
                if "mcp" in js_file.name.lower() and js_file.is_file():
                    server_info = await self._analyze_nodejs_server(js_file)
                    if server_info:
                        discovered.append(server_info)
            
            # Look for Docker-based servers
            for dockerfile in path_obj.rglob("Dockerfile*"):
                if "mcp" in dockerfile.read_text().lower():
                    server_info = await self._analyze_docker_server(dockerfile)
                    if server_info:
                        discovered.append(server_info)
            
            # Look for package.json files indicating Node.js MCP servers
            for package_json in path_obj.rglob("package.json"):
                server_info = await self._analyze_package_json(package_json)
                if server_info:
                    discovered.append(server_info)
            
            logger.debug(f"[DISCOVERY] Found {len(discovered)} servers in {path}")
            
        except Exception as e:
            logger.error(f"[ERROR] Discovery failed in path {path}: {e}")
        
        return discovered
    
    async def _analyze_python_server(self, file_path: Path) -> Optional[MCPServerInfo]:
        """Analyze a Python file to extract MCP server information"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Basic checks for MCP server patterns
            if not any(pattern in content.lower() for pattern in [
                "mcp", "model context protocol", "server", "fastapi", "flask"
            ]):
                return None
            
            server_name = file_path.stem
            server_id = f"python_{server_name}_{int(time.time())}"
            
            # Extract port from common patterns
            port = self._extract_port_from_content(content, default=3000)
            
            # Classify tier based on server name
            tier = self._classify_server_tier(server_name)
            
            # Try to detect capabilities
            capabilities = self._extract_capabilities_from_python(content)
            
            server_info = MCPServerInfo(
                server_id=server_id,
                name=server_name,
                description=f"Python MCP Server: {server_name}",
                tier=tier,
                protocol=ServerProtocol.HTTP,
                host="localhost",
                port=port,
                executable_path=str(file_path),
                startup_command=f"python {file_path}",
                capabilities=capabilities,
                config_file=str(file_path.parent / f"{server_name}_config.json") if (file_path.parent / f"{server_name}_config.json").exists() else None

            
            logger.debug(f"[DISCOVERY] Analyzed Python server: {server_name}")
            return server_info
            
        except Exception as e:
            logger.warning(f"[WARNING] Failed to analyze Python server {file_path}: {e}")
            return None
    
    async def _analyze_nodejs_server(self, file_path: Path) -> Optional[MCPServerInfo]:
        """Analyze a Node.js file to extract MCP server information"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            if not any(pattern in content.lower() for pattern in [
                "mcp", "express", "server", "listen"
            ]):
                return None
            
            server_name = file_path.stem
            server_id = f"nodejs_{server_name}_{int(time.time())}"
            
            port = self._extract_port_from_content(content, default=3000)
            tier = self._classify_server_tier(server_name)
            capabilities = self._extract_capabilities_from_nodejs(content)
            
            server_info = MCPServerInfo(
                server_id=server_id,
                name=server_name,
                description=f"Node.js MCP Server: {server_name}",
                tier=tier,
                protocol=ServerProtocol.HTTP,
                host="localhost",
                port=port,
                executable_path=str(file_path),
                startup_command=f"node {file_path}",
                capabilities=capabilities

            
            logger.debug(f"[DISCOVERY] Analyzed Node.js server: {server_name}")
            return server_info
            
        except Exception as e:
            logger.warning(f"[WARNING] Failed to analyze Node.js server {file_path}: {e}")
            return None
    
    async def _analyze_docker_server(self, dockerfile_path: Path) -> Optional[MCPServerInfo]:
        """Analyze a Dockerfile to extract MCP server information"""
        try:
            content = dockerfile_path.read_text(encoding='utf-8')
            
            if "mcp" not in content.lower():
                return None
            
            server_name = f"docker_{dockerfile_path.parent.name}"
            server_id = f"docker_{server_name}_{int(time.time())}"
            
            # Extract exposed port
            port = 3000
            for line in content.split('\n'):
                if line.strip().startswith('EXPOSE'):
                    try:
                        port = int(line.split()[1])
                        break
                    except (IndexError, ValueError):
                        pass
            
            tier = self._classify_server_tier(server_name)
            
            server_info = MCPServerInfo(
                server_id=server_id,
                name=server_name,
                description=f"Docker MCP Server: {server_name}",
                tier=tier,
                protocol=ServerProtocol.HTTP,
                host="localhost",
                port=port,
                executable_path=str(dockerfile_path),
                startup_command=f"docker build -t {server_name} {dockerfile_path.parent} && docker run -p {port}:{port} {server_name}",
                capabilities=[]

            
            logger.debug(f"[DISCOVERY] Analyzed Docker server: {server_name}")
            return server_info
            
        except Exception as e:
            logger.warning(f"[WARNING] Failed to analyze Docker server {dockerfile_path}: {e}")
            return None
    
    async def _analyze_package_json(self, package_json_path: Path) -> Optional[MCPServerInfo]:
        """Analyze package.json to extract MCP server information"""
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Check if this is an MCP-related package
            if not any(keyword in str(package_data).lower() for keyword in [
                "mcp", "model-context-protocol", "@modelcontextprotocol"
            ]):
                return None
            
            server_name = package_data.get("name", package_json_path.parent.name)
            server_id = f"npm_{server_name}_{int(time.time())}"
            
            # Look for port in scripts or config
            port = 3000
            scripts = package_data.get("scripts", {})
            for script in scripts.values():
                if isinstance(script, str):
                    extracted_port = self._extract_port_from_content(script, default=None)
                    if extracted_port:
                        port = extracted_port
                        break
            
            tier = self._classify_server_tier(server_name)
            
            # Determine startup command
            startup_command = "npm start"
            if "start" in scripts:
                startup_command = "npm start"
            elif "dev" in scripts:
                startup_command = "npm run dev"
            elif package_data.get("main"):
                startup_command = f"node {package_data['main']}"
            
            server_info = MCPServerInfo(
                server_id=server_id,
                name=server_name,
                description=package_data.get("description", f"NPM MCP Server: {server_name}"),
                tier=tier,
                protocol=ServerProtocol.HTTP,
                host="localhost",
                port=port,
                executable_path=str(package_json_path.parent),
                startup_command=startup_command,
                version=package_data.get("version", "1.0.0"),
                capabilities=[]

            
            logger.debug(f"[DISCOVERY] Analyzed NPM server: {server_name}")
            return server_info
            
        except Exception as e:
            logger.warning(f"[WARNING] Failed to analyze package.json {package_json_path}: {e}")
            return None
    
    def _extract_port_from_content(self, content: str, default: int = 3000) -> int:
        """Extract port number from file content"""
        import re
        
        # Common port patterns
        patterns = [
            r'port[:\s=]+(\d+)',
            r'listen\([\'"]?(\d+)[\'"]?\)',
            r'PORT[:\s=]+(\d+)',
            r'app\.listen\([\'"]?(\d+)[\'"]?\)',
            r'server\.listen\([\'"]?(\d+)[\'"]?\)',
            r'\.port\([\'"]?(\d+)[\'"]?\)',
            r'port[\'"]?\s*:\s*[\'"]?(\d+)[\'"]?'

        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    port = int(matches[0])
                    if 1000 <= port <= 65535:  # Valid port range
                        return port
                except ValueError:
                    continue
        
        return default
    
    def _classify_server_tier(self, server_name: str) -> ServerTier:
        """Classify server tier based on name and functionality"""
        server_name_lower = server_name.lower()
        
        # Check critical tier
        for pattern in self.tier_classification["critical"]:
            if pattern in server_name_lower:
                return ServerTier.CRITICAL
        
        # Check integration tier
        for pattern in self.tier_classification["integration"]:
            if pattern in server_name_lower:
                return ServerTier.INTEGRATION
        
        # Check specialized tier
        for pattern in self.tier_classification["specialized"]:
            if pattern in server_name_lower:
                return ServerTier.SPECIALIZED
        
        # Default to specialized for unknown servers
        return ServerTier.SPECIALIZED
    
    def _extract_capabilities_from_python(self, content: str) -> List[ServerCapability]:
        """Extract capabilities from Python MCP server code"""
        capabilities = []
        
        # Look for common MCP server patterns
        capability_patterns = {
            "file_operations": ["read_file", "write_file", "list_files"],
            "database_access": ["query", "insert", "update", "delete"],
            "api_calls": ["requests", "httpx", "aiohttp"],
            "flash_loan": ["flash_loan", "aave", "compound"],
            "arbitrage": ["arbitrage", "dex", "price"],
            "risk_management": ["risk", "validate", "check"],
            "monitoring": ["health", "metrics", "status"]

        
        for capability_name, patterns in capability_patterns.items():
            if any(pattern in content.lower() for pattern in patterns):
                capabilities.append(ServerCapability(
                    name=capability_name,
                    description=f"Server supports {capability_name.replace('_', ' ')}"

        
        return capabilities
    
    def _extract_capabilities_from_nodejs(self, content: str) -> List[ServerCapability]:
        """Extract capabilities from Node.js MCP server code"""
        capabilities = []
        
        # Similar to Python but with Node.js specific patterns
        capability_patterns = {
            "web_server": ["express", "fastify", "koa"],
            "database": ["mongoose", "sequelize", "prisma"],
            "file_system": ["fs", "path", "readFile", "writeFile"],
            "http_client": ["axios", "fetch", "request"],
            "websocket": ["ws", "socket.io"],
            "mcp_protocol": ["mcp", "model-context-protocol"]

        
        for capability_name, patterns in capability_patterns.items():
            if any(pattern in content.lower() for pattern in patterns):
                capabilities.append(ServerCapability(
                    name=capability_name,
                    description=f"Server supports {capability_name.replace('_', ' ')}"

        
        return capabilities
    
    async def register_server(self, server_info: MCPServerInfo) -> bool:
        """
        Register a discovered or manually configured MCP server
        
        Args:
            server_info: Complete server information
            
        Returns:
            True if registration was successful
        """
        try:
            # Check for duplicates
            existing_server = self._find_existing_server(server_info)
            if existing_server:
                logger.info(f"[REGISTRY] Updating existing server: {server_info.name}")
                self.servers[existing_server.server_id] = server_info
            else:
                logger.info(f"[REGISTRY] Registering new server: {server_info.name}")
                self.servers[server_info.server_id] = server_info
                self.discovery_stats["auto_registered"] += 1
            
            # Perform initial health check
            await self._initial_health_check(server_info)
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to register server {server_info.name}: {e}")
            return False
    
    def _find_existing_server(self, new_server: MCPServerInfo) -> Optional[MCPServerInfo]:
        """Find if a server with similar characteristics already exists"""
        for server in self.servers.values():
            if (server.name == new_server.name or 
                (server.host == new_server.host and server.port == new_server.port)):
                return server
        return None
    
    async def _initial_health_check(self, server_info: MCPServerInfo):
        """Perform initial health check on newly registered server"""
        try:
            # For now, just mark as unknown - actual health checking will be done by HealthMonitor
            server_info.status = ServerStatus.UNKNOWN
            server_info.last_health_check = datetime.now()
            
            logger.debug(f"[HEALTH] Initial health check completed for {server_info.name}")
            
        except Exception as e:
            logger.warning(f"[WARNING] Initial health check failed for {server_info.name}: {e}")
            server_info.status = ServerStatus.ERROR
            server_info.last_error = str(e)
    
    async def get_servers_by_tier(self, tier: ServerTier) -> List[MCPServerInfo]:
        """Get all servers in a specific tier"""
        return [server for server in self.servers.values() if server.tier == tier]
    
    async def get_servers_by_capability(self, capability: str) -> List[MCPServerInfo]:
        """Get all servers that support a specific capability"""
        matching_servers = []
        
        for server in self.servers.values():
            for server_capability in server.capabilities:
                if capability.lower() in server_capability.name.lower():
                    matching_servers.append(server)
                    break
        
        return matching_servers
    
    async def get_healthy_servers(self) -> List[MCPServerInfo]:
        """Get all currently healthy servers"""
        return [server for server in self.servers.values() if server.status == ServerStatus.HEALTHY]
    
    async def get_server_by_id(self, server_id: str) -> Optional[MCPServerInfo]:
        """Get server information by ID"""
        return self.servers.get(server_id)
    
    async def get_server_by_name(self, name: str) -> Optional[MCPServerInfo]:
        """Get server information by name"""
        for server in self.servers.values():
            if server.name == name:
                return server
        return None
    
    async def _load_configured_servers(self):
        """Load pre-configured servers from configuration"""
        try:
            # Load from existing LangChain and AutoGen configurations
            langchain_config_path = "config/langchain_config.yaml"
            autogen_config_path = "config/autogen_config.yaml"
            
            if os.path.exists(langchain_config_path):
                await self._load_from_langchain_config(langchain_config_path)
            
            if os.path.exists(autogen_config_path):
                await self._load_from_autogen_config(autogen_config_path)
            
            # Load from unified MCP configuration if exists
            unified_config_path = "config/unified_mcp_config.json"
            if os.path.exists(unified_config_path):
                await self._load_from_unified_config(unified_config_path)
            
        except Exception as e:
            logger.warning(f"[WARNING] Failed to load configured servers: {e}")
    
    async def _load_from_langchain_config(self, config_path: str):
        """Load servers from LangChain configuration"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            mcp_servers = config.get("mcp_servers", {})
            for tier_name, servers in mcp_servers.items():
                tier = ServerTier(tier_name.lower()) if tier_name.lower() in ["critical", "integration", "specialized"] else ServerTier.SPECIALIZED
                
                for server_name, server_config in servers.items():
                    server_info = MCPServerInfo(
                        server_id=f"langchain_{server_name}",
                        name=server_name,
                        description=f"LangChain configured server: {server_name}",
                        tier=tier,
                        protocol=ServerProtocol(server_config.get("protocol", "http")),
                        host=server_config.get("host", "localhost"),
                        port=server_config.get("port", 3000),
                        capabilities=[
                            ServerCapability(cap, f"LangChain capability: {cap}")
                            for cap in server_config.get("capabilities", [])


                    self.servers[server_info.server_id] = server_info
                    self.discovery_stats["manual_registered"] += 1
            
            logger.info(f"[CONFIG] Loaded {len(mcp_servers)} servers from LangChain config")
            
        except Exception as e:
            logger.warning(f"[WARNING] Failed to load LangChain config: {e}")
    
    async def _load_from_autogen_config(self, config_path: str):
        """Load servers from AutoGen configuration"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            mcp_servers = config.get("mcp_servers", {})
            for server_name, server_config in mcp_servers.items():
                server_info = MCPServerInfo(
                    server_id=f"autogen_{server_name}",
                    name=server_name,
                    description=f"AutoGen configured server: {server_name}",
                    tier=ServerTier.INTEGRATION,  # AutoGen servers are typically integration tier
                    protocol=ServerProtocol(server_config.get("protocol", "http")),
                    host=server_config.get("host", "localhost"),
                    port=server_config.get("port", 3000),
                    capabilities=[
                        ServerCapability(cap, f"AutoGen capability: {cap}")
                        for cap in server_config.get("capabilities", [])


                self.servers[server_info.server_id] = server_info
                self.discovery_stats["manual_registered"] += 1
            
            logger.info(f"[CONFIG] Loaded {len(mcp_servers)} servers from AutoGen config")
            
        except Exception as e:
            logger.warning(f"[WARNING] Failed to load AutoGen config: {e}")
    
    async def _load_from_unified_config(self, config_path: str):
        """Load servers from unified MCP configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for tier_name, servers in config.items():
                if tier_name in ["critical", "integration", "specialized"]:
                    tier = ServerTier(tier_name)
                    
                    for server_name, server_config in servers.items():
                        server_info = MCPServerInfo(
                            server_id=f"unified_{server_name}",
                            name=server_name,
                            description=server_config.get("description", f"Unified config server: {server_name}"),
                            tier=tier,
                            protocol=ServerProtocol(server_config.get("protocol", "http")),
                            host=server_config.get("host", "localhost"),
                            port=server_config.get("port", 3000),
                            capabilities=[
                                ServerCapability(cap, f"Unified capability: {cap}")
                                for cap in server_config.get("capabilities", [])


                        self.servers[server_info.server_id] = server_info
                        self.discovery_stats["manual_registered"] += 1
            
            logger.info("[CONFIG] Loaded servers from unified config")
            
        except Exception as e:
            logger.warning(f"[WARNING] Failed to load unified config: {e}")
    
    async def _health_monitoring_loop(self):
        """Background task for periodic health monitoring"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # This will be integrated with HealthMonitor
                # For now, just log the number of servers
                logger.debug(f"[MONITOR] Monitoring {len(self.servers)} registered servers")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Health monitoring loop failed: {e}")
    
    async def _periodic_discovery_loop(self):
        """Background task for periodic server discovery"""
        while True:
            try:
                # Re-discover every 5 minutes
                await asyncio.sleep(300)
                
                logger.debug("[DISCOVERY] Starting periodic server discovery...")
                await self.discover_servers()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Periodic discovery failed: {e}")
    
    async def get_registry_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status"""
        server_stats = {
            "total": len(self.servers),
            "by_tier": {
                "critical": len([s for s in self.servers.values() if s.tier == ServerTier.CRITICAL]),
                "integration": len([s for s in self.servers.values() if s.tier == ServerTier.INTEGRATION]),
                "specialized": len([s for s in self.servers.values() if s.tier == ServerTier.SPECIALIZED])
            },
            "by_status": {
                "healthy": len([s for s in self.servers.values() if s.status == ServerStatus.HEALTHY]),
                "unhealthy": len([s for s in self.servers.values() if s.status == ServerStatus.UNHEALTHY]),
                "unknown": len([s for s in self.servers.values() if s.status == ServerStatus.UNKNOWN]),
                "error": len([s for s in self.servers.values() if s.status == ServerStatus.ERROR])
            },
            "by_protocol": {
                "http": len([s for s in self.servers.values() if s.protocol == ServerProtocol.HTTP]),
                "websocket": len([s for s in self.servers.values() if s.protocol == ServerProtocol.WEBSOCKET]),
                "stdio": len([s for s in self.servers.values() if s.protocol == ServerProtocol.STDIO]),
                "sse": len([s for s in self.servers.values() if s.protocol == ServerProtocol.SSE])


        
        return {
            "registry_status": "operational",
            "server_statistics": server_stats,
            "discovery_statistics": self.discovery_stats,
            "background_tasks": {
                "health_monitor": self.health_monitor_task is not None and not self.health_monitor_task.done(),
                "discovery": self.discovery_task is not None and not self.discovery_task.done()
            },
            "last_updated": datetime.now().isoformat()

    
    async def export_server_catalog(self) -> Dict[str, Any]:
        """Export complete server catalog for external systems"""
        catalog = {
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "total_servers": len(self.servers),
            "servers": {}

        
        for server_id, server_info in self.servers.items():
            catalog["servers"][server_id] = {
                "name": server_info.name,
                "description": server_info.description,
                "tier": server_info.tier.value,
                "protocol": server_info.protocol.value,
                "base_url": server_info.get_base_url(),
                "health_url": server_info.get_health_url(),
                "status": server_info.status.value,
                "capabilities": [cap.name for cap in server_info.capabilities],
                "version": server_info.version,
                "last_health_check": server_info.last_health_check.isoformat() if server_info.last_health_check else None

        
        return catalog
    
    async def shutdown(self):
        """Shutdown the registry and cleanup resources"""
        logger.info("[SHUTDOWN] Shutting down MCP Server Registry...")
        
        # Cancel background tasks
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass
        
        if self.discovery_task:
            self.discovery_task.cancel()
            try:
                await self.discovery_task
            except asyncio.CancelledError:
                pass
        
        # Stop any running server processes
        for process in self.server_processes.values():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                pass
        
        logger.info("[SHUTDOWN] MCP Server Registry shutdown complete")