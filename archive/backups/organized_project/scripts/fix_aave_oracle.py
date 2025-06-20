#!/usr/bin/env python3
"""
AAVE Price Oracle Fix
====================

Fixes the AAVE price oracle address issue.
"""

import json
from pathlib import Path

def fix_aave_oracle():
    """Fix AAVE price oracle address"""
    
    # Load current config
    config_path = Path("config/aave_config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Updated AAVE V3 Polygon price oracle (correct address)
    correct_oracle = "0xb023e699F5a33916Ea823A16485eb259579C9f86"  # AAVE V3 Price Oracle
    
    # Alternative oracle addresses to try
    alternative_oracles = [
        "0xb023e699F5a33916Ea823A16485eb259579C9f86",  # Current
        "0x0229F777B0fAb107F9591a41d5F02E4e98dB6f2d",  # Alternative 1
        "0xd05e3E715d945B59290df0ae8eF85c1BdB684744"   # Alternative 2  
    ]
    
    print("🔧 FIXING AAVE PRICE ORACLE")
    print("=" * 40)
    print(f"Current oracle: {correct_oracle}")
    
    # Update the configuration with the working oracle
    config["aave_flash_loan_config"]["aave_v3_polygon"]["price_oracle"] = correct_oracle
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ AAVE price oracle address updated")
    
    # For flash loans, we can actually work without the price oracle
    # since we're doing arbitrage and getting prices from DEXs directly
    print("\n💡 NOTE: For arbitrage, DEX prices are primary")
    print("   AAVE oracle is secondary for risk management")

if __name__ == "__main__":
    fix_aave_oracle()
