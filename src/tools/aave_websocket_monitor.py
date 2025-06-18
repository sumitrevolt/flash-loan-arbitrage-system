#!/usr/bin/env python3
"""
Aave Flash Loan WebSocket Monitor
Real-time monitoring with WebSocket for live updates and alerts
"""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Dict, Set, Any
import websockets
from web3 import Web3
from web3.providers.websocket.websocket import WebsocketProvider
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

# Set high precision
getcontext().prec = 50

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Event signatures for monitoring
FLASH_LOAN_EVENT_SIGNATURE = Web3.keccak(text="FlashLoan(address,address,address,uint256,uint8,uint256,uint16)").hex()
SWAP_EVENT_SIGNATURES = {
    'UniswapV2': Web3.keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex(),
    'UniswapV3': Web3.keccak(text="Swap(address,address,int256,int256,uint160,uint128,int24)").hex(),
    'SushiSwap': Web3.keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex(),
}

class AaveWebSocketMonitor:
    """WebSocket-based real-time monitor for Aave flash loans"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # WebSocket connection
        ws_url = os.getenv('POLYGON_WS_URL', self.config.get('polygon_ws_url'))
        self.web3_ws = Web3(WebsocketProvider(ws_url))
        
        # Addresses to monitor
        self.aave_pool_address = Web3.to_checksum_address(self.config['aave']['pool_address'])
        self.monitored_tokens = {
            Web3.to_checksum_address(addr): symbol 
            for addr, symbol in self.config.get('monitored_tokens', {}).items()
        }
        
        # Active subscriptions
        self.subscriptions: Set[str] = set()
        self.event_handlers: Dict[str, Any] = {}
        
        # Alert thresholds
        self.alert_thresholds: Dict[str, Any] = {
            'min_profit': Decimal('100'),  # Alert on profits > $100
            'high_gas': 150,  # Alert on gas > 150 gwei
            'large_loan': Decimal('100000'),  # Alert on loans > $100k
        }
        
    async def subscribe_to_flash_loans(self) -> None:
        """Subscribe to Aave flash loan events"""
        try:
            # Create filter for flash loan events
            flash_loan_filter = {
                'address': self.aave_pool_address,
                'topics': [FLASH_LOAN_EVENT_SIGNATURE]
            }
            
            # TODO: web3.py does not support eth.subscribe. Use polling or another library for real-time events.
            logger.info("Subscribed to Aave flash loan events (placeholder, polling not implemented)")
            return None
            
        except Exception as e:
            logger.error(f"Failed to subscribe to flash loans: {e}")
            return None
    
    async def subscribe_to_dex_swaps(self, dex_addresses: Dict[str, str]) -> Dict[str, Any]:
        """Subscribe to DEX swap events"""
        subscriptions: Dict[str, Any] = {}
        
        for dex_name, address in dex_addresses.items():
            try:
                checksum_address = Web3.to_checksum_address(address)
                
                # Get appropriate event signature
                event_signature = SWAP_EVENT_SIGNATURES.get(dex_name)
                if not event_signature:
                    continue
                
                # Create filter
                swap_filter = {
                    'address': checksum_address,
                    'topics': [event_signature]
                }
                
                # TODO: web3.py does not support eth.subscribe. Use polling or another library for real-time events.
                logger.info(f"Subscribed to {dex_name} swap events (placeholder, polling not implemented)")
                
            except Exception as e:
                logger.error(f"Failed to subscribe to {dex_name}: {e}")
        
        return subscriptions
    
    async def handle_flash_loan_event(self, event: Dict[str, Any]) -> Dict[str, Any] | None:
        """Process flash loan event"""
        try:
            # Decode event data
            tx_hash = event['transactionHash'].hex()
            block_number = event['blockNumber']
            
            # Get transaction details (web3.py methods are synchronous)
            tx = self.web3_ws.eth.get_transaction(tx_hash)
            tx_receipt = self.web3_ws.eth.get_transaction_receipt(tx_hash)
            
            # Calculate metrics
            gas_used = tx_receipt['gasUsed']
            gas_price = tx['gasPrice']
            gas_cost_wei = gas_used * gas_price
            gas_cost_usd = Decimal(gas_cost_wei) / Decimal('1e18') * Decimal('2000')  # Assume ETH = $2000
            
            # Extract loan details from logs
            # This is simplified - in production you'd decode the actual event data
            loan_data = {
                'tx_hash': tx_hash,
                'block': block_number,
                'from': tx['from'],
                'gas_cost': gas_cost_usd,
                'success': tx_receipt['status'] == 1,
                'timestamp': datetime.now()
            }
            
            # Check for alerts
            if gas_cost_usd > self.alert_thresholds['high_gas']:
                await self.send_alert('HIGH_GAS', loan_data)
            
            # Log the event
            logger.info(f"Flash loan detected: {tx_hash} - Gas: ${gas_cost_usd:.2f}")
            
            return loan_data
            
        except Exception as e:
            logger.error(f"Error handling flash loan event: {e}")
            return None
    
    async def handle_swap_event(self, event: Dict[str, Any], dex_name: str) -> Dict[str, Any] | None:
        """Process DEX swap event"""
        try:
            # Check if this swap involves monitored tokens
            # This is simplified - in production you'd decode the actual event
            
            swap_data = {
                'dex': dex_name,
                'tx_hash': event['transactionHash'].hex(),
                'block': event['blockNumber'],
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Swap detected on {dex_name}: {swap_data['tx_hash']}")
            
            return swap_data
            
        except Exception as e:
            logger.error(f"Error handling swap event: {e}")
            return None
    
    async def monitor_gas_prices(self) -> None:
        """Monitor gas prices in real-time"""
        while True:
            try:
                gas_price = self.web3_ws.eth.gas_price
                gas_price_gwei = Decimal(gas_price) / Decimal('1e9')
                
                if gas_price_gwei > self.alert_thresholds['high_gas']:
                    await self.send_alert('HIGH_GAS_PRICE', {'gas_price': gas_price_gwei})
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring gas: {e}")
                await asyncio.sleep(30)
    
    async def send_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Send alert notification"""
        alert = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        logger.warning(f"🚨 ALERT: {alert_type} - {json.dumps(data, default=str)}")
        
        # In production, this would send to Discord, Telegram, etc.
        # For now, just log it prominently
        print(f"\n{'='*60}")
        print(f"🚨 ALERT: {alert_type}")
        print(f"Time: {alert['timestamp']}")
        print(f"Data: {json.dumps(data, indent=2, default=str)}")
        print(f"{'='*60}\n")
    
    async def start_monitoring(self) -> None:
        """Start all monitoring tasks"""
        logger.info("Starting WebSocket monitoring...")
        
        # Subscribe to events
        await self.subscribe_to_flash_loans()
        
        # Subscribe to DEX events
        dex_addresses = {
            'UniswapV3': self.config['dexes']['uniswapv3']['router'],
            'SushiSwap': self.config['dexes']['sushiswap']['router'],
        }
        await self.subscribe_to_dex_swaps(dex_addresses)
        
        # Start gas monitoring
        gas_task = asyncio.create_task(self.monitor_gas_prices())
        
        # Listen for events
        # TODO: web3.py does not support eth.subscribe. You must implement polling for logs or use another library for real-time event streaming.
        logger.info("Event listening not implemented: web3.py does not support eth.subscribe. Use polling or another library.")
        await asyncio.sleep(3600)  # Placeholder to keep the task alive
        gas_task.cancel()
    
    async def process_event(self, message: Dict[str, Any]) -> None:
        """Process incoming WebSocket event"""
        try:
            subscription_id = message['subscription']
            event_data = message['result']
            
            # Determine event type and handle accordingly
            if event_data['address'].lower() == self.aave_pool_address.lower():
                await self.handle_flash_loan_event(event_data)
            else:
                # It's a DEX swap event
                await self.handle_swap_event(event_data, 'Unknown')
                
        except Exception as e:
            logger.error(f"Error processing event: {e}")

