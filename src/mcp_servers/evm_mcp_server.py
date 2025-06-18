#!/usr/bin/env python3
"""
EVM MCP Server
Provides Ethereum Virtual Machine blockchain integration for the flash loan system

Key capabilities:
- Smart contract interaction for EVM blockchains
- Transaction management and monitoring
- Gas price optimization
- Multi-chain support for EVM compatible networks
"""

import asyncio
import json
import sys
import logging
import os
import time
import requests
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(os.path.join("logs", "evm_mcp_server.log"))
    ]
)
logger = logging.getLogger("evm-mcp-server")

class EVMMCPServer:
    """EVM MCP Server for blockchain integration"""
    
    def __init__(self):
        self.name = "evm-mcp-server"
        self.server_type = "blockchain_integration_evm"
        self.version = "1.0.0"
        self.tools = []
        self.active_requests = {}
        self.request_history = []
        self.coordinator_url = os.getenv("MCP_COORDINATOR_URL", "http://localhost:9000")
        self.status = "operational"
        self.networks = {
            "ethereum": {
                "rpc_url": os.getenv("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/your-api-key"),
                "chain_id": 1,
                "name": "Ethereum Mainnet"
            },
            "polygon": {
                "rpc_url": os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
                "chain_id": 137,
                "name": "Polygon Mainnet"
            },
            "arbitrum": {
                "rpc_url": os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
                "chain_id": 42161,
                "name": "Arbitrum One"
            }
        }
        self._setup_tools()
        
    def _setup_tools(self):
        """Setup available tools for the EVM server"""
        self.tools = [
            {
                "name": "get_network_status",
                "description": "Get status of supported EVM networks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "network": {"type": "string", "description": "Network name (ethereum, polygon, etc.)"}
                    }
                }
            },
            {
                "name": "estimate_gas",
                "description": "Estimate gas for a transaction",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "network": {"type": "string", "description": "Network name"},
                        "from_address": {"type": "string", "description": "Sender address"},
                        "to_address": {"type": "string", "description": "Recipient address"},
                        "data": {"type": "string", "description": "Transaction data hexstring"},
                        "value": {"type": "string", "description": "Value in wei"}
                    },
                    "required": ["network", "to_address"]
                }
            },
            {
                "name": "get_gas_price",
                "description": "Get current gas price on specified network",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "network": {"type": "string", "description": "Network name"}
                    },
                    "required": ["network"]
                }
            },
            {
                "name": "send_transaction",
                "description": "Send a transaction to the blockchain",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "network": {"type": "string", "description": "Network name"},
                        "private_key": {"type": "string", "description": "Private key for signing"},
                        "to_address": {"type": "string", "description": "Recipient address"},
                        "data": {"type": "string", "description": "Transaction data hexstring"},
                        "value": {"type": "string", "description": "Value in wei"},
                        "gas_limit": {"type": "number", "description": "Gas limit"},
                        "gas_price": {"type": "string", "description": "Gas price in wei"}
                    },
                    "required": ["network", "to_address"]
                }
            },
            {
                "name": "get_transaction_receipt",
                "description": "Get receipt for a transaction",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "network": {"type": "string", "description": "Network name"},
                        "tx_hash": {"type": "string", "description": "Transaction hash"}
                    },
                    "required": ["network", "tx_hash"]
                }
            },
            {
                "name": "call_contract",
                "description": "Call a contract method (read-only)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "network": {"type": "string", "description": "Network name"},
                        "contract_address": {"type": "string", "description": "Contract address"},
                        "abi": {"type": "object", "description": "Contract ABI"},
                        "function_name": {"type": "string", "description": "Function name to call"},
                        "function_params": {"type": "array", "description": "Function parameters"}
                    },
                    "required": ["network", "contract_address", "function_name"]
                }
            },
            {
                "name": "health_check",
                "description": "Check the health of the EVM server",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "register_with_coordinator",
                "description": "Register this server with the MCP coordinator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "coordinator_url": {"type": "string", "description": "URL of the coordinator"},
                        "capabilities": {"type": "array", "items": {"type": "string"}, "description": "Server capabilities"}
                    }
                }
            }
        ]
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP JSON-RPC messages"""
        method = message.get("method")
        params = message.get("params", {})
        id_val = message.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": id_val,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", 
                "id": id_val,
                "result": {
                    "tools": self.tools
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            result: str = await self.call_tool(tool_name, tool_args)
            
            return {
                "jsonrpc": "2.0",
                "id": id_val,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
        
        # Handle HTTP-style requests for backward compatibility
        elif method == "POST" and "path" in params:
            path = params.get("path", "")
            body = params.get("body", {})
            
            if path == "/network_status":
                result: str = await self.call_tool("get_network_status", body)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/gas_price":
                result: str = await self.call_tool("get_gas_price", body)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/send_transaction":
                result: str = await self.call_tool("send_transaction", body)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/call_contract":
                result: str = await self.call_tool("call_contract", body)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/health":
                result: str = await self.call_tool("health_check", {})
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
            
            elif path == "/register":
                result: str = await self.call_tool("register_with_coordinator", body)
                return {"jsonrpc": "2.0", "id": id_val, "result": json.loads(result)}
        
        return {
            "jsonrpc": "2.0",
            "id": id_val,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }
    
    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Handle tool calls for the EVM server"""
        logger.info(f"Tool call: {name} with args {args}")
        
        if name == "get_network_status":
            return await self._get_network_status(args)
        
        elif name == "estimate_gas":
            return await self._estimate_gas(args)
        
        elif name == "get_gas_price":
            return await self._get_gas_price(args)
        
        elif name == "send_transaction":
            return await self._send_transaction(args)
        
        elif name == "get_transaction_receipt":
            return await self._get_transaction_receipt(args)
        
        elif name == "call_contract":
            return await self._call_contract(args)
        
        elif name == "health_check":
            return await self._health_check(args)
        
        elif name == "register_with_coordinator":
            return await self._register_with_coordinator(args)
        
        return json.dumps({
            "error": f"Unknown tool: {name}",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _get_network_status(self, args: Dict[str, Any]) -> str:
        """Get status of supported EVM networks"""
        network = args.get("network")
        
        if network and network in self.networks:
            # Simulate network status check for specific network
            return json.dumps({
                "success": True,
                "network": network,
                "status": "connected",
                "chain_id": self.networks[network]["chain_id"],
                "latest_block": 12345678,  # Simulated block number
                "timestamp": datetime.now().isoformat()
            })
        else:
            # Return status for all networks
            statuses = {}
            for net_name, net_info in self.networks.items():
                statuses[net_name] = {
                    "status": "connected",
                    "chain_id": net_info["chain_id"],
                    "latest_block": 12345678  # Simulated block number
                }
            
            return json.dumps({
                "success": True,
                "networks": statuses,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _estimate_gas(self, args: Dict[str, Any]) -> str:
        """Estimate gas for a transaction"""
        network = args.get("network")
        to_address = args.get("to_address")
        
        if not network or network not in self.networks:
            return json.dumps({
                "success": False,
                "error": "Invalid or missing network",
                "timestamp": datetime.now().isoformat()
            })
        
        if not to_address:
            return json.dumps({
                "success": False,
                "error": "Missing to_address",
                "timestamp": datetime.now().isoformat()
            })
        
        # Simulate gas estimation
        estimated_gas = 50000 + (hash(to_address) % 10000)  # Simulated gas amount
        
        return json.dumps({
            "success": True,
            "network": network,
            "estimated_gas": estimated_gas,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _get_gas_price(self, args: Dict[str, Any]) -> str:
        """Get current gas price on specified network"""
        network = args.get("network")
        
        if not network or network not in self.networks:
            return json.dumps({
                "success": False,
                "error": "Invalid or missing network",
                "timestamp": datetime.now().isoformat()
            })
        
        # Simulate gas price information
        base_prices = {
            "ethereum": 30,
            "polygon": 80,
            "arbitrum": 0.1
        }
        
        # Simulate EIP-1559 prices where applicable
        if network in ["ethereum", "polygon"]:
            return json.dumps({
                "success": True,
                "network": network,
                "gas_price_wei": str(int(base_prices[network] * 1e9)),  # Convert Gwei to Wei
                "max_fee_per_gas_wei": str(int(base_prices[network] * 1.2 * 1e9)),
                "max_priority_fee_per_gas_wei": str(int(2 * 1e9)),  # 2 Gwei
                "eip1559_supported": True,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return json.dumps({
                "success": True,
                "network": network,
                "gas_price_wei": str(int(base_prices[network] * 1e9)),  # Convert Gwei to Wei
                "eip1559_supported": False,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _send_transaction(self, args: Dict[str, Any]) -> str:
        """Send a transaction to the blockchain"""
        network = args.get("network")
        to_address = args.get("to_address")
        
        if not network or network not in self.networks:
            return json.dumps({
                "success": False,
                "error": "Invalid or missing network",
                "timestamp": datetime.now().isoformat()
            })
        
        if not to_address:
            return json.dumps({
                "success": False,
                "error": "Missing to_address",
                "timestamp": datetime.now().isoformat()
            })
        
        # Simulate transaction submission
        # Generate a fake transaction hash
        import hashlib
        fake_tx_hash = "0x" + hashlib.sha256(f"{network}:{to_address}:{time.time()}".encode()).hexdigest()
        
        return json.dumps({
            "success": True,
            "network": network,
            "transaction_hash": fake_tx_hash,
            "timestamp": datetime.now().isoformat(),
            "message": "Transaction submitted, check receipt for confirmation"
        })
    
    async def _get_transaction_receipt(self, args: Dict[str, Any]) -> str:
        """Get receipt for a transaction"""
        network = args.get("network")
        tx_hash = args.get("tx_hash")
        
        if not network or network not in self.networks:
            return json.dumps({
                "success": False,
                "error": "Invalid or missing network",
                "timestamp": datetime.now().isoformat()
            })
        
        if not tx_hash:
            return json.dumps({
                "success": False,
                "error": "Missing transaction hash",
                "timestamp": datetime.now().isoformat()
            })
        
        # Simulate transaction receipt
        receipt = {
            "transaction_hash": tx_hash,
            "block_number": 12345678,
            "block_hash": "0x" + "0" * 64,
            "from": "0x" + "1" * 40,
            "to": "0x" + "2" * 40,
            "gas_used": 50000,
            "effective_gas_price": int(30 * 1e9),  # 30 Gwei in Wei
            "status": 1,  # 1 = success
            "logs": []
        }
        
        return json.dumps({
            "success": True,
            "network": network,
            "receipt": receipt,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _call_contract(self, args: Dict[str, Any]) -> str:
        """Call a contract method (read-only)"""
        network = args.get("network")
        contract_address = args.get("contract_address")
        function_name = args.get("function_name")
        
        if not network or network not in self.networks:
            return json.dumps({
                "success": False,
                "error": "Invalid or missing network",
                "timestamp": datetime.now().isoformat()
            })
        
        if not contract_address:
            return json.dumps({
                "success": False,
                "error": "Missing contract_address",
                "timestamp": datetime.now().isoformat()
            })
        
        if not function_name:
            return json.dumps({
                "success": False,
                "error": "Missing function_name",
                "timestamp": datetime.now().isoformat()
            })
        
        # Simulate contract call result
        result: str = None
        if function_name == "balanceOf":
            result: str = 10000000000000000000  # 10 ETH in wei
        elif function_name == "totalSupply":
            result: str = 1000000000000000000000000  # 1M tokens
        elif function_name == "symbol":
            result: str = "TKN"
        elif function_name == "decimals":
            result: str = 18
        else:
            result: str = [123, "test", True]  # Generic simulated result
        
        return json.dumps({
            "success": True,
            "network": network,
            "contract_address": contract_address,
            "function_name": function_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _health_check(self, args: Dict[str, Any]) -> str:
        """Check the health of the EVM server"""
        network_statuses = {}
        
        # Simulate checking network connections
        for name, network in self.networks.items():
            network_statuses[name] = {
                "connected": True,
                "latest_block": 12345678,
                "response_time_ms": 50 + (hash(name) % 100)  # Simulated response time
            }
        
        health_data = {
            "status": self.status,
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "name": self.name,
                "type": self.server_type,
                "version": self.version
            },
            "networks": network_statuses,
            "active_requests": len(self.active_requests),
            "request_history": len(self.request_history)
        }
        
        return json.dumps(health_data, indent=2)
    
    async def _register_with_coordinator(self, args: Dict[str, Any]) -> str:
        """Register this server with the MCP coordinator"""
        coordinator_url = args.get("coordinator_url") or self.coordinator_url
        capabilities = args.get("capabilities", self._get_default_capabilities())
        
        logger.info(f"Registering with coordinator at {coordinator_url}")
        
        try:
            server_port = os.getenv("MCP_PORT", "8003")
            server_url = f"http://localhost:{server_port}"
            
            response = requests.post(
                f"{coordinator_url}/register_server",
                json={
                    "server_name": self.name,
                    "server_type": self.server_type,
                    "server_url": server_url,
                    "capabilities": capabilities
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result: str = response.json()
                logger.info(f"Successfully registered with coordinator: {result}")
                return json.dumps({
                    "success": True,
                    "coordinator_url": coordinator_url,
                    "registration_result": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.warning(f"Failed to register with coordinator: {response.status_code} - {response.text}")
                return json.dumps({
                    "success": False,
                    "error": f"Coordinator returned status {response.status_code}",
                    "response": response.text,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error registering with coordinator: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _get_default_capabilities(self) -> List[str]:
        """Get default capabilities for this server type"""
        return [
            "blockchain_interaction",
            "transaction_management",
            "contract_calls",
            "gas_estimation",
            "multi_chain_support"
        ]
    
    async def _heartbeat_loop(self):
        """Send regular heartbeats to the coordinator"""
        while True:
            try:
                response = requests.post(
                    f"{self.coordinator_url}/server_heartbeat",
                    json={
                        "server_name": self.name,
                        "status": self.status,
                        "stats": {
                            "active_requests": len(self.active_requests),
                            "uptime_seconds": int(time.time() - self.start_time)
                        }
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.debug(f"Heartbeat sent successfully")
                else:
                    logger.warning(f"Failed to send heartbeat: {response.status_code}")
                    
                    # If we got a 404, try to re-register
                    if response.status_code == 404:
                        logger.info("Server not registered, attempting to re-register")
                        await self._register_with_coordinator({})
                
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
            
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
    
    async def run(self):
        """Run the EVM MCP server"""
        self.start_time = time.time()
        logger.info(f"Starting {self.name} v{self.version} (stdio mode)")
        
        # Register with coordinator
        await self._register_with_coordinator({})
        
        # Start the heartbeat loop
        asyncio.create_task(self._heartbeat_loop())
        
        # Start the server
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
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
            except Exception as e:
                logger.error(f"Server error: {str(e)}")
                break

def main():
    """Main entry point"""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Create and run the EVM server
    server = EVMMCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info(f"{server.name} shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()