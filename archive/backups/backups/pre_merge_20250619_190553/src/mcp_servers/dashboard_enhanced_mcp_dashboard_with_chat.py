#!/usr/bin/env python3
"""
Enhanced MCP Dashboard with Revenue Monitoring
Provides real-time monitoring for flash loan arbitrage system, tracking profits and system status
"""

import os
import json
import time
import logging
import argparse
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, List, Any, TypedDict
import matplotlib.pyplot as plt
# from matplotlib.figure import Figure
# from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import numpy as np
import requests  # For MCP server interaction

# The following imports are commented out because they're currently unused
# If you need them later, uncomment them
# import sys
# import threading
# import pandas as pd
# from pathlib import Path

# Parse command line arguments
parser = argparse.ArgumentParser(description='Flash Loan Arbitrage Dashboard')
parser.add_argument('--config', type=str, default='config/arbitrage-config.json',
                    help='Path to configuration file')
parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                    help='Logging level')
parser.add_argument('--log-file', type=str, default='logs/revenue_dashboard.log',
                    help='Path to log file')
args = parser.parse_args()

# Ensure logs directory exists
os.makedirs(os.path.dirname(args.log_file), exist_ok=True)

# Configure logging
log_level = getattr(logging, args.log_level)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(args.log_file)
    ]
)
logger = logging.getLogger("RevenueDashboard")

# Constants
DEFAULT_DATA_PATH = os.path.join(os.path.expanduser("~"), "Documents", "flash-loan-data.json")
DATA_FILE_PATH = os.environ.get("FLASH_LOAN_DATA_PATH", DEFAULT_DATA_PATH)
REFRESH_INTERVAL = 5000  # milliseconds
CONFIG_PATH = args.config

# Log startup information
logger.info(f"Starting Flash Loan Arbitrage Dashboard")
logger.info(f"Using configuration file: {CONFIG_PATH}")

# ──────────────────────────────────────────────────────────────────────────────
# Typed-dict models to give Pylance concrete field information
class Opportunity(TypedDict, total=False):
    id: str
    tokenIn: str
    tokenOut: str
    amountIn: str
    expectedProfit: str
    dexBuy: str
    dexSell: str
    buyPrice: str
    sellPrice: str
    gasCost: str
    confidence: float
    timestamp: int
    status: str


class Execution(TypedDict, total=False):
    id: str
    opportunityId: str
    txHash: str
    actualProfit: str
    gasUsed: str
    executionTime: float
    status: str
    error: str
    timestamp: int


class DexConfig(TypedDict, total=False):
    name: str
    routerAddress: str
    factoryAddress: str
    feeTier: float
    enabled: bool
# ──────────────────────────────────────────────────────────────────────────────

