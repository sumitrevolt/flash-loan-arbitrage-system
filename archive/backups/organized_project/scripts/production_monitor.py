#!/usr/bin/env python3
"""
Production System Performance Monitor
Monitors all MCP servers and system performance in real-time
"""

import asyncio
import logging
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psutil
import aiohttp
import sqlite3
from dataclasses import dataclass, asdict
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ServerMetrics:
    """Server performance metrics"""
    name: str
    host: str
    port: int
    response_time: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    requests_per_minute: int
    success_rate: float
    error_count: int
    last_updated: str
    health_status: str

@dataclass
class SystemMetrics:
    """Overall system metrics"""
    timestamp: str
    total_servers: int
    healthy_servers: int
    avg_response_time: float
    total_requests: int
    total_errors: int
    system_cpu: float
    system_memory: float
    system_disk: float
    docker_containers: int
    active_trading_sessions: int

class ProductionMonitor:
    """Comprehensive production monitoring system"""
    
    def __init__(self):
        self.db_path = "production_metrics.db"
        self.mcp_servers = []
        self.monitoring_active = False
        self.metrics_history = []
        self.alert_thresholds = {
            "response_time": 5.0,  # seconds
            "cpu_usage": 80.0,     # percentage
            "memory_usage": 85.0,  # percentage
            "success_rate": 95.0,  # percentage
            "disk_usage": 90.0     # percentage
        }
        
    async def initialize(self):
        """Initialize monitoring system"""
        logger.info("🚀 Initializing Production Monitor...")
        
        # Create database for metrics storage
        self.setup_database()
        
        # Discover MCP servers
        await self.discover_mcp_servers()
        
        # Create monitoring directories
        os.makedirs("monitoring_reports", exist_ok=True)
        os.makedirs("performance_logs", exist_ok=True)
        os.makedirs("alerts", exist_ok=True)
        
        logger.info("✅ Production Monitor initialized")
    
    def setup_database(self):
        """Setup SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Server metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                server_name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                response_time REAL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                requests_per_minute INTEGER,
                success_rate REAL,
                error_count INTEGER,
                health_status TEXT
            )
        ''')
        
        # System metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_servers INTEGER,
                healthy_servers INTEGER,
                avg_response_time REAL,
                total_requests INTEGER,
                total_errors INTEGER,
                system_cpu REAL,
                system_memory REAL,
                system_disk REAL,
                docker_containers INTEGER,
                active_trading_sessions INTEGER
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                server_name TEXT,
                metric_name TEXT,
                metric_value REAL,
                threshold REAL,
                severity TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolution_time TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("📊 Database initialized")
    
    async def discover_mcp_servers(self):
        """Discover all running MCP servers"""
        logger.info("🔍 Discovering MCP servers...")
        
        # MCP server port ranges
        mcp_ports = list(range(8100, 8121)) + list(range(8200, 8210))
        
        self.mcp_servers = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for port in mcp_ports:
                try:
                    url = f"http://localhost:{port}/health"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            server_info = {
                                "name": data.get("service", f"mcp-server-{port}"),
                                "host": "localhost",
                                "port": port,
                                "capabilities": data.get("capabilities", []),
                                "health_status": data.get("status", "unknown")
                            }
                            self.mcp_servers.append(server_info)
                            
                except Exception as e:
                    # Server not responding, skip
                    continue
        
        logger.info(f"📍 Discovered {len(self.mcp_servers)} active MCP servers")
        return self.mcp_servers
    
    async def collect_server_metrics(self, server: Dict[str, Any]) -> ServerMetrics:
        """Collect metrics for a single server"""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Health check
                health_url = f"http://{server['host']}:{server['port']}/health"
                async with session.get(health_url) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        health_data = await response.json()
                        health_status = health_data.get("status", "unknown")
                    else:
                        health_status = "unhealthy"
                
                # Metrics endpoint
                metrics_url = f"http://{server['host']}:{server['port']}/metrics"
                try:
                    async with session.get(metrics_url) as response:
                        if response.status == 200:
                            metrics_data = await response.json()
                        else:
                            metrics_data = {}
                except:
                    metrics_data = {}
            
            # Get system metrics for this process (approximation)
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return ServerMetrics(
                name=server["name"],
                host=server["host"],
                port=server["port"],
                response_time=response_time,
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                requests_per_minute=metrics_data.get("requests_per_minute", 0),
                success_rate=metrics_data.get("success_rate", 100.0),
                error_count=metrics_data.get("error_count", 0),
                last_updated=datetime.now().isoformat(),
                health_status=health_status
            )
            
        except Exception as e:
            logger.error(f"❌ Error collecting metrics for {server['name']}: {e}")
            return ServerMetrics(
                name=server["name"],
                host=server["host"],
                port=server["port"],
                response_time=999.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                requests_per_minute=0,
                success_rate=0.0,
                error_count=1,
                last_updated=datetime.now().isoformat(),
                health_status="error"
            )
    
    async def collect_system_metrics(self, server_metrics: List[ServerMetrics]) -> SystemMetrics:
        """Collect overall system metrics"""
        timestamp = datetime.now().isoformat()
        
        # System resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Docker containers count
        try:
            import subprocess
            result = subprocess.run(['docker', 'ps', '-q'], capture_output=True, text=True)
            docker_containers = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        except:
            docker_containers = 0
        
        # Calculate aggregated metrics
        healthy_servers = len([s for s in server_metrics if s.health_status == "healthy"])
        avg_response_time = sum(s.response_time for s in server_metrics) / len(server_metrics) if server_metrics else 0
        total_requests = sum(s.requests_per_minute for s in server_metrics)
        total_errors = sum(s.error_count for s in server_metrics)
        
        return SystemMetrics(
            timestamp=timestamp,
            total_servers=len(server_metrics),
            healthy_servers=healthy_servers,
            avg_response_time=avg_response_time,
            total_requests=total_requests,
            total_errors=total_errors,
            system_cpu=cpu_percent,
            system_memory=memory.percent,
            system_disk=disk.percent,
            docker_containers=docker_containers,
            active_trading_sessions=0  # Would need to integrate with trading system
        )
    
    def store_metrics(self, server_metrics: List[ServerMetrics], system_metrics: SystemMetrics):
        """Store metrics in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store server metrics
        for metric in server_metrics:
            cursor.execute('''
                INSERT INTO server_metrics 
                (timestamp, server_name, host, port, response_time, cpu_usage, 
                 memory_usage, disk_usage, requests_per_minute, success_rate, 
                 error_count, health_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.last_updated, metric.name, metric.host, metric.port,
                metric.response_time, metric.cpu_usage, metric.memory_usage,
                metric.disk_usage, metric.requests_per_minute, metric.success_rate,
                metric.error_count, metric.health_status
            ))
        
        # Store system metrics
        cursor.execute('''
            INSERT INTO system_metrics 
            (timestamp, total_servers, healthy_servers, avg_response_time,
             total_requests, total_errors, system_cpu, system_memory,
             system_disk, docker_containers, active_trading_sessions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            system_metrics.timestamp, system_metrics.total_servers,
            system_metrics.healthy_servers, system_metrics.avg_response_time,
            system_metrics.total_requests, system_metrics.total_errors,
            system_metrics.system_cpu, system_metrics.system_memory,
            system_metrics.system_disk, system_metrics.docker_containers,
            system_metrics.active_trading_sessions
        ))
        
        conn.commit()
        conn.close()
    
    def check_alerts(self, server_metrics: List[ServerMetrics], system_metrics: SystemMetrics):
        """Check for alert conditions"""
        alerts = []
        
        # Check server-level alerts
        for metric in server_metrics:
            if metric.response_time > self.alert_thresholds["response_time"]:
                alerts.append({
                    "type": "performance",
                    "server": metric.name,
                    "metric": "response_time",
                    "value": metric.response_time,
                    "threshold": self.alert_thresholds["response_time"],
                    "severity": "warning"
                })
            
            if metric.cpu_usage > self.alert_thresholds["cpu_usage"]:
                alerts.append({
                    "type": "resource",
                    "server": metric.name,
                    "metric": "cpu_usage",
                    "value": metric.cpu_usage,
                    "threshold": self.alert_thresholds["cpu_usage"],
                    "severity": "warning"
                })
            
            if metric.memory_usage > self.alert_thresholds["memory_usage"]:
                alerts.append({
                    "type": "resource",
                    "server": metric.name,
                    "metric": "memory_usage",
                    "value": metric.memory_usage,
                    "threshold": self.alert_thresholds["memory_usage"],
                    "severity": "critical"
                })
            
            if metric.success_rate < self.alert_thresholds["success_rate"]:
                alerts.append({
                    "type": "reliability",
                    "server": metric.name,
                    "metric": "success_rate",
                    "value": metric.success_rate,
                    "threshold": self.alert_thresholds["success_rate"],
                    "severity": "critical"
                })
            
            if metric.health_status != "healthy":
                alerts.append({
                    "type": "health",
                    "server": metric.name,
                    "metric": "health_status",
                    "value": metric.health_status,
                    "threshold": "healthy",
                    "severity": "critical"
                })
        
        # Store alerts in database
        if alerts:
            self.store_alerts(alerts)
            logger.warning(f"⚠️ {len(alerts)} alerts generated")
            
        return alerts
    
    def store_alerts(self, alerts: List[Dict[str, Any]]):
        """Store alerts in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''
                INSERT INTO alerts 
                (timestamp, alert_type, server_name, metric_name, metric_value, 
                 threshold, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                alert["type"],
                alert.get("server", "system"),
                alert["metric"],
                alert["value"],
                alert["threshold"],
                alert["severity"]
            ))
        
        conn.commit()
        conn.close()
    
    async def generate_monitoring_report(self) -> str:
        """Generate monitoring report"""
        logger.info("📄 Generating monitoring report...")
        
        # Get recent metrics from database
        conn = sqlite3.connect(self.db_path)
        
        # Get latest system metrics
        system_df = pd.read_sql_query('''
            SELECT * FROM system_metrics 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', conn)
        
        # Get server metrics from last hour
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        server_df = pd.read_sql_query('''
            SELECT * FROM server_metrics 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC
        ''', conn, params=[one_hour_ago])
        
        # Get recent alerts
        alerts_df = pd.read_sql_query('''
            SELECT * FROM alerts 
            WHERE timestamp > ? AND resolved = FALSE
            ORDER BY timestamp DESC
        ''', conn, params=[one_hour_ago])
        
        conn.close()
        
        # Generate report
        report_lines = [
            "=" * 80,
            "PRODUCTION SYSTEM MONITORING REPORT",
            "=" * 80,
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SYSTEM OVERVIEW:",
        ]
        
        if not system_df.empty:
            latest_system = system_df.iloc[0]
            report_lines.extend([
                f"📊 Total Servers: {latest_system['total_servers']}",
                f"✅ Healthy Servers: {latest_system['healthy_servers']}",
                f"⚡ Avg Response Time: {latest_system['avg_response_time']:.2f}s",
                f"📈 Total Requests/min: {latest_system['total_requests']}",
                f"❌ Total Errors: {latest_system['total_errors']}",
                f"💻 System CPU: {latest_system['system_cpu']:.1f}%",
                f"🧠 System Memory: {latest_system['system_memory']:.1f}%",
                f"💾 System Disk: {latest_system['system_disk']:.1f}%",
                f"🐳 Docker Containers: {latest_system['docker_containers']}",
            ])
        
        report_lines.extend([
            "",
            "SERVER STATUS:",
        ])
        
        if not server_df.empty:
            # Group by server and get latest metrics
            latest_servers = server_df.groupby('server_name').first()
            
            for server_name, metrics in latest_servers.iterrows():
                status_icon = "🟢" if metrics['health_status'] == "healthy" else "🔴"
                report_lines.extend([
                    f"{status_icon} {server_name} ({metrics['host']}:{metrics['port']})",
                    f"   Response: {metrics['response_time']:.2f}s | CPU: {metrics['cpu_usage']:.1f}% | Memory: {metrics['memory_usage']:.1f}%",
                    f"   Success Rate: {metrics['success_rate']:.1f}% | Errors: {metrics['error_count']}",
                ])
        
        if not alerts_df.empty:
            report_lines.extend([
                "",
                "🚨 ACTIVE ALERTS:",
            ])
            
            for _, alert in alerts_df.iterrows():
                severity_icon = "🔴" if alert['severity'] == "critical" else "⚠️"
                report_lines.append(
                    f"{severity_icon} {alert['alert_type'].upper()}: {alert['server_name']} - "
                    f"{alert['metric_name']} = {alert['metric_value']} (threshold: {alert['threshold']})"
                )
        else:
            report_lines.extend([
                "",
                "✅ No active alerts"
            ])
        
        report_lines.extend([
            "",
            "=" * 80,
        ])
        
        report_content = "\n".join(report_lines)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"monitoring_reports/monitoring_report_{timestamp}.txt"
        with open(report_file, "w") as f:
            f.write(report_content)
        
        logger.info(f"📄 Monitoring report saved to {report_file}")
        return report_content
    
    async def monitoring_loop(self, interval: int = 60):
        """Main monitoring loop"""
        logger.info(f"🔄 Starting monitoring loop (interval: {interval}s)")
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                # Collect metrics from all servers
                server_metrics = []
                for server in self.mcp_servers:
                    metrics = await self.collect_server_metrics(server)
                    server_metrics.append(metrics)
                
                # Collect system metrics
                system_metrics = await self.collect_system_metrics(server_metrics)
                
                # Store metrics
                self.store_metrics(server_metrics, system_metrics)
                
                # Check for alerts
                alerts = self.check_alerts(server_metrics, system_metrics)
                
                # Log summary
                healthy_count = len([s for s in server_metrics if s.health_status == "healthy"])
                logger.info(
                    f"📊 Monitoring cycle complete: {healthy_count}/{len(server_metrics)} servers healthy, "
                    f"avg response: {system_metrics.avg_response_time:.2f}s, "
                    f"alerts: {len(alerts)}"
                )
                
                # Wait for next cycle
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_active = False
        logger.info("🛑 Monitoring stopped")

async def main():
    """Main function"""
    print("🔍 Starting Production System Monitor")
    print("=" * 50)
    
    monitor = ProductionMonitor()
    
    try:
        await monitor.initialize()
        
        # Generate initial report
        await monitor.generate_monitoring_report()
        
        # Start monitoring loop
        await monitor.monitoring_loop(interval=30)  # Monitor every 30 seconds
        
    except KeyboardInterrupt:
        logger.info("👋 Monitoring stopped by user")
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"❌ Monitor failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
