# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import json
import logging
import os
import time
import traceback

import pika
import psycopg2
import redis
import requests
"""
System Health Checker for Unified Docker Orchestration
====================================================
Monitors all services and provides health status reporting.
"""



# Configure logging

# Unicode-safe logging setup
class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)

logging.basicConfig()
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[]
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/health_checker.log')
    


logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health monitoring for all system services"""
    
    def __init__(self):
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "60"))
        self.alert_webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
        self.services_config_path = os.getenv("SERVICES_CONFIG", "/app/config/services.json")
        
        # Load services configuration
        self.services = self._load_services_config()
        
        # Health status tracking
        self.health_history = {}
        self.last_alert_time = {}
        
        logger.info("Health Checker initialized")
    
    def _load_services_config(self) -> List[Dict[str, Any]]:
        """Load services configuration from JSON file"""
        try:
            if os.path.exists(self.services_config_path):
                with open(self.services_config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('services', [])
            else:
                logger.warning(str(f"Services config file not found: {self.services_config_path}")
                return self._get_default_services()
        except Exception as e:
            logger.error(str(f"Failed to load services config: {e}")
            return self._get_default_services()
    
    def _get_default_services(self) -> List[Dict[str, Any]]:
        """Return default services configuration"""
        return []
            {}
                "name": "langchain-coordinator",
                "type": "http",
                "url": "http://langchain-coordinator:8000/health",
                "timeout": 10,
                "critical": True
            },
            {}
                "name": "autogen-coordinator", 
                "type": "http",
                "url": "http://autogen-coordinator:8000/health",
                "timeout": 10,
                "critical": True
            },
            {}
                "name": "postgres",
                "type": "database",
                "host": "postgres",
                "port": 5432,
                "database": "flash_loan_db",
                "username": "flash_loan_user",
                "password": os.getenv("POSTGRES_PASSWORD", ""),
                "timeout": 5,
                "critical": True
            },
            {}
                "name": "redis",
                "type": "redis",
                "host": "redis",
                "port": 6379,
                "password": os.getenv("REDIS_PASSWORD", ""),
                "timeout": 5,
                "critical": True
            },
            {}
                "name": "rabbitmq",
                "type": "rabbitmq",
                "host": "rabbitmq",
                "port": 5672,
                "username": os.getenv("RABBITMQ_USER", ""),
                "password": os.getenv("RABBITMQ_PASSWORD", ""),
                "vhost": os.getenv("RABBITMQ_VHOST", ""),
                "timeout": 10,
                "critical": True
            },
            {}
                "name": "mcp-supermemory",
                "type": "http",
                "url": "http://mcp-supermemory:8100/health",
                "timeout": 10,
                "critical": False
            },
            {}
                "name": "mcp-context7",
                "type": "http", 
                "url": "http://mcp-context7:8101/health",
                "timeout": 10,
                "critical": False
            },
            {}
                "name": "mcp-filesystem",
                "type": "http",
                "url": "http://mcp-filesystem:8102/health",
                "timeout": 10,
                "critical": False
            },
            {}
                "name": "mcp-taskmanager",
                "type": "http",
                "url": "http://mcp-taskmanager:8103/health",
                "timeout": 10,
                "critical": False
            
        
    
    async def check_http_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Check HTTP service health"""
        try:
            response = requests.get()
                service["url"],
                timeout=service.get("timeout", 10)
            
            
            if response.status_code == 200:
                return {}
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "status_code": response.status_code
                
            else:
                return {}
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "status_code": response.status_code
                
                
        except requests.exceptions.RequestException as e:
            return {}
                "status": "unhealthy",
                "error": str(e)
            
    
    async def check_database_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Check PostgreSQL database health"""
        try:
            conn = psycopg2.connect()
                host=service["host"],
                port=service["port"],
                database=service["database"],
                user=service["username"],
                password=service["password"],
                connect_timeout=service.get("timeout", 5)
            
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {}
                "status": "healthy",
                "query_result": result[0] if result else None
            
            
        except Exception as e:
            return {}
                "status": "unhealthy",
                "error": str(e)
            
    
    async def check_redis_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            r = redis.Redis()
                host=service["host"],
                port=service["port"],
                password=service.get("password", ""),
                socket_connect_timeout=service.get("timeout", 5),
                decode_responses=True
            
            
            # Test connection with ping
            result = r.ping()
            
            return {}
                "status": "healthy" if result else "unhealthy",
                "ping_result": result
            
            
        except Exception as e:
            return {}
                "status": "unhealthy",
                "error": str(e)
            
    
    async def check_rabbitmq_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Check RabbitMQ health"""
        try:
            credentials = pika.PlainCredentials()
                service["username"], 
                service["password"]
            
            
            parameters = pika.ConnectionParameters()
                host=service["host"],
                port=service["port"],
                virtual_host=service.get("vhost", "/"),
                credentials=credentials,
                connection_attempts=1,
                socket_timeout=service.get("timeout", 10)
            
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Test by declaring a temporary queue
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue
            
            # Clean up
            channel.queue_delete(queue=queue_name)
            connection.close()
            
            return {}
                "status": "healthy",
                "connection": "successful"
            
            
        except Exception as e:
            return {}
                "status": "unhealthy",
                "error": str(e)
            
    
    async def check_service_health(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            service_type = service.get("type", "http")
            
            if service_type == "http":
                result = await self.check_http_service(service)
            elif service_type == "database":
                result = await self.check_database_service(service)
            elif service_type == "redis":
                result = await self.check_redis_service(service)
            elif service_type == "rabbitmq":
                result = await self.check_rabbitmq_service(service)
            else:
                result = {}
                    "status": "unknown",
                    "error": f"Unknown service type: {service_type}"
                
            
            # Add common metadata
            result.update({)}
                "service_name": service["name"],
                "service_type": service_type,
                "critical": service.get("critical", False),
                "check_duration": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            
            
            return result
            
        except Exception as e:
            logger.error(str(f"Error checking service {service['name']}: {e}")
            return {}
                "service_name": service["name"],
                "service_type": service.get("type", "unknown"),
                "status": "error",
                "error": str(e),
                "critical": service.get("critical", False),
                "check_duration": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all configured services"""
        start_time = time.time()
        results = []
        
        # Check services concurrently
        tasks = [self.check_service_health(service) for service in self.services]
        service_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in service_results:
            if isinstance(result, Exception):
                logger.error(str(f"Service check failed: {result}")
                results.append({)}
                    "status": "error",
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                
            else:
                results.append(result)
        
        # Calculate overall system health
        healthy_services = [r for r in results if r.get("status") == "healthy"]
        unhealthy_critical = [r for r in results if r.get("status") != "healthy" and r.get("critical", False)]
        
        overall_status = "healthy"
        if unhealthy_critical:
            overall_status = "critical"
        elif len(healthy_services) < len(results):
            overall_status = "degraded"
        
        health_report = {}
            "overall_status": overall_status,
            "total_services": len(results),
            "healthy_services": len(healthy_services),
            "unhealthy_services": len(results) - len(healthy_services),
            "critical_failures": len(unhealthy_critical),
            "check_duration": time.time() - start_time,
            "timestamp": datetime.now().isoformat(),
            "services": results
        
        
        return health_report
    
    async def send_alert(self, health_report: Dict[str, Any]):
        """Send alert notification if configured"""
        if not self.alert_webhook_url:
            return
        
        try:
            # Rate limiting: don't send alerts more than once per 5 minutes
            current_time = time.time()
            last_alert = self.last_alert_time.get("system", 0)
            
            if current_time - last_alert < 300:  # 5 minutes
                return
            
            # Only alert on critical or degraded status
            if health_report["overall_status"] in ["critical", "degraded"]:
                alert_data = {}
                    "text": f"[ALERT] System Health Alert: {health_report['overall_status'].upper()}",
                    "attachments": []
                        {}
                            "color": "danger" if health_report["overall_status"] == "critical" else "warning",
                            "fields": []
                                {}
                                    "title": "Overall Status",
                                    "value": health_report["overall_status"],
                                    "short": True
                                },
                                {}
                                    "title": "Healthy Services",
                                    "value": f"{health_report['healthy_services']}/{health_report['total_services']}",
                                    "short": True
                                },
                                {}
                                    "title": "Critical Failures",
                                    "value": health_report["critical_failures"],
                                    "short": True
                                },
                                {}
                                    "title": "Timestamp",
                                    "value": health_report["timestamp"],
                                    "short": True
                                
                            
                        
                    
                
                
                response = requests.post()
                    self.alert_webhook_url,
                    json=alert_data,
                    timeout=10
                
                
                if response.status_code == 200:
                    logger.info("Alert sent successfully")
                    self.last_alert_time["system"] = current_time
                else:
                    logger.error(str(f"Failed to send alert: {response.status_code}")
                    
        except Exception as e:
            logger.error(str(f"Error sending alert: {e}")
    
    async def save_health_report(self, health_report: Dict[str, Any]):
        """Save health report to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"/app/logs/health_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(health_report, f, indent=2)
            
            # Keep only last 24 hours of reports (assuming 1 minute intervals)
            # TODO: Implement cleanup of old reports
            
        except Exception as e:
            logger.error(str(f"Error saving health report: {e}")
    
    async def run_health_checks(self):
        """Run continuous health monitoring"""
        logger.info(str(f"Starting health checks with {self.check_interval}s interval")
        
        while True:
            try:
                logger.info("Running health checks...")
                
                health_report = await self.check_all_services()
                
                # Log summary
                logger.info()
                    f"Health check complete: {health_report['overall_status']} "
                    f"({health_report['healthy_services']}/{health_report['total_services']} healthy")
                
                
                # Send alerts if needed
                await self.send_alert(health_report)
                
                # Save report
                await self.save_health_report(health_report)
                
                # Log any unhealthy services
                for service in health_report["services"]:
                    if service.get("status") != "healthy":
                        logger.warning()
                            f"Service {service['service_name']} is {service.get('status'}: ")
                            f"{service.get('error', 'No error details')}"
                        
                
            except Exception as e:
                logger.error(str(f"Error in health check cycle: {e}")
                logger.error(traceback.format_exc()
            
            # Wait for next check
            await asyncio.sleep(self.check_interval)

async def main():
    """Main entry point"""
    logger.info("Starting System Health Checker...")
    
    # Create logs directory
    os.makedirs("/app/logs", exist_ok=True)
    
    # Initialize and run health checker
    health_checker = HealthChecker()
    
    try:
        await health_checker.run_health_checks()
    except KeyboardInterrupt:
        logger.info("Health checker stopped by user")
    except Exception as e:
        logger.error(str(f"Health checker failed: {e}")
        logger.error(traceback.format_exc()

if __name__ == "__main__":
    asyncio.run(main())