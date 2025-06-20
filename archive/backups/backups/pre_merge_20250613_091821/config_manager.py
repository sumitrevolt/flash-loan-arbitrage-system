#!/usr/bin/env python3
"""
Unified Configuration Manager for Flash Loan Arbitrage System
Handles all configuration updates and management
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Unified configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/unified_production_config.json"
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            print(f"Config file not found, creating default: {config_file}")
            config = self.get_default_config()
            self.save_config(config)
            return config
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "networks": {
                "polygon": {
                    "rpc_url": os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
                    "chain_id": 137,
                    "explorer_url": "https://polygonscan.com"
                }
            },
            "contracts": {
                "flash_loan_arbitrage": "0x153dDf13D58397740c40E9D1a6e183A8c0F36c32",
                "aave_lending_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
                "quickswap_router": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
                "sushiswap_router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
            },
            "tokens": {
                "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
            },
            "trading": {
                "monitoring_interval": 2.0,
                "display_calculations": True,
                "min_profit_threshold": 0.005,
                "max_slippage": 0.02,
                "max_gas_price_gwei": 150
            },
            "mcp_servers": {
                "foundry": {"port": 8001, "enabled": True},
                "copilot": {"port": 8002, "enabled": True},
                "arbitrage": {"port": 8003, "enabled": True},
                "flash_loan": {"port": 8004, "enabled": True}
            }
        }
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated {config_file}")
    
    def update_contract_addresses(self, addresses: Dict[str, str]):
        """Update contract addresses"""
        if 'contracts' not in self.config:
            self.config['contracts'] = {}
        
        # Use dictionary merging to avoid type issues
        self.config['contracts'] = {**self.config['contracts'], **addresses}
        self.save_config()
    
    def update_trading_settings(self, settings: Dict[str, Any]):
        """Update trading settings"""
        if 'trading' not in self.config:
            self.config['trading'] = {}
        
        # Use dictionary merging to avoid type issues
        self.config['trading'] = {**self.config['trading'], **settings}
        self.save_config()
    
    def update_mcp_server_config(self, server: str, config: Dict[str, Any]):
        """Update MCP server configuration"""
        if 'mcp_servers' not in self.config:
            self.config['mcp_servers'] = {}
        
        if server not in self.config['mcp_servers']:
            self.config['mcp_servers'][server] = {}
        
        # Use dictionary merging to avoid type issues
        self.config['mcp_servers'][server] = {**self.config['mcp_servers'][server], **config}
        self.save_config()
    
    def get_network_config(self, network: str) -> Dict[str, Any]:
        """Get network configuration"""
        return self.config.get('networks', {}).get(network, {})
    
    def get_contract_address(self, contract: str) -> str:
        """Get contract address"""
        return self.config.get('contracts', {}).get(contract, '')
    
    def get_token_address(self, token: str) -> str:
        """Get token address"""
        return self.config.get('tokens', {}).get(token, '')
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration"""
        return self.config.get('trading', {})
    
    def get_mcp_server_config(self, server: str) -> Dict[str, Any]:
        """Get MCP server configuration"""
        return self.config.get('mcp_servers', {}).get(server, {})

def main():
    """Update configuration for real contract interaction"""
    manager = ConfigManager()
    
    # Update for production
    manager.update_trading_settings({
        "monitoring_interval": 2.0,
        "display_calculations": True,
        "min_profit_threshold": 0.005,
        "max_slippage": 0.02
    })
    
    print("✅ Configuration updated for production")

if __name__ == "__main__":
    main()