class AaveMonitorWebSocketServer:
    """WebSocket server for broadcasting monitor updates to clients"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.monitor_data: Dict[str, Any] = {
            'flash_loans': [],
            'opportunities': [],
            'alerts': [],
            'metrics': {}
        }
    
    async def register_client(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Register a new client"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        # Send current state
        await websocket.send(json.dumps({
            'type': 'initial_state',
            'data': self.monitor_data
        }))
    
    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Unregister a client"""
        self.clients.remove(websocket)
        logger.info(f"Client disconnected: {websocket.remote_address}")
    
    async def broadcast_update(self, update_type: str, data: Dict[str, Any]) -> None:
        """Broadcast update to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': update_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }, default=str)
        
        # Send to all clients
        disconnected: Set[websockets.WebSocketServerProtocol] = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            await self.unregister_client(client)
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        """Handle client connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                # Handle client messages (if any)
                data = json.loads(message)
                
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self) -> None:
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever

async def main():
    """Main function to run both monitor and server"""
    # Load configuration
    config_path = 'production_config.json'
    
    # Create monitor
    monitor = AaveWebSocketMonitor(config_path)
    
    # Create WebSocket server
    ws_server = AaveMonitorWebSocketServer()
    
    # Run both concurrently
    await asyncio.gather(
        monitor.start_monitoring(),
        ws_server.start_server()
    )

if __name__ == "__main__":
    print("🚀 Starting Aave Flash Loan WebSocket Monitor...")
    print("📡 WebSocket server will be available at ws://localhost:8765")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped by user")