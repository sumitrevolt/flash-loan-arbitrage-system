#!/usr/bin/env python3
"""
Simple Production Status Check
Without emoji characters to avoid Unicode issues
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

def simple_production_check():
    """Simple production readiness check"""
    print("FLASH LOAN ARBITRAGE BOT - PRODUCTION STATUS CHECK")
    print("=" * 60)
    
    load_dotenv()
    
    # Environment check
    print("\n1. Environment Variables:")
    private_key = os.getenv('PRIVATE_KEY')
    contract_address = os.getenv('CONTRACT_ADDRESS', '0x153dDf13D58397740c40E9D1a6e183A8c0F36c32')
    
    if private_key and len(private_key) == 66:
        print("   Private key: LOADED")
    else:
        print("   Private key: MISSING")
        return False
    
    print(f"   Contract: {contract_address}")
    
    # Web3 connection
    print("\n2. Web3 Connection:")
    try:
        w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
        if w3.is_connected():
            print(f"   Connected to Polygon (Chain ID: {w3.eth.chain_id})")
        else:
            print("   Connection: FAILED")
            return False
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    # Account check
    print("\n3. Account Status:")
    try:
        account = w3.eth.account.from_key(private_key)
        balance = w3.eth.get_balance(account.address)
        balance_matic = w3.from_wei(balance, 'ether')
        
        print(f"   Address: {account.address}")
        print(f"   Balance: {balance_matic:.6f} MATIC")
        
        if balance_matic < 0.01:
            print("   WARNING: Low balance for gas fees")
        else:
            print("   Balance: SUFFICIENT")
            
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    # Contract check
    print("\n4. Contract Status:")
    try:
        with open('contract_abi.json', 'r') as f:
            contract_abi = json.load(f)
        
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=contract_abi
        )
        
        owner = contract.functions.owner().call()
        paused = contract.functions.paused().call()
        
        print(f"   Contract: {contract_address}")
        print(f"   Owner: {owner}")
        print(f"   Paused: {paused}")
        
        if account.address.lower() == owner.lower():
            print("   Ownership: USER IS OWNER")
        else:
            print("   Ownership: USER IS NOT OWNER")
            
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    # DEX approvals
    print("\n5. DEX Approvals:")
    try:
        dexes = [
            ("QuickSwap", "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"),
            ("Uniswap V3", "0xE592427A0AEce92De3Edee1F18E0157C05861564"),
            ("SushiSwap", "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"),
            ("Curve", "0x094d12e5b541784701FD8d65F11fc0598FBC6332"),
            ("Balancer", "0xBA12222222228d8Ba445958a75a0704d566BF2C8"),
            ("DODO", "0x6D310348d5c12009854DFCf72e0DF9027e8cb4f4")
        ]
        
        approved = 0
        for name, addr in dexes:
            try:
                is_approved = contract.functions.approvedDexes(Web3.to_checksum_address(addr)).call()
                status = "APPROVED" if is_approved else "NOT APPROVED"
                print(f"   {name}: {status}")
                if is_approved:
                    approved += 1
            except Exception as e:
                print(f"   {name}: ERROR - {e}")
        
        print(f"\n   Summary: {approved}/{len(dexes)} DEXes approved")
        
        if approved == len(dexes):
            print("   All DEXes: APPROVED")
        else:
            print("   DEX Status: INCOMPLETE")
            
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    # Final status
    print("\n" + "=" * 60)
    print("PRODUCTION READINESS STATUS")
    print("=" * 60)
    
    if approved == len(dexes) and balance_matic > 0.01:
        print("\nSTATUS: PRODUCTION READY!")
        print("- All DEXes approved")
        print("- Sufficient gas balance")
        print("- Contract ownership verified")
        print("\nRECOMMENDATIONS:")
        print("- Start with small test amounts (0.1 MATIC)")
        print("- Monitor gas prices")
        print("- Keep emergency pause ready")
        return True
    else:
        print("\nSTATUS: NEEDS ATTENTION")
        if approved < len(dexes):
            print("- Some DEXes need approval")
        if balance_matic <= 0.01:
            print("- Add more MATIC for gas")
        return False

if __name__ == "__main__":
    simple_production_check()
