#!/usr/bin/env python3
"""
Simple MCP Server Orchestrator - Fixed Version
Starts individual MCP servers for Cline integration
"""

import subprocess
import time
import json
import os
import socket
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMCPOrchestrator:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.mcp_servers_dir = self.base_dir / "mcp_servers"
        self.processes = {}
        
    def setup_directories(self):
        """Create necessary directories"""
        self.mcp_servers_dir.mkdir(exist_ok=True)
        
        # Create server directories
        server_names = ["context7_clean", "flash_loan_blockchain", "matic_mcp_server"]
        for name in server_names:
            (self.mcp_servers_dir / name).mkdir(exist_ok=True)
    
    def create_context7_server(self):
        """Create context7_clean MCP server"""
        server_dir = self.mcp_servers_dir / "context7_clean"
        
        server_code = '''#!/usr/bin/env python3
from flask import Flask, jsonify
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "server": "context7_clean", "port": 4100})

@app.route('/mcp/capabilities')
def capabilities():
    return jsonify({
        "server_info": {"name": "context7_clean", "version": "1.0.0"},
        "capabilities": {
            "tools": ["clean_context", "list_contexts"],
            "resources": ["contexts", "documentation"]
        }
    })

@app.route('/contexts')
def list_contexts():
    return jsonify({"contexts": ["langchain", "openai", "web3", "ethereum"]})

if __name__ == '__main__':
    print("Starting Context7 Clean MCP Server on port 4100")
    app.run(host='0.0.0.0', port=4100, debug=False)
'''
        
        with open(server_dir / "server.py", 'w') as f:
            f.write(server_code)
            
    def create_flash_loan_server(self):
        """Create flash_loan_blockchain MCP server"""
        server_dir = self.mcp_servers_dir / "flash_loan_blockchain"
        
        server_code = '''#!/usr/bin/env python3
from flask import Flask, jsonify, request
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "server": "flash_loan_blockchain", "port": 4101})

@app.route('/mcp/capabilities')
def capabilities():
    return jsonify({
        "server_info": {"name": "flash_loan_blockchain", "version": "1.0.0"},
        "capabilities": {
            "tools": ["simulate_flash_loan", "calculate_arbitrage"],
            "resources": ["protocols", "opportunities"]
        }
    })

@app.route('/protocols')
def protocols():
    return jsonify({"protocols": ["aave", "compound", "uniswap", "balancer"]})

@app.route('/arbitrage/<token_pair>')
def arbitrage(token_pair):
    return jsonify({
        "token_pair": token_pair,
        "potential_profit": 0.02,
        "gas_cost": 0.001,
        "net_profit": 0.019,
        "recommended": True
    })

if __name__ == '__main__':
    print("Starting Flash Loan Blockchain MCP Server on port 4101")
    app.run(host='0.0.0.0', port=4101, debug=False)
'''
        
        with open(server_dir / "server.py", 'w') as f:
            f.write(server_code)
    
    def create_matic_server(self):
        """Create matic_mcp_server"""
        server_dir = self.mcp_servers_dir / "matic_mcp_server"
        
        server_code = '''#!/usr/bin/env python3
from flask import Flask, jsonify
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "server": "matic_mcp_server", "port": 4102})

@app.route('/mcp/capabilities')
def capabilities():
    return jsonify({
        "server_info": {"name": "matic_mcp_server", "version": "1.0.0"},
        "capabilities": {
            "tools": ["get_gas_price", "get_token_info"],
            "resources": ["network", "tokens"]
        }
    })

@app.route('/network')
def network():
    return jsonify({
        "chain_id": 137,
        "name": "Polygon Mainnet",
        "rpc_url": "https://polygon-rpc.com"
    })

@app.route('/gas')
def gas():
    return jsonify({
        "slow": 30,
        "standard": 35,
        "fast": 40,
        "unit": "gwei"
    })

if __name__ == '__main__':
    print("Starting Matic MCP Server on port 4102")
    app.run(host='0.0.0.0', port=4102, debug=False)
'''
        
        with open(server_dir / "server.py", 'w') as f:
            f.write(server_code)
    
    def check_port(self, port):
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result: str = sock.connect_ex(('localhost', port))
                return result != 0
        except:
            return True
    
    def start_server(self, name, port, server_dir):
        """Start a single MCP server"""
        if not self.check_port(port):
            logger.warning(f"Port {port} already in use for {name}")
            return False
            
        try:
            logger.info(f"Starting {name} on port {port}")
            process = subprocess.Popen(
                ['python', 'server.py'],
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[name] = process
            logger.info(f"Started {name} with PID {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            return False
    
    def create_cline_config(self):
        """Create Cline MCP configuration"""
        config = {
            "mcpServers": {
                "context7_clean": {
                    "command": "python",
                    "args": ["server.py"],
                    "cwd": str(self.mcp_servers_dir / "context7_clean"),
                    "env": {}
                },
                "flash_loan_blockchain": {
                    "command": "python",
                    "args": ["server.py"],
                    "cwd": str(self.mcp_servers_dir / "flash_loan_blockchain"),
                    "env": {}
                },
                "matic_mcp_server": {
                    "command": "python",
                    "args": ["server.py"],
                    "cwd": str(self.mcp_servers_dir / "matic_mcp_server"),
                    "env": {}
                }
            }
        }
        
        # Save to VS Code settings
        vscode_dir = self.base_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        settings_file = vscode_dir / "settings.json"
        existing_settings = {}
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    existing_settings = json.load(f)
            except:
                pass
        
        existing_settings.update(config)
        
        with open(settings_file, 'w') as f:
            json.dump(existing_settings, f, indent=2)
        
        logger.info(f"Saved Cline configuration to {settings_file}")
    
    def run(self):
        """Main run method"""
        print("🚀 Simple MCP Server Orchestrator")
        print("=" * 40)
        
        # Setup
        logger.info("Setting up directories...")
        self.setup_directories()
        
        # Create server scripts
        logger.info("Creating server scripts...")
        self.create_context7_server()
        self.create_flash_loan_server()
        self.create_matic_server()
        
        # Start servers
        servers = [
            ("context7_clean", 4100, self.mcp_servers_dir / "context7_clean"),
            ("flash_loan_blockchain", 4101, self.mcp_servers_dir / "flash_loan_blockchain"),
            ("matic_mcp_server", 4102, self.mcp_servers_dir / "matic_mcp_server")
        ]
        
        success_count = 0
        for name, port, server_dir in servers:
            if self.start_server(name, port, server_dir):
                success_count += 1
        
        print(f"\n✅ Started {success_count}/{len(servers)} servers")
        
        if success_count > 0:
            # Wait for servers to start
            time.sleep(5)
            
            # Test health endpoints
            import requests
            print("\n📊 Health Check:")
            for name, port, _ in servers:
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=3)
                    if response.status_code == 200:
                        print(f"  ✅ {name} (:{port}) - Healthy")
                    else:
                        print(f"  ❌ {name} (:{port}) - Unhealthy")
                except:
                    print(f"  ❌ {name} (:{port}) - Not responding")
            
            # Create Cline config
            self.create_cline_config()
            
            print(f"\n🎉 MCP servers ready for Cline!")
            print(f"📝 Next steps:")
            print(f"  1. Restart VS Code/Cline")
            print(f"  2. Check MCP server status in Cline")
            print(f"  3. Servers should now appear as 'online'")
            
            print(f"\n⏹️  Press Ctrl+C to stop servers")
            
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                print(f"\n🛑 Stopping servers...")
                for name, process in self.processes.items():
                    process.terminate()
                    logger.info(f"Stopped {name}")
                print("✅ All servers stopped")
        else:
            print("❌ No servers started successfully")
            return 1
        
        return 0

def main():
    orchestrator = SimpleMCPOrchestrator()
    return orchestrator.run()

if __name__ == "__main__":
    exit(main())
