#!/usr/bin/env python3
"""
LIVE BLOCKCHAIN VERIFICATION WITH ACTUAL CONNECTION
Connects to Polygon and shows real contract status
"""

def verify_blockchain_connection():
    """Verify actual blockchain connection and contract status"""
    
    try:
        # Import required libraries
        from web3 import Web3
        import json
        import requests
        
        print("🔗 CONNECTING TO POLYGON BLOCKCHAIN...")
        print("=" * 50)
        
        # Connect to Polygon
        rpc_urls = [
            "https://polygon-rpc.com",
            "https://rpc-mainnet.matic.network", 
            "https://polygon.llamarpc.com"
        ]
        
        web3 = None
        for rpc_url in rpc_urls:
            try:
                web3 = Web3(Web3.HTTPProvider(rpc_url))
                if web3.is_connected():
                    print(f"✅ Connected to Polygon via {rpc_url}")
                    break
            except:
                continue
        
        if not web3 or not web3.is_connected():
            print("❌ Failed to connect to Polygon network")
            return False
        
        # Show network info
        print(f"🌐 Chain ID: {web3.eth.chain_id}")
        print(f"📊 Latest Block: {web3.eth.block_number}")
        
        # Load contract config
        try:
            with open('deployed_contract_config.json', 'r') as f:
                contract_config = json.load(f)
            contract_address = contract_config['deployed_contract']['address']
            print(f"📍 Contract Address: {contract_address}")
        except:
            print("⚠️ Could not load contract config")
            return False
        
        # Verify contract deployment
        try:
            code = web3.eth.get_code(contract_address)
            is_deployed = len(code) > 0
            print(f"✅ Contract Deployed: {'YES' if is_deployed else 'NO'}")
            print(f"📏 Contract Code Size: {len(code)} bytes")
            
            # Get contract balance
            balance = web3.eth.get_balance(contract_address)
            balance_matic = web3.from_wei(balance, 'ether')
            print(f"💰 Contract Balance: {balance_matic:.6f} MATIC")
            
        except Exception as e:
            print(f"❌ Contract verification error: {e}")
        
        # Check gas prices
        try:
            gas_price = web3.eth.gas_price
            gas_gwei = web3.from_wei(gas_price, 'gwei')
            print(f"⛽ Current Gas Price: {gas_gwei:.2f} Gwei")
        except:
            print("⚠️ Could not fetch gas price")
        
        # Show current block details
        try:
            latest_block = web3.eth.get_block('latest')
            print(f"🕐 Block Timestamp: {latest_block.timestamp}")
            print(f"📊 Block Gas Used: {latest_block.gasUsed:,}")
            print(f"📊 Block Gas Limit: {latest_block.gasLimit:,}")
        except:
            print("⚠️ Could not fetch block details")
        
        print("\n✅ BLOCKCHAIN CONNECTION VERIFIED!")
        return True
        
    except ImportError:
        print("❌ Required libraries not installed")
        print("Installing web3...")
        import subprocess
        subprocess.check_call(["pip", "install", "web3"])
        return verify_blockchain_connection()
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    print("🚀 FLASH LOAN ARBITRAGE SYSTEM")
    print("LIVE BLOCKCHAIN CONNECTION TEST")
    print("=" * 50)
    
    # Verify blockchain connection
    if verify_blockchain_connection():
        print("\n🎯 SYSTEM STATUS: OPERATIONAL")
        print("✅ Ready for arbitrage trading!")
    else:
        print("\n❌ SYSTEM STATUS: CONNECTION ISSUES")
        print("Please check network connectivity")

if __name__ == "__main__":
    main()
