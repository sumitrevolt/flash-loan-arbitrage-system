#!/usr/bin/env python3
"""
Unified Production System Status Checker
Comprehensive health check for all MCP servers and arbitrage bot
"""

import asyncio
import aiohttp
import json
import logging
import time
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SystemStatusChecker')

class SystemStatusChecker:
    """Check status of all production system components"""
    
    def __init__(self) -> None:
        self.mcp_servers: Dict[str, Dict[str, Any]] = {
            'foundry': {'port': 8001, 'name': 'Foundry MCP Server'},
            'evm': {'port': 8002, 'name': 'EVM MCP Server'},
            'matic': {'port': 8003, 'name': 'Matic MCP Server'}
        }
        self.status_report: Dict[str, Any] = {}
        
    async def check_mcp_server(self, server_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check if an MCP server is running and responsive"""
        server_status: Dict[str, Any] = {
            'name': config['name'],
            'port': config['port'],
            'healthy': False,
            'response_time': None,
            'error': None
        }
        
        try:
            start_time: float = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{config['port']}/health", 
                                     timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time: float = time.time() - start_time
                    server_status['response_time'] = round(response_time * 1000, 2)
                    
                    if response.status == 200:
                        data = await response.json()
                        server_status['healthy'] = True
                        server_status['data'] = data
                        logger.info(f"✅ {config['name']} is running (Response: {server_status['response_time']}ms)")
                    else:
                        server_status['error'] = f"HTTP {response.status}"
                        logger.warning(f"⚠️ {config['name']} returned HTTP {response.status}")
                        
        except asyncio.TimeoutError:
            server_status['error'] = "Connection timeout"
            logger.error(f"❌ {config['name']} timeout")
        except aiohttp.ClientConnectorError:
            server_status['error'] = "Connection refused"
            logger.error(f"❌ {config['name']} connection refused")
        except Exception as e:
            server_status['error'] = str(e)
            logger.error(f"❌ {config['name']} error: {e}")
            
        return server_status
    
    async def check_all_mcp_servers(self) -> Dict[str, Any]:
        """Check all MCP servers concurrently"""
        logger.info("Checking MCP servers...")
        
        tasks = []
        for server_name, config in self.mcp_servers.items():
            task = self.check_mcp_server(server_name, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        server_results = {}
        for i, (server_name, config) in enumerate(self.mcp_servers.items()):
            server_results[server_name] = results[i]
            
        return server_results
    
    async def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity to Polygon RPC"""
        network_status = {
            'polygon_rpc': False,
            'block_number': None,
            'response_time': None,
            'error': None
        }
        
        polygon_rpc = "https://polygon-rpc.com/"
        
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                rpc_data = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }
                
                async with session.post(polygon_rpc, 
                                      json=rpc_data,
                                      timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response_time = time.time() - start_time
                    network_status['response_time'] = round(response_time * 1000, 2)
                    
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            network_status['polygon_rpc'] = True
                            # Convert hex to decimal
                            block_hex = data['result']
                            network_status['block_number'] = int(block_hex, 16)
                            logger.info(f"✅ Polygon network connected (Block: {network_status['block_number']}, {network_status['response_time']}ms)")
                        else:
                            network_status['error'] = "Invalid RPC response"
                    else:
                        network_status['error'] = f"HTTP {response.status}"
                        
        except Exception as e:
            network_status['error'] = str(e)
            logger.error(f"❌ Network connectivity check failed: {e}")
            
        return network_status
    
    def check_configuration_files(self) -> Dict[str, Any]:
        """Check if required configuration files exist"""
        config_status = {
            'files_present': {},
            'all_files_exist': True
        }
          required_configs = [
            'config/unified_production_config.json',
            'src/core/unified_production_arbitrage_bot.py',
            'UNIFIED_PRODUCTION_LAUNCHER.py',
            'foundry-mcp-server/working_enhanced_foundry_mcp_server.py',
            'mcp/evm-mcp-server/evm_mcp_server.py',
            'mcp/matic-mcp-server/matic_mcp_server.py'
        ]
        
        for config_file in required_configs:
            file_path = Path(config_file)
            exists = file_path.exists()
            config_status['files_present'][config_file] = exists
            if not exists:
                config_status['all_files_exist'] = False
                logger.warning(f"⚠️ Missing file: {config_file}")
            else:
                logger.debug(f"✅ Found: {config_file}")
                
        return config_status
    
    async def run_status_check(self) -> Dict[str, Any]:
        """Run comprehensive status check"""
        logger.info("=" * 60)
        logger.info("UNIFIED PRODUCTION SYSTEM STATUS CHECK")
        logger.info("=" * 60)
        
        # Check all components
        server_results = await self.check_all_mcp_servers()
        network_status = await self.check_network_connectivity()
        config_status = self.check_configuration_files()
        
        # Compile status report
        healthy_servers = sum(1 for result in server_results.values() if result['healthy'])
        total_servers = len(server_results)
        
        self.status_report = {
            'timestamp': datetime.now().isoformat(),
            'servers': server_results,
            'network': network_status,
            'configuration': config_status,
            'healthy_servers': healthy_servers,
            'total_servers': total_servers,
            'system_healthy': (
                healthy_servers >= 2 and  # At least 2 servers running
                network_status['polygon_rpc'] and
                config_status['all_files_exist']
            )
        }
        
        # Generate recommendations
        recommendations = []
        if self.status_report['system_healthy']:
            recommendations.append("✅ System is ready for production trading!")
            self.status_report['overall_status'] = 'Healthy'
        else:
            self.status_report['overall_status'] = 'Degraded'
            
            if healthy_servers == 0:
                recommendations.append("🚨 No MCP servers are running. Start servers with: START_UNIFIED_PRODUCTION.bat")
            elif healthy_servers < total_servers:
                recommendations.append(f"⚠️ Only {healthy_servers}/{total_servers} MCP servers are running")
                
            if not network_status['polygon_rpc']:
                recommendations.append("🌐 Network connectivity issue - check internet connection")
                
            if not config_status['all_files_exist']:
                recommendations.append("📁 Missing configuration files - check project structure")
        
        self.status_report['recommendations'] = recommendations
        
        # Print summary
        self.print_summary()
        
        return self.status_report
    
    def print_summary(self):
        """Print human-readable status summary"""
        print("\n" + "=" * 60)
        print("📊 SYSTEM STATUS SUMMARY")
        print("=" * 60)
        
        # Overall status
        status_icon = "✅" if self.status_report['system_healthy'] else "⚠️"
        print(f"\n🎯 Overall Status: {status_icon} {self.status_report['overall_status']}")
        
        # MCP Servers
        print("\n🖥️ MCP SERVERS:")
        for server_name, status in self.status_report['servers'].items():
            health_icon = "✅" if status['healthy'] else "❌"
            response_time = f"({status['response_time']}ms)" if status['response_time'] else ""
            error_info = f" - {status['error']}" if status['error'] else ""
            print(f"  {health_icon} {status['name']} (Port {status['port']}) {response_time}{error_info}")
        
        # Network status
        network = self.status_report['network']
        net_icon = "✅" if network['polygon_rpc'] else "❌"
        response_time = f"({network.get('response_time', 'N/A')}ms)" if network.get('response_time') else ""
        print(f"\n🌐 NETWORK CONNECTIVITY:")
        print(f"  {net_icon} Polygon RPC {response_time}")
        if network.get('block_number'):
            print(f"     Current Block: #{network['block_number']:,}")
        
        # Configuration
        config = self.status_report['configuration']
        config_icon = "✅" if config['all_files_exist'] else "❌"
        print(f"\n📁 CONFIGURATION:")
        print(f"  {config_icon} All required files present: {config['all_files_exist']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in self.status_report['recommendations']:
            print(f"  {rec}")
        
        print("=" * 60)

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Check unified production system status')
    parser.add_argument('--continuous', '-c', action='store_true', 
                       help='Run continuous monitoring (check every 30 seconds)')
    parser.add_argument('--interval', '-i', type=int, default=30,
                       help='Monitoring interval in seconds (default: 30)')
    args = parser.parse_args()
    
    checker = SystemStatusChecker()
    
    if args.continuous:
        print("🔄 Starting continuous monitoring...")
        print(f"⏱️ Check interval: {args.interval} seconds")
        print("📖 Press Ctrl+C to stop")
        
        try:
            while True:
                await checker.run_status_check()
                print(f"\n⏱️ Next check in {args.interval} seconds...")
                await asyncio.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
    else:
        # Single check
        await checker.run_status_check()

if __name__ == "__main__":
    asyncio.run(main())
