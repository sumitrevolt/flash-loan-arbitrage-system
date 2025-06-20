#!/usr/bin/env python3
"""
Monitoring MCP Server
====================

Monitors AAVE flash loan system performance, health, and opportunities.
Provides real-time insights and alerts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MonitoringMCP")

class MonitoringMCPServer:
    """System monitoring and alerting server"""
    
    def __init__(self):
        self.server_name = "monitoring_mcp_server"
        self.port = 8004
        self.running = False
        
        # Monitoring metrics
        self.metrics = {
            "total_opportunities_found": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_profit_earned": 0.0,
            "average_profit_per_execution": 0.0,
            "uptime_start": datetime.now(),
            "last_opportunity_time": None,
            "system_health_score": 1.0
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            "min_opportunities_per_hour": 5,
            "max_failed_execution_rate": 0.2,  # 20%
            "min_system_health_score": 0.8,
            "max_time_since_last_opportunity_minutes": 60
        }
        
        # Connected servers status
        self.server_status = {
            "aave_flash_loan_mcp_server": {"status": "unknown", "last_check": None},
            "dex_aggregator_mcp_server": {"status": "unknown", "last_check": None},
            "risk_management_mcp_server": {"status": "unknown", "last_check": None},
            "profit_optimizer_mcp_server": {"status": "unknown", "last_check": None}
        }
        
        # Recent events
        self.recent_events = []
        self.max_events = 100
    
    def log_event(self, event_type: str, description: str, data: Dict[str, Any] = None):
        """Log a system event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "description": description,
            "data": data or {}
        }
        
        self.recent_events.append(event)
        
        # Keep only recent events
        if len(self.recent_events) > self.max_events:
            self.recent_events = self.recent_events[-self.max_events:]
        
        logger.info(f"Event logged: {event_type} - {description}")
    
    def update_metrics(self, metric_updates: Dict[str, Any]):
        """Update system metrics"""
        for key, value in metric_updates.items():
            if key in self.metrics:
                if key == "total_profit_earned":
                    self.metrics[key] += value
                elif key in ["total_opportunities_found", "successful_executions", "failed_executions"]:
                    self.metrics[key] += value
                else:
                    self.metrics[key] = value
        
        # Recalculate derived metrics
        total_executions = self.metrics["successful_executions"] + self.metrics["failed_executions"]
        if total_executions > 0:
            self.metrics["average_profit_per_execution"] = (
                self.metrics["total_profit_earned"] / self.metrics["successful_executions"] 
                if self.metrics["successful_executions"] > 0 else 0
            )
    
    def calculate_health_score(self) -> float:
        """Calculate overall system health score"""
        health_factors = []
        
        # Check server connectivity
        active_servers = sum(1 for status in self.server_status.values() 
                           if status["status"] == "healthy")
        server_health = active_servers / len(self.server_status)
        health_factors.append(server_health)
        
        # Check execution success rate
        total_executions = self.metrics["successful_executions"] + self.metrics["failed_executions"]
        if total_executions > 0:
            success_rate = self.metrics["successful_executions"] / total_executions
            health_factors.append(success_rate)
        else:
            health_factors.append(1.0)  # No executions yet
        
        # Check recent opportunity detection
        if self.metrics["last_opportunity_time"]:
            time_diff = datetime.now() - datetime.fromisoformat(self.metrics["last_opportunity_time"])
            if time_diff.total_seconds() < 3600:  # Within last hour
                opportunity_health = 1.0
            else:
                opportunity_health = max(0.0, 1.0 - time_diff.total_seconds() / 7200)  # Decay over 2 hours
            health_factors.append(opportunity_health)
        
        # Calculate overall health
        health_score = sum(health_factors) / len(health_factors) if health_factors else 0.0
        self.metrics["system_health_score"] = health_score
        
        return health_score
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for system alerts"""
        alerts = []
        
        # Check health score
        health_score = self.calculate_health_score()
        if health_score < self.alert_thresholds["min_system_health_score"]:
            alerts.append({
                "type": "health_warning",
                "message": f"System health score low: {health_score:.2f}",
                "severity": "medium"
            })
        
        # Check failed execution rate
        total_execs = self.metrics["successful_executions"] + self.metrics["failed_executions"]
        if total_execs > 0:
            fail_rate = self.metrics["failed_executions"] / total_execs
            if fail_rate > self.alert_thresholds["max_failed_execution_rate"]:
                alerts.append({
                    "type": "execution_failure",
                    "message": f"High failure rate: {fail_rate:.1%}",
                    "severity": "high"
                })
        
        # Check opportunity detection
        if self.metrics["last_opportunity_time"]:
            time_diff = datetime.now() - datetime.fromisoformat(self.metrics["last_opportunity_time"])
            if time_diff.total_seconds() > self.alert_thresholds["max_time_since_last_opportunity_minutes"] * 60:
                alerts.append({
                    "type": "opportunity_detection",
                    "message": f"No opportunities found for {time_diff.total_seconds()/60:.0f} minutes",
                    "severity": "medium"
                })
        
        return alerts
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        uptime = datetime.now() - self.metrics["uptime_start"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_formatted": str(uptime),
            "metrics": self.metrics,
            "server_status": self.server_status,
            "health_score": self.calculate_health_score(),
            "alerts": self.check_alerts(),
            "recent_events": self.recent_events[-10:],  # Last 10 events
            "profit_target_range": "$4 - $30",
            "execution_mode": "TEST" if not os.getenv("ENABLE_REAL_EXECUTION", "false").lower() == "true" else "LIVE"
        }
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        try:
            if method == "log_event":
                event_type = params.get("event_type", "unknown")
                description = params.get("description", "")
                data = params.get("data", {})
                self.log_event(event_type, description, data)
                return {"status": "logged"}
                
            elif method == "update_metrics":
                metric_updates = params.get("metrics", {})
                self.update_metrics(metric_updates)
                return {"status": "updated"}
                
            elif method == "get_status":
                return self.get_system_status()
                
            elif method == "get_metrics":
                return {"metrics": self.metrics}
                
            elif method == "get_alerts":
                return {"alerts": self.check_alerts()}
                
            elif method == "update_server_status":
                server_name = params.get("server_name", "")
                status = params.get("status", "unknown")
                if server_name in self.server_status:
                    self.server_status[server_name] = {
                        "status": status,
                        "last_check": datetime.now().isoformat()
                    }
                return {"status": "updated"}
                
            elif method == "health_check":
                return {
                    "status": "healthy",
                    "server": self.server_name,
                    "timestamp": datetime.now().isoformat(),
                    "monitoring_active": self.running,
                    "health_score": self.calculate_health_score()
                }
                
            else:
                return {"error": f"Unknown method: {method}"}
                
        except Exception as e:
            logger.error(f"Error handling request {method}: {e}")
            return {"error": str(e)}
    
    async def start_server(self):
        """Start the MCP server"""
        self.running = True
        logger.info(f"Starting {self.server_name} on port {self.port}")
        
        # Log startup event
        self.log_event("system_startup", "Monitoring MCP server started")
        
        try:
            while self.running:
                # Periodic monitoring tasks
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
                # Calculate health score
                health_score = self.calculate_health_score()
                
                # Check for alerts
                alerts = self.check_alerts()
                
                # Log periodic status
                if len(alerts) > 0:
                    logger.warning(f"Active alerts: {len(alerts)}, Health score: {health_score:.2f}")
                else:
                    logger.info(f"System healthy - Health score: {health_score:.2f}")
                
                # Log significant events
                if health_score < 0.5:
                    self.log_event("health_critical", f"Critical health score: {health_score:.2f}")
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.log_event("system_error", f"Server error: {e}")
        finally:
            self.log_event("system_shutdown", "Monitoring MCP server shutting down")
            logger.info(f"{self.server_name} shutting down")
    
    def stop_server(self):
        """Stop the MCP server"""
        self.running = False

async def main():
    """Main server function"""
    server = MonitoringMCPServer()
    
    try:
        logger.info("=" * 50)
        logger.info("MONITORING MCP SERVER")
        logger.info("=" * 50)
        logger.info("Real-time monitoring for AAVE flash loan system")
        logger.info("Health checks, metrics, and alerting")
        logger.info("=" * 50)
        
        await server.start_server()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        server.stop_server()
    except Exception as e:
        logger.error(f"Server startup error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
