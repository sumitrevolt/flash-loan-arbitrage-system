# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import asyncio
import json
import os
import subprocess
import sys
import time

import aiohttp
"""
MCP Server Docker Management Tool
Provides easy management of containerized MCP servers
"""


class MCPServerManager:
    def __init__(self, compose_file: str = "docker/docker-compose.mcp-servers.yml"):
        self.compose_file = compose_file
        self.base_dir = Path(__file__).parent.parent
        self.compose_path = self.base_dir / compose_file
        
    def run_command(self, cmd: List[str], capture=True) -> subprocess.CompletedProcess:
        """Run a command and return result"""
        try:
            if capture:
                result: str = subprocess.run()
                    cmd, 
                    cwd=self.base_dir,
                    capture_output=True, 
                    text=True, 
                    check=False
                
            else:
                result: str = subprocess.run(cmd, cwd=self.base_dir, check=False)
            return result
        except Exception as e:
            print(f"[ERROR] Error running command {' '.join(cmd)}: {e}")
            return subprocess.CompletedProcess(cmd, 1, "", str(e))
    
    def build_servers(self, parallel: bool = True) -> bool:
        """Build all MCP server Docker images"""
        print("🔨 Building MCP server Docker images...")
        
        cmd = ["docker", "compose", "-f", self.compose_file, "build"]
        if parallel:
            cmd.append("--parallel")
        
        result: str = self.run_command(cmd, capture=False)
        
        if result.returncode == 0:
            print("[OK] Successfully built all MCP server images")
            return True
        else:
            print("[ERROR] Failed to build MCP server images")
            return False
    
    def start_infrastructure(self) -> bool:
        """Start infrastructure services (Redis, PostgreSQL, RabbitMQ)"""
        print("[INIT] Starting infrastructure services...")
        
        infrastructure_services = ["redis", "postgres", "rabbitmq"]
        
        for service in infrastructure_services:
            print(f"   Starting {service}...")
            cmd = ["docker", "compose", "-f", self.compose_file, "up", "-d", service]
            result: str = self.run_command(cmd)
            
            if result.returncode != 0:
                print(f"[ERROR] Failed to start {service}")
                return False
        
        # Wait for services to be ready
        print("⏳ Waiting for infrastructure services to be ready...")
        time.sleep(10)
        
        return self.check_infrastructure_health()
    
    def check_infrastructure_health(self) -> bool:
        """Check if infrastructure services are healthy"""
        print("[SEARCH] Checking infrastructure health...")
        
        health_checks = {}
            "redis": self._check_redis_health,
            "postgres": self._check_postgres_health,
            "rabbitmq": self._check_rabbitmq_health
        
        
        all_healthy = True
        for service, check_func in health_checks.items():
            if check_func():
                print(f"   [OK] {service} is healthy")
            else:
                print(f"   [ERROR] {service} is not healthy")
                all_healthy = False
        
        return all_healthy
    
    def _check_redis_health(self) -> bool:
        """Check Redis health"""
        cmd = ["docker", "exec", "mcp-redis", "redis-cli", "ping"]
        result: str = self.run_command(cmd)
        return result.returncode == 0 and "PONG" in result.stdout
    
    def _check_postgres_health(self) -> bool:
        """Check PostgreSQL health"""
        cmd = ["docker", "exec", "mcp-postgres", "pg_isready", "-U", "postgres"]
        result: str = self.run_command(cmd)
        return result.returncode == 0
    
    def _check_rabbitmq_health(self) -> bool:
        """Check RabbitMQ health"""
        cmd = ["docker", "exec", "mcp-rabbitmq", "rabbitmq-diagnostics", "ping"]
        result: str = self.run_command(cmd)
        return result.returncode == 0
    
    def start_mcp_servers(self, servers: Optional[List[str]] = None) -> bool:
        """Start MCP servers"""
        if servers:
            print(f"[INIT] Starting specific MCP servers: {', '.join(servers)}")
            cmd = ["docker", "compose", "-f", self.compose_file, "up", "-d"] + servers
        else:
            print("[INIT] Starting all MCP servers...")
            cmd = ["docker", "compose", "-f", self.compose_file, "up", "-d"]
        
        result: str = self.run_command(cmd, capture=False)
        
        if result.returncode == 0:
            print("[OK] Successfully started MCP servers")
            return True
        else:
            print("[ERROR] Failed to start MCP servers")
            return False
    
    def stop_servers(self, servers: Optional[List[str]] = None) -> bool:
        """Stop MCP servers"""
        if servers:
            print(f"[STOP] Stopping specific servers: {', '.join(servers)}")
            cmd = ["docker", "compose", "-f", self.compose_file, "stop"] + servers
        else:
            print("[STOP] Stopping all servers...")
            cmd = ["docker", "compose", "-f", self.compose_file, "down"]
        
        result: str = self.run_command(cmd, capture=False)
        
        if result.returncode == 0:
            print("[OK] Successfully stopped servers")
            return True
        else:
            print("[ERROR] Failed to stop servers")
            return False
    
    def restart_servers(self, servers: Optional[List[str]] = None) -> bool:
        """Restart MCP servers"""
        if servers:
            print(f"[SYNC] Restarting specific servers: {', '.join(servers)}")
            cmd = ["docker", "compose", "-f", self.compose_file, "restart"] + servers
        else:
            print("[SYNC] Restarting all servers...")
            cmd = ["docker", "compose", "-f", self.compose_file, "restart"]
        
        result: str = self.run_command(cmd, capture=False)
        
        if result.returncode == 0:
            print("[OK] Successfully restarted servers")
            return True
        else:
            print("[ERROR] Failed to restart servers")
            return False
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all containers"""
        print("[METRICS] Getting server status...")
        
        cmd = ["docker", "compose", "-f", self.compose_file, "ps", "--format", "json"]
        result: str = self.run_command(cmd)
        
        if result.returncode != 0:
            print("[ERROR] Failed to get server status")
            return {}
        
        try:
            # Parse JSON output (one JSON object per line)
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    containers.append(json.loads(line))
            
            status = {}
                'total_containers': len(containers),
                'running': 0,
                'stopped': 0,
                'containers': containers
            
            
            for container in containers:
                if container.get('State') == 'running':
                    status['running'] += 1
                else:
                    status['stopped'] += 1
            
            return status
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse status JSON: {e}")
            return {}
    
    def show_logs(self, service: str, follow: bool = False, tail: int = 100):
        """Show logs for a specific service"""
        print(f"📋 Showing logs for {service}...")
        
        cmd = ["docker", "compose", "-f", self.compose_file, "logs"]
        if follow:
            cmd.append("--follow")
        cmd.extend(["--tail", str(tail), service])
        
        self.run_command(cmd, capture=False)
    
    async def check_mcp_server_health(self, server_name: str, port: int) -> Dict[str, Any]:
        """Check health of a specific MCP server"""
        health_urls = []
            f'http://localhost:{port}/health',
            f'http://localhost:{port}/status',
            f'http://localhost:{port}/'
        
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for url in health_urls:
                try:
                    async with session.get(url) as response:
                        if response.status in [200, 404]:
                            return {}
                                'server': server_name,
                                'port': port,
                                'status': 'healthy',
                                'url': url,
                                'response_code': response.status
                            
                except Exception as e:
                    continue
        
        return {}
            'server': server_name,
            'port': port,
            'status': 'unhealthy',
            'error': 'No response from any endpoint'
        
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all MCP servers"""
        print("🏥 Performing health check on all MCP servers...")
        
        # Define server ports based on docker-compose
        server_ports = {}
            'mcp-context7-clean': 8001,
            'mcp-grok3': 3003,
            'mcp-start-grok3': 8002,
            'mcp-copilot': 8003,
            'mcp-context7': 8004,
            'mcp-matic-clean': 8005,
            'mcp-matic': 8006,
            'mcp-foundry': 8007,
            'mcp-flash-loan': 8008,
            'mcp-evm': 8009,
            'mcp-matic-server': 8010,
            'mcp-coordinator-enhanced': 3000,
            'mcp-integration-bridge': 8011,
            'mcp-server-coordinator': 3001,
            'mcp-unified-coordinator': 8012,
            'mcp-dex-price': 8013,
            'mcp-price-oracle': 8014,
            'mcp-dex-services': 8015,
            'mcp-evm-integration': 8016,
            'mcp-contract-executor': 3005,
            'mcp-flash-loan-strategist': 3004,
            'mcp-dashboard': 8080,
            'mcp-github': 8017,
            'mcp-filesystem': 8018
        
        
        tasks = []
        for server, port in server_ports.items():
            tasks.append(self.check_mcp_server_health(server, port))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = 0
        unhealthy_count = 0
        
        print("\n[METRICS] MCP Server Health Report:")
        print("=" * 60)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"[ERROR] Error checking server: {result}")
                unhealthy_count += 1
                continue
                
            if result['status'] == 'healthy':
                print(f"[OK] {result['server']} (port {result['port']}) - Healthy")
                healthy_count += 1
            else:
                print(f"[ERROR] {result['server']} (port {result['port']}) - Unhealthy")
                unhealthy_count += 1
        
        print("=" * 60)
        print(f"[GROWTH] Summary: {healthy_count} healthy, {unhealthy_count} unhealthy")
        
        return {}
            'healthy': healthy_count,
            'unhealthy': unhealthy_count,
            'total': len(server_ports),
            'details': results
        
    
    def cleanup(self, volumes: bool = False) -> bool:
        """Clean up containers and optionally volumes"""
        print("🧹 Cleaning up containers...")
        
        cmd = ["docker", "compose", "-f", self.compose_file, "down"]
        if volumes:
            cmd.append("--volumes")
            print("   Including volumes...")
        
        result: str = self.run_command(cmd, capture=False)
        
        if result.returncode == 0:
            print("[OK] Successfully cleaned up")
            return True
        else:
            print("[ERROR] Failed to clean up")
            return False
    
    def setup_github_mcp(self, github_token: str = None) -> bool:
        """Setup GitHub MCP server with authentication"""
        print("[SETUP] Setting up GitHub MCP server...")
        
        if not github_token:
            github_token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN') or os.getenv('GITHUB_TOKEN')
        
        if not github_token:
            print("[ERROR] No GitHub token provided. Set GITHUB_PERSONAL_ACCESS_TOKEN environment variable")
            return False
        
        # Pull GitHub MCP server image
        print("[PACKAGE] Pulling GitHub MCP server image...")
        result = self.run_command(["docker", "pull", "ghcr.io/github/github-mcp-server"])
        
        if result.returncode != 0:
            print("[ERROR] Failed to pull GitHub MCP server image")
            return False
        
        # Test the server setup
        print("🧪 Testing GitHub MCP server...")
        test_result = self.run_command([)]
            "docker", "run", "--rm", "-i",
            "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={github_token}",
            "ghcr.io/github/github-mcp-server",
            "--toolsets", "repos"
        
        
        if test_result.returncode == 0:
            print("[OK] GitHub MCP server setup successful")
            return True
        else:
            print("[ERROR] GitHub MCP server test failed")
            return False
    
    def list_available_servers(self) -> Dict[str, str]:
        """List all available MCP servers with descriptions"""
        servers = {}
            'mcp-github': 'GitHub version control operations (repos, issues, PRs)',
            'mcp-filesystem': 'Local filesystem and Git operations',
            'mcp-context7': 'Documentation and code examples',
            'mcp-flash-loan': 'Flash loan trading operations',
            'mcp-evm': 'Ethereum Virtual Machine interactions',
            'mcp-dex-price': 'DEX price monitoring and arbitrage',
            'mcp-dashboard': 'Web dashboard for monitoring',
            'mcp-coordinator': 'Multi-agent coordination services'
        
        
        print("\n📋 Available MCP Servers:")
        print("=" * 60)
        for server, description in servers.items():
            print(f"   {server}: {description}")
        print("=" * 60)
        
        return servers

