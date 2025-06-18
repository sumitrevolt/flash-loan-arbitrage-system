#!/usr/bin/env python3
"""
Agent Enhancement Template
=========================

This template can be used to enhance your existing AI agents with interaction capabilities.
Copy the relevant parts to your existing agent files to add interaction features.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)

class AgentInteractionMixin:
    """Mixin class to add interaction capabilities to existing agents"""
    
    def __init__(self, agent_name: str, capabilities: List[str]):
        self.agent_name = agent_name
        self.capabilities = capabilities
        self.interaction_enabled = False
        self.orchestrator_url = "http://localhost:8888"  # Default orchestrator URL
        
        # Agent metrics
        self.agent_metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'events_received': 0,
            'uptime_start': datetime.now(),
            'last_activity': None
        }
    
    def add_interaction_routes(self, app: Flask):
        """Add interaction routes to existing Flask app"""
        
        @app.route('/process_task', methods=['POST'])
        def process_task():
            """Process a task from the interaction system"""
            try:
                task_data = request.get_json()
                if not task_data:
                    return jsonify({'error': 'No task data provided'}), 400
                
                # Process task asynchronously
                asyncio.create_task(self._handle_interaction_task(task_data))
                
                return jsonify({
                    'status': 'accepted',
                    'task_id': task_data.get('task_id'),
                    'agent': self.agent_name
                })
                
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/receive_event', methods=['POST'])
        def receive_event():
            """Receive an event from the event bus"""
            try:
                event_data = request.get_json()
                if not event_data:
                    return jsonify({'error': 'No event data provided'}), 400
                
                # Handle event asynchronously
                asyncio.create_task(self._handle_interaction_event(event_data))
                
                self.agent_metrics['events_received'] += 1
                
                return jsonify({
                    'status': 'received',
                    'event_id': event_data.get('id'),
                    'agent': self.agent_name
                })
                
            except Exception as e:
                logger.error(f"Error receiving event: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/agent_status')
        def agent_status():
            """Get detailed agent status including interaction capabilities"""
            uptime = (datetime.now() - self.agent_metrics['uptime_start']).total_seconds()
            
            return jsonify({
                'agent': self.agent_name,
                'status': 'active',
                'interaction_enabled': self.interaction_enabled,
                'capabilities': self.capabilities,
                'metrics': {
                    **self.agent_metrics,
                    'uptime_seconds': uptime
                },
                'timestamp': datetime.now().isoformat()
            })
    
    async def _handle_interaction_task(self, task_data: Dict):
        """Handle a task from the interaction system"""
        try:
            task_id = task_data.get('task_id')
            task_type = task_data.get('task_type')
            data = task_data.get('data', {})
            
            logger.info(f"Processing task {task_id}: {task_type}")
            
            # Route task based on type and capabilities
            result = await self._process_task_by_type(task_type, data)
            
            # Send result back to orchestrator
            await self._send_task_result(task_id, result)
            
            self.agent_metrics['tasks_completed'] += 1
            self.agent_metrics['last_activity'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error handling task {task_data.get('task_id', 'unknown')}: {e}")
            self.agent_metrics['tasks_failed'] += 1
            
            # Send error result
            await self._send_task_result(task_data.get('task_id'), {
                'status': 'error',
                'error': str(e)
            })
    
    async def _handle_interaction_event(self, event_data: Dict):
        """Handle an event from the event bus"""
        try:
            event_type = event_data.get('type')
            data = event_data.get('data', {})
            
            logger.info(f"Received event: {event_type}")
            
            # Route event based on type
            await self._process_event_by_type(event_type, data)
            
            self.agent_metrics['last_activity'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error handling event {event_data.get('type', 'unknown')}: {e}")
    
    async def _process_task_by_type(self, task_type: str, data: Dict) -> Dict:
        """Process task based on type - override in specific agents"""
        # Default implementation - override in specific agents
        
        if task_type == 'health_check':
            return {
                'status': 'healthy',
                'agent': self.agent_name,
                'capabilities': self.capabilities,
                'timestamp': datetime.now().isoformat()
            }
        
        # Add more generic task handlers here
        return {
            'status': 'completed',
            'message': f'Task {task_type} processed by {self.agent_name}',
            'data': data
        }
    
    async def _process_event_by_type(self, event_type: str, data: Dict):
        """Process event based on type - override in specific agents"""
        # Default implementation - override in specific agents
        logger.info(f"Agent {self.agent_name} received event {event_type}")
    
    async def _send_task_result(self, task_id: str, result: Dict):
        """Send task result back to orchestrator"""
        try:
            result_payload = {
                'task_id': task_id,
                'agent': self.agent_name,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.orchestrator_url}/task_result", 
                                      json=result_payload, 
                                      timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to send task result: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending task result: {e}")

# Example: Enhanced Liquidity Monitor Agent
class EnhancedLiquidityMonitor(AgentInteractionMixin):
    """Enhanced version of liquidity monitor with interaction capabilities"""
    
    def __init__(self):
        super().__init__(
            agent_name='liquidity_monitor',
            capabilities=[
                'liquidity_tracking',
                'pool_analysis', 
                'dex_monitoring',
                'liquidity_alerts',
                'volume_analysis',
                'price_impact_calculation'
            ]
        )
        
        self.app = Flask(__name__)
        self.liquidity_data = {}
        self.monitoring_active = False
        
        # Add interaction routes
        self.add_interaction_routes(self.app)
        
        # Add existing routes
        self._setup_existing_routes()
    
    def _setup_existing_routes(self):
        """Setup existing agent routes"""
        
        @self.app.route('/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'agent': self.agent_name,
                'interaction_enabled': self.interaction_enabled,
                'monitoring_active': self.monitoring_active,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/start_monitoring', methods=['POST'])
        def start_monitoring():
            self.monitoring_active = True
            return jsonify({'status': 'monitoring_started'})
        
        @self.app.route('/stop_monitoring', methods=['POST'])
        def stop_monitoring():
            self.monitoring_active = False
            return jsonify({'status': 'monitoring_stopped'})
        
        @self.app.route('/liquidity_data')
        def get_liquidity_data():
            return jsonify(self.liquidity_data)
    
    async def _process_task_by_type(self, task_type: str, data: Dict) -> Dict:
        """Process liquidity monitor specific tasks"""
        
        if task_type == 'liquidity_monitoring':
            return await self._monitor_liquidity(data)
        elif task_type == 'pool_analysis':
            return await self._analyze_pools(data)
        elif task_type == 'liquidity_check':
            return await self._check_liquidity(data)
        elif task_type == 'enhanced_price_monitoring':
            return await self._enhanced_price_monitoring(data)
        else:
            # Call parent method for generic tasks
            return await super()._process_task_by_type(task_type, data)
    
    async def _process_event_by_type(self, event_type: str, data: Dict):
        """Process liquidity monitor specific events"""
        
        if event_type == 'price_update':
            await self._handle_price_update(data)
        elif event_type == 'arbitrage_opportunity_found':
            await self._handle_arbitrage_opportunity(data)
        elif event_type == 'high_gas_price':
            await self._handle_high_gas_price(data)
        else:
            await super()._process_event_by_type(event_type, data)
    
    async def _monitor_liquidity(self, data: Dict) -> Dict:
        """Monitor liquidity across DEXes"""
        try:
            tokens = data.get('tokens', [])
            dexs = data.get('dexs', [])
            
            liquidity_results = {}
            
            for token in tokens:
                token_liquidity = {}
                for dex in dexs:
                    # Simulate liquidity check (replace with actual implementation)
                    token_liquidity[dex] = {
                        'liquidity_usd': 100000,  # Replace with actual data
                        'volume_24h': 50000,
                        'price_impact_1000': 0.01
                    }
                
                liquidity_results[token] = token_liquidity
            
            self.liquidity_data.update(liquidity_results)
            
            return {
                'status': 'completed',
                'liquidity_data': liquidity_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _analyze_pools(self, data: Dict) -> Dict:
        """Analyze specific liquidity pools"""
        try:
            pools = data.get('pools', [])
            
            analysis_results = {}
            
            for pool in pools:
                # Simulate pool analysis (replace with actual implementation)
                analysis_results[pool] = {
                    'tvl_usd': 500000,
                    'apy': 12.5,
                    'impermanent_loss_risk': 'medium',
                    'volume_24h': 100000
                }
            
            return {
                'status': 'completed',
                'pool_analysis': analysis_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _check_liquidity(self, data: Dict) -> Dict:
        """Check liquidity for specific requirements"""
        try:
            token_pair = data.get('token_pair')
            min_liquidity = data.get('min_liquidity', 0)
            
            # Simulate liquidity check (replace with actual implementation)
            available_liquidity = 750000  # USD
            
            return {
                'status': 'completed',
                'token_pair': token_pair,
                'available_liquidity_usd': available_liquidity,
                'sufficient_liquidity': available_liquidity >= min_liquidity,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _enhanced_price_monitoring(self, data: Dict) -> Dict:
        """Enhanced price monitoring with predictions and sentiment"""
        try:
            tokens = data.get('tokens', [])
            include_predictions = data.get('include_predictions', False)
            include_sentiment = data.get('include_sentiment', False)
            
            monitoring_results = {}
            
            for token in tokens:
                token_data = {
                    'current_price': 100.0,  # Replace with actual price
                    'price_change_24h': 2.5,
                    'volume_24h': 1000000,
                    'liquidity_score': 8.5
                }
                
                if include_predictions:
                    token_data['price_prediction_1h'] = 101.2
                    token_data['trend_direction'] = 'bullish'
                
                if include_sentiment:
                    token_data['sentiment_score'] = 0.75
                    token_data['social_mentions'] = 450
                
                monitoring_results[token] = token_data
            
            return {
                'status': 'completed',
                'monitoring_data': monitoring_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _handle_price_update(self, data: Dict):
        """Handle price update events"""
        logger.info(f"Price update received: {data}")
        # Update internal price data and check for alerts
    
    async def _handle_arbitrage_opportunity(self, data: Dict):
        """Handle arbitrage opportunity events"""
        logger.info(f"Arbitrage opportunity detected: {data}")
        # Check if liquidity is sufficient for the opportunity
    
    async def _handle_high_gas_price(self, data: Dict):
        """Handle high gas price events"""
        logger.info(f"High gas price alert: {data}")
        # Adjust monitoring frequency or alert thresholds
    
    def run(self, host='0.0.0.0', port=9010):
        """Run the enhanced agent"""
        self.interaction_enabled = True
        logger.info(f"Starting Enhanced {self.agent_name} on port {port}")
        self.app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    # Example usage
    agent = EnhancedLiquidityMonitor()
    agent.run()
