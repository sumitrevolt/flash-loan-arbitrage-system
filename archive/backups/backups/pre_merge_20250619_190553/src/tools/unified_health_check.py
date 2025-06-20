#!/usr/bin/env python3
"""
Unified Health Check System
===========================

Consolidated health checking for all system components.
Replaces scattered health check scripts.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UnifiedHealthCheck")

class ComponentHealthChecker:
    """Health checker for individual components"""
    
    def __init__(self, name: str, url: str, timeout: int = 5):
        self.name = name
        self.url = url
        self.timeout = timeout
        self.last_check: Optional[datetime] = None
        self.status = "unknown"
        self.response_time_ms = 0

    async def check_health(self) -> Dict[str, Any]:
        """Check health of this component"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.url}/health") as response:
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        self.status = "healthy"
                        self.response_time_ms = response_time
                        self.last_check = datetime.now()
                        
                        return {
                            "status": "healthy",
                            "response_time_ms": response_time,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        self.status = "unhealthy"
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}",
                            "response_time_ms": response_time,
                            "timestamp": datetime.now().isoformat()
                        }
                        
        except asyncio.TimeoutError:
            self.status = "timeout"
            return {
                "status": "timeout",
                "error": f"Timeout after {self.timeout}s",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.status = "error"
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

class UnifiedHealthCheckSystem:
    """Unified health check system for all components"""
    
    def __init__(self):
        self.components = {
            'flash_loan_mcp': ComponentHealthChecker('Flash Loan MCP', 'http://localhost:8001'),
            'monitoring_dashboard': ComponentHealthChecker('Monitoring Dashboard', 'http://localhost:8080'),
            'arbitrage_trading': ComponentHealthChecker('Arbitrage Trading', 'http://localhost:8004'),
            'foundry_mcp': ComponentHealthChecker('Foundry MCP', 'http://localhost:8001'),
        }
        
        self.system_checks = {
            'web3_connection': self._check_web3_connection,
            'environment_vars': self._check_environment_variables,
            'file_permissions': self._check_file_permissions,
            'disk_space': self._check_disk_space
        }

    async def check_all_components(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all components"""
        results: Dict[str, Dict[str, Any]] = {}
        
        logger.info("🔍 Checking component health...")
        
        for name, checker in self.components.items():
            logger.info(f"   Checking {name}...")
            results[name] = await checker.check_health()
        
        return results

    async def check_system_health(self) -> Dict[str, Dict[str, Any]]:
        """Check overall system health"""
        results: Dict[str, Dict[str, Any]] = {}
        
        logger.info("🔍 Checking system health...")
        
        for name, check_func in self.system_checks.items():
            logger.info(f"   Checking {name}...")
            try:
                results[name] = await check_func()
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        return results

    async def _check_web3_connection(self) -> Dict[str, Any]:
        """Check Web3 connection"""
        try:
            from web3 import Web3
            
            rpc_url = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if w3.is_connected():
                block_number = w3.eth.block_number
                return {
                    "status": "healthy",
                    "rpc_url": rpc_url,
                    "latest_block": block_number,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Failed to connect to RPC",
                    "rpc_url": rpc_url,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables"""
        required_vars = ['POLYGON_RPC_URL', 'PRIVATE_KEY']
        optional_vars = ['ETHERSCAN_API_KEY', 'TELEGRAM_BOT_TOKEN']
        
        missing_required: List[str] = []
        missing_optional: List[str] = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        status = "healthy" if not missing_required else "unhealthy"
        
        return {
            "status": status,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "timestamp": datetime.now().isoformat()
        }

    async def _check_file_permissions(self) -> Dict[str, Any]:
        """Check file permissions"""
        project_root = Path(__file__).parent.parent
        
        critical_files = [
            project_root / "working_flash_loan_mcp.py",
            project_root / "scripts" / "unified_project_launcher.py"
        ]
        
        permission_issues: List[str] = []
        
        for file_path in critical_files:
            if not file_path.exists():
                permission_issues.append(f"Missing: {file_path}")
            elif not os.access(file_path, os.R_OK):
                permission_issues.append(f"Not readable: {file_path}")
            elif not os.access(file_path, os.X_OK) and file_path.suffix == '.py':
                permission_issues.append(f"Not executable: {file_path}")
        
        status = "healthy" if not permission_issues else "unhealthy"
        
        return {
            "status": status,
            "issues": permission_issues,
            "timestamp": datetime.now().isoformat()
        }

    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            import shutil
            
            project_root = Path(__file__).parent.parent
            total, used, free = shutil.disk_usage(project_root)
            
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            used_pct = (used / total) * 100
            
            status = "healthy" if free_gb > 1.0 else "warning" if free_gb > 0.5 else "critical"
            
            return {
                "status": status,
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percentage": round(used_pct, 1),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        logger.info("🏥 Generating comprehensive health report...")
        
        component_results = await self.check_all_components()
        system_results = await self.check_system_health()
        
        # Calculate overall health
        healthy_components = sum(1 for result in component_results.values() if result.get('status') == 'healthy')
        total_components = len(component_results)
        
        healthy_systems = sum(1 for result in system_results.values() if result.get('status') == 'healthy')
        total_systems = len(system_results)
        
        overall_health = "healthy"
        if healthy_components < total_components or healthy_systems < total_systems:
            overall_health = "degraded"
        if healthy_components == 0:
            overall_health = "critical"
        
        report: Dict[str, Any] = {
            "overall_health": overall_health,
            "summary": {
                "healthy_components": f"{healthy_components}/{total_components}",
                "healthy_systems": f"{healthy_systems}/{total_systems}",
                "timestamp": datetime.now().isoformat()
            },
            "components": component_results,
            "system_checks": system_results,
            "recommendations": self._generate_recommendations(component_results, system_results) # type: ignore
        }
        
        return report

    def _generate_recommendations(self, component_results: Dict[str, Dict[str, Any]], system_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations: List[str] = []
        
        # Check for unhealthy components
        for name, result in component_results.items():
            if result.get('status') != 'healthy':
                recommendations.append(f"Restart or investigate {name} service")
        
        # Check for system issues
        for name, result in system_results.items():
            if result.get('status') == 'unhealthy':
                if name == 'web3_connection':
                    recommendations.append("Check RPC URL and network connectivity")
                elif name == 'environment_vars':
                    missing_req: List[str] = result.get('missing_required', [])
                    if missing_req:
                        recommendations.append(f"Set required environment variables: {', '.join(missing_req)}")
        
        if not recommendations:
            recommendations.append("All systems healthy! ✅")
        
        return recommendations

    def print_health_report(self, report: Dict[str, Any]) -> None:
        """Print formatted health report"""
        print("\n" + "="*60)
        print("🏥 FLASH LOAN SYSTEM HEALTH REPORT")
        print("="*60)
        
        # Overall status
        status_emoji = {"healthy": "✅", "degraded": "⚠️", "critical": "❌"}
        overall = report['overall_health']
        print(f"\n📊 Overall Status: {status_emoji.get(overall, '❓')} {overall.upper()}")
        
        # Summary
        summary = report['summary']
        print(f"   Components: {summary['healthy_components']}")
        print(f"   Systems: {summary['healthy_systems']}")
        print(f"   Checked: {summary['timestamp']}")
        
        # Component details
        print(f"\n🔧 Component Status:")
        for name, result in report['components'].items():
            status = result.get('status', 'unknown')
            emoji = status_emoji.get(status, '❓')
            response_time = result.get('response_time_ms', 0)
            print(f"   {emoji} {name}: {status} ({response_time:.0f}ms)")
        
        # System details
        print(f"\n⚙️ System Status:")
        for name, result in report['system_checks'].items():
            status = result.get('status', 'unknown')
            emoji = status_emoji.get(status, '❓')
            print(f"   {emoji} {name}: {status}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
        
        print("="*60)

async def main():
    """Main entry point for health check"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Health Check System")
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--components-only', action='store_true', help='Check components only')
    parser.add_argument('--system-only', action='store_true', help='Check system only')
    
    args = parser.parse_args()
    
    health_checker = UnifiedHealthCheckSystem()
    
    try:
        if args.components_only:
            results = await health_checker.check_all_components()
        elif args.system_only:
            results = await health_checker.check_system_health()
        else:
            results = await health_checker.generate_health_report()
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            if 'overall_health' in results:
                health_checker.print_health_report(results)
            else:
                # Simple results
                for name, result in results.items():
                    status = result.get('status', 'unknown')
                    print(f"{name}: {status}")
    
    except KeyboardInterrupt:
        logger.info("Health check interrupted")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
