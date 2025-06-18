#!/usr/bin/env python3
"""
Health check script for MCP servers
Verifies that the MCP server is running and responding correctly
"""

import sys
import os
import asyncio
import json
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

import aiohttp
import psutil

class MCPHealthChecker:
    def __init__(self):
        self.server_name = os.getenv('MCP_SERVER_NAME', 'unknown')
        self.server_port = int(os.getenv('MCP_SERVER_PORT', '3000'))
        self.server_file = os.getenv('MCP_SERVER_FILE', '')
        self.health_timeout = int(os.getenv('HEALTH_TIMEOUT', '10'))
        
    async def check_port_available(self, port: int) -> bool:
        """Check if port is available and responding"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result: str = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    async def check_http_endpoint(self, port: int) -> bool:
        """Check HTTP endpoint health"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                urls_to_check = [
                    f'http://localhost:{port}/health',
                    f'http://localhost:{port}/status',
                    f'http://localhost:{port}/',
                ]
                
                for url in urls_to_check:
                    try:
                        async with session.get(url) as response:
                            if response.status in [200, 404]:  # 404 is OK if no health endpoint
                                return True
                    except:
                        continue
                        
                return False
        except:
            return False
    
    def check_process_running(self) -> bool:
        """Check if MCP server process is running"""
        try:
            # Look for Python processes running our server file
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                        cmdline: str = ' '.join(proc.info['cmdline'] or [])
                        if self.server_file and self.server_file in cmdline:
                            return True
                        if self.server_name and self.server_name.lower() in cmdline.lower():
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except:
            return False
    
    def check_log_errors(self) -> Dict[str, Any]:
        """Check recent log files for errors"""
        log_info = {
            'has_errors': False,
            'error_count': 0,
            'recent_errors': []
        }
        
        try:
            log_files = [
                '/app/logs/mcp_server.log',
                '/app/logs/error.log',
                f'/app/logs/{self.server_name}.log'
            ]
            
            for log_file in log_files:
                if Path(log_file).exists():
                    try:
                        with open(log_file, 'r') as f:
                            # Read last 50 lines
                            lines = f.readlines()[-50:]
                            for line in lines:
                                if any(level in line.upper() for level in ['ERROR', 'CRITICAL', 'FATAL']):
                                    log_info['has_errors'] = True
                                    log_info['error_count'] += 1
                                    if len(log_info['recent_errors']) < 3:
                                        log_info['recent_errors'].append(line.strip())
                    except:
                        continue
        except:
            pass
            
        return log_info
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get basic system statistics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except:
            return {}
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        start_time = time.time()
        
        health_status = {
            'server_name': self.server_name,
            'timestamp': time.time(),
            'healthy': False,
            'checks': {},
            'system_stats': {},
            'duration_ms': 0
        }
        
        # Process check
        process_running = self.check_process_running()
        health_status['checks']['process_running'] = process_running
        
        # Port check
        port_available = False
        if self.server_port:
            port_available = await self.check_port_available(self.server_port)
            health_status['checks']['port_available'] = port_available
            
            # HTTP endpoint check if port is available
            if port_available:
                http_responding = await self.check_http_endpoint(self.server_port)
                health_status['checks']['http_responding'] = http_responding
        
        # Log error check
        log_info = self.check_log_errors()
        health_status['checks']['log_errors'] = log_info
        
        # System stats
        health_status['system_stats'] = self.get_system_stats()
        
        # Overall health determination
        critical_checks = [process_running]
        if self.server_port:
            critical_checks.append(port_available)
            
        health_status['healthy'] = (
            all(critical_checks) and 
            not log_info['has_errors'] and
            health_status['system_stats'].get('memory_percent', 0) < 95
        )
        
        health_status['duration_ms'] = int((time.time() - start_time) * 1000)
        
        return health_status

def main():
    """Main health check function"""
    import os
    
    try:
        checker = MCPHealthChecker()
        health_result: str = asyncio.run(checker.run_health_check())
        
        # Print health status for logging
        print(json.dumps(health_result, indent=2))
        
        # Exit with appropriate code
        if health_result['healthy']:
            print(f"✅ {checker.server_name} is healthy")
            sys.exit(0)
        else:
            print(f"❌ {checker.server_name} is unhealthy")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
