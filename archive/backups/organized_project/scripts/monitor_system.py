#!/usr/bin/env python3
"""
System Monitor for 32-Container LangChain Flash Loan System
Monitors the build and deployment progress of all containers
"""

import subprocess
import time
import json
from datetime import datetime

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check_docker_images():
    """Check Docker images that have been built"""
    print("=== DOCKER IMAGES ===")
    stdout, stderr, code = run_command("docker images --format 'table {{.Repository}}\\t{{.Tag}}\\t{{.CreatedAt}}' | findstr flashloan")
    if stdout:
        print(stdout)
    else:
        print("No flashloan images found yet")
    print()

def check_containers():
    """Check running containers"""
    print("=== RUNNING CONTAINERS ===")
    stdout, stderr, code = run_command("docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'")
    if stdout:
        print(stdout)
    else:
        print("No containers running")
    print()

def check_container_logs(container_name):
    """Check logs for a specific container"""
    stdout, stderr, code = run_command(f"docker logs {container_name} --tail 5")
    if code == 0:
        print(f"=== {container_name.upper()} LOGS ===")
        print(stdout)
        print()

def check_build_progress():
    """Check if docker-compose build is still running"""
    stdout, stderr, code = run_command("tasklist | findstr docker")
    if "docker" in stdout.lower():
        print("=== BUILD STATUS ===")
        print("Docker build processes are still running")
        print()
        return True
    return False

def check_system_health():
    """Check health of all components"""
    print(f"=== SYSTEM HEALTH CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # Check if build is in progress
    build_running = check_build_progress()
    
    # Check images
    check_docker_images()
    
    # Check containers
    check_containers()
    
    # Check orchestrator logs if running
    stdout, stderr, code = run_command("docker ps --filter name=flashloan-orchestrator --format '{{.Names}}'")
    if stdout:
        check_container_logs("flashloan-orchestrator")
    
    return build_running

def main():
    """Main monitoring loop"""
    print("LangChain Flash Loan System Monitor")
    print("Monitoring 32-container deployment...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            build_running = check_system_health()
            
            if not build_running:
                print("Build process appears to be complete. Checking final status...")
                # Do one final comprehensive check
                check_system_health()
                break
            
            print("Waiting 30 seconds before next check...\n")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")

if __name__ == "__main__":
    main()
