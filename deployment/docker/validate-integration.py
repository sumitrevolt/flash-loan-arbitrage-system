# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import argparse
import asyncio
import json
import logging
import os
import sys
import time
import traceback

from concurrent.futures import ThreadPoolExecutor
import aiohttp
import asyncpg
import psutil
import redis.asyncio as redis
import yaml
"""
Integration Validation Script for the Unified LangChain-AutoGen-MCP System

This script performs comprehensive validation of:
- LangChain and AutoGen coordinator communication
- MCP server connectivity and response times
- Redis and PostgreSQL data persistence
- Monitoring stack functionality
- Load testing on critical endpoints
"""


# Third-party imports

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
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/integration-validation-{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    

logger = logging.getLogger(__name__)

class ValidationConfig:
    """Configuration for integration validation"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.base_dir / "config"
        self.logs_dir = self.base_dir / "logs"
        self.results_dir = self.logs_dir / "validation-results"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        
        # Service endpoints
        self.endpoints = {}
            'langchain_coordinator': 'http://localhost:8000',
            'autogen_coordinator': 'http://localhost:8010',
            'mcp_supermemory': 'http://localhost:8100',
            'mcp_context7': 'http://localhost:8101',
            'mcp_filesystem': 'http://localhost:8102',
            'mcp_taskmanager': 'http://localhost:8103',
            'prometheus': 'http://localhost:9090',
            'grafana': 'http://localhost:3000',
            'elasticsearch': 'http://localhost:9200',
            'kibana': 'http://localhost:5601',
            'web_dashboard': 'http://localhost:8090'
        
        
        # Database configurations
        self.postgres_config = {}
            'host': 'localhost',
            'port': 5432,
            'user': 'flash_loan_user',
            'password': 'flash_loan_secure_2025',
            'database': 'flash_loan_db'
        
        
        self.redis_config = {}
            'host': 'localhost',
            'port': 6379,
            'password': 'flash_loan_redis_2025',
            'db': 0
        
        
        # Load test configurations
        self.load_test_config = {}
            'concurrent_requests': 10,
            'total_requests': 100,
            'timeout': 30,
            'ramp_up_time': 5
        
        
        # Performance thresholds
        self.thresholds = {}
            'response_time_ms': 5000,
            'error_rate_percent': 5,
            'cpu_usage_percent': 80,
            'memory_usage_percent': 85,
            'disk_usage_percent': 90
        

class IntegrationValidator:
    """Main validation class for the integrated system"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.results = {}
            'validation_run': {}
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'version': '1.0.0',
                'system': 'LangChain-AutoGen-MCP Unified System'
            },
            'tests': {}
                'coordinator_communication': {'status': 'pending', 'results': {}},
                'mcp_connectivity': {'status': 'pending', 'results': {}},
                'database_persistence': {'status': 'pending', 'results': {}},
                'monitoring_stack': {'status': 'pending', 'results': {}},
                'load_testing': {'status': 'pending', 'results': {}},
                'performance_metrics': {'status': 'pending', 'results': {}}
            },
            'summary': {}
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'duration_seconds': 0
            
        
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _update_test_result(self, test_category: str, test_name: str, )
                           status: str, details: str, duration: float = 0, 
                           metrics: Optional[Dict] = None):
        """Update test results with timing and metrics"""
        if test_category not in self.results['tests']:
            self.results['tests'][test_category] = {'status': 'pending', 'results': {}}
            
        self.results['tests'][test_category]['results'][test_name] = {}
            'status': status,
            'details': details,
            'duration_seconds': duration,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics': metrics or {}
        
        
        # Update summary counters
        self.results['summary']['total_tests'] += 1
        if status == 'passed':
            self.results['summary']['passed'] += 1
        elif status == 'failed':
            self.results['summary']['failed'] += 1
        elif status == 'warning':
            self.results['summary']['warnings'] += 1
    
    async def test_service_health(self, service_name: str, endpoint: str) -> Tuple[bool, str, float]:
        """Test basic health endpoint of a service"""
        start_time = time.time()
        try:
            health_url = f"{endpoint}/health"
            async with self.session.get(health_url) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    return True, f"Health check passed ({response.status})", duration
                else:
                    return False, f"Health check failed ({response.status})", duration
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Health check error: {str(e)}", duration
    
    async def test_coordinator_communication(self):
        """Test communication between LangChain and AutoGen coordinators"""
        logger.info("Testing coordinator communication...")
        
        # Test LangChain coordinator health
        langchain_healthy, langchain_msg, langchain_duration = await self.test_service_health()
            'langchain', self.config.endpoints['langchain_coordinator']
        
        self._update_test_result('coordinator_communication', 'langchain_health', )
                               'passed' if langchain_healthy else 'failed',
                               langchain_msg, langchain_duration
        
        # Test AutoGen coordinator health
        autogen_healthy, autogen_msg, autogen_duration = await self.test_service_health()
            'autogen', self.config.endpoints['autogen_coordinator']
        
        self._update_test_result('coordinator_communication', 'autogen_health',)
                               'passed' if autogen_healthy else 'failed',
                               autogen_msg, autogen_duration
        
        # Test inter-coordinator communication
        if langchain_healthy and autogen_healthy:
            await self._test_inter_coordinator_communication()
        else:
            self._update_test_result('coordinator_communication', 'inter_coordinator',)
                                   'failed', 'Cannot test - coordinators not healthy', 0
    
    async def _test_inter_coordinator_communication(self):
        """Test communication between coordinators"""
        start_time = time.time()
        try:
            # Test LangChain to AutoGen communication
            payload = {}
                'task': 'test_coordination',
                'target': 'autogen',
                'message': 'Test message from LangChain coordinator',
                'test_mode': True
            
            
            async with self.session.post()
                f"{self.config.endpoints['langchain_coordinator']}/api/v1/coordinate",
                json=payload
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    result = await response.json()
                    self._update_test_result('coordinator_communication', 'langchain_to_autogen',)
                                           'passed', f"Communication successful: {result.get('status', 'OK')}", 
                                           duration
                else:
                    self._update_test_result('coordinator_communication', 'langchain_to_autogen',)
                                           'failed', f"Communication failed ({response.status})", 
                                           duration
                    
        except Exception as e:
            duration = time.time() - start_time
            self._update_test_result('coordinator_communication', 'langchain_to_autogen',)
                                   'failed', f"Communication error: {str(e)}", duration
        
        # Test AutoGen to LangChain communication
        start_time = time.time()
        try:
            payload = {}
                'task': 'test_coordination',
                'target': 'langchain',
                'message': 'Test message from AutoGen coordinator',
                'test_mode': True
            
            
            async with self.session.post()
                f"{self.config.endpoints['autogen_coordinator']}/api/v1/coordinate",
                json=payload
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    result = await response.json()
                    self._update_test_result('coordinator_communication', 'autogen_to_langchain',)
                                           'passed', f"Communication successful: {result.get('status', 'OK')}", 
                                           duration
                else:
                    self._update_test_result('coordinator_communication', 'autogen_to_langchain',)
                                           'failed', f"Communication failed ({response.status})", 
                                           duration
                    
        except Exception as e:
            duration = time.time() - start_time
            self._update_test_result('coordinator_communication', 'autogen_to_langchain',)
                                   'failed', f"Communication error: {str(e)}", duration
    
    async def test_mcp_connectivity(self):
        """Test MCP server connectivity and response times"""
        logger.info("Testing MCP server connectivity...")
        
        mcp_servers = {}
            'supermemory': self.config.endpoints['mcp_supermemory'],
            'context7': self.config.endpoints['mcp_context7'],
            'filesystem': self.config.endpoints['mcp_filesystem'],
            'taskmanager': self.config.endpoints['mcp_taskmanager']
        
        
        for server_name, endpoint in mcp_servers.items():
            healthy, msg, duration = await self.test_service_health(server_name, endpoint)
            self._update_test_result('mcp_connectivity', f'{server_name}_health',)
                                   'passed' if healthy else 'failed', msg, duration
            
            # Test MCP server specific functionality
            if healthy:
                await self._test_mcp_functionality(server_name, endpoint)
    
    async def _test_mcp_functionality(self, server_name: str, endpoint: str):
        """Test specific MCP server functionality"""
        start_time = time.time()
        try:
            if server_name == 'supermemory':
                # Test memory operations
                test_payload = {}
                    'action': 'test_memory',
                    'data': {'message': 'Test memory storage', 'test_mode': True}
                
            elif server_name == 'context7':
                # Test documentation retrieval
                test_payload = {}
                    'action': 'test_docs',
                    'library': 'test-library',
                    'test_mode': True
                
            elif server_name == 'filesystem':
                # Test file operations
                test_payload = {}
                    'action': 'test_filesystem',
                    'operation': 'list_directory',
                    'path': '/tmp',
                    'test_mode': True
                
            elif server_name == 'taskmanager':
                # Test task management
                test_payload = {}
                    'action': 'test_task',
                    'task': 'Create test task',
                    'test_mode': True
                
            else:
                return
            
            async with self.session.post(f"{endpoint}/api/test", json=test_payload) as response:
                duration = time.time() - start_time
                if response.status in [200, 201]:
                    result = await response.json()
                    self._update_test_result('mcp_connectivity', f'{server_name}_functionality',)
                                           'passed', f"Functionality test passed: {result.get('status', 'OK')}", 
                                           duration
                else:
                    self._update_test_result('mcp_connectivity', f'{server_name}_functionality',)
                                           'warning', f"Functionality test unavailable ({response.status})", 
                                           duration
                    
        except Exception as e:
            duration = time.time() - start_time
            self._update_test_result('mcp_connectivity', f'{server_name}_functionality',)
                                   'warning', f"Functionality test error: {str(e)}", duration
    
    async def test_database_persistence(self):
        """Test Redis and PostgreSQL data persistence"""
        logger.info("Testing database persistence...")
        
        # Test PostgreSQL
        await self._test_postgresql_persistence()
        
        # Test Redis
        await self._test_redis_persistence()
    
    async def _test_postgresql_persistence(self):
        """Test PostgreSQL connectivity and basic operations"""
        start_time = time.time()
        try:
            # Connect to PostgreSQL
            conn = await asyncpg.connect(**self.config.postgres_config)
            
            # Test basic query
            result = await conn.fetchval("SELECT version()")
            await conn.close()
            
            duration = time.time() - start_time
            self._update_test_result('database_persistence', 'postgresql_connectivity',)
                                   'passed', f"PostgreSQL connected successfully: {result[:50]}...", 
                                   duration
            
            # Test table operations
            await self._test_postgresql_operations()
            
        except Exception as e:
            duration = time.time() - start_time
            self._update_test_result('database_persistence', 'postgresql_connectivity',)
                                   'failed', f"PostgreSQL connection failed: {str(e)}", duration
    
    async def _test_postgresql_operations(self):
        """Test PostgreSQL CRUD operations"""
        start_time = time.time()
        try:
            conn = await asyncpg.connect(**self.config.postgres_config)
            
            # Create test table
            await conn.execute(""")
                CREATE TABLE IF NOT EXISTS validation_test ()
                    id SERIAL PRIMARY KEY,
                    test_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                
            """
            
            # Insert test data
            test_data = f"Integration test data - {datetime.now().isoformat()}"
            await conn.execute()
                "INSERT INTO validation_test (test_data) VALUES ($1)", test_data
            
            
            # Read test data
            result = await conn.fetchrow()
                "SELECT test_data FROM validation_test WHERE test_data = $1", test_data
            
            
            # Cleanup
            await conn.execute("DELETE FROM validation_test WHERE test_data = $1", test_data)
            await conn.close()
            
            duration = time.time() - start_time
            if result and result['test_data'] == test_data:
                self._update_test_result('database_persistence', 'postgresql_operations',)
                                       'passed', "CRUD operations successful", duration
            else:
                self._update_test_result('database_persistence', 'postgresql_operations',)
                                       'failed', "CRUD operations failed - data mismatch", duration
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_test_result('database_persistence', 'postgresql_operations',)
                                   'failed', f"CRUD operations failed: {str(e)}", duration
    
    async def _test_redis_persistence(self):
        """Test Redis connectivity and basic operations"""
        start_time = time.time()
        try:
            # Connect to Redis
            redis_client = redis.Redis(**self.config.redis_config)
            
            # Test connection
            pong = await redis_client.ping()
            if not pong:
                raise Exception("Redis ping failed")
            
            # Test basic operations
            test_key = f"validation_test:{int(time.time())}"
            test_value = json.dumps({)}
                'test_data': 'Integration test',
                'timestamp': datetime.now(, ensure_ascii=True, default=str).isoformat()
            
            
            # Set and get
            await redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved_value = await redis_client.get(test_key)
            
            # Cleanup
            await redis_client.delete(test_key)
            await redis_client.close()
            
            duration = time.time() - start_time
            if retrieved_value and retrieved_value.decode() == test_value:
                self._update_test_result('database_persistence', 'redis_operations',)
                                       'passed', "Redis operations successful", duration
            else:
                self._update_test_result('database_persistence', 'redis_operations',)
                                       'failed', "Redis operations failed - data mismatch", duration
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_test_result('database_persistence', 'redis_operations',)
                                   'failed', f"Redis operations failed: {str(e)}", duration
    
    async def test_monitoring_stack(self):
        """Test monitoring stack functionality"""
        logger.info("Testing monitoring stack...")
        
        monitoring_services = {}
            'prometheus': self.config.endpoints['prometheus'],
            'grafana': self.config.endpoints['grafana'],
            'elasticsearch': self.config.endpoints['elasticsearch'],
            'kibana': self.config.endpoints['kibana']
        
        
        for service_name, endpoint in monitoring_services.items():
            await self._test_monitoring_service(service_name, endpoint)
    
    async def _test_monitoring_service(self, service_name: str, endpoint: str):
        """Test individual monitoring service"""
        start_time = time.time()
        try:
            if service_name == 'prometheus':
                test_url = f"{endpoint}/-/healthy"
            elif service_name == 'grafana':
                test_url = f"{endpoint}/api/health"
            elif service_name == 'elasticsearch':
                test_url = f"{endpoint}/_cluster/health"
            elif service_name == 'kibana':
                test_url = f"{endpoint}/api/status"
            else:
                test_url = f"{endpoint}/health"
            
            async with self.session.get(test_url) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    self._update_test_result('monitoring_stack', f'{service_name}_health',)
                                           'passed', f"Service healthy ({response.status})", duration
                else:
                    self._update_test_result('monitoring_stack', f'{service_name}_health',)
                                           'failed', f"Service unhealthy ({response.status})", duration
                    
        except Exception as e:
            duration = time.time() - start_time
            self._update_test_result('monitoring_stack', f'{service_name}_health',)
                                   'failed', f"Service error: {str(e)}", duration
    
    async def perform_load_testing(self):
        """Perform load testing on critical endpoints"""
        logger.info("Performing load testing...")
        
        critical_endpoints = []
            ('langchain_coordinator', f"{self.config.endpoints['langchain_coordinator']}/api/v1/status"),
            ('autogen_coordinator', f"{self.config.endpoints['autogen_coordinator']}/health"),
            ('mcp_supermemory', f"{self.config.endpoints['mcp_supermemory']}/health"),
            ('web_dashboard', f"{self.config.endpoints['web_dashboard']}/health")
        
        
        for service_name, endpoint in critical_endpoints:
            await self._perform_service_load_test(service_name, endpoint)
    
    async def _perform_service_load_test(self, service_name: str, endpoint: str):
        """Perform load test on a specific service"""
        start_time = time.time()
        concurrent_requests = self.config.load_test_config['concurrent_requests']
        total_requests = self.config.load_test_config['total_requests']
        
        logger.info(str(f"Load testing {service_name}: {total_requests} requests, {concurrent_requests} concurrent")
        
        # Semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)
        results = []
        
        async def make_request():
            async with semaphore:
                request_start = time.time()
                try:
                    async with self.session.get(endpoint) as response:
                        request_duration = time.time() - request_start
                        return {}
                            'status': response.status,
                            'duration': request_duration,
                            'success': 200 <= response.status < 300
                        
                except Exception as e:
                    request_duration = time.time() - request_start
                    return {}
                        'status': 0,
                        'duration': request_duration,
                        'success': False,
                        'error': str(e)
                    
        
        try:
            # Execute all requests
            tasks = [make_request() for _ in range(total_requests)]
            results = await asyncio.gather(*tasks)
            
            # Analyze results
            total_duration = time.time() - start_time
            successful_requests = sum(1 for r in results if r['success'])
            failed_requests = total_requests - successful_requests
            avg_response_time = sum(r['duration'] for r in results) / len(results)
            error_rate = (failed_requests / total_requests) * 100
            requests_per_second = total_requests / total_duration
            
            metrics = {}
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'avg_response_time_ms': avg_response_time * 1000,
                'error_rate_percent': error_rate,
                'requests_per_second': requests_per_second,
                'total_duration_seconds': total_duration
            
            
            # Determine test status
            if error_rate <= self.config.thresholds['error_rate_percent']:
                status = 'passed'
                details = f"Load test passed: {successful_requests}/{total_requests} requests successful"
            else:
                status = 'failed'
                details = f"Load test failed: {error_rate:.2f}% error rate exceeds threshold"
            
            self._update_test_result('load_testing', f'{service_name}_load_test',)
                                   status, details, total_duration, metrics
            
        except Exception as e:
            total_duration = time.time() - start_time
            self._update_test_result('load_testing', f'{service_name}_load_test',)
                                   'failed', f"Load test error: {str(e)}", total_duration
    
    async def collect_performance_metrics(self):
        """Collect system performance metrics"""
        logger.info("Collecting performance metrics...")
        
        start_time = time.time()
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Docker container metrics (if available)
            docker_metrics = await self._collect_docker_metrics()
            
            metrics = {}
                'system': {}
                    'cpu_usage_percent': cpu_percent,
                    'memory_usage_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_usage_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3)
                },
                'docker': docker_metrics
            
            
            # Check against thresholds
            warnings = []
            if cpu_percent > self.config.thresholds['cpu_usage_percent']:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > self.config.thresholds['memory_usage_percent']:
                warnings.append(f"High memory usage: {memory.percent}%")
            if disk.percent > self.config.thresholds['disk_usage_percent']:
                warnings.append(f"High disk usage: {disk.percent}%")
            
            duration = time.time() - start_time
            status = 'warning' if warnings else 'passed'
            details = '; '.join(warnings) if warnings else "All metrics within thresholds"
            
            self._update_test_result('performance_metrics', 'system_metrics',)
                                   status, details, duration, metrics
            
        except Exception as e:
            duration = time.time() - start_time
            self._update_test_result('performance_metrics', 'system_metrics',)
                                   'failed', f"Metrics collection failed: {str(e)}", duration
    
    async def _collect_docker_metrics(self) -> Dict[str, Any]:
        """Collect Docker container metrics"""
        docker_metrics = {}
        try:
            # This would require docker python client
            # For now, return placeholder
            docker_metrics = {}
                'containers_running': 'N/A',
                'total_memory_usage': 'N/A',
                'total_cpu_usage': 'N/A'
            
        except Exception as e:
            logger.warning(str(f"Could not collect Docker metrics: {e}")
            docker_metrics = {'error': str(e)}
        
        return docker_metrics
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("Starting comprehensive integration validation...")
        validation_start = time.time()
        
        try:
            # Run all test phases
            await self.test_coordinator_communication()
            await self.test_mcp_connectivity()
            await self.test_database_persistence()
            await self.test_monitoring_stack()
            await self.perform_load_testing()
            await self.collect_performance_metrics()
            
            # Update overall completion time
            total_duration = time.time() - validation_start
            self.results['summary']['duration_seconds'] = total_duration
            self.results['validation_run']['end_timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Update test category statuses
            for category, tests in self.results['tests'].items():
                if tests['results']:
                    failed_tests = [t for t in tests['results'].values() if t['status'] == 'failed']
                    if failed_tests:
                        tests['status'] = 'failed'
                    else:
                        warning_tests = [t for t in tests['results'].values() if t['status'] == 'warning']
                        tests['status'] = 'warning' if warning_tests else 'passed'
                else:
                    tests['status'] = 'skipped'
            
            logger.info(str(f"Validation completed in {total_duration:.2f} seconds")
            return self.results
            
        except Exception as e:
            logger.error(str(f"Validation failed with error: {e}")
            logger.error(traceback.format_exc()
            self.results['validation_run']['error'] = str(e)
            return self.results
    
    def save_results(self, output_file: Optional[str] = None):
        """Save validation results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.config.results_dir / f"integration-validation-{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(str(f"Results saved to: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print validation summary to console"""
        summary = self.results['summary']
        print("\n" + "="*60)
        print("INTEGRATION VALIDATION SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Warnings: {summary['warnings']}")
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        print("="*60)
        
        # Print failed tests
        if summary['failed'] > 0:
            print("\nFAILED TESTS:")
            for category, tests in self.results['tests'].items():
                for test_name, result in tests.get('results', {}).items():
                    if result['status'] == 'failed':
                        print(f"  - {category}.{test_name}: {result['details']}")
        
        # Print warnings
        if summary['warnings'] > 0:
            print("\nWARNINGS:")
            for category, tests in self.results['tests'].items():
                for test_name, result in tests.get('results', {}).items():
                    if result['status'] == 'warning':
                        print(f"  - {category}.{test_name}: {result['details']}")

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Integration Validation for LangChain-AutoGen-MCP System')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--config', '-c', help='Configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = ValidationConfig()
    
    # Run validation
    async with IntegrationValidator(config) as validator:
        results = await validator.run_validation()
        
        # Save results
        output_file = validator.save_results(args.output)
        
        # Print summary
        validator.print_summary()
        
        # Exit with appropriate code
        if results['summary']['failed'] > 0:
            sys.exit(1)
        elif results['summary']['warnings'] > 0:
            sys.exit(2)
        else:
            sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())