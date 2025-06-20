#!/usr/bin/env python3
"""
Flash Loan Arbitrage Production Orchestrator
This script coordinates all components of the flash loan arbitrage system for real revenue generation.
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
  # import signal  # Unused, safe to remove
from datetime import datetime
from pathlib import Path
import threading
import queue
from typing import Dict, Any, Optional, Tuple, TypedDict, List, cast
import requests

# Parse command line arguments
parser = argparse.ArgumentParser(description='Flash Loan Arbitrage Orchestrator')
parser.add_argument('--config', type=str, default='config/arbitrage-config.json',
                    help='Path to configuration file')
parser.add_argument('--mode', type=str, choices=['development', 'production'], default='production',
                    help='Operation mode')
parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                    help='Logging level')
parser.add_argument('--log-file', type=str, default='logs/arbitrage_orchestrator.log',
                    help='Path to log file')
args = parser.parse_args()

# Ensure logs directory exists
os.makedirs(os.path.dirname(args.log_file), exist_ok=True)

# Set up logging
log_level = getattr(logging, args.log_level)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(args.log_file)
    ]
)
logger = logging.getLogger("ArbitrageOrchestrator")

# Log startup information
logger.info(f"Starting Flash Loan Arbitrage Orchestrator in {args.mode} mode")
logger.info(f"Using configuration file: {args.config}")

# ---------------------------------------------------------------------------
# Core orchestrator class
class ArbitrageOrchestrator:
    """Main orchestrator for the flash loan arbitrage system"""

    class Stats(TypedDict):
        opportunities_detected: int
        trades_executed: int
        successful_trades: int
        failed_trades: int
        total_profit_usd: float
        start_time: datetime
        last_trade_time: Optional[datetime]

    def __init__(self, config_path: str):
        self.config_path: str = config_path
        self.load_config()
        self.running: bool = False
        self.processes: Dict[str, subprocess.Popen[str]] = {}
        self.stats: ArbitrageOrchestrator.Stats = {
            "opportunities_detected": 0,
            "trades_executed": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 0.0,
            "start_time": datetime.now(),
            "last_trade_time": None
        }
        self.event_queue: queue.Queue[Tuple[str, str]] = queue.Queue()
        self.active_network: Optional[str] = None
        self.base_dir: Path = Path(__file__).parent.absolute()
        self.mode: str = args.mode  # Add mode from command line args
          def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            
            # Validate configuration
            self._validate_config()
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)
    
    def _validate_config(self):
        """Validate the configuration"""
        # Check if at least one network is enabled
        if not any(network["enabled"] for network in self.config["networks"].values()):
            logger.error("No networks are enabled in the configuration")
            sys.exit(1)
        
        # Check if at least one DEX is enabled
        if not any(dex["enabled"] for dex in self.config["dexes"].values()):
            logger.error("No DEXs are enabled in the configuration")
            sys.exit(1)
        
        # Check if at least one token pair is enabled
        if not any(pair["enabled"] for pair in self.config["token_pairs"]):
            logger.error("No token pairs are enabled in the configuration")
            sys.exit(1)
            
        # Select the active network (first enabled one)
        for network_name, network in self.config["networks"].items():
            if network["enabled"]:
                self.active_network = network_name
                logger.info(f"Active network set to {network_name}")
                break
                
        # Ensure we found an active network
        if self.active_network is None:
            logger.error("No active network found - this should not happen after validation")
            sys.exit(1)
    
    def start(self):
        """Start the arbitrage system"""
        logger.info("Starting Flash Loan Arbitrage System...")
        self.running = True
        
        # Start event handler thread
        threading.Thread(target=self._event_handler, daemon=True).start()
        
        try:
            # Start MCP servers
            self._start_mcp_servers()
            
            # Start opportunity scanner
            self._start_opportunity_scanner()
            
            # Start monitoring dashboard
            self._start_monitoring()
            
            # Main loop
            while self.running:
                self._display_status()
                time.sleep(10)
        
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop all components of the arbitrage system"""
        logger.info("Stopping Flash Loan Arbitrage System...")
        self.running = False
        
        # Stop all processes
        for name, process in self.processes.items():
            logger.info(f"Stopping {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping {name}: {str(e)}")
                try:
                    process.kill()
                except:
                    pass
        
        logger.info("All components stopped")
    
    def _start_mcp_servers(self):
        """Start the MCP servers"""
        logger.info("Starting MCP servers...")
        
        # Start Flash Loan Arbitrage MCP
        flash_loan_mcp_cmd = [
            "node",
            os.path.join(self.base_dir, "mcp", "flash-loan-arbitrage-mcp", "index.js")
        ]
        self.processes["flash_loan_mcp"] = subprocess.Popen(
            flash_loan_mcp_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("Flash Loan Arbitrage MCP started")
        
        # Start MCP Task Manager
        task_manager_cmd = [
            "node",
            os.path.join(self.base_dir, "mcp", "mcp-taskmanager", "index.js")
        ]
        self.processes["task_manager"] = subprocess.Popen(
            task_manager_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("MCP Task Manager started")
    
    def _start_opportunity_scanner(self):
        """Start the opportunity scanner"""
        logger.info("Starting opportunity scanner...")
        
        # Start the production arbitrage bot
        bot_cmd: List[str] = [
            sys.executable,
            os.path.join(self.base_dir, "core", "production_arbitrage_bot_final.py"),
            "--config", self.config_path,
            "--network", cast(str, self.active_network)
        ]
        self.processes["arbitrage_bot"] = subprocess.Popen(
            bot_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("Production arbitrage bot started")
        
        # Start log monitoring thread for the bot
        threading.Thread(
            target=self._monitor_process_output,
            args=("arbitrage_bot", self.processes["arbitrage_bot"]),
            daemon=True
        ).start()
    
    def _start_monitoring(self):
        """Start the monitoring dashboard"""
        logger.info("Starting monitoring dashboard...")
        
        # Start the enhanced MCP dashboard
        dashboard_cmd = [
            sys.executable,
            os.path.join(self.base_dir, "dashboard", "enhanced_mcp_dashboard_with_chat.py")
        ]
        self.processes["dashboard"] = subprocess.Popen(
            dashboard_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("Monitoring dashboard started")
    
    def _monitor_process_output(self, name: str, process: subprocess.Popen[Any]) -> None:
        """Monitor the output of a process and parse relevant events"""
        # stdout can be None when not captured; ensure it exists for type-safety
        if process.stdout is None:
            return
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            # Log the output
            logger.debug(f"{name} output: {line.strip()}")
            # Parse opportunities and trades
            if "OPPORTUNITY DETECTED" in line:
                self.event_queue.put(("opportunity_detected", line))
            elif "TRADE EXECUTED" in line:
                self.event_queue.put(("trade_executed", line))
            elif "TRADE FAILED" in line:
                self.event_queue.put(("trade_failed", line))
            elif "PROFIT" in line and "$" in line:
                self.event_queue.put(("profit_reported", line))
    
    def _event_handler(self):
        """Process events from the queue"""
        while self.running:
            try:
                event_type, data = self.event_queue.get(timeout=1)
                
                if event_type == "opportunity_detected":
                    self.stats["opportunities_detected"] += 1
                    
                elif event_type == "trade_executed":
                    self.stats["trades_executed"] += 1
                    self.stats["successful_trades"] += 1
                    self.stats["last_trade_time"] = datetime.now()
                    
                elif event_type == "trade_failed":
                    self.stats["failed_trades"] += 1
                    
                elif event_type == "profit_reported":
                    # Extract profit amount from the data
                    try:
                        profit_str = data.split("$")[1].split()[0]
                        profit = float(profit_str)
                        self.stats["total_profit_usd"] += profit
                        
                        # Send notification if monitoring is configured
                        self._send_profit_notification(profit)
                    except Exception as e:
                        logger.error(f"Failed to parse profit: {str(e)}")
                
                # Log the event
                logger.info(f"Event: {event_type} - {data.strip()}")
                
                self.event_queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Error in event handler: {str(e)}")
    
    def _send_profit_notification(self, profit: float) -> None:
        """Send a notification about profit"""
        # Discord webhook notification
        if self.config["monitoring"]["discord_webhook"]:
            try:
                webhook_url = self.config["monitoring"]["discord_webhook"]
                message = {
                    "content": f"🚀 **Flash Loan Arbitrage Profit: ${profit:.2f}** 💰\n"
                              f"Total profit: ${self.stats['total_profit_usd']:.2f}"
                }
                requests.post(webhook_url, json=message)
            except Exception as e:
                logger.error(f"Failed to send Discord notification: {str(e)}")
        
        # TODO: Add other notification methods (Telegram, Email, etc.)
    
    def _display_status(self):
        """Display the current status of the system"""
        uptime = datetime.now() - self.stats["start_time"]
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        logger.info("=" * 50)
        logger.info("FLASH LOAN ARBITRAGE SYSTEM STATUS")
        logger.info("=" * 50)
        logger.info(f"Uptime: {uptime_str}")
        logger.info(f"Active Network: {self.active_network}")
        logger.info(f"Opportunities Detected: {self.stats['opportunities_detected']}")
        logger.info(f"Trades Executed: {self.stats['trades_executed']}")
        logger.info(f"Success Rate: {self._calculate_success_rate():.2f}%")
        logger.info(f"Total Profit: ${self.stats['total_profit_usd']:.2f}")
        
        if self.stats["last_trade_time"]:
            last_trade_ago = datetime.now() - self.stats["last_trade_time"]
            last_trade_ago_str = str(last_trade_ago).split('.')[0]
            logger.info(f"Last Trade: {last_trade_ago_str} ago")
        
        logger.info("=" * 50)
    
    def _calculate_success_rate(self):
        """Calculate the success rate of trades"""
        if self.stats["trades_executed"] == 0:
            return 0.0
        return (self.stats["successful_trades"] / self.stats["trades_executed"]) * 100

def main():
    # Use the args already parsed at the module level
    logger.info(f"Starting Flash Loan Arbitrage Orchestrator with {args.config}")
    
    # Create orchestrator instance with config path from args
    orchestrator = ArbitrageOrchestrator(args.config)
    orchestrator.start()

if __name__ == "__main__":
    main()
