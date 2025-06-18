#!/usr/bin/env python3
"""
Docker Troubleshooting and Fix Script for Flash Loan Arbitrage System
Diagnoses and fixes common Docker issues automatically
"""

import subprocess
import time
import platform
from pathlib import Path
from typing import Dict, Tuple, List

class DockerTroubleshooter:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.is_windows = platform.system() == "Windows"
        
    def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            if self.is_windows:
                # Use PowerShell for better Windows compatibility
                full_command = f'powershell.exe -Command "{command}"'
            else:
                full_command = command
                
            result: str = subprocess.run(
                full_command, 
                shell=True, 
        # WARNING: This is a security risk
        # WARNING: This is a security risk
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=self.project_root
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Error running command: {str(e)}"

    def print_status(self, message: str, status: str = "info"):
        """Print colored status messages."""
        colors = {
            "success": "✅",
            "error": "❌", 
            "warning": "⚠️",
            "info": "ℹ️",
            "working": "🔄"
        }
        print(f"{colors.get(status, 'ℹ️')} {message}")

    def check_docker_installation(self) -> bool:
        """Check if Docker is properly installed."""
        self.print_status("Checking Docker installation...", "working")
        
        success, output = self.run_command("docker --version")
        if not success:
            self.print_status("Docker is not installed or not in PATH", "error")
            self.print_status("Please install Docker Desktop from: https://www.docker.com/products/docker-desktop", "info")
            return False
        
        self.print_status(f"Docker found: {output.strip()}", "success")
        return True

    def check_docker_daemon(self) -> bool:
        """Check if Docker daemon is running."""
        self.print_status("Checking Docker daemon status...", "working")
        
        success, _ = self.run_command("docker info")
        if not success:
            self.print_status("Docker daemon is not running", "error")
            if self.is_windows:
                self.print_status("Please start Docker Desktop from the Start Menu", "info")
            else:
                self.print_status("Please start Docker service: sudo systemctl start docker", "info")
            return False
        
        self.print_status("Docker daemon is running", "success")
        return True

    def check_docker_compose(self) -> bool:
        """Check if Docker Compose is available."""
        self.print_status("Checking Docker Compose...", "working")
        
        # Try new compose command first
        success, output = self.run_command("docker compose version")
        if not success:
            # Fall back to legacy docker-compose
            success, output = self.run_command("docker-compose --version")
            if not success:
                self.print_status("Docker Compose is not available", "error")
                return False
        
        self.print_status(f"Docker Compose found: {output.strip()}", "success")
        return True

    def check_ports(self) -> Dict[int, bool]:
        """Check if required ports are available."""
        self.print_status("Checking port availability...", "working")
        
        required_ports = [3000, 5432, 6379, 8900, 8901, 8902, 8903, 8904, 8905]
        port_status: Dict[int, bool] = {}
        
        for port in required_ports:
            if self.is_windows:
                success, output = self.run_command(f"netstat -an | Select-String ':{port}'")
            else:
                success, output = self.run_command(f"netstat -an | grep :{port}")
                
            is_available = not success or "LISTEN" not in output.upper()
            port_status[port] = is_available
            
            if is_available:
                self.print_status(f"Port {port} is available", "success")
            else:
                self.print_status(f"Port {port} is in use", "warning")
        
        return port_status

    def stop_existing_containers(self) -> bool:
        """Stop and remove existing containers."""
        self.print_status("Stopping existing containers...", "working")
        
        # Stop containers using docker-compose
        _, _ = self.run_command("docker compose down")
        _, _ = self.run_command("docker-compose down")
        
        # Stop all running containers
        success3, output = self.run_command("docker ps -q")
        if success3 and output.strip():
            container_ids: List[str] = output.strip().split('\n')
            for container_id in container_ids:
                self.run_command(f"docker stop {container_id}")
        
        self.print_status("Containers stopped", "success")
        return True

    def cleanup_docker_resources(self) -> bool:
        """Clean up Docker resources."""
        self.print_status("Cleaning up Docker resources...", "working")
        
        # Remove stopped containers
        self.run_command("docker container prune -f")
        
        # Remove unused images
        self.run_command("docker image prune -f")
        
        # Remove unused volumes (be careful with this)
        self.run_command("docker volume prune -f")
        
        # Remove unused networks
        self.run_command("docker network prune -f")
        
        self.print_status("Docker cleanup completed", "success")
        return True

    def check_docker_files(self) -> bool:
        """Check if required Docker files exist."""
        self.print_status("Checking Docker configuration files...", "working")
        
        required_files = [
            "docker-compose.yml",
            "docker-compose-fixed.yml"
        ]
        
        missing_files: List[str] = []
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                missing_files.append(file_name)
                self.print_status(f"Missing: {file_name}", "error")
            else:
                self.print_status(f"Found: {file_name}", "success")
        
        if missing_files:
            self.print_status(f"Missing files: {', '.join(missing_files)}", "error")
            return False
        
        return True

    def create_dockerignore(self) -> None:
        """Create .dockerignore file."""
        dockerignore_content = """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# Compiled binary addons
build/
dist/

# Dependency directories
node_modules/
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env

# Next.js build output
.next

# Nuxt.js build output
.nuxt

# Vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Git
.git/
.gitignore

# Documentation
README.md
docs/

# Backup files
*.backup
*.bak
"""
        
        dockerignore_path = self.project_root / ".dockerignore"
        with open(dockerignore_path, 'w') as f:
            f.write(dockerignore_content.strip())
        
        self.print_status("Created .dockerignore file", "success")

    def fix_compose_file(self) -> bool:
        """Fix common issues in docker-compose.yml."""
        self.print_status("Checking docker-compose.yml for issues...", "working")
        
        compose_file = self.project_root / "docker-compose.yml"
        if not compose_file.exists():
            self.print_status("docker-compose.yml not found", "error")
            return False
        
        # Read and validate compose file
        try:
            with open(compose_file, 'r') as f:
                content = f.read()
                
            # Check for common issues
            issues_found: List[str] = []
            
            if "version:" not in content:
                issues_found.append("Missing version specification")
            
            if "networks:" not in content:
                issues_found.append("Missing networks configuration")
                
            if "volumes:" not in content:
                issues_found.append("Missing volumes configuration")
            
            if issues_found:
                self.print_status(f"Issues found in docker-compose.yml: {', '.join(issues_found)}", "warning")
            else:
                self.print_status("docker-compose.yml looks good", "success")
                
            return True
            
        except Exception as e:
            self.print_status(f"Error reading docker-compose.yml: {str(e)}", "error")
            return False

    def build_images(self) -> bool:
        """Build Docker images."""
        self.print_status("Building Docker images...", "working")
        
        # Try with the fixed compose file first
        success, output = self.run_command("docker compose -f docker-compose-fixed.yml build", timeout=300)
        if not success:
            # Fall back to regular compose file
            success, output = self.run_command("docker compose build", timeout=300)
            if not success:
                self.print_status(f"Failed to build images: {output}", "error")
                return False
        
        self.print_status("Docker images built successfully", "success")
        return True

    def start_services(self) -> bool:
        """Start Docker services."""
        self.print_status("Starting Docker services...", "working")
        
        # Try with the fixed compose file first
        success, output = self.run_command("docker compose -f docker-compose-fixed.yml up -d")
        if not success:
            # Fall back to regular compose file
            success, output = self.run_command("docker compose up -d")
            if not success:
                self.print_status(f"Failed to start services: {output}", "error")
                return False
        
        self.print_status("Docker services started successfully", "success")
        return True

    def check_service_health(self) -> None:
        """Check health of running services."""
        self.print_status("Checking service health...", "working")
        
        # Wait for services to start
        time.sleep(10)
        
        # Check running containers
        success, output = self.run_command("docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'")
        if success:
            self.print_status("Running containers:", "info")
            print(output)
        
        # Check logs for errors
        success, output = self.run_command("docker compose logs --tail=20")
        if success and ("error" in output.lower() or "failed" in output.lower()):
            self.print_status("Some services may have errors. Check logs:", "warning")
            print(output[-1000:])  # Show last 1000 characters

    def run_troubleshooting(self) -> bool:
        """Run complete troubleshooting process."""
        print("🐳 Flash Loan Docker Troubleshooting Script")
        print("=" * 60)
        
        # Step 1: Check Docker installation
        if not self.check_docker_installation():
            return False
        
        # Step 2: Check Docker daemon
        if not self.check_docker_daemon():
            return False
        
        # Step 3: Check Docker Compose
        if not self.check_docker_compose():
            return False
        
        # Step 4: Check ports
        port_status = self.check_ports()
        busy_ports: List[int] = [port for port, available in port_status.items() if not available]
        
        if busy_ports:
            self.print_status(f"Ports {busy_ports} are busy", "warning")
            self.print_status("You may need to stop services using these ports", "info")
        
        # Step 5: Check Docker files
        if not self.check_docker_files():
            self.print_status("Some Docker files are missing", "error")
            return False
        
        # Step 6: Create .dockerignore if missing
        if not (self.project_root / ".dockerignore").exists():
            self.create_dockerignore()
        
        # Step 7: Stop existing containers
        self.stop_existing_containers()
        
        # Step 8: Clean up resources
        self.cleanup_docker_resources()
        
        # Step 9: Fix compose file
        self.fix_compose_file()
        
        # Step 10: Build images
        if not self.build_images():
            return False
        
        # Step 11: Start services
        if not self.start_services():
            return False
        
        # Step 12: Check service health
        self.check_service_health()
        
        return True

def main():
    """Main function."""
    troubleshooter = DockerTroubleshooter()
    
    if troubleshooter.run_troubleshooting():
        print("\n🎉 Docker troubleshooting completed successfully!")
        print("\n📋 Next steps:")
        print("1. Check service status: docker compose ps")
        print("2. View logs: docker compose logs -f")
        print("3. Access your services:")
        print("   - Main API: http://localhost:3000")
        print("   - MCP Coordinator: http://localhost:8900")
        print("   - PostgreSQL: localhost:5432")
        print("   - Redis: localhost:6379")
        print("\n🛠️  Useful commands:")
        print("- Stop services: docker compose down")
        print("- Restart services: docker compose restart")
        print("- View service status: docker compose ps")
        print("- Follow logs: docker compose logs -f")
    else:
        print("\n❌ Docker troubleshooting failed!")
        print("Please check the errors above and try again.")
        print("\n🆘 If problems persist, try:")
        print("1. Restart Docker Desktop")
        print("2. Reset Docker Desktop to factory defaults")
        print("3. Check for Windows/Docker compatibility issues")

if __name__ == "__main__":
    main()
