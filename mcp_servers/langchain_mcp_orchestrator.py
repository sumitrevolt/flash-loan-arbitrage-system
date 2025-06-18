#!/usr/bin/env python3
"""
LangChain-based MCP Server Orchestrator
Fixes MCP server connection issues and ensures proper server startup
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import socket
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    port: int
    executable: str
    args: List[str]
    working_dir: str
    env_vars: Dict[str, str] = None
    health_endpoint: str = "/health"
    startup_time: int = 10  # seconds to wait for startup

class LangChainMCPOrchestrator:
    """LangChain-based MCP server orchestrator"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.mcp_servers_dir = self.base_dir / "mcp_servers"
        self.processes = {}
        self.server_configs = {}
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure required directories exist"""
        self.mcp_servers_dir.mkdir(exist_ok=True)
        
        # Create individual server directories
        server_dirs = [
            "context7_clean",
            "flash_loan_blockchain", 
            "matic_mcp_server",
            "ai_integration",
            "blockchain_integration"
        ]
        
        for server_dir in server_dirs:
            (self.mcp_servers_dir / server_dir).mkdir(exist_ok=True)
            
    def create_mcp_server_configs(self) -> Dict[str, MCPServerConfig]:
        """Create configurations for all MCP servers"""
        configs = {}
        
        # Context7 Clean MCP Server
        configs["context7_clean"] = MCPServerConfig(
            name="context7_clean",
            port=4100,
            executable="python",
            args=["context7_mcp_server.py"],
            working_dir=str(self.mcp_servers_dir / "context7_clean"),
            env_vars={"MCP_SERVER_NAME": "context7_clean", "PORT": "4100"}
        )
        
        # Flash Loan Blockchain MCP Server
        configs["flash_loan_blockchain"] = MCPServerConfig(
            name="flash_loan_blockchain",
            port=4101,
            executable="python", 
            args=["flash_loan_mcp_server.py"],
            working_dir=str(self.mcp_servers_dir / "flash_loan_blockchain"),
            env_vars={"MCP_SERVER_NAME": "flash_loan_blockchain", "PORT": "4101"}
        )
        
        # Matic MCP Server
        configs["matic_mcp_server"] = MCPServerConfig(
            name="matic_mcp_server",
            port=4102,
            executable="python",
            args=["matic_mcp_server.py"],
            working_dir=str(self.mcp_servers_dir / "matic_mcp_server"),
            env_vars={"MCP_SERVER_NAME": "matic_mcp_server", "PORT": "4102"}
        )
        
        # AI Integration MCP Server
        configs["ai_integration"] = MCPServerConfig(
            name="ai_integration",
            port=4103,
            executable="python",
            args=["ai_integration_server.py"],
            working_dir=str(self.mcp_servers_dir / "ai_integration"),
            env_vars={"MCP_SERVER_NAME": "ai_integration", "PORT": "4103"}
        )
        
        # Blockchain Integration MCP Server  
        configs["blockchain_integration"] = MCPServerConfig(
            name="blockchain_integration",
            port=4104,
            executable="python",
            args=["blockchain_integration_server.py"],
            working_dir=str(self.mcp_servers_dir / "blockchain_integration"),
            env_vars={"MCP_SERVER_NAME": "blockchain_integration", "PORT": "4104"}
        )
        
        return configs
    
    def create_mcp_server_script(self, config: MCPServerConfig):
        """Create the actual MCP server script"""
        server_dir = Path(config.working_dir)
        server_dir.mkdir(exist_ok=True)
        
        # Create server script based on server type
        if "context7" in config.name:
            self.create_context7_server(server_dir, config)
        elif "flash_loan" in config.name:
            self.create_flash_loan_server(server_dir, config)
        elif "matic" in config.name:
            self.create_matic_server(server_dir, config)
        elif "ai_integration" in config.name:
            self.create_ai_integration_server(server_dir, config)
        elif "blockchain_integration" in config.name:
            self.create_blockchain_integration_server(server_dir, config)
    
    def create_context7_server(self, server_dir: Path, config: MCPServerConfig):
        """Create Context7 MCP server"""
        server_script = f"""#!/usr/bin/env python3
