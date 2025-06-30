# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import json
import logging

import docker
import redis
import requests
"""
Docker Container System Diagnostics
=====================================
Comprehensive logging and monitoring for the multi-container setup
"""


# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportOptionalMemberAccess=false

# Configure logging

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

logging.basicConfig()
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[]
        logging.FileHandler('system_diagnostics.log'),
        logging.StreamHandler()
    

logger = logging.getLogger(__name__)

ContainerList = List[Any]
RedisClient = Any

class SystemDiagnostics:
    def __init__(self) -> None:
        self.docker_client: Any = docker.from_env()
        self.redis_client: Optional[RedisClient] = None
        self.diagnostics: Dict[str, Any] = {}
            'timestamp': datetime.now().isoformat(),
            'container_conflicts': [],
            'resource_usage': {},
            'network_issues': [],
            'service_discovery': {},
            'health_checks': {},
            'configuration_issues': []
        
    
    async def run_full_diagnostics(self) -> None:
        """Run comprehensive system diagnostics"""
        logger.info("[SEARCH] Starting comprehensive system diagnostics...")
        
        try:
            # Check for container conflicts
            await self.check_container_conflicts()
            
            # Analyze resource usage
            await self.analyze_resource_usage()
            
            # Validate network configuration
            await self.validate_network_config()
            
            # Test service discovery
            await self.test_service_discovery()
            
            # Check health endpoints
            await self.check_health_endpoints()
            
            # Analyze configuration issues
            await self.analyze_configuration()
            
            # Generate report
            await self.generate_report()
            
        except Exception as e:
            logger.error(str(f"[ERROR] Diagnostics failed: {e}")
            raise
    
    async def check_container_conflicts(self) -> None:
        """Check for conflicting containers and port bindings"""
        logger.info("[SEARCH] Checking for container conflicts...")
        
        containers: ContainerList = self.docker_client.containers.list(all=True)
        port_map: Dict[str, str] = {}
        
        for container in containers:
            if not container.name:
                continue
            # Check port conflicts
            if container.attrs.get('NetworkSettings', {}).get('Ports'):
                for _container_port, host_bindings in container.attrs['NetworkSettings']['Ports'].items():
                    if host_bindings:
                        for binding in host_bindings:
                            host_port = binding.get('HostPort')
                            if host_port:
                                if host_port in port_map:
                                    conflict: Dict[str, Any] = {}
                                        'port': host_port,
                                        'containers': [port_map[host_port], container.name],
                                        'severity': 'HIGH'
                                    
                                    self.diagnostics['container_conflicts'].append(conflict)
                                    logger.warning(str(f"[WARN] Port conflict on {host_port}: {port_map[host_port]} vs {container.name}")
                                else:
                                    port_map[host_port] = container.name

    async def analyze_resource_usage(self) -> None:
        """Analyze CPU, memory, and network usage for each container"""
        logger.info("[METRICS] Analyzing resource usage...")
        
        containers: ContainerList = self.docker_client.containers.list()
        
        for container in containers:
            if not container.name:
                continue
            try:
                stats: Dict[str, Any] = container.stats(stream=False)
                
                # CPU Usage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                number_cpus = stats['cpu_stats']['online_cpus']
                cpu_percent = (cpu_delta / system_cpu_delta) * number_cpus * 100.0 if system_cpu_delta > 0 else 0
                
                # Memory Usage
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0
                
                self.diagnostics['resource_usage'][container.name] = {}
                    'cpu_percent': f"{cpu_percent:.2f}",
                    'memory_usage_mb': f"{memory_usage / (1024*1024):.2f}MB",
                    'memory_percent': f"{memory_percent:.2f}",
                    'memory_limit_mb': f"{memory_limit / (1024*1024):.2f}MB"
                
                logger.info(str(f"[OK] Resource usage for {container.name}: CPU {cpu_percent:.2f}%, Memory {memory_percent:.2f}%")
                
            except Exception as e:
                logger.error(str(f"[ERROR] Failed to get stats for {container.name}: {e}")

    async def validate_network_config(self) -> None:
        """Validate network configurations and connectivity"""
        logger.info("[NETWORK] Validating network configuration...")
        
        networks: List[Any] = self.docker_client.networks.list()
        
        for network in networks:
            if not network.attrs.get('IPAM', {}).get('Config'):
                issue: Dict[str, Any] = {}
                    'network': network.name,
                    'issue': 'No IPAM configuration found',
                    'severity': 'MEDIUM'
                
                self.diagnostics['network_issues'].append(issue)
                logger.warning(str(f"[WARN] Network {network.name} has no IPAM configuration")

    async def test_service_discovery(self) -> None:
        """Test service discovery using Redis"""
        logger.info("[SYNC] Testing service discovery...")
        
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
        
            # Simulate service registration
            self.redis_client.set('service:master_coordinator', 'localhost:8000')
        
            # Retrieve service
            service_host: Optional[str] = self.redis_client.get('service:master_coordinator')
            if service_host:
                self.diagnostics['service_discovery']['master_coordinator'] = service_host
                logger.info("[OK] Service discovery test passed for master_coordinator")
            else:
                logger.error("[ERROR] Service discovery test failed for master_coordinator")
            
        except Exception as e:
            logger.error(str(f"[ERROR] An unexpected error occurred during service discovery: {e}")
            self.diagnostics['service_discovery']['error'] = str(e)

    async def check_health_endpoints(self) -> None:
        """Check health endpoints of all services"""
        logger.info("❤️  Checking health endpoints...")
        
        services: Dict[str, str] = {}
            'master_coordinator': 'http://localhost:8000/health',
            'data_processor': 'http://localhost:8001/health',
            'trade_executor': 'http://localhost:8002/health'
        
        
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.diagnostics['health_checks'][service] = 'OK'
                    logger.info(str(f"[OK] Health check for {service} passed")
                else:
                    self.diagnostics['health_checks'][service] = f"Failed with status {response.status_code}"
                    logger.warning(str(f"[WARN] Health check for {service} failed with status {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.diagnostics['health_checks'][service] = f"Failed with exception: {e}"
                logger.error(str(f"[ERROR] Health check for {service} failed: {e}")

    async def analyze_configuration(self) -> None:
        """Analyze Docker Compose files for potential issues"""
        logger.info("📄 Analyzing configuration files...")
        
        compose_files = list(Path('.').glob('**/docker-compose*.yml'))
        
        for file_path in compose_files:
            try:
                with open(file_path, 'r') as f:
                    # This is a placeholder for a real YAML parser and validator
                    content = f.read()
                    if 'image: latest' in content:
                        issue = {}
                            'file': str(file_path),
                            'issue': 'Using "latest" tag for images is not recommended',
                            'severity': 'LOW'
                        
                        self.diagnostics['configuration_issues'].append(issue)
                        logger.warning(str(f"[WARN] Found 'image: latest' in {file_path}")
            except Exception as e:
                logger.error(str(f"[ERROR] Failed to analyze {file_path}: {e}")

    async def generate_report(self) -> None:
        """Generate a JSON report of the diagnostics"""
        logger.info("[LOG] Generating diagnostics report...")
        
        report_path = Path('system_diagnostics_report.json')
        
        try:
            with open(report_path, 'w') as f:
                json.dump(self.diagnostics, f, indent=4)
            logger.info(str(f"[OK] Diagnostics report generated at {report_path}")
        except Exception as e:
            logger.error(str(f"[ERROR] Failed to generate report: {e}")

async def main() -> None:
    """Main entry point for the diagnostics tool"""
    diagnostics_tool = SystemDiagnostics()
    await diagnostics_tool.run_full_diagnostics()

if __name__ == '__main__':
    asyncio.run(main())