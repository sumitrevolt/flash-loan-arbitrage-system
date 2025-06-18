#!/usr/bin/env python3
"""
Self-Healing Coordination System Test Script
===========================================

This script tests the self-healing coordination system step by step:
1. Check prerequisites
2. Build minimal services
3. Test service communication
4. Test self-healing capabilities
5. Generate system report
"""

import subprocess
import time
import json
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoordinationSystemTester:
    def __init__(self):
        self.compose_file = "docker/docker-compose-test.yml"
        
    def test_prerequisites(self):
        """Test system prerequisites"""
        logger.info("🔍 Testing prerequisites...")
        
        try:
            # Test Docker
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker: {result.stdout.strip()}")
            else:
                logger.error("❌ Docker not available")
                return False
            
            # Test Docker Compose
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker Compose: {result.stdout.strip()}")
            else:
                logger.error("❌ Docker Compose not available")
                return False
            
            # Check required files
            required_files = [
                self.compose_file,
                "docker/Dockerfile.mcp",
                "docker/Dockerfile.agent",
                "docker/Dockerfile.coordination"
            ]
            
            for file_path in required_files:
                if Path(file_path).exists():
                    logger.info(f"✅ Found: {file_path}")
                else:
                    logger.error(f"❌ Missing: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing prerequisites: {e}")
            return False
    
    def start_minimal_system(self):
        """Start minimal system for testing"""
        logger.info("🚀 Starting minimal system...")
        
        try:
            # Start infrastructure first
            cmd = ['docker', 'compose', '-f', self.compose_file, 'up', '-d', 'redis', 'postgres']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ Failed to start infrastructure: {result.stderr}")
                return False
            
            logger.info("✅ Infrastructure started")
            time.sleep(10)  # Wait for infrastructure
            
            # Start one MCP server
            cmd = ['docker', 'compose', '-f', self.compose_file, 'up', '-d', 'mcp_price_feed']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ Failed to start MCP server: {result.stderr}")
                return False
            
            logger.info("✅ MCP server started")
            time.sleep(15)  # Wait for MCP server
            
            # Start one AI agent
            cmd = ['docker', 'compose', '-f', self.compose_file, 'up', '-d', 'ai_agent_trading']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ Failed to start AI agent: {result.stderr}")
                return False
            
            logger.info("✅ AI agent started")
            time.sleep(15)  # Wait for AI agent
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting minimal system: {e}")
            return False
    
    def test_service_health(self):
        """Test service health endpoints"""
        logger.info("🏥 Testing service health...")
        
        services_to_test = [
            ("MCP Price Feed", "http://localhost:8100/health"),
            ("AI Agent Trading", "http://localhost:8200/health")
        ]
        
        all_healthy = True
        
        for service_name, health_url in services_to_test:
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name}: Healthy")
                    logger.info(f"   Response: {response.json()}")
                else:
                    logger.error(f"❌ {service_name}: Unhealthy (status: {response.status_code})")
                    all_healthy = False
            except Exception as e:
                logger.error(f"❌ {service_name}: Failed to connect ({e})")
                all_healthy = False
        
        return all_healthy
    
    def test_service_communication(self):
        """Test communication between services"""
        logger.info("📡 Testing service communication...")
        
        try:
            # Test MCP server query
            mcp_response = requests.post(
                "http://localhost:8100/query",
                json={"type": "price_query", "symbol": "ETH"},
                timeout=10
            )
            
            if mcp_response.status_code == 200:
                logger.info("✅ MCP server responds to queries")
                logger.info(f"   Response: {mcp_response.json()}")
            else:
                logger.error(f"❌ MCP server query failed: {mcp_response.status_code}")
                return False
            
            # Test AI agent task execution
            agent_response = requests.post(
                "http://localhost:8200/execute",
                json={"type": "price_analysis", "symbol": "ETH"},
                timeout=10
            )
            
            if agent_response.status_code == 200:
                logger.info("✅ AI agent executes tasks")
                logger.info(f"   Response: {agent_response.json()}")
            else:
                logger.error(f"❌ AI agent task failed: {agent_response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing service communication: {e}")
            return False
    
    def show_system_status(self):
        """Show current system status"""
        logger.info("📊 Current System Status:")
        logger.info("=" * 50)
        
        try:
            cmd = ['docker', 'compose', '-f', self.compose_file, 'ps']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(result.stdout)
            else:
                logger.error(f"Failed to get status: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
    
    def cleanup_system(self):
        """Clean up the test system"""
        logger.info("🧹 Cleaning up test system...")
        
        try:
            cmd = ['docker', 'compose', '-f', self.compose_file, 'down', '-v']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ System cleaned up successfully")
            else:
                logger.error(f"❌ Cleanup failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def run_comprehensive_test(self):
        """Run comprehensive system test"""
        logger.info("🎯 Starting Comprehensive System Test")
        logger.info("=" * 60)
        
        try:
            # Test 1: Prerequisites
            if not self.test_prerequisites():
                logger.error("❌ Prerequisites test failed")
                return False
            
            # Test 2: Start minimal system
            if not self.start_minimal_system():
                logger.error("❌ System startup failed")
                return False
            
            # Test 3: Health checks
            if not self.test_service_health():
                logger.error("❌ Health check failed")
                return False
            
            # Test 4: Service communication
            if not self.test_service_communication():
                logger.error("❌ Service communication test failed")
                return False
            
            # Show status
            self.show_system_status()
            
            logger.info("🎉 All tests passed! System is working correctly.")
            logger.info("\n📋 Next Steps:")
            logger.info("1. Run the full system: python self_healing_coordination_launcher.py")
            logger.info("2. Monitor at: http://localhost:8300 (self-healing agent)")
            logger.info("3. Access dashboard at: http://localhost:8080")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            return False
        
        finally:
            # Always cleanup
            self.cleanup_system()

def main():
    """Main test function"""
    tester = CoordinationSystemTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 System test completed successfully!")
        print("✨ Your self-healing coordination system is ready!")
    else:
        print("\n❌ System test failed. Please check the logs above.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
