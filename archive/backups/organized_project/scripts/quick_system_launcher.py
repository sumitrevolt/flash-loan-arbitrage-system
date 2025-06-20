#!/usr/bin/env python3
"""
Quick System Launcher with Unicode Fix
=====================================

This launcher provides a simple way to start the system with Unicode fixes applied.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from unicode_safe_logger import get_unicode_safe_logger

logger = get_unicode_safe_logger(__name__)

def check_prerequisites():
    """Check if all prerequisites are met"""
    logger.info("[CHECK] Checking system prerequisites...")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        logger.info(f"[SUCCESS] Docker found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("[ERROR] Docker not found. Please install Docker Desktop.")
        return False
    
    # Check Docker Compose
    try:
        result = subprocess.run(['docker', 'compose', 'version'], 
                              capture_output=True, text=True, check=True)
        logger.info(f"[SUCCESS] Docker Compose found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("[ERROR] Docker Compose not found.")
        return False
    
    # Check configuration files
    required_files = [
        'unified_mcp_config.json',
        'ai_agents_config.json',
        'docker/docker-compose-self-healing.yml'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            logger.error(f"[ERROR] Missing required file: {file_path}")
            return False
        logger.info(f"[SUCCESS] Found: {file_path}")
    
    logger.info("[SUCCESS] All prerequisites met!")
    return True

def launch_system():
    """Launch the coordination system"""
    logger.info("[LAUNCH] Starting coordination system...")
    
    if not check_prerequisites():
        logger.error("[ERROR] Prerequisites not met. Exiting.")
        return False
    
    try:
        # Start with the self-healing compose file
        compose_file = "docker/docker-compose-self-healing.yml"
        
        logger.info(f"[PROCESS] Starting services from {compose_file}")
        
        # Build images first
        logger.info("[PROCESS] Building Docker images...")
        build_result = subprocess.run([
            'docker', 'compose', '-f', compose_file, 'build'
        ], capture_output=True, text=True)
        
        if build_result.returncode != 0:
            logger.error(f"[ERROR] Failed to build images: {build_result.stderr}")
            return False
        
        logger.info("[SUCCESS] Images built successfully")
        
        # Start services
        logger.info("[PROCESS] Starting services...")
        start_result = subprocess.run([
            'docker', 'compose', '-f', compose_file, 'up', '-d'
        ], capture_output=True, text=True)
        
        if start_result.returncode != 0:
            logger.error(f"[ERROR] Failed to start services: {start_result.stderr}")
            return False
        
        logger.info("[SUCCESS] Services started successfully!")
        
        # Show status
        logger.info("[INFO] Checking service status...")
        status_result = subprocess.run([
            'docker', 'compose', '-f', compose_file, 'ps'
        ], capture_output=True, text=True)
        
        if status_result.stdout:
            logger.info(f"[INFO] Service status:\n{status_result.stdout}")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error during launch: {e}")
        return False

def show_system_info():
    """Show system information"""
    logger.info("[INFO] System Information:")
    
    # Load configurations
    try:
        with open('unified_mcp_config.json', 'r') as f:
            mcp_config = json.load(f)
        
        with open('ai_agents_config.json', 'r') as f:
            ai_config = json.load(f)
        
        logger.info(f"[INFO] MCP Servers: {len(mcp_config.get('servers', {}))}")
        logger.info(f"[INFO] AI Agents: {len(ai_config.get('agents', {}))}")
        
        logger.info("[INFO] Key Services:")
        logger.info("  - MCP Coordination Hub: http://localhost:8000")
        logger.info("  - AI Agent Dashboard: http://localhost:8001")
        logger.info("  - System Health: http://localhost:8002/health")
        logger.info("  - Monitoring: http://localhost:3000")
        
    except Exception as e:
        logger.error(f"[ERROR] Could not load system info: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        if action == 'info':
            show_system_info()
        elif action == 'check':
            check_prerequisites()
        elif action == 'launch':
            launch_system()
        else:
            logger.info("[INFO] Available actions: info, check, launch")
    else:
        # Default action: launch
        if launch_system():
            show_system_info()
            logger.info("[SUCCESS] System launched successfully!")
            logger.info("[INFO] Use 'Ctrl+C' to stop the system")
        else:
            logger.error("[ERROR] Failed to launch system")
            sys.exit(1)

if __name__ == "__main__":
    main()
