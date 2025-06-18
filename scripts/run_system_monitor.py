#!/usr/bin/env python3
"""
Run script for the Flash Loan System Monitor.
Starts the system monitor and provides a simple CLI interface.
"""

import argparse
import time
import logging
import os
import json
import threading
from typing import Dict, Any, Optional, List, Generator, TextIO, IO
from datetime import datetime
import psutil
import asyncio
from contextlib import contextmanager
import sys

# Define allowed directory patterns (relative to base directory)
ALLOWED_PATHS = {
    'config': True,
    'data/metrics': True,
    'logs': True
}

def validate_path(path: str, base_dir: Optional[str] = None) -> bool:
    """
    Validate if a path is safe and within allowed directories.
    
    Args:
        path: Path to validate
        base_dir: Optional base directory (defaults to current working directory)
        
    Returns:
        bool: True if path is safe, False otherwise
    """
    try:
        if base_dir is None:
            base_dir = os.getcwd()

        # Convert paths to absolute and normalize
        abs_base = os.path.abspath(os.path.normpath(base_dir))
        abs_path = os.path.abspath(os.path.normpath(path))
        
        # Check if path is within base directory
        if not os.path.commonpath([abs_base, abs_path]).startswith(abs_base):
            return False
            
        # Get relative path for pattern matching
        rel_path = os.path.relpath(abs_path, abs_base)
        pattern = rel_path.split(os.sep)[0]
        
        return pattern in ALLOWED_PATHS
    except Exception:
        return False

@contextmanager
def safe_open(path: str, mode: str, base_dir: Optional[str] = None) -> Generator[IO[str], None, None]:
    """
    Safely open a file with path validation.
    
    Args:
        path: Path to file
        mode: File open mode ('r' or 'w')
        base_dir: Optional base directory (defaults to current directory)
        
    Returns:
        TextIO: File handle
        
    Raises:
        ValueError: If path is invalid
        IOError: If file operation fails
    """
    if not validate_path(path, base_dir):
        raise ValueError(f"Invalid or unsafe path: {path}")
        
    directory = os.path.dirname(os.path.abspath(path))
    if 'w' in mode:
        os.makedirs(directory, exist_ok=True)
        
    file = open(path, mode)
    try:
        yield file
    finally:
        file.close()

def initialize_logging(log_path: str) -> None:
    """
    Initialize logging with safe path validation.
    
    Args:
        log_path: Path to log file
        
    Raises:
        ValueError: If log path is invalid
    """
    if not validate_path(log_path):
        raise ValueError(f"Invalid log path: {log_path}")
        
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path)
        ]
    )

def setup_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Flash Loan System Monitor")
    
    parser.add_argument(
        "--contract",
        type=str,
        default="0x153dDf13D58397740c40E9D1a6e183A8c0F36c32",
        help="FlashLoanArbitrageFixed contract address"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/monitor_config.json",
        help="Path to monitor configuration file"
    )
    
    parser.add_argument(
        "--metrics_file",
        type=str,
        default="data/metrics/system_metrics.json",
        help="Path to metrics output file"
    )
    
    return parser.parse_args()

def create_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Create monitor configuration."""
    config = {
        "enabled": True,
        "interval_seconds": args.interval,
        "metrics_file": args.metrics_file,
        "max_errors_stored": 100,
        "log_to_console": True,
        "log_to_file": True,
        "log_file": "logs/system_monitor.log",
        "contract_address": args.contract
    }
    
    try:
        if not validate_path(args.config):
            raise ValueError(f"Invalid config path: {args.config}")
            
        with safe_open(args.config, 'w') as f:
            json.dump(config, f, indent=2, sort_keys=True)
            logger.info(f"Configuration saved to {args.config}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        sys.exit(1)
        
    return config

class SystemMonitor:
    """System monitor for tracking performance and health metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metrics = {}
        self.alerts = []
        
    @contextmanager
    def _open_log_files(self) -> Generator[List[TextIO], None, None]:
        """Yield opened log files and close them automatically."""
        handles: List[TextIO] = []
        try:
            for path in (
                "logs/flash_loan_system.log",
                "logs/auto_executor.log",
                "logs/price_monitor.log",
                "logs/transaction_executor.log",
            ):
                if os.path.exists(path):
                    handles.append(open(path, "r"))
            yield handles
        finally:
            for h in handles:
                h.close()

    def save_metrics(self, file_path: str, metrics: Dict[str, Any]):
        """Save metrics to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving metrics to {file_path}: {e}")

    def load_metrics(self, file_path: str) -> Dict[str, Any]:
        """Load metrics from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load metrics from {file_path}: {e}")
            return {}

    def update_rpc_metrics(self, rpc_data: Dict[str, Any]):
        """Update RPC metrics"""
        if 'rpc_metrics' not in self.metrics:
            self.metrics['rpc_metrics'] = []
        self.metrics['rpc_metrics'].append(rpc_data)
        # Keep only last 100 entries
        if len(self.metrics['rpc_metrics']) > 100:
            self.metrics['rpc_metrics'] = self.metrics['rpc_metrics'][-100:]
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "timestamp": time.time(),
            "status": "Running",
            "uptime": "N/A",
            "last_update": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return self.metrics

    def stop_monitoring(self):
        """Stop monitoring"""
        self.logger.info("Monitoring stopped")

