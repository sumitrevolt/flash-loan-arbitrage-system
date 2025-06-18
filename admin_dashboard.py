#!/usr/bin/env python3
"""
Admin Dashboard and Control Interface
====================================

Web-based admin interface for controlling the arbitrage system.
Provides real-time monitoring and control capabilities.
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import json
import os
import subprocess
import psutil
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML Template for Admin Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Arbitrage System Admin Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .metric { text-align: center; padding: 15px; border-radius: 8px; }
        .metric-value { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .metric-label { color: #666; }
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-info { background: #17a2b8; color: white; }
        .status-running { background: #d4edda; color: #155724; }
        .status-paused { background: #fff3cd; color: #856404; }
        .status-stopped { background: #f8d7da; color: #721c24; }
        .opportunities-table { width: 100%; border-collapse: collapse; }
        .opportunities-table th, .opportunities-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        .opportunities-table th { background: #f8f9fa; }
        .log-container { height: 300px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; }
        .refresh-notice { color: #666; font-style: italic; margin-top: 10px; }
        .chart-container { height: 300px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 24/7 Arbitrage System - Admin Dashboard</h1>
            <p>Production monitoring and control interface</p>
        </div>

        <!-- System Controls -->
        <div class="card">
            <h2>System Controls</h2>
            <div style="text-align: center;">
                <button class="btn btn-success" onclick="controlSystem('start')">▶️ Start System</button>
                <button class="btn btn-warning" onclick="controlSystem('pause')">⏸️ Pause System</button>
                <button class="btn btn-info" onclick="controlSystem('resume')">▶️ Resume System</button>
                <button class="btn btn-danger" onclick="controlSystem('stop')">⏹️ Stop System</button>
            </div>
            <div id="control-status" style="margin-top: 15px; text-align: center;"></div>
        </div>

        <!-- System Status -->
        <div class="card">
            <h2>System Status</h2>
            <div class="status-grid">
                <div class="metric status-running">
                    <div class="metric-value" id="system-status">{{ system_status }}</div>
                    <div class="metric-label">System Status</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="uptime">{{ uptime }}</div>
                    <div class="metric-label">Uptime</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="opportunities-found">{{ opportunities_found }}</div>
                    <div class="metric-label">Opportunities Found</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="opportunities-executed">{{ opportunities_executed }}</div>
                    <div class="metric-label">Opportunities Executed</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="total-profit">${{ total_profit }}</div>
                    <div class="metric-label">Total Profit</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="success-rate">{{ success_rate }}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>
        </div>

        <!-- MCP Servers & AI Agents Status -->
        <div class="card">
            <h2>MCP Servers & AI Agents</h2>
            <div class="status-grid">
                <div class="metric">
                    <div class="metric-value" id="mcp-status">{{ mcp_servers_active }}/6</div>
                    <div class="metric-label">MCP Servers Active</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="ai-status">{{ ai_agents_active }}/4</div>
                    <div class="metric-label">AI Agents Active</div>
                </div>
            </div>
            <div id="services-detail" style="margin-top: 15px;">
                <!-- Services details will be populated by JavaScript -->
            </div>
        </div>

        <!-- Current Opportunities -->
        <div class="card">
            <h2>Current Arbitrage Opportunities</h2>
            <div id="opportunities-container">
                <table class="opportunities-table">
                    <thead>
                        <tr>
                            <th>Token</th>
                            <th>Buy DEX</th>
                            <th>Sell DEX</th>
                            <th>Price Diff</th>
                            <th>Net Profit</th>
                            <th>Confidence</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="opportunities-table-body">
                        <!-- Opportunities will be populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- System Configuration -->
        <div class="card">
            <h2>Configuration</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h4>Profit Parameters</h4>
                    <p>Min Profit: ${{ min_profit }}</p>
                    <p>Max Profit: ${{ max_profit }}</p>
                    <p>Monitoring Interval: {{ monitoring_interval }}s</p>
                </div>
                <div>
                    <h4>Network Info</h4>
                    <p>Network: Polygon Mainnet</p>
                    <p>Wallet: {{ wallet_address }}</p>
                    <p>Contract: {{ contract_address }}</p>
                </div>
            </div>
        </div>

        <!-- System Logs -->
        <div class="card">
            <h2>Recent System Logs</h2>
            <div class="log-container" id="system-logs">
                <!-- Logs will be populated by JavaScript -->
            </div>
            <div class="refresh-notice">Logs auto-refresh every 10 seconds</div>
        </div>
    </div>

    <script>
        // Auto-refresh dashboard every 5 seconds
        setInterval(refreshDashboard, 5000);
        
        // Auto-refresh logs every 10 seconds
        setInterval(refreshLogs, 10000);
        
        // Initial load
        refreshDashboard();
        refreshLogs();
        
        function refreshDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateMetrics(data);
                    updateOpportunities(data.opportunities || []);
                    updateServicesStatus(data.services || {});
                })
                .catch(error => console.error('Error refreshing dashboard:', error));
        }
        
        function refreshLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('system-logs').innerHTML = data.logs.join('\\n');
                })
                .catch(error => console.error('Error refreshing logs:', error));
        }
        
        function updateMetrics(data) {
            document.getElementById('system-status').textContent = data.system_status || 'Unknown';
            document.getElementById('uptime').textContent = data.uptime || '0s';
            document.getElementById('opportunities-found').textContent = data.opportunities_found || '0';
            document.getElementById('opportunities-executed').textContent = data.opportunities_executed || '0';
            document.getElementById('total-profit').textContent = (data.total_profit || 0).toFixed(2);
            document.getElementById('success-rate').textContent = (data.success_rate || 0).toFixed(1);
            document.getElementById('mcp-status').textContent = (data.mcp_servers_active || 0) + '/6';
            document.getElementById('ai-status').textContent = (data.ai_agents_active || 0) + '/4';
        }
        
        function updateOpportunities(opportunities) {
            const tbody = document.getElementById('opportunities-table-body');
            tbody.innerHTML = '';
            
            if (opportunities.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #666;">No opportunities currently detected</td></tr>';
                return;
            }
            
            opportunities.slice(0, 10).forEach(opp => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${opp.token_symbol || 'N/A'}</td>
                    <td>${opp.buy_dex || 'N/A'}</td>
                    <td>${opp.sell_dex || 'N/A'}</td>
                    <td>${(opp.price_diff_pct || 0).toFixed(2)}%</td>
                    <td>$${(opp.net_profit_usd || 0).toFixed(2)}</td>
                    <td>${((opp.confidence_score || 0) * 100).toFixed(0)}%</td>
                    <td>${opp.execution_ready ? '✅ Ready' : '⏳ Pending'}</td>
                `;
            });
        }
        
        function updateServicesStatus(services) {
            const container = document.getElementById('services-detail');
            let html = '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">';
            
            html += '<div><h4>MCP Servers</h4><ul>';
            for (const [name, status] of Object.entries(services.mcp_servers || {})) {
                html += `<li>${name}: ${status ? '✅ Active' : '❌ Inactive'}</li>`;
            }
            html += '</ul></div>';
            
            html += '<div><h4>AI Agents</h4><ul>';
            for (const [name, status] of Object.entries(services.ai_agents || {})) {
                html += `<li>${name}: ${status ? '✅ Active' : '❌ Inactive'}</li>`;
            }
            html += '</ul></div></div>';
            
            container.innerHTML = html;
        }
        
        function controlSystem(action) {
            fetch('/api/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({action: action})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('control-status').innerHTML = 
                    `<div style="color: ${data.success ? 'green' : 'red'};">${data.message}</div>`;
                if (data.success) {
                    setTimeout(refreshDashboard, 1000);
                }
            })
            .catch(error => {
                document.getElementById('control-status').innerHTML = 
                    `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
    </script>
</body>
</html>
"""