def main():
    parser = argparse.ArgumentParser(description="MCP Server Docker Management Tool")
    parser.add_argument("--compose-file", default="docker/docker-compose.mcp-servers.yml",)
                       help="Path to docker-compose file"
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Build MCP server images")
    build_parser.add_argument("--no-parallel", action="store_true", help="Disable parallel builds")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start services")
    start_parser.add_argument("--infra-only", action="store_true", help="Start only infrastructure")
    start_parser.add_argument("--servers", nargs="+", help="Specific servers to start")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument("--servers", nargs="+", help="Specific servers to stop")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart services")
    restart_parser.add_argument("--servers", nargs="+", help="Specific servers to restart")
    
    # Status command
    subparsers.add_parser("status", help="Show container status")
    
    # Health command
    subparsers.add_parser("health", help="Check MCP server health")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show service logs")
    logs_parser.add_argument("service", help="Service name")
    logs_parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")
    logs_parser.add_argument("--tail", type=int, default=100, help="Number of lines to show")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up containers")
    cleanup_parser.add_argument("--volumes", action="store_true", help="Remove volumes too")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = MCPServerManager(args.compose_file)
    
    if args.command == "build":
        manager.build_servers(parallel=not args.no_parallel)
    
    elif args.command == "start":
        if args.infra_only:
            manager.start_infrastructure()
        else:
            manager.start_infrastructure()
            time.sleep(5)  # Give infrastructure time to start
            manager.start_mcp_servers(args.servers)
    
    elif args.command == "stop":
        manager.stop_servers(args.servers)
    
    elif args.command == "restart":
        manager.restart_servers(args.servers)
    
    elif args.command == "status":
        status = manager.get_server_status()
        print(f"\n[METRICS] Container Status:")
        print(f"   Total: {status.get('total_containers', 0)}")
        print(f"   Running: {status.get('running', 0)}")
        print(f"   Stopped: {status.get('stopped', 0)}")
        
        if status.get('containers'):
            print("\nDetailed Status:")
            for container in status['containers']:
                state = container.get('State', 'unknown')
                name = container.get('Name', 'unknown')
                print(f"   {name}: {state}")
    
    elif args.command == "health":
        asyncio.run(manager.health_check_all())
    
    elif args.command == "logs":
        manager.show_logs(args.service, args.follow, args.tail)
    
    elif args.command == "cleanup":
        manager.cleanup(args.volumes)

if __name__ == "__main__":
    main()