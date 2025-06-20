#!/usr/bin/env python3
"""
System Status Monitor for Flash Loan Docker Containers
"""

import subprocess
import time
import json
from datetime import datetime

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def check_docker_status():
    """Check Docker daemon status"""
    stdout, stderr, code = run_command("docker version --format json")
    if code == 0:
        try:
            version_info = json.loads(stdout)
            return True, f"Docker {version_info.get('Client', {}).get('Version', 'unknown')}"
        except:
            return True, "Docker running"
    return False, stderr

def check_containers():
    """Check container status"""
    stdout, stderr, code = run_command("docker compose ps --format json")
    if code == 0 and stdout:
        try:
            containers = json.loads(stdout) if stdout.startswith('[') else [json.loads(line) for line in stdout.split('\n') if line.strip()]
            return containers
        except:
            return []
    return []

def check_build_progress():
    """Check if build is in progress"""
    stdout, stderr, code = run_command("docker compose ps --format table")
    return stdout, stderr

def monitor_system():
    """Main monitoring function"""
    print("=== Flash Loan System Monitor ===")
    print(f"Started at: {datetime.now()}")
    print("-" * 50)
    
    # Check Docker status
    docker_ok, docker_msg = check_docker_status()
    print(f"Docker Status: {'✅' if docker_ok else '❌'} {docker_msg}")
    
    if not docker_ok:
        print("Docker is not running. Please start Docker and try again.")
        return
    
    # Monitor containers
    print("\nMonitoring containers...")
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n--- Check #{iteration} at {datetime.now().strftime('%H:%M:%S')} ---")
        
        # Check containers
        containers = check_containers()
        if containers:
            print("Containers found:")
            for container in containers:
                name = container.get('Name', 'unknown')
                status = container.get('State', 'unknown')
                health = container.get('Health', 'unknown')
                print(f"  📦 {name}: {status} (Health: {health})")
        else:
            print("No containers running yet...")
            
            # Check if build is happening
            build_output, build_error = check_build_progress()
            if "build" in build_error.lower() or "building" in build_output.lower():
                print("🔨 Build appears to be in progress...")
            
        # Check logs from specific containers if they exist
        log_containers = ['flashloan-orchestrator', 'flashloan-mcp-servers', 'flashloan-agents']
        for container_name in log_containers:
            stdout, stderr, code = run_command(f"docker logs --tail=3 {container_name} 2>/dev/null")
            if code == 0 and stdout:
                print(f"📋 Recent logs from {container_name}:")
                for line in stdout.split('\n')[-3:]:
                    if line.strip():
                        print(f"    {line}")
        
        # Wait before next check
        time.sleep(30)

if __name__ == "__main__":
    try:
        monitor_system()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
    except Exception as e:
        print(f"\nMonitoring error: {e}")
