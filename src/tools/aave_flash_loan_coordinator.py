#!/usr/bin/env python3
"""
Aave Flash Loan Coordinator
Main coordinator service for managing Aave flash loan operations
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class AaveFlashLoanCoordinator:
    """Main coordinator for Aave flash loan operations"""
    
    def __init__(self, port: int = 9000):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Setup structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.dev.ConsoleRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger(__name__)
        
        # Initialize connections
        self.redis_client = None
        self.db_connection = None
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            try:
                status = {
                    'status': 'healthy',
                    'service': 'aave-flash-loan-coordinator',
                    'version': '1.0.0',
                    'redis': self._check_redis(),
                    'database': self._check_database()
                }
                return jsonify(status), 200
            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e)
                }), 500
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get coordinator status"""
            return jsonify({
                'status': 'running',
                'service': 'aave-flash-loan-coordinator',
                'port': self.port,
                'uptime': 'unknown'
            })
        
        @self.app.route('/flash-loan/execute', methods=['POST'])
        def execute_flash_loan():
            """Execute flash loan operation"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                # Log the request
                self.logger.info("Flash loan execution requested", data=data)
                
                # For now, return a mock response
                return jsonify({
                    'status': 'initiated',
                    'transaction_id': 'mock_tx_123',
                    'message': 'Flash loan execution initiated'
                })
                
            except Exception as e:
                self.logger.error("Flash loan execution failed", error=str(e))
                return jsonify({'error': str(e)}), 500
    
    def _check_redis(self) -> bool:
        """Check Redis connection"""
        try:
            if not self.redis_client:
                redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
                self.redis_client = redis.from_url(redis_url)
            
            self.redis_client.ping()
            return True
        except Exception as e:
            self.logger.warning("Redis check failed", error=str(e))
            return False
    
    def _check_database(self) -> bool:
        """Check database connection"""
        try:
            if not self.db_connection:
                db_url = os.getenv('POSTGRES_URL', 
                    'postgresql://flash_loan:flash_loan_secure_123@postgres:5432/flash_loan_db')
                
                # Parse the URL
                parts = db_url.replace('postgresql://', '').split('@')
                user_pass = parts[0]
                host_db = parts[1]
                
                user, password = user_pass.split(':')
                host, database = host_db.split('/')
                host, port = host.split(':')
                
                self.db_connection = psycopg2.connect(
                    host=host,
                    port=int(port),
                    database=database,
                    user=user,
                    password=password,
                    cursor_factory=RealDictCursor
                )
            
            # Test connection
            with self.db_connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
            
            return True
            
        except Exception as e:
            self.logger.warning("Database check failed", error=str(e))
            return False
    
    def run(self):
        """Run the coordinator service"""
        self.logger.info("Starting Aave Flash Loan Coordinator", port=self.port)
        
        try:
            self.app.run(
                host='0.0.0.0',
                port=self.port,
                debug=False,
                threaded=True
            )
        except Exception as e:
            self.logger.error("Failed to start coordinator", error=str(e))
            sys.exit(1)

def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    coordinator = AaveFlashLoanCoordinator()
    coordinator.run()

if __name__ == '__main__':
    main()
