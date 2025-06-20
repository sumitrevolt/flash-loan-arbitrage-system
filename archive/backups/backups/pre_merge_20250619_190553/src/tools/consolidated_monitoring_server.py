#!/usr/bin/env python3
"""
Consolidated Monitoring MCP Server
=================================
Unified monitoring server combining all monitoring functionality
System health, alerts, dashboards, and reporting
"""

import asyncio
import json
import logging
import time
from decimal import Decimal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from flask import Flask, jsonify, render_template_string
import requests
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Alert structure"""
    id: str
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class SystemMetrics:
    """System metrics structure"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int
    response_time: float

class ConsolidatedMonitoringServer:
    """
    Consolidated monitoring server for all system components
    Replaces multiple duplicate monitoring servers
    """
    
    def __init__(self):
        self.app = Flask(__name__)
        self.alerts: List[Alert] = []
        self.metrics_history: List[SystemMetrics] = []
        self.service_status: Dict[str, Dict] = {}
        
        # External service URLs
        self.services = {
            "pricing_server": "http://localhost:8001",
            "trading_server": "http://localhost:8002",
            "arbitrage_detector": "http://localhost:8003"
        }
        
        # Alert thresholds
        self.thresholds = {
            "cpu_usage_warning": 70.0,
            "cpu_usage_critical": 90.0,
            "memory_usage_warning": 80.0,
            "memory_usage_critical": 95.0,
            "disk_usage_warning": 80.0,
            "disk_usage_critical": 90.0,
            "response_time_warning": 5.0,
            "response_time_critical": 10.0,
            "service_down_critical": True
        }
        
        self.setup_routes()
        self.start_monitoring()
        
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health')
        def health():
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services_monitored": len(self.services),
                "active_alerts": len([a for a in self.alerts if not a.resolved]),
                "uptime": self.get_uptime()
            })
            
        @self.app.route('/dashboard')
        def dashboard():
            """Web dashboard for monitoring"""
            return render_template_string(DASHBOARD_HTML, 
                                        services=self.service_status,
                                        alerts=self.alerts[-10:],
                                        metrics=self.get_latest_metrics())
            
        @self.app.route('/alerts')
        def get_alerts():
            """Get all alerts"""
            alerts_data = []
            for alert in self.alerts[-100:]:  # Last 100 alerts
                alerts_data.append({
                    "id": alert.id,
                    "level": alert.level.value,
                    "message": alert.message,
                    "source": alert.source,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged,
                    "resolved": alert.resolved
                })
            return jsonify(alerts_data)
            
        @self.app.route('/alerts/active')
        def get_active_alerts():
            """Get active (unresolved) alerts"""
            active_alerts = [a for a in self.alerts if not a.resolved]
            alerts_data = []
            for alert in active_alerts:
                alerts_data.append({
                    "id": alert.id,
                    "level": alert.level.value,
                    "message": alert.message,
                    "source": alert.source,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged
                })
            return jsonify(alerts_data)
            
        @self.app.route('/services')
        def get_services():
            """Get status of all monitored services"""
            return jsonify(self.service_status)
            
        @self.app.route('/metrics')
        def get_metrics():
            """Get system metrics"""
            return jsonify(self.get_latest_metrics())
            
        @self.app.route('/metrics/history')
        def get_metrics_history():
            """Get metrics history"""
            history_data = []
            for metric in self.metrics_history[-100:]:  # Last 100 metrics
                history_data.append({
                    "timestamp": metric.timestamp.isoformat(),
                    "cpu_usage": metric.cpu_usage,
                    "memory_usage": metric.memory_usage,
                    "disk_usage": metric.disk_usage,
                    "response_time": metric.response_time,
                    "active_connections": metric.active_connections
                })
            return jsonify(history_data)
            
        @self.app.route('/status')
        def get_system_status():
            """Get comprehensive system status"""
            active_alerts = len([a for a in self.alerts if not a.resolved])
            critical_alerts = len([a for a in self.alerts 
                                 if not a.resolved and a.level == AlertLevel.CRITICAL])
            
            services_up = len([s for s in self.service_status.values() 
                             if s.get("status") == "healthy"])
            total_services = len(self.service_status)
            
            latest_metrics = self.get_latest_metrics()
            
            return jsonify({
                "overall_status": self.get_overall_status(),
                "services": {
                    "healthy": services_up,
                    "total": total_services,
                    "percentage": (services_up / total_services * 100) if total_services > 0 else 0
                },
                "alerts": {
                    "active": active_alerts,
                    "critical": critical_alerts
                },
                "system": latest_metrics,
                "uptime": self.get_uptime()
            })
            
    def start_monitoring(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self.monitor_services_loop())
        asyncio.create_task(self.monitor_system_loop())
        asyncio.create_task(self.cleanup_old_data_loop())
        
    async def monitor_services_loop(self):
        """Monitor external services continuously"""
        while True:
            try:
                await self.check_all_services()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error monitoring services: {e}")
                await asyncio.sleep(60)
                
    async def monitor_system_loop(self):
        """Monitor system metrics continuously"""
        while True:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(10)  # Collect every 10 seconds
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(30)
                
    async def cleanup_old_data_loop(self):
        """Clean up old data periodically"""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                self.cleanup_old_data()
            except Exception as e:
                logger.error(f"Error cleaning up data: {e}")
                
    async def check_all_services(self):
        """Check health of all monitored services"""
        for service_name, url in self.services.items():
            await self.check_service_health(service_name, url)
            
    async def check_service_health(self, service_name: str, url: str):
        """Check health of a single service"""
        try:
            start_time = time.time()
            response = requests.get(f"{url}/health", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.service_status[service_name] = {
                    "status": "healthy",
                    "response_time": response_time,
                    "last_check": datetime.now().isoformat(),
                    "details": response.json()
                }
                
                # Check response time thresholds
                if response_time > self.thresholds["response_time_critical"]:
                    self.create_alert(
                        AlertLevel.CRITICAL,
                        f"{service_name} response time critical: {response_time:.2f}s",
                        service_name
                    )
                elif response_time > self.thresholds["response_time_warning"]:
                    self.create_alert(
                        AlertLevel.WARNING,
                        f"{service_name} response time high: {response_time:.2f}s",
                        service_name
                    )
                    
            else:
                self.service_status[service_name] = {
                    "status": "unhealthy",
                    "response_time": response_time,
                    "last_check": datetime.now().isoformat(),
                    "error": f"HTTP {response.status_code}"
                }
                
                self.create_alert(
                    AlertLevel.ERROR,
                    f"{service_name} returned HTTP {response.status_code}",
                    service_name
                )
                
        except requests.exceptions.Timeout:
            self.service_status[service_name] = {
                "status": "timeout",
                "last_check": datetime.now().isoformat(),
                "error": "Request timeout"
            }
            
            self.create_alert(
                AlertLevel.ERROR,
                f"{service_name} request timeout",
                service_name
            )
            
        except Exception as e:
            self.service_status[service_name] = {
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
            
            self.create_alert(
                AlertLevel.CRITICAL,
                f"{service_name} is down: {str(e)}",
                service_name
            )
            
    async def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv
            }
            
            # Active connections
            connections = len([c for c in psutil.net_connections() 
                             if c.status == psutil.CONN_ESTABLISHED])
            
            # Average response time of services
            avg_response_time = sum(
                s.get("response_time", 0) for s in self.service_status.values()
            ) / len(self.service_status) if self.service_status else 0
            
            # Create metrics object
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=connections,
                response_time=avg_response_time
            )
            
            self.metrics_history.append(metrics)
            
            # Check thresholds and create alerts
            self.check_metrics_thresholds(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            
    def check_metrics_thresholds(self, metrics: SystemMetrics):
        """Check metrics against thresholds and create alerts"""
        
        # CPU usage alerts
        if metrics.cpu_usage > self.thresholds["cpu_usage_critical"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                f"CPU usage critical: {metrics.cpu_usage:.1f}%",
                "system"
            )
        elif metrics.cpu_usage > self.thresholds["cpu_usage_warning"]:
            self.create_alert(
                AlertLevel.WARNING,
                f"CPU usage high: {metrics.cpu_usage:.1f}%",
                "system"
            )
            
        # Memory usage alerts
        if metrics.memory_usage > self.thresholds["memory_usage_critical"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                f"Memory usage critical: {metrics.memory_usage:.1f}%",
                "system"
            )
        elif metrics.memory_usage > self.thresholds["memory_usage_warning"]:
            self.create_alert(
                AlertLevel.WARNING,
                f"Memory usage high: {metrics.memory_usage:.1f}%",
                "system"
            )
            
        # Disk usage alerts
        if metrics.disk_usage > self.thresholds["disk_usage_critical"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                f"Disk usage critical: {metrics.disk_usage:.1f}%",
                "system"
            )
        elif metrics.disk_usage > self.thresholds["disk_usage_warning"]:
            self.create_alert(
                AlertLevel.WARNING,
                f"Disk usage high: {metrics.disk_usage:.1f}%",
                "system"
            )
            
    def create_alert(self, level: AlertLevel, message: str, source: str):
        """Create a new alert"""
        # Avoid duplicate alerts (same message within 5 minutes)
        recent_alerts = [a for a in self.alerts 
                        if (datetime.now() - a.timestamp).seconds < 300
                        and a.message == message and a.source == source]
        
        if not recent_alerts:
            alert = Alert(
                id=f"alert_{int(time.time())}_{len(self.alerts)}",
                level=level,
                message=message,
                source=source,
                timestamp=datetime.now()
            )
            self.alerts.append(alert)
            logger.warning(f"ALERT [{level.value.upper()}] {source}: {message}")
            
    def get_latest_metrics(self) -> Dict:
        """Get latest system metrics"""
        if not self.metrics_history:
            return {}
            
        latest = self.metrics_history[-1]
        return {
            "timestamp": latest.timestamp.isoformat(),
            "cpu_usage": latest.cpu_usage,
            "memory_usage": latest.memory_usage,
            "disk_usage": latest.disk_usage,
            "network_io": latest.network_io,
            "active_connections": latest.active_connections,
            "response_time": latest.response_time
        }
        
    def get_overall_status(self) -> str:
        """Get overall system status"""
        critical_alerts = [a for a in self.alerts 
                          if not a.resolved and a.level == AlertLevel.CRITICAL]
        
        if critical_alerts:
            return "critical"
            
        unhealthy_services = [s for s in self.service_status.values() 
                            if s.get("status") != "healthy"]
        
        if unhealthy_services:
            return "warning"
            
        return "healthy"
        
    def get_uptime(self) -> str:
        """Get system uptime"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return str(uptime).split('.')[0]  # Remove microseconds
        except:
            return "unknown"
            
    def cleanup_old_data(self):
        """Clean up old alerts and metrics"""
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
            
        # Keep only last 1000 metrics (about 3 hours at 10s intervals)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
            
        logger.info("Cleaned up old monitoring data")
        
    def run(self, host='0.0.0.0', port=8004):
        """Run the monitoring server"""
        logger.info(f"🚀 Starting Consolidated Monitoring MCP Server on {host}:{port}")
        logger.info(f"Monitoring {len(self.services)} services")
        
        self.app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True
        )

# Simple HTML dashboard template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Flash Loan System Monitor</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status-healthy { color: green; }
        .status-warning { color: orange; }
        .status-critical { color: red; }
        .alert { padding: 10px; margin: 5px 0; border-radius: 5px; }
        .alert-critical { background-color: #ffebee; border-left: 5px solid red; }
        .alert-warning { background-color: #fff3e0; border-left: 5px solid orange; }
        .alert-info { background-color: #e3f2fd; border-left: 5px solid blue; }
        .metrics { display: flex; gap: 20px; }
        .metric { padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🚀 Flash Loan System Monitor</h1>
    
    <h2>Services Status</h2>
    {% for name, status in services.items() %}
    <div class="service">
        <strong>{{ name }}:</strong> 
        <span class="status-{{ status['status'] }}">{{ status['status'] }}</span>
        <small>({{ status.get('response_time', 0):.3f}s)</small>
    </div>
    {% endfor %}
    
    <h2>System Metrics</h2>
    <div class="metrics">
        <div class="metric">
            <strong>CPU:</strong> {{ "%.1f"|format(metrics.get('cpu_usage', 0)) }}%
        </div>
        <div class="metric">
            <strong>Memory:</strong> {{ "%.1f"|format(metrics.get('memory_usage', 0)) }}%
        </div>
        <div class="metric">
            <strong>Disk:</strong> {{ "%.1f"|format(metrics.get('disk_usage', 0)) }}%
        </div>
    </div>
    
    <h2>Recent Alerts</h2>
    {% for alert in alerts %}
    <div class="alert alert-{{ alert.level.value }}">
        <strong>[{{ alert.level.value.upper() }}]</strong> {{ alert.message }}
        <small>({{ alert.timestamp.strftime('%H:%M:%S') }})</small>
    </div>
    {% endfor %}
</body>
</html>
"""

def main():
    """Main entry point"""
    server = ConsolidatedMonitoringServer()
    server.run()

if __name__ == "__main__":
    main()
