#!/usr/bin/env python3
"""
Docker Deployment Script for Enhanced LangChain Orchestrator
===========================================================
This script handles the complete Docker deployment with auto-fixing.
"""

import os
import sys
import subprocess
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional

class DockerDeploymentManager:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.compose_file = self.project_dir / "docker-compose.yml"
        self.env_file = self.project_dir / ".env"
        self.orchestrator_file = self.project_dir / "enhanced_langchain_orchestrator.py"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker is not installed or not running")
                return False
            print(f"✅ Docker: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ Docker command not found")
            return False
        
        # Check Docker Compose
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker Compose is not installed")
                return False
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ Docker Compose command not found")
            return False
        
        # Check required files
        required_files = [
            'Dockerfile',
            'docker-compose.yml',
            'enhanced_langchain_orchestrator.py',
            'requirements-enhanced-complete.txt'
        ]
        
        for file in required_files:
            file_path = self.project_dir / file
            if not file_path.exists():
                print(f"❌ Required file missing: {file}")
                return False
            print(f"✅ Found: {file}")
        
        return True
    
    def setup_environment(self) -> bool:
        """Setup environment variables"""
        print("🔧 Setting up environment...")
        
        if not self.env_file.exists():
            # Copy from example
            env_example = self.project_dir / ".env.example"
            if env_example.exists():
                with open(env_example, 'r') as src, open(self.env_file, 'w') as dst:
                    dst.write(src.read())
                print("✅ Created .env from example")
            else:
                # Create minimal .env
                env_content = """# Basic configuration
OPENAI_API_KEY=your_openai_api_key_here
REDIS_PASSWORD=langchain_redis_password_2025
POSTGRES_PASSWORD=langchain_password_2025
SECRET_KEY=your_super_secret_key_here
"""
                with open(self.env_file, 'w') as f:
                    f.write(env_content)
                print("✅ Created minimal .env file")
        
        # Warn about API keys
        with open(self.env_file, 'r') as f:
            env_content = f.read()
            if 'your_openai_api_key_here' in env_content:
                print("⚠️  Warning: Please update your API keys in .env file")
        
        return True
    
    def run_auto_fix(self) -> bool:
        """Run auto-fix on the orchestrator file"""
        print("🔧 Running auto-fix on orchestrator...")
        
        try:
            result = subprocess.run([
                sys.executable, 
                'auto_fix_orchestrator.py', 
                str(self.orchestrator_file)
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if result.returncode == 0:
                print("✅ Auto-fix completed successfully")
                print(result.stdout)
                return True
            else:
                print("⚠️  Auto-fix encountered issues:")
                print(result.stderr)
                # Continue anyway
                return True
        except Exception as e:
            print(f"⚠️  Could not run auto-fix: {e}")
            return True  # Continue anyway
    
    def build_images(self) -> bool:
        """Build Docker images"""
        print("🏗️  Building Docker images...")
        
        try:
            # Build with no cache to ensure fresh build
            cmd = ['docker-compose', 'build', '--no-cache']
            result = subprocess.run(cmd, cwd=self.project_dir)
            
            if result.returncode == 0:
                print("✅ Docker images built successfully")
                return True
            else:
                print("❌ Failed to build Docker images")
                return False
        except Exception as e:
            print(f"❌ Error building images: {e}")
            return False
    
    def start_services(self) -> bool:
        """Start all services"""
        print("🚀 Starting services...")
        
        try:
            # Start services
            cmd = ['docker-compose', 'up', '-d']
            result = subprocess.run(cmd, cwd=self.project_dir)
            
            if result.returncode == 0:
                print("✅ Services started successfully")
                return True
            else:
                print("❌ Failed to start services")
                return False
        except Exception as e:
            print(f"❌ Error starting services: {e}")
            return False
    
    def wait_for_services(self, timeout: int = 300) -> bool:
        """Wait for services to be healthy"""
        print("⏳ Waiting for services to be ready...")
        
        services_to_check = [
            ('http://localhost:8000/health', 'LangChain Orchestrator'),
            ('http://localhost:6379', 'Redis', self._check_redis),
            ('http://localhost:5432', 'PostgreSQL', self._check_postgres),
        ]
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_healthy = True
            
            for service_check in services_to_check:
                if len(service_check) == 2:
                    url, name = service_check
                    if not self._check_http_service(url):
                        all_healthy = False
                        print(f"⏳ Waiting for {name}...")
                        break
                else:
                    url, name, check_func = service_check
                    if not check_func():
                        all_healthy = False
                        print(f"⏳ Waiting for {name}...")
                        break
            
            if all_healthy:
                print("✅ All services are ready!")
                return True
            
            time.sleep(10)
        
        print("❌ Timeout waiting for services")
        return False
    
    def _check_http_service(self, url: str) -> bool:
        """Check if HTTP service is responding"""
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_redis(self) -> bool:
        """Check Redis connectivity"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, password='langchain_redis_password_2025')
            r.ping()
            return True
        except:
            return False
    
    def _check_postgres(self) -> bool:
        """Check PostgreSQL connectivity"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='localhost',
                database='langchain_db',
                user='langchain_user',
                password='langchain_password_2025'
            )
            conn.close()
            return True
        except:
            return False
    
    def show_status(self):
        """Show deployment status"""
        print("\n📊 Deployment Status:")
        print("=" * 50)
        
        try:
            # Show running containers
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True, cwd=self.project_dir)
            print("🐳 Container Status:")
            print(result.stdout)
            
            # Show logs for main service
            print("\n📋 Recent Logs (last 20 lines):")
            result = subprocess.run(['docker-compose', 'logs', '--tail=20', 'langchain-orchestrator'], 
                                  capture_output=True, text=True, cwd=self.project_dir)
            print(result.stdout)
            
        except Exception as e:
            print(f"Error getting status: {e}")
        
        print("\n🌐 Service URLs:")
        print("- Main Orchestrator: http://localhost:8000")
        print("- Health Check: http://localhost:8000/health")
        print("- Grafana Dashboard: http://localhost:3000 (admin/langchain_admin_2025)")
        print("- Prometheus: http://localhost:9090")
        
    def cleanup(self):
        """Clean up deployment"""
        print("🧹 Cleaning up...")
        
        try:
            # Stop services
            subprocess.run(['docker-compose', 'down'], cwd=self.project_dir)
            print("✅ Services stopped")
            
            # Optional: Remove volumes (uncomment if needed)
            # subprocess.run(['docker-compose', 'down', '-v'], cwd=self.project_dir)
            # print("✅ Volumes removed")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def deploy(self) -> bool:
        """Run complete deployment"""
        print("🚀 Starting Enhanced LangChain Orchestrator Deployment")
        print("=" * 60)
        
        steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Environment Setup", self.setup_environment),
            ("Auto-Fix Orchestrator", self.run_auto_fix),
            ("Build Images", self.build_images),
            ("Start Services", self.start_services),
            ("Wait for Services", self.wait_for_services),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            print("-" * 40)
            
            if not step_func():
                print(f"❌ Failed at step: {step_name}")
                return False
        
        print("\n🎉 Deployment completed successfully!")
        self.show_status()
        return True

def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()
    
    print(f"📁 Project directory: {project_dir}")
    
    deployer = DockerDeploymentManager(project_dir)
    
    try:
        success = deployer.deploy()
        if success:
            print("\n✅ Deployment successful!")
            print("📖 Use 'docker-compose logs -f' to follow logs")
            print("🛑 Use 'docker-compose down' to stop services")
        else:
            print("\n❌ Deployment failed!")
            print("🔍 Check the logs above for details")
            deployer.cleanup()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Deployment interrupted by user")
        deployer.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        deployer.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