class ArbitrageDashboard:
    """Dashboard for monitoring flash loan arbitrage system"""
    
    def __init__(self, root: tk.Tk, config_path: str) -> None:
        self.root: tk.Tk = root
        self.root.title("Flash Loan Arbitrage Revenue Dashboard")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        self.config_path: str = config_path

        # Data storage
        self.opportunities: List[Opportunity] = []
        self.executions: List[Execution] = []
        self.revenue_data: Dict[str, Any] = {
            "totalProfit": "0",
            "totalTrades": 0,
            "successRate": 0,
            "averageProfit": "0",
            "lastUpdated": int(time.time())
        }
        self.dex_configs: List[DexConfig] = []  # typed-dict list

        # Historical data for charts
        self.profit_history: List[float] = []
        self.timestamp_history: List[datetime] = []

        # Tkinter widgets (type annotations for clarity)
        self.status_label: ttk.Label
        self.last_updated_label: ttk.Label
        self.total_profit_label: ttk.Label
        self.total_trades_label: ttk.Label
        self.success_rate_label: ttk.Label
        self.avg_profit_label: ttk.Label
        self.opportunity_filter: ttk.Entry
        self.opportunities_tree: ttk.Treeview
        self.opportunity_details: scrolledtext.ScrolledText
        self.execution_filter: ttk.Entry
        self.executions_tree: ttk.Treeview
        self.execution_details: scrolledtext.ScrolledText
        self.dex_tree: ttk.Treeview
        self.system_config: scrolledtext.ScrolledText
        self.log_viewer: scrolledtext.ScrolledText
        self.fig: Any
        self.ax: Any
        self.canvas: Any

        # Track if data changed
        self.data_changed: bool = True

        # Chat UI components
        self.chat_input: ttk.Entry
        self.chat_output: scrolledtext.ScrolledText

        self._setup_ui()
        self._setup_chat_ui()
        self._load_data()

        # Start periodic refresh
        self._refresh_data()


    def _setup_chat_ui(self) -> None:
        """Set up the chat UI components"""
        chat_frame = ttk.LabelFrame(self.root, text="MCP Server Chat", padding="10")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_output = scrolledtext.ScrolledText(chat_frame, height=10, state='disabled')
        self.chat_output.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, expand=False)

        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        send_button = ttk.Button(input_frame, text="Send", command=self._send_chat_message)
        send_button.pack(side=tk.RIGHT)

    def _send_chat_message(self) -> None:
        """Send chat message to MCP server and display response"""
        message = self.chat_input.get()
        if not message:
            return

        self.chat_output.configure(state='normal')
        self.chat_output.insert(tk.END, f"You: {message}\n")
        self.chat_output.configure(state='disabled')
        self.chat_input.delete(0, tk.END)

        # Placeholder for MCP server interaction
        response = self._query_mcp_server(message)

        self.chat_output.configure(state='normal')
        self.chat_output.insert(tk.END, f"MCP Server: {response}\n")
        self.chat_output.configure(state='disabled')
        self.chat_output.see(tk.END)

    def _query_mcp_server(self, message: str) -> str:
        """Query MCP server (placeholder implementation)"""
        try:
            # Replace with actual MCP server URL and logic
            response = requests.post("http://localhost:8000/query", json={"message": message})
            if response.status_code == 200:
                return response.json().get("response", "No response from MCP server.")
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Exception: {str(e)}"

    def _setup_ui(self) -> None:
        """Set up the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Style configuration
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 12))  # type: ignore
        style.configure("Header.TLabel", font=("Arial", 14, "bold"))  # type: ignore
        style.configure("Stats.TLabel", font=("Arial", 16, "bold"))  # type: ignore
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Flash Loan Arbitrage Revenue Dashboard", 
                 font=("Arial", 18, "bold")).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header_frame, text="Status: Monitoring", 
                                     font=("Arial", 12), foreground="green")
        self.status_label.pack(side=tk.RIGHT)
        
        # Tab control
        tab_control = ttk.Notebook(main_frame)
        
        # Overview tab
        overview_tab = ttk.Frame(tab_control)
        tab_control.add(overview_tab, text="Overview")
        
        # Opportunities tab
        opportunities_tab = ttk.Frame(tab_control)
        tab_control.add(opportunities_tab, text="Opportunities")
        
        # Executions tab
        executions_tab = ttk.Frame(tab_control)
        tab_control.add(executions_tab, text="Executions")
        
        # Configuration tab
        config_tab = ttk.Frame(tab_control)
        tab_control.add(config_tab, text="Configuration")
        
        # Logs tab
        logs_tab = ttk.Frame(tab_control)
        tab_control.add(logs_tab, text="Logs")
        
        tab_control.pack(expand=True, fill=tk.BOTH)
        
        # Setup overview tab
        self._setup_overview_tab(overview_tab)
        
        # Setup opportunities tab
        self._setup_opportunities_tab(opportunities_tab)
        
        # Setup executions tab
        self._setup_executions_tab(executions_tab)
        
        # Setup configuration tab
        self._setup_config_tab(config_tab)
        
        # Setup logs tab
        self._setup_logs_tab(logs_tab)
        
        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.last_updated_label = ttk.Label(footer_frame, text="Last updated: Never")
        self.last_updated_label.pack(side=tk.RIGHT)
    
    def _setup_overview_tab(self, parent: tk.Widget) -> None:
        """Set up the overview tab"""
        # Stats frame
        stats_frame = ttk.Frame(parent, padding="10")
        stats_frame.pack(fill=tk.X, expand=False)
        
        # Total profit
        profit_frame = ttk.Frame(stats_frame)
        profit_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(profit_frame, text="Total Profit", style="Header.TLabel").pack()
        self.total_profit_label = ttk.Label(profit_frame, text="$0.00", style="Stats.TLabel", foreground="green")
        self.total_profit_label.pack()
        
        # Total trades
        trades_frame = ttk.Frame(stats_frame)
        trades_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(trades_frame, text="Total Trades", style="Header.TLabel").pack()
        self.total_trades_label = ttk.Label(trades_frame, text="0", style="Stats.TLabel")
        self.total_trades_label.pack()
        
        # Success rate
        success_frame = ttk.Frame(stats_frame)
        success_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(success_frame, text="Success Rate", style="Header.TLabel").pack()
        self.success_rate_label = ttk.Label(success_frame, text="0%", style="Stats.TLabel")
        self.success_rate_label.pack()
        
        # Average profit
        avg_profit_frame = ttk.Frame(stats_frame)
        avg_profit_frame.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(avg_profit_frame, text="Avg. Profit", style="Header.TLabel").pack()
        self.avg_profit_label = ttk.Label(avg_profit_frame, text="$0.00", style="Stats.TLabel", foreground="green")
        self.avg_profit_label.pack()
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        stats_frame.grid_columnconfigure(3, weight=1)
        
        # Charts frame
        charts_frame = ttk.Frame(parent, padding="10")
        charts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Profit over time chart
        self.fig, self.ax = plt.subplots(figsize=(10, 5))  # type: ignore
        self.canvas = FigureCanvasTkAgg(self.fig, master=charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial empty chart
        self.ax.set_title("Profit Over Time")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Profit ($)")
        self.ax.grid(True)
    
    def _setup_opportunities_tab(self, parent: tk.Widget) -> None:
        """Set up the opportunities tab"""
        # Search and filter frame
        filter_frame = ttk.Frame(parent, padding="10")
        filter_frame.pack(fill=tk.X, expand=False)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.opportunity_filter = ttk.Entry(filter_frame, width=30)
        self.opportunity_filter.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(filter_frame, text="Apply Filter", 
                  command=self._filter_opportunities).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(filter_frame, text="Clear Filter", 
                  command=self._clear_opportunity_filter).pack(side=tk.LEFT)
        
        # Opportunities list
        list_frame = ttk.Frame(parent, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("id", "tokenPair", "profit", "dexBuy", "dexSell", "status", "timestamp")
        self.opportunities_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        self.opportunities_tree.heading("id", text="ID")
        self.opportunities_tree.heading("tokenPair", text="Token Pair")
        self.opportunities_tree.heading("profit", text="Expected Profit")
        self.opportunities_tree.heading("dexBuy", text="Buy DEX")
        self.opportunities_tree.heading("dexSell", text="Sell DEX")
        self.opportunities_tree.heading("status", text="Status")
        self.opportunities_tree.heading("timestamp", text="Timestamp")
        
        self.opportunities_tree.column("id", width=50)
        self.opportunities_tree.column("tokenPair", width=100)
        self.opportunities_tree.column("profit", width=100)
        self.opportunities_tree.column("dexBuy", width=100)
        self.opportunities_tree.column("dexSell", width=100)
        self.opportunities_tree.column("status", width=100)
        self.opportunities_tree.column("timestamp", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.opportunities_tree.yview)  # type: ignore
        self.opportunities_tree.configure(yscroll=scrollbar.set)  # type: ignore
        
        self.opportunities_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Opportunity details
        details_frame = ttk.LabelFrame(parent, text="Opportunity Details", padding="10")
        details_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        self.opportunity_details = scrolledtext.ScrolledText(details_frame, height=10)
        self.opportunity_details.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.opportunities_tree.bind("<<TreeviewSelect>>", self._show_opportunity_details)
    
    def _setup_executions_tab(self, parent: tk.Widget) -> None:
        """Set up the executions tab"""
        # Search and filter frame
        filter_frame = ttk.Frame(parent, padding="10")
        filter_frame.pack(fill=tk.X, expand=False)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.execution_filter = ttk.Entry(filter_frame, width=30)
        self.execution_filter.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(filter_frame, text="Apply Filter", 
                  command=self._filter_executions).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(filter_frame, text="Clear Filter", 
                  command=self._clear_execution_filter).pack(side=tk.LEFT)
        
        # Executions list
        list_frame = ttk.Frame(parent, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("id", "opportunityId", "profit", "status", "timestamp")
        self.executions_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        self.executions_tree.heading("id", text="ID")
        self.executions_tree.heading("opportunityId", text="Opportunity ID")
        self.executions_tree.heading("profit", text="Actual Profit")
        self.executions_tree.heading("status", text="Status")
        self.executions_tree.heading("timestamp", text="Timestamp")
        
        self.executions_tree.column("id", width=50)
        self.executions_tree.column("opportunityId", width=100)
        self.executions_tree.column("profit", width=100)
        self.executions_tree.column("status", width=100)
        self.executions_tree.column("timestamp", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.executions_tree.yview)  # type: ignore
        self.executions_tree.configure(yscroll=scrollbar.set)  # type: ignore
        
        self.executions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Execution details
        details_frame = ttk.LabelFrame(parent, text="Execution Details", padding="10")
        details_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        self.execution_details = scrolledtext.ScrolledText(details_frame, height=10)
        self.execution_details.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.executions_tree.bind("<<TreeviewSelect>>", self._show_execution_details)
    
    def _setup_config_tab(self, parent: tk.Widget) -> None:
        """Set up the configuration tab"""
        # DEX configuration
        dex_frame = ttk.LabelFrame(parent, text="DEX Configuration", padding="10")
        dex_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("name", "router", "factory", "feeTier", "enabled")
        self.dex_tree = ttk.Treeview(dex_frame, columns=columns, show="headings")
        
        self.dex_tree.heading("name", text="DEX Name")
        self.dex_tree.heading("router", text="Router Address")
        self.dex_tree.heading("factory", text="Factory Address")
        self.dex_tree.heading("feeTier", text="Fee Tier")
        self.dex_tree.heading("enabled", text="Enabled")
        
        self.dex_tree.column("name", width=100)
        self.dex_tree.column("router", width=200)
        self.dex_tree.column("factory", width=200)
        self.dex_tree.column("feeTier", width=100)
        self.dex_tree.column("enabled", width=100)
        
        scrollbar = ttk.Scrollbar(dex_frame, orient=tk.VERTICAL, command=self.dex_tree.yview)  # type: ignore[attr-defined]
        self.dex_tree.configure(yscroll=scrollbar.set)  # type: ignore[arg-type]

        self.dex_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # System configuration
        system_frame = ttk.LabelFrame(parent, text="System Configuration", padding="10")
        system_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        config_text = """
        Min Profit Threshold: $15.00
        Max Gas Price: 150 gwei
        Max Slippage: 1.0%
        Scan Interval: 5 seconds
        Network: Polygon Mainnet
        Contract Address: 0x...
        """
        
        self.system_config = scrolledtext.ScrolledText(system_frame, height=10)
        self.system_config.pack(fill=tk.BOTH, expand=True)
        self.system_config.insert(tk.END, config_text)
        self.system_config.configure(state="disabled")
    
    def _setup_logs_tab(self, parent: tk.Widget) -> None:
        """Set up the logs tab"""
        # Log viewer
        log_frame = ttk.Frame(parent, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_viewer = scrolledtext.ScrolledText(log_frame)
        self.log_viewer.pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = ttk.Frame(parent, padding="10")
        control_frame.pack(fill=tk.X, expand=False)
        
        ttk.Button(control_frame, text="Clear Logs", 
                  command=self._clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="Refresh Logs", 
                  command=self._refresh_logs).pack(side=tk.LEFT)
        
        # Load initial logs
        self._refresh_logs()
    
    def _load_data(self):
        """Load data from file"""
        try:
            if os.path.exists(DATA_FILE_PATH):
                with open(DATA_FILE_PATH, "r") as f:
                    data = json.load(f)
                
                self.opportunities = data.get("opportunities", [])
                self.executions = data.get("executions", [])
                self.revenue_data = data.get("revenue", self.revenue_data)
                self.dex_configs = data.get("dexConfigs", [])
                
                # Extract historical data for chart
                self._extract_historical_data()
                
                logger.info(f"Data loaded from {DATA_FILE_PATH}")
                self.data_changed = True
            else:
                logger.warning(f"Data file not found at {DATA_FILE_PATH}")
                
                # Create dummy data for testing/demo
                self._create_dummy_data()
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            
            # Create dummy data for testing/demo
            self._create_dummy_data()
    
    def _extract_historical_data(self):
        """Extract historical profit data for chart"""
        # Clear existing data
        self.profit_history = []
        self.timestamp_history = []
        
        # Get completed executions with profit
        completed_executions = [
            ex for ex in self.executions 
            if ex.get("status") == "success" and ex.get("actualProfit")
        ]
        
        # Sort by timestamp
        completed_executions.sort(key=lambda x: Any: Any: x.get("timestamp", 0))
        
        # Extract data
        cumulative_profit = 0
        for execution in completed_executions:
            try:
                profit = float(execution.get("actualProfit", "0"))
                cumulative_profit += profit
                
                self.profit_history.append(cumulative_profit)
                
                # Convert timestamp to datetime
                timestamp = datetime.fromtimestamp(execution.get("timestamp", 0))
                self.timestamp_history.append(timestamp)
            except (ValueError, TypeError):
                pass
    
    def _create_dummy_data(self):
        """Create dummy data for testing/demo"""
        logger.info("Creating dummy data for demonstration")
        
        # Create dummy opportunities
        self.opportunities = []
        # token_pairs = ["WETH/USDC", "WMATIC/USDC", "DAI/USDC", "WBTC/USDC"]  # Unused
        dexes = ["Uniswap", "SushiSwap", "QuickSwap"]
        statuses = ["detected", "executing", "completed", "failed"]
        
        for i in range(10):
            opportunity: Opportunity = {   # explicit annotation
                "id": f"opp-{i+1}",
                "tokenIn": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC on Polygon
                "tokenOut": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",  # WETH on Polygon
                "amountIn": "1000000000",  # 1000 USDC (6 decimals)
                "expectedProfit": str(15 + i * 2.5),
                "dexBuy": dexes[i % len(dexes)],
                "dexSell": dexes[(i + 1) % len(dexes)],
                "buyPrice": str(1800 + i),
                "sellPrice": str(1815 + i),
                "gasCost": "5",
                "confidence": 0.85 + (i / 100),
                "timestamp": int(time.time()) - (3600 * i),
                "status": statuses[i % len(statuses)]
            }  # type: ignore
            self.opportunities.append(opportunity)
        
        # Create dummy executions
        self.executions = []
        for i in range(8):
            execution: Execution = {      # explicit annotation
                "id": f"exec-{i+1}",
                "opportunityId": f"opp-{i+1}",
                "txHash": f"0x{'0'*40 + str(i+1)}",
                "actualProfit": str(14 + i * 2.2) if i % 4 != 3 else "0",
                "gasUsed": "250000",
                "executionTime": 2.5 + (i / 10),
                "status": "success" if i % 4 != 3 else "failed",
                "error": "" if i % 4 != 3 else "Slippage too high",
                "timestamp": int(time.time()) - (3600 * i)
            }  # type: ignore
            self.executions.append(execution)
        
        # Create dummy revenue data
        total_profit = sum(float(ex.get("actualProfit", "0")) for ex in self.executions if ex.get("status") == "success")
        success_count = sum(1 for ex in self.executions if ex.get("status") == "success")
        
        self.revenue_data = {
            "totalProfit": str(total_profit),
            "totalTrades": len(self.executions),
            "successRate": (success_count / len(self.executions)) * 100 if self.executions else 0,
            "averageProfit": str(total_profit / success_count) if success_count else "0",
            "lastUpdated": int(time.time())
        }
        
        # Create dummy DEX configs
        self.dex_configs = [
            {
                "name": "Uniswap V2",
                "routerAddress": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                "factoryAddress": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                "feeTier": 0.003,
                "enabled": True
            },
            {
                "name": "SushiSwap",
                "routerAddress": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
                "factoryAddress": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
                "feeTier": 0.003,
                "enabled": True
            },
            {
                "name": "QuickSwap",
                "routerAddress": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
                "factoryAddress": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
                "feeTier": 0.003,
                "enabled": True
            }
        ]
        
        # Extract historical data for chart
        self._extract_historical_data()
        
        # Create dummy historical data if empty
        if not self.profit_history:
            self.profit_history = [0]
            for i in range(1, 20):
                profit = self.profit_history[-1] + (5 + np.random.normal(10, 3))
                self.profit_history.append(profit)
            
            now = datetime.now()
            self.timestamp_history = [now - timedelta(hours=i) for i in range(20, 0, -1)]
        
        self.data_changed = True
    
    def _refresh_data(self):
        """Refresh data from file and update UI"""
        self._load_data()
        
        if self.data_changed:
            # Update overview
            self._update_overview()
            
            # Update opportunities list
            self._update_opportunities_list()
            
            # Update executions list
            self._update_executions_list()
            
            # Update DEX configuration
            self._update_dex_config()
            
            # Update last updated time
            last_updated = datetime.fromtimestamp(self.revenue_data.get("lastUpdated", 0))
            self.last_updated_label.config(text=f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            
            self.data_changed = False
        
        # Schedule next refresh
        self.root.after(REFRESH_INTERVAL, self._refresh_data)
    
    def _update_overview(self):
        """Update the overview tab"""
        # Update stats
        total_profit = float(self.revenue_data.get("totalProfit", "0"))
        self.total_profit_label.config(text=f"${total_profit:.2f}")
        
        total_trades = self.revenue_data.get("totalTrades", 0)
        self.total_trades_label.config(text=str(total_trades))
        
        success_rate = self.revenue_data.get("successRate", 0)
        self.success_rate_label.config(text=f"{success_rate:.1f}%")
        
        avg_profit = float(self.revenue_data.get("averageProfit", "0"))
        self.avg_profit_label.config(text=f"${avg_profit:.2f}")
        
        # Update chart
        self.ax.clear()
        
        if self.timestamp_history and self.profit_history:
            self.ax.plot(self.timestamp_history, self.profit_history, marker='o', linestyle='-', color='green')
            
            self.ax.set_title("Cumulative Profit Over Time")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Profit ($)")
            self.ax.grid(True)
            
            # Format x-axis dates
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')  # type: ignore
            
            # Add the most recent profit as an annotation
            if len(self.profit_history) > 0:
                # Matplotlib expects xy as tuple of floats; convert datetime to timestamp
                self.ax.annotate(
                    f"${self.profit_history[-1]:.2f}",
                    xy=(self.timestamp_history[-1].timestamp(), self.profit_history[-1]),
                    xytext=(10, 10),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="green", alpha=0.8)
                )
            
            self.fig.tight_layout()
            self.canvas.draw()
    
    def _update_opportunities_list(self):
        """Update the opportunities list"""
        # Clear existing items
        for item in self.opportunities_tree.get_children():
            self.opportunities_tree.delete(item)
        
        # Add opportunities
        for opp in self.opportunities:
            # Format timestamp
            timestamp = datetime.fromtimestamp(opp.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format token pair
            token_in = opp.get("tokenIn", "").split("/")[-1]
            token_out = opp.get("tokenOut", "").split("/")[-1]
            token_pair = f"{token_in}/{token_out}"
            
            # Insert item
            self.opportunities_tree.insert("", "end", values=(
                opp.get("id", ""),
                token_pair,
                f"${float(opp.get('expectedProfit', 0)):.2f}",
                opp.get("dexBuy", ""),
                opp.get("dexSell", ""),
                opp.get("status", ""),
                timestamp
            ))
    
    def _update_executions_list(self):
        """Update the executions list"""
        # Clear existing items
        for item in self.executions_tree.get_children():
            self.executions_tree.delete(item)
        
        # Add executions
        for ex in self.executions:
            # Format timestamp
            timestamp = datetime.fromtimestamp(ex.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format profit
            profit_str = f"${float(ex.get('actualProfit', 0)):.2f}" if ex.get("actualProfit") else "N/A"
            
            # Insert item
            self.executions_tree.insert("", "end", values=(
                ex.get("id", ""),
                ex.get("opportunityId", ""),
                profit_str,
                ex.get("status", ""),
                timestamp
            ))
    
    def _update_dex_config(self):
        """Update the DEX configuration list"""
        # Clear existing items
        for item in self.dex_tree.get_children():
            self.dex_tree.delete(item)
        
        # Add DEX configs
        for dex in self.dex_configs:
            # Format fee tier
            fee_tier = f"{float(dex.get('feeTier', 0)) * 100:.2f}%"
            
            # Insert item
            self.dex_tree.insert("", "end", values=(
                dex.get("name", ""),
                dex.get("routerAddress", ""),
                dex.get("factoryAddress", ""),
                fee_tier,
                "Yes" if dex.get("enabled", False) else "No"
            ))
    
    def _show_opportunity_details(self, event: Any) -> None:
        """Show details for the selected opportunity"""
        selected_items = self.opportunities_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        opp_id = self.opportunities_tree.item(item, "values")[0]
        
        # Find the opportunity
        opportunity = next((o for o in self.opportunities if o.get("id") == opp_id), None)
        if not opportunity:
            return
        
        # Clear the details text
        self.opportunity_details.delete(1.0, tk.END)
        
        # Format details
        details = f"""Opportunity ID: {opportunity.get('id', '')}