'''
Context7 Clean MCP Server
Provides context management and cleaning capabilities
'''

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class Context7MCPServer:
    def __init__(self):
        self.contexts = {{}}
        self.clean_contexts = {{}}
        
    def clean_context(self, context_data: Dict) -> Dict:
        '''Clean and optimize context data'''
        cleaned = {{
            'libraries': context_data.get('libraries', []),
            'documentation': context_data.get('documentation', ''),
            'code_examples': context_data.get('code_examples', []),
            'metadata': {{
                'cleaned_at': 'now',
                'original_size': len(str(context_data)),
                'cleaned_size': 0
            }}
        }}
        cleaned['metadata']['cleaned_size'] = len(str(cleaned))
        return cleaned
    
    def get_available_contexts(self) -> List[str]:
        '''Get list of available contexts'''
        return ['langchain', 'openai', 'anthropic', 'huggingface', 'web3', 'ethereum']

server = Context7MCPServer()

@app.route('/health')
def health():
    return jsonify({{'status': 'healthy', 'server': 'context7_clean', 'port': {config.port}}}))

@app.route('/contexts', methods=['GET'])
def list_contexts():
    return jsonify({{'contexts': server.get_available_contexts()}})

@app.route('/contexts/<context_name>', methods=['GET'])
def get_context(context_name):
    if context_name in server.contexts:
        return jsonify(server.contexts[context_name])
    return jsonify({{'error': 'Context not found'}}), 404

@app.route('/contexts/<context_name>/clean', methods=['POST'])
def clean_context(context_name):
    context_data = request.get_json() or {{}}
    cleaned = server.clean_context(context_data)
    server.clean_contexts[context_name] = cleaned
    return jsonify(cleaned)

@app.route('/mcp/capabilities', methods=['GET'])
def mcp_capabilities():
    return jsonify({{
        'server_info': {{
            'name': 'context7_clean',
            'version': '1.0.0'
        }},
        'capabilities': {{
            'tools': ['clean_context', 'list_contexts', 'get_context'],
            'resources': ['contexts', 'documentation']
        }}
    }})

if __name__ == '__main__':
    logger.info(f"Starting Context7 Clean MCP Server on port {config.port}")
    app.run(host='0.0.0.0', port={config.port}, debug=False)
"""
        
        with open(server_dir / config.args[0], 'w') as f:
            f.write(server_script)
    
    def create_flash_loan_server(self, server_dir: Path, config: MCPServerConfig):
        """Create Flash Loan MCP server"""
        server_script = f"""#!/usr/bin/env python3
'''
Flash Loan Blockchain MCP Server
Handles flash loan operations and blockchain interactions
'''

import json
import asyncio
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class FlashLoanMCPServer:
    def __init__(self):
        self.active_loans = {{}}
        self.supported_protocols = ['aave', 'compound', 'uniswap', 'balancer']
        
    def calculate_arbitrage_opportunity(self, token_pair: str) -> Dict:
        '''Calculate potential arbitrage opportunities'''
        return {{
            'token_pair': token_pair,
            'potential_profit': 0.02,  # 2% example
            'gas_cost': 0.001,
            'net_profit': 0.019,
            'recommended': True
        }}
    
    def simulate_flash_loan(self, amount: float, token: str, protocol: str) -> Dict:
        '''Simulate flash loan execution'''
        return {{
            'loan_amount': amount,
            'token': token,
            'protocol': protocol,
            'estimated_fee': amount * 0.0009,  # 0.09% fee
            'success_probability': 0.95,
            'execution_time': '2-3 blocks'
        }}

server = FlashLoanMCPServer()

@app.route('/health')
def health():
    return jsonify({{'status': 'healthy', 'server': 'flash_loan_blockchain', 'port': {config.port}}}))

@app.route('/protocols', methods=['GET'])
def list_protocols():
    return jsonify({{'protocols': server.supported_protocols}})

