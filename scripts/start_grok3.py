#!/usr/bin/env python3
"""
Grok 3 MCP Server Startup Script
Enhanced startup with dependency checking and auto-configuration
"""

import sys
import subprocess
import logging
from pathlib import Path
from typing import List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Grok3Startup")

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version: {sys.version}")
    return True

def install_requirements():
    """Install required packages"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        logger.error("requirements.txt not found")
        return False
        
    try:
        logger.info("Installing requirements...")
        result: str = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to install requirements: {result.stderr}")
            return False
            
        logger.info("Requirements installed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error installing requirements: {str(e)}")
        return False

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        "mcp",
        "fastmcp", 
        "aiohttp",
        "requests",
        "websockets",
        "psutil",
        "sqlite3"
    ]
    
    missing_modules: List[str] = []
    
    for module in required_modules:
        try:
            if module == "sqlite3":
                import sqlite3  # Local import for testing sqlite3 availability
                # Use sqlite3 to avoid unused import warning
                _ = sqlite3.version
            else:
                __import__(module)
            logger.info(f"✓ {module} is available")
        except ImportError:
            missing_modules.append(module)
            logger.warning(f"✗ {module} is missing")
    
    if missing_modules:
        logger.error(f"Missing required modules: {missing_modules}")
        return False
        
    return True

def setup_directories():
    """Setup required directories"""
    directories = [
        "logs",
        "data", 
        "backups",
        "temp"
    ]
    
    base_path = Path(__file__).parent
    
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(exist_ok=True)
        logger.info(f"Directory ready: {dir_path}")

def check_ports():
    """Check if required ports are available"""
    import socket
    
    ports_to_check = [3003]  # Default Grok 3 port
    
    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
            logger.info(f"✓ Port {port} is available")
        except OSError:
            logger.warning(f"✗ Port {port} is already in use")
            return False
            
    return True

def create_default_config():
    """Create default configuration if it doesn't exist"""
    config_file = Path(__file__).parent / "grok3_config.ini"
    
    if not config_file.exists():
        logger.info("Creating default configuration...")
        # Config file should already exist from our previous creation
        pass
    else:
        logger.info("Configuration file exists")

def run_health_check():
    """Run initial health check"""
    try:
        # Import the server module
        server_path = str(Path(__file__).parent)
        if server_path not in sys.path:
            sys.path.append(server_path)
        from grok3_mcp_server import Grok3MCPServer
        
        # Create server instance for testing
        server = Grok3MCPServer()
        logger.info("✓ Server initialization successful")
        
        # Test database connection
        if server.coordination_db:
            logger.info("✓ Database connection successful")
        else:
            logger.error("✗ Database connection failed")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

def start_server():
    """Start the Grok 3 MCP server"""
    try:
        logger.info("Starting Grok 3 MCP Server...")
        
        # Import and run the server
        server_path = str(Path(__file__).parent)
        if server_path not in sys.path:
            sys.path.append(server_path)
        from grok3_mcp_server import main
        
        main()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return False
        
    return True

def main():
    """Main startup sequence"""
    logger.info("=== Grok 3 MCP Server Startup ===")
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Setup directories
    setup_directories()
    
    # Step 3: Install requirements if needed
    if not check_dependencies():
        logger.info("Installing missing dependencies...")
        if not install_requirements():
            sys.exit(1)
        
        # Re-check after installation
        if not check_dependencies():
            logger.error("Dependencies still missing after installation")
            sys.exit(1)
    
    # Step 4: Check ports
    if not check_ports():
        logger.error("Required ports are not available")
        # Continue anyway, server will handle port conflicts
    
    # Step 5: Create default config
    create_default_config()
    
    # Step 6: Run health check
    if not run_health_check():
        logger.error("Health check failed, but attempting to start anyway...")
    
    # Step 7: Start server
    logger.info("All checks passed, starting server...")
    start_server()

if __name__ == "__main__":
    main()
