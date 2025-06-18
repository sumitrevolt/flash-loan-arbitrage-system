#!/usr/bin/env python3
"""
Simple Docker Deployment Script for LangChain Orchestrator
Handles Docker deployment with proper error handling and encoding
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description, check=True):
    """Run a command with proper output handling"""
    print(f"\n{description}")
    print("-" * 40)
    
    try:
        # Set environment to handle Unicode properly
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            env=env,
            check=check
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def check_prerequisites():
    """Check if required tools are available"""
    print("Checking prerequisites...")
    
    # Check Docker
    if not run_command("docker --version", "Checking Docker", check=False):
        print("ERROR: Docker is not installed or not in PATH")
        return False
    
    # Check Docker Compose
    if not run_command("docker compose version", "Checking Docker Compose", check=False):
        print("ERROR: Docker Compose is not available")
        return False
    
    return True

def fix_orchestrator():
    """Fix the orchestrator file"""
    print("Fixing orchestrator file...")
    
    if not Path("simple_auto_fix.py").exists():
        print("ERROR: simple_auto_fix.py not found")
        return False
    
    return run_command(
        "python simple_auto_fix.py enhanced_langchain_orchestrator.py",
        "Running auto-fix",
        check=False
    )

def build_docker_images():
    """Build Docker images"""
    print("Building Docker images...")
    
    # Clean up any existing containers
    run_command("docker compose down", "Stopping existing containers", check=False)
    
    # Build images
    return run_command(
        "docker compose build --no-cache",
        "Building Docker images"
    )

def start_services():
    """Start the services"""
    print("Starting services...")
    
    return run_command(
        "docker compose up -d",
        "Starting services"
    )

def check_services():
    """Check if services are running"""
    print("Checking service status...")
    
    return run_command(
        "docker compose ps",
        "Service status",
        check=False
    )

def main():
    """Main deployment function"""
    print("Enhanced LangChain Orchestrator - Simple Deployment")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}")
    
    # Check prerequisites
    if not check_prerequisites():
        print("ERROR: Prerequisites check failed")
        sys.exit(1)
    
    # Fix orchestrator file
    print("\nStep 1: Fixing orchestrator file")
    if not fix_orchestrator():
        print("WARNING: Auto-fix had issues, but continuing...")
    
    # Build Docker images
    print("\nStep 2: Building Docker images")
    if not build_docker_images():
        print("ERROR: Failed to build Docker images")
        sys.exit(1)
    
    # Start services
    print("\nStep 3: Starting services")
    if not start_services():
        print("ERROR: Failed to start services")
        sys.exit(1)
    
    # Check services
    print("\nStep 4: Checking services")
    check_services()
    
    print("\nDeployment completed!")
    print("Services should be running now.")
    print("\nTo check logs, run: docker compose logs -f")
    print("To stop services, run: docker compose down")

if __name__ == "__main__":
    main()
