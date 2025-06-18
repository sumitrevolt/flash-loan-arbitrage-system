#!/usr/bin/env python3
"""
Ultimate Flash Loan System Commander
Command-line interface for managing all 21 MCP servers and AI agents
"""

import asyncio
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
import requests
import subprocess
from typing import Dict, List, Any

from ultimate_langchain_coordinator import UltimateLangChainCoordinator

class FlashLoanCommander:
    """Command-line interface for the flash loan system"""
    
    def __init__(self):
        self.coordinator = UltimateLangChainCoordinator()
        
    async def deploy_system(self, args):
        """Deploy the entire system"""
        print("🚀 Deploying Ultimate Flash Loan System...")
        print("=" * 60)
        
        # Clean deployment if requested
        if args.clean:
            print("🧹 Performing clean deployment...")
            await self.stop_system(args)
            time.sleep(5)
        
        # Deploy all services
        results = await self.coordinator.deploy_all_services()
        
        if results:
            self.print_deployment_results(results)
            
            # Save results to file
            results_file = f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\\n📄 Deployment results saved to: {results_file}")
            
            # Show next steps
            if len(results['success']) == results['total']:
                print("\\n🎉 All services deployed successfully!")
                print("\\nNext steps:")
                print("  • Monitor service health: python ultimate_commander.py status")
                print("  • View service logs: python ultimate_commander.py logs <service_name>")
                print("  • Test system: python ultimate_commander.py test")
            else:
                print("\\n⚠️  Some services failed to deploy")
                print("\\nTroubleshooting:")
                print("  • Check logs: python ultimate_commander.py logs")
                print("  • Retry failed services: python ultimate_commander.py retry")
                print("  • Manual recovery: python ultimate_commander.py recover <service_name>")
        
        return results
    
    async def stop_system(self, args):
        """Stop all system components"""
        print("🛑 Stopping Ultimate Flash Loan System...")
        
        try:
            # Get all running containers
            result: str = subprocess.run(['docker', 'ps', '-q', '--filter', 'name=mcp-', '--filter', 'name=ai-agent-'], 
                                  capture_output=True, text=True)
            
            container_ids = result.stdout.strip().split('\\n') if result.stdout.strip() else []
            
            if container_ids:
                print(f"Found {len(container_ids)} containers to stop...")
                
                # Stop containers
                for container_id in container_ids:
                    if container_id:
                        subprocess.run(['docker', 'stop', container_id], capture_output=True)
                
                # Remove containers if requested
                if args.remove:
                    print("🗑️ Removing containers...")
                    for container_id in container_ids:
                        if container_id:
                            subprocess.run(['docker', 'rm', container_id], capture_output=True)
                
                print("✅ System stopped successfully")
            else:
                print("ℹ️ No running containers found")
                
        except Exception as e:
            print(f"❌ Error stopping system: {e}")
    
    async def check_status(self, args):
        """Check system status"""
        print("📊 Ultimate Flash Loan System Status")
        print("=" * 60)
        
        # Perform health check
        health_status = await self.coordinator.perform_comprehensive_health_check()
        
        # Print overall status
        overall_health = health_status.get('overall_health', 'unknown')
        healthy_count = health_status.get('healthy_count', 0)
        total_count = health_status.get('total_count', 0)
        
        status_icon = {
            'excellent': '🟢',
            'good': '🟡',
            'fair': '🟠',
            'poor': '🔴',
            'unknown': '⚪'
        }.get(overall_health, '⚪')
        
        print(f"\\n{status_icon} Overall Health: {overall_health.upper()}")
        print(f"📈 Services Online: {healthy_count}/{total_count} ({healthy_count/total_count*100:.1f}%)")
        
        # Infrastructure status
        print("\\n🏗️ Infrastructure Services:")
        infra_status = health_status.get('infrastructure', {})
        for name, status in infra_status.items():
            icon = '✅' if status.get('healthy', False) else '❌'
            port = status.get('port', 'N/A')
            print(f"   {icon} {name:20} Port: {port}")
          # MCP servers status
        print("\\n🔧 MCP Servers:")
        services_status = health_status.get('services', {})
        mcp_services = {k: v for k, v in services_status.items() 
                       if self.coordinator.services.get(k) and self.coordinator.services[k].service_type == 'mcp'}
        
        for name, status in mcp_services.items():
            icon = '✅' if status.get('healthy', False) else '❌'
            port = status.get('port', 'N/A')
            role = status.get('role', 'N/A')
            print(f"   {icon} {name:20} Port: {port:5} Role: {role}")
          # AI agents status
        print("\\n🤖 AI Agents:")
        ai_services = {k: v for k, v in services_status.items() 
                      if self.coordinator.services.get(k) and self.coordinator.services[k].service_type == 'ai_agent'}
        
        for name, status in ai_services.items():
            icon = '✅' if status.get('healthy', False) else '❌'
            port = status.get('port', 'N/A')
            role = status.get('role', 'N/A')
            print(f"   {icon} {name:20} Port: {port:5} Role: {role}")
        
        # Performance metrics
        print("\\n📊 Performance Metrics:")
        if healthy_count == total_count:
            print("   🎯 All systems operational")
            print("   🚀 Ready for flash loan operations")
        else:
            failed_count = total_count - healthy_count
            print(f"   ⚠️  {failed_count} services need attention")
            print("   🔧 System requires maintenance")
        
        return health_status
    
    async def show_logs(self, args):
        """Show service logs"""
        service_name = args.service if hasattr(args, 'service') and args.service else None
        
        if service_name:
            print(f"📋 Logs for {service_name}")
            print("=" * 60)
            
            # Get container name
            if service_name in self.coordinator.infrastructure:
                container_name = self.coordinator.infrastructure[service_name].container_name
            elif service_name in self.coordinator.services:
                container_name = self.coordinator.services[service_name].container_name
            else:
                print(f"❌ Service '{service_name}' not found")
                return
            
            try:
                # Get logs
                tail_count = args.lines if hasattr(args, 'lines') else 50
                result: str = subprocess.run(['docker', 'logs', '--tail', str(tail_count), container_name], 
                                      capture_output=True, text=True)
                
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                    
            except Exception as e:
                print(f"❌ Error getting logs: {e}")
        else:
            print("📋 System Logs Overview")
            print("=" * 60)
            
            # Show logs for all services
            all_services = list(self.coordinator.infrastructure.keys()) + list(self.coordinator.services.keys())
            
            for service in all_services[:5]:  # Show first 5 services
                print(f"\\n--- {service} ---")
                try:
                    if service in self.coordinator.infrastructure:
                        container_name = self.coordinator.infrastructure[service].container_name
                    else:
                        container_name = self.coordinator.services[service].container_name
                    
                    result: str = subprocess.run(['docker', 'logs', '--tail', '10', container_name], 
                                          capture_output=True, text=True)
                    
                    if result.stdout:
                        lines = result.stdout.split('\\n')[-5:]  # Last 5 lines
                        for line in lines:
                            if line.strip():
                                print(f"  {line}")
                except Exception as e:
                    print(f"  ❌ Error: {e}")
            
            print(f"\\n💡 Use 'python ultimate_commander.py logs <service_name>' for specific service logs")
    
    async def test_system(self, args):
        """Test system functionality"""
        print("🧪 Testing Ultimate Flash Loan System")
        print("=" * 60)
        
        test_results = {
            'infrastructure_tests': {},
            'mcp_server_tests': {},
            'ai_agent_tests': {},
            'integration_tests': {},
            'overall_score': 0
        }
        
        total_tests = 0
        passed_tests = 0
        
        # Test infrastructure
        print("\\n🏗️ Testing Infrastructure...")
        for name, config in self.coordinator.infrastructure.items():
            total_tests += 1
            try:
                if name == 'redis':
                    result: str = subprocess.run(['docker', 'exec', config.container_name, 'redis-cli', 'ping'], 
                                          capture_output=True, text=True, timeout=10)
                    success = 'PONG' in result.stdout
                elif name == 'postgres':
                    result: str = subprocess.run(['docker', 'exec', config.container_name, 'pg_isready', '-U', 'postgres'], 
                                          capture_output=True, text=True, timeout=10)
                    success = 'accepting connections' in result.stdout
                elif name == 'rabbitmq':
                    result: str = subprocess.run(['docker', 'exec', config.container_name, 'rabbitmqctl', 'status'], 
                                          capture_output=True, text=True, timeout=10)
                    success = result.returncode == 0
                else:
                    success = False
                
                test_results['infrastructure_tests'][name] = success
                status = '✅ PASS' if success else '❌ FAIL'
                print(f"  {status} {name}")
                
                if success:
                    passed_tests += 1
                    
            except Exception as e:
                test_results['infrastructure_tests'][name] = False
                print(f"  ❌ FAIL {name} - {e}")
        
        # Test MCP servers
        print("\\n🔧 Testing MCP Servers...")
        mcp_services = {k: v for k, v in self.coordinator.services.items() 
                       if v.service_type == 'mcp'}
        
        for name, config in list(mcp_services.items())[:5]:  # Test first 5
            total_tests += 1
            try:
                response = requests.get(f'http://localhost:{config.port}/health', timeout=5)
                success = response.status_code == 200
                
                test_results['mcp_server_tests'][name] = success
                status = '✅ PASS' if success else '❌ FAIL'
                print(f"  {status} {name} (port {config.port})")
                
                if success:
                    passed_tests += 1
                    
            except Exception as e:
                test_results['mcp_server_tests'][name] = False
                print(f"  ❌ FAIL {name} - {e}")
        
        # Test AI agents
        print("\\n🤖 Testing AI Agents...")
        ai_services = {k: v for k, v in self.coordinator.services.items() 
                      if v.service_type == 'ai_agent'}
        
        for name, config in ai_services.items():
            total_tests += 1
            try:
                response = requests.get(f'http://localhost:{config.port}/health', timeout=5)
                success = response.status_code == 200
                
                test_results['ai_agent_tests'][name] = success
                status = '✅ PASS' if success else '❌ FAIL'
                print(f"  {status} {name} (port {config.port})")
                
                if success:
                    passed_tests += 1
                    
            except Exception as e:
                test_results['ai_agent_tests'][name] = False
                print(f"  ❌ FAIL {name} - {e}")
        
        # Integration tests
        print("\\n🔗 Testing Integration...")
        integration_tests = [
            ('coordinator_communication', 'http://localhost:3000/status'),
            ('ai_coordination', 'http://localhost:5001/status'),
            ('service_discovery', 'http://localhost:4001/status')
        ]
        
        for test_name, url in integration_tests:
            total_tests += 1
            try:
                response = requests.get(url, timeout=5)
                success = response.status_code == 200
                
                test_results['integration_tests'][test_name] = success
                status = '✅ PASS' if success else '❌ FAIL'
                print(f"  {status} {test_name}")
                
                if success:
                    passed_tests += 1
                    
            except Exception as e:
                test_results['integration_tests'][test_name] = False
                print(f"  ❌ FAIL {test_name} - {e}")
        
        # Calculate overall score
        test_results['overall_score'] = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Print results
        print(f"\\n📊 Test Results:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {test_results['overall_score']:.1f}%")
        
        if test_results['overall_score'] >= 90:
            print("   Status: 🎉 EXCELLENT - System ready for production")
        elif test_results['overall_score'] >= 75:
            print("   Status: ✅ GOOD - System operational with minor issues")
        elif test_results['overall_score'] >= 50:
            print("   Status: ⚠️ FAIR - System needs attention")
        else:
            print("   Status: ❌ POOR - System requires immediate fixes")
        
        # Save test results
        test_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(test_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\\n📄 Test results saved to: {test_file}")
        
        return test_results
    
    async def restart_service(self, args):
        """Restart a specific service"""
        service_name = args.service
        print(f"🔄 Restarting service: {service_name}")
        
        if service_name in self.coordinator.infrastructure:
            container_name = self.coordinator.infrastructure[service_name].container_name
        elif service_name in self.coordinator.services:
            container_name = self.coordinator.services[service_name].container_name
        else:
            print(f"❌ Service '{service_name}' not found")
            return
        
        try:
            result: str = subprocess.run(['docker', 'restart', container_name], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ Service {service_name} restarted successfully")
                
                # Wait and check health
                print("⏳ Checking service health...")
                await asyncio.sleep(10)
                
                if service_name in self.coordinator.services:
                    config = self.coordinator.services[service_name]
                    try:
                        response = requests.get(f'http://localhost:{config.port}/health', timeout=10)
                        if response.status_code == 200:
                            print(f"✅ Service {service_name} is healthy")
                        else:
                            print(f"⚠️ Service {service_name} health check failed")
                    except:
                        print(f"⚠️ Cannot reach service {service_name}")
                else:
                    print(f"ℹ️ Infrastructure service {service_name} restarted")
            else:
                print(f"❌ Failed to restart {service_name}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error restarting service: {e}")
    
    async def interactive_mode(self):
        """Interactive command mode"""
        print("🎮 Ultimate Flash Loan System - Interactive Mode")
        print("=" * 60)
        print("Available commands:")
        print("  deploy    - Deploy the system")
        print("  status    - Check system status")
        print("  logs      - View service logs")
        print("  test      - Run system tests")
        print("  restart   - Restart a service")
        print("  stop      - Stop the system")
        print("  help      - Show this help")
        print("  exit      - Exit interactive mode")
        print()
        
        while True:
            try:
                command = input("🚀 flashloan> ").strip().lower()
                
                if command == 'exit' or command == 'quit':
                    print("👋 Goodbye!")
                    break
                elif command == 'help':
                    print("Available commands: deploy, status, logs, test, restart, stop, help, exit")
                elif command == 'deploy':
                    args = argparse.Namespace(clean=True)
                    await self.deploy_system(args)
                elif command == 'status':
                    args = argparse.Namespace()
                    await self.check_status(args)
                elif command == 'logs':
                    args = argparse.Namespace()
                    await self.show_logs(args)
                elif command == 'test':
                    args = argparse.Namespace()
                    await self.test_system(args)
                elif command == 'stop':
                    args = argparse.Namespace(remove=False)
                    await self.stop_system(args)
                elif command.startswith('restart '):
                    service_name = command.split(' ', 1)[1]
                    args = argparse.Namespace(service=service_name)
                    await self.restart_service(args)
                elif command.startswith('logs '):
                    service_name = command.split(' ', 1)[1]
                    args = argparse.Namespace(service=service_name, lines=50)
                    await self.show_logs(args)
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type 'help' for available commands")
                
                print()  # Empty line for readability
                
            except KeyboardInterrupt:
                print("\\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def print_deployment_results(self, results: Dict[str, Any]):
        """Print deployment results in a formatted way"""
        print("\\n📊 Deployment Results:")
        print(f"   ✅ Successfully deployed: {len(results['success'])}")
        if results['success']:
            for service in results['success']:
                print(f"      • {service}")
        
        if results['failed']:
            print(f"   ❌ Failed to deploy: {len(results['failed'])}")
            for service in results['failed']:
                print(f"      • {service}")
        
        if results['skipped']:
            print(f"   ⏭️ Skipped: {len(results['skipped'])}")
            for service in results['skipped']:
                print(f"      • {service}")
        
        print(f"\\n⏱️ Total deployment time: {results['duration']:.1f} seconds")
        print(f"📈 Success rate: {len(results['success'])/results['total']*100:.1f}%")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Ultimate Flash Loan System Commander')
    parser.add_argument('--version', action='version', version='Ultimate Flash Loan System v1.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy the entire system')
    deploy_parser.add_argument('--clean', action='store_true', help='Clean deployment (stop existing containers first)')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check system status')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop the system')
    stop_parser.add_argument('--remove', action='store_true', help='Remove containers after stopping')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show service logs')
    logs_parser.add_argument('service', nargs='?', help='Specific service name')
    logs_parser.add_argument('--lines', type=int, default=50, help='Number of log lines to show')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run system tests')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart a service')
    restart_parser.add_argument('service', help='Service name to restart')
    
    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Start interactive mode')
    
    args = parser.parse_args()
    
    commander = FlashLoanCommander()
    
    try:
        if args.command == 'deploy':
            await commander.deploy_system(args)
        elif args.command == 'status':
            await commander.check_status(args)
        elif args.command == 'stop':
            await commander.stop_system(args)
        elif args.command == 'logs':
            await commander.show_logs(args)
        elif args.command == 'test':
            await commander.test_system(args)
        elif args.command == 'restart':
            await commander.restart_service(args)
        elif args.command == 'interactive':
            await commander.interactive_mode()
        else:
            # Default to interactive mode if no command specified
            await commander.interactive_mode()
    
    except KeyboardInterrupt:
        print("\\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
