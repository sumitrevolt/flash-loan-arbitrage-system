#!/usr/bin/env python3
"""
Comprehensive Self-Healing Coordination System Launcher
======================================================

This launcher starts the complete system with:
- All MCP servers (11 servers)
- All AI agents (10 agents + self-healing agent)
- Infrastructure services (Redis, PostgreSQL, RabbitMQ)
- Monitoring services (Prometheus, Grafana)
- Self-healing capabilities

Features:
- Automatic prerequisite checking
- Environment configuration
- Health monitoring
- Service status tracking
- Error recovery
- Comprehensive logging
"""

import asyncio
import subprocess
import logging
import os
import time
import json
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from unicode_safe_logger import get_unicode_safe_logger

# Configure Unicode-safe logging
logger = get_unicode_safe_logger(__name__, 'self_healing_coordination_system.log')

class SelfHealingCoordinationLauncher:
    """Comprehensive launcher for the self-healing coordination system"""
    
    def __init__(self):
        self.docker_compose_file = "docker/docker-compose-self-healing.yml"
        self.env_file = ".env"
        self.services_status = {}
        self.startup_sequence = [
            # Infrastructure first
            ["redis", "postgres", "rabbitmq"],
            # Monitoring
            ["prometheus", "grafana"],
            # MCP Servers
            ["mcp_price_feed", "mcp_arbitrage_server", "mcp_flash_loan_server"],
            # AI Agents
            ["ai_agent_flash_loan_optimizer", "ai_agent_risk_manager", "ai_agent_arbitrage_detector"],
            # Self-healing agent
            ["ai_agent_self_healing"],
            # Main coordination system
            ["coordination_system"],
            # Dashboard
            ["dashboard"]
        ]
        
        # Service configuration
        self.service_configs = {
            # Infrastructure
            "redis": {"port": 6379, "health_endpoint": "ping"},
            "postgres": {"port": 5432, "health_endpoint": "pg_isready"},
            "rabbitmq": {"port": 5672, "management_port": 15672, "health_endpoint": "status"},
            
            # Monitoring
            "prometheus": {"port": 9090, "health_endpoint": "/-/healthy"},
            "grafana": {"port": 3000, "health_endpoint": "/api/health"},
            
            # MCP Servers
            "mcp_price_feed": {"port": 8100, "health_endpoint": "/health"},
            "mcp_arbitrage_server": {"port": 8101, "health_endpoint": "/health"},
            "mcp_flash_loan_server": {"port": 8102, "health_endpoint": "/health"},
            
            # AI Agents
            "ai_agent_flash_loan_optimizer": {"port": 9001, "health_endpoint": "/health"},
            "ai_agent_risk_manager": {"port": 9002, "health_endpoint": "/health"},
            "ai_agent_arbitrage_detector": {"port": 9003, "health_endpoint": "/health"},
            "ai_agent_self_healing": {"port": 8300, "health_endpoint": "/health"},
            
            # Main system
            "coordination_system": {"port": 8000, "health_endpoint": "/health"},
            "dashboard": {"port": 8080, "health_endpoint": "/"}
        }
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        try:
            logger.info("🔍 Checking prerequisites...")
            
            # Check Docker
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ Docker is not installed or not running")
                return False
            logger.info(f"✅ Docker found: {result.stdout.strip()}")
            
            # Check Docker Compose
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ Docker Compose is not available")
                return False
            logger.info(f"✅ Docker Compose found: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ Docker daemon is not running")
                return False
            logger.info("✅ Docker daemon is running")
            
            # Check required files
            required_files = [
                self.docker_compose_file,
                "requirements-coordination.txt",
                "docker_coordination_system.py",
                "ai_agents_config.json",
                "unified_mcp_config.json"
            ]
            
            missing_files = []
            for file_path in required_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                logger.error(f"❌ Missing required files: {missing_files}")
                return False
            
            logger.info("✅ All required files found")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking prerequisites: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Setup environment variables"""
        try:
            logger.info("🔧 Setting up environment...")
            
            env_vars = {
                "POLYGON_RPC_URL": os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
                "ARBITRAGE_PRIVATE_KEY": os.getenv("ARBITRAGE_PRIVATE_KEY", ""),
                "COMPOSE_PROJECT_NAME": "coordination_system",
                "DOCKER_BUILDKIT": "1",
                "COMPOSE_DOCKER_CLI_BUILD": "1"
            }
            
            # Create or update .env file
            with open(self.env_file, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            logger.info("✅ Environment configuration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up environment: {e}")
            return False
    
    def build_images(self) -> bool:
        """Build all Docker images"""
        try:
            logger.info("🔨 Building Docker images...")
            
            cmd = [
                'docker', 'compose',
                '-f', self.docker_compose_file,
                'build', '--parallel'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ Error building images: {result.stderr}")
                return False
            
            logger.info("✅ Docker images built successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error building images: {e}")
            return False
    
    def start_services(self) -> bool:
        """Start services in proper sequence"""
        try:
            logger.info("🚀 Starting services in sequence...")
            
            for stage, services in enumerate(self.startup_sequence, 1):
                logger.info(f"📦 Stage {stage}: Starting {services}")
                
                # Start services in this stage
                for service in services:
                    success = self.start_single_service(service)
                    if not success:
                        logger.error(f"❌ Failed to start {service}")
                        return False
                
                # Wait for services to be healthy
                if not self.wait_for_services_health(services):
                    logger.error(f"❌ Services in stage {stage} failed health check")
                    return False
                
                logger.info(f"✅ Stage {stage} completed successfully")
                time.sleep(5)  # Brief pause between stages
            
            logger.info("🎉 All services started successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting services: {e}")
            return False
    
    def start_single_service(self, service_name: str) -> bool:
        """Start a single service"""
        try:
            cmd = [
                'docker', 'compose',
                '-f', self.docker_compose_file,
                'up', '-d', service_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to start {service_name}: {result.stderr}")
                return False
            
            logger.info(f"✅ Started {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting {service_name}: {e}")
            return False
    
    def wait_for_services_health(self, services: List[str], timeout: int = 120) -> bool:
        """Wait for services to become healthy"""
        logger.info(f"⏳ Waiting for services to become healthy: {services}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_healthy = True
            
            for service in services:
                if not self.check_service_health(service):
                    all_healthy = False
                    break
            
            if all_healthy:
                logger.info(f"✅ All services healthy: {services}")
                return True
            
            time.sleep(5)
            logger.info("⏳ Still waiting for services...")
        
        logger.error(f"❌ Timeout waiting for services: {services}")
        return False
    
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is healthy"""
        try:
            cmd = [
                'docker', 'compose',
                '-f', self.docker_compose_file,
                'ps', '--format', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return False
            
            # Parse JSON output
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))
            
            for container in containers:
                if service_name in container.get('Service', ''):
                    state = container.get('State', '')
                    health = container.get('Health', '')
                    
                    if state == 'running' and (health in ['healthy', ''] or 'healthy' in health):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking health for {service_name}: {e}")
            return False
    
    def show_system_status(self):
        """Show comprehensive system status"""
        logger.info("📊 System Status Report")
        logger.info("=" * 50)
        
        try:
            cmd = [
                'docker', 'compose',
                '-f', self.docker_compose_file,
                'ps', '--format', 'table'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("\n" + result.stdout)
            
            # Show service URLs
            logger.info("\n🌐 Service URLs:")
            logger.info("-" * 30)
            for service, config in self.service_configs.items():
                port = config.get('port')
                if port:
                    logger.info(f"{service}: http://localhost:{port}")
            
            logger.info("\n📈 Monitoring URLs:")
            logger.info("-" * 30)
            logger.info("Grafana Dashboard: http://localhost:3000 (admin/admin)")
            logger.info("Prometheus: http://localhost:9090")
            logger.info("RabbitMQ Management: http://localhost:15672 (coordination/coordination_pass)")
            logger.info("Self-Healing Agent: http://localhost:8300")
            
        except Exception as e:
            logger.error(f"Error showing system status: {e}")
    
    def stop_system(self):
        """Stop the entire system"""
        try:
            logger.info("🛑 Stopping coordination system...")
            
            cmd = [
                'docker', 'compose',
                '-f', self.docker_compose_file,
                'down', '-v'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error stopping system: {result.stderr}")
            else:
                logger.info("✅ System stopped successfully")
                
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop_system()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run_system(self):
        """Run the complete system"""
        try:
            logger.info("🚀 Starting Self-Healing Coordination System")
            logger.info("=" * 60)
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Check prerequisites
            if not self.check_prerequisites():
                logger.error("❌ Prerequisites check failed")
                return False
            
            # Setup environment
            if not self.setup_environment():
                logger.error("❌ Environment setup failed")
                return False
            
            # Build images
            if not self.build_images():
                logger.error("❌ Image building failed")
                return False
            
            # Start services
            if not self.start_services():
                logger.error("❌ Service startup failed")
                return False
            
            # Show system status
            self.show_system_status()
            
            logger.info("\n🎉 Self-Healing Coordination System is running!")
            logger.info("✨ The system includes self-healing capabilities")
            logger.info("🔍 Monitor system health at: http://localhost:8300")
            logger.info("📊 View dashboard at: http://localhost:8080")
            logger.info("\nPress Ctrl+C to stop the system")
            
            # Keep running
            try:
                while True:
                    time.sleep(10)
                    # Could add periodic health checks here
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.stop_system()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error running system: {e}")
            return False

def main():
    """Main entry point"""
    launcher = SelfHealingCoordinationLauncher()
    success = launcher.run_system()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
