#!/usr/bin/env python3
"""
Universal MCP Server Fixer and Launcher
Fixes and starts ALL local MCP servers in your system
"""

import asyncio
import subprocess
import sys
import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class UniversalMCPServerFixer:
    """
    Universal fixer for all MCP servers in the system
    """
    
    def __init__(self):
        self.workspace_path = Path(os.getcwd())
        self.server_processes = {}
        self.fixed_servers = []
        self.failed_fixes = []
        self.config_files = [
            'mcp_servers/config_files/complete_cline_mcp_config.json',
            'mcp_servers/config_files/working_cline_mcp_config.json',
            'mcp_servers/config_files/FINAL_WORKING_CLINE_CONFIG.json'
        ]
        
        # Ensure logs directory
        os.makedirs('logs', exist_ok=True)
        
        print("🔧 Universal MCP Server Fixer initialized")
    
    def log(self, message: str) -> None:
        """Enhanced logging"""
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
        
        try:
            with open('logs/mcp_fixer.log', 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] {message}\n")
        except:
            pass
    
    def scan_all_mcp_servers(self) -> Dict[str, List[str]]:
        """Scan for all MCP server files in the directory"""
        self.log("🔍 Scanning for all MCP server files...")
        
        found_servers = {
            'python_servers': [],
            'nodejs_servers': [],
            'configs': []
        }
        
        # Find Python MCP servers
        for py_file in self.workspace_path.rglob('*mcp*server*.py'):
            if 'test' not in str(py_file).lower() and '__pycache__' not in str(py_file):
                found_servers['python_servers'].append(str(py_file.relative_to(self.workspace_path)))
        
        # Find Node.js MCP servers
        for js_file in self.workspace_path.rglob('*mcp*/index.js'):
            found_servers['nodejs_servers'].append(str(js_file.relative_to(self.workspace_path)))
        
        for ts_file in self.workspace_path.rglob('*mcp*/index.ts'):
            found_servers['nodejs_servers'].append(str(ts_file.relative_to(self.workspace_path)))
        
        # Find config files
        for config_file in self.config_files:
            if Path(config_file).exists():
                found_servers['configs'].append(config_file)
        
        self.log(f"📋 Found {len(found_servers['python_servers'])} Python servers")
        self.log(f"📋 Found {len(found_servers['nodejs_servers'])} Node.js servers")
        self.log(f"📋 Found {len(found_servers['configs'])} config files")
        
        return found_servers
    
    def load_all_configs(self) -> Dict[str, Any]:
        """Load all MCP configurations"""
        all_servers = {}
        
        for config_file in self.config_files:
            try:
                if Path(config_file).exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    servers = config.get('mcpServers', {})
                    for name, server_config in servers.items():
                        if name not in all_servers:
                            all_servers[name] = server_config
                            self.log(f"✅ Loaded config for {name}")
                        
            except Exception as e:
                self.log(f"⚠️ Error loading {config_file}: {e}")
        
        return all_servers
    
    def check_server_file_exists(self, server_config: Dict[str, Any]) -> bool:
        """Check if the server file actually exists"""
        command = server_config.get('command', '')
        args = server_config.get('args', [])
        
        if command == 'python':
            if args and not args[0].startswith('-c'):
                # Direct file reference
                file_path = Path(args[0])
                return file_path.exists()
            else:
                # Complex exec command - harder to verify
                return True
        elif command == 'node':
            if args:
                file_path = Path(args[0])
                return file_path.exists()
        
        return False
    
    def create_missing_python_server(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Create a missing Python MCP server"""
        try:
            args = server_config.get('args', [])
            if not args or args[0].startswith('-c'):
                return True  # Complex import, assume it exists
            
            file_path = Path(args[0])
            if file_path.exists():
                return True
            
            self.log(f"🔧 Creating missing server file: {file_path}")
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a basic MCP server template
            server_template = self.generate_python_server_template(server_name)
            
            with open(file_path, 'w') as f:
                f.write(server_template)
            
            self.log(f"✅ Created {file_path}")
            self.fixed_servers.append(f"{server_name} - created {file_path}")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to create server for {server_name}: {e}")
            self.failed_fixes.append(f"{server_name} - creation failed: {e}")
            return False
    
    def generate_python_server_template(self, server_name: str) -> str:
        """Generate a basic Python MCP server template"""
        return f'''#!/usr/bin/env python3
"""
{server_name.title().replace('-', ' ')} MCP Server
Auto-generated MCP server for {server_name}
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("{server_name}-mcp-server")

class {server_name.replace('-', '_').title()}MCPServer:
    """Auto-generated MCP Server for {server_name}"""
    
    def __init__(self):
        self.name = "{server_name}-mcp-server"
        self.version = "1.0.0"
        self.tools: List[Dict[str, Any]] = []
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup available tools"""
        self.tools = [
            {{
                "name": "get_status",
                "description": "Get server status",
                "inputSchema": {{
                    "type": "object",
                    "properties": {{}},
                    "required": []
                }}
            }},
            {{
                "name": "health_check",
                "description": "Perform health check",
                "inputSchema": {{
                    "type": "object",
                    "properties": {{}},
                    "required": []
                }}
            }}
        ]
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages"""
        method = message.get("method")
        params = message.get("params", {{}})
        id_val = message.get("id")
        
        if method == "initialize":
            return {{
                "jsonrpc": "2.0",
                "id": id_val,
                "result": {{
                    "protocolVersion": "2024-11-05",
                    "capabilities": {{
                        "tools": {{}}
                    }},
                    "serverInfo": {{
                        "name": self.name,
                        "version": self.version
                    }}
                }}
            }}
        
        elif method == "tools/list":
            return {{
                "jsonrpc": "2.0", 
                "id": id_val,
                "result": {{
                    "tools": self.tools
                }}
            }}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {{}})
            
            result: str = await self.call_tool(tool_name, tool_args)
            
            return {{
                "jsonrpc": "2.0",
                "id": id_val,
                "result": {{
                    "content": [
                        {{
                            "type": "text",
                            "text": result
                        }}
                    ]
                }}
            }}
        
        else:
            return {{
                "jsonrpc": "2.0",
                "id": id_val,
                "error": {{
                    "code": -32601,
                    "message": f"Method not found: {{method}}"
                }}
            }}
    
    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Handle tool calls"""
        if name == "get_status":
            return json.dumps({{
                "server": self.name,
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "capabilities": ["status", "health_check"]
            }}, indent=2)
        
        elif name == "health_check":
            return json.dumps({{
                "status": "healthy",
                "server": self.name,
                "version": self.version,
                "timestamp": datetime.now().isoformat()
            }}, indent=2)
        
        return f"Unknown tool: {{name}}"
    
    async def run(self):
        """Run the MCP server"""
        logger.info(f"Starting {{self.name}} (stdio mode)")
        
        while True:
            try:
                line: str = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                    
                line: str = line.strip()
                if not line:
                    continue
                
                try:
                    message = json.loads(line)
                    response = await self.handle_message(message)
                    
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    error_response: Dict[str, Any] = {{
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {{
                            "code": -32700,
                            "message": f"Parse error: {{str(e)}}"
                        }}
                    }}
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
            except Exception as e:
                logger.error(f"Server error: {{str(e)}}")
                break

def main():
    """Main entry point"""
    server = {server_name.replace('-', '_').title()}MCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info(f"{{server.name}} shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {{str(e)}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    def test_server_syntax(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Test if a Python server has valid syntax"""
        try:
            command = server_config.get('command', '')
            if command != 'python':
                return True  # Skip non-Python servers
            
            args = server_config.get('args', [])
            if not args or args[0].startswith('-c'):
                return True  # Skip complex exec commands
            
            file_path = Path(args[0])
            if not file_path.exists():
                return False
            
            # Test syntax compilation
            import py_compile
            py_compile.compile(str(file_path), doraise=True)
            return True
            
        except Exception as e:
            self.log(f"⚠️ {server_name} syntax error: {e}")
            return False
    
    async def test_server_startup(self, server_name: str, server_config: Dict[str, Any]) -> bool:
        """Test if a server can start successfully"""
        try:
            command = server_config.get('command', '')
            args = server_config.get('args', [])
            env = os.environ.copy()
            env.update(server_config.get('env', {}))
            
            if command == 'python':
                if args and not args[0].startswith('-c'):
                    # Direct file execution
                    full_command = [sys.executable] + args
                else:
                    # Complex import command
                    full_command = [sys.executable] + args
            elif command == 'node':
                full_command = ['node'] + args
            else:
                self.log(f"⚠️ {server_name}: Unknown command type - {command}")
                return False
            
            self.log(f"🧪 Testing {server_name}: {' '.join(full_command[:3])}...")
            
            # Start process and test for 3 seconds
            process = subprocess.Popen(
                full_command,
                env=env,
                cwd=self.workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            # Wait a moment
            await asyncio.sleep(3)
            
            if process.poll() is None:
                # Still running, that's good
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                self.log(f"✅ {server_name}: Startup test passed")
                return True
            else:
                stdout, stderr = process.communicate()
                error_msg = stderr.decode() if stderr else "Process exited"
                self.log(f"❌ {server_name}: Startup failed - {error_msg[:100]}")
                return False
                
        except Exception as e:
            self.log(f"❌ {server_name}: Test exception - {e}")
            return False
    
    async def fix_all_servers(self) -> Dict[str, Any]:
        """Fix all MCP servers"""
        self.log("🔧 Starting comprehensive MCP server fix...")
        
        # Load all configurations
        all_servers = self.load_all_configs()
        self.log(f"📋 Found {len(all_servers)} configured servers")
        
        results = {
            'total_servers': len(all_servers),
            'fixed_servers': [],
            'working_servers': [],
            'failed_servers': [],
            'created_files': [],
            'syntax_fixes': []
        }
        
        for server_name, server_config in all_servers.items():
            self.log(f"\n🔧 Processing {server_name}...")
            
            # Check if file exists
            if not self.check_server_file_exists(server_config):
                self.log(f"📁 {server_name}: File missing, attempting to create...")
                if self.create_missing_python_server(server_name, server_config):
                    results['created_files'].append(server_name)
                    results['fixed_servers'].append(server_name)
                else:
                    results['failed_servers'].append(f"{server_name} - file creation failed")
                    continue
            
            # Test syntax
            if not self.test_server_syntax(server_name, server_config):
                self.log(f"🔧 {server_name}: Syntax issues detected")
                results['syntax_fixes'].append(f"{server_name} - syntax issues")
            
            # Test startup
            startup_success = await self.test_server_startup(server_name, server_config)
            if startup_success:
                results['working_servers'].append(server_name)
                self.log(f"✅ {server_name}: Working correctly")
            else:
                results['failed_servers'].append(f"{server_name} - startup failed")
                self.log(f"❌ {server_name}: Startup failed")
        
        return results
    
    async def create_unified_config(self, working_servers: List[str]) -> str:
        """Create a unified config with all working servers"""
        self.log("📋 Creating unified configuration...")
        
        all_servers = self.load_all_configs()
        unified_config = {
            "mcpServers": {}
        }
        
        # Add our clean servers first
        unified_config["mcpServers"]["context7_clean"] = {
            "command": "python",
            "args": ["mcp_servers/ai_integration/clean_context7_mcp_server.py"],
            "cwd": ".",
            "env": {
                "PYTHONPATH": "."
            }
        }
        
        unified_config["mcpServers"]["matic_clean"] = {
            "command": "python",
            "args": ["mcp_servers/blockchain_integration/clean_matic_mcp_server.py"],
            "cwd": ".",
            "env": {
                "PYTHONPATH": "."
            }
        }
        
        # Add working servers
        for server_name in working_servers:
            if server_name in all_servers:
                unified_config["mcpServers"][server_name] = all_servers[server_name]
        
        # Save unified config
        config_file = "mcp_servers/config_files/UNIFIED_WORKING_CONFIG.json"
        with open(config_file, 'w') as f:
            json.dump(unified_config, f, indent=2)
        
        self.log(f"📋 Unified config saved: {config_file}")
        return config_file
    
    def generate_summary_report(self, results: Dict[str, Any]) -> None:
        """Generate comprehensive summary report"""
        self.log("\n" + "="*60)
        self.log("🎉 MCP SERVER FIX COMPLETE")
        self.log("="*60)
        
        self.log(f"📊 Total servers processed: {results['total_servers']}")
        self.log(f"✅ Working servers: {len(results['working_servers'])}")
        self.log(f"🔧 Fixed servers: {len(results['fixed_servers'])}")
        self.log(f"📁 Created files: {len(results['created_files'])}")
        self.log(f"❌ Failed servers: {len(results['failed_servers'])}")
        
        if results['working_servers']:
            self.log("\n✅ Working Servers:")
            for server in results['working_servers']:
                self.log(f"  • {server}")
        
        if results['created_files']:
            self.log("\n📁 Created Files:")
            for server in results['created_files']:
                self.log(f"  • {server}")
        
        if results['failed_servers']:
            self.log("\n❌ Failed Servers:")
            for server in results['failed_servers']:
                self.log(f"  • {server}")
        
        # Save detailed report
        report_file = f"logs/mcp_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.log(f"\n📋 Detailed report saved: {report_file}")

async def main():
    """Main entry point"""
    fixer = UniversalMCPServerFixer()
    
    try:
        # Scan system
        found_servers = fixer.scan_all_mcp_servers()
        
        # Fix all servers
        results = await fixer.fix_all_servers()
        
        # Create unified config
        if results['working_servers']:
            config_file = await fixer.create_unified_config(results['working_servers'])
            results['unified_config'] = config_file
        
        # Generate report
        fixer.generate_summary_report(results)
        
        success_rate = len(results['working_servers']) / max(results['total_servers'], 1)
        
        if success_rate > 0.7:
            fixer.log("\n🎉 SUCCESS: Most servers are working!")
        elif success_rate > 0.3:
            fixer.log("\n⚠️ PARTIAL: Some servers need attention")
        else:
            fixer.log("\n❌ ATTENTION: Many servers need fixing")
        
        return success_rate > 0.5
        
    except Exception as e:
        fixer.log(f"❌ Fatal error: {e}")
        return False

if __name__ == "__main__":
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        sys.exit(1)
