#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration File for Flash Loan Arbitrage Bot
This file centralizes all configuration settings required for the arbitrage system,
including WebSocket endpoints for DEX data feeds, MCP server endpoints, blockchain
network settings, flash loan provider details, and wallet configurations.
"""

from typing import Dict, Any
import os

# General System Settings
SYSTEM_SETTINGS = {
    "CHECK_INTERVAL": 10,  # Interval in seconds between arbitrage checks
    "PROFIT_THRESHOLD": 0.015,  # Profit margin threshold for arbitrage execution (1.5% as default)
    "LOG_LEVEL": "INFO",  # Default logging level (DEBUG, INFO, WARNING, ERROR)
    "MAX_TRADE_AMOUNT": 10000.0,  # Maximum trade amount in base token for safety (placeholder, adjust based on risk tolerance)
    "SLIPPAGE_TOLERANCE": 0.005,  # Slippage tolerance as a percentage (0.5% as default)


# WebSocket Endpoints for DEX Data Feeds
# IMPORTANT: Replace placeholder URLs with actual WebSocket endpoints.
# Note: Uniswap and Sushiswap may not provide public WebSocket APIs for price feeds.
# Consider using alternative data providers like The Graph, Alchemy, or Infura WebSocket APIs.
DEX_WEBSOCKET_URLS = {
    "uniswap": "wss://your-uniswap-data-provider.com/websocket",  # Configure with actual data provider WebSocket URL for Uniswap data
    "sushiswap": "wss://your-sushiswap-data-provider.com/websocket"  # Configure with actual data provider WebSocket URL for Sushiswap data
    # Add more DEXs as needed, e.g., "pancakeswap": "wss://your-pancakeswap-data-provider.com/websocket"


# Subscription Payloads for WebSocket Connections
# Adjust these payloads based on the actual API requirements of your data provider.
SUBSCRIPTION_PAYLOADS = {
    "uniswap": {
        "type": "subscribe",
        "channel": "price_feed",
        "pairs": ["ETH/USDT", "WBTC/USDT"]  # Example trading pairs, update based on target pairs for arbitrage
    },
    "sushiswap": {
        "type": "subscribe",
        "channel": "price_feed",
        "pairs": ["ETH/USDT", "WBTC/USDT"]  # Example trading pairs, update based on target pairs for arbitrage

    # Add more DEX subscription payloads as needed


# MCP Server Endpoints
# IMPORTANT: Update with actual server endpoints where MCP servers are hosted.
# Ensure the servers are running and accessible before initializing the system.
MCP_SERVERS = {
    "matic": {
        "endpoint": "http://your-matic-mcp-server:port/matic",  # For Polygon network interactions, configure with actual server address
        "enabled": True,
        "description": "Optimizes Polygon network interactions and flash loan execution"
    },
    "foundry": {
        "endpoint": "http://your-foundry-mcp-server:port/foundry",  # For smart contract testing and deployment, configure with actual server address
        "enabled": True,
        "description": "Streamlines smart contract testing and deployment"
    },
    "evm": {
        "endpoint": "http://your-evm-mcp-server:port/evm",  # For Ethereum-compatible chain operations, configure with actual server address
        "enabled": True,
        "description": "Facilitates integration across Ethereum-compatible chains"
    },
    "copilot": {
        "endpoint": "http://your-copilot-mcp-server:port/copilot",  # For error detection and resolution, configure with actual server address
        "enabled": True,
        "description": "Automates error detection, analysis, and resolution"



# Blockchain Network Settings
# IMPORTANT: Configure with actual network details for the blockchain(s) you are operating on.
BLOCKCHAIN_NETWORKS = {
    "polygon": {
        "rpc_url": "https://your-polygon-rpc-url.com",  # Replace with actual Polygon RPC URL (e.g., from Alchemy, Infura, or QuickNode)
        "chain_id": 137,  # Polygon Mainnet chain ID (confirm for testnets if needed)
        "enabled": True
    },
    "ethereum": {
        "rpc_url": "https://your-ethereum-rpc-url.com",  # Replace with actual Ethereum RPC URL
        "chain_id": 1,  # Ethereum Mainnet chain ID (confirm for testnets if needed)
        "enabled": False  # Disabled by default; enable if targeting Ethereum mainnet

    # Add more networks as needed, e.g., Binance Smart Chain, Arbitrum, etc.


# Flash Loan Provider Settings
# IMPORTANT: Configure with actual smart contract addresses and details for flash loan providers.
FLASH_LOAN_PROVIDERS = {
    "aave": {
        "contract_address": "0xYourAaveLendingPoolAddress",  # Replace with actual Aave Lending Pool contract address on target network
        "network": "polygon",  # Target network for Aave flash loans (update based on deployment)
        "enabled": True,
        "fee_percentage": 0.0009  # Aave flash loan fee (0.09% as of common rates, confirm current rate)
    },
    "dydx": {
        "contract_address": "0xYourDYdXSoloMarginAddress",  # Replace with actual dYdX Solo Margin contract address on target network
        "network": "ethereum",  # Target network for dYdX flash loans (update based on deployment)
        "enabled": False,  # Disabled by default; enable if targeting dYdX
        "fee_percentage": 0.0005  # dYdX flash loan fee (example rate, confirm current rate)

    # Add more flash loan providers as needed


# DEX Smart Contract Addresses or API Details
# IMPORTANT: Configure with actual contract addresses for DEX interactions or API keys for off-chain interactions.
DEX_SETTINGS = {
    "uniswap": {
        "router_address": "0xYourUniswapRouterAddress",  # Replace with actual Uniswap Router contract address on target network
        "factory_address": "0xYourUniswapFactoryAddress",  # Replace with actual Uniswap Factory contract address for pool data
        "network": "polygon",  # Target network for Uniswap (update based on deployment, e.g., Ethereum for mainnet)
        "api_key": "your-uniswap-api-key-if-applicable",  # Replace if using a third-party API for Uniswap data
        "enabled": True
    },
    "sushiswap": {
        "router_address": "0xYourSushiswapRouterAddress",  # Replace with actual Sushiswap Router contract address on target network
        "factory_address": "0xYourSushiswapFactoryAddress",  # Replace with actual Sushiswap Factory contract address for pool data
        "network": "polygon",  # Target network for Sushiswap (update based on deployment)
        "api_key": "your-sushiswap-api-key-if-applicable",  # Replace if using a third-party API for Sushiswap data
        "enabled": True

    # Add more DEX settings as needed


# Wallet and Private Key Settings
# IMPORTANT: Securely configure wallet details for transaction signing.
# DO NOT hardcode private keys in this file for production use.
# Use environment variables or a secure key management system.
WALLET_SETTINGS = {
    "private_key": os.getenv("ARBITRAGE_WALLET_PRIVATE_KEY", "your-private-key-here-securely"),  # Replace with actual private key via environment variable or secure storage
    "address": "0xYourWalletAddress",  # Replace with actual wallet address associated with the private key
    "gas_limit_default": 200000,  # Default gas limit for transactions (adjust based on network conditions)
    "gas_price_multiplier": 1.2  # Multiplier for gas price to ensure transaction inclusion (adjust based on network congestion)


# Token Pairs for Arbitrage
# Configure the token pairs to monitor for arbitrage opportunities.
# Ensure these pairs are supported by the configured DEXs and data feeds.
TARGET_TOKEN_PAIRS = [
    "ETH/USDT",
    "WBTC/USDT",
    # Add more pairs as needed, e.g., "DAI/USDC", "MATIC/USDT"


# Safety and Risk Management Settings
RISK_MANAGEMENT = {
    "max_loss_percentage": 0.01,  # Maximum acceptable loss percentage per trade to abort (1% as default)
    "enable_risk_assessment": True,  # Enable risk assessment checks via Copilot MCP if available
    "min_liquidity_threshold": 5000.0,  # Minimum liquidity in base token on a DEX pool to consider for trade (placeholder, adjust based on risk)
    "enable_gas_optimization": True  # Enable gas optimization queries via Matic or EVM MCP if available


# Environment Variable Overrides
# Override any settings with environment variables if set (for security and flexibility).
# Example: SYSTEM_SETTINGS["CHECK_INTERVAL"] = int(os.getenv("CHECK_INTERVAL", SYSTEM_SETTINGS["CHECK_INTERVAL"]))

def get_config() -> Dict[str, Any]:
    """Return the complete configuration dictionary for use in the arbitrage system."""
    return {
        "system": SYSTEM_SETTINGS,
        "dex_websocket_urls": DEX_WEBSOCKET_URLS,
        "subscription_payloads": SUBSCRIPTION_PAYLOADS,
        "mcp_servers": MCP_SERVERS,
        "blockchain_networks": BLOCKCHAIN_NETWORKS,
        "flash_loan_providers": FLASH_LOAN_PROVIDERS,
        "dex_settings": DEX_SETTINGS,
        "wallet": WALLET_SETTINGS,
        "target_token_pairs": TARGET_TOKEN_PAIRS,
        "risk_management": RISK_MANAGEMENT


if __name__ == "__main__":
    print("Configuration file for Flash Loan Arbitrage Bot.")
    print("This file contains placeholder settings. Update with actual values for operational use.")
    print("Critical configurations needed:")
    print("- WebSocket URLs for DEX data feeds")
    print("- MCP server endpoints")
    print("- Blockchain RPC URLs")
    print("- Flash loan provider contract addresses")
    print("- DEX contract addresses or API keys")
    print("- Wallet private key (securely via environment variables)")
    print("Refer to comments in the file for detailed guidance.")