@app.route('/arbitrage/<token_pair>', methods=['GET'])
def check_arbitrage(token_pair):
    opportunity = server.calculate_arbitrage_opportunity(token_pair)
    return jsonify(opportunity)

@app.route('/flash-loan/simulate', methods=['POST'])
def simulate_flash_loan():
    data = request.get_json()
    amount = data.get('amount', 1000)
    token = data.get('token', 'USDC')
    protocol = data.get('protocol', 'aave')
    
    simulation = server.simulate_flash_loan(amount, token, protocol)
    return jsonify(simulation)

@app.route('/mcp/capabilities', methods=['GET'])
def mcp_capabilities():
    return jsonify({{
        'server_info': {{
            'name': 'flash_loan_blockchain',
            'version': '1.0.0'
        }},
        'capabilities': {{
            'tools': ['calculate_arbitrage', 'simulate_flash_loan', 'list_protocols'],
            'resources': ['protocols', 'arbitrage_opportunities']
        }}
    }})

if __name__ == '__main__':
    logger.info(f"Starting Flash Loan Blockchain MCP Server on port {config.port}")
    app.run(host='0.0.0.0', port={config.port}, debug=False)
"""
        
        with open(server_dir / config.args[0], 'w') as f:
            f.write(server_script)
    
    def create_matic_server(self, server_dir: Path, config: MCPServerConfig):
        """Create Matic/Polygon MCP server"""
        server_script = f"""#!/usr/bin/env python3
'''
Matic MCP Server
Handles Polygon/Matic blockchain operations
'''

import json
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class MaticMCPServer:
    def __init__(self):
        self.network_info = {{
            'chain_id': 137,
            'name': 'Polygon Mainnet',
            'rpc_url': 'https://polygon-rpc.com',
            'block_time': 2  # seconds
        }}
        
    def get_gas_price(self) -> Dict:
        '''Get current gas prices on Polygon'''
        return {{
            'slow': 30,      # 30 gwei
            'standard': 35,  # 35 gwei  
            'fast': 40,      # 40 gwei
            'unit': 'gwei'
        }}
    
    def get_token_info(self, token_address: str) -> Dict:
        '''Get token information'''
        # Mock token data
        tokens = {{
            '0x2791bca1f2de4661ed88a30c99a7a9449aa84174': {{
                'symbol': 'USDC',
                'name': 'USD Coin',
                'decimals': 6
            }},
            '0x8f3cf7ad23cd3cadbd9735aff958023239c6a063': {{
                'symbol': 'DAI', 
                'name': 'Dai Stablecoin',
                'decimals': 18
            }}
        }}
        return tokens.get(token_address.lower(), {{'symbol': 'UNKNOWN', 'name': 'Unknown Token', 'decimals': 18}})

server = MaticMCPServer()

@app.route('/health')
def health():
    return jsonify({{'status': 'healthy', 'server': 'matic_mcp_server', 'port': {config.port}}}))

@app.route('/network', methods=['GET'])
def network_info():
    return jsonify(server.network_info)

@app.route('/gas', methods=['GET'])
def gas_prices():
    return jsonify(server.get_gas_price())

@app.route('/token/<token_address>', methods=['GET'])
def token_info(token_address):
    info = server.get_token_info(token_address)
    return jsonify(info)

@app.route('/mcp/capabilities', methods=['GET'])
def mcp_capabilities():
    return jsonify({{
        'server_info': {{
            'name': 'matic_mcp_server',
            'version': '1.0.0'
        }},
        'capabilities': {{
            'tools': ['get_gas_price', 'get_token_info', 'network_info'],
            'resources': ['network', 'tokens', 'gas_prices']
        }}
    }})

if __name__ == '__main__':
    logger.info(f"Starting Matic MCP Server on port {config.port}")
    app.run(host='0.0.0.0', port={config.port}, debug=False)