Token In: {opportunity.get('tokenIn', '')}
Token Out: {opportunity.get('tokenOut', '')}
Amount In: {float(opportunity.get('amountIn', 0)) / 10**6:.2f} USDC
Expected Profit: ${float(opportunity.get('expectedProfit', 0)):.2f}
Buy DEX: {opportunity.get('dexBuy', '')} @ ${float(opportunity.get('buyPrice', 0)):.2f}
Sell DEX: {opportunity.get('dexSell', '')} @ ${float(opportunity.get('sellPrice', 0)):.2f}
Gas Cost: ${float(opportunity.get('gasCost', 0)):.2f}
Confidence: {float(opportunity.get('confidence', 0)) * 100:.1f}%
Status: {opportunity.get('status', '')}
Timestamp: {datetime.fromtimestamp(opportunity.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Insert details
        self.opportunity_details.insert(tk.END, details)
    
    def _show_execution_details(self, event: Any) -> None:
        """Show details for the selected execution"""
        selected_items = self.executions_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        exec_id = self.executions_tree.item(item, "values")[0]
        
        # Find the execution
        execution = next((e for e in self.executions if e.get("id") == exec_id), None)
        if not execution:
            return
        
        # Clear the details text
        self.execution_details.delete(1.0, tk.END)
        
        # Format details
        details = f"""Execution ID: {execution.get('id', '')}
Opportunity ID: {execution.get('opportunityId', '')}
Transaction Hash: {execution.get('txHash', 'N/A')}
Actual Profit: ${float(execution.get('actualProfit', 0)):.2f}
Gas Used: {execution.get('gasUsed', 'N/A')}
Execution Time: {execution.get('executionTime', 'N/A')} seconds
Status: {execution.get('status', '')}
Error: {execution.get('error', 'None')}
Timestamp: {datetime.fromtimestamp(execution.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Insert details
        self.execution_details.insert(tk.END, details)
    
    def _filter_opportunities(self):
        """Filter the opportunities list"""
        filter_text = self.opportunity_filter.get().lower()
        
        # Clear existing items
        for item in self.opportunities_tree.get_children():
            self.opportunities_tree.delete(item)
        
        # Add filtered opportunities
        for opp in self.opportunities:
            # Skip if doesn't match filter
            if (filter_text and not any(filter_text in str(v).lower() for v in opp.values())):
                continue
            
            # Format timestamp
            timestamp = datetime.fromtimestamp(opp.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format token pair
            token_in = opp.get("tokenIn", "").split("/")[-1]
            token_out = opp.get("tokenOut", "").split("/")[-1]
            token_pair = f"{token_in}/{token_out}"
            
            # Insert item
            self.opportunities_tree.insert("", "end", values=(
                opp.get("id", ""),
                token_pair,
                f"${float(opp.get('expectedProfit', 0)):.2f}",
                opp.get("dexBuy", ""),
                opp.get("dexSell", ""),
                opp.get("status", ""),
                timestamp
            ))
    
    def _clear_opportunity_filter(self):
        """Clear the opportunity filter"""
        self.opportunity_filter.delete(0, tk.END)
        self._update_opportunities_list()
    
    def _filter_executions(self):
        """Filter the executions list"""
        filter_text = self.execution_filter.get().lower()
        
        # Clear existing items
        for item in self.executions_tree.get_children():
            self.executions_tree.delete(item)
        
        # Add filtered executions
        for ex in self.executions:
            # Skip if doesn't match filter
            if (filter_text and not any(filter_text in str(v).lower() for v in ex.values())):
                continue
            
            # Format timestamp
            timestamp = datetime.fromtimestamp(ex.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format profit
            profit_str = f"${float(ex.get('actualProfit', 0)):.2f}" if ex.get("actualProfit") else "N/A"
            
            # Insert item
            self.executions_tree.insert("", "end", values=(
                ex.get("id", ""),
                ex.get("opportunityId", ""),
                profit_str,
                ex.get("status", ""),
                timestamp
            ))
    
    def _clear_execution_filter(self):
        """Clear the execution filter"""
        self.execution_filter.delete(0, tk.END)
        self._update_executions_list()
    
    def _refresh_logs(self):
        """Refresh the logs"""
        try:
            log_files = [
                "arbitrage_orchestrator.log",
                "dashboard/revenue_dashboard.log",
                "mcp/flash-loan-arbitrage-mcp/arbitrage.log"
            ]
            
            combined_logs: List[str] = []
            
            for log_file in log_files:
                log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), log_file)
                if os.path.exists(log_path):
                    with open(log_path, "r") as f:
                        logs = f.readlines()
                        # Take the last 100 lines
                        combined_logs.extend(logs[-100:])
            
            # Sort by timestamp (assuming standard log format)
            combined_logs.sort()
            
            # Clear existing logs
            self.log_viewer.delete(1.0, tk.END)
            
            # Insert logs
            for log_line in combined_logs:
                self.log_viewer.insert(tk.END, log_line)
            
            # Scroll to end
            self.log_viewer.see(tk.END)
        except Exception as e:
            logger.error(f"Error refreshing logs: {str(e)}")
    
    def _clear_logs(self):
        """Clear the logs"""
        self.log_viewer.delete(1.0, tk.END)

def main():
    """Main function"""
    # Parse args already defined above
    root = tk.Tk()
    _ = ArbitrageDashboard(root, args.config)  # Suppress unused variable warning
    root.mainloop()

if __name__ == "__main__":
    main()
