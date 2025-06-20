#!/usr/bin/env python3
"""
Flash Loan Arbitrage System Dashboard
===================================

Real-time monitoring and control dashboard for the 24/7 arbitrage system.
"""

import asyncio
import aiohttp
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ArbitrageDashboard:
    """Real-time dashboard for monitoring arbitrage operations"""
    
    def __init__(self):
        self.refresh_interval = 5  # seconds
        self.is_running = True
        
        # Service endpoints
        self.services = {
            'MCP Flash Loan': 'http://localhost:8103',
            'MCP Arbitrage': 'http://localhost:8104', 
            'MCP Price Feed': 'http://localhost:8106',
            'Agent Arbitrage Bot': 'http://localhost:8206',
            'Agent Executor': 'http://localhost:8202',
            'Agent Risk Manager': 'http://localhost:8203'
        }
        
        self.stats = {
            'system_status': 'UNKNOWN',
            'uptime': '0:00:00',
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'successful_trades': 0,
            'total_profit_usd': 0.0,
            'current_gas_price_gwei': 0.0,
            'active_services': 0,
            'last_update': datetime.now()
        }
    
    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    async def check_service_health(self, name: str, url: str) -> Dict:
        """Check health of a service"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{url}/health", timeout=3) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    return {
                        'name': name,
                        'status': 'HEALTHY' if response.status == 200 else 'UNHEALTHY',
                        'response_time_ms': round(response_time, 1)
                    }
        except Exception:
            return {
                'name': name,
                'status': 'OFFLINE',
                'response_time_ms': 0
            }
    
    async def get_system_stats(self) -> Dict:
        """Get system statistics"""
        try:
            # Try to read from log file
            if os.path.exists('docker_arbitrage_24_7.log'):
                with open('docker_arbitrage_24_7.log', 'r') as f:
                    lines = f.readlines()[-50:]  # Last 50 lines
                    
                    # Parse basic stats from logs
                    for line in reversed(lines):
                        if 'opportunities found' in line.lower():
                            # Extract numbers from log messages
                            pass
            
            # Check if system is paused
            if os.path.exists('PAUSE_ARBITRAGE'):
                self.stats['system_status'] = 'PAUSED'
            else:
                self.stats['system_status'] = 'RUNNING'
                
        except Exception as e:
            print(f"Error reading stats: {e}")
        
        return self.stats
    
    async def refresh_dashboard(self):
        """Refresh dashboard data"""
        try:
            # Check service health
            health_tasks = [
                self.check_service_health(name, url) 
                for name, url in self.services.items()
            ]
            health_results = await asyncio.gather(*health_tasks)
            
            # Count healthy services
            healthy_count = sum(1 for result in health_results if result['status'] == 'HEALTHY')
            self.stats['active_services'] = healthy_count
            
            # Get system stats
            await self.get_system_stats()
            
            # Update timestamp
            self.stats['last_update'] = datetime.now()
            
            return health_results
            
        except Exception as e:
            print(f"Dashboard refresh error: {e}")
            return []
    
    def display_dashboard(self, health_results: List[Dict]):
        """Display the dashboard"""
        self.clear_screen()
        
        print("=" * 80)
        print("             FLASH LOAN ARBITRAGE SYSTEM - LIVE DASHBOARD")
        print("=" * 80)
        print()
        
        # System Status
        status_color = "GREEN" if self.stats['system_status'] == 'RUNNING' else "YELLOW"
        print(f"SYSTEM STATUS: {self.stats['system_status']} ({status_color})")
        print(f"LAST UPDATE:   {self.stats['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Key Metrics
        print("KEY METRICS:")
        print("-" * 40)
        print(f"  Opportunities Found:     {self.stats['opportunities_found']:,}")
        print(f"  Opportunities Executed:  {self.stats['opportunities_executed']:,}")
        print(f"  Successful Trades:       {self.stats['successful_trades']:,}")
        print(f"  Total Profit (USD):      ${self.stats['total_profit_usd']:,.2f}")
        print(f"  Current Gas Price:       {self.stats['current_gas_price_gwei']:.1f} Gwei")
        print()
        
        # Service Health
        print("SERVICE HEALTH:")
        print("-" * 40)
        for result in health_results:
            status_icon = "✓" if result['status'] == 'HEALTHY' else ("?" if result['status'] == 'OFFLINE' else "!")
            response_time = f"{result['response_time_ms']:>5.1f}ms" if result['response_time_ms'] > 0 else "  ---  "
            print(f"  {status_icon} {result['name']:<20} | {result['status']:<9} | {response_time}")
        
        healthy_count = sum(1 for r in health_results if r['status'] == 'HEALTHY')
        total_count = len(health_results)
        health_percentage = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        print()
        print(f"SERVICES: {healthy_count}/{total_count} healthy ({health_percentage:.1f}%)")
        print()
        
        # Current Configuration
        print("CONFIGURATION:")
        print("-" * 40)
        print(f"  Profit Range:         $3.00 - $30.00 USD")
        print(f"  Max Gas Price:        50.0 Gwei")
        print(f"  Supported Tokens:     15 tokens")
        print(f"  Monitored DEXs:       5 DEXs")
        print(f"  Network:              Polygon Mainnet")
        print()
        
        # Admin Controls
        print("ADMIN CONTROLS:")
        print("-" * 40)
        if self.stats['system_status'] == 'RUNNING':
            print("  To PAUSE system:      python docker_arbitrage_orchestrator.py pause")
        else:
            print("  To RESUME system:     python docker_arbitrage_orchestrator.py resume")
        print("  To SHUTDOWN system:   python docker_arbitrage_orchestrator.py shutdown")
        print("  To check STATUS:      python docker_arbitrage_orchestrator.py status")
        print()
        
        # Recent Activity (if available)
        if os.path.exists('docker_arbitrage_24_7.log'):
            print("RECENT ACTIVITY:")
            print("-" * 40)
            try:
                with open('docker_arbitrage_24_7.log', 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent_lines = [line.strip() for line in lines[-5:] if line.strip()]
                    
                    for line in recent_lines:
                        # Remove timestamp and logger name for cleaner display
                        if ' - INFO - ' in line:
                            message = line.split(' - INFO - ', 1)[1]
                            print(f"  INFO:  {message[:60]}...")
                        elif ' - WARNING - ' in line:
                            message = line.split(' - WARNING - ', 1)[1]
                            print(f"  WARN:  {message[:60]}...")
                        elif ' - ERROR - ' in line:
                            message = line.split(' - ERROR - ', 1)[1]
                            print(f"  ERROR: {message[:60]}...")
            except Exception:
                print("  (Unable to read recent activity)")
            print()
        
        print(f"Auto-refresh in {self.refresh_interval} seconds... (Press Ctrl+C to stop)")
    
    async def run_dashboard(self):
        """Run the live dashboard"""
        print("Starting Flash Loan Arbitrage Dashboard...")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while self.is_running:
                health_results = await self.refresh_dashboard()
                self.display_dashboard(health_results)
                
                await asyncio.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            print("\n\nDashboard stopped by user")
        except Exception as e:
            print(f"\nDashboard error: {e}")
    
    async def show_detailed_status(self):
        """Show detailed system status"""
        print("DETAILED SYSTEM STATUS")
        print("=" * 60)
        
        # Check all services
        all_services = {
            **self.services,
            'MCP Blockchain': 'http://localhost:8101',
            'MCP DeFi Analyzer': 'http://localhost:8102',
            'MCP Liquidity': 'http://localhost:8105',
            'MCP Risk Manager': 'http://localhost:8107',
            'Agent Monitor': 'http://localhost:8204',
            'Agent Data Collector': 'http://localhost:8205',
            'Agent Liquidity Manager': 'http://localhost:8207',
            'Agent Reporter': 'http://localhost:8208'
        }
        
        health_tasks = [
            self.check_service_health(name, url) 
            for name, url in all_services.items()
        ]
        health_results = await asyncio.gather(*health_tasks)
        
        # Group by type
        mcp_services = [r for r in health_results if r['name'].startswith('MCP')]
        agent_services = [r for r in health_results if r['name'].startswith('Agent')]
        
        print("\nMCP SERVERS:")
        print("-" * 40)
        for service in sorted(mcp_services, key=lambda x: x['name']):
            status_icon = "✓" if service['status'] == 'HEALTHY' else "✗"
            print(f"  {status_icon} {service['name']:<25} | {service['status']}")
        
        print("\nAI AGENTS:")
        print("-" * 40)
        for service in sorted(agent_services, key=lambda x: x['name']):
            status_icon = "✓" if service['status'] == 'HEALTHY' else "✗"
            print(f"  {status_icon} {service['name']:<25} | {service['status']}")
        
        # System files check
        print("\nSYSTEM FILES:")
        print("-" * 40)
        
        files_to_check = [
            '.env.production',
            'abi/aave_pool.json',
            'docker_arbitrage_24_7.log',
            'docker_arbitrage_orchestrator.py'
        ]
        
        for file_path in files_to_check:
            exists = os.path.exists(file_path)
            status_icon = "✓" if exists else "✗"
            size = f"({os.path.getsize(file_path)} bytes)" if exists else ""
            print(f"  {status_icon} {file_path:<25} | {'EXISTS' if exists else 'MISSING'} {size}")
        
        # Control files
        control_files = ['PAUSE_ARBITRAGE', 'RESUME_ARBITRAGE', 'SHUTDOWN_ARBITRAGE']
        active_controls = [f for f in control_files if os.path.exists(f)]
        
        if active_controls:
            print(f"\nACTIVE CONTROL FILES: {', '.join(active_controls)}")
        
        print("\n" + "=" * 60)

async def main():
    """Main entry point"""
    import sys
    
    dashboard = ArbitrageDashboard()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            await dashboard.show_detailed_status()
        elif command == 'monitor':
            await dashboard.run_dashboard()
        else:
            print("Usage:")
            print("  python dashboard.py                # Live dashboard")
            print("  python dashboard.py monitor        # Live dashboard") 
            print("  python dashboard.py status         # Detailed status")
    else:
        # Default to live dashboard
        await dashboard.run_dashboard()

if __name__ == "__main__":
    asyncio.run(main())
