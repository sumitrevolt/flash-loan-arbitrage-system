#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Unified MCP Coordination System

This script starts the complete coordination system including:
- Server discovery and registry
- Health monitoring
- Deployment management  
- Configuration management
- Log aggregation
- Web dashboard
- Integration with LangChain and AutoGen systems
"""

from datetime import datetime
from pathlib import Path
import argparse
import asyncio
import logging
import os
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_coordination.unified_coordinator import UnifiedCoordinator

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcp_coordination.log')



logger = logging.getLogger(__name__)


def print_banner():
    """Print system banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════════════════╗
    ║                       MCP Unified Coordination System                            ║
    ║                                                                                  ║
    ║  Comprehensive management for LangChain and AutoGen MCP server integrations     ║
    ║                                                                                  ║
    ║  Features:                                                                       ║
    ║  • Automatic server discovery and registration                                  ║
    ║  • Health monitoring with circuit breakers                                      ║
    ║  • Unified deployment management                                                ║
    ║  • Real-time web dashboard                                                      ║
    ║  • Centralized configuration management                                         ║
    ║  • Comprehensive log aggregation                                                ║
    ║  • Flash loan arbitrage coordination                                            ║
    ║                                                                                  ║
    ╚══════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def setup_argument_parser():
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Unified MCP Coordination System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Start with default configuration
  %(prog)s --config config/custom.yaml  # Use custom configuration
  %(prog)s --log-level DEBUG            # Enable debug logging
  %(prog)s --daemonize                  # Run as background daemon
  %(prog)s --check-config               # Validate configuration only
        """

    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file (default: auto-discover)"

    
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"

    
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/mcp_coordination.log",
        help="Log file path (default: logs/mcp_coordination.log)"

    
    parser.add_argument(
        "--daemonize", "-d",
        action="store_true",
        help="Run as background daemon"

    
    parser.add_argument(
        "--pid-file",
        type=str,
        default="mcp_coordination.pid",
        help="PID file for daemon mode (default: mcp_coordination.pid)"

    
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate configuration and exit"

    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="MCP Coordination System v1.0.0"

    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Initialize system but don't start services"

    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force start even if another instance is running"

    
    return parser


def setup_logging(log_level: str, log_file: str):
    """Setup enhanced logging configuration"""
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with detailed output
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'

    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    logger.info(f"Logging configured: level={log_level}, file={log_file}")


def check_system_requirements():
    """Check system requirements and dependencies"""
    logger.info("Checking system requirements...")
    
    requirements = {
        "python_version": (3, 8),
        "required_modules": [
            "asyncio", "aiohttp", "fastapi", "uvicorn", "websockets",
            "yaml", "pydantic", "jinja2", "psutil"
        ],
        "optional_modules": ["docker", "redis", "numpy", "pandas"]

    
    # Check Python version
    if sys.version_info < requirements["python_version"]:
        logger.error(f"Python {requirements['python_version'][0]}.{requirements['python_version'][1]}+ required")
        return False
    
    # Check required modules
    missing_required = []
    for module in requirements["required_modules"]:
        try:
            __import__(module)
        except ImportError:
            missing_required.append(module)
    
    if missing_required:
        logger.error(f"Missing required modules: {', '.join(missing_required)}")
        logger.error("Install with: pip install -r src/mcp_coordination/requirements.txt")
        return False
    
    # Check optional modules
    missing_optional = []
    for module in requirements["optional_modules"]:
        try:
            __import__(module)
        except ImportError:
            missing_optional.append(module)
    
    if missing_optional:
        logger.warning(f"Missing optional modules: {', '.join(missing_optional)}")
        logger.warning("Some features may be limited")
    
    logger.info("System requirements check passed")
    return True


def check_permissions():
    """Check file system permissions"""
    logger.info("Checking permissions...")
    
    required_dirs = [
        "config",
        "logs",
        "mcp_servers",
        "src/mcp_coordination"

    
    for dir_path in required_dirs:
        path = Path(dir_path)
        
        # Create directory if it doesn't exist
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            logger.error(f"Permission denied creating directory: {dir_path}")
            return False
        
        # Check write permissions
        if not os.access(path, os.W_OK):
            logger.error(f"No write permission for directory: {dir_path}")
            return False
    
    logger.info("Permissions check passed")
    return True


def check_running_instance(pid_file: str, force: bool = False):
    """Check if another instance is already running"""
    pid_path = Path(pid_file)
    
    if not pid_path.exists():
        return True
    
    try:
        with open(pid_path, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is still running
        try:
            import psutil
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                if "mcp_coordination" in ' '.join(process.cmdline()).lower():
                    if force:
                        logger.warning(f"Forcing start despite running instance (PID: {pid})")
                        return True
                    else:
                        logger.error(f"Another instance is already running (PID: {pid})")
                        logger.error("Use --force to override or stop the existing instance")
                        return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process doesn't exist or can't access it, remove stale PID file
            pid_path.unlink()
    
    except (ValueError, FileNotFoundError):
        # Invalid or missing PID file
        if pid_path.exists():
            pid_path.unlink()
    
    return True


def write_pid_file(pid_file: str):
    """Write current process PID to file"""
    try:
        pid_path = Path(pid_file)
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(pid_path, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"PID file written: {pid_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write PID file: {e}")
        return False


def cleanup_pid_file(pid_file: str):
    """Remove PID file on exit"""
    try:
        pid_path = Path(pid_file)
        if pid_path.exists():
            pid_path.unlink()
            logger.info("PID file removed")
    except Exception as e:
        logger.warning(f"Failed to remove PID file: {e}")


async def validate_configuration(config_file: str = None):
    """Validate configuration without starting services"""
    logger.info("Validating configuration...")
    
    try:
        coordinator = UnifiedCoordinator(config_file)
        
        # Initialize config manager only
        from src.mcp_coordination.config_manager import ConfigManager
        config_manager = ConfigManager(coordinator.config)
        await config_manager.initialize()
        
        # Validate all configurations
        validation_results = await config_manager.validate_all_configurations()
        
        total_errors = sum(len(errors) for errors in validation_results.values())
        
        if total_errors == 0:
            logger.info("✓ Configuration validation passed")
            print("\n✓ All configurations are valid")
            return True
        else:
            logger.error(f"✗ Configuration validation failed with {total_errors} errors")
            print(f"\n✗ Configuration validation failed with {total_errors} errors:")
            
            for config_name, errors in validation_results.items():
                if errors:
                    print(f"\n{config_name}:")
                    for error in errors:
                        print(f"  - {error}")
            
            return False
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        print(f"\n✗ Configuration validation failed: {e}")
        return False


async def run_system(args):
    """Run the coordination system"""
    coordinator = None
    
    try:
        logger.info("Starting MCP Unified Coordination System...")
        print(f"\n🚀 Starting system at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create coordinator
        coordinator = UnifiedCoordinator(args.config)
        
        if args.dry_run:
            logger.info("Dry run mode: initializing but not starting services")
            await coordinator.initialize()
            print("\n✓ System initialized successfully (dry run)")
            print("✓ All components ready")
            return True
        
        # Run the system
        await coordinator.run()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        print("\n\n⚠️  Shutdown signal received...")
    except Exception as e:
        logger.error(f"System error: {e}")
        print(f"\n❌ System error: {e}")
        return False
    finally:
        if coordinator:
            try:
                await coordinator.shutdown()
                print("✓ System shutdown completed")
            except Exception as e:
                logger.error(f"Shutdown error: {e}")
                print(f"❌ Shutdown error: {e}")
    
    return True


def run_as_daemon(args):
    """Run system as background daemon"""
    try:
        import daemon
        import daemon.pidfile
        
        logger.info("Starting as daemon...")
        
        with daemon.DaemonContext(
            pidfile=daemon.pidfile.PIDLockFile(args.pid_file),
            stdout=open('daemon.log', 'a'),
            stderr=open('daemon.log', 'a')
        ):
            asyncio.run(run_system(args))
            
    except ImportError:
        logger.error("python-daemon package required for daemon mode")
        logger.error("Install with: pip install python-daemon")
        return False
    except Exception as e:
        logger.error(f"Daemon startup failed: {e}")
        return False
    
    return True


def main():
    """Main entry point"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    logger.info("=" * 60)
    logger.info("MCP Unified Coordination System starting...")
    logger.info(f"Arguments: {vars(args)}")
    logger.info("=" * 60)
    
    # Pre-flight checks
    if not check_system_requirements():
        sys.exit(1)
    
    if not check_permissions():
        sys.exit(1)
    
    if not check_running_instance(args.pid_file, args.force):
        sys.exit(1)
    
    # Configuration validation mode
    if args.check_config:
        success = asyncio.run(validate_configuration(args.config))
        sys.exit(0 if success else 1)
    
    # Write PID file
    if not write_pid_file(args.pid_file):
        sys.exit(1)
    
    try:
        # Run system
        if args.daemonize:
            success = run_as_daemon(args)
        else:
            success = asyncio.run(run_system(args))
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        cleanup_pid_file(args.pid_file)


if __name__ == "__main__":
    main()