"""
        
        with open(server_dir / config.args[0], 'w') as f:
            f.write(server_script)
    
    def create_ai_integration_server(self, server_dir: Path, config: MCPServerConfig):
        """Create AI Integration MCP server"""
        server_script = f"""#!/usr/bin/env python3
'''
AI Integration MCP Server
Handles AI model integrations and LangChain operations
'''

import json
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class AIMCPServer:
    def __init__(self):
        self.available_models = ['gpt-4', 'claude-3', 'llama-2', 'mistral']
        self.active_sessions = {{}}
        
    def create_ai_session(self, model: str, config: Dict) -> str:
        '''Create a new AI session'''
        session_id = f"session_{{len(self.active_sessions) + 1}}"
        self.active_sessions[session_id] = {{
            'model': model,
            'config': config,
            'created_at': 'now'
        }}
        return session_id
    
    def get_model_capabilities(self, model: str) -> Dict:
        '''Get capabilities of a specific model'''
        capabilities = {{
            'gpt-4': ['text_generation', 'code_analysis', 'reasoning'],
            'claude-3': ['text_generation', 'analysis', 'coding'],
            'llama-2': ['text_generation', 'conversation'],
            'mistral': ['text_generation', 'multilingual']
        }}
        return {{'model': model, 'capabilities': capabilities.get(model, [])}}

server = AIMCPServer()

@app.route('/health')
def health():
    return jsonify({{'status': 'healthy', 'server': 'ai_integration', 'port': {config.port}}}))

@app.route('/models', methods=['GET'])
def list_models():
    return jsonify({{'models': server.available_models}})

@app.route('/models/<model>/capabilities', methods=['GET'])
def model_capabilities(model):
    return jsonify(server.get_model_capabilities(model))

@app.route('/sessions', methods=['POST'])
def create_session():
    data = request.get_json()
    model = data.get('model', 'gpt-4')
    config = data.get('config', {{}})
    session_id = server.create_ai_session(model, config)
    return jsonify({{'session_id': session_id}})

@app.route('/mcp/capabilities', methods=['GET'])
def mcp_capabilities():
    return jsonify({{
        'server_info': {{
            'name': 'ai_integration',
            'version': '1.0.0'
        }},
        'capabilities': {{
            'tools': ['create_session', 'list_models', 'model_capabilities'],
            'resources': ['models', 'sessions']
        }}
    }})

if __name__ == '__main__':
    logger.info(f"Starting AI Integration MCP Server on port {config.port}")
    app.run(host='0.0.0.0', port={config.port}, debug=False)
"""
        
        with open(server_dir / config.args[0], 'w') as f:
            f.write(server_script)
    
    def create_blockchain_integration_server(self, server_dir: Path, config: MCPServerConfig):
        """Create Blockchain Integration MCP server"""
        server_script = f"""#!/usr/bin/env python3
'''
Blockchain Integration MCP Server
General blockchain operations and integrations
'''

import json
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class BlockchainMCPServer:
    def __init__(self):
        self.supported_chains = ['ethereum', 'polygon', 'bsc', 'arbitrum']
        self.active_connections = {{}}
        
    def get_chain_info(self, chain: str) -> Dict:
        '''Get information about a blockchain'''
        chain_data = {{
            'ethereum': {{'chain_id': 1, 'name': 'Ethereum Mainnet', 'native_token': 'ETH'}},
            'polygon': {{'chain_id': 137, 'name': 'Polygon', 'native_token': 'MATIC'}},
            'bsc': {{'chain_id': 56, 'name': 'BNB Smart Chain', 'native_token': 'BNB'}},
            'arbitrum': {{'chain_id': 42161, 'name': 'Arbitrum One', 'native_token': 'ETH'}}
        }}
        return chain_data.get(chain, {{}})
    
    def estimate_transaction_fee(self, chain: str, tx_type: str) -> Dict:
        '''Estimate transaction fees'''
        base_fees = {{
            'ethereum': 0.002,
            'polygon': 0.0001,
            'bsc': 0.0005,
            'arbitrum': 0.0008
        }}
        
        multipliers = {{
            'simple_transfer': 1.0,
            'contract_interaction': 1.5,
            'complex_defi': 2.0
        }}
        
        base_fee = base_fees.get(chain, 0.001)
        multiplier = multipliers.get(tx_type, 1.0)
        
        return {{
            'chain': chain,
            'transaction_type': tx_type,
            'estimated_fee': base_fee * multiplier,
            'currency': 'ETH' if chain in ['ethereum', 'arbitrum'] else 'MATIC' if chain == 'polygon' else 'BNB'
        }}

