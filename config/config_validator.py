# -*- coding: utf-8 -*-
import json

from web3 import Web3

def validate_wallet_config(config_path):
    with open(config_path) as f:
        config = json.load(f)
    
    # Validate wallet address
    if not Web3.is_address(config['wallet_address']):
        raise ValueError(f"Invalid wallet address: {config['wallet_address']}")
    
    # Validate gas settings
    if not 21000 <= config['gas_limit'] <= 8000000:
        raise ValueError(f"Gas limit {config['gas_limit']} out of range (21000-8000000)")
    
    if not 1.0 <= config['gas_price_multiplier'] <= 2.0:
        raise ValueError(f"Gas price multiplier {config['gas_price_multiplier']} out of range (1.0-2.0)")
    
    if not 1 <= config['max_gas_price_gwei'] <= 1000:
        raise ValueError(f"Max gas price {config['max_gas_price_gwei']}Gwei out of range (1-1000)")

def validate_production_config(config_path):
    with open(config_path) as f:
        config = json.load(f)
    
    # Validate contract address
    if not Web3.is_address(config['deployment']['contract_address']):
        raise ValueError(f"Invalid contract address: {config['deployment']['contract_address']}")
    
    # Validate risk parameters
    risk = config['risk_management']
    if risk['max_daily_trades'] <= 0:
        raise ValueError("max_daily_trades must be positive")
    
    if risk['max_daily_loss'] <= 0:
        raise ValueError("max_daily_loss must be positive")
    
    if risk['max_position_size'] <= 0:
        raise ValueError("max_position_size must be positive")

def validate_all():
    try:
        validate_wallet_config('wallet_config.json')
        validate_production_config('production_config.json')
        print("All configurations validated successfully")
        return True
    except Exception as e:
        print(f"Configuration validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    validate_all()