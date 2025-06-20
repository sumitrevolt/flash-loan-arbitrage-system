#!/usr/bin/env python3
"""
Contract Deployment Verification Tool
====================================

Check if a contract is successfully deployed on Polygon network.
"""

import requests
import json
from web3 import Web3
from dotenv import load_dotenv
import os

def check_contract_deployment(contract_address: str):
    """Check if contract is deployed on Polygon"""
    
    print(f"🔍 Checking contract deployment: {contract_address}")
    print("="*60)
    
    # Load environment
    load_dotenv()
    polygon_rpc = os.getenv('POLYGON_RPC_URL')
    polygonscan_api_key = os.getenv('POLYGONSCAN_API_KEY')
    
    # Method 1: Check via Web3 RPC
    print("\n📡 Method 1: Checking via Polygon RPC...")
    try:
        w3 = Web3(Web3.HTTPProvider(polygon_rpc))
        
        if w3.is_connected():
            print("✅ Connected to Polygon network")
            
            # Get contract code
            code = w3.eth.get_code(contract_address)
            contract_balance = w3.eth.get_balance(contract_address)
            
            if code and code != b'\x00' and len(code) > 2:
                print(f"✅ Contract EXISTS at {contract_address}")
                print(f"📊 Contract code size: {len(code)} bytes")
                print(f"💰 Contract balance: {w3.from_wei(contract_balance, 'ether')} MATIC")
                
                # Try to get transaction count (indicates activity)
                tx_count = w3.eth.get_transaction_count(contract_address)
                print(f"📤 Transaction count: {tx_count}")
                
                deployment_status_rpc = True
            else:
                print(f"❌ No contract code found at {contract_address}")
                deployment_status_rpc = False
        else:
            print("❌ Failed to connect to Polygon network")
            deployment_status_rpc = False
            
    except Exception as e:
        print(f"❌ RPC Error: {e}")
        deployment_status_rpc = False
    
    # Method 2: Check via Polygonscan API
    print("\n🌐 Method 2: Checking via Polygonscan API...")
    try:
        # Get contract source code
        source_response = requests.get(
            'https://api.polygonscan.com/api',
            params={
                'module': 'contract',
                'action': 'getsourcecode',
                'address': contract_address,
                'apikey': polygonscan_api_key
            },
            timeout=10
        )
        
        if source_response.status_code == 200:
            source_data = source_response.json()
            
            if source_data.get('status') == '1' and source_data.get('result'):
                result = source_data['result'][0]
                
                if result.get('ABI') != 'Contract source code not verified':
                    print("✅ Contract found on Polygonscan")
                    print(f"📝 Contract Name: {result.get('ContractName', 'Unknown')}")
                    print(f"🔧 Compiler Version: {result.get('CompilerVersion', 'Unknown')}")
                    print(f"📋 Verification Status: {'Verified' if result.get('ABI') else 'Not Verified'}")
                    
                    deployment_status_polygonscan = True
                else:
                    print("⚠️  Contract exists but not verified on Polygonscan")
                    deployment_status_polygonscan = True
            else:
                print("❌ Contract not found on Polygonscan")
                deployment_status_polygonscan = False
        else:
            print(f"❌ Polygonscan API error: HTTP {source_response.status_code}")
            deployment_status_polygonscan = False
            
    except Exception as e:
        print(f"❌ Polygonscan API Error: {e}")
        deployment_status_polygonscan = False
    
    # Method 3: Check transaction history
    print("\n📊 Method 3: Checking transaction history...")
    try:
        tx_response = requests.get(
            'https://api.polygonscan.com/api',
            params={
                'module': 'account',
                'action': 'txlist',
                'address': contract_address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': 10,
                'sort': 'asc',
                'apikey': polygonscan_api_key
            },
            timeout=10
        )
        
        if tx_response.status_code == 200:
            tx_data = tx_response.json()
            
            if tx_data.get('status') == '1' and tx_data.get('result'):
                transactions = tx_data['result']
                
                # Find contract creation transaction
                creation_tx = None
                for tx in transactions:
                    if tx.get('to') == '' and tx.get('contractAddress', '').lower() == contract_address.lower():
                        creation_tx = tx
                        break
                
                if creation_tx:
                    print("✅ Contract creation transaction found!")
                    print(f"🔗 Creation TX Hash: {creation_tx['hash']}")
                    print(f"📅 Creation Time: Block {creation_tx['blockNumber']}")
                    print(f"👤 Creator Address: {creation_tx['from']}")
                    print(f"⛽ Gas Used: {int(creation_tx['gasUsed']):,}")
                else:
                    print("⚠️  No contract creation transaction found")
                
                print(f"📈 Total transactions: {len(transactions)}")
            else:
                print("📭 No transactions found for this address")
                
    except Exception as e:
        print(f"❌ Transaction history error: {e}")
    
    # Final summary
    print("\n" + "="*60)
    print("📋 DEPLOYMENT VERIFICATION SUMMARY")
    print("="*60)
    
    if deployment_status_rpc and deployment_status_polygonscan:
        print("✅ CONTRACT SUCCESSFULLY DEPLOYED")
        print("   ✅ Confirmed via RPC")
        print("   ✅ Confirmed via Polygonscan")
        print(f"   🌐 View on Polygonscan: https://polygonscan.com/address/{contract_address}")
        
        return True
    elif deployment_status_rpc:
        print("⚠️  CONTRACT PARTIALLY DEPLOYED")
        print("   ✅ Confirmed via RPC")
        print("   ❌ Not indexed on Polygonscan yet")
        print("   ⏳ May need more time for indexing")
        
        return True
    else:
        print("❌ CONTRACT NOT DEPLOYED")
        print("   ❌ No contract code found")
        print("   ❌ Not found on Polygonscan")
        
        return False

if __name__ == "__main__":
    contract_address = "0x7dB59723064aaD15b90042b9205F60A6A7029ABF"
    check_contract_deployment(contract_address)