server = BlockchainMCPServer()

@app.route('/health')
def health():
    return jsonify({{'status': 'healthy', 'server': 'blockchain_integration', 'port': {config.port}}}))

@app.route('/chains', methods=['GET'])
def list_chains():
    return jsonify({{'chains': server.supported_chains}})

@app.route('/chains/<chain>', methods=['GET'])
def chain_info(chain):
    return jsonify(server.get_chain_info(chain))

@app.route('/fees/<chain>/<tx_type>', methods=['GET'])
def estimate_fees(chain, tx_type):
    return jsonify(server.estimate_transaction_fee(chain, tx_type))

@app.route('/mcp/capabilities', methods=['GET'])
def mcp_capabilities():
    return jsonify({{
        'server_info': {{
            'name': 'blockchain_integration',
            'version': '1.0.0'
        }},
        'capabilities': {{
            'tools': ['get_chain_info', 'estimate_fees', 'list_chains'],
            'resources': ['chains', 'transactions', 'fees']
        }}
    }})

if __name__ == '__main__':
    logger.info(f"Starting Blockchain Integration MCP Server on port {config.port}")
    app.run(host='0.0.0.0', port={config.port}, debug=False)
"""
        
        with open(server_dir / config.args[0], 'w') as f:
            f.write(server_script)
    
    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result: str = sock.connect_ex(('localhost', port))
                return result != 0  # Port is available if connection fails
        except:
            return True
    
    def start_mcp_server(self, config: MCPServerConfig) -> bool:
        """Start an individual MCP server"""        logger.info(f"Starting MCP server: {config.name} on port {config.port}")
        
        # Check if port is available
        if not self.check_port_available(config.port):
            logger.warning(f"Port {config.port} is already in use for {config.name}")
            return False
        
        # Create server script if it doesn't exist
        script_path = Path(config.working_dir) / config.args[0]
        if not script_path.exists():
            self.create_mcp_server_script(config)
        
        # Set up environment
        env = os.environ.copy()
        if config.env_vars:
            env.update(config.env_vars)
        
        try:
            # Start the process
            process = subprocess.Popen(
                [config.executable] + config.args,
                cwd=config.working_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[config.name] = process
            logger.info(f"Started {{config.name}} with PID {{process.pid}}")
            
            # Wait a bit for startup
            time.sleep(config.startup_time)
            
            # Check if process is still running
            if process.poll() is None:
                # Test health endpoint
                try:
                    response = requests.get(f"http://localhost:{{config.port}}/health", timeout=5)
                    if response.status_code == 200:
                        logger.info(f"✅ {{config.name}} is healthy on port {{config.port}}")
                        return True
                    else:
                        logger.error(f"❌ {{config.name}} health check failed")
                        return False
                except Exception as e:
                    logger.error(f"❌ {{config.name}} health check error: {{e}}")
                    return False
            else:
                logger.error(f"❌ {{config.name}} process exited early")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {{config.name}}: {{e}}")
            return False
    
    def stop_mcp_server(self, server_name: str):
        """Stop an MCP server"""
        if server_name in self.processes:
            process = self.processes[server_name]
            process.terminate()
            try:
                process.wait(timeout=10)
                logger.info(f"Stopped {{server_name}}")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.info(f"Force killed {{server_name}}")
            del self.processes[server_name]
    
    def start_all_servers(self) -> Dict[str, bool]:
        """Start all MCP servers"""
        logger.info("🚀 Starting all MCP servers...")
        
        configs = self.create_mcp_server_configs()
        results = {{}}
        
        for name, config in configs.items():
            self.server_configs[name] = config
            results[name] = self.start_mcp_server(config)
        
        return results
    
    def get_server_status(self) -> Dict[str, Dict]:
        """Get status of all servers"""
        status = {{}}
        
        for name, config in self.server_configs.items():
            process = self.processes.get(name)
            is_running = process is not None and process.poll() is None
            
            # Test health if running
            health_ok = False
            if is_running:
                try:
                    response = requests.get(f"http://localhost:{{config.port}}/health", timeout=3)
                    health_ok = response.status_code == 200
                except:
                    pass
            
            status[name] = {{
                'running': is_running,
                'healthy': health_ok,
                'port': config.port,
                'pid': process.pid if process else None
            }}
        
        return status
    
    def create_cline_mcp_config(self) -> Dict:
        """Create MCP configuration for Cline/VS Code"""
        mcp_config = {{
            "mcpServers": {{}}
        }}
        
        for name, config in self.server_configs.items():
            mcp_config["mcpServers"][name] = {{
                "command": config.executable,
                "args": config.args,
                "cwd": config.working_dir,
                "env": config.env_vars or {{}},
                "url": f"http://localhost:{{config.port}}"
            }}
        
        return mcp_config
    
    def save_cline_config(self):
        """Save MCP configuration for Cline"""
        config = self.create_cline_mcp_config()
        config_path = self.base_dir / ".vscode" / "settings.json"
        config_path.parent.mkdir(exist_ok=True)
        
        # Load existing settings if they exist
        existing_settings = {{}}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    existing_settings = json.load(f)
            except:
                pass
        
        # Update with MCP config
        existing_settings.update(config)
        
        with open(config_path, 'w') as f:
            json.dump(existing_settings, f, indent=2)
        
        logger.info(f"✅ Saved Cline MCP configuration to {{config_path}}")

def main():
    """Main orchestrator function"""
    print("🏦 LangChain MCP Server Orchestrator")
    print("=" * 50)
    
    orchestrator = LangChainMCPOrchestrator()
    
    try:
        # Start all servers
        results = orchestrator.start_all_servers()
        
        print("\\n📊 Startup Results:")
        print("-" * 30)
        
        success_count = 0
        for server_name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {{server_name:<25}} {{status}}")
            if success:
                success_count += 1
        
        print(f"\\n🎯 Summary: {{success_count}}/{{len(results)}} servers started successfully")
        
        if success_count > 0:
            # Get detailed status
            status = orchestrator.get_server_status()
            print("\\n📋 Server Status:")
            print("-" * 50)
            
            for name, info in status.items():
                running = "🟢" if info['running'] else "🔴"
                healthy = "✅" if info['healthy'] else "❌"
                print(f"  {{name:<25}} {{running}} Running {{healthy}} Healthy (Port: {{info['port']}})")
            
            # Save Cline configuration
            orchestrator.save_cline_config()
            
            print("\\n🎉 MCP servers are now running and configured for Cline!")
            print("\\n📝 Next steps:")
            print("  1. Restart VS Code/Cline")
            print("  2. Check that MCP servers appear as 'online' in Cline")
            print("  3. Test MCP server functionality")
            
            print("\\n⏹️  To stop servers, press Ctrl+C")
            
            # Keep running
            try:
                while True:
                    time.sleep(30)
                    # Check server health periodically
                    current_status = orchestrator.get_server_status()
                    unhealthy = [name for name, info in current_status.items() if info['running'] and not info['healthy']]
                    if unhealthy:
                        logger.warning(f"Unhealthy servers detected: {{unhealthy}}")
            except KeyboardInterrupt:
                print("\\n\\n🛑 Stopping all MCP servers...")
                for server_name in orchestrator.processes.keys():
                    orchestrator.stop_mcp_server(server_name)
                print("✅ All servers stopped")
        else:
            print("\\n❌ No servers started successfully. Check logs for errors.")
            return 1
            
    except Exception as e:
        logger.error(f"Orchestrator error: {{e}}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
