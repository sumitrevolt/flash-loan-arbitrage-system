"""
System Monitoring for Flash Loan Arbitrage System
==============================================

Comprehensive monitoring system for:
- Performance metrics collection
- Health monitoring
- Alerting and notifications
- Resource usage tracking
- Trading performance analytics
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, start_http_server

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    response_times: Dict[str, float] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    active_connections: int = 0

@dataclass
class TradingMetrics:
    """Trading performance metrics"""
    timestamp: datetime
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_profit_usd: float
    total_volume_usd: float
    average_profit_per_trade: float
    success_rate: float
    opportunities_detected: int
    opportunities_executed: int

@dataclass
class Alert:
    """System alert"""
    severity: str  # 'info', 'warning', 'error', 'critical'
    message: str
    timestamp: datetime
    source: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None

class PrometheusMetrics:
    """Prometheus metrics collector"""
    
    def __init__(self):
        # System metrics
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
        self.disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
        
        # Trading metrics
        self.trades_total = Counter('trades_total', 'Total number of trades', ['status'])
        self.profit_total = Counter('profit_usd_total', 'Total profit in USD')
        self.trade_duration = Histogram('trade_duration_seconds', 'Trade execution duration')
        self.opportunities_detected = Counter('opportunities_detected_total', 'Arbitrage opportunities detected')
        
        # System health
        self.service_health = Gauge('service_health', 'Service health status', ['service_name'])
        self.response_time = Histogram('response_time_seconds', 'Response time', ['endpoint'])
        self.error_rate = Counter('errors_total', 'Total errors', ['service', 'error_type'])
    
    def update_system_metrics(self, metrics: SystemMetrics):
        """Update system metrics"""
        self.cpu_usage.set(metrics.cpu_percent)
        self.memory_usage.set(metrics.memory_percent)
        self.disk_usage.set(metrics.disk_usage_percent)
    
    def record_trade(self, success: bool, profit_usd: float, duration_seconds: float):
        """Record trade metrics"""
        status = 'success' if success else 'failure'
        self.trades_total.labels(status=status).inc()
        
        if success:
            self.profit_total.inc(profit_usd)
        
        self.trade_duration.observe(duration_seconds)
    
    def record_opportunity(self):
        """Record detected opportunity"""
        self.opportunities_detected.inc()

class SystemMonitor:
    """Main system monitoring class"""
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        self.prometheus_metrics = PrometheusMetrics()
        self.metrics_history: List[SystemMetrics] = []
        self.trading_history: List[TradingMetrics] = []
        self.alerts: List[Alert] = []
        self.is_running = False
        
        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'error_rate': 0.05,
            'response_time_seconds': 5.0,
            'min_success_rate': 0.7
        }
        
        # Service health tracking
        self.service_health: Dict[str, bool] = {}
        self.last_health_check: Dict[str, datetime] = {}
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start the monitoring loop"""
        self.is_running = True
        logger.info("🔍 Starting system monitoring...")
        
        # Start Prometheus metrics server
        try:
            start_http_server(9090)
            logger.info("📊 Prometheus metrics server started on port 9090")
        except Exception as e:
            logger.warning(f"Failed to start Prometheus server: {e}")
        
        while self.is_running:
            try:
                # Collect system metrics
                await self.collect_system_metrics()
                
                # Check service health
                await self.check_service_health()
                
                # Check alert conditions
                self.check_alerts()
                
                # Cleanup old data
                self.cleanup_old_data()
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                }
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Update Prometheus metrics
            self.prometheus_metrics.update_system_metrics(metrics)
            
            logger.debug(f"📊 Collected metrics: CPU={cpu_percent:.1f}%, Memory={memory.percent:.1f}%")
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    async def check_service_health(self):
        """Check health of all services"""
        services = [
            {'name': 'mcp-arbitrage', 'url': 'http://localhost:8001/health'},
            {'name': 'mcp-price-feed', 'url': 'http://localhost:8002/health'},
            {'name': 'mcp-risk-manager', 'url': 'http://localhost:8003/health'},
            {'name': 'agent-coordinator', 'url': 'http://localhost:9001/health'},
            {'name': 'agent-arbitrage-bot', 'url': 'http://localhost:9002/health'},
        ]
        
        for service in services:
            await self.check_individual_service(service['name'], service['url'])
    
    async def check_individual_service(self, service_name: str, health_url: str):
        """Check health of individual service"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(health_url, timeout=5) as response:
                    response_time = time.time() - start_time
                    
                    is_healthy = response.status == 200
                    self.service_health[service_name] = is_healthy
                    self.last_health_check[service_name] = datetime.now()
                    
                    # Update Prometheus metrics
                    self.prometheus_metrics.service_health.labels(service_name=service_name).set(1 if is_healthy else 0)
                    self.prometheus_metrics.response_time.labels(endpoint=health_url).observe(response_time)
                    
                    if not is_healthy:
                        self.add_alert(
                            severity='error',
                            message=f"Service {service_name} is unhealthy (HTTP {response.status})",
                            source='health_check'
                        )
                    
        except asyncio.TimeoutError:
            self.service_health[service_name] = False
            self.add_alert(
                severity='error',
                message=f"Service {service_name} health check timed out",
                source='health_check'
            )
        except Exception as e:
            self.service_health[service_name] = False
            self.add_alert(
                severity='error',
                message=f"Service {service_name} health check failed: {str(e)}",
                source='health_check'
            )
    
    def check_alerts(self):
        """Check for alert conditions"""
        if not self.metrics_history:
            return
        
        latest_metrics = self.metrics_history[-1]
        
        # CPU usage alert
        if latest_metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            self.add_alert(
                severity='warning',
                message=f"High CPU usage: {latest_metrics.cpu_percent:.1f}%",
                source='system_metrics',
                metric_value=latest_metrics.cpu_percent,
                threshold=self.alert_thresholds['cpu_percent']
            )
        
        # Memory usage alert
        if latest_metrics.memory_percent > self.alert_thresholds['memory_percent']:
            self.add_alert(
                severity='warning',
                message=f"High memory usage: {latest_metrics.memory_percent:.1f}%",
                source='system_metrics',
                metric_value=latest_metrics.memory_percent,
                threshold=self.alert_thresholds['memory_percent']
            )
        
        # Disk usage alert
        if latest_metrics.disk_usage_percent > self.alert_thresholds['disk_usage_percent']:
            self.add_alert(
                severity='error',
                message=f"High disk usage: {latest_metrics.disk_usage_percent:.1f}%",
                source='system_metrics',
                metric_value=latest_metrics.disk_usage_percent,
                threshold=self.alert_thresholds['disk_usage_percent']
            )
        
        # Service health alerts
        for service_name, is_healthy in self.service_health.items():
            if not is_healthy:
                last_check = self.last_health_check.get(service_name)
                if last_check and datetime.now() - last_check > timedelta(minutes=5):
                    self.add_alert(
                        severity='critical',
                        message=f"Service {service_name} has been down for >5 minutes",
                        source='service_health'
                    )
    
    def add_alert(self, severity: str, message: str, source: str, 
                  metric_value: Optional[float] = None, threshold: Optional[float] = None):
        """Add new alert"""
        alert = Alert(
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            source=source,
            metric_value=metric_value,
            threshold=threshold
        )
        
        self.alerts.append(alert)
        
        # Log alert
        log_func = {
            'info': logger.info,
            'warning': logger.warning,
            'error': logger.error,
            'critical': logger.critical
        }.get(severity, logger.info)
        
        log_func(f"🚨 ALERT [{severity.upper()}]: {message}")
    
    def record_trade_result(self, success: bool, profit_usd: float, duration_seconds: float):
        """Record trading result"""
        self.prometheus_metrics.record_trade(success, profit_usd, duration_seconds)
        
        # Log significant events
        if success and profit_usd > 100:
            logger.info(f"💰 Profitable trade: ${profit_usd:.2f} in {duration_seconds:.1f}s")
        elif not success:
            logger.warning(f"❌ Trade failed after {duration_seconds:.1f}s")
    
    def record_arbitrage_opportunity(self, opportunity_data: Dict[str, Any]):
        """Record detected arbitrage opportunity"""
        self.prometheus_metrics.record_opportunity()
        
        profit_potential = opportunity_data.get('profit_usd', 0)
        if profit_potential > 50:
            logger.info(f"🎯 High-value opportunity detected: ${profit_potential:.2f} potential profit")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest_metrics = self.metrics_history[-1]
        recent_alerts = [
            alert for alert in self.alerts[-10:]  # Last 10 alerts
            if alert.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        return {
            "status": "healthy" if len(recent_alerts) == 0 else "degraded",
            "timestamp": latest_metrics.timestamp.isoformat(),
            "metrics": {
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_percent": latest_metrics.memory_percent,
                "disk_usage_percent": latest_metrics.disk_usage_percent
            },
            "service_health": self.service_health,
            "recent_alerts": [
                {
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "source": alert.source
                }
                for alert in recent_alerts
            ],
            "alert_counts": {
                "critical": len([a for a in recent_alerts if a.severity == "critical"]),
                "error": len([a for a in recent_alerts if a.severity == "error"]),
                "warning": len([a for a in recent_alerts if a.severity == "warning"]),
                "info": len([a for a in recent_alerts if a.severity == "info"])
            }
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate performance report for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent metrics
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No data available for the specified period"}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        max_cpu = max(m.cpu_percent for m in recent_metrics)
        max_memory = max(m.memory_percent for m in recent_metrics)
        
        # Count alerts by severity
        recent_alerts = [
            a for a in self.alerts
            if a.timestamp > cutoff_time
        ]
        
        alert_counts = {}
        for severity in ['critical', 'error', 'warning', 'info']:
            alert_counts[severity] = len([a for a in recent_alerts if a.severity == severity])
        
        return {
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "system_performance": {
                "cpu": {
                    "average": round(avg_cpu, 1),
                    "maximum": round(max_cpu, 1)
                },
                "memory": {
                    "average": round(avg_memory, 1),
                    "maximum": round(max_memory, 1)
                }
            },
            "alerts": alert_counts,
            "service_uptime": {
                service: sum(1 for m in recent_metrics if self.service_health.get(service, False)) / len(recent_metrics) * 100
                for service in self.service_health.keys()
            }
        }
    
    def cleanup_old_data(self):
        """Clean up old monitoring data"""
        cutoff_time = datetime.now() - timedelta(days=7)  # Keep 7 days of data
        
        # Clean metrics history
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
        
        # Clean alerts (keep 30 days)
        alert_cutoff = datetime.now() - timedelta(days=30)
        self.alerts = [
            a for a in self.alerts
            if a.timestamp > alert_cutoff
        ]
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.is_running = False
        logger.info("🛑 System monitoring stopped")

# Global monitor instance
system_monitor = SystemMonitor()

async def start_monitoring():
    """Start system monitoring"""
    await system_monitor.start_monitoring()

def get_system_status():
    """Get current system status"""
    return system_monitor.get_system_status()

def record_trade(success: bool, profit_usd: float, duration_seconds: float):
    """Record trade result"""
    system_monitor.record_trade_result(success, profit_usd, duration_seconds)

def record_opportunity(opportunity_data: Dict[str, Any]):
    """Record arbitrage opportunity"""
    system_monitor.record_arbitrage_opportunity(opportunity_data)