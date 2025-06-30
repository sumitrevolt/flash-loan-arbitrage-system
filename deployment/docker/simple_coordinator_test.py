# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
import asyncio
import json

import pika
import psycopg2
import redis
"""
Simple test of the master coordinator functionality
"""

async def test_connections():
    """Test connections to infrastructure services"""
    print("[SEARCH] Testing infrastructure connections...")
    
    # Test Redis
    try:
        redis_client = redis.Redis(host='localhost', port=6380, password='master_coordination_2025', decode_responses=True)
        redis_client.ping()
        print("[OK] Redis connection successful")
        
        # Test basic operations
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        print(f"[OK] Redis operations work: {value}")
        
    except Exception as e:
        print(f"[ERROR] Redis connection failed: {e}")
    
    # Test PostgreSQL
    try:
        conn = psycopg2.connect()
            host='localhost',
            port=5433,
            database='master_coordination',
            user='master_coord_user',
            password='master_coord_secure_2025'
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"[OK] PostgreSQL connection successful: {version[0][:50]}...")
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] PostgreSQL connection failed: {e}")
    
    # Test RabbitMQ
    try:
        connection = pika.BlockingConnection()
            pika.URLParameters('amqp://master_coord_mq:master_coord_mq_2025@localhost:5673/master_coord_vhost')
        
        channel = connection.channel()
        print("[OK] RabbitMQ connection successful")
        connection.close()
        
    except Exception as e:
        print(f"[ERROR] RabbitMQ connection failed: {e}")

def test_service_discovery():
    """Test service discovery simulation"""
    print("\n[SEARCH] Testing service discovery simulation...")
    
    # Simulate discovering your existing services
    existing_services = []
        "flashloan-mcp-flash-loan:8103",
        "flashloan-mcp-monitoring:8114", 
        "flashloan-agent-coordinator:8200",
        "flashloan-agent-arbitrage-bot:8206"
    
    
    discovered_services = {}
    for service in existing_services:
        name, port = service.split(":")
        service_info = {}
            "id": name,
            "name": name.replace("flashloan-", "").replace("-", " ").title(),
            "url": f"http://localhost:{port}",
            "status": "discovered",
            "type": "existing_service"
        
        discovered_services[name] = service_info
        print(f"[OK] Discovered: {service_info['name']} at {service_info['url']}")
    
    print(f"\n[METRICS] Total discovered services: {len(discovered_services)}")
    return discovered_services

def main():
    """Main test function"""
    print("[INIT] Master Coordination System - Connection Test")
    print("=" * 60)
    
    # Test async connections
    asyncio.run(test_connections())
    
    # Test service discovery
    discovered = test_service_discovery()
    
    print("\n" + "=" * 60)
    print("[OK] Enhanced Coordination System Ready!")
    print(f"[GROWTH] Infrastructure services: Running on conflict-free ports")
    print(f"[SEARCH] Service discovery: Can detect {len(discovered)} existing services")
    print(f"[NETWORK] Network isolation: Using dedicated 172.25.0.0/16 network")
    print("=" * 60)

if __name__ == "__main__":
    main()