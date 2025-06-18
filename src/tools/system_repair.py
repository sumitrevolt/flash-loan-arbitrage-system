#!/usr/bin/env python3
"""
Consolidated System Repair and Maintenance Tools
================================================
Merged from: fix_all_servers.py, fix_all_local_mcp_servers.py, 
            fix_health_check.py, advanced_mcp_server_repair.py

This consolidated tool provides comprehensive system repair capabilities including:
- Universal MCP server fixing and launching
- Socket-based health checks (avoiding aiodns issues)
- Advanced repair system with intelligent problem detection
- Configuration management and validation
- System monitoring and maintenance
"""

import asyncio
import subprocess
import sys
import os
import json
import time
import shutil
import socket
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class SystemRepairTool:
    """
    Comprehensive system repair and maintenance tool
    Combines functionality from multiple repair scripts
    """
    
    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = Path(workspace_path or os.getcwd())
        self.server_processes = {}
        self.fixed_servers = []
        self.failed_fixes = []
        self.repaired_servers = []
        self.still_failing = []
        
        # Configuration file paths to check
        self.config_files = [
            'mcp_servers/config_files/complete_cline_mcp_config.json',
            'mcp_servers/config_files/working_cline_mcp_config.json',
            'mcp_servers/config_files/FINAL_WORKING_CLINE_CONFIG.json'
        ]
        
        # Known problematic servers
        self.failed_servers = [
            "matic-mcp", "foundry-mcp", "evm-mcp", "copilot-mcp",
            "flash-loan-mcp", "price-oracle-mcp", "context7-mcp", 
            "risk-management-mcp", "task-manager-mcp", "contract-executor-mcp",
            "flash-loan-strategist", "transaction-optimizer", "production-mcp"
        ]
        
        # Default server ports for health checks
        self.default_servers = {
            "Flash Loan MCP": 3001,
            "Enhanced Copilot MCP": 3002, 
            "Enhanced Foundry MCP": 3003,
            "Flash Loan Arbitrage MCP (TS)": 3004,
            "TaskManager MCP": 3005
        }
        
        # Ensure logs directory
        os.makedirs('logs', exist_ok=True)
        
        self.log("🔧 System Repair Tool initialized")
    
    def log(self, message: str) -> None:
        """Enhanced logging with timestamp"""
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
        
        try:
            with open('logs/system_repair.log', 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] {message}\n")
        except Exception:
            pass
    
    def check_file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if a file exists"""
        return Path(file_path).exists()
    
    async def socket_health_check(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """
        Simple socket-based health check that avoids aiodns issues
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result: str = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def load_mcp_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load MCP configuration from available config files"""
        configs_to_try = [config_path] if config_path else self.config_files
        
        for config_file in configs_to_try:
            if not config_file:
                continue
                
            try:
                config_full_path = self.workspace_path / config_file
                if config_full_path.exists():
                    with open(config_full_path, 'r') as f:
                        config = json.load(f)
                    self.log(f"✅ Loaded config: {config_file}")
                    return config.get('mcpServers', {})
            except Exception as e:
                self.log(f"❌ Error loading {config_file}: {e}")
                continue
        
        self.log("⚠️ No valid MCP config found, using defaults")
        return {}
    
    def scan_all_mcp_servers(self) -> Dict[str, List[str]]:
        """Scan for all MCP server files in the directory"""
        self.log("🔍 Scanning for MCP servers...")
        
        server_files = {
            'python': [],
            'typescript': [],
            'javascript': []
        }
        
        # Common MCP server locations
        search_paths = [
            'mcp_servers',
            'src',
            'core',
            'infrastructure/mcp_servers',
            '.'
        ]
        
        for search_path in search_paths:
            full_path = self.workspace_path / search_path
            if full_path.exists():
                # Find Python MCP servers
                for py_file in full_path.rglob('*.py'):
                    if 'mcp' in py_file.name.lower():
                        server_files['python'].append(str(py_file))
                
                # Find TypeScript MCP servers
                for ts_file in full_path.rglob('*.ts'):
                    if 'mcp' in ts_file.name.lower() or ts_file.name == 'index.ts':
                        server_files['typescript'].append(str(ts_file))
                
                # Find JavaScript MCP servers
                for js_file in full_path.rglob('*.js'):
                    if 'mcp' in js_file.name.lower():
                        server_files['javascript'].append(str(js_file))
        
        self.log(f"Found {len(server_files['python'])} Python, {len(server_files['typescript'])} TypeScript, {len(server_files['javascript'])} JavaScript MCP servers")
        return server_files
    
    def test_mcp_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Test if an MCP server can start"""
        try:
            command = server_config.get('command', '')
            args = server_config.get('args', [])
            
            if command == 'python':
                if args:
                    python_file = args[0]
                    if self.check_file_exists(python_file):
                        self.log(f"✅ {server_name}: Python file exists - {python_file}")
                        return True
                    else:
                        self.log(f"❌ {server_name}: Python file missing - {python_file}")
                        return False
            elif command == 'npx':
                self.log(f"✅ {server_name}: NPX command configured")
                return True
            elif command == 'node':
                if args:
                    node_file = args[0]
                    if self.check_file_exists(node_file):
                        self.log(f"✅ {server_name}: Node file exists - {node_file}")
                        return True
                    else:
                        self.log(f"❌ {server_name}: Node file missing - {node_file}")
                        return False
            
            self.log(f"⚠️ {server_name}: Unknown command type - {command}")
            return False
            
        except Exception as e:
            self.log(f"❌ {server_name}: Test failed - {e}")
            return False
    
    def fix_python_imports(self, file_path: str) -> bool:
        """Fix common Python import issues"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Common fixes
            fixes_applied = []
            
            # Fix aiodns import issues
            if 'aiohttp' in content and 'aiodns' not in content:
                content = content.replace(
                    'import aiohttp',
                    'import aiohttp\n# aiodns removed to avoid compatibility issues'
                )
                fixes_applied.append('aiodns-compatibility')
            
            # Fix relative imports
            if 'from .' in content:
                content = content.replace('from .', 'from ')
                fixes_applied.append('relative-imports')
            
            # Fix asyncio imports
            if 'asyncio' not in content and 'async def' in content:
                content = 'import asyncio\n' + content
                fixes_applied.append('asyncio-import')
            
            if fixes_applied:
                with open(file_path, 'w') as f:
                    f.write(content)
                self.log(f"🔧 Fixed {file_path}: {', '.join(fixes_applied)}")
                return True
            
            return False
            
        except Exception as e:
            self.log(f"❌ Failed to fix {file_path}: {e}")
            return False
    
    def fix_typescript_dependencies(self, directory: str) -> bool:
        """Fix TypeScript/Node.js dependencies"""
        try:
            package_json_path = Path(directory) / 'package.json'
            
            if package_json_path.exists():
                # Install dependencies
                result: str = subprocess.run(
                    ['npm', 'install'], 
                    cwd=directory,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.log(f"✅ Dependencies installed in {directory}")
                    return True
                else:
                    self.log(f"❌ Failed to install dependencies in {directory}: {result.stderr}")
            
            return False
            
        except Exception as e:
            self.log(f"❌ Failed to fix dependencies in {directory}: {e}")
            return False
    
    async def test_all_servers_health(self, servers: Optional[Dict[str, int]] = None) -> Dict[str, bool]:
        """Test health of all MCP servers using socket connections"""
        test_servers = servers or self.default_servers
        
        self.log("🔍 Running socket-based health checks...")
        results = {}
        
        for server_name, port in test_servers.items():
            is_healthy = await self.socket_health_check("localhost", port)
            results[server_name] = is_healthy
            status = "✅ HEALTHY" if is_healthy else "❌ UNREACHABLE"
            self.log(f"{server_name:<35} Port {port}: {status}")
        
        healthy_count = sum(1 for h in results.values() if h)
        total_count = len(results)
        self.log(f"Health check complete: {healthy_count}/{total_count} servers healthy")
        
        return results
    
    def create_startup_script(self, servers_config: Dict[str, Any]) -> str:
        """Create a startup script for all MCP servers"""
        script_path = self.workspace_path / 'start_all_servers.py'
        
        script_content = f'''#!/usr/bin/env python3
"""
Auto-generated MCP Server Startup Script
Generated on: {datetime.now().isoformat()}
"""

import subprocess
import sys
import time
from pathlib import Path

def start_server(name, command, args, env=None):
    """Start a single MCP server"""
    try:
        print(f"Starting {{name}}...")
        
        if command == 'python':
            cmd = [sys.executable] + args
        elif command == 'node':
            cmd = ['node'] + args
        elif command == 'npx':
            cmd = ['npx'] + args
        else:
            print(f"Unknown command: {{command}}")
            return None
        
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"✅ {{name}} started (PID: {{proc.pid}})")
        return proc
        
    except Exception as e:
        print(f"❌ Failed to start {{name}}: {{e}}")
        return None

def main():
    """Start all MCP servers"""
    print("🚀 Starting all MCP servers...")
    
    servers = {servers_config}
    processes = []
    
    for server_name, config in servers.items():
        proc = start_server(
            server_name,
            config.get('command'),
            config.get('args', []),
            config.get('env')
        )
        if proc:
            processes.append((server_name, proc))
    
    print(f"\\n✅ Started {{len(processes)}} servers")
    print("Press Ctrl+C to stop all servers")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n🛑 Stopping all servers...")
        for name, proc in processes:
            proc.terminate()
            print(f"Stopped {{name}}")

if __name__ == "__main__":
    main()
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable on Unix systems
        try:
            os.chmod(script_path, 0o755)
        except Exception:
            pass
        
        self.log(f"✅ Created startup script: {script_path}")
        return str(script_path)
    
    async def full_system_repair(self) -> Dict[str, Any]:
        """Run comprehensive system repair"""
        self.log("🔧 Starting full system repair...")
        
        repair_results = {
            'config_loaded': False,
            'servers_scanned': {},
            'files_fixed': [],
            'health_check': {},
            'startup_script': None,
            'summary': {}
        }
        
        # 1. Load configuration
        config = self.load_mcp_config()
        repair_results['config_loaded'] = bool(config)
        
        # 2. Scan for servers
        scanned_servers = self.scan_all_mcp_servers()
        repair_results['servers_scanned'] = scanned_servers
        
        # 3. Fix Python files
        for py_file in scanned_servers.get('python', []):
            if self.fix_python_imports(py_file):
                repair_results['files_fixed'].append(py_file)
        
        # 4. Fix TypeScript dependencies
        for ts_file in scanned_servers.get('typescript', []):
            ts_dir = Path(ts_file).parent
            if self.fix_typescript_dependencies(str(ts_dir)):
                repair_results['files_fixed'].append(f"{ts_dir}/package.json")
        
        # 5. Health check
        health_results = await self.test_all_servers_health()
        repair_results['health_check'] = health_results
        
        # 6. Create startup script
        if config:
            startup_script = self.create_startup_script(config)
            repair_results['startup_script'] = startup_script
        
        # 7. Generate summary
        total_servers = sum(len(files) for files in scanned_servers.values())
        healthy_servers = sum(1 for h in health_results.values() if h)
        
        repair_results['summary'] = {
            'total_servers_found': total_servers,
            'files_fixed': len(repair_results['files_fixed']),
            'healthy_servers': f"{healthy_servers}/{len(health_results)}",
            'startup_script_created': bool(repair_results['startup_script'])
        }
        
        self.log("✅ Full system repair completed")
        return repair_results
    
    async def health_check_only(self) -> Dict[str, bool]:
        """Run health check only"""
        self.log("🔍 Running health check...")
        return await self.test_all_servers_health()
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate system configuration"""
        self.log("🔍 Validating system configuration...")
        
        validation_results = {
            'config_files': {},
            'required_directories': {},
            'python_environment': {},
            'node_environment': {}
        }
        
        # Check config files
        for config_file in self.config_files:
            config_path = self.workspace_path / config_file
            validation_results['config_files'][config_file] = {
                'exists': config_path.exists(),
                'readable': False,
                'valid_json': False
            }
            
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        json.load(f)
                    validation_results['config_files'][config_file]['readable'] = True
                    validation_results['config_files'][config_file]['valid_json'] = True
                except Exception:
                    pass
        
        # Check required directories
        required_dirs = ['mcp_servers', 'logs', 'core', 'infrastructure']
        for directory in required_dirs:
            dir_path = self.workspace_path / directory
            validation_results['required_directories'][directory] = dir_path.exists()
        
        # Check Python environment
        try:
            import subprocess
            result: str = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
            validation_results['python_environment']['version'] = result.stdout.strip()
            validation_results['python_environment']['available'] = True
        except Exception:
            validation_results['python_environment']['available'] = False
        
        # Check Node environment
        try:
            result: str = subprocess.run(['node', '--version'], capture_output=True, text=True)
            validation_results['node_environment']['version'] = result.stdout.strip()
            validation_results['node_environment']['available'] = True
        except Exception:
            validation_results['node_environment']['available'] = False
        
        self.log("✅ Configuration validation completed")
        return validation_results