class SystemController:
    def __init__(self):
        self.system_process = None
        
    def get_system_status(self):
        """Get current system status"""
        try:
            # Check if main arbitrage system is running
            system_running = self._is_process_running('production_arbitrage_system.py')
            
            # Check MCP servers
            mcp_servers = {
                'real_time_price': self._is_port_in_use(8001),
                'profit_optimizer': self._is_port_in_use(8002),
                'aave_integration': self._is_port_in_use(8003),
                'dex_aggregator': self._is_port_in_use(8004),
                'risk_management': self._is_port_in_use(8005),
                'monitoring': self._is_port_in_use(8006)
            }
            
            # Check AI agents
            ai_agents = {
                'arbitrage_detector': self._is_port_in_use(9001),
                'risk_manager': self._is_port_in_use(9002),
                'route_optimizer': self._is_port_in_use(9003),
                'market_analyzer': self._is_port_in_use(9004)
            }
            
            # Read system stats if available
            stats = self._read_system_stats()
            
            return {
                'system_status': 'Running' if system_running else 'Stopped',
                'system_running': system_running,
                'mcp_servers': mcp_servers,
                'ai_agents': ai_agents,
                'mcp_servers_active': sum(mcp_servers.values()),
                'ai_agents_active': sum(ai_agents.values()),
                'services': {
                    'mcp_servers': mcp_servers,
                    'ai_agents': ai_agents
                },
                **stats
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
            
    def _is_process_running(self, process_name):
        """Check if a process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if any(process_name in arg for arg in proc.info['cmdline'] or []):
                    return True
            return False
        except:
            return False
            
    def _is_port_in_use(self, port):
        """Check if a port is in use"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
            return False
        except:
            return False
            
    def _read_system_stats(self):
        """Read system statistics"""
        try:
            # Try to read from status file
            if os.path.exists('system_status.json'):
                with open('system_status.json', 'r') as f:
                    return json.load(f)
            else:
                # Return default stats
                return {
                    'uptime': '0s',
                    'opportunities_found': 0,
                    'opportunities_executed': 0,
                    'total_profit': 0.0,
                    'success_rate': 0.0,
                    'opportunities': []
                }
        except:
            return {}
            
    def control_system(self, action):
        """Control the arbitrage system"""
        try:
            if action == 'start':
                if not self._is_process_running('production_arbitrage_system.py'):
                    self.system_process = subprocess.Popen([
                        'python', 'production_arbitrage_system.py'
                    ])
                    return {'success': True, 'message': 'System started successfully'}
                else:
                    return {'success': False, 'message': 'System is already running'}
                    
            elif action == 'pause':
                # Create pause control file
                with open('admin_controls.json', 'w') as f:
                    json.dump({'pause': True, 'stop': False}, f)
                return {'success': True, 'message': 'System paused'}
                
            elif action == 'resume':
                # Remove pause control
                with open('admin_controls.json', 'w') as f:
                    json.dump({'pause': False, 'stop': False}, f)
                return {'success': True, 'message': 'System resumed'}
                
            elif action == 'stop':
                # Create stop control file
                with open('admin_controls.json', 'w') as f:
                    json.dump({'pause': False, 'stop': True}, f)
                    
                # Terminate process if running
                if self.system_process:
                    self.system_process.terminate()
                    
                return {'success': True, 'message': 'System stopped'}
                
            else:
                return {'success': False, 'message': f'Unknown action: {action}'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}

controller = SystemController()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    status = controller.get_system_status()
    
    return render_template_string(DASHBOARD_HTML,
        system_status=status.get('system_status', 'Unknown'),
        uptime=status.get('uptime', '0s'),
        opportunities_found=status.get('opportunities_found', 0),
        opportunities_executed=status.get('opportunities_executed', 0),
        total_profit=status.get('total_profit', 0),
        success_rate=status.get('success_rate', 0),
        mcp_servers_active=status.get('mcp_servers_active', 0),
        ai_agents_active=status.get('ai_agents_active', 0),
        min_profit=3.0,
        max_profit=30.0,
        monitoring_interval=2,
        wallet_address=os.getenv('ARBITRAGE_WALLET_ADDRESS', 'Not configured')[:20] + '...',
        contract_address=os.getenv('CONTRACT_ADDRESS', 'Not configured')[:20] + '...'
    )

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify(controller.get_system_status())

@app.route('/api/control', methods=['POST'])
def api_control():
    """API endpoint for system control"""
    data = request.json
    action = data.get('action', '')
    result = controller.control_system(action)
    return jsonify(result)

@app.route('/api/logs')
def api_logs():
    """API endpoint for system logs"""
    try:
        logs = []
        if os.path.exists('logs/production_arbitrage.log'):
            with open('logs/production_arbitrage.log', 'r') as f:
                logs = f.readlines()[-50:]  # Last 50 lines
        
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'logs': [f'Error reading logs: {str(e)}']})

if __name__ == '__main__':
    logger.info("Starting Admin Dashboard on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
