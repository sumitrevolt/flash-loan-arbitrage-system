# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import asyncio
import json
import os
import signal
import subprocess
import sys

from dotenv import load_dotenv
import psutil
"""
Aave Flash Loan Monitoring System Launcher
Launches and manages all monitoring components for the arbitrage bot
"""


# Load environment
load_dotenv()

class AaveMonitoringLauncher:
    """Manages and launches all Aave monitoring components"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen[Any]] = {}
        self.monitoring_components: Dict[str, Dict[str, Any]] = {}
            'main_monitor': {}
                'script': 'monitoring/aave_flash_loan_monitor.py',
                'name': 'Aave Flash Loan Monitor',
                'port': None,
                'critical': True
            },
            'websocket_monitor': {}
                'script': 'monitoring/aave_websocket_monitor.py',
                'name': 'WebSocket Monitor',
                'port': 8765,
                'critical': True
            },
            'arbitrage_monitor': {}
                'script': 'monitoring/live_arbitrage_monitor.py',
                'name': 'Live Arbitrage Monitor',
                'port': None,
                'critical': False
            },
            'prometheus': {}
                'command': ['prometheus', '--config.file=monitoring/prometheus.yml'],
                'name': 'Prometheus',
                'port': 9090,
                'critical': True,
                'external': True
            },
            'grafana': {}
                'command': ['grafana-server', '--homepath=/usr/share/grafana'],
                'name': 'Grafana',
                'port': 3000,
                'critical': False,
                'external': True
            
        
        
        # Alert webhook (optional)
        self.alert_webhook = os.getenv('ALERT_WEBHOOK_URL')
        
    def check_prerequisites(self) -> bool:
        """Check if all required files and dependencies exist"""
        print("[SEARCH] Checking prerequisites...")
        
        # Check Python scripts
        for component, config in self.monitoring_components.items():
            if 'script' in config:
                if not Path(config['script']).exists():
                    print(f"[ERROR] Missing: {config['script']}")
                    return False
        
        # Check config file
        if not Path('production_config.json').exists():
            print("[ERROR] Missing: production_config.json")
            return False
        
        # Check environment variables
        required_env = ['POLYGON_RPC_URL']
        for env in required_env:
            if not os.getenv(env):
                print(f"[ERROR] Missing environment variable: {env}")
                return False
        
        print("[OK] All prerequisites met")
        return True
    
    def check_port_availability(self, port: int) -> bool:
        """Check if a port is available"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return False
        return True
    
    def launch_component(self, component_id: str, config: Dict[str, Any]) -> Optional[subprocess.Popen[Any]]:
        """Launch a monitoring component"""
        try:
            # Check port availability
            if config.get('port') and not self.check_port_availability(config['port']):
                print(f"[WARN]  Port {config['port']} is already in use for {config['name']}")
                return None
            
            # Launch based on type
            if 'script' in config:
                # Python script
                cmd = [sys.executable, config['script']]
                process = subprocess.Popen()
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                
            elif 'command' in config and config.get('external'):
                # External command (like Prometheus/Grafana)
                try:
                    process = subprocess.Popen()
                        config['command'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    
                except FileNotFoundError:
                    print(f"[WARN]  {config['name']} not installed, skipping...")
                    return None
            else:
                return None
            
            print(f"[OK] Launched {config['name']}")
            if config.get('port'):
                print(f"   Available at: http://localhost:{config['port']}")
            
            return process
            
        except Exception as e:
            print(f"[ERROR] Failed to launch {config['name']}: {e}")
            return None
    
    def start_all_monitors(self) -> bool:
        """Start all monitoring components"""
        print("\n[INIT] Starting Aave Flash Loan Monitoring System")
        print("="*60)
        
        if not self.check_prerequisites():
            print("[ERROR] Prerequisites check failed. Please fix the issues above.")
            return False
        
        # Launch each component
        for component_id, config in self.monitoring_components.items():
            process = self.launch_component(component_id, config)
            if process:
                self.processes[component_id] = process
            elif config.get('critical'):
                print(f"[ERROR] Failed to start critical component: {config['name']}")
                self.stop_all_monitors()
                return False
        
        print("\n[OK] All monitoring components started successfully!")
        self.display_status()
        return True
    
    def display_status(self) -> None:
        """Display status of all monitoring components"""
        print("\n[METRICS] Monitoring System Status")
        print("="*60)
        
        for component_id, process in self.processes.items():
            config = self.monitoring_components[component_id]
            
            # Check if process is still running
            if process.poll() is None:
                status = "[OK] Running"
                pid = process.pid
            else:
                status = "[ERROR] Stopped"
                pid = "N/A"
            
            print(f"{config['name']:<25} {status:<15} PID: {pid}")
            
            if config.get('port') and process.poll() is None:
                print(f"{'':>25} URL: http://localhost:{config['port']}")
        
        print("\n📌 Quick Links:")
        print("  • Main Dashboard: http://localhost:8765 (WebSocket)")
        print("  • Prometheus: http://localhost:9090")
        print("  • Grafana: http://localhost:3000")
        print("\n⌨️  Commands:")
        print("  • Press Ctrl+C to stop all monitors")
        print("  • Type 'status' to refresh status")
        print("  • Type 'restart <component>' to restart a component")
    
    def monitor_processes(self) -> None:
        """Monitor running processes and restart if needed"""
        while True:
            try:
                # Check each process
                for component_id, process in list(self.processes.items()):
                    if process.poll() is not None:
                        # Process has stopped
                        config = self.monitoring_components[component_id]
                        print(f"\n[WARN]  {config['name']} has stopped!")
                        
                        if config.get('critical'):
                            print(f"[SYNC] Restarting {config['name']}...")
                            new_process = self.launch_component(component_id, config)
                            if new_process:
                                self.processes[component_id] = new_process
                            else:
                                print(f"[ERROR] Failed to restart {config['name']}")
                
                # Wait before next check
                asyncio.run(asyncio.sleep(5))
                
            except KeyboardInterrupt:
                break
    
    def stop_all_monitors(self) -> None:
        """Stop all monitoring components"""
        print("\n[STOP] Stopping all monitoring components...")
        
        for component_id, process in self.processes.items():
            config = self.monitoring_components[component_id]
            
            if process.poll() is None:
                print(f"   Stopping {config['name']}...")
                process.terminate()
                
                # Give it time to shutdown gracefully
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    process.kill()
                    process.wait()
        
        print("[OK] All monitors stopped")
    
    def create_monitoring_dashboard_html(self) -> None:
        """Create a simple HTML dashboard"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aave Flash Loan Monitoring Dashboard</title>
    <style>
        body {}
            font-family: Arial, sans-serif;
            background-color: #1a1a1a;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        
        .container {}
            max-width: 1200px;
            margin: 0 auto;
        
        h1 {}
            text-align: center;
            color: #00d4ff;
        
        .grid {}
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 30px;
        
        .card {}
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        
        .card h2 {}
            margin-top: 0;
            color: #00d4ff;
        
        .metric {}
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 10px;
            background-color: #3a3a3a;
            border-radius: 5px;
        
        .metric-value {}
            font-weight: bold;
            color: #00ff88;
        
        .status-indicator {}
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        
        .status-active {}
            background-color: #00ff88;
        
        .status-inactive {}
            background-color: #ff4444;
        
        .iframe-container {}
            width: 100%;
            height: 600px;
            margin-top: 20px;
            border-radius: 10px;
            overflow: hidden;
        
        iframe {}
            width: 100%;
            height: 100%;
            border: none;
        
        .links {}
            text-align: center;
            margin-top: 30px;
        
        .links a {}
            color: #00d4ff;
            text-decoration: none;
            margin: 0 15px;
            padding: 10px 20px;
            border: 1px solid #00d4ff;
            border-radius: 5px;
            display: inline-block;
        
        .links a:hover {}
            background-color: #00d4ff;
            color: #1a1a1a;
        
        #ws-status {}
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 5px;
            background-color: #2a2a2a;
        
    </style>
</head>
<body>
    <div id="ws-status">
        <span class="status-indicator status-inactive"></span>
        <span>WebSocket: <span id="ws-connection">Disconnected</span></span>
    </div>
    
    <div class="container">
        <h1>🏦 Aave Flash Loan Monitoring Dashboard</h1>
        
        <div class="grid">
            <div class="card">
                <h2>[METRICS] Pool Metrics</h2>
                <div class="metric">
                    <span>USDC Liquidity</span>
                    <span class="metric-value" id="usdc-liquidity">-</span>
                </div>
                <div class="metric">
                    <span>Flash Loan Fee</span>
                    <span class="metric-value">0.09%</span>
                </div>
                <div class="metric">
                    <span>Gas Price</span>
                    <span class="metric-value" id="gas-price">-</span>
                </div>
            </div>
            
            <div class="card">
                <h2>[GROWTH] Performance</h2>
                <div class="metric">
                    <span>Total Executions</span>
                    <span class="metric-value" id="total-executions">0</span>
                </div>
                <div class="metric">
                    <span>Success Rate</span>
                    <span class="metric-value" id="success-rate">0%</span>
                </div>
                <div class="metric">
                    <span>Total Profit</span>
                    <span class="metric-value" id="total-profit">$0</span>
                </div>
            </div>
            
            <div class="card">
                <h2>[TASK] Active Opportunities</h2>
                <div id="opportunities-list">
                    <p style="text-align: center; color: #666;">Waiting for data...</p>
                </div>
            </div>
            
            <div class="card">
                <h2>[ALERT] Recent Alerts</h2>
                <div id="alerts-list">
                    <p style="text-align: center; color: #666;">No alerts</p>
                </div>
            </div>
        </div>
        
        <div class="links">
            <a href="http://localhost:9090" target="_blank">Prometheus</a>
            <a href="http://localhost:3000" target="_blank">Grafana</a>
            <a href="#" onclick="connectWebSocket()">Reconnect WebSocket</a>
        </div>
    </div>
    
    <script>
        let ws = null;
        
        function connectWebSocket() {}
            if (ws) {}
                ws.close();
            
            
            ws = new WebSocket('ws://localhost:8765');
            
            ws.onopen = function() {}
                document.getElementById('ws-connection').textContent = 'Connected';
                document.querySelector('#ws-status .status-indicator').classList.remove('status-inactive');
                document.querySelector('#ws-status .status-indicator').classList.add('status-active');
            };
            
            ws.onmessage = function(event) {}
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = function() {}
                document.getElementById('ws-connection').textContent = 'Disconnected';
                document.querySelector('#ws-status .status-indicator').classList.remove('status-active');
                document.querySelector('#ws-status .status-indicator').classList.add('status-inactive');
                
                // Reconnect after 5 seconds
                setTimeout(connectWebSocket, 5000);
            };
            
            ws.onerror = function(error) {}
                console.error('WebSocket error:', error);
            };
        
        
        function updateDashboard(data) {}
            // Update metrics based on the data received
            if (data.type === 'metrics_update') {}
                if (data.data.gas_price) {}
                    document.getElementById('gas-price').textContent = data.data.gas_price + ' gwei';
                
                // Update other metrics...
            
        
        
        // Connect on page load
        connectWebSocket();
        
        // Ping every 30 seconds to keep connection alive
        setInterval(function() {)}
            if (ws && ws.readyState === WebSocket.OPEN) {}
                ws.send(JSON.stringify({type: 'ping'}));
            
        }, 30000);
    </script>
</body>
</html>
        """
        
        # Save the HTML file
        with open('monitoring/dashboard.html', 'w') as f:
            f.write(html_content)
        
        print("📄 Created dashboard.html")

def main():
    """Main function"""
    launcher = AaveMonitoringLauncher()
    
    # Create dashboard HTML
    launcher.create_monitoring_dashboard_html()
    
    # Handle signals for graceful shutdown
    def signal_handler(sig: int, frame: Any) -> None:
        print("\n\n[STOP] Received shutdown signal")
        launcher.stop_all_monitors()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start all monitors
    if launcher.start_all_monitors():
        print("\n[OK] Monitoring system is running!")
        print("[METRICS] Open dashboard.html in your browser for the web interface")
        
        # Monitor processes
        launcher.monitor_processes()
    else:
        print("\n[ERROR] Failed to start monitoring system")
        sys.exit(1)

if __name__ == "__main__":
    main()