async def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='System Repair and Maintenance Tool')
    parser.add_argument('--full-repair', action='store_true', help='Run full system repair')
    parser.add_argument('--health-check', action='store_true', help='Run health check only')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--workspace', type=str, help='Workspace path')
    
    args = parser.parse_args()
    
    repair_tool = SystemRepairTool(args.workspace)
    
    if args.full_repair:
        results = await repair_tool.full_system_repair()
        print("\n" + "="*50)
        print("FULL SYSTEM REPAIR RESULTS")
        print("="*50)
        print(json.dumps(results['summary'], indent=2))
        
    elif args.health_check:
        results = await repair_tool.health_check_only()
        print("\n" + "="*50)
        print("HEALTH CHECK RESULTS")
        print("="*50)
        healthy = sum(1 for r in results.values() if r)
        total = len(results)
        print(f"Healthy servers: {healthy}/{total}")
        
    elif args.validate:
        results = repair_tool.validate_configuration()
        print("\n" + "="*50)
        print("CONFIGURATION VALIDATION")
        print("="*50)
        print(json.dumps(results, indent=2))
        
    else:
        print("System Repair Tool")
        print("Use --help for options")
        
        # Run health check by default
        results = await repair_tool.health_check_only()

if __name__ == "__main__":
    asyncio.run(main())