@contextmanager
def safe_file_operation(filepath: str, mode: str = 'r') -> Generator[IO[Any], None, None]:
    """Safely handle file operations with proper error handling."""
    try:
        with open(filepath, mode) as f:
            yield f
    except Exception as e:
        logger.error(f"Error with file operation on {filepath}: {e}")
        # Create a dummy file-like object for error cases
        import io
        if 'w' in mode:
            yield io.StringIO()
        else:
            yield io.StringIO("")

def save_system_state(state: Dict[str, Any], filepath: str = "data/system_state.json"):
    """Save system state to file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with safe_file_operation(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving system state: {e}")

def load_system_state(filepath: str = "data/system_state.json") -> Dict[str, Any]:
    """Load system state from file."""
    try:
        if os.path.exists(filepath):
            with safe_file_operation(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading system state: {e}")
    
    return {}

async def monitor_system_health():
    """Monitor system health and performance."""
    monitor = SystemMonitor()
    
    while True:
        try:
            # Update metrics
            rpc_metrics = {
                "timestamp": time.time(),
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent
            }
            
            monitor.update_rpc_metrics(rpc_metrics)
            
            # Get performance summary
            summary = monitor.get_performance_summary()
            
            # Save state
            save_system_state(summary)
            
            logger.info(f"System health: CPU {summary['cpu_percent']}%, Memory {summary['memory_percent']}%")
            
            # Wait before next check
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in system health monitoring: {e}")
            await asyncio.sleep(60)

def main() -> None:
    """Main entry point."""
    try:
        # Initialize logging
        log_path = "logs/system_monitor.log"
        initialize_logging(log_path)
    except ValueError as e:
        print(f"Failed to initialize logging: {e}")
        sys.exit(1)

    # Create logger after initialization
    global logger
    logger = logging.getLogger("SystemMonitor")
    
    args = setup_args()
    
    # Validate all paths
    paths_to_validate = [
        (args.config, "config"),
        (args.metrics_file, "metrics"),
        (log_path, "log")
    ]
    
    for path, path_type in paths_to_validate:
        if not validate_path(path):
            logger.error(f"Invalid {path_type} path: {path}")
            sys.exit(1)
    
    # Create or load config
    try:
        if not os.path.exists(args.config):
            logger.info(f"Creating new config at {args.config}")
            config = create_config(args)
        else:
            with safe_open(args.config, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded existing config from {args.config}")
    except Exception as e:
        logger.error(f"Failed to handle config: {e}")
        sys.exit(1)
    
    # Create metrics directory
    try:
        metrics_dir = os.path.dirname(args.metrics_file)
        if not os.path.exists(metrics_dir):
            os.makedirs(metrics_dir, exist_ok=True)
            logger.info(f"Created metrics directory: {metrics_dir}")
    except Exception as e:
        logger.error(f"Failed to create metrics directory: {e}")
        sys.exit(1)
        
    # Import required modules
    try:
        from system_monitor import system_monitor
    except ImportError:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        try:
            from src.flash_loan.core.system_monitor import system_monitor
        except ImportError:
            logger.error("Could not import system_monitor")
            sys.exit(1)
            
    logger.info("Starting system monitor...")
    
    try:
        # Import RPC manager
        try:
            from enhanced_rpc_manager import enhanced_rpc_manager
        except ImportError:
            try:
                from src.flash_loan.core.enhanced_rpc_manager import enhanced_rpc_manager
            except ImportError:
                logger.warning("Could not import enhanced_rpc_manager")
                enhanced_rpc_manager = None
                
        # Main monitoring loop
        while True:
            try:
                if enhanced_rpc_manager:
                    rpc_metrics = enhanced_rpc_manager.get_performance_metrics()
                    system_monitor.update_rpc_metrics(rpc_metrics)
                    
                summary = system_monitor.get_performance_summary()
                
                # Clear screen safely
                if os.name == 'nt':
                    os.system('cls')
        # WARNING: This is a security risk
        # WARNING: This is a security risk
                else:
                    os.system('clear')
        # WARNING: This is a security risk
        # WARNING: This is a security risk
                
                # Display monitoring information
                print("=" * 80)
                print("FLASH LOAN SYSTEM MONITOR")
                print("=" * 80)
                print(f"Contract: {args.contract}")
                print(f"Status: {summary.get('status', 'N/A')}")
                print(f"Uptime: {summary.get('uptime', 'N/A')}")
                print(f"Last Update: {summary.get('last_update', 'N/A')}")
                print("-" * 80)
                
                # Display metrics
                metrics = system_monitor.get_metrics()
                if metrics and "performance" in metrics:
                    perf = metrics["performance"]
                    print("\nSYSTEM METRICS:")
                    print(f"Thread Count: {perf.get('thread_count', 'N/A')}")
                    
                    if (memory_mb := perf.get('memory_usage_mb', 0)) > 0:
                        print(f"Memory Usage: {memory_mb:.2f} MB")
                        
                    if (cpu_usage := perf.get('cpu_usage', -1)) >= 0:
                        print(f"CPU Usage: {cpu_usage:.1f}%")
                        
                print("-" * 80)
                
                time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Stopping system monitor...")
                system_monitor.stop_monitoring()
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Stopping system monitor...")
        system_monitor.stop_monitoring()
        
    # Start system health monitoring
    try:
        asyncio.run(monitor_system_health())
    except Exception as e:
        logger.error(f"Error starting system health monitor: {e}")
        
if __name__ == "__main__":
    main()
