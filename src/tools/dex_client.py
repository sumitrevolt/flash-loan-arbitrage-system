# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
import asyncio
import json

import websockets
"""
WebSocket Client for DEX Management Server
Test client to verify server functionality
"""

class DEXManagementClient:
    """Client for communicating with DEX Management Server"""
    
    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port
        self.websocket = None
        self.connected = False
        
    async def connect(self):
        """Connect to the server"""
        try:
            uri = f"ws://{self.host}:{self.port}"
            print(f"🔗 Connecting to {uri}...")
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print("[OK] Connected to DEX Management Server")
            
            # Wait for welcome message
            welcome_msg = await self.websocket.recv()
            welcome_data = json.loads(welcome_msg)
            if welcome_data.get("type") == "welcome":
                print("[CELEBRATE] Welcome message received")
                print(f"Server: {welcome_data.get('server', 'Unknown')}")
                print(f"Version: {welcome_data.get('version', 'Unknown')}")
                return True
            
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            self.connected = False
            return False
    
    async def send_command(self, command, params=None):
        """Send a command to the server"""
        if not self.connected:
            print("[ERROR] Not connected to server")
            return None
            
        try:
            message = {}
                "command": command,
                "params": params or {},
                "id": f"cmd_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            
            
            await self.websocket.send(json.dumps(message, ensure_ascii=True, default=str))
            response = await self.websocket.recv()
            return json.loads(response)
            
        except Exception as e:
            print(f"[ERROR] Error sending command: {e}")
            return None
    
    async def get_dex_status(self):
        """Get DEX approval status"""
        print("\n[METRICS] Getting DEX status...")
        response = await self.send_command("get_dex_status")
        
        if response and "data" in response:
            data = response["data"]
            if "summary" in data:
                summary = data["summary"]
                print(f"Total DEXes: {summary['total']}")
                print(f"Approved DEXes: {summary['approved']}")
                print(f"Pending transactions: {summary['pending']}")
                
            if "dexes" in data:
                print("\nDEX Status Details:")
                for dex_key, dex_info in data["dexes"].items():
                    status = "[OK] APPROVED" if dex_info["approved"] else "[ERROR] NOT APPROVED"
                    print(f"  {dex_info['name']}: {status}")
                    
            return data
        else:
            print("[ERROR] Failed to get DEX status")
            return None
    
    async def approve_dex(self, dex_key):
        """Approve a specific DEX"""
        print(f"\n[INIT] Approving DEX: {dex_key}")
        response = await self.send_command("approve_dex", {"dex": dex_key, "status": True})
        
        if response and "data" in response:
            result: str = response["data"]
            if result.get("success"):
                print(f"[OK] {result.get('message', 'DEX approved successfully')}")
                if result.get("tx_hash"):
                    print(f"[LOG] Transaction: {result['tx_hash']}")
            else:
                print(f"[ERROR] {result.get('error', 'Failed to approve DEX')}")
            return result
        else:
            print("[ERROR] Failed to approve DEX")
            return None
    
    async def approve_all_unapproved_dexes(self):
        """Approve all unapproved DEXes"""
        print("\n[SETUP] Approving all unapproved DEXes...")
        response = await self.send_command("approve_all_dexes")
        
        if response and "data" in response:
            results = response["data"]
            print("Results:")
            for dex_key, result in results.items():
                if result.get("success"):
                    print(f"  [OK] {dex_key}: {result.get('message', 'Approved')}")
                else:
                    print(f"  [ERROR] {dex_key}: {result.get('error', 'Failed')}")
            return results
        else:
            print("[ERROR] Failed to approve DEXes")
            return None
    
    async def get_contract_info(self):
        """Get contract information"""
        print("\n📋 Getting contract info...")
        response = await self.send_command("get_contract_info")
        
        if response and "data" in response:
            data = response["data"]
            if "error" not in data:
                print(f"Contract Address: {data.get('address', 'N/A')}")
                print(f"Owner: {data.get('owner', 'N/A')}")
                print(f"Paused: {data.get('paused', 'N/A')}")
                print(f"Network: {data.get('network', 'N/A')}")
                print(f"User is Owner: {data.get('user_is_owner', 'N/A')}")
            else:
                print(f"[ERROR] Error: {data['error']}")
            return data
        else:
            print("[ERROR] Failed to get contract info")
            return None
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print("🔌 Disconnected from server")

async def main():
    """Main test function"""
    print("🧪 DEX Management Client Test")
    print("=" * 50)
    
    client = DEXManagementClient()
    
    try:
        # Connect to server
        if not await client.connect():
            print("[ERROR] Failed to connect to server. Make sure the server is running.")
            return
        
        # Get contract info
        await client.get_contract_info()
        
        # Get DEX status
        dex_status = await client.get_dex_status()
        
        if dex_status and "summary" in dex_status:
            summary = dex_status["summary"]
            unapproved_count = summary["total"] - summary["approved"]
            
            if unapproved_count > 0:
                print(f"\n🔔 Found {unapproved_count} unapproved DEXes")
                
                # Ask user if they want to approve
                user_input = input("\nDo you want to approve all unapproved DEXes? (y/n): ").lower().strip()
                
                if user_input == 'y':
                    await client.approve_all_unapproved_dexes()
                    
                    # Refresh status
                    print("\n[SYNC] Refreshing DEX status...")
                    await client.get_dex_status()
                else:
                    print("[ERROR] Operation cancelled by user")
            else:
                print("[OK] All DEXes are already approved!")
        
    except KeyboardInterrupt:
        print("\n[STOP] Test interrupted by user")
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
    finally:
        await client.disconnect()
        
    print("\n[TASK] Test completed")

if __name__ == "__main__":
    asyncio.run(main())