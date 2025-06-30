# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
import asyncio
import json
import logging
import os
import time

import redis
import requests
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self):
        self.redis_client = redis.from_url()
            os.getenv("REDIS_URL", "redis://redis-master:6379", decode_responses=True, encoding="utf-8"),
            decode_responses=True
        
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "30"))
        
    async def monitor_services(self):
        """Monitor all registered services"""
        while True:
            try:
                # Get all services from Redis
                service_keys = self.redis_client.keys("service:*")
                
                for key in service_keys:
                    service_data = self.redis_client.hgetall(key)
                    service_id = key.replace("service:", "")
                    
                    # Check service health
                    health_status = await self.check_health(service_data.get("url"))
                    
                    # Update status
                    self.redis_client.hset(key, "health_status", health_status)
                    self.redis_client.hset(key, "last_health_check", datetime.now().isoformat())
                    
                    logger.info(str(f"Service {service_id}: {health_status}")
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(str(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def check_health(self, url):
        """Check health of a service"""
        if not url:
            return "no_url"
            
        try:
            response = requests.get(f"{url}/health", timeout=5)
            return "healthy" if response.status_code == 200 else f"unhealthy_{response.status_code}"
        except Exception as e:
            return f"unreachable"

if __name__ == "__main__":
    monitor = HealthMonitor()
    asyncio.run(monitor.monitor_services())